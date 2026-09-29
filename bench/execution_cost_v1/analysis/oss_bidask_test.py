"""Run OSS `bidask` (EDGE estimator, Ardia-Guidotti-Kroencke) on synthetic OHLC with known spread and on Binance Vision 1m klines.
Run with the venv python that has bidask installed: /tmp/venvs/bidask/bin/python analysis/oss_bidask_test.py"""
import sys, os, json, glob, zipfile
import numpy as np, pandas as pd
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, f"{ROOT}/synthetic")
from synth import simulate_ohlc
import bidask
rows = []
for spread in [0.2, 1.0, 5.0, 20.0]:
    for sigma in [0.3, 0.9, 2.7]:
        for tick in [0.0, 1.0]:
            o = simulate_ohlc(spread, sigma, 250, 60, seed=int(spread * 100 + sigma * 10 + 60), tick_bps=tick)
            base = 1e5; px = lambda a: base * (1 + a / 1e4)
            df = pd.DataFrame(dict(open=px(o["O"]), high=px(o["H"]), low=px(o["L"]), close=px(o["C"])),
                              index=pd.date_range("2026-01-01", periods=250, freq="min"))
            try:
                e = float(bidask.edge(df.open.values, df.high.values, df.low.values, df.close.values)) * 1e4
            except Exception as ex:
                e = float("nan")
            rows.append(dict(spread=spread, sigma=sigma, tick=tick, eff_truth=o["eff_spread"], edge_bps=e))
syn = pd.DataFrame(rows)
real = {}
D = f"{ROOT}/data/vision"
for sym in ["BTCUSDT", "ETHUSDT"]:
    for f in sorted(glob.glob(f"{D}/klines_{sym}_1m_2026-0*.zip")):
        z = zipfile.ZipFile(f); k = pd.read_csv(z.open(z.namelist()[0]), header=None).iloc[:, :5]; k.columns = ["t", "open", "high", "low", "close"]
        k["t"] = pd.to_datetime(k.t // (1 if k.t.iloc[0] < 1e14 else 1000), unit="ms")   # ms or us
        k = k.set_index("t")
        vals = []
        for d, g in k.groupby(k.index.date):
            if len(g) > 1000:
                try: vals.append(float(bidask.edge(g.open.values, g.high.values, g.low.values, g.close.values)) * 1e4)
                except Exception: pass
        real[os.path.basename(f)] = dict(days=len(vals), edge_bps_mean=float(np.nanmean(vals)) if vals else None, nan_days=int(np.sum(np.isnan(vals))))
# ---- live trade-built 1-minute OHLC (OKX / Coinbase / Kraken) vs quoted spread from the same capture
sys.path.insert(0, f"{ROOT}/analysis"); sys.argv = [sys.argv[0]]
import empirical_live as EL
live = {}
lj = json.load(open(f"{ROOT}/results/empirical_live.json"))["per_venue_asset"]
qs = {(o["venue"], o["asset"]): o["spread_bps"]["mean"] for o in lj}
for venue, lst in EL.VENUES.items():
    for asset, bstem, tstem in lst:
        T = EL.load_trades(tstem, venue)
        if T is None or len(T) < 100: continue
        for bar in (60, 30):
            T["bar"] = (T.ts // bar).astype(int)
            g = T.groupby("bar").px.agg(["first", "max", "min", "last"]); g.columns = ["open", "high", "low", "close"]
            try: e = float(bidask.edge(g.open.values, g.high.values, g.low.values, g.close.values)) / 1.0 * 1e4
            except Exception: e = float("nan")
            live[f"{venue}-{asset}-{bar}s"] = dict(n_bars=int(len(g)), edge_bps=e, quoted_spread_mean_bps=qs.get((venue, asset)))
json.dump(dict(synthetic=syn.to_dict("records"), real_binance_klines=real, live_trade_bars=live, bidask_version=getattr(bidask, "__version__", "?")), open(f"{ROOT}/results/oss_bidask_edge.json", "w"), indent=1, default=float)
print(syn.groupby(["spread", "sigma"])[["eff_truth", "edge_bps"]].mean().round(2)); print(real)
