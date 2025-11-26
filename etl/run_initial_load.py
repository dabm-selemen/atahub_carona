#!/usr/bin/env python3
"""
Run Initial Load CLI

Command-line interface for running initial ARP data load.

Usage:
    python run_initial_load.py
    python run_initial_load.py --start 2023-01-01 --end 2024-12-31
    python run_initial_load.py --test
"""

import asyncio
import argparse
from datetime import date
import sys
import structlog
import logging

from orchestrator import run_etl_initial_load
from config import config
from database import cleanup

# Configure logging
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, config.LOG_LEVEL)
    )
)

logger = structlog.get_logger(__name__)


async def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Run initial ARP data load",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--start",
        type=str,
        default=str(config.INITIAL_LOAD_START_DATE),
        help="Start date (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="End date (YYYY-MM-DD, defaults to today)"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (limited pages)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (fetch but don't commit)"
    )

    args = parser.parse_args()

    # Parse dates
    try:
        start_date = date.fromisoformat(args.start)
        end_date = date.fromisoformat(args.end) if args.end else config.initial_end_date
    except ValueError as e:
        logger.error("invalid_date_format", error=str(e))
        sys.exit(1)

    # Set test/dry-run modes
    if args.test:
        config.TEST_MODE = True
    if args.dry_run:
        config.DRY_RUN = True

    logger.info(
        "initial_load_cli_started",
        start_date=str(start_date),
        end_date=str(end_date),
        test_mode=config.TEST_MODE,
        dry_run=config.DRY_RUN
    )

    try:
        # Run initial load
        stats = await run_etl_initial_load(start_date, end_date)

        # Print summary
        print("\n" + "=" * 60)
        print("ETL INITIAL LOAD - SUMMARY")
        print("=" * 60)
        print(f"Date Range:      {start_date} to {end_date}")
        print(f"ARPs Fetched:    {stats.get('arps_fetched', 0):,}")
        print(f"ARPs Inserted:   {stats.get('arps_inserted', 0):,}")
        print(f"ARPs Skipped:    {stats.get('arps_skipped', 0):,}")
        print(f"Items Fetched:   {stats.get('items_fetched', 0):,}")
        print(f"Items Inserted:  {stats.get('items_inserted', 0):,}")
        print(f"Errors:          {stats.get('errors_count', 0):,}")
        print("=" * 60)
        print("[OK] Initial load completed successfully!")

        logger.info("initial_load_cli_completed", **stats)

    except Exception as e:
        logger.error("initial_load_cli_failed", error=str(e))
        print(f"\n[ERROR] Initial load failed: {e}")
        sys.exit(1)

    finally:
        await cleanup()


if __name__ == "__main__":
    asyncio.run(main())
