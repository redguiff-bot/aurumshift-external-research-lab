import sys, os, pickle, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import alpha_lib as L, primitives as X
RES = os.path.join(L.ROOT, "results")
IDX = L.IDX

def load_panel():
    P = pickle.load(open(os.path.join(L.CACHE, "panel.pkl"), "rb"))
    dv = {}
    for a in ["BTC", "ETH"]:
        d = pd.read_csv(os.path.join(L.CACHE, "xv", f"dvol_{a}.csv"))
        d.index = pd.to_datetime(d.ts + 3600_000, unit="ms", utc=True)   # candle usable 1h after its start (close known)
        dv[a] = d.c[~d.index.duplicated()].reindex(IDX).ffill(limit=6)
    P["dvol"] = pd.DataFrame(dv)
    return P

def sub_panel(P, cols):
    Q = {}
    for k, v in P.items():
        Q[k] = v[[c for c in cols if c in v.columns]] if isinstance(v, pd.DataFrame) else v
    return Q

def weights(name, P, **over):
    spec = X.PRIMS[name]; pr = dict(spec["params"]); pr.update(over)
    return spec["fn"](P, **pr)

def bt(name, P, W=None, **kw):
    if W is None: W = weights(name, P)
    kw.setdefault("carry", name == "P07_BASIS_CARRY")
    return L.backtest(W, P, **kw)

def ew_market(P):
    return P["ret"].fillna(0).mean(axis=1)

def baseline_ew_long(P):
    W = pd.DataFrame(1.0 / len(L.SYMS), index=IDX, columns=L.SYMS)
    return L.backtest(W, P)

def vol_regime(P):
    lr = P["lret"]["BTC"]; rv = lr.rolling(168, min_periods=168).std()
    pct = rv.rolling(2160, min_periods=720).rank(pct=True)
    return pd.cut(pct, [-0.01, 1 / 3, 2 / 3, 1.01], labels=["low", "mid", "high"])

def trend_regime(P):
    r30 = np.log(P["c"]["BTC"]).diff(720)
    return pd.Series(np.where(r30.isna(), None, np.where(r30 > 0, "bull", "bear")), index=IDX)

def fund_regime(P):
    m = P["f8"].mean(axis=1)
    pct = m.rolling(2160, min_periods=720).rank(pct=True)
    return pd.cut(pct, [-0.01, 1 / 3, 2 / 3, 1.01], labels=["cold", "neutral", "hot"])

REGIMES = {"vol": vol_regime, "trend": trend_regime, "funding_heat": fund_regime}

def jd(o, fn):
    def conv(x):
        if isinstance(x, (np.floating,)): return None if np.isnan(x) else float(x)
        if isinstance(x, (np.integer,)): return int(x)
        if isinstance(x, (np.bool_,)): return bool(x)
        if isinstance(x, (pd.Timestamp,)): return str(x)
        raise TypeError(str(type(x)))
    json.dump(o, open(os.path.join(RES, fn), "w"), indent=1, default=conv)
