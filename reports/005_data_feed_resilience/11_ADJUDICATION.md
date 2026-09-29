# 11 — Adjudication

Verdict vocabulary: **ADOPT_REFERENCE** (use as the reference source for the class in further research; nothing is integrated), **ADAPT_CANDIDATE**, **PARK** (insufficient evidence, blocked, thin, or restricted), **REJECT**. No synthetic ranking and no scoring; ordering is by group, then name.

## ADOPT_REFERENCE (8)
| Source | Executed | Classes | Basis for verdict |
|---|---|---|---|
| Binance Vision bulk (data.binance.vision) | Y | SPOT, FUND, OI, BASIS, BAR_MTF | Only source with bulk OI/LSR (metrics) + funding + premium index for Binance perps; liquidationSnapshot & bookTicker folders 404 for BTCUSDT |
| Binance data-api.binance.vision (spot mirror) | Y | SPOT, BAR_MTF | api.binance.com/fapi returned HTTP 451 from this egress; the market-data-only mirror works. ToS/licence text NOT_FOUND |
| Coinbase Exchange public | Y | SPOT, GOLD | USD spot; PAXG-USD as gold proxy |
| Deribit public v2 | Y | FUND, OI, BASIS, OPT, GOLD, BAR_MTF | Only keyless source with full BTC options surface (944 instruments) + DVOL; OI reported in USD contracts for BTC |
| ECB Data Portal (SDMX) + eurofxref | Y | FX | reference (fixing) rate, not tradable price |
| Kraken spot REST/WS | Y | SPOT, BAR_MTF | USD-quoted; tight to peers (0.43 bps median dev from group consensus) |
| NY Fed Markets API (SOFR etc.) | Y | MACRO | closest to native revision signalling among keyless macro sources |
| OKX v5 public | Y | SPOT, FUND, OI, LIQ, OPT, BASIS, BAR_MTF | Best single derivatives coverage among keyless venues; REST liquidation endpoint undocumented => contract risk |

## ADAPT_CANDIDATE (22)
| Source | Executed | Classes | Basis for verdict |
|---|---|---|---|
| Alpha Vantage (demo key) | Y | FX | docs: 25 requests/day free; EURUSD close 1.13700 on 2026-09-28 vs ECB fix 1.1378 (different time basis) |
| BLS Public Data API | Y | MACRO | OBSERVED: first probe returned REQUEST_NOT_PROCESSED daily-threshold message, later probe REQUEST_SUCCEEDED => shared-IP/day quota unpredictable |
| Bank of Canada Valet | Y | FX, MACRO | free-use terms quoted in docs |
| Bank of England IADB | Y | FX, MACRO | GBP/USD spot 4pm; XUDLERS is EUR-per-GBP (not EURUSD) |
| Bitfinex public v2 | Y | SPOT, LIQ, OI | SPOT price level sits ~13 bps above USD peers (unexplained; cause UNKNOWN) => do not use for level-sensitive work until explained; liquidation history is the useful part |
| Bitget v2 | Y | SPOT, FUND, OI | 1 minute (2026-09-29T09:02Z) missing while OKX/MEXC/Kraken have trades, persisted across 2 fetches; funding rate frequently pinned at 0.0001 (cap/floor?) in sample |
| Bitstamp | Y | SPOT | docs: commercial exploitation of data => contact vendor |
| CFTC Commitments of Traders (Socrata) | Y | COMM, GOLD, MACRO | positioning, not price. Publication (release) timestamp absent => PIT needs external schedule |
| Dukascopy historical feed (bi5) | Y | FX, GOLD, COMM, BAR_MTF | non-commercial only (docs quote); decoder needed; 20 s download latency once |
| Eurostat dissemination API | Y | MACRO | dataset-level update stamp is a usable observation-time proxy |
| Faireconomy/ForexFactory weekly calendar JSON | Y | CAL | schedule + forecast + previous only, no release values; unofficial; licence NOT_FOUND |
| Frankfurter | Y | FX | values identical to ECB for the 8 overlapping days (derived, not independent) |
| Gate.io v4 | Y | SPOT, FUND, LIQ, OI | Best ret. corr to consensus (0.988) among USDT spot; OI in contracts (quanto 0.0001 BTC): unit trap |
| Hyperliquid info API | Y | SPOT, FUND, OI, LIQ, GOLD, BAR_MTF | OI snapshot in BTC (34.3k) in same call as funding/premium; `xyz` dex lists commodity/equity perps incl. GOLD (mid 4153.05) |
| Kraken Futures public | Y | FUND, OI, BASIS | fixed-maturity FI_ contracts showed openInterest 0 and no last trade => thin basis venue |
| KuCoin public | Y | SPOT, FUND | funding values differ from OKX/Gate (venue-specific) |
| LBMA precious metals prices (prices.lbma.org.uk JSON) | Y | GOLD | docs: IBA licence required to redistribute (quoted for platinum/palladium; gold terms not verified) |
| Tokenised-gold pairs (PAXG/XAUT on OKX, Kraken, Coinbase, Deribit, Hyperliquid xyz) | Y | GOLD | 24/7 gold proxies; snapshot spread vs XAU spot proxy: OKX XAUT +0.07%, Kraken XAUT +0.05%, PAXG +0.19..+0.21%, Deribit PAXG perp +0.4%: token != spot XAU |
| US Treasury daily par yield curve (CSV) | Y | MACRO | row counts anomalous; verify pagination before relying on it |
| World Bank API + Commodity Pink Sheet | Y | MACRO, COMM | CC BY 4.0 per docs quote |
| Yahoo Finance chart endpoint (unofficial) | Y | FX, GOLD, COMM, MACRO, BAR_MTF | HTTP 429 seen on root probe and NG=F; XAUUSD=X returned no data; ToS restrictive on redistribution (docs: developer terms) |
| alternative.me Fear&Greed | Y | NEWS | sentiment index, commercial use allowed with attribution per docs |

## REJECT (1)
| Source | Executed | Classes | Basis for verdict |
|---|---|---|---|
| Trading Economics API | N | MACRO, CAL, FX, COMM | paid subscription required |

## PARK (37)
| Source | Executed | Classes | Basis for verdict |
|---|---|---|---|
| ALFRED (archival FRED) | BLK | MACRO | PIT_NATIVE is a documented claim only - execution blocked |
| BEA API | N | MACRO | key required; free status not verified |
| BLS release schedule ICS | BLK | CAL | NOT TESTED |
| Binance main REST/WS (api/fapi.binance.com) | BLK | SPOT, FUND, OI, LIQ | NOT TESTED: blocked at test egress; capability from Vision/mirror only |
| Binance.US | Y | SPOT | 112/240 zero-volume bars; corr 0.59: too thin |
| BitMEX public | Y | FUND, LIQ | XBTUSD is settled; liquidation REST returned [] at sample time; low current relevance |
| Bybit v5 | BLK | SPOT, FUND, OI, LIQ | NOT TESTED (geo-block) |
| CoinGecko public API | Y | SPOT | aggregated pricing, coarse bars; attribution required by terms; MCP connector failed to connect in this session |
| Coinalyze API | N | FUND, OI, LIQ | aggregated OI/funding/liquidations vendor - highest-relevance UNTESTED candidate; free-key terms UNKNOWN |
| CryptoCompare / CoinDesk data API | N | SPOT | key required; free tier existence NOT verified here |
| CryptoPanic | BLK | NEWS | NOT TESTED |
| EIA Open Data API v2 | N | COMM, MACRO | not executed: needs key. Public-domain per docs |
| FRED API + fredgraph.csv | PART | MACRO, COMM | DATA PATH NOT EXECUTED. Highest-priority follow-up: run with a free key from an unrestricted network. Third-party series carry copyright restrictions (docs quote) |
| Financial Modeling Prep | N | CAL | legacy /api/v3 endpoint; free-tier calendar capability UNKNOWN |
| Finnhub | N | CAL, FX | docs: no redistribution of data or derived results; economic-calendar free-tier capability UNKNOWN |
| GDELT DOC API | BLK | NEWS | NOT TESTED; docs: unrestricted use |
| Gemini public | Y | SPOT | 23/240 flat and 16/240 zero-volume bars (gap-filled); ret. corr vs consensus 0.79 => low information per bar |
| HTX spot | Y | SPOT | -4.5 bps vs USDT-group consensus, 8/240 flat bars; larger deviation than peers |
| IMF DataMapper API | BLK | MACRO | NOT TESTED |
| MEXC spot | Y | SPOT | no docs facts extracted (NOT_FOUND); futures API unreachable here |
| OANDA fxTrade Practice API | N | FX | practice account needed; not tested |
| OECD SDMX | N | MACRO | NOT TESTED PROPERLY (own error) |
| Polygon.io | N | FX | free plan documented for stocks (5 calls/min); FX capability on free plan UNKNOWN |
| Stooq CSV | BLK | FX, GOLD, COMM | NOT TESTED |
| Swiss National Bank data portal | Y | MACRO, FX | not evaluated beyond reachability |
| Swissquote public quotes | Y | GOLD, FX | undocumented endpoint; bid 4152.875 / ask 4153.565 at snapshot |
| TipRanks connector (economic calendar etc.) | N | CAL, NEWS | deliberately NOT executed: would consume the account holder's quota and terms are unverified |
| Twelve Data (demo key) | Y | FX | free plan: personal/internal/non-commercial (docs quote) |
| US Treasury FiscalData API | Y | MACRO | public domain 'without restriction' (docs quote); low frequency |
| dYdX v4 indexer | Y | FUND | 150/240 zero-volume bars and ret. corr 0.43 vs consensus in sample: thin market |
| exchangerate.host | N | FX | free-plan capability UNKNOWN |
| fawazahmed0/currency-api (jsDelivr) | Y | FX | licence NOT_FOUND |
| federalreserve.gov FOMC calendar page | Y | CAL | scrape only; not parsed |
| gold-api.com | Y | GOLD | snapshot only |
| mempool.space / blockchain.info charts | Y | NEWS | auxiliary, off-scope for market data gaps |
| metals.live / goldprice.org | BLK | GOLD | NOT TESTED |
| open.er-api.com | Y | FX | terms: attribution; no redistribution |

## Class-level candidate view (executed sources with ADOPT_REFERENCE or ADAPT_CANDIDATE)
* **Crypto spot** (11): Binance Vision bulk (data.binance.vision), Binance data-api.binance.vision (spot mirror), Bitfinex public v2, Bitget v2, Bitstamp, Coinbase Exchange public, Gate.io v4, Hyperliquid info API, Kraken spot REST/WS, KuCoin public, OKX v5 public
* **Derivatives (funding/OI/liq/basis/options)** (9): Binance Vision bulk (data.binance.vision), Bitfinex public v2, Bitget v2, Deribit public v2, Gate.io v4, Hyperliquid info API, Kraken Futures public, KuCoin public, OKX v5 public
* **FX** (7): Alpha Vantage (demo key), Bank of Canada Valet, Bank of England IADB, Dukascopy historical feed (bi5), ECB Data Portal (SDMX) + eurofxref, Frankfurter, Yahoo Finance chart endpoint (unofficial)
* **Commodities + gold** (9): CFTC Commitments of Traders (Socrata), Coinbase Exchange public, Deribit public v2, Dukascopy historical feed (bi5), Hyperliquid info API, LBMA precious metals prices (prices.lbma.org.uk JSON), Tokenised-gold pairs (PAXG/XAUT on OKX, Kraken, Coinbase, Deribit, Hyperliquid xyz), World Bank API + Commodity Pink Sheet, Yahoo Finance chart endpoint (unofficial)
* **Macro** (9): BLS Public Data API, Bank of Canada Valet, Bank of England IADB, CFTC Commitments of Traders (Socrata), Eurostat dissemination API, NY Fed Markets API (SOFR etc.), US Treasury daily par yield curve (CSV), World Bank API + Commodity Pink Sheet, Yahoo Finance chart endpoint (unofficial)
* **Calendar** (1): Faireconomy/ForexFactory weekly calendar JSON

## Drop-in and invalidation
* **ANY_DROP_IN_SOURCE = NO.** "Drop-in" was defined as: keyless or stable free access + executed + PIT-native or provider-signalled finality + documented permissive licence + covers a gap class without adaptation. No source meets all conditions (exchange licences unverified; no PIT-native source executed; contract hazards listed in 08).
* **ANY_SCIENTIFIC_INVALIDATION = NO.** Nothing observed invalidates a stated hypothesis of the mission; observed hazards (unit drift, unflagged forming bar, venue-specific funding) are constraints, not refutations.
