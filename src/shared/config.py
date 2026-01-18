"""Configuration management using Pydantic settings."""

from functools import lru_cache
from typing import Dict, List

from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    database_url: str = Field(
        ...,
        description="PostgreSQL connection string (e.g., postgresql://user:pass@host:port/db)",
    )

    # Exchange API Credentials
    exchange_credentials: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="Exchange API credentials as JSON object",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Trading Symbols (internal storage as string)
    TOP_SYMBOLS_str: str = Field(
        default="BTC/USDT,ETH/USDT,BNB/USDT,SOL/USDT,XRP/USDT,ADA/USDT,DOGE/USDT,AVAX/USDT,MATIC/USDT,LINK/USDT",
        alias="TOP_SYMBOLS",
        description="Comma-separated list of top cryptocurrency trading pairs to monitor",
    )

    # Data Ingestion Settings
    ingestion_interval_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Interval between data ingestion cycles in seconds",
    )
    batch_size: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Batch size for database inserts",
    )

    # Connection Pool Settings
    db_pool_min_size: int = Field(
        default=5,
        ge=1,
        description="Minimum number of connections in the pool",
    )
    db_pool_max_size: int = Field(
        default=20,
        ge=1,
        description="Maximum number of connections in the pool",
    )
    db_pool_max_queries: int = Field(
        default=50000,
        ge=1,
        description="Maximum number of queries per connection before recycling",
    )
    db_pool_max_inactive_lifetime: float = Field(
        default=300.0,
        ge=0.0,
        description="Maximum inactive connection lifetime in seconds",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field
    @property
    def top_symbols(self) -> List[str]:
        """Parse and validate top_symbols from comma-separated string."""
        symbols = [s.strip() for s in self.TOP_SYMBOLS_str.split(",") if s.strip()]

        # Validate each symbol
        for symbol in symbols:
            parts = symbol.split("/")
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid symbol format: {symbol}. Expected format: BASE/QUOTE (e.g., BTC/USDT)"
                )
            if not all(part.isalpha() and len(part) >= 2 for part in parts):
                raise ValueError(
                    f"Invalid symbol format: {symbol}. Symbol parts must be alphabetic and at least 2 characters"
                )
        return symbols

    @field_validator("exchange_credentials", mode="before")
    @classmethod
    def parse_exchange_credentials(cls, v: str | Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        """Parse exchange credentials from JSON string or dict."""
        if isinstance(v, str):
            import json

            if not v or v.strip() in ("{}", "[]", '""', "''"):
                return {}
            try:
                return json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in EXCHANGE_API_KEYS: {e}")
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This function is cached to avoid reloading environment variables on every call.
    The cache can be cleared by calling get_settings.cache_clear() if needed.
    """
    return Settings()
