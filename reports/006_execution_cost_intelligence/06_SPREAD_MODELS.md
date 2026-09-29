# 06 — Spread models: quoted vs effective vs realized vs OHLC vs trade-based

Question: which spread measures are usable for a non-HFT cost layer, and where does each break? Candle-based estimators are **not** assumed equivalent to quotes; they are falsified against quotes wherever quotes exist (crypto), and against a synthetic truth elsewhere.

Evidence: (1) live public L2 + trades, ≈ 50 min, OKX/Coinbase/Kraken × BTC/ETH/SOL (1 264–1 498 snapshots per series, `05`); (2) Binance Vision aggTrades (BTC 4 days, ETH 2 days) and 1-minute klines (BTC 3 months, ETH 1 month); (3) synthetic OHLC with known spread (`synthetic/run_synth.py::exp_spread_estimators`); (4) OSS `bidask` (EDGE).

## 1. Quoted spread (L1) — the reference

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

* All three venues quote BTC/ETH at (nearly) **one tick** most of the time (`one_tick_frac` 0.44–1.0) and the tick itself is 0.001–0.04 bps for BTC/ETH: the half-spread of BTC is **≈ 0.006 bps** on OKX/Kraken, i.e. **≈ 50–750× smaller than the 4–30 s one-sigma mid drift** (`10`; ratio depends on venue). For tick-bound majors the spread is a rounding error next to timing and depth; for SOL (≈ 1 tick = 0.83 bps) it is a real cost.
* Coinbase quotes are wider/more variable than OKX (BTC mean 0.069 bps, p95 0.47 bps; ETH 0.29, p95 0.95): OBSERVED intermittent widening. Mean ≠ typical: use the distribution, not only the mean.
* Sampling: REST polling every 2.0–2.6 s with 76–278 ms round trips means the "quote" is an unsynchronised snapshot. For a cost layer this is fine (spread is persistent); it is not fine for effective/realized spread (below).

## 2. Effective and realized spread from polled snapshots — where it breaks

| venue | asset | quoted_mean | effective_mean | effective_median | realized_5s | realized_30s | side_flag_agree |
|---|---|---|---|---|---|---|---|
| okx | BTC | 0.012 | 0.660 | 0.012 | -1.242 | -0.752 | 0.805 |
| okx | ETH | 0.037 | 1.267 | 0.475 | -0.760 | -0.485 | 0.811 |
| okx | SOL | 0.826 | 1.478 | 0.827 | -1.143 | 0.127 | 0.748 |
| coinbase | BTC | 0.069 | 0.390 | 0.001 | -0.661 | -0.369 | 0.330 |
| coinbase | ETH | 0.287 | 1.509 | 0.587 | -0.872 | -0.670 | 0.308 |
| coinbase | SOL | 1.151 | 1.950 | 0.827 | -0.315 | 0.169 | 0.247 |
| kraken | BTC | 0.038 | 1.294 | 0.606 | -1.317 | -0.755 | 0.850 |
| kraken | ETH | 0.191 | 1.432 | 0.623 | -1.230 | 0.100 | 0.787 |
| kraken | SOL | 0.942 | 1.766 | 0.826 | 0.112 | -0.358 | 0.704 |

* Mean **effective** spread (2·|px − mid|) is **0.4–1.9 bps** vs quoted 0.01–1.15: on tick-bound BTC it is 6–55× too high; the **median** recovers the quote for OKX/Coinbase BTC (0.012 / 0.001 bps) but not for Kraken.
* Cause (INFERENCE, consistent with the numbers): the "mid" is a snapshot 1–1.5 s stale on average; with σ ≈ 0.8 bps/√s the expected staleness error is `σ√age·√(2/π) ≈ 0.7 bps`, which matches the OKX BTC mean (0.66). **Effective spread measured against polled snapshots is a staleness meter when the true spread ≪ σ√age.** It needs a message-rate L1 stream (not available from the REST snapshots used here) to be meaningful.
* **Realized** spread (2·side·(px − mid_{t+h})) is negative at h = 5 s in 8 of 9 series (−0.3 … −1.3 bps): consistent with adverse selection / flow momentum (OBSERVED; the Binance tape shows +0.6–1.8 bps continuation after top-quartile signed flow, `10`), but the same staleness noise contaminates it. Its sign, not its magnitude, is the usable information. A taker cost layer should not use realized spread as cost (it measures the maker's P&L).
* Trade side: the venue flag agreed with the quote rule in 75–85 % (OKX, Kraken) and only 25–33 % for Coinbase (flag = maker side; used inverted). The residual disagreement is dominated by the same staleness.

## 3. Trade-based estimator (no quotes needed): consecutive opposite-aggressor prints

Binance Vision aggTrades carry the aggressor flag. Taking consecutive prints < 5 ms apart with opposite aggressor, the price difference is a direct read of the prevailing spread:

| sym | days | agg_trades | V_day_usd_bn | tick_bps | flip_spread_median_bps | flip_spread_mean_bps | flip_frac_zero |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 4 | 4316070 | 1.8280 | 0.0012 | 0.0012 | 0.0473 | 0.0935 |
| ETHUSDT | 2 | 2383021 | 1.1961 | 0.0365 | 0.0365 | 0.1381 | 0.1560 |

The **median equals one tick exactly** (0.0012 bps BTC, 0.0365 bps ETH); the mean is 0.05–0.14 bps because of episodes of wider spreads (and 9–16 % zero differences). OBSERVED. This is the cleanest *quote-free* spread read available from free data — but it requires an aggressor flag and sub-ms timestamps; it does not exist for FX/gold/commodities (`14`).

## 4. OHLC proxies vs quotes — falsified as equivalents

Live 1-minute trade-built bars (≈ 51–75 bars per series) against the quoted spread of the same capture:

| venue | asset | n_bars | corwin_schultz | cs_negative_frac | abdi_ranaldo | roll | hl_range_proxy | quoted_spread_mean_bps | effective_spread_mean_bps |
|---|---|---|---|---|---|---|---|---|---|
| okx | BTC | 51 | 2.127 | 0.440 | 1.979 | 4.386 | 3.406 | 0.012 | 0.660 |
| okx | ETH | 51 | 3.027 | 0.320 | 4.503 | 7.231 | 4.693 | 0.037 | 1.267 |
| okx | SOL | 51 | 4.942 | 0.360 | 4.507 | 8.921 | 7.018 | 0.826 | 1.478 |
| coinbase | BTC | 51 | 2.300 | 0.420 | 2.277 | 4.593 | 3.813 | 0.069 | 0.390 |
| coinbase | ETH | 52 | 2.962 | 0.314 | 3.580 | 6.079 | 4.641 | 0.287 | 1.509 |
| coinbase | SOL | 51 | 5.051 | 0.340 | 4.312 | 8.756 | 7.019 | 1.151 | 1.950 |
| kraken | BTC | 60 | 1.960 | 0.424 | 1.680 | 4.566 | 3.121 | 0.038 | 1.294 |
| kraken | ETH | 70 | 1.898 | 0.464 | 2.734 | 6.065 | 3.699 | 0.191 | 1.432 |
| kraken | SOL | 75 | 3.216 | 0.419 | 3.591 | 9.205 | 5.794 | 0.942 | 1.766 |

Binance klines, 1-minute, daily estimates averaged over 30/31 days (tick 0.0012 bps BTC, 0.037 bps ETH; trade-flip median = 1 tick):

| sym | file | days | corwin_schultz_bps_mean | abdi_ranaldo | roll | hl_range |
|---|---|---|---|---|---|---|
| BTCUSDT | BTCUSDT_1m_2026-06 | 30 | 1.516 | 0.414 | 1.339 | 2.992 |
| BTCUSDT | BTCUSDT_1m_2026-07 | 31 | 0.837 | 0.296 | 1.091 | 1.740 |
| BTCUSDT | BTCUSDT_1m_2026-08 | 31 | 0.781 | 0.090 | 0.701 | 1.573 |
| ETHUSDT | ETHUSDT_1m_2026-08 | 31 | 1.254 | 0.124 | 1.083 | 2.379 |

Synthetic OHLC with known spread (mean over 250 one-minute bars × seeds; `tick` = quote grid 1 bp):

| spread | sigma | tick | eff_spread_truth | roll | corwin_schultz | abdi_ranaldo | hl_range_proxy |
|---|---|---|---|---|---|---|---|
| 0.20 | 0.30 | 1bp | 0.52 | 0.48 | 1.18 | 0.32 | 2.50 |
| 0.20 | 0.30 | none | 0.20 | 0.46 | 1.14 | 0.08 | 2.46 |
| 0.20 | 0.90 | 1bp | 0.52 | 0.92 | 3.73 | 0.28 | 8.28 |
| 0.20 | 0.90 | none | 0.20 | 0.69 | 3.79 | 0.00 | 8.23 |
| 0.20 | 2.70 | 1bp | 0.52 | 0.00 | 12.42 | 0.00 | 22.52 |
| 0.20 | 2.70 | none | 0.20 | 0.00 | 12.37 | 0.00 | 22.46 |
| 1.00 | 0.30 | 1bp | 0.99 | 0.78 | 1.55 | 0.97 | 2.99 |
| 1.00 | 0.30 | none | 1.00 | 1.22 | 1.50 | 0.94 | 2.82 |
| 1.00 | 0.90 | 1bp | 1.00 | 4.35 | 4.12 | 3.37 | 7.73 |
| 1.00 | 0.90 | none | 1.00 | 4.35 | 4.10 | 3.16 | 7.66 |
| 1.00 | 2.70 | 1bp | 1.00 | 24.63 | 13.72 | 15.85 | 22.16 |
| 1.00 | 2.70 | none | 1.00 | 24.64 | 13.70 | 15.75 | 22.20 |
| 5.00 | 0.30 | 1bp | 5.00 | 5.10 | 4.71 | 4.86 | 4.63 |
| 5.00 | 0.30 | none | 5.00 | 5.19 | 4.65 | 4.86 | 4.58 |
| 5.00 | 0.90 | 1bp | 4.99 | 6.27 | 6.84 | 2.41 | 9.72 |
| 5.00 | 0.90 | none | 5.00 | 6.19 | 6.89 | 2.41 | 9.65 |
| 5.00 | 2.70 | 1bp | 5.00 | 7.20 | 13.25 | 3.63 | 22.83 |
| 5.00 | 2.70 | none | 5.00 | 7.12 | 13.27 | 3.69 | 22.81 |
| 20.00 | 0.30 | 1bp | 20.00 | 21.02 | 18.87 | 19.83 | 12.53 |
| 20.00 | 0.30 | none | 20.00 | 20.98 | 18.81 | 19.78 | 12.51 |
| 20.00 | 0.90 | 1bp | 20.00 | 20.43 | 17.80 | 19.59 | 16.87 |
| 20.00 | 0.90 | none | 20.00 | 20.34 | 17.70 | 19.52 | 17.01 |
| 20.00 | 2.70 | 1bp | 19.99 | 27.72 | 23.78 | 18.06 | 30.92 |
| 20.00 | 2.70 | none | 20.00 | 27.64 | 23.72 | 17.98 | 30.73 |

OSS EDGE (`bidask`) on the same synthetic grid and on real data:

| spread | sigma | tick | eff_truth | edge_bps |
|---|---|---|---|---|
| 0.20 | 0.30 | 1bp | 0.52 | 0.96 |
| 0.20 | 0.30 | none | 0.20 | 0.53 |
| 0.20 | 0.90 | 1bp | 0.53 | 1.33 |
| 0.20 | 0.90 | none | 0.20 | 1.10 |
| 0.20 | 2.70 | 1bp | 0.52 | 2.69 |
| 0.20 | 2.70 | none | 0.20 | 2.27 |
| 1.00 | 0.30 | 1bp | 1.00 | 1.28 |
| 1.00 | 0.30 | none | 1.00 | 1.01 |
| 1.00 | 0.90 | 1bp | 0.99 | 1.44 |
| 1.00 | 0.90 | none | 1.00 | 1.37 |
| 1.00 | 2.70 | 1bp | 1.00 | 3.08 |
| 1.00 | 2.70 | none | 1.00 | 2.88 |
| 5.00 | 0.30 | 1bp | 5.00 | 5.16 |
| 5.00 | 0.30 | none | 5.00 | 5.02 |
| 5.00 | 0.90 | 1bp | 4.99 | 5.04 |
| 5.00 | 0.90 | none | 5.00 | 4.97 |
| 5.00 | 2.70 | 1bp | 5.01 | 5.99 |
| 5.00 | 2.70 | none | 5.00 | 5.91 |
| 20.00 | 0.30 | 1bp | 20.01 | 21.85 |
| 20.00 | 0.30 | none | 20.00 | 20.93 |
| 20.00 | 0.90 | 1bp | 20.00 | 20.87 |
| 20.00 | 0.90 | none | 20.00 | 20.50 |
| 20.00 | 2.70 | 1bp | 19.99 | 21.92 |
| 20.00 | 2.70 | none | 20.00 | 21.84 |

| index | days | edge_bps_mean | nan_days |
|---|---|---|---|
| klines_BTCUSDT_1m_2026-06.zip | 30.00 | 0.10 | 0.00 |
| klines_BTCUSDT_1m_2026-07.zip | 31.00 | 0.06 | 0.00 |
| klines_BTCUSDT_1m_2026-08.zip | 31.00 | 0.07 | 0.00 |
| klines_ETHUSDT_1m_2026-08.zip | 31.00 | 0.18 | 0.00 |

EDGE on the ≈ 50 live trade bars (noisy; shown for completeness):

| index | n_bars | edge_bps | quoted_spread_mean_bps |
|---|---|---|---|
| okx-BTC-60s | 51 | 0.98 | 0.01 |
| okx-BTC-30s | 101 | 0.39 | 0.01 |
| okx-ETH-60s | 51 | 1.06 | 0.04 |
| okx-ETH-30s | 101 | 0.45 | 0.04 |
| okx-SOL-60s | 51 | 1.30 | 0.83 |
| okx-SOL-30s | 101 | 0.44 | 0.83 |
| coinbase-BTC-60s | 51 | 0.09 | 0.07 |
| coinbase-BTC-30s | 101 | 0.47 | 0.07 |
| coinbase-ETH-60s | 52 | 1.44 | 0.29 |
| coinbase-ETH-30s | 103 | 0.71 | 0.29 |
| coinbase-SOL-60s | 51 | 1.03 | 1.15 |
| coinbase-SOL-30s | 102 | 0.92 | 1.15 |
| kraken-BTC-60s | 60 | 0.62 | 0.04 |
| kraken-BTC-30s | 119 | 0.65 | 0.04 |
| kraken-ETH-60s | 70 | 0.18 | 0.19 |
| kraken-ETH-30s | 140 | 1.36 | 0.19 |
| kraken-SOL-60s | 75 | 2.67 | 0.94 |
| kraken-SOL-30s | 150 | 1.14 | 0.94 |

### Where each estimator breaks (all OBSERVED here)

| Estimator | Needs | Breaks when | Evidence |
|---|---|---|---|
| Quoted spread (L1) | L1 stream | staleness of the snapshot; intermittent widening (use distribution) | live table §1 |
| Effective spread | quote at trade time + aggressor | true spread ≪ σ√staleness (polled snapshots) | §2: 6–55× too high on BTC |
| Realized spread | + horizon | always mixes cost with adverse selection; negative for takers' counterparties | §2 |
| Roll (1984) | serial covariance of trade prices | flow autocorrelation, large ticks/vol: reads 4.4–9.2 bps live (quoted ≤ 1.2), 0.7–1.3 bps on Binance BTC | §4 |
| Corwin–Schultz (2012) | H/L bars | dominated by volatility: synthetic 0.2 bps spread → 1.2/3.8/12.4 bps at σ = 0.3/0.9/2.7; 31–46 % of bar-pairs floor at 0 live; real BTC 0.8–1.5 bps vs tick-bound truth ~0.001 | synthetic, live, Vision |
| Abdi–Ranaldo (2017) | C/H/L | better than CS at low σ, collapses to 0 at high σ (synthetic 0.2 bps, σ = 2.7 → 0.00); live 1.7–4.5 bps | synthetic, live |
| H/L range × ½ | H/L | is a volatility measure, not a spread | 3.1–7.0 bps live |
| EDGE (Ardia et al. 2024, OSS `bidask`) | OHLC, long sample | true spread ≲ 1 tick with high σ (0.2 → 0.75–2.5 bps synthetic); < 100 bars (live: 0.09–2.7 bps, unstable) | synthetic, live, Vision 0.06–0.18 |
| Trade-flip | aggressor flag + µs timestamps | no flag / coarse timestamps | Vision |

## 5. Verdict (reference only)

* `SPREAD_REFERENCE = quoted L1 spread (distribution, with staleness age)` when quotes exist; effective spread only from a message-rate L1+trades feed; OHLCV-only ⇒ `EDGE` as an **upper-bound sanity band on samples ≥ 1 000 bars** (never as a measurement) and otherwise `UNKNOWN`.
* Candle-based Roll / Corwin–Schultz / Abdi–Ranaldo / range proxies: **not supported** as spread substitutes for liquid crypto (2–100× overstated vs quotes) — and there is no free quote data to test them for FX/gold/commodities (`MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA`). On FX/gold/WTI hourly bars they return 1.9–28 bps (`results/fx_gold_ohlc.json`), which cannot be judged without quotes; note that ~all of it is volatility.
