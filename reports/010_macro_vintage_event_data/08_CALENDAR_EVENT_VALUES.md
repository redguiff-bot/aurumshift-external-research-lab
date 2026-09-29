# 08 — Calendars and event values

Two classes, kept separate.

## A. Schedule-only (no values)
| Source | Content | Machine-readable | Notes |
|---|---|---|---|
| BEA `release_dates.json` + ICS | release name + UTC datetime, 2025-01→2026-12 (31 releases) | YES | official; no actual/previous/forecast/revision id. Past dates match ALFRED for GDP (19/19) |
| ALFRED / FRED release dates | dates (863 for release 53) | YES (txt/xlsx via `downloaddates`) | date only; FRED docs: dates are "published by data sources and do not necessarily represent when data will be available" |
| FRED `releases/calendar` | HTML | scrape | |
| EIA WPSR schedule | prose (10:30 ET Wed; holiday shifts) | NO | |
| CFTC COT schedule | HTML list (2026 Fridays + holiday-delayed*) | scrape | |
| BLS schedule / ICS | – | 403 to automated fetch | UNKNOWN |
| Eurostat / BoE MPC calendars | HTML pages fetched (203 KB / 79 KB) | not parsed | UNKNOWN |

## B. Release-value feeds (actual / previous / forecast)
- **Official**: none found that has actual + previous + forecast + revision id + timestamp. Official forecast fields are essentially absent (consensus forecasts are commercial).
- Official *actual* series with revisions: ALFRED (US), OECD editions.
- **Non-official contrast (TipRanks MCP)**: rows `{event, time, actual, estimate, prev, unit, impact}`, e.g. 2026-09-01T14:00 JOLTs actual 7.271 / est 7.3 / prev 7.359. No event id, no timezone marker, no revision history, consensus source opaque, licence UNKNOWN. Sample in `raw/tipranks_calendar_sample.json`. Not used for any classification above.

## C. Event identifier
No source exposed a stable provider event ID for a release instance except BEA ICS `UID` (per event) and FRED `release_id` (release family, not instance). Instance key must be built: `(release_id, release_date)`.
