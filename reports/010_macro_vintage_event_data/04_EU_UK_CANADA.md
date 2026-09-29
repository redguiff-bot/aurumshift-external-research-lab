# 04 — Euro area, UK, Canada, international

| Source | Executed | Time semantics observed | Revision/vintage | Class |
|---|---|---|---|---|
| ECB SDMX (ICP HICP, EXR) | yes | `TIME_PERIOD`; `OBS_STATUS` A (normal) / E (estimated) in HICP rows; `OBS_COM` carries methodology notices (HICP methodology change from 2026-02-04, dataset replaced) | `updatedAfter` and `includeHistory=true` → HTTP 200 but rows identical to the plain query (so not usable as revision history; OBSERVED for EXR lastN=2) | PIT_ADAPTABLE |
| Eurostat (`prc_hicp_manr`) | yes | dataset-level `updated` = 2026-02-06T23:00:00+0100 (query returned data to 2026-01 only on the run's filter); no per-observation flag key in JSON-stat here (`status` null) | SDMX 2.1 `updatedAfter` → 200, not shown to give history | PIT_ADAPTABLE (dataset stamp) |
| Bank of England IADB | yes (`/boeapps/iadb/fromshowcolumns.asp`) | date + value only; HTTP `Date` header | none | PIT_WEAK |
| Bank of Canada Valet | yes | `d` date + `v` only; no Last-Modified | none | PIT_WEAK |
| World Bank v2 | yes | `lastupdated` per source (WDI 2026-07-13); rows `date`,`value`,`obs_status`; source 57 "WDI Database Archives" listed (lastupdated 2025-10-29) but my archive queries returned "indicator not found/data not found" | archive access not demonstrated | PIT_WEAK (archive UNKNOWN) |
| IMF DataMapper | yes | year + value; latest WEO only; no vintage param | none (WEO archive pages: 403) | PIT_WEAK |
| IMF SDMX `api.imf.org` | dataflow list only | – | – | UNKNOWN |
| OECD SDMX | yes | standard dataflows: latest only. **`DF_STES_REVISIONS`** (dimensions REF_AREA.FREQ.MEASURE.UNIT_MEASURE.ACTIVITY.EDITION) | `EDITION` = monthly snapshot (`202003`…`202609`, 79 editions). Query `USA.M.PRVM.IX.BTE..` → 3148 rows; 2020-03 production index: 99.57 (ed. 202005), 100.21 (202006), 100.23, 100.34, 100.47, 100.39 … | PIT_NATIVE (monthly edition, one measure family) |

Notes: full-key OECD queries returned HTTP 413 ("request entity too large") when too many dimensions were wildcarded; a restricted key worked. Time-of-release is absent everywhere in this table: RELEASE_TIME_UNKNOWN except where 05 says otherwise.
