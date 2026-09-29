# 08 — PIT readiness

Classification uses what each source *emits*, not what a downstream store could add. Criteria: event timestamp · observation/receipt timestamp · provider event ID · revision/correction signal · finality · backfill discrimination.

* **PIT_NATIVE** = provider itself supplies as-of/vintage semantics.
* **PIT_ADAPTABLE** = event time + ≥1 of (ID, finality flag, revision indicator, server receipt stamp, immutable file metadata) so that a consumer can build PIT with its own receipt stamps.
* **PIT_WEAK** = only overwriting/latest values or missing event time granularity.
* **PIT_UNSUITABLE** = snapshot with no history and no reliable event time.

| class | all | executed |
|---|---|---|
| PIT_NATIVE | 1 | 0 |
| PIT_ADAPTABLE | 34 | 30 |
| PIT_WEAK | 30 | 13 |
| PIT_UNSUITABLE | 3 | 3 |

## Signals actually observed (per executed source class)
| Signal | Present in | Absent / not observed |
|---|---|---|
| Event timestamp | all bar/tick/funding sources | gold-api (updatedAt only), open.er-api (daily stamp) |
| Provider receipt/server stamp | **Deribit** (`usIn`/`usOut` µs in every JSON-RPC response); HTTP `Date` header on all (coarse) | all other exchange REST payloads |
| Provider event ID | Deribit trade_id; Coinbase match trade_id/sequence; Binance trade id; Hyperliquid tid; dYdX `effectiveAtHeight` (block) | candle endpoints (no IDs), funding rows |
| Revision/correction signal | NY Fed `revisionIndicator`; ECB `OBS_STATUS`, `updatedAfter`; Eurostat dataset `updated`; BLS footnote codes | every exchange feed; FRED path unexecuted |
| Finality | OKX `confirm`, Gate closed-flag, Binance Vision immutable dated files (+ CHECKSUM, ETag, Last-Modified) | Kraken/Coinbase/Bitstamp etc. (forming bar returned unflagged on Kraken) |
| Backfill discrimination | Binance Vision (bulk vs API distinguishable by origin and `Last-Modified`) | all REST candle endpoints: a re-fetch returns the same rows with no ingestion metadata |

## Per-source classification
| Source | PIT class | Executed | Why |
|---|---|---|---|
| ALFRED (archival FRED) | PIT_NATIVE | BLK | documented vintage semantics; NOT executed |
| Binance data-api.binance.vision (spot mirror) | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Binance main REST/WS (api/fapi.binance.com) | PIT_ADAPTABLE | BLK | event time + at least one of ID/finality/revision/receipt metadata |
| Binance.US | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Binance Vision bulk (data.binance.vision) | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Bitfinex public v2 | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Bitget v2 | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| BitMEX public | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Bitstamp | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| BLS Public Data API | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Bank of Canada Valet | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Bank of England IADB | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Bybit v5 | PIT_ADAPTABLE | BLK | event time + at least one of ID/finality/revision/receipt metadata |
| CFTC Commitments of Traders (Socrata) | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Coinbase Exchange public | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Deribit public v2 | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Dukascopy historical feed (bi5) | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| dYdX v4 indexer | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| ECB Data Portal (SDMX) + eurofxref | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| EIA Open Data API v2 | PIT_ADAPTABLE | N | event time + at least one of ID/finality/revision/receipt metadata |
| Eurostat dissemination API | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| FRED API + fredgraph.csv | PIT_ADAPTABLE | PART | event time + at least one of ID/finality/revision/receipt metadata |
| Gate.io v4 | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| HTX spot | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Hyperliquid info API | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Kraken spot REST/WS | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Kraken Futures public | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| KuCoin public | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| LBMA precious metals prices (prices.lbma.org.uk JSON) | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| MEXC spot | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| NY Fed Markets API (SOFR etc.) | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| OKX v5 public | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Tokenised-gold pairs (PAXG/XAUT on OKX, Kraken, Coinbase, Deribit, Hyperliquid xyz) | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| US Treasury FiscalData API | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| US Treasury daily par yield curve (CSV) | PIT_ADAPTABLE | Y | event time + at least one of ID/finality/revision/receipt metadata |
| Alpha Vantage (demo key) | PIT_WEAK | Y | latest-only or coarse/no event ID or revision signal |
| alternative.me Fear&Greed | PIT_WEAK | Y | latest-only or coarse/no event ID or revision signal |
| BEA API | PIT_WEAK | N | latest-only or coarse/no event ID or revision signal |
| BLS release schedule ICS | PIT_WEAK | BLK | latest-only or coarse/no event ID or revision signal |
| Coinalyze API | PIT_WEAK | N | latest-only or coarse/no event ID or revision signal |
| CoinGecko public API | PIT_WEAK | Y | latest-only or coarse/no event ID or revision signal |
| CryptoCompare / CoinDesk data API | PIT_WEAK | N | latest-only or coarse/no event ID or revision signal |
| CryptoPanic | PIT_WEAK | BLK | latest-only or coarse/no event ID or revision signal |
| exchangerate.host | PIT_WEAK | N | latest-only or coarse/no event ID or revision signal |
| Faireconomy/ForexFactory weekly calendar JSON | PIT_WEAK | Y | latest-only or coarse/no event ID or revision signal |
| fawazahmed0/currency-api (jsDelivr) | PIT_WEAK | Y | latest-only or coarse/no event ID or revision signal |
| Finnhub | PIT_WEAK | N | latest-only or coarse/no event ID or revision signal |
| Financial Modeling Prep | PIT_WEAK | N | latest-only or coarse/no event ID or revision signal |
| federalreserve.gov FOMC calendar page | PIT_WEAK | Y | latest-only or coarse/no event ID or revision signal |
| Frankfurter | PIT_WEAK | Y | latest-only or coarse/no event ID or revision signal |
| GDELT DOC API | PIT_WEAK | BLK | latest-only or coarse/no event ID or revision signal |
| Gemini public | PIT_WEAK | Y | latest-only or coarse/no event ID or revision signal |
| IMF DataMapper API | PIT_WEAK | BLK | latest-only or coarse/no event ID or revision signal |
| metals.live / goldprice.org | PIT_WEAK | BLK | latest-only or coarse/no event ID or revision signal |
| OANDA fxTrade Practice API | PIT_WEAK | N | latest-only or coarse/no event ID or revision signal |
| OECD SDMX | PIT_WEAK | N | latest-only or coarse/no event ID or revision signal |
| mempool.space / blockchain.info charts | PIT_WEAK | Y | latest-only or coarse/no event ID or revision signal |
| Polygon.io | PIT_WEAK | N | latest-only or coarse/no event ID or revision signal |
| Swiss National Bank data portal | PIT_WEAK | Y | latest-only or coarse/no event ID or revision signal |
| Stooq CSV | PIT_WEAK | BLK | latest-only or coarse/no event ID or revision signal |
| TipRanks connector (economic calendar etc.) | PIT_WEAK | N | latest-only or coarse/no event ID or revision signal |
| Trading Economics API | PIT_WEAK | N | latest-only or coarse/no event ID or revision signal |
| Twelve Data (demo key) | PIT_WEAK | Y | latest-only or coarse/no event ID or revision signal |
| World Bank API + Commodity Pink Sheet | PIT_WEAK | Y | latest-only or coarse/no event ID or revision signal |
| Yahoo Finance chart endpoint (unofficial) | PIT_WEAK | Y | latest-only or coarse/no event ID or revision signal |
| gold-api.com | PIT_UNSUITABLE | Y | overwritten snapshot, no history |
| open.er-api.com | PIT_UNSUITABLE | Y | overwritten snapshot, no history |
| Swissquote public quotes | PIT_UNSUITABLE | Y | overwritten snapshot, no history |

## Findings
1. No executed source is PIT_NATIVE. The only PIT_NATIVE claim (ALFRED vintages) is DOCUMENTED_CLAIM and the host was unreachable — it must not be counted as evidence.
2. Bar/funding/OI APIs give event time but let the same key be re-fetched with no ingestion metadata; a consumer must stamp `received_at` itself and store every fetch (re-fetch diff over 6 min showed 0 changes on 17 series, so the *risk* appears low on closed 1m bars but was not excluded for longer horizons).
3. Closed-bar finality is provider-signalled only on OKX and Gate; elsewhere it must be inferred from `bar_open + 60 s < received_at`.
4. Backfills are cleanly separable only for Binance Vision (file-level metadata) — a strong reason to use it as the historical reference and the live APIs for the trailing edge, with a tested join rule at the seam (seam consistency for 2026-09-26: 1440/1440 identical).
5. Timestamp-unit drift (µs vs ms), column-order drift and unflagged forming bars are PIT hazards (look-ahead by including the forming bar) and need per-source contract tests.
