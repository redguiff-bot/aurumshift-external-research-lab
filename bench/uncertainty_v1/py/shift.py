"""Distribution-shift detection + 4-way uncertainty attribution (NO_SIGNAL / DATA_GAP / MODEL_UNCERTAINTY / OUT_OF_DISTRIBUTION)."""
import sys, json, numpy as np, pandas as pd, time
from scipy.stats import ks_2samp
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import roc_auc_score, f1_score
from worlds import *; from models import *; import calibrators as C; import metrics as M

WIN, BLK = 200, 100


def stats_block(base, Xref, Xw, Lw_conf, yw_wrong_conf):
    Xr = impute(Xref, base.mu)
    out = {}
    fin = ~np.isnan(Xw).any(1)
    out["ks_max"] = max(ks_2samp(Xr[:, j], Xw[~np.isnan(Xw[:, j]), j]).statistic for j in range(Xw.shape[1])) if fin.sum() > 30 else 0.0
    out["mahal_mean"] = float(base.mahal(Xw).mean())
    out["missing_rate"] = float(np.isnan(Xw).any(1).mean())
    out["repeat_rate"] = float(repeat_flag(Xw).any(1)[1:].mean())
    Xa = np.vstack([Xr[np.random.default_rng(0).choice(len(Xr), 400, replace=False)], impute(Xw, base.mu)])
    ya = np.r_[np.zeros(400), np.ones(len(Xw))]
    try:
        pr = cross_val_predict(LogisticRegression(max_iter=200), feats(Xa), ya, cv=2, method="predict_proba")[:, 1]
        out["domain_auc"] = roc_auc_score(ya, pr)
    except Exception: out["domain_auc"] = 0.5
    return out


def detection(seed, mag, scenarios):
    rows = []
    for sc in scenarios:
        Wd = make_world(seed, sc, mag); s = Wd["sl"]; X, y = Wd["x"], Wd["y"]; on = Wd["onset_rel"]
        base = Base(seed=seed, n_ens=2).fit(X[s["train"]], y[s["train"]])
        Xc = X[s["cal"]]; Lc = base.logits(Xc); yc = y[s["cal"]]
        f = C.fit_apply("beta", Lc, yc)
        Xv = X[s["val"]]; Xh = X[s["hold"]]; Pv = f(base.logits(Xv)); Ph = f(base.logits(Xh))
        yv, yh = y[s["val"]], y[s["hold"]]
        def series(Xs, Ps, ys, n0):
            out = []
            for b in range(WIN, len(Xs) + 1, BLK):
                sl_ = slice(b - WIN, b); st = stats_block(base, Xc, Xs[sl_], None, None)
                hi = b - H_MAT; ml = slice(max(0, hi - WIN), hi)
                st["loss_win"] = M.logloss(Ps[ml], ys[ml]) if hi > 50 else np.nan
                st["end"] = b; out.append(st)
            return pd.DataFrame(out)
        H_MAT = 10
        dv = series(Xv, Pv, yv, 0); dh = series(Xh, Ph, yh, len(Xv))
        # label-based loss monitor: needs matured labels only
        for det in ["ks_max", "mahal_mean", "domain_auc", "missing_rate", "repeat_rate", "loss_win"]:
            thr = dv[det].max() * (1.0 if det not in ("missing_rate", "repeat_rate") else 1.0)
            if det in ("missing_rate", "repeat_rate"): thr = max(0.02, thr)
            al = dh[det].values > thr
            pre = dh["end"].values <= on; post = ~pre
            far = al[pre].mean() if pre.any() else np.nan
            firsts = dh["end"].values[post & al]
            delay = (firsts[0] - on) if len(firsts) else np.nan
            rows.append(dict(seed=seed, scenario=sc, detector=det, threshold=thr, far_pre=far, detected=bool(len(firsts)),
                             delay=delay, post_alarm_rate=al[post].mean()))
    return rows


def row_features(base, cal_f, Xc, Xrows):
    P = cal_f(base.logits(Xrows))
    return dict(nan=np.isnan(Xrows).any(1), rep=np.r_[False, repeat_flag(Xrows).any(1)[1:]], mahal=base.mahal(Xrows),
                mi=base.epistemic(Xrows), conf=P.max(1), P=P)


QO, QM, TN = (.99, .995, .999), (.9, .95, .99), (.4, .45, .5, .55, .6)


def classify(d, cfg):
    out = np.array(["NORMAL"] * len(d), dtype=object)
    out[d.conf.values < cfg["tau_ns"]] = "NO_SIGNAL"
    if cfg.get("use_mi", True): out[d[f"mi_{cfg['q_mi']}"].values] = "MODEL_UNCERTAINTY"
    if cfg.get("use_ood", True): out[d[f"ood_{cfg['q_ood']}"].values] = "OUT_OF_DISTRIBUTION"
    if cfg.get("use_gap_flags", True): out[d.nan.values | d.rep.values] = "DATA_GAP"
    return out


def assemble(seed, mag, kind="lr", scen=("none", "feature_shift", "venue_change", "missing_features", "stale_features", "rare_cluster", "vol_jump", "regime_transition")):
    """Per-row features + ground-truth cause: post-onset rows of each causal scenario + pre-onset rows of 'none'."""
    pool = []; ref = None
    for sc in scen:
        Wd = make_world(seed, sc, mag); s = Wd["sl"]; X, y = Wd["x"], Wd["y"]; on = Wd["onset_rel"]
        base = Base(seed=seed, kind=kind, n_ens=8).fit(X[s["train"]], y[s["train"]])
        Lc = base.logits(X[s["cal"]]); f = C.fit_apply("beta", Lc, y[s["cal"]])
        if ref is None:
            Xc = X[s["cal"]]; mh, mi = base.mahal(Xc), base.epistemic(Xc)
            ref = dict(mahal={q: np.quantile(mh, q) for q in QO}, mi={q: np.quantile(mi, q) for q in QM})
        ft = row_features(base, f, None, X[s["hold"]])
        yh = y[s["hold"]]
        keep = np.arange(len(yh)) >= on if sc != "none" else np.arange(len(yh)) < on
        d = pd.DataFrame(dict(seed=seed, scenario=sc, truth=Wd["cause"][s["hold"]], wrong=(ft["P"].argmax(1) != yh), conf=ft["conf"],
                              nan=ft["nan"], rep=ft["rep"], mahal=ft["mahal"], mi=ft["mi"]))
        for q in QO: d[f"ood_{q}"] = ft["mahal"] > ref["mahal"][q]
        for q in QM: d[f"mi_{q}"] = ft["mi"] > ref["mi"][q]
        pool.append(d[keep])
    return pd.concat(pool)


CAUSE4 = ["NORMAL", "NO_SIGNAL", "DATA_GAP", "MODEL_UNCERTAINTY", "OUT_OF_DISTRIBUTION"]
CAUSAL_SCEN = ("none", "feature_shift", "venue_change", "missing_features", "stale_features", "rare_cluster")


def macro_f1(d, cfg):
    d = d[d.scenario.isin(CAUSAL_SCEN)]
    return f1_score(d.truth.values, classify(d, cfg), labels=CAUSE4, average="macro", zero_division=0)


if __name__ == "__main__":
    mode, a, b, mag, out = sys.argv[1], *map(int, sys.argv[2].split("-")), float(sys.argv[3]), sys.argv[4]
    dd = pd.concat([assemble(sd, mag) for sd in range(a, b)]); dd.to_csv(out + f"_diagrows_{mode}_{a}_{b}.csv.gz", index=False)
    if mode == "tune":
        import itertools
        res = [dict(q_ood=qo, q_mi=qm, tau_ns=tn, f1=macro_f1(dd, dict(q_ood=qo, q_mi=qm, tau_ns=tn))) for qo, qm, tn in itertools.product(QO, QM, TN)]
        r = pd.DataFrame(res).sort_values("f1", ascending=False); r.to_csv(out + "_diag_tuning.csv", index=False); print(r.head())
    else:
        rows = []
        for sd in range(a, b): rows += detection(sd, mag, ["none", "vol_jump", "regime_transition", "feature_shift", "missing_features", "stale_features", "venue_change", "rare_cluster"])
        pd.DataFrame(rows).to_csv(out + f"_detection_{a}_{b}.csv", index=False)
