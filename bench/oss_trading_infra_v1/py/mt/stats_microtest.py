"""Online statistics + streaming indicators vs exact batch oracles, on the same synthetic 1-min series."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, json, time, tracemalloc
from common import *
df = synth(200_000, seed=11); c = df.close.values; r = np.diff(np.log(c))
res = {}
# ---- online mean/var (river) vs numpy
from river import stats as rs
t0 = time.perf_counter(); m = rs.Mean(); v = rs.Var()
for x in r: m.update(x); v.update(x)
dt = time.perf_counter() - t0
res["river_mean_var"] = {"n": len(r), "abs_err_mean": float(abs(m.get() - r.mean())), "abs_err_var_rel": float(abs(v.get() - r.var(ddof=1)) / r.var(ddof=1)), "us_per_update": round(dt / len(r) * 1e6, 2)}
# rolling window & EWM
rm = rs.RollingMean = None
from river import utils
rmean = utils.Rolling(rs.Mean(), window_size=100); out = []
for x in r: rmean.update(x); out.append(rmean.get())
ref = pd.Series(r).rolling(100).mean().values
res["river_rolling_mean_w100_maxabs_err_after_warmup"] = float(np.nanmax(np.abs(np.array(out)[99:] - ref[99:])))
ew = rs.EWMean(fading_factor=0.05); oe = []
for x in r: ew.update(x); oe.append(ew.get())
ref_e = pd.Series(r).ewm(alpha=0.05, adjust=False).mean().values
res["river_ewmean_vs_pandas_adjust_False_maxabs"] = float(np.max(np.abs(np.array(oe) - ref_e)))
# quantile streaming
qs = {"river_P2_quantile": rs.Quantile(0.99)}
for x in r: qs["river_P2_quantile"].update(x)
exact = {q: float(np.quantile(r, q)) for q in (0.5, 0.99)}
res["quantile_p99_exact"] = exact[0.99]
res["river_P2_p99"] = {"est": qs["river_P2_quantile"].get(), "rel_err": abs(qs["river_P2_quantile"].get() - exact[0.99]) / abs(exact[0.99])}
# t-digest & ddsketch & hdr
from tdigest import TDigest
td = TDigest(); t0 = time.perf_counter()
for x in r[:50_000]: td.update(x)
res["tdigest_p99_50k"] = {"est": td.percentile(99), "exact": float(np.percentile(r[:50_000], 99)), "sec": round(time.perf_counter() - t0, 2)}
from ddsketch import DDSketch
dd = DDSketch(relative_accuracy=0.01); a = np.abs(r) + 1e-12
for x in a: dd.add(x)
ex = float(np.quantile(a, 0.99)); es = dd.get_quantile_value(0.99)
res["ddsketch_abs_ret_p99"] = {"est": es, "exact": ex, "rel_err": abs(es - ex) / ex, "claimed_rel_accuracy": 0.01}
d1, d2 = DDSketch(0.01), DDSketch(0.01)
for x in a[:100000]: d1.add(x)
for x in a[100000:]: d2.add(x)
d1.merge(d2); res["ddsketch_merge_p99_rel_err_vs_exact"] = abs(d1.get_quantile_value(0.99) - ex) / ex
try:
    from hdrh.histogram import HdrHistogram
    hh = HdrHistogram(1, 10**9, 3)
    ints = (a * 1e8).astype(int) + 1
    for x in ints: hh.record_value(int(x))
    res["hdrhistogram_p99_rel_err"] = abs(hh.get_value_at_percentile(99) - float(np.quantile(ints, .99))) / float(np.quantile(ints, .99))
except Exception as e: res["hdrhistogram"] = f"error {type(e).__name__}: {e}"
# determinism of streaming
def run_once():
    q = rs.Quantile(0.5); 
    for x in r[:20000]: q.update(x)
    return q.get()
res["river_deterministic"] = run_once() == run_once()
# ---- streaming indicators (talipp) vs batch (ta) vs numpy oracles: EMA, RSI, ATR-ish
import talipp.indicators as ti
from talipp.ohlcv import OHLCVFactory
import ta as tapkg
n = 20_000; sub = df.iloc[:n]; cl = sub.close.values
t0 = time.perf_counter(); ema = ti.EMA(20)
for x in cl: ema.add(float(x))
res["talipp_ema20_stream_sec_20k"] = round(time.perf_counter() - t0, 2)
ref = tapkg.trend.EMAIndicator(sub.close, 20).ema_indicator().values
tv = np.array([np.nan if v is None else v for v in ema.output_values] if hasattr(ema, "output_values") else [np.nan if v is None else v for v in ema], dtype=float)
ok = ~np.isnan(tv) & ~np.isnan(ref)
res["ema20_talipp_vs_ta"] = {"n_compared": int(ok.sum()), "maxabs": float(np.max(np.abs(tv[ok] - ref[ok])))}
pd_ewm = sub.close.ewm(span=20, adjust=False).mean().values
res["ema20_ta_vs_pandas_ewm_adjustFalse_maxabs_after_100"] = float(np.nanmax(np.abs(ref[100:] - pd_ewm[100:])))
res["ema20_talipp_vs_pandas_ewm_adjustFalse_maxabs_after_100"] = float(np.nanmax(np.abs(tv[100:] - pd_ewm[100:])))
rsi_t = ti.RSI(14)
for x in cl: rsi_t.add(float(x))
tv2 = np.array([np.nan if v is None else v for v in rsi_t], dtype=float)
ref2 = tapkg.momentum.RSIIndicator(sub.close, 14).rsi().values
ok = ~np.isnan(tv2) & ~np.isnan(ref2)
res["rsi14_talipp_vs_ta"] = {"n_compared": int(ok.sum()), "maxabs_after_200": float(np.max(np.abs(tv2[ok][200:] - ref2[ok][200:])))}
# ATR: talipp vs ta
ohlcv = [__import__("talipp.ohlcv", fromlist=["OHLCV"]).OHLCV(float(o), float(h), float(l), float(cc), float(vv)) for o, h, l, cc, vv in zip(sub.open, sub.high, sub.low, sub.close, sub.volume)]
atr_t = ti.ATR(14, input_values=ohlcv)
tv3 = np.array([np.nan if v is None else v for v in atr_t], dtype=float)
ref3 = tapkg.volatility.AverageTrueRange(sub.high, sub.low, sub.close, 14).average_true_range().values
ok = ~np.isnan(tv3) & ~np.isnan(ref3)
res["atr14_talipp_vs_ta"] = {"n_compared": int(ok.sum()), "maxabs_after_200": float(np.max(np.abs(tv3[ok][-n+400:] - ref3[ok][-n+400:])))}
# Point-in-time property: batch prefix consistency of ta (indicator at t unchanged when future is appended?)
full = tapkg.momentum.RSIIndicator(sub.close, 14).rsi().values
pre = tapkg.momentum.RSIIndicator(sub.close.iloc[:10_000], 14).rsi().values
res["ta_rsi_prefix_consistency_maxabs"] = float(np.nanmax(np.abs(full[:10_000] - pre)))
print(json.dumps(res, indent=1)); save("stats_microtest.json", res)
