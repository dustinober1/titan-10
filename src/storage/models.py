"""TimescaleDB hypertable schema definitions."""

# OHLCV table creation
ohlcv_table_sql = """
-- Create OHLCV table for time-series market data
CREATE TABLE IF NOT EXISTS ohlcv (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (time, symbol, exchange)
);
"""

# Convert to hypertable for time-series optimization
create_hypertable_sql = """
-- Convert ohlcv table to hypertable with 1-day chunks
SELECT create_hypertable('ohlcv', 'time', chunk_time_interval => INTERVAL '1 day')
IF NOT EXISTS;
"""

# Create indexes for common query patterns
indexes_sql = """
-- Index for symbol-based queries with time ordering
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_time ON ohlcv (symbol, time DESC);

-- Index for exchange-based queries with time ordering
CREATE INDEX IF NOT EXISTS idx_ohlcv_exchange_time ON ohlcv (exchange, time DESC);

-- Index for time-range queries (most common pattern)
CREATE INDEX IF NOT EXISTS idx_ohlcv_time ON ohlcv (time DESC);
"""

# Configure compression for older data
compression_sql = """
-- Enable compression on the hypertable
ALTER TABLE ohlcv SET (
    timescaledb.compress = true,
    timescaledb.compress_orderby = 'time',
    timescaledb.compress_interval = '7 days'
);

-- Add compression policy (compress data older than 7 days)
-- This is run once; subsequent policy management via add_compression_policy
"""

# Compression policy (run after data exists)
compression_policy_sql = """
-- Add compression policy for data older than 7 days
SELECT add_compression_policy('ohlcv', INTERVAL '7 days')
IF NOT EXISTS;
"""

# Backfill checkpoints table for resumable backfill
checkpoints_table_sql = """
-- Create backfill checkpoints table for tracking resume capability
CREATE TABLE IF NOT EXISTS backfill_checkpoints (
    symbol VARCHAR(20) PRIMARY KEY,
    last_timestamp BIGINT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

# Index for checkpoints queries
checkpoints_index_sql = """
-- Index for checkpoint lookups
CREATE INDEX IF NOT EXISTS idx_backfill_checkpoints_updated_at
ON backfill_checkpoints (updated_at DESC);
"""

# All migrations combined
migration_sql = f"""
{ohlcv_table_sql}

{create_hypertable_sql}

{indexes_sql}

{compression_sql}

{checkpoints_table_sql}

{checkpoints_index_sql}
"""

__all__ = [
    "ohlcv_table_sql",
    "create_hypertable_sql",
    "indexes_sql",
    "compression_sql",
    "compression_policy_sql",
    "checkpoints_table_sql",
    "checkpoints_index_sql",
    "migration_sql",
]
