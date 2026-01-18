"""Pytest configuration with Testcontainers fixtures for database integration tests."""

import pytest
import asyncio
from typing import AsyncGenerator

import asyncpg
from testcontainers.postgres import PostgresContainer


# Shared PostgreSQL container for all integration tests
@pytest.fixture(scope="session")
def postgres_container():
    """Create a PostgreSQL container for the test session."""
    with PostgresContainer(
        image="postgres:16",
        username="test",
        password="test",
        dbname="titan_test"
    ) as postgres:
        yield postgres


@pytest.fixture(scope="session")
def postgres_url(postgres_container) -> str:
    """Get the connection URL for the PostgreSQL container."""
    return postgres_container.get_connection_url()


@pytest.fixture(scope="session")
def postgres_dsn(postgres_container) -> str:
    """Get the DSN for asyncpg connection."""
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)
    return f"postgresql://test:test@{host}:{port}/titan_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_pool(postgres_dsn) -> AsyncGenerator[asyncpg.Pool, None]:
    """Create an asyncpg connection pool for the test database."""
    pool = await asyncpg.create_pool(postgres_dsn, min_size=1, max_size=5)
    
    # Create the required tables matching the actual schema
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS ohlcv (
                time TIMESTAMPTZ NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                exchange VARCHAR(20) NOT NULL,
                open DOUBLE PRECISION NOT NULL,
                high DOUBLE PRECISION NOT NULL,
                low DOUBLE PRECISION NOT NULL,
                close DOUBLE PRECISION NOT NULL,
                volume DOUBLE PRECISION NOT NULL,
                PRIMARY KEY (time, symbol, exchange)
            );
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS backfill_checkpoints (
                symbol VARCHAR(20) PRIMARY KEY,
                last_timestamp BIGINT NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
    
    yield pool
    
    # Cleanup
    async with pool.acquire() as conn:
        await conn.execute("DROP TABLE IF EXISTS ohlcv CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS backfill_checkpoints CASCADE;")
    
    await pool.close()

