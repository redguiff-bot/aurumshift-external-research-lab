# 04 — ECB, Eurostat, BoE, BoC, World Bank, IMF, OECD

| Source | Semantics found (executed) | Class |
|---|---|---|
| **ECB SDMX** | `TIME_PERIOD`, `OBS_STATUS` (HICP: `E` estimate for 2025-10 flash, `A` normal — flag reveals provisional vs normal *now*, not its history), `OBS_COM`. **`updatedAfter=<ISO ts>` filter works** (returned 3 FX obs updated after 2026-09-25) → change-feed primitive usable for forward capture | PIT_ADAPTABLE |
| **Eurostat** | JSON-stat carries dataset-level `updated` (e.g. `2026-02-06T23:00:00+0100` for prc_hicp_manr; `2026-09-22T11:00:00+0200` for une_rt_m); `status` map empty for tested cells; `sinceTimePeriod` param → HTTP 400 | PIT_ADAPTABLE (latest state + update stamp) |
| **Bank of England IADB** | CSV `DATE,IUDBEDR`; python-requests → Akamai 403, curl → 200 (redirect to `_iadb-FromShowColumns.asp`); no vintages | PIT_ADAPTABLE (policy rate: rarely revised) |
| **Bank of Canada Valet** | observations `d`/`v`; terms page reachable; no vintage | PIT_ADAPTABLE |
| **World Bank** | WDI (source 2, `lastupdated` 2026-07-13) latest-only. **Source 57 "WDI Database Archives" (lastupdated 2025-10-29): dimension `Version` = YYYYMM editions (142 for USA/GDP/2015).** USA GDP 2015 (current US$): 17 946 996 000 000 (2016-07…11) → 18 036 648 000 000 (2016-12) → 18 036 600 000 000 (2017-03) → 18 219 297 584 000 (2019-10…2020-05) | PIT_NATIVE (edition/month granularity; archive lags live by ≈8 months; annual data) |
| **IMF** | DataMapper API 200 latest WEO only; guessed WEO archive file URLs `WEOApr2024all.ashx` → `BlobNotFound` (URLs unverified, not a source statement) | PIT_WEAK (vintages UNKNOWN) |
| **OECD SDMX** | `DSD_STES_REVISIONS@DF_STES_REVISIONS` v4.0, key `REF_AREA.FREQ.MEASURE.UNIT_MEASURE.ACTIVITY.EDITION` (+1 more field; 7-part key works). USA quarterly 2019: 3351 rows, 89 editions `201905…202609`; e.g. `P3_S13_Q` 2019-Q1: 2 564 418 000 000 (ed. 201905) → 2 563 813 000 000 (201906) → 2 564 101 000 000 (201907) → 2 614 301 000 000 (201908…) | **PIT_NATIVE** (monthly edition; publication day UNKNOWN) |
Also 1 547 OECD dataflows listed; only one matched "revision".
