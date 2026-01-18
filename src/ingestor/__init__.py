"""Data ingestion module for CCXT exchange integration."""

from src.ingestor.exchange import ExchangeWrapper
from src.ingestor.fetcher import CryptoFetcher
from src.ingestor.normalizer import validate_ohlcv
from src.ingestor.scheduler import IngestionScheduler, start_scheduler

__all__ = [
    "ExchangeWrapper",
    "CryptoFetcher",
    "validate_ohlcv",
    "IngestionScheduler",
    "start_scheduler",
]

