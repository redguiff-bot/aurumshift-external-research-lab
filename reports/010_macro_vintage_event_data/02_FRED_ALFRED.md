# 02 — FRED / ALFRED

Scripts: `bench/macro_vintage_v1/py/alfred_test.py`, `alfred_paths.py`; results `results/alfred_lookahead.json`, `results/alfred_paths.json`.

## What was and was not executed
* **FRED API (`api.stlouisfed.org`, `realtime_start/realtime_end`, `output_type`)** — NOT executed with data: every call returns `400 … api_key is not set`; no key exists in this environment (PROVEN: `raw/fred_api_nokey`). Its vintage semantics are therefore only DOCUMENTED_CLAIM here; nothing about them is asserted.
* **FRED web CSV (`fredgraph.csv`)** — executed. It **ignores** `vintage_date` and returns the latest history (PROVEN, `results/alfred_paths.json → traps.fredgraph_vintage_date_ignored`: GDPC1 with `vintage_date=2009-01-30` returns 16485.350 for 2008-10-01, not 11599.4).
* **ALFRED web CSV (`alfred.stlouisfed.org/graph/alfredgraph.csv?id=…&vintage_date=YYYY-MM-DD`)** — executed and behaves as a true as-of query. This is an **undocumented-to-us web endpoint**, not the documented API (INFERENCE: it is the endpoint behind the ALFRED graph/download UI).
* **ALFRED vintage list** — the `series/downloaddata?seid=…` page lists every vintage date (418 for GDPC1, 859 PAYEMS, 669 CPIAUCSL, 1223 INDPRO, 799 UNRATE). The form POST for bulk files (`file_type` 1–4, csv/xlsx) returned HTTP 500 for my requests (cause UNKNOWN; not pursued), so bulk "observations by real-time period" files were not obtained.

## Semantics proven (OBSERVED, executed)
1. `vintage_date=T` returns the series as ALFRED held it at the last vintage ≤ T. Four checks (GDPC1@2009-02-15, PAYEMS@2014-10-10, CPIAUCSL@2022-07-15, INDPRO@2019-06-10): result equals the fetch at the previous vintage date and differs from the next vintage's (4/4).
2. T before a series' first vintage → HTTP 404 (empty), not a silent latest fallback (GDPC1 @1985/1991-12-01, PAYEMS @1950).
3. **Silent-failure traps**: (a) a future `vintage_date` (2026-12-31) returns today's latest, column labelled `_20260929`; (b) `realtime_start/realtime_end` on `alfredgraph.csv` are ignored (returns latest); (c) multiple vintages via comma → only the first is honoured, via repeated param → only the last. One vintage per call.
4. Output column name carries the vintage (`GDPC1_20090130`); no timestamp, no release id, no preliminary/final flag, no revision reason.
5. Vintage depth varies by series: DCOILWTICO first vintage 2011-04-06, PCEPI 2000-08-01, GDPC1 1991-12-04, PAYEMS 1955-05-06.
6. `WCESTUS1` (weekly crude stocks) is **not on FRED/ALFRED** (HTML error page, 0 vintages); EIA weekly stocks must come from EIA, which has no vintages.

## Series tested
GDPC1, PAYEMS, CPIAUCSL, CPIAUCNS (never-revised control), INDPRO, UNRATE, PCEPI, DCOILWTICO and DFF (controls). See 06 for numbers.

## Verdict
ALFRED (via web CSV) = **PIT_NATIVE at date granularity**. Not a drop-in: one-vintage-per-call, undocumented endpoint, no intraday release time, no key-based contract executed.
