"""POST-HOC diagnostic: is B's backoff the cause of its X1/X5 behaviour?  B variants (frozen gamma,S; M in 1,4,16) on X1, X5, and S5/S9 for reference."""
import json, os
from multiprocessing import Pool
import numpy as np
from runner import make_scenario, make_policy, run_one
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = json.load(open(os.path.join(ROOT, "configs", "selected_B.json")))["spec"]
def job(a):
    split, scen, seed, M = a
    r = run_one(make_scenario(split, scen, seed), make_policy(dict(B, M=M), seed))
    return dict(split=split, scenario=scen, seed=seed, M=M, **{k: r[k] for k in ["info_ratio", "silent_share", "silent_baseline", "silent_excess", "stale_rate", "starvation_rate", "coverage_W"]})
if __name__ == "__main__":
    jobs = [(sp, sc, sd, M) for sp, sc, seeds in (("adversarial", "X1_PERMANENT_SILENCE", range(4000, 4020)), ("adversarial", "X5_FLAKY_HIGH_VALUE", range(4000, 4020)))
            for sd in seeds for M in (1, 4, 16)]
    with Pool(4) as p: res = p.map(job, jobs)
    with open(os.path.join(ROOT, "results", "adversarial", "followup_B_backoff.json"), "x") as f: json.dump(res, f)
    for sc in ("X1_PERMANENT_SILENCE", "X5_FLAKY_HIGH_VALUE"):
        for M in (1, 4, 16):
            rs = [r for r in res if r["scenario"] == sc and r["M"] == M]
            print(sc, "M", M, {k: round(float(np.mean([r[k] for r in rs])), 3) for k in ["info_ratio", "silent_share", "silent_baseline", "stale_rate", "starvation_rate"]})
