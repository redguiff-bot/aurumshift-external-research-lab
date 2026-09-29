# 02 — Crypto spot (and perp) 1-minute bars

Window: 240 closed minutes ending 2026-09-29 12:55Z (t0 fetched 12:56:58Z; re-fetch t2 362 s later). Raw normalised bars: `bench/data_feeds_v1/raw/bars_t0.json|t1|t2`; code: `py/bars_lib.py`, `py/run_bars.py`, `py/analyze_bars.py`, `py/consensus.py`, `py/lagtest.py`.

Columns: in-window bars / expected · missing · duplicates · native order · zero-volume bars · flat (O=H=L=C) bars · bars whose OHLC / volume changed between t0 and t2 · signed median close deviation and |median|, |p95| in bps versus the **median of the other venues in the same group** (a consensus for comparison, *not* ground truth) · return correlation with the Kraken series at lag 0.

| Venue | bars | miss | dup | order | zero-vol | flat | revised (OHLC/vol) | dev bps (signed) | |dev| med | |dev| p95 | ret corr@0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OKX BTC-USDT | 240/240 | 0 | 0 | desc | 0 | 0 | 0/0 | 0.34 | 0.44 | 1.31 | 0.986 |
| KuCoin BTC-USDT | 240/240 | 0 | 0 | desc | 0 | 0 | 0/0 | -0.02 | 0.76 | 1.82 | 0.944 |
| Gate BTC_USDT | 240/240 | 0 | 0 | asc | 0 | 0 | 0/0 | 0.12 | 0.37 | 1.09 | 0.988 |
| Bitget BTCUSDT | 239/240 | 1 | 0 | asc | 0 | 0 | 0/0 | 0.87 | 0.87 | 2.19 | 0.983 |
| MEXC BTCUSDT | 240/240 | 0 | 0 | asc | 0 | 0 | 0/0 | -1.32 | 1.32 | 2.67 | 0.968 |
| HTX btcusdt | 240/240 | 0 | 0 | desc | 2 | 8 | 0/0 | -4.54 | 4.54 | 6.37 | 0.933 |
| Binance mirror BTCUSDT | 240/240 | 0 | 0 | asc | 0 | 0 | 0/0 | 0.5 | 0.51 | 1.49 | 0.983 |
| Kraken XBTUSD | 240/240 | 0 | 0 | asc | 0 | 0 | 0/0 | -0.29 | 0.43 | 1.74 | 1.0 |
| Coinbase BTC-USD | 240/240 | 0 | 0 | desc | 0 | 0 | 0/0 | -0.28 | 0.62 | 1.97 | 0.982 |
| Bitstamp btcusd | 240/240 | 0 | 0 | asc | 0 | 0 | 0/0 | -0.68 | 0.7 | 2.01 | 0.978 |
| Bitfinex tBTCUSD | 240/240 | 0 | 0 | asc | 0 | 1 | 0/0 | 13.24 | 13.24 | 15.41 | 0.937 |
| Gemini btcusd | 240/240 | 0 | 0 | desc | 16 | 23 | 0/0 | 0.08 | 0.88 | 3.52 | 0.787 |
| Binance.US BTCUSDT | 240/240 | 0 | 0 | asc | 112 | 174 | 0/0 | - | - | - | 0.592 |
| OKX BTC-USDT-SWAP (perp) | 240/240 | 0 | 0 | desc | 0 | 0 | 0/0 | -0.83 | 1.02 | 3.18 | 0.986 |
| Hyperliquid BTC (perp) | 240/240 | 0 | 0 | asc | 0 | 0 | 0/0 | -0.57 | 0.86 | 2.97 | 0.974 |
| Deribit BTC-PERPETUAL | 240/240 | 0 | 0 | asc | 0 | 0 | 0/0 | 2.2 | 2.2 | 3.69 | 0.969 |
| dYdX BTC-USD (perp) | 240/240 | 0 | 0 | desc | 150 | 202 | 0/0 | -0.4 | 2.74 | 9.29 | 0.428 |
| BitMEX XBTUSD | 0/240 | 240 | 0 | asc | 0 | 0 | 0/0 | - | - | - | - |

Groups for consensus: USD spot (Kraken, Coinbase, Bitstamp, Bitfinex, Gemini), USDT spot (OKX, KuCoin, Gate, Bitget, MEXC, HTX, Binance mirror), perp (OKX, Hyperliquid, Deribit, dYdX). Binance.US is not in a consensus group (too thin). BitMEX XBTUSD returned 0 rows: instrument state `Settled` (OBSERVED in `/instrument`).

## Observations
* **Missing intervals.** Only Bitget shows a real gap: minute 2026-09-29T09:02Z absent in both fetches while OKX, MEXC, Kraken carry trades in it (OBSERVED). All "0 missing" for Gemini, Binance.US, dYdX, HTX are gap-filled flat zero-volume bars, not observed trades.
* **Late arrivals / revisions.** 0 bars appeared late and 0 bars were revised for any venue between t0 and t2 (6 min). The bar closed <60 s before t0 was identical at t2 for every venue. This does not exclude revisions on longer horizons (NOT TESTED).
* **Forming bar.** Kraken returned 3 rows at/after the window end (forming bar included, unflagged). OKX and Gate flag closed bars (`confirm`, closed-flag); other venues do not.
* **Pagination/limits.** OKX 100 rows/call (3 calls for 240 bars) and Coinbase 300/call; Bitstamp ignored the start/end window in one call and returned 1000 rows; Gemini returns a fixed ~1440-bar block without range parameters.
* **Quote-currency effect.** USDT-quoted venues sit ≈3–5 bps from USD venues in the same minute; that is a quote-asset basis, not a data fault.
* **Outliers.** Bitfinex ≈ +13 bps above USD peers (persisting through 3 fetches, timing ruled out by lag test); HTX ≈ −4.5 bps within its USDT group; MEXC −1.3 bps. Causes UNKNOWN.

## Bulk historical
Binance Vision spot BTCUSDT 1m daily file 2026-09-26: 1440 rows, 0 duplicates, 0 missing, SHA-256 matches published `.CHECKSUM` (PROVEN), and 1440/1440 bars identical to `data-api.binance.vision` klines for the same day after unit conversion. **Timestamp unit hazard:** 2024-12 monthly file = 13-digit ms, 2025-01 monthly = 16-digit µs, 2026 daily = 16-digit µs (OBSERVED). Futures um klines remain ms. Oldest spot file observed: 2017-08 (21,360 rows).

## MTF bars
Every source above serves 1m natively; coarser bars are also native on the exchange APIs (OKX `bar=`, Kraken `interval=`, Coinbase `granularity`, Hyperliquid `interval`, Binance klines). Only 1m equivalence and 1h/1d samples were executed (1h on the gold-proxy venues; daily on FX). Consistency of native MTF bars versus resampled 1m bars: NOT TESTED.
