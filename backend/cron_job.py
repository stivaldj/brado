"""Cron job module for periodic database synchronization.

Provides a `schedule_sync` function that configures a background APScheduler
instance to call `Database.sync_with_external` at a regular interval.

The implementation is deliberately lightweight – it only sets up the
scheduler, registers the job, and starts the scheduler. The actual
synchronisation logic will be added later.
"""

import logging
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler

# Import the Database class from the project's backend module.
# The import is placed inside the function to avoid circular imports when
# the module is imported early in the application lifecycle.


def schedule_sync(db: "Database", interval_minutes: int = 60) -> None:
    """Configure and start a background scheduler to sync the database.

    Args:
        db: An instance of :class:`backend.database.Database`.
        interval_minutes: How often, in minutes, to run the sync job.

    The function creates a :class:`BackgroundScheduler`, registers a job that
    calls ``db.sync_with_external()`` every ``interval_minutes`` minutes, and
    starts the scheduler. Errors raised by the sync method are caught and
    logged so that the scheduler continues running.
    """
    # Configure a simple logger for this module.
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    scheduler = BackgroundScheduler()

    def _run_sync() -> None:
        try:
            logger.info("Starting database sync")
            db.sync_with_external()
            logger.info("Database sync completed")
        except Exception as exc:
            logger.exception("Database sync failed: %s", exc)

    # Register the periodic job. ``replace_existing`` ensures that re‑calling
    # ``schedule_sync`` does not create duplicate jobs.
    scheduler.add_job(
        _run_sync,
        trigger="interval",
        minutes=interval_minutes,
        id="db_sync_job",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Background scheduler started – sync will run every %d minute(s)",
        interval_minutes,
    )
