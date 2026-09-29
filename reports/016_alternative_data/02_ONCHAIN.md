# 02 — On-chain, mempool, exchange-flow, developer ecosystem

> External research only — no private AurumShift code, no integration claims. Evidence tags: **[OBS]** observed in this study, **[DOC]** stated on a provider page/API response fetched in this study, **[INF]** inference, **[UNK]** unknown/not verified. Study date 2026-09-29 (sandbox clock). Reproduce with `bench/alternative_data_v1/`.


**Bottom line.** Free on-chain data is plentiful and clean at the *event* level (blocks) but the convenient aggregated feeds (Coin Metrics community, Blockchain.com, DefiLlama) serve **recomputed** history. None of the tested on-chain blocks adds out-of-sample information about next-day return or range beyond price/volume/vol/funding/OI + calendar controls. Exchange *flows* (Coin Metrics `FlowIn/OutEx*`) are 41 % explained by same-day price/range/volume moves (react R² = 0.41) — they are largely a price-reactive quantity. The one crypto series that passes is options-implied volatility (Deribit DVOL), which is market-derived.

Test blocks (2021-01 → 2026-09, BTC and ETH where data exist; conservative availability lags in `06`):
| cand | klass | min_p_incr | min_q_fam | max_oos_gain_pct | react_ctmp_max | red_base_max |
|---|---|---|---|---|---|---|
| deribit_dvol_CONTROL_implied_vol | INCREMENTAL_CANDIDATE | 0.000 | 0.000 | 2.292 | 0.190 | 0.422 |
| binance_um_positioning_ratios | INDEPENDENT_NO_EVIDENCE | 0.019 | 0.213 | -0.009 | 0.324 | 0.442 |
| cm_tx_count | INDEPENDENT_NO_EVIDENCE | 0.031 | 0.213 | -0.055 | 0.129 | 0.236 |
| cm_hashrate | INDEPENDENT_NO_EVIDENCE | 0.033 | 0.213 | -0.281 | 0.008 | 0.028 |
| npm_downloads_npm_web3 | INDEPENDENT_NO_EVIDENCE | 0.067 | 0.307 | -0.218 | 0.198 | 0.663 |
| CONTROL_noise_A | INDEPENDENT_NO_EVIDENCE | 0.071 |  | 0.154 | 0.008 | -0.002 |
| bc_tx_fees_btc | INDEPENDENT_NO_EVIDENCE | 0.098 | 0.381 | -0.461 | 0.127 | 0.255 |
| CONTROL_noise_B | INDEPENDENT_NO_EVIDENCE | 0.196 |  | -0.176 | -0.000 | -0.000 |
| bc_mempool_size | INDEPENDENT_NO_EVIDENCE | 0.230 | 0.509 | -0.317 | 0.019 | 0.034 |
| npm_downloads_npm_ethers | PRICE_DERIVATIVE_ONLY | 0.006 | 0.189 | -0.195 | 0.212 | 0.688 |
| llama_dex_volume | PRICE_DERIVATIVE_ONLY | 0.013 | 0.213 | 0.204 | 0.500 | 0.611 |
| cm_exchange_flows | PRICE_DERIVATIVE_ONLY | 0.024 | 0.213 | 0.292 | 0.414 | 0.636 |
| npm_downloads_npm_solana_web3.js | PRICE_DERIVATIVE_ONLY | 0.034 | 0.213 | -0.326 | 0.214 | 0.726 |
| cm_active_addresses | PRICE_DERIVATIVE_ONLY | 0.051 | 0.298 | -0.145 | 0.211 | 0.420 |
| CONTROL_price_derived_drawdown_mom | PRICE_DERIVATIVE_ONLY | 0.057 |  | 0.068 | 0.332 | 0.726 |
| llama_stablecoin_supply | PRICE_DERIVATIVE_ONLY | 0.096 | 0.381 | 0.200 | 0.187 | 0.546 |
| npm_downloads_npm_bitcoinjs-lib | PRICE_DERIVATIVE_ONLY | 0.124 | 0.428 | -0.773 | 0.291 | 0.761 |
| bc_unique_addresses | PRICE_DERIVATIVE_ONLY | 0.166 | 0.473 | -0.194 | 0.215 | 0.489 |
| bc_tx_count | PRICE_DERIVATIVE_ONLY | 0.175 | 0.473 | -0.130 | 0.013 | 0.059 |
| cm_mvrv_CONTROL_price_derived | PRICE_DERIVATIVE_ONLY | 0.177 |  | -0.303 | 0.875 | 0.726 |

Details, controls and sensitivity in `07`. Mempool state (the one *genuinely new* on-chain datum: fee histogram/backlog) has **no history endpoint** [OBS]; it is only usable if captured forward.

### Coin Metrics Community API v4  
`coinmetrics_community` · on-chain · executed **Y** · PIT **LOOKAHEAD_RISK** · info **TESTED_NO_INCREMENT**

* **access:** REST JSON https://community-api.coinmetrics.io/v4 ; no key [DOC]; 32 community metrics incl. exchange flows (FlowIn/OutEx*), SplyEx*, active addresses, tx count, MVRV, hash rate [OBS catalog]
* **cost:** free-nokey
* **history:** 2009 -> T-1d; completion lag median 3-5 h after day end for 2021+ rows, 2807 h (backfilled) for 2020 rows [OBS]; coverage — BTC/ETH + many assets; BTC history from 2009-01-03 [OBS]; exchange flows from 2011-04-24 [OBS]
* **latency:** HTTP median 848 ms; freshness 42.6 h; statuses 200
* **timestamp semantics:** Daily rows dated at day start; per-row AssetCompletionTime (unix s) [OBS]; per-metric '-status' and '-status-time' fields [OBS]
* **revision semantics:** All 2219 sampled rows have status=flash [OBS]; 2067/2219 rows carry status-time in 2026-04 (bulk recompute) and 2024/2219 rows were recomputed >30d after completion -> served values are NOT the originally published values [OBS]. Exchange-flow metrics depend on retro-labelled exchange address clusters [INF].
* **PIT readiness:** LOOKAHEAD_RISK — Only 2021+ rows have plausible original completion stamps; even those were recomputed in 2026-04.
* **licence:** 'Creative Commons license' [DOC docs.coinmetrics.io]; variant (NC?) not stated on fetched page [UNK] -> treat as non-commercial-only until confirmed
* **rate limits:** 6000 req / 20 s sliding window (x-ratelimit-limit header) [OBS]
* **operational stability:** probe statuses 200
* **note:** Best free on-chain candidate for FORWARD capture: completion timestamp + status fields allow first-seen PIT logging; history is recomputed -> LOOKAHEAD_RISK.

### Blockchain.com charts API  
`blockchain_com_charts` · on-chain · executed **Y** · PIT **LOOKAHEAD_RISK** · info **TESTED_NO_INCREMENT**

* **access:** REST JSON https://api.blockchain.info/charts/{chart}?timespan=all [OBS]
* **cost:** free-nokey
* **history:** 2009 -> T-1d; coverage — BTC network stats since 2009 [OBS n=6454]
* **latency:** HTTP median 513 ms; freshness 42.6 h; statuses 200
* **timestamp semantics:** Daily bucket start timestamps only; last-modified header = request time [OBS]
* **revision semantics:** No revision/vintage information exposed; values may be recomputed silently [UNK]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** Site terms fetched limit use of 'the Services' to personal non-commercial use [DOC blockchain.com/legal/terms]; whether this applies to the charts API is [UNK]
* **rate limits:** Undocumented for unauthenticated use (auth key optional, 'default rate limits') [DOC]
* **operational stability:** probe statuses 200
* **note:** Cross-check source for Coin Metrics; history rows have no publication stamps.

### mempool.space REST API  
`mempool_space` · mempool · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** REST JSON https://mempool.space/api/... (blocks, mempool snapshot, fee histogram, recommended fees, hashrate, block-fee history) [OBS]
* **cost:** free-nokey
* **history:** Mempool congestion is only observable live; coverage — BTC mainnet; block-fee history since 2009 (6474 rows), hashrate 3y [OBS]
* **latency:** HTTP median 498 ms; freshness 0.1 h; statuses 200,200,200,200,200
* **timestamp semantics:** Blocks: header timestamp (miner-set, not publication) + height + hash + 'stale' flag; mempool/fee endpoints are live snapshots with no timestamp [OBS]
* **revision semantics:** Block history immutable except reorgs [INF]; mempool/fee-histogram have NO history endpoint -> cannot be reconstructed [OBS]
* **PIT readiness:** SNAPSHOT_ONLY — Historical block-fee aggregates are a restated derivative; mempool snapshots need self-capture.
* **licence:** Terms page fetched but no licence keywords found [UNK]; software is open source [INF]
* **rate limits:** No published limits found on fetched pages; none hit in 3-call bursts [OBS]
* **operational stability:** probe statuses 200,200,200,200,200
* **note:** Mempool state (the genuinely new datum) is snapshot-only: usable only if you poll & store it yourself (forward PIT).

### Blockstream Esplora API  
`blockstream_esplora` · on-chain · executed **Y** · PIT **PIT_ADAPTABLE** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** REST https://blockstream.info/api/... (tip height tested) [OBS]
* **cost:** free-nokey
* **history:** chain history; coverage — Bitcoin mainnet
* **latency:** HTTP median 730 ms; freshness n/a; statuses 200
* **timestamp semantics:** Block height/hash immutable except reorgs [INF]
* **revision semantics:** n/a
* **PIT readiness:** PIT_ADAPTABLE
* **licence:** Not fetched [UNK]
* **rate limits:** not measured
* **operational stability:** probe statuses 200
* **note:** Raw-chain access; heavy to derive flows yourself.

### Blockchair API (free tier)  
`blockchair` · on-chain · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** REST https://api.blockchair.com/bitcoin/stats [OBS]; docs page returned 401 to our fetch [OBS]
* **cost:** free-nokey
* **history:** snapshot; coverage — Multi-chain
* **latency:** HTTP median 926 ms; freshness -0.0 h; statuses 200
* **timestamp semantics:** Snapshot with cache metadata
* **revision semantics:** n/a
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Not verified [UNK]
* **rate limits:** Not measured (docs not readable) [UNK]
* **operational stability:** probe statuses 200
* **note:** Only current stats exercised.

### Public Ethereum JSON-RPC (publicnode)  
`ethereum_public_rpc` · on-chain · executed **Y** · PIT **PIT_ADAPTABLE** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** JSON-RPC POST https://ethereum-rpc.publicnode.com ; eth_getBlockByNumber('latest') parsed [OBS]
* **cost:** free-nokey
* **history:** full chain via archive nodes [UNK]; coverage — Ethereum mainnet
* **latency:** HTTP median 498 ms; freshness -0.0 h; statuses 200
* **timestamp semantics:** Block timestamp (validator-set) + number + hash; immutability after finality [INF]
* **revision semantics:** Reorg risk pre-finality [INF]
* **PIT readiness:** PIT_ADAPTABLE
* **licence:** Not verified [UNK]
* **rate limits:** Not measured; llamarpc returned 525 (unstable) [OBS]
* **operational stability:** probe statuses 200
* **note:** Gas/base-fee is on-chain congestion truth with block-level PIT; no history pulled here.

### Etherscan API (V1 no-key)  
`etherscan_free` · on-chain · executed **N** · PIT **UNKNOWN** · info **UNTESTED_BLOCKED**

* **access:** Reachable; V1 endpoint deprecated, requires V2 API key [OBS response text]
* **cost:** free-key
* **history:** n/a; coverage — Ethereum
* **latency:** HTTP median 579 ms; freshness n/a; statuses 200
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** UNKNOWN
* **licence:** Not fetched [UNK]
* **rate limits:** n/a
* **operational stability:** probe statuses 200
* **note:** Needs (free) key; none available in sandbox.

### DefiLlama free API (stablecoins, TVL, DEX volume, fees)  
`defillama_free` · on-chain · executed **Y** · PIT **LOOKAHEAD_RISK** · info **TESTED_NO_INCREMENT**

* **access:** REST JSON https://stablecoins.llama.fi, https://api.llama.fi [OBS]; bridges endpoint returned HTTP 402 'upgrade to paid API plan' [OBS]
* **cost:** free-nokey
* **history:** T-0/T-1; coverage — Stablecoin supply since 2017-11, DEX volume 2014, TVL 2017 [OBS]
* **latency:** HTTP median 640 ms; freshness 18.6 h; statuses 200,200,200,402
* **timestamp semantics:** Daily unix-s buckets; response has last-modified/age headers = cache time only [OBS]
* **revision semantics:** Series are recomputed/restated as protocols are added or repriced (documented behaviour not verified; Wayback vintage check blocked by HTTP 429) [UNK]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** Docs page returned 403 to our fetch; licence [UNK]
* **rate limits:** Not published on fetched pages [UNK]; none hit
* **operational stability:** probe statuses 200,200,200,402
* **note:** Restated history; bridges paid.

### Glassnode API  
`glassnode` · on-chain · executed **N** · PIT **UNKNOWN** · info **UNTESTED_BLOCKED**

* **access:** HTTP 401 'Authorization Required' [OBS]
* **cost:** paid/key
* **history:** n/a; coverage — 
* **latency:** HTTP median n/a; freshness n/a; statuses 401
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** UNKNOWN
* **licence:** Not fetched [UNK]
* **rate limits:** n/a
* **operational stability:** probe statuses 401
* **note:** Free tier limited/keyed [UNK].

### beaconcha.in API  
`beaconcha_in` · on-chain · executed **N** · PIT **UNKNOWN** · info **UNTESTED_BLOCKED**

* **access:** HTTP 401 'a valid API key is required' [OBS]
* **cost:** free-key
* **history:** n/a; coverage — 
* **latency:** HTTP median n/a; freshness n/a; statuses 401
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** UNKNOWN
* **licence:** Not fetched [UNK]
* **rate limits:** n/a
* **operational stability:** probe statuses 401
* **note:** Staking queue data behind a key.

### CoinGecko public API  
`coingecko_api` · on-chain · executed **N** · PIT **UNKNOWN** · info **PRICE_DATA_NOT_ALT**

* **access:** HTTP 401 on market_chart and /news without key [OBS] (ping returned 200 earlier) 
* **cost:** free-key
* **history:** n/a; coverage — Prices
* **latency:** HTTP median n/a; freshness n/a; statuses 401,401
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** UNKNOWN
* **licence:** API terms fetched: no re-distribution/sub-licensing [DOC coingecko.com/en/api_terms]
* **rate limits:** n/a
* **operational stability:** probe statuses 401,401
* **note:** Price data; not alternative.

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

### Binance futures REST (fapi)  
`binance_fapi` · exchange flows · executed **N** · PIT **PIT_ADAPTABLE** · info **UNTESTED_BLOCKED**

* **access:** HTTP 451 'restricted location' from sandbox egress [OBS]
* **cost:** free-nokey
* **history:** n/a; coverage — 
* **latency:** HTTP median n/a; freshness n/a; statuses 451
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** PIT_ADAPTABLE
* **licence:** n/a
* **rate limits:** n/a
* **operational stability:** probe statuses 451
* **note:** Geo-blocked here; not negative evidence.

### OKX public REST (rubik stats, funding history)  
`okx_public_rubik` · exchange flows · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** REST https://www.okx.com/api/v5/rubik/stat/... [OBS]
* **cost:** free-nokey
* **history:** rolling 72-180 daily points; coverage — BTC/ETH contracts
* **latency:** HTTP median 646 ms; freshness 2.6 h; statuses 200,200,200
* **timestamp semantics:** Bucket start ms
* **revision semantics:** Rolling window only: long/short 180 daily pts (~6 months), taker volume 72 pts, funding ~33 days [OBS] -> history not sufficient for testing
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Docs page fetched; no licence text [UNK]
* **rate limits:** Not measured; none hit
* **operational stability:** probe statuses 200,200,200
* **note:** Useful only by continuous capture.

### Bitfinex public stats (margin long/short position size)  
`bitfinex_margin` · exchange flows · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** REST https://api-pub.bitfinex.com/v2/stats1/pos.size:1m:tBTCUSD:long/hist [OBS]
* **cost:** free-nokey
* **history:** days-weeks per call; coverage — BTCUSD margin
* **latency:** HTTP median 601 ms; freshness -0.0 h; statuses 200
* **timestamp semantics:** ms timestamps, 1-min resolution [OBS]
* **revision semantics:** 10000-row page covered only 7 days (2026-09-22->09-29) [OBS]; deeper paging not tested
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Not fetched [UNK]
* **rate limits:** Not measured
* **operational stability:** probe statuses 200
* **note:** Public margin positioning (funding-market signal); deeper history untested.

### Deribit public API (DVOL index, options book summary)  
`deribit_public` · exchange flows · executed **Y** · PIT **PIT_NATIVE** · info **TESTED_CANDIDATE**

* **access:** REST https://www.deribit.com/api/v2/public/get_volatility_index_data ; get_book_summary_by_currency [OBS]
* **cost:** free-nokey
* **history:** real-time; daily bars T-0; coverage — BTC/ETH; DVOL daily since 2021-03-24 (2015 rows collected) [OBS]
* **latency:** HTTP median 645 ms; freshness -0.0 h; statuses 200,200
* **timestamp semantics:** Index bars with ms open timestamps; JSON-RPC responses carry server usIn/usOut microsecond stamps (report 005) [DOC/OBS-prior]
* **revision semantics:** Closed index bars are immutable prints [INF]; no revision fields [OBS]
* **PIT readiness:** PIT_NATIVE
* **licence:** Docs page fetched; no licence text found [UNK]; API usage policy exists [DOC index]
* **rate limits:** Credit/rate limits documented (not measured); none hit [DOC index]
* **operational stability:** probe statuses 200,200
* **note:** Options-market implied vol: only crypto series to pass OOS tests (vol targets). Market-derived, not 'alternative' in the non-market sense.

### Hyperliquid public info API  
`hyperliquid_info` · exchange flows · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** POST https://api.hyperliquid.xyz/info type=metaAndAssetCtxs [OBS] (GET returns 405)
* **cost:** free-nokey
* **history:** snapshot; coverage — Perps (234 assets) [OBS]
* **latency:** HTTP median 715 ms; freshness n/a; statuses 200
* **timestamp semantics:** Snapshot
* **revision semantics:** n/a
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Not fetched [UNK]
* **rate limits:** Not measured
* **operational stability:** probe statuses 200
* **note:** Snapshot of funding/OI/mark; capture needed.

### Bybit v5 public REST  
`bybit_v5` · exchange flows · executed **N** · PIT **PIT_ADAPTABLE** · info **UNTESTED_BLOCKED**

* **access:** HTTP 403 (CloudFront geo/WAF block) from sandbox egress [OBS]
* **cost:** free-nokey
* **history:** n/a; coverage — 
* **latency:** HTTP median n/a; freshness n/a; statuses 403
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** PIT_ADAPTABLE
* **licence:** n/a
* **rate limits:** n/a
* **operational stability:** probe statuses 403
* **note:** Blocked here; not negative evidence.

### GH Archive hourly event files  
`gharchive` · developer/GitHub · executed **Y** · PIT **PIT_NATIVE** · info **UNTESTED_LOW_POWER**

* **access:** Static gz https://data.gharchive.org/YYYY-MM-DD-H.json.gz ; one hour (18 MB gz, 122,625 events) parsed [OBS]
* **cost:** free-nokey
* **history:** 2011 -> ~5 min after hour end; coverage — All public GitHub events since 2011 [DOC site]; crypto-repo filtering requires full-day scans (~hundreds MB/day)
* **latency:** HTTP median 780 ms; freshness n/a; statuses 200
* **timestamp semantics:** Every event has created_at (second resolution); file Last-Modified = 5.1 min after hour end [OBS pit_probes.json]
* **revision semantics:** Immutable hourly files [INF]; events for later-deleted repos remain [UNK]
* **PIT readiness:** PIT_NATIVE
* **licence:** Site states BigQuery free 1 TB/month processing [DOC]; underlying GitHub event licensing [UNK]
* **rate limits:** Static CDN
* **operational stability:** probe statuses 200
* **note:** Only PIT-clean developer feed found, but a multi-year crypto-repo series was not built (bandwidth budget).

### GitHub REST API (commits/releases of crypto repos)  
`github_rest_api` · developer/GitHub · executed **N** · PIT **LOOKAHEAD_RISK** · info **UNTESTED_BLOCKED**

* **access:** HTTP 403 from proxy: session scoped to one repository (deliberately not bypassed) [OBS]
* **cost:** free-key
* **history:** n/a; coverage — 
* **latency:** HTTP median n/a; freshness n/a; statuses 403
* **timestamp semantics:** commit author/committer dates are author-controlled, not push time [INF]
* **revision semantics:** History rewrites via force-push [INF]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** n/a
* **rate limits:** Documented core limit 15000/h was returned for the session token by /rate_limit [OBS] (not used)
* **operational stability:** probe statuses 403
* **note:** Commit dates are not publication times -> LOOKAHEAD_RISK even if fetched.

### npm download counts API  
`npm_downloads` · developer/GitHub · executed **Y** · PIT **LOOKAHEAD_RISK** · info **TESTED_NO_INCREMENT**

* **access:** REST https://api.npmjs.org/downloads/range/{a}:{b}/{pkg} ; 4 crypto libs pulled 2020-09 -> 2026-09 [OBS]
* **cost:** free-nokey
* **history:** T-1d; coverage — Package downloads since 2015 [INF]
* **latency:** HTTP median 594 ms; freshness 40194.6 h; statuses 200
* **timestamp semantics:** Daily buckets [OBS]
* **revision semantics:** No revision info; counts include CI/mirror traffic [INF]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** Terms page returned 404 [UNK]
* **rate limits:** Range limited per request (chunked 18 months) [OBS]
* **operational stability:** probe statuses 200
* **note:** Weekday seasonality masqueraded as signal until calendar dummies were added (see 07).

### PyPI download stats  
`pypistats` · developer/GitHub · executed **Y** · PIT **LOOKAHEAD_RISK** · info **UNTESTED_LOW_POWER**

* **access:** REST https://pypistats.org/api/packages/web3/overall [OBS]
* **cost:** free-nokey
* **history:** ~180 d; coverage — PyPI
* **latency:** HTTP median 555 ms; freshness 42.6 h; statuses 200
* **timestamp semantics:** Daily
* **revision semantics:** Rolling ~180-day window only [OBS n=368]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** Not fetched [UNK]
* **rate limits:** Not measured
* **operational stability:** probe statuses 200
* **note:** Window too short.

### crates.io download stats  
`crates_io` · developer/GitHub · executed **Y** · PIT **LOOKAHEAD_RISK** · info **UNTESTED_LOW_POWER**

* **access:** REST https://crates.io/api/v1/crates/bitcoin/downloads [OBS]
* **cost:** free-nokey
* **history:** ~90 d; coverage — crates.io
* **latency:** HTTP median 476 ms; freshness 18.6 h; statuses 200
* **timestamp semantics:** Daily
* **revision semantics:** ~90-day window only [OBS n=355 rows across versions]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** Not fetched [UNK]
* **rate limits:** Not measured
* **operational stability:** probe statuses 200
* **note:** Window too short.
