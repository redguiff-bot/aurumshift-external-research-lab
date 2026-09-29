# 01 — Source landscape

> External research only — no private AurumShift code, no integration claims. Evidence tags: **[OBS]** observed in this study, **[DOC]** stated on a provider page/API response fetched in this study, **[INF]** inference, **[UNK]** unknown/not verified. Study date 2026-09-29 (sandbox clock). Reproduce with `bench/alternative_data_v1/`.


69 sources (47 executed) across the 16 requested categories. "Executed" = at least one real data pull parsed and logged (`bench/alternative_data_v1/results/probe_results.json`, `data/collect_log.json`, `results/pit_probes.json`); reachable-but-keyed endpoints (Etherscan V1, AISHub, GIE AGSI) are **not** counted as executed even though HTTP 200 came back (their bodies are auth errors). Full 12-field cards live in the category reports 02–05; this page is the index. Latency = median of ≤3 sequential calls from the sandbox egress; freshness = age of newest record at probe time.

## By category
| category | sources | executed | free |
|---|---|---|---|
| CFTC positioning | 1 | 1 | 1 |
| ETF flows | 3 | 0 | 0 |
| RSS | 8 | 7 | 8 |
| developer/GitHub | 5 | 4 | 5 |
| energy inventories | 3 | 1 | 3 |
| exchange flows | 7 | 5 | 7 |
| mempool | 1 | 1 | 1 |
| news | 2 | 1 | 2 |
| on-chain | 10 | 6 | 9 |
| prediction markets | 2 | 2 | 2 |
| public government | 7 | 4 | 7 |
| public social | 8 | 6 | 6 |
| search/trend | 3 | 2 | 2 |
| shipping | 3 | 1 | 3 |
| weather | 6 | 6 | 6 |

## All sources
| source | category | exec | cost | PIT | info | latency | freshness | http |
|---|---|---|---|---|---|---|---|---|
| Coin Metrics Community API v4 | on-chain | Y | free-nokey | LOOKAHEAD_RISK | TESTED_NO_INCREMENT | 848 ms | 42.6 h | 200 |
| Blockchain.com charts API | on-chain | Y | free-nokey | LOOKAHEAD_RISK | TESTED_NO_INCREMENT | 513 ms | 42.6 h | 200 |
| mempool.space REST API | mempool | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 498 ms | 0.1 h | 200,200,200,200,200 |
| Blockstream Esplora API | on-chain | Y | free-nokey | PIT_ADAPTABLE | UNTESTED_NEEDS_FORWARD_CAPTURE | 730 ms | n/a | 200 |
| Blockchair API (free tier) | on-chain | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 926 ms | -0.0 h | 200 |
| Public Ethereum JSON-RPC (publicnode) | on-chain | Y | free-nokey | PIT_ADAPTABLE | UNTESTED_NEEDS_FORWARD_CAPTURE | 498 ms | -0.0 h | 200 |
| Etherscan API (V1 no-key) | on-chain | N | free-key | UNKNOWN | UNTESTED_BLOCKED | 579 ms | n/a | 200 |
| DefiLlama free API (stablecoins, TVL, DEX volume, fees) | on-chain | Y | free-nokey | LOOKAHEAD_RISK | TESTED_NO_INCREMENT | 640 ms | 18.6 h | 200,200,200,402 |
| Glassnode API | on-chain | N | paid/key | UNKNOWN | UNTESTED_BLOCKED | n/a | n/a | 401 |
| beaconcha.in API | on-chain | N | free-key | UNKNOWN | UNTESTED_BLOCKED | n/a | n/a | 401 |
| CoinGecko public API | on-chain | N | free-key | UNKNOWN | PRICE_DATA_NOT_ALT | n/a | n/a | 401,401 |
| Binance Vision futures 'metrics' daily files (OI, long/short ratios, taker ratio; 5-min rows) | exchange flows | Y | free-nokey | LOOKAHEAD_RISK | TESTED_NO_INCREMENT | 625 ms | n/a | 200 |
| Binance futures REST (fapi) | exchange flows | N | free-nokey | PIT_ADAPTABLE | UNTESTED_BLOCKED | n/a | n/a | 451 |
| OKX public REST (rubik stats, funding history) | exchange flows | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 646 ms | 2.6 h | 200,200,200 |
| Bitfinex public stats (margin long/short position size) | exchange flows | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 601 ms | -0.0 h | 200 |
| Deribit public API (DVOL index, options book summary) | exchange flows | Y | free-nokey | PIT_NATIVE | TESTED_CANDIDATE | 645 ms | -0.0 h | 200,200 |
| Hyperliquid public info API | exchange flows | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 715 ms | n/a | 200 |
| Bybit v5 public REST | exchange flows | N | free-nokey | PIT_ADAPTABLE | UNTESTED_BLOCKED | n/a | n/a | 403 |
| GH Archive hourly event files | developer/GitHub | Y | free-nokey | PIT_NATIVE | UNTESTED_LOW_POWER | 780 ms | n/a | 200 |
| GitHub REST API (commits/releases of crypto repos) | developer/GitHub | N | free-key | LOOKAHEAD_RISK | UNTESTED_BLOCKED | n/a | n/a | 403 |
| npm download counts API | developer/GitHub | Y | free-nokey | LOOKAHEAD_RISK | TESTED_NO_INCREMENT | 594 ms | 40194.6 h | 200 |
| PyPI download stats | developer/GitHub | Y | free-nokey | LOOKAHEAD_RISK | UNTESTED_LOW_POWER | 555 ms | 42.6 h | 200 |
| crates.io download stats | developer/GitHub | Y | free-nokey | LOOKAHEAD_RISK | UNTESTED_LOW_POWER | 476 ms | 18.6 h | 200 |
| Wikimedia REST pageviews | search/trend | Y | free-nokey | LOOKAHEAD_RISK | TESTED_NO_INCREMENT | n/a | n/a | 429 |
| Google Trends (unofficial endpoints) | search/trend | N | restricted | LOOKAHEAD_RISK | UNTESTED_BLOCKED | n/a | n/a | 404 |
| Crypto Fear & Greed Index (alternative.me) | search/trend | Y | free-nokey | LOOKAHEAD_RISK | TESTED_PRICE_DERIVATIVE | 646 ms | 18.6 h | 200 |
| Hacker News Algolia search API | public social | Y | free-nokey | PIT_ADAPTABLE | UNTESTED_NEEDS_FORWARD_CAPTURE | 676 ms | 7.8 h | 200 |
| Reddit RSS/Atom (r/Bitcoin) | public social | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 490 ms | -0.0 h | 200,403 |
| Arctic Shift Reddit archive API | public social | Y | free-nokey | LOOKAHEAD_RISK | UNTESTED_NEEDS_FORWARD_CAPTURE | 1470 ms | 0.4 h | 200 |
| StockTwits public stream | public social | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 477 ms | -0.0 h | 200 |
| Mastodon public tag timeline | public social | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 557 ms | 0.3 h | 200 |
| Bluesky public search API | public social | N | restricted | UNKNOWN | UNTESTED_BLOCKED | n/a | n/a | 403 |
| 4chan /biz/ catalog | public social | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 582 ms | n/a | 200 |
| LunarCrush API | public social | N | paid/key | UNKNOWN | UNTESTED_BLOCKED | n/a | n/a | 401 |
| GDELT 2.0 raw 15-minute files (GKG/Events/Mentions) | news | Y | free-nokey | PIT_NATIVE | UNTESTED_LOW_POWER | 545 ms | n/a | 200,200 |
| GDELT DOC 2.0 API (timelines) | news | N | free-nokey | LOOKAHEAD_RISK | UNTESTED_BLOCKED | n/a | n/a | 429 |
| Cointelegraph RSS | RSS | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 538 ms | 1.4 h | 200 |
| CoinDesk RSS | RSS | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 576 ms | 0.2 h | 200 |
| Decrypt RSS | RSS | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 486 ms | 0.3 h | 200 |
| BBC News business RSS | RSS | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 414 ms | 1.3 h | 200 |
| Federal Reserve press RSS | RSS | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 519 ms | n/a | 200 |
| SEC press-release RSS | RSS | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 524 ms | 4.7 h | 200 |
| ECB press RSS | RSS | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 808 ms | 10.6 h | 200 |
| US Treasury press RSS | RSS | N | free-nokey | UNKNOWN | UNTESTED_BLOCKED | n/a | n/a | 404 |
| Polymarket Gamma + CLOB APIs | prediction markets | Y | free-nokey | PIT_NATIVE | UNTESTED_LOW_POWER | 452 ms | 10751.5 h | 200,200 |
| Kalshi public market-data API | prediction markets | Y | free-nokey | PIT_NATIVE | UNTESTED_LOW_POWER | 444 ms | 0.0 h | 200,200 |
| CFTC Commitments of Traders (Socrata public reporting) | CFTC positioning | Y | free-nokey | PIT_ADAPTABLE | TESTED_NO_INCREMENT | 854 ms | 186.6 h | 200,200,200,404 |
| iShares fund pages / holdings CSV (IBIT, IVV) | ETF flows | N | restricted | UNKNOWN | UNTESTED_BLOCKED | 997 ms | n/a | 200,200 |
| Farside Investors ETF flow tables | ETF flows | N | restricted | UNKNOWN | UNTESTED_BLOCKED | n/a | n/a | 403 |
| SEC EDGAR (submissions, XBRL frames, full-text search) | public government | Y | free-nokey | PIT_NATIVE | UNTESTED_LOW_POWER | 516 ms | 1315.0 h | 200,200,403,200 |
| Yahoo Finance chart endpoints (unofficial) | ETF flows | N | restricted | LOOKAHEAD_RISK | PRICE_DATA_NOT_ALT | n/a | n/a | 429 |
| IMF PortWatch daily chokepoint transits (ArcGIS FeatureServer) | shipping | Y | free-nokey | LOOKAHEAD_RISK | TESTED_NO_INCREMENT | 686 ms | 43914.6 h | 200,200 |
| AISHub | shipping | N | free-key | UNKNOWN | UNTESTED_BLOCKED | 1259 ms | n/a | 200 |
| Stooq Baltic Dry Index CSV | shipping | N | free-nokey | UNKNOWN | UNTESTED_BLOCKED | n/a | n/a | 0 |
| EIA bulk files (PET.zip, NG.zip) + WPSR/ NG storage release files | energy inventories | Y | free-nokey | LOOKAHEAD_RISK | TESTED_CANDIDATE | 5124 ms | n/a | 200,200,200,200 |
| EIA API v2 | energy inventories | N | free-key | PIT_ADAPTABLE | UNTESTED_BLOCKED | n/a | n/a | 403 |
| GIE AGSI+ EU gas storage | energy inventories | N | free-key | UNKNOWN | UNTESTED_BLOCKED | 825 ms | n/a | 200 |
| Open-Meteo (forecast, archive, historical-forecast) | weather | Y | free-nokey | PIT_ADAPTABLE | UNTESTED_NEEDS_FORWARD_CAPTURE | 863 ms | 24019.6 h | 429,429,200 |
| NOAA/NWS api.weather.gov | weather | Y | free-nokey | SNAPSHOT_ONLY | UNTESTED_NEEDS_FORWARD_CAPTURE | 484 ms | -148.4 h | 200 |
| NOAA CPC population-weighted degree days | weather | Y | free-nokey | LOOKAHEAD_RISK | TESTED_NO_INCREMENT | 576 ms | n/a | 200 |
| NOAA NCEI Access Data Service (GHCN-daily) | weather | Y | free-nokey | LOOKAHEAD_RISK | UNTESTED_LOW_POWER | 568 ms | 52578.6 h | 200 |
| NASA POWER daily API | weather | Y | free-nokey | LOOKAHEAD_RISK | UNTESTED_LOW_POWER | 517 ms | n/a | 200 |
| NOAA GFS on AWS open data (S3) | weather | Y | free-nokey | PIT_NATIVE | UNTESTED_LOW_POWER | 527 ms | n/a | 200 |
| US Treasury FiscalData (Daily Treasury Statement: TGA) | public government | Y | free-nokey | LOOKAHEAD_RISK | TESTED_NO_INCREMENT | 1310 ms | 4026.6 h | 200 |
| NY Fed Markets API (reverse-repo operations) | public government | Y | free-nokey | LOOKAHEAD_RISK | TESTED_NO_INCREMENT | 700 ms | 42.6 h | 200 |
| FRED / ALFRED CSV | public government | N | free-key | PIT_NATIVE | UNTESTED_BLOCKED | n/a | n/a | 0 |
| Federal Reserve H.4.1 data download | public government | N | free-nokey | UNKNOWN | UNTESTED_BLOCKED | 516 ms | n/a | 200 |
| ECB euro FX reference rates | public government | Y | free-nokey | PIT_ADAPTABLE | PRICE_DATA_NOT_ALT | 918 ms | n/a | 200 |
| IMF DataMapper API | public government | N | free-nokey | UNKNOWN | UNTESTED_BLOCKED | n/a | n/a | 403 |

### Access blockers observed from the sandbox (each is *missing evidence*, not negative evidence)
* Geo/WAF: Binance fapi (451), Bybit (403), Bluesky (403), Reddit `.json` (403), IMF DataMapper (403), sec.gov HTML/atom (403 without accepted UA), Farside (Cloudflare challenge).
* Quotas on the shared egress IP: Open-Meteo forecast/archive (daily limit), GDELT DOC (429 at ≥1 call/20 s), Wikimedia (429 in probes; bulk pull succeeded after retry-after back-off), Wayback Machine (429 / tunnel closed), Kalshi (429 once), Yahoo (429).
* Keys: EIA API v2, Etherscan V2, GIE AGSI, beaconcha.in, Glassnode, LunarCrush, CoinGecko (all "free key" or paid; none provisioned).
* Session scope: GitHub REST for third-party repositories (deliberately not bypassed; GH Archive used instead).
* Reachability: FRED/ALFRED, Stooq (timeouts/resets).
