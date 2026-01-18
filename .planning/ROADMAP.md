# Roadmap: Titan-10

## Overview

Titan-10 delivers a cryptocurrency quantitative research engine through five incremental phases. The journey begins with building autonomous data ingestion infrastructure that survives exchange API failures and rate limits, then adds technical analysis capabilities, exposes insights via a fast REST API, instruments comprehensive monitoring, and culminates in production-ready deployment. Each phase delivers verifiable capabilities: working data pipelines, computed indicators, responsive API endpoints, operational visibility, and single-command deployment.

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation & Data Ingestion** - Autonomous data pipelines with multi-exchange redundancy
- [ ] **Phase 2: Analysis Engine** - Technical indicator computation and statistical metrics
- [ ] **Phase 3: API Layer** - Fast REST endpoints with Redis caching
- [ ] **Phase 4: Operations & Monitoring** - Observability and alerting infrastructure
- [ ] **Phase 5: Deployment & Production Readiness** - Single-command Docker deployment

## Phase Details

### Phase 1: Foundation & Data Ingestion
**Goal**: System autonomously ingests and stores cryptocurrency market data from multiple exchanges with built-in resilience to failures
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07, DATA-08, DATA-09, AUTO-01, AUTO-02, AUTO-03, AUTO-04, AUTO-05
**Success Criteria** (what must be TRUE):
  1. System starts fetching real-time OHLCV data from top 20 cryptocurrencies and persists to TimescaleDB without manual intervention
  2. System successfully backfills 5 years of historical daily candle data on first startup
  3. System automatically recovers from exchange API disconnections and rate limit errors without crashing
  4. System detects and reports data gaps in the historical archive
  5. All stored data uses UTC timestamps with normalized OHLCV constraints (no negative prices, high >= low, etc.)
**Plans**: 5 plans in 3 waves

Plans:
- [ ] 01-01-PLAN.md — Project scaffolding and TimescaleDB hypertable setup
- [ ] 01-02-PLAN.md — CCXT integration with real-time data fetching
- [ ] 01-03-PLAN.md — Historical backfill with checkpoint-based recovery
- [ ] 01-04-PLAN.md — Multi-exchange redundancy and data normalization
- [ ] 01-05-PLAN.md — Autonomous error handling with exponential backoff and circuit breakers

### Phase 2: Analysis Engine
**Goal**: System computes technical indicators and statistical metrics from stored market data
**Depends on**: Phase 1 (requires market data in TimescaleDB)
**Requirements**: ANAL-01, ANAL-02, ANAL-03, ANAL-04, ANAL-05, ANAL-06, ANAL-07, AUTO-06
**Success Criteria** (what must be TRUE):
  1. System computes 20+ technical indicators (RSI, MACD, Bollinger Bands, ADX, etc.) using pandas-ta
  2. System calculates custom statistical metrics (30-day volatility, Z-score, correlation matrix, Alpha vs Bitcoin)
  3. System detects Bollinger Band squeeze conditions and stores results
  4. All computed metrics are stored in separate TimescaleDB hypertable with proper timestamp alignment
  5. System validates data quality before computing indicators (prevents garbage-in, garbage-out)
**Plans**: TBD

Plans:
- [ ] 02-01: Technical indicator computation engine with pandas-ta
- [ ] 02-02: Statistical metrics calculation (volatility, Z-score, correlation)
- [ ] 02-03: Bollinger Band squeeze detection and performance attribution
- [ ] 02-04: Look-ahead bias prevention and data quality validation

### Phase 3: API Layer
**Goal**: System serves market data and analysis results via fast REST API with sub-100ms cached response times
**Depends on**: Phase 1 (data) and Phase 2 (analysis)
**Requirements**: API-01, API-02, API-03, API-04, API-05, API-06
**Success Criteria** (what must be TRUE):
  1. GET /v1/summary/{symbol} returns current price and daily percentage change
  2. GET /v1/deep-dive/{symbol} returns technical indicators, metrics, and squeeze status
  3. GET /v1/reports/correlation returns correlation heatmap matrix
  4. Cached API responses return in under 100ms measured from external request
  5. All responses include proper pagination, filtering, and error handling
**Plans**: TBD

Plans:
- [ ] 03-01: FastAPI application setup with Pydantic V2 validation
- [ ] 03-02: Core data endpoints (summary, deep-dive, correlation)
- [ ] 03-03: Redis caching implementation with 60s TTL
- [ ] 03-04: Performance optimization and response time validation

### Phase 4: Operations & Monitoring
**Goal**: System provides comprehensive visibility into health, performance, and operational status
**Depends on**: Phase 3 (requires API endpoints to instrument)
**Requirements**: API-07, API-08, API-09, API-10, AUTO-07
**Success Criteria** (what must be TRUE):
  1. System exposes health check endpoints that report database, cache, and exchange connectivity status
  2. System logs all operations with structured logging and correlation IDs for request tracing
  3. System publishes Prometheus metrics for data ingestion rates, API response times, and error counts
  4. Grafana dashboards display real-time system health and historical performance trends
  5. System sends alerts only when autonomous recovery fails (retries exhausted, circuit breakers open)
**Plans**: TBD

Plans:
- [ ] 04-01: Health check endpoints and structured logging
- [ ] 04-02: Prometheus metrics collection and instrumentation
- [ ] 04-03: Grafana dashboard setup and configuration
- [ ] 04-04: Alert rules for autonomous recovery failures

### Phase 5: Deployment & Production Readiness
**Goal**: System deploys to production with single command and maintains data persistence across restarts
**Depends on**: Phase 4 (requires monitoring to validate production health)
**Requirements**: DEPL-01, DEPL-02, DEPL-03, DEPL-04, DEPL-05
**Success Criteria** (what must be TRUE):
  1. System starts fully operational with single `docker-compose up` command
  2. PostgreSQL data persists across container restarts (no data loss on stop/start)
  3. All containers pass health checks before accepting traffic
  4. Redis container operates within configured memory limits
  5. System auto-initializes TimescaleDB extension and creates hypertables on first run
**Plans**: TBD

Plans:
- [ ] 05-01: Docker Compose configuration with all services
- [ ] 05-02: PostgreSQL + TimescaleDB container setup with persistent volumes
- [ ] 05-03: Redis container with memory limits and configuration
- [ ] 05-04: Health check implementation for all containers
- [ ] 05-05: Auto-initialization scripts for database schema and extensions

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Data Ingestion | 0/5 | Ready to execute | - |
| 2. Analysis Engine | 0/4 | Not started | - |
| 3. API Layer | 0/4 | Not started | - |
| 4. Operations & Monitoring | 0/4 | Not started | - |
| 5. Deployment & Production Readiness | 0/5 | Not started | - |
