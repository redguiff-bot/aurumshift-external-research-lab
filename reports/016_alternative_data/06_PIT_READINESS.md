# 06 — PIT readiness and leakage

> External research only — no private AurumShift code, no integration claims. Evidence tags: **[OBS]** observed in this study, **[DOC]** stated on a provider page/API response fetched in this study, **[INF]** inference, **[UNK]** unknown/not verified. Study date 2026-09-29 (sandbox clock). Reproduce with `bench/alternative_data_v1/`.


## Definitions used (strict)
* **PIT_NATIVE** — provider issues per-row (or per-immutable-file) publication/ingestion/event stamps that are not rewritten, and revisions arrive as new rows/files, so an as-of replay needs no consumer-side capture.
* **PIT_ADAPTABLE** — event time plus at least one of {immutable ID/height/hash, finality flag, release-time system field, archived model runs}; a consumer can build PIT *going forward* (or for a documented slice of history) by stamping receipt.
* **LOOKAHEAD_RISK** — historical rows have **no** historical publication timestamp (or values were provably recomputed after the stamp). Mission rule: such history is unusable as-is; it may be used only with a conservative lag and results are upper-bound/contaminated.
* **SNAPSHOT_ONLY** — no history endpoint (or a window of hours-to-months); PIT can only come from continuous self-capture.
* **UNKNOWN** — not executed, so not classifiable from evidence.

Executed sources by class: **PIT_NATIVE 7**, **PIT_ADAPTABLE 6**, **LOOKAHEAD_RISK 17**, **SNAPSHOT_ONLY 17**. All 69 discovered: {'LOOKAHEAD_RISK': 21, 'SNAPSHOT_ONLY': 17, 'PIT_ADAPTABLE': 9, 'UNKNOWN': 14, 'PIT_NATIVE': 8}.

## Evidence gathered (not assumed)
* **Coin Metrics community** [OBS]: `AssetCompletionTime` lag after day end — median by year {'2020': 2807.19, '2021': 4.0, '2022': 5.43, '2023': 5.21, '2024': 3.72, '2025': 3.0, '2026': 3.0} h; 178/2219 rows completed >72 h late (2020 back-fill). Every row `status=flash`. `status-time` (last recompute) distribution: {'2026-04': 2067, '2026-05': 31, '2026-06': 30, '2026-07': 31, '2026-08': 31, '2026-09': 29}; **2024/2219 rows were recomputed >30 days after completion** → served values ≠ originally published values → LOOKAHEAD_RISK for history despite the excellent stamp fields. Exchange flows depend on retro-labelled address clusters [INF].
* **Binance Vision** [OBS]: {"spot_kline_1d": {"n": 40, "restated_gt3d": 4, "median_lag_days": -0.3, "max_lag_days": 943.16}, "um_metrics": {"n": 40, "restated_gt3d": 33, "median_lag_days": 371.45, "max_lag_days": 1897.48}}.
* **CFTC** [OBS]: {"rows": 442, "bulk_loaded_rows": 231, "first_real_stamp_row_date": "2022-09-13", "real_rows": 211, "real_lag_days_median": 3.813094583333333, "real_lag_days_p90": 6.854776076388889, "real_lag_days_max": 50.854681238425925}.
* **GDELT** [OBS]: Last-Modified − nominal stamp = [-9.4, -4.5, -5.4, -8.2, -10.1, -10.0, -10.0] min for 7 files across 2016–2026 (files are written just before their stamp; consistent over 10 years → reliable batch-time stamp).
* **GH Archive** [OBS]: 122,625 events in the 2026-09-27 12:00 file; created_at 2026-09-27T12:00:00Z → 2026-09-27T12:59:57Z; Last-Modified 2026-09-27 13:05:08 (= +5.1 min after hour end).
* **Kalshi** [OBS]: `open_time`, `close_time`, `settlement_ts`, `updated_time` on markets; candlestick history retained after settlement.
* **Wayback vintage comparison** (would have measured DefiLlama/Fear&Greed restatement): **blocked** (HTTP 429/tunnel closed) → restatement of those series is UNKNOWN, classified LOOKAHEAD_RISK by the no-stamp rule.
* **EIA** [OBS]: only series-level `last_updated`; WPSR CSV `Last-Modified` = 13:37 UTC on release day (before the customary 10:30 ET = 14:30 UTC release [rule]) → file stamp is **not** usable as release time.

## Availability lags used in the information tests
| input | lag (obs date ≤ decision date − lag) | reason |
|---|---|---|
| Price/volume/funding/OI baseline | d-1 | real-time exchange data; Binance `metrics` are 5-min rows |
| Coin Metrics flows / activity / hash rate / MVRV | d-2 | completion 2–5 h after day end (median 3–5 h for 2021+) > decision at 00:00 UTC of d |
| Blockchain.com, DefiLlama, Wikimedia, npm (other daily aggregates) | d-2 | no publication stamps → conservative |
| Deribit DVOL (control) | d-1 | daily bar closes at 00:00 UTC |
| Fear & Greed | d-1 | value stamped 00:00 UTC of its date; composition [UNK] |
| NY Fed reverse repo | d-1 | same-day publication (rule) |
| Treasury TGA | d-3 | DTS next-business-day 16:00 ET (rule) + weekend |
| CFTC TFF | release-time | rule Friday 19:30 UTC or real `:created_at` after 2022-09-14; first decision day at/after release |
| Binance long/short & taker ratios | d-1 | 5-min rows; file appears ~1–3 h after day end but real-time REST exists [INF] |
| EIA crude/gas (event study) | release day / next day | rule-based; day-level resolution cannot separate pre/post release |
| PortWatch | 2 weeks | weekly refresh + revisions [INF] |

## Register
| source | exec | PIT | why |
|---|---|---|---|
| Coin Metrics Community API v4 | Y | LOOKAHEAD_RISK | Only 2021+ rows have plausible original completion stamps; even those were recomputed in 2026-04. |
| Blockchain.com charts API | Y | LOOKAHEAD_RISK | No revision/vintage information exposed; values may be recomputed silently [UNK] |
| mempool.space REST API | Y | SNAPSHOT_ONLY | Historical block-fee aggregates are a restated derivative; mempool snapshots need self-capture. |
| Blockstream Esplora API | Y | PIT_ADAPTABLE | n/a |
| Blockchair API (free tier) | Y | SNAPSHOT_ONLY | n/a |
| Public Ethereum JSON-RPC (publicnode) | Y | PIT_ADAPTABLE | Reorg risk pre-finality [INF] |
| Etherscan API (V1 no-key) | N | UNKNOWN | n/a |
| DefiLlama free API (stablecoins, TVL, DEX volume, fees) | Y | LOOKAHEAD_RISK | Series are recomputed/restated as protocols are added or repriced (documented behaviour not verified; Wayback vintage check blocked by HTTP 429) [UNK] |
| Glassnode API | N | UNKNOWN | n/a |
| beaconcha.in API | N | UNKNOWN | n/a |
| CoinGecko public API | N | UNKNOWN | n/a |
| Binance Vision futures 'metrics' daily files (OI, long/short ratios, taker ratio; 5-min rows) | Y | LOOKAHEAD_RISK | Fresh files carry a trustworthy stamp; old files were rewritten. |
| Binance futures REST (fapi) | N | PIT_ADAPTABLE | n/a |
| OKX public REST (rubik stats, funding history) | Y | SNAPSHOT_ONLY | Rolling window only: long/short 180 daily pts (~6 months), taker volume 72 pts, funding ~33 days [OBS] -> history not sufficient for testing |
| Bitfinex public stats (margin long/short position size) | Y | SNAPSHOT_ONLY | 10000-row page covered only 7 days (2026-09-22->09-29) [OBS]; deeper paging not tested |
| Deribit public API (DVOL index, options book summary) | Y | PIT_NATIVE | Closed index bars are immutable prints [INF]; no revision fields [OBS] |
| Hyperliquid public info API | Y | SNAPSHOT_ONLY | n/a |
| Bybit v5 public REST | N | PIT_ADAPTABLE | n/a |
| GH Archive hourly event files | Y | PIT_NATIVE | Immutable hourly files [INF]; events for later-deleted repos remain [UNK] |
| GitHub REST API (commits/releases of crypto repos) | N | LOOKAHEAD_RISK | History rewrites via force-push [INF] |
| npm download counts API | Y | LOOKAHEAD_RISK | No revision info; counts include CI/mirror traffic [INF] |
| PyPI download stats | Y | LOOKAHEAD_RISK | Rolling ~180-day window only [OBS n=368] |
| crates.io download stats | Y | LOOKAHEAD_RISK | ~90-day window only [OBS n=355 rows across versions] |
| Wikimedia REST pageviews | Y | LOOKAHEAD_RISK | Bot-filtering ('user' agent class) may be re-classified retroactively [INF] |
| Google Trends (unofficial endpoints) | N | LOOKAHEAD_RISK | Values normalised per query and resampled on each call [INF] |
| Crypto Fear & Greed Index (alternative.me) | Y | LOOKAHEAD_RISK | No vintages; composite methodology (volatility, momentum/volume, social, dominance, trends) is re-weighted by provider over time [UNK] |
| Hacker News Algolia search API | Y | PIT_ADAPTABLE | Items can be edited/deleted; scores change [INF] |
| Reddit RSS/Atom (r/Bitcoin) | Y | SNAPSHOT_ONLY | Edits/removals invisible |
| Arctic Shift Reddit archive API | Y | LOOKAHEAD_RISK | Deleted/edited content state depends on ingestion time [INF] |
| StockTwits public stream | Y | SNAPSHOT_ONLY | Deletions invisible |
| Mastodon public tag timeline | Y | SNAPSHOT_ONLY | n/a |
| Bluesky public search API | N | UNKNOWN | n/a |
| 4chan /biz/ catalog | Y | SNAPSHOT_ONLY | Threads deleted/pruned |
| LunarCrush API | N | UNKNOWN | n/a |
| GDELT 2.0 raw 15-minute files (GKG/Events/Mentions) | Y | PIT_NATIVE | Files are static per batch [INF]; late arrivals are added to later batches [INF] |
| GDELT DOC 2.0 API (timelines) | N | LOOKAHEAD_RISK | Recomputed each call [INF] |
| Cointelegraph RSS | Y | SNAPSHOT_ONLY | Items can be edited after publication; feed keeps last 30 items = 32 h [OBS] |
| CoinDesk RSS | Y | SNAPSHOT_ONLY | 25 items = 33 h [OBS] |
| Decrypt RSS | Y | SNAPSHOT_ONLY | 56 items = 274 days [OBS] (low-frequency feed) |
| BBC News business RSS | Y | SNAPSHOT_ONLY | 52 items = 91 days [OBS] |
| Federal Reserve press RSS | Y | SNAPSHOT_ONLY | n/a |
| SEC press-release RSS | Y | SNAPSHOT_ONLY | 25 items = 61 days [OBS] |
| ECB press RSS | Y | SNAPSHOT_ONLY | 15 items = 15 days [OBS] |
| US Treasury press RSS | N | UNKNOWN | n/a |
| Polymarket Gamma + CLOB APIs | Y | PIT_NATIVE | Executed prices are immutable prints [INF]; market metadata (titles, resolution) can be edited [INF] |
| Kalshi public market-data API | Y | PIT_NATIVE | Settled markets keep candle history; market fields updated at settlement [OBS] |
| CFTC Commitments of Traders (Socrata public reporting) | Y | PIT_ADAPTABLE | 231/442 CME-Bitcoin TFF rows carry ':created_at' = 2022-09-13 (bulk load); the 211 rows after that carry real release stamps: 183 on Fridays, median lag 3.8 d after as-of, p90 6.9 d, max 50.9 d [OBS pit_probes.json]. Revisions: up |
| iShares fund pages / holdings CSV (IBIT, IVV) | N | UNKNOWN | n/a |
| Farside Investors ETF flow tables | N | UNKNOWN | n/a |
| SEC EDGAR (submissions, XBRL frames, full-text search) | Y | PIT_NATIVE | Amendments are new filings; frames data restated per latest filing [INF] |
| Yahoo Finance chart endpoints (unofficial) | N | LOOKAHEAD_RISK | n/a |
| IMF PortWatch daily chokepoint transits (ArcGIS FeatureServer) | Y | LOOKAHEAD_RISK | Vessel counts are AIS-derived and revised as AIS backfills [INF] |
| AISHub | N | UNKNOWN | n/a |
| Stooq Baltic Dry Index CSV | N | UNKNOWN | n/a |
| EIA bulk files (PET.zip, NG.zip) + WPSR/ NG storage release files | Y | LOOKAHEAD_RISK | Bulk files have no vintages -> LOOKAHEAD_RISK by mission definition; weekly first-release values rarely revised but that is [UNK]. |
| EIA API v2 | N | PIT_ADAPTABLE | no vintages [UNK] |
| GIE AGSI+ EU gas storage | N | UNKNOWN | n/a |
| Open-Meteo (forecast, archive, historical-forecast) | Y | PIT_ADAPTABLE | Archived forecasts are as-issued (PIT-friendly) [INF] |
| NOAA/NWS api.weather.gov | Y | SNAPSHOT_ONLY | Current forecast only; no archive [OBS] |
| NOAA CPC population-weighted degree days | Y | LOOKAHEAD_RISK | Observed weather (not forecast); files rewritten [OBS] |
| NOAA NCEI Access Data Service (GHCN-daily) | Y | LOOKAHEAD_RISK | QC flags/rewrites [INF] |
| NASA POWER daily API | Y | LOOKAHEAD_RISK | Reanalysis re-processed [INF] |
| NOAA GFS on AWS open data (S3) | Y | PIT_NATIVE | Model runs are immutable files [INF] |
| US Treasury FiscalData (Daily Treasury Statement: TGA) | Y | LOOKAHEAD_RISK | No vintages; series changed account names (TGA 'closing balance' rows have close_today_bal='null', open_today_bal used) [OBS] |
| NY Fed Markets API (reverse-repo operations) | Y | LOOKAHEAD_RISK | No vintages for RRP; other NY Fed endpoints carry revisionIndicator (report 005) |
| FRED / ALFRED CSV | N | PIT_NATIVE | ALFRED = native vintages [DOC-prior] |
| Federal Reserve H.4.1 data download | N | UNKNOWN | n/a |
| ECB euro FX reference rates | Y | PIT_ADAPTABLE | OBS_STATUS exists in SDMX (report 005) |
| IMF DataMapper API | N | UNKNOWN | n/a |

## How each LOOKAHEAD_RISK source could be upgraded
Stamp every pull with receipt time and content hash, keep all vintages append-only, and treat data older than the first capture as *contaminated history* (usable only with the lags above). Sources with per-record completion/ingestion stamps (Coin Metrics `AssetCompletionTime`/`status-time`, CFTC `:created_at`, Socrata `:updated_at`) make forward capture verifiable; sources with none (DefiLlama, Blockchain.com, Fear & Greed, EIA bulk, Treasury, NY Fed, PortWatch, npm, Wikimedia) need a first-seen log from day one.
