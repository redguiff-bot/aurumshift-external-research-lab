"""Orthogonality / redundancy / persistence / turnover."""
from common import *
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
P = load_panel(); NAMES = list(X.PRIMS); out = {}
Ws = {k: weights(k, P) for k in NAMES}; BT = {k: bt(k, P, W=Ws[k]) for k in NAMES}
ev = slice(L.EVAL_START, None)
G = pd.DataFrame({k: BT[k].loc[ev, "gross"].resample("1D").sum() for k in NAMES})
N = pd.DataFrame({k: BT[k].loc[ev, "net"].resample("1D").sum() for k in NAMES})
mkt = P["ret"].fillna(0).mean(axis=1).loc[ev].resample("1D").sum()
out["corr_gross"] = G.corr().round(3).to_dict(); out["corr_net"] = N.corr().round(3).to_dict()
# position correlation (directional perp-equivalent exposure; P07 is delta-neutral -> excluded)
pos = {k: Ws[k].reindex(IDX).fillna(0.0).loc[ev].values.ravel() for k in NAMES if k != "P07_BASIS_CARRY"}
PC = pd.DataFrame(pos).corr().round(3); out["corr_position"] = PC.to_dict()
Gc = G.drop(columns=["P07_BASIS_CARRY"]).dropna(axis=1, how="any")
C = Gc.corr().fillna(0); ev_ = np.linalg.eigvalsh(C.values); ev_ = ev_[ev_ > 0]
out["effective_independent_bets_pr"] = float(ev_.sum() ** 2 / (ev_ ** 2).sum()); out["n_primitives_in_pca"] = int(Gc.shape[1])
# unique variance R2 vs others, max partner
red = {}
for k in Gc.columns:
    y = Gc[k].values; Xo = Gc.drop(columns=[k]).values; Xo = np.c_[np.ones(len(Xo)), Xo]
    b = np.linalg.lstsq(Xo, y, rcond=None)[0]; r2 = 1 - ((y - Xo @ b) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    o = C[k].drop(k).abs(); red[k] = {"R2_vs_others": float(r2), "max_abs_corr": float(o.max()), "partner": o.idxmax()}
out["redundancy"] = red
D = 1 - C.abs().values; np.fill_diagonal(D, 0); Z = linkage(squareform(D, checks=False), "average")
lab = fcluster(Z, t=0.5, criterion="distance"); out["clusters_absdist_lt_0.5"] = {k: int(l) for k, l in zip(Gc.columns, lab)}
# market beta / alpha
bet = {}
for k in NAMES:
    y = G[k].values; xx = np.c_[np.ones(len(mkt)), mkt.values]
    b, res, *_ = np.linalg.lstsq(xx, y, rcond=None); e = y - xx @ b
    s2 = e @ e / (len(y) - 2); cov = s2 * np.linalg.inv(xx.T @ xx)
    bet[k] = {"beta": float(b[1]), "alpha_ann": float(b[0] * 365), "alpha_t": float(b[0] / np.sqrt(cov[0, 0])) if s2 > 0 else None, "corr_mkt": float(np.corrcoef(y, mkt.values)[0, 1]) if y.std() > 0 else None}
out["market_beta"] = bet
# persistence
per = {}
for k in NAMES:
    W = Ws[k].reindex(IDX).fillna(0.0).loc[ev]; a = {}
    for lg in (1, 6, 24, 72):
        x = W.values[lg:].ravel(); y = W.values[:-lg].ravel(); m = (x != 0) | (y != 0)
        a[f"wac_lag{lg}"] = float(np.corrcoef(x[m], y[m])[0, 1]) if m.sum() > 100 and x[m].std() > 0 and y[m].std() > 0 else None
    runs = []
    for c in W.columns:
        s = np.sign(W[c].values); i = 0
        while i < len(s):
            if s[i] == 0: i += 1; continue
            j = i
            while j < len(s) and s[j] == s[i]: j += 1
            runs.append(j - i); i = j
    a["mean_hold_hours"] = float(np.mean(runs)) if runs else None; a["n_position_runs"] = len(runs)
    f = L.summarize(BT[k]); a["turnover_per_year"] = f["turn_ann"]; a["cost_drag_ann_at_base"] = f["cost_ann"]
    g = BT[k].loc[ev, "gross"].resample("1D").sum(); r90 = g.rolling(90).sum().dropna()
    a["frac_90d_windows_gross_pos"] = float((r90 > 0).mean()) if len(r90) else None
    per[k] = a
out["persistence"] = per
jd(out, "s2_ortho.json")
print("PR", out["effective_independent_bets_pr"], out["clusters_absdist_lt_0.5"])
print(C.round(2).to_string())
