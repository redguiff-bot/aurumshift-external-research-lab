# 07 — Slippage and market impact

## 1. Slippage models compared: assumptions, inputs

| Model | Cost predicted (bps vs arrival mid, fees excluded) | Implicit assumptions | Inputs |
|---|---|---|---|
| Frictionless mid fill (E1) | 0 | executable at mid | – |
| Fixed bps `c` | `c` (default 5, or calibrated) | cost independent of size, spread, volatility, depth, time | – |
| Half-spread only ("zero slippage") | `s/2` | book infinitely deep at the touch | L1 |
| Spread-proportional | `k·s/2` | cost ∝ spread; size-blind | L1 |
| Volatility-scaled | `s/2 + a·σ` | cost ∝ σ (i.e. timing is charged as a positive mean) | L1, σ |
| Size/depth-linear | `s/2 + b·N/D_1bp` | linear walk out of the depth within 1 bp | L1 size + depth within 1 bp |
| Square-root | `s/2 + Y·σ_day·√(N/V_day)` | concave impact; Y transports across instruments | σ_day, V_day (OHLCV), optionally s |
| L2 book walk | `s/2 + VWAP_distance(N)` on the snapshot | static book over the latency window; own order only | L2 snapshot (visible depth ≥ N) |

Assumptions to state explicitly before using any of them: (a) what the reference is (arrival mid), (b) whether spread is inside the model (it is for all but fixed-bps/vol-scaled in a way that double counts if a spread line is added — see §5), (c) whether timing drift is charged with a non-zero mean (vol-scaled does; the walk does not), (d) size regime (validity ≤ visible depth).

## 2. Sensitivity to order size, volatility, depth, latency

**Size** (synthetic, `04` §3; bias by size shown there): frictionless and half-spread models are exact only for tiny orders; all models without a size term are off by 1–30 bps at 1e7 USD; the walk is exact while depth is visible.

**Volatility and depth** (synthetic, 1M USD, ratio of cost relative to the `base` scenario; truth vs model). The truth here has *no* volatility–liquidity coupling, so volatility does not move the mean cost (×1.03) while σ-carrying models (`vol_scaled`, `sqrt`) predict ×2.1: that gap is a property of the synthetic world, **not** a finding about markets — in the live data volatility and spread do move together (`05` §2, Spearman 0.26–0.78), and in the `coupled_hivol / coupled_lovol` scenarios (spread and depth co-move with σ) the σ-carrying sqrt model improves (mean |bias| 1.03 / 0.47 vs 2.86 / 0.68 for half-spread-only):

| model | hivol: truth x | hivol: model x | lovol: truth x | lovol: model x | deep: truth x | deep: model x | shallow: truth x | shallow: model x |
|---|---|---|---|---|---|---|---|---|
| E1_mid_fill | 1.03 | n/a | 1.03 | n/a | 0.55 | n/a | 5.20 | n/a |
| fixed_5bps_default | 1.03 | 1.00 | 1.03 | 1.00 | 0.55 | 1.00 | 5.20 | 1.00 |
| fixed_bps_calibrated | 1.03 | 1.00 | 1.03 | 1.00 | 0.55 | 1.00 | 5.20 | 1.00 |
| half_spread_only(E3) | 1.03 | 1.00 | 1.03 | 1.00 | 0.55 | 1.00 | 5.20 | 4.00 |
| spread_prop | 1.03 | 1.00 | 1.03 | 1.00 | 0.55 | 1.00 | 5.20 | 4.00 |
| vol_scaled | 1.03 | 2.08 | 1.03 | 0.64 | 0.55 | 1.00 | 5.20 | 2.38 |
| size_depth(L1+D1bp) | 1.03 | 1.00 | 1.03 | 1.00 | 0.55 | 0.59 | 5.20 | 8.66 |
| sqrt_law(OHLCV-only) | 1.03 | 2.16 | 1.03 | 0.61 | 0.55 | 0.68 | 5.20 | 2.54 |
| sqrt_law(L1 spread) | 1.03 | 2.16 | 1.03 | 0.61 | 0.55 | 0.68 | 5.20 | 3.80 |
| book_walk_L2_top20(20bps) | 1.03 | 1.00 | 1.03 | 1.00 | 0.55 | 0.55 | 5.20 | 5.09 |
| book_walk_L2_top20+sqrt_fallback | 1.03 | 1.00 | 1.03 | 1.00 | 0.55 | 0.55 | 5.20 | 5.09 |
| book_walk_L2(100bps) | 1.03 | 1.00 | 1.03 | 1.00 | 0.55 | 0.55 | 5.20 | 5.09 |

**Latency**: does not change the mean cost of the walk or of any static model in a random walk (mean drift ≈ 0), it changes the *variance* by σ²L — see `10` B. Under trend/adverse flow it shifts the mean by `drift·L` and every static model is biased by exactly that amount.

## 3. Empirical: book-walk cost from public snapshots (not realised slippage)

Mean cost (bps vs mid) of a hypothetical BUY market order of notional N walking the visible ask levels. Top-25-level run (visible depth 1.8–20 bps) and coverage (share of snapshots whose visible depth ≥ N):

| venue | asset | 1000 | 10000 | 100000 | 300000 | 1000000 | 3000000 |
|---|---|---|---|---|---|---|---|
| coinbase | BTC | 0.09 | 0.21 | 0.61 | 1.09 | 0.93 | n/a |
| coinbase | ETH | 0.19 | 0.37 | 1.44 | 1.96 | n/a | n/a |
| coinbase | SOL | 0.83 | 1.67 | 5.24 | 9.92 | 14.66 | n/a |
| kraken | BTC | 0.09 | 0.17 | 0.34 | 0.42 | 0.75 | n/a |
| kraken | ETH | 0.21 | 0.52 | 1.45 | 2.01 | 2.74 | n/a |
| kraken | SOL | 0.58 | 1.02 | 3.53 | 5.60 | 9.79 | 15.94 |
| okx | BTC | 0.02 | 0.08 | 0.37 | 0.69 | n/a | n/a |
| okx | ETH | 0.03 | 0.09 | 0.78 | 1.38 | n/a | n/a |
| okx | SOL | 0.49 | 0.66 | 3.13 | 7.19 | 14.88 | n/a |

| venue | asset | 1000 | 10000 | 100000 | 300000 | 1000000 | 3000000 |
|---|---|---|---|---|---|---|---|
| coinbase | BTC | 1.00 | 1.00 | 1.00 | 0.92 | 0.01 | 0.00 |
| coinbase | ETH | 1.00 | 1.00 | 1.00 | 0.26 | 0.00 | 0.00 |
| coinbase | SOL | 1.00 | 1.00 | 1.00 | 1.00 | 0.04 | 0.00 |
| kraken | BTC | 1.00 | 1.00 | 1.00 | 0.98 | 0.76 | 0.00 |
| kraken | ETH | 1.00 | 1.00 | 1.00 | 0.85 | 0.06 | 0.00 |
| kraken | SOL | 1.00 | 1.00 | 1.00 | 1.00 | 0.95 | 0.03 |
| okx | BTC | 1.00 | 0.99 | 0.98 | 0.78 | 0.00 | 0.00 |
| okx | ETH | 1.00 | 1.00 | 1.00 | 0.72 | 0.00 | 0.00 |
| okx | SOL | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | 0.00 |

Deep run (400 levels, 8 minutes, 192–240 snapshots per series) — coverage is ≥ 98 % for all N up to 3M USD:

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

Observations (OBSERVED, one window):

* At 100k USD the walk costs 0.29–0.77 bps (BTC), 1.15–1.63 (ETH), 2.7–4.0 (SOL); at 1M USD 1.1–2.5 (BTC), 4.0–5.1 (ETH), 10–18 (SOL). Local exponent of walk cost in N between 100k and 1M: 0.39–0.87 (median 0.55); i.e. close to, but not identical to, a square-root scaling.
* A 5 bps default overstates BTC at ≤ 100k USD by ≥ 6× (up to ~500× at 1k USD) and understates SOL at 1M USD by 2–3.5×; the frictionless fill is defensible only for BTC/ETH at ≤ 10k USD (true walk cost 0.01–0.65 bps).
* **Visible-depth limit**: with the usual top-25 REST view the walk is defined for BTC only up to ≈ 0.1–0.3M USD (coverage 0.98 at 100k, 0.78 at 300k on OKX, ~0 at 1M) — a PAPER using 25 levels must return `INSUFFICIENT_VISIBLE_DEPTH` above that, not extrapolate.
* **Venue dispersion** (same asset, same size): 100k USD BTC 0.29–0.77 bps, ETH 1.15–1.63, SOL 2.7–4.0.

### 3.1 Snapshot staleness

Error of predicting the walk at `t + Δ` with the snapshot at `t` (bias, mean absolute error, p95 of |error|, and mean cost), Δ = 4 s and 30 s:

| venue | asset | stale_s | N | n | mean_err | mae | p95_abs | mean_cost |
|---|---|---|---|---|---|---|---|---|
| okx | BTC | 4 | 10000 | 1248 | -0.001 | 0.134 | 0.781 | 0.085 |
| okx | BTC | 4 | 100000 | 1208 | 0.000 | 0.386 | 1.159 | 0.368 |
| okx | BTC | 30 | 10000 | 1238 | 0.006 | 0.144 | 0.804 | 0.089 |
| okx | BTC | 30 | 100000 | 1192 | 0.011 | 0.412 | 1.176 | 0.377 |
| okx | ETH | 4 | 10000 | 1262 | 0.000 | 0.135 | 0.692 | 0.093 |
| okx | ETH | 4 | 100000 | 1254 | 0.001 | 0.482 | 1.214 | 0.783 |
| okx | ETH | 30 | 10000 | 1251 | 0.001 | 0.129 | 0.670 | 0.093 |
| okx | ETH | 30 | 100000 | 1244 | 0.016 | 0.483 | 1.218 | 0.796 |
| okx | SOL | 4 | 10000 | 1262 | -0.000 | 0.346 | 1.400 | 0.655 |
| okx | SOL | 4 | 100000 | 1262 | -0.001 | 0.728 | 1.866 | 3.132 |
| okx | SOL | 30 | 10000 | 1251 | 0.003 | 0.368 | 1.384 | 0.658 |
| okx | SOL | 30 | 100000 | 1251 | 0.005 | 0.813 | 2.109 | 3.137 |
| coinbase | BTC | 4 | 10000 | 1496 | -0.005 | 0.241 | 0.786 | 0.204 |
| coinbase | BTC | 4 | 100000 | 1496 | -0.008 | 0.351 | 0.904 | 0.603 |
| coinbase | BTC | 30 | 10000 | 1483 | 0.003 | 0.257 | 0.812 | 0.212 |
| coinbase | BTC | 30 | 100000 | 1483 | 0.002 | 0.381 | 0.983 | 0.613 |
| coinbase | ETH | 4 | 10000 | 1496 | 0.001 | 0.298 | 0.846 | 0.374 |
| coinbase | ETH | 4 | 100000 | 1488 | 0.002 | 0.376 | 1.022 | 1.440 |
| coinbase | ETH | 30 | 10000 | 1483 | 0.006 | 0.339 | 0.955 | 0.380 |
| coinbase | ETH | 30 | 100000 | 1475 | 0.011 | 0.414 | 1.124 | 1.449 |
| coinbase | SOL | 4 | 10000 | 1496 | 0.010 | 0.813 | 2.332 | 1.684 |
| coinbase | SOL | 4 | 100000 | 1496 | -0.008 | 1.080 | 2.880 | 5.237 |
| coinbase | SOL | 30 | 10000 | 1483 | -0.014 | 0.898 | 2.298 | 1.662 |
| coinbase | SOL | 30 | 100000 | 1483 | -0.008 | 1.299 | 3.240 | 5.243 |
| kraken | BTC | 4 | 10000 | 1481 | -0.002 | 0.231 | 1.386 | 0.166 |
| kraken | BTC | 4 | 100000 | 1477 | -0.002 | 0.357 | 1.624 | 0.337 |
| kraken | BTC | 4 | 1000000 | 926 | 0.018 | 0.424 | 1.753 | 0.741 |
| kraken | BTC | 30 | 10000 | 1467 | -0.003 | 0.252 | 1.479 | 0.165 |
| kraken | BTC | 30 | 100000 | 1462 | -0.006 | 0.398 | 1.861 | 0.334 |
| kraken | BTC | 30 | 1000000 | 860 | 0.023 | 0.431 | 1.566 | 0.735 |
| kraken | ETH | 4 | 10000 | 1481 | -0.001 | 0.414 | 1.427 | 0.522 |
| kraken | ETH | 4 | 100000 | 1479 | 0.005 | 0.590 | 1.592 | 1.451 |
| kraken | ETH | 30 | 10000 | 1467 | 0.010 | 0.465 | 1.509 | 0.531 |
| kraken | ETH | 30 | 100000 | 1465 | 0.025 | 0.651 | 1.678 | 1.467 |
| kraken | SOL | 4 | 10000 | 1481 | 0.003 | 0.546 | 1.575 | 1.022 |
| kraken | SOL | 4 | 100000 | 1481 | -0.011 | 0.618 | 1.557 | 3.515 |
| kraken | SOL | 4 | 1000000 | 1351 | -0.002 | 0.773 | 2.054 | 9.781 |
| kraken | SOL | 30 | 10000 | 1467 | 0.013 | 0.579 | 1.611 | 1.029 |
| kraken | SOL | 30 | 100000 | 1467 | 0.004 | 0.690 | 1.750 | 3.529 |
| kraken | SOL | 30 | 1000000 | 1334 | 0.001 | 0.898 | 2.268 | 9.794 |

* **Near-unbiased**: top-25 run — |mean error| ≤ 0.05 bps everywhere (median ≤ 0.012 bps; ≤ 3 % of the cost at N ≥ 100k, ≤ 10 % at 1k–10k); deep run — ≤ 0.11 bps up to 300k USD, and for 1–3M USD median 0.012–0.062 bps but up to 0.53 bps (1M) and 1.62 bps (3M, OKX SOL at 30 s) on the noisiest series; relative to cost the median is ≤ 3.3 % and the maximum 14 % (small orders). Not exact, but no systematic sign.
* **Error floor, not decay**: MAE at Δ = 30 s is only 7–20 % above Δ = 4 s (e.g. OKX BTC 100k: 0.41 vs 0.39; Coinbase SOL 100k: 1.30 vs 1.08): the dominant error is book flicker faster than 4 s, not slow drift of liquidity; the Δ→0 limit is unmeasurable with 2 s polling (UNKNOWN).
* The error is of the same order as the cost itself for small orders (MAE 0.13 vs mean cost 0.09 bps for OKX BTC 10k), so per-trade walk costs are noisy; averages are reliable.

### 3.2 Does the walk beat calibrated constants? (falsification attempt)

Predict the walk at t+4 s with (a) the snapshot walk (no calibration), (b) a constant calibrated per series×N on the first half of the capture, (c) half-spread only, (d) spread-proportional / sqrt with parameters calibrated on the first half; test on the second half. Top-25 run (N ≤ 1M):

| venue | asset | N | book_walk(snapshot t) | fixed_bps(train mean) | half_spread_only | spread_prop(k train) | sqrt(Y train) |
|---|---|---|---|---|---|---|---|
| coinbase | BTC | 10000 | 0.287 | 0.224 | 0.242 | 1.058 | 0.236 |
| coinbase | BTC | 100000 | 0.396 | 0.319 | 0.618 | 3.535 | 0.318 |
| coinbase | ETH | 10000 | 0.345 | 0.286 | 0.351 | 0.489 | 0.301 |
| coinbase | ETH | 100000 | 0.423 | 0.398 | 1.368 | 2.065 | 0.396 |
| coinbase | SOL | 10000 | 0.878 | 0.846 | 1.235 | 1.085 | 0.893 |
| coinbase | SOL | 100000 | 1.091 | 2.257 | 5.662 | 2.416 | 2.178 |
| kraken | BTC | 10000 | 0.369 | 0.275 | 0.270 | 0.393 | 0.282 |
| kraken | BTC | 100000 | 0.527 | 0.408 | 0.463 | 0.853 | 0.414 |
| kraken | BTC | 1000000 | 0.651 | 0.493 | 0.911 | 1.798 | 0.495 |
| kraken | ETH | 10000 | 0.584 | 0.732 | 0.755 | 1.403 | 0.663 |
| kraken | ETH | 100000 | 0.691 | 0.933 | 1.719 | 7.036 | 0.835 |
| kraken | ETH | 1000000 | n/a | 2.099 | 3.365 | 20.508 | 1.816 |
| kraken | SOL | 10000 | 0.639 | 0.519 | 0.645 | 0.608 | 0.544 |
| kraken | SOL | 100000 | 0.626 | 0.508 | 3.048 | 1.112 | 0.535 |
| kraken | SOL | 1000000 | 0.810 | 0.955 | 9.650 | 2.723 | 0.935 |
| okx | BTC | 10000 | 0.148 | 0.132 | 0.083 | 0.133 | 0.132 |
| okx | BTC | 100000 | 0.436 | 0.338 | 0.399 | 0.338 | 0.338 |
| okx | ETH | 10000 | 0.162 | 0.121 | 0.089 | 0.121 | 0.121 |
| okx | ETH | 100000 | 0.483 | 0.414 | 0.908 | 0.414 | 0.414 |
| okx | SOL | 10000 | 0.329 | 0.300 | 0.222 | 0.300 | 0.300 |
| okx | SOL | 100000 | 0.787 | 0.646 | 2.679 | 0.646 | 0.646 |

Deep run (N up to 3M; 8-minute capture, so calibration and test halves are 4 minutes each):

| venue | asset | N | book_walk(snapshot t) | fixed_bps(train mean) | half_spread_only | spread_prop(k train) | sqrt(Y train) |
|---|---|---|---|---|---|---|---|
| coinbase | BTC | 100000 | 0.419 | 0.315 | 0.790 | 1.535 | 0.326 |
| coinbase | BTC | 1000000 | 0.532 | 0.334 | 2.361 | 4.443 | 0.344 |
| coinbase | BTC | 3000000 | 0.863 | 0.953 | 6.634 | 11.652 | 0.955 |
| coinbase | ETH | 100000 | 0.432 | 0.349 | 1.305 | 1.681 | 0.352 |
| coinbase | ETH | 1000000 | 0.506 | 1.584 | 5.732 | 5.588 | 1.524 |
| coinbase | ETH | 3000000 | 1.136 | 4.318 | 14.824 | 13.922 | 4.257 |
| coinbase | SOL | 100000 | 1.264 | 1.459 | 3.480 | 1.637 | 1.440 |
| coinbase | SOL | 1000000 | 1.243 | 2.291 | 14.801 | 4.765 | 2.294 |
| coinbase | SOL | 3000000 | 2.816 | 4.459 | 33.793 | 11.519 | 4.479 |
| kraken | BTC | 100000 | 0.267 | 0.273 | 0.226 | 0.180 | 0.270 |
| kraken | BTC | 1000000 | 0.597 | 0.543 | 0.979 | 0.437 | 0.540 |
| kraken | BTC | 3000000 | 0.643 | 0.500 | 3.241 | 1.670 | 0.499 |
| kraken | ETH | 100000 | 0.715 | 0.601 | 1.446 | 1.306 | 0.572 |
| kraken | ETH | 1000000 | 0.837 | 0.629 | 3.946 | 3.437 | 0.634 |
| kraken | ETH | 3000000 | 0.890 | 0.703 | 7.361 | 6.386 | 0.735 |
| kraken | SOL | 100000 | 0.854 | 0.695 | 3.004 | 1.248 | 0.694 |
| kraken | SOL | 1000000 | 1.101 | 0.810 | 9.444 | 3.135 | 0.805 |
| kraken | SOL | 3000000 | 3.545 | 3.618 | 19.654 | 6.102 | 3.601 |
| okx | BTC | 100000 | 0.334 | 0.307 | 0.293 | 0.307 | 0.307 |
| okx | BTC | 1000000 | 0.559 | 0.443 | 2.520 | 0.444 | 0.443 |
| okx | BTC | 3000000 | 0.525 | 0.661 | 5.540 | 0.662 | 0.661 |
| okx | ETH | 100000 | 0.496 | 0.388 | 1.250 | 0.493 | 0.387 |
| okx | ETH | 1000000 | 0.388 | 0.492 | 4.148 | 0.930 | 0.491 |
| okx | ETH | 3000000 | 0.503 | 0.794 | 8.180 | 1.737 | 0.793 |
| okx | SOL | 100000 | 0.692 | 0.806 | 1.985 | 0.808 | 0.806 |
| okx | SOL | 1000000 | 1.884 | 4.760 | 19.604 | 4.740 | 4.759 |
| okx | SOL | 3000000 | 3.287 | 13.293 | 66.958 | 13.235 | 13.293 |

cells (series × N × run): 92. Walk MAE < calibrated-constant MAE in 34 cells (37%); walk MAE < half-spread-only MAE in 55 (60%). Mean |bias|: walk 0.025 bps vs constant 0.518 bps. By notional (share of cells where walk beats constant): 1,000: 28% (n=18), 10,000: 28% (n=18), 100,000: 28% (n=18), 300,000: 39% (n=18), 1,000,000: 45% (n=11), 3,000,000: 78% (n=9)

Reading: the per-instrument-per-size constants are a *strong* baseline for MAE because the capture is stationary and small orders are dominated by book flicker — **the walk wins mostly where the book regime changes within the window (Coinbase/OKX/Kraken ETH and SOL at ≥ 1M USD; 78 % of the 3M-USD cells)**, and has no systematic bias (mean |bias| 0.025 vs 0.52 bps for the half-sample constants). The constants win in MAE for BTC and for small sizes but they need a per-venue, per-instrument, per-size history that a PAPER does not have on day one; §3.3 tests what happens when that history comes from *other* instruments.

### 3.3 Calibration transport: leave-one-series-out

Fit the constant / `Y` / spread multiple on the other 8 venue-asset series and predict the ninth (mean walk cost at N; only series with ≥ 95 % coverage):

Top-25 run:

| N | n_series | model | median_abs_rel_err | mean_signed_rel_err | worst_factor | mae_bps |
|---|---|---|---|---|---|---|
| 10000 | 9 | fixed | 0.77 | 1.61 | 6.97 | 0.44 |
| 10000 | 9 | sqrt | 0.37 | 0.35 | 3.27 | 0.16 |
| 10000 | 9 | spread_prop | 0.54 | -0.21 | 5.35 | 0.20 |
| 10000 | 9 | half_spread_only | 0.80 | -0.72 | 14.25 | 0.34 |
| 100000 | 9 | fixed | 0.72 | 1.40 | 6.10 | 1.57 |
| 100000 | 9 | sqrt | 0.53 | 0.38 | 3.30 | 0.73 |
| 100000 | 9 | spread_prop | 0.39 | -0.25 | 6.63 | 0.52 |
| 100000 | 9 | half_spread_only | 0.93 | -0.92 | 61.92 | 1.68 |

Deep run (N up to 1M USD):

| N | n_series | model | median_abs_rel_err | mean_signed_rel_err | worst_factor | mae_bps |
|---|---|---|---|---|---|---|
| 10000 | 9 | fixed | 0.64 | 1.96 | 9.41 | 0.37 |
| 10000 | 9 | sqrt | 0.36 | 0.50 | 3.10 | 0.15 |
| 10000 | 9 | spread_prop | 0.73 | -0.24 | 4.83 | 0.21 |
| 10000 | 9 | half_spread_only | 0.75 | -0.70 | 11.34 | 0.27 |
| 100000 | 9 | fixed | 0.60 | 1.28 | 6.80 | 1.24 |
| 100000 | 9 | sqrt | 0.46 | 0.58 | 5.03 | 0.66 |
| 100000 | 9 | spread_prop | 0.58 | -0.28 | 6.88 | 0.79 |
| 100000 | 9 | half_spread_only | 0.95 | -0.92 | 58.45 | 1.57 |
| 1000000 | 9 | fixed | 0.80 | 1.17 | 6.96 | 5.55 |
| 1000000 | 9 | sqrt | 0.41 | 0.69 | 5.50 | 3.98 |
| 1000000 | 9 | spread_prop | 0.66 | -0.23 | 12.20 | 3.36 |
| 1000000 | 9 | half_spread_only | 0.98 | -0.98 | 414.21 | 6.67 |

* A single calibrated **constant transports with median relative error 60–80 %** and worst-case factors 6–9×; **sqrt-with-cross-series-Y is the best transporter (median error 36–53 %, worst 3–5.5×)** but is still ±50 %. Half-spread-only under-charges by 75–98 % (worst 11–414×). *No cross-instrument constant is trustworthy to better than about a factor of two*; conversely the sqrt form (size and σ/V scaling) removes about half of the constant model's transport error.
* Therefore, for `OHLCV_ONLY` the supportable statement is a **band from a sqrt-law prior with a cross-instrument Y**, flagged `ESTIMATED` with ±50–100 % error and a 3–5× tail — not a measurement.

## 4. Market impact

### 4.1 Which impact concepts survive at non-HFT intraday scale

| Concept | Definition | Survives at 1e4–1e7 USD, minutes-scale? | Charged as |
|---|---|---|---|
| **Spread crossing** | half-spread at execution | yes (0.006 bps BTC … 0.4–0.6 bps SOL) | `spread` |
| **Temporary impact of this order** (book walk, same instant) | VWAP beyond touch | yes — the dominant size cost (0.3–2.5 bps BTC at 0.1–1M USD) | `slippage` (walk) — **not** additionally an "impact" line |
| **Transient impact of earlier own child orders** | displacement of mid still decaying when the next child hits (propagator/depletion) | only for multi-child parents or repeated orders within τ ≈ tens of seconds to minutes (synthetic E15: 5 children of 500k USD cost 2.5–5.1 bps/order vs 2.3 for one, depending on spacing 600 s … 1 s; `04` §5) | `impact` |
| **Permanent impact** | information/inventory effect that persists | negligible for one small order (aggregate market flow gives λ = 2.3–6.6 bps per 1M USD **net market flow per minute**, R² 0.2–0.34, Binance tape, `§4.2`; own-order share is a tiny fraction); matters only as a marking effect for *later* fills | `impact` on later children only; never on this fill |
| **Adverse price movement** (timing) | exogenous drift + informed flow during the latency window | yes, zero-mean in RW; conditional mean +0.6…+1.8 bps after strong flow | `timing` |

### 4.2 Aggregate flow–return regression on Binance aggTrades (context, not metaorder impact)

1-minute and 5-minute bars, signed USD flow `Q` vs bar return; fit on all days but the last, out-of-sample RMSE on the last day (bps):

| sym | bar_s | n_bars | lambda_bps_per_musd | R2 | loglog_slope | oos_rmse_zero | oos_rmse_linear | oos_rmse_sqrt |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 60 | 5760 | 2.634 | 0.280 | 0.672 | 5.109 | 4.402 | 4.057 |
| BTCUSDT | 300 | 1152 | 2.271 | 0.344 | 0.562 | 11.766 | 9.538 | 9.313 |
| ETHUSDT | 60 | 2880 | 6.599 | 0.217 | 0.850 | 6.809 | 6.460 | 6.084 |
| ETHUSDT | 300 | 576 | 6.483 | 0.279 | 1.005 | 15.101 | 13.609 | 13.095 |

* Flow explains 22–34 % of bar return variance (R²), slope 2.3–6.6 bps per 1M USD net flow; the log-log slope of signed impact vs |Q| deciles is 0.56–1.0 (BTC 0.67/0.56, ETH 0.85/1.0): **inconclusive between square-root and linear**, and OOS RMSE ranks sqrt < linear < zero but by ≤ 8 % (vs linear) and ≤ 21 % (vs zero). This is aggregate flow, endogenous (returns also cause flow) and *not* a metaorder study — it does not measure the impact of a single trader's order and must not be used to calibrate one. Metaorder-level evidence for current crypto venues is UNKNOWN in the accessible literature (`02`).

### 4.3 What the sliced-execution synthetic bench says about impact modelling

(`04` §4) memory-less walks under-charge multi-child parents by up to 2.6 bps at 20 slices; a propagator layer removes about half; a linear AC form mis-orders schedules; a schedule-blind sqrt cannot rank. Depletion recovery (τ ≈ 20 s) is a first-order term that the propagator-only model omits.

## 5. Accounting decomposition (no double counting)

Every model above is **IS-calibrated** (it predicts the price move from arrival mid to average fill) and therefore already contains some rungs of the ladder in `11`. Adding a second model's rungs on top double counts:

| Model | Rungs implicitly inside | Safe pairing |
|---|---|---|
| Fixed bps | spread + slippage + mean timing | use alone; all other lines `EMBEDDED_BY_BASIS`-like (declare basis `FIXED_IS`) |
| Spread-proportional | spread + (some) slippage | alone, or with an explicit fee line |
| Vol-scaled | spread + timing (non-zero mean) | alone |
| Square-root (IS-calibrated) | spread + slippage + mean timing (+ average own impact) | alone; **do not add a spread line** (this is the most common double count) |
| Almgren–Chriss (ε, γ, η) | ε = spread/fixed cost, γ permanent, η temporary | alone; do not pair ε with a spread line |
| L2 walk | half-spread + slippage | `BOOK_VWAP` basis; add only `timing` band, fees, `impact` (multi-child) |
| Propagator | transient/permanent impact of *earlier* fills only | pair with walk (temporary part) — never with an IS-calibrated model |

The contract (`11`) turns this table into code: choosing a model fixes a fill basis and the ledger refuses charges for embedded rungs; the naive stack "full spread + 1 bp slippage + sqrt" over-charges a 1M USD trade in the synthetic base book by ×1.98.

## 6. Verdicts

* **`SLIPPAGE_REFERENCE`**: L2 book walk over the visible levels with an explicit `INSUFFICIENT_VISIBLE_DEPTH` flag and a staleness band taken from the empirical snapshot-to-snapshot error (≈ 0.1–0.8 bps for ≤ 100k USD; wider above). Supported for the regime and range tested (BTC/ETH/SOL, three venues, N ≤ 3M USD, 400 levels).
* **`IMPACT_REFERENCE`**: for a single child order, no separate impact line beyond the walk; for multi-child/repeated orders, walk per child + depletion/recovery + transient impact memory (propagator family) — **ADAPT_CANDIDATE**, needs calibration from the user's own PAPER runs (not calibratable from free data). Square-root law as an OHLCV-only prior with a ±50–100 % band.
* Not supported: any fixed/proportional model as a default, and any impact model calibrated on aggregate tape flow as if it were order-level.
