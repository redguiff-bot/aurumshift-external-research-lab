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
10. The analysis scripts were written after H1 results existed (they implement the pre-registered rules; the targeted pairs, D6 stress test and OSS probe are post-hoc/diagnostic and are labelled as such). Frozen parameters were not touched. `git diff ad2adda -- bench/capacity_v1/src/{world,engine,policies,common,run_tuning}.py` should be empty (checked before commit).
11. Grid edges: SHADOW θ frozen at the lowest value (θ=0 equals SLOTHOUR); UNCERTAINTY_LCB ω frozen at the highest tested value 0.6 — optimum may be beyond. LinTS has a single prior/feature design and a 3-point α grid; a better-engineered bandit might close the gap (UNKNOWN).
12. Parameters tuned at K=4 only; the K sweep is descriptive.
13. The ORACLE_GREEDY_UB is a greedy perfect-foresight reference that also skips negative-net trades; it is not the offline optimum, so "regret vs oracle" mixes allocation loss with unavoidable noise/foresight and must not be read as attainable headroom.
14. `hq_capture` is inflated by high-admission policies (OLDEST_SLOT). `max_denial_hours` counts economically correct denials of poor instruments. Rejected-quality is measured at the last-emission time counterfactual (hidden outcome), not at expiry time.
15. Failure-mode diagnostics use 10 seeds and validation-split worlds; small differences are unresolved. Score gaming and quality inversion remain **unmitigated** by every implemented policy.
16. Wall-time in H1 (`sel_time_s`) was measured under 4-process load; the serial benchmark (`results/analysis/compute_cost_serial.csv`) is the reference. CPU numbers are for this container only.

Sources and tooling:
17. Literature claims in 02 are DOCUMENTED_CLAIM from prior knowledge; papers were not re-fetched. OSS metadata is PyPI-only (no source inspection, issues, or benchmarks except scipy's assignment check). Installed scipy in the container is older than the latest PyPI version (Python 3.11 vs scipy's ≥3.12 requirement).
18. No AurumShift private code, data or formulas were used or inferred; nothing here says a method is compatible with AurumShift. Final adjudication belongs to a later local evaluation.
