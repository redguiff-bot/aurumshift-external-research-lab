# capacity_v1 — synthetic capacity/turnover allocation study (external research only)

Reports: `reports/008_risk_capacity_turnover/`. No private AurumShift code, no integration.

```
py/env.py                 simulator (world generation, run loop, metrics, hindsight LP bound)
py/scenarios.py           S1..S12 + H1..H3, split-specific variants/seeds
py/policies.py            baselines, candidate methods, oracles (flagged NOT_IMPLEMENTABLE), tuning grids
py/runner.py              tune | validate | robust | failure | heldout   (heldout refuses to run if tuned params changed)
py/validate_and_leakage.py  Erlang-B check, greedy==MILP, LSA==top-k, leakage tests (T1..T4) -> results/validation.json
py/heldout_verdict.py     pre-registered adjudication (hash recorded in prereg/PREREGISTRATION.json)
py/analyze.py, report_tables.py, build_reports.py   tables for the reports
py/posthoc.py             exploratory diagnostics on VALIDATION worlds only (no verdict weight)
py/oss_probe.py           executes SciPy/OR-Tools/SimPy/MABWiser/River/PyPortfolioOpt/scikit-learn/CVXPY checks
prereg/PREREGISTRATION.json   v2, committed before the held-out run
results/                  raw CSVs (gz), tuned params, verdict JSON, tables/; superseded_run1/ = archived first run
```
Reproduce (Python 3.11, numpy/scipy/pandas; OSS probe also needs ortools, mabwiser, simpy, river, cvxpy, pyportfolioopt, scikit-learn):
`python3 validate_and_leakage.py; python3 runner.py tune; python3 runner.py validate; <pre-register>; python3 runner.py heldout; python3 heldout_verdict.py`
