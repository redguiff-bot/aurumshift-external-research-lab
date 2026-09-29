# 02 — Algorithm landscape

Doctrine: REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST. Literature pointers below are **DOCUMENTED_CLAIM**: author/venue/year recalled from memory of the literature, not re-fetched in this session (there was no primary-source retrieval step for these); the *behaviour* claimed for each implemented method is only what was **OBSERVED** in 09/12. `Status`: **EXEC** = implemented and run in the held-out study; **EXEC-OSS** = an external library was executed on the same environment; **REF** = considered from the literature/library docs, not run.

| # | Idea | Family | Reference (DOCUMENTED_CLAIM) | Status | Implemented as |
|---|---|---|---|---|---|
| 1 | Raw score ranking | opportunity ranking | — | EXEC | `RANK_SCORE_RAW` |
| 2 | Expected-net-value admission (score − cost, admit if >0) | EV admission | textbook | EXEC | `RANK_NET` |
| 3 | Cost handling: UNKNOWN imputed vs treated as 0 | EV admission | — | EXEC | `RANK_NET`, `RANK_NET_UNKCOST_ZERO` |
| 4 | Missing evidence neutral vs reject | EV admission | — | EXEC | `RANK_NET`, `RANK_NET_MISSING_REJECT` |
| 5 | Hierarchical Bayesian calibration + lower confidence bound | uncertainty-aware admission | empirical-Bayes shrinkage (standard) | EXEC | `UNCERTAINTY_LCB` |
| 6 | Marginal risk contribution (Euler) penalty | diversification / marginal risk | Markowitz 1952; risk contributions (Maillard–Roncalli–Teïletche 2010) | EXEC | `MARGINAL_RISK` |
| 7 | Cross-covariance (correlation-only) penalty | diversification | as 6 | EXEC | `CORR_PENALTY` |
| 8 | Hard reject if correlated with an open position | diversification | — | EXEC | `CORR_HARD_REJECT` |
| 9 | Per-cluster concentration cap (laminar constraint) | portfolio-constrained ranking | matroid greedy (Edmonds) | EXEC | `CLUSTER_CAP` |
| 10 | Value per expected slot-hour (+ overhead h0) | turnover / slot economics | revenue-management "value density" | EXEC | `SLOTHOUR_DENSITY` |
| 11 | Staleness-hazard-adjusted density | turnover / hazard | — | EXEC | `SLOTHOUR_HAZARD` |
| 12 | Forced exit with minimum holding + margin (swap-out worst) | turnover-aware selection | Gârleanu–Pedersen 2013 (trading-cost logic) | EXEC | `EVICT_SWAP` |
| 13 | Shadow price / bid-price control (dual ascent on utilisation) | shadow price / opportunity cost | Talluri–van Ryzin 1998 (bid-price controls) | EXEC | `SHADOW_PRICE` |
| 14 | Fluid quantile threshold (booking-limit style) | shadow price / queueing | Talluri–van Ryzin; fluid LP heuristics | EXEC | `FLUID_QUANTILE` |
| 15 | Online knapsack threshold Ψ(fill) | knapsack / online | Zhou–Chakrabarty–Lukose 2008 | EXEC | `ONLINE_KNAPSACK_PSI` |
| 16 | Trunk reservation for low-value class | queueing / admission control | Erlang loss, Kelly 1991; Miller 1969; Stidham 1985 | EXEC | `TRUNK_RESERVATION` |
| 17 | Secretary rule (observe 1/e, then take first better; irrevocable) | secretary / online selection | Ferguson 1989 survey | EXEC | `SECRETARY_1_OVER_E` |
| 18 | LinUCB contextual bandit (delayed reward at close) | contextual bandit | Li–Chu–Langford–Schapire 2010 | EXEC | `LINUCB` |
| 19 | Linear Thompson sampling | contextual bandit | Agrawal–Goyal 2013 | EXEC | `LIN_TS` |
| 20 | Sleeping experts (Hedge over instruments awake when they have a candidate) | sleeping experts | Freund–Schapire–Singer–Warmuth 1997; Kleinberg–Niculescu-Mizil–Sharma 2010 | EXEC | `SLEEPING_HEDGE` |
| 21 | Composition: calibrated LCB + hazard + density + fluid quantile | COMPOSE | this study | EXEC | `COMPOSED` |
| 22 | FIFO / round-robin / random / equal-quota / oldest-slot | baselines | — | EXEC | see 03 |
| 23 | Batch selection under cardinality + cluster caps as MILP | knapsack / assignment | HiGHS via `scipy.optimize.milp`; OR-Tools CP-SAT | EXEC-OSS | proven ≡ greedy (200/200, 100/100) |
| 24 | Hungarian / linear sum assignment of opps to slots | assignment | Kuhn 1955; `scipy.optimize.linear_sum_assignment` | EXEC-OSS | proven ≡ top-k for identical slots (200/200) |
| 25 | Offline time-indexed LP (hindsight schedule) | constrained optimisation | LP relaxation via HiGHS | EXEC-OSS | upper bound, never a policy |
| 26 | Oracle score / oracle density | upper bound | — | EXEC | `ORACLE_*_NOT_IMPLEMENTABLE` |
| 27 | MABWiser LinUCB (arm = instrument) | contextual bandit library | Fidelity MABWiser | EXEC-OSS | probe (11) |
| 28 | Batch/online assignment (online bipartite matching, AdWords) | online assignment | Karp–Vazirani–Vazirani 1990; Mehta et al. 2007 | REF | slots are identical; problem collapses to selection |
| 29 | Bandits with knapsacks | constrained online optimisation | Badanidiyuru–Kleinberg–Slivkins 2013 | REF | slot-hours are the knapsack resource; not implemented (PARK) |
| 30 | Multiple-choice / knapsack secretary | online selection | Kleinberg 2005; Babaioff et al. 2007 | REF | `FLUID_QUANTILE` approximates the "top fraction" rule |
| 31 | MDP admission control (optimal policy by DP) | queueing | Miller 1969; Stidham 1985 | REF | needs known distributions; trunk reservation used as its heuristic |
| 32 | HRP / ERC / min-variance portfolio weighting | portfolio allocation library | López de Prado 2016; PyPortfolioOpt, Riskfolio-Lib | EXEC-OSS (HRP ran) / REF | sizes a fixed asset set; does not admit time-stamped opps |
| 33 | Ledoit–Wolf covariance shrinkage | risk model input | Ledoit–Wolf 2004; scikit-learn / PyPortfolioOpt | EXEC-OSS | compared with own estimator (11) |
| 34 | Off-policy evaluation of contextual bandits | bandit infrastructure | Open Bandit Pipeline; Vowpal Wabbit | REF | PARK: not needed for a simulator |
| 35 | Discrete-event simulation of M/G/c/c loss system | queue/admission simulation | SimPy | EXEC-OSS | simulator cross-check (11) |
| 36 | River online bandit module | bandit library | river | EXEC-OSS (smoke) | arm-level only |

**ALGORITHMS_DISCOVERED = 36** (rows above; #22 counts the five baselines as one row). **ALGORITHMS_EXECUTED** = 29 policies in the held-out grid (27 implementable + 2 upper-bound oracles), + 2 post-hoc diagnostic policies (`LIFO_NETPOS`, `MARGINAL_DIAG`), + 1 leakage canary, + 1 library bandit (`MABWISER_LINUCB`), and the solver checks in rows 23–25, 32, 33, 35, 36.

## Not assumed appropriate
The mission warned "do not assume a bandit is appropriate". The evidence in 09/12 is that it is **not**: LinUCB/LinTS are *below* plain net-EV ranking (−0.023 / −0.020 dz), because the reward (net per hold-hour) is very noisy, feedback arrives only at close, only admitted opps are ever observed (selection bias), and the environment already provides a usable prior (the score). See 10 for the one condition (negative calibration slope) where a bandit is the only method that recovers.
