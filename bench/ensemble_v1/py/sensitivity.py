"""Hyper-parameter sensitivity on fresh seeds (3000..3007), CORE scenarios, correct semantics.
Reporting only (never used for selection). Output ../results/sensitivity.csv"""
import csv, json
import numpy as np
from multiprocessing import Pool
import scenarios as S, runner as R, registry as G
import tune2

TUNED = json.load(open("../results/tuned_params.json"))
SEEDS = list(range(3000, 3008))
METH = ["SleepHedge", "FixedShare", "DiscFreeze", "EWMA", "BMA", "CtxLag", "CtxNoisy", "WTA"]


def job(a):
    meth, hp, sc, sd = a
    if meth in ("DivEWMA", "DivSH"):
        G.BASE_HP.update(TUNED["_base_for_div"])
    scn = S.make(sc, sd)
    m = R.metrics(scn, R.run(scn, G.REG[meth][0](hp), "correct", rseed=sd))
    return meth, json.dumps(hp, sort_keys=True), sc, sd, m["regret"]

if __name__ == "__main__":
    tasks = []
    for meth in METH:
        grid = {json.dumps(h, sort_keys=True): h for h in list(G.REG[meth][1]) + tune2.EXT.get(meth, [])}
        for h in grid.values():
            for sc in S.CORE:
                for sd in SEEDS:
                    tasks.append((meth, h, sc, sd))
    with Pool(4) as p:
        rows = p.map(job, tasks, chunksize=40)
    agg = {}
    for meth, hp, sc, sd, reg in rows:
        agg.setdefault((meth, hp), {}).setdefault(sc, []).append(reg)
    with open("../results/sensitivity.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["method", "hp", "PR_x1e3"] + S.CORE)
        for (meth, hp), d in sorted(agg.items(), key=lambda kv: (kv[0][0], np.mean([np.mean(v) for v in kv[1].values()]))):
            w.writerow([meth, hp, round(1e3 * np.mean([np.mean(v) for v in d.values()]), 3)] + [round(1e3 * np.mean(d[s]), 2) for s in S.CORE])
    print("done")
