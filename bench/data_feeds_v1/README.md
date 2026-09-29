# bench/data_feeds_v1

Raw artifacts and code for `reports/005_data_feed_resilience/`. External research only; no private AurumShift code.

* `py/probe_lib.py` — HTTP helper (timing, raw capture). `py/sweep1.py`, `sweep2.py` — discovery sweeps.
* `py/bars_lib.py`, `run_bars.py <tag>` — normalised 1-minute bar fetch on 18 venue series; `analyze_bars.py <tag>`, `consensus.py`, `lagtest.py` — comparison.
* `py/dv.py` (funding/OI/options/basis/liquidations), `ws_sample.py` (20 s WS samples), `fxgold.py`, `macro.py`, `latency.py`.
* `py/catalog.py` + `py/gen_reports.py` — source catalog and generator for the report tables/counts (`results/final_block.txt`).
* `results/` — derived JSON; `results/docs_facts.json` — official-page quotes (NOT_FOUND where not retrievable). `raw/` — first-pass response captures and normalised bars (large bodies >400 KB removed, see report 12).

Reproduce: `pip install requests websockets`, run from `py/`. Results depend on the network egress (several providers geo-block cloud IPs) and the wall-clock time.
