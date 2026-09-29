# 09 — Adjudication

```
FEATURES_DISCOVERED=80 distinct pre-validation candidates over 5 seeds (18/20/19/22/20 per seed)
FEATURES_HELDOUT_STABLE=0
SYMBOLIC_EXPRESSIONS_STABLE=0
NONREDUNDANT_FEATURES=0
CAUSAL_IDENTIFIED_COUNT=0
COMPLEXITY_JUSTIFIED=NO
FINAL_VERDICT=NO_STABLE_NEW_FEATURES
```

## Verdict logic (pre-registered order)
1. Validity: synthetic recall 1.0 ≥ 0.6 and false discoveries 0 ≤ 1 → PASS; null mean held-out-stable 0.0 ≤ 0.5 → PASS ⇒ not `STUDY_INCONCLUSIVE`.
2. `≥1` non-redundant held-out-stable feature? **No (0)** ⇒ not `LIMITED_STABLE_FEATURES_SUPPORTED` / `FEATURE_DISCOVERY_REFERENCE_SUPPORTED`.
3. ⇒ `NO_STABLE_NEW_FEATURES`.

## What this does and does not support
- Supports: as a *process*, MI/CMI → orthogonalisation → stability selection → validation gate → BIC selection → frozen held-out, with a shifted-target null and a known-truth arena, controls false discovery in this setting and recovers real signal when it exists (OBSERVED). Recommended as a reference design for a local evaluation (ADAPT as protocol; nothing here is code to integrate).
- Does **not** support: any specific formula, any claim that GP/symbolic regression adds value over a pair-wise interaction library (it did not, even on known truth), any causal statement, any profitability statement (no costs, no execution, 4h vol-scaled target).
- Baseline result of note: with 20 causal primitives, 4h horizon, 2024–2026 crypto, the OOS R² of all baselines is ≤0. Local evaluation should not expect free wins from these primitives.

## Interpretability cards
No expression was retained on real data ⇒ no real-data cards. Card for the closest near-miss and for the retained synthetic expression:

**Near-miss (not retained): `vol72`** — formula: rolling-z of the 72h std of 1h log returns; units: dimensionless z-score (raw unit: log-price); inputs: ≥72 closed 1h bars plus 500 bars warm-up for z-score; expected monotonicity: positive vs vol-scaled 4h return (IC_val +0.030, p 0.19–0.26, not established); failure modes: volatility-regime shift, exchange outage gaps distort the std, heavy tails (clip ±6); forward-safety: causal (truncation test), orientation and standardisation frozen on train; status: NOT retained (validation p>0.10), classification `NOT_STABLE`.

**Synthetic retained (method demonstration only): `f1*f2`** — product of two z-scored inputs; unit: z²; inputs: two synchronous features; expected monotonicity: none in either input alone (sign flips with sign(f1)), monotone in the product; failure modes: correlated inputs, heavy tails inflate the product (clip ±6), outliers; forward-safety by construction (same-timestamp inputs); class: `PREDICTIVE`, `INVARIANT_ASSOCIATION` in 4/6 runs.
