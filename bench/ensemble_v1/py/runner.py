"""Registry, simulation loop, per-seed metrics, tuning and held-out drivers.
usage: python runner.py tune | heldout | smoke"""
import sys, os, json, itertools, time, gzip, io
import numpy as np, pandas as pd
from multiprocessing import Pool
import env as E
import learners as Ls

HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results")
T = 5000; NB = 100
CLUSTER_IDX = [1, 2, 8, 9]

def grid(**kw):
    keys = list(kw); return [dict(zip(keys, v)) for v in itertools.product(*[kw[k] for k in keys])]

# name -> (factory, grid, kind)
REG = {
    "EQUAL": (lambda S, K, **p: Ls.Equal(S, K), [{}], "baseline"),
    "STATIC": (lambda S, K, **p: Ls.Static(S, K, **p), grid(kappa=[10., 30., 100.]), "baseline"),
    "WTA": (lambda S, K, **p: Ls.WTA(S, K), [{}], "baseline"),
    "EWMA": (lambda S, K, **p: Ls.EWMA(S, K, **p), grid(alpha=[0.01, 0.03, 0.1, 0.3], beta=[5., 20., 60., 200.]), "baseline"),
    "HEDGE_CUM": (lambda S, K, **p: Ls.HedgeCum(S, K, **p), grid(eta=[0.01, 0.03, 0.1, 0.3, 1., 3.]), "candidate"),
    "SLEEP_HEDGE": (lambda S, K, **p: Ls.SleepHedge(S, K, **p), grid(eta=[0.03, 0.1, 0.3, 1., 3., 10.]), "candidate"),
    "EG": (lambda S, K, **p: Ls.EG(S, K, **p), grid(eta=[0.01, 0.03, 0.1, 0.3, 1., 3.]), "candidate"),
    "FIXED_SHARE": (lambda S, K, **p: Ls.SleepHedge(S, K, **p), grid(eta=[0.3, 1., 3., 10.], alpha=[0.01, 0.05, 0.15]), "candidate"),
    "DISC_AWAKE": (lambda S, K, **p: Ls.SleepHedge(S, K, disc="awake", **p), grid(eta=[1., 3., 10.], gamma=[0.9, 0.97, 0.99, 0.998]), "candidate"),
    "DISC_CLOCK": (lambda S, K, **p: Ls.SleepHedge(S, K, disc="clock", **p), grid(eta=[1., 3., 10.], gamma=[0.9, 0.97, 0.99, 0.998]), "candidate"),
    "BMA": (lambda S, K, **p: Ls.BMA(S, K, **p), grid(kappa=[0.03, 0.1, 0.3, 1.0]), "candidate"),
    "MPP": (lambda S, K, **p: Ls.SleepHedge(S, K, alpha=0.01, **p), grid(eta=[1., 3., 10.], mpp=[0.02, 0.1, 0.3]), "candidate"),
    "SLEEP_FLOOR": (lambda S, K, **p: Ls.SleepHedge(S, K, **p), grid(eta=[0.3, 1., 3.], floor=[0.05, 0.2]), "candidate"),
    "CONTEXT_MIX": (lambda S, K, **p: Ls.ContextMix(S, K, **p), grid(eta_g=[0.1, 0.3, 1.], eta_c=[1., 3., 10.]), "candidate"),
    "DIVERSITY": (lambda S, K, **p: Ls.Diversity(S, K, alpha=0.05, **p), grid(eta=[0.3, 1., 3., 10.], theta=[0.5, 1.0]), "candidate"),
    "EXP3": (lambda S, K, **p: Ls.Exp3(S, K, **p), grid(eta=[1., 3., 10.], gamma=[0.02, 0.1]), "bandit"),
    "EPS_GREEDY": (lambda S, K, **p: Ls.EpsGreedy(S, K, **p), grid(eps=[0.05, 0.15], alpha=[0.03, 0.1]), "bandit"),
}
# ablations: (name, base method whose tuned params are reused, overrides)
ABL = {
    "EWMA_INACTIVE_NEG": ("EWMA", dict(inactive_neg=True)),
    "EWMA_MISSING_NEG": ("EWMA", dict(missing_neg=True)),
    "SLEEP_INACTIVE_NEG": ("SLEEP_HEDGE", dict(inactive_neg=True)),
    "SLEEP_MISSING_NEG": ("SLEEP_HEDGE", dict(missing_neg=True)),
    "EG_UNCENTRED": ("EG", dict(centre=False)),
    "SLEEP_UNCENTRED": ("SLEEP_HEDGE", dict(centre=False)),
}
FACT = {k: v[0] for k, v in REG.items()}
FACT.update({"EWMA_INACTIVE_NEG": REG["EWMA"][0], "EWMA_MISSING_NEG": REG["EWMA"][0], "SLEEP_INACTIVE_NEG": REG["SLEEP_HEDGE"][0],
             "SLEEP_MISSING_NEG": REG["SLEEP_HEDGE"][0], "EG_UNCENTRED": REG["EG"][0], "SLEEP_UNCENTRED": REG["SLEEP_HEDGE"][0]})


def prep(W):
    reg = W["regime"]; S, Tt = reg.shape
    enter = np.zeros((S, Tt), bool); enter[:, 1:] = (reg[:, 1:] == 3) & (reg[:, :-1] != 3); occ = np.cumsum(enter, 1)
    rare = reg == 3; W["rare_early"] = (rare & (occ <= 2)).T; W["rare_late"] = (rare & (occ >= 3)).T
    ch = np.zeros((S, Tt), bool); ch[:, 1:] = reg[:, 1:] != reg[:, :-1]
    re_m = np.zeros((S, Tt), bool); pre_m = np.zeros((S, Tt), bool)
    for s in range(S):
        for t in np.flatnonzero(ch[s]):
            if t >= 100 and t + 50 <= Tt: re_m[s, t:t + 50] = True; pre_m[s, t - 100:t] = True
    W["re_m"] = re_m.T; W["pre_m"] = pre_m.T
    W["awake_t"] = np.ascontiguousarray(W["awake"].transpose(1, 0, 2)); W["obs_t"] = np.ascontiguousarray(W["observed"].transpose(1, 0, 2))
    W["p_t"] = np.ascontiguousarray(W["p"].transpose(1, 0, 2)); W["y_t"] = W["y"].T.copy(); W["q_t"] = W["q"].T.copy()
    W["ctx_t"] = W["ctx"].T.astype(np.int64).copy(); W["sd_t"] = np.ascontiguousarray(W["sd"].transpose(1, 0, 2))
    return W


def simulate(W, learner):
    S, Tt, K = W["S"], W["T"], W["K"]; e = np.zeros((Tt, S)); Wt = np.zeros((Tt, S, K), np.float32)
    for t in range(Tt):
        aw, ob, p, y, c = W["awake_t"][t], W["obs_t"][t], W["p_t"][t], W["y_t"][t], W["ctx_t"][t]
        if isinstance(learner, Ls.Oracle): learner.sdt = W["sd_t"][t]
        w = learner.weights(aw, c); wr = learner.report(w)
        yh = np.where(aw.any(1), (w * np.where(aw, p, 0)).sum(1), 0.5)
        e[t] = (yh - W["q_t"][t]) ** 2; Wt[t] = wr
        learner.update(p, y, aw, ob, w, c)
    return e, Wt


def metrics(W, e, Wt):
    T_ = W["T"]; half = T_ // 2; reg = W["regime"].T; M = {}
    M["mse"] = e.mean(0)
    for r in range(4):
        m = reg == r; M[f"mse_r{r}"] = np.where(m.sum(0) > 0, (e * m).sum(0) / np.maximum(m.sum(0), 1), np.nan)
    for nm in ("rare_early", "rare_late", "re_m", "pre_m"):
        m = W[nm]; M[f"mse_{nm}"] = np.where(m.sum(0) > 0, (e * m).sum(0) / np.maximum(m.sum(0), 1), np.nan)
    m = W["rare_late"]; M["spec5_share_rare_late"] = np.where(m.sum(0) > 0, (Wt[:, :, 5] * m).sum(0) / np.maximum(m.sum(0), 1), np.nan)
    M["eff_n"] = (1.0 / np.maximum((Wt ** 2).sum(2), 1e-9)).mean(0); M["max_w"] = Wt.max(2).mean(0)
    M["cluster_share"] = Wt[:, :, CLUSTER_IDX].sum(2).mean(0)
    M["share8_250"] = Wt[half + 200:half + 300, :, 8].mean(0); M["share8_450"] = Wt[half + 400:half + 500, :, 8].mean(0)
    M["mse_new_win"] = e[half:half + 500].mean(0)
    return M


def blocks(e, Wt):
    bs = e.shape[0] // NB; eb = e[:NB * bs].reshape(NB, bs, -1).mean(1).T; wb = Wt[:NB * bs].reshape(NB, bs, *Wt.shape[1:]).mean(1).transpose(1, 0, 2)
    return eb.astype(np.float32), wb.astype(np.float16)


def run_scenario(args):
    scen, seed0, S, cfgs, save_blocks = args
    W = prep(E.make_scenario(scen, S, T, seed0 + hash(scen) % 1000 if False else seed0 + sum(map(ord, scen))))
    rows = []; B = {}
    for (meth, ps, tag) in cfgs:
        params = dict(ps)
        if meth == "ORACLE": L = Ls.Oracle(S, W["K"])
        else: L = FACT[meth](S, W["K"], **params)
        e, Wt = simulate(W, L); M = metrics(W, e, Wt)
        for s in range(S): rows.append(dict(scenario=scen, method=meth, cfg=tag, seed=seed0 + s, **{k: float(v[s]) for k, v in M.items()}))
        if save_blocks: B[f"{meth}"] = blocks(e, Wt)
    return rows, B


def cfg_tag(ps): return json.dumps(ps, sort_keys=True)

def tune(nseeds=10, seed0=100):
    cfgs = [("ORACLE", {}, "{}")]
    for m, (f, g, kind) in REG.items():
        for ps in g: cfgs.append((m, ps, cfg_tag(ps)))
    t0 = time.time(); tasks = [(s, seed0, nseeds, cfgs, False) for s in E.SCENARIOS]
    with Pool(4) as pool: out = pool.map(run_scenario, tasks, chunksize=1)
    df = pd.DataFrame([r for rows, _ in out for r in rows]); df.to_csv(os.path.join(RES, "tuning_raw.csv.gz"), index=False)
    # nrm score per scenario, per (method,cfg); averaged over scenarios
    g = df.groupby(["scenario", "method", "cfg"]).mse.mean().reset_index()
    orc = g[g.method == "ORACLE"].set_index("scenario").mse; eq = g[g.method == "EQUAL"].set_index("scenario").mse
    g["nrm"] = (g.mse - g.scenario.map(orc)) / (g.scenario.map(eq) - g.scenario.map(orc))
    tab = g[g.method != "ORACLE"].groupby(["method", "cfg"]).nrm.agg(["mean", "max"]).reset_index().sort_values(["method", "mean"])
    tab.to_csv(os.path.join(RES, "tuning_table.csv"), index=False)
    best = {m: json.loads(tab[tab.method == m].iloc[0].cfg) for m in REG}
    json.dump(best, open(os.path.join(RES, "tuned_params.json"), "w"), indent=1)
    print("tuning done", round(time.time() - t0), "s"); print(tab.groupby("method").first()[["cfg", "mean", "max"]])


def heldout(nseeds=30, seed0=1000):
    best = json.load(open(os.path.join(RES, "tuned_params.json")))
    cfgs = [("ORACLE", {}, "{}")]
    for m in REG: cfgs.append((m, best[m], "tuned"))
    for a, (base, ov) in ABL.items(): cfgs.append((a, {**best[base], **ov}, "tuned+ablation"))
    # untuned defaults for BMA-as-Bayes (kappa=1) reported through the grid winner; also literature-default SLEEP_HEDGE eta=10 fixed
    cfgs.append(("SLEEP_HEDGE", {"eta": 1.}, "default_eta1")); cfgs.append(("EWMA", {"alpha": 0.03, "beta": 20.}, "default"))
    t0 = time.time(); tasks = [(s, seed0, nseeds, cfgs, True) for s in E.SCENARIOS]
    with Pool(4) as pool: out = pool.map(run_scenario, tasks, chunksize=1)
    df = pd.DataFrame([r for rows, _ in out for r in rows]); df.to_csv(os.path.join(RES, "heldout_raw.csv.gz"), index=False)
    for (scen, _), (rows, B) in zip(zip(E.SCENARIOS, out), out):
        np.savez_compressed(os.path.join(RES, f"blocks_{scen}.npz"), **{f"{k}__e": v[0] for k, v in B.items()}, **{f"{k}__w": v[1] for k, v in B.items()})
    print("heldout done", round(time.time() - t0), "s")

def smoke():
    t0 = time.time(); cfgs = [("ORACLE", {}, "{}")] + [(m, REG[m][1][0], "x") for m in REG]
    rows, _ = run_scenario(("S1_SEMANTICS_GAPS", 5, 4, cfgs, False)); df = pd.DataFrame(rows)
    print(df.groupby("method").mse.mean().sort_values()); print(round(time.time() - t0, 1), "s")

if __name__ == "__main__":
    {"tune": tune, "heldout": heldout, "smoke": smoke}[sys.argv[1]]()
