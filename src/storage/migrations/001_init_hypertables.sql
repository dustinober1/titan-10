-- Migration 001: Initialize TimescaleDB hypertables for OHLCV data
-- This migration creates the time-series optimized schema for market data storage
--
-- Prerequisites:
--   - PostgreSQL 16+ with TimescaleDB extension installed
--   - Database created with CREATE EXTENSION IF NOT EXISTS timescaledb;
--
-- Usage:
--   psql -h localhost -U postgres -d titan_db -f 001_init_hypertables.sql
--
-- Idempotency: All statements use IF NOT EXISTS for safe re-running

-- ============================================================================
-- SECTION 1: OHLCV Hypertable Creation
-- ============================================================================

-- Create OHLCV table for time-series market data
-- Stores Open, High, Low, Close, Volume data per timestamp, symbol, and exchange
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

-- Convert to hypertable for time-series optimization
-- Chunk interval: 1 day (balances query performance and chunk management)
SELECT create_hypertable('ohlcv', 'time', chunk_time_interval => INTERVAL '1 day')
IF NOT EXISTS;

-- ============================================================================
-- SECTION 2: Indexes for Query Performance
-- ============================================================================

-- Index for symbol-based queries (e.g., "get BTC/USDT data")
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_time ON ohlcv (symbol, time DESC);

-- Index for exchange-based queries (e.g., "get all Binance data")
CREATE INDEX IF NOT EXISTS idx_ohlcv_exchange_time ON ohlcv (exchange, time DESC);

-- Index for time-range queries (most common pattern)
CREATE INDEX IF NOT EXISTS idx_ohlcv_time ON ohlcv (time DESC);

-- ============================================================================
-- SECTION 3: Compression Configuration
-- ============================================================================

-- Enable compression on the hypertable
-- IMPORTANT: Do NOT use compress_segmentby on 'symbol' (high cardinality anti-pattern)
-- Compression settings:
--   - compress_orderby: 'time' (temporal ordering for better compression)
--   - compress_interval: '7 days' (compress data older than 7 days)
ALTER TABLE ohlcv SET (
    timescaledb.compress = true,
    timescaledb.compress_orderby = 'time',
    timescaledb.compress_interval = '7 days'
);

-- Add compression policy for automatic background compression
-- Data older than 7 days will be compressed automatically
SELECT add_compression_policy('ohlcv', INTERVAL '7 days')
IF NOT EXISTS;

-- ============================================================================
-- SECTION 4: Backfill Checkpoints Table
-- ============================================================================

-- Create backfill checkpoints table for tracking resume capability
-- Enables intelligent backfill to resume from last successful timestamp
CREATE TABLE IF NOT EXISTS backfill_checkpoints (
    symbol VARCHAR(20) PRIMARY KEY,
    last_timestamp BIGINT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for checkpoint queries (e.g., "get all stale checkpoints")
CREATE INDEX IF NOT EXISTS idx_backfill_checkpoints_updated_at
ON backfill_checkpoints (updated_at DESC);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify hypertable creation
\echo 'Checking hypertable status...'
SELECT hypertable_name, chunk_time_interval, compression, number_chunks
FROM timescaledb_information.hypertables
WHERE hypertable_name = 'ohlcv';

-- Verify indexes
\echo 'Checking indexes...'
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'ohlcv';

-- Verify compression policy
\echo 'Checking compression policy...'
SELECT policy_name, hypertable_name, schedule_interval
FROM timescaledb_information.jobs
WHERE hypertable_name = 'ohlcv';
