#!/usr/bin/env bash
# Re-runs every microtest and rewrites results/*.json(l). Network tests (t11) need outbound HTTPS; results are time-dependent.
set -u; E=${EBASE:-/tmp/e}; cd "$(dirname "$0")"; R=results
$E/core/bin/python py/repo_health.py "${GITBARE:-/tmp/g}" $R/repo_health.json >/dev/null 2>&1 || true
for c in sortedcontainers nautilus hftbacktest; do py=$E/core/bin/python; [ $c = nautilus ] && py=$E/nautilus/bin/python; $py py/t01_orderbook.py $c 2>/dev/null | tail -1; done > $R/t01_orderbook.jsonl
for i in 1 2; do $E/nautilus/bin/python -W ignore py/t02_nautilus_replay.py 100000 2>/dev/null | tail -1 > $R/t02_nautilus_run$i.json; done
for L in 0 250; do $E/nautilus/bin/python -W ignore py/t02_nautilus_replay.py 20000 $L 2>/dev/null | tail -1 > $R/t02b_nautilus_latency_${L}ms.json; done
bash run_t03.sh
for e in "vbt vectorbt" "vbt vectorbt_native_MA" "bktpy backtesting" "core backtrader" "core bt"; do set -- $e; $E/$1/bin/python py/t04_causality.py $2 2>/dev/null | tail -1; done > $R/t04_causality.jsonl
for e in "core ta" "misc pandas_ta" "vbt vectorbt" "misc tsfresh"; do set -- $e; $E/$1/bin/python py/t05_feature_prefix.py $2 2>/dev/null | tail -1 > $R/t05_prefix_$2.json; done
$E/core/bin/python py/t06_river_online.py 2>/dev/null | tail -1 > $R/t06_river.json
for e in "core pypfopt" "core riskfolio" "core skfolio" "core metrics" "misc metrics"; do set -- $e; $E/$1/bin/python py/t07_portfolio_risk.py $2 2>/dev/null | tail -1 > $R/t07_$2_$1.json; done
$E/core/bin/python py/t08_calendars.py 2>/dev/null | tail -1 > $R/t08_calendars.json
for e in "core pandera" "gx great_expectations" "misc pointblank" "misc frictionless"; do set -- $e; $E/$1/bin/python py/t09_dataquality.py $2 2>/dev/null | tail -1 > $R/t09_dq_$2.json; done
$E/arctic/bin/python py/t10_storage.py arcticdb 2>/dev/null | tail -1 > $R/t10_arcticdb.json; $E/core/bin/python py/t10_storage.py duckdb_parquet 2>/dev/null | tail -1 > $R/t10_duckdb_parquet.json
for c in ccxt_rest ccxt_ws; do $E/core/bin/python py/t11_collectors.py $c 2>/dev/null | tail -1 > $R/t11_$c.json; done
for c in cryptofeed yfinance; do $E/misc/bin/python py/t11_collectors.py $c 2>/dev/null | tail -1 > $R/t11_$c.json; done
$E/core/bin/python py/t12a_hft_queue.py 2>/dev/null | tail -1 > $R/t12a_hft_queue.json
$E/zipline/bin/python py/t12b_zipline_volshare.py 2>/dev/null | tail -1 > $R/t12b_zipline_volshare.json
$E/nautilus/bin/python py/t12c_nautilus_bookwalk.py 2>/dev/null | tail -1 > $R/t12c_nautilus_bookwalk.json
$E/abides/bin/python py/t13_abides.py 2>/dev/null | tail -1 > $R/t13_abides.json
$E/dbn/bin/python py/t14_dbn.py 2>/dev/null | tail -1 > $R/t14_dbn.json
$E/wq13/bin/python py/t15_almgren_chriss.py 2>/dev/null | tail -1 > $R/t15_almgren_chriss.json
$E/wq/bin/python py/t16_nanobook.py 2>/dev/null | tail -1 > $R/t16_nanobook.json
