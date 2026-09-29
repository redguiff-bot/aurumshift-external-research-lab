"""Tuning on tuning seeds only. Usage: python3 tune.py [round]  -> ../results/tuned_params.json"""
import sys, json, csv, time
import numpy as np
from multiprocessing import Pool
import scenarios as S, runner as R, registry as G

SEEDS = list(range(0, 6))
OUT = "../results/"


def job(args):
    meth, hp, scn_name, seed = args
    scn = S.make(scn_name, seed)
    if meth in ("DivEWMA", "DivSH"):
        G.BASE_HP.update(BASE)
    l = G.REG[meth][0](hp)
    W = R.run(scn, l, "correct", rseed=seed)
    m = R.metrics(scn, W)
    return meth, json.dumps(hp, sort_keys=True), scn_name, seed, m["regret"], m["reward"]


BASE = {}


def tune(methods, cfg_override=None):
    global BASE
    tasks = []
    for meth in methods:
        grid = (cfg_override or {}).get(meth, G.REG[meth][1])
        for hp in grid:
            for sc in S.CORE:
                for sd in SEEDS:
                    tasks.append((meth, hp, sc, sd))
    with Pool(4, initializer=_init, initargs=(BASE,)) as p:
        rows = p.map(job, tasks, chunksize=40)
    return rows


def _init(base):
    global BASE
    BASE = base


def summarize(rows):
    agg = {}
    for meth, hp, sc, sd, reg, rew in rows:
        agg.setdefault((meth, hp), {}).setdefault(sc, []).append(reg)
    best = {}
    for (meth, hp), d in agg.items():
        pr = float(np.mean([np.mean(v) for v in d.values()]))
        if meth not in best or pr < best[meth][0] - 1e-12:
            best[meth] = (pr, hp)
    return agg, best


if __name__ == "__main__":
    t0 = time.time()
    base_methods = [m for m in G.REG if m not in ("DivEWMA", "DivSH")]
    rows = tune(base_methods)
    agg, best = summarize(rows)
    BASE = {}
    G.BASE_HP["EWMA"] = json.loads(best["EWMA"][1])
    G.BASE_HP["SleepHedge"] = json.loads(best["SleepHedge"][1])
    BASE = {"EWMA": G.BASE_HP["EWMA"], "SleepHedge": G.BASE_HP["SleepHedge"]}
    rows2 = tune(["DivEWMA", "DivSH"])
    rows += rows2
    agg, best = summarize(rows)
    with open(OUT + "tuning_raw.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["method", "hp", "scenario", "seed", "regret", "reward"])
        w.writerows(rows)
    tuned, edges = {}, {}
    for meth, (pr, hp) in best.items():
        hp = json.loads(hp)
        tuned[meth] = {"hp": hp, "pooled_tuning_regret": pr}
        # grid-edge flag
        grid = G.REG[meth][1]
        flags = []
        for k in hp:
            vals = sorted({g[k] for g in grid})
            if len(vals) > 1 and hp[k] in (vals[0], vals[-1]):
                flags.append(f"{k}={hp[k]}({'min' if hp[k]==vals[0] else 'max'})")
        edges[meth] = flags
    tuned["_base_for_div"] = BASE
    tuned["_grid_edge_flags"] = edges
    json.dump(tuned, open(OUT + "tuned_params_round1.json", "w"), indent=1)
    print("done", round(time.time() - t0), "s")
    for m, v in sorted(best.items(), key=lambda kv: kv[1][0]):
        print(f"{m:14s} {v[0]:.5f} {v[1]} edge={edges[m]}")
