"""Public-data tasks (all fetched from OpenML/sklearn at run time; nothing redistributed).
 1 electricity (ELEC2, OpenML) : time-ordered, real non-stationarity -> static vs online calibration, conformal under drift
 2 credit-g, breast_cancer      : iid random resplits (train/cal/val/test) -> textbook static calibration/selective/conformal
 3 california housing regression : iid split vs covariate-shift split -> interval coverage
Split discipline: train -> base model, cal -> calibrators, val -> hyper-choices (W, HL), held-out/test -> reported once."""
import sys, json, warnings, numpy as np, pandas as pd
from scipy.special import softmax
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import HistGradientBoostingClassifier as HGB, HistGradientBoostingRegressor as HGR
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import fetch_openml, load_breast_cancer, fetch_california_housing
warnings.filterwarnings("ignore")
import calibrators as C, metrics as M, online as O, conformal as CF

TAU = 0.8


def fitbase(kind, Xt, yt):
    if kind == "lr":
        sc = StandardScaler().fit(Xt); m = LogisticRegression(max_iter=1000).fit(sc.transform(Xt), yt)
        return lambda X: m.decision_function(sc.transform(X)) if len(m.classes_) > 2 else np.stack([-m.decision_function(sc.transform(X)) / 2, m.decision_function(sc.transform(X)) / 2], 1)
    m = HGB(max_iter=200, learning_rate=0.2, early_stopping=False, random_state=0).fit(Xt, yt)
    return lambda X: np.log(np.clip(m.predict_proba(X), 1e-6, 1))


def msum(P, y):
    f, cw, hi = M.false_conf(P, y, TAU)
    return dict(n=len(y), acc=(P.argmax(1) == y).mean(), brier=M.brier(P, y), logloss=M.logloss(P, y), ece=M.ece(P, y),
                fcr=f, cwm=cw, hi_conf_rate=hi)


def electricity():
    d = fetch_openml("electricity", version=1, as_frame=True, parser="auto")
    X = d.data.drop(columns=["date"]); X["day"] = X["day"].astype(float); X = X.values.astype(float)
    y = (d.target.values == "UP").astype(int); n = len(y)
    itr, ical, ival, ihold = slice(0, 6000), slice(6000, 9000), slice(9000, 12000), slice(12000, n)
    rows, roll, cfrows = [], [], []
    for kind in ("lr", "gbm"):
        f = fitbase(kind, X[itr], y[itr]); Lc = f(X[ical]); yc = y[ical]
        Lall = f(X[ival.start:]); yall = y[ival.start:]; off = 3000; yh = yall[off:]
        # --- select W/HL on val only (online recal evaluated on val stream with history = cal)
        Lv = np.vstack([Lc, f(X[ival])]); yv2 = np.r_[yc, y[ival]]
        best = {}
        for mode, key, vals in (("window", "W", [500, 1000, 2000]), ("decay", "HL", [250, 500, 1000])):
            sc_ = []
            for v in vals:
                P = O.online_probs(Lv, yv2, 3000, "beta", mode=mode, **{key: v}); sc_.append(M.brier(P, y[ival]))
            best[mode] = vals[int(np.argmin(sc_))]
        for cn in C.NAMES:
            fs = C.fit_apply(cn, Lc, yc); Ps = fs(Lall[off:])
            variants = {"static": Ps}
            if cn in ("beta", "temperature", "isotonic"):
                variants["window"] = O.online_probs(Lall, yall, off, cn, mode="window", W=best["window"])
                variants["decay"] = O.online_probs(Lall, yall, off, cn, mode="decay", HL=best["decay"])
                variants["leak_h0"] = O.online_probs(Lall, yall, off, cn, mode="window", W=best["window"], delay=1)
                variants["leak_peek"] = O.online_probs(Lall, yall, off, cn, mode="window", W=best["window"], delay=1, peek=O.R)
            for vn, P in variants.items():
                rows.append(dict(task="electricity", base=kind, cal=cn, variant=vn, chosen_W=best["window"], chosen_HL=best["decay"], **msum(P, yh)))
                for k0 in range(0, len(P) - 1999, 2000):
                    r = msum(P[k0:k0 + 2000], yh[k0:k0 + 2000]); r.update(task="electricity", base=kind, cal=cn, variant=vn, block=k0 // 2000); roll.append(r)
        # conformal LAC on raw probs, alpha .2
        Pa = softmax(Lall, 1); sc_all = 1 - Pa[np.arange(len(yall)), yall]; sc_cal = 1 - softmax(Lc, 1)[np.arange(len(yc)), yc]
        for mn in ("split", "rolling", "weighted", "aci_split", "aci_rolling"):
            q, al = CF.stream_scores(sc_all, off, mn, 0.2, W=best["window"], HL=best["decay"], gamma=0.01, cal_scores=sc_cal)
            sets = (1 - Pa[off:]) <= q[:, None]; cov = sets[np.arange(len(yh)), yh]
            for k0 in range(0, len(yh) - 1999, 2000):
                sl_ = slice(k0, k0 + 2000)
                cfrows.append(dict(task="electricity", base=kind, method=mn, block=k0 // 2000, coverage=cov[sl_].mean(), set_size=sets[sl_].sum(1).mean(),
                                   singleton_rate=(sets[sl_].sum(1) == 1).mean()))
    return rows, roll, cfrows


def iid_tasks(nrep=20):
    rows, cfrows, rcrows = [], [], []
    ds = {"credit-g": lambda: (lambda d: (pd.get_dummies(d.data).values.astype(float), (d.target.values == "bad").astype(int)))(fetch_openml("credit-g", version=1, as_frame=True, parser="auto")),
          "breast_cancer": lambda: (lambda d: (d.data, d.target))(load_breast_cancer())}
    for name, ld in ds.items():
        X, y = ld(); n = len(y)
        for rep in range(nrep):
            p = np.random.default_rng(rep).permutation(n)
            a, b, c_, d_ = int(.4 * n), int(.6 * n), int(.8 * n), n       # train / cal / val / test
            itr, ical, ival, ite = p[:a], p[a:b], p[b:c_], p[c_:]
            for kind in ("lr", "gbm"):
                f = fitbase(kind, X[itr], y[itr]); Lc, Lt = f(X[ical]), f(X[ite]); yc, yt = y[ical], y[ite]
                for cn in C.NAMES:
                    P = C.fit_apply(cn, Lc, yc)(Lt)
                    rows.append(dict(task=name, rep=rep, base=kind, cal=cn, **msum(P, yt)))
                    if cn in ("raw", "platt", "beta"):
                        err = P.argmax(1) != yt; cov, risk, aurc = M.risk_coverage(P.max(1), err)
                        rcrows.append(dict(task=name, rep=rep, base=kind, cal=cn, aurc=aurc, risk_full=risk[-1], risk_at_50=risk[int(.5 * len(risk)) - 1]))
                Pc = softmax(Lc, 1); sc_cal = 1 - Pc[np.arange(len(yc)), yc]; Pt = softmax(Lt, 1)
                q = CF.qhat(sc_cal, 1 - 0.2); sets = (1 - Pt) <= q
                cfrows.append(dict(task=name, rep=rep, base=kind, coverage=sets[np.arange(len(yt)), yt].mean(), set_size=sets.sum(1).mean()))
    return rows, cfrows, rcrows


def california(nrep=10):
    d = fetch_california_housing(); X, y = d.data, d.target; rows = []
    for rep in range(nrep):
        rng = np.random.default_rng(rep)
        for split in ("iid", "shift_medinc"):
            if split == "iid":
                p = rng.permutation(len(y)); a, b, c_ = int(.4 * len(y)), int(.6 * len(y)), int(.8 * len(y))
                itr, ical, ival, ite = p[:a], p[a:b], p[b:c_], p[c_:]
            else:   # train/cal on lower-income districts, test on the top income quintile (covariate shift)
                o = np.argsort(X[:, 0] + 1e-6 * rng.standard_normal(len(y))); n = len(y)
                lo = rng.permutation(o[:int(.8 * n)]); itr, ical, ival = lo[:int(.5 * n)], lo[int(.5 * n):int(.65 * n)], lo[int(.65 * n):]
                ite = o[int(.8 * n):]
            m = HGR(max_iter=200, random_state=0).fit(X[itr], y[itr])
            ec = np.abs(y[ical] - m.predict(X[ical])); et = np.abs(y[ite] - m.predict(X[ite]))
            q = CF.qhat(ec, 0.9); z = ec.std() * 1.645
            # weighted CP with estimated density ratio (domain classifier) - Tibshirani et al. 2019
            dom = LogisticRegression(max_iter=500).fit(StandardScaler().fit(np.vstack([X[ical], X[ite]])).transform(np.vstack([X[ical], X[ite]])), np.r_[np.zeros(len(ical)), np.ones(len(ite))])
            sc = StandardScaler().fit(np.vstack([X[ical], X[ite]])); pr = dom.predict_proba(sc.transform(X[ical]))[:, 1]; w = pr / (1 - pr + 1e-6)
            o_ = np.argsort(ec); cw = np.cumsum(w[o_]) / (w.sum() + w.mean()); qw = ec[o_][min(np.searchsorted(cw, 0.9), len(ec) - 1)]
            for mn, qq in (("gaussian", z), ("split", q), ("weighted_cp_oracle_domain_clf", qw)):
                rows.append(dict(task="california", rep=rep, split=split, method=mn, coverage=(et <= qq).mean(), width=2 * qq))
    return rows


if __name__ == "__main__":
    out = sys.argv[1]
    r, l, c = electricity(); pd.DataFrame(r).to_csv(out + "_elec_metrics.csv", index=False); pd.DataFrame(l).to_csv(out + "_elec_blocks.csv", index=False); pd.DataFrame(c).to_csv(out + "_elec_conformal.csv", index=False)
    print("elec done", flush=True)
    r, c, k = iid_tasks(); pd.DataFrame(r).to_csv(out + "_iid_metrics.csv", index=False); pd.DataFrame(c).to_csv(out + "_iid_conformal.csv", index=False); pd.DataFrame(k).to_csv(out + "_iid_riskcov.csv", index=False)
    print("iid done", flush=True)
    pd.DataFrame(california()).to_csv(out + "_california.csv", index=False); print("cal done")
