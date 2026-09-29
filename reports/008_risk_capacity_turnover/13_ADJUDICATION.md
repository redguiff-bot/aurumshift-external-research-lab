# 13 — Adjudication

## Core question
> When capacity is scarce, how should a research/PAPER engine decide which opportunities deserve scarce slots without lookahead, overfitting or hidden capital assumptions?

**Answer supported by this synthetic study (OBSERVED, not transferable without local evidence):**
1. Do not allocate scarce slots by arrival order (FIFO), round-robin, random or equal quota: these four are statistically indistinguishable from each other and ≈0.4–0.5 bps/slot-hour (≈20–28%) below score-based ranking at K=4.
2. Most of the gain comes from two simple, parameter-free, lookahead-free rules: **(i) refuse candidates with estimated net edge ≤ 0** (FIFO_SCREEN: +0.16) and **(ii) rank by estimated net edge per expected slot-hour** (SLOTHOUR: +0.44).
3. Additional machinery (shadow-price thresholds, correlation penalties, Thompson-sampling bandits) does not earn its complexity at the pre-registered margin. Score *pooling* over repeated emissions (UNCERTAINTY_LCB with ω=0.6) adds a small, detectable +0.06 and is the most robust to score noise.
4. All of it degrades with worse scores; with inverted scores no policy protects itself online.

## FIFO adjudication
- FIFO_FAILURE_SCENARIOS (δ=0.25, vs raw FIFO): S12, S3, S4, S5, S5b, S7, S8, S9. FIFO_EQUIVALENT_SCENARIOS: S10, S11, S1, S2, S6. Versus the stronger FIFO_SCREEN control the failure list shrinks from 8 to 6 scenarios (S3, S4, S5b, S7, S8, S9); S12, S5 stop failing, i.e. there a net-edge screen alone closes the gap. In the remaining 6 scenarios ranking is required.
- FIFO is equivalent when demand ≤ capacity (S1, S2; and at cap=10), when the candidate set is dominated by a spam instrument of near-median quality (S10), and in bursts (S11) at δ=0.25 (a ranking gain of ≈+0.25 point estimate becomes detectable at δ=0.1).
- FIFO never showed a starvation problem (soft 0.016) nor higher concentration — its cost is quality (regret, HQ capture, rejected-opportunity quality), not fairness.

## Simple vs complex
Best simple (pre-registered SIMPLE_SET ['FIFO_SCREEN', 'SCORE_RANK', 'SLOTHOUR', 'ROUND_ROBIN']): **SLOTHOUR**. Best complex (COMPLEX_SET ['SLOTHOUR_SHADOW', 'UNCERTAINTY_LCB', 'CORR_AWARE', 'LINTS']): **UNCERTAINTY_LCB**.

| index | SLOTHOUR_SHDW | UNCERT_LCB | CORR_AWARE | LINTS |
|---|---|---|---|---|
| macro_diff_vs_SLOTHOUR | 0.009 | 0.062 | -0.022 | -0.020 |
| ci_lo | -0.028 | 0.027 | -0.051 | -0.057 |
| ci_hi | 0.046 | 0.097 | 0.010 | 0.016 |
| scenario_wins | 5 | 10 | 5 | 5 |
| justified | False | False | False | False |

COMPLEXITY_JUSTIFIED = **FALSE**. UNCERTAINTY_LCB is detectable (+0.062, CI excludes 0, wins 10/13) but 4× below δ=0.25, and it is a *shrinkage* effect (κ=0). Under a looser margin δ=0.05 the verdict on LCB would flip to "justified on effect size, not on complexity cost" — a local decision. LinTS costs ≈24× the decision compute of SLOTHOUR (42.8 vs 1.8 ms/run) for a statistical tie; CORR_AWARE and SHADOW are ties in the macro and mixed per scenario.

Where complexity *does* matter (per-scenario, paired CI excludes 0 vs SLOTHOUR, heldout): UNCERTAINTY_LCB in S8 (+0.26) and S12 (+0.14); SHADOW in S4 (+0.26, but −0.05…−0.15 in S1/S2); none for CORR_AWARE or LINTS.

## Verdict machinery (pre-registered)
- B = methods beating raw FIFO by >δ with CI_lower>0: ['SCORE_RANK', 'SLOTHOUR', 'SLOTHOUR_SHADOW', 'UNCERTAINTY_LCB', 'CORR_AWARE', 'LINTS'] (non-empty ⇒ FIFO_REMAINS_SUFFICIENT_REFERENCE rejected).
- T = methods within δ of best implementable (UNCERTAINTY_LCB) and winning ≥8/13 vs FIFO: ['SCORE_RANK', 'SLOTHOUR', 'SLOTHOUR_SHADOW', 'UNCERTAINTY_LCB', 'CORR_AWARE', 'LINTS'] ⇒ |T|=6 ⇒ **MULTIPLE_CAPACITY_METHODS_SUPPORTED**.
- Sensitivity of the verdict to δ (INFERENCE from macro means): δ=0.1 ⇒ T = {LCB, SHADOW, SLOTHOUR, LINTS, CORR_AWARE} (SCORE_RANK drops out): still multiple; δ=0.5 ⇒ T also contains FIFO_SCREEN/OLDEST_SLOT: still multiple. A single-method verdict would need δ<0.05 (SHADOW is 0.053 below LCB).
- NO_CAPACITY_METHOD_SUPPORTED rejected: every ranking method beats RANDOM by 0.41–0.54 (CIs exclude 0).
- Interpretation: "multiple methods supported" means *the score-ranking family is supported*, not that six distinct algorithms are needed; the honest reading is "a net-edge screen plus net-edge-per-slot-hour ranking is sufficient; the rest is within noise or situational".

## Which methods deserve local evaluation (not adoption, not deployment)
| method | deserves local evaluation? | condition |
|---|---|---|
| FIFO_SCREEN (net-edge screen) | yes, as the *control* | needs a defensible local cost belief (unknown cost must not be zero) |
| SLOTHOUR (net edge / expected hold) | **yes — primary reference** | needs local estimates of expected hold; if hold varies within instrument more than between, prefer SCORE_RANK (validation ladder) |
| UNCERTAINTY_LCB (score pooling ω≈0.6) | yes, secondary | only if candidates repeat per instrument or scores are noisy |
| SLOTHOUR_SHADOW | conditional | only if locally observed quality arrives in late, clustered bursts (S4-like); otherwise it idles slots |
| OLDEST_SLOT-style preemption | diagnostic only | depends on partial-accrual assumption A3; cost-sensitive |
| CORR_AWARE | conditional | only if drawdown control is an explicit goal and groups are few/large |
| LinTS / other bandits, Exp3, ILP/assignment solvers | no (not now) | no evidence of benefit; complexity and tuning burden |
| Starvation safeguards (RR/quota) | no as allocators; yes as *monitoring metrics* | they cost ≈0.45 bps/slot-hour here |

## What the study does NOT conclude
Nothing about `max_open_positions`, the current allocator, any production policy or any cap. The oracle is never presented as implementable. Synthetic effects are descriptive of this generator only.

## Scientific validity checks performed
| check | outcome |
|---|---|
| no-lookahead metamorphic test (12 policies × 4 ingest × 5 scenarios × 2 cuts) | pass; oracle flagged |
| determinism (unit tests + 300 heldout cell re-executions) | pass (0 mismatches) |
| heldout executed once, params frozen with hash, pre-registration precedes heldout in git | yes |
| capacity/one-position-per-instrument invariants | pass |
| UNKNOWN_COST ≠ ZERO_COST test | pass |
| mistakes found and corrected during writing | two mis-statements about OLDEST_SLOT and heavy-tail durations in draft text were corrected against the tables before commit; no result data changed |
ANY_SCIENTIFIC_INVALIDATION = FALSE (see 14 for limitations that bound generalisation).

## Final block
```
ALGORITHMS_DISCOVERED=24 (families/variants catalogued in 02_ALGORITHM_LANDSCAPE.md)
ALGORITHMS_EXECUTED=12 implementable (5 mandatory baselines + FIFO_SCREEN control + 6 candidates) + 1 non-implementable ORACLE_GREEDY_UB upper reference (not counted)

TUNING_SCENARIOS=13 scenarios (S1-S12 + S5b) x 6 seeds, split=tuning
VALIDATION_SCENARIOS=13 x 8 seeds, split=validation (selection among tuning top-3)
HELDOUT_SCENARIOS=13 (S1-S12 + S5b) x 20 seeds, split=heldout (structurally different world parameters)
SEEDS=tuning 1000-1005 | validation 2000-2007 | heldout H1 3000-3019 (H2/H3 3000-3009) | diagnostics 6000-8019

FIFO_FAILURE_SCENARIOS=S12, S3, S4, S5, S5b, S7, S8, S9   (delta=0.25 bps/avail-slot-hour, vs raw FIFO, pre-registered candidate set)
FIFO_EQUIVALENT_SCENARIOS=S10, S11, S1, S2, S6
  (vs the stronger FIFO_SCREEN control: failure=S3, S4, S5b, S7, S8, S9; equivalent=S10, S11, S12, S1, S2, S5, S6)

BEST_SLOT_HOUR_REFERENCE=SLOTHOUR_SHADOW@theta=0.25 by the pre-registered argmax rule; STATISTICALLY TIED with parameter-free SLOTHOUR (diff +0.009, CI [-0.026,+0.044]) -> SLOTHOUR is the practical reference
BEST_DIVERSIFICATION_REFERENCE=CORR_AWARE@gamma~0.4-1.0 (WEAK/CONDITIONAL: no significant M1 gain in any scenario; modest drawdown reduction only in the crisis-in-best-group case; costs M1 when gamma>=1 in benign/collapse worlds); default remains SLOTHOUR
BEST_TURNOVER_REFERENCE=SLOTHOUR (pre-registered argmax SLOTHOUR_SHADOW@0.25 is a tie; shadow-price threshold >=0.5 degrades sharply; OLDEST_SLOT preemption helps only in S4/S6-type worlds under a favourable linear-accrual assumption)

CAP3_SYNTHETIC_RESULT=FIFO 1.83 vs best implementable 2.58 bps/avail-slot-hour (LCB-FIFO +0.75, CI [0.65,0.84])
CAP4_SYNTHETIC_RESULT=FIFO 1.81 vs 2.34 (LCB-FIFO +0.53, CI [0.46,0.59])
CAP6_SYNTHETIC_RESULT=FIFO 1.72 vs 1.93 (LCB-FIFO +0.21, CI [0.16,0.26])
CAP10_SYNTHETIC_RESULT=FIFO 1.31 vs 1.31: no ranking method beats FIFO (LCB-FIFO -0.002, CI [-0.017,+0.014]); SLOTHOUR is slightly WORSE (-0.041)
  (descriptive only, offered load held fixed in absolute terms; NO production cap is recommended)

NO_LOOKAHEAD_PROVEN=TRUE_WITHIN_HARNESS (OBSERVED: prefix-invariance metamorphic test passes for all 12 implementable policies x 4 ingest modes x 5 scenarios x 2 cut points; leaky oracle is flagged; NOT a formal proof about any real system)
CANDIDATE_SPAM_HANDLED=TRUE (scope: modelled, 4 semantics compared, distortion quantified; spam inflates top-instrument admission share ~0.30 vs ~0.14 without spam, semantics reduce it by only 0.01-0.03; economic effect within noise; COOLDOWN hurts ranking policies)
STARVATION_MEASURED=TRUE (hard starvation ~0 for every policy; soft starvation and max denial higher for ranking methods; see 06)

BEST_SIMPLE_REFERENCE=SLOTHOUR
BEST_COMPLEX_REFERENCE=UNCERTAINTY_LCB (omega=0.6, kappa=0: the gain comes from shrinkage/pooling of repeated scores, not from the risk penalty)

COMPLEXITY_JUSTIFIED=FALSE (best complex vs best simple: +0.062 bps/avail-slot-hour, CI [0.027,0.097]: detectable but below the pre-registered practical margin 0.25)

ANY_DROP_IN_ALLOCATOR=FALSE
ANY_SCIENTIFIC_INVALIDATION=FALSE (limitations, not invalidations, are listed in 14)

FINAL_VERDICT=MULTIPLE_CAPACITY_METHODS_SUPPORTED
```
