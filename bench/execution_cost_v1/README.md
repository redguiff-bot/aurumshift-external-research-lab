# bench/execution_cost_v1 — external execution & transaction-cost research bench

EXTERNAL_RESEARCH_ONLY. No AurumShift code, no integration. Report: `../../reports/006_execution_cost_intelligence/`.

```
capture/live_capture.py        REST poller (OKX / Coinbase / Kraken public endpoints): L2 top-N, trades, funding, RTT
data/live, data/deep           raw captures (gz jsonl), public data only (deep = 400-level books, ~8 min)
data/vision/                   Binance Vision zips (NOT committed; fetch commands in analysis/fetch_vision.sh)
data/ohlc/                     public 1h OHLC for FX/gold/WTI/BTC control (unofficial Yahoo chart endpoint)
synthetic/synth.py             deterministic synthetic microstructure truth (market walk, propagator, depletion, limit-order queue)
synthetic/run_synth.py         all synthetic experiments (single/sliced/competing/latency/spread/limit/full-fill/seed stability)
models/models.py               minimal reference implementations of the models under test
contract/cost_contract.py      cost-accounting contract (states, fill-basis embedding, UNKNOWN != 0)
contract/tests_and_threats.py  contract property tests + E1..E15 threat matrix
analysis/*.py                  empirical analyses (live capture, Vision, funding/borrow/roll, FX/gold OHLC, OSS bidask test)
oss_probe/                     OSS candidate findings (json/md) and sourced landscape notes
results/                       all machine-generated outputs (json/csv) that the report tables are built from
report_templates/, build_reports.py   report source + table builder (no hand-typed table numbers)
```

Reproduce (Python 3.11+, numpy, pandas, scipy, requests):

```
python3 synthetic/run_synth.py && python3 contract/tests_and_threats.py     # ~1-2 min, deterministic
sh analysis/fetch_vision.sh                                                 # optional: re-download Binance Vision files
python3 analysis/funding_borrow_roll.py; python3 analysis/empirical_vision.py; python3 analysis/fx_gold_ohlc.py
python3 analysis/empirical_live.py data/live live; python3 analysis/empirical_live.py data/deep deep
/path/to/venv-with-bidask/bin/python analysis/oss_bidask_test.py
python3 build_reports.py
```
Live capture is time-dependent and not reproducible; the raw files used are committed.
