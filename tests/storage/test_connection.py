"""Tests for DatabasePool connection class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestDatabasePool:
    """Tests for DatabasePool class."""

    def test_initialization(self):
        """Test DatabasePool initialization."""
        from src.storage.connection import DatabasePool
        
        pool = DatabasePool(
            dsn="postgresql://user:pass@localhost:5432/testdb",
            min_size=5,
            max_size=20
        )
        
        assert pool.dsn == "postgresql://user:pass@localhost:5432/testdb"
        assert pool.min_size == 5
        assert pool.max_size == 20
        assert pool._pool is None

    def test_initialization_defaults(self):
        """Test DatabasePool with default parameters."""
        from src.storage.connection import DatabasePool
        
        pool = DatabasePool(dsn="postgresql://localhost/db")
        
        assert pool.min_size == 5
        assert pool.max_size == 20

    @pytest.mark.asyncio
    async def test_close_when_no_pool(self):
        """Test close when pool was never initialized."""
        from src.storage.connection import DatabasePool
        
        pool = DatabasePool(dsn="postgresql://localhost/db")
        
        # Should not raise when pool is None
        await pool.close()
        assert pool._pool is None
