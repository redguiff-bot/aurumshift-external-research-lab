# 05 — Held-out results (Phase B)

Data: `bench/v2/results/heldout/S*.json` (1 200 runs = 10 scenarios × **20 seeds (3000–3019)** × 6 policies; **0 errors**; written with exclusive-create; commit `HELDOUT-RAW` after `3328e4d`). Parameters used are the frozen ones in `results/heldout/params_lock.json` (04). Analysis code: `src/analysis.py`; per-scenario tables with median/q10–q90/worst run: `results/heldout_analysis/per_scenario_tables.md`. Numbers are means ± sd over 20 paired seeds; **no seed reduction was needed** (Phase A cost 54 s; Phase B 208 s).

**Evidence label for everything in this file: OBSERVED in this synthetic experimental model** (reproducible from `bench/v2`, falsifiable, but **not** a general PROVEN claim; see 11). Policies: `A` operator-supplied lifecycle-weighted reference (fixed) · `B` D-UCB + guard · `C` River as shipped · `D` VW shared features · `C2` River + guard (composition diagnostic) · `R` round-robin (frame). Metric definitions: 01 §4. `info_ratio` = expected information / per-cycle oracle (round-robin ≈ 0.5).

## 1. Pooled over the 10 scenarios (hierarchical bootstrap 95 % CI: resample seeds within scenario, average scenario means)

| metric (scenarios pooled) | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| info_ratio (n_scen=10) | 0.508 [0.502,0.514] | 0.649 [0.645,0.653] | 0.743 [0.738,0.748] | 0.728 [0.722,0.734] | 0.757 [0.753,0.760] | 0.507 [0.500,0.513] |
| coverage_W (n_scen=10) | 1.000 [1.000,1.000] | 0.984 [0.983,0.984] | 0.598 [0.596,0.601] | 0.759 [0.751,0.767] | 0.830 [0.829,0.831] | 1.000 [1.000,1.000] |
| starvation_rate (n_scen=10) | 0.000 [0.000,0.000] | 0.005 [0.005,0.005] | 0.147 [0.145,0.149] | 0.073 [0.069,0.077] | 0.015 [0.015,0.015] | 0.000 [0.000,0.000] |
| max_starvation_duration (n_scen=10) | 49.015 [48.110,49.935] | 48.875 [48.470,49.300] | 288.755 [284.570,292.900] | 229.805 [223.855,235.775] | 79.245 [78.720,80.000] | 26.095 [25.305,27.090] |
| stale_rate (n_scen=10) | 0.002 [0.002,0.002] | 0.010 [0.010,0.010] | 0.230 [0.228,0.232] | 0.125 [0.120,0.131] | 0.023 [0.022,0.023] | 0.003 [0.003,0.003] |
| silent_excess (n_scen=10) | 0.009 [0.009,0.009] | -0.025 [-0.025,-0.024] | 0.039 [0.035,0.043] | -0.007 [-0.010,-0.004] | -0.026 [-0.026,-0.025] | 0.000 [-0.000,0.000] |
| lowinfo_excess (n_scen=10) | -0.012 [-0.013,-0.012] | -0.055 [-0.057,-0.053] | -0.085 [-0.089,-0.082] | -0.080 [-0.083,-0.077] | -0.072 [-0.075,-0.070] | 0.000 [0.000,0.000] |
| adapt_delay (n_scen=3) | 196.667 [196.667,196.667] | 95.917 [90.650,101.267] | 104.567 [93.600,115.717] | 99.350 [88.917,109.783] | 128.133 [116.200,140.233] | 196.667 [196.667,196.667] |
| new_ttfa_median (n_scen=2) | 3.163 [3.062,3.263] | 1.562 [1.500,1.637] | 35.162 [33.475,36.925] | 14.162 [12.150,16.287] | 35.575 [34.288,36.850] | 9.250 [9.250,9.250] |
| rare_discovery_rate (n_scen=1) | 0.705 [0.645,0.765] | 0.510 [0.440,0.580] | 0.275 [0.210,0.340] | 0.315 [0.220,0.415] | 0.335 [0.275,0.395] | 0.750 [0.675,0.815] |
| gini_attention_rate (n_scen=10) | 0.059 [0.058,0.060] | 0.307 [0.304,0.310] | 0.684 [0.681,0.687] | 0.506 [0.496,0.516] | 0.581 [0.578,0.583] | 0.020 [0.020,0.021] |
| turnover (n_scen=10) | 0.999 [0.999,0.999] | 0.655 [0.653,0.657] | 0.301 [0.299,0.302] | 0.502 [0.493,0.513] | 0.404 [0.403,0.405] | 1.000 [1.000,1.000] |

`silent_excess` and `lowinfo_excess` are pooled over all 10 scenarios (zero where the scenario has no silence / few low-information cells) — use the per-scenario tables in 06 for those. `adapt_delay`, `new_ttfa_median`, `rare_discovery_rate` pool only the scenarios where they are defined (3, 2 and 1). Pooled means hide scenario heterogeneity: read the per-scenario tables below.

## 2. Per-scenario tables (mean ± sd over 20 seeds)

### Information gain (`info_ratio`, ↑)
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S1_MASSIVE_COLD_START | 0.490 ± 0.031 | 0.548 ± 0.027 | 0.769 ± 0.022 | 0.673 ± 0.051 | 0.706 ± 0.021 | 0.491 ± 0.033 |
| S2_ABRUPT_REGIME_CHANGE | 0.546 ± 0.054 | 0.672 ± 0.029 | 0.768 ± 0.027 | 0.720 ± 0.034 | 0.741 ± 0.028 | 0.538 ± 0.054 |
| S3_SLOW_DRIFT | 0.592 ± 0.059 | 0.693 ± 0.035 | 0.753 ± 0.037 | 0.696 ± 0.051 | 0.742 ± 0.037 | 0.586 ± 0.057 |
| S4_TEMPORARY_SILENCE | 0.526 ± 0.057 | 0.679 ± 0.033 | 0.778 ± 0.026 | 0.745 ± 0.030 | 0.790 ± 0.019 | 0.542 ± 0.060 |
| S5_PROVIDER_DATA_GAP | 0.472 ± 0.037 | 0.667 ± 0.029 | 0.635 ± 0.071 | 0.696 ± 0.065 | 0.774 ± 0.034 | 0.483 ± 0.040 |
| S6_STALE_BUT_VALID | 0.575 ± 0.052 | 0.686 ± 0.035 | 0.825 ± 0.021 | 0.768 ± 0.046 | 0.785 ± 0.022 | 0.574 ± 0.054 |
| S7_GENUINELY_LOW_INFORMATION | 0.324 ± 0.017 | 0.599 ± 0.010 | 0.814 ± 0.009 | 0.798 ± 0.023 | 0.744 ± 0.008 | 0.295 ± 0.015 |
| S8_RARE_HIGH_INFORMATION | 0.531 ± 0.038 | 0.662 ± 0.026 | 0.816 ± 0.019 | 0.744 ± 0.039 | 0.777 ± 0.019 | 0.527 ± 0.040 |
| S9_LONG_DORMANCY_RETURN | 0.476 ± 0.043 | 0.665 ± 0.035 | 0.515 ± 0.050 | 0.697 ± 0.048 | 0.739 ± 0.031 | 0.486 ± 0.046 |
| S10_DYNAMIC_POPULATION | 0.546 ± 0.048 | 0.617 ± 0.038 | 0.759 ± 0.036 | 0.740 ± 0.032 | 0.769 ± 0.018 | 0.546 ± 0.049 |

### Starvation rate (`starvation_rate`, ↓; horizon 80 cycles)
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S1_MASSIVE_COLD_START | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.231 ± 0.016 | 0.087 ± 0.046 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| S2_ABRUPT_REGIME_CHANGE | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.142 ± 0.016 | 0.059 ± 0.025 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| S3_SLOW_DRIFT | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.129 ± 0.014 | 0.039 ± 0.027 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| S4_TEMPORARY_SILENCE | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.143 ± 0.014 | 0.078 ± 0.029 | 0.015 ± 0.002 | 0.000 ± 0.000 |
| S5_PROVIDER_DATA_GAP | 0.000 ± 0.000 | 0.021 ± 0.002 | 0.152 ± 0.011 | 0.085 ± 0.027 | 0.060 ± 0.008 | 0.000 ± 0.000 |
| S6_STALE_BUT_VALID | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.140 ± 0.016 | 0.072 ± 0.029 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| S7_GENUINELY_LOW_INFORMATION | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.167 ± 0.016 | 0.149 ± 0.015 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| S8_RARE_HIGH_INFORMATION | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.147 ± 0.013 | 0.063 ± 0.028 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| S9_LONG_DORMANCY_RETURN | 0.000 ± 0.000 | 0.028 ± 0.000 | 0.160 ± 0.011 | 0.076 ± 0.031 | 0.075 ± 0.001 | 0.000 ± 0.000 |
| S10_DYNAMIC_POPULATION | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.061 ± 0.009 | 0.023 ± 0.013 | 0.000 ± 0.000 | 0.000 ± 0.000 |

### Max starvation duration (cycles, ↓)
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S1_MASSIVE_COLD_START | 48 ± 5 | 29 ± 1 | 315 ± 12 | 236 ± 51 | 58 ± 1 | 18 ± 0 |
| S2_ABRUPT_REGIME_CHANGE | 52 ± 6 | 34 ± 4 | 294 ± 30 | 206 ± 36 | 50 ± 1 | 27 ± 3 |
| S3_SLOW_DRIFT | 50 ± 6 | 36 ± 3 | 301 ± 41 | 187 ± 56 | 50 ± 1 | 29 ± 2 |
| S4_TEMPORARY_SILENCE | 49 ± 6 | 50 ± 0 | 287 ± 28 | 252 ± 46 | 100 ± 0 | 28 ± 3 |
| S5_PROVIDER_DATA_GAP | 52 ± 7 | 104 ± 2 | 298 ± 27 | 242 ± 42 | 138 ± 0 | 29 ± 4 |
| S6_STALE_BUT_VALID | 53 ± 11 | 35 ± 6 | 288 ± 38 | 251 ± 46 | 55 ± 15 | 35 ± 20 |
| S7_GENUINELY_LOW_INFORMATION | 53 ± 6 | 36 ± 3 | 307 ± 36 | 297 ± 33 | 50 ± 1 | 29 ± 3 |
| S8_RARE_HIGH_INFORMATION | 50 ± 7 | 36 ± 4 | 316 ± 27 | 229 ± 48 | 50 ± 0 | 29 ± 3 |
| S9_LONG_DORMANCY_RETURN | 53 ± 5 | 104 ± 2 | 302 ± 32 | 252 ± 43 | 188 ± 1 | 28 ± 2 |
| S10_DYNAMIC_POPULATION | 28 ± 7 | 26 ± 0 | 180 ± 26 | 148 ± 33 | 52 ± 0 | 10 ± 1 |

### Stale cell rate (`stale_rate`, ↓; cells able to produce evidence)
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S1_MASSIVE_COLD_START | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.297 ± 0.017 | 0.127 ± 0.055 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| S2_ABRUPT_REGIME_CHANGE | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.219 ± 0.019 | 0.106 ± 0.037 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| S3_SLOW_DRIFT | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.202 ± 0.017 | 0.074 ± 0.042 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| S4_TEMPORARY_SILENCE | 0.000 ± 0.000 | 0.011 ± 0.001 | 0.233 ± 0.017 | 0.138 ± 0.041 | 0.055 ± 0.005 | 0.000 ± 0.000 |
| S5_PROVIDER_DATA_GAP | 0.003 ± 0.001 | 0.020 ± 0.002 | 0.249 ± 0.015 | 0.152 ± 0.041 | 0.087 ± 0.012 | 0.005 ± 0.001 |
| S6_STALE_BUT_VALID | 0.017 ± 0.000 | 0.026 ± 0.001 | 0.297 ± 0.018 | 0.172 ± 0.047 | 0.027 ± 0.001 | 0.017 ± 0.000 |
| S7_GENUINELY_LOW_INFORMATION | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.254 ± 0.018 | 0.226 ± 0.017 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| S8_RARE_HIGH_INFORMATION | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.227 ± 0.015 | 0.107 ± 0.039 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| S9_LONG_DORMANCY_RETURN | 0.002 ± 0.000 | 0.041 ± 0.001 | 0.259 ± 0.011 | 0.127 ± 0.050 | 0.059 ± 0.000 | 0.004 ± 0.000 |
| S10_DYNAMIC_POPULATION | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.067 ± 0.006 | 0.026 ± 0.012 | 0.000 ± 0.000 | 0.000 ± 0.000 |

### Coverage (`coverage_W`, ↑; 40-cycle windows)
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S1_MASSIVE_COLD_START | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.477 ± 0.020 | 0.726 ± 0.069 | 0.795 ± 0.009 | 1.000 ± 0.000 |
| S2_ABRUPT_REGIME_CHANGE | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.608 ± 0.024 | 0.764 ± 0.059 | 0.857 ± 0.009 | 1.000 ± 0.000 |
| S3_SLOW_DRIFT | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.630 ± 0.018 | 0.825 ± 0.069 | 0.865 ± 0.012 | 1.000 ± 0.000 |
| S4_TEMPORARY_SILENCE | 1.000 ± 0.000 | 0.989 ± 0.002 | 0.602 ± 0.020 | 0.749 ± 0.058 | 0.825 ± 0.008 | 1.000 ± 0.000 |
| S5_PROVIDER_DATA_GAP | 1.000 ± 0.000 | 0.942 ± 0.006 | 0.592 ± 0.016 | 0.728 ± 0.069 | 0.756 ± 0.013 | 1.000 ± 0.000 |
| S6_STALE_BUT_VALID | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.608 ± 0.022 | 0.765 ± 0.055 | 0.885 ± 0.011 | 1.000 ± 0.000 |
| S7_GENUINELY_LOW_INFORMATION | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.565 ± 0.020 | 0.608 ± 0.023 | 0.848 ± 0.009 | 1.000 ± 0.000 |
| S8_RARE_HIGH_INFORMATION | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.596 ± 0.020 | 0.784 ± 0.054 | 0.858 ± 0.009 | 1.000 ± 0.000 |
| S9_LONG_DORMANCY_RETURN | 1.000 ± 0.000 | 0.907 ± 0.002 | 0.573 ± 0.012 | 0.744 ± 0.066 | 0.752 ± 0.008 | 1.000 ± 0.000 |
| S10_DYNAMIC_POPULATION | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.731 ± 0.018 | 0.896 ± 0.031 | 0.861 ± 0.010 | 1.000 ± 0.000 |

### Attention concentration (Gini of attempts per eligible cycle; context, neither good nor bad)
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S1_MASSIVE_COLD_START | 0.052 ± 0.004 | 0.223 ± 0.008 | 0.716 ± 0.019 | 0.493 ± 0.088 | 0.552 ± 0.019 | 0.043 ± 0.000 |
| S2_ABRUPT_REGIME_CHANGE | 0.045 ± 0.007 | 0.272 ± 0.026 | 0.652 ± 0.029 | 0.425 ± 0.065 | 0.547 ± 0.023 | 0.008 ± 0.000 |
| S3_SLOW_DRIFT | 0.045 ± 0.007 | 0.228 ± 0.016 | 0.597 ± 0.022 | 0.291 ± 0.074 | 0.496 ± 0.021 | 0.008 ± 0.000 |
| S4_TEMPORARY_SILENCE | 0.059 ± 0.008 | 0.305 ± 0.029 | 0.677 ± 0.027 | 0.529 ± 0.082 | 0.576 ± 0.021 | 0.008 ± 0.000 |
| S5_PROVIDER_DATA_GAP | 0.063 ± 0.005 | 0.290 ± 0.033 | 0.695 ± 0.020 | 0.561 ± 0.092 | 0.609 ± 0.029 | 0.008 ± 0.000 |
| S6_STALE_BUT_VALID | 0.047 ± 0.010 | 0.290 ± 0.024 | 0.666 ± 0.025 | 0.518 ± 0.084 | 0.545 ± 0.021 | 0.008 ± 0.000 |
| S7_GENUINELY_LOW_INFORMATION | 0.069 ± 0.003 | 0.427 ± 0.008 | 0.743 ± 0.014 | 0.711 ± 0.026 | 0.627 ± 0.011 | 0.008 ± 0.000 |
| S8_RARE_HIGH_INFORMATION | 0.054 ± 0.009 | 0.313 ± 0.018 | 0.683 ± 0.022 | 0.511 ± 0.070 | 0.576 ± 0.016 | 0.008 ± 0.000 |
| S9_LONG_DORMANCY_RETURN | 0.076 ± 0.005 | 0.334 ± 0.024 | 0.725 ± 0.011 | 0.508 ± 0.098 | 0.626 ± 0.014 | 0.008 ± 0.000 |
| S10_DYNAMIC_POPULATION | 0.081 ± 0.004 | 0.392 ± 0.011 | 0.688 ± 0.016 | 0.516 ± 0.053 | 0.653 ± 0.018 | 0.095 ± 0.002 |

### Turnover (`1 − |S_t ∩ S_(t−1)|/K`; context)
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S1_MASSIVE_COLD_START | 1.000 ± 0.000 | 0.892 ± 0.010 | 0.282 ± 0.010 | 0.574 ± 0.077 | 0.461 ± 0.009 | 1.000 ± 0.000 |
| S2_ABRUPT_REGIME_CHANGE | 1.000 ± 0.000 | 0.635 ± 0.027 | 0.314 ± 0.012 | 0.516 ± 0.078 | 0.416 ± 0.007 | 1.000 ± 0.000 |
| S3_SLOW_DRIFT | 1.000 ± 0.000 | 0.651 ± 0.012 | 0.336 ± 0.013 | 0.587 ± 0.091 | 0.428 ± 0.008 | 1.000 ± 0.000 |
| S4_TEMPORARY_SILENCE | 0.999 ± 0.001 | 0.636 ± 0.020 | 0.309 ± 0.012 | 0.517 ± 0.083 | 0.407 ± 0.008 | 1.000 ± 0.000 |
| S5_PROVIDER_DATA_GAP | 1.000 ± 0.000 | 0.657 ± 0.024 | 0.305 ± 0.010 | 0.469 ± 0.083 | 0.391 ± 0.012 | 1.000 ± 0.000 |
| S6_STALE_BUT_VALID | 1.000 ± 0.000 | 0.656 ± 0.019 | 0.316 ± 0.013 | 0.529 ± 0.079 | 0.431 ± 0.009 | 1.000 ± 0.000 |
| S7_GENUINELY_LOW_INFORMATION | 1.000 ± 0.000 | 0.620 ± 0.011 | 0.280 ± 0.010 | 0.354 ± 0.036 | 0.394 ± 0.008 | 1.000 ± 0.000 |
| S8_RARE_HIGH_INFORMATION | 1.000 ± 0.000 | 0.647 ± 0.012 | 0.309 ± 0.012 | 0.536 ± 0.072 | 0.414 ± 0.010 | 1.000 ± 0.000 |
| S9_LONG_DORMANCY_RETURN | 1.000 ± 0.000 | 0.620 ± 0.016 | 0.286 ± 0.008 | 0.496 ± 0.085 | 0.390 ± 0.009 | 1.000 ± 0.000 |
| S10_DYNAMIC_POPULATION | 0.997 ± 0.001 | 0.533 ± 0.007 | 0.270 ± 0.009 | 0.446 ± 0.050 | 0.309 ± 0.007 | 1.000 ± 0.000 |

### Adaptation delay (cycles after the structural change until the target cells get ≥ 2× their population share over 10 cycles; **censored** at the remaining horizon)
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S2_ABRUPT_REGIME_CHANGE | 220 ± 0 | 54 ± 30 | 89 ± 64 | 82 ± 45 | 95 ± 77 | 220 ± 0 |
| S3_SLOW_DRIFT | 280 ± 0 | 174 ± 23 | 215 ± 46 | 183 ± 54 | 199 ± 39 | 280 ± 0 |
| S9_LONG_DORMANCY_RETURN | 90 ± 0 | 60 ± 1 | 9 ± 0 | 32 ± 21 | 90 ± 0 | 90 ± 0 |

Censored fraction of runs (delay never reached):
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S2_ABRUPT_REGIME_CHANGE | 1.00 | 0.00 | 0.10 | 0.00 | 0.15 | 1.00 |
| S3_SLOW_DRIFT | 1.00 | 0.00 | 0.00 | 0.05 | 0.00 | 1.00 |
| S9_LONG_DORMANCY_RETURN | 1.00 | 0.00 | 0.00 | 0.05 | 1.00 | 1.00 |

Silent-cell attention (`silent_excess = share − uniform baseline`):
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S4_TEMPORARY_SILENCE | +0.030 ± +0.001 | -0.026 ± +0.000 | +0.024 ± +0.021 | -0.003 ± +0.016 | -0.028 ± +0.001 | +0.000 ± +0.001 |
| S5_PROVIDER_DATA_GAP | +0.024 ± +0.002 | -0.112 ± +0.011 | +0.106 ± +0.074 | -0.027 ± +0.055 | -0.114 ± +0.011 | +0.000 ± +0.001 |
| S9_LONG_DORMANCY_RETURN | +0.034 ± +0.001 | -0.107 ± +0.000 | +0.264 ± +0.058 | -0.040 ± +0.040 | -0.115 ± +0.000 | -0.000 ± +0.001 |

## 3. What the numbers say (OBSERVED unless stated)

1. **The ranking depends on the metric — there is a coverage ↔ information frontier and no policy is on the good side of both.** Policies A and R sit at one end (coverage 1.000, starvation 0, stale ≈ 0, information ≈ 0.51). River-as-shipped `C` and VW `D` sit at the other (information 0.74/0.73 but coverage 0.60/0.76, starvation 0.147/0.073, stale 0.23/0.125). `B` and `C2` are intermediate (info 0.649 / 0.757; starvation 0.005 / 0.015; coverage 0.984 / 0.830).
2. **Policy A is behaviourally indistinguishable from round-robin on information and adaptation** (`info_ratio` Δ = +0.001, effect `d_z = 0.09`, far below the 0.03 practical threshold; adaptation delay censored in every run of S2/S3 for both). It is *slightly* worse than round-robin on `max_starvation_duration` (49 vs 26 cycles) and slightly above the uniform baseline on silent attention (+0.9 pt pooled; +2.4 to +3.4 pt in S4/S5/S9). It respects every semantic invariant. INFERENCE for cause (not tested beyond 07): the weight spread `1.5 : 0.5` (×3) is small, states change only after ≥ 20 evidence events, and the floor is 5 %, so allocation stays close to uniform; the tested variants (floor 0–20 %, flat/steep weights, alternative classifier) did not change this (07).
3. **`B` beats `A` on information gain in 10/10 scenarios and in 20/20 seeds of each** (Δ +0.058 in S1 … +0.275 in S7; pooled +0.141, CI [0.138, 0.144]) and adapts in S2/S3/S9 (delay ≈ 54 / 174 / 60 vs censored) while keeping starvation ≤ 0.028 per run (pooled 0.005) and silent attention **below** the uniform baseline. Cost vs A/R: slightly lower coverage (0.984), a small starvation rate in the gap scenarios (S5 0.021, S9 0.028), and lower rare-event discovery in S8 (0.51 vs 0.70/0.75).
4. **`C` (River as shipped) starves and is captured by silent cells.** Pooled starvation 0.147 (worst run 0.274), max starvation 289 cycles (worst 388), stale 0.23, 4.7 % of S1's new cells never attempted, and in S9 **39.5 %** of attention goes to silent cells versus a 13 % uniform baseline (+0.264). This reproduces V1's PROVEN in-sample finding on independent scenarios (V1 03 §3: 20–24 % of cells untouched; V1 03 §3.5: 72–89 % gap-window waste for forgetting rules) — here as OBSERVED in a new model.
5. **`C2` (River + the shared guard) fixes most of C's coverage pathologies** (starvation 0.147 → 0.015, stale 0.23 → 0.023, silent excess +0.039 → −0.026) and has the best information gain (0.757) and best worst-case information (min 0.657) — but it is **slow on new cells** (median first attempt 35 cycles in S1/S10 vs 1.6 for B; ε-greedy reaches new cells only by exploration) and it **fails P7** in S9 (censored in 100 % of runs; target share 0.000 — see 06).
6. **`D` (VW, shared features, ε-greedy 0.2, no group feature selected)** sits between C and B: starvation 0.073, stale 0.125, information 0.728 (≈ C, +0.016), silent excess −0.007 (does not track silence, but does not chase it), median new-cell delay 14 cycles. The group feature was not selected on dev (04) and no advantage from feature sharing is visible in this benchmark.
7. **Variance across seeds is small relative to between-policy gaps** (mean coefficient of variation of `info_ratio` over seeds: A .084, B .046, C .046, D .058, C2 .031, R .086). Worst individual runs are reported in the per-scenario tables and in 09: none of A/B/C2 produced a run with starvation > 0.08; C reached 0.274 and D 0.174.
8. **Determinism (PROVEN for the tested cases):** 18 checks (3 scenarios × 6 policies × 3 processes with `PYTHONHASHSEED` ∈ {0, 1, 12345}) gave identical pick-sequence hashes; unit test repeats each policy twice on identical hashes. Cross-machine determinism is UNKNOWN.

## 4. Computational cost (OBSERVED; 4 workers in parallel on 4 cores → comparable, not absolute)

| policy | mean s / run (3 200 attempts + burn-in) | max s / run |
|---|---|---|
| A | 0.030 | 0.048 |
| B | 0.032 | 0.044 |
| C | 0.064 | 0.099 |
| D | 3.607 | 4.550 |
| C2 | 0.068 | 0.128 |
| R | 0.003 | 0.006 |

RSS is dominated by the interpreter + numpy (River adds ≈ tens of MB, VW is a native library; V1 measured peak RSS 47 MB for numpy-only, ≈ 173–183 MB with River, ≈ 71 MB with VW, at 160 cells — **not** re-measured in V2, UNKNOWN for V2). Scaling beyond ~250 cells was not tested (UNKNOWN).

## 5. Dependency and operational cost (qualitative + measured)

`A`, `R`: numpy only. `B`: numpy only (~60 lines incl. guard), needs a persistent per-cell `(N, X, last_attempt, consecutive_no_evidence)` — trivially relational. `C/C2`: River 0.26.1 (numpy ≥ 2.2.5, scipy ≥ 1.14.1, narwhals; Python ≥ 3.11) — state is an opaque pickle-able object (V1 04 R7) and must be paired with the guard ledger anyway. `D`: VW 9.11.9 native wheel, 0 Python deps, single-maintainer upstream (V1 04 V1), ≈ 60–120× slower per run in this harness, opaque binary model, feature engineering burden. Library quality is judged separately in 10 and **is not inferred from these behaviour results**.
