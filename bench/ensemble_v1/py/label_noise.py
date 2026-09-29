"""How good must the regime label be for the context mixture to beat the best baseline by >=10%?
Held-out seeds 1000..1019, CORE, CtxMix(tuned CtxOracle hp) with label flipped w.p. p (uniform other label)."""
import json, csv
import numpy as np
from multiprocessing import Pool
import scenarios as S, runner as R, registry as G, learners as L

T = json.load(open("../results/tuned_params.json"))
SEEDS = list(range(1000, 1020)); PS = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5]

def job(a):
    p, sc, sd = a
    scn = S.make(sc, sd)
    rr = np.random.default_rng(sd * 7 + int(p * 100))
    z = scn["regime"].copy(); f = rr.random(len(z)) < p
    z[f] = rr.integers(0, 4, f.sum()); scn["regime_noisy"] = z
    hp = T["CtxOracle"]["hp"]
    l = L.CtxMix(12, ctx_key="regime_noisy", alpha=0.005, **hp)
    m = R.metrics(scn, R.run(scn, l, "correct", rseed=sd))
    return p, sc, sd, m["regret"]

if __name__ == "__main__":
    tasks = [(p, sc, sd) for p in PS for sc in S.CORE for sd in SEEDS]
    with Pool(4) as pool: rows = pool.map(job, tasks, chunksize=20)
    import gzip
    base = {}
    for line in gzip.open("../results/heldout_runs.jsonl.gz", "rt"):
        m = json.loads(line)
        if m["tag"] == "heldout" and m["mode"] == "correct" and m["method"] in ("WTA", "EWMA") and m["seed"] in SEEDS and m["scenario"] in S.CORE:
            base.setdefault(m["method"], {}).setdefault(m["seed"], []).append(m["regret"])
    pr_b = {k: float(np.mean([np.mean(v) for v in d.values()])) for k, d in base.items()}
    out = []
    for p in PS:
        pr = float(np.mean([r[3] for r in rows if r[0] == p]))
        out.append((p, pr * 1e3, pr / pr_b["WTA"], pr / pr_b["EWMA"]))
    with open("../results/label_noise.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["flip_prob", "PR_x1e3", "ratio_vs_WTA", "ratio_vs_EWMA"]); w.writerows(out)
    print("WTA PR x1e3 (same seeds):", pr_b["WTA"] * 1e3)
    for o in out: print("p=%.2f PR=%.2f  /WTA=%.2f  /EWMA=%.2f" % o)
