"""Causal primitive set. Every feature at row t uses only bars whose close_time <= close of bar t.
Target y_t = log(c[t+H]/c[t]) / (sigma24_t*sqrt(H)); NOT a feature. All primitives are causally rolling z-scored
(window W, shifted so the z-score at t uses stats from bars <= t) => unit: dimensionless z-score."""
import numpy as np, pandas as pd

H = 4          # forward horizon (bars) for the target
W = 500        # rolling z-score window
PRIMS = {  # name: (description, units_raw, expected sign hint (None = no prior))
 "r1":   ("1h log return", "log-price", None),
 "r4":   ("4h log return", "log-price", None),
 "r12":  ("12h log return", "log-price", None),
 "r24":  ("24h log return", "log-price", None),
 "r72":  ("72h log return", "log-price", None),
 "vol24":("std of 1h returns, 24h", "log-price", None),
 "vol72":("std of 1h returns, 72h", "log-price", None),
 "rng1": ("(high-low)/close, 1h", "ratio", None),
 "rng24":("mean rng1, 24h", "ratio", None),
 "vlm":  ("log volume minus 72h mean log volume", "log-units", None),
 "qvlm": ("log quote-volume minus 72h mean", "log-USDT", None),
 "trd":  ("log trade-count minus 72h mean", "log-count", None),
 "tb1":  ("taker-buy base share, 1h", "share", None),
 "tb24": ("taker-buy base share, 24h vol-weighted", "share", None),
 "clp":  ("close location in bar (c-l)/(h-l)", "share", None),
 "dh24": ("close vs 24h high, log", "log-price", None),
 "dl24": ("close vs 24h low, log", "log-price", None),
 "ma24": ("close/MA24 - 1", "ratio", None),
 "ma72": ("close/MA72 - 1", "ratio", None),
 "amh":  ("|r1|/quote volume (Amihud-like), log", "log-illiq", None),
}

def _z(s, w=W):
    m = s.rolling(w, min_periods=w // 2).mean(); v = s.rolling(w, min_periods=w // 2).std()
    return (s - m) / v.replace(0, np.nan)

def primitives_raw(df):
    c, h, l = df.close, df.high, df.low
    lr = np.log(c).diff()
    o = pd.DataFrame(index=df.index)
    for n in (1, 4, 12, 24, 72):
        o[f"r{n}"] = np.log(c).diff(n)
    o["vol24"] = lr.rolling(24).std(); o["vol72"] = lr.rolling(72).std()
    rng = (h - l) / c
    o["rng1"] = rng; o["rng24"] = rng.rolling(24).mean()
    lv = np.log(df.volume + 1e-9); o["vlm"] = lv - lv.rolling(72).mean()
    lq = np.log(df.quote_vol + 1e-9); o["qvlm"] = lq - lq.rolling(72).mean()
    lt = np.log(df.trades + 1.0); o["trd"] = lt - lt.rolling(72).mean()
    o["tb1"] = df.taker_base / df.volume.replace(0, np.nan)
    o["tb24"] = df.taker_base.rolling(24).sum() / df.volume.rolling(24).sum().replace(0, np.nan)
    o["clp"] = (c - l) / (h - l).replace(0, np.nan)
    o["dh24"] = np.log(c / h.rolling(24).max()); o["dl24"] = np.log(c / l.rolling(24).min())
    o["ma24"] = c / c.rolling(24).mean() - 1; o["ma72"] = c / c.rolling(72).mean() - 1
    o["amh"] = np.log(lr.abs() / df.quote_vol.replace(0, np.nan) + 1e-12)
    return o

def build(df):
    """returns X (z-scored primitives, causal), y (vol-scaled forward return), meta"""
    raw = primitives_raw(df)
    X = raw.apply(_z).clip(-6, 6)
    c = df.close
    sig = np.log(c).diff().rolling(24).std()
    fwd = np.log(c.shift(-H) / c)
    y = fwd / (sig * np.sqrt(H))
    y = y.clip(-6, 6)
    X["_t"] = df.open_time.values
    X["y"] = y.values
    X["fwd_raw"] = fwd.values
    return X.dropna().reset_index(drop=True)
