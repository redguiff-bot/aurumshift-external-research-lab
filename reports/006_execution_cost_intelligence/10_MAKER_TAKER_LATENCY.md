# 10 — Maker vs taker, and latency

## Part A — Is the maker/taker choice practically modelable without HFT queue simulation?

### A.1 Structure (PROVEN arithmetic, relative to arrival mid, BUY)

* taker: `half_spread + walk + fee_t`
* maker (post at the touch, wait H, then chase with a market order): `P·(−half_spread + fee_m) + (1−P)·(drift_nofill + half_spread + walk + fee_t)`
* ⇒ `maker − taker = −P·(2·half_spread + Δfee) + (1−P)·drift_nofill`, with `Δfee = fee_t − fee_m`.
* break-even fill probability **P\* = X / (X + 2·half_spread + Δfee)** where `X = E[drift | no fill]` is the cost of being left behind.

Three inputs are needed and only one of them is cheaply observable: the spread (L1), the fee gap Δfee (a schedule: UNKNOWN for OKX/Bybit/Coinbase official tables here, `02` M; **parameterised** below), and the pair (P, X) — the fill probability and the opportunity cost, which depend on queue position and on alpha/drift over the waiting horizon.

### A.2 Synthetic: the decision is about drift, not about the fill model

432 cells (queue 0/0.5/1, aggressor volume, drift 0/0.1/0.4 bps/s, flow informativeness, σ, fee pair (2,5) or (8,10), spread 1 or 5 bps), 800 trials each, H = 60 s:

maker better in 61.8% of grid cells; mean regret always-maker 4.30 bps, always-taker 2.29 bps (432 cells)

By drift (bps/s; positive = price runs away from a passive buyer, i.e. the strategy has alpha in the direction of the trade):

| drift | fill_frac | IS_maker_bps | IS_taker_bps | post-fill adverse (bps) |
|---|---|---|---|---|
| 0.00 | 0.92 | 4.59 | 9.12 | 0.53 |
| 0.10 | 0.79 | 6.88 | 9.12 | -2.34 |
| 0.40 | 0.40 | 21.95 | 9.12 | -11.06 |

By fee pair and queue position:

| fee_m | fee_t | IS_maker | IS_taker |
|---|---|---|---|
| 2.00 | 5.00 | 8.29 | 6.62 |
| 8.00 | 10.00 | 13.99 | 11.62 |

| queue_frac | ff | IS_maker | IS_taker |
|---|---|---|---|
| 0.00 | 0.74 | 10.34 | 9.12 |
| 0.50 | 0.69 | 11.50 | 9.12 |
| 1.00 | 0.68 | 11.58 | 9.12 |

Decision quality of fill models (accuracy = agrees with the truth on "maker or taker?"; regret = extra cost of the model's choice vs the best choice; "alpha_aware" means the model is *told* the true drift, "blind" means it assumes zero drift):

| model|drift-knowledge | decision_accuracy | mean_regret_bps |
|---|---|---|
| always_fill(E1-maker)|blind | 0.62 | 4.30 |
| always_fill(E1-maker)|alpha_aware | 0.62 | 4.30 |
| const_p|blind | 0.62 | 4.30 |
| const_p|alpha_aware | 0.95 | 0.03 |
| price_through(sigma,tick)|blind | 0.62 | 4.30 |
| price_through(sigma,tick)|alpha_aware | 0.70 | 2.79 |
| queue_volume(L1 size+trade rate)|blind | 0.62 | 4.30 |
| queue_volume(L1 size+trade rate)|alpha_aware | 0.71 | 2.05 |
| hybrid(through OR queue)|blind | 0.62 | 4.30 |
| hybrid(through OR queue)|alpha_aware | 0.65 | 3.76 |

* **All fill models are equally wrong when the drift is unknown** (accuracy 62 %, regret 4.3 bps — identical to always-maker). The variable that decides is `drift_nofill` (the opportunity cost), i.e. the strategy's own alpha horizon, not the queue.
* When drift is *given*, the **calibrated constant `p`** reaches 95 % accuracy (regret 0.03 bps) and beats the price-through (70 %, 2.8 bps), displayed-queue (71 %, 2.1 bps) and hybrid (65 %, 3.8 bps) models: in this world **complexity in the fill model buys nothing**.
* Averaged over the whole grid maker is **more** expensive than taker in both fee sets (by 1.7 bps at fees (2,5) and 2.4 bps at (8,10); tables above) because the grid contains many high-drift cells; maker still wins in 62 % of the cells. The average hides the structure: it is the cell-level drift/queue combination that decides.
* Limits: synthetic; the constant p is fitted in-sample on the same grid (an optimistic baseline); real cancellations are not modelled in the truth beyond a single cancel rate.

### A.3 Live: what public data can and cannot say

For 9 series × 30 s, hypothetical bid at the touch (`08` §3). Post-fill adverse markout (mid 30 s after the fill vs the fill price, positive = adverse for a buyer) versus the unconditional markout, with a 20-snapshot block-bootstrap 95 % CI of the difference:

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

* **Adverse selection is present and measurable**: conditional − unconditional = +0.29 … +1.40 bps in all 18 series×horizons, with the 95 % CI excluding 0 in 16 of 18 (the two exceptions are OKX SOL). For BTC on OKX it is +0.55 bps — ~90× the half-spread. OBSERVED for this one window (n ≈ 410–490 overlapping windows per series).
* **Opportunity cost X is large** relative to the spread: when the bid is not touched within 30 s the mid has risen by 3.3–6.9 bps on average (front-of-queue definition). Break-even fill probabilities:

| venue | asset | half_spread | drift_if_nofill_30s | drift_if_fill_30s | n_nofill | P_lower | P_upper | P*(fee gap 0bps) | P*(fee gap 1bps) | P*(fee gap 2bps) | P*(fee gap 5bps) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| okx | BTC | 0.006 | 3.467 | -0.686 | 54 | 0.496 | 0.869 | 0.997 | 0.774 | 0.633 | 0.409 |
| okx | ETH | 0.018 | 4.395 | -0.967 | 46 | 0.528 | 0.889 | 0.992 | 0.809 | 0.683 | 0.466 |
| okx | SOL | 0.413 | 6.515 | -0.606 | 52 | 0.508 | 0.874 | 0.887 | 0.781 | 0.697 | 0.528 |
| coinbase | BTC | 0.034 | 4.029 | -0.554 | 50 | 0.741 | 0.898 | 0.983 | 0.790 | 0.661 | 0.443 |
| coinbase | ETH | 0.143 | 4.412 | -0.945 | 63 | 0.755 | 0.871 | 0.939 | 0.774 | 0.659 | 0.455 |
| coinbase | SOL | 0.576 | 6.905 | -0.985 | 79 | 0.586 | 0.839 | 0.857 | 0.762 | 0.687 | 0.529 |
| kraken | BTC | 0.019 | 3.281 | -0.851 | 83 | 0.416 | 0.829 | 0.989 | 0.760 | 0.617 | 0.394 |
| kraken | ETH | 0.096 | 4.136 | -1.541 | 104 | 0.464 | 0.786 | 0.956 | 0.776 | 0.654 | 0.443 |
| kraken | SOL | 0.471 | 5.589 | -1.073 | 97 | 0.357 | 0.800 | 0.856 | 0.742 | 0.655 | 0.485 |

Reading: with a zero fee gap, a passive BTC/ETH order at the touch needs P > 0.94–1.0 to beat the taker (the half-spread is ~0.006 bps, there is nothing to save); with a 2 bps fee gap P\* ≈ 0.62–0.70 lies **inside** the observable bracket [P_lower, P_upper] (P_lower 0.36–0.76, P_upper 0.79–0.90) for 7 of 9 series — the public data cannot tell whether maker wins there (Coinbase BTC/ETH have P_lower above P\*: maker wins even at the back of the queue); with a 5 bps gap P\* ≈ 0.39–0.53 and maker wins even at the back of the queue in 7 of 9 series (ambiguous for OKX SOL and Kraken SOL).

### A.4 Verdict

* Maker/taker **can be modelled as a decision rule** `maker iff P·(2·hs + Δfee) > (1−P)·X`, but its inputs `P` and `X` are **not identifiable from free data**: `P` only within a bracket 0.07–0.44 wide (mean 0.27), `X` only conditionally on an alpha horizon. Where the bracket straddles `P*` (typical for fee gaps ≈ 1–3 bps, i.e. today's spot tiers if the secondary fee data are right, UNKNOWN), the choice is **unjustifiable from public data** and must be flagged `MAKER_TAKER_UNDECIDABLE`.
* A defensible reference PAPER policy is therefore to keep the choice as an *input* (order-type flag) and cost both legs: taker fully (`spread + walk + fee`), maker as bracket (`fill_prob ∈ [P_lower, P_upper]`, unfilled remainder charged at chase cost with `X` from the live conditional distribution above, and adverse markout as a diagnostic).
* Cancellation risk (orders cancelled on drift, on venue events) is not observable here.

## Part B — Latency at AurumShift scale (no HFT assumptions)

### B.1 Timeline model

`t_decision → (system delay) → t_submit → (network + venue) → t_arrive/t_fill`, and the market observation `t_obs ≤ t_decision` has an age. Price risk = drift of the executable price from `t_obs` (what the model saw) to `t_fill`:
`total_age = (t_decision − t_obs) + (t_submit − t_decision) + (t_fill − t_submit)`. The contract's `timing` line owns this rung (`11`). Measured pieces:

* REST round trips (public endpoints from this sandbox, p50): OKX 275–278 ms, Coinbase 76–166 ms, Kraken 161–164 ms (`05`). These are *this environment's* numbers, not AurumShift's (UNKNOWN).
* Mid drift over horizon (live, snapshots ≥ 4 s so that the sampling gap does not blur the horizon):

| venue | asset | horizon_s | sd_bps | sd_over_half_spread | sqrt_scaling_pred | mean_bps |
|---|---|---|---|---|---|---|
| okx | BTC | 4 | 1.752 | 295.367 | 1.546 | -0.022 |
| okx | BTC | 10 | 2.759 | 465.166 | 2.444 | -0.059 |
| okx | BTC | 30 | 4.432 | 747.144 | 4.233 | -0.137 |
| okx | ETH | 4 | 2.313 | 126.390 | 2.017 | -0.061 |
| okx | ETH | 10 | 3.550 | 194.034 | 3.190 | -0.145 |
| okx | ETH | 30 | 5.586 | 305.270 | 5.525 | -0.385 |
| coinbase | BTC | 4 | 1.870 | 54.351 | 1.636 | -0.020 |
| coinbase | BTC | 10 | 2.744 | 79.752 | 2.587 | -0.051 |
| coinbase | BTC | 30 | 4.505 | 130.934 | 4.481 | -0.127 |
| coinbase | ETH | 4 | 2.284 | 15.944 | 2.048 | -0.086 |
| coinbase | ETH | 10 | 3.381 | 23.601 | 3.238 | -0.121 |
| coinbase | ETH | 30 | 5.436 | 37.946 | 5.608 | -0.413 |
| kraken | BTC | 4 | 1.715 | 90.537 | 1.508 | -0.016 |
| kraken | BTC | 10 | 2.690 | 142.034 | 2.384 | -0.063 |
| kraken | BTC | 30 | 4.433 | 234.076 | 4.129 | -0.151 |
| kraken | ETH | 4 | 2.177 | 22.791 | 1.874 | -0.051 |
| kraken | ETH | 10 | 3.252 | 34.038 | 2.962 | -0.149 |
| kraken | ETH | 30 | 5.483 | 57.394 | 5.131 | -0.406 |

* Binance aggTrades last-trade price drift, all horizons (4 / 2 days):

| sym | horizon_s | sd_bps | sd_over_sqrt_h | p99_abs | mean_bps | momentum_after_top_quartile_flow |
|---|---|---|---|---|---|---|
| BTCUSDT | 0.100 | 1.028 | 3.250 | 4.080 | 0.027 | 0.591 |
| BTCUSDT | 0.500 | 1.534 | 2.169 | 5.869 | 0.029 | 0.766 |
| BTCUSDT | 1.000 | 1.958 | 1.958 | 7.415 | 0.041 | 0.880 |
| BTCUSDT | 2.000 | 2.462 | 1.741 | 9.320 | 0.039 | 1.011 |
| BTCUSDT | 5.000 | 3.691 | 1.651 | 13.398 | 0.052 | 1.264 |
| BTCUSDT | 10.000 | 4.941 | 1.563 | 19.071 | 0.094 | 1.232 |
| BTCUSDT | 30.000 | 8.268 | 1.510 | 29.781 | 0.374 | 1.837 |
| BTCUSDT | 60.000 | 10.018 | 1.293 | 35.771 | 0.414 | 1.074 |
| ETHUSDT | 0.100 | 1.268 | 4.009 | 5.142 | 0.014 | 0.570 |
| ETHUSDT | 0.500 | 1.760 | 2.489 | 6.832 | -0.005 | 0.621 |
| ETHUSDT | 1.000 | 2.130 | 2.130 | 8.040 | -0.011 | 0.662 |
| ETHUSDT | 2.000 | 2.728 | 1.929 | 10.316 | -0.005 | 0.668 |
| ETHUSDT | 5.000 | 3.982 | 1.781 | 14.571 | -0.003 | 0.653 |
| ETHUSDT | 10.000 | 5.304 | 1.677 | 18.858 | 0.026 | 0.592 |
| ETHUSDT | 30.000 | 8.607 | 1.571 | 29.544 | 0.195 | 1.069 |
| ETHUSDT | 60.000 | 11.374 | 1.468 | 37.500 | 0.233 | 0.632 |

### B.2 Findings (OBSERVED)

1. **Unconditional mean drift is ≈ 0** (|mean| ≤ 0.42 bps even at 30–60 s) and **the standard deviation follows σ√L within ~10–15 % at ≥ 4 s** live (e.g. OKX BTC: 1.75 bps at 4 s vs 1.55 predicted; 4.43 vs 4.23 at 30 s). A zero-mean symmetric band `σ√L` is thus adequate for the *mean* cost.
2. **σ must be estimated at the latency horizon**: on Binance tape `sd/√h` falls from 3.25 (0.1 s) to 1.96 (1 s), 1.56 (10 s), 1.29 (60 s) for BTC — microstructure noise inflates short-horizon variance; extrapolating a 1-minute σ to a 100-ms latency would *under*-state the band by ~2.5×.
3. **Drift is conditionally biased**: after the top quartile of 1-second signed flow, the next 1–30 s return continues in the flow direction by +0.6 … +1.8 bps (BTC 0.88 at 1 s, ETH 0.66). A random-walk perturbation misses this adverse-flow term, which is the mechanism behind the maker adverse selection in A.3 and the taker slippage-under-latency in `04` (trend/gap rows).
4. **Scale vs spread**: for BTC on OKX the 4-s drift sd (1.75 bps) is ~300× the half-spread and ≥ 4× the book-walk cost of a 100k USD order (0.37 bps): at these venues **timing variance, not spread, dominates the cost distribution** (the mean is still ~0).
5. Tail: synthetic gap scenario (+15 bps) shifts every model by ≈ 13 bps; FX/gold/WTI hourly series show **session gaps** with mean |gap| of 11.5 bps (EURUSD), 54 bps (XAU futures), 250 bps (WTI continuous, roll-contaminated) versus 1-hour σ of 6.5 / 31 / 75 bps (`results/fx_gold_ohlc.json`): weekend/rollover gaps are ≈ 1.1–3.3 σ_hour and cannot be handled by a latency perturbation.

### B.3 Is a simple bounded perturbation enough?

* **Yes** for the *expected* cost of taker orders in RW-like regimes at 0.1–30 s latency: `timing ~ N(0, (σ_L√L)²)` with σ_L calibrated at horizon L (synthetic `rw`, `meanrev`; live BTC/ETH), reported as a band, mean 0.
* **No** for (i) flow-conditional drift (needs `E[drift | signed-flow z-score]` from a tape: available from free aggTrades-like data), (ii) gaps/session boundaries (needs an explicit gap flag/band; FX/gold/commodities have weekend gaps that dominate), (iii) stale-snapshot risk when the book was thin (`withdraw`).
* A stronger model than "bounded perturbation" is warranted only for (i), and the minimal version is an additive conditional mean `β·flow_z·σ√L` fitted on a tape; no HFT-style latency-arbitrage or queue-jumping model is needed at this scale (INFERENCE).
