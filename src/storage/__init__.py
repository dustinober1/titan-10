"""Database storage layer with connection pooling and auto-reconnect."""

from src.storage.connection import DatabasePool

# Module-level pool instance (singleton pattern)
_pool: DatabasePool | None = None


async def create_pool(dsn: str) -> DatabasePool:
    """
    Create and initialize the global database connection pool.

    Args:
        dsn: Database connection string

    Returns:
        Initialized DatabasePool instance

    Raises:
        RuntimeError: If pool is already initialized
    """
    global _pool

    if _pool is not None:
        raise RuntimeError("Database pool already initialized. Use get_pool() to access it.")

    _pool = DatabasePool(dsn)
    await _pool.init()
    return _pool


def get_pool() -> DatabasePool | None:
    """
    Get the global database connection pool.

    Returns:
        DatabasePool instance or None if not initialized
    """
    return _pool


async def close_pool() -> None:
    """Close the global database connection pool if initialized."""
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None


__all__ = ["DatabasePool", "create_pool", "get_pool", "close_pool"]
