# 07 — Turnover and slot-hour economics

Question: does explicit slot-hour economics beat raw expected-return ranking? Each idea below was attacked as a falsification target.

## Held-out paired differences vs `RANK_NET` (latent dz; count/level differences per run)
| policy | d_lat_dz | d_n_evict | d_admit_per_slot_hour | d_mean_hold | d_utilisation |
|---|---|---|---|---|---|
| SLOTHOUR_DENSITY | +0.0018 [+0.0006,+0.0028] | +0.0000 [+0.0000,+0.0000] | +0.0034 [+0.0027,+0.0042] | -0.6684 [-0.7801,-0.5645] | -0.0023 [-0.0026,-0.0021] |
| SLOTHOUR_HAZARD | -0.0017 [-0.0039,+0.0004] | +0.0000 [+0.0000,+0.0000] | +0.0065 [+0.0051,+0.0079] | -1.1289 [-1.3298,-0.9498] | -0.0037 [-0.0041,-0.0034] |
| SHADOW_PRICE | +0.0156 [+0.0120,+0.0190] | +0.0000 [+0.0000,+0.0000] | +0.0045 [+0.0028,+0.0062] | -1.6434 [-1.8613,-1.4457] | -0.0645 [-0.0684,-0.0607] |
| FLUID_QUANTILE | +0.0129 [+0.0092,+0.0166] | +0.0000 [+0.0000,+0.0000] | +0.0057 [+0.0040,+0.0075] | -1.8086 [-2.0437,-1.5786] | -0.0601 [-0.0641,-0.0564] |
| ONLINE_KNAPSACK_PSI | +0.0146 [+0.0100,+0.0187] | +0.0000 [+0.0000,+0.0000] | +0.0034 [+0.0016,+0.0052] | -2.1029 [-2.2996,-1.8964] | -0.1027 [-0.1083,-0.0972] |
| TRUNK_RESERVATION | +0.0100 [+0.0060,+0.0138] | +0.0000 [+0.0000,+0.0000] | +0.0064 [+0.0045,+0.0084] | -2.0061 [-2.2720,-1.7614] | -0.0661 [-0.0684,-0.0637] |
| EVICT_SWAP | +0.0048 [+0.0010,+0.0084] | +35.2789 [+33.0883,+37.5859] | +0.0151 [+0.0131,+0.0174] | -2.7327 [-3.0147,-2.4785] | -0.0097 [-0.0104,-0.0089] |
| OLDEST_SLOT | -0.2183 [-0.2299,-0.2071] | +154.7278 [+147.2362,+162.3958] | +0.0348 [+0.0324,+0.0374] | -4.8807 [-5.3132,-4.4634] | +0.0546 [+0.0497,+0.0593] |

## Findings
1. **Value per expected hold-hour alone (`SLOTHOUR_DENSITY`) ≈ raw net ranking** (+0.002 dz, CI +0.001…+0.003; practically nil), and the hazard-adjusted variant is indistinguishable (−0.002, CI −0.004…+0.001). The obvious idea — divide expected net by expected hold time — did **not** survive as a distinct gain here. Why (INFERENCE): the duration estimate is weak (ρ_d = 0.3 informative fraction) and mostly instrument-level, and when the slot is scarce a tie among candidates is rare; the ordering barely changes. Tuning also drove its overhead `h0` to the top of the grid (12–24 h), i.e. towards ordinary EV ranking.
2. **What does help is opportunity-cost *thresholding***: `SHADOW_PRICE` (+0.016), `ONLINE_KNAPSACK_PSI` (+0.015), `FLUID_QUANTILE` (+0.013), `TRUNK_RESERVATION` (+0.010) are all above `RANK_NET` with CI excluding 0. They share one mechanism visible in the data: utilisation falls by 6–10 points and mean hold falls by 1.6–2.1 h — they refuse marginal opportunities when slots are scarce (a slot-hour price), instead of always filling free slots with the best of a poor set.
3. **`EVICT_SWAP` (explicit turnover, min-hold 12 h, margin 1.5×) gives a small positive net** (+0.005) at the price of ≈ 35 forced exits per run (of ~430 admissions); tuning selected the longest minimum hold in the grid. `OLDEST_SLOT` (turnover-neutral churn baseline) is strongly negative (−0.218 vs `RANK_NET`, ≈ 155 forced exits per run). **Falsified**: churn for its own sake, and short minimum holds. Not falsified: a *value-triggered* swap with a high margin — but its benefit is tiny relative to the opportunity-cost thresholds that avoid churn altogether.
4. **Short vs long durations (S6)** — held-out variants with fast/slow density ratio 1.8, 0.9, 3.0 (mean latent per slot-hour):

| variant | FIFO | FIFO_NETPOS | RANK_NET | SLOTHOUR_DENSITY | SHADOW_PRICE | COMPOSED | ORACLE_DENSITY_NOT_IMPLEMENTABLE | RANK_NET long_slot_hour_share | SLOTHOUR_DENSITY long_slot_hour_share |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.008 | 1.140 | 1.293 | 1.295 | 1.326 | 1.323 | 1.487 | 0.674 | 0.678 |
| 1 | 2.140 | 2.383 | 2.778 | 2.838 | 2.912 | 2.816 | 3.287 | 0.677 | 0.649 |
| 2 | 0.539 | 0.677 | 0.746 | 0.756 | 0.822 | 0.809 | 0.813 | 0.661 | 0.650 |

   `SLOTHOUR_DENSITY` beats `RANK_NET` in 3/3 variants but by small amounts (+0.002, +0.060, +0.010 bps/slot-hour for ratios 1.8, 0.9, 3.0); the largest gain is in the ratio-0.9 variant, where the *slow* instruments have the better density — the opposite of the textbook "short beats long" story. `SHADOW_PRICE` is the best implementable method in all three variants (it even exceeds `ORACLE_DENSITY` in variant 2, which confirms that the greedy oracle is not an upper bound; only the LP is). Long positions hold 65–68 % of slot-hours under both `RANK_NET` and `SLOTHOUR_DENSITY`: **long-slot capture is not fixed by density ranking alone.**

5. **Minimum-holding constraints as a stand-alone rule** were only tested inside `EVICT_SWAP` and `OLDEST_SLOT` (grid 0/3/6/12 h); the best (12) is the maximum tested — the grid edge is reported, not extended, because gains were already marginal.

`BEST_TURNOVER_REFERENCE` (descriptive): **`SHADOW_PRICE`** (opportunity-cost threshold; +0.016 dz, no forced exits) — statistically tied with `ONLINE_KNAPSACK_PSI` (paired difference between them ≈ 0.001). `EVICT_SWAP` is the only *explicit turnover* rule with a positive sign, and it is an order of magnitude smaller.
