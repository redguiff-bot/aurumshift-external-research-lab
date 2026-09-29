# 08 — Adjudication

Classes: **ADOPT_REFERENCE** = safe to use as library/oracle/spec with little coupling; **ADAPT_CANDIDATE** = useful, needs wrapping/adaptation/data conversion or a pinned version; **PARK** = revisit on trigger; **REJECT** = not for this purpose. No "best framework" is claimed; classes are per capability. AurumShift compatibility is UNKNOWN by boundary and is not asserted.

## Executed (32)
| Project | Capability | Class | Decisive evidence | Watch-outs |
|---|---|---|---|---|
| exchange_calendars | calendars | ADOPT_REFERENCE | T08 100 %; Apache; 62 commits/12 m, 14 authors | rolling ±1 y default window |
| pandas_market_calendars | calendars (24/7, CME, FX) | ADOPT_REFERENCE | T08 100 %; 211 calendars; MIT | cross-check against exchange_calendars |
| river | online statistics, drift | ADOPT_REFERENCE | T06; state picklable; BSD | rolling var precision = pandas; API drift (`EWMean`, `Rolling`) |
| nautilus_trader | replay / fills / latency / L2 book (semantic oracle) | ADOPT_REFERENCE | T01, T02, T12c | LGPL, 870 MB, top author 85 %, live adapters in wheel; component reuse would be ADAPT |
| hftbacktest | L2/L3 book, queue, latency | **ADAPT_CANDIDATE** | T01, T12a | event-array conversion; last commit 2025-12; 1 Python test file; BF 1 |
| duckdb | offline replay/analytics engine | ADOPT_REFERENCE | T10; MIT | no versioning; `ASOF JOIN` PIT hazard (004) |
| sortedcontainers | reference book structure | ADOPT_REFERENCE | T01 baseline | no releases since 2021 (stable) |
| vectorbt | vectorised backtest as independent oracle | ADOPT_REFERENCE | T03 exact, T04 causal | Commons Clause; fills at caller-chosen price only |
| PyPortfolioOpt | mean-variance | ADOPT_REFERENCE | T07 3e-10 | HRP broken on current SciPy |
| pandera | schema/DQ checks in code | **ADAPT_CANDIDATE** | T09 12/12, 0.11 s | rules (monotonic, OHLC relations, gaps) must be authored |
| skfolio | portfolio/risk estimators | **ADAPT_CANDIDATE** | T07, sklearn API, 25 authors | 7.6e-5 solver tolerance |
| ccxt | REST/WS collection, unified schema | **ADAPT_CANDIDATE** | T11 6/8 venues | drop forming bar; add receipt stamp; CA handling; per-venue quirks (005) |
| cryptofeed (≤2.x) | WS collection with receipt timestamps | **ADAPT_CANDIDATE** | T11 | 3.x is AGPL + py3.13; BF 1 |
| zipline-reloaded | slippage/commission models | PARK | T03z, T12b exact | 4 commits/12 m, 1 author; tz break; 3-dp prices; ingest store |
| backtesting.py | single-asset backtest | PARK | T03 +5.6 exit | AGPL; single instrument |
| bt | allocation backtest | PARK | T04 causal | no slippage; sizing reserve |
| backtrader | backtest | **REJECT** | T03 exact, T04 causal | GPL-3.0, no commit since 2023-04 |
| ta | indicators | PARK | T05 5/91 leaky warm-up | 1 commit/12 m; usable only with allow-list |
| pandas-ta | indicators | **REJECT** | T05 9/271 leaky incl. full-sample regression | beta; licence metadata empty; upstream repo not resolved |
| tsfresh | rolling feature extraction | PARK | T05 causal | slow; 6 commits/12 m |
| riskfolio-lib | portfolio/risk | PARK | T07 3e-6 | 1 test file; 88 % single author |
| empyrical-reloaded | metrics | PARK | T07 exact | 0 commits in 12 m |
| quantstats | tear-sheets | PARK | T07 | parametric VaR default; 96 % single author |
| great_expectations | DQ suites | PARK | T09 12/12 | 35 dists/302 MB; equal detection to lighter tools |
| pointblank | DQ | PARK | T09 12/12 | 1.33 s/200 k rows; 92 % single author; project < 2 y |
| frictionless | table validation | PARK | T09 5/12 | no sequence/cross-column checks |
| arcticdb | versioned TS store | PARK | T10 | BSL 1.1; second datastore; destructive prune/delete; client-side version time |
| yfinance | daily/1m fallback | PARK | T11 | unofficial endpoint (report 005) |
| ABIDES-JPM | agent-based scenarios | PARK | T13 reproducible | dormant since 2023-12, py3.9 pins |
| nanobook | matching engine | PARK | T16 exact | young, bundled broker code |
| databento-dbn | record format | PARK | T14 partial | roundtrip unproven; paid client |
| wraquant | Almgren–Chriss | **REJECT** | T15 formula only | py≥3.13, undeclared dep, no calibration, 4 releases |

## Discovered, not executed (22) — evidence limited to repo-health numbers and documentation
ADOPT_REFERENCE (1): binance-public-data (file-layout spec; execution covered by report 005; dormant since 2025-01).
REJECT (5, scope/authority/licence/maintenance — INFERENCE for licence facts from memory): hummingbot (live trading framework), freqtrade (GPL-3.0, live bot), fastquant (no release since 2023-01), mlfinlab (proprietary distribution — INFERENCE), original Quantopian zipline (archived — INFERENCE).
PARK (16): vnpy, qlib, pysystemtrade, rqalpha, QuantConnect LEAN, dukascopy-node, QuestDB, ClickHouse, TimescaleDB (report 004), Feast (report 004), MACE, TA-Lib, alphalens-reloaded, pyfolio-reloaded, arch (installed, not tested), polars (used in report 004).

## Counts
| Class | Executed | Not executed | Total |
|---|---|---|---|
| ADOPT_REFERENCE | 8 | 1 | **9** |
| ADAPT_CANDIDATE | 5 | 0 | **5** |
| PARK | 16 | 16 | **32** |
| REJECT | 3 | 5 | **8** |
| **Total** | 32 | 22 | **54** |

## Capability coverage after the study
* Covered by ≥1 candidate that passed a known-answer test: calendars, online statistics, L2 book, queue-aware replay, deterministic event replay, vectorised/event backtest oracles, parametric cost models, mean-variance/CVaR portfolios, DQ rule checks, collection with receipt time (cryptofeed), unified REST OHLCV (ccxt).
* **Not covered by any OSS candidate tested:** append-only PIT/revision store with server-side receipt time; empirical (data-calibrated) transaction-cost/impact estimation; causal-by-construction indicator library without an allow-list; a licence-clean streaming collector for current Python.

## Second service / second datastore / drop-in
* SECOND_SERVICE_REQUIRED (whole set, 54): QuestDB, ClickHouse, Feast, hummingbot, freqtrade = **5** (none executed).
* SECOND_DATASTORE_REQUIRED: ArcticDB, zipline bundle, QuestDB, ClickHouse, Feast, freqtrade (SQLite), hummingbot (SQLite) = **7**; DuckDB only if persisted.
* Drop-in (library-level only, no wrapper beyond `pip install`, known-answer pass, permissive licence, no service): exchange_calendars, pandas_market_calendars. river and pandera are near drop-in but need rule/semantics authoring. Whether any fits AurumShift is UNKNOWN by boundary.
