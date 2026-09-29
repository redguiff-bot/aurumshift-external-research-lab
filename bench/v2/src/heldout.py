"""PHASE B -- full held-out run.  Reads FROZEN selected parameters; writes immutable raw results (open(...,'x')).
Usage: python heldout.py [--seeds 20] [--workers 4]"""
import json, os, sys, time, hashlib, argparse, resource, platform
from multiprocessing import Pool
from runner import make_scenario, make_policy, run_one
from scenarios_heldout import HELDOUT_NAMES
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def load_policies():
    P = {"A": dict(kind="A"), "R": dict(kind="R")}
    for k in ("B", "C", "C2", "D"):
        P[k] = json.load(open(os.path.join(ROOT, "configs", f"selected_{k}.json")))["spec"]
    return P
def job(a):
    scen, seed, pols = a
    sc = make_scenario("heldout", scen, seed)
    out = []
    for lab, spec in pols.items():
        try:
            r = run_one(sc, make_policy(spec, seed)); r["label"] = lab; r["policy_spec"] = spec
        except Exception:
            import traceback; r = dict(label=lab, scenario=scen, seed=seed, error=traceback.format_exc())
        out.append(r)
    return scen, seed, out
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, default=20); ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    pols = load_policies()
    outd = os.path.join(ROOT, "results", "heldout"); os.makedirs(outd, exist_ok=True)
    lock = dict(locked_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), policies=pols,
                selected_file_sha256={k: sha(os.path.join(ROOT, "configs", f"selected_{k}.json")) for k in ("B", "C", "C2", "D")},
                freeze_manifest_sha256=sha(os.path.join(ROOT, "configs", "freeze_manifest.json")),
                protocol_sha256=sha(os.path.join(ROOT, "configs", "protocol.json")),
                heldout_generator_sha256=sha(os.path.join(ROOT, "src", "scenarios_heldout.py")),
                seeds=[3000, 3000 + a.seeds], python=platform.python_version())
    with open(os.path.join(outd, "params_lock.json"), "x") as f: json.dump(lock, f, indent=1)
    jobs = [(s, 3000 + i, pols) for s in HELDOUT_NAMES for i in range(a.seeds)]
    t0 = time.time(); by = {}
    with Pool(a.workers) as p:
        for scen, seed, out in p.imap_unordered(job, jobs, chunksize=1):
            by.setdefault(scen, []).extend(out)
    for scen, rs in by.items():
        with open(os.path.join(outd, f"{scen}.json"), "x") as f:
            json.dump(dict(scenario=scen, runs=rs), f, default=float)
    errs = [r for rs in by.values() for r in rs if "error" in r]
    json.dump(dict(wall_seconds=time.time() - t0, n_runs=sum(len(v) for v in by.values()), n_errors=len(errs),
                   maxrss_mb_parent=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024),
              open(os.path.join(outd, "run_summary.json"), "x"))
    print("done", sum(len(v) for v in by.values()), "runs", len(errs), "errors", "%.0fs" % (time.time() - t0))
