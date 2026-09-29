import numpy as np, pandas as pd, hashlib, time, json, sys, os
def synth(n=5000, seed=7, start="2024-01-02 14:30", freq="1min"):
    rng = np.random.default_rng(seed)
    r = rng.normal(0, 4e-4, n)
    c = 100*np.exp(np.cumsum(r))
    o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 1e-4, n))
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 1e-4, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 1e-4, n)))
    v = rng.integers(100, 1000, n).astype(float)
    idx = pd.date_range(start, periods=n, freq=freq, tz="UTC")
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v}, index=idx)
def sig(df, f=20, s=50):
    """long when SMA(f) > SMA(s), computed on close at bar t (available after bar t closes)"""
    return (df.close.rolling(f).mean() > df.close.rolling(s).mean()).fillna(False)
def h(x): return hashlib.sha256(json.dumps(x, sort_keys=True, default=str).encode()).hexdigest()[:12]
def timed(fn, *a, **k):
    t = time.perf_counter(); r = fn(*a, **k); return r, round(time.perf_counter()-t, 4)
RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "results")
def save(name, obj): json.dump(obj, open(os.path.join(RESULTS, name), "w"), indent=1, default=str)
