"""Shared clean 1-minute bar frame + 12 single-defect variants (defects taken from report-005 hazards)."""
import numpy as np, pandas as pd
N = 200_000; T0 = int(pd.Timestamp("2025-03-01", tz="UTC").timestamp()*1000)
def clean():
    rng = np.random.default_rng(11); r = rng.normal(0, 4e-4, N); c = 60000*np.exp(np.cumsum(r)); o = np.r_[60000.0, c[:-1]]
    h = np.maximum(o, c)*(1+np.abs(rng.normal(0, 1e-4, N))); l = np.minimum(o, c)*(1-np.abs(rng.normal(0, 1e-4, N)))
    return pd.DataFrame(dict(ts=T0 + np.arange(N)*60_000, open=o, high=h, low=l, close=c, volume=rng.uniform(0.1, 20, N)))
def variants():
    b = clean(); out = {"clean": b}
    def v(name, f): d = b.copy(); f(d); out[name] = d
    def dup(d): d.loc[5000, "ts"] = d.loc[4999, "ts"]
    v("duplicate_ts",      dup)
    def nonmono(d): d.loc[7000, "ts"] += 200_000
    v("non_monotonic",     nonmono)
    v("high_lt_low",       lambda d: d.__setitem__("high", d.high.where(d.index != 9000, d.low - 1)))
    v("close_gt_high",     lambda d: d.__setitem__("close", d.close.where(d.index != 9500, d.high + 50)))
    v("negative_volume",   lambda d: d.__setitem__("volume", d.volume.where(d.index != 10000, -1.0)))
    v("null_close",        lambda d: d.__setitem__("close", d.close.where(d.index != 11000, np.nan)))
    v("ts_unit_switch_us", lambda d: d.__setitem__("ts", d.ts.where(d.index < 150_000, d.ts*1000)))
    d = b.drop(index=range(20000, 20010)).reset_index(drop=True); out["missing_minutes"] = d
    def flat(d):
        i = slice(30000, 30060); p = d.close.iloc[30000]
        for c in ("open", "high", "low", "close"): d.loc[i, c] = p
        d.loc[i, "volume"] = 0.0
    v("flat_zero_volume_run", flat)
    v("price_spike_x10",   lambda d: d.__setitem__("close", d.close.where(d.index != 40000, d.close*10)))
    v("future_timestamp",  lambda d: d.__setitem__("ts", d.ts.where(d.index != N-1, int(pd.Timestamp("2035-01-01", tz="UTC").timestamp()*1000))))
    def stale(d):
        for c in ("open", "high", "low", "close", "volume"): d.loc[50000:50029, c] = d.loc[50000, c]
    v("stale_repeated_bar", stale)
    return out
ASOF_MS = int(pd.Timestamp("2025-09-29", tz="UTC").timestamp()*1000)
DEFECTS = ["duplicate_ts","non_monotonic","high_lt_low","close_gt_high","negative_volume","null_close","ts_unit_switch_us","missing_minutes","flat_zero_volume_run","price_spike_x10","future_timestamp","stale_repeated_bar"]
