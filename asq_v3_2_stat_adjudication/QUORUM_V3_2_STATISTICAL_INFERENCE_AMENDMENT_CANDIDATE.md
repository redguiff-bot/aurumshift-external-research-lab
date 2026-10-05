# QUORUM_V3_2_STATISTICAL_INFERENCE_AMENDMENT_CANDIDATE

STATUS: CANDIDATE — NOT FROZEN — NOT ACTIVATED — APPEND-ONLY
ANCHOR: AS-Q V3.1 consolidated candidate SHA256 `8cb9adf43692667e6be98769a9082073447230e73b99b881b5a566e5447237da`
ANCHOR_VERIFIED: FALSE (V3.1 bytes not accessible from this repository; the hash is quoted from the mission, not recomputed)
SOURCE: `redguiff-bot/aurumshift-external-research-lab` @ `d0b311db3e8bded2eeb0415832e9553ebb434b8b` (external lab; contains NO AurumShift source, NO SOURCE_DE_VERITE.md, NO MEMORY, NO V3/V3.1)
SCOPE: statistical inference contract only. No quorum change, no implementation, no real AS-Q outcome/PnL inspected.

Evidence labels (lab doctrine): PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN.
Everything below is INFERENCE (design adjudication) unless explicitly labelled. Numeric defaults are marked `ADJ_DEFAULT`: they are adjudicated here, may be changed only BEFORE any benchmark result is consumed, and any later change requires a new matrix version and fresh benchmark seeds.

---------------------------------------------------------------------
## S-0 Nature of the experiment (framing that drives everything else)

Both arms are computed offline from the SAME frozen pre-treatment DecisionInput by the SAME deterministic DecisionEngine (quorum 2 vs 1). There is no stochastic treatment assignment. Consequences:

- No confounding between arms by construction. The only sources of error are (i) measurement of outcomes, (ii) sampling variation of the market process, (iii) selection of which pairs are analysed.
- Inference is sampling-based over the market/decision process (super-population of future decision inputs), NOT randomization-based. Serial and cross-sectional dependence of that process therefore matters fully.
- The estimand is a counterfactual policy-value difference under an explicit no-market-impact evaluator (paper-only; sizes assumed small vs L1). This assumption is stated, not hidden (see S-5).
- The N=757 differential is ENGINEERING EQUIVALENCE evidence (action/reason/confidence mismatch = 0). It is not economic N. INFERENCE (power-critical, UNKNOWN to verify): if zero action mismatches is representative of the live input distribution, the active fraction p_active may be very small, making the all-pairs effect heavily diluted. The operator must state whether the N=757 inputs were chosen to exercise quorum divergence.

---------------------------------------------------------------------
## S-1 Causal unit

PAIR_UNIT = one frozen pre-treatment DecisionInput (authoritative PRE_DECISION_INPUT, content-hashed) for one instrument at one decision cutoff, evaluated by the same engine build/config under A (quorum=2) and B (quorum=1).

pair_id = H(frozen_input_hash, instrument_id, decision_cutoff_ts, engine_build_id, config_hash_excluding_treatment_arm). Minted when the input is frozen, BEFORE either arm is evaluated. Never recomputed, never changed by a later economic-predicate version, evaluator version, or outcome.

DEPENDENCE_BLOCK = decision epoch = the synchronized decision cycle (all instruments sharing the same decision_cutoff_ts bucket). Contract: instruments within an epoch are CLUSTERED, not independent; the epoch is one multivariate experimental block.

CLUSTER_KEY = decision_epoch_id = floor(decision_cutoff_ts / decision_cadence), as recorded at freeze time.

Second-level dependence (serial): blocks are ordered in time; consecutive epochs are dependent (volatility clustering, regime persistence, and overlapping outcome windows, see S-6). The inference series is therefore the ordered series of epoch totals, never the pair-level rows.

Estimator structure (ratio of sums, handles unbalanced clusters):
- S_t = sum over pairs i in epoch t of d_ti, n_t = number of denominator pairs in epoch t.
- Delta_hat = (sum_t S_t) / (sum_t n_t).
- Variance from the ordered score series u_t = S_t − Delta_hat * n_t (HAC) or from joint resampling of (S_t, n_t) (bootstrap). Never from pair-level iid formulas.
- Epochs with n_t = 0 (gaps) keep their ordinal slot and carry a gap flag; they are not silently removed.

---------------------------------------------------------------------
## S-2 Primary estimand

Treatment: quorum_required 2 → 1. Not "does B trade more".

d_i = Y_B,i − Y_A,i, where Y_*,i is the net economic outcome (after costs) in bps of reference notional at horizon H, produced by the SAME counterfactual evaluator for both arms (S-5). Y = 0 by definition when the arm's decision is NO_TRADE (a known zero, not UNKNOWN).

PRIMARY_ESTIMAND: Delta = E[ Y_B − Y_A | pair in DENOMINATOR ], an intention-to-treat style average over ALL pre-treatment-eligible pairs, including pairs where A and B decide identically (d = 0 exactly, under identical decision tuples).

PRIMARY_ESTIMAND_POPULATION: DENOMINATOR (S-3): every pair whose pair_id was minted pre-treatment and that passed PRE_TREATMENT criteria only.

Identity (reported always): Delta = P(S) · Delta_S, where S = {pairs whose (action, side, size, confidence-driving sizing) differ between arms}, Delta_S = E[d | S].

QUORUM_ONLY_SUPPRESSED adjudication:
- It is defined from the arms' outputs (A = NO_TRADE, B = TRADE), hence it is a POST-TREATMENT classification. Using it to define the primary population is rejected.
- It is NOT post-treatment-selection-biased if and only if: (a) engine is deterministic in the frozen input, (b) neither arm's decision depends on state altered by the other arm or by earlier outcomes (no feedback), (c) the class label is computed and sealed for every denominator pair BEFORE any outcome is read. Under (a)–(c) it is a principal-stratum-like partition fully observed for every pair (no monotonicity assumption required), a legitimate subgroup defined by pre-outcome quantities.
- QUORUM_ONLY_SUPPRESSED_ROLE = SECONDARY (estimand Delta_QOS = E[d | QUORUM_ONLY_SUPPRESSED]); automatically demoted to DESCRIPTIVE_ONLY if any of (a)–(c) fails or cannot be shown.
- Secondary estimands (no confirmatory claim): Delta_S; Delta_QOS; action/suppression rate shifts (descriptive); per-active-trade bps; portfolio translation Delta × pairs/day × notional (arithmetic, untested).

---------------------------------------------------------------------
## S-3 Eligibility timing and sets

| Criterion | Class |
|---|---|
| authoritative frozen PRE_DECISION_INPUT present, hash verified | PRE_TREATMENT |
| instrument in preregistered universe | PRE_TREATMENT |
| cutoff inside capture window, no declared blackout | PRE_TREATMENT |
| decision-time data freshness required by the engine input | PRE_TREATMENT |
| engine ran without exception in both arms | POST_TREATMENT → never a filter: fault pairs stay in DENOMINATOR, status ENGINE_FAULT, count toward SAFETY_STOP |
| action executed / trade taken | POST_TREATMENT → forbidden as filter |
| QUORUM_ONLY_SUPPRESSED / S membership | POST_TREATMENT → stratum label only |
| profitable / positive outcome | OUTCOME → forbidden |
| horizon matured, L1 reference present (MAX_L1_AGE), depth, costs known | ECONOMIC_OBSERVABILITY |
| ECONOMIC_MEASUREMENT_COMPLETE_V1 | ECONOMIC_OBSERVABILITY |
| UNKNOWN anything | UNKNOWN → treated as ECONOMIC_OBSERVABILITY failure, never as exclusion from DENOMINATOR |

DENOMINATOR_CONTRACT: append-only ledger of pairs satisfying PRE_TREATMENT criteria only, sealed per epoch at freeze time. Immutable. Defines N and all weights.

ANALYSIS_SET_CONTRACT: DENOMINATOR pairs whose maturity deadline (cutoff + H + preregistered settlement lag) has passed at the analysis data-cut. Maturity is calendar-determined, so unmatured pairs are "not yet due", not "missing". Filter by maturity date only, never by outcome.

ECONOMIC_COMPLETE_SET_CONTRACT: ANALYSIS_SET pairs with status COMPLETE for both arms under the economic predicate version frozen for the experiment, PLUS pairs with an identical decision tuple (d = 0 by identity, NOT_APPLICABLE-by-construction, counted as known zeros). A predicate/evaluator re-run appends a new status row; it never alters pair_id, DENOMINATOR or ANALYSIS_SET. Primary inference uses the frozen predicate version only.

Forbidden silent redefinitions of the population: executed-only, profitable-only, COMPLETE-only.

---------------------------------------------------------------------
## S-4 Missing economic outcomes

Pairs with identical decision tuples need no economic measurement (d = 0): they are complete. Missingness therefore concerns only S-active pairs, where at least one arm trades.

| Situation | Status | Denominator | Point estimation | Bounds / sensitivity |
|---|---|---|---|---|
| identical decision tuple | NOT_APPLICABLE (known zero) | yes | yes (d=0) | n/a |
| A=NO_TRADE, B trades, all measurable | COMPLETE | yes | yes | n/a |
| cost UNKNOWN | UNKNOWN (never zero) | yes | no | yes |
| missing/stale reference (L1 age > MAX_L1_AGE) | UNKNOWN | yes | no | yes |
| insufficient depth for size | UNKNOWN in primary (no-fill=0 only as preregistered sensitivity variant) | yes | no | yes |
| horizon-end price absent (data gap) = censored | UNKNOWN | yes | no | yes |
| no executable counterfactual | UNKNOWN | yes | no | yes |
| ENGINE_FAULT | UNKNOWN + safety counter | yes | no | yes |

UNKNOWN_OUTCOME_POLICY: UNKNOWN pairs remain in DENOMINATOR; never imputed as zero or as profit; excluded from the point-estimate numerator only through the explicit estimator below; always carried into bounds.

PARTIAL_IDENTIFICATION_REQUIRED = TRUE. Reason: depth and staleness failures are plausibly informative (illiquid/fast markets are where B's extra trades are worst); MAR cannot be assumed.

Mandatory outputs:
1. Point estimate under assumption M1 (below), with IPW by preregistered pre-treatment covariates X (instrument, epoch volatility bucket, spread bucket, hour-of-day, strategy family).
2. Manski worst/best-case bounds: Delta in [ (sum_complete d + n_miss·d_min)/N , (sum_complete d + n_miss·d_max)/N ]. Requires a FINITE preregistered support [d_min, d_max] derived outcome-blind (evaluator rules + market-only volatility, not decision outcomes). Without finite support, bounds are uninformative; if unavailable, report UNBOUNDED and the claim is INSUFFICIENT_INFORMATION.
3. Tipping-point analysis: shift tau applied to missing-pair mean d; report the tau that flips the conclusion; the operator-preregistered tau* grid must not flip it for a positive claim.

Minimum assumptions for complete-case inference (all explicit):
- M1: Y missing independent of d given X (MAR|X) within active pairs, with positivity: P(complete | X) ≥ pi_min (operator-required).
- M2: missingness mechanism is pair-level and arm-symmetric (same evaluator, same market path).
- M3: evaluator version and cost model constant over the experiment.
- M4: missing share among active pairs ≤ m_cap (operator-required); above m_cap → INSUFFICIENT_INFORMATION.
Violating any → no point-estimate claim; bounds only.

---------------------------------------------------------------------
## S-5 A/B economic symmetry

Risk: actual PAPER A (real fills, real mechanics) vs counterfactual B (estimator) mixes two measurement regimes; any difference is partly a measurement-regime difference.

PRIMARY_OUTCOME_GENERATOR_A = counterfactual evaluator CF (version frozen) applied to A's decision tuple on the frozen market path (G3-qualified source, MAX_L1_AGE calibrated), frozen cost model.
PRIMARY_OUTCOME_GENERATOR_B = the identical CF code path, same market path, same cost model, same fill rules, applied to B's decision tuple.
PAPER_A_ROLE = external validation layer only: compares Y_A,paper vs Y_A,CF on naturally executed A trades (distribution of residuals, bias, tail). It never enters Delta. A residual outside a preregistered band flags the evaluator INVALID_FOR_PRIMARY.

Limitation to record: this validates CF only on A-executed trades; B-only trades are an extrapolation of the validated evaluator (support gap). Also: Binance @ticker is L1-only (INFERENCE), so any depth beyond L1 is not observed; sizes > L1 quantity → UNKNOWN (S-4), not a modelled fill.

Hard dependencies before primary economic inference: G3 closed (MAX_L1_AGE calibration done, outcome-blind) AND the cost UNKNOWN→ZERO repair made canonical.

---------------------------------------------------------------------
## S-6 Horizon and overlap

PRIMARY_HORIZON = PT1H (1 bar), status PROVISIONAL / ENGINEERING_PLACEHOLDER, UNRESOLVED. It becomes the primary preregistered horizon only if the operator attests it is consistent with (a) strategy-family holding period, (b) decision cadence, (c) the cost model (round-trip at horizon end). Otherwise it is secondary. This amendment does not optimize or replace H; alternative horizons are preregistered sensitivities, never hypotheses chosen after seeing data.

Scope statement: the primary estimand is an H-horizon mark-out net of round-trip costs, not full strategy PnL (strategy exits, carry and path-dependent stops are not modelled).

OVERLAP_POLICY: let k = ceil(H / decision_cadence). If k > 1, outcomes in consecutive epochs overlap, producing MA(k−1)-type dependence (plus persistent volatility). Then: (i) effective independent blocks ≈ T/k, never T; (ii) HAC bandwidth ≥ k−1 and bootstrap mean block length ≥ k (preregistered rule); (iii) a non-overlapping subsample (every k-th epoch) is a mandatory robustness analysis; (iv) stopping thresholds are expressed in epochs and effective blocks, not pairs; (v) benchmark MA(k−1) DGP levels must include the actual k.

---------------------------------------------------------------------
## S-7 Primary inference method: candidates and qualification gates

No method is selected here. Candidates (all operate on the ordered epoch series, S-1):
- C1 HAC (Newey–West, statsmodels), fixed-lag rule from k and T; variants with small-sample correction / t reference.
- C2 HAC with fixed-b critical values (Kiefer–Vogelsang).
- C3 Studentized Stationary Bootstrap (arch), automatic block length (Politis–White/Patton–Politis–White) with floor k.
- C4 Moving-block / epoch-cluster bootstrap on (S_t, n_t).
- NC Naive iid t-test: NEGATIVE CONTROL only (must reproduce undercoverage under serial dependence; the external radar claim is not treated as reverified).
- CS Confidence sequence: ANYTIME MONITOR only, not a primary candidate (S-8).

Role design: one PRIMARY + one ROBUSTNESS method from a different assumption family. Conclusion must also hold under the robustness method, else verdict INCONCLUSIVE_METHOD_SENSITIVE.

PRIMARY_METHOD_ACCEPTANCE_GATES (ADJ_DEFAULT; bands fixed before any result; evaluated on synthetic DGPs only, S-13):
- Tolerance rationale: with R replications the Monte-Carlo SE of a 5% rate is sqrt(.05·.95/R); R=2000 → 0.49 pp. Bands are ±3 SE around nominal for core cells (so a correct method almost never fails by chance) plus a Clopper–Pearson upper cap that rejects methods genuinely above ~7.5% (Bradley liberal limit 1.5× nominal).
- G-COV (core cells): two-sided 95% CI non-coverage point estimate in [3.5%, 6.5%] AND Clopper–Pearson 95% upper bound ≤ 7.5%. Stress cells: non-coverage ≤ 10%; any stress cell > 15% is a hard fail.
- G-T1: Type-I at nominal 5% (two-sided) under the same bands; at the non-inferiority/equivalence boundary (theta = ±M) one-sided rejection ≤ 3.2% (nominal 2.5%, R≥5000).
- G-SERIAL, G-CROSS, G-TAIL, G-UNBAL: the G-COV band must hold in the respective factor cells.
- G-MISS: under MCAR and correctly modelled MAR the G-COV band holds; under MNAR the Manski bounds contain the true Delta in 100% of replications (support assumption true) and false-success rate ≤ 10% when true Delta is at the null.
- G-PEEK: final-inference procedure combined with the preregistered stopping rule has rejection rate within the G-T1 band; naive repeated-look positive control must inflate ≥ 2× nominal (harness sensitivity check).
- G-WIDTH: median CI width ≤ 1.35 × oracle (known long-run variance) in core cells; conservative methods are not invalid but are penalized here.
- G-DET: bitwise-identical (or ≤1e-12 relative) results across 3 repeats, 1 vs 4 threads, two machines; seeds recorded.
- G-RUN: ADJ_DEFAULT p95 ≤ 10 min single core, ≤ 2 GB at maximum T and K with ≥10,000 bootstrap draws; operator may relax before benchmark.
- G-FAIL: CI computation failure/degenerate rate ≤ 0.1%, no silent fallback.
- Validity region: the smallest number of effective blocks for which all core gates pass becomes a lower bound on B_min (S-11). A method has no authority below it.

---------------------------------------------------------------------
## S-8 Anytime monitoring and peeking

PRIMARY_FINAL_INFERENCE: single fixed-information evaluation (S-11) using the frozen primary method. Only this can yield SUCCESS_STOP.

ANYTIME_MONITOR: a confidence sequence on Delta (valid for heavy tails and dependence, to be qualified in the benchmark) run by an automated sealed monitor that emits only discrete states {CONTINUE, SAFETY_STOP, FUTILITY_STOP}, never numeric effect, CI or p-value to operators.

Operators MAY inspect during capture: counts of pairs/epochs/maturities, missing and UNKNOWN rates by reason, active fraction (action-based, outcome-blind), engine faults, input-mutation counter, data-source health, evaluator residual diagnostics of PAPER A vs CF (validation only).
Operators MAY NOT inspect: Delta, any outcome-derived CI/p-value, subgroup effects, or outcome distributions by arm.
SAFETY_STOP triggers (integrity, outcome-independent): input mutation > 0; engine exception rate above preregistered cap; B placing any order; PRE_DECISION_INPUT hash mismatch; G3 source breach or MAX_L1_AGE violation rate above cap; UNKNOWN share above cap.
FUTILITY_STOP: the CS proves the preregistered claim criterion can no longer be met (e.g., CS upper bound below the success threshold). Result is NOT_PROMOTED, not proof of harm.
NEVER positive: no CS statement, no interim estimate, no replay, no operator judgment may trigger promotion. Positive claim only at the final evaluation.
Config freeze: any engine/universe/evaluator/threshold change mid-capture starts a NEW experiment epoch; epochs are never pooled across a change. Retex outputs from this experiment must not feed back into arm configuration, universe or horizon during capture.

---------------------------------------------------------------------
## S-9 Multiplicity

CONFIRMATORY: exactly one, H1 on Delta (claim type fixed in S-10). Full alpha is spent on H1. No multiplicity machinery.
SECONDARY (estimates with unadjusted CIs, no promotion power): Delta_S, Delta_QOS, action/suppression metrics, non-overlapping robustness, no-fill=0 variant, PAPER A validation.
EXPLORATORY (labelled, no inferential claims): instrument strata, regime strata, strategy-family strata, alternative horizons, cost-model challengers (except the preregistered qualitative robustness check that the sign of the conclusion does not reverse under declared challenger cost models).
SPA / StepM: NOT required. They apply only if several competing treatments/strategies/models are compared to select a winner. Trigger: if the operator adds arms or candidate strategies, the family must be re-preregistered with Holm or SPA/StepM before capture.
Cap: strata lists and challenger lists are preregistered finite lists; no post-hoc additions.

---------------------------------------------------------------------
## S-10 Materiality

MATERIALITY_UNIT = bps of reference notional, net of costs, per DENOMINATOR pair (i.e., the per-eligible-pair mean Delta). Secondary conversions (per active trade = Delta / P(S); portfolio-level = Delta × pairs/day × notional) are arithmetic reports, not tested.
MATERIALITY_PARAMETER = OPERATOR_REQUIRED (not chosen here).
PROMOTION_CLAIM_TYPE = OPERATOR_REQUIRED, exactly one among:
- Superiority by M: lower bound of the two-sided 95% CI > +M.
- Non-inferiority with margin M: lower bound of the 95% CI > −M.
- Equivalence / economically negligible with margin M: 90% CI ⊂ (−M, +M) (TOST, α=0.05 each side).
The experiment, the stopping rule and the benchmark's boundary-size tests all use the same M and claim type. Required sensitivity table: for operator-supplied M grid, verdict per M (descriptive only; cannot switch the frozen decision). If M is chosen after seeing any outcome-derived information, the experiment is void.

---------------------------------------------------------------------
## S-11 Stopping contract

Rejected: fixed N=500 universal rule; N≈250–500 is scenario-specific.

Information gate (outcome-independent where possible):
B_min = max( B_method (validity region from benchmark), B_power(M, variance prior, P(S)) )
- epochs matured and sealed ≥ B_min; effective blocks ≥ B_min/k.
- active pairs ≥ A_min (operator-required).
- missing share among active pairs ≤ m_cap; UNKNOWN reasons stable.
- variance prior comes from outcome-blind sources or replay (S-12 allowed roles), never from this experiment's effect estimate.
- G3 closed, cost-repair canonical, evaluator validated, config hash unchanged.

States:
- SUCCESS_STOP: information gate met at the single preregistered final look AND primary claim criterion holds AND robustness method agrees AND tipping-point survives AND bounds reported. A CI wider than W_max (operator-required) at the final look → INSUFFICIENT_INFORMATION, not extension.
- FUTILITY_STOP: from the sealed CS monitor only; verdict NOT_PROMOTED.
- MAX_DURATION_STOP: calendar/resource cap reached before the information gate → INSUFFICIENT_INFORMATION; descriptive report only, no claim either way.
- SAFETY_STOP: integrity triggers (S-8); yields no scientific claim in either direction; data retained.
- INSUFFICIENT_INFORMATION: terminal verdict, never "negative evidence".
Extension beyond the final look is UNRESOLVED and allowed only if the benchmark shows (G-PEEK) that a preregistered width-based extension preserves Type-I within band.
Forbidden: stopping on a favorable estimate, adding data until significant, changing M/H/claim type after seeing outcomes.

---------------------------------------------------------------------
## S-12 Forward vs replay

FORWARD_REPLAY_POOLING = FORBIDDEN (default). Pooling is reconsidered only after a preregistered transportability demonstration (stability of P(S), evaluator, cost regime, market regime); even then replay is reported as a separate stratum and never added to confirmatory N.
REPLAY_ALLOWED_ROLES: power estimation (variance, active fraction, missing rate, dependence structure — not effect size used to choose H/M/claim type); variance estimation; mechanism falsification (can only weaken, not promote); robustness (separately reported); external replication (preregistered replay protocol, separate verdict).
Legacy 4,140,367 decisions: ELIGIBLE confirmatory corpus = 0; at most descriptive base-rate hints with provenance warning (not causal evidence).
Contamination control: log every replay outcome access before freeze; if replay effect sizes influence any design parameter, disclose and mark the forward test non-pristine.

---------------------------------------------------------------------
## S-13 Statistical benchmark contract for Codex

Synthetic data only. Real AS-Q outcomes forbidden. Matrix, seeds, R and bands frozen and hashed BEFORE any result is consumed for method selection. R=2000 per core cell, R=5000 for null and boundary cells.

DGP: epoch series with K instruments per epoch; d_ti = common_t·sqrt(rho) + idio_ti·sqrt(1−rho), activity indicator Bernoulli(p_active), noise tail family, serial structure on common_t, missingness on active pairs.

| Dimension | Levels |
|---|---|
| T (epochs) | 60, 120, 250, 500, 1000, 2000 |
| K per epoch | 1, 5, 20 |
| true Delta | 0; ±M-boundary (several M'); 0.1σ, 0.2σ, 0.3σ, 0.5σ of block-mean SD |
| serial | AR(1) φ ∈ {0, 0.3, 0.6, 0.9}; MA(k−1) k ∈ {1, 2, 4, 12}; volatility clustering (GARCH-like) |
| cross-instrument common shock ρ | 0, 0.2, 0.5, 0.8 (+ heterogeneous loadings) |
| tails | Gaussian, t5, t3, t2.5 (infinite 4th moment), skewed |
| sparsity p_active | 1.0, 0.3, 0.1, 0.02 |
| cluster imbalance | balanced; Poisson sizes; heavy-skew sizes; empty epochs; size correlated with shock |
| missing share m (active pairs) | 0, 0.05, 0.2, 0.4 under MCAR, MAR|X, MNAR (adverse d more likely missing), arm-asymmetric |
| peeking | single final look; 5/20/100 info-based looks with naive stop-at-p<.05 (positive control); CS monitor; preregistered width-based extension |
| robustness | regime break; irregular epoch spacing |

Cells: fractional design for the core (plausible region declared a priori by operator), one-factor-at-a-time for stress. Metrics: coverage, Type-I (nominal and boundary), power at designed alternatives, bias, RMSE, CI width ratio, failure rate, bounds validity, tipping-point behavior, stopping-rule size, determinism, runtime, memory.

| Metric | Threshold (ADJ_DEFAULT) | Failure consequence |
|---|---|---|
| core non-coverage / Type-I | within [3.5%, 6.5%], CP upper ≤ 7.5% | ineligible as PRIMARY; may remain ROBUSTNESS if stress gates pass |
| stress non-coverage | ≤ 10%, hard fail > 15% | ineligible for any inferential role |
| boundary one-sided size | ≤ 3.2% | ineligible for NI/equivalence claims |
| MNAR bounds validity | 100% containment | missing-outcome policy rejected; no point claim under m>0 |
| false success under MNAR null | ≤ 10% | tipping/bounds gate strengthened, benchmark re-run required |
| peeking size | within T1 band; positive control ≥ 2× | stopping rule rejected; fixed single look only |
| CI width ratio | ≤ 1.35× oracle | method downgraded (power) but not invalid |
| determinism | 100% reproducible | ineligible for everything |
| runtime/memory | within budget | ineligible unless approximated within bands |
| failure rate | ≤ 0.1% | ineligible |
Selection rule (preregistered, lexicographic): (1) all gates pass; (2) smallest worst-case coverage error over core cells; (3) simplicity/fewest dependencies. If no method passes: INFERENCE_METHOD_UNRESOLVED; thresholds are NOT relaxed post hoc; a new matrix version and fresh seeds are required.

---------------------------------------------------------------------
## S-14 Red team (ordered by impact on validity)

1. Post-treatment selection / QUORUM_ONLY_SUPPRESSED as population: mitigated by ITT primary; stratum only under determinism + no-feedback + pre-outcome sealing.
2. A actual vs B counterfactual asymmetry: mitigated by symmetric CF evaluator; PAPER A validation only; support gap noted.
3. Informative missing outcomes / G3 incompleteness: mitigated by denominators, bounds, tipping point, m_cap; primary inference blocked until G3 closes.
4. Serial dependence and overlapping horizons: epoch-series inference, k-based bandwidth/block floors, non-overlap robustness.
5. Cross-instrument dependence: epoch is the cluster; instrument-independence rejected.
6. Peeking / stopping on favorable result: sealed monitor, single final look, no numeric interim.
7. Small N and sparse activity (p_active may be tiny, N=757 mismatch=0): CLT may fail; benchmark sparsity and validity region.
8. Heavy tails: t2.5/t3 cells; CS and bootstrap qualification.
9. Multiple testing, regime mining, instrument mining: one confirmatory H; strata exploratory; finite preregistered lists.
10. Cost-model dependence: frozen primary cost model; challengers exploratory + sign-reversal check.
11. Retex feedback / config drift: freeze, new epoch on any change, no pooling.
12. Future replay contamination: replay roles restricted, access logged, no pooling.
13. Residual unmodelled risk: no-market-impact assumption, H mark-out ≠ strategy PnL, L1-only depth, evaluator shared-model error cancelling in d but not in levels.

---------------------------------------------------------------------
## S-15 V3.1 clause mapping (BLOCKED: exact V3.1 source unavailable)

Names below are taken from the mission text only; their presence/wording inside V3.1 itself is UNVERIFIED. No exact section mapping is claimed.

| Clause name (from mission) | Class |
|---|---|
| fixed N=500 / N≈250–500 as stopping basis | REJECTED as universal rule → AMENDED (S-11) |
| treatment = quorum_required 2→1 | PRESERVED |
| "does B trade more" as scientific question | REJECTED → AMENDED (S-2) |
| QUORUM_ONLY_SUPPRESSED as population | AMENDED (SECONDARY / DESCRIPTIVE_ONLY) |
| H=1 bar / PT1H | AMENDED (PROVISIONAL, attestation required) |
| MATERIALITY_MARGIN operator-selected | PRESERVED; unit and claim type added |
| N=757 differential | PRESERVED as engineering evidence only |
| legacy 4.14M decisions ineligible | PRESERVED |
| ECONOMIC_MEASUREMENT_COMPLETE_V1 / UNKNOWN ⇒ ineligible | AMENDED: ineligible for point estimation, retained in DENOMINATOR, carried to bounds |
| A paper outcome vs B counterfactual | AMENDED (symmetric CF; PAPER A = validation) |
| HAC primary / Stationary bootstrap robustness / CS monitor / SPA-StepM | UNRESOLVED (method selection pending benchmark) |
| G3 open / primary economic inference blocked | PRESERVED |
| quorum value | PRESERVED (unchanged) |

---------------------------------------------------------------------
## Operator-required parameters (none chosen here)

M and claim type; A_min; B_method confirmation from benchmark; m_cap; pi_min; W_max; d_min/d_max derivation; max duration/resource cap; tau* grid; runtime budget; attestation that PT1H matches strategy lifetime and cadence; statement whether N=757 inputs exercised quorum divergence; PAPER A residual band.
