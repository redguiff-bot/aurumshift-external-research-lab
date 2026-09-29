#!/usr/bin/env bash
# Recreates the isolated virtualenvs used by the microtests (uv required). EBASE defaults to /tmp/e.
set -euo pipefail; E=${EBASE:-/tmp/e}; mkdir -p "$E"
mk(){ n=$1; py=$2; shift 2; uv venv -q --python "$py" "$E/$n"; uv pip install -q --python "$E/$n/bin/python" "$@"; }
mk core 3.12 hftbacktest river exchange_calendars pandas_market_calendars pandera duckdb polars pyarrow sortedcontainers riskfolio-lib PyPortfolioOpt skfolio empyrical-reloaded ta backtrader bt ccxt numba pandas numpy pytest psutil
mk nautilus 3.12 nautilus_trader pandas
mk vbt 3.12 vectorbt
mk zipline 3.12 zipline-reloaded
mk gx 3.12 great_expectations pandas
mk arctic 3.12 arcticdb pandas
mk bktpy 3.12 backtesting
mk misc 3.12 quantstats pandas-ta arch tsfresh frictionless pointblank cryptofeed yfinance
mk dbn 3.12 databento pandas
mk wq 3.12 nanobook numpy
mk wq13 3.13 wraquant polars            # wraquant needs >=3.13 and does not declare polars (OBSERVED)
# ABIDES-JPM: python 3.9 + pinned legacy stack
uv venv -q --python 3.9 "$E/abides"
git clone -q --depth 1 https://github.com/jpmorganchase/abides-jpmc-public "$E/abides_src"
uv pip install -q --python "$E/abides/bin/python" "$E/abides_src/abides-core" "$E/abides_src/abides-markets"
uv pip install -q --python "$E/abides/bin/python" numpy==1.22.0 pandas==1.2.4 psutil scipy tqdm coloredlogs pomegranate==0.14.5
