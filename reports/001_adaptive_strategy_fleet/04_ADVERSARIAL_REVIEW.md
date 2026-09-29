# 04 — Adversarial review (Phase 5)

Goal: for every finalist, actively argue **against** adoption. Each attack carries an evidence label and a pointer. Severity is my judgement for a *research-only, PostgreSQL-first, PIT/provenance-critical* setting (from `claude.md`).

Attack axes: hidden operational complexity · maintenance risk · pathological behaviour · cold start · starvation · feedback loops · licence · abandoned dependencies · reproducibility · tuning burden.

## 1. River

| # | Attack | Label | Evidence | Severity |
|---|---|---|---|---|
| R1 | **Reward-greedy defaults starve.** UCB-Mean and Thompson leave 31–38/160 cells never pulled and 72–82% stale; established cells silently drop out of attention. | PROVEN | `03` §3; debug run: zero-pull set = established cells | High (this is the core failure the engine must avoid) |
| R2 | **Forgetting estimator ≠ forgetting policy.** Bonus uses cumulative `_n`, `_counts`; `EWMean` + UCB never beats uniform (regret 4.25–4.79 over 9 settings). Users who "just swap the reward object" get a silently broken D-UCB. | PROVEN (behaviour) + OBSERVED (source `ucb.py`) | `03` §4 | High |
| R3 | **NaN poisoning:** one NaN reward ingested → next `pull` raises `IndexError`; failure is deferred and far from the cause. | OBSERVED (single probe, installed 0.26.1) | `bench/failsoft_check.py` | Medium-High (a missing-data bug becomes a crashed scheduler; but wrapper sanitising is trivial) |
| R4 | **Silent cells hijack attention** under forgetting rules (gap waste 0.72). No "attempt without evidence" channel. | PROVEN (scenario) | `03` §3.5 | High for AurumShift (missing evidence ≠ negative evidence) |
| R5 | **Exp3 unusable** with logged history / batched delayed feedback (`KeyError`). | OBSERVED | `results/main/river_exp3.json` | Low-Med (avoidable: don't use Exp3) |
| R6 | **Test suite does not validate allocation quality:** the only behavioural test is skipped as "flaky"; 3 pass/22 skip. | OBSERVED | `tests/bandit/test_policies.py:78` | Medium — we would own the statistical validation |
| R7 | **Opaque persistence:** pickled Python objects (round-trip bit-exact, but not SQL-inspectable; PIT/provenance need columns, not blobs). Thompson blob 122 KB for 30 arms. | OBSERVED + INFERENCE (PIT implication) | `bench/persistence_check.py` | Medium |
| R8 | **Pickle ⇒ version coupling:** restoring across River versions is unverified. | UNKNOWN | — | Medium |
| R9 | **Heavy transitive stack for what we'd use:** numpy≥2.2.5 + scipy≥1.14.1 (256 MB) to use ~200 lines of policy code. | OBSERVED | `03` §6 | Low-Med |
| R10 | **Scope creep pressure:** River is a general online-ML library (432 py files); bandit module is a small corner with a modest test investment. Maintainer attention is elsewhere (open issues: Bayesian LR, FSRS, Rust migration; drift-module "roadmap" issue). | OBSERVED (issue titles, WebFetch) | `02` §1 | Low-Med |
| R11 | Drift detectors present but **no evidence they improve allocation**; not benchmarked. | UNKNOWN | — | — |

Counter-weights (for balance): active (299 commits/365 d, 39 authors), BSD-3, seeded and process-deterministic, dynamic arm list per call, pluggable statistics, clean small API, pickle continuation exact.

## 2. Vowpal Wabbit

| # | Attack | Label | Evidence | Severity |
|---|---|---|---|---|
| V1 | **Bus factor ≈ 1**: 178 of 182 commits in 365 d under one author name. | OBSERVED | `git log --format=%an` | High for a long-lived dependency |
| V2 | **Release churn artefacts:** 9.11.8 and 9.11.9 published the same day; 9.11.9 "identical in content", Java publishing fixes; Windows JAR "never loadable" since 2026-02. Indicates release-engineering fragility (not in the Python path). | OBSERVED (CHANGELOG) | `CHANGELOG.md` | Low for Python-only use |
| V3 | **45×-slower Python loop** than River/MABWiser (13.2 s / 12k picks) due to per-pick ADF example parsing (cause INFERENCE). Irrelevant at small scale; relevant if selection is called per event. | PROVEN (time) | `03` §3 | Low-Med |
| V4 | **Tuning-dominated behaviour:** with the same algorithm family, 5 settings span `regret_all` 2.04–4.26 and Gini 0.33–0.84; default learning rate jumped pmf to 0.93 after one update. | PROVEN + OBSERVED | `03` §3–4 | High per doctrine #9 ("excessive tuning ⇒ reject/park unless benefit exceptional") |
| V5 | **Adaptation weak in tested configs** (degraded cells keep 5–46% attention; improved 3–5%). Default ε-decay schedule shrinks exploration ~t^(−1/3), opposite of what drift requires. | PROVEN (bench) + OBSERVED (source) | `03` §3.3; `epsilon_decay.cc` | High if used naïvely |
| V6 | **Cold-start is exploration-noise-driven** for ε-greedy configs: median 94–101 rounds to first pull of a new cell. `squarecb` 16.8. | PROVEN | `03` §3.2 | Medium |
| V7 | **Not SQL-inspectable binary model**; IPS-style logged probabilities required (we approximated for batches) — misuse silently biases learning. | OBSERVED + INFERENCE | `02` §2 | Medium |
| V8 | **The advantage that would justify VW (feature sharing/contextual generalisation, champion/challenger) was NOT tested.** | UNKNOWN | `03` §7 | — |
| V9 | Extra feature-engineering/format burden ("|A c17" strings); a new concept ("ADF", "reductions") to operate. | INFERENCE | — | Medium (low operator relay preferred) |
| V10 | Open-issues reading ("0") unreliable → cannot assess defect backlog. | UNKNOWN | `05` | — |

## 3. MABWiser

| # | Attack | Label | Evidence | Severity |
|---|---|---|---|---|
| M1 | **Stale:** last commit/release 2024-08-30 (760 days), 0 commits in 365 d. | OBSERVED | `05` | High |
| M2 | **Bit-rot vs current NumPy:** 1 failing test out of 534 with numpy 2.4.6. Unmaintained ⇒ more will follow. | OBSERVED (failure) / INFERENCE (cause, trajectory) | `02` §3 | Medium-High |
| M3 | **Cold-start defect:** untrained/new arm expectation = 0 → new cells ranked last. 139/160 cells never pulled; α ∈ {0.5, 2, 5} does not fix it. | PROVEN | `03` §3.2/§4 | Critical for our use |
| M4 | **No forgetting at all** (grep), so drift/degradation adaptation is structurally absent (58% attention on degraded cells for UCB1). | OBSERVED + PROVEN | `03` §3.3 | High |
| M5 | **Heaviest dependency stack** (20 pkgs, 474 MB: pandas, scikit-learn, seaborn, matplotlib) for a batch-array API. | OBSERVED | `03` §6 | Medium |
| M6 | Batch-array `fit/partial_fit` API recomputes over all arms per call (O(arms)); awkward for event-driven single updates. | OBSERVED (source) + INFERENCE | `ucb.py` `_fit_arm` loop | Low-Med |
| M7 | `fit` with an unknown arm is silently accepted (effect unknown). | OBSERVED / UNKNOWN effect | `bench/failsoft_check.py` | Low-Med |
| M8 | *Positive:* validates NaN/None/inf loudly; deterministic; Apache-2.0. Not enough to offset M1–M4. | OBSERVED / PROVEN | — | — |

## 4. Optuna

| # | Attack | Label | Evidence | Severity |
|---|---|---|---|---|
| O1 | **Pruning is terminal and rank-relative at fixed rungs** — cells judged "bad" are killed; conflicts with "missing evidence is not negative evidence" and with cells that improve later (regime change). | OBSERVED (source semantics) + INFERENCE (conflict) | `_successive_halving.py` `prune()`, `TrialPruned` | High if used as-is |
| O2 | **No notion of a growing competition, drift, or unobserved steps.** Rung statistics are computed over trials that reached the rung; late arrivals compete against a different rung population. | INFERENCE (from source) | — | Medium-High |
| O3 | **Problem-shape mismatch:** optimises hyper-parameters of a single objective; adopting it as a fleet scheduler means bending trial/study/storage schema (study per… ?) — design ambiguity. | INFERENCE | — | Medium |
| O4 | **Storage complexity:** RDB schema (SQLAlchemy/alembic migrations) is Optuna's own — would be a *second* authoritative store next to AurumShift tables ("one authoritative source per concern"). Migration risk across majors (5.0.0 issue: "RDBStorage shifts trial timestamps written before v5.0 by the local UTC offset", #6868). | OBSERVED (issue title via WebFetch) + INFERENCE | `02` §4 | High for provenance |
| O5 | **Long-running memory growth** report: "TPESampler RSS grows unbounded with trial count" (#6777). | DOCUMENTED_CLAIM (issue title) | — | Medium (only if TPE used) |
| O6 | Not benchmarked for allocation; effect of SHA-rung logic on coverage/adaptation UNKNOWN. | UNKNOWN | `03` §7 | — |
| O7 | Dependency stack moderate (11 pkgs); MIT; healthiest maintenance of all candidates (mitigating). | OBSERVED | `05` | — |

## 5. SMPyBandits

| # | Attack | Label | Evidence | Severity |
|---|---|---|---|---|
| S1 | **Does not import on current SciPy** (`btdtri`). | PROVEN | `02` §5 | Disqualifying as a dependency |
| S2 | **Abandoned upstream:** release 2019; classifiers Python 2.7/3.4; depends on abandoned `scikit-optimize` (1 commit, 2021). | OBSERVED | `05` | High |
| S3 | **Fixed `nbArms`; global-step windows** (SW-UCB window is in *steps*, not per-cell time) ⇒ no dynamic arm set, and window/`inf` re-exploration semantics couple all cells. | OBSERVED (source) | `SlidingWindowUCB.py` | Medium |
| S4 | Research-simulator design (Monte-Carlo envs, plotting), heavy for production embedding. | INFERENCE | — | Medium |
| S5 | *Value that remains:* readable reference implementations of D-UCB (γ^{1+Δ} trick), SW-UCB (+inf for absent-in-window arms), discounted Thompson, CUSUM-UCB, AdSwitch, MIT-licensed — reuse as **spec**, not as import. | OBSERVED | `02` §5 | — |

## 6. The pattern the benchmark actually favours (my reference: D-UCB + staleness guard)

This is **my own code** (`ref_ducb*`), included so the adversarial review also attacks the recommended direction (CUSTOM-last doctrine).

| # | Attack | Label | Evidence |
|---|---|---|---|
| P1 | **In-sample tuning.** γ=0.998 and the 200-round guard were chosen *after* seeing results on the same scenario family; out-of-sample robustness unknown. | PROVEN (that it is in-sample) / UNKNOWN (generalisation) | `03` §4 |
| P2 | **γ frontier is real:** coverage/starvation vs adaptation trade-off, zero free lunch except the staleness guard; the guard threshold is another knob. | PROVEN | `03` §4 |
| P3 | **Silent-cell hijack persists for γ ≤ 0.995 even with the guard** (gap waste 0.83–0.89 at those γ; 0.28 at 0.998 with guard). | PROVEN | `03` §3.5, §4 |
| P4 | **Feedback-loop risk in the guard:** a forced revisit of a cell that will *always* return nothing (data gap) consumes attention every S rounds, forever, unless the "no-evidence" outcome is modelled (backoff). Not tested. | INFERENCE / UNKNOWN | — |
| P5 | Reward definition risk: if "reward" is tied to realised performance rather than information value, the scheduler drifts into capital allocation (mission's explicit red line). The abstraction here is information-value-only. | INFERENCE | `00` §1 |
| P6 | Maintenance is ours; ~25 lines but with statistical subtleties (discount clock: per-round vs per-pull vs wall-clock). | INFERENCE | `bench.py` `RefDUCB.update` (discounts once per round) |

## 7. Cross-cutting adversarial conclusions

1. **Every reward-driven allocator in the set exhibits at least one of: starvation of established cells, starvation of new cells, silent-cell hijack, or non-adaptation** (PROVEN, `03`). A wrapper for coverage/staleness/no-evidence semantics is unavoidable whichever library is picked (INFERENCE).
2. **Popularity is not evidence of fitness**: MABWiser is a well-known bandit package and fails cold start by construction (PROVEN).
3. **The tuning burden is real** (doctrine #9): VW and D-UCB behaviour is dominated by 1–2 knobs; River-UCB+EWMean cannot be tuned out of its defect.
4. **Benchmark limits** (single scenario family, Bernoulli, in-sample selection of guard parameters) mean *none* of the quantitative conclusions should be transported to AurumShift data without a replay on the real system.
