"""HELD-OUT evaluation (seeds 1..15) with the configs frozen by run_tuning.py.  LOWSNR=1 env -> low-SNR sensitivity (8 seeds, 3 scenarios)."""
import json, os, numpy as np, warnings; warnings.filterwarnings("ignore")
from multiprocessing import Pool
import scenarios as S, harness as H
from models import GRID
TUNED = json.load(open("../results/tuned_config.json")); LOW = bool(os.environ.get("LOWSNR"))
SEEDS = list(range(1, 9)) if LOW else list(range(1, 16)); SCEN = ["abrupt", "recurring", "random_walk"] if LOW else S.NAMES
def job(a):
    (name, kind), sc, seed = a
    st = S.make(sc, seed); r = H.run(st, kind, name, TUNED[f"{name}|{kind}"]["hp"]); d = H.summarise(st, kind, r)
    d.update(model=name, kind=kind, scenario=sc, seed=seed, hash=r["hash"], n_learn=r["n_learn"]); return d
if __name__ == "__main__":
    jobs = [(k, sc, sd) for k in GRID for sc in SCEN for sd in SEEDS]
    with Pool(4) as p: rows = p.map(job, jobs, chunksize=2)
    json.dump(rows, open("../results/main_lowsnr.json" if LOW else "../results/main.json", "w")); print(len(rows), "runs")
