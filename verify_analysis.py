import asyncio
import logging
from src.quant.analysis import AnalysisEngine
from src.storage.db import get_db

async def test_analysis():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    engine = AnalysisEngine()
    
    async for session in get_db():
        logger.info("Starting analysis for BTC/USDT...")
        count = await engine.calculate_metrics("BTC/USDT", session)
        logger.info(f"Processed {count} rows for BTC/USDT")

if __name__ == "__main__":
    asyncio.run(test_analysis())
