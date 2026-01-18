"""Data ingestion module for CCXT exchange integration."""

from src.ingestor.exchange import ExchangeWrapper
from src.ingestor.fetcher import fetch_realtime_ohlcv
from src.ingestor.normalizer import validate_ohlcv
from src.ingestor.scheduler import IngestionScheduler, start_scheduler

__all__ = [
    "ExchangeWrapper",
    "fetch_realtime_ohlcv",
    "validate_ohlcv",
    "IngestionScheduler",
    "start_scheduler",
]
