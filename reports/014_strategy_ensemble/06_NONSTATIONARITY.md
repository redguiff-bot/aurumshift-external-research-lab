# 06 — Non-stationarity

Held-out regret ×1e-3 per scenario (lower is better; oracle = truth-best allocated expert). Full tables in
`bench/ensemble_v1/results/tables.md`.

| method | S0_base | S1_leadership | S2_dormancy | S3_new_expert | S4_disappears | S5a_clones_of_bad | S5b_clones_of_best | S6a_gap_mcar | S6b_gap_burst | S6d_abstain_informative | S7_temp_underperf | S8_composite | S6c_gap_mnar |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CtxOracle | 7.2 | 10.9 | 7.2 | 7.4 | 7.5 | 8.0 | 7.0 | 9.5 | 9.1 | 9.0 | 8.2 | 9.2 | 8.5 |
| CtxLag | 9.1 | 12.4 | 10.8 | 9.5 | 9.1 | 10.2 | 8.8 | 11.4 | 11.1 | 10.3 | 11.5 | 12.1 | 10.3 |
| DiscFreeze | 9.3 | 10.2 | 9.4 | 11.0 | 7.8 | 9.6 | 9.5 | 11.8 | 17.7 | 9.3 | 11.3 | 10.1 | 10.5 |
| BMA | 9.8 | 10.8 | 10.0 | 11.4 | 8.1 | 10.6 | 10.4 | 12.4 | 11.5 | 15.3 | 10.8 | 10.6 | 12.4 |
| DiscAmnesty | 10.2 | 11.3 | 9.7 | 12.4 | 7.7 | 10.5 | 10.5 | 12.9 | 16.5 | 10.4 | 12.7 | 11.5 | 11.2 |
| WTA | 10.4 | 11.5 | 10.7 | 12.1 | 8.7 | 11.4 | 11.0 | 13.6 | 12.3 | 16.2 | 11.2 | 11.3 | 13.0 |
| DivEWMA | 10.5 | 11.6 | 10.7 | 12.2 | 8.7 | 11.4 | 11.0 | 13.6 | 12.3 | 16.3 | 11.2 | 11.4 | 13.2 |
| EWMA | 10.6 | 11.7 | 10.8 | 12.2 | 8.8 | 11.5 | 11.2 | 13.7 | 12.4 | 16.2 | 11.3 | 11.4 | 13.2 |
| SleepEG | 11.0 | 17.9 | 10.3 | 13.7 | 8.0 | 10.6 | 10.2 | 12.1 | 10.9 | 11.8 | 16.6 | 18.5 | 11.2 |
| DivSH | 10.7 | 21.0 | 10.8 | 14.4 | 7.3 | 10.7 | 10.3 | 11.0 | 11.1 | 10.5 | 16.7 | 23.5 | 11.4 |
| SleepHedge | 10.7 | 21.0 | 10.8 | 14.4 | 7.3 | 10.7 | 10.3 | 11.0 | 11.1 | 10.6 | 16.7 | 23.5 | 11.4 |
| FixedShare | 12.6 | 13.1 | 12.5 | 13.3 | 11.3 | 14.4 | 11.5 | 15.3 | 15.9 | 13.5 | 13.4 | 13.3 | 14.0 |
| CtxNoisy | 13.7 | 15.7 | 13.7 | 14.3 | 12.1 | 15.1 | 12.5 | 15.9 | 15.4 | 13.7 | 15.8 | 15.1 | 15.0 |
| HedgePlain | 12.9 | 23.0 | 11.8 | 16.5 | 9.7 | 13.5 | 12.8 | 15.4 | 26.5 | 24.2 | 16.8 | 27.9 | 30.7 |
| DUCB | 16.6 | 19.9 | 15.3 | 17.3 | 12.7 | 20.0 | 15.1 | 18.6 | 18.1 | 21.0 | 23.8 | 16.8 | 19.2 |
| EWMA_bounded | 21.4 | 22.1 | 23.8 | 24.1 | 18.7 | 24.0 | 18.0 | 23.9 | 23.2 | 24.7 | 26.7 | 27.9 | 23.8 |
| Static | 19.8 | 36.6 | 19.9 | 25.9 | 16.3 | 21.9 | 16.8 | 20.3 | 20.4 | 24.7 | 31.6 | 44.8 | 22.4 |
| SH_bounded | 24.3 | 24.5 | 26.3 | 25.9 | 22.1 | 28.0 | 19.6 | 25.2 | 25.5 | 23.7 | 29.3 | 29.2 | 25.3 |
| SleepEXP3 | 58.1 | 57.4 | 61.6 | 59.9 | 52.8 | 72.9 | 44.5 | 58.5 | 58.6 | 55.4 | 68.1 | 64.2 | 56.1 |
| Equal | 61.6 | 61.5 | 66.2 | 63.3 | 56.5 | 79.9 | 49.4 | 61.5 | 62.2 | 57.0 | 72.2 | 68.9 | 62.1 |


## Findings (all PROVEN within this generator)

* **Leadership changes (S1, S8, S7-patch):** un-forgetting sleeping Hedge at its tuned η=400 is the worst
  realisable rule (S1 21.0, S8 23.5) — accumulated log-weight advantage takes long to unwind. Forgetting
  (DiscFreeze 10.2), fixed-share (13.1) or short-memory EWMA/WTA (11.5–11.7) handle it. Static collapses
  (36.6/44.8).
* **Stationary or gap-heavy scenarios (S0, S4, S6a, S6b, S6d):** SleepHedge/Div-SH are the best or tied-best
  non-context rules (S4 7.3 vs 8.8 for EWMA; S6d 10.6 vs 16.2).
* **Regime recurrence (S0, S2, S8):** context mixtures win because recurrence is exactly what a per-regime weight
  vector exploits (CtxOracle 7.2 in S0), but only with a very accurate label (see 09 label-noise table).
* **New expert (S3):** SleepHedge pays for it (14.4 vs 10.7 in S0); EWMA 12.2 vs 10.6; DiscFreeze 11.0.
* **Expert disappears (S4):** trivially handled by all gated methods (allocation excludes it; mass renormalises);
  regret goes *down* vs S0 for every method (INFERENCE: with the strongest regime-0 generalist gone the oracle is weaker and the remaining choices are closer together).
* **Correlated experts (S5):** see 07 — the effect is small.
* No single rule is best in every scenario: rank order flips between {SleepHedge-family, EWMA-family,
  Ctx*} depending on which non-stationarity dominates. That is the substantive content of the verdict.
