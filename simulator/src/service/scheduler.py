"""Scheduler for continuous data generation.

This module provides scheduling functionality with drift correction
to ensure data is generated at precise 15-minute intervals.
"""

import logging
from datetime import datetime, timedelta
from typing import Callable, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import time

logger = logging.getLogger(__name__)


class DataGenerationScheduler:
    """Manages scheduled data generation with drift correction."""

    def __init__(self, interval_minutes: int = 15, max_retries: int = 3,
                 retry_delay_seconds: int = 60):
        """Initialize scheduler.

        Args:
            interval_minutes: Interval between data generations (default 15)
            max_retries: Maximum number of retries on failure
            retry_delay_seconds: Delay between retries in seconds
        """
        self.interval_minutes = interval_minutes
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds

        self.scheduler: Optional[BackgroundScheduler] = None
        self.job_callback: Optional[Callable] = None
        self.retry_count = 0

    def start(self, job_callback: Callable[[], bool]):
        """Start the scheduler with the provided job callback.

        Args:
            job_callback: Function to call on each interval (should return True on success)
        """
        self.job_callback = job_callback
        self.scheduler = BackgroundScheduler()

        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

        # Schedule job to run at :00, :15, :30, :45 of every hour
        # This ensures alignment to standard intervals
        if self.interval_minutes == 15:
            trigger = CronTrigger(minute='0,15,30,45')
        elif self.interval_minutes == 30:
            trigger = CronTrigger(minute='0,30')
        elif self.interval_minutes == 60:
            trigger = CronTrigger(minute='0')
        else:
            # Fallback for custom intervals
            trigger = CronTrigger(minute=f'*/{self.interval_minutes}')

        self.scheduler.add_job(
            self._execute_with_retry,
            trigger=trigger,
            id='data_generation_job',
            name='Data Generation Job',
            max_instances=1,  # Prevent overlapping executions
            coalesce=True,    # Combine missed executions
            misfire_grace_time=60  # Allow 60 second grace period for missed jobs
        )

        self.scheduler.start()
        logger.info(f"Scheduler started with {self.interval_minutes}-minute intervals")

        # Immediately execute on startup to catch up if needed
        logger.info("Executing initial data generation...")
        self._execute_with_retry()

    def _execute_with_retry(self):
        """Execute job with retry logic."""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Executing data generation job (attempt {attempt + 1}/{self.max_retries})")

                success = self.job_callback()

                if success:
                    self.retry_count = 0  # Reset on success
                    logger.info("Data generation job completed successfully")
                    return
                else:
                    logger.warning(f"Data generation job failed (attempt {attempt + 1})")

            except Exception as e:
                logger.error(f"Error in data generation job (attempt {attempt + 1}): {e}", exc_info=True)

            # Wait before retry (except on last attempt)
            if attempt < self.max_retries - 1:
                logger.info(f"Retrying in {self.retry_delay_seconds} seconds...")
                time.sleep(self.retry_delay_seconds)

        # All retries exhausted
        self.retry_count += 1
        logger.error(f"Data generation job failed after {self.max_retries} attempts")

    def _job_executed_listener(self, event):
        """Listen to job execution events for monitoring.

        Args:
            event: APScheduler event object
        """
        if event.exception:
            logger.error(f"Job {event.job_id} raised exception: {event.exception}")
        else:
            logger.debug(f"Job {event.job_id} executed successfully")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")

    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time.

        Returns:
            Next run time or None if scheduler not running
        """
        if self.scheduler and self.scheduler.running:
            job = self.scheduler.get_job('data_generation_job')
            if job:
                return job.next_run_time
        return None

    def is_running(self) -> bool:
        """Check if scheduler is running.

        Returns:
            True if running, False otherwise
        """
        return self.scheduler is not None and self.scheduler.running

    def get_status(self) -> dict:
        """Get scheduler status information.

        Returns:
            Dictionary with scheduler status
        """
        status = {
            'running': self.is_running(),
            'interval_minutes': self.interval_minutes,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }

        next_run = self.get_next_run_time()
        if next_run:
            status['next_run_time'] = next_run.isoformat()

        return status
