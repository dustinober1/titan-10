# Domain Pitfalls

**Domain:** Cryptocurrency Quantitative Research Platform
**Researched:** 2025-01-18
**Overall Confidence:** HIGH

---

## Exchange API Pitfalls

### Pitfall 1: Rate Limit Exceeded → IP Ban

**What goes wrong:** Exceeding exchange API rate limits results in automated IP bans (HTTP 418), blocking all future requests.

**Why it happens:**
- Exchanges track cumulative rate limit violations
- Failing to back off after HTTP 429 warnings triggers automatic bans
- Repeated violations result in longer or permanent bans

**Consequences:**
- Complete loss of data from that exchange
- Hours to days of downtime (bans are not automatically lifted)
- Requires manual intervention to contact exchange support
- Historical backfill jobs fail mid-execution

**Prevention:**
- **Respect rate limits strictly:** Stay 20% below documented limits
- **Implement exponential backoff:** After HTTP 429, wait exponentially longer (1s, 2s, 4s, 8s, 16s, 32s, 60s max)
- **Monitor rate limit headers:** Parse `X-MBX-USED-WEIGHT` (Binance) or similar headers
- **Circuit breakers:** Stop requesting from exchange for 60 seconds after 3rd 429
- **Distributed rate limiting:** If using multiple workers, coordinate rate limits via Redis

**Warning Signs:**
- HTTP 429 errors appearing in logs
- Increasing latency from exchange responses
- HTTP 418 errors (already banned)

**Phase to Address:** Phase 1 (Data Ingestion) - Critical path

**Sources:**
- [Binance: How to Avoid Getting Banned by Rate Limits](https://www.binance.com/en/academy/articles/how-to-avoid-getting-banned-by-rate-limits) (July 2025)
- [Binance API Limits Documentation](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits)
- [CoinAPI: Crypto API Comparison](https://www.coinapi.io/blog/crypto-api-comparison-coinapi-vs-cryptocurrencies-2025)

---

### Pitfall 2: Missing Candle Data (Gaps)

**What goes wrong:** Exchange APIs return incomplete OHLCV data with missing candles, creating gaps that invalidate volatility calculations and backtests.

**Why it happens:**
- Exchange downtime (planned maintenance or outages)
- Network interruptions during data fetching
- Exchange APIs not returning data for illiquid periods
- API pagination errors causing data skips

**Consequences:**
- Volatility calculations are incorrect (missing high/low periods)
- Backtest results are unrealistic (gaps hide drawdowns)
- Technical indicators produce wrong values
- Research conclusions are invalid

**Prevention:**
- **Gap detection:** Query for expected candle count, compare to actual
- **Automatic gap filling:** Forward-fill missing candles with previous close (flag as filled)
- **Data quality metrics:** Track % of missing data per symbol/timeframe
- **Multi-source redundancy:** Fetch from secondary exchange if primary has gaps
- **Alert on gaps:** Notify when gap rate exceeds threshold (e.g., >5%)

**Warning Signs:**
- Uneven spacing between timestamps
- Fewer candles than expected for date range
- Volatility metrics suddenly drop to zero

**Phase to Address:** Phase 1 (Data Ingestion) - Data quality validation

**Sources:**
- [CoinAPI: Backtest with Real Market Data](https://www.coinapi.io/blog/backtest-crypto-strategies-with-real-market-data) (August 2025)
- [GitHub Issue #11308: Missing Data from Coinbase](https://github.com/freqtrade/freqtrade/issues/11308) (January 2025)

---

### Pitfall 3: WebSocket Disconnections Without Recovery

**What goes wrong:** WebSocket connections to exchanges drop unexpectedly and fail to reconnect, causing real-time data ingestion to stop.

**Why it happens:**
- Cloudflare terminations (common with Kraken)
- Network interruptions
- Exchange-side WebSocket restarts
- Idle connection timeouts

**Consequences:**
- Real-time data stops flowing silently
- System appears healthy (no errors) but data is stale
- Missed trading signals or market events
- Manual intervention required to restart

**Prevention:**
- **Automatic reconnection:** Detect disconnection, reconnect immediately
- **Exponential backoff:** After failed reconnect, wait 1s, 2s, 4s, 8s, 16s, 32s, 60s max
- **Ping/pong heartbeat:** Send ping every 15 seconds, expect pong within 7.5 seconds
- **Connection state monitoring:** Track last message timestamp, alert if >30 seconds stale
- **Subscription resumption:** After reconnect, resubscribe to all channels

**Warning Signs:**
- Last message timestamp >30 seconds ago
- WebSocket connection state shows "disconnected"
- No new data in database for real-time symbols

**Phase to Address:** Phase 1 (Data Ingestion) - WebSocket implementation

**Sources:**
- [CoinGecko WebSocket API (Beta) Documentation](https://dev.to/yousrasd/avoiding-stale-data-redis-caching-gotchas-c1h) (June 2025)
- [Reddit: Solana WebSocket Discussion](https://www.reddit.com/r/solana/) - Community insights on reconnection patterns

---

### Pitfall 4: Exchange API Downtime During Market Stress

**What goes wrong:** Exchange APIs fail during high volatility periods (flash crashes, liquidations), exactly when data is most critical.

**Why it happens:**
- Exchange infrastructure overloaded during market stress
- Cloud provider outages affecting multiple exchanges simultaneously
- Exchange emergency maintenance during extreme volatility

**Consequences:**
- Missing data during most important market periods
- Inability to backtest crash scenarios accurately
- Trading systems make decisions without complete information
- Historical record of major market events is incomplete

**Prevention:**
- **Multi-exchange redundancy:** Fetch same symbol from 3+ exchanges, merge data
- **Graceful degradation:** Continue with available exchanges, flag missing sources
- **Increased backoff during outages:** Detect exchange downtime, back off to 60s intervals
- **Incident monitoring:** Track exchange status pages, alert on degradation
- **Local cache warming:** Ensure cached data is available during outages

**Warning Signs:**
- HTTP 503 errors from exchange
- Timeout errors increasing
- Exchange status page showing incidents
- Multiple exchanges failing simultaneously (cloud outage)

**Phase to Address:** Phase 1 (Data Ingestion) - Multi-exchange architecture

**Sources:**
- [Binance H1 2025 API Uptime Report](https://www.binance.com/en/blog/tech/4885724370067176471) (August 2025)
- [Inside the $19B Flash Crash](https://insights4vc.substack.com/p/inside-the-19b-flash-crash) (October 2025)
- [October 2025 Crypto Crash: Infrastructure Failures](https://medium.com/@nicolakharvey/infrastructure-failures-that-amplified-the-crash-545656ab1c09)

---

## Time-Series Data Pitfalls

### Pitfall 5: TimescaleDB Compression Performance Degradation

**What goes wrong:** TimescaleDB compression creates performance issues instead of improving it, causing slow queries.

**Why it happens:**
- Chunks that are too small (<1 MB) create significant overhead
- Using `compress_segmentby` with stock ticker creates inefficient segments
- Improper segmentby configuration leading to many small segments
- High IO during compression operations blocking queries

**Consequences:**
- Queries hitting compressed chunks are slower than uncompressed
- Database performance degrades over time
- Compression operations consume excessive IO
- API response times exceed SLA

**Prevention:**
- **Avoid over-segmentation:** Don't use `compress_segmentby` on high-cardinality fields like symbol
- **Monitor chunk sizes:** Ensure chunks are >1 MB before compression
- **Use time-based compression:** Compress by time range, not by symbol
- **Schedule compression:** Run compression during low-traffic periods (2-4 AM UTC)
- **Test compression performance:** Benchmark query performance before/after compression

**Warning Signs:**
- Queries slower after compression enabled
- High IO wait during compression operations
- Many small chunks in database
- `pg_stat_user_tables` shows high sequential scans

**Phase to Address:** Phase 1 (Data Storage) - Compression strategy

**Sources:**
- [My Experience with TimescaleDB Compression](https://mail-dpant.medium.com/my-experience-with-timescaledb-compression-68405425827) - Deepak Pant
- [TimescaleDB Issue #8715: Chunk Performance Degradation](https://github.com/timescale/timescaledb/issues/8715) (September 2025)
- [TimescaleDB Issue #7225: Long Wait Time & High IO When Compressing](https://github.com/timescale/timescaledb/issues/7225) (August 2024)

---

### Pitfall 6: Continuous Aggregate Refresh Failures

**What goes wrong:** TimescaleDB continuous aggregates fail to refresh or refresh incorrectly, producing stale or wrong pre-computed data.

**Why it happens:**
- DST time changes break sub-hour continuous aggregates
- Hierarchical continuous aggregates generate duplicate time buckets
- Refresh recalculates more data than expected (performance issue)
- Documentation gaps around refresh policy behavior

**Consequences:**
- Stale pre-computed data served to users
- Incorrect analysis results
- Performance degradation from excessive recalculation
- Duplicate data in aggregates

**Prevention:**
- **Avoid sub-hour aggregates:** Use hourly or daily granularity to avoid DST issues
- **Test refresh policies:** Verify refresh behavior matches documentation
- **Monitor refresh lag:** Track time between raw data and aggregate update
- **Avoid hierarchical aggregates:** Don't chain aggregates (hourly → daily)
- **Version awareness:** Use TimescaleDB 2.20.1+ which includes decompression limit fixes

**Warning Signs:**
- Continuous aggregate data older than raw data
- Duplicate time buckets in query results
- Refresh operations taking longer than expected
- Error logs mentioning "inverted windows" or "DST"

**Phase to Address:** Phase 1 (Data Storage) - Continuous aggregate design

**Sources:**
- [TimescaleDB Issue #8898: DST Time Changes](https://github.com/timescale/timescaledb/issues/8898) (November 2025)
- [TimescaleDB Issue #8792: Excessive Recalculation](https://github.com/timescale/timescaledb/issues/8792) (October 2025)
- [StackOverflow: Hierarchical Continuous Aggregates](https://stackoverflow.com/questions/77686166/timescaledb-hierarchical-continuous-aggregates-generate-duplicated-time-bucket)

---

### Pitfall 7: Timezone Confusion in Timestamps

**What goes wrong:** Mixing UTC and local timestamps, or using inconsistent timestamp formats, causes data alignment issues and incorrect analysis.

**Why it happens:**
- Exchanges return timestamps in different timezones
- Converting between multiple datetime formats
- Daylight Saving Time shifts
- Not enforcing UTC consistently

**Consequences:**
- Data misalignment across exchanges
- Incorrect time-based filtering
- Candles don't align for comparison
- Backtests use wrong time periods
- Nearly impossible to debug

**Prevention:**
- **Golden rule:** Always store timestamps in UTC in ISO8601 format
- **Normalize at ingestion:** Convert all exchange timestamps to UTC immediately
- **Timezone-aware datetimes:** Use Python `datetime` with `tzinfo` set
- **Validate timezone info:** Reject data without timezone information
- **Document timezone handling:** Clear comments about timezone assumptions

**Warning Signs:**
- Timestamps without timezone info
- Data appearing at wrong UTC times
- Seasonal patterns in data (DST shift artifacts)
- Candles from different exchanges not aligning

**Phase to Address:** Phase 1 (Data Ingestion) - Timestamp normalization

**Sources:**
- [How to Handle Date and Time Correctly](https://dev.to/kcsujeet/how-to-handle-date-and-time-correctly-to-avoid-timezone-bugs-4o03) (February 2025)
- [Why Accurate Timestamps Matter](https://finage.co.uk/blog/why-accurate-timestamps-in-market-data-matter-more-than-you-think--686110d96d7e61204e4e74a4) (June 2025)
- [Why Datetime Formatting is Critical](https://medium.com/cryptosheets/why-datetime-formatting-for-crypto-api-data-is-the-most-important-part-of-your-trading-analysis-93fef04ed9d8)

---

### Pitfall 8: Survivorship Bias in Historical Data

**What goes wrong:** Only including currently listed cryptocurrencies, ignoring delisted/failed projects, creating artificially inflated historical returns.

**Why it happens:**
- Most data providers only show currently listed assets
- Delisted cryptocurrencies are harder to obtain
- Historical data for failed projects is often incomplete
- Laziness in data collection

**Consequences:**
- Backtest results are overly optimistic (ignoring failed assets)
- Strategy appears profitable when it would have failed
- Misleading risk assessments
- Invalid research conclusions
- Real trading performance worse than backtest

**Prevention:**
- **Include delisted pairs:** Track delisted cryptocurrencies with historical data
- **Document data coverage:** Explicitly state which delisted assets are included
- **Bias testing:** Compare results with vs. without delisted assets
- **Multiple data sources:** Cross-check data for bias detection
- **Transparent reporting:** Show survivorship bias impact in research

**Warning Signs:**
- Backtest returns too good to be true
- No losses from failed projects in historical period
- Data provider only shows currently listed assets
- Can't find historical data for well-known failed projects

**Phase to Address:** Phase 1 (Data Ingestion) - Historical data sourcing

**Sources:**
- [Survivorship and Delisting Bias in Cryptocurrency Markets](https://www.alexandria.unisg.ch/268147/1/Survivorship_and_Delisting_Bias_in_Cryptocurrency_Markets.pdf) - University of St. Gallen
- [CoinAPI: Survivorship Bias in Backtesting](https://www.coinapi.io/blog/backtest-crypto-strategies-with-real-market-data) (August 2025)
- [Reddit: Where to Get Survivorship-Bias-Free Data](https://www.reddit.com/r/quant/comments/190tt0i/where_to_get_crypto_data_without_survivorshipbias/)

---

## Analysis & Computation Pitfalls

### Pitfall 9: Look-Ahead Bias in Backtesting

**What goes wrong:** Backtests incorporate future data that wouldn't be available in real-time, creating unrealistic performance.

**Why it happens:**
- Using closing prices to execute trades at close (knowing the close beforehand)
- Calculating indicators using future data
- Aligning data across exchanges with perfect hindsight
- Filling trades at historical prices without slippage

**Consequences:**
- Backtest shows profit when real trading would lose money
- Strategy fails catastrophically in production
- Wasted development time on unprofitable strategies
- Loss of confidence in quantitative system

**Prevention:**
- **Strict timestamp discipline:** Indicators only use data from timestamp < current time
- ** realistic execution:** Execute trades at next bar's open, not current bar's close
- **Walk-forward validation:** Test on out-of-sample data
- **Point-in-time data:** Use data as it appeared at that moment (not restated)
- **Code review:** Have another quant review for look-ahead bias

**Warning Signs:**
- Strategy buys exactly at bottoms, sells exactly at tops
- Sharpe ratio >3 (suspiciously high)
- Perfect timing of market turns
- Indicator values seem to "predict" price movements too accurately

**Phase to Address:** Phase 2 (Analysis Features) - Backtesting framework

**Sources:**
- [7 Common Backtesting Mistakes](https://quantstrategy.io/blog/7-common-backtesting-mistakes-that-lead-to-false-confidence) - Look-ahead bias as "most fundamental error"
- [Algorithmic Crypto Trading Research](https://link.springer.com/article/10.1186/s40854-025-00866-w) - Springer (2025)
- [Machine Learning Multi-Factor Model](https://dl.acm.org/doi/full/10.1141/3766918.3766922) - ACM (2025)

---

### Pitfall 10: Overfitting to Historical Data

**What goes wrong:** Optimizing strategy parameters too closely to historical data, creating a strategy that works perfectly in backtest but fails in production.

**Why it happens:**
- Excessive parameter tuning
- Adding rules to explain past anomalies
- Using too many features relative to data size
- Testing on same data used for optimization

**Consequences:**
- Backtest returns are excellent, live trading loses money
- Strategy stops working immediately after deployment
- Wasted resources on unprofitable strategies
- False confidence in quantitative approach

**Prevention:**
- **Out-of-sample testing:** Hold out 20-30% of data for validation
- **Walk-forward analysis:** Rolling out-of-sample testing
- **Parameter stability:** Test strategy across different parameter values
- **Minimum data length:** Require at least 5 years of data for backtesting
- **Simplicity preference:** Prefer simpler strategies with fewer parameters

**Warning Signs:**
- Strategy requires 10+ parameters to work
- Adding more rules always improves backtest
- Performance varies wildly with small parameter changes
- Strategy only works in specific time periods

**Phase to Address:** Phase 2 (Analysis Features) - Validation framework

**Sources:**
- [Crypto Backtesting Guide 2025](https://bitsgap.com/blog/crypto-backtesting-guide-2025-tools-tips-and-how-bitsgap-helps) (April 2025)
- [The 7 Most Common Backtesting Mistakes](https://amicode.substack.com/p/the-7-most-common-backtesting-mistakes)
- [The Limits of Out-of-Sample Testing](https://harbourfrontquant.substack.com/p/the-limits-of-out-of-sample-testing)

---

## API & Caching Pitfalls

### Pitfall 11: Stale Data in Redis Cache

**What goes wrong:** Cached data becomes stale but continues to be served, providing incorrect results to API users.

**Why it happens:**
- Missing TTL configuration (data never expires)
- TTL set too high for volatile data
- Cache not invalidated when underlying data changes
- Race conditions in cache refresh

**Consequences:**
- API returns outdated prices or indicators
- Trading decisions based on stale data
- User trust erodes when they notice discrepancies
- Difficult to debug (cache hits look successful)

**Prevention:**
- **Always set TTL:** Never cache without expiration time
- **Appropriate TTL values:**
  - Real-time prices: 1-5 seconds
  - Computed indicators: 60 seconds
  - Symbol metadata: 300 seconds
  - Exchange info: 3600 seconds
- **Cache invalidation:** Invalidate cache when data updates
- **Stale-while-revalidate:** Serve stale data while refreshing in background
- **Cache versioning:** Include version in cache key to force invalidation

**Warning Signs:**
- API data doesn't match exchange data
- Prices don't update for extended periods
- Indicator values don't change with new candles
- User complaints about data accuracy

**Phase to Address:** Phase 1 (API Layer) - Caching implementation

**Sources:**
- [Avoiding Stale Data: Redis Caching Gotchas](https://dev.to/yousrasd/avoiding-stale-data-redis-caching-gotchas-c1h) (June 2025)
- [Redis Wrong for Years](https://medium.com/@diyasanjaysatpute147/i-was-using-redis-wrong-for-years-here-is-how-i-finally-learned-caching-properly-a769e7dcbe0b)
- [Boosting Speed: Redis Caching Strategies](https://dev.to/ash_dubai/boosting-speed-essential-redis-caching-strategies-for-saas-in-2025-50pl)

---

### Pitfall 12: Cache Stampede (Thundering Herd)

**What goes wrong:** Multiple API requests simultaneously miss cache and fetch from database, overwhelming the database.

**Why it happens:**
- Cache expires for popular query
- Many concurrent API requests arrive
- All requests query database simultaneously
- Cache not repopulated fast enough

**Consequences:**
- Database connection pool exhaustion
- Database CPU spikes to 100%
- API timeouts and errors
- Cascading failure across system

**Prevention:**
- **Single-flight locks:** Only one request refreshes cache, others wait
- **Cache warming:** Pre-populate cache before expiry
- **Soft TTL:** Mark data as stale but continue serving while refreshing
- **Request coalescing:** Merge identical in-flight requests
- **Rate limiting:** Limit requests per client during cache miss

**Warning Signs:**
- Database load spikes at regular intervals (matches cache TTL)
- Many simultaneous queries for same data
- API errors during cache expiry periods
- Database connection pool exhaustion

**Phase to Address:** Phase 1 (API Layer) - Caching optimization

**Sources:**
- [FastAPI + Redis at 50k RPS](https://medium.com/@hadiyolworld007/fastapi-redis-at-50k-rps-the-undocumented-caching-playbook-e6c6407ba4dc) - Advanced caching patterns
- [Redis CVE-2025-21605](https://redis.io/blog/security-advisory-cve-2025-21605/) - DoS vulnerability from unlimited output buffer

---

### Pitfall 13: Connection Pool Exhaustion

**What goes wrong:** PostgreSQL connection pool exhausted, causing new requests to fail with timeout errors.

**Why it happens:**
- Too many concurrent requests relative to pool size
- Long-running database queries holding connections
- Connections not released properly (connection leaks)
- Async tasks creating more connections than pool size

**Consequences:**
- API returns 500 errors or times out
- System appears unhealthy
- Requires restart to recover
- Cascading failures as requests retry

**Prevention:**
- **Proper pool sizing:** Set pool size = (number of CPUs × 2) + 1 for I/O-bound workloads
- **Use PgBouncer:** Connection pooler proxy between app and PostgreSQL
- **Limit concurrent requests:** Use anyio CapacityLimiter to throttle database access
- **Connection timeout:** Set strict timeout (e.g., 30 seconds)
- **Monitor pool metrics:** Track active/idle connections, alert if pool >80% full

**Warning Signs:**
- `psycopg_pool.PoolTimeout` errors
- API timeouts in logs
- Database shows many connections in "idle in transaction"
- Response times degrade under load

**Phase to Address:** Phase 1 (Database Layer) - Connection pooling

**Sources:**
- [Async Python Almost Destroyed Our API](https://python.plainenglish.io/async-python-almost-destroyed-our-api-heres-what-we-learned-c0087d564f7c) (December 2025)
- [How to Avoid Pool Exhaustion in FastAPI](https://stackoverflow.com/questions/73195338/how-to-avoid-database-connection-pool-from-being-exhausted-when-using-fastapi-in)
- [PostgreSQL Connection Limits: Performance Optimization](https://rizqimulki.com/postgresql-connection-limits-performance-optimization-for-ai-microservices-0847ebb4d8b1) (October 2025)

---

## Autonomous Runtime Pitfalls

### Pitfall 14: Fail-and-Stop Data Pipeline

**What goes wrong:** Any error in data ingestion pipeline stops the entire process, requiring manual restart.

**Why it happens:**
- Unhandled exceptions crash worker processes
- No retry logic for transient failures
- Single point of failure in data pipeline
- Errors logged but pipeline doesn't continue

**Consequences:**
- Data ingestion stops until human intervenes
- Gaps in historical data during downtime
- System appears healthy (process running) but data is stale
- Defeats purpose of autonomous operation

**Prevention:**
- **Try-except around all external calls:** Never let exception crash process
- **Retry with exponential backoff:** Transient failures recover automatically
- **Circuit breakers:** Stop failing operations, auto-recover when healthy
- **Per-symbol error tracking:** Fail one symbol without affecting others
- **Dead letter queue:** Log failed operations for later replay

**Warning Signs:**
- Data freshness metrics degrading
- Last successful fetch timestamp old
- No data in database for recent time periods
- Worker process still running but not producing data

**Phase to Address:** Phase 1 (Data Ingestion) - Error handling

**Sources:**
- [A Framework for Affordable High-Quality Blockchain Data](https://arxiv.org/html/2511.13318v1) - Health checks and failure patterns (November 2025)
- [2025 Annual Guide: Crypto Data Engineering](https://read.cryptodatabytes.com/p/2025-annual-guide-crypto-data-engineering) (January 2025)

---

### Pitfall 15: Silent Failures in Data Quality

**What goes wrong:** Bad data passes validation silently, corrupting analysis without triggering alerts.

**Why it happens:**
- Insufficient data quality checks
- Validation logic too permissive
- Only checking schema, not values
- Not monitoring statistical properties

**Consequences:**
- Incorrect research results
- Wasted time debugging bad analysis
- Loss of trust in system
- Decisions based on flawed data

**Prevention:**
- **Multi-layer validation:**
  - Schema validation (data types, required fields)
  - Range validation (price >0, volume >=0)
  - Statistical validation (no extreme outliers)
  - Cross-validation (OHLC relationships: low <= open,close <= high)
- **Continuous monitoring:** Track data quality metrics (null counts, outlier rates)
- **Alert on anomalies:** Notify when quality metrics deviate
- **Sample inspection:** Randomly inspect data for issues

**Warning Signs:**
- Prices of 0 or negative
- High > low (impossible)
- Volume suddenly drops to 0
- Extreme price spikes (10x+ in one candle)

**Phase to Address:** Phase 1 (Data Ingestion) - Data quality validation

**Sources:**
- [Building a Real-Time Cryptocurrency Data Pipeline](https://medium.com/@chiheb.mhamdi/building-a-real-time-cryptocurrency-data-engineering-pipeline-from-ingestion-to-api-access-e5e322bef434) (April 2025) - Data quality best practices

---

### Pitfall 16: Unbounded Retry Storms

**What goes wrong:** Retry logic runs infinitely, overwhelming the system and causing cascading failures.

**Why it happens:**
- No maximum retry limit
- Retry doesn't use backoff
- All components retry simultaneously
- Permanent errors retried endlessly

**Consequences:**
- System becomes unresponsive
- Resource exhaustion (CPU, memory, connections)
- Cascading failures to dependent services
- Difficult to recover (requires restart)

**Prevention:**
- **Max retry limit:** Stop after 5-10 attempts
- **Exponential backoff with jitter:** 1s, 2s, 4s, 8s, 16s, 32s, 60s max
- **Circuit breaker:** Open circuit after 5 consecutive failures, retry after 60s
- **Distinguishable errors:** Only retry transient errors (503, timeout), not permanent (404, 400)
- **Retry budget:** Limit total retries per minute

**Warning Signs:**
- Log spam with retry messages
- System CPU usage high
- Many connections in opening state
- Response times increasing

**Phase to Address:** Phase 1 (Error Handling) - Retry configuration

**Sources:**
- [Tenacity Documentation](https://tenacity.readthedocs.io/) - Retry best practices
- [Google SRE: Circuit Breakers](https://sre.google/sre-book/handling-overload/)

---

### Pitfall 17: Backfill Without Checkpoints

**What goes wrong:** Long-running backfill jobs fail near completion, requiring restart from beginning.

**Why it happens:**
- No checkpoint/savepoint mechanism
- Job fails due to transient error
- No progress tracking
- Can't resume from failure point

**Consequences:**
- Wasted time and resources (days of backfill rerun)
- Delayed data availability
- Discourages frequent backfills
- API rate limits exceeded during re-backfill

**Prevention:**
- **Checkpoint after each symbol:** Record last successfully fetched symbol
- **Atomic commits:** Commit data per symbol, not at end
- **Progress tracking:** Store job state in database
- **Resume capability:** On restart, continue from last checkpoint
- **Validation before commit:** Verify data before marking complete

**Warning Signs:**
- Backfill jobs failing after 12+ hours
- Having to restart backfill from beginning
- No progress indicators during backfill
- Fear of starting long backfills

**Phase to Address:** Phase 1 (Data Ingestion) - Backfill implementation

**Sources:**
- [Streaming CEX, DEX, and Blockchain Events](https://community.databricks.com/t5/technical-blog/streaming-cex-dex-and-blockchain-events-in-databricks-for-web3/ba-p/120503) (June 2025) - Checkpoint patterns
- [MystenLabs Sui Releases](https://github.com/MystenLabs/sui/releases) - `--first-checkpoint` functionality

---

## Testing Pitfalls

### Pitfall 18: Testing Only with Live Exchange Data

**What goes wrong:** Tests fail flakily because they depend on live exchange APIs which have rate limits, downtime, and changing data.

**Why it happens:**
- Tests call real exchange APIs
- No test data fixtures
- Tests assume specific market conditions
- No mocking of external dependencies

**Consequences:**
- Flaky tests (pass sometimes, fail sometimes)
- Slow test suite (waiting for API responses)
- Rate limit bans during CI/CD
- Tests can't run offline
- Difficult to reproduce failures

**Prevention:**
- **Mock all external APIs:** Use fixtures for exchange responses
- **Record and replay:** Record real API responses once, replay in tests
- **Test data fixtures:** Store sample OHLCV data for testing
- **Deterministic tests:** Same inputs always produce same outputs
- **Sandbox environments:** Use exchange testnets when integration testing required

**Warning Signs:**
- Tests fail randomly
- Test suite takes >10 minutes
- Tests fail with rate limit errors
- Can't run tests without internet

**Phase to Address:** Phase 1 (Testing Infrastructure) - Test data setup

**Sources:**
- [Top Mistakes When Building Crypto Trading Bot](https://www.tokenmetrics.com/blog/avoid-common-pitfalls-first-crypto-trading-bot) - Safe testing methods
- [Best Testing Practices for CTA Trading](https://medium.com/balaena-quant-insights/best-backtesting-practices-for-cta-trading-in-cryptocurrency-e79677cb6375)

---

### Pitfall 19: Insufficient Monitoring in Production

**What goes wrong:** System deployed to production without comprehensive monitoring, making it impossible to detect issues before users.

**Why it happens:**
- Monitoring treated as afterthought
- Only basic uptime checks
- No alerting on data quality
- No visibility into system internals

**Consequences:**
- Users notice problems before operators
- Difficult to debug production issues
- Can't measure system health
- No historical performance data
- Reactive instead of proactive

**Prevention:**
- **Metrics collection from day one:** Instrument all critical paths
- **Key metrics to track:**
  - API response times (p50, p95, p99)
  - Cache hit rates
  - Exchange API errors
  - Data freshness (last successful fetch)
  - Database query performance
- **Alert on anomalies:**
  - API response time >100ms (p95)
  - Cache hit rate <90%
  - Data age >60 seconds
  - Error rate >1%
- **Dashboards:** Grafana dashboards for system health
- **Structured logging:** JSON logs with correlation IDs

**Warning Signs:**
- "Is the system down?" questions from users
- No metrics available during incident
- Manual SSH into server to check status
- No historical performance data

**Phase to Address:** Phase 1 (Operations) - Monitoring setup

**Sources:**
- [10 Monitoring Best Practices](https://middleware.io/blog/monitoring-best-practices-for-developers/) (2025)
- [System Design: Monitoring and Alerting](https://medium.com/double-pointer/system-design-interview-metrics-monitoring-and-alerting-system-9083a17d5a51)
- [Google SRE: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)

---

## Phase-Specific Warnings

| Phase | Topic | Likely Pitfall | Mitigation |
|-------|-------|----------------|------------|
| **Phase 1: Data Ingestion** | Exchange API integration | Rate limit IP bans | Implement exponential backoff + circuit breakers from day one |
| **Phase 1: Data Ingestion** | Historical backfill | Job failure after 24+ hours | Build checkpoint/resume mechanism before first backfill |
| **Phase 1: Data Storage** | TimescaleDB setup | Compression performance degradation | Test compression on realistic data before production |
| **Phase 1: API Layer** | Caching implementation | Stale data served to users | Set TTLs on all cache entries, implement stale-while-revalidate |
| **Phase 1: Operations** | Monitoring | No visibility into system health | Instrument all code paths before deploying to production |
| **Phase 2: Analysis** | Indicator computation | Look-ahead bias | Strict timestamp discipline, code review for bias |
| **Phase 2: Backtesting** | Strategy validation | Overfitting to historical data | Require out-of-sample testing, walk-forward analysis |
| **Phase 3: Advanced** | Real-time ingestion | WebSocket disconnections | Implement automatic reconnection with ping/pong heartbeat |

---

## Critical vs Moderate vs Minor Pitfalls

### Critical Pitfalls (Cause Reworks or Major Issues)

1. **Rate limit IP bans** - Complete data loss, requires manual intervention
2. **Look-ahead bias** - Invalidates all research, requires complete rework
3. **Survivorship bias** - Backtests lie, strategies fail in production
4. **Fail-and-stop pipeline** - Defeats autonomous operation purpose
5. **Silent data quality failures** - Corrupts research without detection
6. **Stale cached data** - Provides incorrect results to users
7. **Unbounded retry storms** - Cascading system failures

### Moderate Pitfalls (Cause Delays or Technical Debt)

8. **Missing candle data (gaps)** - Invalidates volatility calculations
9. **WebSocket disconnections** - Real-time data stops flowing
10. **TimescaleDB compression issues** - Performance degradation
11. **Continuous aggregate failures** - Stale pre-computed data
12. **Timezone confusion** - Data misalignment, nearly impossible to debug
13. **Cache stampede** - Database overload during cache expiry
14. **Connection pool exhaustion** - API timeouts, requires restart
15. **Overfitting** - Strategies work in backtest but not production
16. **Backfill without checkpoints** - Wasted days of computation

### Minor Pitfalls (Cause Annoyance but Fixable)

17. **Testing with live data** - Flaky tests, slows development
18. **Insufficient monitoring** - Reactive instead of proactive

---

## Prevention Strategies Summary

### Architectural Decisions That Prevent Multiple Pitfalls

1. **Multi-exchange redundancy** prevents:
   - Exchange downtime data loss
   - Single point of failure
   - Rate limit impact

2. **UTC timestamps everywhere** prevents:
   - Timezone confusion
   - DST-related issues
   - Data misalignment

3. **Comprehensive monitoring** prevents:
   - Silent failures
   - Late incident detection
   - Inability to debug production issues

4. **Checkpoint-based backfill** prevents:
   - Wasted computation
   - Fear of long backfills
   - Delayed data availability

5. **Mocked external dependencies in tests** prevents:
   - Flaky tests
   - CI/CD failures
   - Slow test suites

---

## Sources

### HIGH Confidence (Official Documentation/Articles)
- [Binance: How to Avoid Getting Banned by Rate Limits](https://www.binance.com/en/academy/articles/how-to-avoid-getting-banned-by-rate-limits) (July 2025)
- [Binance API Limits Documentation](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits)
- [CoinAPI: Backtest with Real Market Data](https://www.coinapi.io/blog/backtest-crypto-strategies-with-real-market-data) (August 2025)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Redis Security Advisories](https://redis.io/blog/security-advisory-cve-2025-21605/) (April 2025)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### MEDIUM Confidence (Verified Sources)
- [Survivorship and Delisting Bias in Cryptocurrency Markets](https://www.alexandria.unisg.ch/268147/1/Survivorship_and_Delisting_Bias_in_Cryptocurrency_Markets.pdf) - University of St. Gallen
- [Crypto Backtesting Guide 2025](https://bitsgap.com/blog/crypto-backtesting-guide-2025-tools-tips-and-how-bitsgap-helps) (April 2025)
- [Building a Real-Time Cryptocurrency Data Pipeline](https://medium.com/@chiheb.mhamdi/building-a-real-time-cryptocurrency-data-engineering-pipeline-from-ingestion-to-api-access-e5e322bef434) (April 2025)
- [7 Common Backtesting Mistakes](https://quantstrategy.io/blog/7-common-backtesting-mistakes-that-lead-to-false-confidence)
- [Binance H1 2025 API Uptime Report](https://www.binance.com/en/blog/tech/4885724370067176471) (August 2025)
- [TimescaleDB GitHub Issues](https://github.com/timescale/timescaledb/issues) - Various compression and continuous aggregate issues

### LOW Confidence (WebSearch - Community Discussions)
- Reddit discussions on cryptocurrency quantitative trading
- Stack Overflow questions on WebSocket reconnection
- GitHub issues from open-source crypto trading projects
- Medium articles on crypto trading pitfalls

**Research Note:** All critical pitfalls are supported by HIGH or MEDIUM confidence sources. LOW confidence sources used only for supplementary context and community patterns.
