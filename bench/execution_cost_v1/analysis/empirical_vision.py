"""Binance Vision (public dumps) — historical calibration/reference ONLY (not live execution evidence)."""
import glob, zipfile, json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.join(os.path.dirname(__file__), ".."); D = f"{ROOT}/data/vision"; R = f"{ROOT}/results"
sys.path.insert(0, f"{ROOT}/models"); import models as M
out = {}

def load_agg(sym):
    dfs = []
    for f in sorted(glob.glob(f"{D}/aggTrades_{sym}_*.zip")):
        z = zipfile.ZipFile(f)
        df = pd.read_csv(z.open(z.namelist()[0]), header=None, names=["id", "px", "qty", "f", "l", "ts", "bm", "bestm"])
        df["day"] = os.path.basename(f).split("_")[-1][:10]
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    # timestamps: microseconds since 2025 for spot; sanity-check
    df["t"] = df.ts / (1e6 if df.ts.iloc[0] > 1e15 else 1e3)
    df["side"] = np.where(df.bm, -1, 1)                    # isBuyerMaker=True => seller was aggressor
    df["usd"] = df.px * df.qty
    return df

for sym in ["BTCUSDT", "ETHUSDT"]:
    df = load_agg(sym); o = {}
    o["days"] = sorted(df.day.unique().tolist()); o["n_aggtrades"] = int(len(df))
    o["V_day_usd"] = df.groupby("day").usd.sum().to_dict()
    px = df.px.values
    dp = np.abs(np.diff(px)); o["tick_bps"] = float(dp[dp > 0].min() / np.median(px) * 1e4)
    # trade-based spread estimator: opposite-aggressor consecutive prints within 5 ms => price difference ~ spread
    t = df.t.values; s = df.side.values
    m = (np.diff(t) < 0.005) & (s[1:] != s[:-1])
    flip = (px[1:] - px[:-1]) * s[1:]                        # buy-aggr after sell-aggr: ask-bid > 0
    fb = flip[m] / np.median(px) * 1e4
    o["flip_spread_bps"] = dict(n=int(m.sum()), mean=float(fb.mean()), median=float(np.median(fb)), p75=float(np.percentile(fb, 75)), frac_zero=float(np.mean(fb <= 1e-9)))
    # mid-proxy (last trade) drift by horizon
    tt = df.t.values; pp = px
    drift = {}
    for h in (0.1, 0.5, 1, 2, 5, 10, 30, 60):
        j = np.searchsorted(tt, tt + h); ok = j < len(tt)
        sub = np.arange(0, len(tt), 7)[: 400000]; sub = sub[ok[sub]]
        d = (pp[j[sub]] / pp[sub] - 1) * 1e4
        # flow in previous 1s (signed usd) -> conditional next-h return
        j0 = np.searchsorted(tt, tt[sub] - 1.0)
        cs = np.concatenate([[0], np.cumsum((df.side * df.usd).values)])
        flow = cs[sub + 1] - cs[j0]
        big = np.abs(flow) > np.percentile(np.abs(flow), 75)
        cond = float(np.mean(d[big] * np.sign(flow[big])))
        drift[str(h)] = dict(sd_bps=float(d.std()), mean_bps=float(d.mean()), p99_abs=float(np.percentile(np.abs(d), 99)), momentum_after_top_quartile_flow_bps=cond,
                             sd_over_sqrt_h=float(d.std() / np.sqrt(h)))
    o["last_trade_drift_by_horizon_s"] = drift
    # impact: 1-min and 5-min bars: signed flow vs return
    for bar in (60, 300):
        b = (df.t // bar).astype(int)
        g = df.groupby(b).agg(o=("px", "first"), c=("px", "last"), usd=("usd", "sum"))
        g["q"] = df.assign(sq=df.side * df.usd).groupby(b).sq.sum(); g["r"] = (g.c / g.o - 1) * 1e4
        g["day"] = df.groupby(b).day.first()
        g = g.dropna()
        sig = g.r.std()
        lam = float(np.polyfit(g.q / 1e6, g.r, 1)[0]); r2 = float(np.corrcoef(g.q, g.r)[0, 1] ** 2)
        # exponent: bin by |q| deciles, log-log slope of mean |r| vs mean |q|
        qa = g.q.abs(); dec = pd.qcut(qa, 10, duplicates="drop")
        tab = g.groupby(dec, observed=True).apply(lambda x: pd.Series(dict(q=x.q.abs().mean(), r=(x.r * np.sign(x.q)).mean())))
        tab = tab[tab.r > 0]
        slope = float(np.polyfit(np.log(tab.q), np.log(tab.r), 1)[0]) if len(tab) > 4 else None
        # OOS: fit on first half of days, evaluate on last day: linear vs sqrt vs zero
        days = sorted(g.day.unique()); tr = g[g.day.isin(days[:-1])]; te = g[g.day == days[-1]]
        lam_tr = np.polyfit(tr.q / 1e6, tr.r, 1)[0]
        Vd = np.mean(list(o["V_day_usd"].values())); sg = tr.r.std()
        x = np.sign(tr.q) * np.sqrt(tr.q.abs() / Vd); Y = float(np.sum(x * tr.r) / np.sum(x * x))
        xt = np.sign(te.q) * np.sqrt(te.q.abs() / Vd)
        o[f"impact_{bar}s"] = dict(n_bars=int(len(g)), lambda_bps_per_musd=lam, r2=r2, loglog_slope_delta=slope, decile_table=[[float(a), float(b)] for a, b in tab.values],
                                   oos_days=days[-1], oos_rmse_zero=float(np.sqrt(np.mean(te.r ** 2))), oos_rmse_linear=float(np.sqrt(np.mean((te.r - lam_tr * te.q / 1e6) ** 2))),
                                   oos_rmse_sqrt=float(np.sqrt(np.mean((te.r - Y * xt) ** 2))), sqrt_Y_over_unit=float(Y), sd_bar_ret_bps=float(sig))
    out[sym] = o
# ---- OHLC proxies on 1m klines (Binance spot) vs trade-flip spread ----
for sym in ["BTCUSDT", "ETHUSDT"]:
    fs = sorted(glob.glob(f"{D}/klines_{sym}_1m_2026-0*.zip"))
    res = {}
    for f in fs:
        z = zipfile.ZipFile(f); k = pd.read_csv(z.open(z.namelist()[0]), header=None).iloc[:, :6]; k.columns = ["t", "O", "H", "L", "C", "V"]
        k["day"] = (k.t // (86400 * (1e6 if k.t.iloc[0] > 1e15 else 1e3))).astype(int)
        cs_l, ar_l, ro_l, hl_l = [], [], [], []
        for _, g in k.groupby("day"):
            if len(g) < 1000: continue
            cs, _ = M.corwin_schultz(g.H.values, g.L.values); cs_l.append(cs * 1e4); ar_l.append(M.abdi_ranaldo(g.C.values, g.H.values, g.L.values) * 1e4)
            ro_l.append(M.roll(g.C.values) / g.C.mean() * 1e4); hl_l.append(M.hl_range_proxy(g.H.values, g.L.values) * 1e4)
        res[os.path.basename(f)] = dict(days=len(cs_l), corwin_schultz_bps_mean=float(np.mean(cs_l)), abdi_ranaldo=float(np.mean(ar_l)), roll=float(np.mean(ro_l)), hl_range=float(np.mean(hl_l)))
    out[sym]["ohlc_1m_proxies_by_month_bps"] = res
# ---- bookDepth (USD-M perp) cumulative depth exponent ----
z = zipfile.ZipFile(f"{D}/bookDepth_um_BTCUSDT_2026-09-20.zip"); bd = pd.read_csv(z.open(z.namelist()[0]))
med = bd.groupby("percentage").notional.median().sort_index()
pos = med[med.index > 0]; xs = np.log(pos.index.values * 100); ys = np.log(pos.values)
out["bookDepth_um_BTCUSDT_2026-09-20"] = dict(median_cum_notional_by_pct=med.to_dict(), loglog_slope_beta_bps_20_to_500=float(np.polyfit(xs, ys, 1)[0]),
                                              note="bands are +-0.2,1,2,3,4,5 % of mid: far-book only; says nothing about top-of-book")
json.dump(out, open(f"{R}/empirical_vision.json", "w"), indent=1, default=str)
for s in ("BTCUSDT", "ETHUSDT"):
    o = out[s]; print(s, "tick_bps", round(o["tick_bps"], 5), "flip", o["flip_spread_bps"], "V_day", {k: round(v / 1e9, 2) for k, v in o["V_day_usd"].items()})
    print(" impact60", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in o["impact_60s"].items() if k != "decile_table"})
    print(" ohlc", o["ohlc_1m_proxies_by_month_bps"])
    print(" drift1s", o["last_trade_drift_by_horizon_s"]["1"], o["last_trade_drift_by_horizon_s"]["10"])
print(out["bookDepth_um_BTCUSDT_2026-09-20"]["loglog_slope_beta_bps_20_to_500"])
