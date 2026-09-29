import sys, json, time; sys.path.insert(0, 'src')
import runner, registry as REG
from streams import SCENARIOS

best = json.load(open("results/tune.json"))["best"]
if __name__ == "__main__":
    t0 = time.time()
    cfg = {"main": (20, 2.0, "tuned"), "lowsnr": (10, 4.0, "tuned"), "default": (10, 2.0, "default")}
    which = sys.argv[1:] or list(cfg)
    for tag in which:
        n, noise, kind = cfg[tag]
        jobs = [(m, best[m]["params"] if kind == "tuned" else v["default"], sc, sd, noise)
                for m, v in REG.R.items() for sc in SCENARIOS for sd in range(n)]
        print(tag, len(jobs), flush=True)
        rows = runner.run_jobs(jobs)
        runner.save(rows, f"results/eval_{tag}")
        print(tag, "done", time.time() - t0, flush=True)
