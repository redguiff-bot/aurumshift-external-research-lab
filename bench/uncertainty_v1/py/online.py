"""Static vs incremental (online) calibration with explicit label-maturity delay.

Row s (absolute stream index) has its label available only at time s+H (forward-return horizon H).
At hold-relative time t, a recalibrator may use only rows s <= t_abs - H.  Leaky variants exist
ONLY to quantify how much look-ahead would flatter results (and to test the harness)."""
import sys, json, numpy as np, pandas as pd, time
from scipy.special import softmax
from worlds import *; from models import *; import calibrators as C; import metrics as M

H = 10          # label maturity delay (steps)
R = 50          # refit period (steps)


def online_probs(Lall, yall, off, cal, mode, W=600, HL=400, delay=H, peek=0, min_n=300):
    """Lall/yall: logits & labels for [val | hold] (off = len(val)); returns probs for hold rows."""
    n = len(Lall) - off; P = np.zeros((n, Lall.shape[1])); Ts = []
    for t0 in range(0, n, R):
        ta = off + t0                                     # absolute index of first row served by this fit
        hi = ta - delay + 1 + peek                         # rows s < hi are used (s <= ta-delay [+peek])
        lo = 0 if mode in ("expanding", "decay") else max(0, hi - W)
        hi = min(hi, len(Lall)); idx = np.arange(lo, hi)
        w = None
        if mode == "decay": w = 0.5 ** ((hi - 1 - idx) / HL)
        f = C.fit_apply(cal, Lall[idx], yall[idx], w)
        blk = slice(t0, min(n, t0 + R)); P[blk] = f(Lall[off + blk.start: off + blk.stop])
        Ts.append(getattr(f, "T", np.nan))
    return P


def static_probs(Lc, yc, Lall, off, cal):
    f = C.fit_apply(cal, Lc, yc); return f(Lall[off:]), f(Lall[:off])


def choose_tau(Pv, yv):
    best, bt = -1e9, 0.0
    for tau in np.linspace(0.34, 0.9, 29):
        a = M.actions(Pv, Pv.max(1) >= tau); u = M.utility(a, yv).sum()
        if u > best: best, bt = u, tau
    return bt


def variants(grid):
    v = [("static", None, {})]
    for W in grid["W"]: v.append(("window", f"W{W}", dict(mode="window", W=W)))
    v.append(("expanding", "all", dict(mode="expanding")))
    for hl in grid["HL"]: v.append(("decay", f"HL{hl}", dict(mode="decay", HL=hl)))
    return v


def run(seed, mag, grid, cals=("temperature", "beta", "isotonic"), kinds=("lr", "gbm"), scenarios=SCENARIOS, leaky=True):
    rows, roll = [], []
    for sc in scenarios:
        Wd = make_world(seed, sc, mag); s = Wd["sl"]; X, y = Wd["x"], Wd["y"]; on = Wd["onset_rel"]
        for kind in kinds:
            base = Base(seed=seed, kind=kind, n_ens=2).fit(X[s["train"]], y[s["train"]])
            Lc = base.logits(X[s["cal"]]); yc = y[s["cal"]]
            Lall = base.logits(np.vstack([X[s["val"]], X[s["hold"]]])); yall = np.r_[y[s["val"]], y[s["hold"]]]
            off = N_VAL; yh = yall[off:]
            for cal in cals:
                Ph0, Pv0 = static_probs(Lc, yc, Lall, off, cal); tau = choose_tau(Pv0, yall[:off])
                vs = variants(grid) + ([("leak_h0", "beta_W", dict(mode="window", W=grid["W"][0], delay=1)),
                                        ("leak_peek", "beta_W", dict(mode="window", W=grid["W"][0], delay=1, peek=R))] if leaky else [])
                for vn, vp, kw in vs:
                    P = Ph0 if vn == "static" else online_probs(Lall, yall, off, cal, **kw)
                    acc_ = P.max(1) >= tau; a = M.actions(P, acc_); a_na = M.actions(P)
                    for ph, sl_ in (("pre", slice(0, on)), ("post", slice(on, None))):
                        r = dict(seed=seed, scenario=sc, base=kind, cal=cal, variant=vn, param=vp, phase=ph,
                                 **M.summary(P[sl_], yh[sl_]), turnover=M.turnover(a[sl_]), turnover_noabst=M.turnover(a_na[sl_]),
                                 abstain=float(1 - acc_[sl_].mean()), utility=float(M.utility(a[sl_], yh[sl_]).mean()),
                                 tau=tau)
                        rows.append(r)
                    if vp in (None, f"W{grid['W'][0]}", "all", f"HL{grid['HL'][0]}") or vn.startswith("leak"):
                        for k0 in range(0, len(P) - 499, 500):
                            roll.append(dict(seed=seed, scenario=sc, base=kind, cal=cal, variant=vn, param=vp, win=k0 // 500,
                                             ece=M.ece(P[k0:k0 + 500], yh[k0:k0 + 500]), brier=M.brier(P[k0:k0 + 500], yh[k0:k0 + 500]),
                                             cwm=M.false_conf(P[k0:k0 + 500], yh[k0:k0 + 500])[1]))
    return rows, roll


if __name__ == "__main__":
    a, b = map(int, sys.argv[1].split("-")); mag = float(sys.argv[2]); out = sys.argv[3]
    grid = json.loads(sys.argv[4]); leaky = len(sys.argv) > 5 and sys.argv[5] == "leaky"
    RR, RL = [], []; t0 = time.time()
    for sd in range(a, b):
        r, l = run(sd, mag, grid, leaky=leaky); RR += r; RL += l; print("seed", sd, round(time.time() - t0), flush=True)
    pd.DataFrame(RR).to_csv(out + "_online.csv", index=False); pd.DataFrame(RL).to_csv(out + "_rolling.csv", index=False)
