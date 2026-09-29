# 03 — US official macro sources

| Source | Observation period | Publication ts | Revision info | Vintage/as-of | Prelim/final | Series id | Event id | Executed evidence |
|---|---|---|---|---|---|---|---|---|
| BLS API v1 | `year`+`period` (M08) | none | footnote code `P` = preliminary; `latest:"true"` flag on newest row | none | yes (P) | `CES0000000001` | none | 32 rows; 20/20 overlapping months equal ALFRED latest PAYEMS; second call blocked by per-IP quota (`REQUEST_NOT_PROCESSED`); v2 needs registration key |
| BLS release calendar | – | scheduled ET time in ICS (`DTSTART;TZID=US-Eastern:…T083000`) | – | – | – | – | ICS `UID` | 313 events 2025-01-03 … 2026-12-30 |
| BEA API | – | – | – | – | – | – | – | needs `UserID`; not executed |
| BEA schedule | – | scheduled UTC time in ICS (e.g. `20250130T133000Z`) | (Advance/Second/Third estimate in title) | – | in title | – | none (no UID used) | 119 events |
| EIA API v2 | `period` | none | none | none | none | `WCESTUS1`-style series ids | none | one DEMO_KEY call returned rows; then OVER_RATE_LIMIT |
| NY Fed | `effectiveDate` | none | `revisionIndicator` (empty in all 250 SOFR rows) | none | via indicator | type (SOFR) | none | 250 rows |
| US Treasury FiscalData | `record_date` | none | none | none | none | endpoint | none | rows returned keyless |
| US Treasury yield XML | `NEW_DATE` | Atom `<updated>` = 2026-09-29T02:38:00Z on feed and entries | none | none | none | – | entry id | 19 entries |
| CFTC COT (Socrata) | `report_date_as_yyyy_mm_dd` | `:created_at` 2026-09-25T19:30:08Z on recent rows (Fri 15:30 ET) | `:updated_at` | none | none | `id` | `:id` | see 05 |
| Philadelphia Fed RTDSM | quarter | none (vintage = month) | full monthly vintages | **yes** | – | `ROUTPUT##M#` | none | 731 vintage columns 1965M11–2026M9 |
| Fed G.17 | – | release-dates page only | – | – | – | – | – | HTML fetched |

BLS/BEA archived-release cross-check (PROVEN): the BLS archived Employment Situation of 2009-01-09 states "Total nonfarm payroll employment declined sharply (-524,000) in December"; ALFRED's 2009-01-09 vintage gives Dec-2008 135,489 − Nov 136,013 = −524. Independent agreement of initial release.

Philly Fed vs ALFRED (PROVEN, independent providers): real GDP 2008:Q4 — RTDSM `ROUTPUT09M2` = 11599.4 and `ROUTPUT09M3` = 11525.0 and `ROUTPUT09M8` = 13141.9; ALFRED GDPC1 vintages 2009-01-30 / 2009-02-27 / 2009-07-31 = 11599.4 / 11525.0 / 13141.9 (exact). RTDSM `ROUTPUT09M1` is `#N/A` (vintage taken before the advance release). RTDSM 09M3 (11525.0) precedes ALFRED's 2009-03-26 third estimate (11522.1): consistent with a mid-month snapshot (INFERENCE; documentation on the snapshot day not extracted).
