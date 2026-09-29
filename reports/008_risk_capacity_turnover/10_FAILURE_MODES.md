# 10 — Failure modes

Targeted probes on the reference (chronic, correlated) family with **separate seeds 4000–4005** (never the held-out seeds), caps 4 and 6; the detailed per-policy rows are in `results/tables/failure_detail_cap4.md` (cap 4). Latent bps per slot-hour unless stated. `FIFO` is shown throughout as the fixed reference.

## 1. Candidate spam (one instrument floods near-duplicate low-value opps with an inflated score)
Spam rate per hour 0 / 0.5 / 1.2 / 3.0 (spam opps are 0 / 39 % / 61 % / 79 % of all arrivals):

| Policy | 0 | 0.5 | 1.2 | 3.0 | spam share of admissions at 3.0 |
|---|---|---|---|---|---|
| FIFO | 0.115 | −0.143 | −0.247 | −0.317 | 0.50 |
| EQUAL_QUOTA | 0.188 | 0.065 | 0.020 | 0.044 | 0.11 |
| RANK_NET | 0.763 | 0.411 | 0.302 | 0.216 | 0.67 |
| SHADOW_PRICE | 0.883 | 0.640 | 0.521 | 0.362 | 0.57 |
| LINUCB | 0.596 | 0.487 | 0.346 | 0.260 | 0.53 |
| COMPOSED | 0.824 | 0.711 | 0.661 | 0.638 | 0.26 |

**`CANDIDATE_SPAM_HANDLED`: handled by `COMPOSED` (−22 % from no-spam to 3.0/h), only partly by everything else (`RANK_NET` −72 %, `SHADOW_PRICE` −59 %, `FIFO` becomes negative).** Mechanism (OBSERVED): the score of the spam instrument is inflated, so plain score ranking is *pulled toward* it; the hierarchical per-instrument calibration in `COMPOSED`/`UNCERTAINTY_LCB` learns that instrument-0 scores predict nothing and prices them accordingly. `EQUAL_QUOTA` is spam-robust by construction but earns little. Held-out families S10/H3 agree (spam admit share: `RANK_NET` 0.54, `COMPOSED` 0.36, oracle 0.20; opp share 0.64). No method handles spam through *identity* (dedup) — none was implemented; it is an obvious next candidate but out of scope.

## 2. Score gaming (spam instrument's score bias raised 0 → 12 → 30 → 60)
`RANK_NET`: 0.585 → 0.325 → −0.069 → −0.371 (spam share of admissions 0.25 → 0.94; 3.8 of 12 positive-value instruments starved); `SHADOW_PRICE`: 0.810 → 0.540 → 0.006 → −0.441; `COMPOSED`: 0.767 → 0.678 → 0.644 → 0.606 (starvation 0); `FIFO` −0.201 flat. **A value-ranking allocator with an uncalibrated self-reported score is exploitable; a causally calibrated one is not, within this attack model** (a constant per-instrument bias; an adaptive adversary that varies the bias over time was not tested).

## 3. Starvation of instruments
Measured as `starved_pos_inst` (instruments with ≥ 5 offered positive-value opps and zero admissions) and `min_admit_ratio`. Held-out, caps 4/6, mean over all families: ≤ 0.02 for every baseline and every value-aware method, **except** `SECRETARY_1_OVER_E` (1.15), `LIN_TS` (0.28; 1.37 in the spam families) and `LINUCB` (0.07; 0.50 in the spam families) — bandits under-explore instruments that once looked bad. Under score gaming/spam of an *individual* instrument, other instruments are starved by the spam instrument's captured slots (`RANK_NET` 3.8 starved at bias 60). `STARVATION_MEASURED = yes`; it is real only where a score can be gamed or a learner under-explores; simple EV ranking does not starve instruments by itself in this environment.

## 4. Long-slot capture and short-slot churn
Long positions (duration above the run's 75th percentile) hold **65–68 %** of slot-hours under `RANK_NET` and `SLOTHOUR_DENSITY` in S6 — by construction long positions hold slots; no rule shifts it materially (07). Heavy-tailed Pareto durations with an edge–duration correlation (0 / 8 / 16 bps per log-duration unit): long-slot share 0.54–0.58 for every value-aware policy, latent value 0.55–0.65, no shortlist method separates from `RANK_NET` by more than 0.02. **Long-slot capture is a property of the opportunity mix, not something these allocators fix.** Short-slot churn: `OLDEST_SLOT` (≈155 forced exits per run) −0.22 dz vs `RANK_NET`; `EVICT_SWAP` ≈35 exits, +0.005.

## 5. Correlation collapse
See 06: at cluster-factor ×8, `RANK_NET` daily-PnL sd 493 bps and drawdown 2,860; `MARGINAL_RISK` 259 and 1,516; `CLUSTER_CAP` 486 (unchanged). Expected value is unaffected in this model.

## 6. Regime lag
Regime shift at mid-horizon (edge means permuted; two of four clusters' score calibration slope flips to −1). Latent value per slot-hour by quarter (cap 4; `RANK_NET`): 0.81 / 0.88 / **0.20 / 0.20**; `COMPOSED` 0.88 / 0.93 / 0.20 / 0.19; `SHADOW_PRICE` 0.91 / 0.96 / 0.21 / 0.21; `LINUCB` 0.66 / 0.79 / 0.18 / 0.19; `FIFO` 0.14 / 0.23 / 0.15 / 0.07. **No method recovers within the 500 h after the shift**; all lose ≈ 75 % of their pre-shift value and land near FIFO. The calibrating and learning methods do *not* adapt faster than plain ranking in this horizon (estimated with data that is 100 % pre-shift at the change point). Held-out S7/H1 show the same shape (quarters 2–3 ≈ 0.35 vs ≈ 0.85–1.0 before, for every value-aware policy; oracles unchanged at ≈ 1.05). `regime lag = not solved by any tested method`.

## 7. Noisy-score instability
Score noise sd 10 → 30 → 60 with strong per-instrument heterogeneity: `RANK_NET` 0.709 → 0.484 → 0.354; `SHADOW_PRICE` 0.812 → 0.502 → 0.387; `COMPOSED` 0.792 → 0.374 → 0.306 — **`COMPOSED` falls *below* `RANK_NET`** (−0.11 and −0.05) at high noise; the cause is its estimated components (per-instrument calibration on few noisy closes, quantile threshold on a noisy density buffer): its threshold coefficient of variation is 4–5 and its cluster HHI rises from 0.69 to 0.78–0.82. Simple rules (`RANK_NET`, `SHADOW_PRICE`) degrade gracefully. This is the main cost of the composition and the reason the verdict is fragile (12).

## 8. Capacity oscillation
Toggle rate of the "all slots full" state (per step) and threshold variability (held-out, caps 4/6): `FIFO` 0.04–0.11 (it stays full), `RANK_NET` 0.12–0.14, `SHADOW_PRICE` 0.13–0.17 (dual-price coefficient of variation 0.4–0.6), `ONLINE_KNAPSACK_PSI` state-based (no drift), `COMPOSED` 0.08–0.16 but with a highly variable quantile threshold (CV 0.4–6.8). Oscillation in the sense of slot-count cycling is visible for the price-adaptive policies but did **not** translate into lower value in the tested regimes; the relevant number is the threshold CV above.

## 9. Other falsification results
* **UNKNOWN_COST != ZERO_COST**: treating unknown cost as 0 costs `RANK_NET` −0.004 dz (CI −0.005…−0.003) at 10 % unknown; the loss grows with unknown share: 0.643 → 0.566 (−12 %) at 70 % unknown, and at 4× costs the zero-imputation variant loses a further 0.217 bps/slot-hour. Rejecting opps with missing *score* (`RANK_NET_MISSING_REJECT`) is statistically identical to neutral imputation here (dz 0.000) — missing evidence was not negative evidence in this environment, but rejecting it did not hurt either.
* **Poor calibration**: slope 0.5 / 0.2 / −0.3 → all score-based methods degrade toward FIFO and go below it at negative slope.
* **Bandits**: below `RANK_NET` (−0.02) everywhere except negative slope; see 02/12.
