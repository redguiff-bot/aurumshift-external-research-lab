"""Isolated install footprint per candidate: fresh uv venv (py3.11, warm uv cache), install only that package, count distributions + site-packages MB + import time."""
import subprocess, json, os, time, shutil, sys
from concurrent.futures import ThreadPoolExecutor
PK = [("hftbacktest","hftbacktest","hftbacktest"),("nautilus_trader","nautilus_trader","nautilus_trader"),("ccxt","ccxt","ccxt"),("cryptofeed","cryptofeed","cryptofeed"),
 ("backtesting.py","backtesting","backtesting"),("vectorbt","vectorbt","vectorbt"),("backtrader","backtrader","backtrader"),("bt","bt","bt"),("zipline-reloaded","zipline-reloaded","zipline"),
 ("cvxportfolio","cvxportfolio","cvxportfolio"),("PyPortfolioOpt","pyportfolioopt","pypfopt"),("Riskfolio-Lib","riskfolio-lib","riskfolio"),("skfolio","skfolio","skfolio"),
 ("river","river","river"),("talipp","talipp","talipp"),("ta","ta","ta"),("TA-Lib","TA-Lib","talib"),("ddsketch","ddsketch","ddsketch"),("tdigest","tdigest","tdigest"),("hdrhistogram","hdrhistogram","hdrh"),
 ("exchange_calendars","exchange-calendars","exchange_calendars"),("pandas_market_calendars","pandas-market-calendars","pandas_market_calendars"),
 ("pandera","pandera","pandera"),("great_expectations","great-expectations","great_expectations"),("frictionless-py","frictionless","frictionless"),("pointblank","pointblank","pointblank"),
 ("DuckDB","duckdb","duckdb"),("ArcticDB","arcticdb","arcticdb"),("pyarrow","pyarrow","pyarrow"),("polars","polars","polars"),("tardis-python","tardis-dev","tardis_dev"),("quantstats","quantstats","quantstats"),("empyrical-reloaded","empyrical-reloaded","empyrical")]
def one(t):
    name, pkg, mod = t; d = f"/tmp/fp/{name.replace('/','_')}"
    shutil.rmtree(d, ignore_errors=True)
    env = {**os.environ, "VIRTUAL_ENV": d}
    subprocess.run(["uv", "venv", "-q", d, "--python", "3.11"], check=True)
    t0 = time.perf_counter(); r = subprocess.run(["uv", "pip", "install", "-q", pkg], env=env, capture_output=True, text=True); dt = time.perf_counter() - t0
    if r.returncode: return {"name": name, "error": r.stderr[-200:]}
    lst = subprocess.run(["uv", "pip", "list", "--format", "json"], env=env, capture_output=True, text=True).stdout
    n = len(json.loads(lst)); sp = subprocess.run(f"du -sm {d}/lib/python3.11/site-packages | cut -f1", shell=True, capture_output=True, text=True).stdout.strip()
    t1 = time.perf_counter(); ri = subprocess.run([f"{d}/bin/python", "-c", f"import {mod}"], capture_output=True, text=True); it = time.perf_counter() - t1
    return {"name": name, "pkg": pkg, "n_distributions_installed": n, "site_packages_MB": int(sp), "install_seconds_warm_cache": round(dt, 1), "import_seconds": round(it, 2), "import_ok": ri.returncode == 0, "import_err": ri.stderr.strip().splitlines()[-1][:120] if ri.returncode else ""}
with ThreadPoolExecutor(4) as ex: res = list(ex.map(one, PK))
json.dump(res, open("../results/footprint.json", "w"), indent=1)
for r in res: print(r)
