#!/usr/bin/env python3
"""
ETL Scheduler

Runs ETL jobs on a schedule using APScheduler.
Configured to run incremental updates daily at specified time.

Usage:
    python scheduler.py
"""

import asyncio
import signal
import sys
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import structlog

from config import config
from orchestrator import run_etl_incremental
from database import cleanup

# Configure logging
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(structlog.processors, config.LOG_LEVEL)
    )
)

logger = structlog.get_logger(__name__)


class ETLScheduler:
    """
    ETL Job Scheduler

    Manages scheduled execution of ETL jobs.
    """

    def __init__(self):
        """Initialize scheduler"""
        self.scheduler = AsyncIOScheduler(timezone=config.ETL_SCHEDULE_TIMEZONE)
        self.running = False

    async def run_incremental_job(self):
        """Job function for incremental updates"""
        logger.info("scheduled_incremental_job_started")

        try:
            stats = await run_etl_incremental()

            logger.info(
                "scheduled_incremental_job_completed",
                **stats
            )

        except Exception as e:
            logger.error(
                "scheduled_incremental_job_failed",
                error=str(e)
            )

    def start(self):
        """Start scheduler"""
        if not config.ETL_SCHEDULE_ENABLED:
            logger.warning("scheduler_disabled_in_config")
            return

        # Add incremental update job
        self.scheduler.add_job(
            self.run_incremental_job,
            trigger=CronTrigger(
                hour=config.ETL_SCHEDULE_HOUR,
                minute=config.ETL_SCHEDULE_MINUTE,
                timezone=config.ETL_SCHEDULE_TIMEZONE
            ),
            id="incremental_update",
            name="Daily Incremental Update",
            replace_existing=True,
            max_instances=1  # Prevent overlapping executions
        )

        self.scheduler.start()
        self.running = True

        logger.info(
            "scheduler_started",
            schedule_time=f"{config.ETL_SCHEDULE_HOUR:02d}:{config.ETL_SCHEDULE_MINUTE:02d}",
            timezone=config.ETL_SCHEDULE_TIMEZONE
        )

        # Print schedule info
        print("\n" + "=" * 60)
        print("ETL SCHEDULER STARTED")
        print("=" * 60)
        print(f"Schedule:   Daily at {config.ETL_SCHEDULE_HOUR:02d}:{config.ETL_SCHEDULE_MINUTE:02d} {config.ETL_SCHEDULE_TIMEZONE}")
        print(f"Job Type:   Incremental Update")
        print(f"Status:     Running")
        print("=" * 60)
        print("\nPress Ctrl+C to stop the scheduler\n")

        # Print next run time
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            print(f"Next run: {job.next_run_time}")

    def stop(self):
        """Stop scheduler"""
        if self.running:
            self.scheduler.shutdown()
            self.running = False
            logger.info("scheduler_stopped")

    async def run_forever(self):
        """Keep scheduler running"""
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("keyboard_interrupt_received")
        finally:
            self.stop()


async def main():
    """Main function"""
    scheduler = ETLScheduler()

    # Setup signal handlers
    loop = asyncio.get_event_loop()

    def signal_handler(signum, frame):
        logger.info("signal_received", signal=signum)
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start scheduler
    scheduler.start()

    # Run forever
    try:
        await scheduler.run_forever()
    finally:
        await cleanup()


if __name__ == "__main__":
    asyncio.run(main())
