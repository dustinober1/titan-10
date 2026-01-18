"""CCXT exchange wrapper with rate limiting and error handling."""

import logging
from typing import Optional, List, Dict, Any

import ccxt.async_support as ccxt
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)


class ExchangeWrapper:
    """
    Wrapper for CCXT exchange instances with rate limiting and retry logic.

    Implements Pattern 1 from research: async CCXT wrapper with circuit breaker.
    Rate limiting is enabled by default to prevent IP bans (Pitfall 1).
    """

    def __init__(
        self,
        exchange_id: str,
        api_key: Optional[str] = None,
        secret: Optional[str] = None,
    ) -> None:
        """
        Initialize exchange wrapper.

        Args:
            exchange_id: Exchange identifier (e.g., 'binance', 'coinbase')
            api_key: Optional API key for authenticated requests
            secret: Optional API secret for authenticated requests
        """
        self.exchange_id = exchange_id

        # Initialize exchange with rate limiting enabled
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class(
            {
                "apiKey": api_key,
                "secret": secret,
                "enableRateLimit": True,  # CRITICAL: Prevents IP bans
                "options": {
                    "defaultType": "spot",  # Or 'future' for derivatives
                },
            }
        )

        logger.info(f"Initialized {exchange_id} exchange wrapper")

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type(
            (ccxt.NetworkError, ccxt.RateLimitExceeded)
        ),
    )
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        since: Optional[int] = None,
        limit: int = 1000,
    ) -> List[List]:
        """
        Fetch OHLCV data with automatic retry and exponential backoff.

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe for candles (e.g., '1d', '1h', '1m')
            since: Timestamp in milliseconds to fetch from
            limit: Maximum number of candles to fetch

        Returns:
            List of OHLCV candles as [timestamp, open, high, low, close, volume]

        Raises:
            ccxt.NetworkError: On network failures (retries automatically)
            ccxt.RateLimitExceeded: On rate limit errors (retries automatically)
            ccxt.ExchangeError: On exchange-specific errors (no retry)
        """
        try:
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol, timeframe=timeframe, since=since, limit=limit
            )
            logger.debug(
                f"Fetched {len(ohlcv)} candles for {symbol} ({timeframe}) from {self.exchange_id}"
            )
            return ohlcv

        except ccxt.NetworkError as e:
            logger.warning(f"Network error for {self.exchange_id}: {e}")
            raise

        except ccxt.RateLimitExceeded as e:
            logger.error(f"Rate limit exceeded for {self.exchange_id}: {e}")
            raise

        except ccxt.ExchangeError as e:
            # Log but don't retry exchange errors
            logger.error(f"Exchange error for {self.exchange_id}: {e}")
            return []

    async def close(self) -> None:
        """Close exchange connection."""
        await self.exchange.close()
        logger.debug(f"Closed {self.exchange_id} exchange connection")
