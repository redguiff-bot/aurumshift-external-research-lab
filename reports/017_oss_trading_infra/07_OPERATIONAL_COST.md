# 07 — Operational footprint

Sources: `results/footprint.json` (installed distributions and site-packages size per shared venv — an upper bound per package), licences from installed metadata, architecture from execution.

| Group | Venv | Installed dists | site-packages | Notes |
|---|---|---|---|---|
| nautilus_trader | nautilus | 15 | 870 MB | Python ≥3.12; ships Rust/Cython binaries; also contains live adapters (runtime authority surface, not exercised) |
| vectorbt | vbt | 59 | 678 MB | plotly, sklearn, numba stack |
| zipline-reloaded | zipline | 64 | 503 MB | needs `ingest` bundle store on disk; exchange_calendars/tz incompatibility (below) |
| great_expectations | gx | 35 | 302 MB | heaviest DQ option |
| arcticdb | arctic | 12 | 197 MB | embedded LMDB dir; BSL 1.1 |
| backtesting.py | bktpy | 14 | 171 MB | AGPL-3.0 |
| core stack (hftbacktest, river, calendars, pandera, duckdb, polars, portfolio libs, backtrader, bt, ccxt…) | core | 159 | 1 836 MB | shared, not per-package |
| misc (quantstats, pandas-ta, arch, tsfresh, frictionless, pointblank, cryptofeed, yfinance) | misc | 123 | 842 MB | shared |
| ABIDES | abides (py3.9) | 16 | 315 MB | legacy pins |
| databento-dbn | dbn | 22 | 306 MB | |
| wraquant (py3.13) | wq13 | 23 | 464 MB | |
| nanobook | wq | 2 | 66 MB | |

## Services and datastores (executed set)
* Separate daemons required by executed candidates: **0** (everything is in-process; collectors need the remote venue only).
* Extra persistent stores introduced: ArcticDB (LMDB dir, or S3/Azure/Mongo), zipline (bundle ingest), DuckDB only if persisted. river state is picklable objects.
* Nothing executed requires a second *authoritative* database; ArcticDB and zipline would create one if used as system of record.

## Integration frictions actually met
* zipline-reloaded 3.1.1 + exchange_calendars 4.13.2: `run_algorithm` failed with tz-aware start/end (`Date must be timezone naive`) — worked with naive dates. Maintainer activity: 4 commits in 12 months, 1 author.
* PyPortfolioOpt `HRPOpt` broken on current SciPy. wraquant missing `polars` dependency and requires Python 3.13. ABIDES needs Python 3.9 and numpy 1.22. cryptofeed 3.x requires Python 3.13 and switched to AGPL.
* ccxt: CA-bundle handling (sandbox); forming-bar and no receipt timestamp.
* Python-version fragmentation: candidates required 3.9, 3.12 and 3.13 in one study → three interpreters.

## Licence hazards (DOCUMENTED_CLAIM from package metadata/LICENSE files)
LGPL-3.0+ (nautilus), GPL-3.0+ (backtrader, freqtrade), AGPL-3.0 (backtesting.py, cryptofeed 3.x), BSL 1.1 (ArcticDB), Apache-2.0 + Commons Clause (vectorbt). Legal interpretation is out of scope; internal research use is a different question from redistribution or hosting.

## Runtime authority
Executed libraries that ship live-trading/broker code in the same distribution: nautilus_trader (exchange adapters), nanobook (`IbkrBroker`), hftbacktest (live bot support, DOCUMENTED_CLAIM). Not-executed bots (hummingbot, freqtrade, vnpy, LEAN) are execution-authority frameworks by design. Using backtest-only components from these is possible but the dependency and import surface still includes them (INFERENCE).
