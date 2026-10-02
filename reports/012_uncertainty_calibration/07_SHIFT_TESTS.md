# 07 — Distribution-shift tests, detection and cause attribution (Q3 second half, Q4; §5)

12 held-out seeds (`py/shift.py`; `results/tables/detect_*.md`, `diag_*.md`). Detector windows: 200 rows evaluated every 100 rows on the held-out stream; alarm threshold = maximum statistic observed on the in-distribution validation stream (no p-values: features are autocorrelated). "Delay" is measured from onset to the *end* of the first alarming window, so ≈100 is the minimum.

## Scenario effects on calibrated confidence (static vs online) — see `03`/`04`
All six requested shifts were run: volatility jump, regime transition, feature shift, missing features, stale features, venue change (+ rare cluster). Static ECE drift ranges +0.04…+0.15 (GBM); calibration does not survive without recalibration. **A model that stays confident while wrong is penalised explicitly** through CWM/FCR: raw GBM CWM is 0.34–0.50 across scenarios, temperature-scaled static 0.07–0.17, online-recalibrated 0.01–0.03 in the six shift scenarios (GBM; 0.06–0.07 in the shift-free worlds, where the model is simply noisy).

## Detection (OBSERVED)
Detection rate over 12 seeds / median delay in steps:
| scenario | domain-clf AUC | KS max | Mahalanobis | missing-rate | repeat-rate | loss window (matured labels) |
|---|---|---|---|---|---|---|
| feature_shift | 1.00 / 200 | 1.00 / 100 | 1.00 / 100 | 0 | 0 | 1.00 / 100 |
| venue_change | 1.00 / 200 | 1.00 / 200 | 1.00 / 100 | 0 | 0 | 1.00 / 150 |
| missing_features | 1.00 / 200 | 0.75 / 1500 | 0.00 | **1.00 / 100** | 0 | 1.00 / 250 |
| stale_features | 0.83 / 1500 | 1.00 / 300 | 0.83 / 1250 | 0 | **1.00 / 100** | 1.00 / 100 |
| rare_cluster | 0.42 / 1000 | 0.58 / 1400 | 0.92 / 700 | 0 | 0 | 1.00 / 300 |
| vol_jump | 0.42 / 1300 | 0.58 / 1400 | 0.67 / 1600 | 0 | 0 | **1.00 / 150** |
| regime_transition | 0.42 / 1300 | 0.58 / 1400 | 0.67 / 1600 | 0 | 0 | **1.00 / 500** |
| none (false alarms) | 0.42 | 0.58 | 0.67 | 0 | 0 | 0.58 |
For the `none` world the "detection rate" is the share of seeds with *any* alarm in the 3000 post-"onset" steps = a per-seed false-alarm probability; the corresponding block-level false-alarm rates before onset are domain-clf 2.4 %, loss window 4.8 %, KS 5.4 %, Mahalanobis 7.7 %. Consequently **entries of 0.42–0.67 for vol_jump / regime_transition / rare_cluster-by-input-detectors are indistinguishable from false alarms**. INFERENCE: with autocorrelated inputs, "max-on-validation" thresholds yield a non-trivial false-alarm rate; a production alarm needs a persistence rule.

Findings:
1. **Covariate/venue shift** is caught quickly by any input-space detector.
2. **Missing and stale data** are caught instantly and *exactly* by the trivial NaN-rate and repeated-value monitors; the statistical detectors are slow or blind (Mahalanobis after mean-imputation sees nothing: 0 % detection).
3. **Volatility jumps and regime transitions are invisible to input detectors** (features are unchanged/in-distribution). Only monitoring realised loss on matured labels detects them (100 % of seeds; 150 / 500 steps) — a label-delayed, coarse signal.

## Q4 — attributing uncertainty to a cause (OBSERVED; rules frozen from tuning seeds)
Cascade (first match wins): DATA_GAP (row has NaN or a repeated feature value) → OUT_OF_DISTRIBUTION (Mahalanobis > 99th percentile of the calibration set) → MODEL_UNCERTAINTY (bootstrap-ensemble MI > 95th percentile) → NO_SIGNAL (temperature/beta-calibrated max-probability < 0.5) → NORMAL. Thresholds maximised macro-F1 on tuning seeds (0.516 there). Held-out pool: 5 causal scenarios' post-onset rows + pre-onset baseline rows, 12 seeds, ≈ 198k rows.

| true cause | precision | recall | F1 |
|---|---|---|---|
| NORMAL | 0.545 | 0.902 | 0.679 |
| NO_SIGNAL | 0.602 | 0.873 | 0.713 |
| DATA_GAP | 1.000 | 1.000 | 1.000 (**by construction** — truth = injected fault = flag) |
| MODEL_UNCERTAINTY | 0.047 | 0.168 | **0.073** |
| OUT_OF_DISTRIBUTION | 0.966 | 0.389 | 0.555 |
| macro | 0.632 | 0.666 | **0.604** (seed CI ± 0.003) |
Ablations (F1): without the gap flags DATA_GAP → 0 and macro-F1 0.325; without the OOD rule OOD → 0 (macro 0.479); without the MI rule MODEL_UNCERTAINTY → 0 (macro 0.585); confidence alone (NO_SIGNAL-vs-rest) macro 0.181. In-distribution rows are wrongly given a fault label 5.9 % of the time.

**Answer to Q4:** NO_SIGNAL vs the rest is separable from *calibrated confidence* (with the caveat that NO_SIGNAL truth here is defined by the oracle posterior). DATA_GAP needs explicit data-quality metadata (NaN/staleness flags), not model uncertainty. OOD is separable when the shift is large in input space (recall is limited because many shifted rows still lie inside the training support) . **MODEL_UNCERTAINTY (rare cluster, sparse training support) was not separable from ensemble disagreement, at this ensemble size and base learner.** The volatility-jump / regime-transition cases (mean confidence 0.575 while error rate is 0.49 / 0.64) were flagged as DATA_GAP/MODEL/OOD only 5.9 % of the time — the false-flag base rate; 38.5 % were labelled NO_SIGNAL, i.e. seen only through lowered confidence, which is what recalibrated (online) confidence does after the fact. Error rate by predicted label (all pooled rows): NORMAL 0.44 (mean conf 0.70), NO_SIGNAL 0.61 (0.41), DATA_GAP 0.56 (0.54), MODEL_UNCERTAINTY 0.56 (0.55), OOD 0.48 (0.73) — note **OOD-flagged rows keep mean confidence 0.73 while being wrong 48 %**: the classic false-confidence failure that only an explicit OOD gate can address.
