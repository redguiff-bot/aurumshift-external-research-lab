# 07 — Operational cost

## Isolated install footprint (`py/footprint.py`)
Each candidate installed **alone** into a fresh Python 3.11 venv (uv, warm cache, so install seconds are not meaningful and are omitted); size = `site-packages` MB; import time measured once in that venv.

| Candidate | Distributions installed (alone, fresh py3.11 venv) | site-packages MB | Import s | Import OK in isolation |
|---|---|---|---|---|
| hftbacktest | 43 | 735 | 1.17 | yes |
| nautilus_trader | 15 | 574 | 0.06 | yes |
| ccxt | 23 | 83 | 1.94 | yes |
| cryptofeed | 26 | 40 | 0.82 | yes |
| backtesting.py | 15 | 158 | 2.54 | yes |
| vectorbt | 59 | 622 | 8.05 | yes |
| backtrader | 1 | 2 | 0.49 | yes |
| bt | 43 | 389 | 6.44 | yes |
| zipline-reloaded | 64 | 464 | 6.29 | yes |
| cvxportfolio | 30 | 554 | 5.35 | yes |
| PyPortfolioOpt | 24 | 476 | 3.49 | NO: ModuleNotFoundError: No module named 'packaging' |
| Riskfolio-Lib | 85 | 963 | 8.45 | yes |
| skfolio | 19 | 358 | 4.33 | yes |
| river | 4 | 179 | 0.01 | yes |
| talipp | 1 | 1 | 0.01 | yes |
| ta | 5 | 100 | 1.3 | yes |
| TA-Lib | 2 | 85 | 0.29 | yes |
| ddsketch | 2 | 1 | 0.04 | yes |
| tdigest | 3 | 2 | 0.03 | yes |
| hdrhistogram | 3 | 5 | 0.02 | yes |
| exchange_calendars | 9 | 104 | 1.35 | yes |
| pandas_market_calendars | 10 | 104 | 1.51 | yes |
| pandera | 10 | 11 | 0.12 | yes |
| great_expectations | 35 | 267 | 6.72 | yes |
| frictionless-py | 39 | 35 | 0.46 | yes |
| pointblank | 47 | 145 | 1.08 | yes |
| DuckDB | 1 | 59 | 0.08 | yes |
| ArcticDB | 12 | 186 | 1.65 | yes |
| pyarrow | 1 | 152 | 0.07 | yes |
| polars | 2 | 177 | 0.46 | yes |
| tardis-python | 15 | 35 | 0.44 | yes |
| quantstats | 35 | 349 | 4.81 | yes |
| empyrical-reloaded | 8 | 216 | 3.26 | NO: ModuleNotFoundError: No module named 'pytz' |

Reading (OBSERVED): pure-Python leaf libraries are ≤ 5 MB (`backtrader` 2 MB, `talipp` 1 MB, `ddsketch` 1 MB, `tdigest` 2 MB, `hdrhistogram` 5 MB); numeric-stack candidates are 100–1 000 MB because numpy/pandas/scipy/numba/cvxpy come with them (vectorbt 622 MB and 8 s import; Riskfolio-Lib 963 MB; cvxportfolio 554 MB; hftbacktest 735 MB via numba/llvmlite; Nautilus 574 MB). Two libraries do **not** import in isolation because of undeclared dependencies: `PyPortfolioOpt` (`packaging`) and `empyrical-reloaded` (`pytz`).

## Services and datastores required
| Candidate | Extra running service | Extra datastore | Basis |
|---|---|---|---|
| tcapy | Redis, Celery workers, Memcached | MongoDB/Arctic/KDB/InfluxDB + MySQL/Postgres | README (DOCUMENTED_CLAIM) |
| QuestDB, ClickHouse (server), InfluxDB, VictoriaMetrics | yes (database server) | yes (own storage) | product nature; ClickHouse only run as `clickhouse-local` (866 MB single binary) |
| ArcticDB | no (library) | yes (LMDB/S3/Azure store) | OBSERVED with LMDB |
| zipline-reloaded | no | its own bundle directory (416 KB for 2 × 400 days) | OBSERVED |
| tstables | no | HDF5 file store | INFERENCE |
| TimescaleDB, pg_partman | **no new service** — extensions inside the existing PostgreSQL; need server restart (`shared_preload_libraries`) and package access | none | OBSERVED |
| DuckDB, polars, pyarrow | none | none unless Parquet files are kept (then they become a second copy of the data) | OBSERVED |
| Nautilus, hftbacktest, cryptofeed, ccxt, all pure libraries | none; cryptofeed/ccxt need outbound network | none required | OBSERVED |

## Runtime authority surface
* Live-order capable frameworks: nautilus_trader (live adapters ship with the wheel), freqtrade, hummingbot, LEAN, vnpy, pysystemtrade (IB). When used for replay only, the order-routing code is present but unused (INFERENCE).
* Pure libraries with no order authority: hftbacktest (simulation only), exchange_calendars, river, DuckDB, polars, pyarrow, cost/portfolio libraries, DQ libraries.

## Licences observed (not legal advice)
| Type | Candidates |
|---|---|
| permissive (MIT / BSD / Apache / PostgreSQL / NCSA / MPL-2.0 file-level) | ccxt, hftbacktest, river, exchange_calendars, pandera, DuckDB, polars, pyarrow, skfolio, PyPortfolioOpt, Riskfolio-Lib, TA-Lib, talipp, ta, ddsketch, hdrhistogram, tdigest, empyrical-reloaded, quantstats, zipline-reloaded, bt, pg_partman, tardis-python (MPL-2.0), arch (NCSA) |
| weak copyleft | nautilus_trader (LGPL-3.0-or-later) |
| strong copyleft | cryptofeed (AGPL-3.0-or-later), backtesting.py (AGPL-3.0), cvxportfolio, freqtrade, pysystemtrade (GPL-3.0), backtrader (GPL-3.0+) |
| source-available / non-OSI | vectorbt (Apache-2.0 + Commons Clause), ArcticDB (BSL 1.1), soda-core (Elastic License 2.0), TimescaleDB features used here (Timescale License; core Apache-2.0) |
| no licence file found | binance-public-data, tstables |
Whether any of these terms constrains AurumShift depends on how it would be used (offline oracle vs linked into a service) and on AurumShift's own licensing, which this study cannot see: **UNKNOWN**.

## Maintenance risk (from `01`)
Single-maintainer or frozen with an ADAPT/ADOPT tag: cvxportfolio (100 % one author, 375 commits, last release 2025-07), hftbacktest (slowing: last commit 2025-12), talipp (last release 2025-09), ddsketch (last release 2024-04), empyrical-reloaded (stable, 0 commits), cryptofeed (39 commits, top author 74 %). These remain usable as pinned, vendored-reference code but need an owner if adapted.

## Operator-relay cost (INFERENCE from what had to be done here)
Pure-library candidates worked on `pip install`; the ones that needed operator knowledge: TimescaleDB (repo + preload + restart), ABIDES (Python 3.9 + 2020 pins), ccxt behind a TLS-terminating proxy (`validateServerSsl` path), cryptofeed on py3.11 (event-loop line), numba first-call JIT (22 s in vectorbt, seconds in hftbacktest), DuckDB first-use extension download.
