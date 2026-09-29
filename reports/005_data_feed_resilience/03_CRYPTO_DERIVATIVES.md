# 03 — Crypto derivatives (funding, OI, basis, liquidations, options)

Code: `py/sweep1.py`, `py/dv.py`, `py/ws_sample.py`. Results: `results/derivs_analysis.json`, `results/ws_sample.json`, `results/ws_okx_retry.json`. Snapshot time ≈ 2026-09-29 13:00 UTC.

## Funding (BTC perpetuals, last 7 d)
| Venue/series | rows | gap between rows (min) | span |
|---|---|---|---|
| okx_BTC-USDT-SWAP | 30 | [480] | 09-19 16:00 → 09-29 08:00 |
| okx_realized_field | 30 | [480] | 09-19 16:00 → 09-29 08:00 |
| gate_BTC_USDT | 30 | [479, 480] | 09-19 16:00 → 09-29 08:00 |
| bitget_BTCUSDT | 30 | [480] | 09-19 16:00 → 09-29 08:00 |
| kucoin_XBTUSDTM | 21 | [480] | 09-22 16:00 → 09-29 08:00 |
| hyperliquid_BTC(1h) | 168 | [59, 60] | 09-22 14:00 → 09-29 13:00 |
| dydx_BTC-USD(1h) | 200 | [60] | 09-21 06:00 → 09-29 13:00 |
| krakenfut_PF_XBTUSD(1h,relative) | 200 | [60] | 09-21 06:00 → 09-29 13:00 |
| deribit_BTC-PERPETUAL(1h) | 168 | [60] | 09-22 14:00 → 09-29 13:00 |
| bitmex_XBTUSDT | 30 | [480] | 09-06 20:00 → 09-16 12:00 |

Cadence: 8-hour on OKX, Gate, Bitget, KuCoin, BitMEX; 1-hour on Hyperliquid, dYdX, Deribit, Kraken Futures. Timestamp jitter (OBSERVED): Hyperliquid `time` is …:00:00.059 style (not on the boundary); Gate first row carries +1 s. Kraken Futures returns a 1 MB response for the full history (from 2025-09-24) with `fundingRate` and `relativeFundingRate` (units differ; not normalised here).

Comparison at the 8-hour boundaries (units: bps per 8 h; Hyperliquid = sum of the 9 hourly rows covering the window):

| boundary | OKX | Gate | Bitget | KuCoin | Hyperliquid Σ |
|---|---|---|---|---|---|
| 09-24 16Z | -0.03 | -0.08 | +0.44 | +0.26 | +0.88 |
| 09-25 00Z | -0.04 | +0.07 | +0.27 | +0.09 | +1.13 |
| 09-25 08Z | +0.72 | +0.28 | +0.53 | +0.26 | +1.13 |
| 09-25 16Z | +0.34 | -0.07 | +0.78 | +0.29 | +1.13 |
| 09-26 00Z | +0.17 | -0.28 | +0.48 | -0.28 | +1.02 |
| 09-26 08Z | +0.21 | -0.09 | +0.71 | -0.05 | +0.77 |
| 09-26 16Z | -0.06 | -0.20 | +0.24 | -0.14 | +1.02 |
| 09-27 00Z | -0.09 | -0.15 | +0.24 | +0.22 | +0.73 |
| 09-27 08Z | -0.18 | -0.04 | +0.17 | +0.04 | +1.13 |
| 09-27 16Z | -0.11 | +0.04 | +0.07 | +0.05 | +1.13 |
| 09-28 00Z | +0.46 | -0.23 | +0.12 | -0.01 | +0.98 |
| 09-28 08Z | -0.08 | -0.15 | +1.00 | -0.22 | -0.03 |
| 09-28 16Z | +0.71 | +0.51 | +1.00 | +0.65 | +1.00 |
| 09-29 00Z | +0.54 | +0.17 | +1.00 | +0.17 | +0.57 |
| 09-29 08Z | +0.25 | +0.00 | +1.00 | +0.28 | +0.32 |

Sign disagreement among OKX/Gate/Bitget/KuCoin in 11/15 boundaries. Bitget printed exactly 1.00 bps in 3 of the last 4 rows (possible cap/floor, INFERENCE); Hyperliquid's per-hour value sits near its base rate. **Conclusion:** funding is a venue-specific realised quantity; cross-venue "corroboration" means comparing distributions, not values.

## Open interest
Snapshot (units as delivered; last column converts to BTC at 84,340 USD only for scale):

| Venue | field | unit | value | ≈ BTC |
|---|---|---|---|---|
| OKX BTC-USDT-SWAP | oiCcy | BTC | 28,328.5 | 28,329 |
| Bitget BTCUSDT | size | BTC | 31,577.4 | 31,577 |
| Hyperliquid BTC | openInterest | BTC | 34,292.4 | 34,292 |
| Deribit BTC-PERPETUAL | open_interest | USD | 796,941,590.0 | 9,449 |
| Gate BTC_USDT | position_size × quanto 0.0001 | contracts→BTC | 26,681.8 | 26,682 |
| Kraken Futures PF_XBTUSD | openInterest | unit UNKNOWN | 2,335.4 | 2,335 |
| dYdX BTC-USD | openInterest | BTC (documented unit not verified) | 201.1 | 201 |

Bitfinex `status/deriv` positional row carries a value at index 18 (8,933.01) that matches the documented open-interest slot (position mapping is INFERENCE from the API's documented layout; unit not verified). History: OKX `open-interest-history` 100 rows = 8.25 h @5 min; Gate `contract_stats` 99 rows @5 min (also carries long/short ratio and liquidation sizes); Binance Vision `futures/um/daily/metrics` 289 rows/day @5 min (sum OI ≈ 95,234 BTC at 2026-09-26 00:00, Binance aggregate — bulk only, main API blocked here).

## Liquidations
| Source | mode | observed |
|---|---|---|
| OKX | REST `/public/liquidation-orders` | 100 rows spanning 164 min. **Endpoint not in current docs** (docs list only WS channel) |
| OKX | WS `liquidation-orders` | 5 events in 15 s (port 443 path; :8443 reset by egress) |
| Gate | REST `/futures/usdt/liq_orders` | 13 rows / 19 min (BTC_USDT) |
| Bitfinex | REST `/liquidations/hist` | 500 rows / 78 h across ALL symbols (not per-symbol filtered in the probe) |
| BitMEX | REST / WS | REST `[]` at sample time; WS 1 liquidation msg in 20 s |
| Binance Vision | bulk `liquidationSnapshot` | HTTP 404 for BTCUSDT (folder not present) |
| Binance main / Bybit | REST/WS | BLOCKED at egress (451 / 403) |

Liquidation feeds are sample-based windows, not complete tapes: no source provides an event ID observed in the probe rows except positional/order IDs (Bitfinex position id). Completeness NOT verifiable.

## Basis (Deribit dated futures vs index)
| Instrument | mark | index (est. delivery) | days to expiry | basis % | annualised % (simple) | OI (USD) |
|---|---|---|---|---|---|---|
| BTC-30SEP26 | 84,329.79 | 84,337.71 | 0.8 | -0.009 | -4.33 | 1,692,400 |
| BTC-1OCT26 | 84,338.55 | 84,337.71 | 1.8 | +0.001 | +0.20 | 1,118,490 |
| BTC-2OCT26 | 84,357.18 | 84,337.71 | 2.8 | +0.023 | +3.02 | 8,872,130 |
| BTC-3OCT26 | 84,367.58 | 84,337.71 | 3.8 | +0.035 | +3.41 | 76,420 |
| BTC-9OCT26 | 84,420.18 | 84,337.71 | 9.8 | +0.098 | +3.65 | 5,752,860 |
| BTC-16OCT26 | 84,493.08 | 84,337.71 | 16.8 | +0.184 | +4.00 | 1,614,710 |
| BTC-30OCT26 | 84,659.01 | 84,337.71 | 30.8 | +0.381 | +4.52 | 69,544,490 |
| BTC-27NOV26 | 85,024.70 | 84,337.71 | 58.8 | +0.815 | +5.06 | 33,557,470 |
| BTC-25DEC26 | 85,349.78 | 84,337.71 | 86.8 | +1.200 | +5.05 | 311,788,310 |
| BTC-26MAR27 | 86,405.70 | 84,337.71 | 177.8 | +2.452 | +5.03 | 83,713,480 |
| BTC-25JUN27 | 87,610.01 | 84,337.71 | 268.8 | +3.880 | +5.27 | 63,730,580 |
| BTC-24SEP27 | 88,726.55 | 84,337.71 | 359.8 | +5.204 | +5.28 | 3,575,080 |

Deribit exposes `estimated_delivery_price` (= index) beside `mark_price` in one call. OKX lists dated futures (`BTC-USD-261030`, `…261127`, `…261225`, `…270326`, …) but the basis test was executed on Deribit only. Kraken fixed-maturity `FI_XBTUSD_261030/261225`: OI 0, no last trade (thin).

## Options IV / skew
Deribit BTC options: 944 instruments · OKX BTC-USD options: 1272 · common (expiry, strike, type) with both marks: 690.
Mark IV difference Deribit − OKX (vol points): median +0.34, mean +0.67, |median| 0.48, p05 -1.14, p95 +2.37.

| expiry | ATM strike | Deribit mark_iv | OKX markVol | Δ |
|---|---|---|---|---|
| 2026-09-30 | 84500C | 26.56 | 24.19 | +2.37 |
| 2026-10-01 | 84500C | 30.55 | 29.19 | +1.36 |
| 2026-10-02 | 84500P | 33.08 | 32.14 | +0.94 |
| 2026-10-03 | 84500C | 33.37 | 32.73 | +0.64 |
| 2026-10-09 | 84000C | 33.48 | 33.0 | +0.48 |
| 2026-10-16 | 84000C | 33.84 | 33.59 | +0.25 |
| 2026-10-30 | 85000C | 34.9 | 34.75 | +0.15 |
| 2026-11-27 | 85000P | 37.11 | 36.85 | +0.26 |

Near-dated expiries differ most (2.4 vol pts at 1-day). Deribit DVOL: 72 hourly rows for 3 days. Deribit `get_book_summary_by_currency(kind=option)` returns the whole surface in one 421 KB call (mark_iv, bid/ask, OI, underlying); OKX `opt-summary` returns 749 KB with greeks (delta, gamma, vega, theta) and `markVol`. Skew (25Δ risk reversal) was not computed: NOT TESTED.

## WebSocket bounded samples (20 s each; `results/ws_sample.json`)
| Endpoint | msgs | notes |
|---|---|---|
| Deribit trades/ticker/index | 76 | median recv−event 68.6 ms, p95 292.1 ms (local clock vs provider ts; clock skew not measured) |
| Hyperliquid trades + L2 | 68 | median 300.5 ms, p95 625.8 ms |
| OKX (port 443) trades+liq+funding | 40 (15 s) | median ≈68 ms; `:8443` connection reset by egress |
| Binance data-stream mirror | 627 | median 66.0 ms, p95 80.1 ms; `stream.binance.com:9443` reset |
| Coinbase matches+ticker | 214 | no numeric event ts parsed |
| Kraken v2 trade | 39 | 17 trades + 20 heartbeats |
| Bitstamp | 12 | median 45.6 ms |
| Bitfinex | 15 | |
| Gemini book+trades | 2102 | 2102 update msgs (book-heavy) |
| BitMEX trade+liquidation | 5 | 1 trade, 1 liquidation |
| dYdX v4 trades | 2 | connected+subscribed only; 0 trades in 20 s |
| Bybit | 1 | 1 control msg, no data (geo-block suspected, INFERENCE) |
| KuCoin | 0 | needs token bootstrap; proxy 502 on placeholder URL (probe artefact) |
