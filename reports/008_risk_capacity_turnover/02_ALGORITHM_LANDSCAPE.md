# 02 — Algorithm landscape

Literature statements below are **DOCUMENTED_CLAIM** from prior knowledge; the papers were **not re-fetched** in this session, so exact theorem statements are UNKNOWN at page level. Empirical statements marked OBSERVED come from this study's simulator. "EXEC" = implemented and run; "PARK" = worth local thought later; "REJECT" = judged unsuitable here.

| # | Family / algorithm | Idea | Key reference (DOCUMENTED_CLAIM) | Status |
|---|---|---|---|---|
| 1 | FIFO | first-come-first-served | — | EXEC (baseline A) |
| 2 | Round-robin by instrument | fairness across sources | — | EXEC (baseline B) |
| 3 | Random, fixed seed | null model | — | EXEC (baseline C) |
| 4 | Equal-opportunity quota | deficit round-robin on admission counts | Shreedhar–Varghese DRR 1995 (scheduling analogue) | EXEC (baseline D) |
| 5 | Oldest-slot / turnover-neutral | preempt oldest position after min hold | — | EXEC (baseline E) |
| 6 | Net-edge screen + FIFO | admit in arrival order only if E[net]>0 | — | EXEC (control, added for fairness) |
| 7 | Expected-value ranking | rank by score − cost | classic EV admission | EXEC (SCORE_RANK) |
| 8 | Slot-hour / density ranking | rank by E[net]/E[hold] — knapsack "density" greedy | Kellerer–Pferschy–Pisinger, *Knapsack Problems* 2004 | EXEC (SLOTHOUR) |
| 9 | Shadow-price / opportunity-cost threshold | admit iff rate ≥ θ·λ, λ = marginal slot-hour value | LP duality; Lagrangian admission control | EXEC (SLOTHOUR_SHADOW) |
| 10 | Uncertainty-aware admission | shrink noisy scores (empirical Bayes) + lower confidence bound | Efron–Morris shrinkage; LCB from bandit literature | EXEC (UNCERTAINTY_LCB) |
| 11 | Marginal-risk / correlation-aware greedy | penalise same-group concentration | Markowitz 1952 (marginal variance) | EXEC (CORR_AWARE) |
| 12 | Contextual bandit — linear Thompson sampling | learn reward model from delayed censored feedback | Agrawal–Goyal 2013 | EXEC (LINTS) |
| 13 | Contextual bandit — LinUCB | optimism under uncertainty | Li–Chu–Langford–Schapire 2010 | PARK (same feature model as #12; not run) |
| 14 | Bandits with knapsacks | bandit + resource budgets | Badanidiyuru–Kleinberg–Slivkins 2013 | PARK (no budget beyond slots; slot-hour usage is stochastic but observed only at close) |
| 15 | Sleeping experts / sleeping bandits | only some arms awake each round | Freund et al. 1997; Kleinberg–Niculescu-Mizil–Sharma 2010 | PARK (natural fit for "instruments available at t"; not needed to run given #12 ≈ #10 result) |
| 16 | Adversarial bandits (Exp3/Exp4) | no stochastic assumption | Auer et al. 2002 | REJECT (worst-case exploration cost unjustified; feedback delayed/censored) |
| 17 | Assignment / min-cost-flow (Hungarian, LSA) | jointly assign candidates to slots | Kuhn 1955; Jonker–Volgenant | PARK — **PROVEN by reduction**: with slot-independent weights the optimal assignment is top-f by weight (also OBSERVED: 500/500 random trials with `scipy.optimize.linear_sum_assignment`); only useful with slot-specific or pairwise terms |
| 18 | ILP / knapsack with pairwise risk terms | exact joint selection | MILP solvers (HiGHS, CBC, CP-SAT) | PARK (greedy #11 within noise of no penalty; an exact solver cannot beat noise in scores) |
| 19 | Secretary / online selection | threshold from observed prefix | Dynkin 1963; Kleinberg 2005 (K-secretary) | PARK (rolling-quantile threshold ≈ #9, which is mostly harmful) |
| 20 | Constrained online optimisation (primal–dual / online gradient) | learn dual price of slots | Agrawal–Devanur 2014; Mahdavi–Jin–Yang 2012 | PARK (shadow price #9 is its static special case) |
| 21 | Whittle index (restless bandits) | per-arm index for time-varying state | Whittle 1988 | PARK (requires a per-instrument state model; unknown locally) |
| 22 | Queueing admission control (M/M/c/K threshold, MDP) | threshold by occupancy | Stidham 1985; Miller 1969 | PARK (admission-by-occupancy is subsumed by #9 in this study) |
| 23 | Lyapunov drift-plus-penalty | queue-stability + utility | Neely 2010 | PARK |
| 24 | Portfolio-constrained ranking (HRP / mean-variance / risk parity) | portfolio-level weights | Markowitz; López de Prado 2016 (HRP) | REJECT for slot admission (weights, not admissions; used only via #11's marginal concentration idea) |

Count: **24 discovered**; **12 implementable executed** (rows 1–12; the oracle is a separate reference); rows 13–24 = 10 PARK (13, 14, 15, 17, 18, 19, 20, 21, 22, 23) + 2 REJECT (16, 24). "Do not assume a bandit is appropriate": OBSERVED — LinTS ties SLOTHOUR (−0.02, CI [−0.05,+0.02]) while costing ~25× compute per decision and adding hyper-parameters; it did not earn its place here.

## How the ideas map to the mission's "turnover" list
| idea | executed as | result (heldout unless noted) |
|---|---|---|
| expected net / expected hold | SLOTHOUR | +0.07 vs SCORE_RANK (CI [+0.03,+0.11]); sig. positive in S5b, S6 only |
| hazard-adjusted opportunity value | *not separately executed*; approximated by UNCERTAINTY_LCB's variance-aware rate | UNKNOWN whether a true hazard model adds anything |
| turnover penalty | *subsumed* by cost in net value and by the SHADOW threshold | see 08 |
| minimum holding constraint | OLDEST_SLOT min_hold ∈ {2,4,8} | 4 best (validation); 2 worse (cost churn); see 08 |
| slot shadow-price threshold | SLOTHOUR_SHADOW θ ∈ {0.25…1.25} | best θ at the *lowest* grid value; θ≥0.5 degrades sharply |
