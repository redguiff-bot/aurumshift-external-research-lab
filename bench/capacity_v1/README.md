# bench/capacity_v1 — capacity-constrained admission / slot-economics study (external, synthetic)

Study: `reports/008_risk_capacity_turnover/`. EXTERNAL_RESEARCH_ONLY: no AurumShift private code, no integration, no production recommendation.

```
src/      world.py (deterministic generator), engine.py (simulator+metrics), policies.py (12 implementable + oracle upper ref),
          common.py, run_tuning.py (tuning->validation->freeze), run_heldout.py (executes once), run_diag.py, run_div_stress.py,
          analysis.py, analysis_diag.py, analysis_extra.py, verify_repro.py, oss_probe.py, make_reports.py
configs/  frozen_params.json (validation-selected), prereg.json (committed before heldout)
tests/    test_capacity.py (77 tests: determinism, invariants, unknown-cost != zero-cost, NO-LOOKAHEAD metamorphic test, oracle canary)
results/  tuning/ validation/ heldout/ (H1 primary, H2 ingest matrix, H3 capacity sweep; immutable) diagnostics/ analysis/
```
Reproduce (numpy, pandas, scipy, pytest; Python 3.11):
```
PYTHONPATH=src pytest -q tests
python3 src/run_tuning.py            # ~1.5 min on 4 cores
python3 src/run_heldout.py           # ~2 min; refuses to overwrite existing heldout results
python3 src/run_diag.py && python3 src/run_div_stress.py
python3 src/analysis.py && python3 src/analysis_diag.py && python3 src/analysis_extra.py && python3 src/verify_repro.py && python3 src/oss_probe.py
python3 src/make_reports.py          # regenerates the report tables
```
Seeds: tuning 1000-1005, validation 2000-2007, heldout 3000-3019 (H2/H3 3000-3009), diagnostics 6000-7009, div-stress 8000-8019.
Order of evidence in git: simulator/tests/tuning/freeze/pre-registration commit precedes any heldout file.
