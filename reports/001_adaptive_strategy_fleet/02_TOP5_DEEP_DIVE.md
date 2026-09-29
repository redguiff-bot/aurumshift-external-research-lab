# 02 — Top-5 deep dive (Phase 3)

Clones (blobless, HEAD at 2026-09-29): river `03b481820`, mabwiser `b104071`, vowpal_wabbit `00196b35`, optuna `0d05a9673`, SMPyBandits `012fc13`
(also Ax `57efa05a`, contextualbandits `fc49364` for metadata only). Installed/executed versions: see `bench/requirements-observed.txt`.
Scripts for every OBSERVED/PROVEN item below are in `bench/` (`bench.py`, `persistence_check.py`, `failsoft_check.py`).

A note on running repo tests: in the River and MABWiser clones the source tree shadows the installed wheel (River needs a compiled Rust extension not present in
a bare clone; MABWiser's root `__init__.py` shadows the package). I therefore copied each `tests/` directory out and ran it **against the installed wheel**.
That is a deviation from "run the repo's CI" and is stated for each below.

---

## 1. River — `river.bandit`, `river.stats`, `river.drift`  → *strongest primitive set*

Sources: [repo](https://github.com/online-ml/river) · [UCB docs](https://riverml.xyz/latest/api/bandit/UCB/)

**Architecture (OBSERVED, `river/bandit/*.py`, 1,173 lines).** `Policy` base (`base.py`) holds `_rewards: defaultdict(reward_obj.clone)`, `_counts: Counter`, `_n`.
Policies: `UCB`, `BayesUCB`, `ThompsonSampling`, `EpsilonGreedy`, `Exp3`, `LinUCB` (contextual), `RandomPolicy`.
`pull(arm_ids)` takes the **currently available arm list on every call** ⇒ the arm set is dynamic by construction; a never-updated arm gets index `+inf` in UCB (`ucb.py`).
`update(arm_id, reward)` is a single-observation online update.

**Algorithm/extensibility (OBSERVED).** The reward estimator is a *pluggable object* (`stats.Mean`, `stats.EWMean(fading_factor)`, `utils.Rolling(...)`, `proba.Beta`, any metric). Forgetting is therefore obtainable by swapping the estimator.
**But** the UCB exploration bonus is `delta*sqrt(2*log(self._n)/self._counts[arm])` with **cumulative** `_n`/`_counts` (source, `ucb.py`), so a forgetting estimator does *not* shrink the effective sample size in the bonus. (INFERENCE from source + PROVEN behaviourally in `03`: `river_ucb_ew` under-explores/over-chases noise; regret ≈ round-robin in all 9 sweep settings.)
`river.stats` has no `RollingMean` (checked: `AttributeError`); rolling windows go via `utils.Rolling`. (OBSERVED)

**Persistence/state (OBSERVED).** Policies are plain Python objects; pickle round-trip continues **bit-identically** (`bench/persistence_check.py`: UCB-Mean, UCB-EWMean, Thompson-Beta all `identical continuation: True`; Thompson blob 122 KB for 30 arms — INFERENCE: each per-arm distribution carries its own seeded RNG). No relational/SQL persistence exists (searched `river/` for storage code: none — INFERENCE from absence, UNKNOWN for other modules).

**Determinism (PROVEN for tested policies).** Every policy takes `seed`, uses `random.Random(seed)`; same seed ⇒ identical selection hash across 3 different `PYTHONHASHSEED` values for `UCB` (mean/EW), `ThompsonSampling`, `EpsilonGreedy` (`results/determinism/`).

**Fail-soft (OBSERVED, `bench/failsoft_check.py`):**
* `pull([])` → `ValueError: max() arg is an empty sequence` (no graceful "nothing to do").
* `update(arm, None)` → `TypeError`.
* **A single NaN reward ingested by `UCB` poisons it: the *next* `pull` raises `IndexError`** (state is silently corrupted at ingest; failure appears later). Input sanitising is the caller's job.
* `Exp3.update` requires `_probabilities[arm]` from a preceding `pull`; in my harness both history warm-start and batched/delayed feedback raised `KeyError: 26` (`results/main/river_exp3.json`, OBSERVED). ⇒ Exp3 is unusable with logged history or batch feedback (`_probabilities` is overwritten on each `pull`, INFERENCE).

**Tests (OBSERVED, run against installed wheel).** `tests/bandit`: 3 passed, **22 skipped** — the only behavioural test (`test_better_than_random_policy`) is `@pytest.mark.skip(reason="flaky")` (source line 78). `tests/model_selection/test_bandit.py`: 14 passed. Docstring examples carry hard-coded reward sums (e.g. "Sum: 744.") — regression tests, not statistical validation. (OBSERVED)

**Maintenance/releases (OBSERVED).** 0.26.0 (2026-08-20), 0.26.1 (2026-08-21), 0.25.0 (2026-05-31); 299 commits and 39 distinct authors in 365 d, 69 commits in 90 d; last commit 2026-09-28. Open issues 52 (WebFetch summary; includes "Drift module roadmap: broaden detector coverage + build an evaluation harness", June 2026 — DOCUMENTED_CLAIM of an intent, not delivered work).
**Dependencies (OBSERVED).** `numpy>=2.2.5`, `scipy>=1.14.1`, `narwhals`; Python ≥3.11; clean venv site-packages 256 MB (numpy alone = 97 MB); 4 packages. Rust extension ships in wheels.
**Licence:** BSD-3-Clause (OBSERVED LICENSE + PyPI).

**Drift primitives (OBSERVED file list).** `river/drift/{adwin,page_hinkley,kswin,...}.py` exist; **not** benchmarked here (UNKNOWN effect on allocation).

---

## 2. Vowpal Wabbit — `--cb_explore_adf`, `--squarecb`, `--epsilon_decay` → *only contextual/generalising candidate*

Sources: [repo](https://github.com/VowpalWabbit/vowpal_wabbit) · [Python docs](https://vowpalwabbit.org/docs/vowpal_wabbit/python/latest/) · [Bake-off paper](https://arxiv.org/abs/1802.04064)

**Architecture (OBSERVED).** C++ core (`vowpalwabbit/core/src/reductions/`), Python binding `vowpalwabbit.Workspace`. Exploration is a *reduction stack*; `cb_explore_adf` predicts a probability mass function over an action set supplied **per call**, so the available cell set can change every round.
Generalisation: actions can share features (e.g. strategy/instrument/horizon tokens), which lets low-sample cells borrow strength. **My benchmark used only a per-cell id feature** (i.e. no sharing), so it did **not** test this advantage (UNKNOWN benefit).
**Champion/challenger:** `reductions/epsilon_decay.cc` (475 lines) maintains a model set with a confidence-sequence significance test and `min_champ_examples` (OBSERVED source). `--epsilon_decay` ran on 50 updates without error (OBSERVED). Note default schedule `epsilon = init * (t+1)^(-1/3)` (source `decayed_epsilon`) *decays exploration*, which is the opposite of what non-stationarity needs unless `constant_epsilon` is used (INFERENCE).

**Persistence (OBSERVED).** `Workspace.save()` → 1.5 KB model file; reloading with `-i` reproduced the identical pmf on my probe. Binary model, not SQL-inspectable.
**Determinism (PROVEN for tested).** `--random_seed` + own Python RNG: identical selection hash for 3 `PYTHONHASHSEED` values (`eps_default`, `squarecb_constlr`).
**Fail-soft:** not probed exhaustively (UNKNOWN); no NaN test performed.
**Sensitivity (PROVEN in bench):** a single logged update with cost −1, prob 0.5 moved the pmf from uniform to [0.93, 0.03, 0.03] at default learning rate (OBSERVED, first probe) — aggressive; `--power_t 0 --learning_rate` needs tuning (see `03`, the 5 VW settings tried span `regret_all` 2.04–4.26).
**Cost (PROVEN, bench):** 13.2 s per 12,000-pick run vs 0.3–2.7 s for the others (≈5–47×; Python→C++ round-trip per pick with up to 160 action strings, INFERENCE for the cause).
**Tests:** VW's C++/ctest suite **not built** here (only the PyPI wheel was exercised) — UNKNOWN.
**Maintenance (OBSERVED).** 9.11.9 released 2026-09-27 (9.11.8 same day; the changelog says 9.11.9 exists only to republish Java artefacts); 182 commits/365 d but **178 attributed to a single author name** (`git log --format=%an`), 5 names total ⇒ bus-factor risk. Issue page fetch reported "0 open issues" — unreliable/unknown (may be disabled or summariser error).
**Dependencies:** wheel has **0** Python dependencies; 34 MB site-packages. **Licence:** BSD-3 (OBSERVED PyPI; repo LICENSE is a custom BSD text with Microsoft/Yahoo header).

---

## 3. MABWiser — stale control

Sources: [repo](https://github.com/fidelity/mabwiser) · [docs](https://fidelity.github.io/mabwiser/)

**Architecture (OBSERVED, 5,301 lines).** `MAB(arms, learning_policy, neighborhood_policy, seed)`; policies `EpsilonGreedy`, `UCB1`, `ThompsonSampling`, `Softmax`, `Popularity`, `LinGreedy/LinUCB/LinTS`, neighbourhood policies (Radius, KNN, LSH, Clusters, TreeBandit). Batch API: `fit`, `partial_fit`, `predict`, `predict_expectations`, `add_arm`, `remove_arm`, `warm_start`, plus a `Simulator`.
**No forgetting of any kind:** `grep -rn "decay\|discount\|window\|forget" mabwiser/*.py` returned nothing (OBSERVED). Estimates are cumulative sums/counts (`ucb.py`: `arm_to_sum`, `arm_to_count`).
**Cold-start defect for allocation (PROVEN):** `_UCB1` initialises `arm_to_expectation = 0` and only computes an index for arms with `arm_to_count>0`; `predict_expectations()` returns **0 for an untrained or newly `add_arm`-ed arm** (probe output: `{'a':1.55,'b':2.48,'c':0,'d':0}`), so with positive rewards a new cell is ranked **last**. Benchmark: 138/160 cells never selected (`03`).
**Persistence:** pickle round-trip of a Thompson policy gave identical `predict_expectations` (OBSERVED); no SQL state.
**Determinism (PROVEN).** Identical selection hash for 3 `PYTHONHASHSEED` values (UCB1, TS, ε-greedy).
**Fail-soft (OBSERVED).** `predict` before `fit` raises `Exception("Call fit before prediction")`; NaN/None/inf rewards are **rejected explicitly** (`TypeError`) — better input hygiene than River; `fit` with an arm not in the arm list is silently accepted (returns `None`; effect UNKNOWN).
**Tests (OBSERVED, copied `tests/` vs installed wheel, excl. lints/examples).** 533 passed, **1 failed** (`test_ridge.py::test_predict_ridge_scaler`, `TypeError: only 0-dimensional arrays can be converted to Python scalars` — NumPy-scalar-conversion incompatibility with numpy 2.4.6, INFERENCE on cause). Confirms bit-rot against current NumPy in a non-bandit-core path.
**Maintenance (OBSERVED).** Last commit and last release 2.7.4 = **2024-08-30** (760 days before study), 0 commits in 365 d, CHANGELOG last entry "Changed np.Inf to np.inf to fix CI issues".
**Dependencies (OBSERVED).** `numpy, scipy, pandas, scikit-learn, joblib, seaborn` (→ matplotlib etc.): 20 packages, 474 MB site-packages. **Licence:** Apache-2.0 (OBSERVED). Issue page: "0 open issues, 0 PRs" (summariser — treat as UNKNOWN reliability).

---

## 4. Optuna — successive-halving / Hyperband pruners, RDB storage, ask-and-tell

Sources: [repo](https://github.com/optuna/optuna) · [SuccessiveHalvingPruner](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.pruners.SuccessiveHalvingPruner.html) · [RDB recipe](https://optuna.readthedocs.io/en/stable/tutorial/20_recipes/001_rdb.html) · [paper arXiv:1907.10902](https://arxiv.org/abs/1907.10902)

**Architecture (OBSERVED).** `Study` ↔ `Storage` (in-memory, `RDBStorage` via SQLAlchemy, `JournalStorage`, gRPC proxy) ↔ `Sampler` ↔ `Pruner`. Pruners (`optuna/pruners/`): `SuccessiveHalving` (269 lines), `Hyperband` (326), Median, Percentile, Patient, Threshold, Wilcoxon, Nop. `RDBStorage` source contains a **PostgreSQL-specific upsert path** (`storage.py` L806–807 `engine.name == "postgresql"`) — PostgreSQL is a first-class SQL backend (OBSERVED code; production behaviour not tested, UNKNOWN). A heartbeat mechanism marks stale trials failed (`storages/_heartbeat.py`).
**Semantics (OBSERVED source).** `SuccessiveHalvingPruner.prune()` promotes a trial to the next rung only if it is in the top `1/reduction_factor` of *competing values at that rung*; otherwise `raise TrialPruned` → terminal state. Comparison is against other trials' values at the same step, so it is a *relative-rank racing* rule.
**Determinism (PROVEN small case).** Seeded `RandomSampler` + `SuccessiveHalvingPruner(reduction_factor=3)` over 60 trials ran twice → identical trial states/steps (54 pruned/6 complete both times). Seeded TPE not tested (UNKNOWN). An open issue reports "TPESampler RSS grows unbounded with trial count in long-running studies" (#6777, Jul 2026 — DOCUMENTED_CLAIM, WebFetch).
**Fail-soft.** Stale-trial handling exists (heartbeat tests pass); I did not fault-inject (UNKNOWN beyond tests).
**Tests (OBSERVED).** `tests/pruners_tests` + `tests/storages_tests/test_heartbeat.py`: **125 passed** (needed extra `cmaes`, `fakeredis` installed; run from copied tests dir).
**Maintenance (OBSERVED).** 5.0.0 on 2026-09-04 (RC 2026-07-31; 4.9.0 2026-05-28); 1,793 commits/365 d, 430 in 90 d, 102 authors; 9 open issues (WebFetch) — the healthiest project of the set.
**Dependencies (OBSERVED).** `alembic, colorlog, numpy, packaging, sqlalchemy, tqdm, PyYAML` (11 packages, 139 MB); Python ≥3.9. **Licence:** MIT (+ `LICENSE_THIRD_PARTY`).
**Fit caveat.** It optimises *hyper-parameters of one objective*; a "trial" = a config, `report(step)` = one evidence increment. Mapping cells to trials is natural (INFERENCE), but there is no notion of new trials arriving into an existing competition later, of drift, or of "not observed" (a step with no report is just absent).

---

## 5. SMPyBandits — algorithm reference (not a dependency)

Sources: [repo](https://github.com/SMPyBandits/SMPyBandits) · [Garivier & Moulines](https://arxiv.org/abs/0805.3415)

**Content (OBSERVED, `SMPyBandits/Policies/`).** `SlidingWindowUCB.py` (SW-UCB), `DiscountedUCB.py` (D-UCB with the exact-discount `γ^{1+Δ}` trick), `DiscountedThompson.py`, `AdSwitch.py`, `CUSUM_UCB.py`, `Monitored_UCB.py`, `Exp3R/S/++`, `SlidingWindowRestart.py`, `OracleSequentiallyRestartPolicy.py`.
Design property worth copying (OBSERVED code): SW-UCB returns `+inf` for an arm with **no pull inside the window** — an automatic re-exploration/starvation guard.
**Fixed arm set:** constructors take `nbArms` (no dynamic arm add) (OBSERVED).
**Executability (PROVEN failure).** `pip install SMPyBandits` (0.9.7) then `from SMPyBandits.Policies import SWUCB` → `ImportError: cannot import name 'btdtri' from 'scipy.special'` (SciPy 1.17.1) at `Policies/Posterior/Beta.py`. Package metadata still lists Python 2.7/3.4 classifiers and depends on `scikit-optimize` (repo `scikit-optimize` has 1 commit, last 2021-10 — abandoned). **Not benchmarked: execution impossible without patching.**
**Maintenance (OBSERVED).** Last tag 0.9.7 (2019-10-25); 2 commits in 365 d, both community PR merges (June 2026); 27 open issues (WebFetch), the visible ones dated 2019–2022.
**Licence:** MIT.

---

## 6. Metadata-only candidates (not in top 5)

| Project | Evidence gathered (OBSERVED) | Not done |
|---|---|---|
| Ax 1.3.1 | MIT; 747 commits/365 d; `pip install --dry-run` resolves **69 packages incl. torch 2.14.0, triton, ~14 NVIDIA CUDA wheels**; 36 open issues (WebFetch) | no execution, no code review |
| contextualbandits 0.3.30 | BSD-2; 7 commits/365 d, 3 authors; requires `cython` | no execution |
| OSS Vizier 0.1.24 | Apache-2.0; PyPI release 2025-02-01 but 34 commits/365 d at HEAD; deps `grpcio, protobuf, sqlalchemy…` | no execution |
