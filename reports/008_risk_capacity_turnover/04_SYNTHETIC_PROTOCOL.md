# 04 — Synthetic protocol

Code: `bench/capacity_v1/src/world.py` (generator), `engine.py` (simulator), `policies.py`. Everything is deterministic: world seed = crc32(scenario|split) + 1000003·seed; policies use their own seeded RNG. Common random numbers: outcome of entering (i,t) is a pure function of the world, so counterfactuals and cross-policy comparisons are paired.

## World
N instruments (10/12/15 depending on split), G groups, K=4 slots (K∈{3,4,6,10} in sensitivity), W=600 admission steps + 48 h settlement pad. Per-instrument edge μ_i, volatility σ_i, mean duration d_i, cost c_i; instrument-level AR(1) opportunity state (φ=0.9); Markov regime multipliers (default switch prob 1/300 per step); group factor + market factor with loadings ρ_g, ρ_m(t). Arrivals: Poisson per instrument with heterogeneous rates; offered candidate load L = Σλ·E[D]/4 (fixed in absolute terms, so K=10 is under-loaded). Scores: s = a_i + b·E + τ·ξ, plus optional staleness (reuse of previous score) and missingness (NaN).

## Scenarios (base overrides; splits change N, G, τ, duration CV, edge/vol/cost ranges)
| id | what it stresses | overrides |
|---|---|---|
| S1 sparse | demand < capacity | L=0.4 |
| S2 moderate | occasional saturation | L=1.2 |
| S3 chronic | permanent saturation | L=3.5 |
| S4 late high-quality | HQ candidates arrive in a 8h window after LQ burst has filled slots with long (14h) low-edge trades | L=3.5, phase profile |
| S5 correlated (crisis) | best-edge group carries a hidden negative factor drift in 30–60% of the window; ρ_g=0.8 | diversification **beneficial** |
| S5b correlated (benign) | same but no crisis; best edges cluster in one group | diversification may **hurt** |
| S6 short vs long | short (2h, edge 14) low-edge vs long (16h, edge 45): per-trade EV prefers long, per-hour prefers short | L=3.5 |
| S7 regime shift | edge ranking flips at W/2 | hard flip |
| S8 noisy ranking | score noise ×2.5 | τ×2.5 |
| S9 missing quality | 50% of scores NaN | p_miss=0.5 |
| S10 spam | 2 mediocre-edge instruments emit ×20 | ingest semantics matter |
| S11 burst | ×15 arrival for 4 of every 60 steps | L=2.5 |
| S12 nearly equal | all edges/durations/costs ≈ equal | selection ≈ noise |

Diagnostic-only scenarios (validation split, never heldout): F_score_gaming, F_corr_collapse, F_inversion, F_poor_cal, F_stale, F_starve_skew, F_short_churn_cost.

## No-lookahead — how it is enforced and tested
1. Structural: hidden latents never enter `View`/`Pub`; learning feedback is delivered only at trade close and only for admitted trades (censored feedback).
2. **Metamorphic leak test** (`tests/test_capacity.py`): a twin world keeps every *observable* identical but redraws all hidden latents (E, D, Z, factor paths) for index ≥ t0. Any implementable policy must make identical admissions for t ≤ t0. Executed for 12 policies × 4 ingest modes × 5 scenarios × cut points {150,300}; **all pass** (OBSERVED). The perfect-foresight oracle **fails** it in ≥4/5 scenarios, so the test has power (OBSERVED).
3. Explicit statement: any method requiring future PnL/duration at admission is non-implementable; only the oracle does, and it is used solely as an upper reference.
Scope: this proves the harness is leak-free for the implemented policies; it says nothing about a real pipeline's leakage (UNKNOWN).

## Other tests (all passing: 77)
Determinism (12 policies), world determinism/seed sensitivity, capacity invariants, `UNKNOWN_COST != ZERO_COST` (zero-belief admits more than known and conservative), missing score ≠ negative score, eviction accounting. Re-execution of 300 random heldout cells reproduced all trade hashes (0 mismatches of 300).

## Splits
| split | seeds | world params |
|---|---|---|
| TUNING | 1000–1005 | N=10, G=5, τ=8, CV=0.6 |
| VALIDATION | 2000–2007 (selection); 6000–8019 (diagnostics) | N=12, G=4, τ=9, CV=0.8 |
| HELDOUT | 3000–3019 | N=15, G=5, τ=10, CV=0.7, different edge/vol/duration/cost ranges |
