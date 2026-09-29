"""Simulation loop + metrics. mode: 'correct' (missing evidence freezes state) or 'naive_zero'."""
import numpy as np
import scenarios as S
import registry as G


def run(scn, learner, mode="correct", rseed=0):
    T, K = scn["T"], scn["K"]
    st, R, MU = scn["state"], scn["R"], scn["MU"]
    z, zn = scn["regime"], scn["regime_noisy"]
    rng = np.random.default_rng(777 + rseed)
    W = np.zeros((T, K), np.float32)
    for t in range(T):
        exist = st[t] > S.NOT_EXIST
        alloc = st[t] >= S.GAP
        ctx = {"regime": int(z[t]), "regime_noisy": int(zn[t]),
               "regime_lag": int(z[t - 1]) if t else int(z[t]), "rng": rng}
        learner._register(exist)
        w = learner.weights(alloc, ctx)
        W[t] = w
        obs = st[t] == S.OBS
        if mode == "naive_zero":
            r = np.where(obs, R[t], 0.0)
            obs = exist
        else:
            r = R[t]
        learner.update(alloc, obs, r, exist, ctx)
    return W


def metrics(scn, W):
    st, R, MU = scn["state"], scn["R"], scn["MU"]
    T = scn["T"]
    alloc = st >= S.GAP
    Wf = W.astype(float)
    exp_r = (Wf * MU).sum(1)
    real = (Wf * R).sum(1)
    mu_a = np.where(alloc, MU, -np.inf)
    orc = mu_a.max(1)
    best = mu_a.argmax(1)
    nA = alloc.sum(1)
    wb = Wf[np.arange(T), best]
    reg = orc - exp_r
    out = dict(regret=float(reg.mean()), reward=float(real.mean()), exp_reward=float(exp_r.mean()),
               oracle=float(orc.mean()), best_mass=float(wb.mean()),
               starved=float((wb < 0.5 / nA).mean()),
               maxw=float(Wf.max(1).mean()))
    seg = {}
    for name, a, b in scn["segments"]:
        d = dict(regret=float(reg[a:b].mean()), best_mass=float(wb[a:b].mean()))
        for k in scn["targets"]:
            m = alloc[a:b, k]
            d["w_" + S.NAMES[k]] = float(Wf[a:b, k][m].mean()) if m.any() else float("nan")
        seg[name] = d
    out["seg"] = seg
    ev = {}
    # new-expert / recovery timing: rounds (allocated) until trailing-25 mean weight >= 0.25
    def tts(k, t0, thr=0.25, cap=400, win=25):
        idx = np.where(alloc[t0:, k])[0] + t0
        if len(idx) < win:
            return float(cap)
        ws = Wf[idx, k]
        cs = np.cumsum(np.insert(ws, 0, 0.0))
        tr = (cs[win:] - cs[:-win]) / win
        hit = np.where(tr >= thr)[0]
        return float(min(hit[0] + win, cap)) if len(hit) else float(cap)
    if "intro" in scn["events"]:
        k, t0 = scn["events"]["intro"]
        ev["tts_new"] = tts(k, t0)
        idx = np.where(alloc[t0:, k])[0][:100] + t0
        ev["new_w100"] = float(Wf[idx, k].mean()) if len(idx) else float("nan")
    if scn["script"] is not None:
        eps = []
        for a, b in scn["script"]:
            idx = np.where(alloc[a:b, S.RARE])[0][:25] + a
            eps.append(float(Wf[idx, S.RARE].mean()) if len(idx) else float("nan"))
        ev["rare_first25"] = eps
        ev["rare_bestmass_first25"] = [
            float(wb[np.where(alloc[a:b, S.RARE])[0][:25] + a].mean()) for a, b in scn["script"]]
    if scn["name"] == "S7_temp_underperf":
        k = S.LATE
        a, b = T // 2, T // 2 + 150
        pre = float(Wf[a - 100:a, k][alloc[a - 100:a, k]].mean())
        ev["late_pre"] = pre
        tail = np.where(alloc[b:, k])[0] + b
        ws = Wf[tail, k]
        cs = np.cumsum(np.insert(ws, 0, 0.0))
        w10 = 10
        tr = (cs[w10:] - cs[:-w10]) / w10
        hit = np.where(tr >= 0.5 * pre)[0]
        ev["late_recovery"] = float(min(hit[0] + w10, 300)) if len(hit) else 300.0
    out["ev"] = ev
    return out
