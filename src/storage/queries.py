"""SQL query helpers for gap detection and data retrieval."""

import logging
from typing import List, Optional
from datetime import datetime

from src.storage.connection import DatabasePool

logger = logging.getLogger(__name__)


async def detect_gaps(
    pool: DatabasePool,
    symbol: str,
    timeframe: str = "1d",
) -> List[datetime]:
    """
    Detect missing candles in historical data using TimescaleDB.

    Uses generate_series to create expected time series and LEFT JOIN to find gaps.
    Implements DATA-06 requirement: detect and report data gaps in historical archive.

    Args:
        pool: Database connection pool
        symbol: Trading symbol to check for gaps
        timeframe: Candle timeframe (default: '1d' for daily candles)

    Returns:
        List of timestamps where candles are missing
    """
    await pool._ensure_connection()

    async with pool._pool.acquire() as conn:
        # For daily timeframe, use 1 day interval
        if timeframe == "1d":
            query = """
                WITH expected_times AS (
                    SELECT generate_series(
                        (SELECT MIN(time) FROM ohlcv WHERE symbol = $1),
                        (SELECT MAX(time) FROM ohlcv WHERE symbol = $1),
                        INTERVAL '1 day'
                    ) AS time
                ),
                actual_times AS (
                    SELECT DISTINCT time FROM ohlcv WHERE symbol = $1
                )
                SELECT expected_times.time
                FROM expected_times
                LEFT JOIN actual_times ON expected_times.time = actual_times.time
                WHERE actual_times.time IS NULL
                ORDER BY expected_times.time;
            """

            gaps = await conn.fetch(query, symbol)

            if gaps:
                logger.warning(f"Found {len(gaps)} missing candles for {symbol}")
                for gap in gaps:
                    logger.debug(f"Missing candle for {symbol} at {gap['time']}")
            else:
                logger.info(f"No gaps detected for {symbol}")

            return [gap["time"] for gap in gaps]

        else:
            logger.warning(f"Gap detection not implemented for timeframe: {timeframe}")
            return []


async def get_latest_timestamp(
    pool: DatabasePool,
    symbol: str,
) -> Optional[datetime]:
    """
    Get the newest data point timestamp for a symbol.

    Args:
        pool: Database connection pool
        symbol: Trading symbol to query

    Returns:
        Latest timestamp or None if no data exists
    """
    await pool._ensure_connection()

    async with pool._pool.acquire() as conn:
        query = """
            SELECT MAX(time) as latest_time
            FROM ohlcv
            WHERE symbol = $1;
        """

        row = await conn.fetchrow(query, symbol)

        if row and row["latest_time"]:
            logger.debug(f"Latest timestamp for {symbol}: {row['latest_time']}")
            return row["latest_time"]
        else:
            logger.warning(f"No data found for {symbol}")
            return None
