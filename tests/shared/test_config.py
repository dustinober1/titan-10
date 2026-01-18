"""Tests for configuration management."""

import os
import pytest
from unittest.mock import patch

from src.shared.config import Settings, get_settings


class TestSettingsDefaults:
    """Tests for Settings default values."""

    def test_default_log_level(self):
        """Test default log level is INFO."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}, clear=True):
            get_settings.cache_clear()
            settings = Settings(_env_file=None)
            assert settings.log_level == "INFO"

    def test_default_ingestion_interval(self):
        """Test default ingestion interval is 60 seconds."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.ingestion_interval_seconds == 60

    def test_default_batch_size(self):
        """Test default batch size is 100."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.batch_size == 100

    def test_default_pool_sizes(self):
        """Test default connection pool sizes."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.db_pool_min_size == 5
            assert settings.db_pool_max_size == 20


class TestSymbolParsing:
    """Tests for symbol parsing and validation."""

    def test_default_symbols_parsed(self):
        """Test that default symbols are parsed correctly."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}, clear=True):
            settings = Settings(_env_file=None)
            symbols = settings.top_symbols
            assert "BTC/USDT" in symbols
            assert "ETH/USDT" in symbols
            assert len(symbols) == 10

    def test_custom_symbols_parsed(self):
        """Test that custom symbols are parsed correctly."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "TOP_SYMBOLS": "BTC/USDT,ETH/USDT,SOL/USDT"
        }, clear=True):
            settings = Settings(_env_file=None)
            symbols = settings.top_symbols
            assert symbols == ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

    def test_invalid_symbol_format_rejected(self):
        """Test that invalid symbol format raises error."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "TOP_SYMBOLS": "BTCUSDT"  # Missing slash
        }, clear=True):
            with pytest.raises(ValueError) as exc_info:
                settings = Settings(_env_file=None)
                _ = settings.top_symbols  # Access computed field
            assert "Invalid symbol format" in str(exc_info.value)

    def test_symbol_with_numbers_rejected(self):
        """Test that symbols with numbers are rejected."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "TOP_SYMBOLS": "BTC1/USDT"  # Contains number
        }, clear=True):
            with pytest.raises(ValueError) as exc_info:
                settings = Settings(_env_file=None)
                _ = settings.top_symbols
            assert "alphabetic" in str(exc_info.value).lower()


class TestExchangeCredentials:
    """Tests for exchange credentials parsing."""

    def test_empty_credentials(self):
        """Test that empty credentials return empty dict."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "EXCHANGE_CREDENTIALS": "{}"
        }, clear=True):
            settings = Settings(_env_file=None)
            assert settings.exchange_credentials == {}

    def test_valid_json_credentials(self):
        """Test that valid JSON credentials are parsed."""
        creds_json = '{"binance": {"api_key": "key123", "secret": "secret456"}}'
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "EXCHANGE_CREDENTIALS": creds_json
        }, clear=True):
            settings = Settings(_env_file=None)
            assert "binance" in settings.exchange_credentials
            assert settings.exchange_credentials["binance"]["api_key"] == "key123"

    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises error."""
        from pydantic_settings import SettingsError
        
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "EXCHANGE_CREDENTIALS": "not valid json"
        }, clear=True):
            with pytest.raises((ValueError, SettingsError)) as exc_info:
                Settings(_env_file=None)
            # Pydantic-settings wraps the error
            error_str = str(exc_info.value)
            assert "exchange_credentials" in error_str or "Invalid JSON" in error_str


class TestGetSettingsCache:
    """Tests for get_settings caching."""

    def test_settings_cached(self):
        """Test that settings are cached."""
        get_settings.cache_clear()
        
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}, clear=True):
            settings1 = get_settings()
            settings2 = get_settings()
            assert settings1 is settings2

    def test_cache_clear_works(self):
        """Test that cache can be cleared."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}, clear=True):
            settings1 = get_settings()
            get_settings.cache_clear()
            settings2 = get_settings()
            # After cache clear, should be new instance
            assert settings1 is not settings2
