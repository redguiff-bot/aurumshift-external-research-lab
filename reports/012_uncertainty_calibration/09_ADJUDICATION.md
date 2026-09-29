# 09 — Adjudication

Boundary: these are **external-research** candidates (ADOPT / ADAPT / PARK / REJECT). Nothing here asserts compatibility with, or knowledge of, the private AurumShift implementation; final integration is to be adjudicated against the real repository, including whether it has a point-in-time label store with a known maturity delay, what confidence scores it emits, and its real cost model.

## Candidate decisions
| candidate | decision | basis |
|---|---|---|
| Temperature scaling on logits, fit on a held-out calibration split | **ADOPT** (reference) | best or tied-best in every stationary test; 1 parameter; argmax-preserving |
| Sliding-window (W≈600 rows) temperature recalibration, matured labels only, refit ~every 50 steps | **ADAPT** | recovers ≈80–100 % of the shift-induced ECE excess; free in stationary data; needs label-maturity contract and window tuning (edge-of-grid on ELEC2) |
| Realised-loss monitor on matured labels | **ADOPT** as shift alarm | only detector of concept/vol shifts |
| NaN-rate and repeated-value/age monitors as explicit DATA_GAP flags | **ADOPT** | exact, instant; statistical detectors cannot replace them |
| Domain-classifier two-sample test on features | **ADAPT** | best false-alarm rate of the statistical detectors (2.4 %); needs persistence rule |
| Confidence-threshold abstention with validation τ, on *online-calibrated* confidence | **ADAPT** | prevents large losses under negative-EV shifts; modest in-distribution; payoff-dependent |
| ACI on rolling scores (γ=0.01) as a marginal-coverage monitor for intervals | **ADAPT (monitoring only)** | 0.899 marginal coverage under all tested shifts; no conditional/local claim |
| Beta, isotonic, BBQ-lite | **PARK** | no gain over temperature; isotonic most look-ahead-sensitive |
| Recency-weighted / rolling conformal | **PARK** | heuristic; transient undercoverage |
| Weighted conformal with estimated density ratio | **PARK** | improves but far from nominal (0.65 vs 0.90) |
| Conformal-singleton abstention as a trade gate (α=0.2, weak signal) | **PARK** | discards 58–76 % of decisions |
| Bootstrap-ensemble disagreement as abstention/epistemic score | **REJECT** (as evaluated) | not better than max-prob; MODEL_UNCERTAINTY F1 0.07 (deep ensembles / MC-dropout not tested) |
| Platt scaling on over-confident tree ensembles | **REJECT** | ECE 0.119 |
| Split-conformal coverage claims under drift | **REJECT** | 0.77 vs 0.90, 0.54 for vol jump |
| Gaussian intervals | **REJECT** | 0.75 in stationary, 0.58 under shift |
| Static calibration claims across regime change | **REJECT** | ECE drift up to +0.19 |

## Answers to the four questions
* **Q1** Yes (stationary; miscalibration fixable by a monotone/temperature map). No gain if the model is already calibrated.
* **Q2** Partly: modest lift over random; risk-control value under negative-EV shift only with online-calibrated confidence; ensemble disagreement does not help.
* **Q3** Static: no. Online with matured labels: mostly yes, after a transient; cannot fix a wrong model (regime transition Brier stays high).
* **Q4** Partly: DATA_GAP (via flags), NO_SIGNAL (via calibrated confidence), OOD (high precision/low recall). MODEL_UNCERTAINTY not separable; concept shifts invisible to input-space uncertainty.

## Final block
METHODS_DISCOVERED=52
METHODS_EXECUTED=33

STATIC_CALIBRATION_SUPPORTED=YES_IN_STATIONARY_REGIME_ONLY (temperature scaling; large gain for over-confident learners, none for calibrated ones)
ONLINE_CALIBRATION_SUPPORTED=YES (sliding-window/decayed temperature with matured labels; synthetic 12 seeds + ELEC2; needs label-delay contract)
ABSTENTION_SUPPORTED=PARTIAL (modest ~1.4x lift over random; helpful for risk control under negative-EV shift with online-calibrated confidence; utility-negative beyond ~5% abstention in a stationary positive-EV payoff; ensemble-disagreement not supported)
CONFORMAL_SUPPORTED=PARTIAL (valid only for exchangeable data; ACI-type gives empirical long-run marginal coverage under drift; no conditional or finite-sample time-series validity claimed)

CALIBRATION_SURVIVES_SHIFT=NO_FOR_STATIC; YES_WITH_LAG_FOR_ONLINE_RECALIBRATION
FALSE_CONFIDENCE_REDUCED=YES (confident-wrong mass 0.34->0.07 by calibration; 0.13->0.03 under shift by online recalibration; not eliminated for OOD or concept shift without explicit gates)

BEST_SIMPLE_REFERENCE=temperature_scaling_on_logits_fit_on_held_out_calibration_split + validation_chosen_confidence_threshold
BEST_ONLINE_REFERENCE=sliding_window_temperature_scaling(W=600,refit_every=50,label_maturity_delay=10) + realised_loss_monitor; ACI_on_rolling_scores(gamma=0.01) for marginal interval coverage monitoring

FINAL_VERDICT=LIMITED_UNCERTAINTY_METHODS_SUPPORTED
