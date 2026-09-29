# 04 — Synthetic protocol

Code: `bench/capacity_v1/py/{env,scenarios,policies,runner,analyze,heldout_verdict,report_tables,validate_and_leakage,posthoc,oss_probe}.py`; all raw output in `bench/capacity_v1/results/`. Deterministic: every world is a function of `(parameters, seed)` through five independent `SeedSequence` streams (structure, arrivals, latent, observables, market), so a policy can never perturb the world and all policies see identical worlds (common random numbers).

## Environment (see 01 for the decision problem)
Arrival processes: Poisson, two-state MMPP, periodic, deterministic burst windows, spam stream from one instrument. Heterogeneity: per-instrument mean edge, duration, volatility, cost, score noise. Correlation: hourly returns `r_i = β F_cluster + σ_i ε`, positions carry a random side ±1, so same-cluster same-side positions are correlated. Regimes: at a change point instrument-mean edges are permuted, some clusters' score calibration slope flips, cluster-factor volatility rises. Quality information: `score = a + b·edge_now + persistent bias + iid noise`, per-instrument noise level, optional freeze (`stale`) and optional missingness; `dur_hat` is a noisy instrument-level prior blended with the true duration (ρ_d = 0.3 by default).

## Scenarios (12 mandatory + 3 held-out-only)
| ID | Construction |
|---|---|
| S1 sparse demand | offered load 0.15 (at C = 4) |
| S2 moderate saturation | load 1.0 |
| S3 chronic saturation | load 4.0 |
| S4 late high-quality | long durations; edge alternates between a long low-quality phase (60 % of each 60 h period, 1.8× arrival rate) and a short high-quality phase |
| S5 correlated | 2 clusters of 6, high cluster factor, the crowded cluster has higher mean edge |
| S6 short-low vs long-high | fast instruments (2 h, low edge) vs slow (36 h, high edge); density ratio varied by variant |
| S7 regime shift | mid-horizon: edge means permuted, two clusters' calibration slope flips, cluster vol ×2 |
| S8 noisy ranking | score noise ×2.8 with heavy per-instrument heterogeneity |
| S9 missing quality | 40 % missing score, 35 % unknown cost, 30 % missing duration estimate |
| S10 repeated spam | one instrument emits 1.2 near-duplicate low-value opps per hour with an inflated score (+12) |
| S11 burst | ×12 arrival rate for 3 h every 100 h |
| S12 all nearly equal | zero between-instrument dispersion, tiny score noise, homogeneous durations |
| H1 (held-out only) | chronic + correlated + regime shift |
| H2 (held-out only) | burst + very noisy + missing evidence |
| H3 (held-out only) | spam + fast/slow instruments |

## Splits (disjoint parameter draws and seeds)
| Split | Families | Variants | Seeds | Caps | Use |
|---|---|---|---|---|---|
| TUNING | S1–S12 | 3 (jitter ×0.80–1.25 on load, score noise, duration, cluster vol, edge dispersion) | 1000–1002 | 4, 6 | choose hyper-parameters (grids in `policies.GRIDS`, 92 configurations over 17 tunable policies) |
| VALIDATION | S1–S12 | 3 (jitter ×0.75–1.30, S6 ratios differ) | 2000–2003 | 3, 4, 6, 10 | check tuning optimism, pick the shortlist |
| ROBUST / FAILURE | reference family + one-at-a-time perturbations | — | 3000–3004 / 4000–4005 | 3,4,6,10 / 4,6 | vary arrival, noise, calibration, duration, correlation, regime, cost, unknown cost, load; failure-mode probes |
| **HELDOUT** | S1–S12 + H1–H3 | 3 (jitter ×0.65–1.50, wider than the others; S6 ratios 1.8/0.9/3.0 not seen before) | 9000–9009 | 3, 4, 6, 10 | final comparison, never tuned on |

Held-out size: 15 families × 3 variants × 10 seeds = 450 worlds × 4 caps × 29 policies = **52,200 runs** (~46.5 M simulated opportunities).

## Tuning objective
Mean over tuning cells of `(lat_per_slot_hour − FIFO) / dens0_rms`. Hyper-parameters that ended on a grid edge were extended once (round 2, tuning split only). Final tuned values that still sit on an edge (`SLOTHOUR_HAZARD τ = 1`, `ONLINE_KNAPSACK_PSI U = 1.5`, `CORR_PENALTY g = 0.02`, `CORR_HARD_REJECT ρ = 0.95`) mean "the knob wants to be off/neutral" and are reported as such, not re-extended.

## Pre-registration
`bench/capacity_v1/prereg/PREREGISTRATION.json` (v2) fixes the primary metric, thresholds (`δ_material = 0.10`, `δ_equivalence = 0.02`, FIFO-equivalence upper bound 0.04), the shortlist (`COMPOSED`, `SHADOW_PRICE`, `ONLINE_KNAPSACK_PSI`, chosen mechanically from validation), the verdict rules and the SHA-256 of the tuned parameters and of the verdict script. `runner.py heldout` refuses to run if the tuned parameters changed; the verdict is produced by the committed script `heldout_verdict.py`. **History (disclosed):** a first pre-registration (v1, commit `3bbc451`) was superseded *before any held-out data existed* because (a) the covariance estimator's warm-up was biased (prior `eye·40` decays slowly) and its shrinkage 0.2 was too strong for strongly correlated clusters, and (b) the normaliser `dens0_sd` exploded in near-identical scenarios (S12). Both were fixed, tuning/validation/pre-registration redone (v2), and a first held-out launch was killed at start and discarded uninspected. The v1 artefacts are kept in `results/superseded_run1/`.

## No-lookahead tests (run on the final code)
* **T1 counterfactual**: scramble the latent fields (edge, duration, cost) of every opp the baseline run never admitted; the full decision log must be identical.
* **T2 future truncation**: scramble everything knowable only after t0 = 400 (arrivals after t0, their observables, scores/returns after t0, all future returns); decisions at t ≤ t0 must be identical.
* **T3 canary**: a deliberately leaky policy (`LEAKY_CANARY_NOT_IMPLEMENTABLE`) must be *detected* by both T1 and T2 — it was, in 5/5 cases.
* **T4 static audit**: the source of every implementable policy contains 0 references to `W.edge`, `W.dur`, `cost_true`, `CR`, `needs_world`, `attach(`, `world`; the `View` fields contain no latent field.
* Result: 27 implementable policies × 5 scenario cases = 135 runs, **0 failures**. (First attempt showed 28 false alarms; cause was my test scrambling opps arriving *at* t0, which are legitimately visible at t0 — test fixed to `arrival > t0`, then 0 failures. Disclosed here, not hidden.) `NO_LOOKAHEAD_PROVEN` therefore means "proven within the tested scope": these scenarios, this interface, these perturbations.

## Simulator validation
Own simulator with `ttl = 0`, FIFO, no value structure vs the Erlang-B blocking formula: max absolute error 0.0197 over 9 (C, load) points (hourly discretisation and batched arrivals; a SimPy M/G/c/c run agrees to within 0.01 of the formula (own simulator: within 0.020), see 11).
