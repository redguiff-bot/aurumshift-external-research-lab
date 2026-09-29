# 01 — Source landscape

Evidence labels (claude.md): **OBS** = observed in a probe/test in this run; **DOC** = documented claim, not re-verified; UNKNOWN. Per-source structured records: `bench/alternative_data_v1/results/source_records.json` / `.csv`.

39 sources catalogued across 16 categories; 29 executed (≥1 probe returned HTTP 200 or data pulled). Each probe = 3 calls ≥2.5 s apart (stability sample is small: it is a snapshot, not an SLA measurement).

## on-chain

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **Blockchain.com Charts API** (`bc_charts`) | keyless REST; free | 2009-> (daily, OBS: 1300d pulled) | aggregates lag; cache-control max-age 4h (OBS) | x = period start (unix s); no publication time per row | values regenerated server-side; no vintage/rev flag (Last-Modified = fetch time, OBS) | ToS not verified (UNKNOWN); attribution asked (DOC) | BTC only | undocumented; 429 not seen at 18 calls/13 s (OBS) | 6/6 calls HTTP 200; median 590 ms |
| **Blockstream Esplora** (`blockstream`) | keyless REST; free | full chain via block/tx paging (no aggregates) | live | block/tx times native (blocktime) | immutable after ~6 confs (reorg risk before) | Blockstream public API terms (UNKNOWN exact) | BTC/Liquid | unpublished | 6/6 calls HTTP 200; median 641 ms |
| **Blockchair stats** (`blockchair`) | keyless (1440 req/day free DOC); key for more; free tier | current stats; history via paid dumps (DOC) | live | snapshot time in `context` | n/a | ToS restricts commercial (DOC) | many chains | 1440/day free (DOC) | 3/3 calls HTTP 200; median 839 ms |
| **DefiLlama stablecoins & TVL** (`defillama_stable`) | keyless REST; free | 2017-> daily (OBS) | ~hourly refresh (Last-Modified OBS) | date = day (unix); no publication time | history re-computed when adapters change (DOC/inference); no vintages | CC-BY-like/attribution (DOC, not verified) | multi-chain | generous; undisclosed | 6/6 calls HTTP 200; median 476 ms |

## mempool

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **mempool.space REST (blocks/fees/mining)** (`mempool_space`) | keyless REST/WS; free | mining stats to 3y+ (OBS); mempool/fee-histogram LIVE ONLY (no history endpoint) | sub-second live (DOC); block-level stats after block | block timestamp (miner-set, +-2h tolerance, DOC BIP113) for mining series; live endpoints no history | reorgs can rewrite recent blocks; aggregate series not versioned | AGPL software; public API fair-use (DOC) | BTC only | rate limited per IP, unpublished thresholds (DOC) | 9/9 calls HTTP 200; median 473 ms |

## news

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **GDELT DOC 2.0 API** (`gdelt_doc`) | keyless REST; free | rolling ~3 months (DOC); bulk GKG/Events since 2013/2015 | 15 min (DOC) | DATEADDED in bulk files = ingest time (PIT-friendly, DOC) | DOC API is recomputed on query; bulk files immutable | open, attribution (DOC) | global news | 1 request per 5 s (OBS: server message); 429 when violated | 1/3 calls HTTP 200; non-200: 429; median 24405 ms |

## RSS

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **Crypto-news RSS (Cointelegraph)** (`rss_crypto`) | keyless RSS; free | recent items only (~30) | minutes | pubDate per item (publisher-set) | edits silently possible | content copyright; headline use only (DOC) | crypto | n/a | 3/3 calls HTTP 200; median 454 ms |
| **Federal Reserve press RSS** (`rss_fed`) | keyless RSS; free | recent items | minutes | pubDate = release time | documents rarely amended | US gov public domain (DOC) | US monetary policy | n/a | 3/3 calls HTTP 200; median 397 ms |

## public social

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **Hacker News (Algolia)** (`hn_algolia`) | keyless REST; free | 2006-> (OBS daily counts pulled) | seconds | created_at_i = post time (native) | deletions/flagging change counts retroactively; nbHits inexact (OBS exhaustive=false) | HN data terms UNKNOWN | tech/crypto chatter | 10k/h per IP (DOC) | 3/3 calls HTTP 200; median 459 ms |
| **StockTwits symbol stream** (`stocktwits`) | keyless (limited); free | last ~30 msgs, paginate back limited | live | created_at per message | deletions | ToS forbids redistribution (DOC) | retail sentiment tags | 200/h unauth (DOC) | 3/3 calls HTTP 200; median 503 ms |
| **Reddit .json listing** (`reddit_json`) | keyless but blocked to datacentre/proxy IPs; free (commercial use needs licence, DOC) | recent 1000 per listing | live | created_utc | deletions | restrictive (DOC) | social | strict | 0/3 calls HTTP 200; non-200: 403 |
| **Bluesky AppView** (`bluesky`) | keyless public AppView; free | search recent; firehose live | live | createdAt (client-declared!) + indexedAt | deletions | open protocol | social | 3000/5min (DOC) | 2/3 calls HTTP 200; non-200: None; median 534 ms |

## search/trend

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **Google Trends (unofficial)** (`gtrends`) | no official API; unofficial scrapers; free | 2004->; re-normalised 0-100 per query window | days | window-relative index; values differ each query (sampling) | re-sampled EVERY request (documented behaviour) | ToS forbids scraping (DOC) | search interest | aggressive blocking | 0/3 calls HTTP 200; non-200: 404 |
| **Wikimedia pageviews REST** (`wikipedia_pv`) | keyless REST; UA required; free | 2015-07-> | daily data ~ next day (DOC) | day bucket (UTC) | finalised daily; bot filtering agent=user classification retro-improved (DOC) | CC0 data (DOC) | all wiki articles | 200 req/s doc; shared-IP 429 seen (OBS) | 2/3 calls HTTP 200; non-200: 429; median 394 ms |
| **alternative.me Fear & Greed** (`fear_greed`) | keyless REST; free | 2018-> daily (OBS) | daily | timestamp = day; no publication time | unknown; composite of vol/momentum/volume/social/dominance | attribution required (DOC) | crypto | 60/min (DOC) | 3/3 calls HTTP 200; median 337 ms |

## prediction markets

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **Polymarket Gamma+CLOB** (`polymarket`) | keyless read; free | per-market price history (clob prices-history, fidelity>=1min for active) | seconds | trade/price time native | market resolution changes state; price history immutable-ish (DOC) | ToS: read-only public data; geo restrictions on trading (DOC) | event contracts, mostly politics/crypto price bands | documented per-endpoint (DOC) | 6/6 calls HTTP 200; median 471 ms |
| **Kalshi public market data** (`kalshi`) | keyless read for market data; free | candlesticks per market | seconds | created/updated time fields, trades timestamped | settled markets fixed | ToS (UNKNOWN exact) | macro (CPI, Fed, gas) + others | documented (DOC) | 3/3 calls HTTP 200; median 390 ms |

## CFTC positioning

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **CFTC Public Reporting (Socrata) COT** (`cftc_cot`) | keyless Socrata (app token optional); free | legacy 1986->, TFF 2006->, disaggregated 2006-> (DOC), BTC CME from 2017-12 | Tuesday data released Friday 15:30 ET (DOC); holiday shifts | report_date = Tuesday as-of date; NO release timestamp per row (OBS) | resubmissions/corrections possible; dataset overwritten in place, no vintages (Last-Modified per dataset OBS) | US gov public domain (DOC) | US futures | Socrata throttling w/o token (DOC) | 3/3 calls HTTP 200; median 856 ms |

## ETF/public flow

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **Farside ETF flows** (`etf_farside`) | HTML behind Cloudflare challenge; free (site) | since Jan-2024 (DOC) | daily evening | date only | restated by site (DOC) | no explicit licence; scraping discouraged | US spot BTC ETFs | bot-blocked (OBS 403) | 0/3 calls HTTP 200; non-200: 403 |
| **SPDR GLD holdings (issuer)** (`etf_ssga_gld`) | keyless file (current snapshot); free | current file only; history by own capture (OBS: guessed file URL returned HTTP 404, so the file path is UNVERIFIED) | daily | as-of date inside file | overwritten daily | issuer terms (UNKNOWN) | GLD gold tonnes | n/a | 0/3 calls HTTP 200; non-200: 404 (guessed file URL, provider verdict UNKNOWN) |

## public government

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **SEC EDGAR (13F, Form 4, 8-K)** (`sec_edgar`) | keyless w/ declared UA; free | 1994-> ; acceptedDateTime per filing (PIT-native!) | seconds (public dissemination) | acceptanceDateTime per filing (OBS: field present in submissions JSON, e.g. 2026-08-13T19:53:24Z for a VanEck Bitcoin ETF filing) | amendments are new filings (10-K/A); originals kept | US gov public domain | US filers incl. ETF trusts | 10 req/s (DOC) | 3/3 calls HTTP 200; median 527 ms |
| **Treasury FiscalData DTS (TGA)** (`fiscal_dts`) | keyless REST; free | 2005-> daily | T+1 business day ~16:00 ET (DOC) | record_date only; no publication stamp | DTS values final; format changes 2022 (DOC) | US gov public domain | US Treasury cash | generous (DOC) | 3/3 calls HTTP 200; median 803 ms |
| **NY Fed markets (RRP/SOFR)** (`nyfed`) | keyless REST; free | 2013->  | same day ~13:15 ET (DOC) | operation date; revisionIndicator (see report 005) | revisionIndicator present | public domain-like | US money markets | n/a | 3/3 calls HTTP 200; median 662 ms |

## GitHub ecosystem

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **ClickHouse public playground github_events (GH Archive)** (`gh_playground`) | keyless SQL over HTTP (read-only user `play`); free | 2011-> nominal; gaps OBS (see 02/06) | ~<1h behind (OBS max(created_at) vs now) but daily counts ended 2026-07-02 for tracked repos (OBS) | created_at = GitHub event time (native) | repo renames/deletions retroactive; no vintage | GH Archive CC-BY-4.0-ish (DOC); playground is a demo, no SLA | all public GitHub events | shared demo cluster; quotas (DOC) | 3/3 calls HTTP 200; median 526 ms |
| **GitHub REST API** (`github_rest`) | token for useful limits; free | deep | live | commit author/committer dates (client-set!) | history rewritable (force-push) | ToS | repos | 60/h unauth (DOC) | 0/3 calls HTTP 200; non-200: 403 — blocked by THIS SESSION's repository-scope policy, not a provider verdict |

## developer activity

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **GH Archive hourly dumps** (`gharchive`) | keyless file download; free | 2011-> hourly files (~60-150 MB each) | files ~1h after hour (DOC) | created_at per event; file Last-Modified = publication (OBS header) | immutable files | CC-BY (DOC, unverified) | all public GitHub events | none documented | 3/3 calls HTTP 200; median 587 ms |
| **npm downloads / pypistats** (`npm_pypi`) | keyless REST; free | npm 2015->; pypistats 180 d only | daily ~1 day | day bucket | bot/mirror traffic restated (DOC) | public | package ecosystems | npm 429 at high rate (DOC) | 6/6 calls HTTP 200; median 544 ms |

## shipping

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **IMF PortWatch (ArcGIS FeatureServer)** (`portwatch`) | keyless ArcGIS query; free | 2019-> daily | published weekly, ~few days lag (DOC) | date = transit day; no publication time | nowcast model, historical values revised (DOC) | CC-BY 4.0 (DOC) | 28 chokepoints, ~1400 ports | ArcGIS maxRecordCount (2000 OBS pagination) | 3/3 calls HTTP 200; median 630 ms |
| **Baltic Dry Index / freight indices** (`baltic_shipping`) | paid (Baltic Exchange); paid (DOC) | n/a | n/a | n/a | n/a | proprietary | n/a | n/a | not executed (no keyless endpoint) — NOT EXECUTED: no free primary source found; Yahoo/Investing proxies are unofficial |
| **AIS open feeds (AISHub, GFW)** (`ais_open`) | AISHub requires data-sharing; GFW token; free w/ conditions | n/a | n/a | n/a | n/a | conditional | n/a | n/a | not executed (no keyless endpoint) — NOT EXECUTED: needs account/receiver sharing; PortWatch used as executed shipping proxy |

## energy inventories

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **EIA weekly petroleum/gas files (xls)** (`eia_files`) | keyless xls; API v2 needs free key; free | 1982-> weekly | WPSR Wed 10:30 ET / WNGSR Thu 10:30 ET (DOC) | week-ending date; no publication stamp | final values only; revisions in monthly data (DOC) | US gov public domain | US inventories | n/a | 3/3 calls HTTP 200; median 10257 ms |
| **EIA API v2** (`eia_api`) | free API key (registration); free | same | same | same | same | public domain | US energy | 5k rows/req; key | 0/3 calls HTTP 200; non-200: 403 |
| **GIE AGSI+ EU gas storage** (`gie_agsi`) | free API key (x-key) required; free | 2011-> | daily 18:00 CET, ~19:30 (DOC) | gasDayStart + updatedAt (DOC fields) | values are revised, `updatedAt` present (DOC) | attribution (DOC) | EU gas storage | key | HTTP 200 x3 but body is a key-required error (no data); not executed |

## weather

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **Open-Meteo archive / historical-forecast** (`openmeteo`) | keyless (non-commercial); free non-commercial; commercial paid | archive 1940-> ERA5; historical-forecast 2022-> (stored model runs, PIT-ish, DOC) | ERA5 lag ~5 d (DOC) | valid time; archive is reanalysis (hindsight-assimilated) = NOT PIT | ERA5T -> ERA5 revisions (DOC) | CC-BY 4.0 for data; API non-commercial (DOC) | global | 10k/day free (DOC); daily limit hit on hist-forecast (OBS) | 0/6 calls HTTP 200; non-200: 429 |
| **NWS api.weather.gov** (`nws`) | keyless w/ UA; free | obs ~7 days; forecasts current only | minutes | issuance time | forecast text replaced | US gov public domain | US | undisclosed | 3/3 calls HTTP 200; median 505 ms (landing page only; no forecast data probed) |
| **NOAA NDBC buoys realtime** (`noaa_ndbc`) | keyless; free | 45 days rolling realtime | hourly | obs time | QC revised in archive | public domain | ocean | n/a | 3/3 calls HTTP 200; median 682 ms |

## exchange flows where public

| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |
|---|---|---|---|---|---|---|---|---|---|
| **Deribit public API (index/funding/OI)** (`deribit_dvol`) | keyless REST/WS; free | funding history years (DOC); trades history deep | ms | usIn/usOut server stamps (see report 005) | trades immutable | ToS (UNKNOWN exact) | BTC/ETH derivs | 20 req/s credit system (DOC) | 6/6 calls HTTP 200; median 475 ms |
| **Binance Vision (data.binance.vision)** (`binance_vision`) | keyless files; free | OI/long-short metrics since 2021-12 (OBS) | next-day files (OBS Last-Modified) | 5-min bar times; file Last-Modified = publication | files immutable (checksums) | Binance Vision terms (DOC) | Binance derivatives | none documented | 3/3 calls HTTP 200; median 664 ms |
| **Exchange wallet/reserve flows (Glassnode/CryptoQuant/Arkham)** (`exchange_reserves`) | FREE TIER LIMITED / paid API; paid for history+resolution (DOC) | n/a | n/a | n/a | n/a | proprietary licence (DOC) | labels proprietary | n/a | not executed (no keyless endpoint) — NOT EXECUTED: no keyless free source with history found; on-chain address-label clusters are vendor-derived |

