# 02 — FRED / ALFRED (highest priority)

Scripts: `bench/macro_vintage_v1/py/{probe_sources,alfred_vintage,lookahead,asof_vs_today}.py`. Raw: `raw/alfred/`, `raw/fred/`.

## 2.1 Endpoints and what each proved
| Endpoint | Key | Vintage semantics | Status |
|---|---|---|---|
| `api.stlouisfed.org/fred/series/observations` (`realtime_start/end`, `vintage_dates`) | required (`400 … api_key … not registered`) | documented ("(closed, closed)" real-time period, defaults to today — `docs/api/fred/realtime_period.html`, archived) | **DOCUMENTED_CLAIM, not executed** |
| `fred.stlouisfed.org/graph/fredgraph.csv` | none | **none — ignores `vintage_date` and `realtime_*`** (sha256 `2ba40024…` identical for 3 requests) | PROVEN latest-only |
| `alfred.stlouisfed.org/graph/alfredgraph.csv?id=S&vintage_date=T` | none | one vintage per call; column header `S_YYYYMMDD` | **PROVEN vintage-native** |
| `alfred.stlouisfed.org/series/downloaddata?seid=S` (GET) | none | HTML page listing every vintage date (e.g. PAYEMS 859) | PROVEN (vintage list) |
| same, POST form (bulk all-vintage file) | none | HTTP 500 with my hand-built POST (fields `form[file_type]`, `form[entered_vintage_dates]`…) | FAILED — untested |
| `alfred.stlouisfed.org/release/downloaddates?rid=N&ff=txt` | none | release dates (date only) | PROVEN |
Multi-vintage in one call: comma/`+` forms did not work (comma → only first vintage honoured; `+` → today). Repeated `vintage_date=` → last wins. Use one call per vintage.

## 2.2 Vintage semantics (PROVEN)
- Vintage list per series (from `downloaddata`): GDPC1 418 (1991-12-04→2026-08-26), GDP 414, PAYEMS 859 (1955-05-06→2026-09-04), INDPRO 1223 (1927-01-26→2026-09-18), CPIAUCSL 669, UNRATE 799, DGS10 5118 (daily: market series, one vintage per day, not revisions).
- `vintage_date=T` = state on date T. Release-day test (`results/release_day_inclusion.json`): PAYEMS May-2020, vintage 2020-06-04 → no value; vintage 2020-06-05 (release day) → 132912. GDPC1 Q2-2020: 2020-07-29 → none; 2020-07-30 → 17205.822. **⇒ vintage granularity is one day; an intraday (08:30 ET) cut cannot be expressed.**
- A non-vintage date returns the nearest earlier state (e.g. vintage 2020-06-15 → 2020-06-05 values).

## 2.3 Revision paths (`results/alfred_revision_paths.json`; first appearance found by bisection)
| Series / obs | first release vintage → value | subsequent | today |
|---|---|---|---|
| PAYEMS Apr-2020 (k persons) | 2020-05-08 → 131072 | 05-11 → 131045; 06-05 → 130403; 07-02 → 130303; 2021-06-04 → 130161; 2023-06-02 → 130430 | 130426 (2026-09-04) |
| PAYEMS Dec-2022 | 2023-01-06 → 153743 | 02-03 → 154556; 2024-02-02 → 154291 | 154342 |
| PAYEMS Mar-2019 | 2019-04-05 → 150816 | 05-03 → 150832; 2020-05-08 → 150282 | 150295 |
| INDPRO Apr-2020 | 2020-05-15 → 92.5919 | 06-16 → 91.2823; 2021-05-28 → 84.2018 | 84.5619* |
| INDPRO Mar-2022 | 2022-04-15 → 104.5853 | 06-28 → 103.719; 2023-05-16 → 102.478 | 101.3907* |
| CPIAUCSL Jun-2021 | 2021-07-13 → 270.981 | unchanged for 5 months; 2022-07-13 → 270.955 (seasonal re-estimation) | 270.654 |
| CPIAUCSL Jun-2022 | 2022-07-13 → 295.328 | 2023-08-10 → 294.728 | 294.957 |
| GDPC1 Q2-2020 (adv 2020-07-30) | 17205.822 | 08-27 → 17282.188; 09-30 → 17302.511; 2021-08-26 → 17258.205 | 19077.992* |
| GDP (nominal) Q2-2020 | 19408.759 | 08-27 → 19486.509; 09-30 → 19520.114; 2021-08-26 → 19477.444 | 19958.291 |
| UNRATE Apr-2020 | 14.7 | unchanged until 2021-06-04 → 14.8 (annual seasonal revision) | 14.8 |
\* levels include base-year re-referencing (chained-dollar / index base); not pure revisions — see 06.
Note the **PAYEMS 05-08 → 05-11 correction**: ALFRED holds a vintage 3 days after the first release; a "first release only" rule would miss intra-cycle corrections.

## 2.4 Not covered
Weekly oil inventories / rates on FRED: `WCESTUS1` not tested (time-box); DGS10 used only as vintage-count control. FRED API `realtime_start/realtime_end`, `output_type=4` (initial release only) and `vintage_dates` remain unexecuted (need key). Classification: **ALFRED = PIT_NATIVE (date-granular)**, FRED CSV = PIT_UNSUITABLE for history, FRED API = PIT_NATIVE by documentation only.
