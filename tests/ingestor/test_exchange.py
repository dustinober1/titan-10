"""Tests for exchange wrapper."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import ccxt.async_support as ccxt

from src.ingestor.exchange import ExchangeWrapper


class TestExchangeWrapperInit:
    """Tests for ExchangeWrapper initialization."""

    def test_initialization_with_defaults(self):
        """Test wrapper initialization with default parameters."""
        with patch.object(ccxt, 'binance') as mock_binance:
            mock_exchange = MagicMock()
            mock_binance.return_value = mock_exchange
            
            wrapper = ExchangeWrapper("binance")
            
            assert wrapper.exchange_id == "binance"
            mock_binance.assert_called_once()
            # Check that rate limiting is enabled
            call_kwargs = mock_binance.call_args[0][0]
            assert call_kwargs["enableRateLimit"] is True

    def test_initialization_with_credentials(self):
        """Test wrapper initialization with API credentials."""
        with patch.object(ccxt, 'binance') as mock_binance:
            mock_exchange = MagicMock()
            mock_binance.return_value = mock_exchange
            
            wrapper = ExchangeWrapper(
                "binance",
                api_key="test_key",
                secret="test_secret"
            )
            
            call_kwargs = mock_binance.call_args[0][0]
            assert call_kwargs["apiKey"] == "test_key"
            assert call_kwargs["secret"] == "test_secret"


class TestExchangeWrapperFetchOHLCV:
    """Tests for fetch_ohlcv method."""

    @pytest.mark.asyncio
    async def test_fetch_ohlcv_success(self):
        """Test successful OHLCV fetch."""
        mock_data = [
            [1704067200000, 42000.0, 42500.0, 41800.0, 42300.0, 1000.0],
            [1704067260000, 42300.0, 42600.0, 42100.0, 42400.0, 800.0],
        ]
        
        with patch.object(ccxt, 'binance') as mock_binance:
            mock_exchange = AsyncMock()
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=mock_data)
            mock_binance.return_value = mock_exchange
            
            wrapper = ExchangeWrapper("binance")
            result = await wrapper.fetch_ohlcv("BTC/USDT", "1d", limit=100)
            
            assert result == mock_data
            mock_exchange.fetch_ohlcv.assert_called_once_with(
                "BTC/USDT", timeframe="1d", since=None, limit=100
            )

    @pytest.mark.asyncio
    async def test_fetch_ohlcv_with_since(self):
        """Test OHLCV fetch with since parameter."""
        mock_data = [[1704067200000, 42000.0, 42500.0, 41800.0, 42300.0, 1000.0]]
        
        with patch.object(ccxt, 'binance') as mock_binance:
            mock_exchange = AsyncMock()
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=mock_data)
            mock_binance.return_value = mock_exchange
            
            wrapper = ExchangeWrapper("binance")
            since_ts = 1704000000000
            result = await wrapper.fetch_ohlcv("ETH/USDT", "1h", since=since_ts)
            
            mock_exchange.fetch_ohlcv.assert_called_once_with(
                "ETH/USDT", timeframe="1h", since=since_ts, limit=1000
            )

    @pytest.mark.asyncio
    async def test_fetch_ohlcv_exchange_error_returns_empty(self):
        """Test that exchange errors return empty list."""
        with patch.object(ccxt, 'binance') as mock_binance:
            mock_exchange = AsyncMock()
            mock_exchange.fetch_ohlcv = AsyncMock(
                side_effect=ccxt.ExchangeError("Symbol not found")
            )
            mock_binance.return_value = mock_exchange
            
            wrapper = ExchangeWrapper("binance")
            result = await wrapper.fetch_ohlcv("INVALID/PAIR")
            
            assert result == []


class TestExchangeWrapperClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_connection(self):
        """Test closing exchange connection."""
        with patch.object(ccxt, 'binance') as mock_binance:
            mock_exchange = AsyncMock()
            mock_binance.return_value = mock_exchange
            
            wrapper = ExchangeWrapper("binance")
            await wrapper.close()
            
            mock_exchange.close.assert_called_once()
