# 10 — Limitations

**Data realism**
* The synthetic world is authored by this study: features are Gaussian AR(1), the label is a threshold on a linear latent return, shifts are stylised. Conclusions about *relative* method behaviour under those shifts are OBSERVED; magnitudes are not predictions for any real market (UNKNOWN). The LR base is nearly correctly specified, which is why calibration adds nothing there.
* Public data are not financial returns: ELEC2 is a drifting electricity-price direction task; credit-g / breast-cancer / California are iid tabular tasks. There is **no venue, microstructure, or intraday financial dataset** here, so "venue change" is only simulated.
* Only 3 classes, one horizon, one H=10 label-maturity delay. Real forward-return labels overlap in time and mature at asset-specific horizons.
* The payoff (+1 / −1 / −0.3 / 0) is a toy. The abstention conclusions (small optimal abstention rate, utility falling with budget) follow directly from it; a real cost model with fees/slippage/adverse selection would change them (INFERENCE).

**Statistics**
* 12 held-out and 4 tuning seeds; intervals are t-CIs over seeds sharing generator code; scenario results within a seed are correlated. Public iid tasks use overlapping random re-splits and small test sets (≈114–200 rows), so their spread is understated. No multiple-comparison correction; treat differences below ≈0.01 ECE as noise (10-bin ECE floor ≈ 0.04 at n=500).
* Hyperparameters were tuned on only 4 seeds at 0.6× magnitude; ELEC2's best window/half-life sit at the grid edge.
* The process disclosures in `02_PROTOCOL.md` apply (bug fixed pre-held-out; abstention harness designed after seeing calibration held-out tables).
* Detector thresholds ("max on validation") are ad hoc; false-alarm behaviour is reported, not controlled.

**Method coverage**
* "Bayesian calibration" is represented only by BBQ-lite (posterior means, no credible intervals) — full Bayesian/Laplace calibrators with predictive intervals were **not executed**. Dirichlet/vector scaling, deep ensembles, MC-dropout, EnbPI, conformal PID, SAOCP, AgACI, APS/RAPS, CQR, Learn-then-Test, BBSE, ODIN and sequential change detectors were catalogued but not run (19 of 52).
* Top-label calibrators are not class-wise calibrators; multi-class calibration beyond temperature is untested.
* No neural networks; the "ensemble" is a bootstrap of the same LR/GBM, a weak proxy for deep-ensemble epistemic uncertainty (the MODEL_UNCERTAINTY negative result is specific to that proxy).
* The DATA_GAP class is defined by the injected fault and detected by the same flag, so its F1 = 1.0 is not evidence about model-based uncertainty.
* ACI with delayed feedback is run empirically; no coverage theorem is claimed. Time-series conformal *validity* was assessed from literature statements (titles verified, full texts not re-read) plus empirical coverage — not proven here.
* Not measured: calibrator-parameter jitter, sensitivity to refit period R and to H, computational cost, robustness to label noise/delay jitter.

**Scope**
* External research only. No AurumShift code, data, or thresholds were used; no statement about AurumShift's current calibration, label store, or performance is made. Any adoption requires re-running these tests against the real point-in-time data.
