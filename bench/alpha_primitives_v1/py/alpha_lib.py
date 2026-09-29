"""alpha_primitives_v1 core library. External research only. Timeline convention:
panel index = bar OPEN time (UTC). A decision 'after bar i' uses only data of bars <= i (closed at open_i+1h)
and earns the return of bar i+1 (close_i -> close_{i+1}). Extra latency L delays the weights L more bars."""
import os, glob, json
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
SYMS = ["BTC", "ETH", "SOL", "XRP", "BNB", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
MAJORS = ["BTC", "ETH", "BNB", "SOL", "XRP"]
MINORS = ["DOGE", "ADA", "LINK", "AVAX", "LTC"]
IDX = pd.date_range("2024-01-01", "2026-08-31 23:00", freq="h", tz="UTC")
EVAL_START = pd.Timestamp("2024-03-01", tz="UTC")
SPLIT = pd.Timestamp("2025-06-01", tz="UTC")   # dev: [EVAL_START, SPLIT)  holdout: [SPLIT, end]
# generic per-side cost (bps of traded notional): taker fee 5 + slippage/half-spread. Tier by liquidity class.
COST_BPS = {"BTC": 6.0, "ETH": 6.0, **{s: 8.0 for s in ["SOL", "XRP", "BNB", "DOGE", "ADA", "LINK", "AVAX", "LTC"]}}
UNKNOWN_COST_BPS = 15.0  # UNKNOWN_COST != ZERO_COST: unmapped asset/venue gets a conservative charge

KCOLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "qv", "count", "tbv", "tbqv", "ign"]

def _read_kl(path):
    df = pd.read_csv(path, header=None, names=KCOLS, skiprows=1 if open(path).readline().startswith("open_time") else 0)
    t = df.open_time.astype("int64")
    t = np.where(t > 10**14, t // 1000, t)
    df.index = pd.to_datetime(t, unit="ms", utc=True)
    return df.drop(columns=["open_time", "close_time", "ign"]).astype(float)

def load_klines(kind, sym):
    fs = sorted(glob.glob(os.path.join(CACHE, kind, sym, "*.csv")))
    df = pd.concat([_read_kl(f) for f in fs]).sort_index()
    df = df[~df.index.duplicated()]
    return df.reindex(IDX)

def load_funding(sym):
    fs = sorted(glob.glob(os.path.join(CACHE, "um_fund", sym, "*.csv")))
    df = pd.concat([pd.read_csv(f) for f in fs]).sort_values("calc_time")
    df["ts"] = pd.to_datetime(df.calc_time, unit="ms", utc=True)
    return df

def load_metrics(sym):
    fs = sorted(glob.glob(os.path.join(CACHE, "um_metrics", sym, "*.csv")))
    df = pd.concat([pd.read_csv(f, usecols=["create_time", "sum_open_interest"]) for f in fs])
    df["create_time"] = pd.to_datetime(df.create_time, utc=True)
    return df.set_index("create_time").sort_index()

def build_panel():
    """Returns dict of DataFrames (index IDX, columns SYMS)."""
    P = {k: {} for k in ["c", "qv", "tbqv", "hi", "lo", "sc", "oi", "prem", "fund_bar", "f8"]}
    miss = {}
    for s in SYMS:
        k = load_klines("um_kl", s); sp = load_klines("spot_kl", s); pr = load_klines("um_prem", s)
        miss[s] = {"perp_missing_bars": int(k.close.isna().sum()), "spot_missing_bars": int(sp.close.isna().sum()),
                   "prem_missing_bars": int(pr.close.isna().sum())}
        P["c"][s] = k.close; P["qv"][s] = k.qv; P["tbqv"][s] = k.tbqv; P["hi"][s] = k.high; P["lo"][s] = k.low
        P["sc"][s] = sp.close; P["prem"][s] = pr.close
        # OI: last 5m snapshot stamped <= bar_close - 5min (receipt-stamp conservative), then per hour
        m = load_metrics(s).sum_open_interest
        m.index = m.index + pd.Timedelta(minutes=5)   # available 5 min after stamp
        hourly = m.resample("1h", label="left", closed="left").last()   # last value known within [t, t+1h)
        P["oi"][s] = hourly.reindex(IDX)
        f = load_funding(s)
        f["f8"] = f.last_funding_rate * 8.0 / f.funding_interval_hours
        bar = f.ts.dt.floor("h")
        fb = f.groupby(bar).last_funding_rate.sum().reindex(IDX).fillna(0.0)  # cash rate settled during bar i
        P["fund_bar"][s] = fb
        # feature: mean of last 3 normalised settlements known at bar close (calc_time <= close)
        f["avail"] = f.ts.dt.floor("h")   # settlement happens in bar `avail`; known once that bar closed
        # mean of last 3 distinct settlements: use event series
        ev = f.set_index("avail").f8
        ev = ev[~ev.index.duplicated(keep="last")]
        m3 = ev.rolling(3, min_periods=3).mean()
        P["f8"][s] = m3.reindex(IDX).ffill()
    out = {k: pd.DataFrame(v)[SYMS] for k, v in P.items()}
    for k in ["oi", "qv", "tbqv"]:
        out[k] = out[k].where(out[k] > 0)
    out["ret"] = out["c"].pct_change(fill_method=None)
    out["lret"] = np.log(out["c"]).diff()
    out["sret"] = out["sc"].pct_change(fill_method=None)
    out["missing"] = miss
    return out

# ---------- generic feature helpers (all trailing / causal) ----------
def vol_est(lret, w=168):
    return lret.rolling(w, min_periods=w // 2).std()

def zscore(x, w=720, minp=240):
    m = x.rolling(w, min_periods=minp).mean(); s = x.rolling(w, min_periods=minp).std()
    return (x - m) / s.replace(0, np.nan)

def hold_every(w, R, offset=0):
    """re-estimate weights only every R bars; hold in between (position persistence)."""
    if R <= 1: return w
    mask = (np.arange(len(w)) % R) == offset
    return w.where(pd.Series(mask, index=w.index), np.nan).ffill()

def rank_neutral(s):
    r = s.rank(axis=1)
    d = r.sub(r.mean(axis=1), axis=0)
    g = d.abs().sum(axis=1).replace(0, np.nan)
    return d.div(g, axis=0)

def dir_weights(s):
    n = s.notna().sum(axis=1).replace(0, np.nan)
    return s.clip(-1, 1).div(n, axis=0)

# ---------- backtest ----------
def backtest(W, P, lag=0, cost_mult=1.0, funding=True, ret_key="ret", cost_map=None, assets=None, carry=False, spot_extra_bps=5.0):
    """W: weights decided after bar i (index IDX). Earns ret[i+1+lag].
    carry=True: W is capital weight of a delta-neutral pair (long spot, short perp); pays both legs' costs (spot fee +spot_extra_bps).
    Returns hourly pnl parts as fraction of gross capital."""
    cols = assets or list(W.columns)
    W = W[cols].reindex(IDX).fillna(0.0)
    Wd = W.shift(1 + lag).fillna(0.0)          # weight held during bar i
    cm = cost_map or COST_BPS
    cb = pd.Series({c: cm.get(c, UNKNOWN_COST_BPS) for c in cols})
    turn = Wd.diff().abs().fillna(0.0)
    if carry:
        price = (Wd * (P["sret"][cols].fillna(0.0) - P["ret"][cols].fillna(0.0))).sum(axis=1)
        fund = (Wd * P["fund_bar"][cols]).sum(axis=1) if funding else price * 0.0   # short perp receives positive funding
        cost = (turn * (2 * cb + spot_extra_bps) / 1e4).sum(axis=1) * cost_mult
        gexp = 2 * Wd.abs().sum(axis=1)
    else:
        R = P[ret_key][cols].fillna(0.0)
        price = (Wd * R).sum(axis=1)
        fund = -(Wd * P["fund_bar"][cols]).sum(axis=1) if funding else price * 0.0
        cost = (turn * cb / 1e4).sum(axis=1) * cost_mult
        gexp = Wd.abs().sum(axis=1)
    return pd.DataFrame({"price": price, "funding": fund, "cost": cost, "gross": price + fund, "net": price + fund - cost,
                         "turn": turn.sum(axis=1), "gross_exp": gexp})

def daily(x):
    return x.resample("1D").sum()

def sharpe(d):
    d = d.dropna()
    if len(d) < 20 or d.std() == 0: return np.nan
    return d.mean() / d.std() * np.sqrt(365)

def max_dd(d):
    c = d.cumsum(); return float((c - c.cummax()).min())

def sbootstrap(d, n=2000, block=7, seed=0):
    """stationary bootstrap on daily returns; returns array of Sharpe replicates of the ORIGINAL-mean sample and centered-null p-value."""
    rng = np.random.default_rng(seed); x = d.dropna().values; T = len(x)
    if T < 30: return None
    p = 1.0 / block; out = np.empty(n)
    for b in range(n):
        idx = np.empty(T, dtype=int); idx[0] = rng.integers(T)
        u = rng.random(T); nw = rng.integers(T, size=T)
        for t in range(1, T):
            idx[t] = nw[t] if u[t] < p else (idx[t - 1] + 1) % T
        y = x[idx]; out[b] = y.mean() / (y.std() + 1e-18) * np.sqrt(365)
    obs = x.mean() / (x.std() + 1e-18) * np.sqrt(365)
    pval = float((out - obs >= obs).mean())   # one-sided: P(boot Sharpe centered >= observed)
    return {"lo5": float(np.percentile(out, 5)), "hi95": float(np.percentile(out, 95)), "p_one_sided": pval, "obs": float(obs)}

def summarize(bt, start=EVAL_START, end=None, boot=False):
    b = bt.loc[start:end] if end is not None else bt.loc[start:]
    dl = b[["price", "funding", "cost", "gross", "net"]].resample("1D").sum()
    yrs = len(dl) / 365.0
    res = {"days": len(dl), "gross_ann": float(dl.gross.sum() / yrs), "net_ann": float(dl.net.sum() / yrs),
           "price_ann": float(dl.price.sum() / yrs), "funding_ann": float(dl.funding.sum() / yrs), "cost_ann": float(dl.cost.sum() / yrs),
           "gross_sharpe": float(sharpe(dl.gross)), "net_sharpe": float(sharpe(dl.net)),
           "turn_ann": float(b.turn.sum() / yrs), "avg_gross_exp": float(b.gross_exp.mean()),
           "maxdd_net": max_dd(dl.net), "hit_net_day": float((dl.net > 0).mean())}
    if boot:
        bs = sbootstrap(dl.net); res["boot"] = bs
    return res
