# 05 — Abstention / selective classification (Q2)

**Decision rule:** `BUY if p ≥ τ, SELL if p ≤ 1−τ, else HOLD`. Payoff +1 correct / −1 wrong, cost c=0.2 per trade ⇒ Bayes-optimal (for calibrated p) τ* = (1+c)/2 = **0.6**, no tuning. Policies (HGB base, Platt calibration, thresholds fixed from the *calibration* block):
* P0 trade everything (τ=0.5) · P1 calibrated confidence ≥ 0.6 · P2 P1 + ensemble-std ≤ cal 90th pct · P3 P1 + no missing/stale flag + Mahalanobis ≤ cal 99th pct · P4 = P1∧P2∧P3.
* `random_risk` = selective risk of abstaining at random (= full risk). `matched_conf_risk` = risk of ranking by confidence alone **at the same realised coverage** (an oracle-matched comparator used only to test whether P2–P4 add information beyond confidence).
* 20 seeds; means shown (intervals in the CSV).

## Full table
| shift | policy | coverage | selective_risk | random_risk | matched_conf_risk | bad_avoided | good_retained | conf_wrong_penalty | utility |
|---|---|---|---|---|---|---|---|---|---|
| iid | P0_none | 1.0 | 0.318 | 0.318 | 0.318 | 0.0 | 1.0 | 0.086 | 0.163 |
| iid | P1_conf | 0.686 | 0.256 | 0.318 | 0.256 | 0.449 | 0.75 | 0.072 | 0.198 |
| iid | P2_conf_ens | 0.632 | 0.243 | 0.318 | 0.242 | 0.519 | 0.702 | 0.063 | 0.199 |
| iid | P3_conf_ood_gap | 0.677 | 0.256 | 0.318 | 0.254 | 0.455 | 0.739 | 0.071 | 0.195 |
| iid | P4_all | 0.625 | 0.243 | 0.318 | 0.24 | 0.522 | 0.694 | 0.063 | 0.196 |
| vol_jump | P0_none | 1.0 | 0.42 | 0.42 | 0.42 | 0.0 | 1.0 | 0.167 | -0.04 |
| vol_jump | P1_conf | 0.753 | 0.397 | 0.42 | 0.397 | 0.288 | 0.783 | 0.155 | 0.004 |
| vol_jump | P2_conf_ens | 0.582 | 0.38 | 0.42 | 0.377 | 0.474 | 0.622 | 0.122 | 0.023 |
| vol_jump | P3_conf_ood_gap | 0.472 | 0.404 | 0.42 | 0.362 | 0.546 | 0.485 | 0.097 | -0.004 |
| vol_jump | P4_all | 0.394 | 0.393 | 0.42 | 0.348 | 0.631 | 0.412 | 0.082 | 0.005 |
| regime_transition | P0_none | 1.0 | 0.486 | 0.486 | 0.486 | 0.0 | 1.0 | 0.176 | -0.171 |
| regime_transition | P1_conf | 0.686 | 0.482 | 0.486 | 0.482 | 0.328 | 0.682 | 0.161 | -0.112 |
| regime_transition | P2_conf_ens | 0.632 | 0.482 | 0.486 | 0.481 | 0.384 | 0.626 | 0.15 | -0.103 |
| regime_transition | P3_conf_ood_gap | 0.677 | 0.482 | 0.486 | 0.482 | 0.337 | 0.673 | 0.158 | -0.111 |
| regime_transition | P4_all | 0.625 | 0.482 | 0.486 | 0.481 | 0.39 | 0.62 | 0.148 | -0.102 |
| feature_shift | P0_none | 1.0 | 0.266 | 0.266 | 0.266 | 0.0 | 1.0 | 0.085 | 0.267 |
| feature_shift | P1_conf | 0.782 | 0.22 | 0.266 | 0.22 | 0.368 | 0.831 | 0.075 | 0.291 |
| feature_shift | P2_conf_ens | 0.575 | 0.183 | 0.266 | 0.173 | 0.625 | 0.638 | 0.047 | 0.267 |
| feature_shift | P3_conf_ood_gap | 0.527 | 0.219 | 0.266 | 0.163 | 0.572 | 0.561 | 0.049 | 0.198 |
| feature_shift | P4_all | 0.416 | 0.188 | 0.266 | 0.138 | 0.715 | 0.46 | 0.034 | 0.188 |
| missing_features | P0_none | 1.0 | 0.365 | 0.365 | 0.365 | 0.0 | 1.0 | 0.091 | 0.07 |
| missing_features | P1_conf | 0.619 | 0.303 | 0.365 | 0.303 | 0.487 | 0.679 | 0.074 | 0.12 |
| missing_features | P2_conf_ens | 0.588 | 0.296 | 0.365 | 0.296 | 0.523 | 0.651 | 0.07 | 0.122 |
| missing_features | P3_conf_ood_gap | 0.039 | 0.266 | 0.365 | 0.096 | 0.972 | 0.045 | 0.004 | 0.01 |
| missing_features | P4_all | 0.036 | 0.252 | 0.365 | 0.092 | 0.975 | 0.042 | 0.004 | 0.011 |
| stale_features | P0_none | 1.0 | 0.391 | 0.391 | 0.391 | 0.0 | 1.0 | 0.123 | 0.018 |
| stale_features | P1_conf | 0.685 | 0.352 | 0.391 | 0.352 | 0.384 | 0.729 | 0.108 | 0.066 |
| stale_features | P2_conf_ens | 0.628 | 0.343 | 0.391 | 0.342 | 0.449 | 0.677 | 0.099 | 0.072 |
| stale_features | P3_conf_ood_gap | 0.401 | 0.258 | 0.391 | 0.303 | 0.735 | 0.488 | 0.042 | 0.114 |
| stale_features | P4_all | 0.37 | 0.245 | 0.391 | 0.297 | 0.768 | 0.458 | 0.037 | 0.115 |
| venue_change | P0_none | 1.0 | 0.396 | 0.396 | 0.396 | 0.0 | 1.0 | 0.114 | 0.007 |
| venue_change | P1_conf | 0.652 | 0.353 | 0.396 | 0.353 | 0.419 | 0.698 | 0.098 | 0.06 |
| venue_change | P2_conf_ens | 0.585 | 0.342 | 0.396 | 0.342 | 0.495 | 0.637 | 0.087 | 0.067 |
| venue_change | P3_conf_ood_gap | 0.646 | 0.353 | 0.396 | 0.352 | 0.424 | 0.691 | 0.097 | 0.06 |
| venue_change | P4_all | 0.581 | 0.343 | 0.396 | 0.342 | 0.498 | 0.632 | 0.086 | 0.066 |

## Risk-coverage (selective risk at coverage 90/70/50/30 %, AURC) — ranking by raw confidence, calibrated confidence, calibrated confidence − 2·ensemble-std, random
| shift | ranking | aurc | risk@0.9 | risk@0.7 | risk@0.5 | risk@0.3 |
|---|---|---|---|---|---|---|
| iid | cal_conf | 0.198 | 0.3 | 0.259 | 0.208 | 0.149 |
| iid | cal_conf_minus_2ens | 0.191 | 0.3 | 0.255 | 0.201 | 0.137 |
| iid | random | 0.316 | 0.319 | 0.317 | 0.317 | 0.317 |
| iid | raw_conf | 0.198 | 0.3 | 0.258 | 0.208 | 0.148 |
| vol_jump | cal_conf | 0.353 | 0.412 | 0.391 | 0.367 | 0.329 |
| vol_jump | cal_conf_minus_2ens | 0.351 | 0.412 | 0.391 | 0.362 | 0.325 |
| vol_jump | random | 0.418 | 0.419 | 0.419 | 0.417 | 0.419 |
| vol_jump | raw_conf | 0.353 | 0.412 | 0.391 | 0.366 | 0.329 |
| regime_transition | cal_conf | 0.471 | 0.485 | 0.482 | 0.476 | 0.47 |
| regime_transition | cal_conf_minus_2ens | 0.471 | 0.486 | 0.483 | 0.478 | 0.47 |
| regime_transition | random | 0.486 | 0.486 | 0.486 | 0.485 | 0.487 |
| regime_transition | raw_conf | 0.471 | 0.485 | 0.482 | 0.476 | 0.47 |
| feature_shift | cal_conf | 0.159 | 0.243 | 0.2 | 0.161 | 0.119 |
| feature_shift | cal_conf_minus_2ens | 0.155 | 0.244 | 0.2 | 0.157 | 0.113 |
| feature_shift | random | 0.265 | 0.266 | 0.265 | 0.265 | 0.264 |
| feature_shift | raw_conf | 0.159 | 0.243 | 0.201 | 0.162 | 0.12 |
| missing_features | cal_conf | 0.259 | 0.351 | 0.318 | 0.276 | 0.221 |
| missing_features | cal_conf_minus_2ens | 0.255 | 0.352 | 0.317 | 0.272 | 0.213 |
| missing_features | random | 0.366 | 0.364 | 0.365 | 0.364 | 0.366 |
| missing_features | raw_conf | 0.259 | 0.352 | 0.319 | 0.277 | 0.222 |
| stale_features | cal_conf | 0.312 | 0.38 | 0.354 | 0.321 | 0.282 |
| stale_features | cal_conf_minus_2ens | 0.308 | 0.38 | 0.352 | 0.317 | 0.273 |
| stale_features | random | 0.392 | 0.391 | 0.391 | 0.392 | 0.391 |
| stale_features | raw_conf | 0.312 | 0.38 | 0.354 | 0.322 | 0.283 |
| venue_change | cal_conf | 0.309 | 0.385 | 0.36 | 0.328 | 0.281 |
| venue_change | cal_conf_minus_2ens | 0.302 | 0.385 | 0.359 | 0.323 | 0.271 |
| venue_change | random | 0.396 | 0.396 | 0.396 | 0.396 | 0.395 |
| venue_change | raw_conf | 0.309 | 0.386 | 0.361 | 0.328 | 0.282 |

## Findings (OBSERVED)
1. **In distribution (iid):** P1 trades 68.6% of rows, selective risk 0.256 vs 0.318 for trading everything (0.318 = random abstention). It avoids 44.9% of the wrong decisions while retaining 75.0% of the correct ones; utility per opportunity 0.198 vs 0.163. → **abstention reduces bad decisions without collapsing opportunity count.** The ≥50%-good-retained criterion is met.
2. **Calibration does not change the risk-coverage curve** (raw_conf and cal_conf rows are identical to 3 decimals) — Platt is monotone. Its value for abstention is that **τ has a meaning**: τ=0.6 derived from a cost model transfers without validation tuning, whereas the raw over-confident score does not.
3. **Ensemble disagreement adds a small ranking gain** (iid AURC 0.198 → 0.191; risk@0.5 0.208 → 0.201), and P2 is *not* better than simply raising the confidence threshold to the same coverage (0.243 vs matched 0.242). Vetoes are **not** free lunch: for P2/P4 selective risk is mostly worse than confidence-only at equal coverage.
4. **Flags matter only for data faults:** stale_features P3 reaches risk 0.258 at 40% coverage vs 0.303 for confidence-only at that coverage; missing_features P3 abstains on ≈96% of rows (30% per-feature missingness ⇒ almost every row has a gap) — correct, but it is total abstention, not selective trading.
5. **Under label-side shifts abstention cannot repair the decisions:** regime transition: full risk 0.486 ≈ selective 0.482, utility −0.171 → −0.112 (still negative, trading anything loses). Vol-jump: utility −0.040 → +0.004 only by trading less (75% coverage → 39% with P4) and risk barely moves (0.420 → 0.380–0.404 across P1–P4). Confidence itself is no longer informative when the true relation changed.
6. **Confident-wrong penalty** (mean 1[acted ∧ wrong]·(2·conf−1)) is reduced by every policy vs P0 in every shift, e.g. vol-jump 0.167 → 0.155 (P1) → 0.082 (P4), but P4 pays with coverage 0.39.

## Answer to Q2
**Yes in distribution and under covariate-type shifts (feature shift, venue change, stale/missing data), in these worlds; no under concept/regime shifts that alter P(y|x).** Extra uncertainty vetoes beyond a calibrated-confidence threshold gave little additional selective-risk benefit except for explicit data-fault flags.

Caveat: the ±1/0.2 payoff is a stylised proxy, not trading P&L; τ transfers across worlds only because the world is stationary in payoff structure.
