"""
ARP Processor

Handles fetching, transforming, and persisting ARP (Price Registration Records) data.
"""

import asyncio
from typing import List, Dict, Any, Tuple
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from api_client import AsyncARPAPIClient
from database import bulk_upsert_arps, bulk_upsert_orgaos
from .transformers import transform_arps_batch, validate_arp
from config import config

logger = structlog.get_logger(__name__)


class ARPProcessor:
    """
    Processor for ARP data

    Coordinates fetching ARPs from API and persisting to database.
    """

    def __init__(self, api_client: AsyncARPAPIClient):
        """
        Initialize ARP processor

        Args:
            api_client: API client instance
        """
        self.api_client = api_client
        self.stats = {
            "fetched": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }

    async def fetch_arps_for_date_range(
        self,
        date_start: date,
        date_end: date,
        max_pages: int = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all ARPs for a date range (handles pagination)

        Args:
            date_start: Start date
            date_end: End date
            max_pages: Maximum pages to fetch (None = all pages)

        Returns:
            List of ARP dictionaries from API
        """
        all_arps = []
        page = 1

        logger.info(
            "fetching_arps_range",
            date_start=str(date_start),
            date_end=str(date_end)
        )

        while True:
            try:
                response = await self.api_client.fetch_arps_page(
                    date_start,
                    date_end,
                    page
                )

                arps = response.get("resultado", [])
                if not arps:
                    break

                all_arps.extend(arps)
                self.stats["fetched"] += len(arps)

                logger.info(
                    "arps_page_fetched",
                    page=page,
                    arps_in_page=len(arps),
                    total_fetched=self.stats["fetched"]
                )

                # Check if more pages
                total_pages = response.get("totalPaginas", 1)
                if page >= total_pages:
                    break

                # Check max_pages limit (for testing)
                if max_pages and page >= max_pages:
                    logger.warning("max_pages_reached", max_pages=max_pages)
                    break

                page += 1

            except Exception as e:
                logger.error(
                    "fetch_arps_page_error",
                    page=page,
                    error=str(e)
                )
                self.stats["errors"] += 1
                break

        logger.info(
            "arps_range_fetch_complete",
            total_arps=len(all_arps),
            total_pages=page
        )

        return all_arps

    async def process_and_persist_arps(
        self,
        session: AsyncSession,
        api_arps: List[Dict[str, Any]],
        validate: bool = True
    ) -> Tuple[int, int, int]:
        """
        Transform and persist ARPs to database

        Args:
            session: Database session
            api_arps: List of ARPs from API
            validate: Whether to validate data before insertion

        Returns:
            Tuple of (inserted_count, updated_count, skipped_count)
        """
        if not api_arps:
            return 0, 0, 0

        # Transform ARPs and extract orgaos
        transformed_arps, orgaos = transform_arps_batch(api_arps)

        logger.info(
            "arps_transformed",
            arps_count=len(transformed_arps),
            orgaos_count=len(orgaos)
        )

        # Validate if enabled
        if validate and config.VALIDATE_DATA:
            valid_arps = []
            for arp in transformed_arps:
                is_valid, errors = validate_arp(arp)
                if is_valid:
                    valid_arps.append(arp)
                else:
                    logger.warning(
                        "arp_validation_failed_skipping",
                        arp=arp.get("numero_arp"),
                        errors=errors
                    )
                    self.stats["skipped"] += 1

            transformed_arps = valid_arps

        # Insert orgaos first (foreign key constraint)
        if orgaos:
            try:
                await bulk_upsert_orgaos(session, orgaos)
                logger.debug("orgaos_persisted", count=len(orgaos))
            except Exception as e:
                logger.error("orgaos_persist_error", error=str(e))
                raise

        # Insert ARPs in batches
        batch_size = config.BATCH_SIZE_ARPS
        inserted = 0
        updated = 0  # Note: UPSERT logic counts as updates

        for i in range(0, len(transformed_arps), batch_size):
            batch = transformed_arps[i:i + batch_size]

            try:
                count = await bulk_upsert_arps(session, batch)
                inserted += count
                logger.debug(
                    "arps_batch_persisted",
                    batch=i // batch_size + 1,
                    count=count
                )
            except Exception as e:
                logger.error(
                    "arps_batch_persist_error",
                    batch=i // batch_size + 1,
                    error=str(e)
                )
                self.stats["errors"] += len(batch)
                continue

        self.stats["inserted"] += inserted

        logger.info(
            "arps_persist_complete",
            inserted=inserted,
            skipped=self.stats["skipped"]
        )

        return inserted, 0, self.stats["skipped"]

    async def process_date_range(
        self,
        session: AsyncSession,
        date_start: date,
        date_end: date,
        max_pages: int = None
    ) -> Dict[str, int]:
        """
        Complete processing for a date range: fetch, transform, persist

        Args:
            session: Database session
            date_start: Start date
            date_end: End date
            max_pages: Maximum pages to fetch (for testing)

        Returns:
            Statistics dictionary
        """
        logger.info(
            "processing_date_range",
            date_start=str(date_start),
            date_end=str(date_end)
        )

        # Reset stats
        self.stats = {
            "fetched": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }

        # Fetch ARPs
        api_arps = await self.fetch_arps_for_date_range(
            date_start,
            date_end,
            max_pages
        )

        if not api_arps:
            logger.warning("no_arps_found_for_range")
            return self.stats

        # Process and persist
        inserted, updated, skipped = await self.process_and_persist_arps(
            session,
            api_arps
        )

        logger.info(
            "date_range_processing_complete",
            **self.stats
        )

        return self.stats

    def get_stats(self) -> Dict[str, int]:
        """Get current processing statistics"""
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            "fetched": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test ARP processor
    async def test():
        from database import get_db_session

        logger.info("Testing ARP processor...")

        async with AsyncARPAPIClient() as client:
            processor = ARPProcessor(client)

            # Test with small date range and page limit
            async with get_db_session() as session:
                stats = await processor.process_date_range(
                    session,
                    date_start=date(2024, 1, 1),
                    date_end=date(2024, 1, 31),
                    max_pages=1  # Only 1 page for testing
                )

                print("\n✅ ARP Processor Test Complete")
                print(f"   Fetched: {stats['fetched']}")
                print(f"   Inserted: {stats['inserted']}")
                print(f"   Errors: {stats['errors']}")

    asyncio.run(test())
