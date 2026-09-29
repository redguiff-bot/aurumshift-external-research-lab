# 06 — Revision / vintage tests and look-ahead proof

Executed against ALFRED (vintage) and FRED (latest) web CSV endpoints; every row is one live call pair, receipts in `results/alfred_lookahead.json`.

## A. Value known at T vs today's value for the same observation
`known@T` = last observation returned by ALFRED `vintage_date=T`; `latest` = same observation from `fredgraph.csv` on 2026-09-29. *Level* differences for GDPC1 / INDPRO / PCEPI are inflated by base-year/rebasing (chained-dollar and index re-referencing) — the **growth** columns remove that effect.

| series | T | vintage used | obs | known@T | latest | latest−known | growth% @T | growth% latest |
|---|---|---|---|---|---|---|---|---|
| GDPC1 | 2009-02-15 | 2009-01-30 | 2008-10-01 | 11599.4 | 16485.35 | 4885.95 | -0.965 | -2.189 |
| GDPC1 | 2011-08-15 | 2011-07-29 | 2011-04-01 | 13270.1 | 17035.114 | 3765.014 | 0.319 | 0.677 |
| GDPC1 | 2013-08-15 | 2013-07-31 | 2013-04-01 | 15648.7 | 17709.671 | 2060.971 | 0.416 | 0.268 |
| GDPC1 | 2018-08-15 | 2018-07-27 | 2018-04-01 | 18507.2 | 20150.476 | 1643.276 | 1.000 | 0.531 |
| PAYEMS | 2009-01-12 | 2009-01-09 | 2008-12-01 | 135489.0 | 134847.0 | -642.0 | -0.385 | -0.512 |
| PAYEMS | 2009-03-12 | 2009-03-06 | 2009-02-01 | 133768.0 | 133318.0 | -450.0 | -0.484 | -0.568 |
| PAYEMS | 2014-10-10 | 2014-10-03 | 2014-09-01 | 139435.0 | 139563.0 | 128.0 | 0.178 | 0.211 |
| PAYEMS | 2020-05-11 | 2020-05-11 | 2020-04-01 | 131045.0 | 130426.0 | -619.0 | -13.548 | -13.565 |
| CPIAUCSL | 2009-01-20 | 2009-01-16 | 2008-12-01 | 211.49 | 211.398 | -0.092 | -0.737 | -0.823 |
| CPIAUCSL | 2015-03-01 | 2015-02-26 | 2015-01-01 | 234.677 | 234.747 | 0.07 | -0.680 | -0.637 |
| CPIAUCSL | 2022-07-15 | 2022-07-13 | 2022-06-01 | 295.328 | 294.957 | -0.371 | 1.322 | 1.256 |
| CPIAUCSL | 2024-03-15 | 2024-03-12 | 2024-02-01 | 311.054 | 310.967 | -0.087 | 0.442 | 0.410 |
| CPIAUCNS | 2009-01-20 | 2009-01-16 | 2008-12-01 | 210.228 | 210.228 | 0.0 | -1.034 | -1.034 |
| CPIAUCNS | 2022-07-15 | 2022-07-13 | 2022-06-01 | 296.311 | 296.311 | 0.0 | 1.374 | 1.374 |
| INDPRO | 2009-01-20 | 2009-01-16 | 2008-12-01 | 103.5966 | 90.8357 | -12.7609 | -2.001 | -2.820 |
| INDPRO | 2012-05-01 | 2012-04-17 | 2012-03-01 | 96.5685 | 96.74 | 0.1715 | -0.005 | -0.518 |
| INDPRO | 2019-06-10 | 2019-05-15 | 2019-04-01 | 109.1818 | 102.274 | -6.9078 | -0.511 | -0.585 |
| INDPRO | 2022-08-01 | 2022-07-15 | 2022-06-01 | 104.3648 | 101.018 | -3.3468 | -0.199 | -0.311 |
| UNRATE | 2009-01-12 | 2009-01-09 | 2008-12-01 | 7.2 | 7.3 | 0.1 | 5.882 | 7.353 |
| UNRATE | 2010-03-01 | 2010-02-05 | 2010-01-01 | 9.7 | 9.8 | 0.1 | -3.000 | -1.010 |
| UNRATE | 2020-05-11 | 2020-05-08 | 2020-04-01 | 14.7 | 14.8 | 0.1 | 234.091 | 236.364 |
| DCOILWTICO | 2015-01-15 | 2015-01-14 | 2015-01-12 | 46.06 | 46.06 | 0.0 | -4.736 | -4.736 |
| DCOILWTICO | 2022-07-15 | 2022-07-13 | 2022-07-11 | 106.09 | 106.09 | 0.0 | -0.646 | -0.646 |
| PCEPI | 2012-05-01 | 2012-04-30 | 2012-03-01 | 115.62 | 94.284 | -21.336 | 0.208 | 0.191 |
| PCEPI | 2022-07-15 | 2022-06-30 | 2022-05-01 | 122.052 | 115.525 | -6.527 | 0.588 | 0.621 |
| DFF | 2015-01-15 | 2015-01-15 | 2015-01-14 | 0.12 | 0.12 | 0.0 | 0.000 | 0.000 |
| DFF | 2022-07-15 | 2022-07-15 | 2022-07-14 | 1.58 | 1.58 | 0.0 | 0.000 | 0.000 |

Controls: CPIAUCNS (NSA CPI) — 0 revisions in both tests; DFF and DCOILWTICO — 0. So the machinery reports *no* revision where none exists (PROVEN), and large revisions where they do.

Headline look-ahead cases (all OBSERVED):
* **Payrolls Dec-2008**: known 2009-01-09 = 135,489 (−524k m/m, matches BLS archive); today = 134,847 (−0.51% m/m vs −0.39%).
* **GDP 2008:Q4**: first print 2009-01-30 growth −0.96% (q/q, real), today −2.19% — sign same, magnitude 2.3×.
* **INDPRO Dec-2008**: known −2.00% m/m, today −2.82%.
* **UNRATE Dec-2008**: known 7.2%, today 7.3%; April-2020: 14.7 → 14.8.
* Number of observations in the trailing 2-year window that differ from today's values at each T: 8–33 (see `n_obs_revised_vs_latest` in JSON). Using latest-value data at T therefore changes not only the newest print but most of the recent history.

## B. Revision paths of single observations (value by vintage, distinct values only)

**GDPC1:2008-10-01** — first vintage with the observation 2009-01-30; latest 16485.35
`2009-01-30: 11599.4 → 2009-02-27: 11525.0 → 2009-03-26: 11522.1 → 2009-07-31: 13141.9 → 2010-07-30: 12993.7 → 2011-07-29: 12883.5 → 2013-07-31: 14574.6 → 2014-07-30: 14577.0 → 2017-10-27: 14576.985 → 2018-07-27: 15328.027 → 2021-07-29: 15366.607 → 2023-09-28: 16485.35`

**PAYEMS:2008-12-01** — first vintage with the observation 2009-01-09; latest 134847.0
`2009-01-09: 135489.0 → 2009-02-06: 135178.0 → 2009-03-06: 135074.0 → 2010-02-05: 134328.0 → 2011-02-04: 134383.0 → 2012-02-03: 134379.0 → 2013-02-01: 134425.0 → 2014-02-07: 134774.0 → 2015-02-06: 134773.0 → 2016-02-05: 134844.0 → 2017-02-03: 134846.0 → 2018-02-02: 134842.0`

**INDPRO:2008-12-01** — first vintage with the observation 2009-01-16; latest 90.8357
`2009-01-16: 103.5966 → 2009-02-18: 103.2183 → 2009-03-16: 103.1895 → 2009-03-27: 102.3671 → 2009-04-15: 102.5212 → 2009-05-15: 102.4338 → 2009-06-16: 102.365 → 2010-06-25: 91.0342 → 2011-03-25: 89.3334 → 2012-03-30: 89.3744 → 2013-03-22: 89.5631 → 2014-04-16: 89.5075`

**CPIAUCSL:2022-06-01** — first vintage with the observation 2022-07-13; latest 294.957
`2022-07-13: 295.328 → 2023-02-10: 294.728 → 2024-02-09: 294.996 → 2025-02-12: 295.072 → 2026-02-13: 294.957`

**UNRATE:2020-04-01** — first vintage with the observation 2020-05-08; latest 14.8
`2020-05-08: 14.7 → 2021-01-08: 14.8 → 2022-01-07: 14.7 → 2024-01-05: 14.9 → 2024-01-10: 14.8`

**PAYEMS:2020-04-01** — first vintage with the observation 2020-05-08; latest 130426.0
`2020-05-08: 131072.0 → 2020-05-11: 131045.0 → 2020-06-05: 130403.0 → 2020-07-02: 130303.0 → 2021-02-05: 130161.0 → 2022-02-04: 130513.0 → 2023-02-03: 130430.0 → 2024-02-02: 130421.0 → 2025-02-07: 130424.0 → 2026-02-11: 130426.0`

Observations: GDP 2008:Q4 moves 11599.4 → 11525.0 → 11522.1 in three months, jumps to 13141.9 at the 2009-07-31 comprehensive revision (re-basing), and ends at 16485.35 after later re-basings. PAYEMS 2008-12 keeps changing at each February benchmark for ≥ 10 years. CPIAUCSL 2022-06 changes only at annual seasonal-factor updates (Feb each year). PAYEMS 2020-04 has vintages 2020-05-08 (131,072) and **2020-05-11** (131,045) — a second vintage 3 days after the BLS release date, cause UNKNOWN (not explained by any calendar fetched).

## C. Edge behaviour
See 02 (as-of = last vintage ≤ T, 404 before first vintage, silent latest fallback for future dates, ignored params).

## D. Conclusion
**LOOKAHEAD_FROM_LATEST_VALUE_PROVEN = YES.** Querying FRED today for a historical date returns the fully revised value; ALFRED returns what was known. Also, `fredgraph.csv` silently ignores `vintage_date`, so a naive 'add vintage_date' to a FRED call produces look-ahead without any error.