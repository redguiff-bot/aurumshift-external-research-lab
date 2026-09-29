# 05 — Held-out protocol

## Procedure (executed in this order; commit history is the evidence)
1. Build simulator + tests (77 pass).
2. **TUNING**: every (policy, parameter, ingest mode) config on 13 scenarios × seeds 1000–1005 (K=4). Tuning objective: macro-mean M1 (tuning only).
3. **VALIDATION**: top-3 configs per policy re-run on 13 × seeds 2000–2007 (different world parameters); best on validation is frozen → `configs/frozen_params.json`.
4. **PRE-REGISTRATION** committed (`configs/prereg.json`): metrics, equivalence margin δ=0.25 bps, rules for FIFO failure/equivalence, complexity justification, verdict rules, sha256 of code and frozen params. Commit `ad2adda` precedes any heldout file.
5. **HELDOUT** (`src/run_heldout.py`, refuses to overwrite): H1 primary (13×20 seeds×13 policies), H2 ingest matrix (10 seeds × 4 modes), H3 capacity sweep (K∈{3,4,6,10}, 10 seeds; parameters **not** retuned per K).
6. Analysis code was written after heldout results existed but **implements only the pre-registered rules**; additional analyses (targeted pairs, D6 stress) are labelled post-hoc/diagnostic and were run on validation-split worlds or as descriptive comparisons. No parameter changed after heldout.

Frozen configuration: sha256(frozen_params.json) = `ebcd46c4668407ad…`; code hash at freeze `952d5c02e31a5f67…` (later commits add analysis/report scripts only).
Note: the pre-registered hash covers `src/*.py` at freeze time; `run_heldout.py`, `analysis*.py`, `run_diag.py`, `verify_repro.py`, `oss_probe.py`, `make_reports.py` were added afterwards. Simulator, policies and world files (`world.py`, `engine.py`, `policies.py`, `common.py`, `run_tuning.py`) were unchanged (verify with `git diff ad2adda -- bench/capacity_v1/src/{world,engine,policies,common,run_tuning}.py`).

## Frozen parameters
| index | params | ingest_primary | validation_M1 |
|---|---|---|---|
| CORR_AWARE | {"gamma": 0.1} | SCORE_UPDATE | 2.447 |
| EQUAL_QUOTA | {} | RAW | 2.006 |
| FIFO | {} | RAW | 2.052 |
| FIFO_SCREEN | {} | SCORE_UPDATE | 2.206 |
| LINTS | {"alpha": 0.1} | SCORE_UPDATE | 2.472 |
| OLDEST_SLOT | {"min_hold": 4} | RAW | 2.387 |
| ORACLE_GREEDY_UB | {} | RAW | n/a |
| RANDOM | {} | RAW | 2.037 |
| ROUND_ROBIN | {} | RAW | 2.004 |
| SCORE_RANK | {} | SCORE_UPDATE | 2.399 |
| SLOTHOUR | {} | SCORE_UPDATE | 2.449 |
| SLOTHOUR_SHADOW | {"theta": 0.25} | SCORE_UPDATE | 2.451 |
| UNCERTAINTY_LCB | {"kappa": 0.0, "omega": 0.6} | SCORE_UPDATE | 2.505 |

Baselines A–E use RAW ingest as primary (naive default) regardless of the tuned mode; their tuned modes are reported in H2.

## Pre-registered rules and outcomes
- Equivalence margin δ = 0.25 bps/avail-slot-hour (INFERENCE: ≈10% of typical M1; sensitivity δ∈{0.1,0.5} reported in 13).
- COMPLEXITY_JUSTIFIED ⇔ complex method beats best simple by >δ, CI_lower>0 and wins ≥8/13 → **not met** (13).
- Verdict machinery: B (beats FIFO by δ with CI>0) = ['SCORE_RANK', 'SLOTHOUR', 'SLOTHOUR_SHADOW', 'UNCERTAINTY_LCB', 'CORR_AWARE', 'LINTS']; T (within δ of best implementable = UNCERTAINTY_LCB) = ['SCORE_RANK', 'SLOTHOUR', 'SLOTHOUR_SHADOW', 'UNCERTAINTY_LCB', 'CORR_AWARE', 'LINTS'] ⇒ |T|≥2 ⇒ MULTIPLE_CAPACITY_METHODS_SUPPORTED.

## What "no post-hoc tuning" means here
No parameter, scenario definition, seed set, metric or rule was altered after heldout execution. Seeds and scenario definitions for heldout share code with tuning but the *world parameters* differ (N, G, τ, CV, ranges). Threat: heldout worlds are from the same generator family (see 14).
