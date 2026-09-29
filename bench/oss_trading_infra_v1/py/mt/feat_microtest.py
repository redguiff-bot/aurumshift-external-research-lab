"""Batch indicator libraries vs each other + prefix (no-lookahead) consistency. Run in the venv holding TA-Lib (and pandas-ta on py3.12 separately)."""
import warnings, sys, json, time; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from common import *
df = synth(20_000, seed=11); res = {"python": sys.version.split()[0]}
out = {}
try:
    import talib; out["TA-Lib"] = {"version": talib.__version__}
    ref = {"EMA20": talib.EMA(df.close.values, 20), "RSI14": talib.RSI(df.close.values, 14), "ATR14": talib.ATR(df.high.values, df.low.values, df.close.values, 14)}
    t0 = time.perf_counter(); [talib.RSI(df.close.values, 14) for _ in range(100)]; out["TA-Lib"]["rsi_20k_ms"] = round((time.perf_counter() - t0) * 10, 3)
    full = talib.RSI(df.close.values, 14); pre = talib.RSI(df.close.values[:10_000], 14)
    out["TA-Lib"]["prefix_consistency_maxabs"] = float(np.nanmax(np.abs(full[:10_000] - pre)))
    out["TA-Lib"]["ref"] = {k: float(np.nanmean(v[-1000:])) for k, v in ref.items()}
    try:
        import ta as tapkg
        out["TA-Lib"]["vs_ta_rsi_maxabs_after_200"] = float(np.nanmax(np.abs(ref["RSI14"][200:] - tapkg.momentum.RSIIndicator(df.close, 14).rsi().values[200:])))
        out["TA-Lib"]["vs_ta_atr_maxabs_after_200"] = float(np.nanmax(np.abs(ref["ATR14"][200:] - tapkg.volatility.AverageTrueRange(df.high, df.low, df.close, 14).average_true_range().values[200:])))
    except ImportError: pass
except Exception as e: out["TA-Lib"] = {"error": f"{type(e).__name__}: {e}"}
try:
    import pandas_ta as pta; out["pandas-ta"] = {"version": pta.version if hasattr(pta, "version") else "?"}
    r = pta.rsi(df.close, 14); a = pta.atr(df.high, df.low, df.close, 14)
    out["pandas-ta"]["mean_rsi_last1000"] = float(r.iloc[-1000:].mean()); out["pandas-ta"]["mean_atr_last1000"] = float(a.iloc[-1000:].mean())
    pre = pta.rsi(df.close.iloc[:10_000], 14); out["pandas-ta"]["prefix_consistency_maxabs"] = float(np.nanmax(np.abs(r.iloc[:10_000].values - pre.values)))
    try:
        import talib; out["pandas-ta"]["vs_talib_rsi_maxabs_after_200"] = float(np.nanmax(np.abs(r.values[200:] - talib.RSI(df.close.values, 14)[200:])))
    except ImportError: pass
except Exception as e: out.setdefault("pandas-ta", {})["error"] = f"{type(e).__name__}: {str(e)[:200]}"
res["libs"] = out
print(json.dumps(res, indent=1)); save(f"feat_microtest_py{sys.version_info.minor}_{'talib' if 'TA-Lib' in out and 'error' not in out['TA-Lib'] else 'nolib'}.json", res)
