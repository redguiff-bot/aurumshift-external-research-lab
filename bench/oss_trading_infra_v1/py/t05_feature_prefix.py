"""T05 — feature/indicator causality (prefix invariance) across ALL indicators a library exposes, plus known-answer checks.
Column c is 'leaky' if value at row t computed on data[:T] differs from value computed on the full series (t<T-guard)."""
import sys, json, warnings, time; warnings.filterwarnings("ignore")
sys.path.insert(0, __file__.rsplit("/",1)[0])
import numpy as np, pandas as pd
from common import make_bars
lib = sys.argv[1]; T = 400; full = make_bars(n=600, seed=9); part = full.iloc[:T]
res = dict(lib=lib)
def cmp_frames(a, b, tol=1e-9):
    global T
    common = [c for c in a.columns if c in b.columns]; leaky = []; ok = 0; allnan = []
    for c in common:
        x = a[c].iloc[:T]; y = b[c].iloc[:T]
        if x.isna().all() and y.isna().all(): allnan.append(c); continue
        xa, ya = pd.to_numeric(x, errors="coerce").values, pd.to_numeric(y, errors="coerce").values
        bad = ~(np.isclose(xa, ya, rtol=1e-7, atol=tol, equal_nan=True))
        (leaky if bad.any() else [None]).append(c) if bad.any() else None
        ok += (not bad.any())
    return dict(n_columns=len(common), n_causal=ok, n_leaky=len(leaky), leaky_columns=leaky, n_all_nan=len(allnan))

if lib == "ta":
    import ta
    def feats(d): return ta.add_all_ta_features(d.copy(), open="Open", high="High", low="Low", close="Close", volume="Volume", fillna=False)
    t = time.perf_counter(); a = feats(full); res["seconds_full"] = time.perf_counter()-t; b = feats(part)
    res.update(cmp_frames(a, b))
    # known answer: RSI(14) Wilder vs hand-rolled
    c = full.Close; d = c.diff(); up = d.clip(lower=0); dn = -d.clip(upper=0)
    ru = up.ewm(alpha=1/14, adjust=False).mean(); rd = dn.ewm(alpha=1/14, adjust=False).mean(); rsi = 100-100/(1+ru/rd)
    from ta.momentum import RSIIndicator
    r2 = RSIIndicator(c, 14).rsi(); res["rsi14_max_abs_diff_vs_hand_wilder"] = float((rsi-r2).abs().iloc[100:].max())
elif lib == "pandas_ta":
    import pandas_ta as pta
    def feats(d):
        d = d.copy(); d.columns = [x.lower() for x in d.columns]
        try:
            d.ta.study(pta.AllStudy, verbose=False, timed=False, ordered=False)
        except Exception as e:
            res.setdefault("strategy_errors", []).append(repr(e)[:200])
        return d
    t = time.perf_counter(); a = feats(full); res["seconds_full"] = time.perf_counter()-t; b = feats(part)
    a = a.drop(columns=[c for c in ["open","high","low","close","volume"] if c in a.columns]); b = b.drop(columns=[c for c in ["open","high","low","close","volume"] if c in b.columns])
    res.update(cmp_frames(a, b))
elif lib == "vectorbt":
    import vectorbt as vbt
    ind = ["MA", "MSTD", "BBANDS", "RSI", "STOCH", "MACD", "ATR", "OBV"]
    out = {}
    for name in ind:
        cls = getattr(vbt, name)
        def run(d):
            args = {"MA": (d.Close,), "MSTD": (d.Close,), "BBANDS": (d.Close,), "RSI": (d.Close,), "STOCH": (d.High, d.Low, d.Close), "MACD": (d.Close,), "ATR": (d.High, d.Low, d.Close), "OBV": (d.Close, d.Volume)}[name]
            return cls.run(*args, window=14) if name in ("MA", "MSTD", "BBANDS", "RSI", "ATR") else cls.run(*args)
        A, B = run(full), run(part)
        leaky = []
        for o in A.output_names:
            x = getattr(A, o).iloc[:T].values.astype(float); y = getattr(B, o).iloc[:T].values.astype(float)
            if not np.allclose(x, y, rtol=1e-7, atol=1e-9, equal_nan=True): leaky.append(o)
        out[name] = dict(outputs=len(A.output_names), leaky=leaky)
    res["indicators"] = out
elif lib == "tsfresh":
    from tsfresh import extract_features
    from tsfresh.utilities.dataframe_functions import roll_time_series
    from tsfresh.feature_extraction import MinimalFCParameters
    def feats(d):
        x = pd.DataFrame(dict(id=1, time=np.arange(len(d)), v=d.Close.values))
        r = roll_time_series(x, column_id="id", column_sort="time", max_timeshift=19, min_timeshift=19, disable_progressbar=True, n_jobs=1)
        f = extract_features(r, column_id="id", column_sort="time", default_fc_parameters=MinimalFCParameters(), disable_progressbar=True, n_jobs=1)
        f.index = [i[1] for i in f.index]; return f
    t = time.perf_counter(); a = feats(full); res["seconds_full"] = time.perf_counter()-t; b = feats(part)
    idx = a.index.intersection(b.index); idx = idx[idx < T]
    a = a.loc[idx].reset_index(drop=True); b = b.loc[idx].reset_index(drop=True)
    T = len(a); res.update(cmp_frames(a, b))
    res["note"] = "roll_time_series with min_timeshift=max_timeshift=19: each window uses only rows <= its own timestamp"
print(json.dumps(res))
