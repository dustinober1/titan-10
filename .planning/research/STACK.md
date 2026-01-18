# Technology Stack

**Project:** Titan-10 - Cryptocurrency Quantitative Research Engine
**Researched:** 2025-01-18
**Overall Confidence:** HIGH

## Executive Summary

The recommended stack for Titan-10 prioritizes **reliability, async performance, and autonomous operation**. All choices are production-proven in 2025 with active maintenance and strong communities. The stack leverages Python's async ecosystem to handle concurrent data ingestion from multiple exchanges while maintaining sub-100ms API response times through intelligent caching.

---

## Core Libraries

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Python** | 3.11+ | Runtime | Project constraint, excellent async support, stable |
| **uv** | Latest | Dependency Manager | **10-100x faster** than Poetry/pip, modern locking, required by project |
| **pydantic** | 2.0+ | Data Validation | Type-safe config, automatic validation, FastAPI integration |
| **pydantic-settings** | 2.0+ | Settings Management | Environment variable loading, validation, secrets management |

**Confidence:** HIGH

**Rationale:**
- Python 3.11 provides significant performance improvements over 3.10 (up to 60% faster)
- Pydantic v2 is **5-50x faster** than v1 with critical bug fixes
- uv is the modern standard for Python dependency management (orders of magnitude faster than pip)

---

## Data Ingestion

| Technology | Version | Purpose | When to Use |
|------------|---------|---------|-------------|
| **CCXT** | 4.5+ | Exchange Connectivity | **PRIMARY** - Unified API across 100+ exchanges, async support, rate limiting built-in |
| **ccxt.async_support** | 4.5+ | Async Exchange Operations | **REQUIRED** - Concurrent data fetching from multiple exchanges |
| **orjson** | Latest | JSON Parsing (Optional) | High-performance JSON parsing for WebSocket streams |

**Confidence:** HIGH

**Rationale:**
- **CCXT is the de facto standard** for cryptocurrency exchange connectivity with 40.5k+ GitHub stars
- Supports 108 exchanges with unified API, eliminating vendor lock-in
- **Built-in rate limiting** prevents exchange API bans (leaky bucket and rolling window algorithms)
- Async support critical for fetching from 20 exchanges concurrently
- **orjson** provides 2-3x faster JSON parsing for high-volume WebSocket data (optional optimization)

**Why NOT alternatives:**
- **Exchange-specific APIs** (Binance, Coinbase): Creates 20x integration complexity, no unified data structure
- **Vezgo**: Paid service, adds dependency on third-party, CCXT is free and open-source
- **Custom implementations**: Reinventing the wheel, maintenance burden, exchange API changes handled by CCXT maintainers

---

## Analysis & Computation

| Technology | Version | Purpose | When to Use |
|------------|---------|---------|-------------|
| **pandas** | 2.0+ | Data Manipulation | **REQUIRED** - Foundation for time-series analysis |
| **numpy** | Latest | Numerical Computing | **REQUIRED** - Performance-critical calculations |
| **pandas-ta** | 0.3.14b+ | Technical Indicators | **PRIMARY** - 130+ indicators, native pandas integration, easy to use |
| **TA-Lib** | 0.6.8+ | Advanced Indicators | **OPTIONAL** - 150+ indicators, candlestick patterns, faster C-based calculations |
| **scipy** | Latest | Statistical Analysis | **REQUIRED** - Volatility, Z-Score, Correlation calculations |
| **statsmodels** | Latest | Advanced Statistics | **OPTIONAL** - Time-series analysis, regression if needed |

**Confidence:** HIGH for pandas-ta, MEDIUM for TA-Lib

**Rationale:**
- **pandas-ta** recommended as primary library:
  - Native pandas DataFrame extension (`df.ta.rsi()`)
  - 130+ indicators including modern ones (VWAP, Keltner Channels)
  - No C dependency hell (pure Python)
  - Easy to extend with custom indicators
  - Multiprocessing support for bulk indicator computation

- **TA-Lib** as optional enhancement:
  - **2-4x faster** than pandas-ta (C-based calculations)
  - Superior candlestick pattern recognition (63 patterns)
  - Industry standard since 1999
  - Installation challenges on some platforms (requires C library compilation)
  - Use both: pandas-ta for ease of use, TA-Lib for performance-critical paths

**Performance Comparison (2025 benchmarks):**
- TA-Lib: **100-200µs** per indicator call (C-based)
- pandas-ta: **200-500µs** per indicator call (Python-based)
- For MVP: pandas-ta is sufficient and easier to implement

**Why NOT alternatives:**
- **TA (ta-lib)**: Same as TA-Lib, just different package name
- **纯手工实现**: Unnecessary complexity, maintenance burden, well-tested libraries exist

---

## API Layer

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **FastAPI** | 0.110+ | REST API Framework | **3x faster** than Flask, native async, automatic OpenAPI docs, 2025 standard |
| **uvicorn** | Latest | ASGI Server | Production-grade async server, recommended by FastAPI |
| **pydantic** | 2.0+ | Request/Response Validation | Automatic validation, type safety, integrated with FastAPI |

**Confidence:** HIGH

**Rationale:**
- **FastAPI is the dominant Python framework in 2025** (most popular per JetBrains PyCharm blog)
- Can achieve **10,000+ RPS** with proper optimization
- Automatic OpenAPI documentation (no manual API doc maintenance)
- Native async support critical for concurrent data fetching
- Pydantic integration provides **automatic request validation**

**Why NOT alternatives:**
- **Flask**: 3x slower, no native async (requires Flask 2.0+), manual API docs
- **Django**: Overkill for API-only project, ORM not needed, heavier footprint
- **Starlette**: Too low-level, FastAPI built on Starlette with better DX

---

## Database & Caching

### PostgreSQL + TimescaleDB

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **PostgreSQL** | 16 | Primary Database | Project constraint, ACID compliance, reliability |
| **TimescaleDB** | Latest (2.15+) | Time-Series Extension | **83% storage compression**, hypertables, continuous aggregates, automatic partitioning |
| **asyncpg** | Latest | Async PostgreSQL Client | **Fastest** async PostgreSQL driver, connection pooling, prepared statements |

**Confidence:** HIGH

**Rationale:**
- **TimescaleDB is the standard for PostgreSQL time-series data** in 2025
- **83% storage compression** through columnar compression (critical for 5 years of historical data)
- **Hypertables** automatically partition data by time (no manual maintenance)
- **Continuous aggregates** pre-compute common queries (massive performance boost)
- **Asyncpg is 2-3x faster** than psycopg2 with async support
- Connection pooling built-in (no external pool manager needed)

**Best Practices (2025):**
- Always use time bounds in queries (leverage hypertable partitioning)
- Use appropriate aggregate granularity (don't fetch tick-by-tick for daily charts)
- Leverage **SkipScan** for DISTINCT queries
- Enable compression for historical data

### Redis

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **redis-py** | 4.2+ (built-in async) | Response Caching | **Sub-100ms response times**, built-in async support (no separate aioredis package) |
| **redis** | 7.0+ | Cache Server | In-memory storage, TTL support, atomic operations |

**Confidence:** HIGH

**Rationale:**
- **aioredis merged into redis-py 4.2+** - no separate package needed
- Use `from redis import asyncio as aioredis` for async operations
- **Sub-millisecond response times** for cached indicator calculations
- TTL support for automatic cache invalidation
- Atomic operations prevent race conditions

**Critical for < 100ms API requirement:**
- Cache computed indicators (RSI, MACD, Bollinger Bands) with 60s TTL
- Cache symbol lists with 300s TTL
- Cache exchange metadata with 3600s TTL

---

## Task Scheduling & Async Orchestration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **APScheduler** | 3.10+ | Job Scheduling | **AsyncIOScheduler** for cron-like scheduling, battle-tested, async function support |
| **asyncio** | Built-in | Concurrent I/O | **Mandatory** for modern trading bots, efficient handling of I/O-bound tasks |

**Confidence:** HIGH

**Rationale:**
- **APScheduler with AsyncIOScheduler** allows scheduling async functions directly
- Cron-like syntax for periodic tasks (e.g., fetch OHLCV every 60 seconds)
- **asyncio** is fundamental to concurrent exchange polling
- Avoids threading overhead (asyncio is lighter for I/O-bound tasks)

**Scheduled Tasks:**
1. **Real-time ingestion**: Every 60s (cron: `* * * * *`)
2. **Historical backfill**: Daily at 2 AM UTC (cron: `0 2 * * *`)
3. **Cache warming**: Every 30s (cron: `*/30 * * * * *`)
4. **Health checks**: Every 30s (cron: `*/30 * * * * *`)

---

## Reliability & Error Handling

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **tenacity** | 4.4.0+ | Retry Logic | **Exponential backoff**, automatic retries, decorator-based, production-proven |
| **logging** | Built-in | Structured Logging | Python stdlib, JSON formatting for log aggregation |
| **structlog** | Latest | Structured Logging (Optional) | Better DX than stdlib logging, JSON output, context binding |

**Confidence:** HIGH

**Rationale:**
- **Tenacity is the standard for retry logic** in Python 2025
- Exponential backoff prevents overwhelming exchange APIs during outages
- Decorator-based API (`@retry`) is clean and maintainable
- **Critical for autonomous operation**: automatic recovery from network issues

**Example:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=60)
)
async def fetch_ohlcv(symbol: str):
    # CCXT fetch with automatic retry
    pass
```

**Why NOT alternatives:**
- **Custom retry logic**: Error-prone, reinventing the wheel
- **backoff library**: Less feature-rich than tenacity

---

## Monitoring & Observability

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **prometheus-fastapi-instrumentator** | Latest | Metrics Collection | **Official** FastAPI integration, automatic HTTP metrics |
| **Prometheus** | Latest | Metrics Storage | Industry standard, time-series metrics, alerting |
| **Grafana** | Latest | Visualization | Dashboards, alerting, Prometheus integration |

**Confidence:** HIGH

**Rationale:**
- **prometheus-fastapi-instrumentator** is the official package for FastAPI metrics
- Automatic collection of request count, latency, errors
- **Critical for autonomous systems**: detect issues before they become outages
- Prometheus + Grafana is the industry-standard stack

**Key Metrics to Track:**
1. **API response times** (p50, p95, p99)
2. **Cache hit rates** (target: > 90%)
3. **Exchange API errors** (rate limits, timeouts)
4. **Database query performance**
5. **Data freshness** (last successful fetch time)

**Why NOT alternatives:**
- **Datadog/New Relic**: Expensive, overkill for single-project deployment
- **CloudWatch**: AWS-specific, vendor lock-in

---

## What We're NOT Using (and Why)

### Message Queues (Kafka, RabbitMQ)

**Why NOT for v1:**
- **Overkill for single-server deployment**: Titan-10 is monolithic (per project constraints)
- **Operational complexity**: Requires additional infrastructure, monitoring, maintenance
- **Unnecessary latency**: Direct function calls are faster than queue-based messaging
- **Project scope**: Single research tool, not distributed system

**When to consider (v2+):**
- Scaling to multiple servers
- Need for reliable message delivery guarantees
- Complex event-driven workflows

### Stream Processing (Spark, Flink)

**Why NOT for v1:**
- **Overkill for 20 exchanges**: Volume is manageable with asyncio + CCXT
- **Operational complexity**: Requires cluster management, resource allocation
- **Project scope**: Research platform, not real-time trading execution
- **Latency**: Batch processing adds latency unacceptable for real-time analysis

**When to consider (v2+):**
- Processing 100+ exchanges
- Complex multi-exchange arbitrage strategies
- Machine learning model serving on streaming data

### ORM (SQLAlchemy, Django ORM)

**Why NOT:**
- **Unnecessary abstraction**: Direct SQL with asyncpg is simpler and faster
- **Performance overhead**: ORM adds query building overhead
- **Project scope**: Simple schema (3 tables), no complex relationships
- **Type safety**: Pydantic provides validation without ORM overhead

**When to consider (v2+):**
- Complex multi-table relationships
- Need for database-agnostic queries
- Large team with varying SQL expertise

### WebSocket Servers (socket.io, websockets)

**Why NOT for v1:**
- **Project constraint**: API-only, consumers build their own frontends
- **REST is sufficient**: Polling every 60s doesn't require real-time push
- **Complexity**: WebSocket state management adds operational burden

**When to consider (v2+):**
- Real-time UI requirements
- Sub-second data freshness requirements
- Push notifications for critical alerts

---

## Installation

```bash
# Core dependencies (managed by uv)
uv add pandas numpy scipy pydantic pydantic-settings

# Data ingestion
uv add ccxt>=4.5
uv add orjson  # Optional: for WebSocket performance

# Analysis
uv add pandas-ta>=0.3.14b
# TA-Lib requires system library installation
# macOS: brew install ta-lib
# Ubuntu: sudo apt-get install libta-lib-dev
# Then: uv add ta-lib

# API
uv add fastapi uvicorn[standard]

# Database
uv add asyncpg
# TimescaleDB is a PostgreSQL extension, installed via package manager
# Docker: timescale/timescaledb:latest-pg16

# Caching
uv add redis>=4.2

# Task scheduling
uv add apscheduler

# Reliability
uv add tenacity

# Monitoring
uv add prometheus-fastapi-instrumentator

# Development
uv add -D pytest pytest-asyncio ruff mypy
```

---

## Docker Compose Stack

```yaml
services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_DB: titan10
      POSTGRES_USER: titan10
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  titan10:
    build: .
    environment:
      DATABASE_URL: postgresql://titan10:${POSTGRES_PASSWORD}@postgres/titan10
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
```

---

## Sources

### Primary Sources (HIGH Confidence)
- [CCXT GitHub Repository](https://github.com/ccxt/ccxt) - Official CCXT library with 40.5k+ stars
- [pandas-ta GitHub Repository](https://github.com/twopirllc/pandas-ta) - Official pandas-ta documentation
- [TA-Lib GitHub Repository](https://github.com/TA-Lib/ta-lib-python) - Official TA-Lib Python wrapper
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/) - Official asyncpg documentation
- [TimescaleDB Documentation](https://docs.timescale.com/) - Official TimescaleDB documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Official FastAPI documentation
- [Pydantic Documentation](https://docs.pydantic.dev/) - Official Pydantic v2 documentation

### Secondary Sources (MEDIUM Confidence)
- [The Ultimate Python Quantitative Trading Ecosystem 2025](https://medium.com/@mahmoud.abdou2002/the-ultimate-python-quantitative-trading-ecosystem-2025-guide-074c480bce2e)
- [Asynchronous Python Postgres Drivers: A Deep Dive](https://leapcell.io/blog/asynchronous-python-postgres-drivers-a-deep-dive-into-performance-features-and-usability)
- [Python in the Backend in 2025: Asyncio and FastAPI](https://www.nucamp.co/blog/coding-bootcamp-backend-with-python-2025-python-in-the-backend-in-2025-leveraging-asyncio-and-fastapi-for-highperformance-systems)
- [Building Real-Time Solana DEX Analytics with TimescaleDB](https://medium.com/@rakesh.therani/building-real-time-solana-dex-analytics-with-timescaledb-2a7d75d89ecb)
- [Job Scheduling in Python with APScheduler](https://betterstack.com/community/guides/scaling-python/apscheduler-scheduled-tasks/)

### Tertiary Sources (LOW Confidence - WebSearch Only)
- Various comparison articles and blog posts (cross-referenced with official documentation)
