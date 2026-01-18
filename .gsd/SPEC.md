# SPEC.md — Project Specification

> **Status**: `FINALIZED`

## Vision
A robust, autonomous cryptocurrency quantitative engine (Titan-10) that ingests real-time and historical data from top 20 assets, applies sophisticated technical and statistical analysis, and exposes derived metrics via a high-performance API. The system serves as the foundational data and analytics layer for quantitative strategies and frontend dashboards.

## Goals
1.  **Reliable Data Ingestion**: Fetch real-time (1-min candles) and backfill (5-year daily) OHLCV data for top 20 cryptocurrencies with resilience against rate limits and disconnects.
2.  **Advanced Analytics**: Automatically calculate technical indicators (RSI, MACD, Bollinger Bands) and statistical metrics (Z-Score, Volatility, Correlation) upon data arrival.
3.  **High-Performance API**: Provide a low-latency (<100ms) REST API for consuming market summaries, deep-dive analytics, and correlation reports.

## Non-Goals (Out of Scope)
-   **Trade Execution**: The system will not place or manage orders on exchanges.
-   **Frontend UI**: Scope is limited to the Backend/API layer; no graphical user interface will be built.
-   **User Management**: No authentication or multi-user support in the initial version.

## Users
-   **Quantitative Analysts**: Using historical and derived data for strategy backtesting.
-   **Frontend Applications**: Consuming real-time analytics for visualization (e.g., dashboards).

## Constraints
-   **Latency**: API response time < 100ms for cached analysis endpoints.
-   **Stability**: Must auto-recover from websocket disconnects and API 429 rate limits (Exponential Backoff).
-   **Tech Stack**:
    -   *Runtime*: Python 3.11+
    -   *Database*: PostgreSQL 16 + TimescaleDB
    -   *API*: FastAPI + Redis
    -   *Analysis*: pandas-ta
-   **Granularity**: 1-minute candles for real-time; Daily for historical.

## Success Criteria
-   [ ] **Backfill**: System automatically fills 5-year history on startup.
-   [ ] **Reliability**: Ingestion recovers from simulated network/API failures without crashing.
-   [ ] **Performance**: `/v1/deep-dive` endpoint responds in < 100ms (p95).
-   [ ] **Quality**: 100% pass rate on Unit and Integration (Testcontainers) tests.
