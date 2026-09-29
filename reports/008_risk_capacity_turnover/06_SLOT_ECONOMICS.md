# 06 — Slot economics, spam and starvation

## Macro results per policy (heldout H1; mean over scenarios of per-scenario means; OBSERVED)
| policy | net_per_avail_slot_hour | net_per_busy_slot_hour | regret_vs_oracle_M1 | idle_slot_hours | idle_with_backlog | turnover_per_slot_hour | churn_reentry_frac | mean_hold | hhi_inst | hhi_group | rej_rate_instw | adm_rate | hq_capture |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIFO | 1.781 | 2.028 | 3.938 | 292.723 | 0.000 | 0.104 | 0.305 | 8.753 | 0.094 | 0.231 | 3.461 | 3.439 | 0.638 |
| ROUND_ROBIN | 1.775 | 2.024 | 3.944 | 296.138 | 0.000 | 0.104 | 0.259 | 8.755 | 0.090 | 0.223 | 3.417 | 3.419 | 0.660 |
| RANDOM | 1.739 | 1.986 | 3.980 | 298.862 | 0.000 | 0.104 | 0.305 | 8.711 | 0.092 | 0.226 | 3.344 | 3.412 | 0.644 |
| EQUAL_QUOTA | 1.740 | 1.985 | 3.979 | 295.308 | 0.000 | 0.102 | 0.227 | 8.842 | 0.083 | 0.216 | 3.486 | 3.346 | 0.623 |
| OLDEST_SLOT | 1.966 | 2.256 | 3.753 | 320.304 | 0.000 | 0.196 | 0.441 | 5.041 | 0.087 | 0.226 | 3.495 | 2.920 | 0.934 |
| FIFO_SCREEN | 1.944 | 2.304 | 3.775 | 371.323 | 51.808 | 0.100 | 0.307 | 8.737 | 0.097 | 0.232 | 3.033 | 3.873 | 0.698 |
| SCORE_RANK | 2.145 | 2.543 | 3.574 | 379.369 | 56.612 | 0.098 | 0.336 | 8.935 | 0.098 | 0.232 | 2.818 | 4.283 | 0.700 |
| SLOTHOUR | 2.216 | 2.628 | 3.503 | 382.854 | 57.796 | 0.104 | 0.339 | 8.379 | 0.092 | 0.228 | 2.706 | 4.419 | 0.742 |
| SLOTHOUR_SHADOW | 2.225 | 2.845 | 3.494 | 510.385 | 158.500 | 0.100 | 0.343 | 8.158 | 0.095 | 0.232 | 2.701 | 4.727 | 0.729 |
| UNCERTAINTY_LCB | 2.278 | 2.657 | 3.441 | 359.354 | 39.281 | 0.106 | 0.364 | 8.363 | 0.095 | 0.231 | 2.767 | 4.495 | 0.752 |
| CORR_AWARE | 2.194 | 2.604 | 3.525 | 382.688 | 57.258 | 0.104 | 0.337 | 8.376 | 0.092 | 0.227 | 2.713 | 4.404 | 0.741 |
| LINTS | 2.196 | 2.607 | 3.523 | 383.331 | 57.665 | 0.105 | 0.338 | 8.345 | 0.091 | 0.227 | 2.735 | 4.396 | 0.743 |
| ORACLE_GREEDY_UB | 5.719 | 6.660 | 0.000 | 376.496 | 58.535 | 0.121 | 0.331 | 7.361 | 0.088 | 0.223 | 1.530 | 9.256 | 0.889 |

Definitions: M1 = net / (K·W); rejected-quality = mean realised net **per hold-hour** of rejected candidates (instrument-weighted; lower is better because rejected opportunities were worse); adm_rate = same for admitted trades; regret = ORACLE_GREEDY_UB M1 − policy M1 (oracle is a greedy foresight upper reference, **not implementable**, and also avoids negative-net trades, which no score-based method can fully do).

Findings:
- **Slot-hour economics is visible in the numbers** (OBSERVED): admitted quality per hold-hour rises from 3.44 (FIFO) to 4.42 (SLOTHOUR) while rejected quality falls from 3.46 to 2.71. The oracle sits at 9.26 / 1.53. Even the best implementable policy closes only ~13% of the FIFO→oracle gap (INFERENCE: the rest is score noise plus outcome noise that no admission rule can remove).
- **Opportunity cost**: idle slot-hours are *higher* for ranking policies (screening) — e.g. SLOTHOUR idles 383 vs FIFO 293 slot-hours — yet earns more. Idle-with-backlog (declined although candidates waited) is 58 for SLOTHOUR and 158 for the shadow-price policy. Idleness is a *decision*, not a defect, when the marginal candidate has negative estimated net.
- **Turnover/churn**: OLDEST_SLOT doubles turnover (0.20 vs 0.10 admissions/slot-hour) and re-entry churn (0.44); ranking policies do not increase turnover materially.
- **Concentration**: instrument HHI is ≈0.09–0.10 for all policies (uniform would be 1/15≈0.067); group HHI ≈0.22–0.23 (uniform 0.2). Ranking does **not** produce material extra concentration at the group level here (INFERENCE: one-position-per-instrument and few instruments per group cap it — see 07 and 14).

## Starvation (measured explicitly; do not hide behind aggregate PnL)
Definitions: *hard starvation rate* = share of instruments with ≥5 emissions that received zero admissions; *soft* = admissions < 25% of the mean; *max denial hours* = longest span from an instrument's first emission after its last admission until its next admission (an economically correct denial of a poor instrument also counts — read as an upper bound); *top_inst_admit_share* = largest share of admissions to one instrument.

| policy | starve_inst_rate | starve_soft_rate | max_denial_hours | top_inst_admit_share | hhi_inst |
|---|---|---|---|---|---|
| FIFO | 0.000 | 0.016 | 214.773 | 0.144 | 0.094 |
| ROUND_ROBIN | 0.000 | 0.008 | 193.369 | 0.130 | 0.090 |
| RANDOM | 0.000 | 0.008 | 205.150 | 0.141 | 0.092 |
| EQUAL_QUOTA | 0.000 | 0.000 | 132.669 | 0.095 | 0.083 |
| OLDEST_SLOT | 0.000 | 0.007 | 104.958 | 0.134 | 0.087 |
| FIFO_SCREEN | 0.001 | 0.023 | 247.592 | 0.149 | 0.097 |
| SCORE_RANK | 0.003 | 0.039 | 289.915 | 0.155 | 0.098 |
| SLOTHOUR | 0.002 | 0.031 | 272.692 | 0.160 | 0.092 |
| SLOTHOUR_SHADOW | 0.002 | 0.058 | 324.988 | 0.170 | 0.095 |
| UNCERTAINTY_LCB | 0.005 | 0.059 | 330.496 | 0.168 | 0.095 |
| CORR_AWARE | 0.002 | 0.029 | 272.427 | 0.161 | 0.092 |
| LINTS | 0.002 | 0.027 | 260.823 | 0.161 | 0.091 |
| ORACLE_GREEDY_UB | 0.000 | 0.012 | 197.304 | 0.145 | 0.088 |

- Hard starvation is ≈0 for every policy (max 0.005) — with this arrival structure every instrument eventually gets in (OBSERVED; would not hold with true score-dominance, UNKNOWN).
- Soft starvation is 2–7× higher for ranking methods (SLOTHOUR 0.031, SHADOW 0.058, LCB 0.059 vs RR/EQUAL_QUOTA/RANDOM ≤0.008) and denial spells are longer (≈270–330 h vs 130–215 h).
- **Do safeguards distort economic allocation?** Yes, materially: EQUAL_QUOTA and ROUND_ROBIN have no starvation but sit at M1 1.74/1.77 — i.e. they give back the *entire* ranking gain (−0.44 to −0.48 vs SLOTHOUR). A fairness guarantee therefore has a measurable price of ≈0.45 bps/slot-hour here (OBSERVED, synthetic). Whether fairness matters economically for the real system is UNKNOWN; no lighter safeguard (e.g. age-bonus, minimum-share) was tested — parked.

## Candidate spam (S10 + H2 + D4 diagnostics)
Spam instruments emit ×20 events but have mediocre edge. Four ingest semantics compared (heldout H2, 10 seeds, K=4).

Top-instrument admission share in S10 (largest share of admissions to a single instrument; non-spam scenarios ≈0.14–0.17):
| policy | COOLDOWN | DEDUP_LATEST | RAW | SCORE_UPDATE |
|---|---|---|---|---|
| FIFO | 0.303 | 0.293 | 0.326 | 0.328 |
| FIFO_SCREEN | 0.316 | 0.310 | 0.342 | 0.343 |
| ROUND_ROBIN | 0.281 | 0.287 | 0.287 | 0.287 |
| SLOTHOUR | 0.314 | 0.335 | 0.348 | 0.335 |
| UNCERTAINTY_LCB | 0.322 | 0.336 | 0.341 | 0.336 |

M1 in S10 by ingest semantics:
| policy | COOLDOWN | DEDUP_LATEST | RAW | SCORE_UPDATE |
|---|---|---|---|---|
| FIFO | 2.227 | 2.272 | 2.163 | 2.220 |
| FIFO_SCREEN | 2.121 | 2.295 | 2.214 | 2.198 |
| ROUND_ROBIN | 2.136 | 2.174 | 2.174 | 2.174 |
| SLOTHOUR | 2.240 | 2.389 | 2.297 | 2.389 |
| UNCERTAINTY_LCB | 2.403 | 2.361 | 2.416 | 2.361 |

Paired effect vs RAW (validation-split S10, seeds 7000–7009, frozen params; effect on M1 and top-instrument admission share):
| policy | ingest | metric | diff_vs_RAW | lo | hi |
|---|---|---|---|---|---|
| FIFO | DEDUP_LATEST | net_per_avail_slot_hour | 0.105 | -0.020 | 0.230 |
| FIFO | DEDUP_LATEST | top_inst_admit_share | -0.024 | -0.040 | -0.013 |
| FIFO | COOLDOWN | net_per_avail_slot_hour | -0.030 | -0.165 | 0.115 |
| FIFO | COOLDOWN | top_inst_admit_share | -0.022 | -0.035 | -0.008 |
| FIFO | SCORE_UPDATE | net_per_avail_slot_hour | 0.081 | -0.037 | 0.250 |
| FIFO | SCORE_UPDATE | top_inst_admit_share | 0.003 | -0.004 | 0.010 |
| SLOTHOUR | DEDUP_LATEST | net_per_avail_slot_hour | -0.043 | -0.149 | 0.061 |
| SLOTHOUR | DEDUP_LATEST | top_inst_admit_share | -0.007 | -0.015 | -0.000 |
| SLOTHOUR | COOLDOWN | net_per_avail_slot_hour | -0.252 | -0.370 | -0.118 |
| SLOTHOUR | COOLDOWN | top_inst_admit_share | -0.034 | -0.044 | -0.024 |
| SLOTHOUR | SCORE_UPDATE | net_per_avail_slot_hour | -0.043 | -0.153 | 0.063 |
| SLOTHOUR | SCORE_UPDATE | top_inst_admit_share | -0.007 | -0.016 | 0.000 |
| SCORE_RANK | DEDUP_LATEST | net_per_avail_slot_hour | 0.005 | -0.107 | 0.116 |
| SCORE_RANK | DEDUP_LATEST | top_inst_admit_share | -0.010 | -0.015 | -0.005 |
| SCORE_RANK | COOLDOWN | net_per_avail_slot_hour | -0.221 | -0.288 | -0.155 |
| SCORE_RANK | COOLDOWN | top_inst_admit_share | -0.034 | -0.044 | -0.025 |
| SCORE_RANK | SCORE_UPDATE | net_per_avail_slot_hour | 0.005 | -0.099 | 0.116 |
| SCORE_RANK | SCORE_UPDATE | top_inst_admit_share | -0.010 | -0.015 | -0.005 |
| UNCERTAINTY_LCB | DEDUP_LATEST | net_per_avail_slot_hour | 0.036 | -0.058 | 0.116 |
| UNCERTAINTY_LCB | DEDUP_LATEST | top_inst_admit_share | 0.002 | -0.005 | 0.010 |
| UNCERTAINTY_LCB | COOLDOWN | net_per_avail_slot_hour | -0.054 | -0.191 | 0.069 |
| UNCERTAINTY_LCB | COOLDOWN | top_inst_admit_share | -0.031 | -0.048 | -0.015 |
| UNCERTAINTY_LCB | SCORE_UPDATE | net_per_avail_slot_hour | 0.036 | -0.061 | 0.116 |
| UNCERTAINTY_LCB | SCORE_UPDATE | top_inst_admit_share | 0.002 | -0.005 | 0.010 |
| FIFO_SCREEN | DEDUP_LATEST | net_per_avail_slot_hour | 0.012 | -0.110 | 0.137 |
| FIFO_SCREEN | DEDUP_LATEST | top_inst_admit_share | -0.021 | -0.032 | -0.011 |
| FIFO_SCREEN | COOLDOWN | net_per_avail_slot_hour | -0.271 | -0.409 | -0.125 |
| FIFO_SCREEN | COOLDOWN | top_inst_admit_share | -0.030 | -0.040 | -0.019 |
| FIFO_SCREEN | SCORE_UPDATE | net_per_avail_slot_hour | -0.012 | -0.138 | 0.116 |
| FIFO_SCREEN | SCORE_UPDATE | top_inst_admit_share | -0.002 | -0.011 | 0.007 |

Findings (OBSERVED unless noted):
- Spam **does distort who receives slots**: a single spam instrument takes ≈0.30–0.35 of all admissions under RAW vs ≈0.14–0.16 elsewhere (score-driven policies re-admit the spam instrument every time its slot frees; RR/EQUAL_QUOTA cap it at ≈0.23–0.29).
- Semantics reduce concentration only modestly (−0.01 to −0.03 with CIs excluding 0 for most); **M1 effects are within noise** for DEDUP_LATEST and SCORE_UPDATE (safe choices; SCORE_UPDATE was the tuned mode for all ranking policies), while **COOLDOWN hurts ranking policies (−0.22…−0.27)** because it discards fresh scores — a "cooldown" is not a free spam filter.
- Because the spam instruments' edge is mediocre but not poor, the *economic* damage of spam is small here; a scenario where spam instruments have clearly negative edge would show more (UNKNOWN, not run).
- CANDIDATE_SPAM_HANDLED=TRUE means: spam is explicitly modelled, four semantics compared, distortion measured, and a harmless default (SCORE_UPDATE or DEDUP_LATEST) identified. It does **not** mean spam is neutralised.
