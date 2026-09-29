# 00 — Executive summary

Mission `AURUMSHIFT_EXTERNAL_OSS_TRADING_RESEARCH_INFRA_DISCOVERY_V1` — external research only; no private AurumShift code read; no integration proposed. Run date (sandbox clock) 2026-09-29. Labels per `claude.md`.

## What was done
* 54 OSS projects catalogued across 13 component classes; 32 installed and exercised with 16 microtests (T01–T16) on synthetic or live-public data, in 12 isolated virtualenvs (3 Python versions). Maintenance/bus-factor/test presence computed from git history of 35 repositories. Stars unused.
* Every ranking-relevant statement traces to `bench/oss_trading_infra_v1/results/` or is labelled INFERENCE/DOCUMENTED_CLAIM/UNKNOWN.

## Findings (OBSERVED unless noted)
1. **Order books and replay are solved by OSS, and verified.** nautilus_trader, hftbacktest and nanobook reproduce reference books/matching exactly; nautilus replay is bit-identical across processes; hftbacktest queue-position and maker rebate follow the known answer; nautilus walks an L2 book exactly (avg 101.00). None provides PIT/revision semantics.
2. **Backtest engines agree with hand PnL only if their fill convention is understood.** vectorbt, backtrader and zipline match to ≤1e-9 (same-bar close, next open, next close respectively); backtesting.py deviates by +5.6 on a 1 800 PnL through an unapplied exit spread; bt has no slippage and sized 99 not 100. All four engines tested for causality passed prefix invariance.
3. **Indicator libraries leak silently.** ta: 5/91 columns back-fill warm-up with future values; pandas-ta: 9/271 (centered DPO, Ichimoku chikou, full-sample regression bands). vectorbt (8) and tsfresh rolling (10) had none.
4. **Utilities that are ready today:** exchange_calendars and pandas_market_calendars (100 % on NYSE holiday/early-close/DST known answers), river (accurate, picklable, deterministic), PyPortfolioOpt/skfolio/riskfolio (closed-form agreement 3e-10 … 7.6e-5), pandera/GX/pointblank (12/12 injected defects).
5. **Collection:** ccxt gives a uniform OHLCV schema on 6/8 venues (2 egress-blocked) but returns the forming bar unflagged and has no receipt time; cryptofeed provides receipt timestamps natively but its latest release is AGPL and Python ≥3.13.
6. **Cost models are parametric.** zipline volume-share slippage reproduces its formula to 1e-14 (default bundles quantise prices to 3 decimals); Almgren–Chriss in OSS is a ten-line formula without calibration. No executed project estimates costs from data.
7. **No OSS store gives enforced append-only PIT with server-side receipt time.** ArcticDB versions well (as-of by version/time) but has destructive prune/delete, client-side version time, BSL licence and is a second datastore; DuckDB/Parquet has no versioning.
8. **Maintenance is uneven:** backtrader (no commit since 2023-04), ABIDES (2023-12), empyrical-reloaded (0 commits/12 m), zipline-reloaded (4 commits, 1 author); of the 26 executed projects with cloned history, 16 have bus factor 1 by the 50 % proxy and 3 had no commits in 12 months.
9. **Compatibility rot is real:** PyPortfolioOpt HRP crashes on current SciPy; zipline-reloaded fails with exchange_calendars 4.13.2 on tz-aware dates; wraquant misses a dependency; ABIDES needs Python 3.9.

## Adjudication
ADOPT_REFERENCE 9 · ADAPT_CANDIDATE 5 · PARK 32 · REJECT 8 (see `08_ADJUDICATION.md`). No "best framework" is claimed; classes are per capability.

## Limits that matter
Discovery not exhaustive (GitHub search blocked); synthetic data; one configuration per test; AurumShift compatibility UNKNOWN by boundary (see `09`).

## Final block
```
PROJECTS_DISCOVERED=54
PROJECTS_EXECUTED=32   (31 with a completed microtest, 1 partial: databento-dbn)

ADOPT_REFERENCE_COUNT=9
ADAPT_CANDIDATE_COUNT=5
PARK_COUNT=32
REJECT_COUNT=8

SECOND_SERVICE_REQUIRED_CANDIDATES=5   (QuestDB, ClickHouse, Feast, hummingbot, freqtrade; none executed)
SECOND_DATASTORE_REQUIRED_CANDIDATES=7 (ArcticDB, zipline bundle, QuestDB, ClickHouse, Feast, freqtrade, hummingbot; DuckDB only if persisted)

ANY_DROP_IN_COMPONENT=YES (library level only: exchange_calendars, pandas_market_calendars; AurumShift fit UNKNOWN by boundary)

FINAL_VERDICT=MULTIPLE_OSS_COMPONENTS_SUPPORTED
```
