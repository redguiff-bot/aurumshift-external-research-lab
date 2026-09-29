"""POST-HOC adversarial runs (seeds 4000-4019) with FROZEN selected parameters.  Usage: python adversarial.py"""
import json, os, time
from multiprocessing import Pool
from runner import make_scenario, make_policy, run_one
from scenarios_adv import ADV_NAMES
from heldout import load_policies
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def job(a):
    scen, seed, pols = a
    sc = make_scenario("adversarial", scen, seed); out = []
    for lab, spec in pols.items():
        try:
            r = run_one(sc, make_policy(spec, seed)); r["label"] = lab
        except Exception:
            import traceback; r = dict(label=lab, scenario=scen, seed=seed, error=traceback.format_exc())
        out.append(r)
    return scen, out
if __name__ == "__main__":
    pols = load_policies(); by = {}
    with Pool(4) as p:
        for scen, out in p.imap_unordered(job, [(s, 4000 + i, pols) for s in ADV_NAMES for i in range(20)]):
            by.setdefault(scen, []).extend(out)
    d = os.path.join(ROOT, "results", "adversarial"); os.makedirs(d, exist_ok=True)
    for s, rs in by.items():
        with open(os.path.join(d, f"{s}.json"), "x") as f: json.dump(dict(scenario=s, runs=rs, note="POST-HOC adversarial; not held-out"), f, default=float)
    print("done", sum(len(v) for v in by.values()), "errors", sum("error" in r for v in by.values() for r in v))
