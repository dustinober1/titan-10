# REQUIREMENTS.md

## Format
| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| REQ-01 | Ingest real-time 1-minute OHLCV data for top 20 crypto assets | SPEC Goal 1 | Pending |
| REQ-02 | Backfill 5 years of daily historical data on startup | SPEC Goal 1 | Pending |
| REQ-03 | Resilient ingestion with Exponential Backoff for 429 errors | SPEC Constraint | Pending |
| REQ-04 | Calculate RSI, MACD, Bollinger Bands on new data arrival | SPEC Goal 2 | Pending |
| REQ-05 | Calculate Volatility, Correlation, Z-Score metrics | SPEC Goal 2 | Pending |
| REQ-06 | Store raw and derived data in TimescaleDB hypertables | SPEC Constraint | Pending |
| REQ-07 | Provide REST API for market summaries | SPEC Goal 3 | Pending |
| REQ-08 | Provide deep-dive analytics API with <100ms latency | SPEC Goal 3 | Pending |
| REQ-09 | Provide correlation matrix report API | SPEC Goal 3 | Pending |
| REQ-10 | Cache deep-dive endpoints with Redis (60s TTL) | SPEC Constraint | Pending |
| REQ-11 | 100% pass rate on Unit and Integration tests | SPEC Success Criteria | Pending |
