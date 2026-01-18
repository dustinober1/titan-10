# Titan-10

## What This Is

A cryptocurrency quantitative research engine that fetches real-time and historical market data for top 20 cryptocurrencies, computes technical indicators and custom metrics, and serves analysis via a REST API. Built as a demonstration of AI-assisted development ("vibe coding") - the entire system runs autonomously once deployed.

## Core Value

The system must autonomously ingest, analyze, and serve cryptocurrency market data without human intervention.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Data ingestion from top 20 cryptocurrencies via CCXT
- [ ] Real-time 1-minute candle polling (60s intervals)
- [ ] Historical backfill (5 years of daily data)
- [ ] Technical indicator computation (RSI, MACD, Bollinger Bands)
- [ ] Custom statistical metrics (Volatility, Z-Score, Correlation)
- [ ] REST API with < 100ms cached response time
- [ ] Automatic recovery from API rate limits and disconnects
- [ ] Docker-based deployment (single command startup)

### Out of Scope

- Trading execution — This is a research platform, not a trading bot
- User authentication — Single-user research tool
- Real-time UI — API-only, consumers build their own frontends
- Order book data — Focus on candle/OHLCV data only
- Machine learning models — Statistical analysis only for v1

## Context

**Primary Purpose:** Demonstration project showing what's possible with AI-assisted software development. The goal is to build a complete, functional quantitative research system with minimal manual coding intervention.

**Technical Environment:**
- Python 3.11 with uv dependency manager
- PostgreSQL 16 + TimescaleDB for time-series data
- Redis for response caching
- Docker Compose for deployment
- FastAPI for API layer

**Prior Work:**
- Design document exists at `docs/plans/2025-01-18-titan-10-design.md`
- Architecture already specified (monolithic with 4 logical modules)
- Database schema designed (TimescaleDB hypertables)

**Known Constraints:**
- Exchange API rate limits require exponential backoff
- Historical backfill must be resilient to partial failures
- System must auto-recover from network issues

## Constraints

- **Tech Stack**: Python 3.11, uv, Docker, PostgreSQL 16 + TimescaleDB, Redis, FastAPI — Chosen for modern, fast development workflow
- **Deployment**: Pure Docker Compose — Must start with single command
- **Architecture**: Monolithic — Simpler for AI-assisted development, easier to reason about
- **Latency**: API response < 100ms (cached) — Required for usable research tool
- **Reliability**: Auto-recovery from failures — System runs autonomously without human intervention

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Monolithic architecture | Simplifies AI-assisted development, easier to reason about for research platform | — Pending |
| uv over Poetry | Modern, much faster dependency resolution | — Pending |
| TimescaleDB over Redis-only | Proper time-series database with compression and continuous aggregates | — Pending |
| CCXT for data sources | Unified API across 100+ exchanges, async support | — Pending |

---
*Last updated: 2025-01-18 after initialization*
