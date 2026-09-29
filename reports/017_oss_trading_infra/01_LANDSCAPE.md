# 01 — Landscape and screen

## Method
* Candidate discovery: enumerated per component class from the well-known OSS ecosystem (INFERENCE from prior knowledge, then checked against live upstream state — a name being on the list is not an endorsement). 67 candidates, of which some serve several classes.
* Metadata collected mechanically by `bench/oss_trading_infra_v1/py/screen.py` (blobless bare clone with `--shallow-since=2025-09-29`, PyPI JSON): commits and distinct authors in the last 12 months, share of the top author (bus-factor proxy), authors needed for 50 % of commits, last commit, licence file head, test-file paths (regex), CI files, PyPI release dates and `requires_dist`. Raw output: `bench/oss_trading_infra_v1/results/screen.json`.
* GitHub REST API returned 403 to the sandbox proxy; only git-protocol and PyPI were used.
* Not collected: ClickHouse (clone exceeded the time budget) and `pandas-ta` (upstream repository no longer reachable — `git ls-remote` asks for credentials); both are shown as "—".
* Screen limits: a commit count is not quality; a high commit count can be generated code (`ccxt`); "top author %" says nothing about who else can merge; test-file regex misses inline Rust tests (`hftbacktest`) and JS/C# layouts.

## Component classes and where the candidates fall
| Class | Candidates screened |
|---|---|
| market-data collectors | ccxt, cryptofeed, freqtrade, hummingbot, openbb, findatapy, nautilus_trader, vnpy |
| historical downloaders | binance-public-data, ccxt, tardis-python, databento-python, yfinance, pandas-datareader, LEAN |
| order-book libraries | hftbacktest, nautilus_trader, orderbook (dyn4mik3), ABIDES (2), cryptofeed, sortedcontainers |
| replay engines / event simulators | hftbacktest, nautilus_trader, ABIDES (2), LEAN |
| transaction-cost models | cvxportfolio, tcapy, hftbacktest (fee models), nautilus_trader (fee/fill models) |
| feature computation | TA-Lib, pandas-ta, ta, talipp, tsfresh, qlib, alphalens-reloaded, arch, DuckDB, polars |
| online statistics | river, tdigest, ddsketch, hdrhistogram, talipp, sortedcontainers |
| portfolio / risk | PyPortfolioOpt, Riskfolio-Lib, skfolio, cvxportfolio, bt, quantstats, empyrical-reloaded, pyfolio-reloaded, arch, pysystemtrade |
| backtest engines | vectorbt, backtrader, backtesting.py, zipline-reloaded, bt, qstrader, LEAN, vnpy, qlib, freqtrade, nautilus_trader, hftbacktest |
| market calendars | exchange_calendars, pandas_market_calendars, python-holidays, zipline-reloaded |
| data-quality frameworks | great_expectations, pandera, soda-core, pointblank, whylogs, frictionless-py, pydantic |
| time-series storage utilities | TimescaleDB, pg_partman, QuestDB, ClickHouse, DuckDB, ArcticDB, pyarrow, polars, VictoriaMetrics, InfluxDB, tstables |

## Screen table (all 67)
Licence column = what the repository LICENSE file / PyPI classifier says (OBSERVED); it is not a legal reading. "Executed" = EXEC (behavioural microtest), INSTALL (installed/imported only), NO (metadata only).

| Candidate | Classes | Language | Licence (as observed) | Commits 12 m | Authors 12 m | Top author % | Last commit | Last PyPI release | PyPI rel. 12 m | Test files (path regex) | Executed | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ccxt | COLL,DL | TypeScript/Python/PHP/C#/Go | MIT | 10126 | 113 | 50 | 2026-09-29 | 2026-09-24 | 76 | 2173 | EXEC | ADAPT_CANDIDATE |
| cryptofeed | COLL,OB | Python | AGPL-3.0-or-later (flag) | 39 | 4 | 74 | 2026-09-28 | 2026-09-27 | 3 | 22 | EXEC | ADAPT_CANDIDATE |
| binance-public-data | DL | Python/shell | no LICENSE file at HEAD (UNKNOWN) | 0 | 0 | — | 2025-01-09 | — | — | 0 | EXEC | ADOPT_REFERENCE |
| freqtrade | COLL,DL,BT | Python | GPL-3.0 (flag) | 3282 | 46 | 70 | 2026-09-29 | 2026-09-29 | 17 | 206 | NO | PARK |
| hummingbot | COLL,OB,SIM | Python/Cython | Apache-2.0 | 1733 | 41 | 27 | 2026-09-22 | — | — | 694 | NO | PARK |
| yfinance | DL | Python | Apache-2.0 | 319 | 50 | 54 | 2026-09-25 | 2026-08-26 | 12 | 105 | EXEC | PARK |
| openbb | DL,COLL | Python | Apache-2.0 | 135 | 21 | 73 | 2026-09-29 | 2026-09-29 | 6 | 1543 | NO | PARK |
| databento-python | DL | Python | Apache-2.0 | 157 | 10 | 73 | 2026-09-22 | 2026-09-22 | 27 | 114 | NO | PARK |
| tardis-python | DL | Python | MPL-2.0 | 35 | 2 | 66 | 2026-09-28 | 2026-09-28 | 14 | 10 | EXEC | ADAPT_CANDIDATE |
| pandas-datareader | DL | Python | BSD-3-Clause | 35 | 3 | 86 | 2026-07-21 | 2026-06-24 | 2 | 32 | NO | PARK |
| findatapy | DL,COLL | Python | Apache-2.0 | 11 | 1 | 100 | 2026-07-02 | 2026-03-20 | 2 | 9 | NO | PARK |
| hftbacktest | REPLAY,SIM,OB,TCM,BT | Rust/Python | MIT | 24 | 5 | 62 | 2025-12-23 | 2025-12-10 | 2 | 1 | EXEC | ADAPT_CANDIDATE |
| nautilus_trader | REPLAY,SIM,OB,BT,TCM,COLL | Rust/Python/Cython | LGPL-3.0-or-later (flag) | 5529 | 127 | 85 | 2026-09-29 | 2026-09-15 | 16 | 462 | EXEC | ADAPT_CANDIDATE |
| abides-jpmc-public | SIM,OB | Python | BSD-3-Clause | 0 | 0 | — | 2023-12-13 | — | — | 22 | EXEC | PARK |
| abides-gym-markets | SIM,OB | Python | BSD-3-Clause (GT) | 0 | 0 | — | 2020-11-19 | — | — | 9 | NO | REJECT |
| orderbook (dyn4mik3) | OB | Python | MIT | 1 | 1 | 100 | 2026-02-03 | 2013-12-31 | 0 | 2 | EXEC | REJECT |
| vectorbt | BT | Python/numba | Apache-2.0 + Commons Clause (not OSI) | 158 | 11 | 77 | 2026-09-26 | 2026-09-26 | 6 | 28 | EXEC | PARK |
| backtrader | BT | Python | GPL-3.0+ (flag) | 0 | 0 | — | 2023-04-19 | 2023-04-19 | 0 | 83 | EXEC | PARK |
| backtesting.py | BT | Python | AGPL-3.0 (flag) | 33 | 12 | 64 | 2026-08-05 | 2026-07-22 | 1 | 6 | EXEC | ADOPT_REFERENCE |
| zipline-reloaded | BT,CAL | Python/Cython | Apache-2.0 | 4 | 1 | 100 | 2025-11-13 | 2025-07-19 | 0 | 123 | EXEC | PARK |
| bt | BT,PORT | Python | MIT | 223 | 17 | 70 | 2026-09-27 | 2026-09-12 | 7 | 6 | EXEC | PARK |
| qstrader | BT | Python | MIT | 0 | 0 | — | 2024-06-24 | 2024-06-24 | 0 | 35 | INSTALL | PARK |
| pysystemtrade | BT,PORT | Python | GPL-3.0 (flag) | 189 | 15 | 69 | 2026-09-26 | — | — | 95 | NO | PARK |
| qlib | BT,FEAT,PORT | Python/Cython | MIT | 27 | 13 | 52 | 2026-09-16 | 2025-08-15 | 0 | 48 | NO | PARK |
| LEAN | BT,REPLAY,DL | C# | Apache-2.0 | 441 | 35 | 27 | 2026-09-28 | — | — | 1029 | NO | PARK |
| vnpy | BT,COLL | Python | MIT | 48 | 5 | 77 | 2026-08-06 | 2026-05-14 | 3 | 4 | NO | PARK |
| cvxportfolio | TCM,PORT,BT | Python | GPL-3.0 (flag) | 375 | 1 | 100 | 2026-04-27 | 2025-07-06 | 0 | 18 | EXEC | ADAPT_CANDIDATE |
| tcapy | TCM | Python | Apache-2.0 (per LICENCE file) | 0 | 0 | — | 2022-05-23 | — | — | 19 | NO | REJECT |
| PyPortfolioOpt | PORT | Python | MIT | 41 | 11 | 51 | 2026-07-08 | 2026-02-26 | 1 | 24 | EXEC | ADOPT_REFERENCE |
| Riskfolio-Lib | PORT | Python | BSD-3-Clause | 51 | 4 | 88 | 2026-09-24 | 2026-05-31 | 4 | 357 | EXEC | ADOPT_REFERENCE |
| skfolio | PORT | Python | BSD-3-Clause | 235 | 25 | 31 | 2026-09-29 | 2026-09-29 | 52 | 216 | EXEC | ADAPT_CANDIDATE |
| quantstats | PORT | Python | Apache-2.0 | 21 | 2 | 95 | 2026-09-27 | 2026-09-27 | 6 | 9 | EXEC | PARK |
| empyrical-reloaded | PORT | Python | Apache-2.0 | 0 | 0 | — | 2025-07-29 | 2025-06-01 | 0 | 11 | EXEC | ADOPT_REFERENCE |
| pyfolio-reloaded | PORT | Python | Apache-2.0 | 0 | 0 | — | 2025-06-02 | 2025-06-02 | 0 | 28 | NO | PARK |
| alphalens-reloaded | FEAT,PORT | Python | Apache-2.0 | 0 | 0 | — | 2025-06-02 | 2025-06-02 | 0 | 5 | NO | PARK |
| arch | PORT,FEAT | Python/Cython | NCSA | 113 | 7 | 79 | 2026-09-27 | 2025-10-21 | 1 | 39 | NO | PARK |
| TA-Lib (python) | FEAT | C/Cython | BSD-2-Clause | 57 | 9 | 61 | 2026-09-13 | 2026-09-21 | 5 | 7 | EXEC | ADOPT_REFERENCE |
| pandas-ta | FEAT | Python | unknown (repo gone) | — | — | — | — | 2025-09-14 | 0 | — | EXEC | REJECT |
| ta | FEAT | Python | MIT | 1 | 1 | 100 | 2026-03-18 | 2023-11-02 | 0 | 38 | EXEC | PARK |
| talipp | FEAT,ONLINE | Python | MIT | 0 | 0 | — | 2025-09-09 | 2025-09-09 | 0 | 63 | EXEC | ADAPT_CANDIDATE |
| tsfresh | FEAT | Python | MIT | 6 | 5 | 33 | 2026-07-06 | 2026-05-31 | 1 | 41 | NO | PARK |
| river | ONLINE,FEAT | Python/Rust | BSD-3-Clause | 299 | 38 | 59 | 2026-09-28 | 2026-08-21 | 7 | 143 | EXEC | ADOPT_REFERENCE |
| tdigest | ONLINE | Python | MIT | 0 | 0 | — | 2022-10-11 | 2019-05-07 | 0 | 1 | EXEC | PARK |
| sketches-py (ddsketch) | ONLINE | Python | Apache-2.0 | 1 | 1 | 100 | 2026-01-30 | 2024-04-01 | 0 | 6 | EXEC | ADOPT_REFERENCE |
| hdrhistogram (hdrh) | ONLINE | Python | Apache-2.0 | 6 | 4 | 50 | 2026-06-09 | — | — | 7 | EXEC | ADOPT_REFERENCE |
| exchange_calendars | CAL | Python | Apache-2.0 | 62 | 14 | 34 | 2026-09-14 | 2026-03-10 | 6 | 148 | EXEC | ADOPT_REFERENCE |
| pandas_market_calendars | CAL | Python | MIT | 100 | 14 | 43 | 2026-05-26 | 2026-05-27 | 12 | 43 | EXEC | PARK |
| python-holidays | CAL | Python | MIT | 690 | 83 | 23 | 2026-09-28 | 2026-09-28 | 70 | 313 | INSTALL | PARK |
| great_expectations | DQ | Python | Apache-2.0 | 528 | 59 | 35 | 2026-09-28 | 2026-09-25 | 37 | 815 | EXEC | PARK |
| pandera | DQ | Python | MIT | 267 | 56 | 21 | 2026-09-26 | 2026-09-01 | 15 | 207 | EXEC | ADAPT_CANDIDATE |
| soda-core | DQ | Python | Elastic License 2.0 (not OSI) | 264 | 16 | 34 | 2026-09-29 | 2026-09-23 | 26 | 238 | NO | REJECT |
| pointblank (python) | DQ | Python | MIT | 2105 | 8 | 92 | 2026-09-25 | 2026-08-13 | 14 | 251 | EXEC | PARK |
| whylogs | DQ | Python/Java | Apache-2.0 | 0 | 0 | — | 2025-01-10 | 2024-12-03 | 0 | 131 | NO | REJECT |
| frictionless-py | DQ | Python | MIT | 26 | 7 | 77 | 2026-09-25 | 2026-09-25 | 4 | 458 | EXEC | PARK |
| pydantic | DQ | Python/Rust | MIT | 659 | 133 | 43 | 2026-09-29 | 2026-09-09 | 22 | 358 | NO | PARK |
| TimescaleDB | TSS | C | Apache-2.0 core + Timescale License features (flag) | 1214 | 42 | 39 | 2026-09-29 | — | — | 2172 | EXEC | ADAPT_CANDIDATE |
| pg_partman | TSS | SQL/PLpgSQL | PostgreSQL License | 20 | 7 | 65 | 2026-08-22 | — | — | 91 | EXEC | ADOPT_REFERENCE |
| QuestDB | TSS | Java/Rust | Apache-2.0 | 867 | 35 | 20 | 2026-09-28 | — | — | 2676 | NO | PARK |
| ClickHouse | TSS | C++ | Apache-2.0 | — | — | — | — | — | — | — | EXEC | PARK |
| DuckDB | TSS,FEAT | C++ | MIT | 23579 | 359 | 15 | 2026-09-29 | 2026-09-28 | 90 | 6716 | EXEC | ADOPT_REFERENCE |
| ArcticDB | TSS | C++/Python | Business Source License 1.1 (not OSI) | 453 | 17 | 22 | 2026-09-28 | 2026-09-29 | 40 | 447 | EXEC | PARK |
| Apache Arrow (pyarrow) | TSS | C++/Python | Apache-2.0 | 1374 | 217 | 11 | 2026-09-29 | 2026-08-10 | 6 | 1023 | EXEC | ADOPT_REFERENCE |
| polars | TSS,FEAT | Rust/Python | MIT | 2379 | 201 | 15 | 2026-09-29 | 2026-09-20 | 30 | 718 | EXEC | ADOPT_REFERENCE |
| sortedcontainers | OB,ONLINE | Python | Apache-2.0 | 0 | 0 | — | 2024-03-01 | 2021-05-16 | 0 | 32 | INSTALL | PARK |
| VictoriaMetrics | TSS | Go | Apache-2.0 | 1555 | 104 | 21 | 2026-09-29 | — | — | 465 | NO | PARK |
| InfluxDB | TSS | Rust | Apache-2.0/MIT (per repo LICENSE) | 106 | 19 | 23 | 2026-09-18 | — | — | 113 | NO | PARK |
| tstables | TSS | Python | none found | 0 | 0 | — | 2015-10-10 | — | — | 3 | NO | REJECT |

## Reading the screen (OBSERVED, not a ranking)
* **Abandoned or frozen upstream (0 commits in 12 m):** backtrader (last release 2023-04), qstrader, tcapy (2022), whylogs, tdigest, talipp, empyrical-reloaded, pyfolio-reloaded, alphalens-reloaded, sortedcontainers, abides-*, tstables. Frozen is not the same as broken — `empyrical-reloaded`, `sortedcontainers` and `talipp` still behaved correctly in tests — but they carry no security/compat maintenance guarantee.
* **Bus-factor proxy ≥ 85 % of 12-month commits by one author:** cvxportfolio (100 %), zipline-reloaded (100 %, 4 commits), findatapy (100 %), ta (100 %), quantstats (95 %), pointblank (92 %), Riskfolio-Lib (88 %), nautilus_trader (85 %). Nautilus has 127 distinct authors yet one dominant committer.
* **Broadest maintainer base (top author < 35 %):** DuckDB, pyarrow, polars, python-holidays, pandera, great_expectations, QuestDB, VictoriaMetrics, skfolio, exchange_calendars, LEAN, hummingbot(27 %).
* **Runtime-authority candidates** (built to place live orders): freqtrade, hummingbot, nautilus_trader, LEAN, vnpy, pysystemtrade. Parked or constrained to backtest-only use in `08`.
