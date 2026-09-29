# bench/alternative_data_v1

Raw artifacts and code for `reports/016_alternative_data/`. External research only; no private AurumShift code; no integration.

* `py/lib.py` HTTP helper (retry, timing, header capture). `py/catalog.py` source catalogue (39 sources; OBS vs DOC fields). `py/pit.py` PIT classification. `py/adjudication.py` doctrine outcomes.
* `py/s1_probe.py` — 3-call probes per endpoint → `results/probe_results.json`. `py/s2b_revision.py` — re-fetch revision test → `results/revision_test.json`. `py/s5_latency.py` — newest-row latency snapshot.
* `py/s2_fetch.py <fn...>` — daily histories → `data/*.csv` (window 2023-10..2026-09). `py/s3_incremental.py` — pre-registered incremental-information tests → `results/incremental.{json,csv}`. `py/s4_power.py` — power/MDE simulation → `results/power_btc.json`.
* `py/gen_reports.py` — writes the markdown reports from the results (numbers are read from `results/`, not typed).
* `results/source_records.{json,csv}` per-source attribute records; `results/final_block.txt`; `results/gh_playground_stability.json`, `results/cftc_headers.json` manual observations (timestamps inside).

Reproduce (network egress dependent; several providers rate-limit or block shared IPs): `pip install pandas numpy scipy statsmodels requests xlrd`, then from `py/`: `python3 s2_fetch.py`, `s1_probe.py`, `s2b_revision.py`, `s5_latency.py`, `s3_incremental.py`, `s4_power.py`, `gen_reports.py`. Data are single-time snapshots taken 2026-09-29 (UTC); vendor history can be recomputed, so a re-run may differ.
