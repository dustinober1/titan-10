# Titan-10 Design Document

**Date**: 2025-01-18
**Purpose**: Research Platform for backtesting strategies and analyzing market patterns
**Tech Stack**: Python 3.11, uv, Docker, PostgreSQL 16 + TimescaleDB, Redis, FastAPI

---

## Architecture Overview

Titan-10 will be a monolithic Python application deployed via Docker Compose, consisting of:

**Core Application Container** (`titan-api`):
- FastAPI application serving both the API and background tasks
- Four logical modules (not separate services):
  - **Ingestor** (`src/ingestor`): CCXT-based data fetching with exponential backoff
  - **Quant** (`src/quant`): pandas-ta analysis engine
  - **Gateway** (`src/api`): FastAPI endpoints with Pydantic V2
  - **Shared** (`src/shared`): Database models, utilities, configuration

**Infrastructure Containers**:
- **PostgreSQL + TimescaleDB**: Time-series data storage with hypertables
- **Redis**: Caching layer for API responses (60s TTL)
- **nginx** (optional): Reverse proxy for production

**Key Architectural Decisions**:
- Single codebase simplifies refactoring analysis logic
- Background tasks use FastAPI's `BackgroundTasks` or separate async loop
- Database triggers could fire analysis, but for a monolith, an async scheduler is simpler
- All containers in one `docker-compose.yml` for single-command startup

---

## Project Structure

```
titan-10/
├── docker/
│   ├── postgresql.conf          # TimescaleDB tuning
│   └── init.sql                  # Hypertable creation
├── src/
│   ├── ingestor/
│   │   ├── __init__.py
│   │   ├── ccxt_client.py        # ExchangeInterface class
│   │   └── backfill.py           # BackfillWorker
│   ├── quant/
│   │   ├── __init__.py
│   │   ├── analysis.py           # AnalysisService
│   │   └── indicators.py         # Custom metrics (volatility, z-score)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app
│   │   ├── routes/
│   │   │   ├── summary.py
│   │   │   ├── deep_dive.py
│   │   │   └── correlation.py
│   │   └── schemas.py            # Pydantic V2 models
│   └── shared/
│       ├── __init__.py
│       ├── database.py           # SQLAlchemy async setup
│       ├── models.py             # ORM models
│       ├── config.py             # Settings (Pydantic Settings)
│       └── redis.py              # Redis client
├── tests/
│   ├── unit/                     # pytest unit tests
│   ├── integration/              # testcontainers tests
│   └── fixtures/                 # Sample data
├── pyproject.toml                # uv configuration
├── docker-compose.yml
└── README.md
```

**Module Contracts**:
- `Ingestor` → writes to `raw_market_data` only
- `Quant` → reads from `raw_market_data`, writes to `computed_metrics`
- `Gateway` → reads only, never writes
- `Shared` → no circular imports, all models point here

---

## Database Schema (TimescaleDB)

```sql
-- Raw market data hypertable
CREATE TABLE raw_market_data (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (time, symbol)
);

SELECT create_hypertable('raw_market_data', 'time',
    partitioning_column => 'symbol',
    number_partitions => 4);

-- Computed metrics hypertable
CREATE TABLE computed_metrics (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    rsi_14 DOUBLE PRECISION,
    macd_line DOUBLE PRECISION,
    macd_signal DOUBLE PRECISION,
    volatility_30d DOUBLE PRECISION,
    z_score DOUBLE PRECISION,
    PRIMARY KEY (time, symbol)
);

SELECT create_hypertable('computed_metrics', 'time');

-- Critical indexes for query performance
CREATE INDEX idx_raw_symbol_time ON raw_market_data (symbol, time DESC);
CREATE INDEX idx_raw_time_range ON raw_market_data (time DESC);
CREATE INDEX idx_comp_symbol_time ON computed_metrics (symbol, time DESC);
```

**TimescaleDB-Specific Optimizations**:
- `chunk_time_interval`: Set to 1 day for efficient partitioning
- `compression`: Enable on `raw_market_data` for data older than 30 days
- `continuous aggregates`: Pre-compute daily OHLCV from 1-minute data

---

## Data Flow & Execution Model

**Startup Flow**:
1. Containers start (API → waits for Postgres → waits for Redis)
2. API connects to DB, runs migrations (Alembic)
3. `BackfillWorker` checks for gaps in `raw_market_data`
4. If gap > 1 day, fetch historical data from CCXT in batches
5. Once backfill complete, start real-time polling (60s interval)

**Runtime Loop**:
```
Every 60 seconds:
┌─────────────────────────────────────────────────────────────┐
│ 1. Ingestor.fetch_latest()                                  │
│    ├─ CCXT fetch_ohlcv (top 20 symbols)                     │
│    └─ Bulk insert to raw_market_data                        │
│                                                             │
│ 2. Quant.analyze_new_data() [triggered by insert]           │
│    ├─ pandas-ta: RSI, MACD, Bollinger Bands                │
│    ├─ Custom: Volatility (30d rolling std), Z-score        │
│    └─ Insert to computed_metrics                            │
│                                                             │
│ 3. Gateway [API Layer]                                      │
│    ├─ GET /v1/summary/{symbol} → Redis cache (60s TTL)     │
│    ├─ GET /v1/deep-dive/{symbol} → Redis cache (60s TTL)   │
│    └─ GET /v1/reports/correlation → Computed on-demand     │
└─────────────────────────────────────────────────────────────┘
```

**Error Handling**:
- CCXT 429 errors → Exponential backoff (1s → 2s → 4s → 8s, max 60s)
- Exchange disconnect → Log alert, retry after 30s
- DB connection loss → SQLAlchemy pool pre-ping, auto-reconnect
- Analysis failure → Log error, don't block ingestion (raw data still saved)

---

## Testing Strategy

**Unit Tests** (`pytest`, `tests/unit/`):
- Mock CCXT responses, test retry logic on 429 errors
- Test analysis functions with static price arrays
- Verify Pydantic schemas serialize/deserialize correctly
- Run on every commit: `uv run pytest tests/unit/`

**Integration Tests** (`testcontainers`, `tests/integration/`):
- Spin up real PostgreSQL + TimescaleDB container
- Insert raw data, trigger analysis, assert computed_metrics rows
- Test API endpoints with TestClient
- Run before merge: `uv run pytest tests/integration/`

**Performance Tests** (optional):
- Benchmark CCXT fetch latency
- Verify API response time < 100ms (cached)
- Load test correlation endpoint with 20 symbols

**Quality Gates**:
```bash
# Pre-commit hooks (via pre-commit)
- ruff check --fix              # Linting
- ruff format --check           # Formatting
- mypy src/                     # Type checking (strict mode)

# CI/CD pipeline
- pytest tests/unit/            # Fast feedback
- pytest tests/integration/     # Slower, real DB
- coverage report --fail-under 80
```

---

## Docker Configuration

**docker-compose.yml**:
```yaml
services:
  titan-api:
    build: .
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    ports:
      - "8000:8000"
    volumes:
      - ./src:/app/src

  postgres:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_DB: titan10
      POSTGRES_USER: titan
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/home/postgres/pgdata/data
      - ./docker/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U titan"]
      interval: 5s

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

volumes:
  postgres_data:
```

**Single-Command Startup**:
```bash
# First time setup
cp .env.example .env
docker compose up -d

# Run migrations
docker compose exec titan-api alembic upgrade head
```

**Key Points**:
- Hot-reload in development via volume mount
- Health checks prevent race conditions
- Redis memory-limited to prevent bloat
- PostgreSQL data persists across restarts

---

## API Endpoints

**GET /v1/summary/{symbol}**
- Current price + daily % change
- Cached for 60s

**GET /v1/deep-dive/{symbol}**
- RSI, MACD, Volatility, Z-score
- Squeeze detection (Bollinger Band Width < 5th percentile)
- Cached for 60s

**GET /v1/reports/correlation**
- Heatmap matrix of top 20 assets
- Computed on-demand (no cache)
