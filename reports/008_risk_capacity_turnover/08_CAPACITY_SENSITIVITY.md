# 08 — Capacity sensitivity (synthetic only)

Slot counts 3, 4, 6, 10 were run on identical worlds. **This is sensitivity of the synthetic environment, not a cap recommendation.** Arrival intensity is defined by an offered load at `C_ref = 4`, so C = 3 is more saturated and C = 10 much less.

## Absolute outcome per slot-hour (held-out, mean over all cells)
| policy | cap | lat_per_slot_hour | real_per_slot_hour | utilisation | hq_missed_frac | lp_bound | capture_of_lp |
|---|---|---|---|---|---|---|---|
| FIFO | 3 | 0.158 | 0.144 | 0.909 | 0.660 | 1.445 | 0.109 |
| FIFO | 4 | 0.161 | 0.163 | 0.894 | 0.577 | 1.260 | 0.128 |
| FIFO | 6 | 0.162 | 0.159 | 0.862 | 0.436 | 1.006 | 0.161 |
| FIFO | 10 | 0.168 | 0.164 | 0.788 | 0.222 | 0.714 | 0.235 |
| FIFO_NETPOS | 3 | 0.457 | 0.459 | 0.867 | 0.596 | 1.445 | 0.316 |
| FIFO_NETPOS | 4 | 0.441 | 0.439 | 0.846 | 0.509 | 1.260 | 0.350 |
| FIFO_NETPOS | 6 | 0.418 | 0.416 | 0.800 | 0.364 | 1.006 | 0.416 |
| FIFO_NETPOS | 10 | 0.371 | 0.370 | 0.695 | 0.183 | 0.714 | 0.520 |
| RANK_NET | 3 | 0.660 | 0.654 | 0.865 | 0.565 | 1.445 | 0.456 |
| RANK_NET | 4 | 0.619 | 0.618 | 0.843 | 0.475 | 1.260 | 0.492 |
| RANK_NET | 6 | 0.552 | 0.553 | 0.795 | 0.338 | 1.006 | 0.549 |
| RANK_NET | 10 | 0.443 | 0.442 | 0.690 | 0.174 | 0.714 | 0.620 |
| COMPOSED | 3 | 0.791 | 0.793 | 0.763 | 0.499 | 1.445 | 0.547 |
| COMPOSED | 4 | 0.708 | 0.712 | 0.766 | 0.425 | 1.260 | 0.562 |
| COMPOSED | 6 | 0.602 | 0.605 | 0.739 | 0.314 | 1.006 | 0.599 |
| COMPOSED | 10 | 0.473 | 0.475 | 0.633 | 0.191 | 0.714 | 0.662 |
| SHADOW_PRICE | 3 | 0.724 | 0.722 | 0.785 | 0.496 | 1.445 | 0.501 |
| SHADOW_PRICE | 4 | 0.660 | 0.662 | 0.767 | 0.413 | 1.260 | 0.524 |
| SHADOW_PRICE | 6 | 0.566 | 0.571 | 0.730 | 0.292 | 1.006 | 0.563 |
| SHADOW_PRICE | 10 | 0.440 | 0.440 | 0.653 | 0.158 | 0.714 | 0.615 |
| ONLINE_KNAPSACK_PSI | 3 | 0.707 | 0.690 | 0.802 | 0.489 | 1.445 | 0.489 |
| ONLINE_KNAPSACK_PSI | 4 | 0.666 | 0.658 | 0.755 | 0.395 | 1.260 | 0.529 |
| ONLINE_KNAPSACK_PSI | 6 | 0.575 | 0.575 | 0.675 | 0.276 | 1.006 | 0.571 |
| ONLINE_KNAPSACK_PSI | 10 | 0.438 | 0.437 | 0.551 | 0.168 | 0.714 | 0.613 |
| ORACLE_DENSITY_NOT_IMPLEMENTABLE | 3 | 1.030 | 1.026 | 0.827 | 0.392 | 1.445 | 0.713 |
| ORACLE_DENSITY_NOT_IMPLEMENTABLE | 4 | 0.961 | 0.958 | 0.795 | 0.291 | 1.260 | 0.763 |
| ORACLE_DENSITY_NOT_IMPLEMENTABLE | 6 | 0.843 | 0.843 | 0.727 | 0.159 | 1.006 | 0.838 |
| ORACLE_DENSITY_NOT_IMPLEMENTABLE | 10 | 0.663 | 0.661 | 0.588 | 0.045 | 0.714 | 0.927 |

## Paired dz vs FIFO by cap
| policy | cap3 dz vs FIFO | cap4 dz vs FIFO | cap6 dz vs FIFO | cap10 dz vs FIFO |
|---|---|---|---|---|
| FIFO_NETPOS | +0.104 [+0.098,+0.110] | +0.098 [+0.092,+0.103] | +0.089 [+0.084,+0.095] | +0.070 [+0.065,+0.074] |
| RANK_NET | +0.182 [+0.172,+0.193] | +0.168 [+0.158,+0.177] | +0.142 [+0.133,+0.152] | +0.099 [+0.092,+0.107] |
| COMPOSED | +0.224 [+0.211,+0.237] | +0.195 [+0.184,+0.207] | +0.157 [+0.147,+0.168] | +0.107 [+0.098,+0.117] |
| SHADOW_PRICE | +0.213 [+0.201,+0.227] | +0.189 [+0.178,+0.201] | +0.152 [+0.142,+0.163] | +0.100 [+0.092,+0.108] |
| ONLINE_KNAPSACK_PSI | +0.210 [+0.198,+0.223] | +0.192 [+0.181,+0.204] | +0.154 [+0.143,+0.165] | +0.094 [+0.086,+0.103] |
| FLUID_QUANTILE | +0.214 [+0.201,+0.228] | +0.186 [+0.175,+0.199] | +0.147 [+0.137,+0.157] | +0.097 [+0.089,+0.105] |
| EQUAL_QUOTA | +0.028 [+0.024,+0.033] | +0.031 [+0.027,+0.035] | +0.031 [+0.027,+0.035] | +0.026 [+0.022,+0.030] |
| ROUND_ROBIN | +0.033 [+0.028,+0.038] | +0.031 [+0.026,+0.036] | +0.029 [+0.025,+0.033] | +0.023 [+0.019,+0.027] |
| RANDOM_SEEDED | +0.024 [+0.018,+0.030] | +0.022 [+0.017,+0.028] | +0.021 [+0.016,+0.026] | +0.016 [+0.012,+0.021] |

## Reading
* **`CAP3_SYNTHETIC_RESULT`**: FIFO 0.158, `RANK_NET` 0.660, `COMPOSED` 0.791 bps/slot-hour; oracle-density 1.030; LP bound 1.445. Gain of `COMPOSED` over FIFO +0.224 dz (largest of any cap).
* **`CAP4_SYNTHETIC_RESULT`**: FIFO 0.161, `RANK_NET` 0.619, `COMPOSED` 0.708; LP bound 1.260; `COMPOSED` +0.195 dz over FIFO.
* **`CAP6_SYNTHETIC_RESULT`**: FIFO 0.162, `RANK_NET` 0.552, `COMPOSED` 0.602; LP bound 1.006; `COMPOSED` +0.157 dz.
* Cap 10 (least scarce): FIFO 0.168, `RANK_NET` 0.443, `COMPOSED` 0.473; +0.107 dz; the composed edge over `RANK_NET` shrinks to +0.008 dz and `ONLINE_KNAPSACK_PSI` loses to `RANK_NET` (−0.005).
* **Monotone pattern (OBSERVED)**: the value of a smart allocator falls as capacity rises (pooled dz vs FIFO for `COMPOSED`: 0.224 → 0.195 → 0.157 → 0.107; vs `RANK_NET`: 0.042 → 0.028 → 0.015 → 0.008). Outcome per slot-hour also falls with C for every value-aware method (0.79 → 0.47 for `COMPOSED`): marginal slots hold worse opportunities. FIFO is flat (~0.16) because it does not discriminate. INFERENCE: this is the expected shape of a concave value-of-capacity curve, and it is entirely a property of the assumed opportunity-quality distribution; it says nothing about what any real cap should be.
* Utilisation falls with C for all policies (FIFO 0.91 → 0.79) and the missed-HQ fraction falls (FIFO 0.66 → 0.22), as it must.
* The rank ordering of methods is stable across caps (sign of each shortlist method's gain vs `RANK_NET` positive at 3/4 caps or more; cap 10 for `ONLINE_KNAPSACK_PSI` is the only exception).
