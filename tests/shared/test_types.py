"""Tests for shared types."""

import pytest
from datetime import datetime

from src.shared.types import OHLCV


class TestOHLCVType:
    """Tests for OHLCV TypedDict."""

    def test_ohlcv_structure(self):
        """Test OHLCV TypedDict can be created."""
        ohlcv: OHLCV = {
            "timestamp": 1704067200000,
            "open": 42000.0,
            "high": 42500.0,
            "low": 41800.0,
            "close": 42300.0,
            "volume": 1000.0,
        }
        
        assert ohlcv["timestamp"] == 1704067200000
        assert ohlcv["open"] == 42000.0
        assert ohlcv["high"] == 42500.0
        assert ohlcv["low"] == 41800.0
        assert ohlcv["close"] == 42300.0
        assert ohlcv["volume"] == 1000.0

    def test_ohlcv_keys(self):
        """Test OHLCV has expected keys."""
        ohlcv: OHLCV = {
            "timestamp": 0,
            "open": 0.0,
            "high": 0.0,
            "low": 0.0,
            "close": 0.0,
            "volume": 0.0,
        }
        
        expected_keys = {"timestamp", "open", "high", "low", "close", "volume"}
        assert set(ohlcv.keys()) == expected_keys
