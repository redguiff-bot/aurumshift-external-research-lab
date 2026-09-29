# bench/v2 — cell-attention held-out benchmark (external research, synthetic)

Study: `reports/003_cell_attention_heldout_v2/`. V1 (read-only prior evidence): `reports/001_adaptive_strategy_fleet/`.

```
src/         scenario_core.py, scenarios_dev.py (train/validation), scenarios_heldout.py (S1-S10), scenarios_adv.py (post-hoc X1-X5),
             ledger.py, policies.py (A, B, C/C2, D, R), metrics.py, runner.py, tune.py, heldout.py, analysis.py,
             sensitivity.py, sens_summary.py, adversarial.py, adv_followup.py, determinism.py, verify_isolation.py, phase_a.py, freeze.py
configs/     protocol.json (pre-registration), freeze_manifest.json, selected_{B,C,C2,D}.json (frozen parameters)
environment/ python version, install commands, pip freeze
results/     phaseA/ (harness validation, NOT comparative), tuning/, heldout/ (immutable raw + params_lock.json), heldout_analysis/,
             sensitivity/ (+ summary), adversarial/ (post-hoc), determinism/, isolation_report.json
logs/        execution logs
tests/       test_semantics.py (18 tests)
```
Run tests: `PYTHONPATH=src pytest -q tests`. Seeds: train 1000-1004, validation 2000-2004, held-out 3000-3019, pilot 9000-9002, adversarial 4000-4019.
