# 07 — OSS components

Evidence levels: PROVEN (executed/inspected here), OBSERVED (measured here), DOCUMENTED_CLAIM (docs/paper only), INFERENCE, UNKNOWN.

| component | version | licence | executed here | persistence / determinism | notes |
|---|---|---|---|---|---|
| **River** (`online-ml/river`) | 0.26.1 (PyPI 2026-08-21; 0.24→0.26 released Apr–Aug 2026: OBSERVED from PyPI JSON) | BSD-3-Clause (PROVEN: LICENSE file in wheel) | yes (all River rows in 04) | models are plain Python objects → `pickle` works for all of them (OBSERVED, see 06); RNG-using learners take `seed=` | runtime deps only numpy, scipy, narwhals (PROVEN from wheel METADATA); pure-Python/Cython loops ⇒ 10²–10⁴ µs per update for tree ensembles (OBSERVED, table "compute" in 04) |
| `river.linear_model.LogisticRegression / LinearRegression / PA* / BayesianLinearRegression` | 0.26.1 | BSD-3 | yes | tiny state (dict of weights) | `BayesianLinearRegression` has an optional `smoothing` (forgetting) parameter; PA* have no probability output (needs calibration) |
| `river.tree.HoeffdingTree*`, `HoeffdingAdaptiveTree*`, `river.forest.ARF*`, `river.ensemble.ADWINBagging*` | 0.26.1 | BSD-3 | yes | state **grows** with data unless `max_size`/`max_depth` limit it (OBSERVED: 10²–10³ KB) | ARF/HAT embed ADWIN per member (PROVEN by source: `forest/adaptive_random_forest.py` clones `drift_detector` per model) |
| `river.drift.ADWIN` | 0.26.1 | BSD-3 | yes (inside DriftReset/Bank) | O(log n) buckets | DOCUMENTED_CLAIM (Bifet & Gavaldà 2007) rate guarantees; only empirically probed here |
| scikit-learn `LogisticRegression` | 1.9.1 | BSD-3 | yes (baselines) | deterministic (lbfgs) | batch reference only |
| numpy RLS / Kalman | own code (~40 LOC) | this repo | yes | 8×8 covariance: ≈840 bytes pickled | no library needed; adopting a library (e.g. `filterpy`, `statsmodels` `RecursiveLS`) buys nothing at this size (INFERENCE; not executed) |
| Vowpal Wabbit, MOA/CapyMOA, `scikit-multiflow` | – | – | **no** | – | UNKNOWN for this study: JVM/C++ toolchains outside the "lightweight" brief; `scikit-multiflow` is documented by its authors as merged into River (DOCUMENTED_CLAIM, not re-verified) |

Reuse-vs-custom verdict (research-only, no integration claim): use River where it is a *learner* (SGD linear, PA, HAT/ARF, ADWIN); the recurrence-memory and warm-start-reset wrappers are ~40 LOC each and were written here because no reviewed component provides them — they are CUSTOM and stay flagged as such until they earn their place in 09.
