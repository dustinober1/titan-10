import asyncio
import sys
from sqlalchemy import text
from src.storage.db import get_db

async def test_connection():
    print("Testing async database connection...")
    try:
        async for session in get_db():
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            print(f"Connection successful! Result: {value}")
            return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
