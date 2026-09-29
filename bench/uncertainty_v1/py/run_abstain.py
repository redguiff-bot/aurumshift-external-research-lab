"""Selective decision quality: abstain (=HOLD) when uncertain; thresholds fixed on VAL only, applied unchanged to held-out."""
import sys, json, numpy as np, pandas as pd
from worlds import *; from models import *; from scipy.special import softmax; import calibrators as C, metrics as M, online as O

CFG = json.load(open(__import__("os").path.join(__import__("os").path.dirname(__file__), "..", "frozen_config.json")))["online"]


def eval_abst(P, y, accept, rng):
    a0 = M.actions(P); u0 = M.utility(a0, y); trade = a0 != 1
    a1 = M.actions(P, accept); u1 = M.utility(a1, y)
    good, bad = trade & (u0 > 0), trade & (u0 < 0)
    ab_rate = 1 - accept[trade].mean() if trade.any() else np.nan
    # random abstention at the same rate on trades (mean over draws)
    rb = []
    for _ in range(20):
        acc_r = np.where(trade, rng.random(len(y)) >= ab_rate, True); rb.append(M.utility(M.actions(P, acc_r), y).sum())
    f0 = M.false_conf(P, y)[1]
    Pc = P.copy(); accepted_wrong_conf = ((P.max(1) >= M.TAU_FC) & (P.argmax(1) != y) & accept & trade).mean()
    return dict(trades=int(trade.sum()), abstain_on_trades=ab_rate, good_retained=(accept[good].mean() if good.any() else np.nan),
                bad_removed=(1 - accept[bad].mean() if bad.any() else np.nan), util_per_trade_before=u0[trade].mean() if trade.any() else np.nan,
                util_per_trade_after=(u1[a1 != 1].mean() if (a1 != 1).any() else np.nan), util_total_before=u0.sum(), util_total_after=u1.sum(),
                util_total_random=float(np.mean(rb)), conf_wrong_trade_mass_before=((P.max(1) >= M.TAU_FC) & (P.argmax(1) != y) & trade).mean(),
                conf_wrong_trade_mass_after=accepted_wrong_conf, turnover_after=M.turnover(a1))


def run(seed, mag, kinds=("lr", "gbm")):
    rows = []; rng = np.random.default_rng(seed)
    for sc in SCENARIOS:
        Wd = make_world(seed, sc, mag); s = Wd["sl"]; X, y = Wd["x"], Wd["y"]; on = Wd["onset_rel"]
        for kind in kinds:
            base = Base(seed=seed, kind=kind, n_ens=5).fit(X[s["train"]], y[s["train"]])
            Lc, yc = base.logits(X[s["cal"]]), y[s["cal"]]
            Xa = np.vstack([X[s["val"]], X[s["hold"]]]); Lall = base.logits(Xa); yall = np.r_[y[s["val"]], y[s["hold"]]]; off = N_VAL
            mi = base.epistemic(Xa)
            Ps_h, Ps_v = O.static_probs(Lc, yc, Lall, off, "temperature")
            Po_h = O.online_probs(Lall, yall, off, "temperature", mode="window", W=CFG["window_W"])
            Praw = softmax(Lall, 1)
            yv, yh = yall[:off], yall[off:]
            tau = O.choose_tau(Ps_v, yv)
            trade_v = M.actions(Ps_v) != 1
            rho = 1 - (Ps_v.max(1) >= tau)[trade_v].mean()
            H_ = lambda p: -(p * np.log(p + 1e-12)).sum(1)
            def thr_for(score_v):        # accept if score >= thr, thr set so that val abstain rate on trade rows == rho
                return np.quantile(score_v[trade_v], rho)
            entries = {"conf_static_temp": (Ps_h, Ps_h.max(1) >= tau), "conf_online_temp": (Po_h, Po_h.max(1) >= tau),
                       "raw_msp": (Praw[off:], Praw[off:].max(1) >= thr_for(Praw[:off].max(1))),
                       "neg_entropy_static": (Ps_h, -H_(Ps_h) >= thr_for(-H_(Ps_v))),
                       "neg_epistemic_MI": (Ps_h, -mi[off:] >= thr_for(-mi[:off])),
                       "no_abstention": (Ps_h, np.ones(len(yh), bool))}
            for bud in (0.10, 0.25, 0.40):     # fixed abstention budgets (thresholds = val quantiles on trade rows)
                def th(score_v): return np.quantile(score_v[trade_v], bud)
                entries[f"conf_static_temp@{bud}"] = (Ps_h, Ps_h.max(1) >= th(Ps_v.max(1)))
                entries[f"conf_online_temp@{bud}"] = (Po_h, Po_h.max(1) >= th(Ps_v.max(1)))
                entries[f"raw_msp@{bud}"] = (Praw[off:], Praw[off:].max(1) >= th(Praw[:off].max(1)))
                entries[f"neg_epistemic_MI@{bud}"] = (Ps_h, -mi[off:] >= th(-mi[:off]))
                entries[f"neg_entropy_static@{bud}"] = (Ps_h, -H_(Ps_h) >= th(-H_(Ps_v)))
            for en, (P, acc) in entries.items():
                for ph, sl_ in (("pre", slice(0, on)), ("post", slice(on, None))):
                    rows.append(dict(seed=seed, scenario=sc, base=kind, rule=en, phase=ph, tau=tau, val_abstain_rate=rho,
                                     **eval_abst(P[sl_], yh[sl_], acc[sl_], rng)))
    return rows


if __name__ == "__main__":
    a, b = map(int, sys.argv[1].split("-")); mag = float(sys.argv[2]); out = sys.argv[3]
    R = []
    for sd in range(a, b): R += run(sd, mag); print("seed", sd, flush=True)
    pd.DataFrame(R).to_csv(out + "_abstain.csv", index=False)
