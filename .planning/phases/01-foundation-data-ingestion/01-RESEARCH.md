# Phase 1: Foundation & Data Ingestion - Research

**Researched:** 2026-01-18
**Domain:** Cryptocurrency data ingestion, time-series storage, autonomous systems
**Confidence:** HIGH

## Summary

Phase 1 establishes the foundation for Titan-10's autonomous cryptocurrency data pipeline. Research confirms that **CCXT with async support** is the industry standard for multi-exchange connectivity, providing unified API access to 100+ exchanges with built-in rate limiting. **TimescaleDB** (PostgreSQL extension) is the definitive choice for time-series OHLCV data, offering 83% storage compression and automatic partitioning via hypertables.

The critical insight from research: **autonomous operation requires layered resilience**. Exchange APIs fail frequently (rate limits, downtime, network issues), so the system must implement exponential backoff with jitter, circuit breakers, and per-symbol error isolation. Historical backfill jobs require checkpoint mechanisms to resume after failures without restarting from beginning.

**Primary recommendation:** Use CCXT async_support with Tenacity retry decorators, store data in TimescaleDB hypertables with compression, and implement APScheduler's AsyncIOScheduler for periodic data fetching tasks.

## Standard Stack

### Core Data Ingestion

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **CCXT** | 4.5+ | Multi-exchange connectivity | De facto standard, 108 exchanges unified API, built-in rate limiting |
| **ccxt.async_support** | 4.5+ | Async exchange operations | REQUIRED for concurrent fetching from 20 exchanges |
| **python-dotenv** | Latest | Environment configuration | Project constraint for configuration management |
| **pydantic** | 2.0+ | Data validation | Type-safe config, validates OHLCV constraints |
| **pydantic-settings** | 2.0+ | Settings management | Environment variable loading, secrets handling |

### Database & Storage

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **PostgreSQL** | 16 | Primary database | Project constraint, ACID compliance, reliability |
| **TimescaleDB** | 2.15+ | Time-series extension | 83% compression, hypertables, continuous aggregates |
| **asyncpg** | Latest | Async PostgreSQL client | Fastest async driver (2-3x faster than psycopg2), connection pooling |

### Reliability & Scheduling

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **tenacity** | 4.4.0+ | Retry logic | Exponential backoff, decorator-based, production-proven |
| **APScheduler** | 3.10+ | Job scheduling | AsyncIOScheduler for cron-like scheduling of async functions |

### Development

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **pytest** | Latest | Testing framework | Async test support with pytest-asyncio |
| **pytest-asyncio** | Latest | Async test utilities | Required for testing CCXT async functions |
| **ruff** | Latest | Linting/formatting | Fast Python linter, replaces black/flake8 |
| **mypy** | Latest | Type checking | Static type analysis for code quality |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CCXT | Exchange-specific APIs | 20x integration complexity, no unified schema |
| TimescaleDB | InfluxDB, MongoDB | Less mature ecosystem, No SQL queries |
| Tenacity | Custom retry logic | Error-prone, reinventing wheel |
| asyncpg | psycopg2, SQLAlchemy | Slower, no native async support |

**Installation:**
```bash
# Core dependencies (managed by uv)
uv add ccxt>=4.5
uv add python-dotenv
uv add "pydantic>=2.0"
uv add "pydantic-settings>=2.0"

# Database
uv add asyncpg
# TimescaleDB installed via Docker: timescale/timescaledb:latest-pg16

# Reliability & scheduling
uv add tenacity>=4.4.0
uv add "apscheduler>=3.10"

# Development
uv add -D pytest pytest-asyncio ruff mypy
```

## Architecture Patterns

### Recommended Project Structure

```
src/
├── ingestor/              # Data ingestion module
│   ├── __init__.py
│   ├── exchange.py        # CCXT exchange wrapper
│   ├── fetcher.py         # OHLCV fetching logic
│   ├── backfill.py        # Historical data backfill
│   ├── normalizer.py      # Data normalization/validation
│   └── scheduler.py       # APScheduler job setup
├── storage/               # Database layer
│   ├── __init__.py
│   ├── connection.py      # asyncpg connection pool
│   ├── models.py          # Database schema definitions
│   ├── queries.py         # SQL query helpers
│   └── migrations/        # TimescaleDB setup scripts
├── shared/                # Shared utilities
│   ├── __init__.py
│   ├── config.py          # Pydantic settings
│   ├── logging.py         # Structured logging
│   └── types.py           # Shared type definitions
└── tests/                 # Test suite
    ├── __init__.py
    ├── fixtures/          # Test data fixtures
    ├── test_fetcher.py
    ├── test_backfill.py
    └── test_normalizer.py
```

### Pattern 1: Async CCXT Exchange Wrapper

**What:** Wrapper class for CCXT exchange instantiation with rate limiting and error handling
**When to use:** All exchange API interactions
**Example:**
```python
# Source: CCXT Official Documentation
import ccxt.async_support as ccxt
from tenacity import retry, stop_after_attempt, wait_exponential

class ExchangeWrapper:
    def __init__(self, exchange_id: str, api_key: str = None, secret: str = None):
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,  # CRITICAL: Built-in rate limiting
            'options': {
                'defaultType': 'spot',  # Or 'future' for derivatives
            }
        })

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60)
    )
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1d',
        since: int = None,
        limit: int = 1000
    ) -> list:
        """Fetch OHLCV data with automatic retry"""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                since=since,
                limit=limit
            )
            return ohlcv
        except ccxt.NetworkError as e:
            # Retry on network errors
            raise
        except ccxt.ExchangeError as e:
            # Log but don't retry exchange errors
            logger.error(f"Exchange error for {self.exchange_id}: {e}")
            return []

    async def close(self):
        """Close exchange connection"""
        await self.exchange.close()
```

### Pattern 2: Historical Backfill with Checkpoints

**What:** Incremental backfill with progress tracking and resume capability
**When to use:** Initial 5-year historical data load
**Example:**
```python
from datetime import datetime, timedelta
import asyncio

class BackfillManager:
    def __init__(self, exchange_wrapper, storage):
        self.exchange = exchange_wrapper
        self.storage = storage
        self.checkpoints = {}  # symbol -> last_timestamp

    async def backfill_symbol(
        self,
        symbol: str,
        timeframe: str = '1d',
        years_back: int = 5
    ):
        """Backfill historical data with checkpoint resume"""

        # Check for existing checkpoint
        last_timestamp = self.checkpoints.get(symbol)
        if last_timestamp:
            start_date = datetime.fromtimestamp(last_timestamp / 1000)
            logger.info(f"Resuming {symbol} from {start_date}")
        else:
            start_date = datetime.now() - timedelta(days=years_back * 365)

        all_candles = []
        current_since = int(start_date.timestamp() * 1000)

        while True:
            try:
                # Fetch batch (typically 500-1000 candles)
                candles = await self.exchange.fetch_ohlcv(
                    symbol,
                    timeframe=timeframe,
                    since=current_since,
                    limit=1000
                )

                if not candles:
                    break

                all_candles.extend(candles)

                # Update checkpoint after each successful batch
                last_ts = candles[-1][0]
                self.checkpoints[symbol] = last_ts
                await self.storage.save_checkpoint(symbol, last_ts)

                # Move to next batch
                current_since = last_ts + 1

                # Rate limit respect (CCXT handles this, but be safe)
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error backfilling {symbol}: {e}")
                # Continue from last checkpoint on next run
                break

        # Bulk insert to database
        await self.storage.insert_ohlcv(symbol, all_candles)
        logger.info(f"Backfilled {len(all_candles)} candles for {symbol}")
```

### Pattern 3: APScheduler Async Job Scheduling

**What:** Schedule async functions for periodic data fetching
**When to use:** Real-time ingestion (every 60s) and daily backfill
**Example:**
```python
# Source: APScheduler Documentation + WebSearch 2025
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class IngestionScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def fetch_realtime_data(self):
        """Fetch latest OHLCV for top 20 symbols"""
        symbols = ['BTC/USDT', 'ETH/USDT', ...]  # Top 20

        tasks = []
        for symbol in symbols:
            task = self.fetch_symbol_data(symbol)
            tasks.append(task)

        # Fetch from all exchanges concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

    async def fetch_symbol_data(self, symbol: str):
        """Fetch data for single symbol with error isolation"""
        try:
            exchange = ExchangeWrapper('binance')
            candles = await exchange.fetch_ohlcv(symbol, timeframe='1m')
            await self.storage.insert_ohlcv(symbol, candles)
            await exchange.close()
        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
            # Don't crash - continue with other symbols

    def start(self):
        """Start scheduled jobs"""

        # Real-time ingestion: Every 60 seconds
        self.scheduler.add_job(
            self.fetch_realtime_data,
            'interval',
            seconds=60,
            id='realtime_ingestion',
            replace_existing=True
        )

        # Historical backfill: Daily at 2 AM UTC
        self.scheduler.add_job(
            self.daily_backfill,
            CronTrigger(hour=2, minute=0),
            id='daily_backfill',
            replace_existing=True
        )

        # Data gap detection: Every 5 minutes
        self.scheduler.add_job(
            self.detect_gaps,
            'interval',
            minutes=5,
            id='gap_detection',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("Scheduler started")
```

### Pattern 4: TimescaleDB Hypertable Setup

**What:** Create time-series optimized tables with automatic partitioning
**When to use:** Database schema initialization
**Example:**
```python
# Source: TimescaleDB Official Documentation
CREATE TABLE ohlcv (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    open DECIMAL(20, 8) NOT NULL,
    high DECIMAL(20, 8) NOT NULL,
    low DECIMAL(20, 8) NOT NULL,
    close DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(30, 8) NOT NULL,
    PRIMARY KEY (time, symbol, exchange)
);

-- Convert to hypertable (partition by time)
SELECT create_hypertable('ohlcv', 'time',
    chunk_time_interval => INTERVAL '1 day'
);

-- Create indexes for common queries
CREATE INDEX idx_ohlcv_symbol_time ON ohlcv (symbol, time DESC);
CREATE INDEX idx_ohlcv_exchange_time ON ohlcv (exchange, time DESC);

-- Enable compression for historical data
ALTER TABLE ohlcv SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol,exchange',
    timescaledb.compress_orderby = 'time'
);

-- Add compression policy (compress data older than 7 days)
ALTER TABLE ohlcv SET (timescaledb.compress, timescaledb.compress_interval = '7 days');
```

### Pattern 5: asyncpg Connection Pool

**What:** Managed async database connection pool
**When to use:** All database operations
**Example:**
```python
# Source: asyncpg Documentation + WebSearch 2025
import asyncpg

class DatabasePool:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool = None

    async def init(self):
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(
            self.dsn,
            min_size=5,      # Minimum connections
            max_size=20,     # Maximum connections
            command_timeout=60,
            max_queries=50000,  # Recreate connection after N queries
            max_inactive_connection_lifetime=300.0
        )
        logger.info("Database pool initialized")

    async def insert_ohlcv(self, symbol: str, candles: list):
        """Batch insert OHLCV data"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(
                    """INSERT INTO ohlcv (time, symbol, exchange, open, high, low, close, volume)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (time, symbol, exchange) DO NOTHING""",
                    candles
                )

    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
```

### Anti-Patterns to Avoid

- **Synchronous CCXT in async context:** Use `ccxt.async_support`, not `ccxt` module
- **No rate limiting:** Always enable `enableRateLimit: True` in CCXT config
- **Hard-coded retry logic:** Use Tenacity decorators instead of custom retry loops
- **Missing checkpoints:** Long backfill jobs MUST have checkpoint/resume capability
- **Ignoring exchange errors:** Log all errors, implement circuit breakers for failing exchanges
- **Single-threaded fetching:** Use asyncio.gather() for concurrent multi-exchange fetching

## Don't Hand-Roll

Problems with existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| **Rate limiting** | Custom rate limiter with tokens/buckets | CCXT `enableRateLimit: True` | Exchange-specific limits handled automatically, IP ban prevention |
| **Retry logic** | Custom retry with sleep loops | Tenacity `@retry` decorator | Exponential backoff with jitter, battle-tested, handles edge cases |
| **Async scheduling** | Custom cron with threading | APScheduler AsyncIOScheduler | Native async support, cron-like syntax, persistent jobs |
| **OHLCV normalization** | Manual timestamp conversion | CCXT unified API | Consistent format across 100+ exchanges, handles timezone differences |
| **Time partitioning** | Manual table partitioning | TimescaleDB hypertables | Automatic partitioning, compression, continuous aggregates |
| **Connection pooling** | Custom connection manager | asyncpg.create_pool() | Proven reliability, automatic reconnection, prepared statements |

**Key insight:** Building custom solutions for these problems introduces subtle bugs (off-by-one errors in rate limits, race conditions in connection pools, timezone bugs in timestamp handling). Established libraries have handled these edge cases over years of production use.

## Common Pitfalls

### Pitfall 1: Rate Limit Exceeded → IP Ban

**What goes wrong:** Exceeding exchange API rate limits results in automated IP bans (HTTP 418), blocking all future requests for hours to days.

**Why it happens:**
- Exchanges track cumulative rate limit violations
- Failing to back off after HTTP 429 warnings triggers automatic bans
- CCXT has built-in rate limiting but it must be enabled

**How to avoid:**
```python
# ALWAYS enable rate limiting
exchange = ccxt.binance({
    'enableRateLimit': True,  # CRITICAL
})

# Add exponential backoff for extra safety
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=60)
)
async def fetch_with_retry():
    ...
```

**Warning signs:**
- HTTP 429 errors appearing in logs
- Increasing latency from exchange responses
- HTTP 418 errors (already banned)

**Sources:**
- [CCXT Documentation - Rate Limit](https://docs.ccxt.com/en/latest/manual/) - Official rate limiting guidance
- [Binance: How to Avoid Getting Banned by Rate Limits](https://www.binance.com/en/academy/articles/how-to-avoid-getting-banned-by-rate-limits) (HIGH confidence)

### Pitfall 2: Missing Candle Data (Gaps)

**What goes wrong:** Exchange APIs return incomplete OHLCV data with missing candles, creating gaps that invalidate volatility calculations.

**Why it happens:**
- Exchange downtime (maintenance or outages)
- Network interruptions during data fetching
- APIs not returning data for illiquid periods

**How to avoid:**
```python
async def detect_gaps(symbol: str, timeframe: str):
    """Detect missing candles in historical data"""

    # Get expected time range
    start_time = datetime.now() - timedelta(days=365)
    end_time = datetime.now()

    # Calculate expected candle count
    if timeframe == '1d':
        expected_candles = 365
    elif timeframe == '1h':
        expected_candles = 365 * 24

    # Query actual candle count
    async with pool.acquire() as conn:
        actual_count = await conn.fetchval(
            """SELECT COUNT(*) FROM ohlcv
            WHERE symbol = $1 AND time >= $2 AND time <= $3""",
            symbol, start_time, end_time
        )

    # Calculate gap percentage
    gap_rate = (expected_candles - actual_count) / expected_candles * 100

    if gap_rate > 5:  # Alert if >5% missing
        logger.warning(f"High gap rate for {symbol}: {gap_rate:.1f}%")
        await send_alert(symbol, gap_rate)
```

**Warning signs:**
- Uneven spacing between timestamps
- Fewer candles than expected for date range
- Volatility metrics suddenly drop to zero

**Sources:**
- [CoinAPI: Backtest with Real Market Data](https://www.coinapi.io/blog/backtest-crypto-strategies-with-real-market-data) (MEDIUM confidence)

### Pitfall 3: TimescaleDB Compression Performance Degradation

**What goes wrong:** TimescaleDB compression creates performance issues instead of improving it, causing slow queries.

**Why it happens:**
- Chunks that are too small (<1 MB) create significant overhead
- Using `compress_segmentby` on high-cardinality fields like symbol
- Improper segmentby configuration

**How to avoid:**
```sql
-- AVOID: Compressing by symbol (high cardinality)
ALTER TABLE ohlcv SET (
    timescaledb.compress_segmentby = 'symbol'  -- BAD
);

-- GOOD: Compress by time only
ALTER TABLE ohlcv SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time',
    timescaledb.compress_interval = '7 days'
);

-- Monitor chunk sizes
SELECT * FROM timescaledb_information.chunks
WHERE hypertable_name = 'ohlcv';
```

**Warning signs:**
- Queries slower after compression enabled
- High IO wait during compression operations
- Many small chunks in database

**Sources:**
- [TimescaleDB GitHub Issue #8715](https://github.com/timescale/timescaledb/issues/8715) - Chunk performance issues
- [My experience with timescaledb Compression](https://mail-dpant.medium.com/my-experience-with-timescaledb-compression-68405425827) (MEDIUM confidence)

### Pitfall 4: Backfill Without Checkpoints

**What goes wrong:** Long-running backfill jobs fail near completion, requiring restart from beginning.

**Why it happens:**
- No checkpoint/savepoint mechanism
- Job fails due to transient error
- No progress tracking

**How to avoid:**
```python
# Create checkpoints table
CREATE TABLE backfill_checkpoints (
    symbol VARCHAR(20) PRIMARY KEY,
    last_timestamp BIGINT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

# Save progress after each batch
async def save_checkpoint(self, symbol: str, timestamp: int):
    await self.pool.execute(
        """INSERT INTO backfill_checkpoints (symbol, last_timestamp)
        VALUES ($1, $2)
        ON CONFLICT (symbol) DO UPDATE
        SET last_timestamp = $2, updated_at = NOW()""",
        symbol, timestamp
    )

# Resume from checkpoint on restart
async def get_last_checkpoint(self, symbol: str) -> int:
    row = await self.pool.fetchrow(
        "SELECT last_timestamp FROM backfill_checkpoints WHERE symbol = $1",
        symbol
    )
    return row['last_timestamp'] if row else None
```

**Warning signs:**
- Backfill jobs failing after 12+ hours
- Having to restart backfill from beginning
- No progress indicators during backfill

**Sources:**
- [Streaming CEX, DEX, and Blockchain Events](https://community.databricks.com/t/technical-blog/streaming-cex-dex-and-blockchain-events-in-databricks-for-web3/ba-p/120503) (MEDIUM confidence)

### Pitfall 5: Connection Pool Exhaustion

**What goes wrong:** PostgreSQL connection pool exhausted, causing new requests to fail with timeout errors.

**Why it happens:**
- Too many concurrent requests relative to pool size
- Long-running database queries holding connections
- Connections not released properly

**How to avoid:**
```python
# Proper pool sizing
pool = await asyncpg.create_pool(
    dsn,
    min_size=5,
    max_size=20,  # Formula: (num CPUs × 2) + 1 for I/O-bound workloads
    command_timeout=30,  # Strict timeout
    max_inactive_connection_lifetime=300.0
)

# Use connection limiters for concurrent requests
from anyio import CapacityLimiter

db_semaphore = CapacityLimiter(20)  # Max 20 concurrent DB operations

async def safe_db_operation():
    async with db_semaphore:
        async with pool.acquire() as conn:
            # DB operation here
            pass
```

**Warning signs:**
- `asyncpg.PoolTimeout` errors
- API timeouts in logs
- Database shows many connections in "idle in transaction"

**Sources:**
- [Async Python Almost Destroyed Our API](https://python.plainenglish.io/async-python-almost-destroyed-our-api-heres-what-we-learned-c0087d564f7c) (MEDIUM confidence)
- [PostgreSQL Connection Limits: Performance Optimization](https://rizqimulki.com/postgresql-connection-limits-performance-optimization-for-ai-microservices-0847ebb4d8b1) (MEDIUM confidence)

## Code Examples

### CCXT Async OHLCV Fetching

```python
# Source: CCXT Official Documentation
import ccxt.async_support as ccxt
import asyncio

async def fetch_multi_exchange_ohlcv(symbol: str):
    """Fetch OHLCV from multiple exchanges concurrently"""

    exchanges = ['binance', 'coinbase', 'kraken', 'okx', 'bybit']

    async def fetch_from_exchange(exchange_id: str):
        exchange = getattr(ccxt, exchange_id)()
        try:
            # Enable rate limiting
            exchange.enableRateLimit = True

            # Fetch OHLCV
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='1d')
            return {exchange_id: ohlcv}
        finally:
            await exchange.close()

    # Fetch from all exchanges concurrently
    results = await asyncio.gather(
        *[fetch_from_exchange(e) for e in exchanges],
        return_exceptions=True
    )

    # Merge results
    all_data = {}
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Fetch failed: {result}")
        else:
            all_data.update(result)

    return all_data
```

### Tenacity Retry with Exponential Backoff

```python
# Source: Tenacity Official Documentation
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    retry_if_exception_type
)
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    retry=retry_if_exception_type((ccxt.NetworkError, ccxt.ExchangeError))
)
async def resilient_fetch_ohlcv(exchange, symbol: str):
    """Fetch OHLCV with automatic retry and logging"""
    return await exchange.fetch_ohlcv(symbol, timeframe='1d')
```

### Data Validation with Pydantic

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime

class OHLCVData(BaseModel):
    timestamp: int
    symbol: str
    exchange: str
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)

    @validator('high')
    def high_must_be_gte_low(cls, v, values):
        if 'low' in values and v < values['low']:
            raise ValueError('high must be >= low')
        return v

    @validator('low')
    def low_must_be_lte_high(cls, v, values):
        if 'high' in values and v > values['high']:
            raise ValueError('low must be <= high')
        return v

    @validator('open', 'close')
    def price_within_range(cls, v, values):
        if 'high' in values and 'low' in values:
            if not (values['low'] <= v <= values['high']):
                raise ValueError('price must be between low and high')
        return v

# Usage
try:
    ohlcv = OHLCVData(
        timestamp=1640995200000,
        symbol='BTC/USDT',
        exchange='binance',
        open=47000.0,
        high=48000.0,
        low=46500.0,
        close=47500.0,
        volume=1234.56
    )
except ValidationError as e:
    logger.error(f"Invalid OHLCV data: {e}")
```

### Gap Detection Query

```python
async def detect_missing_candles(pool, symbol: str, timeframe: str):
    """Detect gaps in OHLCV data using TimescaleDB"""

    # Generate expected time series
    async with pool.acquire() as conn:
        # For daily candles
        if timeframe == '1d':
            query = """
                WITH expected_times AS (
                    SELECT generate_series(
                        (SELECT MIN(time) FROM ohlcv WHERE symbol = $1),
                        (SELECT MAX(time) FROM ohlcv WHERE symbol = $1),
                        INTERVAL '1 day'
                    ) AS time
                ),
                actual_times AS (
                    SELECT DISTINCT time FROM ohlcv WHERE symbol = $1
                )
                SELECT expected_times.time
                FROM expected_times
                LEFT JOIN actual_times ON expected_times.time = actual_times.time
                WHERE actual_times.time IS NULL
                ORDER BY expected_times.time;
            """

            gaps = await conn.fetch(query, symbol)

            if gaps:
                logger.warning(f"Found {len(gaps)} missing candles for {symbol}")
                for gap in gaps:
                    logger.info(f"Missing candle at: {gap['time']}")

            return len(gaps)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| **Synchronous CCXT** | **ccxt.async_support** | CCXT 1.20+ (2020) | 10-100x throughput improvement for multi-exchange fetching |
| **Custom retry loops** | **Tenacity decorators** | 2018+ | Cleaner code, better error handling, exponential backoff built-in |
| **Manual table partitioning** | **TimescaleDB hypertables** | 2017+ | Automatic partitioning, 83% compression, continuous aggregates |
| **psycopg2 (sync)** | **asyncpg (async)** | 2016+ | 2-3x faster, native async support, connection pooling |
| **Threading for concurrency** | **asyncio + await** | Python 3.5+ | Lower overhead, better scalability for I/O-bound tasks |

**Deprecated/outdated:**
- **ccxt synchronous module in async context:** Use `ccxt.async_support` exclusively
- **retrying library:** Replaced by tenacity (no longer maintained)
- **aioredis:** Merged into redis-py 4.2+, use `from redis import asyncio as aioredis`
- **Custom rate limiters:** CCXT built-in rate limiting is production-proven

## Open Questions

### 1. Optimal Backfill Batch Size

**What we know:**
- CCXT typically returns 500-1000 candles per request
- Smaller batches = more API calls (rate limit risk)
- Larger batches = more data lost on failure

**What's unclear:**
- Optimal batch size for different exchanges
- Whether batch size affects API rate limit calculation

**Recommendation:**
Start with 500 candles per batch (conservative), monitor rate limit headers, adjust per exchange based on behavior.

### 2. Multi-Exchange Data Merging Strategy

**What we know:**
- Each exchange has slightly different OHLCV timestamps
- Need to merge data from multiple exchanges for redundancy

**What's unclear:**
- Whether to merge at candle level or use primary/secondary exchanges
- How to handle price discrepancies between exchanges

**Recommendation:**
Store per-exchange data separately (as planned), implement merging at query time using weighted averages or primary exchange selection in Phase 2.

### 3. Compression Timing for Real-Time Data

**What we know:**
- TimescaleDB compression works best on older, static data
- Compression can be scheduled via compression policies

**What's unclear:**
- Optimal compression interval for real-time vs historical data
- Performance impact of compressing recent data

**Recommendation:**
Use 7-day compression interval (compress data older than 7 days), monitor query performance, adjust based on workload patterns.

## Sources

### Primary (HIGH confidence)
- [CCXT Official Documentation](https://docs.ccxt.com/en/latest/) - Complete API reference, async support, rate limiting
- [Tenacity Documentation](https://tenacity.readthedocs.io/en/latest/) - Retry patterns, exponential backoff, async support
- [TimescaleDB Documentation](https://docs.timescale.com/) - Hypertables, compression, continuous aggregates
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/current/usage.html) - Connection pooling, async operations

### Secondary (MEDIUM confidence)
- [Binance: How to Avoid Getting Banned by Rate Limits](https://www.binance.com/en/academy/articles/how-to-avoid-getting-banned-by-rate-limits) - Rate limit best practices
- [CoinAPI: Backtest with Real Market Data](https://www.coinapi.io/blog/backtest-crypto-strategies-with-real-market-data) - Data gap handling
- [My experience with timescaledb Compression](https://mail-dpant.medium.com/my-experience-with-timescaledb-compression-68405425827) - Compression pitfalls
- [Job Scheduling in Python with APScheduler](https://betterstack.com/community/guides/scaling-python/apscheduler-scheduled-tasks/) - APScheduler patterns
- [Boost Your App Performance With Asyncpg and PostgreSQL](https://www.tigerdata.com/blog/how-to-build-applications-with-asyncpg-and-postgresql) - asyncpg best practices
- [How to Organize Crypto OHLCV Data + 190 Indicators](https://forum.tigerdata.com/forum/t/how-to-organize-crypto-ohlcv-data-190-indicators-across-all-timeframes/3003) - Schema design
- [Async Python Almost Destroyed Our API](https://python.plainenglish.io/async-python-almost-destroyed-our-api-heres-what-we-learned-c0087d564f7c) - Connection pool issues

### Tertiary (LOW confidence)
- [Building an Enterprise-Grade Crypto Data Pipeline](https://www.linkedin.com/pulse/building-enterprise-grade-crypto-data-pipeline-from-api-mujtaba-adil-xgmvf) - ETL patterns
- Various Medium articles on CCXT usage (cross-referenced with official docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All technologies are industry standards with official documentation
- Architecture: HIGH - Patterns based on official documentation and proven implementations
- Pitfalls: MEDIUM - Some pitfalls verified with official sources, others from community experience

**Research date:** 2026-01-18
**Valid until:** 2026-02-18 (30 days - libraries are stable, but verify before implementation)
