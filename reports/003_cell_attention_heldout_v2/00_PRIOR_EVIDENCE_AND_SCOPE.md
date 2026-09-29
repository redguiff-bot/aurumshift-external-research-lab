# 00 — Prior evidence, provenance map and scope

Mission: `EXTERNAL_RESEARCH_CELL_ATTENTION_HELDOUT_BENCHMARK_V2` · date of study: 2026-09-29 · branch `claude/cell-attention-heldout-v2` (base: `claude/kind-bohr-n5e2gl`, V1 head `034d04a`).
Doctrine: `claude.md` of this lab (external research only; no private AurumShift code; no fabricated results).

## 1. Recovery of V1 (verified, not assumed)

```
V1_REPOSITORY=redguiff-bot/aurumshift-external-research-lab
V1_BRANCH=claude/kind-bohr-n5e2gl   (head 034d04a; = refs/pull/2/head, draft PR #2)
V1_REPORTS_FOUND=reports/001_adaptive_strategy_fleet/00..07
V1_REPORT_COUNT=8
V1_BENCH_FOUND=yes — but at reports/001_adaptive_strategy_fleet/bench/ (NOT at repo-root bench/)
V1_RAW_RESULTS_FOUND=yes — results/{main (14 JSON, 20 seeds), sweep (17), determinism (36)} + main_tables.md, sweep_tables.md
```

All eight V1 reports were read. The V1 tree is **read-only prior evidence** here: no V1 file was modified (`git diff 034d04a -- reports/001_adaptive_strategy_fleet` is empty; checked at the end, see 11). V2 code lives in `bench/v2/` at the repo root.

## 2. Provenance map — three strictly separated sources

Every element used by V2 belongs to exactly one of the classes below. Reports never blur them.

### 2.1 V1-DERIVED evidence and semantics (external research, `reports/001_adaptive_strategy_fleet/`)

| Item | Where in V1 | Label in V1 | How V2 uses it |
|---|---|---|---|
| Three-valued attempt outcome `EVIDENCE` / `ATTEMPTED_NO_EVIDENCE` (with bounded backoff) / `NOT_ATTEMPTED`; `ATTEMPTED_NO_EVIDENCE` must map neither to reward 0 nor be dropped | 06 §1 | INFERENCE, motivated by PROVEN silent-cell hijack (03 §3.5) | Environment semantics (all policies); backoff in the shared guard |
| Track `time_since_last_evidence` separately from `time_since_last_attempt` | 06 §1 | INFERENCE | Observable `Ledger` |
| Dynamic cell set (arms appear / disappear) | 06 §1, 03 (late arrivals) | OBSERVED | S1, S10 |
| Forgetting must discount value AND count ("effective sample size") | 04 R2, 06 §1 | PROVEN (behaviour) + OBSERVED (source) | Policy B (discount on both), note on River (see 03) |
| Reason codes `EXPLORE_NEW`, `EXPLOIT_PROMISING`, `REVISIT_STALE`, `RECHECK_DEGRADING`; hard per-cell share cap | 06 §1, §3 | INFERENCE | Counted in policy stats; per-cell cap = 1 attempt / cycle (structural) |
| Staleness-forced revisit guard removes starvation (in-sample) | 03 §4 | PROVEN in-sample, own code; UNKNOWN out-of-sample | Policy B / C2 guard (parameters re-selected on TRAIN, never reused from V1) |
| D-UCB γ frontier (coverage ↔ adaptation) | 03 §4 | PROVEN in-sample | Design motivation of search space for B |
| Metrics: coverage, starvation, staleness, Gini/top-10 % share, adaptation share, gap waste, regret vs oracle | 03 §2 | — | Extended (see 01) |
| Library facts: River `UCB` unseen ⇒ +inf; `EWMean` + UCB uses cumulative counts; no NO-OBSERVATION channel in River/VW/MABWiser; VW single-maintainer, slow; MABWiser cold-start defect | 02, 03, 04 | mixed | Re-checked where they matter (03, 10); V1 numbers are quoted with V1 labels, never upgraded |
| Recommendation of a held-out multi-scenario benchmark; parameters selected on one scenario set and reported on another | 07 §3.2 | INFERENCE | This mission |

V1 pointers relayed by the operator (no ADOPT candidate; reward-following starvation; silent-cell capture under forgetting; MABWiser rejected; River strongest reusable component; D-UCB+guard promising but in-sample; VW feature sharing untested) were **verified against the V1 text**: all are present in V1 (07 §1–§4, 03 §3–§4, 04) with the labels quoted above, with two precisions that matter: (i) V1's "River strongest" is ranked **as a source of primitives/API shape**, while River's shipped policies were REJECTED as allocators; (ii) V1's D-UCB+guard is the reviewer's **own** code with **in-sample** parameters and the guard's no-evidence backoff was **not implemented/tested**.

### 2.2 OPERATOR-SUPPLIED reference contract — Policy A (NOT V1 evidence)

> The external V1 research did not define this policy. Policy A is supplied by the operator from the current private AurumShift research contract and is used only as an external benchmark reference. No private AurumShift source was accessed or claimed.

`POLICY_A = AURUMSHIFT_LIFECYCLE_WEIGHTED_REFERENCE` — classification `OPERATOR_SUPPLIED_REFERENCE_CONTRACT` (not `V1_DERIVED`).
A `grep` for `lifecycle`, `exploration floor`, `LIFECYCLE_WEIGHTED` over all V1 reports, V1 bench code and the sibling study 002 branch returned **zero** matches (verified, OBSERVED).
Contract as received: states `EXPLORATION / PROMISING / PROVEN / DEGRADING / RETIRED`; `RETIRED` ⇒ ineligible, attention 0; missing/stale evidence never makes a cell ineligible; weights `1.50 / 1.00 / 0.75 / 0.50 / 0.00`; `share_i = remaining_budget · w_i / Σ w_j`; exploration floor ratio `0.05`, distributed uniformly across exploration-marked eligible cells (no evidence yet, stale beyond the scenario freshness threshold, `data_gap`, `pit_unverified`), returned to the main budget when none; `final = floor_share + weighted_share`; `Σ final == total_budget`, no negative allocation; deterministic. **Fixed — weights and floor ratio are never tuned.**

### 2.3 NEW V2 experimental definitions (this study)

Everything else: the synthetic scenario families S1–S10 and the dev scenarios; the observable `Ledger`; the **evidence-derived lifecycle classifier** that feeds Policy A (the operator contract defines the states and weights but not how a cell's state is inferred from evidence — see 01 §5, a major, explicit source of uncertainty for A); the realisation of A's fractional shares as discrete attempts (credit accumulation); Policies B, C, C2, D as parameterised here; metrics definitions; the tuning objective; the statistical protocol. These are labelled **V2-DEFINED** and are the study's own choices; they are not claims about V1 or about private AurumShift.

## 3. Scope and boundaries

* External synthetic benchmark. Nothing here says a policy is compatible with, or should be integrated into, private AurumShift. `ADOPT_REFERENCE` (11) means *"strong external reference policy for future local evaluation"* only.
* The benchmark ranks **policy behaviour under this experimental model**, never libraries. Library quality (maintenance, licence, cost) is reported separately (10).
* No financial reward. The information metric is scenario-defined and independent of PnL.

## 4. Evidence labels

`PROVEN` (reproducible check in `bench/v2/results`, falsifiable) · `OBSERVED` (directly seen, not a general guarantee) · `DOCUMENTED_CLAIM` · `INFERENCE` · `UNKNOWN`. A synthetic OBSERVED/PROVEN-in-benchmark result is never promoted to a general PROVEN claim: every result label below carries the qualifier "in this experimental model" implicitly and states it where it matters.

## 5. Report map

`01` design · `02` scenario generator · `03` policy implementations · `04` train/validation selection · `05` held-out results · `06` pathology tests · `07` parameter sensitivity · `08` statistics · `09` adversarial review · `10` maintenance/licence refresh · `11` final adjudication.
