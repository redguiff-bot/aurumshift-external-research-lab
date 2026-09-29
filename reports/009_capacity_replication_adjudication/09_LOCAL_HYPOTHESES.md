# 09 — Local falsification shortlist

Purpose: hypotheses worth testing later against **AurumShift's own evidence**, in a local, PAPER-safe, read-only or replay setting. This report authorises no test, no integration and no change. The hypotheses come from what the two synthetic studies agree on; every one can be wrong locally, and each is written so that it can be **falsified** by local data.

Ranking rule: prefer what replicates in both studies (05), then what is cheap to check with data a system like this already produces.

## Replicated in both studies

### H1′ — Arrival-order admission wastes scarce slots relative to net-value ranking
- Wording differs from the mission's H1 on purpose. Both studies agree that **net-value ranking beats FIFO when demand exceeds capacity**. They do *not* agree that FIFO is worse than random (A: slightly, because of a decay assumption; B: tied), so the claim is about ranking, not about randomness.
- Effect to expect if it transfers: 20% of FIFO value (B), 2.7× FIFO's normalised value (A). Both vanish when demand ≤ capacity (S1; B at K=10).
- **Falsified locally if**: over a period with candidates ≥ free slots, replaying candidate logs shows that the estimated-net ranking's top-k has no higher realised (or shadow-realised) net than the arrival-order top-k, with paired CI including zero.
- Needs: candidate log with arrival time, score at decision time, cost estimate, and eventual outcome (or a counterfactual-safe proxy). Depends on **whether local arrival order carries quality information**, which both studies assume it does not (B limitation 2).

### H2 — An estimated-net screen (score − cost > 0) captures a material share of the gain
- Both: material (B 45%, A 65% of the ranking gain), world-dependent (33% to 72% in A's own worlds). Rises as cost approaches edge.
- **Falsified locally if**: rejecting candidates with estimated net ≤ 0 removes no losers (rejected-candidate realised net not lower than admitted), or the local cost estimate is too poor to define a sign. UNKNOWN cost must not be treated as zero (both studies test this; B's D3 shows a `zero` cost belief costs `FIFO_SCREEN` about 0.3–0.5 bps at 2×–3× cost).
- Needs: a defensible local per-trade cost estimate.

### H5 — Bandit and correlation-penalty machinery is unnecessary absent local evidence
- Both: bandits tie or lose (B −0.020, A −0.013 to −0.029) at ≈24× compute; correlation penalties do not move net value (B −0.022 n.s., A 0.000 to +0.004). Modest drawdown/PnL-dispersion reductions in both.
- **Falsified locally if**: a simple ranking shows concentrated drawdown attributable to correlated simultaneous admissions that a group penalty demonstrably removes without lowering net value. This is a *risk* hypothesis, not a return one.
- Needs: local group/cluster definitions and realised co-movement.

## Partially replicated — test only if the cheap ones pass

### H3′ — Ranking by estimated net (optionally divided by expected hold) is a sufficient simple reference
- Both: net ranking is the reference; dividing by hold adds +0.07 (B, driven by a strongly heterogeneous S6) and ≈0 (A). So the sufficient reference is *net ranking*, with hold normalisation as an option whose value depends on hold heterogeneity.
- **Falsified locally if**: hold-duration dispersion is small relative to value dispersion (then normalisation is noise), or if net-per-slot-hour ranking changes admissions materially and improves realised net (then it is worth having).
- Needs: local distribution of realised hold durations, by instrument.

### H4 — Uncertainty pooling helps mainly when repeated scores are noisy
- Both: a small positive gain over simple ranking (B +0.062, A +0.010 for pooling, +0.025 for the composite), strongest under noisy or repeated scores (B: S8 +0.26, S12 +0.14). B shows the gain is shrinkage (κ=0), not a risk penalty.
- **Falsified locally if**: repeated emissions of the same candidate are not noisier than between-candidate dispersion, or pooling reduces top-k realised quality.
- Needs: repeated-score history per instrument.

## Conditional — do not test until cost/edge data exists

### H6 (new) — Preemption is beneficial only when net edge per trade is large relative to per-trade cost
- Both simulators agree on the *mechanism* (07 D1): positive at low cost, negative at 3× cost, and the sign flips within a factor of ≈3. Their headline signs disagree because their worlds sit on opposite sides.
- **Falsified locally if** the measured edge/cost ratio is below the switching point in either direction, or the forced-close cost is not the same as the entry cost.
- Note the danger: an exit rule is not an allocator and could change realised behaviour; this stays research-only, replay-only.

## Not proposed
- Any capacity value, any allocator deployment, any cap experiment. The K sweeps are synthetic sensitivity (08 §8).
- Shadow-price, knapsack, LinTS/LinUCB, sleeping experts, ILP solvers: no replicated benefit.
- Starvation safeguards (RR, quota) as allocators: cost about 0.12–0.13 dz in A and 0.4–0.5 bps in B relative to net ranking; keep as monitoring metrics only.

## Local prerequisites common to all (from both studies' limitations)
1. Score calibration and its drift (both assume calibrated-by-construction scores; B shows the ranking advantage shrinks ≈45–47% when calibration is poor).
2. Whether arrival order carries information.
3. Real cost per admission and per forced close, and their dependence on turnover.
4. Realised hold distribution and its relationship to edge.
5. A paired, no-lookahead replay harness, which both studies show how to test (metamorphic prefix invariance).
