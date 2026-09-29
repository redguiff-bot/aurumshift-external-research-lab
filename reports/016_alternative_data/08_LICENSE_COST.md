# 08 — Licence and cost

All executed sources were **free at the point of use**; no key, account or payment was used. Licence statements are DOCUMENTED_CLAIM unless marked OBS and were **not** legally reviewed — treat every row as needing verification before any use beyond internal research.

| Source | Cost | Access | Licence / terms | Commercial-use risk |
|---|---|---|---|---|
| Blockchain.com Charts API | free | keyless REST | ToS not verified (UNKNOWN); attribution asked (DOC) | UNKNOWN |
| mempool.space REST (blocks/fees/mining) | free | keyless REST/WS | AGPL software; public API fair-use (DOC) | low-moderate (attribution/fair-use, DOC) |
| Blockstream Esplora | free | keyless REST | Blockstream public API terms (UNKNOWN exact) | UNKNOWN |
| Blockchair stats | free tier | keyless (1440 req/day free DOC); key for more | ToS restricts commercial (DOC) | HIGH / needs licence |
| DefiLlama stablecoins & TVL | free | keyless REST | CC-BY-like/attribution (DOC, not verified) | UNKNOWN |
| GDELT DOC 2.0 API | free | keyless REST | open, attribution (DOC) | low-moderate (attribution/fair-use, DOC) |
| Crypto-news RSS (Cointelegraph) | free | keyless RSS | content copyright; headline use only (DOC) | low-moderate (attribution/fair-use, DOC) |
| Federal Reserve press RSS | free | keyless RSS | US gov public domain (DOC) | low (US gov public domain, DOC) |
| Hacker News (Algolia) | free | keyless REST | HN data terms UNKNOWN | UNKNOWN |
| StockTwits symbol stream | free | keyless (limited) | ToS forbids redistribution (DOC) | HIGH / needs licence |
| Reddit .json listing | free (commercial use needs licence, DOC) | keyless but blocked to datacentre/proxy IPs | restrictive (DOC) | HIGH / needs licence |
| Bluesky AppView | free | keyless public AppView | open protocol | low-moderate (attribution/fair-use, DOC) |
| Google Trends (unofficial) | free | no official API; unofficial scrapers | ToS forbids scraping (DOC) | HIGH / needs licence |
| Wikimedia pageviews REST | free | keyless REST; UA required | CC0 data (DOC) | low-moderate (attribution/fair-use, DOC) |
| alternative.me Fear & Greed | free | keyless REST | attribution required (DOC) | low-moderate (attribution/fair-use, DOC) |
| Polymarket Gamma+CLOB | free | keyless read | ToS: read-only public data; geo restrictions on trading (DOC) | HIGH / needs licence |
| Kalshi public market data | free | keyless read for market data | ToS (UNKNOWN exact) | UNKNOWN |
| CFTC Public Reporting (Socrata) COT | free | keyless Socrata (app token optional) | US gov public domain (DOC) | low (US gov public domain, DOC) |
| Farside ETF flows | free (site) | HTML behind Cloudflare challenge | no explicit licence; scraping discouraged | low-moderate (attribution/fair-use, DOC) |
| SPDR GLD holdings (issuer) | free | keyless file (current snapshot) | issuer terms (UNKNOWN) | UNKNOWN |
| SEC EDGAR (13F, Form 4, 8-K) | free | keyless w/ declared UA | US gov public domain | low (US gov public domain, DOC) |
| Treasury FiscalData DTS (TGA) | free | keyless REST | US gov public domain | low (US gov public domain, DOC) |
| NY Fed markets (RRP/SOFR) | free | keyless REST | public domain-like | low (US gov public domain, DOC) |
| ClickHouse public playground github_events (GH Archive) | free | keyless SQL over HTTP (read-only user `play`) | GH Archive CC-BY-4.0-ish (DOC); playground is a demo, no SLA | low-moderate (attribution/fair-use, DOC) |
| GH Archive hourly dumps | free | keyless file download | CC-BY (DOC, unverified) | low-moderate (attribution/fair-use, DOC) |
| GitHub REST API | free | token for useful limits | ToS | low-moderate (attribution/fair-use, DOC) |
| npm downloads / pypistats | free | keyless REST | public | low-moderate (attribution/fair-use, DOC) |
| IMF PortWatch (ArcGIS FeatureServer) | free | keyless ArcGIS query | CC-BY 4.0 (DOC) | low-moderate (attribution/fair-use, DOC) |
| EIA weekly petroleum/gas files (xls) | free | keyless xls; API v2 needs free key | US gov public domain | low (US gov public domain, DOC) |
| EIA API v2 | free | free API key (registration) | public domain | low (US gov public domain, DOC) |
| GIE AGSI+ EU gas storage | free | free API key (x-key) required | attribution (DOC) | low-moderate (attribution/fair-use, DOC) |
| Open-Meteo archive / historical-forecast | free non-commercial; commercial paid | keyless (non-commercial) | CC-BY 4.0 for data; API non-commercial (DOC) | HIGH / needs licence |
| NWS api.weather.gov | free | keyless w/ UA | US gov public domain | low (US gov public domain, DOC) |
| NOAA NDBC buoys realtime | free | keyless | public domain | low (US gov public domain, DOC) |
| Deribit public API (index/funding/OI) | free | keyless REST/WS | ToS (UNKNOWN exact) | UNKNOWN |
| Binance Vision (data.binance.vision) | free | keyless files | Binance Vision terms (DOC) | low-moderate (attribution/fair-use, DOC) |
| Exchange wallet/reserve flows (Glassnode/CryptoQuant/Arkham) | paid for history+resolution (DOC) | FREE TIER LIMITED / paid API | proprietary licence (DOC) | HIGH / needs licence |
| Baltic Dry Index / freight indices | paid (DOC) | paid (Baltic Exchange) | proprietary | HIGH / needs licence |
| AIS open feeds (AISHub, GFW) | free w/ conditions | AISHub requires data-sharing; GFW token | conditional | low-moderate (attribution/fair-use, DOC) |


Risk tally over 39 sources: UNKNOWN=7, low-moderate=15, HIGH=8, low=9. Free sources: 37 (executed: 29). Not free / not executable: exchange reserves (vendor), Baltic indices (paid), AISHub/GFW (account with conditions), Open-Meteo commercial (paid).

Cost beyond licence: GH Archive ≈ 60-150 MB/hour of raw data; Binance Vision daily metrics ≈ 11 kB/day; EIA files 130 kB each.
