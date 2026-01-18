# ROADMAP.md

> **Current Phase**: Not started
> **Milestone**: v1.0 (Foundation & Pipeline)

## Must-Haves (from SPEC)
- [ ] Reliable Data Ingestion (Real-time & Historical)
- [ ] Advanced Technical & Statistical Analysis
- [ ] High-Performance API (<100ms)

## Phases

### Phase 1: Foundation
**Status**: ✅ Complete
**Objective**: Setup core infrastructure, database, and dependency management.
**Requirements**: REQ-06, REQ-11 (Framework)
**Tasks**:
- [x] Initialize Git with poetry/uv
- [x] Configure docker-compose (Postgres + TimescaleDB)
- [x] Create database connection & SQLAlchemy async engine

### Phase 2: The Data Pipeline
**Status**: ✅ Complete
**Objective**: Implement resilient data fetching and storage.
**Requirements**: REQ-01, REQ-02, REQ-03, REQ-06
**Tasks**:
- [x] Implement CCXT fetcher (BTC/USDT)
- [x] Create DB migrations for `raw_market_data`
- [x] Write Integration Tests (Fetch -> DB -> Read)

### Phase 3: The Math
**Status**: ✅ Complete
**Objective**: Implement analytical engine and statistical metrics.
**Requirements**: REQ-04, REQ-05
**Tasks**:
- [x] Implement AnalysisService (pandas-ta)
- [x] Create `computed_metrics` table
- [x] Implement Math Unit Tests
- [x] Wire up event-driven analysis trigger

### Phase 4: The API & Polish
**Status**: 🚧 Next
**Objective**: Expose data via high-performance API.
**Requirements**: REQ-07, REQ-08, REQ-09, REQ-10
**Tasks**:
- [ ] Build FastAPI endpoints (Summary, Deep-Dive, Correlation)
- [ ] Add Swagger Documentation
- [ ] Implement Redis Caching
