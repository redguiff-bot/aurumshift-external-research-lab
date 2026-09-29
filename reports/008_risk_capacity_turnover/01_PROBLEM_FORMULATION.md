# 01 — Problem formulation

Mission `AURUMSHIFT_EXTERNAL_RISK_CAPACITY_AND_TURNOVER_ALLOCATION_V1`. External research only: no private AurumShift code was read, no integration is proposed, nothing here is a production cap recommendation. Evidence labels follow `claude.md` (PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN); every number in this report is **OBSERVED on a synthetic simulator** unless stated otherwise, and synthetic ≠ real.

## The decision problem (generic)
* `C` identical position slots (C ∈ {3,4,6,10} as *synthetic sensitivity only*).
* Time is discrete (1 step = 1 hour). Opportunities ("opps") arrive at a stochastic rate, wait in a pending pool for at most `ttl = 3` steps (then are lost), and at every step an allocator may admit at most `free` of them.
* An admitted opp holds its slot for a stochastic duration (lognormal, or heavy-tailed Pareto in the robustness sweeps). No early exit, except where a policy is allowed to *force-close* a position (the eviction policies) and pays an explicit extra cost.
* Heterogeneous instruments (12, in 2–4 correlation clusters), each with its own mean edge, mean duration, volatility, fee/slippage and score-noise level.
* **At admission time** the allocator sees only `View(cid, inst, cluster, side, age, score, score_age, cost, dur_hat)`; `score` and `dur_hat` are noisy, possibly missing (NaN), possibly stale; `cost` may be UNKNOWN (NaN). It also receives (a) the instrument returns of steps ≤ t−1 and (b) the realised net outcome of a position **when that position closes**.
* **Never visible**: true edge, true duration, true cost, future returns, outcome of rejected/never-admitted opps.

## Generic net-outcome abstraction (no private formulas)
```
net = edge_at_admission * (hold/duration)        # expected drift, pro-rata, decays with waiting: edge * exp(-age/tau)
    + side * Σ instrument returns over the hold  # market noise; instruments share cluster factors -> correlation
    - cost_true                                   # explicit fee+slippage, always > 0
    - evict_extra                                 # only when force-closed early
```
* `UNKNOWN_COST != ZERO_COST`: unknown cost is *observed* as NaN and the true cost is never zero. Policies must impute (running mean of known costs) or reject; an ablation `RANK_NET_UNKCOST_ZERO` shows what treating it as zero costs (see 12).
* Two evaluation quantities: `real_*` uses the realised random path; `lat_*` (latent) uses the expected edge without market noise, so it is far less noisy. **Primary metric = latent expected net outcome per slot-hour** (`lat_per_slot_hour`, bps/slot-hour), normalised for cross-scenario pooling by the run's root-mean-square opportunity value density (`dz`), always paired against a reference policy on identical worlds (common random numbers).

## What "slot economics" means here
Slot-hour = one slot occupied for one hour. A policy is judged by outcome per **available** slot-hour (idle slots count as lost capacity), not per trade. Rejected opportunities are counted **per unique opportunity** (`opp_id`), not per re-evaluation: the pending pool re-shows the same opp up to 4 times, and the simulator measures `evals_per_opp` ≈ 3.0 on average over the held-out set (1.0 in S1, 3.6–3.8 in the chronic/spam families), so a raw "reject count" overstates independent rejections roughly threefold; that is the "13,000 repeated rejects ≠ 13,000 opportunities" point in miniature, and every rejected-opportunity metric below is per unique opp.

## Scope limits (also in 13)
* Allocation of *slots*, not position sizing. `max_open_positions` is a parameter of the simulator, **not** a recommendation; nothing here says the cap should move.
* Synthetic environment written by the researcher: it can falsify ideas but cannot validate them for any real venue.
