# bench/uncertainty_v1 — uncertainty calibration & abstention (external research)

Reproduces `reports/012_uncertainty_calibration/`. Python 3.11, numpy, scipy, scikit-learn, pandas, tabulate, matplotlib. Public data are downloaded at run time (OpenML `electricity`, `credit-g`; sklearn `breast_cancer`, `california_housing`); nothing is redistributed. Set `OMP_NUM_THREADS=1` when running several processes.

```
py/worlds.py           synthetic BUY/SELL/HOLD worlds + 8 shift scenarios (+ iid control)
py/calibrators.py      Platt, beta, isotonic, BBQ-lite, temperature (top-label calibrators are argmax-preserving)
py/models.py           LR / over-fit GBM base, bootstrap ensemble (MI), Mahalanobis, repeat detector
py/metrics.py          Brier, log loss, ECE, reliability, FCR/CWM, utility, turnover, risk-coverage
py/run_static.py       static calibration + selective scores        (a-b seeds, magnitude, prefix)
py/online.py           static vs sliding/expanding/decay recalibration with label-maturity delay + leaky controls
py/conformal.py        regression intervals and LAC sets: gaussian, split, rolling, weighted, ACI, normalised
py/run_abstain.py      abstention rules / budgets, thresholds from validation only
py/shift.py            shift detectors + 4-way cause attribution (tune | hold modes)
py/run_public.py       ELEC2, credit-g, breast-cancer, California
py/analyze.py          -> results/tables/*.md, results/key_numbers.json ; py/figures.py -> results/figures ; py/methods_catalog.py
tests/test_no_lookahead.py   leakage harness (run from this directory: python3 tests/test_no_lookahead.py)
frozen_config.json     hyperparameters frozen from tuning seeds 100-103 (mag 0.6) before held-out seeds 0-11 (mag 1.0)
results/               raw per-seed CSVs, tables, figures
```
Held-out commands used (from `py/`): `run_static.py 0-6|6-12 1.0 ../results/static_hold_<a-b>`; `online.py 0-6|6-12 1.0 ../results/hold_a|b '{"W":[600],"HL":[400]}' leaky`; `conformal.py 0-6|6-12 1.0 ../results/hold_a|b '{"W":300,"HL":150,"gamma":0.01}'`; `run_abstain.py`; `shift.py hold 0-6|6-12 1.0 ../results/diag`; `run_public.py ../results/public`. Tuning: seeds 100-104, magnitude 0.6 (`static_tune_*`, `tune_*_online.csv`, `ctune_*`, `diag_diag_tuning.csv`). Then `cd bench/uncertainty_v1 && python3 py/analyze.py && python3 py/figures.py && python3 py/methods_catalog.py`.
Note: `results/diag_diagrows_*.csv.gz` hold the per-row diagnosis features (regenerable).
