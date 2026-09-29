"""Process-level determinism: run (scenario, seed) for every policy in 3 fresh processes with different PYTHONHASHSEED
and compare pick-sequence hashes.  Usage: python determinism.py  (uses frozen selected params)"""
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = r'''
import json, sys
sys.path.insert(0, "src")
from heldout import load_policies
from runner import make_scenario, make_policy, run_one
out = {}
for scen in ["S1_MASSIVE_COLD_START", "S5_PROVIDER_DATA_GAP", "S10_DYNAMIC_POPULATION"]:
    sc = make_scenario("heldout", scen, 3000)
    for lab, spec in load_policies().items():
        out[scen + "|" + lab] = run_one(sc, make_policy(spec, 3000))["seqhash"]
print(json.dumps(out))
'''
res = {}
for hs in ("0", "1", "12345"):
    env = dict(os.environ, PYTHONHASHSEED=hs)
    o = subprocess.run([sys.executable, "-c", CODE], cwd=ROOT, env=env, capture_output=True, text=True)
    res[hs] = json.loads(o.stdout.strip().splitlines()[-1])
keys = res["0"].keys()
report = {k: dict(identical=len({res[h][k] for h in res}) == 1, hashes=[res[h][k] for h in res]) for k in keys}
os.makedirs(os.path.join(ROOT, "results", "determinism"), exist_ok=True)
json.dump(report, open(os.path.join(ROOT, "results", "determinism", "determinism.json"), "w"), indent=1)
print("all identical:", all(v["identical"] for v in report.values()), len(report), "checks")
