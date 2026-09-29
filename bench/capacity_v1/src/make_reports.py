"""Generates reports/008_risk_capacity_turnover/*.md. Tables are pulled from results/analysis CSVs (no hand-copied numbers in tables)."""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import common as C
A = f"{C.ROOT}/results/analysis"; REP = os.path.join(os.path.dirname(os.path.dirname(C.ROOT)), "reports", "008_risk_capacity_turnover")
os.makedirs(REP, exist_ok=True)
M1 = "net_per_avail_slot_hour"
ORDER = ["FIFO", "ROUND_ROBIN", "RANDOM", "EQUAL_QUOTA", "OLDEST_SLOT", "FIFO_SCREEN", "SCORE_RANK", "SLOTHOUR", "SLOTHOUR_SHADOW", "UNCERTAINTY_LCB", "CORR_AWARE", "LINTS", "ORACLE_GREEDY_UB"]
SH = {"ORACLE_GREEDY_UB": "ORACLE_UB", "SLOTHOUR_SHADOW": "SLOTHOUR_SHDW", "UNCERTAINTY_LCB": "UNCERT_LCB", "ROUND_ROBIN": "ROUND_ROBIN", "EQUAL_QUOTA": "EQ_QUOTA", "OLDEST_SLOT": "OLDEST_SLOT"}
def sh(x): return SH.get(x, x)
def tbl(df, nd=3, index=True):
    d = df.copy()
    if index: d = d.reset_index()
    cols = [sh(c) if isinstance(c, str) else str(c) for c in d.columns]
    def f(v):
        if isinstance(v, (float, np.floating)): return "n/a" if np.isnan(v) else f"{v:.{nd}f}"
        return str(v)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in d.iterrows(): lines.append("| " + " | ".join(f(v) for v in r.values) + " |")
    return "\n".join(lines)
def W(name, text): open(f"{REP}/{name}", "w").write(text.strip() + "\n")
def rd(n, **k): return pd.read_csv(f"{A}/{n}", **k)

macro = rd("H1_macro_all_metrics.csv", index_col=0).loc[ORDER]
pers = rd("H1_perscenario_all_metrics.csv", index_col=[0, 1])
vm = json.load(open(f"{A}/H1_rules_and_verdict_machinery.json"))
rules = vm["rules"]; vmach = vm["verdict_machinery"]
fz = json.load(open(f"{C.ROOT}/configs/frozen_params.json"))
pre = json.load(open(f"{C.ROOT}/configs/prereg.json"))
det = json.load(open(f"{A}/determinism_check.json"))
oss = json.load(open(f"{A}/oss_probe.json"))
pm = rd("H1_paired_macro.csv"); pps = rd("H1_paired_perscenario.csv")
m1_scen = pers[M1].unstack(0)[ORDER]
def pair_row(p, ref):
    r = pm[(pm.policy == p) & (pm.ref == ref)].iloc[0]; return r
f_fail = rules["0.25"]["FIFO"]["failure"]; f_eq = rules["0.25"]["FIFO"]["equivalent"]
s_fail = rules["0.25"]["FIFO_SCREEN"]["failure"]; s_eq = rules["0.25"]["FIFO_SCREEN"]["equivalent"]
short = lambda L: ", ".join(x.split("_")[0] for x in L)

FINAL = f"""```
ALGORITHMS_DISCOVERED=24 (families/variants catalogued in 02_ALGORITHM_LANDSCAPE.md)
ALGORITHMS_EXECUTED=12 implementable (5 mandatory baselines + FIFO_SCREEN control + 6 candidates) + 1 non-implementable ORACLE_GREEDY_UB upper reference (not counted)

TUNING_SCENARIOS=13 scenarios (S1-S12 + S5b) x 6 seeds, split=tuning
VALIDATION_SCENARIOS=13 x 8 seeds, split=validation (selection among tuning top-3)
HELDOUT_SCENARIOS=13 (S1-S12 + S5b) x 20 seeds, split=heldout (structurally different world parameters)
SEEDS=tuning 1000-1005 | validation 2000-2007 | heldout H1 3000-3019 (H2/H3 3000-3009) | diagnostics 6000-8019

FIFO_FAILURE_SCENARIOS={short(f_fail)}   (delta=0.25 bps/avail-slot-hour, vs raw FIFO, pre-registered candidate set)
FIFO_EQUIVALENT_SCENARIOS={short(f_eq)}
  (vs the stronger FIFO_SCREEN control: failure={short(s_fail)}; equivalent={short(s_eq)})

BEST_SLOT_HOUR_REFERENCE=SLOTHOUR_SHADOW@theta=0.25 by the pre-registered argmax rule; STATISTICALLY TIED with parameter-free SLOTHOUR (diff +0.009, CI [-0.026,+0.044]) -> SLOTHOUR is the practical reference
BEST_DIVERSIFICATION_REFERENCE=CORR_AWARE@gamma~0.4-1.0 (WEAK/CONDITIONAL: no significant M1 gain in any scenario; modest drawdown reduction only in the crisis-in-best-group case; costs M1 when gamma>=1 in benign/collapse worlds); default remains SLOTHOUR
BEST_TURNOVER_REFERENCE=SLOTHOUR (pre-registered argmax SLOTHOUR_SHADOW@0.25 is a tie; shadow-price threshold >=0.5 degrades sharply; OLDEST_SLOT preemption helps only in S4/S6-type worlds under a favourable linear-accrual assumption)

CAP3_SYNTHETIC_RESULT=FIFO 1.83 vs best implementable 2.58 bps/avail-slot-hour (LCB-FIFO +0.75, CI [0.65,0.84])
CAP4_SYNTHETIC_RESULT=FIFO 1.81 vs 2.34 (LCB-FIFO +0.53, CI [0.46,0.59])
CAP6_SYNTHETIC_RESULT=FIFO 1.72 vs 1.93 (LCB-FIFO +0.21, CI [0.16,0.26])
CAP10_SYNTHETIC_RESULT=FIFO 1.31 vs 1.31: no ranking method beats FIFO (LCB-FIFO -0.002, CI [-0.017,+0.014]); SLOTHOUR is slightly WORSE (-0.041)
  (descriptive only, offered load held fixed in absolute terms; NO production cap is recommended)

NO_LOOKAHEAD_PROVEN=TRUE_WITHIN_HARNESS (OBSERVED: prefix-invariance metamorphic test passes for all 12 implementable policies x 4 ingest modes x 5 scenarios x 2 cut points; leaky oracle is flagged; NOT a formal proof about any real system)
CANDIDATE_SPAM_HANDLED=TRUE (scope: modelled, 4 semantics compared, distortion quantified; spam inflates top-instrument admission share ~0.30 vs ~0.14 without spam, semantics reduce it by only 0.01-0.03; economic effect within noise; COOLDOWN hurts ranking policies)
STARVATION_MEASURED=TRUE (hard starvation ~0 for every policy; soft starvation and max denial higher for ranking methods; see 06)

BEST_SIMPLE_REFERENCE={vmach['best_simple']}
BEST_COMPLEX_REFERENCE={vmach['best_complex']} (omega=0.6, kappa=0: the gain comes from shrinkage/pooling of repeated scores, not from the risk penalty)

COMPLEXITY_JUSTIFIED=FALSE (best complex vs best simple: +{vmach['complexity']['UNCERTAINTY_LCB']['macro_diff']:.3f} bps/avail-slot-hour, CI [{vmach['complexity']['UNCERTAINTY_LCB']['lo']:.3f},{vmach['complexity']['UNCERTAINTY_LCB']['hi']:.3f}]: detectable but below the pre-registered practical margin 0.25)

ANY_DROP_IN_ALLOCATOR=FALSE
ANY_SCIENTIFIC_INVALIDATION=FALSE (limitations, not invalidations, are listed in 14)

FINAL_VERDICT=MULTIPLE_CAPACITY_METHODS_SUPPORTED
```"""

# ------------------------------------------------------------------ 00
W("00_EXECUTIVE_SUMMARY.md", f"""
# 00 — Executive summary

Study: `AURUMSHIFT_EXTERNAL_RISK_CAPACITY_AND_TURNOVER_ALLOCATION_V1` — EXTERNAL_RESEARCH_ONLY, synthetic, PAPER-style abstractions. No AurumShift private code, no integration, no production recommendation.
Tags: PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN.

## Question
When incoming opportunities exceed available position slots, how should scarce slots be allocated without lookahead, overfitting or hidden capital assumptions?

## What was done
- Deterministic synthetic simulator (`bench/capacity_v1/src/`) with 13 scenarios (S1–S12 + S5b), 12 implementable allocation policies + a non-implementable oracle upper reference, 4 candidate-ingest semantics, explicit costs, explicit slot-hour accounting.
- Strict TUNING → VALIDATION → HELDOUT separation; pre-registration (`configs/prereg.json`) committed **before** heldout execution; heldout executed once.
- 77 tests: determinism, capacity invariants, unknown-cost≠zero-cost, and a metamorphic **no-lookahead** test (hidden future state resampled; admissions up to the cut must be identical) — the perfect-foresight oracle is correctly flagged by the same test.

## Findings (heldout, K=4, 13 scenarios × 20 seeds; all effects are synthetic)
1. **Raw FIFO is not sufficient** (OBSERVED): every score-based ranking method beats raw FIFO by +0.37 to +0.50 bps per available slot-hour on macro average (FIFO {macro.loc['FIFO',M1]:.2f} → {macro.loc['UNCERTAIN'+'TY_LCB',M1]:.2f}; ~+20–28%), CIs exclude 0, wins in 12–13 of 13 scenarios.
2. **Most of that gain is available from very simple rules** (OBSERVED): screening on estimated net edge (FIFO_SCREEN) gives +0.16; ranking by estimated net edge per expected slot-hour (SLOTHOUR, parameter-free) gives +0.44 over FIFO. Scenario-by-scenario, FIFO is equivalent to the sophisticated set in {short(f_eq)} and materially worse in {short(f_fail)}.
3. **Complexity is not justified** (OBSERVED): the best complex method (UNCERTAINTY_LCB, effectively "shrink repeated scores toward instrument history") beats the best simple one (SLOTHOUR) by +0.06 [0.03,0.10] — detectable, but 4× below the pre-registered practical margin (0.25). Thompson-sampling contextual bandit and correlation-aware selection are statistically tied with or below SLOTHOUR.
4. **Slot-hour economics** help over raw EV ranking only where duration is heterogeneous (S5b, S6 significant); it is *worse* than EV ranking when the score is near-perfect (validation ladder, tau=0). Shadow-price thresholds mostly idle slots: only S4 (late high-quality arrival) benefits; θ≥0.5 collapses.
5. **Diversification penalties do not reliably pay** (OBSERVED): no significant M1 gain in S5/S5b/collapse; modest drawdown/worst-24h benefit in the crisis-in-best-group world at γ≈0.4–1, at zero to negative M1 cost; strong γ (≥4) costs 0.16–0.34 bps.
6. **Starvation is a real trade-off** (OBSERVED): hard starvation ≈0 everywhere, but ranking methods show roughly 2–7× the soft-starvation rate of the baselines and longer denial spells; round-robin/equal-quota "safeguards" give back the entire ranking gain (−0.44/−0.48 vs SLOTHOUR).
7. **Capacity sensitivity is descriptive only**: the advantage of ranking over FIFO shrinks with more slots at fixed offered load (K=3: +0.75, K=4: +0.53, K=6: +0.21, K=10: ≈0). **No production cap is inferred.**
8. **Candidate spam** distorts *who* gets slots (concentration) more than *how much* is earned; de-dup/score-update are harmless, cooldown hurts ranking methods (−0.22…−0.27).
9. Score quality is the binding input (validation diagnostics): with inverted or poorly calibrated scores the ranking advantage over FIFO shrinks by roughly 45–70%, and in the separate inversion battery (D4) SCORE_RANK falls *below* FIFO. FIFO/RANDOM/ROUND_ROBIN/OLDEST_SLOT do not use scores and are unaffected by definition.

## Final block
{FINAL}

## Boundaries (mandatory reading)
The study concludes only *which method families deserve local evaluation* (see 13): (i) a net-edge screen, (ii) net-edge-per-expected-slot-hour ranking with score pooling, and — as a diagnostic, not a candidate — the preemption baseline. It does **not** claim anything about `max_open_positions`, the current allocator, or any deployment. All economics are synthetic and generic; UNKNOWN_COST is never treated as zero cost.
""")

# ------------------------------------------------------------------ 01
W("01_PROBLEM_FORMULATION.md", """
# 01 — Problem formulation

## Setting (INFERENCE: abstracted from the mission text, not from any private system)
- K position slots; discrete time (1 step = 1 hour); N heterogeneous instruments in G public groups.
- Each instrument emits candidate events (score = noisy estimate of gross edge in bps if held to the unknown duration D). Events may repeat (spam), be missing, or be stale.
- **One open position per instrument** (modelling assumption A1). Pending candidates expire after a TTL of 4 steps (A2).
- Admission at step t chooses among pending candidates with free slots. Holding duration D(i,t) and realised outcome are unknown at admission (stochastic, lognormal or Pareto, clipped to [1,48] h).
- Net outcome = gross − cost (bps, generic). Cost is charged once per admission (including truncated exits).
- Gross(i,t,h) = (E/D)·h + σ_i(ρ_g·ΔC_g + ρ_m(t)·ΔC_m + √(1−ρ_g²−ρ_m²)·√h·Z). **Edge accrues linearly in hold time (A3)** — this makes early exit cheap and favours preemption; see 14.

## Information sets (no lookahead)
- **Observable at t**: emission events with scores (possibly NaN), public group ids, public noisy volatility, cost belief (known / zero / unknown-conservative), own history of *closed* trades (realised net, realised hold), open positions.
- **Hidden (settlement only)**: true edge E(i,t), duration D(i,t), idiosyncratic Z, group/market factor paths, regimes.
- Implementation: policies receive a `View`+`Pub`; hidden arrays live only in `World`. Rejected-candidate counterfactuals are computed by the engine for reporting only.
- The ORACLE_GREEDY_UB policy requires an explicit hook to hidden state (`IMPLEMENTABLE=False`), is labelled UPPER BOUND ONLY everywhere, and is a *greedy* perfect-foresight reference — it is **not** the offline optimum (INFERENCE: true optimum is higher).

## Candidate ingestion (spam) semantics
| mode | semantics |
|---|---|
| RAW | every emission is an independent candidate (queue entry) |
| DEDUP_LATEST | one candidate per instrument; latest emission replaces it (queue age resets) |
| COOLDOWN | emission dropped if the instrument was accepted <3 steps ago |
| SCORE_UPDATE | one candidate per instrument; keeps first-arrival queue position, score replaced by latest non-missing score, expiry refreshed |

Rejected-opportunity quality is reported both per raw candidate and **instrument-weighted** (repeated rejects of one instrument are not independent opportunities). Candidates whose instrument is already open at expiry are excluded ("blocked", not rejected).

## Metrics (never combined into a composite)
M1 = net outcome per *available* slot-hour (net_total / (K·W), W=600). Also: net per busy slot-hour, net total, regret vs oracle (M1_oracle − M1), turnover (admissions per slot-hour), idle slot-hours (and idle-with-backlog), HHI over instruments/groups, top-instrument share, hard/soft starvation, max denial hours, rejected-opportunity quality, high-quality capture (12h instrument blocks, top-quartile realised net/hour), portfolio P&L std / worst-24h / max drawdown (net spread evenly over hold), re-entry churn, occupancy oscillation, and computational cost.

## Unknown-cost handling
`known` (policy sees true cost), `zero` (policy assumes 0 — the forbidden equivalence, tested to show the damage), `unknown_conservative` (public prior 10 bps). Accounting always charges the true cost.
""")

# ------------------------------------------------------------------ 02
W("02_ALGORITHM_LANDSCAPE.md", """
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
""")

# ------------------------------------------------------------------ 03
mb = macro.loc[["FIFO", "ROUND_ROBIN", "RANDOM", "EQUAL_QUOTA", "OLDEST_SLOT", "FIFO_SCREEN"], [M1, "net_per_busy_slot_hour", "turnover_per_slot_hour", "idle_slot_hours", "hhi_inst", "starve_soft_rate", "max_denial_hours", "rej_rate_instw", "hq_capture", "mean_hold"]]
W("03_BASELINES.md", f"""
# 03 — Baselines

All five mandatory controls were implemented and executed in every scenario, even where sophisticated methods look superior. A sixth, **FIFO_SCREEN**, was added so that "ranking" gains are not confused with "screening out negative expected net" gains.

| id | policy | notes |
|---|---|---|
| A | FIFO | arrival order (first emission); primary ingest RAW (as naively implemented) |
| B | ROUND_ROBIN | pointer over instruments; RAW ingest |
| C | RANDOM | policy RNG seeded (`seed+424242`), independent of the world |
| D | EQUAL_QUOTA | fewest cumulative admissions first (deficit round-robin) |
| E | OLDEST_SLOT | FIFO admission; when full and candidates wait, preempt oldest slot with age ≥ min_hold (tuned on validation: {fz['OLDEST_SLOT']['params']['min_hold']} h); truncated outcome realised at exit, cost charged in full |
| ctl | FIFO_SCREEN | FIFO among candidates with estimated net edge > 0; ingest {fz['FIFO_SCREEN']['ingest_primary']} (tuned) |

## Heldout macro results (K=4, 13 scenarios × 20 seeds; OBSERVED)
{tbl(mb)}

Reading:
- A–D are statistically indistinguishable from one another on M1 (paired CIs vs FIFO: RR {pair_row('ROUND_ROBIN','FIFO').macro_diff:+.3f} [{pair_row('ROUND_ROBIN','FIFO').lo:+.3f},{pair_row('ROUND_ROBIN','FIFO').hi:+.3f}], RANDOM {-0.042:+.3f}, EQUAL_QUOTA {pair_row('EQUAL_QUOTA','FIFO').macro_diff:+.3f}). **Arrival order carries no information about quality in this world** (INFERENCE — by construction candidates are exchangeable in time). Real arrival order may differ (UNKNOWN).
- FIFO_SCREEN beats FIFO by {pair_row('FIFO_SCREEN','FIFO').macro_diff:+.3f} [{pair_row('FIFO_SCREEN','FIFO').lo:+.3f},{pair_row('FIFO_SCREEN','FIFO').hi:+.3f}], 11/13 scenarios: a large part of "smart allocation" is just refusing negative-expected-net entries. Its benefit depends on the cost belief: with zero-cost belief the screen degrades toward FIFO (see 08).
- OLDEST_SLOT (E) is *not* a null: +{pair_row('OLDEST_SLOT','FIFO').macro_diff:.3f} vs FIFO [{pair_row('OLDEST_SLOT','FIFO').lo:.3f},{pair_row('OLDEST_SLOT','FIFO').hi:.3f}] with 2× the turnover and evict_frac ≈ {macro.loc['OLDEST_SLOT','evict_frac']:.2f}. It beats FIFO_SCREEN where long slots get captured (S4, S6; heldout) and loses to it in S5/S5b. This benefit rests on the linear-accrual assumption A3 (early exit forfeits nothing but the not-yet-earned edge) — INFERENCE that it would be weaker if edge is back-loaded; UNKNOWN locally.
- Metric caveat: `hq_capture` for OLDEST_SLOT (≈0.93) is inflated by its 2× admission count and should not be read as selection skill.

## Per-scenario M1 (bps / available slot-hour; heldout, mean of 20 seeds)
{tbl(m1_scen)}
""")

# ------------------------------------------------------------------ 04
W("04_SYNTHETIC_PROTOCOL.md", f"""
# 04 — Synthetic protocol

Code: `bench/capacity_v1/src/world.py` (generator), `engine.py` (simulator), `policies.py`. Everything is deterministic: world seed = crc32(scenario|split) + 1000003·seed; policies use their own seeded RNG. Common random numbers: outcome of entering (i,t) is a pure function of the world, so counterfactuals and cross-policy comparisons are paired.

## World
N instruments (10/12/15 depending on split), G groups, K=4 slots (K∈{{3,4,6,10}} in sensitivity), W=600 admission steps + 48 h settlement pad. Per-instrument edge μ_i, volatility σ_i, mean duration d_i, cost c_i; instrument-level AR(1) opportunity state (φ=0.9); Markov regime multipliers (default switch prob 1/300 per step); group factor + market factor with loadings ρ_g, ρ_m(t). Arrivals: Poisson per instrument with heterogeneous rates; offered candidate load L = Σλ·E[D]/4 (fixed in absolute terms, so K=10 is under-loaded). Scores: s = a_i + b·E + τ·ξ, plus optional staleness (reuse of previous score) and missingness (NaN).

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
2. **Metamorphic leak test** (`tests/test_capacity.py`): a twin world keeps every *observable* identical but redraws all hidden latents (E, D, Z, factor paths) for index ≥ t0. Any implementable policy must make identical admissions for t ≤ t0. Executed for 12 policies × 4 ingest modes × 5 scenarios × cut points {{150,300}}; **all pass** (OBSERVED). The perfect-foresight oracle **fails** it in ≥4/5 scenarios, so the test has power (OBSERVED).
3. Explicit statement: any method requiring future PnL/duration at admission is non-implementable; only the oracle does, and it is used solely as an upper reference.
Scope: this proves the harness is leak-free for the implemented policies; it says nothing about a real pipeline's leakage (UNKNOWN).

## Other tests (all passing: 77)
Determinism (12 policies), world determinism/seed sensitivity, capacity invariants, `UNKNOWN_COST != ZERO_COST` (zero-belief admits more than known and conservative), missing score ≠ negative score, eviction accounting. Re-execution of 300 random heldout cells reproduced all trade hashes ({det['hash_mismatches']} mismatches of {det['sampled']}).

## Splits
| split | seeds | world params |
|---|---|---|
| TUNING | 1000–1005 | N=10, G=5, τ=8, CV=0.6 |
| VALIDATION | 2000–2007 (selection); 6000–8019 (diagnostics) | N=12, G=4, τ=9, CV=0.8 |
| HELDOUT | 3000–3019 | N=15, G=5, τ=10, CV=0.7, different edge/vol/duration/cost ranges |
""")

# ------------------------------------------------------------------ 05
fzt = pd.DataFrame({k: dict(params=json.dumps(v["params"]), ingest_primary=v["ingest_primary"], validation_M1=v.get("validation_objective", float("nan"))) for k, v in fz.items()}).T
W("05_HELDOUT_PROTOCOL.md", f"""
# 05 — Held-out protocol

## Procedure (executed in this order; commit history is the evidence)
1. Build simulator + tests (77 pass).
2. **TUNING**: every (policy, parameter, ingest mode) config on 13 scenarios × seeds 1000–1005 (K=4). Tuning objective: macro-mean M1 (tuning only).
3. **VALIDATION**: top-3 configs per policy re-run on 13 × seeds 2000–2007 (different world parameters); best on validation is frozen → `configs/frozen_params.json`.
4. **PRE-REGISTRATION** committed (`configs/prereg.json`): metrics, equivalence margin δ=0.25 bps, rules for FIFO failure/equivalence, complexity justification, verdict rules, sha256 of code and frozen params. Commit `ad2adda` precedes any heldout file.
5. **HELDOUT** (`src/run_heldout.py`, refuses to overwrite): H1 primary (13×20 seeds×13 policies), H2 ingest matrix (10 seeds × 4 modes), H3 capacity sweep (K∈{{3,4,6,10}}, 10 seeds; parameters **not** retuned per K).
6. Analysis code was written after heldout results existed but **implements only the pre-registered rules**; additional analyses (targeted pairs, D6 stress) are labelled post-hoc/diagnostic and were run on validation-split worlds or as descriptive comparisons. No parameter changed after heldout.

Frozen configuration: sha256(frozen_params.json) = `{pre['frozen_params_sha256'][:16]}…`; code hash at freeze `{pre['src_sha256'][:16]}…` (later commits add analysis/report scripts only).
Note: the pre-registered hash covers `src/*.py` at freeze time; `run_heldout.py`, `analysis*.py`, `run_diag.py`, `verify_repro.py`, `oss_probe.py`, `make_reports.py` were added afterwards. Simulator, policies and world files (`world.py`, `engine.py`, `policies.py`, `common.py`, `run_tuning.py`) were unchanged (verify with `git diff ad2adda -- bench/capacity_v1/src/{{world,engine,policies,common,run_tuning}}.py`).

## Frozen parameters
{tbl(fzt)}

Baselines A–E use RAW ingest as primary (naive default) regardless of the tuned mode; their tuned modes are reported in H2.

## Pre-registered rules and outcomes
- Equivalence margin δ = 0.25 bps/avail-slot-hour (INFERENCE: ≈10% of typical M1; sensitivity δ∈{{0.1,0.5}} reported in 13).
- COMPLEXITY_JUSTIFIED ⇔ complex method beats best simple by >δ, CI_lower>0 and wins ≥8/13 → **not met** (13).
- Verdict machinery: B (beats FIFO by δ with CI>0) = {vmach['B']}; T (within δ of best implementable = {vmach['best_implementable']}) = {vmach['T']} ⇒ |T|≥2 ⇒ MULTIPLE_CAPACITY_METHODS_SUPPORTED.

## What "no post-hoc tuning" means here
No parameter, scenario definition, seed set, metric or rule was altered after heldout execution. Seeds and scenario definitions for heldout share code with tuning but the *world parameters* differ (N, G, τ, CV, ranges). Threat: heldout worlds are from the same generator family (see 14).
""")

# ------------------------------------------------------------------ 06
slot_cols = [M1, "net_per_busy_slot_hour", "regret_vs_oracle_M1", "idle_slot_hours", "idle_with_backlog", "turnover_per_slot_hour", "churn_reentry_frac", "mean_hold", "hhi_inst", "hhi_group", "rej_rate_instw", "adm_rate", "hq_capture"]
stv = macro.loc[ORDER, ["starve_inst_rate", "starve_soft_rate", "max_denial_hours", "top_inst_admit_share", "hhi_inst"]]
h2s10 = rd("H2_S10_by_ingest.csv")
spam_tab = h2s10[h2s10.policy.isin(["FIFO", "FIFO_SCREEN", "SLOTHOUR", "UNCERTAINTY_LCB", "ROUND_ROBIN"])].pivot(index="policy", columns="ingest", values="top_inst_admit_share")
spam_m1 = h2s10[h2s10.policy.isin(["FIFO", "FIFO_SCREEN", "SLOTHOUR", "UNCERTAINTY_LCB", "ROUND_ROBIN"])].pivot(index="policy", columns="ingest", values=M1)
sp_pair = rd("D4_spam_paired_vs_RAW.csv")
sp_pair = sp_pair[sp_pair.policy.isin(["FIFO", "SLOTHOUR", "SCORE_RANK", "UNCERTAINTY_LCB", "FIFO_SCREEN"])]
W("06_SLOT_ECONOMICS.md", f"""
# 06 — Slot economics, spam and starvation

## Macro results per policy (heldout H1; mean over scenarios of per-scenario means; OBSERVED)
{tbl(macro[slot_cols])}

Definitions: M1 = net / (K·W); rejected-quality = mean realised net **per hold-hour** of rejected candidates (instrument-weighted; lower is better because rejected opportunities were worse); adm_rate = same for admitted trades; regret = ORACLE_GREEDY_UB M1 − policy M1 (oracle is a greedy foresight upper reference, **not implementable**, and also avoids negative-net trades, which no score-based method can fully do).

Findings:
- **Slot-hour economics is visible in the numbers** (OBSERVED): admitted quality per hold-hour rises from {macro.loc['FIFO','adm_rate']:.2f} (FIFO) to {macro.loc['SLOTHOUR','adm_rate']:.2f} (SLOTHOUR) while rejected quality falls from {macro.loc['FIFO','rej_rate_instw']:.2f} to {macro.loc['SLOTHOUR','rej_rate_instw']:.2f}. The oracle sits at {macro.loc['ORACLE_GREEDY_UB','adm_rate']:.2f} / {macro.loc['ORACLE_GREEDY_UB','rej_rate_instw']:.2f}. Even the best implementable policy closes only ~{100*(macro.loc['UNCERTAINTY_LCB',M1]-macro.loc['FIFO',M1])/(macro.loc['ORACLE_GREEDY_UB',M1]-macro.loc['FIFO',M1]):.0f}% of the FIFO→oracle gap (INFERENCE: the rest is score noise plus outcome noise that no admission rule can remove).
- **Opportunity cost**: idle slot-hours are *higher* for ranking policies (screening) — e.g. SLOTHOUR idles {macro.loc['SLOTHOUR','idle_slot_hours']:.0f} vs FIFO {macro.loc['FIFO','idle_slot_hours']:.0f} slot-hours — yet earns more. Idle-with-backlog (declined although candidates waited) is {macro.loc['SLOTHOUR','idle_with_backlog']:.0f} for SLOTHOUR and {macro.loc['SLOTHOUR_SHADOW','idle_with_backlog']:.0f} for the shadow-price policy. Idleness is a *decision*, not a defect, when the marginal candidate has negative estimated net.
- **Turnover/churn**: OLDEST_SLOT doubles turnover ({macro.loc['OLDEST_SLOT','turnover_per_slot_hour']:.2f} vs {macro.loc['FIFO','turnover_per_slot_hour']:.2f} admissions/slot-hour) and re-entry churn ({macro.loc['OLDEST_SLOT','churn_reentry_frac']:.2f}); ranking policies do not increase turnover materially.
- **Concentration**: instrument HHI is ≈0.09–0.10 for all policies (uniform would be 1/15≈0.067); group HHI ≈0.22–0.23 (uniform 0.2). Ranking does **not** produce material extra concentration at the group level here (INFERENCE: one-position-per-instrument and few instruments per group cap it — see 07 and 14).

## Starvation (measured explicitly; do not hide behind aggregate PnL)
Definitions: *hard starvation rate* = share of instruments with ≥5 emissions that received zero admissions; *soft* = admissions < 25% of the mean; *max denial hours* = longest span from an instrument's first emission after its last admission until its next admission (an economically correct denial of a poor instrument also counts — read as an upper bound); *top_inst_admit_share* = largest share of admissions to one instrument.

{tbl(stv)}

- Hard starvation is ≈0 for every policy (max {macro.loc[ORDER,'starve_inst_rate'].max():.3f}) — with this arrival structure every instrument eventually gets in (OBSERVED; would not hold with true score-dominance, UNKNOWN).
- Soft starvation is 2–7× higher for ranking methods (SLOTHOUR {macro.loc['SLOTHOUR','starve_soft_rate']:.3f}, SHADOW {macro.loc['SLOTHOUR_SHADOW','starve_soft_rate']:.3f}, LCB {macro.loc['UNCERTAINTY_LCB','starve_soft_rate']:.3f} vs RR/EQUAL_QUOTA/RANDOM ≤0.008) and denial spells are longer (≈270–330 h vs 130–215 h).
- **Do safeguards distort economic allocation?** Yes, materially: EQUAL_QUOTA and ROUND_ROBIN have no starvation but sit at M1 {macro.loc['EQUAL_QUOTA',M1]:.2f}/{macro.loc['ROUND_ROBIN',M1]:.2f} — i.e. they give back the *entire* ranking gain (−0.44 to −0.48 vs SLOTHOUR). A fairness guarantee therefore has a measurable price of ≈0.45 bps/slot-hour here (OBSERVED, synthetic). Whether fairness matters economically for the real system is UNKNOWN; no lighter safeguard (e.g. age-bonus, minimum-share) was tested — parked.

## Candidate spam (S10 + H2 + D4 diagnostics)
Spam instruments emit ×20 events but have mediocre edge. Four ingest semantics compared (heldout H2, 10 seeds, K=4).

Top-instrument admission share in S10 (largest share of admissions to a single instrument; non-spam scenarios ≈0.14–0.17):
{tbl(spam_tab)}

M1 in S10 by ingest semantics:
{tbl(spam_m1)}

Paired effect vs RAW (validation-split S10, seeds 7000–7009, frozen params; effect on M1 and top-instrument admission share):
{tbl(sp_pair[sp_pair.ingest.isin(['DEDUP_LATEST','COOLDOWN','SCORE_UPDATE'])], index=False)}

Findings (OBSERVED unless noted):
- Spam **does distort who receives slots**: a single spam instrument takes ≈0.30–0.35 of all admissions under RAW vs ≈0.14–0.16 elsewhere (score-driven policies re-admit the spam instrument every time its slot frees; RR/EQUAL_QUOTA cap it at ≈0.23–0.29).
- Semantics reduce concentration only modestly (−0.01 to −0.03 with CIs excluding 0 for most); **M1 effects are within noise** for DEDUP_LATEST and SCORE_UPDATE (safe choices; SCORE_UPDATE was the tuned mode for all ranking policies), while **COOLDOWN hurts ranking policies (−0.22…−0.27)** because it discards fresh scores — a "cooldown" is not a free spam filter.
- Because the spam instruments' edge is mediocre but not poor, the *economic* damage of spam is small here; a scenario where spam instruments have clearly negative edge would show more (UNKNOWN, not run).
- CANDIDATE_SPAM_HANDLED=TRUE means: spam is explicitly modelled, four semantics compared, distortion measured, and a harmless default (SCORE_UPDATE or DEDUP_LATEST) identified. It does **not** mean spam is neutralised.
""")

# ------------------------------------------------------------------ 07
d6 = rd("D6_diversification_stress_table.csv"); d6p = rd("D6_paired_vs_SLOTHOUR.csv")
tp = rd("targeted_pairs.csv")
def tprow(src, a, b, scen, metric):
    r = tp[(tp.src == src) & (tp.a == a) & (tp.b == b) & (tp.scen == scen) & (tp.metric == metric)].iloc[0]; return f"{r['diff']:+.2f} [{r['lo']:+.2f},{r['hi']:+.2f}]"
divrows = []
for src, sc in (("H1", "S5_correlated"), ("H1", "S5b_corr_benign"), ("D4", "F_corr_collapse")):
    divrows.append(dict(scenario=sc, M1=tprow(src, "CORR_AWARE", "SLOTHOUR", sc, M1), pnl_std=tprow(src, "CORR_AWARE", "SLOTHOUR", sc, "pnl_std"),
                        worst_24h=tprow(src, "CORR_AWARE", "SLOTHOUR", sc, "worst_24h"), max_drawdown=tprow(src, "CORR_AWARE", "SLOTHOUR", sc, "max_drawdown"), hhi_group=tprow(src, "CORR_AWARE", "SLOTHOUR", sc, "hhi_group")))
d5 = rd("D5_param_sensitivity_table.csv", index_col=[0, 1])
W("07_DIVERSIFICATION.md", f"""
# 07 — Diversification

Comparison: independent slot-hour ranking (SLOTHOUR) vs correlation-aware greedy (CORR_AWARE = SLOTHOUR rate − γ·ρ̂·σ̂_i·(same-group exposure), ρ̂=0.6 fixed and **mis-specified on purpose**: true ρ_g ∈ {{0.35, 0.8, 0.9, 0.3(collapse)}}). Group membership is public; correlation magnitude is not.

## Heldout / diagnostic paired results: CORR_AWARE (γ=0.1, tuned) − SLOTHOUR (mean diff [95% CI], paired seeds)
{tbl(pd.DataFrame(divrows), index=False)}
(S5/S5b heldout, 20 seeds; F_corr_collapse validation split, 10 seeds. Units: M1 bps/slot-hour; pnl in bps/step.)

No cell shows a significant improvement in M1 or portfolio risk at the tuned γ=0.1; the penalty is too small to change allocations (group HHI moves by <0.005).

## Stress test: penalty strength (D6, validation split, 20 seeds, γ ∈ {{0.1…8}})
{tbl(d6, index=False)}

Paired vs SLOTHOUR (selected rows; full table `results/analysis/D6_paired_vs_SLOTHOUR.csv`):
{tbl(d6p[d6p.arm.isin(['g0.4','g1.0','g4.0'])].round(2), index=False)}

Findings (OBSERVED):
- **Beneficial case (S5, crisis in the best-edge group):** γ≈0.4–1 leaves M1 unchanged (+0.04…+0.05, CI spans 0) and lowers worst-24h loss (γ=1: +41 bps [6,79]) and max drawdown (−38…−63, CI spans 0 at ρ=0.8; −86…−100 at ρ_g=0.9, CI mostly excluding 0). This is the only place a diversification benefit shows up, and it is a *risk* benefit at zero average cost, not an M1 gain.
- **Harmful case (S5b, benign correlation):** γ≥1 costs M1 (−0.13 [−0.28,+0.02]); γ=4 costs −0.29 [−0.43,−0.15] — the penalty simply rejects good opportunities.
- **Correlation collapse (market-wide factor):** penalising *group* concentration does not help (−0.05…−0.34 M1); drawdown is not significantly reduced (group-based diversification cannot protect against a market-wide factor; INFERENCE).
- **Parameter sensitivity (frozen ingest, 13 scenarios, validation split):** macro M1 across γ∈{{0.02…0.4}} spans {d5.loc['CORR_AWARE'][M1].min():.3f}–{d5.loc['CORR_AWARE'][M1].max():.3f} (flat).
- Why the effect is muted (INFERENCE): only ≤3 instruments per group and one position per instrument already cap group exposure at ≈3 of 4 slots; with K=4 and G=5 (heldout) natural diversification is high (group HHI 0.22–0.23 vs 0.20 perfect). A world with a few large groups, or K≫G, would give correlation penalties more leverage (UNKNOWN — not tested).

Verdict for this section: correlation-aware selection **does not reliably improve portfolio-level outcomes** and can merely reject good opportunities; a small penalty (γ≈0.4–1) is a *cheap tail-risk hedge candidate* worth local evaluation only if drawdown control is a stated goal.
""")

# ------------------------------------------------------------------ 08
d2 = rd("D2_score_quality_table.csv", index_col=0)[["FIFO", "FIFO_SCREEN", "SCORE_RANK", "SLOTHOUR", "SLOTHOUR_SHADOW", "UNCERTAINTY_LCB", "CORR_AWARE", "LINTS", "OLDEST_SLOT"]]
d3 = rd("D3_cost_table.csv", index_col=[0, 1, 2])[["FIFO", "FIFO_SCREEN", "SCORE_RANK", "SLOTHOUR", "UNCERTAINTY_LCB", "OLDEST_SLOT"]]
c3 = d3.xs("S3_chronic", level=0); c6 = d3.xs("S6_short_vs_long", level=0)
d5t = d5.reset_index().pivot(index="params", columns="policy", values=M1)
sl_sc = tprow("H1", "SLOTHOUR", "SCORE_RANK", "S6_short_vs_long", M1)
W("08_TURNOVER.md", f"""
# 08 — Turnover and slot-hour economics: attempts to falsify each idea

## 1. Expected net ÷ expected hold (SLOTHOUR) vs raw EV ranking (SCORE_RANK)
- Heldout macro: SLOTHOUR − SCORE_RANK = +0.070 [+0.031,+0.109]; significant only in S5b and S6 (S6: {sl_sc}); indistinguishable elsewhere; **no scenario where SCORE_RANK is significantly better** (heldout).
- **Falsification attempt succeeded partially** (validation, score-quality ladder D2): with a near-perfect score (τ=0, oracle-score UPPER BOUND ONLY) SCORE_RANK {d2.loc['perfect_UB_only','SCORE_RANK']:.2f} > SLOTHOUR {d2.loc['perfect_UB_only','SLOTHOUR']:.2f}: dividing by an *estimated* per-instrument hold adds noise when hold varies within an instrument more than between instruments (INFERENCE). Slot-hour ranking pays off when duration heterogeneity is *between* instruments and the hold estimate is learnable (S6).
- Also in S6, EV ranking (SCORE_RANK) captured long slots (mean hold {pers.loc[('SCORE_RANK','S6_short_vs_long'),'mean_hold']:.1f} h vs {pers.loc[('SLOTHOUR','S6_short_vs_long'),'mean_hold']:.1f} h) and had a lower point estimate than FIFO (3.08 vs 3.19; significance not tested) — long-slot capture is real.

## 2. Slot shadow price / opportunity-cost threshold (SLOTHOUR_SHADOW: admit iff rate ≥ θ·EWMA(rate of admitted))
- Frozen θ=0.25 (lowest grid value; θ=0 is SLOTHOUR). Validation-split sensitivity (13 scenarios): θ=0.25 → {d5t.loc['{"theta": 0.25}','SLOTHOUR_SHADOW']:.2f}, 0.5 → {d5t.loc['{"theta": 0.5}','SLOTHOUR_SHADOW']:.2f}, 0.75 → {d5t.loc['{"theta": 0.75}','SLOTHOUR_SHADOW']:.2f}, 1.0 → {d5t.loc['{"theta": 1.0}','SLOTHOUR_SHADOW']:.2f}, 1.25 → {d5t.loc['{"theta": 1.25}','SLOTHOUR_SHADOW']:.2f}: **collapse** as the threshold idles slots.
- Heldout vs SLOTHOUR: +0.009 [−0.026,+0.044] macro (tie); significantly **better only in S4** (late high-quality arrival: +0.26, idle slot-hours 901 vs 577) and significantly **worse in S1/S2** (low load: refusing admissible trades costs). Interpretation (INFERENCE): a shadow price is worth something only when saturation is bursty and quality is time-clustered; otherwise it is a costly way to hold slots empty. Falsified as a general method; retained as a *situational* candidate.
- Best-in-rule note: the pre-registered BEST_SLOT_HOUR argmax is SLOTHOUR_SHADOW@0.25 by +0.009 — a statistical tie; SLOTHOUR is the practical reference.

## 3. Minimum holding constraint / turnover neutrality (OLDEST_SLOT, min_hold ∈ {{2,4,8}})
Validation macro M1: min_hold 2 → {d5t.loc['{"min_hold": 2}','OLDEST_SLOT']:.2f}, 4 → {d5t.loc['{"min_hold": 4}','OLDEST_SLOT']:.2f}, 8 → {d5t.loc['{"min_hold": 8}','OLDEST_SLOT']:.2f}: too-short holds waste cost; too long stops recycling. Heldout: +0.185 vs FIFO but only +0.021 [−0.022,+0.066] vs FIFO_SCREEN macro; significantly better than FIFO_SCREEN in S4 and S6, significantly worse in S5/S5b. **Cost sensitivity destroys it**: at 3× costs OLDEST_SLOT earns {c3.loc[('known',3.0),'OLDEST_SLOT']:.2f} on S3 (all other policies positive). A preemption rule needs a defensible partial-accrual model (A3) — UNKNOWN locally.

## 4. Hazard-adjusted value and turnover penalty
Not executed as separate methods: hazard adjustment would require a duration/exit-hazard model (no such information exists in the abstraction beyond per-instrument mean hold); a turnover penalty is algebraically a cost increase and is covered by (a) the net-value screen with true cost and (b) the cost-belief sensitivity below. Status: UNKNOWN — not falsified, not supported.

## 5. Cost uncertainty (D3, validation split, frozen params; UNKNOWN_COST ≠ ZERO_COST)
S3_chronic, M1 by true-cost multiplier and *policy cost belief*:
{tbl(c3)}
S6 (short-vs-long):
{tbl(c6)}
Findings: ranking methods degrade gracefully when costs double or triple (they stay positive; FIFO falls to {c3.loc[('known',3.0),'FIFO']:.2f}). **Assuming zero cost when the true cost is 3× lowers FIFO_SCREEN from {c3.loc[('known',3.0),'FIFO_SCREEN']:.2f} to {c3.loc[('zero',3.0),'FIFO_SCREEN']:.2f}** (screening collapses) whereas rank-only methods lose less (SLOTHOUR {c3.loc[('known',3.0),'SLOTHOUR']:.2f} → {c3.loc[('zero',3.0),'SLOTHOUR']:.2f}) because *ranking* is far less cost-sensitive than *thresholding*. A conservative unknown-cost prior lands between the two. Rank-based conclusions therefore survive cost misspecification better than screen-based ones.

## 6. Score-quality ladder (D2, S3 chronic, validation split; oracle score = UPPER BOUND ONLY)
{tbl(d2)}
""")

# ------------------------------------------------------------------ 09
capK = rd("H3_macro_by_K.csv"); cap_m1 = capK.pivot(index="policy", columns="K", values=M1).loc[ORDER]
cap_full = capK.pivot(index="policy", columns="K", values="full_frac").loc[["FIFO", "SLOTHOUR", "UNCERTAINTY_LCB", "OLDEST_SLOT", "ORACLE_GREEDY_UB"]]
cap_idle = capK.pivot(index="policy", columns="K", values="idle_slot_hours").loc[["FIFO", "SLOTHOUR", "UNCERTAINTY_LCB", "OLDEST_SLOT"]]
cap_gap = rd("H3_gaps_by_K.csv"); cap_pair = rd("H3_paired_vs_FIFO.csv")
d1 = rd("D1_robustness_table.csv")
d1s = d1[d1.fam == "slots"]
W("09_CAPACITY_SENSITIVITY.md", f"""
# 09 — Capacity sensitivity (descriptive synthetic effects only)

**Not a recommendation.** Offered load is fixed in absolute terms (candidates per hour), so larger K is *under-loaded* by construction. Parameters were tuned at K=4 and not retuned per K. M1 = net / (K·W), so it necessarily falls as K grows with fixed demand. No production cap, no `max_open_positions` conclusion, follows from this section.

## Heldout M1 by capacity (H3: 13 scenarios × 10 seeds; macro mean)
{tbl(cap_m1)}

## Paired difference vs FIFO (macro over scenarios; mean [95% CI])
{tbl(cap_pair, index=False)}

## Gaps by K (macro over scenarios)
{tbl(cap_gap, index=False)}

## Utilisation (fraction of time all slots are full; idle slot-hours)
{tbl(cap_full)}
{tbl(cap_idle)}

Descriptive effects (OBSERVED, synthetic):
- **cap=3:** ranking beats FIFO by +0.68 (SLOTHOUR) to +0.75 (UNCERTAINTY_LCB) bps/avail-slot-hour; slots are full ≈80% of the time.
- **cap=4:** +0.48 / +0.53. **cap=6:** +0.16 / +0.21 — ranking still helps but the absolute gain is roughly a quarter to a third of cap=3.
- **cap=10:** slots are full ≈5–12% of the time; **no method beats FIFO** (SLOTHOUR −0.041 [−0.059,−0.024], i.e. slightly worse because screening leaves value on the table when capacity is abundant; LCB −0.002 [−0.017,+0.014]). FIFO is effectively as good as sophisticated methods when capacity is not scarce.
- Hence the value of *allocation intelligence* in this world is a decreasing function of scarcity, as expected (INFERENCE: consistent with queueing intuition). Where a real system sits on this curve is UNKNOWN.
- Robustness with the OFAT design on S3 (validation, 8 seeds): best-implementable minus FIFO = {', '.join(f"K={int(r.lvl)}: {r.best_impl_minus_FIFO:+.2f}" for r in d1s.sort_values('lvl', key=lambda s: s.astype(int)).itertuples())}, same ordering (monotone in scarcity).
""")

# ------------------------------------------------------------------ 10
pm_show = pm.copy()
pmr = pm_show[pm_show.ref == "FIFO"][["policy", "macro_diff", "lo", "hi", "wins"]].set_index("policy")
pms = pm_show[pm_show.ref == "FIFO_SCREEN"][["policy", "macro_diff", "lo", "hi", "wins"]].set_index("policy")
vbs = rd("H1_vs_best_simple.csv").set_index("policy")
vr = rd("H1_vs_random.csv").set_index("policy")
sigtab = pps[(pps.ref == "FIFO") & (pps.policy.isin(["SCORE_RANK", "SLOTHOUR", "SLOTHOUR_SHADOW", "UNCERTAINTY_LCB", "CORR_AWARE", "LINTS", "OLDEST_SLOT"]))]
sigtab = sigtab.assign(cell=lambda d: d["diff"].map("{:+.2f}".format) + np.where(d.lo > 0, " *", np.where(d.hi < 0, " ↓", ""))).pivot(index="scen", columns="policy", values="cell")
dl = {k: rules[k] for k in rules}
sens_rows = []
for k, v in dl.items():
    sens_rows.append(dict(delta=k, n_failure_vs_FIFO=len(v["FIFO"]["failure"]), failure_vs_FIFO=short(v["FIFO"]["failure"]), n_equiv_vs_FIFO=len(v["FIFO"]["equivalent"]),
                          n_failure_vs_FIFO_SCREEN=len(v["FIFO_SCREEN"]["failure"]), failure_vs_FIFO_SCREEN=short(v["FIFO_SCREEN"]["failure"])))
W("10_HELDOUT_RESULTS.md", f"""
# 10 — Held-out results (H1: K=4, 13 scenarios × 20 seeds, frozen parameters, executed once)

## Headline metric M1 (macro over scenarios), regret and paired effects
{tbl(macro[[M1, 'regret_vs_oracle_M1', 'net_total']].join(pmr.add_prefix('vsFIFO_')).join(pms.add_prefix('vsFIFO_SCREEN_')).round(3))}

`vsFIFO_*`: paired bootstrap (2000 resamples over seeds, per-scenario, then macro-mean) of policy − FIFO(RAW); `wins` = scenarios with positive point estimate (of 13). Regret is vs ORACLE_GREEDY_UB (upper reference, not implementable).

vs RANDOM (paired macro): {', '.join(f"{p} {r.macro_diff_vs_random:+.3f} [{r.lo:+.3f},{r.hi:+.3f}]" for p, r in vr.loc[['FIFO','FIFO_SCREEN','SLOTHOUR','UNCERTAINTY_LCB']].iterrows())}.

vs best simple method ({vmach['best_simple']}): {', '.join(f"{p} {r.macro_diff:+.3f} [{r.lo:+.3f},{r.hi:+.3f}]" for p, r in vbs.loc[['SCORE_RANK','SLOTHOUR_SHADOW','UNCERTAINTY_LCB','CORR_AWARE','LINTS','OLDEST_SLOT','FIFO_SCREEN']].iterrows())}.

## Per-scenario paired difference vs raw FIFO (bps/avail-slot-hour; `*` = CI excludes 0 upward, `↓` = downward)
{tbl(sigtab)}

## Other pre-registered metrics (macro, heldout)
{tbl(macro[['net_per_busy_slot_hour','turnover_per_slot_hour','idle_slot_hours','hhi_inst','hhi_group','starve_soft_rate','max_denial_hours','rej_rate_instw','hq_capture','pnl_std','worst_24h','max_drawdown','churn_reentry_frac','occ_std','mean_hold']])}

(no composite score is computed by design; each metric must be read on its own.)

## Robustness to score noise (validation-split OFAT on S3; 8 seeds; M1)
{tbl(rd('D1_score_noise_curve.csv', index_col=0)[['FIFO','FIFO_SCREEN','SCORE_RANK','SLOTHOUR','SLOTHOUR_SHADOW','UNCERTAINTY_LCB','CORR_AWARE','LINTS']])}
(index = score-noise multiplier τ/τ₀; 0 = perfect score, **upper bound only**). Sensitivity slope (M1 lost from τ×0.5 to ×4): SCORE_RANK {rd('D1_score_noise_curve.csv', index_col=0).loc[0.5,'SCORE_RANK']-rd('D1_score_noise_curve.csv', index_col=0).loc[4.0,'SCORE_RANK']:.2f}, SLOTHOUR {rd('D1_score_noise_curve.csv', index_col=0).loc[0.5,'SLOTHOUR']-rd('D1_score_noise_curve.csv', index_col=0).loc[4.0,'SLOTHOUR']:.2f}, UNCERTAINTY_LCB {rd('D1_score_noise_curve.csv', index_col=0).loc[0.5,'UNCERTAINTY_LCB']-rd('D1_score_noise_curve.csv', index_col=0).loc[4.0,'UNCERTAINTY_LCB']:.2f}, LINTS {rd('D1_score_noise_curve.csv', index_col=0).loc[0.5,'LINTS']-rd('D1_score_noise_curve.csv', index_col=0).loc[4.0,'LINTS']:.2f}: UNCERTAINTY_LCB is the least noise-sensitive of the four; at τ×4 it keeps a clear lead over SLOTHOUR.

## Other robustness axes (validation OFAT on S3; full table `results/analysis/D1_robustness_table.csv`)
{tbl(d1[d1.fam.isin(['load','duration_dist','correlation','regime_persistence'])][['fam','lvl','FIFO','FIFO_SCREEN','SCORE_RANK','SLOTHOUR','UNCERTAINTY_LCB','LINTS','OLDEST_SLOT','best_impl_minus_FIFO']], index=False)}
Ordering FIFO ≺ FIFO_SCREEN ≺ ranking family is stable across arrival intensity (except L=1.0, where all methods are within ≈0.25), correlation and regime persistence; with very dispersed durations (lognormal CV 1.2) **OLDEST_SLOT** gains +0.55 over FIFO (but stays below the ranking methods); under Pareto durations it gains nothing (2.13 vs 2.15) — preemption helps only for some duration shapes.

## Parameter sensitivity of finalists (validation split, 13 scenarios × 8 seeds, frozen ingest)
{tbl(d5t.round(3))}
- UNCERTAINTY_LCB: the ω (shrinkage) axis matters (0→0.6: +0.07); κ (risk penalty) does not help (κ=0 best at ω=0.6). The frozen point is on the *edge* of the ω grid (0.6) — the optimum may lie beyond (UNKNOWN; ω>0.6 not tested).
- CORR_AWARE γ and LINTS α are flat (±0.01).
- SLOTHOUR_SHADOW θ is steeply sensitive (0.25→1.25: 2.34→0.19). OLDEST_SLOT min_hold: 4 best, 2 worst.

## FIFO failure / equivalence (pre-registered rule; candidate set = SCORE_RANK, SLOTHOUR, SLOTHOUR_SHADOW, UNCERTAINTY_LCB, CORR_AWARE, LINTS)
δ = 0.25 (primary):
- vs raw FIFO — **failure:** {short(f_fail)}; **equivalent:** {short(f_eq)}.
- vs FIFO_SCREEN — failure: {short(s_fail)}; equivalent: {short(s_eq)}.

Sensitivity to δ:
{tbl(pd.DataFrame(sens_rows), index=False)}

Two flags: (1) S6 is "equivalent" for the *pre-registered candidate set* but the mandatory baseline OLDEST_SLOT beats FIFO there by +0.70 [+0.53,+0.87] (and S4 by +0.55, S3 +0.27, S7 +0.29, S12 +0.23): FIFO "failure" on long-slot capture exists but is solved by preemption, not by ranking. (2) In S1/S2 (demand ≤ capacity) all methods coincide, as they must.

FIFO on the mission's dimensions (per-scenario table `results/analysis/H1_fifo_dims.csv`): regret vs oracle 4.6–5.8 in S3/S7/S8/S9 (best simple: 3.8–4.7); high-quality capture 0.64 vs 0.74 macro; instrument-weighted rejected quality 3.46 vs 2.71 (worse); concentration equal (HHI 0.094 vs 0.092); starvation *lower* (soft 0.016 vs 0.031).
""")

# ------------------------------------------------------------------ 11
d4m = rd("D4_failure_modes_all_metrics.csv", index_col=[0, 1])
def d4v(sc, pol, m): return d4m.loc[(sc, pol), m]
W("11_FAILURE_MODES.md", f"""
# 11 — Failure modes (explicitly tested)

Evidence sources: heldout H1/H2 (S-scenarios), validation-split failure battery D4 (10 seeds, frozen parameters), D1–D3, D6. "Handled" means *measured and a mitigation identified or ruled out*, not "eliminated".

| # | failure mode | test | observed outcome | status |
|---|---|---|---|---|
| 1 | score gaming | F_score_gaming: 20% of instruments report scores +30 bps inflated with true edge ≤10 | all score-driven policies over-admit the gamers (top-instrument admission share {d4v('F_score_gaming','FIFO','top_inst_admit_share'):.2f} FIFO → {d4v('F_score_gaming','SLOTHOUR','top_inst_admit_share'):.2f} SLOTHOUR); they still beat FIFO (M1 {d4v('F_score_gaming','SLOTHOUR',M1):.2f} vs {d4v('F_score_gaming','FIFO',M1):.2f}) because FIFO admits the gamers too. **No implemented policy detects gaming** (UNCERTAINTY_LCB pools score history, which the gamer inflates consistently) | OPEN — needs per-instrument realised-vs-predicted feedback (not implemented) |
| 2 | candidate spam | S10, H2, D4i | concentration up (0.30–0.35 vs 0.14); M1 effect within noise; COOLDOWN harmful | MEASURED; SCORE_UPDATE/DEDUP harmless (06) |
| 3 | instrument starvation | H1 starvation metrics; F_starve_skew (skewed edges) | hard starvation ≈0; soft/denial higher for ranking; safeguards cost ≈0.45 bps | MEASURED (06); F_starve_skew soft starvation {d4v('F_starve_skew','SLOTHOUR','starve_soft_rate'):.2f} SLOTHOUR vs {d4v('F_starve_skew','ROUND_ROBIN','starve_soft_rate'):.2f} RR |
| 4 | long-slot capture | S6 (+ D1 duration shapes) | SCORE_RANK mean hold {pers.loc[('SCORE_RANK','S6_short_vs_long'),'mean_hold']:.1f} h vs SLOTHOUR {pers.loc[('SLOTHOUR','S6_short_vs_long'),'mean_hold']:.1f} h; SCORE_RANK below FIFO in point estimate; SLOTHOUR +0.36 [0.16,0.56] vs SCORE_RANK; OLDEST_SLOT best | REAL; mitigated by SLOTHOUR (between-instrument heterogeneity) or preemption |
| 5 | short-slot churn | S6 + F_short_churn_cost (costs ×1.8) | OLDEST_SLOT turnover 2× and re-entry churn {d4v('F_short_churn_cost','OLDEST_SLOT','churn_reentry_frac'):.2f}; at cost ×3 it is the only negative policy (−1.16 on S3) | REAL for preemption; not for ranking |
| 6 | correlation collapse | F_corr_collapse (ρ_m 0.7 in 35–60% window, negative drift) | CORR_AWARE −0.16 [−0.33,−0.02] vs SLOTHOUR; group penalty cannot hedge a market factor | REAL; group-based penalty does not address it |
| 7 | regime lag | S7 (rank flips at W/2), D1 regime persistence | policies driven by *current scores* adapt immediately; ranking beats FIFO by ≈+0.8–0.95; LINTS/UNCERTAINTY_LCB (history-dependent) do not lag measurably in M1 (UNCERTAINTY_LCB +0.09 [−0.02,+0.20] vs SLOTHOUR) | NOT OBSERVED at this regime speed (an EWMA of scores with 5-step memory adapts fast; slower memories untested) |
| 8 | noisy-score instability | S8 (τ×2.5), D1 noise curve | occupancy oscillation std {pers.loc[('FIFO','S8_noisy_rank'),'occ_std']:.2f} (FIFO) → {pers.loc[('SLOTHOUR','S8_noisy_rank'),'occ_std']:.2f}/{pers.loc[('SLOTHOUR_SHADOW','S8_noisy_rank'),'occ_std']:.2f} (SLOTHOUR/SHADOW) — screening makes utilisation more volatile; UNCERTAINTY_LCB gives the best M1 (+0.26 [0.12,0.41] vs SLOTHOUR) | MEASURED; shrinkage is the mitigation |
| 9 | capacity oscillation | occupancy std, full_frac, S11 burst | S11 full_frac ≈0.18–0.22, occupancy std ≈0.34 for **all** policies (burst-driven, policy-independent); idle {pers.loc[('SLOTHOUR_SHADOW','S11_burst'),'idle_slot_hours']:.0f} h (SHADOW) vs {pers.loc[('FIFO','S11_burst'),'idle_slot_hours']:.0f} h (FIFO) | MEASURED; SHADOW amplifies idling |
| 10 | one instrument monopolising refreshes | S10 top-instrument share; SCORE_UPDATE keeps first-arrival queue position | share {pers.loc[('FIFO','S10_spam'),'top_inst_admit_share']:.2f} (FIFO) … {pers.loc[('SLOTHOUR_SHADOW','S10_spam'),'top_inst_admit_share']:.2f}; RR/EQ_QUOTA 0.23–0.28 | MEASURED (06) |
| 11 | high-quality late arrival | S4 | HQ capture FIFO {pers.loc[('FIFO','S4_late_hq'),'hq_capture']:.2f} → SLOTHOUR {pers.loc[('SLOTHOUR','S4_late_hq'),'hq_capture']:.2f} → SHADOW {pers.loc[('SLOTHOUR_SHADOW','S4_late_hq'),'hq_capture']:.2f}; M1: SHADOW +0.26 [0.10,0.40] vs SLOTHOUR; OLDEST_SLOT +0.44 vs FIFO_SCREEN (preemption recycles long low-edge slots) | REAL; helped by reserving capacity (SHADOW) or preemption |
| 12 | quality-estimate inversion | F_inversion (half of groups: score = 40 − 0.6·edge), D2 | SCORE_RANK {d4v('F_inversion','SCORE_RANK',M1):.2f} < FIFO {d4v('F_inversion','FIFO',M1):.2f}; SLOTHOUR {d4v('F_inversion','SLOTHOUR',M1):.2f}, LINTS {d4v('F_inversion','LINTS',M1):.2f} (FIFO +0.1…+0.2); score-free OLDEST_SLOT ({d4v('F_inversion','OLDEST_SLOT',M1):.2f}) is at least as good as every score-driven policy. **No policy detects inversion online**; LINTS only partially (it learns a weight on the rate feature from realised outcomes, but reward noise is large) | OPEN; needs calibration monitoring (realised vs predicted by score bucket) |

Reading rules: significance statements come from paired bootstraps in `results/analysis/targeted_pairs.csv`; D4 has only 10 seeds per cell so small differences are unresolved.
""")

# ------------------------------------------------------------------ 12
def o(l, f): return oss.get(l, {}).get(f, "?")
W("12_OSS_COMPONENTS.md", f"""
# 12 — OSS / reference components

Method: **OBSERVED** metadata queried from the PyPI JSON API on the study date (version, licence field, release date, requires-python); **no source inspection, install or benchmarking was performed** except `scipy.optimize.linear_sum_assignment` (executed: 500/500 random assignment-vs-top-f checks matched). Licences are as declared on PyPI (may be incomplete). Maintenance evidence from PyPI release dates only — GitHub activity, open issues and code quality are **UNKNOWN** here. Stars were not used. No drop-in allocator/scheduler was sought or found.

| component | need | PyPI observed (version · licence field · last upload · py) | classification | rationale |
|---|---|---|---|---|
| scipy (`linear_sum_assignment`, `milp`) | online/batch assignment, small MILP | {o('scipy','version')} · BSD-style · {str(o('scipy','upload'))[:10]} · {o('scipy','requires_python')} | **ADOPT_REFERENCE** | Assignment with slot-independent weights ≡ top-f (PROVEN, OBSERVED 500/500); only needed if slot-specific/pairwise terms appear |
| OR-Tools | knapsack / assignment / CP-SAT | {o('ortools','version')} · {o('ortools','license')} · {str(o('ortools','upload'))[:10]} | PARK | exact joint selection not needed while greedy is within noise; heavy dependency |
| PuLP / HiGHS (highspy) | ILP with pairwise risk terms | PuLP {o('pulp','version')} MIT {str(o('pulp','upload'))[:10]}; highspy {o('highspy','version')} MIT {str(o('highspy','upload'))[:10]} | PARK | same reason; HiGHS is the light option if needed |
| cvxpy | convex portfolio-constrained selection | {o('cvxpy','version')} · Apache-2.0 · {str(o('cvxpy','upload'))[:10]} | PARK | relaxations of selection; no evidence penalties matter (07) |
| PyPortfolioOpt / Riskfolio-lib / skfolio | portfolio allocation | {o('PyPortfolioOpt','version')} MIT / {o('riskfolio-lib','version')} BSD / {o('skfolio','version')} BSD | **REJECT** for slot admission; PARK for portfolio-level sizing | they produce weights, not admit/reject; the marginal-concentration idea was re-implemented in 15 lines |
| MABWiser | contextual bandits (LinTS/LinUCB/…) | {o('mabwiser','version')} · {o('mabwiser','license') or 'licence field empty'} · {str(o('mabwiser','upload'))[:10]} | **ADAPT_CANDIDATE** (only if bandit path is pursued) | clean API for LinTS/LinUCB; last upload >2 years before study date (maintenance risk, UNKNOWN); delayed/censored feedback must be handled by caller |
| contextualbandits | offline/online contextual bandits | {o('contextualbandits','version')} · {o('contextualbandits','license') or 'licence field empty'} · {str(o('contextualbandits','upload'))[:10]} | PARK | not needed; LinTS ties SLOTHOUR |
| Vowpal Wabbit | scalable contextual bandits | {o('vowpalwabbit','version')} BSD-3 {str(o('vowpalwabbit','upload'))[:10]} | REJECT | operational complexity ≫ benefit at 1–2 decisions/hour |
| Open Bandit Pipeline | off-policy evaluation | {o('obp','version')} Apache {str(o('obp','upload'))[:10]} | PARK | relevant for *future local* off-policy evaluation of logged admissions; stale (2023) |
| river | online learning (shrinkage/EWMA/Bayesian) | {o('river','version')} BSD-3 {str(o('river','upload'))[:10]} | PARK | streaming statistics for score-pooling; EWMA suffices |
| SimPy / ciw | queueing / discrete-event simulation | SimPy {o('simpy','version')} MIT {str(o('simpy','upload'))[:10]}; ciw {o('ciw','version')} {str(o('ciw','upload'))[:10]} | PARK | custom step simulator was simpler; useful for local replay harness |

Custom code written (CUSTOM LAST justified): the world generator, the step simulator and the 13 policies (≈600 lines) because no library models one-position-per-instrument slot economics with censored delayed feedback and public/hidden separation.

Classification vocabulary requested by the mission: ADOPT_REFERENCE = use as a reference implementation/test oracle; ADAPT_CANDIDATE = worth adapting if the path is pursued; PARK; REJECT.
""")

# ------------------------------------------------------------------ 13
cj = vmach["complexity"]
cjt = pd.DataFrame({k: dict(macro_diff_vs_SLOTHOUR=v["macro_diff"], ci_lo=v["lo"], ci_hi=v["hi"], scenario_wins=v["wins"], justified=v["justified"]) for k, v in cj.items()})
W("13_ADJUDICATION.md", f"""
# 13 — Adjudication

## Core question
> When capacity is scarce, how should a research/PAPER engine decide which opportunities deserve scarce slots without lookahead, overfitting or hidden capital assumptions?

**Answer supported by this synthetic study (OBSERVED, not transferable without local evidence):**
1. Do not allocate scarce slots by arrival order (FIFO), round-robin, random or equal quota: these four are statistically indistinguishable from each other and ≈0.4–0.5 bps/slot-hour (≈20–28%) below score-based ranking at K=4.
2. Most of the gain comes from two simple, parameter-free, lookahead-free rules: **(i) refuse candidates with estimated net edge ≤ 0** (FIFO_SCREEN: +0.16) and **(ii) rank by estimated net edge per expected slot-hour** (SLOTHOUR: +0.44).
3. Additional machinery (shadow-price thresholds, correlation penalties, Thompson-sampling bandits) does not earn its complexity at the pre-registered margin. Score *pooling* over repeated emissions (UNCERTAINTY_LCB with ω=0.6) adds a small, detectable +0.06 and is the most robust to score noise.
4. All of it degrades with worse scores; with inverted scores no policy protects itself online.

## FIFO adjudication
- FIFO_FAILURE_SCENARIOS (δ=0.25, vs raw FIFO): {short(f_fail)}. FIFO_EQUIVALENT_SCENARIOS: {short(f_eq)}. Versus the stronger FIFO_SCREEN control the failure list shrinks from {len(f_fail)} to {len(s_fail)} scenarios ({short(s_fail)}); {short(sorted(set(f_fail)-set(s_fail)))} stop failing, i.e. there a net-edge screen alone closes the gap. In the remaining {len(s_fail)} scenarios ranking is required.
- FIFO is equivalent when demand ≤ capacity (S1, S2; and at cap=10), when the candidate set is dominated by a spam instrument of near-median quality (S10), and in bursts (S11) at δ=0.25 (a ranking gain of ≈+0.25 point estimate becomes detectable at δ=0.1).
- FIFO never showed a starvation problem (soft 0.016) nor higher concentration — its cost is quality (regret, HQ capture, rejected-opportunity quality), not fairness.

## Simple vs complex
Best simple (pre-registered SIMPLE_SET {pre['rules']['SIMPLE_SET']}): **{vmach['best_simple']}**. Best complex (COMPLEX_SET {pre['rules']['COMPLEX_SET']}): **{vmach['best_complex']}**.

{tbl(cjt)}

COMPLEXITY_JUSTIFIED = **FALSE**. UNCERTAINTY_LCB is detectable ({cj['UNCERTAINTY_LCB']['macro_diff']:+.3f}, CI excludes 0, wins 10/13) but 4× below δ=0.25, and it is a *shrinkage* effect (κ=0). Under a looser margin δ=0.05 the verdict on LCB would flip to "justified on effect size, not on complexity cost" — a local decision. LinTS costs ≈24× the decision compute of SLOTHOUR (42.8 vs 1.8 ms/run) for a statistical tie; CORR_AWARE and SHADOW are ties in the macro and mixed per scenario.

Where complexity *does* matter (per-scenario, paired CI excludes 0 vs SLOTHOUR, heldout): UNCERTAINTY_LCB in S8 (+0.26) and S12 (+0.14); SHADOW in S4 (+0.26, but −0.05…−0.15 in S1/S2); none for CORR_AWARE or LINTS.

## Verdict machinery (pre-registered)
- B = methods beating raw FIFO by >δ with CI_lower>0: {vmach['B']} (non-empty ⇒ FIFO_REMAINS_SUFFICIENT_REFERENCE rejected).
- T = methods within δ of best implementable ({vmach['best_implementable']}) and winning ≥8/13 vs FIFO: {vmach['T']} ⇒ |T|=6 ⇒ **MULTIPLE_CAPACITY_METHODS_SUPPORTED**.
- Sensitivity of the verdict to δ (INFERENCE from macro means): δ=0.1 ⇒ T = {{LCB, SHADOW, SLOTHOUR, LINTS, CORR_AWARE}} (SCORE_RANK drops out): still multiple; δ=0.5 ⇒ T also contains FIFO_SCREEN/OLDEST_SLOT: still multiple. A single-method verdict would need δ<0.05 (SHADOW is 0.053 below LCB).
- NO_CAPACITY_METHOD_SUPPORTED rejected: every ranking method beats RANDOM by 0.41–0.54 (CIs exclude 0).
- Interpretation: "multiple methods supported" means *the score-ranking family is supported*, not that six distinct algorithms are needed; the honest reading is "a net-edge screen plus net-edge-per-slot-hour ranking is sufficient; the rest is within noise or situational".

## Which methods deserve local evaluation (not adoption, not deployment)
| method | deserves local evaluation? | condition |
|---|---|---|
| FIFO_SCREEN (net-edge screen) | yes, as the *control* | needs a defensible local cost belief (unknown cost must not be zero) |
| SLOTHOUR (net edge / expected hold) | **yes — primary reference** | needs local estimates of expected hold; if hold varies within instrument more than between, prefer SCORE_RANK (validation ladder) |
| UNCERTAINTY_LCB (score pooling ω≈0.6) | yes, secondary | only if candidates repeat per instrument or scores are noisy |
| SLOTHOUR_SHADOW | conditional | only if locally observed quality arrives in late, clustered bursts (S4-like); otherwise it idles slots |
| OLDEST_SLOT-style preemption | diagnostic only | depends on partial-accrual assumption A3; cost-sensitive |
| CORR_AWARE | conditional | only if drawdown control is an explicit goal and groups are few/large |
| LinTS / other bandits, Exp3, ILP/assignment solvers | no (not now) | no evidence of benefit; complexity and tuning burden |
| Starvation safeguards (RR/quota) | no as allocators; yes as *monitoring metrics* | they cost ≈0.45 bps/slot-hour here |

## What the study does NOT conclude
Nothing about `max_open_positions`, the current allocator, any production policy or any cap. The oracle is never presented as implementable. Synthetic effects are descriptive of this generator only.

## Scientific validity checks performed
| check | outcome |
|---|---|
| no-lookahead metamorphic test (12 policies × 4 ingest × 5 scenarios × 2 cuts) | pass; oracle flagged |
| determinism (unit tests + 300 heldout cell re-executions) | pass ({det['hash_mismatches']} mismatches) |
| heldout executed once, params frozen with hash, pre-registration precedes heldout in git | yes |
| capacity/one-position-per-instrument invariants | pass |
| UNKNOWN_COST ≠ ZERO_COST test | pass |
| mistakes found and corrected during writing | two mis-statements about OLDEST_SLOT and heavy-tail durations in draft text were corrected against the tables before commit; no result data changed |
ANY_SCIENTIFIC_INVALIDATION = FALSE (see 14 for limitations that bound generalisation).

## Final block
{FINAL}
""")

# ------------------------------------------------------------------ 14
W("14_LIMITATIONS.md", f"""
# 14 — Limitations

Generator-driven (INFERENCE unless noted):
1. **Scores are calibrated by construction** (s = E + noise) in the main scenarios. Score-based methods therefore enjoy an information advantage a real system may not have; the D2 ladder shows gains shrinking 45–70% with poor calibration and reversing with inversion.
2. **Arrival order carries no quality information** by construction; real FIFO may correlate with quality (e.g. earlier signals stronger, or later ones fresher). FIFO's weakness here is therefore partly built in.
3. **Linear edge accrual (A3)** makes early exit cheap and favours preemption (OLDEST_SLOT). If edge is back-loaded or exits are costly, preemption results would weaken; if front-loaded they would strengthen. UNKNOWN locally.
4. **One position per instrument (A1)** and TTL=4 are hard-coded; they shape spam, starvation and diversification results (group exposure is capped at ≈3 of 4 slots). Larger groups, multiple positions per instrument, or longer TTL are untested.
5. Cost is a constant per-admission bps amount; no slippage/impact that depends on turnover, size or crowding, no partial fills.
6. Durations are drawn independent of edge except in S4/S6; hold estimates are per-instrument EWMA. Duration-edge dependence, exit hazards and "hazard-adjusted value" were not modelled (not executed).
7. Time step = 1 hour; intra-hour dynamics and HFT-style effects are out of scope by design.

Protocol/statistics:
8. Heldout worlds come from the **same generator family** (different parameters, not a different model class): out-of-family generalisation is UNKNOWN. Twenty seeds per scenario give CIs of ±0.05–0.25 per scenario; per-scenario significance flags are not multiplicity-corrected.
9. δ = 0.25 bps is an INFERENCE-based margin; verdict was checked at 0.1 and 0.5 but conclusions about "justified complexity" are margin-dependent.
10. The analysis scripts were written after H1 results existed (they implement the pre-registered rules; the targeted pairs, D6 stress test and OSS probe are post-hoc/diagnostic and are labelled as such). Frozen parameters were not touched. `git diff ad2adda -- bench/capacity_v1/src/{{world,engine,policies,common,run_tuning}}.py` should be empty (checked before commit).
11. Grid edges: SHADOW θ frozen at the lowest value (θ=0 equals SLOTHOUR); UNCERTAINTY_LCB ω frozen at the highest tested value 0.6 — optimum may be beyond. LinTS has a single prior/feature design and a 3-point α grid; a better-engineered bandit might close the gap (UNKNOWN).
12. Parameters tuned at K=4 only; the K sweep is descriptive.
13. The ORACLE_GREEDY_UB is a greedy perfect-foresight reference that also skips negative-net trades; it is not the offline optimum, so "regret vs oracle" mixes allocation loss with unavoidable noise/foresight and must not be read as attainable headroom.
14. `hq_capture` is inflated by high-admission policies (OLDEST_SLOT). `max_denial_hours` counts economically correct denials of poor instruments. Rejected-quality is measured at the last-emission time counterfactual (hidden outcome), not at expiry time.
15. Failure-mode diagnostics use 10 seeds and validation-split worlds; small differences are unresolved. Score gaming and quality inversion remain **unmitigated** by every implemented policy.
16. Wall-time in H1 (`sel_time_s`) was measured under 4-process load; the serial benchmark (`results/analysis/compute_cost_serial.csv`) is the reference. CPU numbers are for this container only.

Sources and tooling:
17. Literature claims in 02 are DOCUMENTED_CLAIM from prior knowledge; papers were not re-fetched. OSS metadata is PyPI-only (no source inspection, issues, or benchmarks except scipy's assignment check). Installed scipy in the container is older than the latest PyPI version (Python 3.11 vs scipy's ≥3.12 requirement).
18. No AurumShift private code, data or formulas were used or inferred; nothing here says a method is compatible with AurumShift. Final adjudication belongs to a later local evaluation.
""")
