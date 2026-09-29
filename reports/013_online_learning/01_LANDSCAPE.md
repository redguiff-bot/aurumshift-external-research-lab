# 01 — Landscape of lightweight online-learning methods

Evidence labels per `claude.md`. Literature entries are DOCUMENTED_CLAIM (cited from memory of the primary papers; **not re-read in this session**). "Executed" = run in `bench/online_learning_v1` (OBSERVED in 04).

| # | candidate family | primary source | what it claims | state / update | executed here as |
|---|---|---|---|---|---|
| 1 | River estimators | Montiel et al., JMLR 2021; `online-ml/river` (BSD-3, v0.26.1, PROVEN) | unified streaming API `learn_one/predict_one`, pure-Python | per-model objects, picklable (OBSERVED) | the container for rows 2–7,9 |
| 2 | Online linear / logistic (SGD) | classic | O(d) update; tracks drift via constant step-size | d weights | `river.LogisticRegression`, `LinearRegression` |
| 3 | Passive-Aggressive | Crammer et al., JMLR 2006 | margin-based update, no learning-rate schedule | d weights | `PAClassifier`, `PARegressor` (+ own online Platt) |
| 4 | Incremental / Hoeffding trees | Domingos & Hulten, KDD 2000 (VFDT) | split when Hoeffding bound says the best attribute is best | grows with data | `HoeffdingTreeClassifier` |
| 5 | Hoeffding *adaptive* tree | Bifet & Gavaldà 2009 | ADWIN per node, grow alternate subtree on drift | grows | `HoeffdingAdaptiveTree{Classifier,Regressor}` |
| 6 | Adaptive Random Forest | Gomes et al., Machine Learning 2017 | online bagging + per-member drift/warning detectors and background trees | grows × n_models | `ARF{Classifier,Regressor}` (5 members) |
| 7 | Online boosting / bagging | Oza & Russell 2001; ADWIN-bagging (Bifet et al. 2009) | Poisson resampling as online bagging/boosting | grows × n_models | `ADWINBaggingClassifier` (5×HT). `AdaBoost`, `ADWINBoosting`, `SRP`, `LeveragingBagging` **not run** (same family; time) |
| 8 | Recursive least squares | textbook (Haykin) | exact ridge-like solution with exponential forgetting λ | d + d² | own numpy `RLS(λ)` (CUSTOM, ~10 LOC) |
| 9 | Kalman-style adaptive coefficients | Kalman 1960 | random-walk state for w, gain from noise ratio | d + d² | own numpy `Kalman(q)`; river `BayesianLinearRegression(smoothing)` as the OSS analogue |
| 10 | Online probability calibration | Platt 1999 (batch) → online 2-param SGD | recalibrate scores to probabilities as data drifts | 2 scalars | own `PAWrap`/`PlattLR` (CUSTOM) |
| 11 | Drift-triggered reset | ADWIN: Bifet & Gavaldà, SDM 2007 (rate guarantees are DOCUMENTED_CLAIM) | forget on detected change | base + buffer of 150 | `DriftReset` (CUSTOM) wrapping `river.drift.ADWIN` |
| 12 | Bounded rolling retraining | folklore baseline | refit on last W labels every k steps | W samples | `rolling` (also the **baseline**) |
| + | Recurring-regime memory | concept-recurrence literature (e.g. Gama et al. 2014 survey; not verified) | keep old models, re-activate on recurrence | K snapshots | `Bank` (CUSTOM, K=3) |

Not evaluated (UNKNOWN): Vowpal Wabbit, MOA / CapyMOA, deep continual learning (EWC, replay buffers, etc.). Deep methods are out of the "lightweight, bounded, versionable" brief; catastrophic forgetting in the neural sense (McCloskey & Cohen 1989) is therefore only probed through linear-model probes (05).

## Immediate expectations written before running (INFERENCE — to be falsified in 08)
1. On linear-Gaussian drift, RLS/Kalman-type learners should be the strongest incremental methods; trees should lose.
2. Drift-triggered resets help abrupt change, hurt false drift.
3. A rolling refit is a hard baseline to beat by more than ~10–20 %.
4. Recurring regimes are only exploited by an explicit memory.
