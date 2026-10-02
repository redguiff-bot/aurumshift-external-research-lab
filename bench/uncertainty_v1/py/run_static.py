"""Static calibration + selective classification on synthetic worlds.
usage: run_static.py <seeds:a-b> <mag> <out_prefix> [--cfg frozen_config.json]
Splits: model fit on train; calibrators fit on cal; hyper-choices on val (tuning seeds only); scored on held-out."""
import sys, json, numpy as np, pandas as pd, time
from worlds import *; from models import *; import calibrators as C; import metrics as M


def score_types(base, X, P):
    return {"msp": P.max(1), "neg_entropy": -(-(P * np.log(P + 1e-12)).sum(1)),
            "neg_epistemic": -base.epistemic(X), "neg_mahal": -base.mahal(X)}


def run_seed(seed, mag, scenarios=SCENARIOS, kind='lr'):
    rows, rel, rc = [], [], []
    base = None
    for sc in scenarios:
        W = make_world(seed, sc, mag)
        s = W["sl"]; X, y = W["x"], W["y"]
        if base is None or True:
            base = Base(seed=seed, kind=kind, n_ens=5).fit(X[s["train"]], y[s["train"]], W["r"][s["train"]])
        Lc, Lv, Lh = (base.logits(X[s[k]]) for k in ("cal", "val", "hold"))
        yc, yv, yh = (y[s[k]] for k in ("cal", "val", "hold"))
        Xh = X[s["hold"]]; on = W["onset_rel"]
        for cn in C.NAMES:
            f = C.fit_apply(cn, Lc, yc)
            Pv, Ph = f(Lv), f(Lh)
            for ph, sl_ in (("pre", slice(0, on)), ("post", slice(on, None)), ("val", None)):
                if ph == "val": P_, y_ = Pv, yv
                else: P_, y_ = Ph[sl_], yh[sl_]
                r = dict(seed=seed, scenario=sc, method=cn, phase=ph, **M.summary(P_, y_))
                if ph != "val":
                    a = M.actions(P_); r["turnover"] = M.turnover(a)
                r['base'] = kind; rows.append(r)
            if sc in ("none", "vol_jump", "regime_transition", "feature_shift") and seed < 3:
                for ph, sl_ in (("pre", slice(0, on)), ("post", slice(on, None))):
                    for b, n, cm, am in M.reliability(Ph[sl_], yh[sl_]):
                        rel.append(dict(base=kind, seed=seed, scenario=sc, method=cn, phase=ph, bin=b, n=n, conf=cm, acc=am))
            # --- selective classification on calibrated confidences (score types)
            if cn in ("raw", "platt", "isotonic", "temperature", "beta", "bayes_bin"):
                for ph, sl_ in (("pre", slice(0, on)), ("post", slice(on, None))):
                    P_, y_, X_ = Ph[sl_], yh[sl_], Xh[sl_]
                    sc_all = score_types(base, X_, P_)
                    err = P_.argmax(1) != y_
                    for sn, sv in sc_all.items():
                        if sn != "msp" and cn != "platt": continue
                        cov, risk, aurc = M.risk_coverage(sv, err)
                        rc.append(dict(base=kind, seed=seed, scenario=sc, method=cn, phase=ph, score=sn, aurc=aurc,
                                       risk_at_50=float(risk[int(.5 * len(risk)) - 1]),
                                       risk_at_25=float(risk[int(.25 * len(risk)) - 1])))
    return rows, rel, rc


if __name__ == "__main__":
    a, b = map(int, sys.argv[1].split("-")); mag = float(sys.argv[2]); out = sys.argv[3]
    R, L, K = [], [], []
    t0 = time.time()
    for sd in range(a, b):
        for kd in ('lr', 'gbm'):
            r, l, k = run_seed(sd, mag, kind=kd); R += r; L += l; K += k
        print("seed", sd, round(time.time() - t0), "s", flush=True)
    pd.DataFrame(R).to_csv(out + "_metrics.csv", index=False)
    pd.DataFrame(L).to_csv(out + "_reliability.csv", index=False)
    pd.DataFrame(K).to_csv(out + "_riskcov.csv", index=False)
