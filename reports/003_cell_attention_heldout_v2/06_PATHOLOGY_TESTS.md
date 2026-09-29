# 06 — Pathology tests (P1–P8)

Sources: held-out S1–S10 (`results/heldout`), unit tests (`tests/test_semantics.py`), descriptive sensitivity (`results/sensitivity`, 07) and a **post-hoc** diagnostic (`results/adversarial/followup_B_backoff.json`, seeds 4000–4019, written after Phase B and never used for selection). Verdict vocabulary per policy: `NOT_OBSERVED` / `OBSERVED_MILD` / `OBSERVED` (threshold: beyond the practical thresholds of `protocol.json`). All labels are **OBSERVED in this experimental model**, none is a general PROVEN claim, except P8 items marked PROVEN-by-test (deterministic unit tests + counters over all 600 River/VW runs).

Summary (details below):

| Pathology | A | B | C (River as shipped) | D (VW) | C2 (River+guard) |
|---|---|---|---|---|---|
| P1 NEW_ARM_STARVATION | NOT_OBSERVED (mean per-run max first attempt 8 cycles) | NOT_OBSERVED (mean per-run max 8) | **OBSERVED** (4.7 % / 12.6 % of new cells never attempted in S1 / S10; mean per-run max first attempt 306 cycles) | OBSERVED_MILD (0.7 % / 2.1 % never; mean per-run max 114) | OBSERVED_MILD (0 % never in S1, 7.8 % in S10; first attempt ≈ 58 cycles) |
| P2 SILENT_CELL_CAPTURE | NOT_OBSERVED (+0.024…+0.034 over uniform baseline: proportional, not capture) | NOT_OBSERVED (−0.026…−0.112) | **OBSERVED** (+0.024 S4, +0.106 S5, **+0.264 S9**) | NOT_OBSERVED (−0.003…−0.040) | NOT_OBSERVED (−0.028…−0.115) |
| P3 REWARD_LOCK_IN | n/a (no reward following) | OBSERVED_MILD (S3 +0.021) | OBSERVED_MILD (S3 +0.056; S2 not) | OBSERVED_MILD (S3 +0.057) | OBSERVED_MILD (S3 +0.043) |
| P4 FORGETTING_PATHOLOGY | NOT_OBSERVED | NOT_OBSERVED at frozen `M=4`; **OBSERVED if backoff disabled (`M=1`)** | n/a (estimate freezes rather than decays; capture arises through frozen high estimates, see P2) | n/a | NOT_OBSERVED |
| P5 COLD_START_EXPLOSION | NOT_OBSERVED (90% of 90 new cells attempted by cycle 8) | NOT_OBSERVED (mean per-run max 8) | OBSERVED (135 cycles) | OBSERVED_MILD (48) | OBSERVED (56) |
| P6 CHURN | NOT_OBSERVED (turnover ≈ 1: uniform rotation) | NOT_OBSERVED | OBSERVED_MILD (12.6 % new cells unseen; max starvation 180) | OBSERVED_MILD | OBSERVED_MILD |
| P7 RETURN_FROM_DORMANCY | not recovered (100 % censored) | recovered (delay ≈ 60) | recovered fast (9) | recovered (32; 5 % censored) | **OBSERVED failure** (100 % censored, target share 0.000) |
| P8 NO_EVIDENCE_IS_NOT_NEGATIVE | PROVEN-by-test | PROVEN-by-test | PROVEN-by-test | PROVEN-by-test | PROVEN-by-test |

## P1 — NEW_ARM_STARVATION: can a new cell remain permanently unseen?

Cells born during evaluation (S1: 150 new cells; S10: 180 new cells). `never attempted` = not attempted before the end of the run (≤ 320 cycles ⇒ "permanent within the horizon").

Fraction of new cells never attempted:
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S1_MASSIVE_COLD_START | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.047 ± 0.015 | 0.007 ± 0.019 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| S10_DYNAMIC_POPULATION | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.126 ± 0.025 | 0.021 ± 0.024 | 0.078 ± 0.016 | 0.000 ± 0.000 |

Median / p95 / max cycles to first attempt:
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S1_MASSIVE_COLD_START | 4.3 ± 0.5 | 3.1 ± 0.3 | 45.8 ± 7.2 | 22.2 ± 8.3 | 45.8 ± 5.1 | 11.0 ± 0.0 |
| S10_DYNAMIC_POPULATION | 2.0 ± 0.0 | 0.0 ± 0.0 | 24.5 ± 3.8 | 6.1 ± 4.9 | 25.4 ± 3.3 | 7.5 ± 0.0 |
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S1_MASSIVE_COLD_START | 8.0 ± 0.0 | 8.0 ± 0.0 | 197.4 ± 5.8 | 77.0 ± 48.4 | 57.1 ± 0.8 | 18.0 ± 0.0 |
| S10_DYNAMIC_POPULATION | 3.0 ± 0.0 | 1.0 ± 0.0 | 80.4 ± 4.3 | 35.1 ± 12.6 | 51.0 ± 0.0 | 9.0 ± 0.0 |
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S1_MASSIVE_COLD_START | 8 ± 0 | 8 ± 0 | 306 ± 27 | 114 ± 79 | 58 ± 1 | 18 ± 0 |
| S10_DYNAMIC_POPULATION | 3 ± 0 | 1 ± 0 | 140 ± 27 | 73 ± 31 | 52 ± 0 | 9 ± 0 |

Reading: A and B (and R) never leave a new cell unseen; A's exploration weight (1.5) plus its floor reaches new cells in 4 cycles (median); B's `+∞` index for unseen cells does it in 3 (S1), 0 (S10). River-as-shipped ε-greedy (C) reaches new cells only through ε-exploration and leaves 4.7–12.6 % unseen; the guard (C2) removes S1's unseen cells but not S10's (cells that live < the guard interval `S=50` are retired before they are revisited: 7.8 %). VW (D) is mild.

## P2 — SILENT_CELL_CAPTURE: can unavailable cells absorb excessive attention?

Silent share of attempts (uniform allocation would give the baseline):
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S4_TEMPORARY_SILENCE | 0.068 ± 0.001 | 0.011 ± 0.000 | 0.061 ± 0.021 | 0.034 ± 0.016 | 0.009 ± 0.001 | 0.038 ± 0.001 |
| S5_PROVIDER_DATA_GAP | 0.160 ± 0.013 | 0.023 ± 0.002 | 0.242 ± 0.081 | 0.108 ± 0.057 | 0.022 ± 0.002 | 0.136 ± 0.013 |
| S9_LONG_DORMANCY_RETURN | 0.164 ± 0.001 | 0.023 ± 0.000 | 0.395 ± 0.058 | 0.090 ± 0.040 | 0.016 ± 0.000 | 0.130 ± 0.001 |
Baseline:
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S4_TEMPORARY_SILENCE | 0.037 | 0.037 | 0.037 | 0.037 | 0.037 | 0.037 |
| S5_PROVIDER_DATA_GAP | 0.136 | 0.136 | 0.136 | 0.136 | 0.136 | 0.136 |
| S9_LONG_DORMANCY_RETURN | 0.130 | 0.130 | 0.130 | 0.130 | 0.130 | 0.130 |
Excess = share − baseline:
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S4_TEMPORARY_SILENCE | +0.030 ± +0.001 | -0.026 ± +0.000 | +0.024 ± +0.021 | -0.003 ± +0.016 | -0.028 ± +0.001 | +0.000 ± +0.001 |
| S5_PROVIDER_DATA_GAP | +0.024 ± +0.002 | -0.112 ± +0.011 | +0.106 ± +0.074 | -0.027 ± +0.055 | -0.114 ± +0.011 | +0.000 ± +0.001 |
| S9_LONG_DORMANCY_RETURN | +0.034 ± +0.001 | -0.107 ± +0.000 | +0.264 ± +0.058 | -0.040 ± +0.040 | -0.115 ± +0.000 | -0.000 ± +0.001 |
Share on cells silent for > 40 consecutive cycles:
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S4_TEMPORARY_SILENCE | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| S5_PROVIDER_DATA_GAP | 0.120 ± 0.010 | 0.012 ± 0.001 | 0.182 ± 0.057 | 0.081 ± 0.045 | 0.011 ± 0.001 | 0.097 ± 0.010 |
| S9_LONG_DORMANCY_RETURN | 0.135 ± 0.001 | 0.016 ± 0.000 | 0.334 ± 0.049 | 0.072 ± 0.034 | 0.008 ± 0.000 | 0.104 ± 0.001 |

Reading: **only C is captured** (S9: 39.5 % of attention on silent cells vs 13 % baseline; mechanism, INFERENCE consistent with V1 04 R4: a silent cell's River estimate freezes at its last high value and ε-greedy exploits it forever because no-evidence returns nothing to update). A stays slightly above baseline (the `data_gap` mark grants a 5 % floor to such cells, and lifecycle weights never change with silence) — proportional, not capture. B, D, C2 stay below baseline.

## P3 — REWARD_LOCK_IN: can historical winners monopolise the scheduler after a regime change?

Excess attention on the cells that *lost* value (share − population share) in the 50–150 cycles after the change:
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S2_ABRUPT_REGIME_CHANGE | -0.029 ± +0.008 | -0.090 ± +0.017 | -0.150 ± +0.034 | -0.118 ± +0.036 | -0.128 ± +0.026 | +0.001 ± +0.002 |
| S3_SLOW_DRIFT | -0.005 ± +0.002 | +0.021 ± +0.020 | +0.056 ± +0.056 | +0.057 ± +0.064 | +0.043 ± +0.044 | -0.001 ± +0.001 |
Attention on the cells that *gained* value (target share vs population share):
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S2_ABRUPT_REGIME_CHANGE | 0.204 ± 0.038 | 0.369 ± 0.082 | 0.397 ± 0.154 | 0.417 ± 0.161 | 0.375 ± 0.143 | 0.193 ± 0.037 |
| S3_SLOW_DRIFT | 0.170 ± 0.004 | 0.145 ± 0.029 | 0.097 ± 0.065 | 0.123 ± 0.056 | 0.109 ± 0.044 | 0.167 ± 0.002 |
| S9_LONG_DORMANCY_RETURN | 0.253 ± 0.007 | 0.588 ± 0.019 | 0.642 ± 0.093 | 0.444 ± 0.150 | 0.000 ± 0.000 | 0.207 ± 0.006 |
(population shares: S2 0.194, S3 0.167, S9 0.208.) Adaptation delay (and censoring) are in 05 §2.
Reading: in the abrupt change (S2) every adaptive policy quickly moves away from the degraded cells (all negative excess). In the slow drift (S3) all reward-following rules keep 2–6 pts extra attention on the falling cells during that window (mild lock-in) and give the *rising* cells less than their population share until the drift is well advanced — adaptation delays 174–215 cycles. No policy shows monopolisation (max top-10 % share after change 0.52 for C).

## P4 — FORGETTING_PATHOLOGY: does decay make old/silent cells artificially attractive?

In D-UCB, discounting `N` without new evidence *raises* a silent cell's exploration bonus, and an attempt that returns nothing changes no state, so the cell stays attractive (V1 04 P4 predicted a perpetual loop). Post-hoc diagnostic on B (frozen `γ=0.9995`, `S=25`; only the backoff cap `M` varied; X1 = half the fleet permanently silent from τ=40, X5 = the 30 best cells return nothing on 50 % of attempts):

| scenario | M | info_ratio | silent share | uniform baseline | stale | starvation |
|---|---|---|---|---|---|---|
| X1 permanent silence | 1 (no backoff) | 0.209 | **0.674** | 0.438 | 0.000 | 0.000 |
| X1 | 4 (frozen) | 0.694 | 0.075 | 0.438 | 0.000 | 0.066 |
| X1 | 16 | 0.710 | 0.056 | 0.438 | 0.000 | 0.096 |
| X5 flaky high-value | 1 | 0.505 | 0.280 | 0.125 | 0.000 | 0.000 |
| X5 | 4 (frozen) | 0.557 | 0.046 | 0.125 | 0.070 | 0.022 |
| X5 | 16 | 0.557 | 0.042 | 0.125 | 0.073 | 0.034 |

**OBSERVED:** without backoff B is captured (67 % of attention on permanently silent cells; information worse than round-robin's 0.336); with the frozen backoff the loop disappears (7.5 %). Also in the sensitivity grid (07): `M=1` ⇒ silent excess **+0.194** vs −0.079 with `M=4`. So the guard *without* the V1-untested no-evidence backoff is unsafe, which supports V1's INFERENCE (04 P4) and shows the backoff is a necessary component, not an option. The cost of the backoff is the flip side: P7 and X5's under-attention.

## P5 — COLD_START_EXPLOSION (S1: 90 new cells at once, then 60 more)

Cycles until 90 % of the first cohort (90 cells) has been attempted at least once:
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S1_MASSIVE_COLD_START | 8 ± 0 | 8 ± 0 | 135 ± 25 | 48 ± 19 | 56 ± 1 | 12 ± 0 |
Information ratio over the first 40 evaluation cycles:
| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S1_MASSIVE_COLD_START | 0.514 ± 0.029 | 0.538 ± 0.026 | 0.679 ± 0.064 | 0.627 ± 0.062 | 0.679 ± 0.064 | 0.513 ± 0.037 |
A/B/R touch the cohort in 8–12 cycles (K=10 attempts per cycle ⇒ physical minimum ≈ 8.1 cycles for 81 cells). River-based rules need 56–135 cycles (ε-driven). Note C/C2/D obtain a **higher** first-40-cycle information ratio (0.63–0.68 vs 0.51–0.54) by exploiting the established cells while ignoring the cohort — early information gain and cold-start coverage pull in opposite directions.

## P6 — CHURN (S10: 15 waves; 12 births and 10 retirements per wave)

Retirement invariant: **0 attempts on ineligible (retired/unborn) cells in 1 200 held-out runs** (`attempts_on_ineligible`, checked for every policy) — PROVEN for these runs. Allocation stability: turnover A 0.997 / R 1.000 (uniform rotation), B 0.533, D 0.446, C2 0.309, C 0.270 (values in 05). Starvation in S10: A/B/R 0.000, C 0.061, D 0.023, C2 0.000; max starvation duration: R 10, B 26, A 28, C2 52, D 148, C 180. No policy "destabilised" in the sense of a collapse; the reward-following ones simply leave 2–13 % of new cells unseen (P1). A's exploration mask logs (floor units by reason, S10): `no_evidence` 22.2, `pit_unverified` 21.7, both 2.6 units per run — reasons are kept separate.

## P7 — RETURN_FROM_DORMANCY (S9: 25 cells silent τ∈[30,230) then return with higher value)

Delay for the returned cells to reach ≥ 2× their population share (censored at 90 cycles) and censoring fraction — see 05 §2 (delay: A 90*, B 60, C 9, D 32, C2 90*; censored 100 % for A, R, C2 and 0/0/5 % for B/C/D) and target share in the 50–150 window above (A 0.253, B 0.588, C 0.642, D 0.444, **C2 0.000**).
**OBSERVED failure of C2**: with the frozen guard (`S=50`, `M=4`) a cell that returns nothing is revisited after 100 cycles, then every 200; the S9 cells fall silent at τ=30, so their revisits fall at τ≈130 and τ≈330 — the return at τ=230 is only noticed after the end of the run. While a cell is in its backoff window it is also excluded from River's candidate list, so River cannot notice the return either (target share 0.000).
Descriptive sensitivity on S9 (5 seeds, `results/sensitivity/{B,C2}.json`) shows that return latency is essentially **a phase lottery of the backoff schedule, bounded above by `S·M`**, not a smooth function of the parameters: C2 `S100/M4` recovers in 11 cycles (its first backoff interval, 200 cycles, happens to end exactly at the return), `S25/M4` in 72, `S50/M4` and `S25/M16` never (censored 90); B with `S=100` recovers in 9, with the frozen `S=25` in ≈ 59, with `S=50` or `S=200` never within 90 cycles; without backoff (`M=1`) recovery is immediate (9) — at the price of P2/P4 (silent capture). So the frozen configurations are neither uniquely bad nor good here; the honest statement is that **any bounded-backoff design trades silent-cell safety against return latency ≤ S·M, and its outcome on a given return time is a matter of phase** (INFERENCE from the sensitivity table; not a tested closed form). A does not recover attention *because it never concentrates* (returned-cell share 0.253 vs 0.208 population share, slightly above thanks to the `data_gap` floor).

## P8 — NO_EVIDENCE_IS_NOT_NEGATIVE (explicit proof)

1. **Environment:** silent attempts return `ATTEMPTED_NO_EVIDENCE` with `value=None`; `EVIDENCE(0.0)` is a separate outcome (`test_silence_never_returns_a_value`, `test_evidence_zero_is_distinct_from_no_evidence`).
2. **Ledger:** 20 consecutive `ATTEMPTED_NO_EVIDENCE` leave `n_evidence`, `last_evidence`, `m_slow`, `m_fast` bit-identical; only `n_attempts`, `last_attempt`, `consecutive_no_evidence` move (`test_ledger_no_evidence_changes_no_value_statistic`).
3. **Policies, feed-only-silence test:** 25 cycles of `ATTEMPTED_NO_EVIDENCE` only ⇒ B: `ΣN = ΣX = 0`; River: `_n = 0`; VW: `learn_calls = 0` (`test_p8_feeding_only_no_evidence_leaves_estimators_untouched`).
4. **Over all 1 200 held-out runs** (counter audit, 600 runs use River or VW): River `_n == #EVIDENCE events` and `nonfinite_dropped == 0`; VW `learn_calls == #EVIDENCE events` and `no_evidence_skipped == #no-evidence events` — **0 violations in 600 checks** (110 739 no-evidence events over the 1 200 runs). B's `N, X ≥ 0` always.
5. **Lifecycle (A):** state classification is unchanged by age 10⁵ cycles and 15 consecutive no-evidence (`test_policy_a_stale_is_not_degrading_and_gap_is_not_low_information`); staleness and `data_gap` only raise the *exploration mark* (floor share), never the state.
6. **Attention conservation (A):** `Σ final = K` with max error `7.1e-15` over all held-out cycles; no negative share; retired cells never in the eligible set.

Caveat: P8 proves that no policy *scores* missing evidence as failure. It does **not** prove that policies behave well under silence: P2/P7 show they can still mishandle it *without* scoring it (C captured; C2 unable to notice returns).
