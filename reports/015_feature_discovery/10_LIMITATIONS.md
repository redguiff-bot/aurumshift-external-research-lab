# 10 — Limitations

1. **Single asset class and window.** 10 crypto spot pairs on one venue, 2024-05 → 2026-09; markets are highly correlated, so "10 markets" ≈ far fewer independent samples; the block bootstrap shares blocks across markets, but n_eff for gating uses n/4 only (may be too generous, INFERENCE).
2. **One target/horizon.** 4h vol-scaled log return; other horizons, cross-sectional or event targets untested. Overlapping labels handled by embargo + block bootstrap, not by a model.
3. **Primitive set.** 20 OHLCV-derived primitives, no order book, funding, open interest, on-chain, macro. Absence of discoveries is conditional on this input set.
4. **GP budget small** (pop 300, 8 gens, 10 000 rows); PySR/larger searches not run (UNKNOWN).
5. **Synthetic arena is mine.** Effect size and size tuned on a smoke seed; 12/12 recovery is a power point, not a sensitivity curve; the invariance trap was ill-designed; the synthetic has independent markets (no cross-market dependence).
6. **Thresholds** (p<0.10 gate, |IC|≥0.005, BIC form, sign-agreement 70 %, Q-test 0.05) are pre-registered but arbitrary; the Q-test flags magnitude heterogeneity even when sign is consistent.
7. **Null is a shifted-target null**; it does not calibrate false-discovery for structure-preserving alternatives.
8. **Selection on validation is deliberately conservative** and, with n_eff≈6 000, cannot detect single-feature |IC| ≲ 0.02. Real effects at that scale would be missed.
9. **No costs/execution/capacity**; even a stable IC of 0.01 is far from a tradable edge.
10. **Independence from prior branch.** Another session pushed `claude/feature-discovery-v1` with a different pipeline and verdict label; not reviewed here. Verdict disagreement is unresolved.
11. Public API data: revisions/PIT status of exchange klines UNKNOWN (bars taken as final; no restatement checks).
12. Environment: python 3.11, numpy 2.4.6, scikit-learn 1.9.1, scipy 1.17.1, gplearn 0.4.3; runs deterministic per seed given these versions (not bit-checked across machines).
