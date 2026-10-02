"""Conformal / interval methods with explicit label-maturity delay H.
Regression target = latent forward return r; classification = 3-class outcome.
Non-exchangeable (AR features, clustered vol) + shift scenarios; iid_control shows textbook coverage."""
import sys, json, numpy as np, pandas as pd, time
from scipy.stats import norm
from worlds import *; from models import *; import metrics as M

H = 10
ALPHA_R, ALPHA_C = 0.10, 0.20


def qhat(s, level):
    """conformal (1-alpha)-quantile with finite-sample correction; level<=0 -> -inf, >=1 -> +inf."""
    n = len(s)
    if level >= 1 or n == 0: return np.inf
    if level <= 0: return -np.inf
    k = int(np.ceil((n + 1) * level))
    return np.inf if k > n else np.partition(s, k - 1)[k - 1]


def wquant(s, w, level):
    o = np.argsort(s); cw = np.cumsum(w[o]) / (w.sum() + 1.0)      # +1 mass at +inf (test point weight ~1)
    i = np.searchsorted(cw, level); return np.inf if i >= len(s) else s[o][i]


def stream_scores(score_all, off, method, alpha, W=600, HL=400, gamma=0.01, cal_scores=None, delay=H):
    """Return per-step threshold q_t for hold rows.  score_all: nonconformity for [val|hold] rows (known only when matured)."""
    n = len(score_all) - off; q = np.zeros(n); at = alpha; alphas = np.zeros(n)
    for t in range(n):
        ta = off + t; hi = ta - delay + 1                            # matured rows: s <= ta-delay
        if method in ("split", "aci_split"):
            pool = cal_scores
        elif method in ("rolling", "aci_rolling"):
            pool = score_all[max(0, hi - W):hi]
        elif method == "weighted":
            idx = np.arange(0, hi); pool = score_all[idx]; w = 0.5 ** ((hi - 1 - idx) / HL)
        if method == "weighted": q[t] = wquant(pool, w, 1 - alpha)
        elif method.startswith("aci"): q[t] = qhat(pool, 1 - at)
        else: q[t] = qhat(pool, 1 - alpha)
        alphas[t] = at
        if method.startswith("aci"):                                   # delayed feedback: err of row t-delay becomes known now
            s_prev = t - delay
            if s_prev >= 0:
                err = float(score_all[off + s_prev] > q[s_prev]); at = at + gamma * (alpha - err)
    return q, alphas


def regression(seed, mag, grid, scenarios, alpha=ALPHA_R):
    rows = []
    for sc in scenarios:
        Wd = make_world(seed, "none" if sc == "iid_control" else sc, mag, iid=(sc == "iid_control"))
        s = Wd["sl"]; X, r = Wd["x"], Wd["r"]; on = Wd["onset_rel"]
        base = Base(seed=seed, n_ens=1).fit(X[s["train"]], Wd["y"][s["train"]], r[s["train"]])
        pc = base.reg_pred(X[s["cal"]]); ec = np.abs(r[s["cal"]] - pc)
        Xa = np.vstack([X[s["val"]], X[s["hold"]]]); ra = np.r_[r[s["val"]], r[s["hold"]]]
        pa = base.reg_pred(Xa); ea = np.abs(ra - pa); off = N_VAL; eh = ea[off:]
        sig_h = Wd["sigma"][s["hold"]]
        # local-scale (normalised) score: scale = mean |res| over last 50 matured rows
        def scale_series(e_all, first_cal):
            sc_ = np.zeros(len(e_all))
            for t in range(len(e_all)):
                hi = t - H + 1; sc_[t] = e_all[max(0, hi - 50):hi].mean() if hi > 5 else first_cal
            return sc_
        sc_all = scale_series(ea, ec.mean()); ec_full = np.abs(r[s["cal"]] - pc)
        sc_cal = scale_series(np.r_[ec_full, ea], ec.mean())[:len(ec_full)]
        z = norm.ppf(1 - alpha / 2)
        meths = {"gaussian": None, "split": ("split", 1), "rolling": ("rolling", 1), "weighted": ("weighted", 1),
                 "aci_split": ("aci_split", 1), "aci_rolling": ("aci_rolling", 1),
                 "norm_split": ("split", 2), "norm_aci": ("aci_split", 2)}
        for mn, spec in meths.items():
            if mn == "gaussian": half = np.full(len(eh), z * ec.std()); al = np.full(len(eh), alpha)
            elif spec[1] == 1:
                q, al = stream_scores(ea, off, spec[0], alpha, W=grid["W"], HL=grid["HL"], gamma=grid["gamma"], cal_scores=ec)
                half = q
            else:
                nsc = ea / np.maximum(sc_all, 1e-3); ncal = ec_full / np.maximum(sc_cal, 1e-3)
                q, al = stream_scores(nsc, off, spec[0], alpha, gamma=grid["gamma"], cal_scores=ncal)
                half = q * np.maximum(sc_all[off:], 1e-3)
            cov = eh <= half; fin = np.isfinite(half)
            for ph, sl_ in (("pre", slice(0, on)), ("post", slice(on, None))):
                c = cov[sl_]; wv = [c[k:k + 300].mean() for k in range(0, len(c) - 299, 300)]
                lowv = sig_h[sl_] < 1.2
                rows.append(dict(seed=seed, scenario=sc, method=mn, phase=ph, alpha=alpha, coverage=c.mean(),
                                 worst_win_cov=min(wv), cov_gap_abs=abs(c.mean() - (1 - alpha)),
                                 width=float(np.median(np.minimum(2 * half[sl_], 1e3))), inf_rate=float((~fin[sl_]).mean()),
                                 cov_lowvol=c[lowv].mean() if lowv.any() else np.nan,
                                 cov_highvol=c[~lowv].mean() if (~lowv).any() else np.nan,
                                 alpha_final=float(al[sl_][-1]) if len(al) else np.nan))
    return rows


def classification(seed, mag, grid, scenarios, alpha=ALPHA_C, kind="lr"):
    rows = []
    for sc in scenarios:
        Wd = make_world(seed, "none" if sc == "iid_control" else sc, mag, iid=(sc == "iid_control"))
        s = Wd["sl"]; X, y = Wd["x"], Wd["y"]; on = Wd["onset_rel"]
        base = Base(seed=seed, n_ens=1, kind=kind).fit(X[s["train"]], y[s["train"]])
        Pc = base.proba(X[s["cal"]]); sc_cal = 1 - Pc[np.arange(len(Pc)), y[s["cal"]]]
        Pa = base.proba(np.vstack([X[s["val"]], X[s["hold"]]])); ya = np.r_[y[s["val"]], y[s["hold"]]]
        off = N_VAL; Ph = Pa[off:]; yh = ya[off:]
        sc_all = 1 - Pa[np.arange(len(Pa)), ya]
        for mn in ("split", "rolling", "weighted", "aci_split", "aci_rolling"):
            q, al = stream_scores(sc_all, off, mn, alpha, W=grid["W"], HL=grid["HL"], gamma=grid["gamma"], cal_scores=sc_cal)
            sets = (1 - Ph) <= q[:, None]; size = sets.sum(1)
            cov = sets[np.arange(len(yh)), yh]; single = size == 1
            act = np.where(single, Ph.argmax(1), 1)
            for ph, sl_ in (("pre", slice(0, on)), ("post", slice(on, None))):
                sg = single[sl_]
                rows.append(dict(seed=seed, scenario=sc, base=kind, method=mn, phase=ph, alpha=alpha, coverage=cov[sl_].mean(),
                                 set_size=size[sl_].mean(), singleton_rate=sg.mean(), abstain=1 - sg.mean(),
                                 acc_singleton=float((Ph[sl_].argmax(1) == yh[sl_])[sg].mean()) if sg.any() else np.nan,
                                 utility=float(M.utility(act[sl_], yh[sl_]).mean()),
                                 acc_all=float((Ph[sl_].argmax(1) == yh[sl_]).mean()),
                                 empty_rate=float((size[sl_] == 0).mean())))
    return rows


if __name__ == "__main__":
    a, b = map(int, sys.argv[1].split("-")); mag = float(sys.argv[2]); out = sys.argv[3]; grid = json.loads(sys.argv[4])
    scs = SCENARIOS + ["iid_control"]; RR, RC = [], []; t0 = time.time()
    for sd in range(a, b):
        RR += regression(sd, mag, grid, scs)
        for kd in ("lr", "gbm"): RC += classification(sd, mag, grid, scs, kind=kd)
        print("seed", sd, round(time.time() - t0), flush=True)
    pd.DataFrame(RR).to_csv(out + "_conf_reg.csv", index=False); pd.DataFrame(RC).to_csv(out + "_conf_clf.csv", index=False)
