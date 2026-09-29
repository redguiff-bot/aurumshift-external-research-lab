# 00 — Executive summary

Mission: `AURUMSHIFT_EXTERNAL_RISK_CAPACITY_AND_TURNOVER_ALLOCATION_V1` — external research only; no private AurumShift code read; no integration; **this is not permission to increase `max_open_positions`** and it recommends no production cap. Evidence labels per `claude.md`; every number is OBSERVED on a synthetic simulator unless stated.

## What was done
* A deterministic capacity simulator (fixed slot count, Poisson/MMPP/periodic/burst/spam arrivals, heterogeneous instruments, correlated returns, stochastic durations, stale/noisy/missing quality estimates, regime shifts) with generic explicit net-outcome accounting (UNKNOWN_COST ≠ 0). Validated against Erlang-B (max error 0.020) and an independent SimPy run.
* 36 algorithm ideas catalogued (02); **29 policies executed** on a pre-registered held-out protocol: 5 mandatory baselines, 5 controls/ablations (`FIFO_NETPOS`, raw/net ranking, cost/missing-evidence ablations), 17 candidate methods, 2 oracles (upper-bound references only). External libraries were *executed*, not just read (SciPy/HiGHS, OR-Tools, SimPy, MABWiser, River, PyPortfolioOpt, scikit-learn, CVXPY): 11.
* Tuning (3 seeds) → validation (4 seeds) → **pre-registered** held-out: 15 scenario families (S1–S12 + 3 unseen compositions) × 3 variants × 10 seeds × 4 slot counts = 52,200 runs. Plus robustness sweeps (9 axes), failure-mode probes, explicit leakage tests, post-hoc diagnostics (flagged).

## Headline findings
1. **FIFO is not a sufficient reference in 13 of 15 families; it is equivalent only when demand is sparse (S1).** But a large part of that is not "sophistication": FIFO with a net-positive filter recovers 0.090 of the 0.171 dz that the best method gains; a post-hoc freshest-first + filter control comes within 0.008 dz of plain net-value ranking. In this simulator FIFO loses because it (a) admits negative-value opportunities, (b) serves the stalest candidate first while edge decays, (c) cannot decline marginal candidates when slots are scarce.
2. **Pre-registered verdict: `CAPACITY_ALLOCATION_REFERENCE_SUPPORTED` — reference `COMPOSED`** (calibrated LCB value + staleness hazard + per-hold-hour density + fluid quantile threshold), +0.171 dz vs FIFO, **+0.023 dz vs plain net-EV ranking** (bar 0.02). **The margin is thin**: opportunity-cost threshold rules (`SHADOW_PRICE`, `ONLINE_KNAPSACK_PSI`, `FLUID_QUANTILE`) sit within ≈ 0.01 of it; with a 0.03 equivalence margin the same data returns `MULTIPLE_CAPACITY_METHODS_SUPPORTED`.
3. **Slot economics — opportunity-cost thresholds are what help beyond ranking.** The winners leave 6–14 percentage points more slot-hours idle, hold positions ≈ 1.6–2.1 h shorter, and capture more value per available slot-hour. Value-per-expected-hold-hour ranking alone is not distinguishable from net-EV ranking (+0.002 dz).
4. **Diversification.** A *soft* correlation penalty (`CORR_PENALTY`) lowers daily-PnL volatility (−7 bps) and drawdown (−42) at no expected-value cost; a marginal-risk penalty helps more but partly through an own-variance/duration effect (post-hoc). *Hard* correlation rejection and static cluster caps mostly reject good opportunities (−0.016 / −0.006 dz on the correlated families S5/H1) — the mission's suspicion is confirmed for those. Under a correlation-collapse stress the soft penalty halves tail risk; the cap does not.
5. **Turnover.** Forced churn is bad (`OLDEST_SLOT` −0.218 dz vs ranking, ≈155 forced exits per run); a value-triggered swap with a long minimum hold is marginal (+0.005). Bandits, sleeping experts and the 1/e secretary rule are **not supported** (≤ plain ranking).
6. **Capacity sensitivity (synthetic only).** The value of a smart allocator falls monotonically with slot count (`COMPOSED` vs FIFO: +0.224 / +0.195 / +0.157 / +0.107 dz at C = 3/4/6/10; vs plain ranking +0.042 → +0.008). No production cap can be inferred.
7. **Failure modes.** Candidate spam and score gaming devastate plain score ranking (−72 % / −59 % at high spam; ranking becomes negative under score gaming) and are neutralised only by per-instrument causal calibration (`COMPOSED` −22 %). `COMPOSED` is the *fragile* choice under very noisy scores. **No method adapts to a permanent regime change within 500 h.** If the score is uninformative or negatively calibrated, score-based rules are no better than FIFO.
8. **No lookahead (PROVEN within tested scope).** 27 implementable policies × 5 cases, counterfactual-latent and future-truncation tests, 0 failures; a deliberately leaky canary is detected 5/5.

## Integrity notes
A first full run was superseded before any held-out data existed (covariance-estimator warm-up bias, over-strong shrinkage, a normaliser that exploded on near-identical scenarios), found via the OSS cross-check and pre-registration review; v1 is archived and disclosed. The leakage-test boundary bug that produced false alarms is disclosed in 04. The first partial state of this branch was merged (PR #6) by someone else mid-study; the completed study is in the follow-up PR.

## Final block
See `12_ADJUDICATION.md` §6 (same block reproduced below).
```
ALGORITHMS_DISCOVERED=36
ALGORITHMS_EXECUTED=29 held-out policies (27 implementable + 2 upper-bound oracles) + diagnostics/probes (see 12)

HELDOUT_SCENARIOS=15 families x 3 variants (45 instances) x 4 capacity levels
SEEDS=10 per instance (9000–9009); 450 held-out worlds; 52,200 runs

FIFO_FAILURE_SCENARIOS=13 (H1,H2,H3,S2,S3,S4,S5,S7,S8,S9,S10,S11,S12)
FIFO_EQUIVALENT_SCENARIOS=1 (S1)

BEST_SLOT_HOUR_REFERENCE=SHADOW_PRICE (tied with ONLINE_KNAPSACK_PSI, FLUID_QUANTILE)
BEST_DIVERSIFICATION_REFERENCE=CORR_PENALTY (soft, correlation-only)
BEST_TURNOVER_REFERENCE=SHADOW_PRICE (no forced exits)

CAP3_SYNTHETIC_RESULT=FIFO 0.158 / RANK_NET 0.660 / COMPOSED 0.791 bps per slot-hour
CAP4_SYNTHETIC_RESULT=FIFO 0.161 / RANK_NET 0.619 / COMPOSED 0.708
CAP6_SYNTHETIC_RESULT=FIFO 0.162 / RANK_NET 0.552 / COMPOSED 0.602   (synthetic sensitivity only; no cap recommended)

NO_LOOKAHEAD_PROVEN=YES (within tested scope)
CANDIDATE_SPAM_HANDLED=PARTIAL (calibrated methods only)
STARVATION_MEASURED=YES

ANY_DROP_IN_ALLOCATOR=NO
ANY_SCIENTIFIC_INVALIDATION=NO for the final verdict (run 1 superseded before held-out; disclosed)

FINAL_VERDICT=CAPACITY_ALLOCATION_REFERENCE_SUPPORTED
```
