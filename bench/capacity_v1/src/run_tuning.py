"""Phase 1: TUNING (seeds 1000-1005, split=tuning) -> top-3 per policy -> VALIDATION (seeds 2000-2007, split=validation) -> freeze.
Tuning objective (tuning only): macro-mean over scenarios of net_per_avail_slot_hour. K=4. Heldout is never touched here."""
import json, os, sys, hashlib
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import common as C, policies as P, world as W, engine as E

K = 4
SCEN = list(W.SCENARIOS)
TUNE_SEEDS = list(range(1000, 1006)); VAL_SEEDS = list(range(2000, 2008))
POLS = [p for p in P.GRIDS]
OUT = os.path.join(C.ROOT, "results")

def cells(split, seeds, configs):
    out = []
    for (pol, params, ing) in configs:
        for s in SCEN:
            for sd in seeds:
                out.append(dict(scen=s, seed=sd, split=split, policy=pol, params=params, ingest=ing, K=K))
    return out

if __name__ == "__main__":
    configs = [(p, prm, ing) for p in POLS for prm in P.GRIDS[p] for ing in E.INGEST_MODES]
    rows = C.run_many(cells("tuning", TUNE_SEEDS, configs))
    C.write_csv(rows, f"{OUT}/tuning/tuning_runs.csv")
    df = pd.DataFrame(rows)
    df["cfg"] = df.policy + "|" + df.params + "|" + df.ingest
    tune = df.groupby(["cfg", "policy", "params", "ingest", "scen"]).net_per_avail_slot_hour.mean().reset_index()
    tune = tune.groupby(["cfg", "policy", "params", "ingest"]).net_per_avail_slot_hour.mean().reset_index()
    tune.to_csv(f"{OUT}/tuning/tuning_objective.csv", index=False)
    finalists = []
    for p in POLS:
        top = tune[tune.policy == p].sort_values("net_per_avail_slot_hour", ascending=False).head(3)
        for _, r in top.iterrows():
            finalists.append((p, json.loads(r.params), r.ingest))
    vrows = C.run_many(cells("validation", VAL_SEEDS, finalists))
    C.write_csv(vrows, f"{OUT}/validation/validation_runs.csv")
    v = pd.DataFrame(vrows); v["cfg"] = v.policy + "|" + v.params + "|" + v.ingest
    vobj = v.groupby(["cfg", "policy", "params", "ingest", "scen"]).net_per_avail_slot_hour.mean().reset_index()
    vobj = vobj.groupby(["cfg", "policy", "params", "ingest"]).net_per_avail_slot_hour.mean().reset_index()
    vobj.to_csv(f"{OUT}/validation/validation_objective.csv", index=False)
    frozen = {}
    for p in POLS:
        b = vobj[vobj.policy == p].sort_values("net_per_avail_slot_hour", ascending=False).iloc[0]
        frozen[p] = dict(params=json.loads(b.params), ingest_tuned=b.ingest, validation_objective=float(b.net_per_avail_slot_hour))
        # mandatory baselines A-E: primary ingest is RAW (naive, as commonly implemented); tuned ingest reported separately
        if p in ("FIFO", "ROUND_ROBIN", "RANDOM", "EQUAL_QUOTA", "OLDEST_SLOT"):
            frozen[p]["ingest_primary"] = "RAW"
            if p == "OLDEST_SLOT":
                sub = vobj[(vobj.policy == p) & (vobj.ingest == "RAW")]
                if len(sub):
                    frozen[p]["params"] = json.loads(sub.sort_values("net_per_avail_slot_hour", ascending=False).iloc[0].params)
        else:
            frozen[p]["ingest_primary"] = b.ingest
    frozen["ORACLE_GREEDY_UB"] = dict(params={}, ingest_primary="RAW", ingest_tuned="RAW", note="not implementable; upper reference")
    json.dump(frozen, open(f"{C.ROOT}/configs/frozen_params.json", "w"), indent=2, sort_keys=True)
    print(json.dumps(frozen, indent=1))
