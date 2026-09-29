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
