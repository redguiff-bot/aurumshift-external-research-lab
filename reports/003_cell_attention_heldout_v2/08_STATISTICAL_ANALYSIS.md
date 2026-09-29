# 08 — Statistical analysis

Code: `src/analysis.py` (seed 20260929; 10 000 bootstrap resamples). Data: the 1 200 held-out runs (05). Full outputs: `results/heldout_analysis/{analysis.json, pooled_table.md, pairwise_table.md, dominance_table.md, per_scenario_tables.md}`.

## 1. Method (pre-registered in `protocol.json` before Phase B)

* **Pairing.** Every policy faces the identical environment for a given `(scenario, seed)` (common random numbers), so comparisons are **paired by seed within scenario**.
* **Pooling.** For a metric, the pooled difference is the mean over the scenarios where the metric is defined of the within-scenario mean paired difference; its 95 % interval comes from a hierarchical bootstrap that resamples the 20 seeds *within each scenario* (independently) and re-averages. Scenarios are treated as a **fixed** set: intervals quantify **seed-level** uncertainty only, *not* the uncertainty about how the policies would behave on other scenario families. This is the main reason no "generalises" claim is made anywhere (11).
* **Effect sizes.** `d_z` = mean/sd of the pooled paired differences; Cliff's δ = P(X>Y) − P(X<Y) over pooled per-seed values. Practical thresholds per metric (`protocol.json`): info_ratio 0.03, starvation 0.02, stale 0.03, silent excess 0.03, coverage 0.03, adaptation delay 10 cycles, Gini 0.05, first-attempt delay 2 cycles, rare discovery 0.05, low-information excess 0.03, degraded excess 0.02, max starvation 10 cycles.
* **Categories** (no p-values): `DISTINGUISHABLE+MEANINGFUL` (CI excludes 0 **and** |Δ| ≥ threshold) · `STATISTICALLY_DISTINGUISHABLE` (CI excludes 0, |Δ| below threshold — real but too small to matter) · `PRACTICALLY_MEANINGFUL(CI includes 0)` · `INCONCLUSIVE`.
* **Multiple comparisons.** 150 pooled pairwise comparisons were computed; no correction is applied because no single p-value is used for a decision — decisions rest on effect size vs threshold and on the scenario-wise dominance count below. With 20 seeds and CRN the intervals are narrow, so "statistically distinguishable" is cheap; **the practical threshold is the binding criterion**.

Tally over the 150 pooled comparisons: 106 `DISTINGUISHABLE+MEANINGFUL`, 33 `STATISTICALLY_DISTINGUISHABLE` (too small to matter), 1 `PRACTICALLY_MEANINGFUL (CI includes 0)`, **10 `INCONCLUSIVE`**: `A–R` on coverage, starvation, adaptation delay and rare discovery; `A–B` on max starvation duration; `B–D` and `C–D` on adaptation delay; `C–C2` on first-attempt delay; `C–D` and `D–C2` on rare discovery.

## 2. Headline paired comparisons (pooled; Δ = X − Y)

| Comparison | Metric | Δ [95 % CI] | Category | Reading |
|---|---|---|---|---|
| A vs R | info_ratio | +0.001 [+0.001, +0.002] | STATISTICALLY_DISTINGUISHABLE (below threshold) | **A ≡ round-robin for practical purposes** on information; INCONCLUSIVE on coverage, starvation, adaptation delay, rare discovery |
| B vs A | info_ratio | +0.141 [+0.138, +0.144] | DISTINGUISHABLE+MEANINGFUL | B > A in 10/10 scenarios and 20/20 seeds in each |
| B vs A | starvation_rate | +0.005 [+0.005, +0.005] | STATISTICALLY_DISTINGUISHABLE (below 0.02) | B's cost vs A is real but below the practical threshold |
| B vs A | adapt_delay | −100.8 [−106.1, −95.4] | DISTINGUISHABLE+MEANINGFUL | A never adapts (censored) |
| B vs A | silent_excess | −0.033 | DISTINGUISHABLE+MEANINGFUL | B allocates *less* than uniform to silent cells; A slightly more |
| B vs C2 | info_ratio | −0.108 [−0.111, −0.105] | DISTINGUISHABLE+MEANINGFUL | C2 better on information |
| B vs C2 | new_ttfa_median | −34.0 [−35.3, −32.7] | DISTINGUISHABLE+MEANINGFUL | B far faster on new cells |
| B vs C2 | adapt_delay | −32.2 [−41.6, −23.2] | DISTINGUISHABLE+MEANINGFUL | B adapts faster (pooled over S2/S3/S9) |
| B vs C | starvation_rate | −0.142 [−0.144, −0.141] | DISTINGUISHABLE+MEANINGFUL | B ≪ C |
| B vs D | info_ratio | −0.079 [−0.085, −0.073] | DISTINGUISHABLE+MEANINGFUL | D better on information |
| B vs D | starvation_rate | −0.068 [−0.072, −0.065] | DISTINGUISHABLE+MEANINGFUL | B far less starvation |
| B vs D | adapt_delay | −3.4 [−13.4, +6.9] | INCONCLUSIVE | adaptation equivalent |
| C vs D | info_ratio | +0.016 [+0.010, +0.021] | STATISTICALLY_DISTINGUISHABLE (below threshold) | equivalent information; D far less starvation (−0.074) |

## 3. Dominance check (scenario × core-metric cells; practical thresholds)

For every ordered pair (X, Y): over the core metrics that are meaningful in each scenario (information, starvation, stale, coverage, max starvation in all 10; silent excess in S4/S5/S9; adaptation delay in S2/S3/S9; degraded excess in S2/S3; first-attempt delay in S1/S10; low-information excess in S7; rare discovery in S8; 62 cells), count the cells where X is practically better, practically worse, equal. **X dominates Y only if X is practically worse in zero cells and better in a substantial share.**

| X vs Y | X practically better | X practically worse | equal | X worse on |
|---|---|---|---|---|
| A>B | 9 | 25 | 28 | info_ratio@S1, info_ratio@S2, info_ratio@S3, info_ratio@S4, info_ratio@S5, info_ratio@S6, info_ratio@S7, info_ratio@S8, info_ratio@S9, info_ratio@S10… |
| A>C | 46 | 15 | 1 | info_ratio@S1, info_ratio@S2, info_ratio@S3, info_ratio@S4, info_ratio@S5, info_ratio@S6, info_ratio@S7, info_ratio@S8, info_ratio@S9, info_ratio@S10… |
| A>D | 43 | 18 | 1 | info_ratio@S1, info_ratio@S2, info_ratio@S3, info_ratio@S4, info_ratio@S5, info_ratio@S6, info_ratio@S7, info_ratio@S8, info_ratio@S9, info_ratio@S10… |
| A>C2 | 23 | 17 | 22 | info_ratio@S1, info_ratio@S2, info_ratio@S3, info_ratio@S4, info_ratio@S5, info_ratio@S6, info_ratio@S7, info_ratio@S8, info_ratio@S9, info_ratio@S10… |
| A>R | 4 | 12 | 46 | max_starvation_duration@S1, max_starvation_duration@S2, max_starvation_duration@S3, max_starvation_duration@S4, max_starvation_duration@S5, max_starvation_duration@S6, max_starvation_duration@S7, max_starvation_duration@S8, max_starvation_duration@S9, max_starvation_duration@S10… |
| B>A | 25 | 9 | 28 | starvation_rate@S5, starvation_rate@S9, stale_rate@S9, coverage_W@S5, coverage_W@S9, max_starvation_duration@S5, max_starvation_duration@S9, degraded_excess_post@S3, rare_discovery_rate@S8 |
| B>C | 51 | 11 | 0 | info_ratio@S1, info_ratio@S2, info_ratio@S3, info_ratio@S4, info_ratio@S6, info_ratio@S7, info_ratio@S8, info_ratio@S10, adapt_delay@S9, degraded_excess_post@S2… |
| B>D | 46 | 11 | 5 | info_ratio@S1, info_ratio@S2, info_ratio@S4, info_ratio@S6, info_ratio@S7, info_ratio@S8, info_ratio@S9, info_ratio@S10, adapt_delay@S9, degraded_excess_post@S2… |
| B>C2 | 31 | 12 | 19 | info_ratio@S1, info_ratio@S2, info_ratio@S3, info_ratio@S4, info_ratio@S5, info_ratio@S6, info_ratio@S7, info_ratio@S8, info_ratio@S9, info_ratio@S10… |
| B>R | 19 | 12 | 31 | starvation_rate@S5, starvation_rate@S9, stale_rate@S9, coverage_W@S5, coverage_W@S9, max_starvation_duration@S1, max_starvation_duration@S4, max_starvation_duration@S5, max_starvation_duration@S9, max_starvation_duration@S10… |
| C>A | 15 | 46 | 1 | starvation_rate@S1, starvation_rate@S2, starvation_rate@S3, starvation_rate@S4, starvation_rate@S5, starvation_rate@S6, starvation_rate@S7, starvation_rate@S8, starvation_rate@S9, starvation_rate@S10… |
| C>B | 11 | 51 | 0 | info_ratio@S5, info_ratio@S9, starvation_rate@S1, starvation_rate@S2, starvation_rate@S3, starvation_rate@S4, starvation_rate@S5, starvation_rate@S6, starvation_rate@S7, starvation_rate@S8… |
| C>D | 8 | 44 | 10 | info_ratio@S5, info_ratio@S9, starvation_rate@S1, starvation_rate@S2, starvation_rate@S3, starvation_rate@S4, starvation_rate@S5, starvation_rate@S6, starvation_rate@S8, starvation_rate@S9… |
| C>C2 | 7 | 47 | 8 | info_ratio@S5, info_ratio@S9, starvation_rate@S1, starvation_rate@S2, starvation_rate@S3, starvation_rate@S4, starvation_rate@S5, starvation_rate@S6, starvation_rate@S7, starvation_rate@S8… |
| C>R | 14 | 46 | 2 | starvation_rate@S1, starvation_rate@S2, starvation_rate@S3, starvation_rate@S4, starvation_rate@S5, starvation_rate@S6, starvation_rate@S7, starvation_rate@S8, starvation_rate@S9, starvation_rate@S10… |
| D>A | 18 | 43 | 1 | starvation_rate@S1, starvation_rate@S2, starvation_rate@S3, starvation_rate@S4, starvation_rate@S5, starvation_rate@S6, starvation_rate@S7, starvation_rate@S8, starvation_rate@S9, starvation_rate@S10… |
| D>B | 11 | 46 | 5 | starvation_rate@S1, starvation_rate@S2, starvation_rate@S3, starvation_rate@S4, starvation_rate@S5, starvation_rate@S6, starvation_rate@S7, starvation_rate@S8, starvation_rate@S9, starvation_rate@S10… |
| D>C | 44 | 8 | 10 | info_ratio@S1, info_ratio@S2, info_ratio@S3, info_ratio@S4, info_ratio@S6, info_ratio@S8, adapt_delay@S9, degraded_excess_post@S2 |
| D>C2 | 8 | 43 | 11 | info_ratio@S1, info_ratio@S3, info_ratio@S4, info_ratio@S5, info_ratio@S8, info_ratio@S9, starvation_rate@S1, starvation_rate@S2, starvation_rate@S3, starvation_rate@S4… |
| D>R | 16 | 42 | 4 | starvation_rate@S1, starvation_rate@S2, starvation_rate@S3, starvation_rate@S4, starvation_rate@S5, starvation_rate@S6, starvation_rate@S7, starvation_rate@S8, starvation_rate@S9, starvation_rate@S10… |
| C2>A | 17 | 23 | 22 | starvation_rate@S5, starvation_rate@S9, stale_rate@S4, stale_rate@S5, stale_rate@S9, coverage_W@S1, coverage_W@S2, coverage_W@S3, coverage_W@S4, coverage_W@S5… |
| C2>B | 12 | 31 | 19 | starvation_rate@S5, starvation_rate@S9, stale_rate@S4, stale_rate@S5, coverage_W@S1, coverage_W@S2, coverage_W@S3, coverage_W@S4, coverage_W@S5, coverage_W@S6… |
| C2>C | 47 | 7 | 8 | info_ratio@S1, info_ratio@S6, info_ratio@S7, info_ratio@S8, adapt_delay@S9, degraded_excess_post@S2, lowinfo_excess@S7 |
| C2>D | 43 | 8 | 11 | info_ratio@S7, coverage_W@S10, adapt_delay@S2, adapt_delay@S3, adapt_delay@S9, new_ttfa_median@S1, new_ttfa_median@S10, lowinfo_excess@S7 |
| C2>R | 16 | 29 | 17 | starvation_rate@S5, starvation_rate@S9, stale_rate@S4, stale_rate@S5, stale_rate@S9, coverage_W@S1, coverage_W@S2, coverage_W@S3, coverage_W@S4, coverage_W@S5… |
| R>A | 12 | 4 | 46 | degraded_excess_post@S2, new_ttfa_median@S1, new_ttfa_median@S10, lowinfo_excess@S7 |
| R>B | 12 | 19 | 31 | info_ratio@S1, info_ratio@S2, info_ratio@S3, info_ratio@S4, info_ratio@S5, info_ratio@S6, info_ratio@S7, info_ratio@S8, info_ratio@S9, info_ratio@S10… |
| R>C | 46 | 14 | 2 | info_ratio@S1, info_ratio@S2, info_ratio@S3, info_ratio@S4, info_ratio@S5, info_ratio@S6, info_ratio@S7, info_ratio@S8, info_ratio@S10, adapt_delay@S2… |
| R>D | 42 | 16 | 4 | info_ratio@S1, info_ratio@S2, info_ratio@S3, info_ratio@S4, info_ratio@S5, info_ratio@S6, info_ratio@S7, info_ratio@S8, info_ratio@S9, info_ratio@S10… |
| R>C2 | 29 | 16 | 17 | info_ratio@S1, info_ratio@S2, info_ratio@S3, info_ratio@S4, info_ratio@S5, info_ratio@S6, info_ratio@S7, info_ratio@S8, info_ratio@S9, info_ratio@S10… |

Result: for **every** ordered pair the number of cells where X is practically worse is > 0 (minimum 4, for `R>A`). In particular `B>A` has 25 better / 9 worse / 28 equal cells (B is worse on starvation, coverage, max starvation and stale rate in S5/S9, on S3 degraded excess and on S8 rare discovery) and `C2>B` has 12 better / 31 worse. **ANY_POLICY_DOMINATES_ACROSS_HELDOUT = NO** — a direct count of the table above under the stated thresholds.

## 4. Distinguishing the three categories for the main claims

| Claim | Category |
|---|---|
| B improves information gain over A | STATISTICALLY_DISTINGUISHABLE **and** PRACTICALLY_MEANINGFUL (large effect, consistent sign in all 200 scenario-seeds) |
| A differs from round-robin on information | STATISTICALLY_DISTINGUISHABLE but **not** practically meaningful |
| C starves / is captured by silent cells | STATISTICALLY_DISTINGUISHABLE **and** PRACTICALLY_MEANINGFUL (starvation +0.147 over A; S9 silent excess +0.264) |
| B is slightly less covering than A | STATISTICALLY_DISTINGUISHABLE, not practically meaningful (0.005 starvation; coverage −0.016) |
| B vs D adaptation, C vs D information, A vs R coverage | INCONCLUSIVE (equivalent within thresholds) |
| River guard (C2) vs B on information | STATISTICALLY_DISTINGUISHABLE **and** PRACTICALLY_MEANINGFUL, but with opposite sign on new-cell latency and return recovery (trade-off, not superiority) |

## 5. Limits (UNKNOWN / not covered)

Scenario-family uncertainty; dependence on the V2-defined lifecycle classifier for A; 20 seeds × 10 fixed scenarios; a single synthetic reward model; no correction for 150 comparisons; timing measured under 4-way parallel load; cross-machine determinism untested. Nothing here upgrades OBSERVED synthetic results to PROVEN general claims.

## Appendix — all 150 pooled pairwise comparisons

| metric | pair X vs Y | Δ=X−Y pooled [95% CI] | d_z | Cliff δ | category | better |
|---|---|---|---|---|---|---|
| info_ratio | A vs B | -0.141 [-0.144,-0.138] | -2.17 | -1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| info_ratio | A vs C | -0.235 [-0.243,-0.228] | -1.94 | -0.94 | DISTINGUISHABLE+MEANINGFUL | Y |
| info_ratio | A vs D | -0.220 [-0.227,-0.213] | -2.10 | -1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| info_ratio | A vs C2 | -0.249 [-0.254,-0.244] | -3.19 | -1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| info_ratio | A vs R | +0.001 [+0.001,+0.002] | +0.09 | +0.05 | STATISTICALLY_DISTINGUISHABLE | X |
| info_ratio | B vs C | -0.094 [-0.101,-0.088] | -0.81 | -0.67 | DISTINGUISHABLE+MEANINGFUL | Y |
| info_ratio | B vs D | -0.079 [-0.085,-0.073] | -1.14 | -0.75 | DISTINGUISHABLE+MEANINGFUL | Y |
| info_ratio | B vs C2 | -0.108 [-0.111,-0.105] | -2.59 | -1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| info_ratio | B vs R | +0.142 [+0.139,+0.145] | +2.04 | +1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| info_ratio | C vs D | +0.016 [+0.010,+0.021] | +0.18 | +0.43 | STATISTICALLY_DISTINGUISHABLE | X |
| info_ratio | C vs C2 | -0.013 [-0.018,-0.009] | -0.14 | +0.27 | STATISTICALLY_DISTINGUISHABLE | Y |
| info_ratio | C vs R | +0.237 [+0.229,+0.244] | +1.82 | +0.93 | DISTINGUISHABLE+MEANINGFUL | X |
| info_ratio | D vs C2 | -0.029 [-0.034,-0.024] | -0.59 | -0.48 | STATISTICALLY_DISTINGUISHABLE | Y |
| info_ratio | D vs R | +0.221 [+0.214,+0.228] | +1.98 | +1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| info_ratio | C2 vs R | +0.250 [+0.245,+0.255] | +3.01 | +1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| coverage_W | A vs B | +0.016 [+0.016,+0.017] | +0.52 | +0.29 | STATISTICALLY_DISTINGUISHABLE | X |
| coverage_W | A vs C | +0.402 [+0.399,+0.404] | +6.42 | +1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| coverage_W | A vs D | +0.241 [+0.233,+0.249] | +2.68 | +1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| coverage_W | A vs C2 | +0.170 [+0.169,+0.171] | +3.72 | +1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| coverage_W | A vs R | -0.000 [-0.000,+0.000] | -0.07 | -0.01 | INCONCLUSIVE | Y |
| coverage_W | B vs C | +0.385 [+0.383,+0.388] | +5.85 | +1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| coverage_W | B vs D | +0.225 [+0.217,+0.233] | +2.45 | +1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| coverage_W | B vs C2 | +0.154 [+0.152,+0.155] | +5.81 | +1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| coverage_W | B vs R | -0.016 [-0.017,-0.016] | -0.52 | -0.30 | STATISTICALLY_DISTINGUISHABLE | Y |
| coverage_W | C vs D | -0.161 [-0.169,-0.152] | -2.08 | -0.99 | DISTINGUISHABLE+MEANINGFUL | Y |
| coverage_W | C vs C2 | -0.232 [-0.234,-0.229] | -3.93 | -1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| coverage_W | C vs R | -0.402 [-0.404,-0.399] | -6.42 | -1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| coverage_W | D vs C2 | -0.071 [-0.079,-0.064] | -0.79 | -0.49 | DISTINGUISHABLE+MEANINGFUL | Y |
| coverage_W | D vs R | -0.241 [-0.249,-0.233] | -2.68 | -1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| coverage_W | C2 vs R | -0.170 [-0.171,-0.169] | -3.72 | -1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| starvation_rate | A vs B | -0.005 [-0.005,-0.005] | -0.49 | -0.20 | STATISTICALLY_DISTINGUISHABLE | X |
| starvation_rate | A vs C | -0.147 [-0.149,-0.145] | -3.52 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| starvation_rate | A vs D | -0.073 [-0.077,-0.069] | -1.74 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| starvation_rate | A vs C2 | -0.015 [-0.015,-0.015] | -0.56 | -0.31 | STATISTICALLY_DISTINGUISHABLE | X |
| starvation_rate | A vs R | -0.000 [-0.000,+0.000] | -0.10 | -0.01 | INCONCLUSIVE | X |
| starvation_rate | B vs C | -0.142 [-0.144,-0.141] | -3.40 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| starvation_rate | B vs D | -0.068 [-0.072,-0.065] | -1.61 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| starvation_rate | B vs C2 | -0.010 [-0.011,-0.010] | -0.59 | -0.31 | STATISTICALLY_DISTINGUISHABLE | X |
| starvation_rate | B vs R | +0.005 [+0.005,+0.005] | +0.49 | +0.19 | STATISTICALLY_DISTINGUISHABLE | Y |
| starvation_rate | C vs D | +0.074 [+0.070,+0.078] | +1.67 | +0.96 | DISTINGUISHABLE+MEANINGFUL | Y |
| starvation_rate | C vs C2 | +0.132 [+0.130,+0.134] | +2.79 | +1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| starvation_rate | C vs R | +0.147 [+0.145,+0.149] | +3.52 | +1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| starvation_rate | D vs C2 | +0.058 [+0.054,+0.062] | +1.21 | +0.83 | DISTINGUISHABLE+MEANINGFUL | Y |
| starvation_rate | D vs R | +0.073 [+0.069,+0.077] | +1.74 | +1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| starvation_rate | C2 vs R | +0.015 [+0.015,+0.015] | +0.56 | +0.31 | STATISTICALLY_DISTINGUISHABLE | Y |
| max_starvation_duration | A vs B | +0.140 [-0.710,+1.015] | +0.01 | +0.41 | INCONCLUSIVE | Y |
| max_starvation_duration | A vs C | -239.740 [-243.935,-235.570] | -5.49 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| max_starvation_duration | A vs D | -180.790 [-186.770,-174.790] | -3.28 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| max_starvation_duration | A vs C2 | -30.230 [-31.470,-29.075] | -0.67 | -0.45 | DISTINGUISHABLE+MEANINGFUL | X |
| max_starvation_duration | A vs R | +22.920 [+21.585,+24.130] | +2.32 | +0.98 | DISTINGUISHABLE+MEANINGFUL | Y |
| max_starvation_duration | B vs C | -239.880 [-244.080,-235.655] | -4.68 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| max_starvation_duration | B vs D | -180.930 [-186.935,-175.030] | -3.07 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| max_starvation_duration | B vs C2 | -30.370 [-31.215,-29.655] | -1.40 | -0.99 | DISTINGUISHABLE+MEANINGFUL | X |
| max_starvation_duration | B vs R | +22.780 [+21.740,+23.605] | +0.82 | +0.97 | DISTINGUISHABLE+MEANINGFUL | Y |
| max_starvation_duration | C vs D | +58.950 [+51.545,+66.330] | +0.96 | +0.64 | DISTINGUISHABLE+MEANINGFUL | Y |
| max_starvation_duration | C vs C2 | +209.510 [+205.295,+213.730] | +3.35 | +1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| max_starvation_duration | C vs R | +262.660 [+258.315,+266.890] | +5.81 | +1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| max_starvation_duration | D vs C2 | +150.560 [+144.565,+156.540] | +2.25 | +1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| max_starvation_duration | D vs R | +203.710 [+197.625,+209.860] | +3.63 | +1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| max_starvation_duration | C2 vs R | +53.150 [+52.740,+53.540] | +1.18 | +1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| stale_rate | A vs B | -0.008 [-0.008,-0.007] | -0.63 | -0.40 | STATISTICALLY_DISTINGUISHABLE | X |
| stale_rate | A vs C | -0.228 [-0.230,-0.226] | -3.68 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| stale_rate | A vs D | -0.123 [-0.129,-0.118] | -1.93 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| stale_rate | A vs C2 | -0.020 [-0.021,-0.020] | -0.67 | -0.40 | STATISTICALLY_DISTINGUISHABLE | X |
| stale_rate | A vs R | -0.000 [-0.000,-0.000] | -0.46 | -0.17 | STATISTICALLY_DISTINGUISHABLE | X |
| stale_rate | B vs C | -0.221 [-0.223,-0.218] | -3.68 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| stale_rate | B vs D | -0.116 [-0.121,-0.110] | -1.83 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| stale_rate | B vs C2 | -0.013 [-0.013,-0.012] | -0.57 | -0.33 | STATISTICALLY_DISTINGUISHABLE | X |
| stale_rate | B vs R | +0.007 [+0.007,+0.007] | +0.63 | +0.40 | STATISTICALLY_DISTINGUISHABLE | Y |
| stale_rate | C vs D | +0.105 [+0.099,+0.111] | +1.81 | +0.98 | DISTINGUISHABLE+MEANINGFUL | Y |
| stale_rate | C vs C2 | +0.208 [+0.205,+0.210] | +3.29 | +1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| stale_rate | C vs R | +0.228 [+0.226,+0.230] | +3.68 | +1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| stale_rate | D vs C2 | +0.103 [+0.097,+0.108] | +1.56 | +0.98 | DISTINGUISHABLE+MEANINGFUL | Y |
| stale_rate | D vs R | +0.123 [+0.117,+0.128] | +1.93 | +1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| stale_rate | C2 vs R | +0.020 [+0.020,+0.021] | +0.67 | +0.40 | STATISTICALLY_DISTINGUISHABLE | Y |
| silent_excess | A vs B | +0.033 [+0.033,+0.034] | +0.60 | +0.30 | DISTINGUISHABLE+MEANINGFUL | Y |
| silent_excess | A vs C | -0.031 [-0.035,-0.027] | -0.40 | -0.16 | DISTINGUISHABLE+MEANINGFUL | X |
| silent_excess | A vs D | +0.016 [+0.013,+0.019] | +0.47 | +0.25 | STATISTICALLY_DISTINGUISHABLE | Y |
| silent_excess | A vs C2 | +0.034 [+0.034,+0.035] | +0.60 | +0.30 | DISTINGUISHABLE+MEANINGFUL | Y |
| silent_excess | A vs R | +0.009 [+0.009,+0.009] | +0.64 | +0.30 | STATISTICALLY_DISTINGUISHABLE | Y |
| silent_excess | B vs C | -0.064 [-0.068,-0.060] | -0.51 | -0.30 | DISTINGUISHABLE+MEANINGFUL | X |
| silent_excess | B vs D | -0.017 [-0.021,-0.015] | -0.47 | -0.29 | STATISTICALLY_DISTINGUISHABLE | X |
| silent_excess | B vs C2 | +0.001 [+0.001,+0.001] | +0.47 | +0.30 | STATISTICALLY_DISTINGUISHABLE | Y |
| silent_excess | B vs R | -0.025 [-0.025,-0.024] | -0.56 | -0.30 | STATISTICALLY_DISTINGUISHABLE | X |
| silent_excess | C vs D | +0.047 [+0.042,+0.051] | +0.47 | +0.27 | DISTINGUISHABLE+MEANINGFUL | Y |
| silent_excess | C vs C2 | +0.065 [+0.061,+0.069] | +0.51 | +0.30 | DISTINGUISHABLE+MEANINGFUL | Y |
| silent_excess | C vs R | +0.039 [+0.035,+0.044] | +0.45 | +0.26 | DISTINGUISHABLE+MEANINGFUL | Y |
| silent_excess | D vs C2 | +0.019 [+0.016,+0.022] | +0.48 | +0.30 | STATISTICALLY_DISTINGUISHABLE | Y |
| silent_excess | D vs R | -0.007 [-0.010,-0.004] | -0.28 | -0.15 | STATISTICALLY_DISTINGUISHABLE | X |
| silent_excess | C2 vs R | -0.026 [-0.026,-0.025] | -0.57 | -0.30 | STATISTICALLY_DISTINGUISHABLE | X |
| lowinfo_excess | A vs B | +0.043 [+0.041,+0.044] | +0.57 | +0.90 | DISTINGUISHABLE+MEANINGFUL | Y |
| lowinfo_excess | A vs C | +0.073 [+0.070,+0.076] | +0.61 | +0.94 | DISTINGUISHABLE+MEANINGFUL | Y |
| lowinfo_excess | A vs D | +0.068 [+0.065,+0.070] | +0.56 | +0.94 | DISTINGUISHABLE+MEANINGFUL | Y |
| lowinfo_excess | A vs C2 | +0.060 [+0.058,+0.062] | +0.60 | +0.95 | DISTINGUISHABLE+MEANINGFUL | Y |
| lowinfo_excess | A vs R | -0.013 [-0.013,-0.012] | -0.92 | -0.91 | STATISTICALLY_DISTINGUISHABLE | X |
| lowinfo_excess | B vs C | +0.030 [+0.029,+0.031] | +0.67 | +0.95 | DISTINGUISHABLE+MEANINGFUL | Y |
| lowinfo_excess | B vs D | +0.025 [+0.024,+0.026] | +0.54 | +0.83 | STATISTICALLY_DISTINGUISHABLE | Y |
| lowinfo_excess | B vs C2 | +0.017 [+0.016,+0.018] | +0.68 | +0.95 | STATISTICALLY_DISTINGUISHABLE | Y |
| lowinfo_excess | B vs R | -0.055 [-0.058,-0.053] | -0.63 | -0.94 | DISTINGUISHABLE+MEANINGFUL | X |
| lowinfo_excess | C vs D | -0.005 [-0.006,-0.004] | -0.66 | -0.58 | STATISTICALLY_DISTINGUISHABLE | X |
| lowinfo_excess | C vs C2 | -0.013 [-0.014,-0.012] | -0.64 | -0.89 | STATISTICALLY_DISTINGUISHABLE | X |
| lowinfo_excess | C vs R | -0.086 [-0.089,-0.082] | -0.64 | -0.94 | DISTINGUISHABLE+MEANINGFUL | X |
| lowinfo_excess | D vs C2 | -0.008 [-0.009,-0.007] | -0.35 | -0.33 | STATISTICALLY_DISTINGUISHABLE | X |
| lowinfo_excess | D vs R | -0.080 [-0.084,-0.077] | -0.60 | -0.94 | DISTINGUISHABLE+MEANINGFUL | X |
| lowinfo_excess | C2 vs R | -0.072 [-0.075,-0.070] | -0.64 | -0.95 | DISTINGUISHABLE+MEANINGFUL | X |
| adapt_delay | A vs B | +100.750 [+95.383,+106.100] | +1.68 | +1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| adapt_delay | A vs C | +92.100 [+80.599,+103.267] | +1.74 | +0.97 | DISTINGUISHABLE+MEANINGFUL | Y |
| adapt_delay | A vs D | +97.317 [+86.917,+107.600] | +1.83 | +0.97 | DISTINGUISHABLE+MEANINGFUL | Y |
| adapt_delay | A vs C2 | +68.533 [+55.883,+80.534] | +0.96 | +0.62 | DISTINGUISHABLE+MEANINGFUL | Y |
| adapt_delay | A vs R | +0.000 [+0.000,+0.000] | +nan | +0.00 | INCONCLUSIVE | Y |
| adapt_delay | B vs C | -8.650 [-16.534,-0.567] | -0.16 | -0.12 | STATISTICALLY_DISTINGUISHABLE | X |
| adapt_delay | B vs D | -3.433 [-13.400,+6.950] | -0.07 | -0.03 | INCONCLUSIVE | X |
| adapt_delay | B vs C2 | -32.217 [-41.633,-23.200] | -0.85 | -0.67 | DISTINGUISHABLE+MEANINGFUL | X |
| adapt_delay | B vs R | -100.750 [-105.983,-95.400] | -1.68 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| adapt_delay | C vs D | +5.217 [-8.584,+19.817] | +0.09 | -0.23 | INCONCLUSIVE | Y |
| adapt_delay | C vs C2 | -23.567 [-31.783,-15.517] | -0.44 | -0.22 | DISTINGUISHABLE+MEANINGFUL | X |
| adapt_delay | C vs R | -92.100 [-103.067,-80.500] | -1.74 | -0.97 | DISTINGUISHABLE+MEANINGFUL | X |
| adapt_delay | D vs C2 | -28.783 [-44.034,-14.167] | -0.46 | -0.23 | DISTINGUISHABLE+MEANINGFUL | X |
| adapt_delay | D vs R | -97.317 [-107.601,-87.233] | -1.83 | -0.97 | DISTINGUISHABLE+MEANINGFUL | X |
| adapt_delay | C2 vs R | -68.533 [-80.467,-55.700] | -0.96 | -0.62 | DISTINGUISHABLE+MEANINGFUL | X |
| new_ttfa_median | A vs B | +1.600 [+1.462,+1.738] | +2.66 | +0.95 | STATISTICALLY_DISTINGUISHABLE | Y |
| new_ttfa_median | A vs C | -32.000 [-33.775,-30.312] | -2.87 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| new_ttfa_median | A vs D | -11.000 [-13.113,-8.963] | -1.13 | -0.75 | DISTINGUISHABLE+MEANINGFUL | X |
| new_ttfa_median | A vs C2 | -32.413 [-33.675,-31.137] | -3.21 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| new_ttfa_median | A vs R | -6.088 [-6.188,-5.987] | -8.97 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| new_ttfa_median | B vs C | -33.600 [-35.362,-31.900] | -3.11 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| new_ttfa_median | B vs D | -12.600 [-14.738,-10.588] | -1.34 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| new_ttfa_median | B vs C2 | -34.013 [-35.300,-32.700] | -3.49 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| new_ttfa_median | B vs R | -7.688 [-7.750,-7.612] | -26.25 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| new_ttfa_median | C vs D | +21.000 [+18.325,+23.613] | +2.33 | +0.95 | DISTINGUISHABLE+MEANINGFUL | Y |
| new_ttfa_median | C vs C2 | -0.412 [-1.325,+0.475] | -0.14 | -0.15 | INCONCLUSIVE | X |
| new_ttfa_median | C vs R | +25.912 [+24.212,+27.675] | +2.43 | +1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| new_ttfa_median | D vs C2 | -21.413 [-23.675,-19.125] | -2.78 | -1.00 | DISTINGUISHABLE+MEANINGFUL | X |
| new_ttfa_median | D vs R | +4.912 [+2.875,+7.050] | +0.53 | +0.20 | DISTINGUISHABLE+MEANINGFUL | Y |
| new_ttfa_median | C2 vs R | +26.325 [+25.013,+27.587] | +2.75 | +1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| rare_discovery_rate | A vs B | +0.195 [+0.105,+0.285] | +0.93 | +0.70 | DISTINGUISHABLE+MEANINGFUL | X |
| rare_discovery_rate | A vs C | +0.430 [+0.330,+0.525] | +1.85 | +0.90 | DISTINGUISHABLE+MEANINGFUL | X |
| rare_discovery_rate | A vs D | +0.390 [+0.285,+0.500] | +1.55 | +0.90 | DISTINGUISHABLE+MEANINGFUL | X |
| rare_discovery_rate | A vs C2 | +0.370 [+0.300,+0.440] | +2.32 | +0.95 | DISTINGUISHABLE+MEANINGFUL | X |
| rare_discovery_rate | A vs R | -0.045 [-0.120,+0.030] | -0.25 | -0.15 | INCONCLUSIVE | Y |
| rare_discovery_rate | B vs C | +0.235 [+0.135,+0.335] | +1.01 | +0.65 | DISTINGUISHABLE+MEANINGFUL | X |
| rare_discovery_rate | B vs D | +0.195 [+0.120,+0.270] | +1.11 | +0.70 | DISTINGUISHABLE+MEANINGFUL | X |
| rare_discovery_rate | B vs C2 | +0.175 [+0.080,+0.270] | +0.81 | +0.50 | DISTINGUISHABLE+MEANINGFUL | X |
| rare_discovery_rate | B vs R | -0.240 [-0.320,-0.150] | -1.21 | -0.70 | DISTINGUISHABLE+MEANINGFUL | Y |
| rare_discovery_rate | C vs D | -0.040 [-0.165,+0.080] | -0.14 | +0.05 | INCONCLUSIVE | Y |
| rare_discovery_rate | C vs C2 | -0.060 [-0.160,+0.040] | -0.26 | -0.15 | PRACTICALLY_MEANINGFUL(CI includes 0) | Y |
| rare_discovery_rate | C vs R | -0.475 [-0.580,-0.370] | -1.92 | -1.00 | DISTINGUISHABLE+MEANINGFUL | Y |
| rare_discovery_rate | D vs C2 | -0.020 [-0.135,+0.090] | -0.08 | +0.00 | INCONCLUSIVE | Y |
| rare_discovery_rate | D vs R | -0.435 [-0.530,-0.340] | -1.93 | -0.95 | DISTINGUISHABLE+MEANINGFUL | Y |
| rare_discovery_rate | C2 vs R | -0.415 [-0.495,-0.335] | -2.22 | -0.90 | DISTINGUISHABLE+MEANINGFUL | Y |
