"""T06 — river online statistics vs batch references: accuracy, numerical stability, snapshot/restore, determinism, throughput, drift detectors."""
import json, time, pickle, hashlib, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from river import stats, utils, drift
rng = np.random.default_rng(1); N = 200_000
x = rng.normal(0, 1, N) * 0.01 + 1e9            # large offset: stresses naive sum-of-squares
y = 0.5 * (x - 1e9) + rng.normal(0, 0.01, N)
res = {}
# accuracy
m, v, c = stats.Mean(), stats.Var(ddof=1), stats.Cov(ddof=1)
t = time.perf_counter()
for xi, yi in zip(x, y): m.update(xi); v.update(xi); c.update(xi, yi)
dt = time.perf_counter() - t
ref_m = np.mean(x); ref_v = np.var(x, ddof=1); ref_c = np.cov(x, y, ddof=1)[0, 1]
res["mean_rel_err"] = abs(m.get()-ref_m)/abs(ref_m); res["var_rel_err"] = abs(v.get()-ref_v)/ref_v; res["cov_rel_err"] = abs(c.get()-ref_c)/abs(ref_c)
res["updates_per_s_mean_var_cov"] = round(N/dt)
naive = (np.sum(x**2)/N - (np.sum(x)/N)**2) * N/(N-1); res["naive_sumsq_var_rel_err_for_comparison"] = abs(naive-ref_v)/ref_v
# rolling
w = 100; rm = utils.Rolling(stats.Mean, window_size=w); rv = utils.Rolling(stats.Var, window_size=w, ddof=1)
out_m = []; out_v = []
for xi in x[:20000]: rm.update(xi); rv.update(xi); out_m.append(rm.get()); out_v.append(rv.get())
pm = pd.Series(x[:20000]).rolling(w).mean().values; pv = pd.Series(x[:20000]).rolling(w).var().values
ex_m = np.array([np.mean(x[i-w+1:i+1]) for i in range(w-1, 20000)]); ex_v = np.array([np.var(x[i-w+1:i+1], ddof=1) for i in range(w-1, 20000)])
res["rolling_mean_max_abs_err_vs_exact_window"] = float(np.max(np.abs(np.array(out_m)[w-1:]-ex_m)))
res["rolling_var_max_rel_err_vs_exact_window"] = float(np.max(np.abs(np.array(out_v)[w-1:]-ex_v)/ex_v))
res["pandas_rolling_var_max_rel_err_vs_exact_window_for_comparison"] = float(np.nanmax(np.abs(pv[w-1:]-ex_v)/ex_v))
# ewm
e = stats.EWMean(fading_factor=0.95); oe = []
for xi in x[:5000]: e.update(xi); oe.append(e.get())
pe = pd.Series(x[:5000]).ewm(alpha=0.05, adjust=False).mean().values
res["ewmean_max_abs_diff_vs_pandas_adjust_false"] = float(np.max(np.abs(np.array(oe)-pe)))
# snapshot / restore mid-stream
a = stats.Var(); [a.update(xi) for xi in x[:1000]]
blob = pickle.dumps(a); b = pickle.loads(blob)
for xi in x[1000:2000]: a.update(xi); b.update(xi)
res["pickle_restore_identical"] = (a.get() == b.get()); res["pickle_bytes"] = len(blob)
# determinism across two fresh runs
def run():
    s = stats.Var(); q = stats.Quantile(0.5); o = []
    for xi in x[:20000]: s.update(xi); q.update(xi); o.append((s.get(), q.get()))
    return hashlib.sha256(repr(o).encode()).hexdigest()[:16]
res["deterministic_2_runs"] = run() == run()
# drift
sig = np.r_[rng.normal(0, 1, 2000), rng.normal(1.5, 1, 2000)]
for name, det in [("ADWIN", drift.ADWIN()), ("PageHinkley", drift.PageHinkley()), ("KSWIN", drift.KSWIN(seed=1))]:
    hits = []
    for i, s_ in enumerate(sig):
        det.update(s_)
        if det.drift_detected: hits.append(i)
    res[f"drift_{name}"] = dict(first_after_change=next((h for h in hits if h >= 2000), None), false_alarms_before_change=sum(h < 2000 for h in hits), change_at=2000)
print(json.dumps(res, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o)))
