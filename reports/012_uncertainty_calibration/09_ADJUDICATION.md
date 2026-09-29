# 09 — Adjudication against the pre-declared criteria (protocol §02)

| Criterion | Result | Verdict |
|---|---|---|
| Calibrated: ECE ≤ 0.03 held-out, better than raw or raw already ≤0.03 (synthetic, n=6000) | HGB raw 0.118 → Platt/temperature/beta 0.022; LR/GNB raw already 0.022–0.027, calibrated ≈0.023 | **MET** (stationary) |
| Same on real drifting data (ELEC2) | best calibrated ECE 0.068 (HGB+temperature), LR calibration worse than raw (0.15–0.17 vs 0.10) | **NOT MET** |
| Calibration survives shift (ECE ≤0.05 and FCR ≤1.5× iid+0.01) | 2 of 6 shifts (feature shift, missing features) | **NOT MET** in general |
| Abstention helps (risk < random; utility ≥ trade-all; ≥50% good retained) | iid: risk 0.256 < 0.318, utility 0.198 > 0.163, 75% good retained; covariate-type shifts similar; regime transition risk 0.482 ≈ 0.486 (no gain) | **MET except under concept shift** |
| Online supported (≥0.02 worst-chunk ECE gain with CI, turnover ≤1.2× raw, not reliant on leaks) | window Platt, window isotonic, SGD: 3/3 drift scenarios; turnover 0.75–0.98× raw; leak variants not needed (PIT audit passes) | **MET** (sliding/SGD); expanding not met |
| Conformal supported (|cov−(1−α)| ≤0.03, ≤10% windows low) | split: fails under all drift; ACI/weighted: all 9 settings; rolling: 8/9 (ELEC2 α=0.2 fails) | **MET for marginal coverage with ACI/weighted; split NOT valid under drift** |
| Q4 recall ≥0.7 for all four causes | DATA_GAP 0.97, OOD 0.98, NO_SIGNAL 0.36, MODEL_UNCERTAINTY 0.15 | **NOT MET** (2 of 4) |

## Answers to the four questions
* **Q1** Confidence scores can be made empirically calibrated (ECE ≈0.02) under stationarity with a few-thousand-point calibration block using a 1–2-parameter calibrator. On real drifting data the static calibration does not persist.
* **Q2** Abstention reduces bad decisions without collapsing opportunity count in distribution and under covariate-like shifts (−45% bad decisions, +75% of good ones kept at τ=0.6). Under concept shift it does not (utility stays negative).
* **Q3** Calibration does **not** in general survive regime change: 2/6 shift types pass. Sliding-window online recalibration restores it with a lag.
* **Q4** Only partly: data faults and out-of-distribution inputs are separable with simple flags/distance; no-signal versus model-uncertainty is not, with the signals tested.

## Reference candidates (external, no AurumShift integration claim)
* **BEST_SIMPLE_REFERENCE:** Platt scaling (temperature statistically equivalent) fit on a held-aside calibration block; abstain when calibrated confidence < τ with τ=(1+c)/2 from the cost model; explicit missing/stale flags force HOLD. Doctrine class: **ADOPT-as-reference / ADAPT** (needs its own PIT-safe calibration block).
* **BEST_ONLINE_REFERENCE:** sliding-window Platt (W≈1000, refit every ≈250 steps), fed only by labels resolved by *t* (assert `j+h ≤ t`), plus delayed-feedback ACI for set-valued outputs, plus the label-based calibration monitor as a circuit breaker. Class: **ADAPT** (tune W/refit; smooth the slope — instability on ELEC2-LR).
* **REJECT/PARK:** split conformal on non-stationary streams (invalid); expanding-window recalibration (diluted); isotonic/Bayes-binning at n≲3000 (no gain); ensemble/OOD vetoes as generic selective-risk improvers (no gain over confidence at matched coverage); textbook iid coverage claims.

## Verdict
Uncertainty methods are **supported with clear limits** — calibration + cost-based abstention in stationary or covariate-shifted conditions, sliding-window recalibration and ACI under drift — but no method is robust to concept/regime shift without lag, calibration mostly does not survive shift, and cause taxonomy is only half separable.

**FINAL_VERDICT = LIMITED_UNCERTAINTY_METHODS_SUPPORTED**
