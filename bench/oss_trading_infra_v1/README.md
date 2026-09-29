# bench/oss_trading_infra_v1

Code, raw results and environment records for `reports/017_oss_trading_infra/`. External research only; no private AurumShift code.

* `py/catalog.py` — the 67 candidates; `py/screen.py` — metadata screen (git since 2025-09-29 + PyPI) → `results/screen.json`; `py/footprint.py` — isolated install footprint → `results/footprint.json`; `py/adjudication.py` — per-candidate class + evidence; `py/gen_reports.py` — builds the screen/adjudication/footprint tables and `results/final_block_counts.txt` (writes `_*.md` helper tables into the report folder, which are pasted into `01`, `07`, `08` and then removed).
* `py/mt/` — microtests (one script per test group, shared `common.py`): `bt_engines`, `leak_probe`, `hft_microtest`, `naut_microtest` (+ `naut_lib`, `naut_cross_probe`, `naut_l1_probe`), `abides_microtest`, `orderbook_microtest`, `zl_microtest`, `stats_microtest`, `feat_microtest`, `port_microtest`, `tcm_microtest`, `cal_microtest`, `dq_microtest`, `misc_microtest`, `coll_microtest`, `store_microtest`.
* `sql/` — PostgreSQL 16 + TimescaleDB + pg_partman test and the clickhouse-local ASOF check. Raw outputs in `results/tss_microtest.txt`, `results/clickhouse_local_asof.txt`.
* `env/freeze_*.txt` — exact package versions per venv; `env/system.txt` — system packages; `env/stats_install_first_attempt.log` — the failed first install (`hdrh` is `hdrhistogram` on PyPI; `pandas-ta` needs Python ≥ 3.12).
* `results/` — every JSON/text result cited in the reports.

Reproduction notes (working directory, Python versions, proxy CA path, PostgreSQL preload) are in `reports/017_oss_trading_infra/06_COMPONENT_TESTS.md`. Results that touch the network depend on the egress and the clock. Downloaded data and venvs are not committed.
