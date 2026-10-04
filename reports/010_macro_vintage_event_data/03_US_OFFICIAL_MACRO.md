# 03 — US official macro sources (BLS, BEA, EIA, NY Fed, Treasury, CFTC)

| Source | Observation period | Publication / revision info | Vintage? | Class |
|---|---|---|---|---|
| **BLS API v2** | `year`,`period` (M08) | no publication time; `latest:"true"` flag only; footnotes. Unregistered daily threshold hit (`REQUEST_NOT_PROCESSED`, receipts in `raw/`); release schedule/ICS pages 403 to automated fetch | none (latest) | PIT_WEAK (value feed) |
| **BEA** | – | Value API needs UserID (`apps.bea.gov/api/data` → empty 200, not executed). **`release_dates.json`: 31 release names, ISO UTC timestamps** (GDP: 23 dates 2025-01-30→2026-12-23; times 12:30Z/13:30Z). ICS mirrors it (`DTSTART…Z`, `DTSTAMP` 2025-09-23) | schedule only | Calendar = schedule-only; value feed UNKNOWN |
| **EIA API v2** | `period` (weekly date) | no receipt/publication time in payload; API v2 warns 5000-row cap; `DEMO_KEY` works. Schedule page states 10:30 ET Wednesday (1:00 pm for other files; holiday shifts) — prose only | none | PIT_ADAPTABLE (forward capture + documented schedule) |
| **NY Fed Markets (SOFR)** | `effectiveDate` | fields: `percentRate`, percentiles, `volumeInBillions`, **`revisionIndicator`** (empty for all rows 2026-09-01→09-10) | flag, no history | PIT_ADAPTABLE |
| **Treasury FiscalData** | `record_date` | no publication time; docs page: data "free, without restriction … redistribute … commercial or non-commercial" (quoted) | none | PIT_ADAPTABLE (rarely revised series) |
| **CFTC COT** | `report_date_as_yyyy_mm_dd` (Tuesday as-of) | dataset meta `rowsUpdatedAt` = 1790364609 (dataset-level); release schedule page lists Fridays with holiday shifts (2026 list archived) | none | PIT_ADAPTABLE (obs-date ≠ release date; rule-based) |

Key point (OBSERVED): every US official **value** API tested exposes observation date but not release time; timing must come from a separate schedule (BEA JSON is the only machine-readable official one found; BLS blocks automated schedule fetch here).
