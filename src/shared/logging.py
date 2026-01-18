"""Structured logging configuration for Titan-10."""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class UTCFormatter(logging.Formatter):
    """Custom formatter that uses UTC timestamps."""

    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        """Format time with UTC timezone."""
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


class CorrelationFilter(logging.Filter):
    """
    Filter to add correlation_id to log records.

    This is a placeholder for Phase 4 when request tracing will be implemented.
    Currently, it adds None for correlation_id if not present.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation_id to record if not present."""
        if not hasattr(record, "correlation_id"):
            record.correlation_id = None
        return True


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    enable_console: bool = True,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, only console logging is used.
        enable_console: Whether to enable console output. Default: True.

    The log format includes:
    - UTC timestamp
    - Log level
    - Module name
    - Correlation ID (for request tracing in Phase 4)
    - Log message
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove any existing handlers
    root_logger.handlers.clear()

    # Define log format
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    formatter = UTCFormatter(log_format, datefmt="%Y-%m-%dT%H:%M:%SZ")

    # Add correlation filter
    correlation_filter = CorrelationFilter()

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(correlation_filter)
        root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(correlation_filter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name, typically __name__ of the calling module

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
