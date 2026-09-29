# 02 — Protocol (pre-registered before any held-out run)

Status labels follow `claude.md`: PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN.
Everything below was fixed **before** `bench/online_learning_v1/results/main.json` existed (git history of this file is the evidence).

## 1. What is (and is not) tested
* External research only. No AurumShift code, no market data, no integration. All streams are **synthetic** and generated from a known process,
  so regret against the truth is computable exactly. Consequence: results say which *mechanisms* adapt/forget/replay well under controlled drift;
  they say **nothing** about AurumShift's real signal-to-noise, cost structure or drift statistics (see 10_LIMITATIONS).
* Two tracks share the same latent concept path `w_t` (unit vector, D=8, T=4000, burn-in N0=500):
  * **C (classification)**: `P(y=1|x)=sigmoid(3·w_t·x)`; metric = *excess KL* `KL(p_true(x_t) || p_model(x_t))` (noise-free regret; nats/step). Realised accuracy/log-loss reported as context.
  * **R (regression)**: `y = w_t·x + N(0,0.5²)`; metric = *excess MSE* `(pred − w_t·x)²`.
* Protocol is strictly **prequential**: predict(x_t) → then deliver whatever labels have *arrived* → learn. A label of sample τ arrives at clock `τ+1+delay`;
  the harness asserts `τ+1+delay ≤ now` on every delivery. Models get `now` as an explicit update timestamp.

## 2. Candidates (all executed; see 07_OSS_COMPONENTS for provenance)
River 0.26.1 (BSD-3): `LogisticRegression`(SGD), `LinearRegression`(SGD), `PAClassifier`, `PARegressor`, `BayesianLinearRegression`, `HoeffdingTreeClassifier`,
`HoeffdingAdaptiveTree{Classifier,Regressor}`, `ARF{Classifier,Regressor}` (5 members), `ADWINBaggingClassifier`(5×HT), `drift.ADWIN`.
Own thin numpy code (≈40 lines each, flagged CUSTOM): `RLS(λ)`, random-walk `Kalman(q)`, online Platt calibration (2-param SGD) on LR logit / PA margin,
`DriftReset` (ADWIN on own prequential error → fresh model warm-started from the last 150 labelled samples), `Bank` (bounded K=3 snapshot memory + EWMA-loss switching; tests recurring-regime memory).
Not executed (listed in 01_LANDSCAPE with the reason): online boosting other than ADWIN-bagging (River `AdaBoost/ADWINBoosting`, `SRP`, `LeveragingBagging` are variants of the same family, not run), Vowpal Wabbit, MOA.

## 3. Baselines ("complexity must earn its place")
* `frozen`: fit once (ridge / L2-logistic, C=1) on the first 500 labelled samples, never updated.
* `batch`: expanding-window refit every P∈{250,500,1000} steps (tuned).
* `rolling`: bounded window W∈{150,300,600}, refit every 25 steps (tuned). This is simultaneously candidate #12 "bounded rolling retraining".
Baselines get the same tuning budget (a grid of 3) as candidates.

## 4. Drift scenarios (10, details in 03)
stationary (control), abrupt, gradual, recurring (A/B/A/B), temporary shock (100 steps), false drift (3× feature-scale + 3× noise burst, concept unchanged),
random-walk (slow diffusion), abrupt+missing feedback (70 % labels never arrive after the change), abrupt+delayed feedback (100 steps), abrupt nonlinear (interaction concept; fairness to trees).
Sensitivity run (same frozen configs): κ=1, σ=1.5 (≈3× lower SNR) on abrupt/recurring/random_walk, 8 seeds.

## 5. Tuning / evaluation split (no peeking)
* Tuning seeds 100–102, held-out seeds 1–15 (sensitivity: 1–8). One hyper-parameter set per (model, track) chosen by mean regret over **all** scenarios — never per scenario.
* "Best simple reference" per track = best of {frozen, batch, rolling} by **tuning-seed** mean regret over the 8 drift scenarios. "Best incremental reference" is reported both by tuning and by held-out.

## 6. Decision criteria (a method "EARNS ITS PLACE" on a track iff all four hold, on held-out seeds)
* **(a) Gain**: geometric mean over the 8 drift scenarios of `regret_M/regret_BSR` ≤ 0.90 **and** paired bootstrap (over seeds, 4000 resamples) 95 % CI upper bound < 1.0.
* **(b) No blow-up**: per-scenario mean ratio ≤ 1.25 vs the best simple reference on **every one of the 10 scenarios** (including the two controls).
* **(c) Bounded state**: median-of-seed state size at t=4000 ≤ 1.5 × at t=1000 in every scenario (pickle bytes of the entire model object).
* **(d) Replay**: bit-identical predictions on (i) same-process re-run, (ii) two fresh interpreters with different `PYTHONHASHSEED`, (iii) pickle-checkpoint at t=2000 → restore → resume, and (iv) predictions at t≤1500 unchanged when all labels ≥1500 are corrupted (no future leakage). A negative-control cheater must be flagged by (iv) to show the test has power.

## 7. Verdict mapping
* `ONLINE_ADAPTATION_REFERENCE_SUPPORTED` — ≥1 incremental method earns its place on **both** tracks (same method family) and the tuning-seed and held-out rankings agree (Spearman ≥ 0.5).
* `LIMITED_ONLINE_METHODS_SUPPORTED` — ≥1 method earns its place on one track only, **or** methods pass (a),(c),(d) but fail (b) only on a named subset of scenarios (then they are "supported with guard-rails", listed explicitly).
* `BATCH_RETRAIN_REMAINS_SUFFICIENT` — no incremental method passes (a) on either track (rolling/batch refit is within 10 % of the best incremental).
* `NO_ROBUST_ADAPTATION_METHOD` — some methods pass (a) but every one of them fails (b), (c) or (d) in a way that guard-rails cannot bound.
* `STUDY_INCONCLUSIVE` — tuning vs held-out ranking Spearman < 0.5 on either track, or bootstrap CIs on the headline comparison straddle the threshold.
Verdict is computed by `bench/online_learning_v1/py/analyze.py`; the narrative in 09_ADJUDICATION may not contradict it.

## 8. Measures
* Adaptation speed: steps until rolling-50 regret ≤ 1.5× own pre-change level + 0.01 (censored at 600) and 600-step post-change cumulative regret.
* Forgetting: fixed probe set (300 points) evaluated *without* learning at t=999/1999/2999/3999 against concept A and B; return-cost ratio = post-600 regret after returning to A ÷ post-600 regret at the first (novel) switch to B; post-shock damage.
* Variance: CV of regret across seeds, worst-seed / median-seed. State growth: pickle bytes at t=1000/4000. Compute: µs per label / prediction (OBSERVED on a shared 4-core container, indicative only).
