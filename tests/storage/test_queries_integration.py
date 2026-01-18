"""Integration tests for SQL query helpers."""

import pytest
from datetime import datetime, timezone, timedelta

from src.storage.connection import DatabasePool
from src.storage.queries import detect_gaps, get_latest_timestamp


@pytest.mark.asyncio
class TestQueriesIntegration:
    """Integration tests for query helpers with real PostgreSQL."""

    async def test_get_latest_timestamp(self, postgres_dsn, db_pool):
        """Test getting latest timestamp for a symbol."""
        pool = DatabasePool(dsn=postgres_dsn)
        await pool.init()
        
        # Insert test data
        test_data = [
            {"timestamp": 1704067200000, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": 1704153600000, "open": 100, "high": 102, "low": 98, "close": 101, "volume": 15},
        ]
        await pool.insert_ohlcv(test_data, "BTC/USDT", "binance")
        
        # Get latest timestamp
        latest = await get_latest_timestamp(pool, "BTC/USDT")
        
        assert latest is not None
        await pool.close()

    async def test_get_latest_timestamp_no_data(self, postgres_dsn, db_pool):
        """Test getting latest timestamp when no data exists."""
        pool = DatabasePool(dsn=postgres_dsn)
        await pool.init()
        
        latest = await get_latest_timestamp(pool, "NONEXISTENT/PAIR")
        
        assert latest is None
        await pool.close()

    async def test_detect_gaps_no_gaps(self, postgres_dsn, db_pool):
        """Test gap detection when there are no gaps."""
        pool = DatabasePool(dsn=postgres_dsn)
        await pool.init()
        
        # Insert consecutive daily data
        base_ts = 1704067200000  # 2024-01-01
        test_data = [
            {"timestamp": base_ts, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": base_ts + 86400000, "open": 100, "high": 102, "low": 98, "close": 101, "volume": 15},
            {"timestamp": base_ts + 86400000 * 2, "open": 101, "high": 103, "low": 100, "close": 102, "volume": 20},
        ]
        await pool.insert_ohlcv(test_data, "SOL/USDT", "binance")
        
        # Detect gaps
        gaps = await detect_gaps(pool, "SOL/USDT", "1d")
        
        assert len(gaps) == 0
        await pool.close()

    async def test_detect_gaps_with_gaps(self, postgres_dsn, db_pool):
        """Test gap detection when there are gaps."""
        pool = DatabasePool(dsn=postgres_dsn)
        await pool.init()
        
        # Insert data with a gap (missing day 2)
        base_ts = 1704067200000  # 2024-01-01
        test_data = [
            {"timestamp": base_ts, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            # Missing day 2 (base_ts + 86400000)
            {"timestamp": base_ts + 86400000 * 2, "open": 101, "high": 103, "low": 100, "close": 102, "volume": 20},
        ]
        await pool.insert_ohlcv(test_data, "ADA/USDT", "binance")
        
        # Detect gaps
        gaps = await detect_gaps(pool, "ADA/USDT", "1d")
        
        assert len(gaps) == 1
        await pool.close()

