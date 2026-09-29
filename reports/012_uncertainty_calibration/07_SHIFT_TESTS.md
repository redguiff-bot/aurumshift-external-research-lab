# 07 — Distribution-shift tests (Q3, Q4)

Held-out synthetic block [10000:16000], **the same rows** with and without transformation (paired). Models: HGB (over-confident) and LR, calibrators fit on the *un-shifted* calibration block. 20 seeds. Shifts:
* `vol_jump`: features ×1.5 (model sees larger inputs) and true signal-to-noise ×0.35.
* `regime_transition`: signs of two coefficients flipped (P(y|x) changes; features look identical).
* `feature_shift`: +1.5 on four features, relationship unchanged.
* `missing_features`: each feature NaN w.p. 0.3 (mean-imputed); truth from complete features.
* `stale_features`: 40% of time the four leading features are frozen at their last value (10–40-step stalls).
* `venue_change`: inputs come from another "venue": 0.7×x + 0.5 + N(0,0.5²) measurement noise; truth from the true x.

## ECE by shift (HGB base)
| shift | bayes_bin | isotonic | platt | raw |
|---|---|---|---|---|
| iid | 0.026±0.002 | 0.022±0.002 | 0.021±0.002 | 0.116±0.003 |
| vol_jump | 0.144±0.005 | 0.142±0.005 | 0.141±0.004 | 0.251±0.004 |
| regime_transition | 0.177±0.042 | 0.170±0.042 | 0.172±0.042 | 0.283±0.043 |
| feature_shift | 0.054±0.009 | 0.052±0.011 | 0.036±0.008 | 0.113±0.018 |
| missing_features | 0.040±0.003 | 0.033±0.003 | 0.030±0.004 | 0.133±0.005 |
| stale_features | 0.080±0.005 | 0.076±0.005 | 0.076±0.004 | 0.186±0.004 |
| venue_change | 0.076±0.013 | 0.071±0.014 | 0.068±0.012 | 0.177±0.012 |
## False-confidence rate P(wrong ∧ conf ≥ 0.8), HGB base
| shift | bayes_bin | isotonic | platt | raw |
|---|---|---|---|---|
| iid | 0.030±0.004 | 0.027±0.003 | 0.024±0.002 | 0.115±0.002 |
| vol_jump | 0.116±0.009 | 0.112±0.007 | 0.107±0.005 | 0.239±0.004 |
| regime_transition | 0.107±0.022 | 0.103±0.021 | 0.096±0.020 | 0.254±0.035 |
| feature_shift | 0.045±0.013 | 0.042±0.012 | 0.037±0.011 | 0.123±0.017 |
| missing_features | 0.029±0.004 | 0.027±0.003 | 0.023±0.002 | 0.118±0.005 |
| stale_features | 0.062±0.007 | 0.058±0.005 | 0.054±0.004 | 0.172±0.005 |
| venue_change | 0.048±0.009 | 0.046±0.009 | 0.040±0.008 | 0.157±0.010 |
## Brier, HGB base
| shift | bayes_bin | isotonic | platt | raw |
|---|---|---|---|---|
| iid | 0.201±0.001 | 0.201±0.001 | 0.200±0.001 | 0.216±0.002 |
| vol_jump | 0.266±0.002 | 0.266±0.002 | 0.264±0.002 | 0.312±0.003 |
| regime_transition | 0.294±0.024 | 0.292±0.024 | 0.291±0.024 | 0.349±0.034 |
| feature_shift | 0.175±0.021 | 0.174±0.021 | 0.174±0.021 | 0.190±0.025 |
| missing_features | 0.222±0.001 | 0.221±0.001 | 0.220±0.001 | 0.241±0.002 |
| stale_features | 0.240±0.002 | 0.239±0.002 | 0.238±0.002 | 0.272±0.003 |
| venue_change | 0.239±0.005 | 0.238±0.005 | 0.237±0.004 | 0.269±0.007 |
## LR base (ECE / FCR: raw vs Platt)
| ('shift', '') | ('ece', 'platt') | ('ece', 'raw') | ('false_conf_rate', 'platt') | ('false_conf_rate', 'raw') |
|---|---|---|---|---|
| iid | 0.026 | 0.025 | 0.03 | 0.031 |
| vol_jump | 0.158 | 0.16 | 0.135 | 0.138 |
| regime_transition | 0.187 | 0.189 | 0.098 | 0.102 |
| feature_shift | 0.086 | 0.081 | 0.08 | 0.08 |
| missing_features | 0.02 | 0.021 | 0.021 | 0.022 |
| stale_features | 0.069 | 0.072 | 0.054 | 0.057 |
| venue_change | 0.054 | 0.054 | 0.041 | 0.041 |

## Q3 — does calibration survive? (pre-declared: ECE_shift ≤ 0.05 AND FCR ≤ 1.5× iid FCR + 0.01; HGB+Platt)
| shift | ece_shift | ece_iid | fcr_shift | fcr_iid | seeds_surviving | survives |
|---|---|---|---|---|---|---|
| vol_jump | 0.141±0.004 | 0.021±0.002 | 0.107±0.005 | 0.024±0.002 | 0/20 | NO |
| regime_transition | 0.172±0.042 | 0.021±0.002 | 0.096±0.020 | 0.024±0.002 | 1/20 | NO |
| feature_shift | 0.036±0.008 | 0.021±0.002 | 0.037±0.011 | 0.024±0.002 | 17/20 | YES |
| missing_features | 0.030±0.004 | 0.021±0.002 | 0.023±0.002 | 0.024±0.002 | 19/20 | YES |
| stale_features | 0.076±0.004 | 0.021±0.002 | 0.054±0.004 | 0.024±0.002 | 0/20 | NO |
| venue_change | 0.068±0.012 | 0.021±0.002 | 0.040±0.008 | 0.024±0.002 | 7/20 | NO |

**Answer:** calibration survives **2 of 6** shifts (feature shift, missing features). It fails for vol-jump, regime transition, stale features and venue change. Regime transition (ECE 0.172) and vol-jump (0.141) are the severe cases and are exactly the ones a *label-free* detector cannot see (below). Calibrating still helps the over-confident HGB relative to raw (every shift: ECE and FCR lower than raw; for LR, raw ≈ Platt since LR is already calibrated), but a calibrator fitted before the shift is **not** a safe assumption after it. Isotonic and Bayes-binning behave like Platt (no robustness benefit).

## Shift detection
Row-level AUROC (shifted vs iid rows) of label-free signals; `auc_flag` = missing/stale flags:
| shift | auc_maha | auc_ens | auc_lowconf | auc_flag |
|---|---|---|---|---|
| feature_shift | 0.877 | 0.629 | 0.391 | 0.5 |
| missing_features | 0.313 | 0.47 | 0.558 | 0.971 |
| regime_transition | 0.5 | 0.5 | 0.5 | 0.5 |
| stale_features | 0.5 | 0.506 | 0.502 | 0.704 |
| venue_change | 0.495 | 0.535 | 0.534 | 0.5 |
| vol_jump | 0.864 | 0.615 | 0.425 | 0.5 |
* Mahalanobis catches feature/volatility shifts (0.86–0.88) but is **at chance** (≈0.50) for regime transition and venue change and *below* chance for missing features (imputation to the training mean *reduces* distance).
* Ensemble std is weak (0.47–0.63). Low confidence is *anti*-informative for feature_shift and vol_jump (AUROC 0.39, 0.43): the model becomes **more** confident when shifted — the definition of false confidence.
* Flags (missing/stale) work when the fault is explicit (0.97 / 0.70; the stale flag is weaker — INFERENCE: only frozen rows after the first of each stall repeat exactly, and stalls cover ≈40% of time).

Label-based calibration monitor (rolling binomial z<−3 on acted rows, labels delayed 10 steps; alarm rate = share of seeds alarmed within the 6000-step block):
| shift | alarm_rate | median_delay_steps |
|---|---|---|
| iid | 0.15 | 5232.0 |
| vol_jump | 1.0 | 411.0 |
| regime_transition | 1.0 | 454.5 |
| feature_shift | 0.5 | 1203.5 |
| missing_features | 0.9 | 1592.0 |
| stale_features | 1.0 | 505.0 |
| venue_change | 1.0 | 488.5 |
* Detects regime transition, stale, venue, vol-jump in **every seed**, median delay 411–505 steps after onset. It is the **only** signal that detects the regime transition. Costs: false-alarm rate **15% per 6000 steps on iid data** at z=−3 with continuous monitoring (no multiple-testing correction) and detection delay of hundreds of steps.

## Q4 — can uncertainty signals distinguish NO_SIGNAL / DATA_GAP / MODEL_UNCERTAINTY / OOD?
Controlled test: pools of 1200 rows per seed (20 seeds) built by the generator: NO_SIGNAL (x7>1, true P=0.5), DATA_GAP (half 30%-missing, half stalled feed), MODEL_UNCERTAINTY (in-support region x0>1,x1>1 thinned to 8% in *training only*, true signal is strongest there), OOD (features ×1.5 and +3σ), SIGNAL (rest). Rule cascade with thresholds from calibration data only: DATA_GAP (missing/exact-repeat flag) → OOD (Mahalanobis > cal p99) → MODEL_UNCERTAINTY (ensemble std > cal p90) → NO_SIGNAL (|p−0.5| < 0.08) → SIGNAL. Row-normalised confusion (truth rows, prediction columns):
| truth | SIGNAL | NO_SIGNAL | DATA_GAP | MODEL_UNCERTAINTY | OOD |
|---|---|---|---|---|---|
| SIGNAL | 0.734 | 0.185 | 0.0 | 0.07 | 0.011 |
| NO_SIGNAL | 0.396 | 0.36 | 0.0 | 0.222 | 0.021 |
| DATA_GAP | 0.023 | 0.006 | 0.968 | 0.003 | 0.0 |
| MODEL_UNCERTAINTY | 0.72 | 0.098 | 0.0 | 0.149 | 0.033 |
| OOD | 0.014 | 0.001 | 0.0 | 0.006 | 0.979 |
Recall: SIGNAL=0.73, NO_SIGNAL=0.36, DATA_GAP=0.97, MODEL_UNCERTAINTY=0.15, OOD=0.98

* **DATA_GAP (0.97) and OOD (0.98) are separable** — with explicit data-fault flags and a feature-distance detector, respectively.
* **NO_SIGNAL is recognised only 36% of the time** (40% mistaken for SIGNAL, 22% for MODEL_UNCERTAINTY). Weak signal and no signal look alike: a probability near 0.5 could be either. 
* **MODEL_UNCERTAINTY is recognised 15%**; 72% are labelled SIGNAL. The bootstrap ensemble does not disagree enough in the thinned region (the trees still extrapolate confidently).
* Pre-declared criterion (recall ≥0.7 for all four): **not met** — 2 of 4 causes distinguishable.
* Circularity caveat: the causes are defined by the generator, and the OOD/DATA_GAP pools are exactly what the corresponding detector was designed for; the result is an upper bound for real markets, where the causes co-occur.
