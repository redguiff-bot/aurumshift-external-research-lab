# 07 — Diversification

Comparison: independent slot-hour ranking (SLOTHOUR) vs correlation-aware greedy (CORR_AWARE = SLOTHOUR rate − γ·ρ̂·σ̂_i·(same-group exposure), ρ̂=0.6 fixed and **mis-specified on purpose**: true ρ_g ∈ {0.35, 0.8, 0.9, 0.3(collapse)}). Group membership is public; correlation magnitude is not.

## Heldout / diagnostic paired results: CORR_AWARE (γ=0.1, tuned) − SLOTHOUR (mean diff [95% CI], paired seeds)
| scenario | M1 | pnl_std | worst_24h | max_drawdown | hhi_group |
|---|---|---|---|---|---|
| S5_correlated | +0.00 [-0.08,+0.09] | -0.12 [-0.54,+0.28] | +12.86 [-27.22,+52.84] | -47.93 [-154.20,+53.88] | -0.00 [-0.00,+0.00] |
| S5b_corr_benign | -0.05 [-0.14,+0.05] | -0.20 [-0.65,+0.27] | +13.56 [-25.67,+53.65] | -19.44 [-66.93,+23.41] | -0.00 [-0.00,+0.00] |
| F_corr_collapse | -0.16 [-0.33,-0.02] | -0.15 [-1.08,+0.78] | -5.01 [-51.67,+43.79] | +26.20 [-186.47,+233.28] | -0.00 [-0.01,+0.00] |
(S5/S5b heldout, 20 seeds; F_corr_collapse validation split, 10 seeds. Units: M1 bps/slot-hour; pnl in bps/step.)

No cell shows a significant improvement in M1 or portfolio risk at the tuned γ=0.1; the penalty is too small to change allocations (group HHI moves by <0.005).

## Stress test: penalty strength (D6, validation split, 20 seeds, γ ∈ {0.1…8})
| case | arm | net_per_avail_slot_hour | pnl_std | worst_24h | max_drawdown | hhi_group | hq_capture |
|---|---|---|---|---|---|---|---|
| F_corr_collapse|base | SLOTHOUR | 1.864 | 17.671 | -582.404 | 1722.044 | 0.268 | 0.814 |
| F_corr_collapse|base | g0.1 | 1.925 | 17.657 | -578.490 | 1657.102 | 0.266 | 0.818 |
| F_corr_collapse|base | g0.4 | 1.819 | 17.173 | -607.066 | 1636.740 | 0.265 | 0.802 |
| F_corr_collapse|base | g1.0 | 1.767 | 17.183 | -614.894 | 1673.699 | 0.261 | 0.802 |
| F_corr_collapse|base | g2.0 | 1.588 | 17.377 | -633.860 | 1806.316 | 0.259 | 0.787 |
| F_corr_collapse|base | g4.0 | 1.521 | 17.130 | -627.422 | 1784.104 | 0.257 | 0.788 |
| F_corr_collapse|base | g8.0 | 1.448 | 17.107 | -645.703 | 1871.941 | 0.258 | 0.769 |
| S5_correlated|base | SLOTHOUR | 1.992 | 13.958 | -259.544 | 426.193 | 0.285 | 0.793 |
| S5_correlated|base | g0.1 | 1.967 | 13.936 | -280.947 | 437.656 | 0.285 | 0.791 |
| S5_correlated|base | g0.4 | 2.042 | 13.682 | -229.204 | 363.212 | 0.279 | 0.791 |
| S5_correlated|base | g1.0 | 2.037 | 13.238 | -218.845 | 388.267 | 0.271 | 0.778 |
| S5_correlated|base | g2.0 | 1.994 | 13.163 | -231.775 | 339.900 | 0.266 | 0.779 |
| S5_correlated|base | g4.0 | 1.826 | 12.707 | -245.116 | 323.878 | 0.264 | 0.742 |
| S5_correlated|base | g8.0 | 1.865 | 12.814 | -230.301 | 326.130 | 0.264 | 0.750 |
| S5_correlated|rho0.9 | SLOTHOUR | 1.909 | 14.424 | -308.050 | 558.182 | 0.285 | 0.795 |
| S5_correlated|rho0.9 | g0.1 | 1.901 | 14.395 | -323.045 | 565.851 | 0.285 | 0.795 |
| S5_correlated|rho0.9 | g0.4 | 1.948 | 14.033 | -260.166 | 458.315 | 0.279 | 0.795 |
| S5_correlated|rho0.9 | g1.0 | 1.960 | 13.547 | -259.760 | 471.845 | 0.271 | 0.779 |
| S5_correlated|rho0.9 | g2.0 | 1.908 | 13.431 | -262.570 | 416.017 | 0.266 | 0.773 |
| S5_correlated|rho0.9 | g4.0 | 1.752 | 12.979 | -279.063 | 387.552 | 0.264 | 0.738 |
| S5_correlated|rho0.9 | g8.0 | 1.782 | 13.086 | -256.998 | 390.269 | 0.264 | 0.746 |
| S5b_corr_benign|base | SLOTHOUR | 2.748 | 12.954 | -92.937 | 147.556 | 0.287 | 0.783 |
| S5b_corr_benign|base | g0.1 | 2.768 | 12.637 | -88.267 | 131.778 | 0.285 | 0.780 |
| S5b_corr_benign|base | g0.4 | 2.754 | 12.344 | -73.838 | 123.246 | 0.275 | 0.779 |
| S5b_corr_benign|base | g1.0 | 2.622 | 12.076 | -64.244 | 116.724 | 0.268 | 0.757 |
| S5b_corr_benign|base | g2.0 | 2.482 | 12.154 | -86.210 | 138.453 | 0.263 | 0.754 |
| S5b_corr_benign|base | g4.0 | 2.454 | 12.172 | -112.038 | 155.617 | 0.262 | 0.745 |
| S5b_corr_benign|base | g8.0 | 2.474 | 12.091 | -110.842 | 159.352 | 0.262 | 0.751 |
| S5b_corr_benign|rho0.9 | SLOTHOUR | 2.726 | 13.056 | -98.165 | 154.459 | 0.287 | 0.782 |
| S5b_corr_benign|rho0.9 | g0.1 | 2.760 | 12.764 | -99.280 | 137.542 | 0.285 | 0.782 |
| S5b_corr_benign|rho0.9 | g0.4 | 2.727 | 12.456 | -87.230 | 133.040 | 0.275 | 0.781 |
| S5b_corr_benign|rho0.9 | g1.0 | 2.599 | 12.170 | -80.348 | 127.320 | 0.268 | 0.758 |
| S5b_corr_benign|rho0.9 | g2.0 | 2.460 | 12.259 | -97.584 | 146.975 | 0.263 | 0.757 |
| S5b_corr_benign|rho0.9 | g4.0 | 2.433 | 12.214 | -113.137 | 161.415 | 0.262 | 0.751 |
| S5b_corr_benign|rho0.9 | g8.0 | 2.443 | 12.137 | -117.428 | 161.783 | 0.262 | 0.755 |

Paired vs SLOTHOUR (selected rows; full table `results/analysis/D6_paired_vs_SLOTHOUR.csv`):
| case | arm | metric | diff | lo | hi |
|---|---|---|---|---|---|
| S5_correlated|base | g0.4 | net_per_avail_slot_hour | 0.050 | -0.060 | 0.150 |
| S5_correlated|base | g0.4 | max_drawdown | -62.980 | -172.430 | 29.930 |
| S5_correlated|base | g0.4 | worst_24h | 30.340 | -8.420 | 67.640 |
| S5_correlated|base | g1.0 | net_per_avail_slot_hour | 0.040 | -0.090 | 0.160 |
| S5_correlated|base | g1.0 | max_drawdown | -37.930 | -139.900 | 49.030 |
| S5_correlated|base | g1.0 | worst_24h | 40.700 | 5.940 | 79.140 |
| S5_correlated|base | g4.0 | net_per_avail_slot_hour | -0.170 | -0.310 | -0.020 |
| S5_correlated|base | g4.0 | max_drawdown | -102.310 | -232.550 | 9.330 |
| S5_correlated|base | g4.0 | worst_24h | 14.430 | -23.780 | 59.410 |
| S5b_corr_benign|base | g0.4 | net_per_avail_slot_hour | 0.010 | -0.150 | 0.150 |
| S5b_corr_benign|base | g0.4 | max_drawdown | -24.310 | -51.790 | -0.850 |
| S5b_corr_benign|base | g0.4 | worst_24h | 19.100 | -9.220 | 47.000 |
| S5b_corr_benign|base | g1.0 | net_per_avail_slot_hour | -0.130 | -0.280 | 0.020 |
| S5b_corr_benign|base | g1.0 | max_drawdown | -30.830 | -54.910 | -4.370 |
| S5b_corr_benign|base | g1.0 | worst_24h | 28.690 | -3.770 | 58.590 |
| S5b_corr_benign|base | g4.0 | net_per_avail_slot_hour | -0.290 | -0.430 | -0.150 |
| S5b_corr_benign|base | g4.0 | max_drawdown | 8.060 | -14.110 | 31.710 |
| S5b_corr_benign|base | g4.0 | worst_24h | -19.100 | -52.930 | 15.430 |
| F_corr_collapse|base | g0.4 | net_per_avail_slot_hour | -0.050 | -0.170 | 0.090 |
| F_corr_collapse|base | g0.4 | max_drawdown | -85.300 | -208.330 | 34.140 |
| F_corr_collapse|base | g0.4 | worst_24h | -24.660 | -75.000 | 21.530 |
| F_corr_collapse|base | g1.0 | net_per_avail_slot_hour | -0.100 | -0.260 | 0.070 |
| F_corr_collapse|base | g1.0 | max_drawdown | -48.340 | -169.020 | 67.890 |
| F_corr_collapse|base | g1.0 | worst_24h | -32.490 | -84.210 | 20.380 |
| F_corr_collapse|base | g4.0 | net_per_avail_slot_hour | -0.340 | -0.500 | -0.190 |
| F_corr_collapse|base | g4.0 | max_drawdown | 62.060 | -108.230 | 209.640 |
| F_corr_collapse|base | g4.0 | worst_24h | -45.020 | -102.520 | 6.310 |
| S5_correlated|rho0.9 | g0.4 | net_per_avail_slot_hour | 0.040 | -0.060 | 0.140 |
| S5_correlated|rho0.9 | g0.4 | max_drawdown | -99.870 | -196.770 | -5.780 |
| S5_correlated|rho0.9 | g0.4 | worst_24h | 47.880 | 7.060 | 88.960 |
| S5_correlated|rho0.9 | g1.0 | net_per_avail_slot_hour | 0.050 | -0.060 | 0.150 |
| S5_correlated|rho0.9 | g1.0 | max_drawdown | -86.340 | -184.000 | 5.540 |
| S5_correlated|rho0.9 | g1.0 | worst_24h | 48.290 | 13.460 | 88.600 |
| S5_correlated|rho0.9 | g4.0 | net_per_avail_slot_hour | -0.160 | -0.300 | -0.030 |
| S5_correlated|rho0.9 | g4.0 | max_drawdown | -170.630 | -312.980 | -48.960 |
| S5_correlated|rho0.9 | g4.0 | worst_24h | 28.990 | -10.090 | 73.670 |
| S5b_corr_benign|rho0.9 | g0.4 | net_per_avail_slot_hour | 0.000 | -0.150 | 0.150 |
| S5b_corr_benign|rho0.9 | g0.4 | max_drawdown | -21.420 | -48.760 | 5.950 |
| S5b_corr_benign|rho0.9 | g0.4 | worst_24h | 10.930 | -21.050 | 41.960 |
| S5b_corr_benign|rho0.9 | g1.0 | net_per_avail_slot_hour | -0.130 | -0.260 | 0.000 |
| S5b_corr_benign|rho0.9 | g1.0 | max_drawdown | -27.140 | -54.050 | -1.510 |
| S5b_corr_benign|rho0.9 | g1.0 | worst_24h | 17.820 | -11.640 | 47.430 |
| S5b_corr_benign|rho0.9 | g4.0 | net_per_avail_slot_hour | -0.290 | -0.430 | -0.160 |
| S5b_corr_benign|rho0.9 | g4.0 | max_drawdown | 6.960 | -17.450 | 32.370 |
| S5b_corr_benign|rho0.9 | g4.0 | worst_24h | -14.970 | -46.110 | 17.450 |

Findings (OBSERVED):
- **Beneficial case (S5, crisis in the best-edge group):** γ≈0.4–1 leaves M1 unchanged (+0.04…+0.05, CI spans 0) and lowers worst-24h loss (γ=1: +41 bps [6,79]) and max drawdown (−38…−63, CI spans 0 at ρ=0.8; −86…−100 at ρ_g=0.9, CI mostly excluding 0). This is the only place a diversification benefit shows up, and it is a *risk* benefit at zero average cost, not an M1 gain.
- **Harmful case (S5b, benign correlation):** γ≥1 costs M1 (−0.13 [−0.28,+0.02]); γ=4 costs −0.29 [−0.43,−0.15] — the penalty simply rejects good opportunities.
- **Correlation collapse (market-wide factor):** penalising *group* concentration does not help (−0.05…−0.34 M1); drawdown is not significantly reduced (group-based diversification cannot protect against a market-wide factor; INFERENCE).
- **Parameter sensitivity (frozen ingest, 13 scenarios, validation split):** macro M1 across γ∈{0.02…0.4} spans 2.312–2.328 (flat).
- Why the effect is muted (INFERENCE): only ≤3 instruments per group and one position per instrument already cap group exposure at ≈3 of 4 slots; with K=4 and G=5 (heldout) natural diversification is high (group HHI 0.22–0.23 vs 0.20 perfect). A world with a few large groups, or K≫G, would give correlation penalties more leverage (UNKNOWN — not tested).

Verdict for this section: correlation-aware selection **does not reliably improve portfolio-level outcomes** and can merely reject good opportunities; a small penalty (γ≈0.4–1) is a *cheap tail-risk hedge candidate* worth local evaluation only if drawdown control is a stated goal.
