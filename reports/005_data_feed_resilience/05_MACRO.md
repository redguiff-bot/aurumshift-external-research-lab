# 05 — Macro and calendar

Code: `py/macro.py`, `py/sweep2.py`. Results: `results/macro_tests.json`.

| Source | Result (OBSERVED) | Auth | PIT-relevant fields |
|---|---|---|---|
| FRED API | reachable at `api.stlouisfed.org` (HTTP 400 "api_key not set/not registered"); **fredgraph.csv, alfred and fred web hosts: connection closed by proxy (5 attempts)** | free key | `realtime_start/realtime_end` documented (not executed) |
| ALFRED | host unreachable from egress; vintage URL parameters untested | key | vintages (DOCUMENTED_CLAIM) |
| US Treasury daily par yield CSV | 24 rows for 2026 YTD, 35 for 1990 (unexpectedly few — likely pagination; UNEXPLAINED); latest row 09/28/2026 | none | none |
| US Treasury FiscalData | 200, earliest 2001-01-31 in probe | none | `record_date` |
| NY Fed SOFR | 200; latest 2026-09-28 = 3.90; search back to 2018-04-03 (1.75) | none | `revisionIndicator` (empty), `effectiveDate` |
| ECB SDMX | 200 (CSV/JSON); `updatedAfter` accepted | none | OBS_STATUS |
| Eurostat HICP | 200; JSON-stat `updated` = 2026-02-06 for the cube read | none | dataset `updated` |
| BLS API | v1 keyless: first probe `REQUEST_NOT_PROCESSED` (daily threshold), later probe `REQUEST_SUCCEEDED`; v2 without key: threshold message | v1 none / v2 key | footnotes |
| Bank of Canada Valet | 200, daily FXUSDCAD | none | — |
| Bank of England IADB | 200 CSV | none | — |
| CFTC COT | 200; from 1986-01-15 | none/app token | `report_date_as_yyyy_mm_dd` (as-of date; release time absent) |
| World Bank | 200; `lastupdated` 2026-07-13 | none | `lastupdated` |
| EIA / BEA | key required; not executed | key | — |
| IMF DataMapper / OECD | IMF 403 from egress; OECD query malformed by me | — | — |
| SNB | 200 (891 KB cube) | none | — |

## Economic calendar and news
* **Faireconomy / ForexFactory JSON**: 141 events for the current week (9 currencies, impact High/Medium/Low/Holiday). Payload fields: title, country, date (ISO with offset), impact, forecast, previous. **No `actual` field** (0/141), `nextweek`/`lastweek` files 404. Two fetches 2 s apart were byte-identical. Suitable for *scheduled-event times* only.
* Trading Economics: guest key discontinued (HTTP 410). FMP/Finnhub/Polygon: key required, free-tier calendar capability UNKNOWN. BLS ICS release schedule: 403 from egress. Fed FOMC calendar HTML (165 KB) reachable; not parsed. GDELT reset by egress. TipRanks connector present in this session but deliberately not executed (account quota, terms unverified).
* Sentiment: alternative.me Fear&Greed (3,159 daily rows).

## Gap statement
Macro/calendar *release values with release timestamps* are the weakest class: the keyless official sources give observation dates but rarely the moment the value became public. That timing has to come from an external schedule (BLS/Fed calendars, FF-style feeds) or from ALFRED-style vintages, which could not be executed here.
