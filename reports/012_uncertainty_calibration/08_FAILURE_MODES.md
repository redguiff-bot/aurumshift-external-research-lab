# 08 — Failure modes (observed, and process failures during this study)

## Method failure modes (OBSERVED)
| # | Failure mode | Evidence | Mitigation tested |
|---|---|---|---|
| F1 | **Over-confident base model stays confident under shift** (false confidence) | HGB raw FCR 0.115 iid → 0.25 regime transition; even calibrated FCR 0.096–0.107 vs 0.024 iid (vol-jump, regime) | online recalibration (04): FCR 0.065→0.015 after recovery; abstention (05) only trims it |
| F2 | **Confidence *rises* under covariate/volatility shift** | low-confidence AUROC 0.39 (feature shift), 0.43 (vol jump) | none — do not use "low confidence" as the shift alarm |
| F3 | **Concept shift invisible to label-free detectors** | regime transition: Mahalanobis, ensemble, confidence all AUROC ≈ 0.50 | label-based monitor detects it (all seeds, median delay ≈450 steps, but 15% false alarms/6000 steps) |
| F4 | **Imputation hides missingness from distance detectors** | missing_features Mahalanobis AUROC 0.31 | explicit missing-mask flag (AUROC 0.97) |
| F5 | **Static calibrator decay on real drift** | ELEC2 LR: calibrated ECE 0.15–0.17 vs raw 0.10; per-chunk ECE swings 0.05–0.25 | sliding-window recalibration (04) |
| F6 | **Recalibration lag** | worst-chunk ECE stays 0.10 after abrupt break (window Platt) | shorter windows/SGD trade bias for variance (SGD slope sd 0.11–0.23) |
| F7 | **Recalibration parameter instability** | ELEC2-LR SGD/window slope sd 0.56–0.78 | untested: smoothing, priors, slope caps |
| F8 | **Non-parametric calibrators variance** | isotonic/Bayes-binning ECE 0.027–0.028 vs 0.022 (n=3000); worse at n≈170 for LR | prefer Platt/temperature at modest n |
| F9 | **Split CP under drift/covariate shift** | coverage 0.72–0.73 (target 0.80); housing 0.498; reg vol-jump 0.512 | rolling/weighted/ACI restore marginal coverage |
| F10 | **Marginal coverage ≠ acted-decision reliability** | singleton accuracy 0.65–0.73 at "80%" coverage | none tested |
| F11 | **Local under-coverage after a break** even for ACI | worst 500-step window coverage 0.755 (abrupt), 0.73–0.76 (rolling) | none tested (would need strongly-adaptive variants) |
| F12 | **Vetoes not better than a higher confidence threshold** at equal coverage | P2/P4 vs matched_conf_risk in 05 | use flags only for explicit data faults |
| F13 | **Weak-signal vs no-signal confusion**; ensemble misses sparse-region uncertainty | Q4 recall 0.36 / 0.15 | none |
| F14 | **Total abstention when a fault is pervasive** | P3 coverage 0.039 under 30%/feature missingness | expected behaviour; means "no trade", not "graceful degradation" |

## Process failures found and corrected (kept for auditability)
1. **Label leak in first ELEC2 task.** Predicting y_t from `price − mean(prev 48)` gave Brier 0.004 (implausible): the label *is* "price above moving average". Task redefined as forecasting y_{t+1} from features at t. Results in 03/04/06 use the forecasting version.
2. **Calibrator fitted on train rows (online bug).** `run_online` initially fit on `p[:t0]` (train + cal). HGB is in-sample on the train block, so static Platt was fitted on artificially confident data (stationary ECE 0.117). Fixed with a `c0` = calibration-block start argument; online experiment re-run. The stationary control now matches the static experiment (0.013), which is how the bug was found.
3. **Process / CPU oversubscription** (parallel jobs × OpenMP threads, load ≈ 20) stalled the first runs; re-run with `OMP_NUM_THREADS=1`. Results unaffected (identical md5 of `shift_cal.csv` across the re-run).
4. An accidental `pkill -f` killed its own shell once; no results affected.
