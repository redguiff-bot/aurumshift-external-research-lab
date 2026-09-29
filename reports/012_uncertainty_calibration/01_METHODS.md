# 01 — Methods discovered and executed

Evidence labels (repo doctrine): **PROVEN** (derived/verified in this study), **OBSERVED** (measured here), **DOCUMENTED_CLAIM** (from the literature, recalled from memory — *not re-fetched or re-verified in this session*), **INFERENCE**, **UNKNOWN**.

All citations in the "Source" column are DOCUMENTED_CLAIM: no paper was opened in this run, so specific bounds/wording must be checked against the primary source before being relied on.

## Catalogue

| # | Family | Method | Source | Executed | Note |
|---|---|---|---|---|---|
| 1 | Platt | Platt scaling (a·z+b) | Platt 1999 | **YES** | `Platt` |
| 2 | Isotonic | Isotonic regression (PAV) | Zadrozny & Elkan 2002 | **YES** | `Iso`, output clipped to [0.02,0.98] |
| 3 | Beta | Beta calibration | Kull et al. 2017 | **YES** | `Beta`, a,b unconstrained (sign not enforced) |
| 4 | Temperature | Temperature scaling | Guo et al. 2017 | **YES** | `Temp` |
| 5 | Bayesian | Bayesian equal-mass binning (single-binning BBQ-style, Beta posterior) | Naeini et al. 2015 | **YES** | `BayesBin`; simplified — no BBQ model averaging |
| 6 | Bayesian | Full BBQ model averaging / GP / Dirichlet calibration | Naeini 2015; Wenger 2020; Kull 2019 | no | discovered only |
| 7 | Ensemble | Bootstrap-ensemble disagreement (8 shallow GBMs, std of P) | Lakshminarayanan et al. 2017 | **YES** | used as veto/detector and risk-coverage ranking |
| 8 | Prediction intervals | Split-conformal prediction intervals (abs. residual) | Lei et al. 2018 | **YES** | regression, synthetic + California housing |
| 9 | Prediction intervals | Rolling-window conformal intervals | heuristic | **YES** | regression, label-delay aware |
| 10 | Prediction intervals | ACI intervals (regression) | Gibbs & Candès 2021 | **YES** |  |
| 11 | Prediction intervals | Quantile regression / CQR | Romano et al. 2019 | no | discovered only |
| 12 | Conformal | Split conformal, LAC score (classification) | Vovk; Angelopoulos & Bates 2021 | **YES** |  |
| 13 | Conformal | Rolling-window conformal (classification) | heuristic | **YES** |  |
| 14 | Conformal | Recency-weighted conformal (λ=0.998) | Barber et al. 2023 | **YES** | fixed ad-hoc weights, no TV-distance tuning |
| 15 | Online conformal | ACI, textbook immediate feedback (h=0) | Gibbs & Candès 2021 | **YES** | not deployable when labels are delayed |
| 16 | Online conformal | ACI with delayed feedback (h=10 / ELEC2 h=1) | adaptation of Gibbs & Candès | **YES** | guarantee for delayed feedback NOT proven here |
| 17 | Online conformal | AgACI, SAOCP, EnbPI, conformal PID / quantile tracking | Zaffran 2022; Bhatnagar 2023; Xu & Xie 2021; Angelopoulos 2023 | no | discovered only |
| 18 | Selective classification | Confidence-threshold reject option (selective classification) | Chow 1970; Geifman & El-Yaniv 2017 | **YES** |  |
| 19 | Risk-coverage | Risk-coverage curves / AURC | Geifman & El-Yaniv 2017 | **YES** | risk@{0.9,0.7,0.5,0.3}, AURC |
| 20 | Abstention thresholds | Cost-model abstention threshold τ*=(1+c)/2 | INFERENCE (Bayes rule for ±1 payoff, cost c) | **YES** | c=0.2 → τ=0.6 |
| 21 | Abstention thresholds | Veto rules (ensemble std, Mahalanobis, missing/stale flags) | INFERENCE | **YES** | policies P2–P4 |
| 22 | Shift detection | Mahalanobis feature-distance detector | classic | **YES** |  |
| 23 | Shift detection | Confidence-drop / ensemble-std shift detector | Ovadia 2019 | **YES** |  |
| 24 | Shift detection | Missing-value and exact-repeat (stale) flags | engineering | **YES** |  |
| 25 | Shift detection | Label-based rolling binomial calibration monitor | INFERENCE | **YES** | z<-3 on acted rows, labels delayed h=10 |
| 26 | Shift detection | PSI feature drift | industry standard | no | implemented in `ulib.psi`, NOT used in any reported result |
| 27 | Shift detection | Classifier two-sample test, MMD, multivariate KS | Rabanser et al. 2019 | no | discovered only |
| 28 | Online calibration | Online recalibration: sliding-window Platt | heuristic | **YES** | W=1000/2000, refit every 250 |
| 29 | Online calibration | Online recalibration: sliding-window isotonic | heuristic | **YES** |  |
| 30 | Online calibration | Online recalibration: expanding-window Platt | heuristic | **YES** |  |
| 31 | Online calibration | Online recalibration: SGD Platt (lr=0.02) | heuristic | **YES** |  |
| 32 | Online calibration | Deliberately leaky variants (block-fit, global-fit) as lookahead audit | this study | **YES** | never a candidate; measures leak inflation |

**Counting convention:** one row = one method; the last row (leaky lookahead audit variants) is a test device, not a candidate, and is excluded from both counts.

**METHODS_DISCOVERED = 31**, **METHODS_EXECUTED = 26** (5 discovered but not executed).

## Software found (not used)
MAPIE — `pip index` lists 1.5.0 (OBSERVED, index metadata only). netcal, crepes, puncc, TorchCP: UNKNOWN (not inspected). Everything was re-implemented in ~350 lines of numpy/scikit-learn (`bench/uncertainty_v1/py/ulib.py`) so label-delay handling and lookahead are auditable. **No cross-check against MAPIE or netcal was run** — agreement with those libraries is UNKNOWN. The Platt/logistic and isotonic calibrators do call scikit-learn's `LogisticRegression` / `IsotonicRegression`.

## Implementation notes (OBSERVED from code)
* Calibrators are fit on the **calibration block only**; hyper-parameters (τ) are cost-derived or tuned on **validation**; headline numbers are **held-out**.
* Online methods use only labels `y_j` with `j + h ≤ t` (h = label delay; 10 steps synthetic, 1 or 48 half-hours ELEC2). `run_online` asserts this (`pit_ok`).
* Top-label ECE: 15 equal-mass bins (fewer if n small); positive-class ECE also stored.
* A bug found and fixed during the study: the first online run fitted the initial/expanding calibrator on `p[:t0]`, i.e. including the *training* block where the overfit base model is in-sample; static-Platt looked broken (ECE 0.117 stationary). Fixed by a `c0` calibration-block start; all reported online numbers are post-fix (see 08_FAILURE_MODES).
