# 01 — Methods implemented

| Method | Implementation (`bench/feature_discovery_v1/src/pipeline.py`) | Role | Label |
|---|---|---|---|
| Interaction library | 20 primitives + all pairwise products `a*b` (190) + gated `a*|b|` (380) = 590 (376 for 16-primitive synthetic) | candidate space | implemented |
| MI screening | kNN mutual information (sklearn, k=5, 6000 pooled train rows), top-30 kept; top-10 enter the pool | screen | implemented |
| Conditional MI | greedy forward selection on Gaussian-copula (rank→normal) partial correlation, `CMI=-½ln(1-ρ²_partial)`; stop at χ²₁ 99 % with effective n = n/4 (label overlap) | non-redundant selection | implemented (Gaussian-copula CMI is a linear-in-normal-scores proxy; it cannot see purely non-monotone dependence — INFERENCE) |
| Orthogonalisation | (a) CMI residualises on already-selected; (b) held-out *incremental* IC: candidate residualised on the 20 raw primitives with **train-frozen** coefficients | redundancy control | implemented |
| Stability selection | Meinshausen–Bühlmann style: Lasso at λ giving ≥10 non-zeros, 60 subsamples of 50 % of 240-bar time blocks (blocks shared across markets), keep freq ≥ 0.6 | sparse + stability | implemented |
| Symbolic regression / GP | gplearn 0.4.3, ops add/sub/mul/div/neg/abs/max/min, pop 300, 8 gens, parsimony {0.001, 0.01, 0.05} × 5 seeds = 15 fits, top-2 distinct programs/fit; programs clustered by |corr|>0.9 on train; "stable" = cluster present in ≥3 of 5 seeds | expression search | implemented |
| Sparse regression | LassoCV on raw primitives (baseline B2) + Lasso inside stability selection | baseline + screen | implemented |
| Invariant prediction ideas | ICP-*inspired*, not ICP: environments = markets and time halves; require same-sign IC in ≥70 % of the 10 markets, Cochran-Q heterogeneity p ≥ 0.05, both time halves positive | classification only | implemented (a heterogeneity screen; **not** Peters et al.'s ICP with a proven-invariant set) |
| Causal screening | none beyond the above; no instrument/intervention available in observational OHLCV | boundary | see 07 |

Baselines (all fit on discovery-train, hyper-parameters on validation): B1 ridge on all 20 primitives; B2 LassoCV; B3 top-5 by tree-model importance (HistGB, permutation on train as the tree-importance proxy) → ridge; B4 top-5 by permutation importance on validation → ridge; B5 HistGB full.

Not implemented / partial: PySR (not run — heavy Julia dependency; gplearn used); causal discovery algorithms (PC/GES/LiNGAM — deliberately skipped, see 07); model-based interaction discovery (e.g. RuleFit/GA²M) — UNKNOWN whether they would find more.
