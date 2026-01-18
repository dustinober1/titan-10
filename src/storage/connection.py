"""Asyncpg connection pool with auto-reconnect for TimescaleDB."""

import asyncio
import logging
from typing import List, Dict, Any, Optional

import asyncpg

from src.shared.types import OHLCV

logger = logging.getLogger(__name__)


class DatabasePool:
    """
    Asyncpg connection pool with automatic reconnection and retry logic.

    Implements AUTO-02 requirement: Auto-recover from database connection loss.
    Provides exponential backoff retry for reconnection attempts.
    """

    def __init__(self, dsn: str, min_size: int = 5, max_size: int = 20) -> None:
        """
        Initialize database pool configuration.

        Args:
            dsn: Database connection string (e.g., postgresql://user:pass@host:port/db)
            min_size: Minimum number of connections in the pool
            max_size: Maximum number of connections in the pool
        """
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self._pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()
        self._is_reconnecting = False

    async def init(
        self,
        max_queries: int = 50000,
        max_inactive_connection_lifetime: float = 300.0,
        command_timeout: float = 60.0,
    ) -> None:
        """
        Initialize the connection pool.

        Args:
            max_queries: Maximum queries per connection before recycling
            max_inactive_connection_lifetime: Maximum inactive lifetime in seconds
            command_timeout: Default command timeout in seconds
        """
        logger.info(f"Initializing database pool: {self.min_size}-{self.max_size} connections")

        self._pool = await asyncpg.create_pool(
            self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            max_queries=max_queries,
            max_inactive_connection_lifetime=max_inactive_connection_lifetime,
            command_timeout=command_timeout,
        )

        logger.info("Database pool initialized successfully")

    async def _ensure_connection(self) -> None:
        """
        Ensure the pool is healthy, reinitialize if needed.

        This method checks if the pool is healthy and reinitializes it if not.
        Called at the start of each query method to handle connection loss.
        """
        if self._pool is None:
            logger.warning("Pool is None, attempting reconnection...")
            await self.reconnect()
            return

        # Try to acquire a connection to verify pool health
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
        except (asyncpg.PostgresConnectionError, asyncpg.PoolConnectionLimitError) as e:
            logger.warning(f"Pool health check failed: {e}. Attempting reconnection...")
            await self.reconnect()

    async def reconnect(self, max_attempts: int = 5, base_delay: float = 1.0) -> None:
        """
        Reconnect to the database with exponential backoff retry.

        Implements AUTO-02 requirement: Auto-recover from database connection loss.

        Args:
            max_attempts: Maximum number of reconnection attempts
            base_delay: Base delay for exponential backoff (in seconds)

        Raises:
            RuntimeError: If reconnection fails after all attempts
        """
        async with self._lock:
            if self._is_reconnecting:
                logger.debug("Reconnection already in progress, waiting...")
                # Wait for existing reconnection to complete
                while self._is_reconnecting:
                    await asyncio.sleep(0.1)
                return

            self._is_reconnecting = True

        try:
            # Close existing pool if it exists
            if self._pool is not None:
                try:
                    await self._pool.close()
                    logger.info("Closed existing pool for reconnection")
                except Exception as e:
                    logger.warning(f"Error closing pool during reconnection: {e}")

            # Attempt reconnection with exponential backoff
            for attempt in range(1, max_attempts + 1):
                try:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.info(f"Reconnection attempt {attempt}/{max_attempts} after {delay}s delay")

                    await asyncio.sleep(delay)

                    await self.init()
                    logger.info("Reconnection successful")
                    return

                except (asyncpg.PostgresConnectionError, OSError) as e:
                    logger.warning(f"Reconnection attempt {attempt} failed: {e}")

                    if attempt == max_attempts:
                        raise RuntimeError(
                            f"Failed to reconnect to database after {max_attempts} attempts"
                        ) from e

        finally:
            async with self._lock:
                self._is_reconnecting = False

    async def insert_ohlcv(
        self, data: List[Dict[str, Any]], symbol: str, exchange: str
    ) -> None:
        """
        Insert OHLCV data with automatic duplicate handling.

        Args:
            data: List of OHLCV data points
            symbol: Trading symbol (e.g., BTC/USDT)
            exchange: Exchange name (e.g., binance)
        """
        await self._ensure_connection()

        if not data:
            return

        async with self._pool.acquire() as conn:
            # Use executemany for efficient batch inserts
            # ON CONFLICT DO NOTHING prevents duplicates (same time, symbol, exchange)
            await conn.executemany(
                """
                INSERT INTO ohlcv (time, symbol, exchange, open, high, low, close, volume)
                VALUES (
                    to_timestamp($1 / 1000.0),
                    $2,
                    $3,
                    $4,
                    $5,
                    $6,
                    $7,
                    $8
                )
                ON CONFLICT (time, symbol, exchange) DO NOTHING
                """,
                [
                    (
                        point["timestamp"],
                        symbol,
                        exchange,
                        point["open"],
                        point["high"],
                        point["low"],
                        point["close"],
                        point["volume"],
                    )
                    for point in data
                ],
            )

            logger.debug(f"Inserted {len(data)} OHLCV records for {symbol}@{exchange}")

    async def save_checkpoint(self, symbol: str, last_timestamp: int) -> None:
        """
        Save backfill checkpoint for resume capability.

        Args:
            symbol: Trading symbol
            last_timestamp: Last successfully processed timestamp (milliseconds)
        """
        await self._ensure_connection()

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO backfill_checkpoints (symbol, last_timestamp, updated_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (symbol)
                DO UPDATE SET
                    last_timestamp = EXCLUDED.last_timestamp,
                    updated_at = NOW()
                """,
                symbol,
                last_timestamp,
            )

            logger.debug(f"Saved checkpoint for {symbol}: {last_timestamp}")

    async def get_last_checkpoint(self, symbol: str) -> Optional[int]:
        """
        Get last checkpoint timestamp for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Last timestamp in milliseconds, or None if no checkpoint exists
        """
        await self._ensure_connection()

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT last_timestamp
                FROM backfill_checkpoints
                WHERE symbol = $1
                """,
                symbol,
            )

            return row["last_timestamp"] if row else None

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")
