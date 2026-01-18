"""Data normalization and validation using Pydantic models."""

import logging
from typing import List, Dict, Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class OHLCVData(BaseModel):
    """
    Validated OHLCV data model with constraint enforcement.

    Implements DATA-04 requirement: System validates and normalizes all incoming data.
    Enforces OHLCV constraints:
    - All prices must be positive (open, high, low, close)
    - Volume can be zero (no trades) but not negative
    - high must be >= low
    - open and close must be within high/low range

    Example from research: Data Validation with Pydantic
    """

    timestamp: int
    symbol: str
    exchange: str
    open: float = Field(gt=0, description="Open price must be positive")
    high: float = Field(gt=0, description="High price must be positive")
    low: float = Field(gt=0, description="Low price must be positive")
    close: float = Field(gt=0, description="Close price must be positive")
    volume: float = Field(ge=0, description="Volume cannot be negative")

    @field_validator("high")
    @classmethod
    def high_must_be_gte_low(cls, v: float, info) -> float:
        """Validate that high >= low."""
        if "low" in info.data and v < info.data["low"]:
            raise ValueError(f"high ({v}) must be >= low ({info.data['low']})")
        return v

    @field_validator("low")
    @classmethod
    def low_must_be_lte_high(cls, v: float, info) -> float:
        """Validate that low <= high."""
        if "high" in info.data and v > info.data["high"]:
            raise ValueError(f"low ({v}) must be <= high ({info.data['high']})")
        return v

    @field_validator("open", "close")
    @classmethod
    def price_within_range(cls, v: float, info) -> float:
        """Validate that open and close are within high/low range."""
        if "high" in info.data and "low" in info.data:
            high = info.data["high"]
            low = info.data["low"]
            if not (low <= v <= high):
                raise ValueError(
                    f"price ({v}) must be between low ({low}) and high ({high})"
                )
        return v


def validate_ohlcv(
    candles: List[List[Any]], symbol: str, exchange: str
) -> List[OHLCVData]:
    """
    Validate raw CCXT OHLCV candles using Pydantic model.

    Converts CCXT candle tuples [timestamp, open, high, low, close, volume]
    to validated OHLCVData objects.

    Args:
        candles: List of raw CCXT candle tuples
        symbol: Trading symbol (e.g., 'BTC/USDT')
        exchange: Exchange name (e.g., 'binance')

    Returns:
        List of validated OHLCVData objects
        Invalid candles are logged and skipped
    """
    validated_data = []

    for candle in candles:
        try:
            # CCXT format: [timestamp, open, high, low, close, volume]
            data = {
                "timestamp": candle[0],
                "symbol": symbol,
                "exchange": exchange,
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5]),
            }

            # Validate using Pydantic
            ohlcv = OHLCVData(**data)
            validated_data.append(ohlcv)

        except Exception as e:
            # Log validation error but continue processing other candles
            logger.warning(
                f"Invalid OHLCV data for {symbol}@{exchange}: {e}. "
                f"Candle: {candle}"
            )
            continue

    logger.debug(
        f"Validated {len(validated_data)}/{len(candles)} candles for {symbol}@{exchange}"
    )

    return validated_data
