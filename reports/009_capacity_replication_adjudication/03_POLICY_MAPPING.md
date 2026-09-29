# 03 — Policy mapping

Mapping is by **decision semantics read from source**, not by name. "Equivalence" grades: EQUIVALENT (same rule on comparable inputs), CLOSE (same rule, different information or unit), ANALOGUE (same family, different rule), NO_COUNTERPART.

| Family asked | Study A policy | Study B policy | Grade | What differs |
|---|---|---|---|---|
| FIFO | `FIFO`: oldest pending opportunity by age, no filter | `FIFO`: earliest first-emission instrument, one per instrument, ingest RAW | CLOSE | A's queue holds distinct opportunities whose edge decays while waiting; B's queue holds instruments with repeated emissions. Age ordering therefore selects *stale* edge in A (07, item 2) |
| FIFO + net screen | `FIFO_NETPOS`: FIFO restricted to `score − cost > 0`; running-mean imputation for missing score or cost | `FIFO_SCREEN`: FIFO restricted to `val>0`, `val = score − cost_est`, missing score → global mean | EQUIVALENT | B's cost belief is exact (`known`); A's cost is NaN for 10% and imputed |
| Score ranking (raw, no cost) | `RANK_SCORE_RAW` | **none** | NO_COUNTERPART | B never ranks on gross score |
| Net-edge ranking | `RANK_NET`: rank by `score − cost` | `SCORE_RANK`: rank by `score − cost_est`, admits only `val>0` (**despite its name it is a net ranker**) | EQUIVALENT | B additionally rejects `val ≤ 0`; A's `RANK_NET` also skips non-positive values in the shared helper (checked) |
| Net per expected slot-hour | `SLOTHOUR_DENSITY` (`v/(dur_hat + h0)`), `SLOTHOUR_HAZARD` | `SLOTHOUR` (`val / h_est[inst]`) | CLOSE | A uses a noisy **candidate-level** duration estimate (falls back to instrument EMA); B uses only a per-instrument EWMA of past **realised** holds (prior 6 h). Different information, so R4 is a comparison of two unlike estimators |
| Uncertainty / shrinkage | `UNCERTAINTY_LCB` (Bayesian calibration `net ~ a + b·x` with κ prior, LCB with k), `COMPOSED` (density + shrinkage + shadow price) | `UNCERTAINTY_LCB` (shrink to per-instrument score EWMA with ω, penalise by κ·√(σ²h)) | ANALOGUE | A shrinks *realised-vs-score calibration*; B shrinks *score toward instrument history* (pools repeated emissions). B's chosen κ=0, so its gain is pure pooling |
| Shadow price / opportunity cost | `SHADOW_PRICE` (adaptive threshold, target utilisation), `ONLINE_KNAPSACK_PSI`, `FLUID_QUANTILE`, `TRUNK_RESERVATION` | `SLOTHOUR_SHADOW` (threshold θ·EWMA of admitted rates) | ANALOGUE | A's four are distinct mechanisms; B has one |
| Correlation aware | `CORR_PENALTY`, `MARGINAL_RISK` (EWMA covariance), `CLUSTER_CAP`, `CORR_HARD_REJECT` | `CORR_AWARE` (penalty on public-group load, ρ=0.6 constant) | ANALOGUE | A estimates correlation online from returns; B uses public group labels and a fixed ρ |
| Bandit | `LINUCB`, `LIN_TS`, `SLEEPING_HEDGE` | `LINTS` (D=6 linear Thompson, delayed reward) | ANALOGUE | different features and reward definitions |
| Preemption | `OLDEST_SLOT`, `EVICT_SWAP` | `OLDEST_SLOT` | CLOSE for `OLDEST_SLOT` | A charges +3 bps on forced close; hold thresholds differ (A tuned 12 h, B 4 h) |
| Round-robin | `ROUND_ROBIN` (per instrument pointer) | `ROUND_ROBIN` | EQUIVALENT | |
| Quota | `EQUAL_QUOTA` | `EQUAL_QUOTA` | EQUIVALENT | |
| Random | `RANDOM_SEEDED` | `RANDOM` | EQUIVALENT | |
| Optimal stopping | `SECRETARY_1_OVER_E` | none | NO_COUNTERPART | |
| Oracle | latent-edge score/density oracle + LP relaxation | greedy realised-net oracle | not comparable | headroom not comparable (02 row 24) |

## Comparability verdict
`POLICY_SEMANTICS_COMPARABLE=PARTIAL`. Eight of ten families requested map (FIFO, FIFO+screen, net ranking, slot-hour, shrinkage, shadow price, correlation, bandit), but only three map as EQUIVALENT (FIFO+screen, net ranking, RR/quota/random). Slot-hour, shrinkage, correlation, bandit and preemption are ANALOGUE/CLOSE, so those comparisons (R4–R7) carry a semantic caveat. Raw score ranking exists only in A.

## Naming traps to avoid when reading the two corpora
1. B `SCORE_RANK` = A `RANK_NET`, **not** A `RANK_SCORE_RAW`.
2. B `FIFO` runs on RAW ingest while B ranking policies run on SCORE_UPDATE. I checked that this does not confound: B's FIFO moves only 1.81–1.85 across ingest modes, while the gap to `SLOTHOUR` stays about 0.44–0.48.
3. A's "complex" set (`COMPOSED`, `SHADOW_PRICE`, `ONLINE_KNAPSACK_PSI`) is not B's "complex" set; only `UNCERTAINTY_LCB` is in both.
4. "Complex beats simple" is measured against `RANK_NET` in A and `SLOTHOUR` in B; A's `SLOTHOUR_DENSITY` is statistically identical to `RANK_NET` (+0.001), so the reference choice barely matters in A but matters in B (+0.07).
