# 07 — PIT readiness classification

Definitions used: PIT_NATIVE = source itself serves as-of retrieval keyed by a vintage/edition · PIT_ADAPTABLE = we can build PIT by capturing receipts / pairing with schedule going forward · PIT_WEAK = only latest values with partial flags · PIT_UNSUITABLE = latest-only, no way to reconstruct.

| Source | Class | Evidence | Granularity | Executed |
|---|---|---|---|---|
| ALFRED | **PIT_NATIVE** | 7 series vintages; revision paths; release-day test | day | YES |
| OECD STES_REVISIONS | **PIT_NATIVE** | 89 editions for USA 2019 | month | YES |
| World Bank WDI Archives | **PIT_NATIVE** (lagging) | 142 versions; values differ | month | YES |
| FRED API (`realtime_*`) | PIT_NATIVE *by documentation* | docs archived | day | NO (key) |
| FRED web CSV | PIT_UNSUITABLE | params ignored, identical hashes | – | YES |
| NY Fed | PIT_ADAPTABLE | `revisionIndicator` | day | YES |
| ECB | PIT_ADAPTABLE | `updatedAfter`, `OBS_STATUS` | second (server-side) | YES |
| Eurostat | PIT_ADAPTABLE | `updated` stamp | second, latest only | YES |
| EIA | PIT_ADAPTABLE | DEMO_KEY data; schedule prose | – | YES |
| CFTC | PIT_ADAPTABLE | obs date vs Friday schedule | – | YES |
| Treasury FiscalData | PIT_ADAPTABLE | `record_date` | – | YES |
| Bank of Canada | PIT_ADAPTABLE | – | – | YES |
| Bank of England | PIT_ADAPTABLE | curl only | – | YES |
| BLS | PIT_WEAK | latest flag; quota | – | partial |
| IMF | PIT_WEAK | latest WEO; archives UNKNOWN | – | YES (latest) |
| BEA (values) | UNKNOWN | key required | – | NO |
| BEA (calendar) | schedule-only (not a PIT value source) | UTC timestamps | second | YES |
| TipRanks calendar (non-official) | PIT_WEAK | actual/estimate/prev with times, no revisions | minute | contrast |
Counts: PIT_NATIVE executed 3; PIT_ADAPTABLE executed 8.
