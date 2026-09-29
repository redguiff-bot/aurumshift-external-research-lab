# 08 — Fill and partial-fill models

Scope: market-order depth caps (partial fills), probabilistic/participation fills, passive fills at the touch (price-through, queue, hybrid), and the minimum useful model per data regime.
Evidence: synthetic worlds (known truth) and live public bounds (OKX/Coinbase/Kraken, BTC/ETH/SOL, ≈ 50 min). No own orders exist, so **no live fill probability was measured, only bounds**.

## 1. How often does "full fill" distort? (synthetic)

**Market orders.** Full-fill is exact as long as the order is a small fraction of *total* book depth, and wrong in a very lopsided way once it is not (thin-book grid: `A` = depth scale, 5 depths × 4 sizes = 20 cells):

| A | N | N_over_depth | filled | naive_full_fill_cost | truth_cost_filled_part | unfilled_notional |
|---|---|---|---|---|---|---|
| 300 | 1e+04 | 0.00227 | 1 | 0.5 | 6.76 | 0 |
| 300 | 1e+05 | 0.0227 | 1 | 0.5 | 29.4 | 0 |
| 300 | 1e+06 | 0.227 | 1 | 0.5 | 134 | 0 |
| 300 | 1e+07 | 2.27 | 0.441 | 0.5 | 360 | 5.59e+06 |
| 1e+03 | 1e+04 | 0.00068 | 1 | 0.5 | 3.31 | 0 |
| 1e+03 | 1e+05 | 0.0068 | 1 | 0.5 | 13.5 | 0 |
| 1e+03 | 1e+06 | 0.068 | 1 | 0.5 | 60.5 | 0 |
| 1e+03 | 1e+07 | 0.68 | 1 | 0.5 | 279 | 0 |
| 3e+03 | 1e+04 | 0.000227 | 1 | 0.5 | 1.87 | 0 |
| 3e+03 | 1e+05 | 0.00227 | 1 | 0.5 | 6.76 | 0 |
| 3e+03 | 1e+06 | 0.0227 | 1 | 0.5 | 29.4 | 0 |
| 3e+03 | 1e+07 | 0.227 | 1 | 0.5 | 134 | 0 |
| 1e+04 | 1e+04 | 6.8e-05 | 1 | 0.5 | 1.11 | 0 |
| 1e+04 | 1e+05 | 0.00068 | 1 | 0.5 | 3.31 | 0 |
| 1e+04 | 1e+06 | 0.0068 | 1 | 0.5 | 13.5 | 0 |
| 1e+04 | 1e+07 | 0.068 | 1 | 0.5 | 60.5 | 0 |
| 1e+05 | 1e+04 | 6.8e-06 | 1 | 0.5 | 0.637 | 0 |
| 1e+05 | 1e+05 | 6.8e-05 | 1 | 0.5 | 1.11 | 0 |
| 1e+05 | 1e+06 | 0.00068 | 1 | 0.5 | 3.31 | 0 |
| 1e+05 | 1e+07 | 0.0068 | 1 | 0.5 | 13.5 | 0 |

cells with fill < 99 %: 5% of 20 (thin-book grid); those cells have N/depth > 2.3; cells with N/depth < 0.1 all fill 100 %: True. Two separate distortions are visible in that table: (i) **partial fills** appear only when `N/depth ≳ 2` (rare, but then 56 % of a 10M USD order is unexecutable in the thinnest book) and (ii) **cost at touch** — even when the fill is 100 %, "fill at the touch" charges 0.5 bps vs a true walk of 0.6 → 360 bps in the same table. The second distortion is the common one; it is a slippage error (`07`), not a fill-fraction error.

**Passive orders.** "Always fills at the touch" is wrong almost everywhere in the synthetic limit-order world:

passive at the touch, 432 cells: mean fill fraction 0.70; share of cells with fill fraction < 0.95: 96%; < 0.5: 16%; min 0.10

**Live** (bounds, §3): a bid at the touch had a fill probability of at least 0.36–0.84 (back of queue, 30–60 s) and at most 0.79–0.94 (front of queue); even the front-of-queue upper bound is below 1, so "always fills" overstates the fill probability by at least 6–21 points at best and by 16–64 points at the back of the queue.

## 2. Passive fill models compared (synthetic, 432 cells × fill fraction)

Cells vary queue position (0/0.5/1 of displayed queue), aggressor volume (0.5k/2k/20k USD/s), drift (0/0.1/0.4 bps/s), flow-informativeness, volatility, fees, spread. Error = prediction − truth fill fraction over H = 60 s:

| model | bias | MAE | RMSE |
|---|---|---|---|
| always_fill(E1-maker) | 0.30 | 0.30 | 0.39 |
| const_p | 0.00 | 0.21 | 0.25 |
| hybrid(through OR queue) | 0.25 | 0.26 | 0.35 |
| price_through(sigma,tick) | 0.18 | 0.21 | 0.30 |
| queue_volume(L1 size+trade rate) | -0.12 | 0.40 | 0.50 |

* `always_fill` is biased +0.30. `const_p` (calibrated on the whole grid: p = 0.70) has zero bias and MAE 0.21, **as good as the price-through model** (MAE 0.21, bias +0.18) and better than the displayed-queue model (0.40, biased −0.12) and the hybrid (0.26, +0.25).
* The synthetic truth has a non-trivial dependence on drift/queue/volume that none of the four captures well; the *calibrated constant* is a hard baseline. A queue model that needs a displayed queue size and a trade rate **does not beat a constant** in this world (falsification of "more inputs ⇒ better fill model").

## 3. Live evidence: bounds only

For each snapshot a hypothetical BUY limit at the best bid was tracked over the public trade tape for H = 30 / 60 s:

* `P_upper` — any trade at ≤ bid price (assumes we are first in the queue);
* `P_through` — a trade strictly below the bid (independent of queue position);
* `P_lower` — cumulative volume traded at ≤ bid ≥ the displayed queue (we are last; ignores cancellations, which only help us).

| venue | asset | H_s | n | P_upper_front | P_through | P_lower_back | adverse_given_fill | adverse_uncond | diff | ci_lo | ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| okx | BTC | 30 | 413 | 0.869 | 0.768 | 0.496 | 0.698 | 0.143 | 0.554 | 0.351 | 0.767 |
| okx | BTC | 60 | 409 | 0.907 | 0.831 | 0.631 | 0.728 | 0.205 | 0.523 | 0.317 | 0.727 |
| okx | ETH | 30 | 413 | 0.889 | 0.840 | 0.528 | 0.998 | 0.369 | 0.629 | 0.415 | 0.869 |
| okx | ETH | 60 | 409 | 0.939 | 0.917 | 0.694 | 1.079 | 0.428 | 0.650 | 0.458 | 0.869 |
| okx | SOL | 30 | 413 | 0.874 | 0.765 | 0.508 | 0.037 | -0.291 | 0.328 | -0.047 | 0.656 |
| okx | SOL | 60 | 409 | 0.914 | 0.831 | 0.660 | 0.059 | -0.231 | 0.290 | -0.196 | 0.725 |
| coinbase | BTC | 30 | 490 | 0.898 | 0.800 | 0.741 | 0.590 | 0.087 | 0.503 | 0.309 | 0.686 |
| coinbase | BTC | 60 | 485 | 0.934 | 0.845 | 0.819 | 0.593 | 0.142 | 0.452 | 0.246 | 0.641 |
| coinbase | ETH | 30 | 490 | 0.871 | 0.865 | 0.755 | 0.941 | 0.257 | 0.684 | 0.410 | 0.952 |
| coinbase | ETH | 60 | 485 | 0.913 | 0.909 | 0.843 | 0.926 | 0.306 | 0.620 | 0.325 | 0.894 |
| coinbase | SOL | 30 | 490 | 0.839 | 0.718 | 0.586 | 0.436 | -0.287 | 0.722 | 0.387 | 1.056 |
| coinbase | SOL | 60 | 485 | 0.887 | 0.792 | 0.691 | 0.438 | -0.223 | 0.661 | 0.267 | 1.004 |
| kraken | BTC | 30 | 485 | 0.829 | 0.761 | 0.416 | 0.854 | 0.144 | 0.710 | 0.508 | 0.940 |
| kraken | BTC | 60 | 480 | 0.877 | 0.825 | 0.512 | 0.880 | 0.205 | 0.674 | 0.467 | 0.908 |
| kraken | ETH | 30 | 485 | 0.786 | 0.744 | 0.464 | 1.728 | 0.324 | 1.405 | 0.946 | 1.933 |
| kraken | ETH | 60 | 480 | 0.858 | 0.821 | 0.600 | 1.736 | 0.391 | 1.345 | 0.857 | 1.802 |
| kraken | SOL | 30 | 485 | 0.800 | 0.674 | 0.357 | 0.505 | -0.260 | 0.765 | 0.278 | 1.270 |
| kraken | SOL | 60 | 480 | 0.865 | 0.760 | 0.542 | 0.545 | -0.199 | 0.744 | 0.259 | 1.235 |

Brownian first-passage ("price-through") model against the observed `P_through` (tick and σ from the same capture):

| venue | asset | H_s | observed_P_through | model_price_through_BM | err | P_upper_front | P_lower_back | bracket_width |
|---|---|---|---|---|---|---|---|---|
| okx | BTC | 30 | 0.768 | 0.998 | 0.230 | 0.869 | 0.496 | 0.373 |
| okx | BTC | 60 | 0.831 | 0.998 | 0.167 | 0.907 | 0.631 | 0.276 |
| okx | ETH | 30 | 0.840 | 0.995 | 0.155 | 0.889 | 0.528 | 0.361 |
| okx | ETH | 60 | 0.917 | 0.996 | 0.079 | 0.939 | 0.694 | 0.244 |
| okx | SOL | 30 | 0.765 | 0.911 | 0.146 | 0.874 | 0.508 | 0.366 |
| okx | SOL | 60 | 0.831 | 0.937 | 0.106 | 0.914 | 0.660 | 0.254 |
| coinbase | BTC | 30 | 0.800 | 1.000 | 0.200 | 0.898 | 0.741 | 0.157 |
| coinbase | BTC | 60 | 0.845 | 1.000 | 0.154 | 0.934 | 0.819 | 0.115 |
| coinbase | ETH | 30 | 0.865 | 0.995 | 0.129 | 0.871 | 0.755 | 0.116 |
| coinbase | ETH | 60 | 0.909 | 0.996 | 0.087 | 0.913 | 0.843 | 0.070 |
| coinbase | SOL | 30 | 0.718 | 0.914 | 0.196 | 0.839 | 0.586 | 0.253 |
| coinbase | SOL | 60 | 0.792 | 0.939 | 0.147 | 0.887 | 0.691 | 0.196 |
| kraken | BTC | 30 | 0.761 | 0.998 | 0.237 | 0.829 | 0.416 | 0.412 |
| kraken | BTC | 60 | 0.825 | 0.998 | 0.173 | 0.877 | 0.512 | 0.365 |
| kraken | ETH | 30 | 0.744 | 0.994 | 0.250 | 0.786 | 0.464 | 0.322 |
| kraken | ETH | 60 | 0.821 | 0.996 | 0.175 | 0.858 | 0.600 | 0.258 |
| kraken | SOL | 30 | 0.674 | 0.915 | 0.240 | 0.800 | 0.357 | 0.443 |
| kraken | SOL | 60 | 0.760 | 0.940 | 0.179 | 0.865 | 0.542 | 0.323 |

price-through Brownian model: mean error +0.170, MAE 0.170 (n=18 series×horizons); observed [lower,upper] bracket width mean 0.27, min 0.07, max 0.44

* **The bracket [P_lower, P_upper] is 0.07–0.44 wide** (mean 0.27): without queue-position information a passive fill probability cannot be pinned down from public data. This is a structural limit (cancellations are invisible in aggregated L2), not a small-sample issue.
* The Brownian price-through model is **optimistic by 0.17 on average, in every one of 18 cases** (it treats the touch as continuous and ignores that a strict trade-through requires a print below the bid, not just a tick of mid movement). Falsified as a stand-alone fill model for large-tick assets; usable only as an upper bound.
* Queue models of the Cont–Stoikov–Talreja / queue-reactive type need per-level event intensities and queue sizes at message rate (L3 or full L2 diffs): `MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA` in this study (REST snapshots every ≥ 2 s).

## 4. Minimum useful model per data regime (reference)

| Data regime | Market/marketable orders | Passive orders |
|---|---|---|
| `OHLCV_ONLY` | participation cap vs bar volume (fill fraction = min(1, cap·V_bar/N)); cap value is **UNKNOWN** (not calibrated here) | **no fill model supported**; if required, "fill iff bar low < limit − ε" is the price-through rule (upper-bound-like, live P_through 0.67–0.92) and must be reported as an *optimistic* bound with `fill_prob = UNKNOWN` |
| `L1_QUOTES` | fill at touch only for `N ≤ displayed size`; beyond that `INSUFFICIENT_DEPTH` flag (not a silent switch to another model, `04` §3.7) | bracket `[P_lower(queue = displayed size), P_through]`; carry both, decide with the pessimistic end |
| `L2_BOOK` | exact depth-capped walk of the visible levels; unfilled remainder reported; visible-depth limit flagged (`07`) | same bracket; `P_lower` uses the real queue at the level, still ignoring cancels |
| `TRADES_PLUS_BOOK` | + staleness band from snapshot-to-snapshot differences (`07`) | + post-fill markout from the tape (adverse selection of fills, 0.3–1.4 bps at 30 s, `10`); bracket still open without own-order data |

Verdict: `FILL_REFERENCE = depth-capped book walk (market) + explicit [lower, upper] fill bracket (passive)`; probabilistic passive-fill *point* models are not supported by free data.
