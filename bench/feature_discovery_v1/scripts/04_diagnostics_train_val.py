"""Train/validation-only diagnostics: cross-market & cross-time stability of sparse selection,
additive-vs-interaction model test, redundancy, environment invariance (Cochran-Q) and ICP-lite."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from fd import panel, features, pipeline as P, invariance, expr as E
from fd.sparse import stability_selection
from fd.metrics import spearman, rank01

RES = os.path.join(os.path.dirname(__file__), "..", "results")
N = features.NAMES
fro = json.load(open(os.path.join(RES, "discovery_train_val.json")))
out = {}
for target in ("y_ret", "y_vol"):
    tr, tri = panel.panels(target, "train"); va, vai = panel.panels(target, "val")
    d = {}
    # a) sparse stability per market and per time-half (pi=0.7)
    rng = np.random.default_rng(5)
    per = {}
    for m in tr:
        X, y = tr[m]
        st, _ = stability_selection(X, y, [len(y)], rng, B=40)
        per[m] = dict(zip(N, map(float, st)))
    h = len(next(iter(tr.values()))[1]) // 2
    for lab, sl in (("first_half", slice(0, h)), ("second_half", slice(h, None))):
        Xp = np.vstack([tr[m][0][sl] for m in tr]); yp = np.concatenate([tr[m][1][sl] for m in tr])
        st, _ = stability_selection(Xp, yp, [len(tr[m][1][sl]) for m in tr], rng, B=40)
        per[lab] = dict(zip(N, map(float, st)))
    d["sparse_stability"] = per
    tab = pd.DataFrame(per)
    d["sparse_consistency"] = {n: dict(markets_ge_0p7=int((tab.loc[n, list(tr)] >= 0.7).sum()),
                                       both_halves_ge_0p7=bool(tab.loc[n, "first_half"] >= .7 and tab.loc[n, "second_half"] >= .7))
                               for n in N}
    # b) additive vs interaction GBM on validation
    Xp = np.vstack([tr[m][0] for m in tr]); yp = np.concatenate([tr[m][1] for m in tr])
    Xv = np.vstack([va[m][0] for m in va]); yv = np.concatenate([va[m][1] for m in va])
    res = {}
    for dep in (1, 3):
        g = HistGradientBoostingRegressor(max_depth=dep, max_iter=150, learning_rate=0.05, min_samples_leaf=300,
                                          l2_regularization=10.0, random_state=0).fit(Xp, yp)
        pv = g.predict(Xv)
        res[f"depth{dep}"] = dict(ic=spearman(pv, yv), r2=float(1 - ((yv - pv) ** 2).sum() / ((yv - yp.mean()) ** 2).sum()))
    d["gbm_additive_vs_interaction_val"] = res
    # c) invariance of frozen candidates over environments = market x calendar-year (train+val)
    envX, envy = {}, {}
    for m in tr:
        idx = np.concatenate([np.array(tri), np.array(vai)])
        X = np.vstack([tr[m][0], va[m][0]]); y = np.concatenate([tr[m][1], va[m][1]])
        yrs = pd.DatetimeIndex(idx).year.values
        for yr in np.unique(yrs):
            k = yrs == yr
            if k.sum() > 1500:
                envX[f"{m}_{yr}"] = X[k]; envy[f"{m}_{yr}"] = y[k]
    inv = {}
    for c in fro[target]["frozen"]:
        f = {e: P.cand_value(c, envX[e], N) for e in envX}
        q = invariance.cochran_q(f, envy); q["n_env"] = len(envX)
        inv[c["id"]] = q
    d["invariance_train_val"] = inv
    mains = fro[target]["consolidation"].get("mains", [])
    cand = mains[:8] if len(mains) >= 3 else [N[i] for i in np.argsort([-fro[target]["consolidation"]["stab_mean"][n] for n in N])[:6]]
    d["icp_lite"] = dict(candidates=cand, **invariance.icp_lite(envX, envy, N, cand, max_size=3))
    # d) redundancy among frozen candidates and vs mains
    fz = fro[target]["frozen"]
    if fz:
        V = np.column_stack([P.cand_value(c, Xv, N) for c in fz])
        d["corr_frozen"] = np.corrcoef(rank01(V.T[0]) if len(fz) == 1 else np.column_stack([rank01(V[:, i]) for i in range(V.shape[1])]).T).tolist() if len(fz) > 1 else [[1.0]]
        if mains:
            M = np.column_stack([Xv[:, N.index(n)] for n in mains]); M1 = np.column_stack([np.ones(len(M)), M])
            r2 = []
            for i in range(V.shape[1]):
                b = np.linalg.lstsq(M1, V[:, i], rcond=None)[0]
                r2.append(float(1 - ((V[:, i] - M1 @ b) ** 2).sum() / ((V[:, i] - V[:, i].mean()) ** 2).sum()))
            d["r2_frozen_on_mains_val"] = dict(zip([c["id"] for c in fz], r2))
    out[target] = d
    print(target, {k: v for k, v in d.items() if k in ("gbm_additive_vs_interaction_val", "r2_frozen_on_mains_val")}, {k: (v["Q"], v["p"], v["sign_agree"]) for k, v in inv.items()}, d["icp_lite"]["n_accepted"], flush=True)
json.dump(out, open(os.path.join(RES, "diagnostics_train_val.json"), "w"), indent=1, default=float)
