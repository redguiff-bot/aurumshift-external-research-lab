# 012 — Uncertainty calibration and abstention: executive summary

External research only; no private AurumShift code; no integration claim. Code and raw results: `bench/uncertainty_v1/`. Evidence labels as in `01_METHODS.md`. Data: controlled synthetic worlds (20 seeds shift/taxonomy, 8 online/conformal) + public data (ELEC2 real drifting series, breast cancer, California housing). Calibration / validation / held-out kept separate (protocol in 02).

## Headline
1. **Calibration works when stationary.** An over-confident GBM has ECE 0.118 and false-confidence rate 0.119; Platt/temperature/beta bring it to ECE 0.022 (oracle 0.017). Already-calibrated models are not harmed. Isotonic/Bayes-binning are no better at n=3000. (03)
2. **It does not survive shift.** With the pre-declared rule, calibration survives 2 of 6 shifts (feature shift, missing features); it fails on volatility jump (ECE 0.141), regime transition (0.172), stale features (0.076), venue change (0.068). On real ELEC2, a calibrator fit on the calibration window *worsened* ECE for LR (0.103 → 0.15–0.17). (03, 07)
3. **A model can stay confident while wrong:** under feature shift and vol jump, low confidence is anti-informative (AUROC 0.39/0.43); false-confidence rate rises 2–4.5× over iid (0.024 → 0.054–0.107) even after calibration. Regime transitions are invisible to label-free detectors (AUROC 0.50). (07)
4. **Abstention helps, within limits.** τ=0.6 (derived from a ±1 payoff, cost 0.2; no tuning) trades 69% of rows, cuts selective risk 0.318 → 0.256, avoids 45% of bad decisions, keeps 75% of good ones. Under concept shift it does not help (risk 0.486 → 0.482). Ensemble/OOD vetoes add little beyond a higher confidence threshold; data-fault flags do help. (05)
5. **Online recalibration helps under drift if — and only if — PIT-safe:** sliding-window Platt cuts abrupt-regime ECE 0.100 → 0.017 and worst-chunk ECE 0.182 → 0.104; expanding-window is weak. Lookahead audit passes; leaky variants quantify inflation. Parameter instability (slope sd up to 0.78 on ELEC2-LR) is a real risk. (04)
6. **Conformal: split CP is invalid under drift** (coverage 0.72–0.73 vs 0.80; housing covariate shift 0.498; regression vol-jump 0.512). ACI (also with delayed feedback) and recency-weighted CP hold marginal coverage in every setting tested; rolling in 8/9. **But marginal coverage is not decision reliability:** acted (singleton) accuracy is only 0.65–0.73 at "80%" coverage on synthetic streams, and windows right after a break under-cover. (06)
7. **Cause separation (Q4) is half-achieved:** DATA_GAP 0.97 and OOD 0.98 recall; NO_SIGNAL 0.36; MODEL_UNCERTAINTY 0.15 (generator-defined labels — an upper bound). (07)

## Adjudicated recommendation (external candidates only)
* Simple reference: Platt (≈ temperature) on a held-aside calibration block + cost-derived abstention τ + explicit missing/stale HOLD flags.
* Online reference: sliding-window Platt with delayed labels + delayed-feedback ACI + label-based calibration monitor.
* Do **not** claim iid coverage for split conformal on time series; do **not** treat marginal coverage as trade accuracy.

## Process honesty
Two errors were caught and fixed mid-study (an ELEC2 label-definition leak; a calibrator wrongly fit on training rows in the online code) — see 08. All numbers in these reports come from the final code and CSVs in `bench/uncertainty_v1/results/`.

## FINAL BLOCK
```
METHODS_DISCOVERED=31
METHODS_EXECUTED=26

STATIC_CALIBRATION_SUPPORTED=YES_STATIONARY_ONLY (NO across time on ELEC2)
ONLINE_CALIBRATION_SUPPORTED=YES_WITH_LIMITS (sliding-window/SGD, PIT-safe; expanding NO)
ABSTENTION_SUPPORTED=YES_WITH_LIMITS (not under concept/regime shift)
CONFORMAL_SUPPORTED=PARTIAL (ACI/weighted marginal coverage only; split invalid under drift; no decision-level guarantee)

CALIBRATION_SURVIVES_SHIFT=NO (2 of 6 shift types)
FALSE_CONFIDENCE_REDUCED=PARTIAL (yes vs raw and via online recalibration; not restored to iid level under shift)

BEST_SIMPLE_REFERENCE=Platt scaling on a held-aside calibration block + cost-derived confidence threshold + missing/stale flags
BEST_ONLINE_REFERENCE=Sliding-window Platt (delayed labels, PIT-asserted) + delayed-feedback ACI + label-based calibration monitor

FINAL_VERDICT=LIMITED_UNCERTAINTY_METHODS_SUPPORTED
```
