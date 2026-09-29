# 06 — Replay determinism, checkpointability, leakage

Runner: `bench/online_learning_v1/py/run_determinism.py` → `results/determinism.json` (OBSERVED). Scenario `abrupt_delayed`, seed 1, tuned configs, all 25 (model,track) entries.

| test | definition | result |
|---|---|---|
| same-process replay | two runs → identical SHA-256 of the prediction vector | **25/25 identical** |
| cross-process replay | two fresh interpreters with `PYTHONHASHSEED`=1 and 12345 → identical hash (and equal to in-process run) | **25/25 identical** |
| checkpoint / restore | run to t=2000, `pickle.dumps(model)` → `loads` → continue to 4000 → concatenated predictions identical to uninterrupted run | **25/25 identical** |
| no future leakage | corrupt every label with index ≥1500 (flip / 1e6); predictions at t≤1500 must be unchanged (delivery is delayed by 100 steps) | **25/25 unchanged** |
| negative control | a `Cheater` model reading the current label is run under the same protocol | **detected** (predictions at t≤1500 differ) → the test has power |
| update timestamp | `model.last_update` = harness clock of the last label delivery | 3999 for all (delay 100 ⇒ last delivered sample 3898) |

Also enforced on **every** run of the 3 750 held-out runs: harness assertion `τ+1+delay ≤ now` at each label delivery (no run aborted).

## What made it deterministic
* All stochastic River learners were built with an explicit `seed=` (HAT, ARF, ADWIN-bagging); the others are deterministic. numpy RNG use in streams is `default_rng([seed, f(name)])` (no Python `hash()`).
* BLAS threads pinned to 1 for the campaign (`OMP_NUM_THREADS=1`); the determinism suite was also run with that setting. Multi-threaded BLAS reproducibility is **UNKNOWN**.

## Checkpoint size (pickle bytes at t=2000, C/R)
Linear/PA/RLS/Kalman: 0.3–1.7 KB · reset/bank: 20 KB · rolling: 18–35 KB · batch (expanding buffer): 220 KB · HT 63 KB · HAT 69 KB (C) / 353 KB (R) · ADWIN-bag 324 KB · ARF 1.1 MB (R) / 5.0 MB (C).

## Caveats (see also 10)
* One platform, one Python (3.11.15), one numpy/scipy/sklearn/river version set — cross-machine / cross-BLAS bitwise identity is UNKNOWN; sklearn `lbfgs` in the batch baselines is deterministic here only.
* `pickle` is a *checkpoint* format, not a *versionable* one: a River upgrade can silently change a class layout (INFERENCE, not tested — only 0.26.1 was used). For the tiny linear learners (RLS/Kalman/logistic) an explicit versioned dict (`{schema, lam, P, w, last_update}`) would be trivial; for trees it is not (UNKNOWN).
* Determinism was tested on a single seed/scenario per model; a nondeterministic corner (e.g. dict-order-dependent tie-breaks in a tree split) could exist elsewhere.
