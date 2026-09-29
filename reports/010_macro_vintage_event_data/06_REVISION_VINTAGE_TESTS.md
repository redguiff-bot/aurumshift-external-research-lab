# 06 — Revision / vintage / lookahead tests

## 6.1 Concrete "today vs known at T" (`results/asof_vs_today.json`; FRED CSV fetched 2026-09-29 vs ALFRED vintage T)
| Series | Obs | As-of T | Known at T (ALFRED) | Returned today (FRED CSV) | Diff |
|---|---|---|---|---|---|
| PAYEMS | 2020-04 | 2020-06-15 | 130403 | 130426 | +23 |
| PAYEMS | 2022-12 | 2023-01-20 | 153743 | 154342 | +599 |
| INDPRO | 2020-04 | 2020-05-20 | 92.5919 | 84.5619 | −8.03 (base change included) |
| INDPRO | 2022-03 | 2022-04-20 | 104.5853 | 101.3907 | −3.19 (base change included) |
| CPIAUCSL | 2022-06 | 2022-07-20 | 295.328 | 294.957 | −0.371 |
| GDPC1 | 2020-Q2 | 2020-08-01 | 17205.822 | 19077.992 | +1872 (base change dominates) |
| GDP (nominal) | 2020-Q2 | 2020-08-01 | 19408.759 | 19958.291 | +549.5 (no base issue: +2.8%) |
| UNRATE | 2020-04 | 2020-06-01 | 14.7 | 14.8 | +0.1 |
**LOOKAHEAD_FROM_LATEST_VALUE = PROVEN**: querying today (FRED CSV) returns values that did not exist at T for all 8 cases.

## 6.2 Distribution over 2018-01 → 2025-12 releases (`lookahead_latest_vs_firstprint.json`, `lookahead_scalefree.json`)
n = number of releases in which a new newest observation appeared (vintage snapshot ≥ new obs). "Latest" = last ALFRED vintage (2026-08-26…09-18).
| Series | n | first print ≠ today | median |Δ MoM/QoQ %-change| first vs today | max | sign of change flips |
|---|---|---|---|---|---|
| PAYEMS | 95 | 100% | 0.046 pp | 0.46 pp | 3 |
| INDPRO | 95 | 100% | 0.25 pp | 1.94 pp | 16 |
| CPIAUCSL (SA) | 94 | 100% | 0.044 pp | 0.22 pp | 6 |
| UNRATE | 95 | 42% | (rate; % of a rate — not meaningful) | – | 0 |
| GDPC1 | 32 | 100% | 0.16 pp | 1.62 pp | 1 |
Scale-free metric = % change computed within each vintage's own base, so base-year re-referencing of levels does not contaminate it. Level-based stats are also stored but include rebasing (do not read them as revision size).
Example flips (PAYEMS): Aug-2025 first-print change +22k vs −70k today; Jun-2025 +147k → −20k; Jan-2025 +143k → −48k (thousands of persons, month-over-month change).

## 6.3 Method caveats
- ALFRED "latest" is date-limited (2026-09-04 for PAYEMS): today is itself not final (benchmarking continues).
- First-appearance vintage found by bisection (assumes monotone appearance; verified on samples only).
- Single-vintage calls (0.25 s throttle); no bulk POST (HTTP 500).
