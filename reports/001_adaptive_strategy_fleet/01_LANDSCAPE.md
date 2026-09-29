# 01 — Landscape (Phase 1) and filter (Phase 2)

All maintenance numbers below were computed from blobless clones made on 2026-09-29 (`git log`, tags) unless stated;
see `05_LICENSE_AND_MAINTENANCE.md` for the full table and caveats. "365d" = commits in the last 365 days before the clone.

## 1. Families of approach (what each answers)

| Question the engine must answer | Family | Canonical technique / source |
|---|---|---|
| Where to spend the next unit of attention? | (Contextual) multi-armed bandits | UCB / Thompson / Exp3 — [Russo et al., Tutorial on Thompson Sampling, arXiv:1707.02038](https://arxiv.org/abs/1707.02038); [Agrawal & Goyal, arXiv:1111.1797](https://arxiv.org/abs/1111.1797); empirical comparison [Bietti et al., A Contextual Bandit Bake-off, arXiv:1802.04064](https://arxiv.org/abs/1802.04064) |
| Evidence gets stale / cells degrade | Non-stationary bandits | Discounted-UCB & Sliding-Window-UCB — [Garivier & Moulines, arXiv:0805.3415](https://arxiv.org/abs/0805.3415); variation-budget regret — [Besbes, Gur, Zeevi, arXiv:1405.3316](https://arxiv.org/abs/1405.3316); [Cheung, Simchi-Levi, Zhu, arXiv:1810.03024](https://arxiv.org/abs/1810.03024); [Adaptive Smooth Non-Stationary Bandits, arXiv:2407.08654](https://arxiv.org/abs/2407.08654) |
| Did the regime change? | Concept-drift detection (+ restart) | ADWIN / Page-Hinkley / KSWIN — implemented in River (`river/drift/`, OBSERVED file list) |
| Which cells deserve *more* evidence vs. be dropped early? | Racing / successive halving | [Hyperband, arXiv:1603.06560](https://arxiv.org/abs/1603.06560); [ASHA, arXiv:1810.05934](https://arxiv.org/abs/1810.05934); irace (iterated F-race, R) |
| Champion/challenger | Confidence-sequence promotion | VW `--epsilon_decay` (OBSERVED source `epsilon_decay.cc`: `min_champ_examples`, significance level, model set) |
| Population/exploit-explore of configs | Population Based Training | [Jaderberg et al., arXiv:1711.09846](https://arxiv.org/abs/1711.09846) (Ray Tune is the main OSS host) |
| Which config to try next inside a cell | Bayesian optimisation / adaptive design | [BoTorch, arXiv:1910.06403](https://arxiv.org/abs/1910.06403) (Ax), [Optuna, arXiv:1907.10902](https://arxiv.org/abs/1907.10902) (TPE) |
| Adaptive experiments under exogenous drift | Adaptive experimentation | [arXiv:2202.09036](https://arxiv.org/abs/2202.09036) |
| Resource-constrained allocation | Bandits with Knapsacks | [Badanidiyuru et al., arXiv:1305.2545](https://arxiv.org/abs/1305.2545) — **capital/budget-flavoured; downgraded** (mission filter) |
| Label/evidence acquisition | Active learning | modAL (uncertainty sampling), stale since 2023 |

Recent (2025–2026) items surfaced by web search — **snippet-level only, not read** (DOCUMENTED_CLAIM at best; treat quality as UNKNOWN):
RAVEN-UCB [arXiv:2506.02933](https://arxiv.org/abs/2506.02933); Bandits for efficient experimentation with episodic drift [arXiv:2606.09802](https://arxiv.org/abs/2606.09802);
Adaptive exploration for latent-state bandits [arXiv:2602.05139](https://arxiv.org/abs/2602.05139);
BANCO drift-aware batched bandits, [ACM WWW 2026](https://dl.acm.org/doi/10.1145/3774904.3792396); Non-stationary bandit convex optimisation [arXiv:2506.02980](https://arxiv.org/abs/2506.02980).
The 14 classic arXiv IDs above were verified against the arXiv API (titles/years match: OBSERVED).

## 2. Candidate table (23 entries)

Legend — Maint: A = active (release ≤ 6 months and multi-author commits), B = slow/single-maintainer, C = stale/abandoned.
Disposition: **F** = finalist (top-5), **D** = downgraded, **R** = rejected at filter.

| # | Candidate | Kind | License (OBSERVED) | Latest release / last commit (OBSERVED) | Maint | Filter outcome and reason |
|---|---|---|---|---|---|---|
| 1 | [River](https://github.com/online-ml/river) `bandit`+`drift`+`stats` | OSS lib, streaming | BSD-3 | 0.26.1 · 2026-08-21 / 2026-09-28 | A | **F** — streaming API, dynamic arm set, pluggable reward statistic, drift detectors; light deps |
| 2 | [Vowpal Wabbit](https://github.com/VowpalWabbit/vowpal_wabbit) `cb_explore_adf` | C++ lib + Python | BSD-3 | 9.11.9 · 2026-09-27 / 2026-09-28 | A/B (see 05: one author dominates) | **F** — only candidate with contextual generalisation across cells + champion/challenger; 0 Python deps |
| 3 | [MABWiser](https://github.com/fidelity/mabwiser) | OSS lib | Apache-2.0 | 2.7.4 · 2024-08-30 / 2024-08-30 | C | **F (kept to test the "popular bandit lib" hypothesis)**; stale ≥2 years — expected downgrade |
| 4 | [Optuna](https://github.com/optuna/optuna) pruners/storage | OSS lib | MIT | 5.0.0 · 2026-09-04 / 2026-09-25 | A | **F** — successive-halving/Hyperband racing, RDB storage incl. PostgreSQL dialect, ask-and-tell |
| 5 | [SMPyBandits](https://github.com/SMPyBandits/SMPyBandits) | research lib | MIT | 0.9.7 · 2019-10-25 / 2026-06-19 (community merge) | C | **F as algorithm reference** — richest non-stationary policy zoo (SW-UCB, D-UCB, discounted TS, AdSwitch, CUSUM-UCB); **import broken** on current SciPy (OBSERVED) |
| 6 | [Ax](https://github.com/facebook/Ax) / BoTorch | OSS platform | MIT | 1.3.1 · 2026-06-09 / 2026-09-21 | A | **D** — active, but solves parameter search (BO), not fleet attention; `pip` resolves 69 packages incl. torch 2.14 + CUDA wheels (OBSERVED dry-run) |
| 7 | [contextualbandits](https://github.com/david-cortes/contextualbandits) | OSS lib | BSD-2 | 0.3.30 · 2026-02-22 (PyPI) / 2026-06-28 | B | **D** — decent but single-author, Cython build dependency, no forgetting; not executed (UNKNOWN behaviour) |
| 8 | [Google OSS Vizier](https://github.com/google/vizier) | service | Apache-2.0 | 0.1.24 · 2025-02-01 / 2026-09-15 | B | **D** — gRPC/protobuf server architecture = excessive infra for the need |
| 9 | Ray Tune (ASHA, PBT) | distributed framework | Apache-2.0 (PyPI) | ray 2.58.0 · 2026-08-23 (PyPI) | A | **D** — PBT is a technique worth knowing; cluster runtime = excessive infra; internals not reviewed (UNKNOWN) |
| 10 | [Nevergrad](https://github.com/facebookresearch/nevergrad) | optimiser lib | MIT | 1.0.12 · 2025-04-23 / 2026-03-16 | B/C | **R** — derivative-free optimisation, not scheduling; 4 commits/365d, one author |
| 11 | [modAL](https://github.com/modAL-python/modAL) | active-learning lib | MIT | 0.4.2 · 2023-06-01 / 2023-06-01 | C | **R** — abandoned; needs a supervised-model framing |
| 12 | [Open Bandit Pipeline](https://github.com/st-tech/zr-obp) | off-policy eval | Apache-2.0 | 0.5.7 · 2023-04-14 / 2022-11-04 | C | **R** — abandoned; OPE not allocation |
| 13 | [scikit-multiflow](https://github.com/scikit-multiflow/scikit-multiflow) | streaming ML | BSD-3 | 0.5.3 · 2020-06-17 / 2020-11-19 | C | **R** — superseded by River |
| 14 | [irace](https://github.com/MLopez-Ibanez/irace) | R racing | GPL (≥2) | v4.5 / 2026-09-15 | A | **D** — racing methodology valuable; R runtime + GPL; not reviewed in depth |
| 15 | [GrowthBook](https://github.com/growthbook/growthbook) | A/B platform | MIT-Expat **plus** proprietary `enterprise` dirs | v5.1.0 · 2026-09-21 / 2026-09-29 | A | **R** — product/web platform; mixed license; infra burden; wrong problem shape |
| 16 | Statsig / Eppo / Optimizely-type experimentation SaaS | SaaS | proprietary | n/a | n/a | **R** — opaque SaaS (mission rule). Individual products **not** examined (UNKNOWN) |
| 17 | Discounted-UCB / Sliding-Window-UCB | technique | paper | 2008 | n/a | **T** — carried into benchmark as *reference implementation written by me* (CUSTOM, labelled `ref_ducb`) |
| 18 | Thompson sampling (+discounted variant) | technique | paper | 2011/2017 | n/a | **T** — via River/MABWiser/SMPyBandits implementations |
| 19 | Successive Halving / Hyperband / ASHA | technique | paper | 2016/2018 | n/a | **T** — via Optuna (reviewed) |
| 20 | Population Based Training | technique | paper | 2017 | n/a | **T/D** — designed for co-evolving NN weights+hyper-parameters; weak fit (INFERENCE) |
| 21 | ADWIN / Page-Hinkley / KSWIN change detection | technique | papers | — | n/a | **T** — via River drift module (source present; not benchmarked) |
| 22 | Bandits with Knapsacks | technique | paper | 2013 | n/a | **R for this use** — budget/capital semantics |
| 23 | Exogenous-nonstationary adaptive experimentation | technique | [arXiv:2202.09036](https://arxiv.org/abs/2202.09036) | 2022 | n/a | **T (read-list)** — not reviewed beyond title/abstract metadata |

## 3. Phase-2 selection: the 5 strongest

Selection criteria: fit to the *attention-allocation* problem, executable reproducibility, licence, maintenance, dependency weight, statefulness.
Stars were **not** used.

1. **River** (bandit + drift + stats primitives)
2. **Vowpal Wabbit** (`cb_explore_adf`, `epsilon_decay`)
3. **MABWiser** — retained deliberately as the "popular, simple bandit library" control, despite the stale flag; the mission asked for a downgrade rationale grounded in code, and this gives it.
4. **Optuna** (successive-halving/Hyperband pruners, RDB storage, ask-tell)
5. **SMPyBandits** — as *algorithm reference* for non-stationary policies (not as dependency)

Runner-ups not selected and why: Ax (dependency weight/problem shape), contextualbandits (single author, no drift handling, unexecuted),
Vizier (server infra), Ray (cluster infra), irace (R+GPL).

Honest observation (INFERENCE from the landscape): **no candidate is a ready-made "research attention scheduler"**. Libraries provide *primitives*
(policies, drift detectors, racing rungs, stores). The benchmark in `03` shows that the behaviours that matter (staleness guard, silent-cell handling,
forgetting with correct effective-sample size) are exactly the ones libraries do **not** provide out of the box.
