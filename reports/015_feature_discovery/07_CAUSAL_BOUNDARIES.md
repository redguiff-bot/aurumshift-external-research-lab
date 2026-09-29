# 07 — Causal boundaries

Classes: `PREDICTIVE` · `INVARIANT_ASSOCIATION` · `CAUSAL_HYPOTHESIS` · `CAUSAL_IDENTIFIED`.

| Class | Operational rule used here | Real data count | Synthetic count |
|---|---|---|---|
| PREDICTIVE | held-out stable (see 02) | 0 | 2/run (planted) |
| INVARIANT_ASSOCIATION | PREDICTIVE + Cochran-Q p≥0.05 across markets + both time halves positive | 0 | `f1*f2` in 4/6 runs; the gated term 0/6 (magnitude varies by market by design) |
| CAUSAL_HYPOTHESIS | invariant + new + documented mechanism + selected in ≥4/5 seeds — assigned **only by a human argument**, code never assigns it | 0 | n/a |
| CAUSAL_IDENTIFIED | requires an identified design (randomised/natural experiment, valid instrument, or a fully specified structural model with assumptions defended) | **0** | 0 (the synthetic SCM is known to me, but no estimator here uses interventions; a known generator is ground truth for the *method*, not an identification result) |

## Why CAUSAL_IDENTIFIED is structurally 0 here
1. Data are passive OHLCV; no exogenous variation in any feature.
2. All features and the target are functions of the same price/volume path and of latent common drivers (news, funding, liquidity, BTC beta). Unobserved confounding is the default; no instrument exists in the data.
3. The invariance screen (markets as environments) is ICP-*inspired*, but the "environments" are not interventions: they share the same macro shocks (crypto markets are highly correlated), so invariance across them is weak evidence even when it holds.
4. Hourly features overlap in information with the label window's microstructure (e.g. taker-buy share and next-hours flow); reverse causation cannot be excluded.

## Where causal screening *is* defensible (INFERENCE, not tested)
Exchange-side natural experiments with plausibly exogenous timing (listing/delisting announcements, fee-tier changes, scheduled token unlocks, funding-rate reset mechanics) could support an identified design for a *specific* mechanism; nothing in this study uses one. Any future "causal" label must name the design and the untestable assumptions.

## Language rule adopted
Even INVARIANT_ASSOCIATION is written "associated with"; no report section says a feature "drives", "causes" or "explains" returns.
