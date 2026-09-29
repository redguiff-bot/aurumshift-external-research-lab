# 07 — Final adjudication (external, generic)

Boundary reminder (`claude.md`): these are **ADOPT / ADAPT / PARK / REJECT candidates from external evidence only**. Nothing here asserts compatibility with private AurumShift code; final integration adjudication happens later against the real repository. No integration was built.

## 1. Headline findings

1. **No external project is a ready-made research-attention scheduler.** Libraries provide primitives (policies, estimators, drift detectors, racing rungs, stores). The behaviours that decide success here — staleness guard, treatment of "attempted, no evidence", forgetting that discounts *both* value and count — are not offered by any reviewed library. (OBSERVED across five source reviews; INFERENCE as the general statement.)
2. **Reward-greedy allocation starves.** The best-regret rules left ≈20–24% of cells untouched and 72–82% stale (PROVEN, `03` §3). Established cells silently fall out of attention as easily as new ones are ignored.
3. **Silent cells hijack attention** under forgetting/UCB rules when the policy learns only from observed evidence (72–89% of gap-window attention, PROVEN in this scenario) — a direct hit on "missing evidence is not negative evidence".
4. **A monotone design frontier exists** (discount γ: coverage ↔ adaptation) and a **staleness-forced revisit** removed starvation at equal regret in-sample (`ref_ducb_fresh` γ=0.998: 0 zero-pull cells, 85% attention to improved cells, regret 1.72 vs round-robin 4.51). This is my own reference code with in-sample parameters — direction, not a result to transport (`04` §6).
5. **Popular ≠ fit:** MABWiser fails cold start by construction (PROVEN) and is stale; SMPyBandits (best algorithm zoo) does not import on current SciPy (PROVEN).
6. **All tested policies are deterministic** across processes and `PYTHONHASHSEED` (PROVEN); River pickle continuation is exact (PROVEN). Determinism is not a differentiator; state *inspectability* is.

## 2. Ranking of the five finalists (for this problem shape)

| Rank | Candidate | Role | One-line reason |
|---|---|---|---|
| 1 | **River** (`stats`, `utils`, per-call-arm `Policy` shape, `drift`) | Primitives + API shape | Active, BSD-3, light deps, dynamic arm list, seeded; but its ready policies starve and UCB+forgetting is mis-specified |
| 2 | **Vowpal Wabbit** | Contextual generalisation / champion-challenger (conditional) | Unique capability, 0 Python deps; single-maintainer, tuning-dominated, slowest, its advantage untested here |
| 3 | **Optuna** | Racing-rung *logic* and stale-worker heartbeat *idea* | Healthiest project; terminal pruning and its own RDB schema conflict with our constraints |
| 4 | **SMPyBandits** | Executable specification of non-stationary algorithms | Best algorithm coverage; unrunnable and abandoned |
| 5 | **MABWiser** | none | Stale, no forgetting, cold-start defect, heaviest deps |

## 3. Classification

Definitions — **ADOPT**: use as-is behind a thin wrapper. **ADAPT**: reuse code/ideas with modification. **PARK**: promising, evidence insufficient or not needed yet; revisit on a stated trigger. **REJECT**: do not pursue for this problem.
"Confidence" is my confidence in the *classification* given the evidence (High/Med/Low).

### 3.1 Components and approaches

| Component / approach | Class | Confidence | Evidence and rationale | Revisit trigger / condition |
|---|---|---|---|---|
| **ADOPT — none as a whole system** | — | High | Finding #1. Nothing reviewed satisfies starvation + silent-cell + drift requirements out of the box. | — |
| River `stats.*` (Mean, EWMean, Var) and `utils.Rolling` as estimator building blocks | **ADAPT** | Med | OBSERVED source; BSD-3; light; but forgetting must be paired with discounted counts (R2) | Confirm on real evidence latency |
| River per-call-arm-list `Policy` shape (`pull(available)`, `update`, seeded RNG, `clone`) | **ADAPT** (as API pattern) | Med | dynamic arm set worked (late arrivals) in `03`; seed-deterministic (PROVEN) | — |
| River `bandit.UCB / ThompsonSampling / EpsilonGreedy / BayesUCB` as the allocator as shipped | **REJECT** (as shipped) | High | starvation and non-adaptation PROVEN (`03`) | — |
| River `bandit.Exp3` | **REJECT** | High | crashed on history/batch feedback (OBSERVED `KeyError`) | — |
| River `drift.ADWIN / PageHinkley / KSWIN` as degradation/regime-change signals feeding restarts | **PARK** | Low-Med | present in source (OBSERVED); **effect on allocation UNKNOWN**; River's own issue tracker lists a detector-evaluation harness as future work | first follow-up experiment: restart-on-drift vs D-UCB on scenario v2 |
| VW `cb_explore_adf` / `--squarecb` | **PARK** | Med | only zero-starvation external rule in the bench (squarecb) but tuning-dominated, slow, single-maintainer; **feature sharing untested** | cells share meaningful features **and** per-cell samples are too sparse for independent estimates |
| VW `--epsilon_decay` champion/challenger | **PARK** | Low | mechanism exists (OBSERVED source); default schedule decays exploration; not benchmarked | need for statistically-gated promotion of alternative configurations |
| MABWiser (any policy) | **REJECT** | High | stale 760 days; PROVEN cold-start starvation; no forgetting; 1 test failing on current NumPy; 474 MB deps | — |
| Optuna as the attention scheduler | **REJECT** | Med | problem-shape mismatch, terminal pruning (O1/O2), second authoritative store (O4) | — |
| Optuna successive-halving/ASHA **rung logic** reinterpreted as non-terminal "attention tiers" | **ADAPT** (idea only) | Low-Med | source-level semantics read; determinism of seeded study PROVEN; **allocation effect UNKNOWN** | test as tiered promotion/demotion in scenario v2 |
| Optuna heartbeat / stale-trial concept (worker liveness → mark stale) | **ADAPT** (idea only) | Low | OBSERVED code+125 tests | if evidence collection runs in unreliable workers |
| Optuna as *hyper-parameter search inside a cell* (its actual purpose) | **PARK** | Med | out of scope of this mission; MIT, healthy | when per-cell config search becomes a need |
| Optuna `RDBStorage`/PostgreSQL schema | **REJECT** (as second store) | Med | own schema/alembic; timestamp-migration issue #6868 | — |
| SMPyBandits package | **REJECT** (as dependency) | High | import failure PROVEN; abandoned | — |
| SMPyBandits algorithms (D-UCB, SW-UCB, discounted Thompson, CUSUM-UCB, AdSwitch) as **specification** | **ADAPT** | Med-High | readable MIT reference code; D-UCB and its paper are the design the benchmark favoured | — |
| Discounted-UCB (arXiv:0805.3415) with discounted count **and** value | **ADAPT** | Med | `ref_ducb` (my code): frontier behaviour PROVEN in-sample | validate out-of-sample, other scenario families |
| Sliding-window UCB (+inf for arms absent in window) | **ADAPT** | Low-Med | code read; property is a built-in re-exploration guard; not benchmarked | compare with staleness guard |
| **Staleness-forced revisit + explicit `ATTEMPTED_NO_EVIDENCE` channel with bounded backoff** | **ADAPT / small custom** (CUSTOM-last, but no reuse option exists) | Med | staleness guard PROVEN in-sample; no-evidence channel motivated by PROVEN hijack; backoff untested | design and test backoff before anything else |
| Discounted Thompson sampling | **PARK** | Low | only implementation found is unrunnable; not tested | if probabilistic exploration is preferred over UCB determinism |
| Successive Halving / Hyperband as *terminal* pruning of cells | **REJECT** | Med | contradicts "missing evidence is not negative evidence" (INFERENCE) | — |
| Population Based Training | **PARK** | Low | weight-copying/co-evolution design; weak fit (INFERENCE); Ray infra | only if configurations (not cells) need evolving |
| Ax / BoTorch | **PARK** | Med | different problem (BO); 69-pkg closure incl. torch/CUDA (OBSERVED) | config search with expensive evaluations |
| contextualbandits | **PARK** | Low | BSD-2, single-author, unexecuted | if a contextual library with bootstrap-TS is needed and VW is refused |
| Google OSS Vizier | **REJECT** | Med | server/gRPC infra ≫ need; stale PyPI channel | — |
| Ray Tune | **REJECT** (infra) / PBT technique **PARK** | Med | cluster runtime; not code-reviewed (UNKNOWN internals) | — |
| irace (racing methodology, R, GPL) | **PARK** | Low | methodology relevant; GPL + R runtime; not reviewed in depth | if a racing design is needed and legal accepts process-level use |
| Nevergrad, modAL, Open Bandit Pipeline, scikit-multiflow | **REJECT** | High | dormant/abandoned or wrong problem (OBSERVED dates) | — |
| GrowthBook and experimentation SaaS (Statsig/Eppo/Optimizely-type) | **REJECT** | High (GrowthBook) / Low (SaaS: products unexamined) | platform infra; mixed licence (OBSERVED); SaaS opaque by mission rule | — |
| Bandits with Knapsacks & capital-flavoured methods | **REJECT** (for this use) | High | red line: research scheduler ≠ capital allocator | — |
| Active learning (uncertainty sampling, modAL-style) | **PARK** | Low | conceptually relevant to "which cell gives most information"; no maintained candidate; not tested | if information-gain estimates per cell become available |

### 3.2 What the classification adds up to (INFERENCE)

* **Composition, not adoption.** The evidence supports COMPOSE/ADAPT: a thin, PostgreSQL-inspectable allocator whose *design* borrows (a) River's per-call-arm/seeded API shape and estimators, (b) D-UCB/SW-UCB from the literature (SMPyBandits as spec), (c) a staleness guard and an explicit no-evidence channel, with (d) drift detectors and racing tiers as *later, measured* additions. That is a small **CUSTOM** core justified by findings #1–#4, in the doctrine's "CUSTOM LAST" position — arrived at only after five reviews found no reuse path for those behaviours.
* **Cheapest high-value next step**: extend the benchmark (scenario v2) before any integration: multiple held-out scenario families (heavy-tailed rewards, correlated cells, varying gap lengths incl. permanent silence, delayed feedback), a no-evidence backoff rule, drift-detector restarts, Optuna-style non-terminal tiers, VW with shared features. Parameters must be selected on one set of scenarios and reported on another.

## 4. Confidence and what would change these conclusions

| Conclusion | Confidence | Would be overturned by |
|---|---|---|
| Reward-greedy library policies starve in fleet-like settings | High (PROVEN here, 20 seeds, robust across 9+ settings) for *this* scenario family; Med for real data | Real evidence-latency/reward structure very different from Bernoulli-stationary-noise |
| MABWiser / SMPyBandits should not be dependencies | High | Upstream revival + fixes |
| River is the best *source of primitives* | Med | A benchmark showing its drift detectors are useless, or a Rust/Python-version constraint in the real system |
| VW deserves PARK not REJECT | Low-Med (its advantage untested) | Feature-sharing experiment |
| Staleness guard + discounting is the right *direction* | Med-Low (in-sample, my own code) | Held-out scenarios where the guard wastes attention (no-evidence loops) |

## 5. Unknowns that remain (explicit)

VW C++ test suite (not built) · River drift/AMF effects on allocation · Optuna behaviour with shared PostgreSQL under concurrency · cross-machine determinism · behaviour beyond 160 cells · Ray internals · SaaS products individually · real open-issue backlogs (WebFetch summaries only; VW/MABWiser "0" unreliable) · Ax/contextualbandits/Vizier runtime behaviour · 2025–2026 papers read only at snippet level.

## 6. Artefact index

`00_RESEARCH_SCOPE.md` · `01_LANDSCAPE.md` · `02_TOP5_DEEP_DIVE.md` · `03_REPRODUCTION_AND_BENCHMARK.md` · `04_ADVERSARIAL_REVIEW.md` · `05_LICENSE_AND_MAINTENANCE.md` · `06_INTEGRATION_SURFACE.md` · this file · `bench/` (`bench.py`, `analyze.py`, `persistence_check.py`, `failsoft_check.py`, `requirements-observed.txt`, `results/{main,sweep,determinism}/*.json`, generated `*_tables.md`).

**Stopped here as instructed: no AurumShift integration was implemented.**
