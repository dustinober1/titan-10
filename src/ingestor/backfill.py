"""Historical data backfill with checkpoint-based recovery."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from src.ingestor.exchange import ExchangeWrapper
from src.storage.connection import DatabasePool

logger = logging.getLogger(__name__)


class BackfillManager:
    """
    Manager for historical data backfill with checkpoint tracking.

    Implements Pattern 2 from research: incremental backfill with progress tracking
    and resume capability. Checkpoints are saved after each batch to enable recovery
    from failures without restarting from beginning (Pitfall 4).
    """

    def __init__(self, exchange_id: str, storage: DatabasePool) -> None:
        """
        Initialize backfill manager.

        Args:
            exchange_id: Exchange to fetch data from (e.g., 'binance')
            storage: Database connection pool for storing data and checkpoints
        """
        self.exchange_id = exchange_id
        self.storage = storage
        self.exchange = ExchangeWrapper(exchange_id)
        self.checkpoints: Dict[str, int] = {}  # symbol -> last_timestamp

        logger.info(f"Initialized BackfillManager for {exchange_id}")

    async def backfill_symbol(
        self,
        symbol: str,
        timeframe: str = "1d",
        years_back: int = 5,
    ) -> int:
        """
        Backfill historical data for a single symbol with checkpoint resume.

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            timeframe: Candle timeframe (default: '1d' for daily candles)
            years_back: Number of years of historical data to fetch

        Returns:
            Number of candles successfully backfilled
        """
        logger.info(f"Starting backfill for {symbol} ({timeframe}, {years_back} years)")

        # Check for existing checkpoint
        last_timestamp = await self.storage.get_last_checkpoint(symbol)
        if last_timestamp:
            start_date = datetime.fromtimestamp(last_timestamp / 1000)
            logger.info(f"Resuming {symbol} from {start_date}")
        else:
            start_date = datetime.now() - timedelta(days=years_back * 365)
            logger.info(f"No checkpoint found for {symbol}, starting from {start_date}")

        all_candles = []
        current_since = int(start_date.timestamp() * 1000)
        batch_count = 0

        while True:
            try:
                # Fetch batch (typically 500-1000 candles)
                candles = await self.exchange.fetch_ohlcv(
                    symbol,
                    timeframe=timeframe,
                    since=current_since,
                    limit=1000,
                )

                if not candles:
                    logger.info(f"No more candles available for {symbol}")
                    break

                all_candles.extend(candles)
                batch_count += 1

                # Update checkpoint after each successful batch
                last_ts = candles[-1][0]
                self.checkpoints[symbol] = last_ts
                await self.storage.save_checkpoint(symbol, last_ts)

                logger.debug(
                    f"Backfilled {len(all_candles)} candles for {symbol} "
                    f"(batch {batch_count}, latest: {datetime.fromtimestamp(last_ts / 1000)})"
                )

                # Move to next batch
                current_since = last_ts + 1

                # Rate limit respect (1 second delay between batches)
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error backfilling {symbol}: {e}")
                # Checkpoint was saved before error, can resume on next run
                break

        # Bulk insert to database
        if all_candles:
            # Convert CCXT format to database format
            db_data = [
                {
                    "timestamp": candle[0],
                    "open": candle[1],
                    "high": candle[2],
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5],
                }
                for candle in all_candles
            ]

            await self.storage.insert_ohlcv(db_data, symbol, self.exchange_id)
            logger.info(f"Backfilled {len(all_candles)} candles for {symbol}")
        else:
            logger.warning(f"No candles to insert for {symbol}")

        return len(all_candles)


async def backfill_all_symbols(
    symbols: List[str],
    exchange_id: str,
    storage: DatabasePool,
    years_back: int = 5,
) -> Dict[str, int]:
    """
    Orchestrate backfill for multiple symbols.

    Args:
        symbols: List of trading symbols to backfill
        exchange_id: Exchange to fetch data from
        storage: Database connection pool
        years_back: Number of years of historical data to fetch

    Returns:
        Dictionary mapping symbol to candle count
    """
    logger.info(f"Starting backfill for {len(symbols)} symbols from {exchange_id}")

    manager = BackfillManager(exchange_id, storage)
    results: Dict[str, int] = {}

    for symbol in symbols:
        try:
            count = await manager.backfill_symbol(symbol, "1d", years_back)
            results[symbol] = count
            logger.info(f"Completed backfill for {symbol}: {count} candles")
        except Exception as e:
            logger.error(f"Failed to backfill {symbol}: {e}")
            results[symbol] = 0
            # Continue with next symbol

    logger.info(f"Backfill complete: {sum(results.values())} total candles across {len(symbols)} symbols")

    return results


async def initial_backfill(storage: DatabasePool) -> Dict[str, int]:
    """
    Main entry point for initial system backfill on startup.

    Fetches 5 years of historical data for all configured top symbols.

    Args:
        storage: Database connection pool

    Returns:
        Dictionary mapping symbol to candle count
    """
    from src.shared.config import get_settings

    settings = get_settings()
    top_symbols = settings.top_symbols

    logger.info(f"Starting initial backfill for {len(top_symbols)} top symbols")

    results = await backfill_all_symbols(
        symbols=top_symbols,
        exchange_id="binance",
        storage=storage,
        years_back=5,
    )

    logger.info("Initial backfill complete")

    return results
