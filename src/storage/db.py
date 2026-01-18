from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from src.shared.config import get_settings

settings = get_settings()

# Create Async Engine
engine = create_async_engine(
    str(settings.database_url),
    echo=False,
    future=True,
    pool_pre_ping=True
)

# Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db() -> None:
    """
    Initialize database - placeholder for migrations or initial setup.
    """
    # In a real scenario, Alembic handles table creation.
    # This might be used for check-on-startup logic.
    pass
