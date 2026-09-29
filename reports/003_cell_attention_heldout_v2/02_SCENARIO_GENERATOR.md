# 02 — Scenario generator (frozen)

Code: `bench/v2/src/scenario_core.py` (builder + global constants), `scenarios_dev.py` (TRAIN/VALIDATION), `scenarios_heldout.py` (S1–S10). sha256 of each in `bench/v2/configs/freeze_manifest.json`. All labels below are **V2-DEFINED** design facts (verified by `tests/test_semantics.py::test_heldout_scenario_structure`), not results.

## 1. Common structure

Absolute cycle `t ∈ [0,400)`; burn-in `t<80` (common uniform logging), evaluation `t ≥ 80`; below, `τ = t − 80`. `K = 10` distinct attempts per cycle. Cells carry: `birth`, `death` (explicit retirement ⇒ `RETIRED`, leaves the eligible set), `group ∈ {0..9}` (generic descriptor visible at birth; cell information probability is group-correlated: `P0 = clip(group_mean + N(0,0.10), 0.03, 0.85)` for established cells), `pit_unverified` (10 %), `mag` (0.5 ordinary, 1.0 rare-high), hidden `P[t,c]` and hidden `silent[t,c]`. New cells: `P0 = clip(0.6·group_mean + 0.4·Beta(2,6) + N(0,0.05))`, with 10 % "gems" `U(0.6,0.8)`. Streams: `SeedSequence([split_code, scenario_idx, seed]).spawn(3)` → generator / outcome uniforms `U[R,n]` / logging seed (common random numbers across policies).

## 2. Held-out families (10; each isolates one failure mode; no variants added to inflate N)

| # | Name | Construction (parameters as frozen) | Distinct failure mode tested |
|---|---|---|---|
| S1 | MASSIVE_COLD_START | 30 established cells; **90 new cells at τ=0** and **60 more at τ=120** (no evidence at birth) | P1 new-arm starvation, P5 cold-start explosion |
| S2 | ABRUPT_REGIME_CHANGE | 120 established; at τ=100 the 2 highest-mean groups drop by 0.45 (floor 0.03) and the 2 lowest-mean groups jump to `U(0.6,0.8)` (group-structured change) | P3 reward lock-in; adaptation delay |
| S3 | SLOW_DRIFT | 120 established; from τ=40 to τ=240 the 20 lowest-`P` cells ramp linearly to `U(0.6,0.8)` and the 20 highest ramp to `U(0.05,0.10)` (cells chosen individually, not by group) | slow degradation/improvement, non-group drift |
| S4 | TEMPORARY_SILENCE | 120 established; 36 random cells are silent for 40 cycles each, start uniform in τ∈[30,230] (staggered); value unchanged after return | P2 silent-cell capture, P4 forgetting pathology |
| S5 | PROVIDER_DATA_GAP | 120 established; 3 whole groups (a "provider") silent τ∈[80,220) simultaneously | correlated outage; `DATA_GAP ≠ LOW_INFORMATION` |
| S6 | STALE_BUT_VALID | 120 stationary cells; all burn-in evidence is stamped **100 cycles old** (`warm_shift=100 > FRESH`) so every cell starts stale although its evidence remains valid; nothing silent, nothing changes | `STALE ≠ DEGRADING`; needless churn vs justified refresh |
| S7 | GENUINELY_LOW_INFORMATION | 120 stationary: 70 cells with `P∈U(0.01,0.06)` (true `ev ≤ 0.03 < 0.05`), 35 medium (group), 15 good `U(0.55,0.80)` | LOW_INFORMATION attention share; `LOW_INFO ≠ DATA_GAP` |
| S8 | RARE_HIGH_INFORMATION | 110 ordinary + 10 rare cells (`P=0.05`, `mag=1.0`, expected `ev = 0.05`) | rare-event discovery |
| S9 | LONG_DORMANCY_RETURN | 120 established; 25 random cells silent τ∈[30,230) (200 cycles) then **return with `P+0.35`** at τ=230 (90 cycles left to recover) | P7 return from dormancy; P2/P4 under long silence |
| S10 | DYNAMIC_POPULATION | 60 established; every 20 cycles (15 waves, τ=0..280) 12 new cells are created and 10 random cells (age ≥ 30) are **explicitly retired** | P6 churn; retired ⇒ attention 0 |

Structural facts asserted by tests: S1 has 90/60 cells born at 80/200; S5's silence is on and off at the frozen boundaries; S6 has `warm_shift=100` and no silence; S7 has ≥ 60 cells with `ev < 0.05`; S8 has exactly 10 rare cells; S9's target cells are silent up to `change_t−1` and non-silent at `change_t`; S10 retires exactly 150 cells and has 240 cells in total.

## 3. Dev families (TRAIN/VALIDATION — deliberately different compositions and numbers)

`T1_mixed_abrupt` (80 est. + 40 new, group-level change at τ=120) · `T2_mixed_drift_gap` (90 est., 15+15 drifting, 25 staggered 50-cycle silences) · `T3_churn_lowinfo` (30 est. + 20 low-information, 8 births/6 retirements every 25 cycles) · `T4_dormancy_rare` (100 est., 5 rare, 15 dormant τ∈[30,150) returning +0.3) · `V1_coldstart_outage` (40 est. + 70 new, 2-group outage τ∈[80,180)) · `V2_abrupt_then_drift` (110 est., 1-group abrupt change then a drift of 10 cells) · `V3_silence_rare_lowinfo` (50 est. + 40 low + 6 rare, 30 staggered 60-cycle silences). None of them is a copy of an S-family; each mixes ≥ 2 mechanisms with different sizes, timings and group structure.

## 4. Isolation evidence

* `tests/test_semantics.py::test_tuning_code_never_references_heldout` (AST-level import check), `::test_dev_generator_refuses_heldout_split`, `::test_seed_ranges_disjoint` — all pass (18/18 tests, see 11 for the final count).
* `results/heldout/params_lock.json` is written (exclusive-create) **before** the held-out run and records the sha256 of the selected parameter files, the protocol, the freeze manifest and the held-out generator.
* Held-out raw results are written with exclusive-create (`open(...,'x')`); a second run cannot silently overwrite them.

`HELDOUT_ISOLATION` verdict: see 11 (`PASS` iff every check above holds at the end of the study and no held-out result preceded any parameter file).
