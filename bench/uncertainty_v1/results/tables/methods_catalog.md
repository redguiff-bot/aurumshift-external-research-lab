| id | family | method | status | source / verification |
|---|---|---|---|---|
| C1 | calibration | Platt scaling (top-label) | EXECUTED | Platt 1999 (citation from memory, NOT re-verified) |
| C2 | calibration | Isotonic regression (top-label) | EXECUTED | Zadrozny & Elkan 2002 (citation from memory, NOT re-verified) |
| C3 | calibration | Beta calibration (top-label) | EXECUTED | Kull et al. 2017 (citation from memory, NOT re-verified) |
| C4 | calibration | Temperature scaling | EXECUTED | Guo et al. 2017, arXiv 1706.04599 (title verified via arXiv API) |
| C5 | calibration | Bayesian binning, simplified 'BBQ-lite' (posterior-mean, bin-count averaging only) | EXECUTED | Naeini et al. 2015 (citation from memory, NOT re-verified) |
| C6 | calibration | Histogram binning | DISCOVERED_NOT_EXECUTED | Zadrozny & Elkan 2001 |
| C7 | calibration | Vector / matrix scaling | DISCOVERED_NOT_EXECUTED | Guo et al. 2017 |
| C8 | calibration | Dirichlet calibration | DISCOVERED_NOT_EXECUTED | Kull et al. 2019, arXiv 1910.12656 (title verified via arXiv API) |
| C9 | calibration | Bayesian logistic / Laplace calibrator with credible intervals on confidence | DISCOVERED_NOT_EXECUTED | general |
| C10 | calibration | Train-time calibration (label smoothing, focal loss) | DISCOVERED_NOT_EXECUTED | general |
| U1 | uncertainty | Max-softmax-probability confidence | EXECUTED | Hendrycks & Gimpel 2016, arXiv 1610.02136 (title verified via arXiv API) |
| U2 | uncertainty | Predictive entropy | EXECUTED | general |
| U3 | uncertainty | Bootstrap-ensemble disagreement (mutual information) | EXECUTED | concept: Lakshminarayanan et al. 2017, arXiv 1612.01474 (title verified via arXiv API); bootstrap LR/GBM instead of NN |
| U4 | uncertainty | Deep ensembles (independent NN inits) | DISCOVERED_NOT_EXECUTED | arXiv 1612.01474 |
| U5 | uncertainty | MC-dropout | DISCOVERED_NOT_EXECUTED | Gal & Ghahramani 2015, arXiv 1506.02142 (title verified via arXiv API) |
| U6 | uncertainty | Gaussian prediction interval from calibration residual std | EXECUTED | textbook |
| U7 | uncertainty | Locally normalised (heteroscedastic) residual scale | EXECUTED | general; used inside conformal variants |
| U8 | uncertainty | Conformalised quantile regression (CQR) | DISCOVERED_NOT_EXECUTED | Romano et al. 2019, arXiv 1905.03222 (title verified via arXiv API) |
| S1 | selective | Selective classification + risk-coverage curves / AURC | EXECUTED | Geifman & El-Yaniv 2017, arXiv 1705.08500 (title verified via arXiv API) |
| S2 | selective | Confidence-threshold abstention, tau chosen on validation by utility | EXECUTED | general |
| S3 | selective | Fixed-budget abstention (validation-quantile thresholds) | EXECUTED | general |
| S4 | selective | Epistemic (ensemble-MI) abstention | EXECUTED | general |
| S5 | selective | Conformal-singleton abstention (reject when set size != 1) | EXECUTED | general |
| S6 | selective | Learned reject option (SelectiveNet, Deep Gamblers) | DISCOVERED_NOT_EXECUTED | general |
| S7 | selective | Learn-then-Test risk control | DISCOVERED_NOT_EXECUTED | Angelopoulos et al. 2021, arXiv 2110.01052 (title verified via arXiv API) |
| F1 | conformal | Split conformal (absolute residual; LAC score 1-p_y) | EXECUTED | LAC: Sadinle et al. arXiv 1609.00451 (title verified via arXiv API); intro: arXiv 2107.07511 (title verified via arXiv API) |
| F2 | conformal | Rolling-window conformal (recency window, matured scores only) | EXECUTED | heuristic; no finite-sample guarantee under drift |
| F3 | conformal | Recency-weighted conformal (exponential decay weights) | EXECUTED | heuristic in the spirit of Barber et al. 2023, arXiv 2202.13415 (title verified via arXiv API) |
| F4 | conformal | Adaptive Conformal Inference (ACI) with delayed feedback, split scores | EXECUTED | Gibbs & Candes 2021, arXiv 2106.00170 (title verified via arXiv API) |
| F5 | conformal | ACI on rolling scores | EXECUTED | composition of F2+F4 |
| F6 | conformal | Normalised conformal and normalised+ACI | EXECUTED | composition of U7+F1/F4 |
| F7 | conformal | Weighted conformal under covariate shift (estimated density ratio; california task only) | EXECUTED | Tibshirani et al. 2019, arXiv 1904.06019 (title verified via arXiv API) |
| F8 | conformal | EnbPI (ensemble batch prediction intervals) | DISCOVERED_NOT_EXECUTED | Xu & Xie 2021, arXiv 2010.09107 (title verified via arXiv API) |
| F9 | conformal | Conformal PID control | DISCOVERED_NOT_EXECUTED | Angelopoulos et al. 2023, arXiv 2307.16895 (title verified via arXiv API) |
| F10 | conformal | SAOCP / strongly adaptive online conformal | DISCOVERED_NOT_EXECUTED | Bhatnagar et al. 2023, arXiv 2302.07869 (title verified via arXiv API) |
| F11 | conformal | AgACI (aggregated ACI) for time series | DISCOVERED_NOT_EXECUTED | Zaffran et al. 2022, arXiv 2202.07282 (title verified via arXiv API) |
| F12 | conformal | APS / RAPS adaptive prediction sets | DISCOVERED_NOT_EXECUTED | Romano et al. 2020, arXiv 2006.02544 (title verified via arXiv API) |
| D1 | shift | Per-feature two-sample KS (windowed) | EXECUTED | general; Rabanser et al. 2018, arXiv 1810.11953 (title verified via arXiv API) |
| D2 | shift | Mahalanobis distance (window mean and per-row percentile) | EXECUTED | general |
| D3 | shift | Domain-classifier two-sample test (cross-validated AUC) | EXECUTED | arXiv 1810.11953 |
| D4 | shift | Missing-value rate monitor | EXECUTED | general |
| D5 | shift | Repeated-value (stale feed) monitor | EXECUTED | general |
| D6 | shift | Realised-loss window monitor on matured labels | EXECUTED | general |
| D7 | shift | Label-shift estimation (BBSE) | DISCOVERED_NOT_EXECUTED | Lipton et al. 2018, arXiv 1802.03916 (title verified via arXiv API) |
| D8 | shift | ODIN / energy-based OOD scores | DISCOVERED_NOT_EXECUTED | Liang et al. 2017, arXiv 1706.02690 (title verified via arXiv API) |
| D9 | shift | Sequential change detectors (CUSUM, Page-Hinkley, ADWIN) | DISCOVERED_NOT_EXECUTED | general |
| O1 | online | Static calibration (fit once on calibration split) | EXECUTED | baseline |
| O2 | online | Sliding-window recalibration with label-maturity delay | EXECUTED | general |
| O3 | online | Expanding-window recalibration | EXECUTED | general |
| O4 | online | Exponential-decay-weighted recalibration | EXECUTED | general |
| O5 | online | Look-ahead-leaky recalibration (h0, peek) - harness control only | EXECUTED | own control |
| O6 | online | Online gradient / Newton calibrators, Bayesian online calibration | DISCOVERED_NOT_EXECUTED | general |
