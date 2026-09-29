# bench/oss_trading_infra_v1

Microtests for report 017 (`reports/017_oss_trading_infra/`). External OSS only; no AurumShift code.

* `setup_envs.sh` – builds 12 isolated virtualenvs under `$EBASE` (default `/tmp/e`).
* `run_all.sh` / `run_t03.sh` – re-run tests, rewriting `results/`.
* `py/` – one script per test (t01 … t16), shared `common.py`, `dq_data.py`; `repo_health.py` computes maintenance metrics from bare blobless git clones.
* `results/` – raw JSON output committed as evidence. `t11_*` (network) are time-stamped snapshots from 2026-09-29 and will differ on re-run.

All synthetic data are seeded (`common.py`, `dq_data.py`, in-script `rng`). No fabricated benchmark numbers: every figure in the reports comes from a file in `results/` or is labelled otherwise.
