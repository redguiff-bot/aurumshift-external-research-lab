# 06 — Stability

| Level | Real | Synthetic | Null |
|---|---|---|---|
| Seeds | 5 (11–15) | 6 | 8 |
| Candidates/seed | 18–22 | 16–27 | 16–23 |
| Passed validation | 0/5 seeds have any | 15–26/seed (planted + correlated relatives) | 0–1/run |
| Final list size | 0 in all 5 | 2 in all 6 | 0 in all 8 |
| Held-out stable | 0 | 2 (both planted) | 0 |
| Lock sha256 | identical across seeds (empty list) `8c7a94b0…` | — | — |

- **Across seeds (real):** stable train clusters differ in formula between seeds (e.g. `max(vol72, ma72)` vs `max(vol72, r72)` vs `sub(clp, max(...))`), and share a common core (`vol72`/`ma72` dominate). No expression reproduces with the same structure in all 5 seeds ⇒ symbolic stability at the *structural* level is LOW; at the *information* level the shared core is a volatility/trend primitive already in the baseline set.
- **Across markets:** for the best validation candidate (`vol72`), sign agreement was 6/6 with p≈0.2; nothing else exceeded 83 %.
- **Across time:** the train→validation IC drop for stable-looking expressions is 2–3×; nothing improved.
- **Under a shifted-target null:** 0/8 stable ⇒ the stability criteria are not over-permissive (PROVEN for this pipeline, this null; a shifted target preserves y's marginal and autocorrelation but destroys any feature–y link, so it does not test predictors with volatility-clustering coupling — INFERENCE).
