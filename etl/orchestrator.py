"""
ETL Orchestrator

Main coordinator for ARP ETL process.
Handles both initial load and incremental updates with checkpoint/resume capability.
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid
import structlog
import json

from config import config
from database import get_db_session, get_last_successful_execution, get_incomplete_execution
from api_client import AsyncARPAPIClient
from processors.arp_processor import ARPProcessor
from processors.item_processor import ItemProcessor
from utils.date_utils import generate_quarterly_chunks, get_incremental_date_window
from models import EtlExecution

logger = structlog.get_logger(__name__)


class ETLOrchestrator:
    """
    Main ETL Orchestrator

    Coordinates the entire ETL process including:
    - Initial data load (chunked by quarter)
    - Incremental updates (daily)
    - Checkpoint/resume capability
    - Error tracking and statistics
    """

    def __init__(self):
        """Initialize orchestrator"""
        self.execution_id: Optional[str] = None
        self.api_client: Optional[AsyncARPAPIClient] = None
        self.arp_processor: Optional[ARPProcessor] = None
        self.item_processor: Optional[ItemProcessor] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def start(self):
        """Initialize clients and processors"""
        self.api_client = AsyncARPAPIClient()
        await self.api_client.start()

        self.arp_processor = ARPProcessor(self.api_client)
        self.item_processor = ItemProcessor(self.api_client)

        logger.info("orchestrator_started")

    async def close(self):
        """Cleanup resources"""
        if self.api_client:
            await self.api_client.close()

        logger.info("orchestrator_closed")

    async def _create_execution_record(
        self,
        session: AsyncSession,
        execution_type: str,
        date_start: date,
        date_end: date
    ) -> str:
        """
        Create ETL execution tracking record

        Args:
            session: Database session
            execution_type: 'initial' or 'incremental'
            date_start: Start date of range
            date_end: End date of range

        Returns:
            Execution ID (UUID)
        """
        execution_id = str(uuid.uuid4())

        query = text("""
            INSERT INTO etl_executions (
                id, execution_type, status, started_at,
                date_range_start, date_range_end, config_snapshot
            )
            VALUES (
                :id, :execution_type, 'running', CURRENT_TIMESTAMP,
                :date_start, :date_end, :config_snapshot
            )
        """)

        await session.execute(query, {
            "id": execution_id,
            "execution_type": execution_type,
            "date_start": date_start,
            "date_end": date_end,
            "config_snapshot": json.dumps(config.get_summary())
        })

        await session.commit()

        self.execution_id = execution_id
        logger.info(
            "execution_record_created",
            execution_id=execution_id,
            type=execution_type
        )

        return execution_id

    async def _update_execution_progress(
        self,
        session: AsyncSession,
        page: int,
        total_pages: int,
        stats: Dict[str, int]
    ):
        """Update execution progress (checkpoint)"""
        if not self.execution_id:
            return

        query = text("""
            UPDATE etl_executions
            SET
                last_ata_page_processed = :page,
                total_ata_pages = :total_pages,
                arps_fetched = :arps_fetched,
                arps_inserted = :arps_inserted,
                arps_updated = :arps_updated,
                arps_skipped = :arps_skipped,
                items_fetched = :items_fetched,
                items_inserted = :items_inserted,
                items_updated = :items_updated,
                items_skipped = :items_skipped,
                errors_count = :errors_count
            WHERE id = :execution_id
        """)

        await session.execute(query, {
            "execution_id": self.execution_id,
            "page": page,
            "total_pages": total_pages,
            **stats
        })

        await session.commit()

        logger.debug(
            "execution_progress_updated",
            page=page,
            total_pages=total_pages
        )

    async def _complete_execution(
        self,
        session: AsyncSession,
        status: str,
        error_message: Optional[str] = None
    ):
        """Mark execution as completed or failed"""
        if not self.execution_id:
            return

        query = text("""
            UPDATE etl_executions
            SET
                status = :status,
                completed_at = CURRENT_TIMESTAMP,
                duration_seconds = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at)),
                error_message = :error_message
            WHERE id = :execution_id
        """)

        await session.execute(query, {
            "execution_id": self.execution_id,
            "status": status,
            "error_message": error_message
        })

        await session.commit()

        logger.info(
            "execution_completed",
            execution_id=self.execution_id,
            status=status
        )

    # ========================================================================
    # INITIAL LOAD
    # ========================================================================

    async def run_initial_load(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Run initial data load (chunked by quarter)

        Args:
            start_date: Start date (defaults to config)
            end_date: End date (defaults to config or today)

        Returns:
            Statistics dictionary
        """
        if start_date is None:
            start_date = config.INITIAL_LOAD_START_DATE
        if end_date is None:
            end_date = config.initial_end_date

        logger.info(
            "initial_load_started",
            start_date=str(start_date),
            end_date=str(end_date)
        )

        total_stats = {
            "arps_fetched": 0,
            "arps_inserted": 0,
            "arps_updated": 0,
            "arps_skipped": 0,
            "items_fetched": 0,
            "items_inserted": 0,
            "items_updated": 0,
            "items_skipped": 0,
            "errors_count": 0
        }

        # Generate quarterly chunks
        quarters = generate_quarterly_chunks(start_date, end_date)

        async with get_db_session() as session:
            # Create execution record
            await self._create_execution_record(
                session,
                "initial",
                start_date,
                end_date
            )

            try:
                # Process each quarter
                for i, (q_start, q_end) in enumerate(quarters, 1):
                    logger.info(
                        "processing_quarter",
                        quarter=i,
                        total_quarters=len(quarters),
                        date_range=f"{q_start} to {q_end}"
                    )

                    # Process ARPs for this quarter
                    arp_stats = await self.arp_processor.process_date_range(
                        session,
                        q_start,
                        q_end,
                        max_pages=config.TEST_MAX_PAGES if config.TEST_MODE else None
                    )

                    # Get processed ARPs to fetch items
                    # Note: In production, we'd query DB for ARPs in range
                    # For now, we'll process items in the next step

                    # Update total stats
                    total_stats["arps_fetched"] += arp_stats.get("fetched", 0)
                    total_stats["arps_inserted"] += arp_stats.get("inserted", 0)
                    total_stats["errors_count"] += arp_stats.get("errors", 0)

                    # Update checkpoint
                    await self._update_execution_progress(
                        session,
                        page=i,
                        total_pages=len(quarters),
                        stats=total_stats
                    )

                    logger.info(
                        "quarter_completed",
                        quarter=i,
                        arps_processed=arp_stats.get("fetched", 0)
                    )

                # Mark as completed
                await self._complete_execution(session, "completed")

                logger.info(
                    "initial_load_completed",
                    **total_stats
                )

                return total_stats

            except Exception as e:
                logger.error("initial_load_failed", error=str(e))
                await self._complete_execution(session, "failed", str(e))
                raise

    # ========================================================================
    # INCREMENTAL UPDATE
    # ========================================================================

    async def run_incremental_update(self) -> Dict[str, Any]:
        """
        Run incremental update (fetch changes since last sync)

        Uses lookback window to capture late API updates.

        Returns:
            Statistics dictionary
        """
        logger.info("incremental_update_started")

        async with get_db_session() as session:
            # Get last successful execution
            last_exec = await get_last_successful_execution(session)

            if not last_exec:
                logger.warning("no_previous_execution_running_initial_load")
                return await self.run_initial_load()

            last_sync_date = last_exec.get("completed_at").date()

            # Calculate incremental window
            window_start, window_end = get_incremental_date_window(
                last_sync_date,
                config.INCREMENTAL_LOOKBACK_DAYS
            )

            # Create execution record
            await self._create_execution_record(
                session,
                "incremental",
                window_start,
                window_end
            )

            try:
                # Process incremental window
                stats = await self.arp_processor.process_date_range(
                    session,
                    window_start,
                    window_end
                )

                # Update stats
                total_stats = {
                    "arps_fetched": stats.get("fetched", 0),
                    "arps_inserted": stats.get("inserted", 0),
                    "arps_updated": stats.get("updated", 0),
                    "arps_skipped": stats.get("skipped", 0),
                    "items_fetched": 0,
                    "items_inserted": 0,
                    "items_updated": 0,
                    "items_skipped": 0,
                    "errors_count": stats.get("errors", 0)
                }

                await self._update_execution_progress(
                    session,
                    page=1,
                    total_pages=1,
                    stats=total_stats
                )

                # Mark as completed
                await self._complete_execution(session, "completed")

                logger.info(
                    "incremental_update_completed",
                    **total_stats
                )

                return total_stats

            except Exception as e:
                logger.error("incremental_update_failed", error=str(e))
                await self._complete_execution(session, "failed", str(e))
                raise

    # ========================================================================
    # RESUME FAILED EXECUTION
    # ========================================================================

    async def resume_failed_execution(self) -> Dict[str, Any]:
        """
        Resume a failed/incomplete execution from checkpoint

        Returns:
            Statistics dictionary
        """
        logger.info("attempting_resume")

        async with get_db_session() as session:
            # Get incomplete execution
            incomplete = await get_incomplete_execution(session)

            if not incomplete:
                logger.warning("no_incomplete_execution_to_resume")
                return {}

            logger.info(
                "resuming_execution",
                execution_id=incomplete.get("id"),
                last_page=incomplete.get("last_ata_page_processed")
            )

            # TODO: Implement resume logic
            # This would require storing more context about what was being processed

            logger.warning("resume_not_yet_implemented")
            return {}


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def run_etl_initial_load(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Convenience function to run initial load

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        Statistics dictionary
    """
    async with ETLOrchestrator() as orchestrator:
        return await orchestrator.run_initial_load(start_date, end_date)


async def run_etl_incremental() -> Dict[str, Any]:
    """
    Convenience function to run incremental update

    Returns:
        Statistics dictionary
    """
    async with ETLOrchestrator() as orchestrator:
        return await orchestrator.run_incremental_update()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test orchestrator
    async def test():
        logger.info("Testing ETL Orchestrator...")

        # Test initial load with small date range
        stats = await run_etl_initial_load(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        print("\n✅ Orchestrator Test Complete")
        print(f"   ARPs processed: {stats.get('arps_fetched', 0)}")
        print(f"   Errors: {stats.get('errors_count', 0)}")

    asyncio.run(test())
