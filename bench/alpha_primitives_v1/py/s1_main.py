"""Main results, IC, causality (truncation) audit, baselines."""
from common import *
P = load_panel(); out = {}; NAMES = list(X.PRIMS)
def ic_weekly(W, P, H, min_obs=30):
    lr = P["lret"]; sig = L.vol_est(lr, 168)
    fwd = lr[::-1].rolling(H, min_periods=H).sum()[::-1].shift(-1) / (sig * np.sqrt(H))
    Wd = W.reindex(IDX); wk = IDX.tz_localize(None).to_period("W").astype(str)
    rows = []
    for w_, g in pd.Series(range(len(IDX)), index=IDX).groupby(wk):
        ii = g.values; x = Wd.values[ii].ravel(); y = fwd.values[ii].ravel()
        m = (~np.isnan(x)) & (~np.isnan(y)) & (x != 0)
        if m.sum() >= min_obs: rows.append((IDX[ii[0]], float((x[m] * y[m]).sum() / np.sqrt((x[m] ** 2).sum() * (y[m] ** 2).sum())), m.sum()))   # uncentered (cosine) IC: consistent with PnL sign
    d = pd.DataFrame(rows, columns=["t", "ic", "n"]).set_index("t") if rows else pd.DataFrame({"ic": [], "n": []}, index=pd.DatetimeIndex([], tz="UTC"))
    return d
def ic_stats(d):
    if len(d) < 8: return {"ic": None, "t": None, "weeks": len(d)}
    return {"ic": float(d.ic.mean()), "t": float(d.ic.mean() / (d.ic.std() / np.sqrt(len(d)))), "weeks": len(d)}
res = {}
for k in NAMES:
    W = weights(k, P); B = bt(k, P, W=W)
    r = {"full": L.summarize(B, boot=True), "dev": L.summarize(B, end=L.SPLIT, boot=True), "holdout": L.summarize(B, start=L.SPLIT, boot=True)}
    # gross bootstrap p-value (information test, before costs)
    dl = B.loc[L.EVAL_START:, ["gross"]].resample("1D").sum().gross
    r["boot_gross_full"] = L.sbootstrap(dl)
    r["boot_gross_holdout"] = L.sbootstrap(B.loc[L.SPLIT:, ["gross"]].resample("1D").sum().gross)
    H = X.PRIMS[k]["H"]
    icd = ic_weekly(W, P, H)
    r["ic_H"] = H; r["ic_full"] = ic_stats(icd)
    r["ic_dev"] = ic_stats(icd[icd.index < L.SPLIT]); r["ic_holdout"] = ic_stats(icd[icd.index >= L.SPLIT])
    f = r["full"]; legs = 2 if k == "P07_BASIS_CARRY" else 1
    r["breakeven_bps_per_side"] = float(f["gross_ann"] / f["turn_ann"] * 1e4) if f["turn_ann"] > 0 else None
    r["avg_cost_bps_paid_per_side"] = float(f["cost_ann"] / f["turn_ann"] * 1e4) if f["turn_ann"] > 0 else None
    r["active_share"] = float((W.abs().sum(axis=1) > 0).loc[L.EVAL_START:].mean())
    r["family"] = X.PRIMS[k]["family"]; r["params"] = X.PRIMS[k]["params"]
    res[k] = r; print(k, round(f["gross_sharpe"], 2), round(f["net_sharpe"], 2), flush=True)
out["primitives"] = res
B0 = baseline_ew_long(P); out["baseline_ew_long"] = {"full": L.summarize(B0), "dev": L.summarize(B0, end=L.SPLIT), "holdout": L.summarize(B0, start=L.SPLIT)}
# ---- causality / truncation audit: weights computed on data cut at T must equal full-data weights up to T
cuts = [pd.Timestamp(x, tz="UTC") for x in ["2024-09-15 13:00", "2025-03-03 07:00", "2025-08-20 22:00", "2026-01-11 03:00", "2026-06-30 18:00"]]
aud = {}
for k in NAMES:
    Wf = weights(k, P).reindex(IDX).fillna(0.0); md = 0.0
    for T in cuts:
        Pt = {kk: (v.loc[:T] if isinstance(v, pd.DataFrame) else v) for kk, v in P.items()}
        Wt = weights(k, Pt).reindex(IDX.intersection(Pt["c"].index)).fillna(0.0)
        T1 = T - pd.Timedelta(hours=1)   # P14 places the value for bar T+1 at decision T; row T+1 absent in truncated data (boundary artifact) -> compare through T-1h
        md = max(md, float((Wt.loc[:T1] - Wf.loc[:T1]).abs().max().max()))
    aud[k] = {"max_abs_diff": md, "pass": md < 1e-9}
    print("audit", k, md, flush=True)
out["causality_audit"] = aud
jd(out, "s1_main.json")
