from datetime import datetime
from sqlalchemy import Column, DateTime, Float, String, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class RawMarketData(Base):
    """
    Immutable raw OHLCV market data.
    Partitioned by time in TimescaleDB (setup via migration).
    """
    __tablename__ = "raw_market_data"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    symbol: Mapped[str] = mapped_column(String, primary_key=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)

    volume: Mapped[float] = mapped_column(Float)

    # Composite primary key (time, symbol) is natural for time-series
    # Additional indexes can be added as needed, but Timescale handles time indexing automatically.


class ComputedMetrics(Base):
    """
    Derived technical and statistical metrics.
    One-to-one mapping with RawMarketData by (time, symbol).
    """
    __tablename__ = "computed_metrics"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    symbol: Mapped[str] = mapped_column(String, primary_key=True)
    
    # Technical Indicators
    rsi_14: Mapped[float | None] = mapped_column(Float, nullable=True)
    macd_line: Mapped[float | None] = mapped_column(Float, nullable=True)
    macd_signal: Mapped[float | None] = mapped_column(Float, nullable=True)
    macd_hist: Mapped[float | None] = mapped_column(Float, nullable=True)
    bb_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    bb_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    bb_width: Mapped[float | None] = mapped_column(Float, nullable=True)
    trend_adx: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Statistical Metrics
    z_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    log_return: Mapped[float | None] = mapped_column(Float, nullable=True)
