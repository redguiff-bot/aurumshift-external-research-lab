"""Hyper-parameter selection on TUNING seeds only (100-102).  One config per (model, track) across ALL scenarios (no per-scenario tuning)."""
import json, sys, itertools, numpy as np, warnings; warnings.filterwarnings("ignore")
from multiprocessing import Pool
import scenarios as S, harness as H
from models import GRID
SEEDS = [100, 101, 102]
def job(a):
    (name, kind), i, sc, seed = a
    st = S.make(sc, seed); r = H.run(st, kind, name, GRID[(name, kind)][i], ); d = H.summarise(st, kind, r)
    return dict(model=name, kind=kind, cfg=i, scenario=sc, seed=seed, regret=d["regret"])
if __name__ == "__main__":
    jobs = [(k, i, sc, sd) for k, g in GRID.items() for i in range(len(g)) for sc in S.NAMES for sd in SEEDS]
    with Pool(4) as p: rows = p.map(job, jobs, chunksize=4)
    json.dump(rows, open("../results/tuning_rows.json", "w"))
    best = {}
    for (name, kind), g in GRID.items():
        sc = [(i, np.mean([r["regret"] for r in rows if r["model"] == name and r["kind"] == kind and r["cfg"] == i])) for i in range(len(g))]
        i = min(sc, key=lambda z: z[1])[0]; best[f"{name}|{kind}"] = dict(cfg_index=i, hp=g[i], tuning_regret=dict((str(j), v) for j, v in sc))
    json.dump(best, open("../results/tuned_config.json", "w"), indent=1); print(json.dumps({k: v["hp"] for k, v in best.items()}))
