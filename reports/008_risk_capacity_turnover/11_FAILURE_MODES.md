# 11 — Failure modes (explicitly tested)

Evidence sources: heldout H1/H2 (S-scenarios), validation-split failure battery D4 (10 seeds, frozen parameters), D1–D3, D6. "Handled" means *measured and a mitigation identified or ruled out*, not "eliminated".

| # | failure mode | test | observed outcome | status |
|---|---|---|---|---|
| 1 | score gaming | F_score_gaming: 20% of instruments report scores +30 bps inflated with true edge ≤10 | all score-driven policies over-admit the gamers (top-instrument admission share 0.15 FIFO → 0.20 SLOTHOUR); they still beat FIFO (M1 2.68 vs 2.28) because FIFO admits the gamers too. **No implemented policy detects gaming** (UNCERTAINTY_LCB pools score history, which the gamer inflates consistently) | OPEN — needs per-instrument realised-vs-predicted feedback (not implemented) |
| 2 | candidate spam | S10, H2, D4i | concentration up (0.30–0.35 vs 0.14); M1 effect within noise; COOLDOWN harmful | MEASURED; SCORE_UPDATE/DEDUP harmless (06) |
| 3 | instrument starvation | H1 starvation metrics; F_starve_skew (skewed edges) | hard starvation ≈0; soft/denial higher for ranking; safeguards cost ≈0.45 bps | MEASURED (06); F_starve_skew soft starvation 0.07 SLOTHOUR vs 0.00 RR |
| 4 | long-slot capture | S6 (+ D1 duration shapes) | SCORE_RANK mean hold 12.0 h vs SLOTHOUR 7.8 h; SCORE_RANK below FIFO in point estimate; SLOTHOUR +0.36 [0.16,0.56] vs SCORE_RANK; OLDEST_SLOT best | REAL; mitigated by SLOTHOUR (between-instrument heterogeneity) or preemption |
| 5 | short-slot churn | S6 + F_short_churn_cost (costs ×1.8) | OLDEST_SLOT turnover 2× and re-entry churn 0.61; at cost ×3 it is the only negative policy (−1.16 on S3) | REAL for preemption; not for ranking |
| 6 | correlation collapse | F_corr_collapse (ρ_m 0.7 in 35–60% window, negative drift) | CORR_AWARE −0.16 [−0.33,−0.02] vs SLOTHOUR; group penalty cannot hedge a market factor | REAL; group-based penalty does not address it |
| 7 | regime lag | S7 (rank flips at W/2), D1 regime persistence | policies driven by *current scores* adapt immediately; ranking beats FIFO by ≈+0.8–0.95; LINTS/UNCERTAINTY_LCB (history-dependent) do not lag measurably in M1 (UNCERTAINTY_LCB +0.09 [−0.02,+0.20] vs SLOTHOUR) | NOT OBSERVED at this regime speed (an EWMA of scores with 5-step memory adapts fast; slower memories untested) |
| 8 | noisy-score instability | S8 (τ×2.5), D1 noise curve | occupancy oscillation std 0.05 (FIFO) → 0.13/0.19 (SLOTHOUR/SHADOW) — screening makes utilisation more volatile; UNCERTAINTY_LCB gives the best M1 (+0.26 [0.12,0.41] vs SLOTHOUR) | MEASURED; shrinkage is the mitigation |
| 9 | capacity oscillation | occupancy std, full_frac, S11 burst | S11 full_frac ≈0.18–0.22, occupancy std ≈0.34 for **all** policies (burst-driven, policy-independent); idle 1499 h (SHADOW) vs 1222 h (FIFO) | MEASURED; SHADOW amplifies idling |
| 10 | one instrument monopolising refreshes | S10 top-instrument share; SCORE_UPDATE keeps first-arrival queue position | share 0.30 (FIFO) … 0.33; RR/EQ_QUOTA 0.23–0.28 | MEASURED (06) |
| 11 | high-quality late arrival | S4 | HQ capture FIFO 0.53 → SLOTHOUR 0.73 → SHADOW 0.77; M1: SHADOW +0.26 [0.10,0.40] vs SLOTHOUR; OLDEST_SLOT +0.44 vs FIFO_SCREEN (preemption recycles long low-edge slots) | REAL; helped by reserving capacity (SHADOW) or preemption |
| 12 | quality-estimate inversion | F_inversion (half of groups: score = 40 − 0.6·edge), D2 | SCORE_RANK 2.43 < FIFO 2.62; SLOTHOUR 2.73, LINTS 2.83 (FIFO +0.1…+0.2); score-free OLDEST_SLOT (2.88) is at least as good as every score-driven policy. **No policy detects inversion online**; LINTS only partially (it learns a weight on the rate feature from realised outcomes, but reward noise is large) | OPEN; needs calibration monitoring (realised vs predicted by score bucket) |

Reading rules: significance statements come from paired bootstraps in `results/analysis/targeted_pairs.csv`; D4 has only 10 seeds per cell so small differences are unresolved.
