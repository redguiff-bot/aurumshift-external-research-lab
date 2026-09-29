# 06 — Diversification

Question: does correlation-aware selection improve **portfolio-level** outcomes, or merely reject good opportunities?

Implemented against the same base ranking (`RANK_NET`):
* `CLUSTER_CAP` — hard cap of ⌈0.75·C⌉ open positions per known cluster (greedy = exact optimum for this laminar constraint; verified equal to a MILP on 200/200 random instances).
* `CORR_PENALTY` — value − γ·(cross-covariance of the candidate with open/selected positions, side-signed), γ tuned = 0.02.
* `MARGINAL_RISK` — full marginal variance contribution incl. own variance, γ tuned = 0.05.
* `CORR_HARD_REJECT` — reject if side-signed correlation with any open position ≥ 0.95 (tuned; smaller ρ hurt in tuning).
The correlation matrix is estimated *causally* from observed returns (bias-corrected EWMA with 0.05 shrinkage, used only after 60 observations). Independent ranking = `RANK_NET`.

## Held-out paired differences vs `RANK_NET` (bootstrap 95 % CI; latent dz in RMS-density units; risk metrics in bps of daily PnL)
| policy | families | d_lat_dz | d_ret_to_risk | d_pnl_day_sd | d_max_dd | d_hhi | d_hq_missed |
|---|---|---|---|---|---|---|---|
| CLUSTER_CAP | all | +0.0002 [-0.0003,+0.0007] | +0.0002 [-0.0021,+0.0027] | +0.1579 [-0.1196,+0.4350] | -3.8473 [-8.4950,+0.4181] | -0.0067 [-0.0080,-0.0055] | +0.0002 [-0.0006,+0.0009] |
| CLUSTER_CAP | corr families S5/H1 | -0.0060 [-0.0071,-0.0048] | -0.0142 [-0.0219,-0.0067] | +0.9050 [-0.6913,+2.4828] | +0.5466 [-20.3070,+22.1207] | -0.0201 [-0.0230,-0.0177] | +0.0083 [+0.0062,+0.0105] |
| CORR_PENALTY | all | +0.0005 [-0.0001,+0.0010] | +0.0263 [+0.0203,+0.0328] | -7.0170 [-8.1499,-5.8957] | -42.1008 [-54.7092,-31.0591] | +0.0006 [-0.0001,+0.0013] | -0.0007 [-0.0017,+0.0004] |
| CORR_PENALTY | corr families S5/H1 | +0.0020 [+0.0001,+0.0039] | +0.0507 [+0.0329,+0.0690] | -25.5211 [-31.3108,-19.9285] | -141.6769 [-209.4839,-84.2086] | -0.0017 [-0.0042,+0.0008] | -0.0021 [-0.0057,+0.0016] |
| MARGINAL_RISK | all | +0.0060 [+0.0047,+0.0073] | +0.0947 [+0.0845,+0.1057] | -16.4759 [-18.5422,-14.5780] | -112.3826 [-132.0274,-93.4885] | +0.0200 [+0.0179,+0.0222] | -0.0110 [-0.0134,-0.0087] |
| MARGINAL_RISK | corr families S5/H1 | +0.0079 [+0.0049,+0.0109] | +0.1651 [+0.1369,+0.1936] | -52.9959 [-62.0557,-44.2494] | -351.5981 [-448.1275,-263.4767] | +0.0317 [+0.0238,+0.0399] | -0.0076 [-0.0137,-0.0018] |
| CORR_HARD_REJECT | all | -0.0070 [-0.0092,-0.0045] | +0.0517 [+0.0388,+0.0654] | -14.6878 [-15.9442,-13.5109] | -87.7631 [-104.9312,-71.7255] | -0.0253 [-0.0292,-0.0218] | +0.0201 [+0.0170,+0.0232] |
| CORR_HARD_REJECT | corr families S5/H1 | -0.0157 [-0.0178,-0.0137] | +0.0217 [-0.0001,+0.0455] | -24.6676 [-29.3596,-20.1414] | -100.3837 [-139.5080,-61.4781] | -0.0217 [-0.0249,-0.0184] | +0.0286 [+0.0232,+0.0340] |
| COMPOSED | all | +0.0231 [+0.0196,+0.0268] | +0.0849 [+0.0706,+0.0991] | -3.7926 [-4.6871,-2.8994] | -61.3174 [-77.4137,-46.1239] | +0.0209 [+0.0169,+0.0249] | -0.0305 [-0.0367,-0.0235] |
| COMPOSED | corr families S5/H1 | +0.0287 [+0.0246,+0.0328] | +0.0665 [+0.0496,+0.0840] | -4.4222 [-7.1012,-1.7289] | -69.6103 [-122.5648,-19.0238] | +0.0140 [+0.0092,+0.0188] | -0.0548 [-0.0611,-0.0483] |

Absolute values on the two correlated families (S5, H1), caps 4 and 6:
| policy | lat_per_slot_hour | ret_to_risk | pnl_day_sd | max_drawdown | hhi_cluster | eff_clusters | max_cluster_share | hq_missed_frac |
|---|---|---|---|---|---|---|---|---|
| ORACLE_DENSITY_NOT_IMPLEMENTABLE | 1.087 | 0.711 | 190.135 | 637.966 | 0.674 | 1.582 | 0.738 | 0.241 |
| ORACLE_SCORE_NOT_IMPLEMENTABLE | 1.039 | 0.687 | 188.468 | 660.354 | 0.677 | 1.575 | 0.741 | 0.321 |
| COMPOSED | 0.780 | 0.538 | 184.886 | 769.015 | 0.689 | 1.555 | 0.751 | 0.402 |
| SHADOW_PRICE | 0.813 | 0.578 | 179.090 | 749.255 | 0.707 | 1.523 | 0.765 | 0.391 |
| ONLINE_KNAPSACK_PSI | 0.843 | 0.606 | 174.424 | 707.470 | 0.714 | 1.512 | 0.771 | 0.355 |
| UNCERTAINTY_LCB | 0.715 | 0.491 | 186.526 | 798.185 | 0.677 | 1.575 | 0.741 | 0.454 |
| FLUID_QUANTILE | 0.806 | 0.552 | 183.253 | 760.209 | 0.697 | 1.541 | 0.758 | 0.386 |
| MARGINAL_RISK | 0.738 | 0.649 | 136.553 | 498.461 | 0.706 | 1.528 | 0.763 | 0.442 |
| SLEEPING_HEDGE | 0.713 | 0.480 | 188.049 | 834.243 | 0.680 | 1.570 | 0.744 | 0.456 |
| TRUNK_RESERVATION | 0.801 | 0.564 | 180.768 | 757.946 | 0.689 | 1.557 | 0.754 | 0.372 |
| CORR_PENALTY | 0.718 | 0.535 | 164.068 | 697.233 | 0.675 | 1.581 | 0.739 | 0.453 |
| RANK_NET_MISSING_REJECT | 0.715 | 0.486 | 188.106 | 814.774 | 0.677 | 1.577 | 0.741 | 0.455 |
| CLUSTER_CAP | 0.682 | 0.464 | 188.853 | 807.772 | 0.639 | 1.642 | 0.712 | 0.470 |
| RANK_NET | 0.715 | 0.486 | 188.106 | 814.774 | 0.677 | 1.577 | 0.741 | 0.455 |
| SLOTHOUR_DENSITY | 0.726 | 0.497 | 190.127 | 812.278 | 0.674 | 1.581 | 0.739 | 0.436 |
| RANK_NET_UNKCOST_ZERO | 0.703 | 0.469 | 189.934 | 872.423 | 0.672 | 1.585 | 0.737 | 0.456 |
| EVICT_SWAP | 0.791 | 0.532 | 188.790 | 818.877 | 0.676 | 1.577 | 0.741 | 0.323 |
| SLOTHOUR_HAZARD | 0.727 | 0.492 | 188.143 | 811.729 | 0.673 | 1.584 | 0.737 | 0.425 |
| CORR_HARD_REJECT | 0.674 | 0.502 | 168.595 | 758.222 | 0.651 | 1.630 | 0.716 | 0.469 |
| LIN_TS | 0.646 | 0.437 | 172.389 | 771.111 | 0.711 | 1.520 | 0.765 | 0.473 |
| RANK_SCORE_RAW | 0.639 | 0.416 | 193.556 | 942.269 | 0.655 | 1.616 | 0.722 | 0.475 |
| LINUCB | 0.609 | 0.384 | 189.079 | 911.484 | 0.670 | 1.592 | 0.732 | 0.473 |
| FIFO_NETPOS | 0.568 | 0.394 | 188.181 | 924.682 | 0.666 | 1.597 | 0.731 | 0.504 |
| EQUAL_QUOTA | 0.226 | 0.159 | 193.037 | 1237.248 | 0.609 | 1.707 | 0.678 | 0.599 |
| ROUND_ROBIN | 0.235 | 0.155 | 193.737 | 1141.299 | 0.611 | 1.704 | 0.679 | 0.597 |
| SECRETARY_1_OVER_E | 0.276 | 0.435 | 80.213 | 309.454 | 0.921 | 1.150 | 0.930 | 0.801 |
| RANDOM_SEEDED | 0.239 | 0.134 | 194.769 | 1282.829 | 0.618 | 1.690 | 0.686 | 0.601 |
| FIFO | 0.177 | 0.117 | 196.976 | 1307.223 | 0.617 | 1.692 | 0.685 | 0.597 |
| OLDEST_SLOT | -0.011 | -0.005 | 198.084 | 1682.635 | 0.613 | 1.700 | 0.681 | 0.391 |

## Findings
* **`CORR_PENALTY` (correlation only) improves portfolio risk at no measurable cost in expected value.** Over all families: daily-PnL sd −7.0 bps (CI −8.1…−5.9), max drawdown −42 (−55…−31), return-to-risk +0.026; latent dz +0.0005 (CI includes 0). On the correlated families: sd −25.5, drawdown −142, return-to-risk +0.051, dz +0.002. **OBSERVED.**
* **`CORR_HARD_REJECT` and `CLUSTER_CAP` do what the mission suspected: they mostly reject good opportunities.** Hard reject: dz −0.007 overall, −0.016 on the correlated families, `hq_missed_frac` +0.02/+0.03, although risk falls. `CLUSTER_CAP` on the correlated families: dz −0.006 *and* return-to-risk −0.014 (worse), HQ misses +0.008, HHI −0.020 (it does diversify by cluster count, but not to any benefit).
* **`MARGINAL_RISK` looks best (dz +0.006, return-to-risk +0.095, sd −16, drawdown −112) but the gain is not primarily correlation.** Post-hoc diagnostic on *validation* worlds (not pre-registered, `posthoc.py`): a variant with only the own-variance term (`MARGINAL_DIAG`, no correlation at all) earns the larger expected-value gain (+0.012 dz vs +0.005) and a smaller risk gain (return-to-risk +0.064 vs +0.087), while `CORR_PENALTY` alone gives +0.026 return-to-risk with dz ≈ 0. INFERENCE: the own-variance term acts as a volatility/duration penalty (long, volatile positions hold slots longer), which is slot economics rather than diversification; the correlation term supplies the pure diversification benefit and it is small in expected-value units.
* **Effect size is small relative to the sampling of scenarios**: even on S5 (strongly correlated) `RANK_NET` → `MARGINAL_RISK` is +0.010 dz. Portfolio-level gains are visible mainly in *risk* metrics (volatility, drawdown), not in mean latent value.
* **Correlation-collapse stress** (cluster-factor volatility ×1…×8 from mid-run, cap 4, failure-mode probe on separate seeds): expected value is unchanged for every policy (edge accrual does not depend on correlation), but risk explodes for the independent ranking: `RANK_NET` daily-PnL sd 105 → 149 → 258 → 493 bps and max drawdown 346 → 589 → 1274 → 2860 as the multiplier goes 1 → 2 → 4 → 8. `MARGINAL_RISK` holds sd to 91 → 116 → 162 → 259 (about half at ×8) and drawdown to 1516, with a *higher* latent value (0.766 vs 0.753 at ×8). `CLUSTER_CAP` does **not** help there (sd 486 vs 493, latent value lower, 0.715). So the soft, estimated-correlation penalty is the useful diversification device; the static structural cap is not. Caveat: the estimator (EWMA over ~100 h) adapts to the regime with a lag; the 8× case is a single step change.

`BEST_DIVERSIFICATION_REFERENCE` (descriptive, pre-registered pick rule = highest held-out return-to-risk among the four with non-negative value effect): **`CORR_PENALTY`** as the clean correlation-only reference, with `MARGINAL_RISK` the higher-scoring but partly-not-correlation composite. Neither is a drop-in allocator (11, 12).
