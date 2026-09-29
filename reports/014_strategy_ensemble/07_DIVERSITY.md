# 07 — Diversity and correlated experts

Tested: S5a (3 near-clones, ρ≈0.95, of the *bad* expert), S5b (3 clones of the *best* generalist), plus
`DivEWMA` / `DivSH` (base weights ÷ crowding from online pairwise correlation, τ tuned).

| method | S0 | S5a clones of bad | S5b clones of best |
|---|---|---|---|
| Equal | 61.6 | 79.9 | 49.4 |
| EWMA | 10.6 | 11.5 | 11.2 |
| DivEWMA | 10.5 | 11.4 | 11.0 |
| SleepHedge | 10.7 | 10.7 | 10.3 |
| DivSH | 10.7 | 10.7 | 10.3 |
| WTA | 10.4 | 11.4 | 11.0 |

* Clones hurt only the rules that do not learn (Equal: +18 in S5a). Every adaptive rule is within ±1 of its S0 regret.
* Diversity wrappers gave **no measurable benefit** (DivSH ≡ SleepHedge to 2 decimals; DivEWMA 0.8% better than EWMA,
  inside noise) and DivEWMA misses the literal (untolerated) stress gate by 1%. τ tuned to the grid minimum (0.1) with a flat objective.
* Why (INFERENCE, important): the objective is expected reward under a *linear* aggregator, so concentrating on the best expert is
  optimal and diversification has nothing to buy; clones are simply ignored by weights that already concentrate. Diversity is
  valuable for **variance/drawdown**, which this study does not model. Result: `NOT_TESTED_FOR_RISK`; for
  expected-reward accuracy diversity-aware weighting is not justified. Equal weighting of correlated clones is harmful.
* Risk check: the S5b concern (a diversity penalty punishing the best expert because its clones are crowded) does not show
  up at the tuned τ=0.1 (DivSH S5b 10.3 = SleepHedge 10.3); other τ values were only evaluated on tuning seeds.
