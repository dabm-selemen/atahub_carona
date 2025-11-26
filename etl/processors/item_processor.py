"""
Item Processor

Handles fetching, transforming, and persisting ARP items data.
"""

import asyncio
from typing import List, Dict, Any, Tuple
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from api_client import AsyncARPAPIClient
from database import bulk_upsert_items
from .transformers import transform_items_batch, validate_item
from utils.date_utils import parse_api_date
from config import config

logger = structlog.get_logger(__name__)


class ItemProcessor:
    """
    Processor for ARP items

    Coordinates fetching items from API and persisting to database.
    """

    def __init__(self, api_client: AsyncARPAPIClient):
        """
        Initialize item processor

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

    async def fetch_items_for_arp(
        self,
        arp: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Fetch all items for a single ARP

        Args:
            arp: ARP dictionary (transformed format with numero_compra, uasg_id, etc.)

        Returns:
            List of item dictionaries from API
        """
        numero_compra = arp.get("numero_compra")
        uasg = arp.get("uasg_id")
        data_vigencia = arp.get("data_inicio_vigencia")

        if not numero_compra or not uasg or not data_vigencia:
            logger.error(
                "missing_arp_fields_for_items",
                arp_id=arp.get("id"),
                numero_arp=arp.get("numero_arp")
            )
            return []

        try:
            # Convert date if needed
            if isinstance(data_vigencia, str):
                data_vigencia = parse_api_date(data_vigencia)

            items = await self.api_client.fetch_all_arp_items(
                numero_compra=numero_compra,
                codigo_unidade_gerenciadora=uasg,
                data_vigencia_inicial=data_vigencia
            )

            self.stats["fetched"] += len(items)

            logger.debug(
                "items_fetched_for_arp",
                numero_compra=numero_compra,
                items_count=len(items)
            )

            return items

        except Exception as e:
            logger.error(
                "fetch_items_error",
                numero_compra=numero_compra,
                error=str(e)
            )
            self.stats["errors"] += 1
            return []

    async def fetch_items_for_arps_concurrent(
        self,
        arps: List[Dict[str, Any]],
        max_concurrent: int = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch items for multiple ARPs concurrently

        Args:
            arps: List of ARP dictionaries
            max_concurrent: Maximum concurrent requests (defaults to config)

        Returns:
            Dictionary mapping arp_id to list of items
        """
        if max_concurrent is None:
            max_concurrent = config.MAX_CONCURRENT_ITEM_REQUESTS

        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_limit(arp: Dict[str, Any]):
            async with semaphore:
                items = await self.fetch_items_for_arp(arp)
                return arp.get("id"), items

        tasks = [fetch_with_limit(arp) for arp in arps]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        items_by_arp = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error("concurrent_fetch_exception", error=str(result))
                continue

            arp_id, items = result
            items_by_arp[arp_id] = items

        logger.info(
            "concurrent_items_fetch_complete",
            arps_count=len(arps),
            arps_with_items=len(items_by_arp)
        )

        return items_by_arp

    async def process_and_persist_items(
        self,
        session: AsyncSession,
        arp_id: str,
        api_items: List[Dict[str, Any]],
        validate: bool = True
    ) -> Tuple[int, int, int]:
        """
        Transform and persist items to database

        Args:
            session: Database session
            arp_id: UUID of parent ARP
            api_items: List of items from API
            validate: Whether to validate data

        Returns:
            Tuple of (inserted_count, updated_count, skipped_count)
        """
        if not api_items:
            return 0, 0, 0

        # Transform items
        transformed_items = transform_items_batch(api_items, arp_id)

        logger.debug(
            "items_transformed",
            arp_id=arp_id,
            items_count=len(transformed_items)
        )

        # Validate if enabled
        if validate and config.VALIDATE_DATA:
            valid_items = []
            for item in transformed_items:
                is_valid, errors = validate_item(item)
                if is_valid:
                    valid_items.append(item)
                else:
                    logger.warning(
                        "item_validation_failed_skipping",
                        item=item.get("numero_item"),
                        errors=errors
                    )
                    self.stats["skipped"] += 1

            transformed_items = valid_items

        # Insert items in batches
        batch_size = config.BATCH_SIZE_ITEMS
        inserted = 0

        for i in range(0, len(transformed_items), batch_size):
            batch = transformed_items[i:i + batch_size]

            try:
                count = await bulk_upsert_items(session, batch)
                inserted += count
                logger.debug(
                    "items_batch_persisted",
                    arp_id=arp_id,
                    batch=i // batch_size + 1,
                    count=count
                )
            except Exception as e:
                logger.error(
                    "items_batch_persist_error",
                    arp_id=arp_id,
                    batch=i // batch_size + 1,
                    error=str(e)
                )
                self.stats["errors"] += len(batch)
                continue

        self.stats["inserted"] += inserted

        return inserted, 0, self.stats["skipped"]

    async def process_items_for_arps(
        self,
        session: AsyncSession,
        arps: List[Dict[str, Any]],
        concurrent: bool = True
    ) -> Dict[str, int]:
        """
        Complete processing for multiple ARPs: fetch items, transform, persist

        Args:
            session: Database session
            arps: List of ARP dictionaries
            concurrent: Whether to fetch items concurrently

        Returns:
            Statistics dictionary
        """
        logger.info(
            "processing_items_for_arps",
            arps_count=len(arps),
            concurrent=concurrent
        )

        # Reset stats
        self.stats = {
            "fetched": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }

        if concurrent:
            # Fetch all items concurrently
            items_by_arp = await self.fetch_items_for_arps_concurrent(arps)

            # Process each ARP's items
            for arp_id, api_items in items_by_arp.items():
                if api_items:
                    await self.process_and_persist_items(
                        session,
                        arp_id,
                        api_items
                    )
        else:
            # Sequential processing (fallback)
            for arp in arps:
                api_items = await self.fetch_items_for_arp(arp)
                if api_items:
                    await self.process_and_persist_items(
                        session,
                        arp.get("id"),
                        api_items
                    )

        logger.info(
            "items_processing_complete",
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
    # Test item processor
    async def test():
        from database import get_db_session

        logger.info("Testing Item processor...")

        # Sample ARP data for testing
        sample_arp = {
            "id": "test-uuid",
            "numero_compra": "00057",
            "uasg_id": "155008",
            "data_inicio_vigencia": date(2023, 7, 26),
            "numero_arp": "00421/2023"
        }

        async with AsyncARPAPIClient() as client:
            processor = ItemProcessor(client)

            # Fetch items for sample ARP
            items = await processor.fetch_items_for_arp(sample_arp)

            print("\n✅ Item Processor Test Complete")
            print(f"   Items fetched: {len(items)}")
            print(f"   Stats: {processor.get_stats()}")

    asyncio.run(test())
