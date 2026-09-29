# 00 — Executive summary

Study: `AURUMSHIFT_EXTERNAL_RISK_CAPACITY_AND_TURNOVER_ALLOCATION_V1` — EXTERNAL_RESEARCH_ONLY, synthetic, PAPER-style abstractions. No AurumShift private code, no integration, no production recommendation.
Tags: PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN.

## Question
When incoming opportunities exceed available position slots, how should scarce slots be allocated without lookahead, overfitting or hidden capital assumptions?

## What was done
- Deterministic synthetic simulator (`bench/capacity_v1/src/`) with 13 scenarios (S1–S12 + S5b), 12 implementable allocation policies + a non-implementable oracle upper reference, 4 candidate-ingest semantics, explicit costs, explicit slot-hour accounting.
- Strict TUNING → VALIDATION → HELDOUT separation; pre-registration (`configs/prereg.json`) committed **before** heldout execution; heldout executed once.
- 77 tests: determinism, capacity invariants, unknown-cost≠zero-cost, and a metamorphic **no-lookahead** test (hidden future state resampled; admissions up to the cut must be identical) — the perfect-foresight oracle is correctly flagged by the same test.

## Findings (heldout, K=4, 13 scenarios × 20 seeds; all effects are synthetic)
1. **Raw FIFO is not sufficient** (OBSERVED): every score-based ranking method beats raw FIFO by +0.37 to +0.50 bps per available slot-hour on macro average (FIFO 1.78 → 2.28; ~+20–28%), CIs exclude 0, wins in 12–13 of 13 scenarios.
2. **Most of that gain is available from very simple rules** (OBSERVED): screening on estimated net edge (FIFO_SCREEN) gives +0.16; ranking by estimated net edge per expected slot-hour (SLOTHOUR, parameter-free) gives +0.44 over FIFO. Scenario-by-scenario, FIFO is equivalent to the sophisticated set in S10, S11, S1, S2, S6 and materially worse in S12, S3, S4, S5, S5b, S7, S8, S9.
3. **Complexity is not justified** (OBSERVED): the best complex method (UNCERTAINTY_LCB, effectively "shrink repeated scores toward instrument history") beats the best simple one (SLOTHOUR) by +0.06 [0.03,0.10] — detectable, but 4× below the pre-registered practical margin (0.25). Thompson-sampling contextual bandit and correlation-aware selection are statistically tied with or below SLOTHOUR.
4. **Slot-hour economics** help over raw EV ranking only where duration is heterogeneous (S5b, S6 significant); it is *worse* than EV ranking when the score is near-perfect (validation ladder, tau=0). Shadow-price thresholds mostly idle slots: only S4 (late high-quality arrival) benefits; θ≥0.5 collapses.
5. **Diversification penalties do not reliably pay** (OBSERVED): no significant M1 gain in S5/S5b/collapse; modest drawdown/worst-24h benefit in the crisis-in-best-group world at γ≈0.4–1, at zero to negative M1 cost; strong γ (≥4) costs 0.16–0.34 bps.
6. **Starvation is a real trade-off** (OBSERVED): hard starvation ≈0 everywhere, but ranking methods show roughly 2–7× the soft-starvation rate of the baselines and longer denial spells; round-robin/equal-quota "safeguards" give back the entire ranking gain (−0.44/−0.48 vs SLOTHOUR).
7. **Capacity sensitivity is descriptive only**: the advantage of ranking over FIFO shrinks with more slots at fixed offered load (K=3: +0.75, K=4: +0.53, K=6: +0.21, K=10: ≈0). **No production cap is inferred.**
8. **Candidate spam** distorts *who* gets slots (concentration) more than *how much* is earned; de-dup/score-update are harmless, cooldown hurts ranking methods (−0.22…−0.27).
9. Score quality is the binding input (validation diagnostics): with inverted or poorly calibrated scores the ranking advantage over FIFO shrinks by roughly 45–70%, and in the separate inversion battery (D4) SCORE_RANK falls *below* FIFO. FIFO/RANDOM/ROUND_ROBIN/OLDEST_SLOT do not use scores and are unaffected by definition.

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

## Boundaries (mandatory reading)
The study concludes only *which method families deserve local evaluation* (see 13): (i) a net-edge screen, (ii) net-edge-per-expected-slot-hour ranking with score pooling, and — as a diagnostic, not a candidate — the preemption baseline. It does **not** claim anything about `max_open_positions`, the current allocator, or any deployment. All economics are synthetic and generic; UNKNOWN_COST is never treated as zero cost.
