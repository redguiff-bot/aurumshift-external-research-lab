import csv, json, os, sys, time, itertools
import numpy as np
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(__file__))
import world as W, engine as E, policies as P

ROOT = os.path.dirname(os.path.dirname(__file__))
METRIC_KEYS = None

def run_cell(a):
    """a = dict(scen, seed, split, policy, params, ingest, K, cost_mult, belief, overrides, tag)"""
    w = W.build_world(a["scen"], a["seed"], a["split"], a.get("overrides"))
    pol = P.make(a["policy"], a.get("params"))
    m = E.run(w, pol, a["K"], a["ingest"], a.get("cost_mult", 1.0), a.get("belief", "known"), seed=a["seed"])
    m.pop("_admits", None)
    row = dict(scen=a["scen"], seed=a["seed"], split=a["split"], policy=a["policy"],
               params=json.dumps(a.get("params") or {}, sort_keys=True), ingest=a["ingest"], K=a["K"],
               cost_mult=a.get("cost_mult", 1.0), belief=a.get("belief", "known"), tag=a.get("tag", ""))
    row.update(m)
    return row

def run_many(cells, procs=4, chunk=8):
    with Pool(procs) as p:
        return p.map(run_cell, cells, chunksize=chunk)

def write_csv(rows, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    keys = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=keys); wr.writeheader(); wr.writerows(rows)

def read_csv(path):
    import pandas as pd
    return pd.read_csv(path)
