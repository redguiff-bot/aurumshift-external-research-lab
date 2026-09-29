# 00 — Executive summary (feature_discovery_v1, external research, branch `claude/feature-discovery-v1-b`)

Boundary: external study on public data (10 Binance spot markets, 1h) + a known-truth synthetic arena. No AurumShift code, no integration, no trading/cost claim. Labels follow the lab doctrine (PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN).

## Question
Can automated discovery (MI/CMI screening, orthogonalisation, stability selection, sparse regression, interaction libraries, gplearn symbolic regression) produce compact, interpretable, non-redundant features that survive a strict time/market hold-out, without silently overfitting?

## Answer
- **Method validity — OBSERVED.** On a known-truth synthetic arena (6 seeds) the pipeline recovered both planted composite terms in 12/12 cases with 0 false discoveries. On 8 null runs (real features, circularly shifted target) it produced **0** held-out-stable features and 0 retained features.
- **Real markets — OBSERVED.** In 5 discovery seeds, 18–22 candidates/seed were generated (80 distinct expressions in total), **0** passed the validation gate (needs same-sign, ≥70 % market agreement, p<0.10), so the frozen final list was empty in all 5 seeds (identical lock digest `8c7a94b0…`, written before held-out access; test asserts this order).
- **Baselines on held-out — OBSERVED.** Every baseline has ≤0 out-of-sample R² (raw ridge −0.0020, LassoCV −0.0005, tree-importance top-5 −0.0022, permutation-importance top-5 −0.0020, GBM −0.0055). There is essentially nothing linear or shallow-tree-visible in these 20 primitives at a 4h vol-scaled horizon for the period tested; the discovery pipeline found no more than the baselines.
- **Complexity — NOT justified** (nothing retained to justify).
- **Causal — none.** 0 CAUSAL_IDENTIFIED. No feature reached even INVARIANT_ASSOCIATION on real data.

```
FEATURES_DISCOVERED=80 distinct pre-validation candidates over 5 seeds (18/20/19/22/20 per seed)
FEATURES_HELDOUT_STABLE=0
SYMBOLIC_EXPRESSIONS_STABLE=0 (2–4 train-stable cross-seed symbolic clusters per seed; none passed validation)
NONREDUNDANT_FEATURES=0

CAUSAL_IDENTIFIED_COUNT=0

COMPLEXITY_JUSTIFIED=NO

FINAL_VERDICT=NO_STABLE_NEW_FEATURES
```

Verdict strength: **MODERATE-LOW** — the negative is credible for *this* feature family, market set, horizon and window (validity checks pass), but it is one asset class, one ~2.3-year window, and one target definition (10_LIMITATIONS). Absence of evidence here is not evidence that no stable features exist elsewhere.

## Note on a pre-existing branch
A different session had already pushed `claude/feature-discovery-v1` (independent pipeline; its commit messages state verdict `LIMITED_STABLE_FEATURES_SUPPORTED`). I did not read or reuse its content, and did not overwrite it, so the two studies are independent. They disagree on the verdict label; reconciling them is left to the operator (differences in candidate library, gate thresholds and target are the first places to look).
