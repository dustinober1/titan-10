"""Integration tests for DatabasePool with real PostgreSQL container."""

import pytest
from datetime import datetime, timezone

from src.storage.connection import DatabasePool


@pytest.mark.asyncio
class TestDatabasePoolIntegration:
    """Integration tests for DatabasePool with real PostgreSQL."""

    async def test_init_and_close(self, postgres_dsn):
        """Test pool initialization and cleanup."""
        pool = DatabasePool(dsn=postgres_dsn)
        await pool.init()
        
        assert pool._pool is not None
        
        await pool.close()
        assert pool._pool is None

    async def test_insert_ohlcv_data(self, postgres_dsn, db_pool):
        """Test inserting OHLCV data."""
        pool = DatabasePool(dsn=postgres_dsn)
        await pool.init()
        
        test_data = [
            {
                "timestamp": 1704067200000,
                "open": 42000.0,
                "high": 42500.0,
                "low": 41800.0,
                "close": 42300.0,
                "volume": 1000.0
            },
            {
                "timestamp": 1704067260000,
                "open": 42300.0,
                "high": 42600.0,
                "low": 42100.0,
                "close": 42400.0,
                "volume": 800.0
            }
        ]
        
        await pool.insert_ohlcv(test_data, "BTC/USDT", "binance")
        
        # Verify data was inserted
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM ohlcv WHERE symbol = $1 ORDER BY time",
                "BTC/USDT"
            )
            assert len(rows) == 2
            assert rows[0]["close"] == 42300.0
        
        await pool.close()

    async def test_checkpoint_save_and_get(self, postgres_dsn, db_pool):
        """Test checkpoint save and retrieval."""
        pool = DatabasePool(dsn=postgres_dsn)
        await pool.init()
        
        # Save checkpoint
        await pool.save_checkpoint("ETH/USDT", 1704067200000)
        
        # Retrieve checkpoint
        checkpoint = await pool.get_last_checkpoint("ETH/USDT")
        assert checkpoint == 1704067200000
        
        await pool.close()

    async def test_checkpoint_returns_none_for_unknown_symbol(self, postgres_dsn, db_pool):
        """Test checkpoint returns None for unknown symbol."""
        pool = DatabasePool(dsn=postgres_dsn)
        await pool.init()
        
        checkpoint = await pool.get_last_checkpoint("UNKNOWN/PAIR")
        assert checkpoint is None
        
        await pool.close()

    async def test_reconnect_after_close(self, postgres_dsn):
        """Test reconnection after pool is closed."""
        pool = DatabasePool(dsn=postgres_dsn)
        await pool.init()
        await pool.close()
        
        # Should be able to reconnect
        await pool.reconnect()
        assert pool._pool is not None
        
        await pool.close()

