# 05 — Release-time contract

Four clocks, never merged: **OBSERVATION_TIME** (period the value describes) · **RELEASE_TIME** (public availability, from the provider) · **REVISION_TIME** (when an existing observation changed) · **RECEIPT_TIME** (our clock; logged per call in `raw/_receipts.jsonl`).

| Source | OBSERVATION | RELEASE | REVISION | RECEIPT | Verdict |
|---|---|---|---|---|---|
| ALFRED values | `observation_date` | **date only** (vintage date; 19/19 BEA GDP dates coincide with ALFRED GDP release dates) — time-of-day RELEASE_TIME_UNKNOWN | vintage date of the changed value (day) | ours | day-granular |
| ALFRED release dates (`downloaddates`) | – | date only | – | ours | |
| BEA `release_dates.json` / ICS | – | **UTC timestamp, scheduled** (12:30Z/13:30Z ⇒ 08:30 ET across DST) — a *plan*, not proof of actual publication | – | ours | schedule-only |
| BLS API | `year`+`period` | RELEASE_TIME_UNKNOWN | none | ours | |
| EIA API | `period` | UNKNOWN in payload; page prose 10:30 ET Wed | none | ours | schedule in prose |
| NY Fed SOFR | `effectiveDate` | UNKNOWN in payload (publication rule is documented elsewhere, not verified here) | `revisionIndicator` flag only | ours | |
| ECB | `TIME_PERIOD` | UNKNOWN per obs; `updatedAfter` gives server-side change filter | `OBS_STATUS` flag; history none | ours | change-feed |
| Eurostat | `time` index | dataset `updated` (to the second, +TZ) — **latest update only** | none | ours | |
| CFTC | `report_date…` (Tuesday) | UNKNOWN per row; Friday schedule page; dataset `rowsUpdatedAt` | none | ours | |
| World Bank archive | year | month (`Version` YYYYMM), day UNKNOWN | edition change | ours | month |
| OECD STES revisions | period | month (`EDITION` YYYYMM), day UNKNOWN | edition change | ours | month |
| BoE / BoC / Treasury / IMF | period | UNKNOWN | none | ours | |

Rules applied in this study: (1) observation date is never used as release time; (2) where no publication timestamp exists, `RELEASE_TIME_UNKNOWN`; (3) the only intraday timestamps in the whole survey are BEA's schedule (plan) and Eurostat's dataset-level `updated`.
Consequence (PROVEN, `release_day_inclusion.json`): an ALFRED vintage dated D includes values released on D → a strategy evaluated at 08:00 ET on D using vintage D would see the 08:30 ET release: **use vintage D−1 for any decision before the release, or pair with a timestamp source.**
