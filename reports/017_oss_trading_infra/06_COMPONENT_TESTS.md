# 06 — Component test register

Every test: script in `bench/oss_trading_infra_v1/py/`, raw output in `results/`, reproducible with `setup_envs.sh` + `run_all.sh` (network tests are time-dependent).

| ID | Question | Method | Result (verdict per candidate) |
|---|---|---|---|
| T01 | Is the L2 book exact? | 200 k seeded level events, SHA-256 of full depth vs dict reference | nautilus, hftbacktest, sortedcontainers PASS |
| T02/T02b | Deterministic replay? latency? fills at touch? | 100 k quotes × 2 processes; LatencyModel 0/250 ms | nautilus PASS (identical digest); latency opt-in |
| T03/T03z | Do fills, fees, slippage equal the analytic answer? | Fixed 2-order schedule, 6 engines | vectorbt, backtrader, zipline PASS; backtesting.py +5.6 (exit spread); bt not comparable (no slippage, 99 sh) |
| T04 | Is the engine causal? | Prefix invariance + leaky control | vectorbt, backtesting.py, backtrader, bt PASS; controls detected |
| T05 | Are indicators causal? | Prefix invariance over all outputs | ta 5/91 fail (warm-up backfill), pandas-ta 9/271 fail, vectorbt 0/8, tsfresh 0/10 |
| T06 | Online stats accurate/restorable? | vs numpy/pandas/exact windows, pickle | river PASS; rolling var = pandas' precision |
| T07 | Portfolio/metrics known answers | closed-form min-var; hand metrics | PyPortfolioOpt, riskfolio, skfolio PASS; PyPortfolioOpt HRP crash; quantstats VaR parametric |
| T08 | Calendars vs known answers | NYSE 2024–25 holidays/early closes/DST | both PASS 100 % |
| T09 | Data-quality detection | 12 defects × 4 frameworks | pandera, GX, pointblank 12/12; frictionless 5/12 |
| T10 | Storage versioning/PIT semantics | ArcticDB vs DuckDB/Parquet | ArcticDB versions OK but destructive ops + BSL + second store; DuckDB no versioning |
| T11 | Real collection | ccxt REST/WS, cryptofeed, yfinance | ccxt 6/8 venues (2 egress-blocked), cryptofeed 25 trades + 3 991 book updates with receipt ts, yfinance OK |
| T12a | Queue-position realism | known-answer queue scenario | hftbacktest PASS (4 queue models; not discriminative) |
| T12b | Volume-share slippage formula | 500-sh order, partial fills | zipline PASS (needs 3-dp price rounding) |
| T12c | Book-walking market order | 3 levels | nautilus PASS (needs `OrderBookDeltas` wrapper) |
| T13 | Agent-based simulator reproducible? | rmsc04, 3 runs | ABIDES PASS in py3.9 pinned env |
| T14 | DBN record timestamps | offline roundtrip | PARTIAL (fields seen; roundtrip UNKNOWN) |
| T15 | Almgren–Chriss known answer | linear + sinh formula | wraquant PASS (trivial formula, no calibration) |
| T16 | Matching engine vs FIFO reference | 20 k orders | nanobook PASS |

## Defects in our own harness found and fixed during the run (kept for transparency)
1. T01 hftbacktest first run mismatched — tester's read loop, not the engine.
2. T03 backtesting.py first run used `spread=2·slip` (wrong mapping); bt first version rebalanced daily (many trades).
3. T04 initial `shift(-1)` leak was nearly invisible to prefix tests → replaced by a 5-bar leak.
4. T06 first rolling-variance comparison used pandas as reference (identical error) → replaced by exact window variance.
5. T09 frictionless clean run failed on path safety → `basepath` set.
6. T12b expected price first ignored 3-dp storage and the exact share definition; both derived from source and data, not fitted afterwards (rounding hypothesis then confirmed at 1.4e-14).

## Not tested (explicit)
Multi-day live collection stability, memory growth, Windows, nautilus/hftbacktest on real L2/L3 archives, ArcticDB on S3, PIT properties of any project under provider revisions, IBKR/other broker adapters (deliberately not touched), any paid API.
