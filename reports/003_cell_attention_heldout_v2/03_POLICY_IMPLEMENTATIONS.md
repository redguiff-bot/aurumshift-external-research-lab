# 03 — Policy implementations

Code: `bench/v2/src/policies.py` (versioned via git; policy A carries `POLICY_A_VERSION = "A-ref-1.0.0"`). Interface: `select(t, ledger) → K distinct eligible cells`; `observe(t, typed_events, ledger)`. No policy sees ground truth. Environment/ledger semantics: 01 §1.

Environment: Python 3.11.15 · numpy 2.4.6 · scipy 1.17.1 · **river 0.26.1** (git HEAD `03b4818`, 2026-09-28) · **vowpalwabbit 9.11.9** (git HEAD `00196b3`, 2026-09-28) · narwhals 2.26.0 · pytest 9.1.1 — isolated venv, install commands and `pip freeze` in `bench/v2/environment/`. Same River/VW versions as V1 (V1: river 0.26.1, vowpalwabbit 9.11.9).

## A — `AURUMSHIFT_LIFECYCLE_WEIGHTED_REFERENCE` (operator-supplied, FIXED)

Source: `OPERATOR_SUPPLIED_REFERENCE_CONTRACT`, **not V1-derived** (00 §2.2). The V1 research did not define this policy; A is used only as an external benchmark reference; no private AurumShift source was accessed.

| Element | Implementation |
|---|---|
| States | `EXPLORATION, PROMISING, PROVEN, DEGRADING, RETIRED`; `RETIRED` ⇒ not eligible (the scenario removes the cell from the eligible set), all others eligible; stale/missing evidence never removes eligibility |
| Weights (fixed) | `1.50 / 1.00 / 0.75 / 0.50 / 0.00` |
| Floor (fixed) | ratio `0.05`; exploration marks: `no evidence yet` \| `stale (> FRESH=60 cycles since last evidence)` \| `data_gap` (last attempt(s) returned no evidence) \| `pit_unverified`; `floor_budget = K·0.05` split uniformly across marked cells; **returned to the main budget when none is marked**; marked cells also keep their weighted share |
| Allocation | `final_i = floor_i + (K − floor_distributed)·w_i/Σw` ⇒ `Σ final = K`, `final ≥ 0` (asserted every cycle; max error logged in `policy_stats.max_conservation_error`) |
| Determinism | no randomness; ties by cell id |
| Semantics | `ATTEMPTED_NO_EVIDENCE` and staleness never change a lifecycle state (unit-tested); they only raise the exploration mark |
| Logs | floor units per exploration bitmask (`1 no_evidence, 2 stale, 4 data_gap, 8 pit`) and weighted units per lifecycle state — reasons are **not merged** |
| V2-defined parts | evidence-derived state classifier (01 §5) and discrete realisation by credit accumulation (01 §5). Both fixed and non-tuned; classifier variant `A_altcls`, floor 0/0.10/0.20 and flat/steep weights appear only as **descriptive sensitivity** (07). Primary comparison uses exactly the operator constants. |

## B — D-UCB + staleness guard (+ bounded no-evidence backoff)

CUSTOM reference implementation (V1 doctrine: "CUSTOM last, but no reuse option exists", 07 §3.1). Index: `X_c/N_c + 0.5·sqrt(2·ln(ΣN)/N_c)`, `N,X` both multiplied by `γ` **every cycle** (discount on value **and** count — V1 06 §1); unseen ⇒ `+∞`. **Guard** (specified before, and independently of, any held-out result): a cell whose `time_since_last_attempt` exceeds `S·min(2^k, M)` (`k` = consecutive no-evidence outcomes; `M=1` disables backoff) is *forced*; forced cells are served most-overdue first, at most `K/2` per cycle; while a cell with `k ≥ 1` is within its backoff window it is excluded from the UCB path (this is the V1-untested "bounded backoff", V1 04 P4). `ATTEMPTED_NO_EVIDENCE` updates neither `N` nor `X`. Reason codes counted: `REVISIT_STALE`, `EXPLORE_NEW` (unseen), `EXPLOIT_PROMISING`. Search space and choice: 04.

## C — River (as shipped) + hygiene wrapper; C2 = River + the same guard

Uses **River's own classes, unmodified**: `river.bandit.EpsilonGreedy(epsilon, reward_obj=river.stats.EWMean(fading_factor), seed)`, `river.bandit.UCB(delta, reward_obj=EWMean|Mean, seed)`; policy object API `pull(arm_ids)` (one arm per call; K distinct picks by removing the pulled arm and pulling again — same approach as V1) and `update(arm_id, reward)`. `EWMean.fading_factor` is the weight of the **new** observation (River docs: "closer to 1 ⇒ adapts more to recent values"; verified in the docstring of 0.26.1).

Wrapper (our code, ~25 lines, all logic that River cannot express):
* **arm lifecycle** — the arm list passed to `pull` is the announced eligible set; retired cells simply disappear (River keeps their state, unused); cells returning after silence keep their River state (no reset).
* **new-arm behaviour (River-native)** — `UCB`: unseen arm ⇒ `+inf` (`ucb.py`, V1 02 §1); `EpsilonGreedy`: unseen arms have reward estimate 0 and are reached only through ε-exploration (`max(arm_ids, key=…)` breaks ties by list order — cells are passed in ascending id order).
* **forgotten/stale arms** — River has none: `EWMean` fades on update only (no time decay), counts are cumulative. There is no staleness notion in River; it is **not expressible** without custom logic — in `C` we add nothing, in `C2` we add the shared guard.
* **NO_OBSERVATION** — River has no channel for it (V1 04 R4). The wrapper calls `update` **only** for `EVIDENCE` (value finite, clipped to [0,1]); `ATTEMPTED_NO_EVIDENCE` is neither `0` nor propagated (asserted: `river._n == #EVIDENCE events`).
* **hygiene** — non-finite values dropped and counted (V1 R3: one NaN poisons `UCB`).
Verdict on expressibility: the invariants "no starvation", "no silent-cell capture", "staleness" cannot be expressed with River alone; they need the guard (custom) — reported, not hidden.
Thompson sampling / Exp3 are not run: the value is not binary (Beta needs {0,1}), Exp3 crashed in V1 on batch feedback (V1 02 §1).

## D — Vowpal Wabbit `--cb_explore_adf` with shared observable features

Validity assessment (mission §7): a credible, leak-free feature-sharing formulation **exists**, so D is executed (not `NOT_EXECUTED_FOR_VALIDITY`). Actions are the eligible cells; each action is described **only** by features computed from the observable ledger and by the static generic `group` descriptor: bucketed `n_evidence`, age since last evidence, age since last attempt, `data_gap` flag (+ consecutive-no-evidence count), `pit_unverified`, bucketed slow mean, bucketed trend (`fast − slow`), plus numeric slow/fast means and `group`. **No cell-id feature** (that would be V1's non-sharing formulation) and **no** ground truth, no future, no change point, no `mag`/`rare` labels. Cost of an attempt = `−value` with the logged probability of the sequential draw without replacement (approximate IPS, as in V1; exact during the common uniform burn-in). `ATTEMPTED_NO_EVIDENCE` produces **no `learn` call** (asserted: `learn_calls == #EVIDENCE events`). Consequence acknowledged: with no label the model never learns anything about `data_gap` states — its behaviour there is decided by initialisation and exploration, which is precisely what the silent-cell tests probe.
Determinism: `--random_seed` + own `random.Random(seed)`.
Limitation: group information is generic metadata shared with all policies but only D uses it; in S2 the change is group-structured (D can in principle exploit it) while S3 is not (it cannot) — the S-families thereby test D's sharing both where it should and should not help. This is a V2 design decision, not a leak: group→dynamics can only be discovered from observations.

## R — Round-robin (reference frame, not a contender)

Least-recently-attempted first, ties by id. Included to give every metric a frame (uniform allocation).

## Selected parameters (frozen before held-out; see 04 for the full search)

PLACEHOLDER_SELECTED
