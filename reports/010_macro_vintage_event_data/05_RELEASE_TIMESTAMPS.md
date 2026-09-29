# 05 — Release-time contract

Four clocks, never conflated:

| Clock | Meaning | Where available (executed) |
|---|---|---|
| OBSERVATION_TIME | period the number describes | every source (`observation_date`, `TIME_PERIOD`, `period`, `record_date`) |
| RELEASE_TIME | when the provider made it public | **date only** via ALFRED vintage date (UTC-agnostic day); **scheduled time-of-day** via BLS ICS (ET) and BEA ICS (UTC); **actual-publication stamps** only for CFTC recent rows (`:created_at`) and Treasury yield feed (`<updated>`) |
| REVISION_TIME | when a number was changed | ALFRED (a new vintage date), Philly RTDSM (month), OECD STES (edition month), CFTC `:updated_at`; otherwise absent |
| RECEIPT_TIME | when *we* got it | only what the consumer stamps; every fetch here recorded `receipt_time_utc` in `raw/*.meta.json`. No provider returns a receipt stamp except HTTP `Date` headers |

Rule applied: observation date is never mapped to release time. Where no publication stamp exists the field is **RELEASE_TIME_UNKNOWN** (BoE, BoC, EIA API, World Bank, IMF DataMapper, Eurostat per-observation, ECB per-observation, NY Fed, FiscalData, Philly Fed within a month).

## Alignment of ALFRED vintage dates with official calendars (PROVEN)
* BLS ICS vs ALFRED, events 2025-01-01…2026-09-28: Employment Situation → PAYEMS 20/20 and UNRATE 20/20 vintage dates equal the calendar date; CPI → CPIAUCSL 20/20. ALFRED had no other vintages in that period for those series. Calendar time-of-day: 08:30 ET for all.
* BEA ICS vs ALFRED GDPC1: 11/11 GDP events (Advance/Second/Third and the shutdown-shifted Q3-2025 Initial 2025-12-23 / Updated 2026-01-22) have a same-day ALFRED vintage (`results/extra_checks.json`). BEA ICS times are UTC (13:30Z or 12:30Z = 08:30 ET across DST).
* Hence a usable RELEASE_TIME construction is: `date = ALFRED vintage date`, `time = official calendar time on that date` — PIT_ADAPTABLE composition, INFERENCE beyond the tested series, and it breaks for unscheduled corrections (PAYEMS 2020-05-11).

## CFTC caveat (OBSERVED, look-ahead trap)
`:created_at` for the 2026-09-22 report = 2026-09-25T19:30:08Z (matches the Friday 15:30 ET COT release), but for report-date 2015-01-06 it is 2022-09-13T14:25:38Z — the dataset migration date. Row-level timestamps are valid publication stamps **only for post-migration rows**; historical rows carry a bulk-load date.
