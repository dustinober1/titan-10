import asyncio
from sqlalchemy import text
from src.storage.db import get_db

async def count_rows():
    async for session in get_db():
        result = await session.execute(text("SELECT count(*) FROM raw_market_data"))
        count = result.scalar()
        print(f"Total rows in raw_market_data: {count}")

if __name__ == "__main__":
    asyncio.run(count_rows())
