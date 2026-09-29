# 01 — Experimental design (pre-registered)

Everything in this file was fixed **before** any held-out run of any policy (`bench/v2/configs/protocol.json`, `configs/freeze_manifest.json`, git commits `817990f`, `3e7958d`). Deviations are listed in §9 and in 11.

## 1. Problem model (V2-DEFINED, extends V1 03 §2)

* A fleet of *cells*. Each cycle a policy must attempt exactly `K = 10` **distinct eligible** cells (a per-cell cap of one attempt per cycle is structural: max share 10 %). Feedback is **batched**: all K attempts are chosen before any outcome is observed.
* `R = 400` cycles. Cycles `0..79` are a **burn-in under a common uniform logging policy** that is independent of the evaluated policy (same events, same propensities for every policy; VW receives exact logged propensities). Metrics are computed on the evaluation window `80..399` only.
* **Typed outcomes (V1 semantics, hard invariant):** an attempt returns `EVIDENCE(value)` with `value ∈ [0,1]` — `0.0` means *"evidence arrived and was uninformative"* (`TRIED_AND_UNINFORMATIVE`) — or `ATTEMPTED_NO_EVIDENCE` (no value at all). An unattempted cell produces nothing (`NOT_ATTEMPTED`). Silence therefore can never look like a negative reward at the environment level; each policy's wrapper is tested for the same property (06, P8).
* **Information value:** an attempt on a non-silent cell is informative with probability `P[t,c]` and then has value `mag` (`0.5` ordinary, `1.0` for "rare high information" cells). The expected information of an attempt is `ev = P·mag`. This scenario-defined metric is independent of any financial quantity.
* **Common random numbers:** the outcome of attempt `(t,c)` is a fixed function of `(scenario, seed, t, c)` (`U[t,c] < P[t,c]`), identical across policies ⇒ policies are compared **paired**, by seed, on the identical environment.
* **Hidden vs visible.** Policies see only the observable `Ledger`: per cell `n_attempts`, `n_evidence`, `last_attempt`, `last_evidence` (tracked separately), `consecutive_no_evidence`, slow/fast EW means of observed values, `pit_unverified` (10 % of cells at birth; cleared after 3 evidence events), a generic static `group` descriptor (visible at birth), plus the announced eligible set (birth = appears, retirement = disappears). They never see `P`, the silence flags, change points, `mag`, or `rare`.
* **Semantic distinctions enforced by construction** (tests in `bench/v2/tests/test_semantics.py`): `NO_OBSERVATION ≠ NEGATIVE_OBSERVATION` (silent ⇒ no value; ledger value statistics untouched by `ATTEMPTED_NO_EVIDENCE`); `DATA_GAP ≠ LOW_INFORMATION` (a cell is `data_gap` only through consecutive no-evidence attempts, "low information" only through observed values); `STALE ≠ DEGRADING` (staleness is age since last evidence; degradation is a fall in *observed* values; the lifecycle classifier is proven insensitive to age and no-evidence); `NOT_YET_TRIED ≠ TRIED_AND_UNINFORMATIVE` (`n_att=0` vs `n_ev>0 ∧ mean≈0`).

## 2. Splits and independence (hard scientific gate)

| Split | Scenarios | Seeds | Purpose |
|---|---|---|---|
| **TRAIN** | `T1_mixed_abrupt`, `T2_mixed_drift_gap`, `T3_churn_lowinfo`, `T4_dormancy_rare` | 1000–1004 | tuning B, C, C2, D |
| **VALIDATION** | `V1_coldstart_outage`, `V2_abrupt_then_drift`, `V3_silence_rare_lowinfo` | 2000–2004 | select among the top-3 train configs |
| **HELD-OUT** | `S1..S10` (02) | 3000–3019 (20 seeds) | all comparative claims |
| PILOT (Phase A) | held-out generators | 9000–9002 | harness validation, invariants only |
| ADVERSARIAL (post-hoc) | `X1..X4`, written after Phase B | 4000–4019 | falsification attempts (09), never used for selection |

Independence is structural, not procedural: (i) separate generator modules — `scenarios_dev.py` (train/validation) never imports `scenarios_heldout.py`, and `tune.py` imports only the dev generator (unit-tested via AST); (ii) disjoint seed ranges (unit-tested); (iii) *distinct composite constructions and parameter values* for train/validation vs held-out (different population sizes, change times, silence lengths, group structure); (iv) independent RNG streams `SeedSequence([split, scenario_idx, seed])` for generator / outcomes / logging; (v) the selected parameter files are hashed and written to `results/heldout/params_lock.json` before the held-out run. Any manual tuning after seeing held-out results would mark the affected result `INVALID_FOR_COMPARISON`; none occurred (11).

## 3. Policies (details in 03)

`A` operator-supplied lifecycle-weighted reference — **fixed, not tuned**. `B` D-UCB + staleness guard (+ bounded backoff). `C` River bandit (as shipped) with hygiene wrapper; `C2` = River + the same guard (a *composition diagnostic* to separate "River" from "guard"; reported separately, not a fifth contender). `D` VW `cb_explore_adf` with shared observable features. `R` round-robin (least recently attempted) — reference frame only. Historic V1 rows (MABWiser etc.) are cited from V1 with their V1 labels; nothing from MABWiser/Optuna/SMPyBandits is a V2 contender.

## 4. Metrics (all on the evaluation window; ground truth used only here)

`COVERAGE` (mean over 40-cycle windows of the fraction of cells eligible for the whole window that received ≥1 attempt) · `STARVATION_RATE` (mean over cycles of the fraction of cells eligible for the last `H=80` cycles with zero attempts in them) · `MAX_STARVATION_DURATION` (longest run without attempts of an eligible cell) · `STALE_CELL_RATE` (fraction of eligible **non-silent** cells whose last evidence is older than `FRESH=60`; cells never evidenced age from birth; `stale_rate_all` also reported) · `SILENT_CELL_ATTENTION_SHARE` (+ baseline = share a uniformly random allocation would give, + `silent_excess`) · `LOW_INFORMATION_ATTENTION_SHARE` (cells with true `ev < 0.05`, non-silent; + baseline/excess) · `RARE_HIGH_INFORMATION_DISCOVERY_RATE` (fraction of rare cells for which a value-1.0 event was *observed* during evaluation) · `ADAPTATION_DELAY` (cycles after the structural change until the 10-cycle share of attempts on the *target* cells reaches 2× their share of the eligible population; **censored** at `R − t_change`, censoring flag kept) · `ATTENTION_CONCENTRATION` (Gini of attempts per eligible cycle; top-10 % share) · `INFORMATION_GAIN` (Σ expected information of attempts; ratio to the per-cycle oracle that attempts the top-K non-silent eligible cells) · `CUMULATIVE_REGRET` (oracle − policy; meaningful only for this information objective, ignores coverage — so it is never used alone) · `TURNOVER` (`1 − |S_t ∩ S_{t−1}|/K`) · `REPRODUCIBILITY` (across-seed dispersion; process-level determinism hashes) · `COMPUTATIONAL_COST` (policy seconds, RSS) · new-cell metrics for P1/P5/P6 (`new_ttfa_*`, `new_never_attempted`, `new_cohort_cov90_time`).

## 5. The lifecycle classifier feeding Policy A (V2-DEFINED — the largest single uncertainty about A)

The operator contract defines states, weights and the floor but not how a state is inferred from evidence. V2 uses a fixed, non-tuned, evidence-only rule (`policies.py: CLS`): `EXPLORATION` if `n_evidence < 5`; else, once `n_evidence ≥ 20`: `DEGRADING` if the fast EW mean has fallen below half the slow one (slow ≥ 0.10) **or** the slow mean is below 0.06 ("proven low information"); `PROVEN` if slow mean ≥ 0.15; otherwise `PROMISING`. `RETIRED` comes only from the scenario's explicit retirement event (the cell then leaves the eligible set). Consequences reported openly: (a) A's behaviour depends on this classifier; a variant where proven-low-information cells stay `PROMISING` (`A_altcls`) is run as a **descriptive sensitivity**; (b) with weights `1.5/1.0/0.75/0.5`, A is essentially a *static, evidence-blind reweighting of round-robin*: states change only with observed values, and the weight spread is small — A cannot concentrate attention. Whether that is a defect or the intended conservative contract is a local (private) question; V2 only measures the behaviour.

Discrete realisation of A's fractional shares (V2-DEFINED): each cycle every eligible cell's credit increases by its fractional share (which sums to K), the K cells with the highest credit (ties by id) are attempted, and each attempted cell's credit decreases by 1. The fractional allocation itself is asserted to satisfy `Σ = K` (max error logged), non-negativity, and retired-cell exclusion; floor units are logged **per exploration-reason bitmask** (`no_evidence | stale | data_gap | pit_unverified`) and weighted units per lifecycle state — reasons are not merged in the logs.

## 6. Selection objective (pre-registered; used for B, C, C2, D only)

`J = info_ratio − 1.0·starvation_rate − 0.5·stale_rate − 0.5·max(silent_excess,0) − 0.25·max(lowinfo_excess,0)`, averaged over TRAIN scenarios×seeds. The top-3 configurations by TRAIN `J` are re-scored on VALIDATION; the best validation `J` is frozen (ties within 0.005 → nearest the grid centre). J is a *tuning device*: the held-out comparison reports every metric separately and never ranks by J alone.

## 7. Statistics (pre-registered; detail in 08)

Paired-by-seed differences; hierarchical bootstrap (10 000 resamples, 95 %) — resample seeds within scenario, average scenario means; effect sizes (paired standardized difference and Cliff's δ); practical thresholds per metric fixed in `protocol.json`. A difference is `STATISTICALLY_DISTINGUISHABLE` if the CI excludes 0, `PRACTICALLY_MEANINGFUL` if the mean difference exceeds the threshold, else `INCONCLUSIVE`. No p-values.

## 8. Staged execution

Phase A (harness validation; 3 dev-seeds × 7 dev scenarios and 3 pilot seeds × 10 held-out generators × 6 policies; wall 54 s ⇒ cost is negligible, so **no downgrade of seeds was needed**) → tuning (04) → freeze of selected parameters → Phase B (20 seeds × 10 scenarios × 6 policies) → pathology tests (06) → descriptive sensitivity (07) → statistics (08) → post-hoc adversarial scenarios (09).

## 9. Deviations from the original brief and honest caveats

* V1 bench lives at `reports/001_adaptive_strategy_fleet/bench/`, not `bench/` (recorded in 00).
* Policy A's contract is operator-supplied (00 §2.2).
* Tuning code tie-rule was corrected (protocol says "nearest the centre"; first implementation used train rank) **before** any held-out run and all dev tuning was re-run: the corrected rule changed the chosen B config from `M16` to `M4` (identical train/validation J — the two differ only in a backoff cap that never bound on dev) and the chosen C config from `fading 0.3` to `fading 0.1` (validation J within 0.005 of the leader ⇒ tie ⇒ nearest the grid centre).
* Pilot invariant tests executed all policies on pilot seeds before the freeze commit; no metric was read (`freeze_manifest.json` carries the disclosure).
* The V1 scenario (160 cells, 1 200 rounds, Bernoulli reward) is **not** re-run here; V2 uses a new model (typed outcomes, groups, retirements, bursts of silence), so V2 numbers are not comparable to V1 numbers and are never mixed with them.
