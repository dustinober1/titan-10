"""OHLCV fetching logic with multi-exchange support and asyncio concurrency."""

import asyncio
import logging
from typing import List, Dict, Any

from src.ingestor.exchange import ExchangeWrapper
from src.storage.connection import DatabasePool

logger = logging.getLogger(__name__)


async def fetch_realtime_ohlcv(
    symbols: List[str],
    exchanges: List[str],
    storage: DatabasePool,
) -> Dict[str, Any]:
    """
    Fetch real-time OHLCV data from multiple exchanges concurrently.

    Uses asyncio.gather for concurrent multi-exchange operations with error isolation.
    One exchange failure doesn't stop others from fetching data.

    Args:
        symbols: List of trading symbols (e.g., ['BTC/USDT', 'ETH/USDT'])
        exchanges: List of exchange IDs (e.g., ['binance', 'coinbase'])
        storage: DatabasePool instance for persisting fetched data

    Returns:
        Dictionary with fetch results:
        {
            'success': List of successful symbol@exchange fetches,
            'failed': List of failed symbol@exchange fetches,
            'total': Total number of fetches attempted
        }
    """
    logger.info(f"Starting real-time OHLCV fetch: {len(symbols)} symbols from {len(exchanges)} exchanges")

    # Create tasks for all symbol/exchange combinations
    tasks = []
    for symbol in symbols:
        for exchange_id in exchanges:
            task = fetch_single_symbol(symbol, exchange_id, storage)
            tasks.append(task)

    # Execute all tasks concurrently with error isolation
    # return_exceptions=True ensures one failure doesn't stop others
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    success_count = 0
    failed_fetches = []

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # Extract symbol and exchange from context
            symbol_idx = i // len(exchanges)
            exchange_idx = i % len(exchanges)
            symbol = symbols[symbol_idx]
            exchange_id = exchanges[exchange_idx]
            failed_fetches.append(f"{symbol}@{exchange_id}")
            logger.error(f"Failed to fetch {symbol}@{exchange_id}: {result}")
        elif result is not None:
            success_count += 1

    logger.info(
        f"Real-time OHLCV fetch complete: {success_count}/{len(tasks)} successful, "
        f"{len(failed_fetches)} failed"
    )

    return {
        "success": success_count,
        "failed": failed_fetches,
        "total": len(tasks),
    }


async def fetch_single_symbol(
    symbol: str,
    exchange_id: str,
    storage: DatabasePool,
    timeframe: str = "1d",
) -> Dict[str, Any]:
    """
    Fetch OHLCV data for a single symbol from a single exchange.

    Handles per-exchange error isolation - if one exchange fails,
    it doesn't affect other exchanges or symbols.

    Args:
        symbol: Trading symbol (e.g., 'BTC/USDT')
        exchange_id: Exchange ID (e.g., 'binance')
        storage: DatabasePool instance for persisting data
        timeframe: Candle timeframe (default: '1d' for Phase 1)

    Returns:
        Dictionary with fetch result:
        {
            'symbol': str,
            'exchange': str,
            'candles_inserted': int,
            'status': 'success' | 'failed'
        }
        Returns None on critical errors
    """
    exchange = None
    try:
        # Create exchange wrapper
        exchange = ExchangeWrapper(exchange_id)

        # Fetch OHLCV data
        candles = await exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe)

        if not candles:
            logger.warning(f"No candles returned for {symbol}@{exchange_id}")
            return {
                "symbol": symbol,
                "exchange": exchange_id,
                "candles_inserted": 0,
                "status": "success",
            }

        # Transform CCXT format to database format
        # CCXT returns: [timestamp, open, high, low, close, volume]
        # Database expects: dict with timestamp, open, high, low, close, volume
        data_points = []
        for candle in candles:
            data_points.append(
                {
                    "timestamp": candle[0],  # milliseconds
                    "open": candle[1],
                    "high": candle[2],
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5],
                }
            )

        # Persist to database
        await storage.insert_ohlcv(data=data_points, symbol=symbol, exchange=exchange_id)

        logger.info(
            f"Fetched and inserted {len(data_points)} candles for {symbol}@{exchange_id}"
        )

        return {
            "symbol": symbol,
            "exchange": exchange_id,
            "candles_inserted": len(data_points),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error fetching {symbol}@{exchange_id}: {e}")
        # Re-raise for asyncio.gather error handling
        raise

    finally:
        # Always close exchange connection
        if exchange:
            try:
                await exchange.close()
            except Exception as e:
                logger.warning(f"Error closing exchange connection for {exchange_id}: {e}")
