import json, os, sys, time, itertools
import numpy as np
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(__file__))
from streams import make_stream, SCENARIOS
import harness as H
import registry as REG

CHECK = (999, 1999, 2999, 3999)


def one(job):
    name, params, scen, seed, noise = job
    task = REG.R[name]["task"]
    S = make_stream(scen, seed, noise)
    model = REG.build(name, params, seed)
    cks = {}
    def cb(t, m):
        if t in CHECK:
            cks[t] = H.state_bytes(m)
    t0 = time.perf_counter()
    preds = H.run(model, S, task, on_step=cb)
    dt = time.perf_counter() - t0
    out = H.summarize(S, task, preds, model, cks)
    out.update(model=name, params=params, scenario=scen, seed=seed, noise=noise,
               task=task, seconds=dt)
    return out


def run_jobs(jobs, procs=4):
    with Pool(procs) as p:
        return p.map(one, jobs, chunksize=1)


def save(rows, path):
    blocks = np.stack([r.pop("blocks") for r in rows])
    np.save(path + ".blocks.npy", blocks)
    with open(path + ".json", "w") as f:
        json.dump(rows, f)
