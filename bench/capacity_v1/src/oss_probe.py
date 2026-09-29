"""OBSERVED metadata from PyPI JSON API for candidate reference libraries + executed sanity test of assignment reduction."""
import json, os, sys, urllib.request
import numpy as np
LIBS = ["scipy", "ortools", "pulp", "highspy", "cvxpy", "PyPortfolioOpt", "riskfolio-lib", "skfolio", "mabwiser", "vowpalwabbit", "obp", "river", "simpy", "ciw", "contextualbandits"]
out = {}
for l in LIBS:
    try:
        d = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{l}/json", timeout=20))
        i = d["info"]; ver = i["version"]; up = d["releases"].get(ver, [{}])
        out[l] = dict(version=ver, license=(i.get("license_expression") or i.get("license") or "")[:60], requires_python=i.get("requires_python"),
                      upload=(up[0].get("upload_time") if up else None), summary=i.get("summary"), n_releases=len(d["releases"]))
    except Exception as e:
        out[l] = dict(error=str(e)[:80])
# executed check: with slot-independent weights, optimal assignment of f slots == top-f by weight (scipy linear_sum_assignment)
try:
    from scipy.optimize import linear_sum_assignment
    rng = np.random.default_rng(0); ok = 0; n = 500
    for _ in range(n):
        c, f = rng.integers(3, 12), rng.integers(1, 5)
        f = min(f, c); w = rng.normal(size=c)
        cost = -np.repeat(w[:, None], f, 1)          # candidates x slots
        r, s = linear_sum_assignment(cost)
        ok += set(r) == set(np.argsort(-w)[:f])
    out["_assignment_reduction_check"] = dict(trials=n, matches=int(ok))
except Exception as e:
    out["_assignment_reduction_check"] = dict(error=str(e))
json.dump(out, open(os.path.join(os.path.dirname(__file__), "..", "results", "analysis", "oss_probe.json"), "w"), indent=1)
for k, v in out.items(): print(k, v)
