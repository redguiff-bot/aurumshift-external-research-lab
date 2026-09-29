"""Prequential (predict-then-learn) harness with delayed / missing feedback, regret vs. the known generating process,
probe-based forgetting, state-size tracking.  Leakage guard: a label is delivered at clock `now` only if its sample index
tau satisfies tau + 1 + delay <= now, asserted on every delivery."""
import time, hashlib, numpy as np
import scenarios as S
from models import build

def _kl(p, q):  # KL(Bern(p)||Bern(q)) vectorised
    q = np.clip(q, 1e-4, 1 - 1e-4); p = np.clip(p, 1e-9, 1 - 1e-9)
    return p * np.log(p / q) + (1 - p) * np.log((1 - p) / (1 - q))

def run(st, kind, name, hp, want_series=True, model=None, stop_at=None, corrupt_after=None, start=0):
    m = model if model is not None else build(name, kind, **hp)
    T = S.T; pred = np.zeros(T); pending = {}; yv = (st.yC if kind == "C" else st.yR).astype(float).copy()
    if corrupt_after is not None: yv[corrupt_after:] = 1e6 if kind == "R" else 1 - yv[corrupt_after:]
    truth_p = st.pC if kind == "C" else st.muR
    Xp, pA, zA = S.probe_truth(st, "A"); _, pB, zB = S.probe_truth(st, "B")
    probes = {}; sizes = {}; n_learn = 0; t_pred = 0.0; t_learn = 0.0; last_upd = []
    for t in range(start, T if stop_at is None else stop_at):
        # deliver labels whose arrival time has come (arrival = tau + 1 + delay)
        tau = t - 1 - st.delay
        if tau >= 0 and not st.missing[tau]:
            assert tau + 1 + st.delay <= t          # no label from the future
            t0 = time.perf_counter(); m.learn(st.X[tau], yv[tau], t); t_learn += time.perf_counter() - t0; n_learn += 1
            last_upd.append(t)
        t0 = time.perf_counter(); pred[t] = m.predict(st.X[t]); t_pred += time.perf_counter() - t0
        if t in st.probe_times:
            pp = np.array([m.predict(x) for x in Xp])
            if kind == "C": probes[t] = (float(_kl(pA, pp).mean()), float(_kl(pB, pp).mean()))
            else: probes[t] = (float(((pp - zA) ** 2).mean()), float(((pp - zB) ** 2).mean()))
        if t in (999, 1999, 3999): sizes[t + 1] = m.state_bytes()
    if stop_at is not None: return pred[start:stop_at], m
    if kind == "C": reg = _kl(truth_p, pred)                    # excess KL vs. generating probability
    else: reg = (pred - truth_p) ** 2                           # excess MSE vs. true conditional mean
    out = dict(pred=pred, regret=reg, probes=probes, sizes=sizes, t_pred_us=1e6 * t_pred / T, t_learn_us=1e6 * t_learn / max(n_learn, 1),
               n_learn=n_learn, last_update=m.last_update, hash=hashlib.sha256(pred.tobytes()).hexdigest()[:16])
    if kind == "C":
        p = np.clip(pred, 1e-4, 1 - 1e-4); out["logloss"] = -(st.yC * np.log(p) + (1 - st.yC) * np.log(1 - p))
        out["acc"] = ((pred > .5) == (st.yC == 1)).astype(float)
    else: out["se"] = (pred - st.yR) ** 2
    return out

def summarise(st, kind, r, horizon=600, win=50):
    """scalar metrics from one run"""
    reg = r["regret"]; N0 = S.N0
    d = dict(regret=float(reg[N0:].mean()), size1000=r["sizes"].get(1000), size4000=r["sizes"].get(4000),
             t_pred_us=r["t_pred_us"], t_learn_us=r["t_learn_us"])
    d["metric"] = float((r["acc"] if kind == "C" else r["se"])[N0:].mean())
    d["logloss"] = float(r["logloss"][N0:].mean()) if kind == "C" else None
    posts, adapt = [], []
    for cp in st.change_points:
        pre = float(reg[max(N0, cp - 300):cp].mean()) if cp > N0 else float(reg[N0:cp].mean()) if cp > N0 else 0.0
        post = float(reg[cp:cp + horizon].mean()); posts.append(post)
        thr = 1.5 * pre + (0.01 if kind == "C" else 0.01)
        roll = np.convolve(reg[cp:cp + horizon + win], np.ones(win) / win, "valid")[:horizon]
        hit = np.where(roll <= thr)[0]; adapt.append(int(hit[0]) if len(hit) else horizon)  # censored at horizon
    d["post_regret"] = posts; d["adapt_steps"] = adapt
    d["probes"] = {str(k): v for k, v in r["probes"].items()}
    return d
