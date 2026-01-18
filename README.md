# Titan-10

Autonomous cryptocurrency market data ingestion and analysis system.

## Overview

Titan-10 is a self-operating system that ingests, analyzes, and serves cryptocurrency market data without human intervention. It supports multiple exchanges, provides real-time OHLCV data storage, and offers intelligent backfill capabilities for missing data.

## Features

- **Multi-Exchange Support**: Ingest data from Binance, Coinbase, Kraken, OKX, and Bybit
- **Time-Series Optimized**: Built on TimescaleDB for efficient storage and querying of OHLCV data
- **Auto-Recovery**: Automatic database reconnection with exponential backoff retry
- **Intelligent Backfill**: Resumable backfill system with checkpoint tracking
- **Configuration-Driven**: Environment-based configuration with Pydantic validation

## Prerequisites

- **Python**: 3.11 or higher
- **PostgreSQL**: 16+ with TimescaleDB extension
- **Package Manager**: uv (recommended) or pip

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd titan-10
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials and exchange API keys
```

4. Initialize the database:
```bash
# Ensure PostgreSQL with TimescaleDB is running
psql -h localhost -U postgres -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

## Quick Start

1. Configure your `.env` file with database connection and exchange credentials

2. Run database migrations:
```bash
python -m src.storage.migrations.apply_migrations
```

3. Start data ingestion:
```bash
python -m src.ingestion.main
```

## Project Structure

```
titan-10/
├── src/
│   ├── shared/          # Configuration, types, and utilities
│   ├── storage/         # Database models, connection pool, migrations
│   └── ingestion/       # Data ingestion logic (Phase 2)
├── pyproject.toml       # Project dependencies and configuration
├── .env.example         # Environment variable template
└── README.md            # This file
```

## Configuration

Key environment variables in `.env`:

- `DATABASE_URL`: PostgreSQL connection string
- `EXCHANGE_API_KEYS`: JSON object containing exchange credentials
- `LOG_LEVEL`: Logging verbosity (INFO, DEBUG, ERROR)
- `TOP_SYMBOLS`: Comma-separated list of trading pairs to monitor

## Development

### Running Tests

```bash
uv run pytest
```

### Code Quality

```bash
# Linting
uv run ruff check src/

# Type checking
uv run mypy src/
```

## License

MIT License - see LICENSE file for details
