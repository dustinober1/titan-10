"""APScheduler integration for periodic data fetching."""

import logging
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.shared.config import get_settings
from src.ingestor.fetcher import fetch_realtime_ohlcv
from src.storage.connection import DatabasePool

logger = logging.getLogger(__name__)


class IngestionScheduler:
    """
    Scheduler for periodic OHLCV data fetching.

    Implements Pattern 3 from research: APScheduler AsyncIOScheduler
    Triggers fetch_realtime_data every 60 seconds for real-time ingestion.
    """

    def __init__(self, storage: DatabasePool) -> None:
        """
        Initialize ingestion scheduler.

        Args:
            storage: DatabasePool instance for data persistence
        """
        self.storage = storage
        self.scheduler = AsyncIOScheduler()
        self.settings = get_settings()

        logger.info("Initialized IngestionScheduler with AsyncIOScheduler")

    async def fetch_realtime_data(self) -> None:
        """
        Fetch real-time OHLCV data for configured symbols and exchanges.

        Called by scheduler every 60 seconds.
        Loads symbols from settings and fetches from configured exchanges.
        """
        try:
            # Get symbols from settings
            symbols: List[str] = self.settings.top_symbols

            # For Phase 1, fetch from Binance only
            # Phase 2 will add multi-exchange redundancy
            exchanges = ["binance"]

            logger.info(
                f"Fetching real-time data: {len(symbols)} symbols from {exchanges}"
            )

            # Fetch and persist data
            result = await fetch_realtime_ohlcv(
                symbols=symbols,
                exchanges=exchanges,
                storage=self.storage,
            )

            logger.info(
                f"Real-time fetch complete: {result['success']}/{result['total']} successful"
            )

        except Exception as e:
            logger.error(f"Error in fetch_realtime_data: {e}")
            # Don't raise - scheduler should continue running

    def start(self) -> None:
        """
        Start the scheduler with periodic jobs.

        Adds job for real-time fetching every 60 seconds.
        Starts the AsyncIOScheduler.
        """
        # Add real-time ingestion job: runs every 60 seconds
        self.scheduler.add_job(
            self.fetch_realtime_data,
            "interval",
            seconds=60,
            id="realtime_ingestion",
            name="Real-time OHLCV ingestion",
            replace_existing=True,
        )

        # Start the scheduler
        self.scheduler.start()

        logger.info("Scheduler started: realtime_ingestion job every 60 seconds")

    def stop(self) -> None:
        """
        Stop the scheduler and shutdown all jobs.

        Waits=False for immediate shutdown without waiting for running jobs to complete.
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")


def start_scheduler(storage: DatabasePool) -> IngestionScheduler:
    """
    Convenience function to create and start ingestion scheduler.

    Args:
        storage: DatabasePool instance for data persistence

    Returns:
        Started IngestionScheduler instance
    """
    scheduler = IngestionScheduler(storage)
    scheduler.start()
    return scheduler
