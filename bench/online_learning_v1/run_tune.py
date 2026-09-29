"""Hyper-parameter selection on DISJOINT seeds (1000..1007), scenario-averaged.
One config per model, chosen without looking at the evaluation seeds.
Selection criterion: mean over scenarios of mean overall excess (lower=better)."""
import sys, json, time; sys.path.insert(0, 'src')
import numpy as np
import runner, registry as REG
from streams import SCENARIOS

SEEDS = list(range(1000, 1008))
if __name__ == "__main__":
    t0 = time.time()
    jobs = [(n, p, sc, sd, 2.0) for n, v in REG.R.items() for p in v["grid"]
            for sc in SCENARIOS for sd in SEEDS]
    print(len(jobs), "jobs", flush=True)
    rows = runner.run_jobs(jobs)
    table = {}
    for r in rows:
        key = (r["model"], json.dumps(r["params"], sort_keys=True))
        table.setdefault(key, {}).setdefault(r["scenario"], []).append(r["overall"])
    best, full = {}, []
    for (m, pj), d in table.items():
        score = float(np.mean([np.mean(d[s]) for s in SCENARIOS]))
        full.append(dict(model=m, params=json.loads(pj), score=score,
                         per_scenario={s: float(np.mean(d[s])) for s in SCENARIOS}))
        if m not in best or score < best[m]["score"]:
            best[m] = dict(params=json.loads(pj), score=score)
    json.dump(dict(best=best, full=full, seeds=SEEDS), open("results/tune.json", "w"), indent=1)
    for m, b in best.items():
        print(f"{m:26s} {b['params']} {b['score']:.4f}")
    print("done", time.time() - t0)
