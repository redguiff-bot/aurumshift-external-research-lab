# 03 — Static calibration (Q1, first half of Q3)

Tables: `bench/uncertainty_v1/results/tables/static_*.md`; figure `results/figures/reliability_gbm.png`. 12 held-out seeds; calibrators fit once on the calibration split.

## In-distribution (scenario `none`; OBSERVED)
| base | method | Brier | log loss | ECE | FCR@0.6 | CWM |
|---|---|---|---|---|---|---|
| lr | raw | 0.528 | 0.892 | 0.022 | 0.248 | 0.101 |
| lr | temperature | 0.528 | 0.893 | 0.022 | 0.248 | 0.101 |
| lr | platt / beta / isotonic / BBQ-lite | 0.528–0.529 | 0.893–0.894 | 0.021–0.024 | 0.245–0.256 | 0.099–0.111 |
| gbm | raw | 0.684 | 1.339 | 0.249 | 0.432 | 0.336 |
| gbm | **temperature** | **0.575** | **0.964** | **0.027** | 0.272 | 0.073 |
| gbm | beta | 0.595 | 1.052 | 0.029 | 0.281 | 0.076 |
| gbm | isotonic | 0.596 | 1.053 | 0.030 | 0.280 | 0.074 |
| gbm | BBQ-lite | 0.596 | 1.053 | 0.028 | 0.272 | 0.067 |
| gbm | platt | 0.634 | 1.279 | 0.119 | 0.342 | 0.153 |

Paired differences vs raw (mean ± 95 % t-CI over 12 seeds): GBM temperature ΔBrier −0.109 ± 0.003, ΔECE −0.222 ± 0.003, ΔCWM −0.263 ± 0.008; LR: every calibrator within ±0.001–0.004 of zero for ECE (isotonic/BBQ-lite slightly *worse* Brier, +0.001 ± 0.001).

Reading: **Q1 = yes when the model is miscalibrated in a way a monotone map can fix, and no gain otherwise.** Temperature scaling dominates because the GBM error is a global over-sharpening; top-label maps only fix the max-probability, so their log loss stays worse (1.05 vs 0.96) — they leave the non-top mass mis-shaped. Platt fails on GBM because confidences saturate near 1 (logit ≈ ±14), so a two-parameter sigmoid cannot represent the reliability curve (INFERENCE from the fitted behaviour; not separately diagnosed). Selection on the four tuning seeds gave the same ranking (`static_tuning_ranking.md`) — temperature was chosen there, not on the held-out seeds.

## Stability over time in a stationary world
Scenario `none`: ECE drift (post−pre) is −0.003 (GBM) / −0.005 (LR): static calibration is stable while the world is stationary, even with autocorrelated features and clustered volatility.

## Under shift (first half of Q3; OBSERVED)
Static ECE drift, post−pre, temperature-scaled (`static_ece_drift.md`):
| scenario | gbm | lr |
|---|---|---|
| feature_shift | +0.126 | +0.179 |
| regime_transition | +0.150 | +0.188 |
| stale_features | +0.108 | +0.124 |
| venue_change | +0.066 | +0.089 |
| vol_jump | +0.053 | +0.051 |
| missing_features | +0.040 | +0.001 |
| rare_cluster | +0.005 | +0.011 |
Confident-wrong mass post-onset (GBM, temperature): 0.174 feature shift, 0.169 regime transition, 0.138 stale, 0.127 venue, 0.107 vol jump vs 0.073 in-distribution. Raw GBM reaches ECE 0.42 (regime). Choice of calibrator does not matter under shift — all static maps drift by the same amount, because the failure is a change in P(y|x) or in the input distribution, not in the shape of the score→accuracy map. The LR `missing_features` case barely drifts because mean imputation pushes probabilities toward the prior, i.e. the model is *accidentally* under-confident where information is missing.

## Public data (OBSERVED)
* iid re-splits (20 reps): credit-g GBM raw ECE 0.21 (Brier 0.457) → temperature 0.054 (Brier 0.358); credit-g LR 0.092 → 0.060; breast-cancer LR raw is already best (ECE 0.028 raw vs 0.033 temperature; log loss 0.097 vs 0.135); breast-cancer GBM ECE 0.042 → 0.037. Small test sets (≈114–200 rows) — noisy; re-splits overlap so the spread understates uncertainty.
* ELEC2 (real drift): static temperature is *worse* than raw for LR (Brier 0.456 → 0.478, log loss 0.744 → 0.879, ECE 0.157 → 0.189) and only helps GBM (Brier 0.530 → 0.471). A calibrator fitted before a drift can make things worse than doing nothing (see `04_ONLINE_CALIBRATION.md`).
