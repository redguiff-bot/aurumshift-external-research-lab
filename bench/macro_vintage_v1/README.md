# bench/macro_vintage_v1

Reproduce: `cd py && python3 probe_sources.py && python3 alfred_test.py && python3 alfred_paths.py && python3 other_sources.py && python3 calendars.py && python3 extra_checks.py && python3 licence_facts.py` (stdlib only; `openpyxl` only if you want to read the Philly Fed xlsx). Network needed; keyless.
* `raw/` raw responses + `*.meta.json` (status, headers, `receipt_time_utc`, sha256).
* `results/` JSON summaries used by the reports in `reports/010_macro_vintage_event_data/`.
* `alfred_test.py` runs the full series loop (slow, ~5 min); `alfred_paths.py` ~10 min.
* BLS v1 and EIA DEMO_KEY quotas are per shared IP; reruns may return quota errors (`other_sources.py` reuses `raw/bls_api_v1`).
