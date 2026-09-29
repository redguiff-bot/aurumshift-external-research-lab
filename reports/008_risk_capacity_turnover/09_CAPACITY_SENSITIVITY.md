# 09 — Capacity sensitivity (descriptive synthetic effects only)

**Not a recommendation.** Offered load is fixed in absolute terms (candidates per hour), so larger K is *under-loaded* by construction. Parameters were tuned at K=4 and not retuned per K. M1 = net / (K·W), so it necessarily falls as K grows with fixed demand. No production cap, no `max_open_positions` conclusion, follows from this section.

## Heldout M1 by capacity (H3: 13 scenarios × 10 seeds; macro mean)
| policy | 3 | 4 | 6 | 10 |
|---|---|---|---|---|
| FIFO | 1.834 | 1.814 | 1.720 | 1.312 |
| ROUND_ROBIN | 1.762 | 1.795 | 1.705 | 1.311 |
| RANDOM | 1.837 | 1.778 | 1.718 | 1.311 |
| EQUAL_QUOTA | 1.865 | 1.771 | 1.669 | 1.298 |
| OLDEST_SLOT | 2.080 | 2.005 | 1.876 | 1.315 |
| FIFO_SCREEN | 2.019 | 1.955 | 1.799 | 1.268 |
| SCORE_RANK | 2.411 | 2.211 | 1.870 | 1.271 |
| SLOTHOUR | 2.513 | 2.290 | 1.876 | 1.270 |
| SLOTHOUR_SHADOW | 2.512 | 2.263 | 1.862 | 1.210 |
| UNCERTAINTY_LCB | 2.579 | 2.340 | 1.933 | 1.310 |
| CORR_AWARE | 2.508 | 2.256 | 1.859 | 1.270 |
| LINTS | 2.536 | 2.248 | 1.862 | 1.273 |
| ORACLE_GREEDY_UB | 6.508 | 5.754 | 4.506 | 2.847 |

## Paired difference vs FIFO (macro over scenarios; mean [95% CI])
| K | policy | macro_diff_vs_FIFO | lo | hi |
|---|---|---|---|---|
| 3 | SLOTHOUR | 0.679 | 0.607 | 0.756 |
| 3 | UNCERTAINTY_LCB | 0.745 | 0.647 | 0.842 |
| 3 | FIFO_SCREEN | 0.185 | 0.110 | 0.259 |
| 4 | SLOTHOUR | 0.476 | 0.413 | 0.539 |
| 4 | UNCERTAINTY_LCB | 0.526 | 0.459 | 0.593 |
| 4 | FIFO_SCREEN | 0.141 | 0.088 | 0.199 |
| 6 | SLOTHOUR | 0.156 | 0.102 | 0.211 |
| 6 | UNCERTAINTY_LCB | 0.213 | 0.164 | 0.260 |
| 6 | FIFO_SCREEN | 0.079 | 0.035 | 0.122 |
| 10 | SLOTHOUR | -0.041 | -0.059 | -0.024 |
| 10 | UNCERTAINTY_LCB | -0.002 | -0.017 | 0.014 |
| 10 | FIFO_SCREEN | -0.043 | -0.060 | -0.027 |

## Gaps by K (macro over scenarios)
| K | FIFO_to_best_impl_gap | FIFO_to_screen_gap | oracle_minus_best_impl |
|---|---|---|---|
| 3.000 | 0.878 | 0.185 | 3.795 |
| 4.000 | 0.595 | 0.141 | 3.345 |
| 6.000 | 0.257 | 0.079 | 2.529 |
| 10.000 | 0.019 | -0.043 | 1.516 |

## Utilisation (fraction of time all slots are full; idle slot-hours)
| policy | 3 | 4 | 6 | 10 |
|---|---|---|---|---|
| FIFO | 0.839 | 0.784 | 0.646 | 0.123 |
| SLOTHOUR | 0.794 | 0.716 | 0.500 | 0.054 |
| UNCERTAINTY_LCB | 0.806 | 0.734 | 0.532 | 0.068 |
| OLDEST_SLOT | 0.822 | 0.755 | 0.571 | 0.112 |
| ORACLE_GREEDY_UB | 0.785 | 0.705 | 0.498 | 0.068 |
| policy | 3 | 4 | 6 | 10 |
|---|---|---|---|---|
| FIFO | 174.231 | 298.323 | 667.238 | 2342.254 |
| SLOTHOUR | 225.754 | 384.731 | 888.800 | 2828.646 |
| UNCERTAINTY_LCB | 211.854 | 360.108 | 831.131 | 2702.277 |
| OLDEST_SLOT | 188.346 | 324.046 | 743.600 | 2360.185 |

Descriptive effects (OBSERVED, synthetic):
- **cap=3:** ranking beats FIFO by +0.68 (SLOTHOUR) to +0.75 (UNCERTAINTY_LCB) bps/avail-slot-hour; slots are full ≈80% of the time.
- **cap=4:** +0.48 / +0.53. **cap=6:** +0.16 / +0.21 — ranking still helps but the absolute gain is roughly a quarter to a third of cap=3.
- **cap=10:** slots are full ≈5–12% of the time; **no method beats FIFO** (SLOTHOUR −0.041 [−0.059,−0.024], i.e. slightly worse because screening leaves value on the table when capacity is abundant; LCB −0.002 [−0.017,+0.014]). FIFO is effectively as good as sophisticated methods when capacity is not scarce.
- Hence the value of *allocation intelligence* in this world is a decreasing function of scarcity, as expected (INFERENCE: consistent with queueing intuition). Where a real system sits on this curve is UNKNOWN.
- Robustness with the OFAT design on S3 (validation, 8 seeds): best-implementable minus FIFO = K=3: +1.68, K=4: +1.30, K=6: +0.60, K=10: +0.05, same ordering (monotone in scarcity).
