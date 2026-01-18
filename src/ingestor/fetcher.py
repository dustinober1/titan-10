from datetime import datetime, timedelta
import logging
import asyncio
from typing import List, Optional

import ccxt.async_support as ccxt
from tenacity import retry, stop_after_attempt, wait_exponential

from src.storage.db import AsyncSessionLocal
from src.storage.models import RawMarketData
from src.shared.config import get_settings
from src.quant.analysis import AnalysisEngine

settings = get_settings()

logger = logging.getLogger(__name__)

class CryptoFetcher:
    """
    Resilient fetcher for cryptocurrency market data.
    """
    def __init__(self):
        self.max_retries = 3
        self.analysis_engine = AnalysisEngine()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1m', limit: int = 100) -> List[dict]:
        """
        Fetch OHLCV data from Binance (default) with exponential backoff.
        """
        # Parse symbol (e.g., BTC/USDT)
        # Using Binance as primary for now as per SPEC/Plan implied simplicity for MVP
        # Ideally, we map symbol -> exchange.
        
        exchange = ccxt.binanceus({
            'enableRateLimit': True,
        })
        
        try:
            # CCXT structure: [timestamp, open, high, low, close, volume]
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return ohlcv
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            raise
        finally:
            await exchange.close()

    async def run_ingestion(self):
        """
        Main ingestion loop for all top symbols.
        """
        symbols = settings.top_symbols
        async with AsyncSessionLocal() as session:
            for symbol in symbols:
                try:
                    logger.info(f"Fetching {symbol}...")
                    candles = await self.fetch_ohlcv(symbol)
                    
                    data_objects = []
                    for c in candles:
                        # c[0] is timestamp in ms
                        dt = datetime.fromtimestamp(c[0] / 1000.0)
                        
                        data = RawMarketData(
                            time=dt,
                            symbol=symbol,
                            open=c[1],
                            high=c[2],
                            low=c[3],
                            close=c[4],
                            volume=c[5]
                        )
                        data_objects.append(data)
                    
                    # Merge/Upsert
                    for obj in data_objects:
                        await session.merge(obj)
                        
                    await session.commit()
                    logger.info(f"Saved {len(data_objects)} candles for {symbol}")

                    # Trigger Analysis
                    logger.info(f"Analyzing {symbol}...")
                    count = await self.analysis_engine.calculate_metrics(symbol, session)
                    logger.info(f"Calculated metrics for {count} rows of {symbol}")
                    
                except Exception as e:
                    logger.error(f"Ingestion failed for {symbol}: {e}")
                    await session.rollback()


async def fetch_realtime_ohlcv(
    symbols: List[str],
    exchanges: List[str],
    storage,
) -> dict:
    """
    Fetch real-time OHLCV data for given symbols from specified exchanges.
    
    This is a convenience function used by the scheduler.
    
    Args:
        symbols: List of trading symbols (e.g., ['BTC/USDT', 'ETH/USDT'])
        exchanges: List of exchange IDs (e.g., ['binance'])
        storage: Database storage pool for persistence
        
    Returns:
        Dict with 'success' and 'total' counts
    """
    fetcher = CryptoFetcher()
    success_count = 0
    
    for symbol in symbols:
        try:
            candles = await fetcher.fetch_ohlcv(symbol, timeframe='1m', limit=100)
            if candles:
                success_count += 1
                logger.info(f"Fetched {len(candles)} candles for {symbol}")
        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
    
    return {
        "success": success_count,
        "total": len(symbols)
    }


if __name__ == "__main__":
    # Integration smoke test
    async def main():
        logging.basicConfig(level=logging.INFO)
        fetcher = CryptoFetcher()
        await fetcher.run_ingestion()
    
    asyncio.run(main())

