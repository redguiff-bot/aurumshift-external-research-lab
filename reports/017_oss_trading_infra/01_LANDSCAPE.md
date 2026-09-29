# 01 — Landscape and screening

Evidence labels: PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN (as in `claude.md`). Test date 2026-09-29 (sandbox clock).
Sources: PyPI JSON metadata (OBSERVED), installed package metadata (OBSERVED), bare blobless git clones for commit history (`bench/.../results/repo_health.json`, OBSERVED), git-tree test-file counts (`repo_tests.json`, OBSERVED, presence only — inline Rust tests are undercounted), web search for discovery (3 queries). GitHub's search API is blocked from this sandbox ("sessions are bound to their configured repositories"), so discovery = known ecosystem + PyPI + web search, **not an exhaustive crawl** (UNKNOWN recall; see 09).

**54 projects discovered, 32 installed and executed** (31 with a real microtest that produced a comparable number; 1 partial). Stars were not used.

## Executed candidates — screen (10 dimensions)

Maintenance = last commit / commits in last 12 months / distinct authors 12 m / share of top author (bus-factor proxy: authors needed for 50 % of 12 m commits). "Deps" = hard `Requires-Dist` count without extras. Services: none of the executed candidates needs a daemon (all in-process/embedded); collectors need the remote venue.

| Project (class) | Licence | Last commit · 12 m commits · authors · top share · BF | Lang | Deps | Data model / PIT | Determinism | Upstream tests (files, share) | Footprint |
|---|---|---|---|---|---|---|---|---|
| nautilus_trader 1.231.0 (replay/backtest/LOB) | LGPL-3.0+ | 2026-09-29 · 5529 · 127 · 85 % · 1 | Rust+Cython+Py (py≥3.12) | 11 | ns timestamps, ts_event/ts_init; no revision model | run-to-run identical (T02) | 480 (15 %) + Rust inline | 870 MB env |
| hftbacktest 2.4.4 (LOB/replay/queue) | MIT | 2025-12-23 · 24 · 5 · 63 % · 1 | Rust+numba | 5 | numpy event array (ev,exch_ts,local_ts,px,qty…): both exchange and local timestamps | exact (T01,T12a) | 1 file (0.8 %) | small |
| vectorbt 1.1.1 (vector backtest) | Apache-2.0 **+ Commons Clause** (not OSI) | 2026-09-26 · 158 · 11 · 77 % · 1 | Py+numba | 17 | dataframes | exact (T03) | 16 (13 %) | 678 MB |
| backtesting.py 0.6.6 | AGPL-3.0 | 2026-08-05 · 33 · 12 · 64 % · 1 | Py | 3 | single OHLC frame | — | 3 (17 %) | 171 MB |
| bt 1.2.3 | MIT | 2026-09-27 · 224 · 17 · 70 % · 1 | Py | 3 | price frame | — | 6 (50 %) | in core |
| backtrader 1.9.78 | GPL-3.0+ | **2023-04-19 · 0** · — | Py | 0 | feeds | — | 83 (24 %) | in core |
| zipline-reloaded 3.1.1 | Apache-2.0 | 2025-11-13 · 4 · 1 · 100 % · 1 | Py+Cython | 28 | bundle (bcolz/sqlite ingest) | exact (T03z/T12b) | 109 (38 %) | 503 MB |
| exchange_calendars 4.13.2 | Apache-2.0 | 2026-09-15 · 62 · 14 · 34 % · 2 | Py | 6 | session/open/close as tz-aware ts | deterministic | 76 (43 %) | small |
| pandas_market_calendars 5.4.0 | MIT | 2026-05-26 · 104 · 15 · 42 % · 2 | Py | 2 | schedule frame | deterministic | 40 (46 %) | small |
| pandera 0.33.1 | MIT | 2026-09-26 · 267 · 56 · 21 % · 3 | Py | 5 | schema on pandas/polars | deterministic | 204 (44 %) | small |
| great_expectations 1.23.2 | Apache-2.0 | 2026-09-28 · 528 · 59 · 35 % · 3 | Py | 22 (35 dists in venv) | expectation suites; ephemeral ctx | deterministic | 569 (33 %) | 302 MB |
| pointblank 0.27.0 | MIT | 2026-09-25 · 2112 · 8 · 92 % · 1 | Py | 10 | validation plan | deterministic | 83 (47 %) | in misc |
| frictionless 5.19.1 | MIT | 2026-09-25 · 26 · 7 · 77 % · 1 | Py | 20 | CSV/table + JSON schema | deterministic | 222 (35 %) | in misc |
| river 0.26.1 | BSD-3 | 2026-09-28 · 299 · 38 · 59 % · 1 | Py+Rust | 3 | per-sample state objects, picklable | identical (T06) | 143 (23 %) | small |
| ta 0.11.0 | MIT | 2026-03-18 · 1 · 1 · 100 % · 1 | Py | 2 | pandas Series | see T05 | 6 (30 %) | tiny |
| pandas-ta 0.4.71b0 | UNKNOWN (metadata empty) | repo clone failed (upstream URL not resolved) | Py (py≥3.12) | 4 | DataFrame accessor | see T05 | UNKNOWN | in misc |
| tsfresh 0.21.2 | MIT | 2026-07-06 · 6 · 5 · 33 % · 2 | Py | 12 | long-format frames | deterministic | 38 (54 %) | in misc |
| PyPortfolioOpt 1.6.0 | MIT | 2026-07-07 · 41 · 11 · 51 % · 1 | Py | 6 | mu, cov | deterministic | 20 (50 %) | in core |
| riskfolio-lib 7.3.0 | BSD | 2026-09-24 · 51 · 4 · 88 % · 1 | Py (cvxpy) | 15 | returns frame | deterministic | 1 (4 %) | in core |
| skfolio 1.4.9 | BSD-3 | 2026-09-29 · 244 · 25 · 33 % · 2 | Py | 7 | sklearn estimators | deterministic | 216 (41 %) | in core |
| empyrical-reloaded 0.5.12 | Apache-2.0 | 2025-07-29 · **0** | Py | 8 | returns series | exact vs hand | 4 (31 %) | in core |
| quantstats 0.0.86 | Apache-2.0 | 2026-09-27 · 22 · 2 · 96 % · 1 | Py | 8 | returns series | exact (Sharpe etc.) | 9 (43 %) | in misc |
| arcticdb 6.26.0 | **BSL 1.1** (→Apache-2.0 after 2 y/version; no "Database Service") | 2026-09-28 · 453 · 17 · 22 % · 3 | C++/Py | 8 | versioned symbols (LMDB/S3/Azure/Mongo) | — | 204 (57 %) | 197 MB |
| duckdb 1.5.6 | MIT | (C++; not cloned) UNKNOWN | C++ | 0 | tables / parquet | deterministic | UNKNOWN | ~ |
| ccxt 4.5.84 | MIT | 2026-09-29 · 10125 · 113 · 51 % · 1 | Py/JS/… | 23 | unified OHLCV/trade dicts | n/a (live) | 1185 (22 %) | in core |
| cryptofeed 2.5.0 executed (3.0.1 is latest) | 2.5.0: XFree86-1.1 (permissive); **3.0.1: AGPL-3.0+, py≥3.13** | 2026-09-28 · 39 · 4 · 74 % · 1 | Py (asyncio) | 9 | callbacks with (data, **receipt_timestamp**) | n/a (live) | 19 (22 %) | in misc |
| yfinance 1.7.0 | Apache-2.0 | 2026-09-25 · 320 · 51 · 53 % · 1 | Py | 12 | Yahoo unofficial scrape | n/a | 22 (31 %) | in misc |
| ABIDES-JPM (abides-core/-markets) | BSD-3 | **2023-12-13 · 0** | Py 3.9, numpy 1.22 pin | 16 dists | agent messages, ns | same seed ⇒ same digest (T13) | 22 (26 %) | 315 MB |
| databento-dbn / databento 0.87.0 | Apache-2.0 (client) — DOCUMENTED_CLAIM | 2026-09-22 · 157 · 10 · 73 % · 1 | Rust+Py | — | DBN records with ts_event, ts_recv, ts_in_delta | — | 37 (39 %) | 306 MB |
| wraquant 1.1.0 | MIT | 4 releases, first 2026 | Py≥3.13 | +undeclared polars | — | deterministic | UNKNOWN | 464 MB |
| nanobook 0.18.1 | MIT | 18 releases; repo not cloned | Rust+Py | numpy | cents ints; event log | replay equal (T16) | UNKNOWN | 66 MB |
| sortedcontainers 2.4.0 (baseline) | Apache-2.0 | last release 2021-05 | Py | 0 | — | — | — | tiny |

Venv sizes are shared per group (`results/footprint.json`), so per-package footprint is an upper bound, not an isolated cost.

## Discovered, not executed (22)
Reason in `08_ADJUDICATION.md`. hummingbot (tick trading bot, 1807 commits/12 m, 696 test files), freqtrade (GPL-3.0, live bot), vnpy (MIT, live gateways, 4 test files), qlib (research platform, 27 commits/12 m), pysystemtrade (6 % test share), rqalpha (China-market engine), QuantConnect LEAN (C#, 4919 source files), binance-public-data (scripts, last commit 2025-01-09), dukascopy-node (Node), QuestDB, ClickHouse, TimescaleDB (covered in report 004), Feast (report 004), MACE (Gymnasium cost-model environments; found by web search), fastquant, TA-Lib (C library), alphalens-reloaded, pyfolio-reloaded, mlfinlab, original Quantopian zipline, arch, polars (used in report 004). Facts about these beyond the repo-health numbers above are DOCUMENTED_CLAIM/INFERENCE from memory or UNKNOWN; none was installed.
