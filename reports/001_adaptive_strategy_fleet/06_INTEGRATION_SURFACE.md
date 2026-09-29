# 06 — Generic integration surface

**Scope guard.** This file describes the *shape* of an integration boundary implied by the general constraints in `claude.md` and by what the benchmark exposed.
It makes **no claim** about AurumShift's actual schema, modules, scheduler, language versions or deployment, none of which were visible. No integration was implemented.
All items are INFERENCE unless a label says otherwise. Final adjudication must be done against the real local repository.

## 1. Minimal contract any allocator needs (derived from the failures observed)

| Concern | What the benchmark showed | Consequence for the boundary |
|---|---|---|
| **Three-valued outcome per attempt** | Silent cells hijacked attention (gap waste up to 0.89, PROVEN) because "pulled, nothing came back" changes no state | The scheduler input must distinguish `EVIDENCE(value)` / `ATTEMPTED_NO_EVIDENCE` / `NOT_ATTEMPTED`, and `ATTEMPTED_NO_EVIDENCE` must **not** be mapped to reward 0 (that would be negative evidence) nor dropped (that creates the loop). It needs its own bounded-backoff rule. None of River/MABWiser/VW has this channel (OBSERVED). |
| **Staleness as first-class state** | Reward-greedy rules left 72–82% of cells stale (PROVEN); a staleness-forced revisit removed starvation at equal regret (PROVEN in-sample) | Track "time since last *evidence*" per cell separately from "time since last *attempt*". |
| **Dynamic cell set** | Cells appear/disappear (late arrivals in the benchmark) | Selection must accept the current eligible set per call (River does; MABWiser needs `add_arm`; SMPyBandits fixed). |
| **Effective sample size under forgetting** | River UCB+EWMean ≠ D-UCB (PROVEN) | Any forgetting must discount **both** value and count. |
| **Input hygiene** | River UCB poisoned by one NaN (OBSERVED); MABWiser rejects NaN loudly | Validate/sanitise at the boundary; never let a NaN reach a policy object. |
| **Determinism** | All tested policies were seed- and `PYTHONHASHSEED`-deterministic (PROVEN) | Persist seed + RNG position (or a counter-based RNG) so a decision can be replayed. |
| **Batch + delayed feedback** | Exp3 failed on it; others fine | Selection API must allow picking K distinct cells before any feedback returns. |
| **Explainability** | Operators need "why this cell" | Return a reason code per pick (e.g., `EXPLORE_NEW`, `EXPLOIT_PROMISING`, `REVISIT_STALE`, `RECHECK_DEGRADING`). |

## 2. State and persistence (PostgreSQL-first, PIT/provenance) — requirements, not a design

* Per-cell state that is **relationally inspectable**: counts, discounted sums, last-evidence time, last-attempt time, consecutive no-evidence attempts, current status. Opaque blobs (River/MABWiser pickle, VW binary model, Optuna's own RDB schema) would be a *second* authority next to the system's own tables — against "one authoritative source per concern" (INFERENCE).
  Pickle continuation was bit-exact for River in my test (PROVEN), so blobs are usable as a *cache*, not as the record.
* **Decision log** (append-only): as-of timestamp, eligible set, chosen set, reason codes, policy version, seed/RNG position, input snapshot reference. Needed for PIT/no-lookahead audits (INFERENCE from `claude.md`).
* **No lookahead**: the allocator may only see evidence with `available_at ≤ decision_time`; a feedback sink that back-fills rewards must write with their own availability time. (Requirement statement; nothing here tests it.)

## 3. The "not a capital allocator" boundary

* The scheduler's reward is an **information-value signal** (e.g., evidence gain, uncertainty reduction, promise of a hypothesis), never P&L, position size or risk budget. In the benchmark reward was Bernoulli information value; nothing financial was modelled.
* Bandits-with-Knapsacks and Kelly-style techniques were deliberately **excluded** ([arXiv:1305.2545](https://arxiv.org/abs/1305.2545) is resource/budget-constrained).
* Output is a *ranking of research attention*, with a hard cap on share per cell/group to bound concentration (Gini/top-10% share measured in `03` are candidate monitoring metrics).

## 4. Candidate-by-candidate surface (what could plug in where)

| Candidate | Natural role (if any) | API surface it offers (OBSERVED) | Gaps to wrap |
|---|---|---|---|
| River `bandit.*` | Reference policy objects; per-call arm list; seeded RNG | `pull(arm_ids)`, `update(arm, reward)`, `reward_obj` plug-in, `clone()`, pickle | third outcome, staleness, effective-n forgetting, NaN guard, SQL state, reason codes |
| River `stats` / `utils.Rolling` / `drift.*` | Streaming statistics and change detectors as *signals* feeding an allocator (drift-aware restart) | `stats.EWMean/Mean/Var…`, `drift.ADWIN/PageHinkley/KSWIN` | effect on allocation unmeasured (UNKNOWN) |
| VW `cb_explore_adf` | Contextual generalisation across cells that share features; champion/challenger via `--epsilon_decay` | `Workspace.predict/learn/save`, per-call action set, seed flag | tuning, IPS-probability bookkeeping, binary state, speed; benefit untested |
| MABWiser | none recommended | `MAB.fit/partial_fit/predict_expectations/add_arm/remove_arm/warm_start` | cold-start defect, no forgetting, stale |
| Optuna | Rung/racing *logic*; ask-and-tell pattern; heartbeat idea for stale workers | `Study.ask/tell`, `Trial.report/should_prune`, `RDBStorage(PostgreSQL)`, `heartbeat` | terminal pruning, second schema, no drift/late arrivals |
| SMPyBandits | Executable-spec for D-UCB / SW-UCB / discounted TS / CUSUM-UCB / AdSwitch | Python classes `getReward/choice` | not importable; fixed arms |
| Own thin scheduler (`ref_ducb_fresh`-style) | The behaviours that mattered: discount both value and count, stale-forced revisit, explicit no-evidence path | ~25 lines NumPy in `bench.py` | in-sample parameters; backoff for no-evidence cells not implemented/tested |

## 5. Open questions that only the real repository can answer (UNKNOWN here)

1. What is the actual reward/promise signal and its latency distribution? (drives discount and batch design)
2. How many cells at peak and how often is selection invoked? (O(arms) selection is fine at 10²–10⁴, untested beyond 160.)
3. Is there an existing authoritative record of evidence sufficiency per cell that the allocator must *read* instead of re-deriving?
4. Which runtime constraints (Python version, native wheels, offline/air-gapped installs) apply? (River needs Python ≥3.11 and NumPy ≥2.2.5; VW needs a platform wheel.)
5. What determinism guarantees are required across machines/BLAS versions? (only same-machine tested)
