# 05 — Slot economics

All numbers: held-out, mean over 15 families × 3 variants × 10 seeds × 4 caps (52,200 runs), bps per slot-hour of **latent expected net outcome** (`lat_*`, costs explicit) unless labelled `real_*` (realised path). `utilisation = 1 − idle`. `hq_missed_frac` = share of *unique* high-quality opps (top-quartile value density and positive value) that expired unadmitted; split into **capacity-forced** (never saw a free slot: `hq_missed_capacity`) vs **declined with a free slot** (`hq_declined_with_free_slot`). `v0_*` = value the opp would have had if admitted on arrival, averaged per unique opp. `opp_cost_missed…` = value of missed HQ opps per available slot-hour.

| policy | lat_per_slot_hour | real_per_slot_hour | lat_per_used_hour | utilisation | idle | mean_hold | admit_per_slot_hour | v0_admitted_mean | v0_rejected_mean | hq_missed_frac | hq_missed_capacity | hq_declined_with_free_slot | opp_cost_missed_value_per_slot_hour | evals_per_opp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE_DENSITY_NOT_IMPLEMENTABLE | 0.874 | 0.872 | 1.177 | 0.734 | 0.266 | 14.080 | 0.057 | 18.014 | -3.492 | 0.222 | 0.221 | 0.001 | 0.371 | 2.944 |
| ORACLE_SCORE_NOT_IMPLEMENTABLE | 0.830 | 0.828 | 1.122 | 0.741 | 0.259 | 15.328 | 0.053 | 18.945 | -3.282 | 0.281 | 0.280 | 0.001 | 0.439 | 2.979 |
| COMPOSED | 0.644 | 0.646 | 0.858 | 0.725 | 0.275 | 13.718 | 0.057 | 13.083 | -1.553 | 0.357 | 0.224 | 0.133 | 0.490 | 2.987 |
| SHADOW_PRICE | 0.598 | 0.599 | 0.796 | 0.734 | 0.266 | 13.245 | 0.063 | 12.258 | -1.642 | 0.340 | 0.231 | 0.109 | 0.490 | 2.933 |
| ONLINE_KNAPSACK_PSI | 0.596 | 0.590 | 0.843 | 0.696 | 0.304 | 12.785 | 0.062 | 12.655 | -1.375 | 0.332 | 0.203 | 0.130 | 0.490 | 3.002 |
| UNCERTAINTY_LCB | 0.592 | 0.589 | 0.749 | 0.769 | 0.231 | 14.963 | 0.056 | 13.370 | -1.411 | 0.400 | 0.322 | 0.078 | 0.542 | 3.021 |
| FLUID_QUANTILE | 0.587 | 0.588 | 0.798 | 0.738 | 0.262 | 13.079 | 0.065 | 11.847 | -1.574 | 0.332 | 0.220 | 0.112 | 0.486 | 2.923 |
| MARGINAL_RISK | 0.585 | 0.587 | 0.778 | 0.751 | 0.249 | 14.250 | 0.058 | 13.354 | -1.256 | 0.377 | 0.304 | 0.073 | 0.529 | 3.027 |
| SLEEPING_HEDGE | 0.580 | 0.574 | 0.722 | 0.798 | 0.202 | 14.917 | 0.059 | 13.053 | -1.577 | 0.383 | 0.343 | 0.040 | 0.537 | 2.985 |
| TRUNK_RESERVATION | 0.572 | 0.573 | 0.778 | 0.732 | 0.268 | 12.882 | 0.065 | 11.486 | -1.322 | 0.327 | 0.168 | 0.159 | 0.493 | 2.931 |
| CORR_PENALTY | 0.570 | 0.568 | 0.719 | 0.790 | 0.210 | 14.802 | 0.059 | 12.949 | -1.482 | 0.387 | 0.340 | 0.047 | 0.541 | 2.992 |
| RANK_NET_MISSING_REJECT | 0.569 | 0.567 | 0.721 | 0.780 | 0.220 | 14.886 | 0.057 | 12.992 | -1.408 | 0.401 | 0.333 | 0.069 | 0.548 | 3.008 |
| CLUSTER_CAP | 0.569 | 0.566 | 0.711 | 0.796 | 0.204 | 14.872 | 0.059 | 12.876 | -1.493 | 0.388 | 0.341 | 0.047 | 0.541 | 2.985 |
| RANK_NET | 0.569 | 0.567 | 0.709 | 0.798 | 0.202 | 14.888 | 0.059 | 12.883 | -1.509 | 0.388 | 0.347 | 0.041 | 0.541 | 2.984 |
| SLOTHOUR_DENSITY | 0.567 | 0.564 | 0.710 | 0.796 | 0.204 | 14.220 | 0.062 | 12.288 | -1.559 | 0.367 | 0.326 | 0.041 | 0.520 | 2.960 |
| RANK_NET_UNKCOST_ZERO | 0.560 | 0.556 | 0.692 | 0.804 | 0.196 | 14.856 | 0.059 | 12.636 | -1.471 | 0.389 | 0.353 | 0.036 | 0.543 | 2.971 |
| EVICT_SWAP | 0.558 | 0.560 | 0.709 | 0.789 | 0.211 | 12.155 | 0.074 | 11.389 | -2.365 | 0.285 | 0.244 | 0.041 | 0.436 | 2.822 |
| SLOTHOUR_HAZARD | 0.547 | 0.543 | 0.691 | 0.795 | 0.205 | 13.759 | 0.065 | 11.458 | -1.444 | 0.356 | 0.315 | 0.041 | 0.519 | 2.942 |
| CORR_HARD_REJECT | 0.546 | 0.545 | 0.721 | 0.749 | 0.251 | 14.162 | 0.057 | 11.931 | -0.298 | 0.408 | 0.298 | 0.109 | 0.560 | 3.019 |
| LIN_TS | 0.526 | 0.524 | 0.679 | 0.677 | 0.323 | 14.301 | 0.052 | 12.439 | -0.160 | 0.433 | 0.252 | 0.181 | 0.588 | 3.100 |
| RANK_SCORE_RAW | 0.523 | 0.519 | 0.611 | 0.834 | 0.166 | 14.802 | 0.062 | 11.376 | -1.606 | 0.394 | 0.378 | 0.016 | 0.548 | 2.902 |
| LINUCB | 0.520 | 0.519 | 0.633 | 0.791 | 0.209 | 15.253 | 0.057 | 12.020 | -0.591 | 0.408 | 0.340 | 0.069 | 0.567 | 2.949 |
| FIFO_NETPOS | 0.422 | 0.421 | 0.553 | 0.802 | 0.198 | 14.522 | 0.060 | 10.969 | -0.925 | 0.413 | 0.375 | 0.038 | 0.596 | 3.114 |
| EQUAL_QUOTA | 0.250 | 0.251 | 0.284 | 0.861 | 0.139 | 14.423 | 0.064 | 6.192 | 4.162 | 0.469 | 0.469 | 0.000 | 0.651 | 2.875 |
| ROUND_ROBIN | 0.241 | 0.243 | 0.275 | 0.859 | 0.141 | 14.292 | 0.064 | 5.853 | 4.236 | 0.471 | 0.468 | 0.003 | 0.657 | 2.875 |
| SECRETARY_1_OVER_E | 0.209 | 0.208 | 1.859 | 0.130 | 0.870 | 9.879 | 0.014 | 16.837 | 3.817 | 0.809 | 0.008 | 0.801 | 0.870 | 3.765 |
| RANDOM_SEEDED | 0.190 | 0.185 | 0.224 | 0.860 | 0.140 | 14.045 | 0.067 | 5.111 | 4.489 | 0.479 | 0.479 | 0.000 | 0.680 | 2.811 |
| FIFO | 0.162 | 0.158 | 0.194 | 0.863 | 0.137 | 14.218 | 0.066 | 5.519 | 4.286 | 0.474 | 0.474 | 0.000 | 0.667 | 3.042 |
| OLDEST_SLOT | -0.019 | -0.020 | 0.009 | 0.853 | 0.147 | 10.007 | 0.094 | 5.295 | 3.861 | 0.314 | 0.314 | 0.000 | 0.465 | 2.621 |

## Reading (all OBSERVED on the synthetic environment)
1. **Outcome per slot-hour, not per trade.** `FIFO` earns 0.162 bps/slot-hour with 86 % utilisation; `RANK_NET` 0.62 at cap 4 (see 08); the best composed method 0.71 at cap 4. Utilisation is *not* the objective: the methods that win (`SHADOW_PRICE`, `ONLINE_KNAPSACK_PSI`, `FLUID_QUANTILE`, `COMPOSED`) run ≈ 6–14 points *less* utilised than `RANK_NET` — they deliberately leave a slot idle rather than fill it with a marginal opportunity. That is opportunity-cost pricing showing up in the data.
2. **Rejected-opportunity quality.** Admitted opps have a much higher mean `v0` than rejected ones for every value-aware method; for `FIFO`/`RANDOM`/`ROUND_ROBIN` the two are close. FIFO's problem in this simulator is not only *what* it admits but *when*: `evals_per_opp` ≈ 3 shows that each unique opp sits in the pool ~3 evaluations, and FIFO always serves the stalest first (edge decays with a time constant of 8 h in the environment; INFERENCE that real decay differs — UNKNOWN).
3. **Missed high-quality opportunities.** Under saturation FIFO misses 65–69 % of HQ opps at caps 4/6 in the chronic and spam families (S3 0.68, S10 0.65, H1 0.69, H3 0.67), almost all capacity-forced (`hq_missed_capacity` ≈ `hq_missed_frac`). `RANK_NET` cuts S3 to 0.44 and S10 to 0.49; `COMPOSED` to 0.35 and 0.38. The composed method deliberately trades some HQ opps *declined with a free slot* (its thresholding) for higher net value. Not every family improves: in S6 `RANK_NET` misses *more* HQ opps than FIFO (0.70 vs 0.66) because its value ranking prefers long slow positions that hold slots (mean hold 27 h vs 19 h), yet it still earns more per slot-hour.
4. **Do not count repeats as independent.** With ttl = 3 the same opp is re-shown up to 4 times; all rejected-opportunity metrics above are per unique opp. Counting evaluations instead would inflate FIFO's "reject count" by ≈ 3× (chronic: 3.66×) without adding a single independent opportunity.
5. **Regret against the hindsight LP** (upper bound, not implementable; per slot-hour, lower is better):

| policy | 3 | 4 | 6 | 10 |
|---|---|---|---|---|
| ORACLE_DENSITY_NOT_IMPLEMENTABLE | 0.415 | 0.299 | 0.163 | 0.052 |
| ORACLE_SCORE_NOT_IMPLEMENTABLE | 0.492 | 0.356 | 0.194 | 0.063 |
| COMPOSED | 0.654 | 0.552 | 0.403 | 0.242 |
| SHADOW_PRICE | 0.722 | 0.599 | 0.440 | 0.275 |
| ONLINE_KNAPSACK_PSI | 0.738 | 0.594 | 0.431 | 0.277 |
| UNCERTAINTY_LCB | 0.762 | 0.618 | 0.431 | 0.247 |
| FLUID_QUANTILE | 0.723 | 0.607 | 0.458 | 0.289 |
| MARGINAL_RISK | 0.756 | 0.617 | 0.443 | 0.271 |
| SLEEPING_HEDGE | 0.778 | 0.630 | 0.441 | 0.257 |
| TRUNK_RESERVATION | 0.752 | 0.627 | 0.465 | 0.294 |
| CORR_PENALTY | 0.787 | 0.638 | 0.451 | 0.269 |
| RANK_NET_MISSING_REJECT | 0.780 | 0.637 | 0.454 | 0.276 |
| CLUSTER_CAP | 0.786 | 0.643 | 0.453 | 0.269 |
| RANK_NET | 0.786 | 0.640 | 0.454 | 0.271 |
| SLOTHOUR_DENSITY | 0.781 | 0.640 | 0.458 | 0.278 |
| RANK_NET_UNKCOST_ZERO | 0.796 | 0.649 | 0.463 | 0.278 |
| EVICT_SWAP | 0.776 | 0.643 | 0.476 | 0.298 |
| SLOTHOUR_HAZARD | 0.806 | 0.662 | 0.478 | 0.292 |
| CORR_HARD_REJECT | 0.790 | 0.647 | 0.474 | 0.329 |
| LIN_TS | 0.853 | 0.692 | 0.484 | 0.291 |
| RANK_SCORE_RAW | 0.835 | 0.686 | 0.499 | 0.313 |
| LINUCB | 0.864 | 0.706 | 0.495 | 0.280 |
| FIFO_NETPOS | 0.988 | 0.819 | 0.587 | 0.343 |
| EQUAL_QUOTA | 1.197 | 1.003 | 0.751 | 0.473 |
| ROUND_ROBIN | 1.200 | 1.016 | 0.764 | 0.480 |
| SECRETARY_1_OVER_E | 1.135 | 1.012 | 0.833 | 0.610 |
| RANDOM_SEEDED | 1.256 | 1.073 | 0.813 | 0.523 |
| FIFO | 1.287 | 1.099 | 0.844 | 0.547 |
| OLDEST_SLOT | 1.521 | 1.320 | 1.023 | 0.636 |

   The LP relaxation lets a perfect scheduler choose admission time within `ttl` with true values/durations. Even `ORACLE_DENSITY` captures only 71–93 % of it (cap 3 → 10), so a large part of the gap is *irreducible with a greedy online rule*, not a defect of any tested method.

## Per-family view (caps 4 and 6): FIFO vs RANK_NET vs COMPOSED
| family | policy | regret_lp | hq_missed_frac | hq_missed_capacity | hhi_cluster | lat_per_slot_hour | utilisation | mean_hold |
|---|---|---|---|---|---|---|---|---|
| H1_chronic_corr_regime | FIFO | 1.580 | 0.687 | 0.687 | 0.612 | 0.140 | 0.993 | 14.671 |
| H1_chronic_corr_regime | RANK_NET | 0.993 | 0.586 | 0.410 | 0.689 | 0.727 | 0.918 | 14.521 |
| H1_chronic_corr_regime | COMPOSED | 0.901 | 0.526 | 0.301 | 0.706 | 0.819 | 0.866 | 13.368 |
| H2_burst_noisy_missing | FIFO | 0.610 | 0.527 | 0.527 | 0.440 | 0.072 | 0.918 | 16.131 |
| H2_burst_noisy_missing | RANK_NET | 0.446 | 0.471 | 0.409 | 0.460 | 0.236 | 0.848 | 16.193 |
| H2_burst_noisy_missing | COMPOSED | 0.438 | 0.522 | 0.270 | 0.527 | 0.245 | 0.702 | 15.617 |
| H3_spam_fastslow | FIFO | 1.853 | 0.674 | 0.674 | 0.420 | 0.217 | 0.998 | 10.395 |
| H3_spam_fastslow | RANK_NET | 1.053 | 0.640 | 0.636 | 0.429 | 1.017 | 0.992 | 14.846 |
| H3_spam_fastslow | COMPOSED | 0.832 | 0.560 | 0.401 | 0.460 | 1.238 | 0.901 | 12.646 |
| S10_spam | FIFO | 1.651 | 0.654 | 0.654 | 0.575 | -0.479 | 0.998 | 10.776 |
| S10_spam | RANK_NET | 0.882 | 0.486 | 0.477 | 0.665 | 0.289 | 0.983 | 10.737 |
| S10_spam | COMPOSED | 0.550 | 0.381 | 0.243 | 0.580 | 0.622 | 0.851 | 9.706 |
| S11_burst | FIFO | 0.525 | 0.340 | 0.340 | 0.503 | 0.095 | 0.762 | 13.726 |
| S11_burst | RANK_NET | 0.173 | 0.182 | 0.171 | 0.571 | 0.447 | 0.614 | 13.426 |
| S11_burst | COMPOSED | 0.169 | 0.162 | 0.151 | 0.574 | 0.451 | 0.606 | 13.155 |
| S12_all_equal | FIFO | 0.397 | 0.578 | 0.578 | 0.414 | 0.246 | 0.971 | 11.079 |
| S12_all_equal | RANK_NET | 0.160 | 0.525 | 0.520 | 0.415 | 0.483 | 0.965 | 11.083 |
| S12_all_equal | COMPOSED | 0.168 | 0.523 | 0.259 | 0.454 | 0.475 | 0.852 | 10.921 |
| S1_sparse | FIFO | 0.051 | 0.001 | 0.001 | 0.900 | 0.032 | 0.110 | 9.594 |
| S1_sparse | RANK_NET | 0.018 | 0.020 | 0.002 | 0.925 | 0.065 | 0.083 | 9.629 |
| S1_sparse | COMPOSED | 0.018 | 0.020 | 0.002 | 0.926 | 0.065 | 0.083 | 9.623 |
| S2_moderate | FIFO | 0.465 | 0.155 | 0.155 | 0.540 | 0.107 | 0.668 | 14.545 |
| S2_moderate | RANK_NET | 0.137 | 0.071 | 0.062 | 0.621 | 0.434 | 0.515 | 14.398 |
| S2_moderate | COMPOSED | 0.136 | 0.064 | 0.055 | 0.622 | 0.436 | 0.513 | 14.341 |
| S3_chronic | FIFO | 1.503 | 0.682 | 0.682 | 0.420 | 0.016 | 0.994 | 13.574 |
| S3_chronic | RANK_NET | 0.671 | 0.443 | 0.431 | 0.422 | 0.848 | 0.960 | 13.345 |
| S3_chronic | COMPOSED | 0.542 | 0.347 | 0.299 | 0.436 | 0.977 | 0.910 | 11.855 |
| S4_late_quality | FIFO | 0.494 | 0.433 | 0.433 | 0.444 | 0.411 | 0.913 | 19.695 |
| S4_late_quality | RANK_NET | 0.319 | 0.344 | 0.329 | 0.456 | 0.585 | 0.867 | 19.479 |
| S4_late_quality | COMPOSED | 0.280 | 0.298 | 0.274 | 0.465 | 0.624 | 0.844 | 18.548 |
| S5_correlated | FIFO | 0.869 | 0.507 | 0.507 | 0.622 | 0.214 | 0.955 | 16.344 |
| S5_correlated | RANK_NET | 0.380 | 0.323 | 0.309 | 0.664 | 0.703 | 0.884 | 16.273 |
| S5_correlated | COMPOSED | 0.342 | 0.277 | 0.255 | 0.672 | 0.741 | 0.858 | 15.440 |
| S6_short_vs_long | FIFO | 1.428 | 0.658 | 0.658 | 0.433 | 1.225 | 0.973 | 19.105 |
| S6_short_vs_long | RANK_NET | 1.045 | 0.701 | 0.691 | 0.429 | 1.608 | 0.965 | 27.320 |
| S6_short_vs_long | COMPOSED | 0.990 | 0.545 | 0.374 | 0.488 | 1.663 | 0.858 | 20.283 |
| S7_regime_shift | FIFO | 1.039 | 0.613 | 0.613 | 0.424 | 0.046 | 0.978 | 16.840 |
| S7_regime_shift | RANK_NET | 0.605 | 0.467 | 0.309 | 0.479 | 0.480 | 0.865 | 16.192 |
| S7_regime_shift | COMPOSED | 0.573 | 0.432 | 0.241 | 0.490 | 0.511 | 0.821 | 15.304 |
| S8_noisy_ranking | FIFO | 1.073 | 0.556 | 0.556 | 0.424 | 0.041 | 0.968 | 14.547 |
| S8_noisy_ranking | RANK_NET | 0.692 | 0.425 | 0.382 | 0.433 | 0.422 | 0.918 | 14.301 |
| S8_noisy_ranking | COMPOSED | 0.635 | 0.415 | 0.276 | 0.474 | 0.479 | 0.846 | 13.597 |
| S9_missing_quality | FIFO | 1.035 | 0.537 | 0.537 | 0.423 | 0.038 | 0.971 | 12.459 |
| S9_missing_quality | RANK_NET | 0.632 | 0.413 | 0.358 | 0.441 | 0.442 | 0.907 | 12.262 |
| S9_missing_quality | COMPOSED | 0.591 | 0.469 | 0.194 | 0.492 | 0.483 | 0.774 | 12.072 |
