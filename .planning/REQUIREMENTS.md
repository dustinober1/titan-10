# Requirements: Titan-10

**Defined:** 2025-01-18
**Core Value:** The system must autonomously ingest, analyze, and serve cryptocurrency market data without human intervention.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Data Management

- [ ] **DATA-01**: System fetches real-time OHLCV data from top 20 cryptocurrencies via CCXT
- [ ] **DATA-02**: System implements multi-exchange redundancy for data sources
- [ ] **DATA-03**: System stores raw and computed data in TimescaleDB hypertables
- [ ] **DATA-04**: System validates and normalizes all incoming data (OHLCV constraints, duplicate detection)
- [ ] **DATA-05**: System backfills 5 years of historical data on startup (daily candles)
- [ ] **DATA-06**: System detects and reports data gaps in historical archive
- [ ] **DATA-07**: System enforces UTC timestamps across all data (timezone consistency)
- [ ] **DATA-08**: System implements exponential backoff for exchange API rate limits
- [ ] **DATA-09**: System implements circuit breakers to prevent cascade failures

### Analysis & Computation

- [ ] **ANAL-01**: System computes 20+ technical indicators (RSI, MACD, Bollinger Bands, ADX, etc.)
- [ ] **ANAL-02**: System computes custom statistical metrics (30-day volatility, Z-score, correlation matrix)
- [ ] **ANAL-03**: System prevents look-ahead bias in all indicator calculations
- [ ] **ANAL-04**: System stores computed metrics in separate TimescaleDB hypertable
- [ ] **ANAL-05**: System uses pandas-ta for technical indicator computation
- [ ] **ANAL-06**: System implements Bollinger Band squeeze detection
- [ ] **ANAL-07**: System computes performance attribution (Alpha vs Bitcoin)

### API & Operations

- [ ] **API-01**: System exposes REST API endpoints via FastAPI
- [ ] **API-02**: GET /v1/summary/{symbol} returns current price + daily % change
- [ ] **API-03**: GET /v1/deep-dive/{symbol} returns indicators + metrics + squeeze status
- [ ] **API-04**: GET /v1/reports/correlation returns correlation heatmap matrix
- [ ] **API-05**: API responses are cached in Redis with 60s TTL
- [ ] **API-06**: API achieves < 100ms response time for cached endpoints
- [ ] **API-07**: System implements health check endpoints
- [ ] **API-08**: System implements structured logging with correlation IDs
- [ ] **API-09**: System implements Prometheus metrics collection
- [ ] **API-10**: System implements Grafana dashboards for monitoring

### Autonomous Runtime

- [ ] **AUTO-01**: System auto-recovers from exchange API disconnections
- [ ] **AUTO-02**: System auto-recovers from database connection loss
- [ ] **AUTO-03**: System continues operating with partial failures (graceful degradation)
- [ ] **AUTO-04**: System implements retry logic with exponential backoff for all external API calls
- [ ] **AUTO-05**: System implements checkpoints for backfill jobs (resume on failure)
- [ ] **AUTO-06**: System validates data quality before serving to API
- [ ] **AUTO-07**: System alerts only when autonomous recovery fails

### Deployment

- [ ] **DEPL-01**: System deploys via single `docker-compose up` command
- [ ] **DEPL-02**: System includes PostgreSQL 16 + TimescaleDB container
- [ ] **DEPL-03**: System includes Redis container with memory limits
- [ ] **DEPL-04**: System implements health checks for all containers
- [ ] **DEPL-05**: System persists PostgreSQL data across container restarts

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Real-Time Features

- **REAL-01**: WebSocket streaming for real-time price updates
- **REAL-02**: Push-based architecture for live data feeds

### Advanced Analysis

- **ANAL-20**: ML-based anomaly detection
- **ANAL-21**: Multi-timeframe analysis
- **ANAL-22**: Predictive scaling indicators

### Authentication & Multi-User

- **AUTH-01**: User authentication system
- **AUTH-02**: API rate limiting per user
- **AUTH-03**: User-specific data retention policies

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Trading execution | Research platform only, not a trading bot |
| Order book data | Focus on candle/OHLCV data only for v1 |
| User authentication | Single-user research tool |
| Real-time UI | API-only, consumers build their own frontends |
| Machine learning models | Statistical analysis only for v1 |
| Multi-region deployment | Single-region deployment sufficient for MVP |
| TA-Lib integration | pandas-ta sufficient for MVP, defer performance optimization |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Pending |
| DATA-02 | Phase 1 | Pending |
| DATA-03 | Phase 1 | Pending |
| DATA-04 | Phase 1 | Pending |
| DATA-05 | Phase 1 | Pending |
| DATA-06 | Phase 1 | Pending |
| DATA-07 | Phase 1 | Pending |
| DATA-08 | Phase 1 | Pending |
| DATA-09 | Phase 1 | Pending |
| ANAL-01 | Phase 2 | Pending |
| ANAL-02 | Phase 2 | Pending |
| ANAL-03 | Phase 2 | Pending |
| ANAL-04 | Phase 2 | Pending |
| ANAL-05 | Phase 2 | Pending |
| ANAL-06 | Phase 2 | Pending |
| ANAL-07 | Phase 2 | Pending |
| API-01 | Phase 3 | Pending |
| API-02 | Phase 3 | Pending |
| API-03 | Phase 3 | Pending |
| API-04 | Phase 3 | Pending |
| API-05 | Phase 3 | Pending |
| API-06 | Phase 3 | Pending |
| AUTO-01 | Phase 1 | Pending |
| AUTO-02 | Phase 1 | Pending |
| AUTO-03 | Phase 1 | Pending |
| AUTO-04 | Phase 1 | Pending |
| AUTO-05 | Phase 1 | Pending |
| AUTO-06 | Phase 2 | Pending |
| AUTO-07 | Phase 4 | Pending |
| API-07 | Phase 4 | Pending |
| API-08 | Phase 4 | Pending |
| API-09 | Phase 4 | Pending |
| API-10 | Phase 4 | Pending |
| DEPL-01 | Phase 5 | Pending |
| DEPL-02 | Phase 5 | Pending |
| DEPL-03 | Phase 5 | Pending |
| DEPL-04 | Phase 5 | Pending |
| DEPL-05 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 35 total
- Mapped to phases: 35
- Unmapped: 0 ✓

---
*Requirements defined: 2025-01-18*
*Last updated: 2025-01-18 after initial definition*
