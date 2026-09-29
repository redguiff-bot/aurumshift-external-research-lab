# 08 — Licence and cost

> External research only — no private AurumShift code, no integration claims. Evidence tags: **[OBS]** observed in this study, **[DOC]** stated on a provider page/API response fetched in this study, **[INF]** inference, **[UNK]** unknown/not verified. Study date 2026-09-29 (sandbox clock). Reproduce with `bench/alternative_data_v1/`.


**Cost.** 54 sources need no key, 8 need a free key (EIA API v2, Etherscan V2, GIE AGSI, beaconcha.in, CoinGecko …), 2 are paid/keyed (Glassnode, LunarCrush), 5 are practically unavailable to programmatic free use (Google Trends, Bluesky, Farside, iShares, Yahoo). Paid endpoint seen: DefiLlama bridges (HTTP 402). All 47 executed sources were pulled at zero cost.

**Licence method.** `py/licenses.py` fetched 50 provider pages (31 providers) and grepped for licence keywords (`results/license_evidence.json`). A licence is called documented only where a snippet was found; where a page was JS-only/403/404 it is **UNVERIFIED** — never inferred. This is not legal advice; AurumShift is research/paper-only, so non-commercial terms are workable *today* but would re-open at any commercial step.

Key documented terms: EIA "public domain" · Treasury FiscalData "free, without restriction … commercial or non-commercial" · NOAA/NWS public domain · Wikimedia analytics CC0 · GDELT free "commercial … of any kind without fee", cite GDELT · Open-Meteo free API "non-commercial", CC-BY 4.0, <10,000 calls/day · Coin Metrics community "Creative Commons license" (variant not stated) · Reddit Data API Terms require agreement for commercial/heavy research · CoinGecko API terms forbid re-distribution/sub-licensing · StockTwits terms forbid circumventing rate limits · Blockchain.com site terms: personal non-commercial use · Yahoo terms forbid unofficial access.

| source | cost | executed | reuse_verdict | licence_evidence |
|---|---|---|---|---|
| Coin Metrics Community API v4 | free-nokey | Y | CONDITIONAL (CC variant unverified; assume non-commercial) | 'Creative Commons license' [DOC docs.coinmetrics.io]; variant (NC?) not stated on fetched page [UNK] -> treat as non-commercial-only until confirmed |
| Blockchain.com charts API | free-nokey | Y | RESTRICTIVE/UNCLEAR (site terms: personal non-commercial) | Site terms fetched limit use of 'the Services' to personal non-commercial use [DOC blockchain.com/legal/terms]; whether this applies to the charts API is [UNK] |
| mempool.space REST API | free-nokey | Y | UNVERIFIED | Terms page fetched but no licence keywords found [UNK]; software is open source [INF] |
| Blockstream Esplora API | free-nokey | Y | UNVERIFIED | Not fetched [UNK] |
| Blockchair API (free tier) | free-nokey | Y | UNVERIFIED | Not verified [UNK] |
| Public Ethereum JSON-RPC (publicnode) | free-nokey | Y | UNVERIFIED | Not verified [UNK] |
| Etherscan API (V1 no-key) | free-key | N | UNVERIFIED | Not fetched [UNK] |
| DefiLlama free API (stablecoins, TVL, DEX volume, fees) | free-nokey | Y | UNVERIFIED (docs 403) | Docs page returned 403 to our fetch; licence [UNK] |
| Glassnode API | paid/key | N | UNVERIFIED | Not fetched [UNK] |
| beaconcha.in API | free-key | N | UNVERIFIED | Not fetched [UNK] |
| CoinGecko public API | free-key | N | RESTRICTIVE (no redistribution) | API terms fetched: no re-distribution/sub-licensing [DOC coingecko.com/en/api_terms] |
| Binance Vision futures 'metrics' daily files (OI, long/short ratios, taker ratio; 5-min rows) | free-nokey | Y | UNVERIFIED (Binance ToS) | Terms page fetched but no licence text found; treat as Binance ToS [UNK] |
| Binance futures REST (fapi) | free-nokey | N | UNVERIFIED | n/a |
| OKX public REST (rubik stats, funding history) | free-nokey | Y | UNVERIFIED | Docs page fetched; no licence text [UNK] |
| Bitfinex public stats (margin long/short position size) | free-nokey | Y | UNVERIFIED | Not fetched [UNK] |
| Deribit public API (DVOL index, options book summary) | free-nokey | Y | UNVERIFIED | Docs page fetched; no licence text found [UNK]; API usage policy exists [DOC index] |
| Hyperliquid public info API | free-nokey | Y | UNVERIFIED | Not fetched [UNK] |
| Bybit v5 public REST | free-nokey | N | UNVERIFIED | n/a |
| GH Archive hourly event files | free-nokey | Y | UNVERIFIED (GitHub event content) | Site states BigQuery free 1 TB/month processing [DOC]; underlying GitHub event licensing [UNK] |
| GitHub REST API (commits/releases of crypto repos) | free-key | N | UNVERIFIED | n/a |
| npm download counts API | free-nokey | Y | UNVERIFIED (terms 404) | Terms page returned 404 [UNK] |
| PyPI download stats | free-nokey | Y | UNVERIFIED | Not fetched [UNK] |
| crates.io download stats | free-nokey | Y | UNVERIFIED | Not fetched [UNK] |
| Wikimedia REST pageviews | free-nokey | Y | CLEAR_OPEN (CC0) | Analytics datasets under CC0 [DOC dumps.wikimedia.org readme] |
| Google Trends (unofficial endpoints) | restricted | N | RESTRICTIVE (scraping) | Google ToS prohibit automated scraping [INF] |
| Crypto Fear & Greed Index (alternative.me) | free-nokey | Y | CONDITIONAL (60 req/min; reuse terms unverified) | Attribution/limits stated at alternative.me/crypto/api [DOC: 60 req/min over 10-min window]; reuse terms [UNK] |
| Hacker News Algolia search API | free-nokey | Y | UNVERIFIED | Not fetched [UNK] |
| Reddit RSS/Atom (r/Bitcoin) | free-nokey | Y | RESTRICTIVE (Data API Terms) | Reddit Data API Terms: commercial use and research above rate limits need a separate agreement [DOC redditinc.com] |
| Arctic Shift Reddit archive API | free-nokey | Y | UNVERIFIED | Third-party archive of Reddit content; Reddit terms apply [INF] |
| StockTwits public stream | free-nokey | Y | RESTRICTIVE (ToS) | Terms fetched prohibit circumventing rate limits/access controls [DOC stocktwits.com/terms]; data redistribution [UNK] |
| Mastodon public tag timeline | free-nokey | Y | UNVERIFIED | Not fetched [UNK] |
| Bluesky public search API | restricted | N | UNVERIFIED | n/a |
| 4chan /biz/ catalog | free-nokey | Y | UNVERIFIED | Not fetched [UNK] |
| LunarCrush API | paid/key | N | UNVERIFIED | n/a |
| GDELT 2.0 raw 15-minute files (GKG/Events/Mentions) | free-nokey | Y | CLEAR_OPEN (free incl. commercial; cite GDELT) | 'free... for academic, commercial, or governmental use of any kind without fee'; redistribution allowed with citation [DOC gdeltproject.org/about] |
| GDELT DOC 2.0 API (timelines) | free-nokey | N | UNVERIFIED | as GDELT |
| Cointelegraph RSS | free-nokey | Y | UNVERIFIED | Site terms fetched; personal-use/redistribution limits [DOC cointelegraph.com/terms-and-privacy, details not parsed] |
| CoinDesk RSS | free-nokey | Y | UNVERIFIED | Not fetched [UNK] |
| Decrypt RSS | free-nokey | Y | UNVERIFIED | Not fetched [UNK] |
| BBC News business RSS | free-nokey | Y | CONDITIONAL (attribution) | Attribution 'BBC News' required when content appears [DOC bbc.co.uk/news/10628494] |
| Federal Reserve press RSS | free-nokey | Y | UNVERIFIED | US government content; reuse terms not fetched [UNK] |
| SEC press-release RSS | free-nokey | Y | UNVERIFIED | Not fetched [UNK] |
| ECB press RSS | free-nokey | Y | UNVERIFIED | Not fetched [UNK] |
| US Treasury press RSS | free-nokey | N | UNVERIFIED | n/a |
| Polymarket Gamma + CLOB APIs | free-nokey | Y | UNVERIFIED | ToS/docs pages fetched but no licence keywords found [UNK] |
| Kalshi public market-data API | free-nokey | Y | UNVERIFIED (docs) | Docs fetched (rate-limit tiers mentioned) but no data licence text found [DOC/UNK] |
| CFTC Commitments of Traders (Socrata public reporting) | free-nokey | Y | UNVERIFIED (US gov; disclaimer page 404) | US government publication; CFTC site disclaimer page returned 404, reuse terms [UNK] |
| iShares fund pages / holdings CSV (IBIT, IVV) | restricted | N | UNVERIFIED | Not fetched [UNK] |
| Farside Investors ETF flow tables | restricted | N | UNVERIFIED | n/a |
| SEC EDGAR (submissions, XBRL frames, full-text search) | free-nokey | Y | UNVERIFIED (fair-access page 403) | Site fair-access pages returned 403 to our fetch; fair-access policy requires declared UA and rate limit [UNK details] |
| Yahoo Finance chart endpoints (unofficial) | restricted | N | RESTRICTIVE (ToS) | Terms fetched: prohibit access by unofficial methods [DOC legal.yahoo.com] |
| IMF PortWatch daily chokepoint transits (ArcGIS FeatureServer) | free-nokey | Y | UNVERIFIED (IMF terms 403) | IMF copyright page returned 403; data-and-methodology page had no licence text [UNK] |
| AISHub | free-key | N | UNVERIFIED | Data-sharing membership model [UNK] |
| Stooq Baltic Dry Index CSV | free-nokey | N | UNVERIFIED | n/a |
| EIA bulk files (PET.zip, NG.zip) + WPSR/ NG storage release files | free-nokey | Y | CLEAR_OPEN (public domain) | 'U.S. government publications are in the public domain' [DOC eia.gov/about/copyrights_reuse.php] |
| EIA API v2 | free-key | N | UNVERIFIED | Public domain [DOC] |
| GIE AGSI+ EU gas storage | free-key | N | UNVERIFIED | n/a |
| Open-Meteo (forecast, archive, historical-forecast) | free-nokey | Y | CONDITIONAL (free API non-commercial, CC-BY 4.0) | Free API: non-commercial only, <10,000 calls/day, 5,000/h, 600/min, CC-BY 4.0 [DOC open-meteo.com/en/terms] |
| NOAA/NWS api.weather.gov | free-nokey | Y | CLEAR_OPEN (public domain) | Public domain unless annotated [DOC weather.gov/disclaimer] |
| NOAA CPC population-weighted degree days | free-nokey | Y | CLEAR_OPEN (public domain) | Public domain [DOC weather.gov/disclaimer] |
| NOAA NCEI Access Data Service (GHCN-daily) | free-nokey | Y | UNVERIFIED | Public domain [DOC weather.gov/disclaimer applies to NOAA sites; NCEI page not fetched] |
| NASA POWER daily API | free-nokey | Y | UNVERIFIED | Docs fetched; no licence keywords [UNK] |
| NOAA GFS on AWS open data (S3) | free-nokey | Y | CLEAR_OPEN (NOAA open data) [INF] | NOAA open data (public domain) [INF] |
| US Treasury FiscalData (Daily Treasury Statement: TGA) | free-nokey | Y | CLEAR_OPEN (no restriction, commercial OK) | 'free, without restriction ... commercial or non-commercial' [DOC fiscaldata.treasury.gov/api-documentation] |
| NY Fed Markets API (reverse-repo operations) | free-nokey | Y | UNVERIFIED | Terms page fetched, no keywords [UNK] |
| FRED / ALFRED CSV | free-key | N | UNVERIFIED | Terms page unreachable [OBS] |
| Federal Reserve H.4.1 data download | free-nokey | N | UNVERIFIED | n/a |
| ECB euro FX reference rates | free-nokey | Y | UNVERIFIED | Not fetched [UNK] |
| IMF DataMapper API | free-nokey | N | UNVERIFIED | n/a |
