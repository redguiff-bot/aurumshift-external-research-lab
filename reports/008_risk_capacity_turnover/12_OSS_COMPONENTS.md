# 12 — OSS / reference components

Method: **OBSERVED** metadata queried from the PyPI JSON API on the study date (version, licence field, release date, requires-python); **no source inspection, install or benchmarking was performed** except `scipy.optimize.linear_sum_assignment` (executed: 500/500 random assignment-vs-top-f checks matched). Licences are as declared on PyPI (may be incomplete). Maintenance evidence from PyPI release dates only — GitHub activity, open issues and code quality are **UNKNOWN** here. Stars were not used. No drop-in allocator/scheduler was sought or found.

| component | need | PyPI observed (version · licence field · last upload · py) | classification | rationale |
|---|---|---|---|---|
| scipy (`linear_sum_assignment`, `milp`) | online/batch assignment, small MILP | 1.18.1 · BSD-style · 2026-08-21 · >=3.12 | **ADOPT_REFERENCE** | Assignment with slot-independent weights ≡ top-f (PROVEN, OBSERVED 500/500); only needed if slot-specific/pairwise terms appear |
| OR-Tools | knapsack / assignment / CP-SAT | 9.15.6755 · Apache 2.0 · 2026-01-14 | PARK | exact joint selection not needed while greedy is within noise; heavy dependency |
| PuLP / HiGHS (highspy) | ILP with pairwise risk terms | PuLP 4.0.0 MIT 2026-09-25; highspy 1.15.1 MIT 2026-07-02 | PARK | same reason; HiGHS is the light option if needed |
| cvxpy | convex portfolio-constrained selection | 1.9.3 · Apache-2.0 · 2026-09-19 | PARK | relaxations of selection; no evidence penalties matter (07) |
| PyPortfolioOpt / Riskfolio-lib / skfolio | portfolio allocation | 1.6.0 MIT / 7.3.0 BSD / 1.4.9 BSD | **REJECT** for slot admission; PARK for portfolio-level sizing | they produce weights, not admit/reject; the marginal-concentration idea was re-implemented in 15 lines |
| MABWiser | contextual bandits (LinTS/LinUCB/…) | 2.7.4 · licence field empty · 2024-08-30 | **ADAPT_CANDIDATE** (only if bandit path is pursued) | clean API for LinTS/LinUCB; last upload >2 years before study date (maintenance risk, UNKNOWN); delayed/censored feedback must be handled by caller |
| contextualbandits | offline/online contextual bandits | 0.3.30 · licence field empty · 2026-02-22 | PARK | not needed; LinTS ties SLOTHOUR |
| Vowpal Wabbit | scalable contextual bandits | 9.11.9 BSD-3 2026-09-27 | REJECT | operational complexity ≫ benefit at 1–2 decisions/hour |
| Open Bandit Pipeline | off-policy evaluation | 0.5.7 Apache 2023-04-14 | PARK | relevant for *future local* off-policy evaluation of logged admissions; stale (2023) |
| river | online learning (shrinkage/EWMA/Bayesian) | 0.26.1 BSD-3 2026-08-21 | PARK | streaming statistics for score-pooling; EWMA suffices |
| SimPy / ciw | queueing / discrete-event simulation | SimPy 4.1.2 MIT 2026-05-24; ciw 3.2.7 2025-12-05 | PARK | custom step simulator was simpler; useful for local replay harness |

Custom code written (CUSTOM LAST justified): the world generator, the step simulator and the 13 policies (≈600 lines) because no library models one-position-per-instrument slot economics with censored delayed feedback and public/hidden separation.

Classification vocabulary requested by the mission: ADOPT_REFERENCE = use as a reference implementation/test oracle; ADAPT_CANDIDATE = worth adapting if the path is pursued; PARK; REJECT.
