# 08 — Falsification tests

| Test | Result | Label |
|---|---|---|
| Causality/truncation: recompute primitives and z-scores on a truncated series → identical up to the cut | pass (`tests/test_isolation.py::test_features_are_causal`) | PROVEN (for these 20 primitives, one market file) |
| Target not among primitives | pass | PROVEN |
| Held-out untouched before LOCK (access log order, every real/null/synth run) | pass, `access_order` = train,val,…,LOCK,test | PROVEN |
| Splits disjoint, ordered, ≥24-bar gap | pass | PROVEN |
| Null (circularly shifted target, 8 seeds, real features): held-out-stable features | **0/8**; validation-gate passes 5 total; final lists empty | OBSERVED |
| Known truth: recovery of planted composites | **12/12** at β=0.06/T=19 000 (effect size set on a smoke seed) | OBSERVED (power at one effect size) |
| Known truth: false discoveries | **0** in 6 runs | OBSERVED |
| Known truth: GP finds planted terms without the library | not tested separately; GP never retained (03) | OBSERVED |
| Trap non-invariant feature (f5) | uninformative (primitive, cannot be "new") | design flaw, OBSERVED |
| Held-out used to select a formula | no: final list empty on real data; frozen before held-out on all runs | PROVEN by lock + access log |
| Real-data results re-run after seeing held-out | no | PROVEN (git history; one pass) |

## Not done (would strengthen)
- Placebo horizons/targets on real data (e.g. target shifted by 1–5 bars), feature-permutation nulls that preserve volatility coupling, other exchanges/asset classes, walk-forward re-discovery, a lower-power synthetic sweep (β ∈ {0.02, 0.03, 0.04}) to state the minimum detectable effect. Without the sweep, "no stable features" on real data cannot be turned into "no feature with |IC| above X" (UNKNOWN X; roughly, n_eff≈6 000 held-out rows/market·6 mkts /4 suggests |IC| < ~0.02 is undetectable per feature — INFERENCE).
