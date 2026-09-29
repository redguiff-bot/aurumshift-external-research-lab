# 10 — Limitations

1. **Synthetic only.** Every conclusion is about algorithm behaviour under the mechanisms coded in `scenarios.py`. No real strategy returns, costs,
   capacity, slippage, delayed/restated outcomes (see report 004 for PIT issues) or heavy tails were used.
2. **Risk-neutral, linear objective.** Metric is expected reward of a weighted average of expert rewards. Under it, concentrating on the best expert is
   optimal, which is why hard-max rules tune best and why bounded weights and diversity look useless. Drawdown/variance/turnover/capacity effects, where
   diversification and floors matter, are **not evaluated**. This is the biggest reason the verdict is inconclusive rather than a ranking.
3. **Shadow evaluation assumed.** All valid experts' returns are observable each round (full information). If only executed strategies are observable,
   the problem moves toward bandit/partial feedback (only crudely represented by SleepEXP3 / DUCB).
4. **Regime label given for free.** The Ctx* rows assume a label at decision time (true, 1-round-lagged, or 20%-flipped). Real regime detection is neither
   accurate nor independent of the strategy universe. Break-even is ≈92.5% accuracy.
5. **Tuning plateau / edges.** After the single pre-declared extension, optima for SleepHedge (η=400), EWMA (β=400), BMA (κ=600, opt=0.1), SH_bounded (B=10), and others
   still sit on a grid edge (`results/tuned_params.json → _grid_edge_flags`). These are plateaus toward winner-take-all, not resolved optima. Hyper-parameters were pooled across
   scenarios; per-scenario tuning was not done.
6. **Scenario-specific gates, arbitrary thresholds.** 10% margin, 150/0.35/100 starvation thresholds, 1.5× robustness factor were fixed by me. Two gate definitions (G4a, G4b) were
   later found to be mis-specified; amended results are labelled POST_HOC. Verdict is sensitive to these thresholds (DiscFreeze misses G1 at 0.91×).
7. **Tuning/held-out share the generator.** Held-out seeds differ but the generator family is identical; stress sets vary only two knobs (SNR, noise). No structural
   distribution shift (e.g. correlation break, non-Gaussian tails) was tested.
8. **Ablations missing.** The DiscFreeze burst-gap failure (S6b) and the S6d mechanism are explained but not isolated by ablation (INFERENCE). Parameter-free algorithms
   (AdaNormalHedge/Squint), textbook BMA, sleeping-bandit theory rates, and trained context models were not executed.
9. **Literature recalled, not re-fetched.** Section 02's citations are from memory of the primary papers (DOCUMENTED_CLAIM); no paper was retrieved in this session.
   OSS inspection covered only `river`, `mabwiser`, `contextualbandits` (PyPI source, not executed); a broader search may find other libraries.
10. **Realised vs expected.** Rankings use noise-free expected regret; realised-reward means are in `tables.md` and agree in ordering except for near-ties.
11. **No AurumShift knowledge.** Nothing here establishes compatibility with, or a need in, the private system.
