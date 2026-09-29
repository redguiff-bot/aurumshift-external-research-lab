# 03 — News, RSS, public social, search/trend, prediction markets

> External research only — no private AurumShift code, no integration claims. Evidence tags: **[OBS]** observed in this study, **[DOC]** stated on a provider page/API response fetched in this study, **[INF]** inference, **[UNK]** unknown/not verified. Study date 2026-09-29 (sandbox clock). Reproduce with `bench/alternative_data_v1/`.


**Bottom line.** This is the family where *PIT-native raw material exists* (GDELT 15-minute files, Kalshi/Polymarket price history, GH Archive) but where **no statistical test was run** — either no history exists to test (RSS feeds keep 32 h–274 days; StockTwits 0.5 h; Mastodon 15 h; Reddit 22 h), the API blocked us (GDELT DOC 429, Google Trends 404, Bluesky/Reddit-JSON 403), or building the series exceeds the bandwidth budget (GDELT GKG files are 3.7–11.9 MB each × 96 per day ≈ 0.17 TB per year). What *was* tested: Wikipedia page-views and the Fear & Greed composite, both **no increment**; F&G is classified PRICE_DERIVATIVE_ONLY (same-day price/range explain 43% of its variation).

Retention of feeds (span of items returned by one call) [OBS pit_probes.json]:
| feed | items | span_hours | status | note |
|---|---|---|---|---|
| hackernews_algolia | 100.0 | 1940.1 | nan | nan |
| reddit_rss | 25.0 | 22.6 | nan | nan |
| stocktwits_stream | 30.0 | 0.5 | nan | nan |
| mastodon_tag_bitcoin | 40.0 | 14.9 | nan | nan |
| rss_bbc_business | 52.0 | 2178.2 | nan | nan |
| rss_cointelegraph | 30.0 | 32.2 | nan | nan |
| rss_coindesk | 25.0 | 32.9 | nan | nan |
| rss_decrypt | 56.0 | 6578.1 | nan | nan |
| rss_federal_reserve_press | 20 | nan | 200 | no parsable timestamps or blocked |
| rss_sec_press | 25.0 | 1464.0 | nan | nan |
| rss_treasury_press | None | nan | 404 | no parsable timestamps or blocked |
| rss_ecb_press | 15.0 | 355.0 | nan | nan |

GDELT file-stamp evidence [OBS]:
| stamp | rows | last_modified | lm_minus_nominal_min | crypto_mention_rows |
|---|---|---|---|---|
| 20160101120000 | 1470 | 2016-01-01 11:50:37 | -9.400 | 1 |
| 20180601120000 | 2872 | 2018-06-01 11:55:27 | -4.500 | 20 |
| 20200601120000 | 2032 | 2020-06-01 11:54:34 | -5.400 | 0 |
| 20220601120000 | 1280 | 2022-06-01 11:51:49 | -8.200 | 6 |
| 20240601120000 | 942 | 2024-06-01 11:49:57 | -10.100 | 4 |
| 20260601120000 | 1218 | 2026-06-01 11:50:02 | -10.000 | 10 |
| 20260928120000 | 1384 | 2026-09-28 11:50:01 | -10.000 | 16 |

Caveat: GDELT's V2.1DATE is the *crawl batch* time (one distinct value per file), **not** the article's publication time [OBS]; a PIT news factor built from it measures "when GDELT saw it".

Prediction markets: Kalshi `KXFED` settled markets expose created/open/close/settlement/updated timestamps and daily candlesticks (316 bars for `KXFED-26SEP-T5.25`, 2025-08-06 → 2026-09-16) [OBS]; Polymarket `prices-history` returned 307 daily points for a closed 2024 market [OBS]. Price-threshold BTC contracts are price derivatives by construction; macro/election contracts are independent information but only ≈1 year of FOMC-type history was reachable → untested.

### Wikimedia REST pageviews  
`wikimedia_pageviews` · search/trend · executed **Y** · PIT **LOOKAHEAD_RISK** · info **TESTED_NO_INCREMENT**

* **access:** REST https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/... ; Bitcoin & Ethereum 2020-09 -> 2026-09 pulled [OBS collect_log]
* **cost:** free-nokey
* **history:** ~1 day; coverage — Since 2015-07 [DOC]
* **latency:** HTTP median n/a; freshness n/a; statuses 429
* **timestamp semantics:** Daily bucket; no publication stamp
* **revision semantics:** Bot-filtering ('user' agent class) may be re-classified retroactively [INF]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** Analytics datasets under CC0 [DOC dumps.wikimedia.org readme]
* **rate limits:** HTTP 429 with retry-after 9-15 s from the shared egress in 4/5 probes; bulk pull succeeded after backoff [OBS]
* **operational stability:** probe statuses 429
* **note:** Attention proxy; no increment over baseline.

### Google Trends (unofficial endpoints)  
`google_trends` · search/trend · executed **N** · PIT **LOOKAHEAD_RISK** · info **UNTESTED_BLOCKED**

* **access:** dailytrends endpoint returned 404 HTML [OBS]; no official free API
* **cost:** restricted
* **history:** n/a; coverage — 
* **latency:** HTTP median n/a; freshness n/a; statuses 404
* **timestamp semantics:** Sampling-based, re-indexed [INF]
* **revision semantics:** Values normalised per query and resampled on each call [INF]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** Google ToS prohibit automated scraping [INF]
* **rate limits:** n/a
* **operational stability:** probe statuses 404
* **note:** No stable free PIT route.

### Crypto Fear & Greed Index (alternative.me)  
`alternative_me_fng` · search/trend · executed **Y** · PIT **LOOKAHEAD_RISK** · info **TESTED_PRICE_DERIVATIVE**

* **access:** REST https://api.alternative.me/fng/?limit=0 [OBS]
* **cost:** free-nokey
* **history:** daily; coverage — Since 2018-02-01 (3159 rows) [OBS]
* **latency:** HTTP median 646 ms; freshness 18.6 h; statuses 200
* **timestamp semantics:** Value stamped 00:00 UTC of its date; 'time_until_update' field in latest row [OBS]
* **revision semantics:** No vintages; composite methodology (volatility, momentum/volume, social, dominance, trends) is re-weighted by provider over time [UNK]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** Attribution/limits stated at alternative.me/crypto/api [DOC: 60 req/min over 10-min window]; reuse terms [UNK]
* **rate limits:** 60 req/min per 10 min [DOC]
* **operational stability:** probe statuses 200
* **note:** Composite includes price volatility/momentum -> high price reactivity.

### Hacker News Algolia search API  
`hackernews_algolia` · public social · executed **Y** · PIT **PIT_ADAPTABLE** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** REST https://hn.algolia.com/api/v1/search_by_date [OBS]
* **cost:** free-nokey
* **history:** deep via pagination [UNK]; coverage — 100 items spanned 81 days for query 'bitcoin' [OBS]
* **latency:** HTTP median 676 ms; freshness 7.8 h; statuses 200
* **timestamp semantics:** created_at per item (second resolution) [OBS]
* **revision semantics:** Items can be edited/deleted; scores change [INF]
* **PIT readiness:** PIT_ADAPTABLE
* **licence:** Not fetched [UNK]
* **rate limits:** Not measured
* **operational stability:** probe statuses 200
* **note:** Low volume for crypto trading.

### Reddit RSS/Atom (r/Bitcoin)  
`reddit_rss` · public social · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** https://www.reddit.com/r/Bitcoin/new/.rss [OBS]; .json variant returned 403 [OBS]
* **cost:** free-nokey
* **history:** ~1 day; coverage — Latest 25 posts only
* **latency:** HTTP median 490 ms; freshness -0.0 h; statuses 200,403
* **timestamp semantics:** Entry <updated> stamps; 25 items = 22.6 h [OBS]
* **revision semantics:** Edits/removals invisible
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Reddit Data API Terms: commercial use and research above rate limits need a separate agreement [DOC redditinc.com]
* **rate limits:** x-ratelimit-remaining 0.0 after a single request in this environment [OBS]
* **operational stability:** probe statuses 200,403
* **note:** Forward capture only; ToS-restricted.

### Arctic Shift Reddit archive API  
`arctic_shift_reddit` · public social · executed **Y** · PIT **LOOKAHEAD_RISK** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** REST https://arctic-shift.photon-reddit.com/api/posts/search [OBS]
* **cost:** free-nokey
* **history:** years [UNK]; coverage — Historical Reddit
* **latency:** HTTP median 1470 ms; freshness 0.4 h; statuses 200
* **timestamp semantics:** created_utc; archive ingestion time not exposed [OBS]
* **revision semantics:** Deleted/edited content state depends on ingestion time [INF]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** Third-party archive of Reddit content; Reddit terms apply [INF]
* **rate limits:** HTTP 429 'too many requests' on repeat calls [OBS]
* **operational stability:** probe statuses 200
* **note:** History without ingestion stamps.

### StockTwits public stream  
`stocktwits` · public social · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** REST https://api.stocktwits.com/api/2/streams/symbol/BTC.X.json [OBS]
* **cost:** free-nokey
* **history:** ~30 min window; coverage — Latest 30 messages = 0.5 h [OBS]
* **latency:** HTTP median 477 ms; freshness -0.0 h; statuses 200
* **timestamp semantics:** created_at per message
* **revision semantics:** Deletions invisible
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Terms fetched prohibit circumventing rate limits/access controls [DOC stocktwits.com/terms]; data redistribution [UNK]
* **rate limits:** Not measured
* **operational stability:** probe statuses 200
* **note:** Forward capture only.

### Mastodon public tag timeline  
`mastodon` · public social · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** REST https://mastodon.social/api/v1/timelines/tag/bitcoin [OBS]
* **cost:** free-nokey
* **history:** ~15 h; coverage — Latest 40 toots = 15 h [OBS]
* **latency:** HTTP median 557 ms; freshness 0.3 h; statuses 200
* **timestamp semantics:** created_at ms
* **revision semantics:** n/a
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Not fetched [UNK]
* **rate limits:** 300/5 min via x-ratelimit headers [OBS]
* **operational stability:** probe statuses 200
* **note:** Tiny, unrepresentative crypto audience.

### Bluesky public search API  
`bluesky` · public social · executed **N** · PIT **UNKNOWN** · info **UNTESTED_BLOCKED**

* **access:** HTTP 403 [OBS]
* **cost:** restricted
* **history:** n/a; coverage — 
* **latency:** HTTP median n/a; freshness n/a; statuses 403
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** UNKNOWN
* **licence:** n/a
* **rate limits:** n/a
* **operational stability:** probe statuses 403
* **note:** Blocked from sandbox.

### 4chan /biz/ catalog  
`4chan_biz` · public social · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** https://a.4cdn.org/biz/catalog.json (201 live threads) [OBS]
* **cost:** free-nokey
* **history:** live only; coverage — Live catalog
* **latency:** HTTP median 582 ms; freshness n/a; statuses 200
* **timestamp semantics:** Thread creation time
* **revision semantics:** Threads deleted/pruned
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Not fetched [UNK]
* **rate limits:** Not measured
* **operational stability:** probe statuses 200
* **note:** Toxic/noisy; ToS/legal concerns [INF].

### LunarCrush API  
`lunarcrush` · public social · executed **N** · PIT **UNKNOWN** · info **UNTESTED_BLOCKED**

* **access:** HTTP 401 [OBS]
* **cost:** paid/key
* **history:** n/a; coverage — 
* **latency:** HTTP median n/a; freshness n/a; statuses 401
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** UNKNOWN
* **licence:** n/a
* **rate limits:** n/a
* **operational stability:** probe statuses 401
* **note:** Keyed.

### GDELT 2.0 raw 15-minute files (GKG/Events/Mentions)  
`gdelt_v2_files` · news · executed **Y** · PIT **PIT_NATIVE** · info **UNTESTED_LOW_POWER**

* **access:** Static zips http://data.gdeltproject.org/gdeltv2/YYYYMMDDHHMMSS.{gkg,export,mentions}.CSV.zip ; masterfile + lastupdate.txt [OBS]
* **cost:** free-nokey
* **history:** batch-stamp + ~0 min; coverage — Global news 2015-02 -> now (GKG v2) [DOC]; file sizes 3.7-11.9 MB [OBS]
* **latency:** HTTP median 545 ms; freshness n/a; statuses 200,200
* **timestamp semantics:** Filename = 15-min batch stamp = V2.1DATE in every row; Last-Modified is 4.5-10.1 min BEFORE the nominal stamp in 7/7 samples spanning 2016-2026 [OBS pit_probes.json]. NOTE: GKG date is crawl/batch time, not article publication time [INF/OBS: one distinct V2.1DATE per file].
* **revision semantics:** Files are static per batch [INF]; late arrivals are added to later batches [INF]
* **PIT readiness:** PIT_NATIVE
* **licence:** 'free... for academic, commercial, or governmental use of any kind without fee'; redistribution allowed with citation [DOC gdeltproject.org/about]
* **rate limits:** Unlimited static; DOC API separate
* **operational stability:** probe statuses 200,200
* **note:** Strongest PIT news source; a multi-year sentiment/volume series would need ~0.17 TB/year of downloads (96 files/day x ~5 MB) -> not built.

### GDELT DOC 2.0 API (timelines)  
`gdelt_doc_api` · news · executed **N** · PIT **LOOKAHEAD_RISK** · info **UNTESTED_BLOCKED**

* **access:** HTTP 429 'one request every 5 seconds' from shared egress even at 1 call/20 s [OBS]
* **cost:** free-nokey
* **history:** 3 months; coverage — 3 months
* **latency:** HTTP median n/a; freshness n/a; statuses 429
* **timestamp semantics:** Timeline buckets recomputed at query time; rolling 3-month window [DOC-indirect]
* **revision semantics:** Recomputed each call [INF]
* **PIT readiness:** LOOKAHEAD_RISK
* **licence:** as GDELT
* **rate limits:** 1 req / 5 s [DOC in 429 body]
* **operational stability:** probe statuses 429
* **note:** Not executed; LOOKAHEAD_RISK by construction.

### Cointelegraph RSS  
`rss_cointelegraph` · RSS · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** https://cointelegraph.com/rss [OBS]
* **cost:** free-nokey
* **history:** 32 h; coverage — 30 items
* **latency:** HTTP median 538 ms; freshness 1.4 h; statuses 200
* **timestamp semantics:** RSS pubDate (publisher-asserted, editable) [OBS]
* **revision semantics:** Items can be edited after publication; feed keeps last 30 items = 32 h [OBS]
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Site terms fetched; personal-use/redistribution limits [DOC cointelegraph.com/terms-and-privacy, details not parsed]
* **rate limits:** None observed
* **operational stability:** probe statuses 200
* **note:** History does not exist -> forward capture only.

### CoinDesk RSS  
`rss_coindesk` · RSS · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** https://www.coindesk.com/arc/outboundfeeds/rss/ [OBS]
* **cost:** free-nokey
* **history:** 33 h; coverage — 25 items
* **latency:** HTTP median 576 ms; freshness 0.2 h; statuses 200
* **timestamp semantics:** pubDate
* **revision semantics:** 25 items = 33 h [OBS]
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Not fetched [UNK]
* **rate limits:** None observed
* **operational stability:** probe statuses 200
* **note:** Forward capture only.

### Decrypt RSS  
`rss_decrypt` · RSS · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** https://decrypt.co/feed [OBS]
* **cost:** free-nokey
* **history:** 274 d; coverage — 56 items
* **latency:** HTTP median 486 ms; freshness 0.3 h; statuses 200
* **timestamp semantics:** pubDate
* **revision semantics:** 56 items = 274 days [OBS] (low-frequency feed)
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Not fetched [UNK]
* **rate limits:** None observed
* **operational stability:** probe statuses 200
* **note:** Forward capture only.

### BBC News business RSS  
`rss_bbc_business` · RSS · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** https://feeds.bbci.co.uk/news/business/rss.xml [OBS]
* **cost:** free-nokey
* **history:** 91 d; coverage — 52 items
* **latency:** HTTP median 414 ms; freshness 1.3 h; statuses 200
* **timestamp semantics:** pubDate
* **revision semantics:** 52 items = 91 days [OBS]
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Attribution 'BBC News' required when content appears [DOC bbc.co.uk/news/10628494]
* **rate limits:** None observed
* **operational stability:** probe statuses 200
* **note:** Forward capture only.

### Federal Reserve press RSS  
`rss_federal_reserve` · RSS · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** https://www.federalreserve.gov/feeds/press_all.xml [OBS]
* **cost:** free-nokey
* **history:** ~20 items; coverage — 20 items
* **latency:** HTTP median 519 ms; freshness n/a; statuses 200
* **timestamp semantics:** Feed dates not parsed by our regex [OBS]
* **revision semantics:** n/a
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** US government content; reuse terms not fetched [UNK]
* **rate limits:** None observed
* **operational stability:** probe statuses 200
* **note:** Official releases = event clock; forward capture only.

### SEC press-release RSS  
`rss_sec_press` · RSS · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** https://www.sec.gov/news/pressreleases.rss [OBS]
* **cost:** free-nokey
* **history:** 61 d; coverage — 25 items
* **latency:** HTTP median 524 ms; freshness 4.7 h; statuses 200
* **timestamp semantics:** pubDate
* **revision semantics:** 25 items = 61 days [OBS]
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Not fetched [UNK]
* **rate limits:** SEC requires declared User-Agent; other sec.gov endpoints returned 403 without it [OBS]
* **operational stability:** probe statuses 200
* **note:** Forward capture only.

### ECB press RSS  
`rss_ecb_press` · RSS · executed **Y** · PIT **SNAPSHOT_ONLY** · info **UNTESTED_NEEDS_FORWARD_CAPTURE**

* **access:** https://www.ecb.europa.eu/rss/press.html [OBS]
* **cost:** free-nokey
* **history:** 15 d; coverage — 15 items
* **latency:** HTTP median 808 ms; freshness 10.6 h; statuses 200
* **timestamp semantics:** pubDate
* **revision semantics:** 15 items = 15 days [OBS]
* **PIT readiness:** SNAPSHOT_ONLY
* **licence:** Not fetched [UNK]
* **rate limits:** None observed
* **operational stability:** probe statuses 200
* **note:** Forward capture only.

### US Treasury press RSS  
`rss_treasury_press` · RSS · executed **N** · PIT **UNKNOWN** · info **UNTESTED_BLOCKED**

* **access:** guessed URL returned 404 [OBS]
* **cost:** free-nokey
* **history:** n/a; coverage — 
* **latency:** HTTP median n/a; freshness n/a; statuses 404
* **timestamp semantics:** n/a
* **revision semantics:** n/a
* **PIT readiness:** UNKNOWN
* **licence:** n/a
* **rate limits:** n/a
* **operational stability:** probe statuses 404
* **note:** Feed URL not found.

### Polymarket Gamma + CLOB APIs  
`polymarket` · prediction markets · executed **Y** · PIT **PIT_NATIVE** · info **UNTESTED_LOW_POWER**

* **access:** REST https://gamma-api.polymarket.com (events/markets/public-search), https://clob.polymarket.com/prices-history [OBS]
* **cost:** free-nokey
* **history:** real-time; coverage — Since 2020 [UNK]; sample market 2024-01-05->2024-11-06 [OBS]
* **latency:** HTTP median 452 ms; freshness 10751.5 h; statuses 200,200
* **timestamp semantics:** Price-history rows {t (unix s), p}; fidelity selectable (daily fidelity gave 307 points for a closed 2024 market) [OBS]
* **revision semantics:** Executed prices are immutable prints [INF]; market metadata (titles, resolution) can be edited [INF]
* **PIT readiness:** PIT_NATIVE
* **licence:** ToS/docs pages fetched but no licence keywords found [UNK]
* **rate limits:** Not measured
* **operational stability:** probe statuses 200,200
* **note:** Independent event probabilities (Fed, elections); BTC-threshold contracts are price derivatives. Enough history exists but a labelled macro-event study was out of scope.

### Kalshi public market-data API  
`kalshi` · prediction markets · executed **Y** · PIT **PIT_NATIVE** · info **UNTESTED_LOW_POWER**

* **access:** REST https://api.elections.kalshi.com/trade-api/v2/{events,markets,series} ; candlesticks endpoint gave 316 daily bars for a settled KXFED market [OBS]
* **cost:** free-nokey
* **history:** real-time; coverage — KXFED markets since 2025-08 [OBS]
* **latency:** HTTP median 444 ms; freshness 0.0 h; statuses 200,200
* **timestamp semantics:** created/open/close/settlement/updated timestamps on every market [OBS pit_probes.json]
* **revision semantics:** Settled markets keep candle history; market fields updated at settlement [OBS]
* **PIT readiness:** PIT_NATIVE
* **licence:** Docs fetched (rate-limit tiers mentioned) but no data licence text found [DOC/UNK]
* **rate limits:** HTTP 429 seen on markets after rapid calls (one of two runs) [OBS]
* **operational stability:** probe statuses 200,200
* **note:** Macro (Fed decision) probabilities are genuinely non-price information; only ~1 year of FOMC events accessible -> not testable here.
