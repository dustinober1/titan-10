"""Common type definitions for the Titan-10 system."""

from enum import Enum
from typing import TypedDict
from datetime import datetime


class Exchange(str, Enum):
    """Supported cryptocurrency exchanges."""

    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    OKX = "okx"
    BYBIT = "bybit"


class Symbol(str):
    """Trading symbol type with validation."""

    def __init__(self, value: str):
        if not self._is_valid_symbol(value):
            raise ValueError(f"Invalid symbol format: {value}. Expected format: BTC/USDT")

    @staticmethod
    def _is_valid_symbol(value: str) -> bool:
        """Validate symbol format (e.g., BTC/USDT)."""
        parts = value.split("/")
        return len(parts) == 2 and all(part.isalpha() and len(part) >= 2 for part in parts)


class OHLCV(TypedDict):
    """OHLCV (Open, High, Low, Close, Volume) data point."""

    timestamp: int  # Unix timestamp in milliseconds
    open: float  # Open price
    high: float  # High price
    low: float  # Low price
    close: float  # Close price
    volume: float  # Trading volume


# Type aliases
SymbolStr = str
Timestamp = int
Price = float
Volume = float
