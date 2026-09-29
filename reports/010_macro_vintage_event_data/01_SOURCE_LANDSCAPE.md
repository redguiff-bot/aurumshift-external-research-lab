# 01 — Source landscape

Run date (test-egress clock, UTC): 2026-09-29. Labels: PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN. All raw responses + receipt stamps: `bench/macro_vintage_v1/raw/` (`*.meta.json`), probe summary `results/probe_sources.json`. Requests were sent with a research User-Agent; BLS/IMF/OECD block anonymous-looking clients (403) so that matters.

Legend — **Exec** = data path returned parsed data this run. Class = PIT class (see 07).

| # | Source | Official? | Access observed | Exec | Notes |
|---|---|---|---|---|---|
| 1 | FRED API `api.stlouisfed.org` | official | HTTP 400 "api_key not set" without key | NO (key required, none available) | vintage params documented, **not executed** |
| 2 | FRED web CSV `fredgraph.csv` | official web | 200 keyless | YES | latest values only; `vintage_date` silently ignored (trap) |
| 3 | ALFRED web CSV `alfredgraph.csv` + `downloaddata` page | official web | 200 keyless | YES | real as-of retrieval, see 02/06 |
| 4 | BLS API v1/v2 | official | v1 200 once (P flag, `latest`); v2/recall → "daily threshold reached" (per-IP quota, shared egress) | YES (1 call) | no vintages |
| 5 | BLS release calendar (HTML + `bls.ics`) | official | 200 with UA (403 without) | YES | 313 events, ET time-of-day |
| 6 | BEA API | official | 200 empty / "Invalid API UserID" | NO (key) | |
| 7 | BEA release schedule (HTML + ICS) | official | 200 | YES | 119 ICS events, UTC times |
| 8 | EIA API v2 | official | 403 no key; `DEMO_KEY` returned data once, then OVER_RATE_LIMIT | YES (1 call) | `period`,`value` only |
| 9 | EIA WPSR schedule | official | 200 | YES | HTML, times |
| 10 | NY Fed Markets API | official | 200 keyless | YES | `revisionIndicator` |
| 11 | ECB Data Portal SDMX | official | 200 keyless | YES | `OBS_STATUS`; `updatedAfter`/`includeHistory` accepted but ignored (bodies identical) |
| 12 | ECB statistical calendar | official | 200 | YES (fetched) | HTML, no times, no values |
| 13 | Eurostat dissemination API | official | 200 keyless | YES | dataset-level `updated` |
| 14 | Eurostat release calendar | official | 200 | YES (fetched) | HTML |
| 15 | Bank of England IADB | official | 302 error page on one URL form; 200 CSV on `/boeapps/iadb/fromshowcolumns.asp` | YES | no revision signal |
| 16 | Bank of Canada Valet | official | 200 keyless | YES | no timestamps in body |
| 17 | US Treasury FiscalData | official | 200 keyless | YES | `record_date` |
| 18 | US Treasury yield-curve XML | official | 200 | YES | Atom `<updated>` |
| 19 | CFTC Public Reporting (Socrata) | official | 200 keyless | YES | Socrata `:created_at/:updated_at` |
| 20 | World Bank API v2 | official | 200 keyless | YES | `lastupdated` per source; source 57 "WDI Database Archives" exists |
| 21 | IMF DataMapper | official | 200 keyless | YES | latest WEO only |
| 22 | IMF SDMX `api.imf.org` | official | dataflow list 200 | PARTIAL (structure only) | |
| 23 | OECD SDMX | official | 200 keyless | YES | includes `DF_STES_REVISIONS` |
| 24 | Philadelphia Fed Real-Time Data Set | official (FRB) | 200 xlsx download | YES | 731 monthly vintages of ROUTPUT |
| 25 | FRED release calendar | official | 200 HTML | YES (fetched) | |
| 26 | Fed G.17 release dates | official | 200 HTML | YES (fetched) | |
| 27 | Census economic-indicator calendar | official | 200 HTML | YES (fetched) | |
| 28 | TipRanks economic calendar (MCP) | **UNOFFICIAL aggregator** | tool call | YES, comparator only | not substituted for any official source |

Counts: 28 catalogued (+ FRED API and BEA API and BLS v2 as key-gated alternates of rows 1/6/4). Data-path executed: 17 data sources (2,3,4,8,10,11,13,15,16,17,18,19,20,21,23,24 + OECD revisions flow) and 8 official calendars fetched. `FRED API`, `BEA API` not executed with data.
