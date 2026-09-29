"""Determinism/reproducibility: re-execute a random sample of heldout H1 cells and compare trade hashes; serial compute-cost benchmark."""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import common as C, world as W, engine as E, policies as P

fz = json.load(open(f"{C.ROOT}/configs/frozen_params.json"))
h1 = pd.read_csv(f"{C.ROOT}/results/heldout/H1_primary.csv")
samp = h1.sample(300, random_state=1)
bad = 0
for _, r in samp.iterrows():
    w = W.build_world(r.scen, int(r.seed), "heldout")
    m = E.run(w, P.make(r.policy, json.loads(r.params)), int(r.K), r.ingest, seed=int(r.seed))
    bad += m["trade_hash"] != r.trade_hash
print("hash_mismatches", bad, "of", len(samp))
rows = []
for pol in fz:
    ts, sel, n_dec = [], [], 0
    for sd in range(3000, 3005):
        w = W.build_world("S3_chronic", sd, "heldout")
        t0 = time.perf_counter(); m = E.run(w, P.make(pol, fz[pol]["params"]), 4, fz[pol]["ingest_primary"], seed=sd)
        ts.append(time.perf_counter() - t0); sel.append(m["sel_time_s"])
    rows.append(dict(policy=pol, run_ms=1000 * np.mean(ts), select_ms_per_run=1000 * np.mean(sel), select_us_per_step=1e6 * np.mean(sel) / w.W))
out = pd.DataFrame(rows); out.to_csv(f"{C.ROOT}/results/analysis/compute_cost_serial.csv", index=False)
json.dump(dict(hash_mismatches=int(bad), sampled=len(samp)), open(f"{C.ROOT}/results/analysis/determinism_check.json", "w"))
print(out.round(2).to_string())
