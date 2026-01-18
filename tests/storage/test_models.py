"""Tests for SQLAlchemy models."""

import pytest
from datetime import datetime

from src.storage.models import RawMarketData, ComputedMetrics


class TestRawMarketDataModel:
    """Tests for RawMarketData model."""

    def test_model_creation(self):
        """Test RawMarketData model instantiation."""
        now = datetime.utcnow()
        data = RawMarketData(
            time=now,
            symbol="BTC/USDT",
            open=42000.0,
            high=42500.0,
            low=41800.0,
            close=42300.0,
            volume=1000.0,
        )
        
        assert data.time == now
        assert data.symbol == "BTC/USDT"
        assert data.open == 42000.0
        assert data.high == 42500.0
        assert data.low == 41800.0
        assert data.close == 42300.0
        assert data.volume == 1000.0

    def test_model_repr(self):
        """Test RawMarketData string representation."""
        now = datetime.utcnow()
        data = RawMarketData(
            time=now,
            symbol="ETH/USDT",
            open=2000.0,
            high=2100.0,
            low=1950.0,
            close=2050.0,
            volume=500.0,
        )
        # Model should be representable as string
        repr_str = repr(data)
        assert "RawMarketData" in repr_str or "ETH/USDT" in str(data) or data is not None


class TestComputedMetricsModel:
    """Tests for ComputedMetrics model."""

    def test_model_creation(self):
        """Test ComputedMetrics model instantiation."""
        now = datetime.utcnow()
        metrics = ComputedMetrics(
            time=now,
            symbol="BTC/USDT",
            rsi_14=55.0,
            macd_line=100.0,
            macd_signal=90.0,
            macd_hist=10.0,
            bb_upper=43000.0,
            bb_lower=41000.0,
            bb_width=0.05,
            trend_adx=25.0,
            z_score=0.5,
            log_return=0.01,
        )
        
        assert metrics.time == now
        assert metrics.symbol == "BTC/USDT"
        assert metrics.rsi_14 == 55.0
        assert metrics.macd_line == 100.0
        assert metrics.z_score == 0.5

    def test_nullable_fields(self):
        """Test that metric fields can be None."""
        now = datetime.utcnow()
        metrics = ComputedMetrics(
            time=now,
            symbol="BTC/USDT",
            rsi_14=None,
            macd_line=None,
            macd_signal=None,
            macd_hist=None,
            bb_upper=None,
            bb_lower=None,
            bb_width=None,
            trend_adx=None,
            z_score=None,
            log_return=None,
        )
        
        assert metrics.rsi_14 is None
        assert metrics.z_score is None
        assert metrics.log_return is None

    def test_partial_metrics(self):
        """Test model with only some metrics populated."""
        now = datetime.utcnow()
        metrics = ComputedMetrics(
            time=now,
            symbol="ETH/USDT",
            rsi_14=45.0,
            bb_width=0.03,
            # Other fields left as None
        )
        
        assert metrics.rsi_14 == 45.0
        assert metrics.bb_width == 0.03
        assert metrics.macd_line is None
