# 01 — Source landscape (15 priority official sources + 1 non-official contrast)

"Executed" = a real HTTP response with data was received and archived in `bench/macro_vintage_v1/raw/`. Date of all calls: 2026-09-29.

| # | Source | Endpoint tested | Result | Executed |
|---|---|---|---|---|
| 1 | FRED API | `api.stlouisfed.org/fred/series/observations` | HTTP 400 "api_key … not registered" (also without key) | reachable, **not executed** (key) |
| 1b | FRED web CSV | `fred.stlouisfed.org/graph/fredgraph.csv` | 200, latest-only; vintage params ignored | YES |
| 2 | ALFRED | `alfred.stlouisfed.org/graph/alfredgraph.csv`, `/series/downloaddata`, `/release/downloaddates?rid=&ff=txt` | 200, true vintages | YES |
| 3 | BLS API v2 | `api.bls.gov/publicAPI/v2/timeseries/data/CES0000000001` | one early success in tool output (2026 M08 marked `latest`), then all calls `REQUEST_NOT_PROCESSED` daily threshold; schedule pages 403 | partial, raw not archived |
| 4 | BEA | `apps.bea.gov/api/data` (needs UserID) → empty 200; `apps.bea.gov/API/signup/release_dates.json` + `/news/schedule/ics/online-calendar-subscription.ics` | schedule with UTC times OK; value API needs registration | schedule only |
| 5 | EIA API v2 | `api.eia.gov/v2/petroleum/stoc/wstk/data` | no key → 403 `API_KEY_MISSING`; `api_key=DEMO_KEY` → 200 data | YES (DEMO_KEY) |
| 6 | NY Fed Markets | `markets.newyorkfed.org/api/rates/secured/sofr/…` | 200; field `revisionIndicator` | YES |
| 7 | ECB SDMX | `data-api.ecb.europa.eu/service/data/…` | 200; `OBS_STATUS`, `updatedAfter=` works | YES |
| 8 | Eurostat | `ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/…` | 200 JSON-stat with dataset `updated` stamp | YES |
| 9 | Bank of England IADB | `…/boeapps/database/_iadb-FromShowColumns.asp` | python 403 (Akamai), curl 200 | YES (curl) |
| 10 | Bank of Canada Valet | `bankofcanada.ca/valet/…` | 200 | YES |
| 11 | US Treasury FiscalData | `…/v2/accounting/od/debt_to_penny` (v1 path = 404) | 200 | YES |
| 12 | CFTC COT (Socrata) | `publicreporting.cftc.gov/resource/6dca-aqww.json` | 200; `report_date_as_yyyy_mm_dd` | YES |
| 13 | World Bank | WDI v2 + source 57 "WDI Database Archives" | 200; `Version` dimension | YES |
| 14 | IMF | `imf.org/external/datamapper/api/v1/…` 200 latest WEO; guessed WEO archive file URLs → `BlobNotFound` | latest only | YES (latest) |
| 15 | OECD SDMX | `sdmx.oecd.org/public/rest/…` incl. flow `DSD_STES_REVISIONS@DF_STES_REVISIONS` | 200; `EDITION` dimension | YES |
| — | TipRanks MCP calendar (NON-OFFICIAL) | `get_economic_calendar` | actual/estimate/prev/time; no vintage | contrast only |

Counts: discovered 16 (15 official + 1 unofficial); official with archived data returned: 12 (ALFRED, EIA, NY Fed, ECB, Eurostat, BoE, BoC, Treasury, CFTC, World Bank, IMF, OECD) + FRED web CSV; BEA schedule-only; BLS partial (unarchived); FRED API refused (no key).
Anti-bot observation (OBSERVED): FRED/ALFRED stalled and IMF 403'd a custom descriptive User-Agent; default UA accepted.
