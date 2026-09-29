# 07 — Cross-provider comparison

No source is treated as ground truth. Pairwise statistics: `results/bars_analysis_t2.json` (136 pairs, ≥30 common minutes; n = 233 each). Consensus deviations: `results/consensus_dev.json`. Lag test: `results/lag_test_vs_kraken.json`.

## Timestamps
Best cross-correlation lag versus Kraken is **0 minutes for all 17 series** (OBSERVED) → all providers label 1-minute bars with the same convention (bar-open time) within the resolution tested. Per-provider raw semantics differ in unit and order (ms vs s vs ISO; newest-first vs oldest-first; Binance Vision spot in µs since 2025-01) — see `01`.

## OHLC
* Exact OHLC equality between any two venues in the same minute: **0 occurrences across 31688 pair-minutes** (every pair 0). Venues print different trades.
* Closest pairs (median |close diff|, bps): 

| venue A | venue B | close med | close p95 | high med | low med | exact | ret corr |
|---|---|---|---|---|---|---|---|
| okx_spot_BTCUSDT | gate_BTC_USDT | 0.33 | 1.05 | 0.37 | 0.32 | 0/233 | 0.9852 |
| kraken_spot_XBTUSD | coinbase_BTC-USD | 0.4 | 1.19 | 0.4 | 0.4 | 0/233 | 0.9837 |
| okx_spot_BTCUSDT | binance_dataapi_BTCUSDT | 0.46 | 1.5 | 0.53 | 0.59 | 0/233 | 0.9833 |
| gate_BTC_USDT | binance_dataapi_BTCUSDT | 0.46 | 1.4 | 0.41 | 0.47 | 0/233 | 0.9861 |
| kraken_spot_XBTUSD | bitstamp_btcusd | 0.48 | 1.49 | 0.73 | 0.46 | 0/233 | 0.9777 |
| okx_swap_BTC-USDT-SWAP | hyperliquid_perp_BTC | 0.52 | 1.71 | 0.51 | 0.57 | 0/233 | 0.9712 |
| bitget_BTCUSDT | binance_dataapi_BTCUSDT | 0.53 | 1.75 | 0.73 | 0.47 | 0/233 | 0.9781 |
| okx_spot_BTCUSDT | bitget_BTCUSDT | 0.58 | 1.52 | 0.63 | 0.55 | 0/233 | 0.9836 |

* Quote currency: USDT-vs-USD pairs differ by ≈3–5 bps median (e.g. Kraken vs OKX 3.31 bps signed, OKX − Kraken).
* Spot vs perp: 0.5–5 bps (basis + venue offsets); OKX swap vs Hyperliquid 0.52 bps median.
* Outliers: Bitfinex vs USD peers ≈ 13 bps; HTX ≈ 4.5 bps; dYdX/Binance.US/Gemini low return correlation (0.43/0.59/0.79) because most of their bars are gap-filled or thinly traded.

## Volume
Not comparable: OKX spot base units; OKX swap contracts (ratio to spot ≈ 0.001); Deribit USD notional; dYdX/Hyperliquid base; Gate base; KuCoin base. Within-group base-volume ratios span 0.003×–9× of the group median (consensus table in `02`). Volume from these APIs should be treated as venue-local activity, not as market volume.

## Missing / late / revised
See `02`: 1 real missing minute (Bitget), gap-filling on four venues, 0 late arrivals, 0 revisions in 6 minutes on 17 series; futures/funding/OI revision behaviour over longer windows NOT TESTED.

## Cross-source: options, funding, OI, gold, FX
Options IV Deribit vs OKX, funding at 8 h boundaries, OI units: `03`. Gold cross-check: `04`. ECB vs Frankfurter identical (derived); ECB fix vs intraday-close sources within 0.6–0.8 pips (cut-off effect).
