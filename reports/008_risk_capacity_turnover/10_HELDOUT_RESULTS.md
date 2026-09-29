# 10 — Held-out results (H1: K=4, 13 scenarios × 20 seeds, frozen parameters, executed once)

## Headline metric M1 (macro over scenarios), regret and paired effects
| policy | net_per_avail_slot_hour | regret_vs_oracle_M1 | net_total | vsFIFO_macro_diff | vsFIFO_lo | vsFIFO_hi | vsFIFO_wins | vsFIFO_SCREEN_macro_diff | vsFIFO_SCREEN_lo | vsFIFO_SCREEN_hi | vsFIFO_SCREEN_wins |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FIFO | 1.781 | 3.938 | 4273.522 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| ROUND_ROBIN | 1.775 | 3.944 | 4259.479 | -0.006 | -0.050 | 0.035 | 8.000 | -0.170 | -0.216 | -0.127 | 2.000 |
| RANDOM | 1.739 | 3.980 | 4172.996 | -0.042 | -0.087 | 0.001 | 6.000 | -0.206 | -0.249 | -0.158 | 2.000 |
| EQUAL_QUOTA | 1.740 | 3.979 | 4175.573 | -0.041 | -0.082 | 0.002 | 5.000 | -0.205 | -0.247 | -0.161 | 2.000 |
| OLDEST_SLOT | 1.966 | 3.753 | 4717.724 | 0.185 | 0.140 | 0.229 | 10.000 | 0.021 | -0.022 | 0.066 | 6.000 |
| FIFO_SCREEN | 1.944 | 3.775 | 4666.656 | 0.164 | 0.124 | 0.205 | 11.000 | n/a | n/a | n/a | n/a |
| SCORE_RANK | 2.145 | 3.574 | 5149.157 | 0.365 | 0.319 | 0.413 | 12.000 | 0.201 | 0.156 | 0.246 | 12.000 |
| SLOTHOUR | 2.216 | 3.503 | 5317.898 | 0.435 | 0.388 | 0.479 | 13.000 | 0.271 | 0.229 | 0.315 | 13.000 |
| SLOTHOUR_SHADOW | 2.225 | 3.494 | 5339.540 | 0.444 | 0.395 | 0.495 | 12.000 | 0.280 | 0.235 | 0.324 | 11.000 |
| UNCERTAINTY_LCB | 2.278 | 3.441 | 5466.471 | 0.497 | 0.449 | 0.545 | 13.000 | 0.333 | 0.289 | 0.379 | 13.000 |
| CORR_AWARE | 2.194 | 3.525 | 5265.904 | 0.413 | 0.366 | 0.462 | 13.000 | 0.250 | 0.205 | 0.294 | 13.000 |
| LINTS | 2.196 | 3.523 | 5271.043 | 0.416 | 0.365 | 0.464 | 13.000 | 0.252 | 0.207 | 0.300 | 13.000 |
| ORACLE_GREEDY_UB | 5.719 | 0.000 | 13725.715 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

`vsFIFO_*`: paired bootstrap (2000 resamples over seeds, per-scenario, then macro-mean) of policy − FIFO(RAW); `wins` = scenarios with positive point estimate (of 13). Regret is vs ORACLE_GREEDY_UB (upper reference, not implementable).

vs RANDOM (paired macro): FIFO +0.042 [-0.001,+0.087], FIFO_SCREEN +0.206 [+0.159,+0.250], SLOTHOUR +0.477 [+0.424,+0.529], UNCERTAINTY_LCB +0.539 [+0.493,+0.587].

vs best simple method (SLOTHOUR): SCORE_RANK -0.070 [-0.109,-0.031], SLOTHOUR_SHADOW +0.009 [-0.026,+0.044], UNCERTAINTY_LCB +0.062 [+0.026,+0.099], CORR_AWARE -0.022 [-0.051,+0.009], LINTS -0.020 [-0.054,+0.017], OLDEST_SLOT -0.250 [-0.296,-0.205], FIFO_SCREEN -0.271 [-0.310,-0.229].

## Per-scenario paired difference vs raw FIFO (bps/avail-slot-hour; `*` = CI excludes 0 upward, `↓` = downward)
| scen | CORR_AWARE | LINTS | OLDEST_SLOT | SCORE_RANK | SLOTHOUR | SLOTHOUR_SHDW | UNCERT_LCB |
|---|---|---|---|---|---|---|---|
| S10_spam | +0.28 * | +0.24 * | +0.15 | +0.22 * | +0.26 * | +0.23 * | +0.27 * |
| S11_burst | +0.23 * | +0.22 * | -0.04 | +0.19 * | +0.24 * | +0.22 * | +0.25 * |
| S12_near_equal | +0.36 * | +0.24 * | +0.23 * | +0.29 * | +0.32 * | +0.27 * | +0.46 * |
| S1_sparse | +0.01 | +0.01 | +0.01 | +0.01 | +0.01 | -0.04 | +0.00 |
| S2_moderate | +0.18 * | +0.15 * | +0.06 | +0.18 * | +0.19 * | +0.05 | +0.14 * |
| S3_chronic | +0.96 * | +1.03 * | +0.27 * | +0.90 * | +1.09 * | +1.18 * | +1.13 * |
| S4_late_hq | +0.29 * | +0.33 * | +0.55 * | +0.28 * | +0.33 * | +0.59 * | +0.39 * |
| S5_correlated | +0.38 * | +0.38 * | -0.08 | +0.33 * | +0.38 * | +0.40 * | +0.42 * |
| S5b_corr_benign | +0.50 * | +0.44 * | -0.09 | +0.40 * | +0.55 * | +0.66 * | +0.52 * |
| S6_short_vs_long | +0.15 * | +0.35 * | +0.70 * | -0.10 | +0.25 * | +0.23 * | +0.30 * |
| S7_regime_shift | +0.87 * | +0.88 * | +0.29 * | +0.90 * | +0.86 * | +0.91 * | +0.95 * |
| S8_noisy_rank | +0.52 * | +0.59 * | +0.15 | +0.51 * | +0.48 * | +0.43 * | +0.74 * |
| S9_missing | +0.66 * | +0.54 * | +0.18 | +0.64 * | +0.70 * | +0.67 * | +0.87 * |

## Other pre-registered metrics (macro, heldout)
| policy | net_per_busy_slot_hour | turnover_per_slot_hour | idle_slot_hours | hhi_inst | hhi_group | starve_soft_rate | max_denial_hours | rej_rate_instw | hq_capture | pnl_std | worst_24h | max_drawdown | churn_reentry_frac | occ_std | mean_hold |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIFO | 2.028 | 0.104 | 292.723 | 0.094 | 0.231 | 0.016 | 214.773 | 3.461 | 0.638 | 11.557 | -176.586 | 263.515 | 0.305 | 0.129 | 8.753 |
| ROUND_ROBIN | 2.024 | 0.104 | 296.138 | 0.090 | 0.223 | 0.008 | 193.369 | 3.417 | 0.660 | 11.471 | -174.790 | 249.654 | 0.259 | 0.131 | 8.755 |
| RANDOM | 1.986 | 0.104 | 298.862 | 0.092 | 0.226 | 0.008 | 205.150 | 3.344 | 0.644 | 11.600 | -174.411 | 265.751 | 0.305 | 0.132 | 8.711 |
| EQUAL_QUOTA | 1.985 | 0.102 | 295.308 | 0.083 | 0.216 | 0.000 | 132.669 | 3.486 | 0.623 | 11.423 | -174.315 | 249.400 | 0.227 | 0.130 | 8.842 |
| OLDEST_SLOT | 2.256 | 0.196 | 320.304 | 0.087 | 0.226 | 0.007 | 104.958 | 3.495 | 0.934 | 15.624 | -200.156 | 305.075 | 0.441 | 0.140 | 5.041 |
| FIFO_SCREEN | 2.304 | 0.100 | 371.323 | 0.097 | 0.232 | 0.023 | 247.592 | 3.033 | 0.698 | 11.427 | -149.076 | 228.573 | 0.307 | 0.155 | 8.737 |
| SCORE_RANK | 2.543 | 0.098 | 379.369 | 0.098 | 0.232 | 0.039 | 289.915 | 2.818 | 0.700 | 11.582 | -139.848 | 216.330 | 0.336 | 0.159 | 8.935 |
| SLOTHOUR | 2.628 | 0.104 | 382.854 | 0.092 | 0.228 | 0.031 | 272.692 | 2.706 | 0.742 | 11.826 | -131.504 | 207.048 | 0.339 | 0.161 | 8.379 |
| SLOTHOUR_SHADOW | 2.845 | 0.100 | 510.385 | 0.095 | 0.232 | 0.058 | 324.988 | 2.701 | 0.729 | 11.779 | -114.886 | 182.222 | 0.343 | 0.195 | 8.158 |
| UNCERTAINTY_LCB | 2.657 | 0.106 | 359.354 | 0.095 | 0.231 | 0.059 | 330.496 | 2.767 | 0.752 | 11.958 | -133.851 | 206.298 | 0.364 | 0.153 | 8.363 |
| CORR_AWARE | 2.604 | 0.104 | 382.688 | 0.092 | 0.227 | 0.029 | 272.427 | 2.713 | 0.741 | 11.764 | -128.336 | 201.053 | 0.337 | 0.161 | 8.376 |
| LINTS | 2.607 | 0.105 | 383.331 | 0.091 | 0.227 | 0.027 | 260.823 | 2.735 | 0.743 | 11.908 | -127.326 | 204.378 | 0.338 | 0.161 | 8.345 |
| ORACLE_GREEDY_UB | 6.660 | 0.121 | 376.496 | 0.088 | 0.223 | 0.012 | 197.304 | 1.530 | 0.889 | 12.035 | 255.450 | 0.000 | 0.331 | 0.170 | 7.361 |

(no composite score is computed by design; each metric must be read on its own.)

## Robustness to score noise (validation-split OFAT on S3; 8 seeds; M1)
| lvl | FIFO | FIFO_SCREEN | SCORE_RANK | SLOTHOUR | SLOTHOUR_SHDW | UNCERT_LCB | CORR_AWARE | LINTS |
|---|---|---|---|---|---|---|---|---|
| 0.000 | 1.894 | 2.397 | 3.150 | 2.980 | 3.385 | 3.140 | 3.249 | 3.208 |
| 0.500 | 1.894 | 2.118 | 3.169 | 3.173 | 3.229 | 3.015 | 3.036 | 3.161 |
| 1.000 | 1.894 | 2.364 | 3.002 | 3.141 | 3.072 | 3.153 | 3.191 | 3.086 |
| 2.000 | 1.894 | 2.290 | 2.691 | 2.639 | 2.604 | 2.886 | 2.724 | 2.747 |
| 4.000 | 1.894 | 2.359 | 2.433 | 2.351 | 2.403 | 2.805 | 2.397 | 2.651 |
(index = score-noise multiplier τ/τ₀; 0 = perfect score, **upper bound only**). Sensitivity slope (M1 lost from τ×0.5 to ×4): SCORE_RANK 0.74, SLOTHOUR 0.82, UNCERTAINTY_LCB 0.21, LINTS 0.51: UNCERTAINTY_LCB is the least noise-sensitive of the four; at τ×4 it keeps a clear lead over SLOTHOUR.

## Other robustness axes (validation OFAT on S3; full table `results/analysis/D1_robustness_table.csv`)
| fam | lvl | FIFO | FIFO_SCREEN | SCORE_RANK | SLOTHOUR | UNCERT_LCB | LINTS | OLDEST_SLOT | best_impl_minus_FIFO |
|---|---|---|---|---|---|---|---|---|---|
| correlation | 0.1 | 1.972 | 2.450 | 3.083 | 3.213 | 3.244 | 3.162 | 2.215 | 1.300 |
| correlation | 0.35 | 1.894 | 2.364 | 3.002 | 3.141 | 3.153 | 3.086 | 2.161 | 1.297 |
| correlation | 0.6 | 1.823 | 2.273 | 2.910 | 3.060 | 3.050 | 2.929 | 2.117 | 1.268 |
| correlation | 0.85 | 1.764 | 2.171 | 2.799 | 2.965 | 2.924 | 2.796 | 2.093 | 1.201 |
| duration_dist | ln_cv0.3 | 1.830 | 2.038 | 2.923 | 2.943 | 3.023 | 2.926 | 1.584 | 1.194 |
| duration_dist | ln_cv0.6 | 1.761 | 2.118 | 2.720 | 2.902 | 2.997 | 2.766 | 2.036 | 1.236 |
| duration_dist | ln_cv1.2 | 2.197 | 2.215 | 2.793 | 2.880 | 3.070 | 2.900 | 2.754 | 0.880 |
| duration_dist | pareto | 2.149 | 2.398 | 3.056 | 3.117 | 3.378 | 3.123 | 2.134 | 1.229 |
| load | 1.0 | 1.324 | 1.453 | 1.487 | 1.479 | 1.567 | 1.486 | 1.462 | 0.243 |
| load | 2.0 | 1.837 | 2.128 | 2.290 | 2.288 | 2.427 | 2.324 | 2.038 | 0.590 |
| load | 3.5 | 1.894 | 2.364 | 3.002 | 3.141 | 3.153 | 3.086 | 2.161 | 1.297 |
| load | 6.0 | 2.242 | 2.160 | 3.326 | 3.476 | 3.853 | 3.443 | 2.425 | 1.611 |
| regime_persistence | 0.0003333333333333333 | 1.917 | 2.393 | 2.965 | 3.104 | 3.191 | 3.082 | 2.177 | 1.274 |
| regime_persistence | 0.0033333333333333335 | 1.894 | 2.364 | 3.002 | 3.141 | 3.153 | 3.086 | 2.161 | 1.297 |
| regime_persistence | 0.01 | 1.844 | 2.432 | 2.850 | 2.954 | 3.031 | 2.925 | 2.090 | 1.187 |
| regime_persistence | 0.03333333333333333 | 1.850 | 2.279 | 2.926 | 2.864 | 3.079 | 2.966 | 2.111 | 1.229 |
Ordering FIFO ≺ FIFO_SCREEN ≺ ranking family is stable across arrival intensity (except L=1.0, where all methods are within ≈0.25), correlation and regime persistence; with very dispersed durations (lognormal CV 1.2) **OLDEST_SLOT** gains +0.55 over FIFO (but stays below the ranking methods); under Pareto durations it gains nothing (2.13 vs 2.15) — preemption helps only for some duration shapes.

## Parameter sensitivity of finalists (validation split, 13 scenarios × 8 seeds, frozen ingest)
| params | CORR_AWARE | LINTS | OLDEST_SLOT | SLOTHOUR_SHDW | UNCERT_LCB |
|---|---|---|---|---|---|
| {"alpha": 0.1} | n/a | 2.325 | n/a | n/a | n/a |
| {"alpha": 0.3} | n/a | 2.331 | n/a | n/a | n/a |
| {"alpha": 0.6} | n/a | 2.317 | n/a | n/a | n/a |
| {"gamma": 0.02} | 2.315 | n/a | n/a | n/a | n/a |
| {"gamma": 0.05} | 2.319 | n/a | n/a | n/a | n/a |
| {"gamma": 0.1} | 2.312 | n/a | n/a | n/a | n/a |
| {"gamma": 0.2} | 2.327 | n/a | n/a | n/a | n/a |
| {"gamma": 0.4} | 2.328 | n/a | n/a | n/a | n/a |
| {"kappa": 0.0, "omega": 0.0} | n/a | n/a | n/a | n/a | 2.349 |
| {"kappa": 0.0, "omega": 0.3} | n/a | n/a | n/a | n/a | 2.370 |
| {"kappa": 0.0, "omega": 0.6} | n/a | n/a | n/a | n/a | 2.418 |
| {"kappa": 0.1, "omega": 0.0} | n/a | n/a | n/a | n/a | 2.344 |
| {"kappa": 0.1, "omega": 0.3} | n/a | n/a | n/a | n/a | 2.368 |
| {"kappa": 0.1, "omega": 0.6} | n/a | n/a | n/a | n/a | 2.377 |
| {"kappa": 0.3, "omega": 0.0} | n/a | n/a | n/a | n/a | 2.307 |
| {"kappa": 0.3, "omega": 0.3} | n/a | n/a | n/a | n/a | 2.364 |
| {"kappa": 0.3, "omega": 0.6} | n/a | n/a | n/a | n/a | 2.380 |
| {"min_hold": 2} | n/a | n/a | 2.093 | n/a | n/a |
| {"min_hold": 4} | n/a | n/a | 2.271 | n/a | n/a |
| {"min_hold": 8} | n/a | n/a | 2.193 | n/a | n/a |
| {"theta": 0.25} | n/a | n/a | n/a | 2.344 | n/a |
| {"theta": 0.5} | n/a | n/a | n/a | 2.053 | n/a |
| {"theta": 0.75} | n/a | n/a | n/a | 1.068 | n/a |
| {"theta": 1.0} | n/a | n/a | n/a | 0.399 | n/a |
| {"theta": 1.25} | n/a | n/a | n/a | 0.189 | n/a |
- UNCERTAINTY_LCB: the ω (shrinkage) axis matters (0→0.6: +0.07); κ (risk penalty) does not help (κ=0 best at ω=0.6). The frozen point is on the *edge* of the ω grid (0.6) — the optimum may lie beyond (UNKNOWN; ω>0.6 not tested).
- CORR_AWARE γ and LINTS α are flat (±0.01).
- SLOTHOUR_SHADOW θ is steeply sensitive (0.25→1.25: 2.34→0.19). OLDEST_SLOT min_hold: 4 best, 2 worst.

## FIFO failure / equivalence (pre-registered rule; candidate set = SCORE_RANK, SLOTHOUR, SLOTHOUR_SHADOW, UNCERTAINTY_LCB, CORR_AWARE, LINTS)
δ = 0.25 (primary):
- vs raw FIFO — **failure:** S12, S3, S4, S5, S5b, S7, S8, S9; **equivalent:** S10, S11, S1, S2, S6.
- vs FIFO_SCREEN — failure: S3, S4, S5b, S7, S8, S9; equivalent: S10, S11, S12, S1, S2, S5, S6.

Sensitivity to δ:
| delta | n_failure_vs_FIFO | failure_vs_FIFO | n_equiv_vs_FIFO | n_failure_vs_FIFO_SCREEN | failure_vs_FIFO_SCREEN |
|---|---|---|---|---|---|
| 0.1 | 11 | S10, S11, S12, S3, S4, S5, S5b, S6, S7, S8, S9 | 2 | 9 | S11, S12, S3, S4, S5b, S6, S7, S8, S9 |
| 0.25 | 8 | S12, S3, S4, S5, S5b, S7, S8, S9 | 5 | 6 | S3, S4, S5b, S7, S8, S9 |
| 0.5 | 4 | S3, S7, S8, S9 | 9 | 1 | S3 |

Two flags: (1) S6 is "equivalent" for the *pre-registered candidate set* but the mandatory baseline OLDEST_SLOT beats FIFO there by +0.70 [+0.53,+0.87] (and S4 by +0.55, S3 +0.27, S7 +0.29, S12 +0.23): FIFO "failure" on long-slot capture exists but is solved by preemption, not by ranking. (2) In S1/S2 (demand ≤ capacity) all methods coincide, as they must.

FIFO on the mission's dimensions (per-scenario table `results/analysis/H1_fifo_dims.csv`): regret vs oracle 4.6–5.8 in S3/S7/S8/S9 (best simple: 3.8–4.7); high-quality capture 0.64 vs 0.74 macro; instrument-weighted rejected quality 3.46 vs 2.71 (worse); concentration equal (HHI 0.094 vs 0.092); starvation *lower* (soft 0.016 vs 0.031).
