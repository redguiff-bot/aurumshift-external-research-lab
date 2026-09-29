"""HELDOUT execution (pre-registered). Writes once; refuses to overwrite."""
import json, os, sys, hashlib
sys.path.insert(0, os.path.dirname(__file__))
import common as C, policies as P, world as W, engine as E

SCEN = list(W.SCENARIOS)
OUT = os.path.join(C.ROOT, "results", "heldout")
fz = json.load(open(f"{C.ROOT}/configs/frozen_params.json"))
pre = json.load(open(f"{C.ROOT}/configs/prereg.json"))
assert hashlib.sha256(open(f"{C.ROOT}/configs/frozen_params.json", "rb").read()).hexdigest() == pre["frozen_params_sha256"]
POLS = list(fz)

def cfg(p, ing=None, K=4, seeds=range(3000, 3020), tag="H1"):
    return [dict(scen=s, seed=sd, split="heldout", policy=p, params=fz[p]["params"],
                 ingest=ing or fz[p]["ingest_primary"], K=K, tag=tag) for s in SCEN for sd in seeds]

if __name__ == "__main__":
    if os.path.exists(f"{OUT}/H1_primary.csv"):
        sys.exit("heldout already executed; refusing to overwrite")
    h1 = [c for p in POLS for c in cfg(p)]
    C.write_csv(C.run_many(h1), f"{OUT}/H1_primary.csv"); print("H1", len(h1))
    h2 = [c for p in POLS for ing in E.INGEST_MODES for c in cfg(p, ing, seeds=range(3000, 3010), tag="H2")]
    C.write_csv(C.run_many(h2), f"{OUT}/H2_ingest_matrix.csv"); print("H2", len(h2))
    h3 = [c for p in POLS for K in (3, 4, 6, 10) for c in cfg(p, None, K, range(3000, 3010), "H3")]
    C.write_csv(C.run_many(h3), f"{OUT}/H3_capacity_sweep.csv"); print("H3", len(h3))
