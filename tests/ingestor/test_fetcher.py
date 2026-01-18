"""Tests for CryptoFetcher class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import ccxt.async_support as ccxt

from src.ingestor.fetcher import CryptoFetcher, fetch_realtime_ohlcv


class TestCryptoFetcher:
    """Tests for CryptoFetcher class."""

    def test_initialization(self):
        """Test CryptoFetcher initialization."""
        fetcher = CryptoFetcher()
        assert fetcher.max_retries == 3
        assert fetcher.analysis_engine is not None

    @pytest.mark.asyncio
    async def test_fetch_ohlcv_success(self):
        """Test successful OHLCV fetch via CryptoFetcher."""
        mock_data = [
            [1704067200000, 42000.0, 42500.0, 41800.0, 42300.0, 1000.0],
            [1704067260000, 42300.0, 42600.0, 42100.0, 42400.0, 800.0],
        ]
        
        with patch.object(ccxt, 'binanceus') as mock_binance:
            mock_exchange = AsyncMock()
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=mock_data)
            mock_binance.return_value = mock_exchange
            
            fetcher = CryptoFetcher()
            result = await fetcher.fetch_ohlcv("BTC/USDT", "1m", limit=100)
            
            assert result == mock_data
            mock_exchange.fetch_ohlcv.assert_called_once_with(
                "BTC/USDT", "1m", limit=100
            )
            mock_exchange.close.assert_called_once()


class TestFetchRealtimeOHLCV:
    """Tests for fetch_realtime_ohlcv function."""

    @pytest.mark.asyncio
    async def test_fetch_realtime_success(self):
        """Test successful real-time fetch."""
        mock_data = [[1704067200000, 42000.0, 42500.0, 41800.0, 42300.0, 1000.0]]
        
        with patch.object(ccxt, 'binanceus') as mock_binance:
            mock_exchange = AsyncMock()
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=mock_data)
            mock_binance.return_value = mock_exchange
            
            result = await fetch_realtime_ohlcv(
                symbols=["BTC/USDT", "ETH/USDT"],
                exchanges=["binance"],
                storage=MagicMock(),
            )
            
            assert result["total"] == 2
            assert result["success"] == 2

    @pytest.mark.asyncio
    async def test_fetch_realtime_partial_failure(self):
        """Test real-time fetch with some failures."""
        mock_data = [[1704067200000, 42000.0, 42500.0, 41800.0, 42300.0, 1000.0]]
        
        with patch.object(ccxt, 'binanceus') as mock_binance:
            mock_exchange = AsyncMock()
            # First call succeeds, second fails
            mock_exchange.fetch_ohlcv = AsyncMock(
                side_effect=[mock_data, Exception("Network error")]
            )
            mock_binance.return_value = mock_exchange
            
            result = await fetch_realtime_ohlcv(
                symbols=["BTC/USDT", "INVALID/PAIR"],
                exchanges=["binance"],
                storage=MagicMock(),
            )
            
            assert result["total"] == 2
            assert result["success"] == 1

    @pytest.mark.asyncio
    async def test_fetch_realtime_empty_symbols(self):
        """Test real-time fetch with empty symbol list."""
        result = await fetch_realtime_ohlcv(
            symbols=[],
            exchanges=["binance"],
            storage=MagicMock(),
        )
        
        assert result["total"] == 0
        assert result["success"] == 0
