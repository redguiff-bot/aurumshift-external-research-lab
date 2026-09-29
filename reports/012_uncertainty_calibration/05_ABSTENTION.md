# 05 — Abstention and selective classification (Q2)

Setup: `py/run_abstain.py`, 12 held-out seeds. Abstain ≡ HOLD (flat). Rules use max-probability of the temperature-scaled model (`conf_static_temp`), the same after sliding-window recalibration (`conf_online_temp`), raw max-probability, entropy, and ensemble MI. τ (or the budget threshold) is set on the **validation** split only and applied unchanged to the held-out stream. "Good retained" = share of trades that would have paid >0 that are still taken; "bad removed" = share of losing trades avoided; the random baseline abstains on trades at the same rate. Tables: `results/tables/abstention_*.md`, `selective_*.md`.

## Selective classification (risk-coverage; OBSERVED)
AURC (lower is better), GBM pre-onset: max-prob 0.342, entropy 0.342, ensemble-MI 0.339, Mahalanobis 0.518; LR pre-onset: 0.273 / 0.272 / 0.410 / 0.479. Post-onset (all shifts pooled): GBM 0.476 / 0.477 / 0.474 / 0.590; LR 0.407 / 0.407 / 0.503 / 0.553. So: **max-probability ≈ entropy; ensemble MI is no better for GBM and clearly worse for LR** (bootstrap LR members barely disagree); Mahalanobis distance is anti-informative for errors in-distribution. Choice of calibrator changes the risk-coverage curve by <0.005 AURC (monotone maps preserve ranking up to ties) — calibration matters for *thresholds*, not for *ranking*.

## Fixed abstention budgets, in-distribution (pre-onset; GBM base; total utility with no abstention = 405.3)
| abstain on trades | bad trades removed | good trades retained | total utility | random abstention at same rate |
|---|---|---|---|---|
| 10 % | 0.151 (LR 0.169) | 0.935 | 406.3 | 364.5 |
| 25 % | 0.362 | 0.826 | 392.1 | 303.3 |
| 40 % | 0.539 | 0.696 | 352.2 | 242.6 |
LR: at 25 % removes 0.383 bad / keeps 0.831 good, utility 497.6 vs 514.1 without abstention. Lift over random ≈1.4–1.5× at 25 %. **Total utility falls as abstention grows** (−3 % at 25 %, −13 % at 40 %) because in this payoff a trade at low confidence is still positive-EV; the validation-optimal τ abstains on only ≈5 % (GBM) / 8 % (LR) of trades and adds +0.5 % utility (407.4 vs 405.3; random 386.2). INFERENCE: the value of abstention is set by the *cost of a wrong trade relative to a missed one*, which is a property of the private system's real cost model, not of this toy payoff.

## Under shift with a frozen validation τ (post-onset; GBM; OBSERVED)
| scenario | rule | abstain on trades | bad removed | good retained | total utility (no abstention → rule; random) |
|---|---|---|---|---|---|
| regime_transition | static conf | 0.05 | 0.05 | 0.95 | −151 → −142 (random −144) |
| regime_transition | **online conf** | 0.40 | 0.42 | 0.64 | −151 → **−36** (random −96) |
| stale_features | static conf | 0.05 | 0.06 | 0.96 | 122 → 131 |
| stale_features | **online conf** | 0.31 | 0.33 | 0.73 | 122 → **146** (random 85) |
| feature_shift | static conf | 0.03 | 0.03 | 0.98 | 120 → 126 |
| feature_shift | **online conf** | 0.22 | 0.24 | 0.81 | 120 → **147** (random 99) |
| vol_jump | static conf | 0.05 | 0.06 | 0.96 | 414 → 418 |
| vol_jump | online conf | 0.16 | 0.18 | 0.87 | 414 → **403** (random 347) |
| none | static / online | 0.05 | 0.08 | 0.97 | 803 → 809 / 808 |
Pooling all shifts (GBM, post): static-confidence abstention 4.6 % of trades, utility +6.8; online-confidence abstention 17.9 %, utility +22.1 (350 → 372; random at the same rate 319). **A fixed threshold on a *static* confidence barely reacts to shift (abstention stays at 3–5 % of trades in every scenario), because the over-confidence is exactly what static calibration cannot see; a fixed threshold on an *online-recalibrated* confidence self-adjusts** — it abstains 22–40 % where trades turn unprofitable. It does not help when the shifted regime is still profitable (vol_jump: −11 utility vs no abstention) — so abstention is a risk-control device, not an alpha source. Opportunity count: 64–87 % of profitable trades are kept in the shifted regimes; 97 % in-distribution.

## Conformal-singleton abstention (see `06_CONFORMAL.md`)
α=0.2 LAC sets (LR): in-distribution ≈38–42 % singleton decisions (58–62 % abstained); shift-only mean abstention 0.76 (ACI-rolling) with singleton accuracy 0.63. Coverage control costs most of the opportunity count here because the underlying 3-class signal is weak.

## Verdict for Q2
Partially supported. Confidence-ranked abstention gives a consistent but modest lift over random (≈1.4×) and can prevent large losses **when combined with online recalibration in a shift that makes trading unprofitable**; it does not by itself raise utility in a stationary positive-EV world, and ensemble-disagreement scores added nothing. False-confidence (CWM) is reduced by calibration, not by abstention (`conf_wrong_trade_mass_*` columns mostly show calibrated confidence already rarely exceeds 0.6 when wrong).
