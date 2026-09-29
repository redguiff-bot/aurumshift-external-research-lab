# 04 — Positioning and flows (CFTC, exchange positioning, ETF/public flows)

> External research only — no private AurumShift code, no integration claims. Evidence tags: **[OBS]** observed in this study, **[DOC]** stated on a provider page/API response fetched in this study, **[INF]** inference, **[UNK]** unknown/not verified. Study date 2026-09-29 (sandbox clock). Reproduce with `bench/alternative_data_v1/`.


**Bottom line.** *CFTC TFF (CME Bitcoin)*: leveraged-fund and asset-manager net positioning has partly independent variation from price (react R² = 0.04) but its univariate association with volatility is fully **absorbed** by the baseline (p_univ<0.01 → p_incr = 0.26; OOS gain -0.63 %). *Binance long/short and taker ratios*: reachable and PIT-fresh but no OOS gain (best DM p = 0.51). *ETF flows*: **no free accessible source** in this environment — treat as missing evidence.

CFTC publication-time facts [OBS `pit_probes.json`]: 442 CME-Bitcoin TFF rows; 231 carry a bulk-load `:created_at` (2022-09-13) — for these only the *rule* (Tuesday as-of → Friday ≈15:30 ET) is available; the 211 later rows have real release stamps (weekday counts {'Friday': 183, 'Monday': 16, 'Tuesday': 6, 'Wednesday': 5, 'Thursday': 1}; lag after as-of: median 3.8 d, p90 6.9 d, max 50.9 d — holiday/shutdown delays).

Binance Vision restatement scan [OBS `binance_vision_lastmodified_scan.csv`]: {"spot_kline_1d": {"n": 40, "restated_gt3d": 4, "median_lag_days": -0.3, "max_lag_days": 943.16}, "um_metrics": {"n": 40, "restated_gt3d": 33, "median_lag_days": 371.45, "max_lag_days": 1897.48}}. Fresh files are stamped ~1–3 h after their day; old files were re-uploaded, so `Last-Modified` cannot be trusted as an original publication time for history.

### CFTC Commitments of Traders (Socrata public reporting)  
`cftc_cot_socrata` · CFTC positioning · executed **Y** · PIT **PIT_ADAPTABLE** · info **TESTED_NO_INCREMENT**

* **access:** REST https://publicreporting.cftc.gov/resource/{gpe5-46if TFF, 6dca-aqww legacy, 72hh-3qpy disaggregated}.json [OBS]; legacy deacot.txt URL 404 [OBS]
* **cost:** free-nokey
* **history:** Friday ~15:30 ET for Tuesday data [rule; observed created weekday]; coverage — CME Bitcoin from 2018-04-10; legacy gold since 1986 [OBS]
* **latency:** HTTP median 854 ms; freshness 186.6 h; statuses 200,200,200,404
* **timestamp semantics:** Report date = Tuesday as-of; row-level system field ':created_at' [OBS]
* **revision semantics:** 231/442 CME-Bitcoin TFF rows carry ':created_at' = 2022-09-13 (bulk load); the 211 rows after that carry real release stamps: 183 on Fridays, median lag 3.8 d after as-of, p90 6.9 d, max 50.9 d [OBS pit_probes.json]. Revisions: updated_at==created_at in sample [OBS].
* **PIT readiness:** PIT_ADAPTABLE
* **licence:** US government publication; CFTC site disclaimer page returned 404, reuse terms [UNK]
* **rate limits:** Not published; none hit in 5000-row page
* **operational stability:** probe statuses 200,200,200,404
* **note:** Rule-based PIT for 2018-22 rows, native stamps afterwards; positioning = information about who holds risk, but our test shows it is subsumed by baseline.

### iShares fund pages / holdings CSV (IBIT, IVV)  
`ishares_etf_files` · ETF flows · executed **N** · PIT **UNKNOWN** · info **UNTESTED_BLOCKED**

* **access:** HTTP 200 but HTML page instead of CSV for both IBIT and IVV URL patterns [OBS]
* **cost:** restricted
* **history:** n/a; coverage — 
* **latency:** HTTP median 997 ms; freshness n/a; statuses 200,200
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** UNKNOWN
* **licence:** Not fetched [UNK]
* **rate limits:** n/a
* **operational stability:** probe statuses 200,200
* **note:** No parseable flow data obtained.

### Farside Investors ETF flow tables  
`farside` · ETF flows · executed **N** · PIT **UNKNOWN** · info **UNTESTED_BLOCKED**

* **access:** HTTP 403 Cloudflare 'Just a moment' challenge [OBS]
* **cost:** restricted
* **history:** n/a; coverage — 
* **latency:** HTTP median n/a; freshness n/a; statuses 403
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** UNKNOWN
* **licence:** n/a
* **rate limits:** n/a
* **operational stability:** probe statuses 403
* **note:** Blocked by bot challenge; not bypassed.

### Yahoo Finance chart endpoints (unofficial)  
`yahoo_finance` · ETF flows · executed **N** · PIT **LOOKAHEAD_RISK** · info **PRICE_DATA_NOT_ALT**

* **access:** Exploratory 200s earlier, 429 in logged probe; quote endpoint 401 [OBS]
* **cost:** restricted
* **history:** n/a; coverage — 
* **latency:** HTTP median n/a; freshness n/a; statuses 429
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** Terms fetched: prohibit access by unofficial methods [DOC legal.yahoo.com]
* **rate limits:** 429 [OBS]
* **operational stability:** probe statuses 429
* **note:** Price data; ToS problem.

### Binance Vision futures 'metrics' daily files (OI, long/short ratios, taker ratio; 5-min rows)  
`binance_vision_um_metrics` · exchange flows · executed **Y** · PIT **LOOKAHEAD_RISK** · info **TESTED_NO_INCREMENT**

* **access:** Static files https://data.binance.vision/data/futures/um/daily/metrics/{SYM}/... [OBS]
* **cost:** free-nokey
* **history:** Daily file appears ~1-3 h after day end [OBS Last-Modified of recent files]; coverage — BTCUSDT since 2020-09-01, ETHUSDT since 2021-12-01 [OBS]
* **latency:** HTTP median 625 ms; freshness n/a; statuses 200
* **timestamp semantics:** 5-min row timestamps; file HTTP Last-Modified [OBS]
* **revision semantics:** 33/40 sampled old metrics files have Last-Modified >3 days after their day (median 371 d, max 1897 d) => history re-uploaded; klines 4/40 restated [OBS binance_vision_lastmodified_scan.csv]
* **PIT readiness:** LOOKAHEAD_RISK — Fresh files carry a trustworthy stamp; old files were rewritten.
* **licence:** Terms page fetched but no licence text found; treat as Binance ToS [UNK]
* **rate limits:** Static CDN; 8-thread download of 4400 files without errors [OBS]
* **operational stability:** probe statuses 200
* **note:** OI/funding = baseline; long-short & taker ratios tested as candidates (same venue).
