#!/usr/bin/env python3
"""
Run Incremental Update CLI

Command-line interface for running incremental ARP data updates.

Usage:
    python run_incremental.py
"""

import asyncio
import argparse
import sys
import structlog

from orchestrator import run_etl_incremental
from config import config
from database import cleanup

# Configure logging
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(structlog.processors, config.LOG_LEVEL)
    )
)

logger = structlog.get_logger(__name__)


async def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Run incremental ARP data update",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (fetch but don't commit)"
    )

    args = parser.parse_args()

    # Set dry-run mode
    if args.dry_run:
        config.DRY_RUN = True

    logger.info(
        "incremental_update_cli_started",
        dry_run=config.DRY_RUN
    )

    try:
        # Run incremental update
        stats = await run_etl_incremental()

        # Print summary
        print("\n" + "=" * 60)
        print("ETL INCREMENTAL UPDATE - SUMMARY")
        print("=" * 60)
        print(f"ARPs Fetched:    {stats.get('arps_fetched', 0):,}")
        print(f"ARPs Inserted:   {stats.get('arps_inserted', 0):,}")
        print(f"ARPs Updated:    {stats.get('arps_updated', 0):,}")
        print(f"ARPs Skipped:    {stats.get('arps_skipped', 0):,}")
        print(f"Items Fetched:   {stats.get('items_fetched', 0):,}")
        print(f"Items Inserted:  {stats.get('items_inserted', 0):,}")
        print(f"Items Updated:   {stats.get('items_updated', 0):,}")
        print(f"Errors:          {stats.get('errors_count', 0):,}")
        print("=" * 60)
        print("✅ Incremental update completed successfully!")

        logger.info("incremental_update_cli_completed", **stats)

    except Exception as e:
        logger.error("incremental_update_cli_failed", error=str(e))
        print(f"\n❌ Incremental update failed: {e}")
        sys.exit(1)

    finally:
        await cleanup()


if __name__ == "__main__":
    asyncio.run(main())
