# 05 — Empirical public-data experiment

Only free, public, unauthenticated data. No AurumShift data. All raw captures for the live part are committed under `bench/execution_cost_v1/data/live` and `data/deep`; Binance Vision zips are re-downloadable (`analysis/fetch_vision.sh`).

## 1. Sources and roles (as fixed by the study brief)

| Source | Role | What was pulled |
|---|---|---|
| OKX (spot BTC/ETH/SOL-USDT + BTC/ETH-USDT-SWAP) | primary live microstructure | REST L2 (25 levels; 400 in the deep run), recent trades with taker side, funding (current + history), mark price |
| Coinbase Exchange (BTC/ETH/SOL-USD) | independent spot cross-check | REST L2 (25/400 levels of the aggregated book), trades (side = maker side), ticker |
| Kraken (XBT/ETH/SOL-USD) | second independent spot cross-check | REST depth (25/400), trades with taker side |
| Binance Vision (data.binance.vision) | historical calibration/reference **only** (not live execution evidence) | spot aggTrades BTC 2026-09-20…23, ETH 09-21/22; 1-minute klines BTC Jun–Aug, ETH Aug; USD-M funding history May–Aug (BTC/ETH); USD-M bookDepth 2026-09-20 |
| Yahoo chart endpoint (unofficial) | FX/gold/WTI OHLC **only for volatility/gap scaling** | 1-hour OHLC, 6 months: GC=F, EURUSD, USDJPY, CL=F, BTC-USD control |

Binance's live API (HTTP 451) and Bybit's (403) were not reachable from the sandbox; they were not used. HFT-grade feeds (WebSocket L3) were not captured: REST polling every ≈ 2.0–2.6 s, 3 threads (one per venue), round-trip time recorded per request.

Live run: 2026-09-29 ≈ 13:01–13:51 UTC (≈ 50 min, ≈ 1 264–1 498 book snapshots per series; ≈ 2 800–20 800 trades per series) plus an 8-minute 400-level "deep" run right after. Everything is one time window on one day.

| venue | asset | n_snap | dur_min | rtt_ms_p50 | gap_s_p50 | tick_bps | spread_mean | spread_p95 | one_tick_frac | vis_depth_bps | beta | sigma | n_trades |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| okx | BTC | 1264 | 49.979 | 278.337 | 2.485 | 0.012 | 0.012 | 0.012 | 1.000 | 1.771 | 0.310 | 0.773 | 18050 |
| okx | ETH | 1264 | 49.974 | 274.955 | 2.494 | 0.037 | 0.037 | 0.037 | 1.000 | 2.502 | 0.407 | 1.009 | 12214 |
| okx | SOL | 1264 | 49.974 | 278.188 | 2.500 | 0.826 | 0.826 | 0.828 | 1.000 | 20.232 | 0.438 | 1.355 | 18112 |
| coinbase | BTC | 1498 | 49.997 | 165.862 | 2.001 | 0.001 | 0.069 | 0.466 | 0.810 | 2.138 | 0.632 | 0.818 | 20793 |
| coinbase | ETH | 1498 | 49.997 | 75.753 | 2.002 | 0.037 | 0.287 | 0.953 | 0.439 | 3.063 | 0.552 | 1.024 | 8879 |
| coinbase | SOL | 1498 | 49.997 | 75.709 | 2.004 | 0.826 | 1.151 | 1.656 | 0.641 | 20.634 | 0.661 | 1.396 | 9656 |
| kraken | BTC | 1483 | 49.984 | 163.810 | 2.001 | 0.012 | 0.038 | 0.012 | 0.950 | 2.475 | 0.576 | 0.754 | 7914 |
| kraken | ETH | 1483 | 49.981 | 161.043 | 2.001 | 0.037 | 0.191 | 1.029 | 0.805 | 3.601 | 0.619 | 0.937 | 3352 |
| kraken | SOL | 1483 | 49.981 | 162.334 | 2.004 | 0.826 | 0.942 | 1.653 | 0.877 | 20.281 | 0.731 | 1.407 | 2801 |

(`beta` = median exponent of the cumulative-depth curve `C(x) ∝ x^β` fitted on the visible levels; `sigma` in bps/√s from snapshot mids; `vis_depth_bps` = median distance covered by the visible ask levels.)

## 2. What the data look like (OBSERVED)

* **Book depth (ask side, USD available within x bps of the touch)** — the top 25 levels only reach 1.8–3.6 bps on BTC/ETH (≈ 20 bps on SOL):

| venue | asset | USD<= 1bps | USD<= 2bps | USD<= 5bps | USD<= 10bps |
|---|---|---|---|---|---|
| okx | BTC | 186,851 | 403,751 | 421,468 | 421,468 |
| okx | ETH | 64,969 | 223,773 | 359,584 | 359,584 |
| okx | SOL | 21,454 | 34,240 | 108,464 | 235,956 |
| coinbase | BTC | 122,811 | 394,971 | 483,458 | 483,458 |
| coinbase | ETH | 25,056 | 108,793 | 245,183 | 245,183 |
| coinbase | SOL | 8,017 | 19,294 | 54,105 | 162,124 |
| kraken | BTC | 765,212 | 1,033,909 | 1,303,705 | 1,304,033 |
| kraken | ETH | 17,264 | 171,891 | 586,877 | 596,213 |
| kraken | SOL | 14,200 | 22,346 | 147,341 | 634,042 |

* The visible cumulative-depth curve is **concave** in distance (β ≈ 0.3–0.7 near the touch), not the convex β ≈ 1.5 that generates a square-root cost in the synthetic base book. Beyond the visible window the shape is UNKNOWN from these snapshots; the Binance USD-M `bookDepth` file (bands ±0.2 … ±5 %, far book) has a log-log slope of 0.81 between 20 and 500 bps for BTCUSDT on 2026-09-20 (`results/empirical_vision.json`), i.e. sub-linear in the far book too.
* **Vol ↔ liquidity coupling** (Spearman between trailing 30-snapshot realised vol and quoted spread / walk cost), positive in all 9 series for the spread (0.26–0.78) and mostly positive for the walk cost — the world where cost scales with vol is not a modelling artefact:

| venue | asset | rho(spread) | rho(walk_1e4) | rho(walk_1e5) |
|---|---|---|---|---|
| okx | BTC | 0.78 | 0.54 | 0.15 |
| okx | ETH | 0.58 | 0.31 | 0.32 |
| okx | SOL | 0.36 | 0.04 | -0.06 |
| coinbase | BTC | 0.65 | 0.21 | 0.21 |
| coinbase | ETH | 0.26 | 0.29 | 0.35 |
| coinbase | SOL | 0.38 | 0.06 | 0.39 |
| kraken | BTC | 0.74 | 0.52 | 0.21 |
| kraken | ETH | 0.53 | 0.54 | 0.56 |
| kraken | SOL | 0.36 | 0.21 | 0.09 |

## 3. Deep run (400 visible levels)

| venue | asset | n_snap | vis_depth_bps | levels | beta_p10 | beta_med | beta_p90 |
|---|---|---|---|---|---|---|---|
| okx | BTC | 192 | 12.89 | 400 | 0.82 | 1.00 | 1.35 |
| okx | ETH | 192 | 26.48 | 400 | 0.98 | 1.17 | 1.32 |
| okx | SOL | 192 | 328.93 | 400 | 0.67 | 0.71 | 0.78 |
| coinbase | BTC | 240 | 70.72 | 400 | 1.00 | 1.10 | 1.25 |
| coinbase | ETH | 240 | 104.07 | 400 | 0.71 | 1.03 | 1.13 |
| coinbase | SOL | 240 | 375.15 | 400 | 0.71 | 0.77 | 0.91 |
| kraken | BTC | 240 | 83.83 | 400 | 0.65 | 0.77 | 1.08 |
| kraken | ETH | 240 | 188.29 | 400 | 0.78 | 0.87 | 1.05 |
| kraken | SOL | 240 | 614.23 | 400 | 0.58 | 0.62 | 0.72 |

Book-walk cost (bps vs mid) at larger notionals once more depth is visible, and the fraction of snapshots whose visible depth covers the notional:

| venue | asset | 1000 | 10000 | 100000 | 300000 | 1000000 | 3000000 |
|---|---|---|---|---|---|---|---|
| coinbase | BTC | 0.10 | 0.20 | 0.77 | 1.32 | 2.30 | 6.14 |
| coinbase | ETH | 0.22 | 0.41 | 1.46 | 2.31 | 5.12 | 12.76 |
| coinbase | SOL | 0.70 | 1.08 | 3.95 | 7.47 | 15.21 | 32.96 |
| kraken | BTC | 0.04 | 0.10 | 0.29 | 0.41 | 1.09 | 3.23 |
| kraken | ETH | 0.24 | 0.65 | 1.63 | 2.49 | 4.00 | 7.15 |
| kraken | SOL | 0.73 | 0.99 | 3.62 | 5.72 | 9.98 | 20.10 |
| okx | BTC | 0.01 | 0.05 | 0.33 | 1.06 | 2.46 | 5.25 |
| okx | ETH | 0.03 | 0.08 | 1.15 | 2.22 | 4.00 | 7.84 |
| okx | SOL | 0.47 | 0.63 | 2.67 | 6.37 | 17.62 | 60.63 |

| venue | asset | 1000 | 10000 | 100000 | 300000 | 1000000 | 3000000 |
|---|---|---|---|---|---|---|---|
| coinbase | BTC | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| coinbase | ETH | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| coinbase | SOL | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| kraken | BTC | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| kraken | ETH | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| kraken | SOL | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| okx | BTC | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.98 |
| okx | ETH | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| okx | SOL | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

## 4. Which models are calibratable from free data?

| Model / quantity | Fields required | Result in this study |
|---|---|---|
| Quoted spread distribution | L1 | **Calibrated** (`06`). Snapshot-based, 2 s cadence |
| Effective / realised spread | quote at trade time + aggressor | **Not from polled snapshots**: dominated by staleness noise (`06` §2). A message-rate feed was not tested → `MODEL_NOT_CALIBRATABLE_FROM_FREE_DATA` for REST polling; UNKNOWN for WebSocket |
| Trade-flip spread | aggressor flag + fine timestamps | **Calibrated** on Binance Vision (median = 1 tick) |
| OHLC proxies (Roll, CS, AR, EDGE) | OHLC | Falsified as quote substitutes; EDGE usable as bound on long samples (`06`) |
| Book-walk slippage | L2 snapshot | **Measurable** within the visible window; near-unbiased vs the next snapshot (median |bias| ≤ 3.3 % of cost), MAE 0.13–0.8 bps for ≤ 100k USD (`07`); **realised** slippage unmeasurable without own fills |
| Fixed / spread-prop / sqrt constants | costs + σ + V_day | Fit trivially in-sample; **transport poorly** across venue-assets (`07` §3, LOO) |
| Propagator / Almgren–Chriss impact | metaorder-tagged fills | `MODEL_NOT_CALIBRATABLE_FROM_FREE_DATA`. Only aggregate 1/5-min flow-return regressions on Binance tape (`07` §4) |
| Fill probability (point) | own order lifecycle / L3 | **Bounds only**: bracket 0.07–0.44 wide (`08`) |
| Queue-reactive / Cont–Stoikov–Talreja | L3 events, queue intensities | `MODEL_NOT_CALIBRATABLE_FROM_FREE_DATA` |
| Adverse selection (markout) | tape + mids | **Measured** (0.3–1.4 bps at 30 s, CI excludes 0 in 16/18) (`10`) |
| Kyle λ (aggregate) | signed volume + returns | Measured on Binance (2.3–6.6 bps per 1M USD/min, R² 0.2–0.34) (`07`) |
| Latency drift | mids/tape | **Measured**, follows σ√L ±15 % at ≥ 4 s (`10`) |
| Perp funding | funding history | **Calibrated** (4 months, 2 venues) (`09`) |
| Short borrow | rate history + tier | `UNKNOWN` (only a venue base rate; unit unverified) |
| Futures roll | curve | **Measured** (OKX BTC-USD dated curve snapshot) |
| FX / gold / commodities quotes, books, fills | quotes, books | `MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA` — see §6 |

## 5. Cross-venue view (fragmentation in the data)

OKX quotes USDT, Coinbase/Kraken USD; for OKX pairs the mean mid difference (1.7–2.7 bps, the USDT/USD basis) was removed. Mid difference sd is 0.9–1.5 bps for BTC/ETH/SOL versus a quoted spread of 0.01–1 bps, so **the best venue changes from snapshot to snapshot at the bps level**; `frac_crossed` is high because the mid dispersion exceeds the spread — with 1.5–3 s of snapshot skew this is **not** an arbitrage signal and is not evidence of tradable edge (fees dominate):

| asset | pair | n | mid_diff_bps_mean | mid_diff_bps_sd | basis_removed | frac_crossed_after_basis | p99_cross_edge_bps |
|---|---|---|---|---|---|---|---|
| BTC | okx-coinbase | 1224 | 2.643 | 0.902 | True | 0.962 | 2.947 |
| BTC | okx-kraken | 1221 | 2.469 | 0.855 | True | 0.973 | 2.906 |
| BTC | coinbase-kraken | 1257 | -0.176 | 0.939 | False | 0.947 | 3.330 |
| ETH | okx-coinbase | 1225 | 2.231 | 0.986 | True | 0.844 | 3.247 |
| ETH | okx-kraken | 1217 | 2.692 | 1.009 | True | 0.918 | 2.924 |
| ETH | coinbase-kraken | 1251 | 0.460 | 1.101 | False | 0.832 | 3.395 |
| SOL | okx-coinbase | 1226 | 1.691 | 1.338 | True | 0.364 | 3.905 |
| SOL | okx-kraken | 1217 | 1.827 | 1.308 | True | 0.371 | 3.477 |
| SOL | coinbase-kraken | 1251 | 0.128 | 1.529 | False | 0.227 | 4.137 |

Per-venue walk costs differ by ×1.7–1.9 across venues for the same asset and size (100k USD: BTC 0.34–0.61 bps, ETH 0.78–1.45, SOL 3.1–5.2, `07`), so **which book a PAPER models** is a first-order choice.

## 6. FX, gold, commodities: policy and what was done

Free reliable L1/L2 are **not available** for these classes in this study, so quote/book-dependent models are `MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA` and were **not** validated (no order-book-walk, no spread/fill/queue calibration from OHLCV). Only public 1-hour OHLC was used to scale volatility, look at session gaps and bound latency effects:

| instrument | bars | hours_per_week | sigma_bps_per_sqrt_s | ann_vol_pct | gaps_gt3h | mean_abs_gap_bps | gap_over_sigma_hour | sd_bps_at_L_2s | sd_bps_at_L_10s | CS_1h_bps | AR_1h_bps | volume |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| XAU (COMEX GC=F futures) | 2912 | 104.00 | 0.52 | 24.31 | 27 | 53.99 | 1.73 | 0.74 | 1.65 | 11.88 | 8.72 | True |
| EURUSD | 3127 | 111.68 | 0.11 | 5.03 | 26 | 11.51 | 1.78 | 0.15 | 0.34 | 1.93 | 1.49 | False |
| USDJPY | 3110 | 111.07 | 0.16 | 7.68 | 26 | 10.99 | 1.11 | 0.23 | 0.52 | 2.97 | 0.00 | False |
| WTI (CL=F futures) | 2908 | 103.86 | 1.25 | 58.40 | 26 | 250.18 | 3.33 | 1.77 | 3.96 | 27.68 | 21.45 | True |
| BTC-USD (control) | 4417 | 157.75 | 0.69 | 38.80 | 0 | n/a | n/a | 0.98 | 2.18 | 12.69 | 1.87 | True |

Observations: (i) σ per √s is 0.11 (EURUSD), 0.16 (USDJPY), 0.52 (gold futures), 1.25 (WTI) bps vs 0.69 for BTC-USD in the same window, so the synthetic base σ = 0.9 is BTC-like, not FX-like; the 2-second latency band is ≈ 0.15–0.7 bps for FX/gold vs ~1 bp for BTC. (ii) These markets are **not 24/7**: 104–112 bars/week present vs 158 for BTC (one hour bars, 168 possible), with 26–27 session gaps > 3 h in 6 months whose mean |gap| is 1.1–3.3 hourly σ — the `gap` scenario is the relevant stress for them, and Corwin–Schultz/AR "spreads" of 0–28 bps on these bars are almost entirely volatility and cannot be checked without quotes. (iii) The WTI series is a continuous-contract series; roll effects contaminate its gap statistics (INFERENCE).

## 7. Reproduce

```
python3 analysis/empirical_live.py data/live live && python3 analysis/empirical_live.py data/deep deep
python3 analysis/transport_loo.py live && python3 analysis/transport_loo.py deep
python3 analysis/empirical_vision.py && python3 analysis/funding_borrow_roll.py && python3 analysis/fx_gold_ohlc.py
```
