#!/usr/bin/env bash
# venvs: see ENVIRONMENT.md. Usage: EBASE=/tmp/e bash run_t03.sh
E=${EBASE:-/tmp/e}; cd "$(dirname "$0")"
for e in "vbt vectorbt" "vbt vectorbt_next_open" "bktpy backtesting_next_open" "bktpy backtesting_trade_on_close" "core bt" "core backtrader"; do set -- $e
  $E/$1/bin/python py/t03_engine_reconcile.py $2 2>/dev/null | tail -1 > results/t03_$2.json; done
$E/zipline/bin/python py/t03z_zipline.py 2>/dev/null | tail -1 > results/t03_zipline.json
