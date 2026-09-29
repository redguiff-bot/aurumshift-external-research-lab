"""Regime-conditional analysis. Regime labels are causal (trailing windows) and lagged one bar to the PnL they condition."""
from common import *
P = load_panel(); NAMES = list(X.PRIMS); out = {"regime_share": {}, "prims": {}}
BT = {k: bt(k, P) for k in NAMES}
labs = {n: f(P).shift(1) for n, f in REGIMES.items()}    # label known at decision time
rng = np.random.default_rng(1)
ev = slice(L.EVAL_START, None)
for n, lb in labs.items(): out["regime_share"][n] = lb.loc[ev].value_counts(normalize=True, dropna=True).round(3).to_dict()
def state_stats(pnl, lb, st, start, end):
    m = (lb == st).loc[start:end]; x = pnl.loc[start:end]
    d = (x * m).resample("1D").sum(); nd = m.resample("1D").sum(); d = d[nd > 0]
    n = len(d)
    if n < 20: return {"days": n, "ann_ret": None, "t": None, "sharpe": None}
    return {"days": n, "share_hours": float(m.mean()), "ann_ret": float(x[m].mean() * 8760), "t": float(d.mean() / (d.std() / np.sqrt(n))) if d.std() > 0 else None, "sharpe": float(d.mean() / d.std() * np.sqrt(365)) if d.std() > 0 else None}
for k in NAMES:
    r = {}
    for n, lb in labs.items():
        states = [s for s in lb.dropna().unique()]
        st = {}
        for s in states:
            st[str(s)] = {"gross_full": state_stats(BT[k].gross, lb, s, L.EVAL_START, None), "net_full": state_stats(BT[k].net, lb, s, L.EVAL_START, None),
                          "gross_dev": state_stats(BT[k].gross, lb, s, L.EVAL_START, L.SPLIT), "gross_holdout": state_stats(BT[k].gross, lb, s, L.SPLIT, None)}
        # permutation p for regime dependence: range across states of mean hourly gross pnl; null = circularly shifted labels (keeps persistence)
        g = BT[k].gross.loc[ev]; l0 = lb.loc[ev]
        def stat(l):
            mm = [g[l == s].mean() for s in states if (l == s).sum() > 100]
            return (max(mm) - min(mm)) if len(mm) > 1 else 0.0
        obs = stat(l0); vals = l0.values; nul = []
        for _ in range(300):
            sh = int(rng.integers(720, len(vals) - 720)); nul.append(stat(pd.Series(np.roll(vals, sh), index=l0.index)))
        p = float((np.array(nul) >= obs).mean())
        # sign consistency dev vs holdout across states
        cons = [np.sign(st[s]["gross_dev"]["ann_ret"]) == np.sign(st[s]["gross_holdout"]["ann_ret"]) for s in st if st[s]["gross_dev"]["ann_ret"] is not None and st[s]["gross_holdout"]["ann_ret"] is not None]
        r[n] = {"states": st, "perm_p_range": p, "obs_range_hourly": float(obs), "sign_consistent_dev_holdout": int(sum(cons)), "n_states_cmp": len(cons)}
    out["prims"][k] = r
    print(k, {n: round(r[n]["perm_p_range"], 3) for n in r}, flush=True)
jd(out, "s3_regime.json")
