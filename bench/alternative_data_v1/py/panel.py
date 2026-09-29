"""Build daily decision-time panels. Decision time for row d is d 00:00 UTC. Every feature uses only information whose
(declared or conservative) availability time is <= that instant. `lag` = whole days between decision day and the newest
usable observation date (lag=1 -> value dated d-1 is usable; lag=2 -> value dated d-2 ...)."""
import os, numpy as np, pandas as pd
D = os.path.join(os.path.dirname(__file__), "..", "data")
NO_CAL = os.environ.get("ALT_NO_CALENDAR") == "1"   # first-pass baseline WITHOUT weekday dummies / lr60 (kept for transparency)

def rd(name, **kw):
    return pd.read_csv(os.path.join(D, name), **kw)

def price(sym):
    k = rd(f"klines_1d_{sym}.csv", index_col=0, parse_dates=True)
    k = k[k.index < k.index.max()] if k.index.max() >= pd.Timestamp.utcnow().tz_localize(None).normalize() else k
    return k

def um_daily(sym):
    """Daily aggregates of Binance Vision 5-minute 'metrics' rows (cached in data/um_metrics_daily_<sym>.csv; the 5-min gz is regenerable via collect.py)."""
    fn = os.path.join(D, f"um_metrics_daily_{sym}.csv")
    if os.path.exists(fn): return pd.read_csv(fn, index_col=0, parse_dates=True)
    m = pd.read_csv(os.path.join(D, f"um_metrics_5m_{sym}.csv.gz"), parse_dates=["create_time"])
    m = m.drop_duplicates("create_time").set_index("create_time")
    g = m.groupby(m.index.normalize())
    out = pd.DataFrame({
        "oi": g.sum_open_interest.last(), "oi_val": g.sum_open_interest_value.last(),
        "lsr_top_cnt": g.count_toptrader_long_short_ratio.mean(), "lsr_top_pos": g.sum_toptrader_long_short_ratio.mean(),
        "lsr_all": g.count_long_short_ratio.mean(), "taker_ratio": g.sum_taker_long_short_vol_ratio.mean()})
    out.to_csv(fn); return out

def funding_daily(sym):
    f = rd(f"funding_8h_{sym}.csv", parse_dates=["ts"]).set_index("ts")
    g = f.groupby(f.index.normalize()).last_funding_rate
    return pd.DataFrame({"fund": g.mean(), "fund_last": g.last()})

def baseline(sym):
    """Features known at decision time d 00:00 (all through day d-1) + targets on day d."""
    k = price(sym); u = um_daily(sym); f = funding_daily(sym)
    df = k[["o", "h", "l", "c", "qvol", "ntrades", "tbqv"]].copy()
    df = df.join(u).join(f)
    r = np.log(df.c / df.c.shift(1)); lr = np.log(df.h / df.l)
    lv = np.log(df.qvol); lnt = np.log(df.ntrades)
    lo = np.log(df.oi)
    x = pd.DataFrame(index=df.index)
    x["r1"] = r; x["r5"] = r.rolling(5).mean(); x["r20"] = r.rolling(20).mean()
    x["lr1"] = np.log(lr); x["lr5"] = np.log(lr).rolling(5).mean(); x["lr20"] = np.log(lr).rolling(20).mean()
    if not NO_CAL: x["lr60"] = np.log(lr).rolling(60).mean()
    x["lv_z"] = lv - lv.rolling(30).mean(); x["lnt_z"] = lnt - lnt.rolling(30).mean()
    x["tbr"] = df.tbqv / df.qvol - 0.5
    x["fund"] = df.fund; x["dfund"] = df.fund - df.fund.rolling(7).mean()
    x["doi1"] = lo.diff(); x["doi5"] = lo.diff(5); x["oi_z"] = lo - lo.rolling(30).mean()
    # shift: value for day d-1 available at decision d
    xb = x.shift(1)
    for i in ([] if NO_CAL else range(1, 7)): xb[f"dow{i}"] = (xb.index.dayofweek == i).astype(float)   # calendar effect of the TARGET day d (known ex ante)
    tg = pd.DataFrame({"ret": r, "lrange": np.log(lr), "absret": r.abs()}, index=df.index)
    price_only = ["r1", "r5", "r20", "lr1", "lr5", "lr20"]
    raw = pd.DataFrame({"r": r, "lr": np.log(lr), "absr": r.abs()}, index=df.index)
    return xb, tg, price_only, raw, df

def lagged(s, lag):
    """series indexed by observation date -> value usable at decision date d (obs date <= d-lag)."""
    s = s.copy(); s.index = pd.to_datetime(s.index).normalize()
    s = s.reindex(pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=lag + 10)))
    return s.ffill(limit=10).shift(lag)

def zs(s, n=30):
    return (s - s.rolling(n).mean()) / s.rolling(n).std()

def block(name, s, lag, kind="log"):
    """two-feature block: trailing z-score of level + 1d change (both computed on obs-date series then lagged)."""
    s = s.copy(); s.index = pd.to_datetime(s.index).normalize()
    s = s[~s.index.duplicated()].sort_index().asfreq("D").ffill(limit=5)
    v = np.log(s.clip(lower=1e-9)) if kind == "log" else s
    b = pd.DataFrame({f"{name}_z": zs(v), f"{name}_d1": v.diff()})
    return b
