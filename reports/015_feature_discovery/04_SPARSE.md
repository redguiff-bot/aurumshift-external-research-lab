# 04 — Sparse regression and screening

## Stability selection (OBSERVED)
Real data, 5 seeds: λ chosen to give ≥10 non-zeros on the full train (α = 0.018–0.025); with 60 block-subsamples/seed and threshold 0.6, **0 of 590 candidates** were selected in any seed (provenance counter: STABSEL = 0). Synthetic: 3–5 features passed in 1-seed smoke tests (not reported), i.e. the mechanism works when signal exists.

## MI / CMI screening (OBSERVED)
- kNN-MI top-10 fed the pool (50 entries over 5 seeds); Gaussian-copula CMI selected 1–2 features/seed (threshold 2.25e-4 nats, χ²₁ 99 %, n_eff=n/4). MI ranking is noisy at 6000 rows: the MI top-10 are dominated by gated volatility products (`x*|vol|`) — INFERENCE: heavy-tail/heteroscedasticity artefacts rather than mean-return information, consistent with their failing validation.
- MI-selected candidates: 0/50 passed validation.

## Baselines on the frozen held-out (OBSERVED; identical across seeds because they do not depend on the seed)
| Model | R²₀ pooled 10 mkts | discovery mkts | unseen mkts | pooled IC |
|---|---|---|---|---|
| B1 ridge, 20 primitives | −0.0020 | −0.0015 | −0.0028 | +0.0053 |
| B2 LassoCV | −0.0005 | +0.00003 | −0.0014 | +0.0113 |
| B3 tree-importance top-5 → ridge (ma72, rng24, vol24, vol72, r72) | −0.0022 | −0.0017 | −0.0029 | +0.0033 |
| B4 permutation-importance top-5 → ridge (ma72, trd, vol24, rng24, vol72) | −0.0020 | −0.0015 | −0.0027 | +0.0055 |
| B5 HistGB, 20 primitives | −0.0055 | −0.0047 | −0.0067 | +0.0166 |

R²₀ = 1 − SSE/Σy² (prediction of 0 is the benchmark). Every model is at or below the zero forecast; the sparse linear model is the least bad, i.e. sparsity/penalty helped and flexibility hurt. The positive pooled IC of B5 (0.017) with negative R² indicates a rank signal that is not calibrated in size (INFERENCE; not exploited, not tested for significance, no cost model). Per-market R² of B1 ranges −0.0047 … +0.0012.

## Synthetic baselines (OBSERVED)
Raw ridge R²≈0.007–0.011, LassoCV ≈ raw, GBM 0.009–0.013, discovered set (raw + 2 retained composites) 0.012–0.018: on known truth the discovery pipeline beats every baseline, so the real-data null is not an artefact of a blind pipeline.
