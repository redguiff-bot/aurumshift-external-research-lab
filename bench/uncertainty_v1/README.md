# bench/uncertainty_v1

Code and raw results for `reports/012_uncertainty_calibration/`. External research only; no private AurumShift code.

* `py/ulib.py` — metrics (Brier, log-loss, ECE, reliability, selective risk, false-confidence, turnover), calibrators (Platt, temperature, beta, isotonic, Bayes-binning), delay-aware online recalibration (`run_online`, PIT assertion + leaky audit variants), conformal (split/rolling/weighted/ACI, classification + regression), detectors, synthetic world.
* `py/exp_static.py` (Q1), `exp_shift.py` (Q2/Q3, risk-coverage), `exp_taxonomy.py` (Q4), `exp_online.py` (§6), `exp_conformal.py` (§7), `make_tables.py` (results → `results/tables/*.md`).
* `data/elec2.csv` — OpenML `electricity` v1 (ELEC2), fetched via `sklearn.datasets.fetch_openml`; California housing / breast cancer come from scikit-learn.
* `results/` — raw CSVs and generated markdown tables.

Reproduce (from `py/`, ~10 min on 4 cores): `pip install numpy scipy scikit-learn pandas`; run the `exp_*.py` scripts then `make_tables.py`. Set `OMP_NUM_THREADS=1` when running several processes. Seeds are fixed; results are deterministic.
