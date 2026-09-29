# 07 — PIT readiness

Classes: **PIT_NATIVE** provider serves an as-of/vintage/edition retrieval (executed); **PIT_ADAPTABLE** no history but a status flag / update stamp / row timestamp that supports correct forward capture with our own receipt stamp; **PIT_WEAK** latest-only, no revision signal (historical use = look-ahead); **PIT_UNSUITABLE**.

| Source | Class | Basis (executed) | Granularity |
|---|---|---|---|
| ALFRED (web CSV) | PIT_NATIVE | as-of by `vintage_date`, 404 before first vintage | day |
| Philadelphia Fed RTDSM | PIT_NATIVE | 731 monthly vintage columns, values equal ALFRED | month |
| OECD `DF_STES_REVISIONS` | PIT_NATIVE | 79 monthly editions, USA production index only tested | month |
| BLS API | PIT_ADAPTABLE | `P` flag, `latest` flag; latest only | – |
| NY Fed | PIT_ADAPTABLE | `revisionIndicator` (no revision seen in 250 rows) | – |
| ECB SDMX | PIT_ADAPTABLE | `OBS_STATUS`; history param ignored | – |
| Eurostat | PIT_ADAPTABLE | dataset `updated` stamp | dataset |
| CFTC | PIT_ADAPTABLE | `:created_at/:updated_at`, valid for recent rows only | second |
| Treasury yield XML | PIT_ADAPTABLE | Atom `<updated>` | feed |
| FRED web `fredgraph.csv` | PIT_UNSUITABLE for history | ignores `vintage_date` | – |
| FRED API | UNKNOWN | not executed (no key) | – |
| BoE, BoC, EIA API, FiscalData, World Bank, IMF DataMapper | PIT_WEAK | latest-only, no revision signal | – |
| TipRanks calendar (unofficial) | PIT_UNSUITABLE as PIT source | no event id, no vintage, duplicate rows seen | – |

PIT_NATIVE executed = 3; PIT_ADAPTABLE executed = 6.

Residual gaps: no intraday release time in any vintage source; ALFRED bulk/API path untested; non-US areas (EA, UK, CA) have no vintage source except the OECD revisions flow (limited measures) — ECB/Eurostat revision histories were **not** found.
