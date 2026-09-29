# 05 — Real economy: shipping, energy inventories, weather, public government datasets

> External research only — no private AurumShift code, no integration claims. Evidence tags: **[OBS]** observed in this study, **[DOC]** stated on a provider page/API response fetched in this study, **[INF]** inference, **[UNK]** unknown/not verified. Study date 2026-09-29 (sandbox clock). Reproduce with `bench/alternative_data_v1/`.


**Bottom line.** This is the only family that produced a non-market candidate: **EIA weekly crude-oil inventory surprise**. Setup: surprise = weekly Δ(commercial crude stocks ex-SPR) minus the mean same-ISO-week Δ over the previous 5 years, scaled by trailing 104-week std (past data only). Release rule: Wednesday after week-ending Friday (+5 d) [rule, not verified per release]. Returns winsorised at 0.5/99.5 % (2020 oil dislocation dominates squared errors — a post-hoc, disclosed choice; raw-return results reported in `10`). Baseline: prior 1-day and 5-day return and 20-day log |return|.

| cand | target | n | first | last | coef_s | t_s | p_incr | q_bh | oos_gain_pct | dm_p_onesided |
|---|---|---|---|---|---|---|---|---|---|---|
| eia_crude_stock_surprise_vs_WTI | release_day:y | 1026 | 2007-01-03 | 2026-09-16 | -0.004 | -5.320 | 0.000 | 0.000 | 2.496 | 0.058 |
| eia_crude_stock_surprise_vs_WTI | release_day:absy | 1026 | 2007-01-03 | 2026-09-16 | -0.000 | -0.453 | 0.650 | 0.839 | -0.190 | 0.777 |
| eia_crude_stock_surprise_vs_WTI | next_day:y | 1026 | 2007-01-04 | 2026-09-17 | -0.000 | -0.175 | 0.861 | 0.863 | -0.205 | 0.771 |
| eia_crude_stock_surprise_vs_WTI | next_day:absy | 1026 | 2007-01-04 | 2026-09-17 | 0.000 | 0.386 | 0.699 | 0.839 | -0.284 | 0.844 |
| eia_gas_storage_surprise_vs_HenryHub | release_day:y | 661 | 2014-01-09 | 2026-09-17 | 0.006 | 2.234 | 0.025 | 0.076 | 1.437 | 0.134 |
| eia_gas_storage_surprise_vs_HenryHub | release_day:absy | 661 | 2014-01-09 | 2026-09-17 | 0.001 | 0.556 | 0.578 | 0.839 | -0.118 | 0.670 |
| eia_gas_storage_surprise_vs_HenryHub | next_day:y | 661 | 2014-01-10 | 2026-09-18 | 0.002 | 0.612 | 0.540 | 0.839 | -0.394 | 0.999 |
| eia_gas_storage_surprise_vs_HenryHub | next_day:absy | 661 | 2014-01-10 | 2026-09-18 | -0.005 | -2.442 | 0.015 | 0.076 | 1.305 | 0.173 |
| cpc_hdd_weekly_anomaly_vs_HenryHub | release_day:y | 902 | 2007-04-09 | 2026-09-21 | -0.010 | -2.346 | 0.019 | 0.076 | 1.680 | 0.075 |
| cpc_hdd_weekly_anomaly_vs_HenryHub | release_day:absy | 902 | 2007-04-09 | 2026-09-21 | 0.004 | 1.480 | 0.139 | 0.333 | 0.318 | 0.315 |
| cpc_hdd_weekly_anomaly_vs_HenryHub | next_day:y | 902 | 2007-04-10 | 2026-09-22 | -0.003 | -1.346 | 0.178 | 0.357 | 0.047 | 0.446 |
| cpc_hdd_weekly_anomaly_vs_HenryHub | next_day:absy | 902 | 2007-04-10 | 2026-09-22 | -0.000 | -0.172 | 0.863 | 0.863 | -0.878 | 0.907 |

Crude robustness (release-day WTI return unless noted):
| cand | series | offset_days | n | first | last | coef_s | t_s | p_incr |
|---|---|---|---|---|---|---|---|---|
| crude_surprise_vs_WTI/placebo_Mon(-2d) | WTI | 3 | 1027 | 2007-01-02 | 2026-09-21 | -0.000 | -0.204 | 0.839 |
| crude_surprise_vs_WTI/placebo_Tue(-1d) | WTI | 4 | 1027 | 2007-01-02 | 2026-09-22 | -0.002 | -2.071 | 0.038 |
| crude_surprise_vs_WTI/true_Wed | WTI | 5 | 1026 | 2007-01-03 | 2026-09-16 | -0.004 | -5.320 | 0.000 |
| crude_surprise_vs_WTI/placebo_Fri(+2d) | WTI | 7 | 1026 | 2007-01-05 | 2026-09-18 | 0.000 | 0.514 | 0.607 |
| crude_surprise_vs_WTI/placebo_Mon_next_wk | WTI | 12 | 1026 | 2007-01-03 | 2026-09-16 | 0.001 | 1.056 | 0.291 |
| crude_surprise_vs_WTI/2007-2014 | WTI | 5 | 417 | 2007-01-03 | 2014-12-31 | -0.004 | -4.111 | 0.000 |
| crude_surprise_vs_WTI/2015-2020 | WTI | 5 | 312 | 2015-01-07 | 2020-12-30 | -0.007 | -4.454 | 0.000 |
| crude_surprise_vs_WTI/2021-2026 | WTI | 5 | 297 | 2021-01-13 | 2026-09-16 | -0.001 | -1.114 | 0.265 |
| crude_surprise_vs_BRENT | Brent | 5 | 1026 | 2007-01-03 | 2026-09-16 | -0.004 | -6.028 | 0.000 |

Reading: (i) sign is economically right (stock build → price down); (ii) the effect is **contemporaneous**, i.e. absorbed within the release day — no next-day drift (p = 0.86); (iii) a small pre-release footprint on Tuesday (p = 0.038) is consistent with the API report the evening before [INF]; (iv) 2007-2014 and 2015-2020 significant, **2021-2026 not** (t = -1.11) — pricing has moved to minutes. It is therefore an *event-clock* information source, not a daily-bar factor; a daily test can neither confirm executability nor rule it out.

Natural-gas storage surprise and CPC weather anomalies: the release-day tests reach q ≈ 0.06–0.08 **but with the economically wrong sign** (larger-than-seasonal injection → price *up*; colder-than-normal → price *down*) and no next-day effect → classified INCONCLUSIVE, not retained (sign check applied after seeing results — disclosed). IMF PortWatch chokepoint transits vs WTI weekly (2-week lag): coefficient 0.189, p = 0.16, n = 381 → no evidence.

EIA series-level `last_updated` (only vintage-like field available) [OBS `eia_series_last_updated.json`]: {'PET.WCESTUS1.W_updated': '2026-09-23T18:02:54-04:00', 'PET.RWTC.D_updated': '2026-09-23T18:02:54-04:00', 'PET.RBRTE.D_updated': '2026-09-23T18:02:54-04:00', 'NG.NW2_EPG0_SWO_R48_BCF.W_updated': '2026-09-24T15:54:15-04:00', 'NG.RNGWHHD.D_updated': '2026-09-23T18:02:54-04:00'}.

### SEC EDGAR (submissions, XBRL frames, full-text search)  
`sec_edgar` · public government · executed **Y** · PIT **PIT_NATIVE** · info **UNTESTED_LOW_POWER**

* **access:** https://data.sec.gov/submissions/CIK*.json, /api/xbrl/frames/..., https://efts.sec.gov/LATEST/search-index [OBS]; www.sec.gov HTML/atom returned 403 for our User-Agent [OBS]
* **cost:** free-nokey
* **history:** acceptance time ~ real time; coverage — Bitcoin ETF issuer CIK: filings since 2023-06 [OBS]
* **latency:** HTTP median 516 ms; freshness 1315.0 h; statuses 200,200,403,200
* **timestamp semantics:** Every filing has acceptanceDateTime (second resolution) [OBS n=74 for one CIK]
* **revision semantics:** Amendments are new filings; frames data restated per latest filing [INF]
* **PIT readiness:** PIT_NATIVE
* **licence:** Site fair-access pages returned 403 to our fetch; fair-access policy requires declared UA and rate limit [UNK details]
* **rate limits:** 403 when UA not accepted; EFTS returned 500 once then 200 [OBS]
* **operational stability:** probe statuses 200,200,403,200
* **note:** acceptanceDateTime = true publication time; ETF share/flow data are only in periodic filings (lag) -> no daily flow series.

### IMF PortWatch daily chokepoint transits (ArcGIS FeatureServer)  
`imf_portwatch` · shipping · executed **Y** · PIT **LOOKAHEAD_RISK** · info **TESTED_NO_INCREMENT**

* **access:** REST https://services9.arcgis.com/.../Daily_Chokepoints_Data/FeatureServer/0/query [OBS]; 5 chokepoints x 2827 days pulled [OBS data]
* **cost:** free-nokey
* **history:** ~2 days; coverage — 2019-01-01 -> 2026-09-27 (2-day freshness) [OBS]
* **latency:** HTTP median 686 ms; freshness 43914.6 h; statuses 200,200
* **timestamp semantics:** Daily date field (no publication stamp); layer Last-Modified header (12:20 UTC) [OBS]
* **revision semantics:** Vessel counts are AIS-derived and revised as AIS backfills [INF]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** IMF copyright page returned 403; data-and-methodology page had no licence text [UNK]
* **rate limits:** Not measured; 2000-record page limit [OBS]
* **operational stability:** probe statuses 200,200
* **note:** Genuine physical-flow data; no weekly WTI effect found at 2-week lag.

### AISHub  
`aishub` · shipping · executed **N** · PIT **UNKNOWN** · info **UNTESTED_BLOCKED**

* **access:** Reachable; 'Invalid username or password' [OBS]
* **cost:** free-key
* **history:** n/a; coverage — 
* **latency:** HTTP median 1259 ms; freshness n/a; statuses 200
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** UNKNOWN
* **licence:** Data-sharing membership model [UNK]
* **rate limits:** n/a
* **operational stability:** probe statuses 200
* **note:** Needs membership.

### Stooq Baltic Dry Index CSV  
`stooq_bdi` · shipping · executed **N** · PIT **UNKNOWN** · info **UNTESTED_BLOCKED**

* **access:** Connection reset by peer [OBS]
* **cost:** free-nokey
* **history:** n/a; coverage — 
* **latency:** HTTP median n/a; freshness n/a; statuses 0
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** UNKNOWN
* **licence:** n/a
* **rate limits:** n/a
* **operational stability:** probe statuses 0
* **note:** Unreachable.

### EIA bulk files (PET.zip, NG.zip) + WPSR/ NG storage release files  
`eia_bulk_wpsr` · energy inventories · executed **Y** · PIT **LOOKAHEAD_RISK** · info **TESTED_CANDIDATE**

* **access:** https://www.eia.gov/opendata/bulk/{PET,NG}.zip ; https://ir.eia.gov/wpsr/table1.csv ; https://ir.eia.gov/ngs/ngs.html [OBS]
* **cost:** free-nokey
* **history:** Wed 10:30 ET (rule) / Thu 10:30 ET gas [rule, not verified]; coverage — Crude stocks 2295 weekly points (1982->), WTI/Brent daily since 1986/1987, HH spot & gas storage [OBS]
* **latency:** HTTP median 5124 ms; freshness n/a; statuses 200,200,200,200
* **timestamp semantics:** Weekly series dated week-ending Friday; series-level 'last_updated' only [OBS]; WPSR file Last-Modified Wed 13:37 UTC [OBS]
* **revision semantics:** No per-row vintages; series overwritten on each release [OBS series 'last_updated' only]
* **PIT readiness:** LOOKAHEAD_RISK — Bulk files have no vintages -> LOOKAHEAD_RISK by mission definition; weekly first-release values rarely revised but that is [UNK].
* **licence:** 'U.S. government publications are in the public domain' [DOC eia.gov/about/copyrights_reuse.php]
* **rate limits:** None observed; 56 MB zip downloads in ~10 s [OBS]
* **operational stability:** probe statuses 200,200,200,200
* **note:** Weekly crude inventory surprise is the only non-market series with a robust, price-independent, economically signed effect.

### EIA API v2  
`eia_api_v2` · energy inventories · executed **N** · PIT **PIT_ADAPTABLE** · info **UNTESTED_BLOCKED**

* **access:** HTTP 403 API_KEY_MISSING [OBS]; free key by registration [DOC eia.gov/opendata/documentation]
* **cost:** free-key
* **history:** n/a; coverage — same as bulk
* **latency:** HTTP median n/a; freshness n/a; statuses 403
* **timestamp semantics:** period + series
* **revision semantics:** no vintages [UNK]
* **PIT readiness:** PIT_ADAPTABLE
* **licence:** Public domain [DOC]
* **rate limits:** not measured
* **operational stability:** probe statuses 403
* **note:** Needs free key (not available in sandbox); bulk used instead.

### GIE AGSI+ EU gas storage  
`gie_agsi` · energy inventories · executed **N** · PIT **UNKNOWN** · info **UNTESTED_BLOCKED**

* **access:** Reachable; 'Invalid or missing API key' [OBS]
* **cost:** free-key
* **history:** n/a; coverage — 
* **latency:** HTTP median 825 ms; freshness n/a; statuses 200
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** UNKNOWN
* **licence:** n/a
* **rate limits:** n/a
* **operational stability:** probe statuses 200
* **note:** Needs free key.

### Open-Meteo (forecast, archive, historical-forecast)  
`open_meteo` · weather · executed **Y** · PIT **PIT_ADAPTABLE** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** REST https://api.open-meteo.com ; historical-forecast-api returned 48 hourly rows in one probe [OBS]; forecast and archive returned 429 'Daily API request limit exceeded' [OBS]
* **cost:** free-nokey
* **history:** hourly; coverage — Global; historical-forecast since 2022 [UNK]
* **latency:** HTTP median 863 ms; freshness 24019.6 h; statuses 429,429,200
* **timestamp semantics:** Hourly timestamps; historical-forecast API stores archived model runs (as-of forecasts) [DOC-indirect/OBS 48 rows]
* **revision semantics:** Archived forecasts are as-issued (PIT-friendly) [INF]
* **PIT readiness:** PIT_ADAPTABLE
* **licence:** Free API: non-commercial only, <10,000 calls/day, 5,000/h, 600/min, CC-BY 4.0 [DOC open-meteo.com/en/terms]
* **rate limits:** Daily limit exhausted by shared egress IP [OBS]
* **operational stability:** probe statuses 429,429,200
* **note:** Best weather-forecast PIT candidate; blocked by shared-IP quota so forecast-surprise vs gas not tested.

### NOAA/NWS api.weather.gov  
`nws_api` · weather · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** https://api.weather.gov/gridpoints/HGX/65,97/forecast [OBS]
* **cost:** free-nokey
* **history:** live; coverage — 14 periods ahead
* **latency:** HTTP median 484 ms; freshness -148.4 h; statuses 200
* **timestamp semantics:** period start/end
* **revision semantics:** Current forecast only; no archive [OBS]
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Public domain unless annotated [DOC weather.gov/disclaimer]
* **rate limits:** Not measured
* **operational stability:** probe statuses 200
* **note:** Forward capture only.

### NOAA CPC population-weighted degree days  
`noaa_cpc_degree_days` · weather · executed **Y** · PIT **LOOKAHEAD_RISK** · info **TESTED_NO_INCREMENT**

* **access:** https://ftp.cpc.ncep.noaa.gov/htdocs/degree_days/weighted/daily_data/{year}/Population.Heating.txt ; 2005-2026 pulled [OBS]
* **cost:** free-nokey
* **history:** ~1 day; coverage — CONUS+9 divisions daily 2005-> [OBS]
* **latency:** HTTP median 576 ms; freshness n/a; statuses 200
* **timestamp semantics:** Daily columns; file Last-Modified for 2024 = 2025-01-02 (yearly rewrite) [OBS]
* **revision semantics:** Observed weather (not forecast); files rewritten [OBS]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** Public domain [DOC weather.gov/disclaimer]
* **rate limits:** none
* **operational stability:** probe statuses 200
* **note:** Realised HDD anomaly is public and priced; no next-day increment.

### NOAA NCEI Access Data Service (GHCN-daily)  
`noaa_ncei` · weather · executed **Y** · PIT **LOOKAHEAD_RISK** · info **UNTESTED_LOW_POWER**

* **access:** https://www.ncei.noaa.gov/access/services/data/v1 [OBS]
* **cost:** free-nokey
* **history:** days; coverage — Stations back decades
* **latency:** HTTP median 568 ms; freshness 52578.6 h; statuses 200
* **timestamp semantics:** Daily
* **revision semantics:** QC flags/rewrites [INF]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** Public domain [DOC weather.gov/disclaimer applies to NOAA sites; NCEI page not fetched]
* **rate limits:** Not measured
* **operational stability:** probe statuses 200
* **note:** Not used in tests.

### NASA POWER daily API  
`nasa_power` · weather · executed **Y** · PIT **LOOKAHEAD_RISK** · info **UNTESTED_LOW_POWER**

* **access:** https://power.larc.nasa.gov/api/temporal/daily/point [OBS]
* **cost:** free-nokey
* **history:** ~days; coverage — Global 1981->
* **latency:** HTTP median 517 ms; freshness n/a; statuses 200
* **timestamp semantics:** Daily
* **revision semantics:** Reanalysis re-processed [INF]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** Docs fetched; no licence keywords [UNK]
* **rate limits:** Not measured
* **operational stability:** probe statuses 200
* **note:** Not used.

### NOAA GFS on AWS open data (S3)  
`noaa_gfs_s3` · weather · executed **Y** · PIT **PIT_NATIVE** · info **UNTESTED_LOW_POWER**

* **access:** https://noaa-gfs-bdp-pds.s3.amazonaws.com/ listing [OBS]
* **cost:** free-nokey
* **history:** ~4 h after cycle [UNK]; coverage — Global NWP since 2021 [UNK]
* **latency:** HTTP median 527 ms; freshness n/a; statuses 200
* **timestamp semantics:** Run cycle in path (gfs.YYYYMMDD/HH) + S3 LastModified [OBS listing]
* **revision semantics:** Model runs are immutable files [INF]
* **PIT readiness:** PIT_NATIVE
* **licence:** NOAA open data (public domain) [INF]
* **rate limits:** S3
* **operational stability:** probe statuses 200
* **note:** The PIT-native forecast source; GRIB processing out of scope.

### US Treasury FiscalData (Daily Treasury Statement: TGA)  
`treasury_fiscaldata` · public government · executed **Y** · PIT **LOOKAHEAD_RISK** · info **TESTED_NO_INCREMENT**

* **access:** https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance [OBS]
* **cost:** free-nokey
* **history:** T+1 business day; coverage — Our filter returned 2022-04-18 -> 2026-09-25 [OBS]
* **latency:** HTTP median 1310 ms; freshness 4026.6 h; statuses 200
* **timestamp semantics:** record_date only; DTS published next business day ~16:00 ET [rule, not verified]
* **revision semantics:** No vintages; series changed account names (TGA 'closing balance' rows have close_today_bal='null', open_today_bal used) [OBS]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** 'free, without restriction ... commercial or non-commercial' [DOC fiscaldata.treasury.gov/api-documentation]
* **rate limits:** Not documented on fetched page; none hit
* **operational stability:** probe statuses 200
* **note:** Liquidity signal; no increment for crypto returns/vol.

### NY Fed Markets API (reverse-repo operations)  
`nyfed_reverse_repo` · public government · executed **Y** · PIT **LOOKAHEAD_RISK** · info **TESTED_NO_INCREMENT**

* **access:** https://markets.newyorkfed.org/api/rp/reverserepo/propositions/search.json [OBS]
* **cost:** free-nokey
* **history:** T+0; coverage — 2020-09-01 -> 2026-09-28 (1525 rows) [OBS]
* **latency:** HTTP median 700 ms; freshness 42.6 h; statuses 200
* **timestamp semantics:** operationDate; operation results published same day ~1:15 pm ET [rule, not verified]
* **revision semantics:** No vintages for RRP; other NY Fed endpoints carry revisionIndicator (report 005)
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** Terms page fetched, no keywords [UNK]
* **rate limits:** none hit
* **operational stability:** probe statuses 200
* **note:** Liquidity signal; no increment.

### FRED / ALFRED CSV  
`fred_alfred` · public government · executed **N** · PIT **PIT_NATIVE** · info **UNTESTED_BLOCKED**

* **access:** fredgraph.csv and alfred.stlouisfed.org timed out (15-20 s) from sandbox [OBS]
* **cost:** free-key
* **history:** n/a; coverage — 
* **latency:** HTTP median n/a; freshness n/a; statuses 0
* **timestamp semantics:** ALFRED vintage dates (documented in report 005)
* **revision semantics:** ALFRED = native vintages [DOC-prior]
* **PIT readiness:** PIT_NATIVE
* **licence:** Terms page unreachable [OBS]
* **rate limits:** n/a
* **operational stability:** probe statuses 0
* **note:** Unreachable here; would be the PIT_NATIVE macro source.

### Federal Reserve H.4.1 data download  
`fed_h41` · public government · executed **N** · PIT **UNKNOWN** · info **UNTESTED_BLOCKED**

* **access:** HTTP 200 with empty body for guessed series hash [OBS]
* **cost:** free-nokey
* **history:** n/a; coverage — 
* **latency:** HTTP median 516 ms; freshness n/a; statuses 200
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** UNKNOWN
* **licence:** n/a
* **rate limits:** n/a
* **operational stability:** probe statuses 200
* **note:** Need correct series id; not pursued.

### ECB euro FX reference rates  
`ecb_eurofxref` · public government · executed **Y** · PIT **PIT_ADAPTABLE** · info **PRICE_DATA_NOT_ALT**

* **access:** https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml [OBS]
* **cost:** free-nokey
* **history:** n/a; coverage — FX
* **latency:** HTTP median 918 ms; freshness n/a; statuses 200
* **timestamp semantics:** Daily fixing date
* **revision semantics:** OBS_STATUS exists in SDMX (report 005)
* **PIT readiness:** PIT_ADAPTABLE
* **licence:** Not fetched [UNK]
* **rate limits:** none
* **operational stability:** probe statuses 200
* **note:** FX price data: not alternative data.

### IMF DataMapper API  
`imf_datamapper` · public government · executed **N** · PIT **UNKNOWN** · info **UNTESTED_BLOCKED**

* **access:** HTTP 403 Access Denied [OBS]
* **cost:** free-nokey
* **history:** n/a; coverage — 
* **latency:** HTTP median n/a; freshness n/a; statuses 403
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** UNKNOWN
* **licence:** n/a
* **rate limits:** n/a
* **operational stability:** probe statuses 403
* **note:** Blocked.
