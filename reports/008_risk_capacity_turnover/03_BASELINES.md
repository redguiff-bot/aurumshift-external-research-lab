# 03 — Baselines

All five mandatory controls were implemented and executed in every scenario, even where sophisticated methods look superior. A sixth, **FIFO_SCREEN**, was added so that "ranking" gains are not confused with "screening out negative expected net" gains.

| id | policy | notes |
|---|---|---|
| A | FIFO | arrival order (first emission); primary ingest RAW (as naively implemented) |
| B | ROUND_ROBIN | pointer over instruments; RAW ingest |
| C | RANDOM | policy RNG seeded (`seed+424242`), independent of the world |
| D | EQUAL_QUOTA | fewest cumulative admissions first (deficit round-robin) |
| E | OLDEST_SLOT | FIFO admission; when full and candidates wait, preempt oldest slot with age ≥ min_hold (tuned on validation: 4 h); truncated outcome realised at exit, cost charged in full |
| ctl | FIFO_SCREEN | FIFO among candidates with estimated net edge > 0; ingest SCORE_UPDATE (tuned) |

## Heldout macro results (K=4, 13 scenarios × 20 seeds; OBSERVED)
| policy | net_per_avail_slot_hour | net_per_busy_slot_hour | turnover_per_slot_hour | idle_slot_hours | hhi_inst | starve_soft_rate | max_denial_hours | rej_rate_instw | hq_capture | mean_hold |
|---|---|---|---|---|---|---|---|---|---|---|
| FIFO | 1.781 | 2.028 | 0.104 | 292.723 | 0.094 | 0.016 | 214.773 | 3.461 | 0.638 | 8.753 |
| ROUND_ROBIN | 1.775 | 2.024 | 0.104 | 296.138 | 0.090 | 0.008 | 193.369 | 3.417 | 0.660 | 8.755 |
| RANDOM | 1.739 | 1.986 | 0.104 | 298.862 | 0.092 | 0.008 | 205.150 | 3.344 | 0.644 | 8.711 |
| EQUAL_QUOTA | 1.740 | 1.985 | 0.102 | 295.308 | 0.083 | 0.000 | 132.669 | 3.486 | 0.623 | 8.842 |
| OLDEST_SLOT | 1.966 | 2.256 | 0.196 | 320.304 | 0.087 | 0.007 | 104.958 | 3.495 | 0.934 | 5.041 |
| FIFO_SCREEN | 1.944 | 2.304 | 0.100 | 371.323 | 0.097 | 0.023 | 247.592 | 3.033 | 0.698 | 8.737 |

Reading:
- A–D are statistically indistinguishable from one another on M1 (paired CIs vs FIFO: RR -0.006 [-0.050,+0.035], RANDOM -0.042, EQUAL_QUOTA -0.041). **Arrival order carries no information about quality in this world** (INFERENCE — by construction candidates are exchangeable in time). Real arrival order may differ (UNKNOWN).
- FIFO_SCREEN beats FIFO by +0.164 [+0.124,+0.205], 11/13 scenarios: a large part of "smart allocation" is just refusing negative-expected-net entries. Its benefit depends on the cost belief: with zero-cost belief the screen degrades toward FIFO (see 08).
- OLDEST_SLOT (E) is *not* a null: +0.185 vs FIFO [0.140,0.229] with 2× the turnover and evict_frac ≈ 0.52. It beats FIFO_SCREEN where long slots get captured (S4, S6; heldout) and loses to it in S5/S5b. This benefit rests on the linear-accrual assumption A3 (early exit forfeits nothing but the not-yet-earned edge) — INFERENCE that it would be weaker if edge is back-loaded; UNKNOWN locally.
- Metric caveat: `hq_capture` for OLDEST_SLOT (≈0.93) is inflated by its 2× admission count and should not be read as selection skill.

## Per-scenario M1 (bps / available slot-hour; heldout, mean of 20 seeds)
| scen | FIFO | ROUND_ROBIN | RANDOM | EQ_QUOTA | OLDEST_SLOT | FIFO_SCREEN | SCORE_RANK | SLOTHOUR | SLOTHOUR_SHDW | UNCERT_LCB | CORR_AWARE | LINTS | ORACLE_UB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S10_spam | 2.003 | 2.087 | 2.019 | 1.907 | 2.156 | 2.156 | 2.220 | 2.262 | 2.230 | 2.275 | 2.279 | 2.242 | 4.883 |
| S11_burst | 0.960 | 0.960 | 0.909 | 0.924 | 0.923 | 0.979 | 1.152 | 1.199 | 1.175 | 1.212 | 1.193 | 1.183 | 3.015 |
| S12_near_equal | 2.646 | 2.592 | 2.543 | 2.678 | 2.881 | 2.814 | 2.934 | 2.965 | 2.914 | 3.109 | 3.010 | 2.886 | 7.758 |
| S1_sparse | 0.828 | 0.833 | 0.831 | 0.837 | 0.843 | 0.825 | 0.835 | 0.836 | 0.789 | 0.832 | 0.836 | 0.836 | 1.825 |
| S2_moderate | 1.469 | 1.458 | 1.478 | 1.419 | 1.533 | 1.579 | 1.653 | 1.663 | 1.516 | 1.604 | 1.647 | 1.622 | 3.988 |
| S3_chronic | 2.123 | 2.231 | 2.079 | 2.021 | 2.398 | 2.353 | 3.024 | 3.213 | 3.304 | 3.256 | 3.083 | 3.153 | 7.880 |
| S4_late_hq | 1.558 | 1.434 | 1.509 | 1.438 | 2.105 | 1.665 | 1.837 | 1.885 | 2.143 | 1.952 | 1.847 | 1.887 | 4.772 |
| S5_correlated | 0.967 | 1.029 | 0.873 | 0.997 | 0.892 | 1.186 | 1.297 | 1.345 | 1.363 | 1.392 | 1.346 | 1.345 | 5.498 |
| S5b_corr_benign | 1.767 | 1.496 | 1.510 | 1.607 | 1.678 | 1.920 | 2.165 | 2.314 | 2.427 | 2.284 | 2.268 | 2.209 | 6.017 |
| S6_short_vs_long | 3.187 | 3.220 | 3.253 | 3.202 | 3.888 | 3.109 | 3.082 | 3.441 | 3.412 | 3.492 | 3.334 | 3.538 | 7.985 |
| S7_regime_shift | 1.866 | 1.821 | 1.960 | 1.808 | 2.154 | 2.264 | 2.765 | 2.727 | 2.779 | 2.819 | 2.731 | 2.746 | 6.911 |
| S8_noisy_rank | 1.783 | 1.805 | 1.785 | 1.709 | 1.934 | 2.103 | 2.293 | 2.262 | 2.212 | 2.523 | 2.301 | 2.369 | 6.699 |
| S9_missing | 1.993 | 2.107 | 1.853 | 2.070 | 2.170 | 2.325 | 2.634 | 2.694 | 2.659 | 2.859 | 2.650 | 2.536 | 7.116 |
