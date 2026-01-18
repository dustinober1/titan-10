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
**Status**: 🚧 Next
**Objective**: Implement resilient data fetching and storage.
**Requirements**: REQ-01, REQ-02, REQ-03, REQ-06
**Tasks**:
- [ ] Implement CCXT fetcher (BTC/USDT)
- [ ] Create DB migrations for `raw_market_data`
- [ ] Write Integration Tests (Fetch -> DB -> Read)

### Phase 3: The Math
**Status**: ⬜ Not Started
**Objective**: Implement analytical engine and statistical metrics.
**Requirements**: REQ-04, REQ-05
**Tasks**:
- [ ] Implement AnalysisService (pandas-ta)
- [ ] Create `computed_metrics` table
- [ ] Implement Math Unit Tests
- [ ] Wire up event-driven analysis trigger

### Phase 4: The API & Polish
**Status**: ⬜ Not Started
**Objective**: Expose data via high-performance API.
**Requirements**: REQ-07, REQ-08, REQ-09, REQ-10
**Tasks**:
- [ ] Build FastAPI endpoints (Summary, Deep-Dive, Correlation)
- [ ] Add Swagger Documentation
- [ ] Implement Redis Caching
