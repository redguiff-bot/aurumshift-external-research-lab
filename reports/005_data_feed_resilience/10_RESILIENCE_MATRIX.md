# 10 — Resilience matrix

Roles are *capability statements from measured behaviour*; no automatic failover design is proposed. Role vocabulary: PRIMARY / SECONDARY / FALLBACK / CORROBORATION_ONLY / HISTORICAL_ONLY. A source only appears where an executed test supports the role.

| Gap class | PRIMARY | SECONDARY | FALLBACK | CORROBORATION_ONLY | HISTORICAL_ONLY |
|---|---|---|---|---|---|
| Crypto spot bars (1m/MTF) | OKX v5 public, Kraken spot REST/WS, Coinbase Exchange public, Binance data-api.binance.vision | Gate.io v4 | — | Bitstamp, KuCoin public, Gemini public, Bitget v2, MEXC spot, HTX spot, CoinGecko public API | Binance Vision bulk |
| Funding | OKX v5 public | Deribit public v2, Hyperliquid info API | Kraken Futures public, Gate.io v4 | KuCoin public, Bitget v2 | Binance Vision bulk |
| Open interest | OKX v5 public | Deribit public v2, Hyperliquid info API | Gate.io v4 | Kraken Futures public, Bitget v2 | Binance Vision bulk |
| Liquidations | — | OKX v5 public | Gate.io v4 | Bitfinex public v2 | — |
| Basis | Deribit public v2 | OKX v5 public | — | — | Binance Vision bulk |
| Options IV/skew | Deribit public v2 | OKX v5 public | — | — | — |
| FX | ECB Data Portal | — | Frankfurter, Alpha Vantage | Bank of England IADB, Bank of Canada Valet, Yahoo Finance chart endpoint | Dukascopy historical feed |
| Gold/metals | — | Tokenised-gold pairs | — | Coinbase Exchange public, Yahoo Finance chart endpoint, gold-api.com, Swissquote public quotes | Dukascopy historical feed, LBMA precious metals prices |
| Commodities | CFTC Commitments of Traders | — | — | Yahoo Finance chart endpoint | World Bank API + Commodity Pink Sheet |
| Macro | NY Fed Markets API | BLS Public Data API, US Treasury daily par yield curve, Eurostat dissemination API | — | — | — |
| Calendar/news | — | — | Faireconomy/ForexFactory weekly calendar JSON | federalreserve.gov FOMC calendar page | — |

Executed sources holding at least one PRIMARY/SECONDARY/FALLBACK role: **18** → Alpha Vantage (demo key), BLS Public Data API, Binance data-api.binance.vision (spot mirror), CFTC Commitments of Traders (Socrata), Coinbase Exchange public, Deribit public v2, ECB Data Portal (SDMX) + eurofxref, Eurostat dissemination API, Faireconomy/ForexFactory weekly calendar JSON, Frankfurter, Gate.io v4, Hyperliquid info API, Kraken Futures public, Kraken spot REST/WS, NY Fed Markets API (SOFR etc.), OKX v5 public, Tokenised-gold pairs (PAXG/XAUT on OKX, Kraken, Coinbase, Deribit, Hyperliquid xyz), US Treasury daily par yield curve (CSV).

## Reading the matrix
* **Crypto spot** has the deepest redundancy: ten keyless venues with |median| close deviation ≤1.32 bps from their group consensus (Kraken, Coinbase, Bitstamp, Gemini, OKX, KuCoin, Gate, Bitget, MEXC, Binance mirror), of which four (OKX, Kraken, Coinbase, Binance mirror) are marked PRIMARY-*capable* on clean-bar evidence — capability, not ranking. Independent *providers* here are independent *venues* (different trade populations), so failover between them changes the series (0 exact OHLC matches) — a substitution is a different price series, not a copy.
* **Derivatives**: OKX + Deribit + Hyperliquid + Gate give ≥3 independent funding/OI feeds; liquidations rely on OKX/Gate/Bitfinex samples (no complete tape verified); options IV has exactly two keyless providers (Deribit, OKX), which agree within 0.5 vol pts (median |Δ|) but up to 2.4 at 1-day expiry.
* **FX/gold/macro/calendar**: redundancy is thin and mostly *daily/reference* data. Official FX is ECB-based (Frankfurter is derived from ECB — not an independent fallback). Intraday FX and commodities depend on Yahoo (unofficial, 429s) and Dukascopy ticks (non-commercial).
* **Blocked-at-egress but potentially decisive:** Binance main/fapi, Bybit, FRED/ALFRED — resilience conclusions for Binance/Bybit derivatives and PIT-native macro are OPEN, not negative.
* Correlated-failure notes (INFERENCE): several sources sit behind Cloudflare; Frankfurter/ECB/Alpha-Vantage EURUSD are not independent of each other's underlying reference; Coinbase PAXG and Deribit PAXG perp share the same underlying token.
