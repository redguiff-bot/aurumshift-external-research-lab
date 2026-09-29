"""PHASE A -- harness validation only (2-3 seeds).  NOT usable for comparative claims.
Dev (train/validation) scenarios: metrics may be inspected.  Held-out generators on PILOT seeds: only invariants/runtime are read."""
import json, os, sys, time
from multiprocessing import Pool
from runner import make_scenario, make_policy, run_one
from scenarios_heldout import HELDOUT_NAMES
from scenarios_dev import DEV_SPECS
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POL = {"A": dict(kind="A"), "R": dict(kind="R"), "B": dict(kind="B", gamma=0.995, S=50, M=4), "C": dict(kind="C"),
       "C2": dict(kind="C2", guard=[50, 4]), "D": dict(kind="D")}
def job(a):
    split, scen, seed, lab = a
    try:
        r = run_one(make_scenario(split, scen, seed), make_policy(POL[lab], seed)); r["label"] = lab
        return r
    except Exception:
        import traceback; return dict(split=split, scenario=scen, seed=seed, label=lab, error=traceback.format_exc())
if __name__ == "__main__":
    jobs = [(sp, sc, sd, lab) for sp, seeds in (("train", (1000, 1001, 1002)), ("validation", (2000, 2001, 2002)))
            for sc in DEV_SPECS[sp] for sd in seeds for lab in POL]
    jobs += [("pilot", sc, sd, lab) for sc in HELDOUT_NAMES for sd in (9000, 9001, 9002) for lab in POL]
    t0 = time.time()
    with Pool(4) as p: res = p.map(job, jobs, chunksize=3)
    os.makedirs(os.path.join(ROOT, "results", "phaseA"), exist_ok=True)
    json.dump(dict(wall_seconds=time.time() - t0, note="PHASE A harness validation; NOT for comparative claims", runs=res),
              open(os.path.join(ROOT, "results", "phaseA", "phaseA_raw.json"), "w"), default=float)
    errs = [r for r in res if "error" in r]
    bad = [r for r in res if "error" not in r and r["attempts_on_ineligible"] != 0]
    print("runs", len(res), "errors", len(errs), "ineligible_attempts_violations", len(bad), "wall %.0fs" % (time.time() - t0))
    for r in errs[:3]: print(r["label"], r["scenario"], r["error"][-600:])
    # runtime per policy (invariant/cost information only)
    import collections
    c = collections.defaultdict(list)
    for r in res:
        if "error" not in r: c[r["label"]].append(r["policy_seconds"])
    print({k: round(sum(v) / len(v), 2) for k, v in c.items()})
