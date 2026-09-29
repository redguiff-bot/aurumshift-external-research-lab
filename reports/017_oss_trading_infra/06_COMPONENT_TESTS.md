# 06 — Component tests: catalogue, oracles, reproduction

Every test below lives in `bench/oss_trading_infra_v1/` and wrote its raw output to `results/`. "Oracle" = what the result was compared to. Tests that had no independent oracle are labelled OBSERVED, not PROVEN.

| # | Test | Script → result | Oracle | Candidates | Outcome |
|---|---|---|---|---|---|
| T1 | Same rule, five bar engines | `py/mt/bt_engines.py` → `bt_engines.json` | 20-line numpy loop | backtesting.py, backtrader, vectorbt, bt, qstrader | 3 of 3 comparable engines agree (57 trades; P&L ≤ 6e-5); bt not comparable; qstrader import only |
| T2 | Look-ahead probe | `leak_probe.py` → `leak_probe.json` | known future array | backtesting.py, backtrader, vectorbt | no engine detects a peeking array; backtrader preloaded exposes `data.close[1]` |
| T3 | L2 queue/latency/fee replay | `hft_microtest.py` → `hft_microtest.json` | hand derivation | hftbacktest | fill 8.0 s; latency respected; fee booked; deterministic; ~11 M events/s |
| T4 | L2 replay + fills | `naut_microtest.py`, `naut_cross_probe.py`, `naut_l1_probe.py` → `naut_microtest.json` | hand derivation | nautilus_trader | book-cross fills OK; print-driven passive fill not reproduced (9 configs); deterministic; ~350 k quotes/s |
| T5 | Agent-based simulator | `abides_microtest.py` → `abides_microtest.json` | seed repeatability | abides-jpmc-public | runs on py3.9 pins only; deterministic per seed |
| T6 | Matching engine | `orderbook_microtest.py` → `orderbook_microtest.json` | FIFO by hand | dyn4mik3/OrderBook | HEAD matches FIFO, has an API bug, PyPI wheel broken |
| T7 | Daily engine + calendar gate | `zl_microtest.py` → `zl_microtest.json` | source constants; ingest assertion | zipline-reloaded | deterministic; weekend bars rejected at ingest |
| T8 | Online statistics | `stats_microtest.py` → `stats_microtest.json` | numpy/pandas exact | river, tdigest, ddsketch, hdrhistogram | errors 1e-21…1e-2 (within claimed bounds for sketches) |
| T9 | Streaming vs batch indicators | `stats_microtest.py`, `feat_microtest.py` → `feat_microtest_*.json` | ta / pandas ewm / TA-Lib | talipp, ta, TA-Lib, pandas-ta | parity ≤ 2.8e-6 after warm-up; SMA-seed EMA divergence 2.4e-3 early |
| T10 | Portfolio optimisers + metrics | `port_microtest.py` → `port_microtest.json` | SLSQP; numpy | PyPortfolioOpt, Riskfolio-Lib, skfolio, empyrical-reloaded, quantstats | ≤ 3e-5 (weights), ≤ 1e-15 (metrics) |
| T11 | Cost-model scaling | `tcm_microtest.py` → `tcm_microtest.json` | closed form (10 bps; 4^1.5) | cvxportfolio | exactly 10 bps; ×4.000; ×8.000 |
| T12 | Calendars | `cal_microtest.py` → `cal_microtest.json` | known holidays/early closes/DST | exchange_calendars, pandas_market_calendars | identical sessions/early closes; dates correct |
| T13 | DQ vs injected faults | `dq_microtest.py` → `dq_microtest.json` | plain-pandas counts | pandera, great_expectations, frictionless | see `02` |
| T14 | DQ (polars) + misc | `misc_microtest.py` → `misc_microtest.json` | injected failures | pointblank, yfinance, tardis-python | 2/1/1 failures; yfinance 5 rows; Tardis free sample 131 910 rows |
| T15 | Collectors | `coll_microtest.py` → `coll_microtest.json` | HTTP/WS success, timestamp semantics | ccxt, cryptofeed | see `02` |
| T16 | Bulk downloader | (repo script run in `/tmp`, output inspected) → described in `02` | sha256 of CHECKSUM | binance-public-data | checksum verified by us; not by the script |
| T17 | PG storage | `sql/tss_microtest.sql` → `results/tss_microtest.txt` | md5 of aggregated bars across layouts | TimescaleDB, pg_partman, native partitioning | equal bars; 13.5× compression (TSL); 1.8× faster query |
| T18 | ASOF / Parquet / PG attach / versioned store | `store_microtest.py` → `store_microtest.json` | pandas `merge_asof` | DuckDB, polars, pyarrow, ArcticDB | equal joins; 0 violations; identical Parquet bytes; PIT versions |
| T19 | ClickHouse ASOF | `sql/clickhouse_local_asof.sql` → `results/clickhouse_local_asof.txt` | hand table | ClickHouse (local) | semantics right; unmatched → 0 |
| T20 | Isolated footprint | `py/footprint.py` → `footprint.json` | — | 33 packages | `07` |
| T21 | Metadata screen | `py/screen.py` → `screen.json` | — | 67 candidates | `01` |

## Reproduce
```
pip install uv
cd bench/oss_trading_infra_v1/py && python screen.py           # network: git + pypi.org
# per-group venvs: see env/freeze_*.txt (exact versions used), e.g.
uv venv /tmp/venvs/hft --python 3.11 && VIRTUAL_ENV=/tmp/venvs/hft uv pip install -r ../env/freeze_hft.txt
cd /tmp && PYTHONPATH=<repo>/bench/oss_trading_infra_v1/py/mt /tmp/venvs/hft/bin/python <repo>/bench/oss_trading_infra_v1/py/mt/hft_microtest.py
```
Notes: run hftbacktest/numba tests from a directory that is **not** inside the installed package (a `types.py` in the cwd shadows the standard library). ABIDES needs Python 3.9. pandas-ta needs Python ≥ 3.12. The PostgreSQL test needs `shared_preload_libraries='timescaledb'` and a data directory owned by the `postgres` user. `coll_microtest.py` needs the sandbox CA path (`/root/.ccr/ca-bundle.crt`) replaced by your own trust store. Results that depend on the network (T14–T16) depend on the egress and the wall-clock.

## Pitfalls encountered while testing (my errors are listed too)
* I first wrote the backtrader test without registering the strategy (0 trades) — fixed and re-run; the reported numbers are from the corrected script.
* My first `backtesting.py` "future index" probe used a positive index, which in that library is an *absolute past* index, not the future; replaced by `Close[len(data)]`.
* My first `talipp`-vs-`ta` EMA run compared from the first bar; the SMA-seed divergence is a real library convention, not a bug in either.
* `pandas-ta` run with TA-Lib installed is not an independent check (it delegates); the reported parity is from a venv without TA-Lib.
* `frictionless` initially returned `resource-error: path is not safe` because of an absolute path — re-run with a relative path.
