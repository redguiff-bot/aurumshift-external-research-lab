# 09 — Held-out results (pre-registered protocol)

Protocol and rules: `bench/capacity_v1/prereg/PREREGISTRATION.json` (v2, committed **before** the held-out run, commit `c4d0b86`); adjudication code `heldout_verdict.py` (SHA-256 recorded in the pre-registration); raw output `results/heldout_raw.csv.gz` (52,200 runs), machine verdict `results/heldout_verdict.json`. The held-out set was run once; no held-out number influenced any parameter, shortlist or threshold. Primary metric: paired latent-net-per-slot-hour difference normalised by RMS opportunity density (`dz`), pooled over caps 3/4/6/10; 95 % bootstrap CI over 450 family×variant×seed blocks.

## 1. All 29 policies (mean over 15 families × 4 caps; `[CI]` = 95 % bootstrap)
| policy | vs FIFO | vs FIFO_NETPOS | vs RANK_NET |
|---|---|---|---|
| ORACLE_DENSITY_NOT_IMPLEMENTABLE | +0.260 [+0.247,+0.274] | +0.170 [+0.159,+0.181] | +0.112 [+0.105,+0.119] |
| ORACLE_SCORE_NOT_IMPLEMENTABLE | +0.248 [+0.235,+0.261] | +0.157 [+0.147,+0.168] | +0.100 [+0.093,+0.107] |
| COMPOSED | +0.171 [+0.160,+0.182] | +0.081 [+0.073,+0.089] | +0.023 [+0.019,+0.027] |
| SHADOW_PRICE | +0.164 [+0.153,+0.175] | +0.073 [+0.066,+0.081] | +0.016 [+0.012,+0.019] |
| ONLINE_KNAPSACK_PSI | +0.163 [+0.153,+0.173] | +0.072 [+0.065,+0.080] | +0.015 [+0.010,+0.019] |
| UNCERTAINTY_LCB | +0.155 [+0.145,+0.165] | +0.065 [+0.057,+0.073] | +0.007 [+0.005,+0.010] |
| FLUID_QUANTILE | +0.161 [+0.151,+0.171] | +0.070 [+0.063,+0.078] | +0.013 [+0.009,+0.017] |
| MARGINAL_RISK | +0.154 [+0.145,+0.163] | +0.064 [+0.057,+0.071] | +0.006 [+0.005,+0.007] |
| SLEEPING_HEDGE | +0.151 [+0.142,+0.161] | +0.061 [+0.054,+0.068] | +0.003 [+0.002,+0.004] |
| TRUNK_RESERVATION | +0.158 [+0.147,+0.169] | +0.068 [+0.060,+0.076] | +0.010 [+0.005,+0.014] |
| CORR_PENALTY | +0.148 [+0.139,+0.158] | +0.058 [+0.051,+0.066] | +0.000 [-0.000,+0.001] |
| RANK_NET_MISSING_REJECT | +0.148 [+0.139,+0.158] | +0.058 [+0.051,+0.065] | +0.000 [-0.000,+0.001] |
| CLUSTER_CAP | +0.148 [+0.139,+0.157] | +0.058 [+0.051,+0.065] | +0.000 [-0.000,+0.001] |
| RANK_NET | +0.148 [+0.139,+0.157] | +0.058 [+0.051,+0.065] | nan |
| SLOTHOUR_DENSITY | +0.150 [+0.140,+0.159] | +0.059 [+0.052,+0.067] | +0.002 [+0.001,+0.003] |
| RANK_NET_UNKCOST_ZERO | +0.144 [+0.135,+0.154] | +0.054 [+0.047,+0.061] | -0.004 [-0.005,-0.003] |
| EVICT_SWAP | +0.153 [+0.143,+0.163] | +0.062 [+0.055,+0.070] | +0.005 [+0.001,+0.009] |
| SLOTHOUR_HAZARD | +0.146 [+0.136,+0.156] | +0.056 [+0.048,+0.064] | -0.002 [-0.004,+0.001] |
| CORR_HARD_REJECT | +0.141 [+0.131,+0.151] | +0.051 [+0.043,+0.058] | -0.007 [-0.009,-0.005] |
| LIN_TS | +0.128 [+0.118,+0.138] | +0.038 [+0.030,+0.045] | -0.020 [-0.026,-0.015] |
| RANK_SCORE_RAW | +0.131 [+0.123,+0.140] | +0.041 [+0.033,+0.049] | -0.017 [-0.018,-0.016] |
| LINUCB | +0.125 [+0.116,+0.135] | +0.035 [+0.027,+0.043] | -0.023 [-0.026,-0.019] |
| FIFO_NETPOS | +0.090 [+0.085,+0.096] | nan | -0.058 [-0.065,-0.051] |
| EQUAL_QUOTA | +0.029 [+0.025,+0.033] | -0.061 [-0.068,-0.055] | -0.119 [-0.127,-0.111] |
| ROUND_ROBIN | +0.029 [+0.025,+0.033] | -0.061 [-0.068,-0.055] | -0.119 [-0.126,-0.112] |
| SECRETARY_1_OVER_E | +0.014 [+0.002,+0.025] | -0.077 [-0.086,-0.067] | -0.134 [-0.147,-0.121] |
| RANDOM_SEEDED | +0.021 [+0.016,+0.026] | -0.070 [-0.077,-0.062] | -0.127 [-0.135,-0.120] |
| FIFO | nan | -0.090 [-0.096,-0.085] | -0.148 [-0.158,-0.139] |
| OLDEST_SLOT | -0.070 [-0.076,-0.064] | -0.161 [-0.169,-0.153] | -0.218 [-0.230,-0.207] |

Oracles and the LP bound are upper-bound references and never enter a verdict rule. `ORACLE_SCORE` is *below* several implementable methods on slot-hour value because ranking by true value without pricing slot occupancy is not optimal; only the hindsight LP is a bound.

## 2. Shortlist and simple reference (pre-registered)
Shortlist (chosen mechanically from validation): `COMPOSED`, `SHADOW_PRICE`, `ONLINE_KNAPSACK_PSI`; simple reference `RANK_NET`.

| method | reference | pooled | cells_ci_pos | cells_material_worse | cap3 | cap4 | cap6 | cap10 |
|---|---|---|---|---|---|---|---|---|
| RANK_NET | FIFO | +0.148 [+0.139,+0.158] | 1.00 | 0.00 | +0.182 | +0.168 | +0.142 | +0.099 |
| RANK_NET | FIFO_NETPOS | +0.058 [+0.051,+0.065] | 0.92 | 0.00 | +0.078 | +0.070 | +0.053 | +0.029 |
| COMPOSED | FIFO | +0.171 [+0.161,+0.182] | 1.00 | 0.00 | +0.224 | +0.195 | +0.157 | +0.107 |
| COMPOSED | FIFO_NETPOS | +0.081 [+0.073,+0.089] | 0.90 | 0.00 | +0.120 | +0.097 | +0.068 | +0.037 |
| COMPOSED | RANK_NET | +0.023 [+0.020,+0.027] | 0.65 | 0.00 | +0.042 | +0.028 | +0.015 | +0.008 |
| SHADOW_PRICE | FIFO | +0.164 [+0.153,+0.174] | 1.00 | 0.00 | +0.213 | +0.189 | +0.152 | +0.100 |
| SHADOW_PRICE | FIFO_NETPOS | +0.073 [+0.066,+0.081] | 0.87 | 0.00 | +0.109 | +0.091 | +0.063 | +0.030 |
| SHADOW_PRICE | RANK_NET | +0.016 [+0.012,+0.019] | 0.75 | 0.00 | +0.031 | +0.022 | +0.010 | +0.000 |
| ONLINE_KNAPSACK_PSI | FIFO | +0.163 [+0.152,+0.173] | 1.00 | 0.00 | +0.210 | +0.192 | +0.154 | +0.094 |
| ONLINE_KNAPSACK_PSI | FIFO_NETPOS | +0.072 [+0.065,+0.080] | 0.87 | 0.00 | +0.106 | +0.095 | +0.064 | +0.024 |
| ONLINE_KNAPSACK_PSI | RANK_NET | +0.015 [+0.010,+0.019] | 0.78 | 0.05 | +0.027 | +0.025 | +0.011 | -0.005 |
| FIFO_NETPOS | FIFO | +0.090 [+0.085,+0.096] | 1.00 | 0.00 | +0.104 | +0.098 | +0.089 | +0.070 |

Pre-registered criteria applied by the script:
| Criterion | COMPOSED | SHADOW_PRICE | ONLINE_KNAPSACK_PSI | RANK_NET |
|---|---|---|---|---|
| (a) pooled dz vs FIFO ≥ 0.10, CI lower > 0 | pass (0.171) | pass (0.164) | pass (0.163) | pass (0.148) |
| (b) ≥ 60 % of (family, cap) cells with CI lower > 0 vs FIFO | pass (1.00) | pass (1.00) | pass (1.00) | pass (1.00) |
| (c) ≤ 15 % of cells materially worse than FIFO | pass (0.00) | pass (0.00) | pass (0.00) | pass (0.00) |
| (d) pooled dz vs RANK_NET ≥ 0.02, CI lower > 0 | **pass (0.023, CI 0.020–0.027)** | fail (0.016) | fail (0.015) | — |
| (e) positive vs RANK_NET at ≥ 3 of 4 caps | pass (4/4) | pass (3/4; cap 10 = 0.000) | pass (3/4) | — |
| (f) leakage tests pass | pass | pass | pass | pass |
| RANK_NET beats FIFO_NETPOS by ≥ 0.02 (CI > 0) | — | — | — | pass (0.058) |

Max CI half-width vs FIFO over the four methods: 0.011 (≪ 0.10), so the study is *not* under-powered for its own thresholds.

## 3. Pre-registered verdict output
`FINAL_VERDICT (machine, per pre-registered rules) = CAPACITY_ALLOCATION_REFERENCE_SUPPORTED`, reference method **`COMPOSED`** (only shortlist method meeting (a)–(f)). **Fragility disclosure**: `COMPOSED` clears the beats-`RANK_NET` bar (0.02) by 0.003, and is separated from `SHADOW_PRICE` by only 0.007 dz and from `ONLINE_KNAPSACK_PSI` by 0.008 dz; the pre-registered logic does not pool them because they individually miss (d). See 12 for the sensitivity: with `δ_equivalence = 0.03` the same data gives `MULTIPLE_CAPACITY_METHODS_SUPPORTED`. The pre-registered verdict is reported as the verdict; the sensitivity is reported as such.

## 4. FIFO failure / equivalence per family (caps 4 and 6; best of `RANK_NET` + shortlist)
Pre-registered rule: FIFO_FAIL if that best method's dz vs FIFO ≥ 0.10 with CI lower > 0; FIFO_EQUIV if its CI upper bound < 0.04.
| family | best_method | dz_vs_FIFO | dz_vs_FIFO_NETPOS | FIFO_FAIL | FIFO_EQUIV |
|---|---|---|---|---|---|
| H1_chronic_corr_regime | ONLINE_KNAPSACK_PSI | +0.238 [+0.218,+0.257] | +0.107 [+0.097,+0.117] | True | False |
| H2_burst_noisy_missing | ONLINE_KNAPSACK_PSI | +0.104 [+0.091,+0.116] | +0.046 [+0.037,+0.055] | True | False |
| H3_spam_fastslow | COMPOSED | +0.173 [+0.156,+0.191] | +0.124 [+0.110,+0.137] | True | False |
| S10_spam | COMPOSED | +0.363 [+0.342,+0.385] | +0.238 [+0.217,+0.258] | True | False |
| S11_burst | ONLINE_KNAPSACK_PSI | +0.151 [+0.138,+0.165] | +0.030 [+0.025,+0.034] | True | False |
| S12_all_equal | RANK_NET | +0.341 [+0.280,+0.399] | +0.292 [+0.237,+0.348] | True | False |
| S1_sparse | ONLINE_KNAPSACK_PSI | +0.010 [+0.008,+0.013] | +0.000 [-0.000,+0.001] | False | True |
| S2_moderate | ONLINE_KNAPSACK_PSI | +0.100 [+0.092,+0.108] | +0.011 [+0.009,+0.014] | True | False |
| S3_chronic | SHADOW_PRICE | +0.364 [+0.343,+0.385] | +0.164 [+0.151,+0.177] | True | False |
| S4_late_quality | ONLINE_KNAPSACK_PSI | +0.127 [+0.117,+0.138] | +0.074 [+0.068,+0.081] | True | False |
| S5_correlated | ONLINE_KNAPSACK_PSI | +0.235 [+0.217,+0.252] | +0.088 [+0.081,+0.097] | True | False |
| S6_short_vs_long | SHADOW_PRICE | +0.086 [+0.070,+0.103] | +0.054 [+0.041,+0.068] | False | False |
| S7_regime_shift | ONLINE_KNAPSACK_PSI | +0.237 [+0.221,+0.253] | +0.094 [+0.084,+0.105] | True | False |
| S8_noisy_ranking | ONLINE_KNAPSACK_PSI | +0.164 [+0.143,+0.184] | +0.060 [+0.050,+0.070] | True | False |
| S9_missing_quality | ONLINE_KNAPSACK_PSI | +0.189 [+0.173,+0.205] | +0.095 [+0.083,+0.107] | True | False |

* **FIFO_FAIL (13 of 15)**: H1, H2, H3, S2, S3, S4, S5, S7, S8, S9, S10, S11, S12.
* **FIFO_EQUIVALENT (1 of 15)**: S1 (sparse demand: every policy admits nearly everything; utilisation 8–11 %).
* **Neither (1 of 15)**: S6 (dz +0.086 vs FIFO, below the 0.10 bar but CI excludes 0).
* **Most of the FIFO failure is a *filter + freshness* effect, not a ranking effect.** Against `FIFO_NETPOS` the same best methods win far less: S2 +0.011, S11 +0.030, H2 +0.046 — in those moderate/burst families a FIFO that at least refuses negative-value opportunities is nearly as good. The large FIFO gaps (S3, S10, S12, S5, S7, H1) shrink to 0.09–0.29 vs `FIFO_NETPOS`. S12 (all candidates nearly equal) is flagged FIFO_FAIL although there is no quality to discriminate: the residual +0.29 dz is explained by the post-hoc control `LIFO_NETPOS` (freshest-first) — FIFO serves the stalest opportunity first while edge decays; this is a modelling assumption (edge decays as e^(−age/8 h)), UNKNOWN in reality.

Sensitivity of "when does FIFO become materially worse?" (robustness sweep, `RANK_NET − FIFO` in bps per slot-hour, cap-pooled, 5 seeds):
| Axis | Levels (low → high) | `RANK_NET − FIFO` | `FIFO_NETPOS − FIFO` |
|---|---|---|---|
| offered load (0.5 / 1.5 / 3 / 6, at C=4) | sparse → chronic | +0.10 / +0.33 / +0.59 / +1.00 | +0.10 / +0.30 / +0.48 / +0.61 |
| score noise (×0.5, 1, 2, 4) | | +0.72 / +0.59 / +0.42 / +0.25 | +0.60 / +0.48 / +0.30 / +0.19 |
| score calibration slope (1.0 / 0.5 / 0.2 / −0.3) | | +0.59 / +0.48 / +0.24 / **−0.30** | +0.48 / +0.41 / +0.22 / −0.29 |
| cost multiplier (0.5×, 1×, 2×, 4×) | | +0.52 / +0.59 / +0.83 / +1.64 | +0.36 / +0.48 / +0.78 / +1.63 |

FIFO becomes materially worse (i) when demand exceeds ~1× capacity (offered load ≥ 1.0 at the given C), (ii) as costs rise (FIFO admits negative-value trades), (iii) when there are duplicate/spam streams (10), and it is not worse only when demand is sparse. It is **not** worse than a score-based rule when the score has no or negative predictive power (slope ≤ 0.2 / negative: all score-based methods lose to or barely beat FIFO). FIFO's robustness in that regime is the only setting where it is the better reference.

## 5. Validation → held-out stability
Pooled dz vs FIFO (tuned on TUNING, then VALIDATION → HELDOUT): `COMPOSED` 0.179 → 0.171, `SHADOW_PRICE` 0.174 → 0.164, `ONLINE_KNAPSACK_PSI` 0.171 → 0.163, `RANK_NET` 0.154 → 0.148, `FIFO_NETPOS` 0.100 → 0.090, `LINUCB` 0.125 → 0.125. Tuning optimism is ≈ 0.006–0.01 dz (less than the beats-`RANK_NET` margin of 0.023; the ordering is preserved). The wider held-out jitter and the three unseen compositions did not break the ordering.

## 6. Robustness (separate seeds 3000–3004, reference family, C = 3/4/6/10 pooled; bps per slot-hour)
| axis | level | FIFO | FIFO_NETPOS | RANK_NET | COMPOSED | SHADOW_PRICE | ONLINE_KNAPSACK_PSI | MARGINAL_RISK | CLUSTER_CAP | LINUCB | SLEEPING_HEDGE | EVICT_SWAP | OLDEST_SLOT | RANK_NET_UNKCOST_ZERO | COMPOSED-RANK_NET | RANK_NET-FIFO | FIFO_NETPOS-FIFO | best_impl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| arrival | 0 | 0.053 | 0.532 | 0.644 | 0.710 | 0.749 | 0.760 | 0.684 | 0.635 | 0.506 | 0.646 | 0.695 | -0.115 | 0.636 | 0.066 | 0.591 | 0.478 | ONLINE_KNAPSACK_PSI |
| arrival | 1 | 0.061 | 0.441 | 0.599 | 0.639 | 0.625 | 0.683 | 0.635 | 0.589 | 0.509 | 0.594 | 0.634 | -0.063 | 0.581 | 0.040 | 0.539 | 0.381 | ONLINE_KNAPSACK_PSI |
| arrival | 2 | 0.081 | 0.547 | 0.647 | 0.699 | 0.699 | 0.745 | 0.681 | 0.640 | 0.560 | 0.647 | 0.689 | -0.066 | 0.632 | 0.052 | 0.566 | 0.466 | ONLINE_KNAPSACK_PSI |
| arrival | 3 | 0.070 | 0.570 | 0.779 | 0.885 | 0.889 | 0.903 | 0.815 | 0.772 | 0.695 | 0.791 | 0.848 | -0.087 | 0.761 | 0.106 | 0.709 | 0.500 | ONLINE_KNAPSACK_PSI |
| corr_scale | 0 | 0.053 | 0.532 | 0.644 | 0.712 | 0.749 | 0.760 | 0.677 | 0.635 | 0.508 | 0.647 | 0.695 | -0.115 | 0.636 | 0.068 | 0.591 | 0.478 | ONLINE_KNAPSACK_PSI |
| corr_scale | 1 | 0.053 | 0.532 | 0.644 | 0.710 | 0.749 | 0.760 | 0.684 | 0.635 | 0.506 | 0.646 | 0.695 | -0.115 | 0.636 | 0.066 | 0.591 | 0.478 | ONLINE_KNAPSACK_PSI |
| corr_scale | 2 | 0.053 | 0.532 | 0.644 | 0.710 | 0.749 | 0.760 | 0.683 | 0.635 | 0.511 | 0.644 | 0.695 | -0.115 | 0.636 | 0.066 | 0.591 | 0.478 | ONLINE_KNAPSACK_PSI |
| corr_scale | 3 | 0.053 | 0.532 | 0.644 | 0.711 | 0.749 | 0.760 | 0.661 | 0.635 | 0.391 | 0.645 | 0.695 | -0.115 | 0.636 | 0.067 | 0.591 | 0.478 | ONLINE_KNAPSACK_PSI |
| cost_unknown | 0 | 0.053 | 0.528 | 0.647 | 0.711 | 0.749 | 0.759 | 0.685 | 0.637 | 0.508 | 0.648 | 0.698 | -0.115 | 0.647 | 0.065 | 0.594 | 0.475 | ONLINE_KNAPSACK_PSI |
| cost_unknown | 1 | 0.053 | 0.532 | 0.644 | 0.710 | 0.749 | 0.760 | 0.684 | 0.635 | 0.506 | 0.646 | 0.695 | -0.115 | 0.636 | 0.066 | 0.591 | 0.478 | ONLINE_KNAPSACK_PSI |
| cost_unknown | 2 | 0.053 | 0.533 | 0.643 | 0.708 | 0.744 | 0.760 | 0.685 | 0.634 | 0.527 | 0.646 | 0.695 | -0.115 | 0.587 | 0.065 | 0.590 | 0.480 | ONLINE_KNAPSACK_PSI |
| cost_unknown | 3 | 0.053 | 0.527 | 0.643 | 0.705 | 0.737 | 0.758 | 0.686 | 0.631 | 0.527 | 0.648 | 0.692 | -0.115 | 0.566 | 0.062 | 0.590 | 0.474 | ONLINE_KNAPSACK_PSI |
| cost_x | 0 | 0.352 | 0.712 | 0.874 | 0.974 | 0.994 | 0.983 | 0.918 | 0.866 | 0.752 | 0.884 | 0.959 | 0.284 | 0.867 | 0.099 | 0.522 | 0.360 | SHADOW_PRICE |
| cost_x | 1 | 0.053 | 0.532 | 0.644 | 0.710 | 0.749 | 0.760 | 0.684 | 0.635 | 0.506 | 0.646 | 0.695 | -0.115 | 0.636 | 0.066 | 0.591 | 0.478 | ONLINE_KNAPSACK_PSI |
| cost_x | 2 | -0.545 | 0.230 | 0.280 | 0.304 | 0.320 | 0.364 | 0.322 | 0.271 | 0.112 | 0.278 | 0.273 | -0.912 | 0.220 | 0.024 | 0.825 | 0.775 | ONLINE_KNAPSACK_PSI |
| cost_x | 3 | -1.741 | -0.110 | -0.106 | -0.098 | -0.104 | -0.056 | -0.069 | -0.105 | -0.207 | -0.099 | -0.113 | -2.507 | -0.323 | 0.008 | 1.635 | 1.631 | SECRETARY_1_OVER_E |
| duration_dist | 0 | 0.055 | 0.576 | 0.713 | 0.793 | 0.831 | 0.828 | 0.765 | 0.705 | 0.592 | 0.725 | 0.760 | -0.122 | 0.704 | 0.080 | 0.658 | 0.521 | SHADOW_PRICE |
| duration_dist | 1 | 0.053 | 0.532 | 0.644 | 0.710 | 0.749 | 0.760 | 0.684 | 0.635 | 0.506 | 0.646 | 0.695 | -0.115 | 0.636 | 0.066 | 0.591 | 0.478 | ONLINE_KNAPSACK_PSI |
| duration_dist | 2 | 0.099 | 0.497 | 0.544 | 0.565 | 0.573 | 0.623 | 0.585 | 0.541 | 0.472 | 0.540 | 0.593 | 0.031 | 0.534 | 0.021 | 0.446 | 0.398 | ONLINE_KNAPSACK_PSI |
| duration_dist | 3 | 0.040 | 0.546 | 0.648 | 0.705 | 0.738 | 0.760 | 0.691 | 0.643 | 0.528 | 0.654 | 0.716 | -0.075 | 0.641 | 0.057 | 0.608 | 0.506 | ONLINE_KNAPSACK_PSI |
| load | 0 | 0.115 | 0.219 | 0.219 | 0.219 | 0.219 | 0.222 | 0.221 | 0.218 | 0.178 | 0.219 | 0.219 | 0.109 | 0.216 | 0.000 | 0.104 | 0.104 | ONLINE_KNAPSACK_PSI |
| load | 1 | 0.134 | 0.432 | 0.461 | 0.467 | 0.470 | 0.506 | 0.488 | 0.457 | 0.393 | 0.459 | 0.474 | 0.078 | 0.456 | 0.006 | 0.327 | 0.298 | ONLINE_KNAPSACK_PSI |
| load | 2 | 0.053 | 0.532 | 0.644 | 0.710 | 0.749 | 0.760 | 0.684 | 0.635 | 0.506 | 0.646 | 0.695 | -0.115 | 0.636 | 0.066 | 0.591 | 0.478 | ONLINE_KNAPSACK_PSI |
| load | 3 | -0.004 | 0.602 | 0.996 | 1.204 | 1.200 | 1.186 | 1.023 | 0.984 | 0.957 | 1.017 | 1.102 | -0.241 | 0.972 | 0.207 | 1.000 | 0.606 | FLUID_QUANTILE |
| regime | 0 | 0.053 | 0.532 | 0.644 | 0.710 | 0.749 | 0.760 | 0.684 | 0.635 | 0.506 | 0.646 | 0.695 | -0.115 | 0.636 | 0.066 | 0.591 | 0.478 | ONLINE_KNAPSACK_PSI |
| regime | 1 | 0.052 | 0.242 | 0.290 | 0.310 | 0.323 | 0.377 | 0.334 | 0.280 | 0.234 | 0.283 | 0.304 | -0.110 | 0.284 | 0.020 | 0.238 | 0.190 | ONLINE_KNAPSACK_PSI |
| regime | 2 | 0.052 | 0.333 | 0.408 | 0.455 | 0.474 | 0.517 | 0.450 | 0.397 | 0.314 | 0.405 | 0.440 | -0.119 | 0.397 | 0.046 | 0.356 | 0.280 | ONLINE_KNAPSACK_PSI |
| regime | 3 | 0.055 | 0.436 | 0.529 | 0.587 | 0.617 | 0.641 | 0.576 | 0.521 | 0.406 | 0.524 | 0.574 | -0.112 | 0.521 | 0.058 | 0.474 | 0.381 | ONLINE_KNAPSACK_PSI |
| score_calib_slope | 0 | 0.053 | 0.532 | 0.644 | 0.710 | 0.749 | 0.760 | 0.684 | 0.635 | 0.506 | 0.646 | 0.695 | -0.115 | 0.636 | 0.066 | 0.591 | 0.478 | ONLINE_KNAPSACK_PSI |
| score_calib_slope | 1 | 0.053 | 0.462 | 0.537 | 0.555 | 0.587 | 0.586 | 0.552 | 0.530 | 0.327 | 0.541 | 0.561 | -0.115 | 0.503 | 0.017 | 0.484 | 0.409 | SHADOW_PRICE |
| score_calib_slope | 2 | 0.053 | 0.272 | 0.294 | 0.291 | 0.293 | 0.273 | 0.283 | 0.290 | 0.154 | 0.311 | 0.290 | -0.115 | 0.273 | -0.003 | 0.241 | 0.219 | SLEEPING_HEDGE |
| score_calib_slope | 3 | 0.053 | -0.241 | -0.246 | -0.207 | -0.250 | -0.200 | -0.211 | -0.243 | 0.252 | -0.232 | -0.264 | -0.115 | -0.245 | 0.039 | -0.299 | -0.294 | LIN_TS |
| score_noise_x | 0 | 0.053 | 0.654 | 0.774 | 0.837 | 0.862 | 0.880 | 0.812 | 0.764 | 0.624 | 0.770 | 0.831 | -0.115 | 0.748 | 0.063 | 0.721 | 0.601 | ONLINE_KNAPSACK_PSI |
| score_noise_x | 1 | 0.053 | 0.532 | 0.644 | 0.710 | 0.749 | 0.760 | 0.684 | 0.635 | 0.506 | 0.646 | 0.695 | -0.115 | 0.636 | 0.066 | 0.591 | 0.478 | ONLINE_KNAPSACK_PSI |
| score_noise_x | 2 | 0.053 | 0.356 | 0.471 | 0.521 | 0.550 | 0.555 | 0.508 | 0.462 | 0.327 | 0.474 | 0.502 | -0.115 | 0.458 | 0.049 | 0.418 | 0.303 | ONLINE_KNAPSACK_PSI |
| score_noise_x | 3 | 0.053 | 0.238 | 0.307 | 0.353 | 0.345 | 0.345 | 0.320 | 0.310 | 0.190 | 0.305 | 0.283 | -0.115 | 0.302 | 0.046 | 0.254 | 0.185 | TRUNK_RESERVATION |

Highlights: the ordering `FIFO ≪ FIFO_NETPOS < RANK_NET < {COMPOSED, SHADOW_PRICE, ONLINE_KNAPSACK_PSI}` holds across arrival process (Poisson/MMPP/periodic/burst), score noise ×0.5…×4, duration distribution (lognormal σ 0.3/0.55/1.0, Pareto), correlation scale, regime timing, unknown-cost share 0–70 %, load 0.5–6. It **breaks** (a) at zero/negative calibration slope (all score-based rules ≈ or < FIFO; LinTS is the only method that recovers, +0.25), (b) at 4× cost (every method loses money; FIFO loses most), (c) at load 0.5 where every value-aware method ties. `COMPOSED − RANK_NET` ranges from −0.003 (calibration slope 0.2) and 0.000 (load 0.5) up to +0.21 (load 6), typically +0.02…+0.07.
