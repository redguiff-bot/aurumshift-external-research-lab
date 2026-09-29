# 12 — Adjudication

Labels: **PROVEN** (checked by construction/test on the simulator), **OBSERVED** (measured in the synthetic study), **INFERENCE**, **UNKNOWN**. Everything about real trading behaviour is UNKNOWN: this is a synthetic falsification study, not evidence about any venue.

## 1. Pre-registered verdict (machine output of `heldout_verdict.py`, rules committed before the run)
`CAPACITY_ALLOCATION_REFERENCE_SUPPORTED`, reference method `COMPOSED` (calibrated lower-confidence-bound value, staleness hazard, per-hold-hour density, fluid quantile threshold; correlation penalty tuned to zero).

## 2. What that verdict does and does not say
* **OBSERVED.** For each of the four pre-registered methods (the three shortlisted ones and `RANK_NET`), the paired gain over FIFO has a bootstrap CI above zero in all 60 (family, cap) cells (in S1 the gain is ≈ 0.01, i.e. equivalent), and no cell is materially worse than FIFO. Pooled gain of the reference over FIFO: +0.171 dz (CI 0.161–0.182), over `FIFO_NETPOS` +0.081, over plain net-EV ranking (`RANK_NET`) **+0.023 (CI 0.020–0.027)**.
* **The decomposition matters more than the label** (OBSERVED pooled dz vs FIFO, 0.171 total for `COMPOSED`): pure filtering of negative-value opportunities (`FIFO_NETPOS`) 0.090; ranking by estimated net value (`RANK_NET`) 0.148; opportunity-cost thresholds (`SHADOW_PRICE`, `ONLINE_KNAPSACK_PSI`, `FLUID_QUANTILE`) 0.161–0.164; the full composition 0.171. Post-hoc (validation worlds): freshest-first with the filter alone (`LIFO_NETPOS`) is within 0.008 dz of `RANK_NET`. In this environment about half of the gain over FIFO is "don't take negative-value opportunities and don't take the stalest one first"; value ranking adds a further 0.058 (about a third); thresholds another 0.013–0.016; the composition's incremental value over plain ranking (0.023) is about an eighth of the total.
* **The margin is thin and sensitive.** `COMPOSED` beats `RANK_NET` by 0.023 against a pre-registered bar of 0.02; `SHADOW_PRICE` (+0.016) and `ONLINE_KNAPSACK_PSI` (+0.015) miss the bar by 0.004–0.005 and differ from `COMPOSED` by <0.01. Sensitivity (computed offline from the same held-out output, *not* a pre-registered alternative): with `δ_equivalence = 0.03`, no shortlist method beats `RANK_NET` by the bar, all three are equivalent to it, and the rule returns `MULTIPLE_CAPACITY_METHODS_SUPPORTED`. With `δ_equivalence = 0.02` (pre-registered) it returns the reference verdict. The honest summary: **a family of opportunity-cost/threshold methods, all within ~0.01 dz of each other and ≈ 0.02 above simple net-EV ranking, is supported; the single "reference" label rests on a 0.003 margin.**
* **`COMPOSED` is the only method that handles candidate spam and score gaming (10), and the most fragile under high score noise** (it drops below `RANK_NET` at score noise sd ≥ 30 with per-instrument heterogeneity). If the score is trustworthy, a threshold rule (`SHADOW_PRICE`) is at least as good and simpler; if the score is gameable, the calibration is what protects. That trade-off is the actual finding.

## 3. Answers to the mission's research question
"When capacity is scarce, how should a research/PAPER engine decide which opportunities deserve scarce slots without lookahead, overfitting or hidden capital assumptions?" — within this synthetic scope:
1. Admit only what has positive estimated **net** value after **explicit costs**, imputing UNKNOWN_COST conservatively (never 0) — worth 0.090 dz by itself.
2. Prefer **fresh** and higher-net-value candidates; do not serve by arrival order.
3. Add an **opportunity-cost threshold** that lets a slot idle when the best available candidate is marginal (shadow price / online-knapsack threshold / fluid quantile): +0.013…+0.016 dz beyond ranking, larger at tighter capacity and higher load.
4. If scores are attacker- or model-generated, calibrate them causally **per instrument** using outcomes at close (hierarchical shrinkage); this alone stops spam/gaming failures.
5. Correlation: use a **soft** penalty (correlation-only or marginal-risk); it lowers volatility and drawdown at ~zero expected-value cost; hard rejects and static cluster caps mainly reject good opportunities.
6. Explicit turnover mechanics (forced early exits) are not supported except as a small, high-margin, long-minimum-hold swap (+0.005); the churn baseline is strongly negative.
7. Bandits, sleeping experts, and secretary rules: **not supported** here (below plain ranking, or worse).

## 4. Falsification ledger
| Claim tried | Outcome |
|---|---|
| FIFO is a sufficient reference | Falsified in 13/15 families (vs FIFO); largely a filter+freshness effect (vs `FIFO_NETPOS`: only 5 families exceed 0.10: S12, S10, S3, H3, H1) |
| Per-slot-hour density ranking beats raw EV | Not supported alone (+0.002); supported only as thresholded opportunity-cost pricing |
| Correlation penalties improve the portfolio | Supported for risk (soft penalties); hard rejects/caps falsified (reject good opps) |
| Correlation matters for the gain of `MARGINAL_RISK` | Partly falsified: own-variance/duration term drives the value gain (post-hoc) |
| Turnover (forced exits) helps | Falsified for churn (`OLDEST_SLOT`), marginal for `EVICT_SWAP` |
| Bandits are appropriate | Falsified vs plain ranking (except negative calibration slope) |
| Missing score ≠ negative evidence | Not distinguishable from rejecting it in this environment |
| UNKNOWN_COST may be treated as 0 | Falsified (−0.004 dz at 10 %, −12 % value at 70 % unknown) |
| Sophisticated rules always beat FIFO | Falsified when the score is uninformative/negatively calibrated (all score-based rules ≈ or < FIFO) |
| The oracle is an upper bound | Falsified for `ORACLE_SCORE`/`ORACLE_DENSITY` (greedy oracles are beaten by threshold methods); only the hindsight LP is a bound |

## 5. Scientific integrity items
* **`ANY_SCIENTIFIC_INVALIDATION`**: *none for the final held-out verdict.* **Run 1 was invalidated before any held-out data existed** (covariance-estimator warm-up bias, shrinkage too strong, normaliser blow-up) and is disclosed and archived in `results/superseded_run1/`; the leakage-test harness itself had a boundary bug (arrivals at t0) that produced 28 false alarms before it was fixed. The pre-registered rules and thresholds were set on the new scale after seeing *validation* results, never held-out results.
* Not invalidated but limiting: three variants per family (so the CIs reflect seed variance within 45 parameter draws, not the full variance of scenario design); several tuned knobs on grid edges; 92 configurations tuned; oracles that are not bounds; all conclusions conditional on assumed edge-decay, score-noise and duration models.
* The pull request for the first, partial state of this branch was merged by someone else while the study was still running; the study was completed on the branch re-created from `main` (this PR). Nothing in the study changed because of that.

## 6. Final block
```
ALGORITHMS_DISCOVERED=36
ALGORITHMS_EXECUTED=29 policies in the held-out grid (27 implementable + 2 upper-bound oracles); + 2 post-hoc diagnostics, 1 leakage canary, 1 library bandit (MABWiser), solver/simulator cross-checks (SciPy HiGHS/LSA, OR-Tools CP-SAT, SimPy)

HELDOUT_SCENARIOS=15 families (S1–S12 + H1–H3) x 3 variants = 45 scenario instances x 4 capacity levels; 52,200 runs
SEEDS=10 per scenario instance (9000–9009) => 450 held-out worlds; tuning 3 (1000–1002), validation 4 (2000–2003), robustness 5 (3000–3004), failure 6 (4000–4005)

FIFO_FAILURE_SCENARIOS=13: H1_chronic_corr_regime, H2_burst_noisy_missing, H3_spam_fastslow, S2_moderate, S3_chronic, S4_late_quality, S5_correlated, S7_regime_shift, S8_noisy_ranking, S9_missing_quality, S10_spam, S11_burst, S12_all_equal  (mostly filter+freshness; see 09)
FIFO_EQUIVALENT_SCENARIOS=1: S1_sparse   (S6_short_vs_long is between: +0.086, below the 0.10 bar)

BEST_SLOT_HOUR_REFERENCE=SHADOW_PRICE (opportunity-cost/bid-price threshold; statistically tied with ONLINE_KNAPSACK_PSI and FLUID_QUANTILE; SLOTHOUR_DENSITY alone is not distinguishable from RANK_NET)
BEST_DIVERSIFICATION_REFERENCE=CORR_PENALTY (correlation-only soft penalty; MARGINAL_RISK scores higher but part of its gain is an own-variance/duration effect)
BEST_TURNOVER_REFERENCE=SHADOW_PRICE (no forced exits); EVICT_SWAP is the only explicit-turnover rule with a positive sign (+0.005) and OLDEST_SLOT is falsified

CAP3_SYNTHETIC_RESULT=FIFO 0.158 / RANK_NET 0.660 / COMPOSED 0.791 bps per slot-hour (LP bound 1.445); COMPOSED +0.224 dz vs FIFO
CAP4_SYNTHETIC_RESULT=FIFO 0.161 / RANK_NET 0.619 / COMPOSED 0.708 (LP bound 1.260); +0.195 dz
CAP6_SYNTHETIC_RESULT=FIFO 0.162 / RANK_NET 0.552 / COMPOSED 0.602 (LP bound 1.006); +0.157 dz   [synthetic sensitivity only; no production cap recommended; max_open_positions is not to be raised on this basis]

NO_LOOKAHEAD_PROVEN=YES within tested scope (27 implementable policies x 5 scenario cases: counterfactual-latent and future-truncation tests, 0 failures; leaky canary detected 5/5; static audit clean)
CANDIDATE_SPAM_HANDLED=PARTIAL — handled by calibrated methods (COMPOSED −22 % under 3 spam opps/h; UNCERTAINTY_LCB); plain ranking and shadow-price rules are not (−72 % / −59 %); no identity/dedup rule was tested
STARVATION_MEASURED=YES — zero for simple EV ranking; non-zero for bandits/secretary and for other instruments under a gamed instrument

ANY_DROP_IN_ALLOCATOR=NO
ANY_SCIENTIFIC_INVALIDATION=NO for the final verdict (run 1 invalidated pre-held-out and superseded; disclosed in 04, 12, 13)

FINAL_VERDICT=CAPACITY_ALLOCATION_REFERENCE_SUPPORTED
```
