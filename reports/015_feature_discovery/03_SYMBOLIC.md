# 03 — Symbolic regression (gplearn)

**Setup:** see 01. 15 fits per discovery seed (3 parsimony levels × 5 seeds), pearson fitness on 10 000 pooled train rows, 70 % subsample per generation.

## Real data (OBSERVED)
- Cross-seed clusters per seed with ≥3 distinct GP seeds ("train-stable"): **3, 2, 4, 2, 2** (13 in total).
- Typical stable expressions were shallow rearrangements of volatility/trend primitives, e.g. `max(vol72, ma72)`, `add(vol72, r72)`, `sub(clp, max(vol72, r72))`, `add(ma72, max(vol72, ma72))`, `max(vol72, r72)`.
- **None** passed the validation gate. Best validation IC among *all* symbolic/library candidates: `sym:vol72` (a bare primitive found by GP) IC_val = +0.030, p = 0.19–0.26 (block bootstrap), 6/6 markets same sign, but not significant; every other candidate had IC_val ≤ 0.02 and p ≥ 0.13, or ≤ 83 % sign agreement with p far from 0.10.
- Train ICs of the stable expressions (0.04–0.05) shrank to 0.01–0.02 on validation (p 0.28–0.60): the textbook signature of GP fitting train noise (INFERENCE from the shrinkage pattern; not a formal test).
- **SYMBOLIC_EXPRESSIONS_STABLE = 0.**

## Synthetic (known truth, OBSERVED)
GP produced 1–3 train-stable clusters per run, but **0 symbolic expressions were finally retained/held-out stable in 6/6 runs**: the planted terms `f1*f2` and `f3*|f4|` were recovered from the (exact-structure) interaction library, not from GP. So in this study symbolic regression added **nothing beyond a 2-operator library** even where truth exists. This is a statement about gplearn at pop 300 / 8 generations, not about symbolic regression in general (UNKNOWN: PySR, larger budgets).

## Bloat / interpretability
GP parsimony at 0.001 produced up to 7-node programs mixing `max`/`sub` of unrelated primitives with no unit logic (max of a volatility z-score and an MA-distance z-score). Because every primitive is a z-score they are dimensionally consistent, but not economically interpretable; they were not retained anyway (see the card for the one retained-style example in 09).
