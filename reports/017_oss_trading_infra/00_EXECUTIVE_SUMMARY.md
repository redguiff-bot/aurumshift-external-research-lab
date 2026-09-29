# 00 — Executive summary

Mission `AURUMSHIFT_EXTERNAL_OSS_TRADING_RESEARCH_INFRA_DISCOVERY_V1` — external research only; no private AurumShift code read; no integration proposed.
Run date (sandbox clock): 2026-09-29 (UTC). Evidence labels follow `claude.md`: PROVEN (independent ground truth) / OBSERVED (we ran or inspected it) / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN.
Doctrine applied: REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST; no platform rewrite; no second authoritative database unless unavoidable.

## What was done
* **67 candidates** across the 13 component classes were catalogued (`bench/oss_trading_infra_v1/py/catalog.py`) and screened from primary sources: shallow git history (commits since 2025-09-29), PyPI metadata, licence files, test-file paths, CI presence (`results/screen.json`).
* **41 candidates were executed** with real microtests that have an independent oracle where one exists (numpy/scipy oracle, hand-derived queue/fill ground truth, cross-library equality, known calendar dates, injected faults); 3 were installed/imported only; 23 are metadata-only (reasons in `08`).
* Isolated install footprint (fresh venv per candidate) was measured for 33 candidates (`07`).
* A real PostgreSQL 16 + TimescaleDB 2.30.2 + pg_partman 5.0.1 instance was stood up in the sandbox to test time-series storage without adding a second datastore.
* Nothing was ranked from README claims; where a claim could not be reproduced it is recorded as UNKNOWN rather than dropped.

## Headline findings
1. **Two replay/simulation cores are usable without a rewrite, with different trade-offs.** `hftbacktest` (MIT, Rust+numba, 11 M events/s warm) reproduced a hand-derived queue-position fill and respected order latency; `nautilus_trader` (LGPL, 349–360 k quotes/s) replays L2 deltas deterministically but did **not** reproduce a print-driven passive fill in 9 configurations (UNKNOWN whether a supported setting exists). Both were bit-/hash-deterministic across repeated runs. (`03`)
2. **Transaction-cost modelling has exactly one integrated OSS candidate with verified behaviour:** `cvxportfolio`'s simulator charged exactly 10 bps of traded notional for a = 0.001 and scaled ×4.000 (spread) and ×8.000 (impact, exponent 1.5) when the trade was 4× larger. It is GPLv3 with a single author (bus factor 1). (`04`)
3. **Look-ahead protection is not something backtest engines provide.** Per-bar engines (`backtesting.py`, `backtrader`) block the future through the per-bar API — except `backtrader` on preloaded data, where `data.close[1]` returned the *next* bar on every bar but the last — and *every* engine accepts a precomputed array that peeks (foresight signal: `backtesting.py` +115.8 %, `vectorbt` +7.5 % at zero fees). PIT safety must come from the data layer, not from the engine. (`03`)
4. **Small pure libraries are the strongest "reuse" finds:** `exchange_calendars` (NYSE 1 758 sessions and 14 early closes identical to `pandas_market_calendars`, special closures and DST correct), `river` (online mean/var/EWMA equal to numpy to 1e-15…1e-21), `hdrhistogram`/`ddsketch` (error within stated bounds), `TA-Lib` (causal, prefix-consistent), `DuckDB`/`polars` (ASOF join equal to pandas on a tie-laden test, 0 look-ahead violations), `pyarrow` (byte-identical Parquet writes). (`02`, `05`)
5. **Time-series storage does not need a second datastore.** Inside the *same* PostgreSQL 16, TimescaleDB gave 13.5× compression (397.7 → 29.4 MB on 3 M rows) and a 1.8× faster 1-minute-bar query, with results byte-equal to native partitioning; but the compression/continuous-aggregate features run under the Timescale License, not Apache-2. Native declarative partitioning matched plain-table speed with zero extensions. Separate TSDB servers (QuestDB, ClickHouse, InfluxDB, VictoriaMetrics) are parked on doctrine. (`02`, `07`)
6. **Hazards found by execution (would corrupt a pipeline silently):** ClickHouse ASOF returns `0` (not NULL) for an unmatched left row by default; `cryptofeed` Coinbase feed now needs credentials and the library needs an event-loop workaround on py3.11 + uvloop; `binance-public-data` downloads `.CHECKSUM` but never verifies it, and 2025 spot files carry µs timestamps; PyPI `orderbook` 0.1.2 cannot even be imported; `PyPortfolioOpt` and `empyrical-reloaded` omit a runtime dependency (`packaging`, `pytz`); `talipp` EMA seeds with an SMA (2.4e-3 early divergence from pandas `ewm`); ccxt returns the still-forming bar on all four reachable venues.
7. **Licence is the most common blocker, not quality.** Copyleft or non-OSI terms sit on `cryptofeed` (AGPL), `backtesting.py` (AGPL), `cvxportfolio`/`freqtrade`/`pysystemtrade` (GPL-3), `backtrader` (GPL-3+), `nautilus_trader` (LGPL-3), `vectorbt` (Commons Clause), `ArcticDB` (BSL 1.1), `soda-core` (Elastic License 2.0). Legal effect on AurumShift is **UNKNOWN** and not assessed here.

## No "best framework" conclusion
The classes have different jobs; the adjudication (`08`) is per component and per gap. Counts: ADOPT_REFERENCE 14 · ADAPT_CANDIDATE 10 · PARK 36 · REJECT 7.

## Final block
```
PROJECTS_DISCOVERED=67
PROJECTS_EXECUTED=41 (behavioural microtest run); 3 install/import only; 23 screened from metadata only

ADOPT_REFERENCE_COUNT=14
ADAPT_CANDIDATE_COUNT=10
PARK_COUNT=36
REJECT_COUNT=7

SECOND_SERVICE_REQUIRED_CANDIDATES=5 (tcapy, QuestDB, ClickHouse, VictoriaMetrics, InfluxDB)
SECOND_DATASTORE_REQUIRED_CANDIDATES=8 (zipline-reloaded, tcapy, QuestDB, ClickHouse, ArcticDB, VictoriaMetrics, InfluxDB, tstables)

ANY_DROP_IN_COMPONENT=YES (narrow, capability-level: exchange_calendars, river, hdrhistogram/ddsketch, TA-Lib, pyarrow, DuckDB/polars as compute-only — pure libraries, no service, permissive licence, verified by microtest; fit against the real AurumShift code is deliberately not asserted)

FINAL_VERDICT=MULTIPLE_OSS_COMPONENTS_SUPPORTED
```
