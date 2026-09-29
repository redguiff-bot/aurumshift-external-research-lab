"""Held-out evaluation with FROZEN tuned parameters. Usage: python3 heldout.py
Writes ../results/heldout_runs.jsonl.gz (one record per run)."""
import sys, json, gzip, time
from multiprocessing import Pool
import scenarios as S, runner as R, registry as G

OUT = "../results/"
TUNED = json.load(open(OUT + "tuned_params.json"))
HELD = list(range(1000, 1040))
STRESS_SEEDS = list(range(2000, 2020))
STRESS = {"lowsnr": dict(snr=0.5), "highnoise": dict(noise=1.6)}


def job(a):
    meth, scn_name, seed, mode, tag, kw = a
    if meth in ("DivEWMA", "DivSH"):
        G.BASE_HP.update(TUNED["_base_for_div"])
    scn = S.make(scn_name, seed, **kw)
    l = G.REG[meth][0](TUNED[meth]["hp"])
    W = R.run(scn, l, mode, rseed=seed)
    m = R.metrics(scn, W)
    m.update(method=meth, scenario=scn_name, seed=seed, mode=mode, tag=tag)
    return m


if __name__ == "__main__":
    t0 = time.time()
    tasks = []
    for meth in G.REG:
        for sc in S.ALL:
            for sd in HELD:
                tasks.append((meth, sc, sd, "correct", "heldout", {}))
    for meth in G.NAIVE_SUBSET:
        for sc in S.CORE:
            for sd in HELD:
                tasks.append((meth, sc, sd, "naive_zero", "heldout", {}))
    for tag, kw in STRESS.items():
        for meth in G.REG:
            for sc in S.CORE:
                for sd in STRESS_SEEDS:
                    tasks.append((meth, sc, sd, "correct", tag, kw))
    print(len(tasks), "runs", flush=True)
    with Pool(4) as p, gzip.open(OUT + "heldout_runs.jsonl.gz", "wt") as f:
        for i, m in enumerate(p.imap_unordered(job, tasks, chunksize=30)):
            f.write(json.dumps(m) + "\n")
            if i % 5000 == 0:
                print(i, round(time.time() - t0), "s", flush=True)
    print("done", round(time.time() - t0), "s")
