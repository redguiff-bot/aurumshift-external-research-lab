# 01 — Methods discovered and executed

Evidence labels (repo doctrine): **PROVEN** (derived/verified in this study), **OBSERVED** (measured here), **DOCUMENTED_CLAIM** (from the literature, recalled from memory — *not re-fetched or re-verified in this session*), **INFERENCE**, **UNKNOWN**.

Literature citations below are DOCUMENTED_CLAIM: I did not open the papers in this run (no paper fetch was performed), so any specific bound or wording must be re-checked against the primary source before being relied on.

## Catalogue (13 requested families → 24 concrete methods discovered)

| # | Family | Concrete method | Source (DOCUMENTED_CLAIM) | Executed? |
|---|---|---|---|---|
| 1 | Platt scaling | logistic on logit(score) (a·z+b) | Platt 1999 | **YES** (`Platt`) |
| 2 | Isotonic | PAV, monotone, non-parametric | Zadrozny & Elkan 2002 | **YES** (`Iso`, clipped to [0.02,0.98]) |
| 3 | Beta calibration | logit q = a·ln p − b·ln(1−p) + c | Kull, Silva Filho, Flach 2017 | **YES** (`Beta`, unconstrained a,b) |
| 4 | Temperature scaling | single T on logits | Guo et al. 2017 | **YES** (`Temp`) |
| 5 | Bayesian calibration | equal-mass binning with Beta posterior (single-binning BBQ-style; yields credible half-width) | Naeini et al. 2015 (BBQ) | **YES**, *simplified* single binning (`BayesBin`) — full BBQ model averaging NOT implemented |
| 5b | Bayesian calibration | GP / Dirichlet / full Bayesian NN | Wenger 2020, Kull 2019 | NO (discovered only) |
| 6 | Ensemble disagreement | bootstrap ensemble of 8 shallow GBMs, std of P(up) | Lakshminarayanan 2017 (deep ensembles) | **YES** |
| 7 | Prediction intervals | split-conformal absolute-residual intervals (regression) | Lei et al. 2018 | **YES** |
| 7b | Prediction intervals | quantile regression / CQR | Romano 2019 | NO (discovered only) |
| 8 | Conformal — split (LAC) | fixed calibration block | Vovk; Angelopoulos & Bates 2021 | **YES** |
| 8b | Conformal — rolling window | recent scores only, label-delay aware | practitioner heuristic | **YES** |
| 8c | Conformal — recency-weighted | exponentially weighted quantile (non-exchangeable) | Barber et al. 2023 (weights) | **YES**, fixed λ=0.998, ad-hoc (no TV-distance-based tuning) |
| 9 | Online conformal | ACI (adaptive α_t) | Gibbs & Candès 2021 | **YES** (h=0 textbook and h=10 delayed-feedback variants) |
| 9b | Online conformal | AgACI / multi-γ aggregation, SAOCP, EnbPI, conformal PID | Zaffran 2022; Bhatnagar 2023; Xu & Xie 2021; Angelopoulos 2023 | NO (discovered only) |
| 10 | Selective classification | confidence-threshold reject option, risk–coverage / AURC | Chow 1970; Geifman & El-Yaniv 2017 | **YES** |
| 11 | Risk-coverage | full curves + AURC per model/calibrator | same | **YES** (AURC computed in `ulib.aurc`; curves derivable from `risk_coverage`) |
| 12 | Abstention thresholds | fixed τ from cost model (τ*=(1+c)/2 for ±1 payoff, cost c) | INFERENCE (Bayes decision rule) | **YES** (c=0.2 → τ=0.6) |
| 13 | Shift detection | Mahalanobis on features; ensemble std; confidence drop; missing/stale flags; label-based rolling calibration monitor (binomial z) | Rabanser 2019, Ovadia 2019 | **YES**; PSI implemented but not used in headline tables |
| 13b | Shift detection | classifier two-sample tests, MMD, KS multivariate | Rabanser 2019 | NO (discovered only) |
| – | Software found | MAPIE (pip index shows 1.5.0 — OBSERVED); netcal, crepes, puncc, TorchCP | package indexes | NOT used: all methods re-implemented in ~350 lines of numpy/scikit-learn so that delay handling / lookahead is auditable. No cross-check against MAPIE was run (UNKNOWN whether outputs agree bit-for-bit). |

**METHODS_DISCOVERED = 24, METHODS_EXECUTED = 16** (Platt, isotonic, beta, temperature, Bayes-binning, bootstrap-ensemble disagreement, split-conformal PI, split CP, rolling CP, recency-weighted CP, ACI h=0, ACI h=10, selective-classification/abstention thresholds, Mahalanobis/ensemble/flag/monitor detectors counted as 4 → 16 distinct executed items when detector variants are counted individually; see counting note in `00_EXECUTIVE_SUMMARY.md`).

Counting note: numbers are a bookkeeping convention (I count each row of the table with an "Executed = YES" as one, sub-variants merged only where the code path is identical). They are not a quality measure.

## Implementation notes (OBSERVED from code in `bench/uncertainty_v1/py/ulib.py`)
* Calibrators are fit on the **calibration block only**; hyper-parameters (abstention τ) are either derived from a cost model or tuned on the **validation block**; all headline numbers come from the **held-out** block.
* Online methods only use labels `y_j` with `j + h ≤ t` (h = label delay, 10 steps in synthetic, 1 or 48 half-hours in ELEC2). `run_online` asserts this (`pit_ok`), and two intentionally leaky variants (`leak_block`, `leak_global`) exist solely to measure how much a lookahead bug would flatter results.
* Top-label ECE uses 15 equal-mass bins (fewer if n is small). Positive-class ECE (`ece_pos`) is also stored.
