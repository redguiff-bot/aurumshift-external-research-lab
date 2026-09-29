"""DESCRIPTIVE parameter sensitivity on the held-out generators (5 seeds).  Results NEVER feed back into selected parameters (frozen).
Usage: python sensitivity.py <A|B|C|C2|D> [--seeds 5] [--workers 4]"""
import json, os, sys, itertools, argparse, time
from multiprocessing import Pool
from runner import make_scenario, make_policy, run_one
from scenarios_heldout import HELDOUT_NAMES
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROT = json.load(open(os.path.join(ROOT, "configs", "protocol.json")))
def sel(k): return json.load(open(os.path.join(ROOT, "configs", f"selected_{k}.json")))["spec"]
def grids(p):
    g = {}
    if p == "A":
        for f in (0.0, 0.05, 0.10, 0.20): g[f"A|floor{f}"] = dict(kind="A_floor", floor=f)
        g["A|altcls"] = dict(kind="A_altcls")
        g["A|w_flat"] = dict(kind="A_w", weights=[1, 1, 1, 1], tag="A_wflat")
        g["A|w_steep"] = dict(kind="A_w", weights=[2.0, 1.0, 0.5, 0.25], tag="A_wsteep")
    elif p == "B":
        b = sel("B")
        for gm, S in itertools.product(PROT["search_spaces"]["B"]["gamma"], [25, 50, 100]):
            g[f"B|g{gm}|S{S}|M{b['M']}"] = dict(b, gamma=gm, S=S)
        for M in (1, 4, 16): g[f"B|g{b['gamma']}|S{b['S']}|M{M}"] = dict(b, M=M)
        for S in (10, 200): g[f"B|g{b['gamma']}|S{S}|M{b['M']}|BEYOND_GRID"] = dict(b, S=S)
    elif p == "C":
        c = sel("C")
        for f, e in itertools.product([0.05, 0.1, 0.3], [0.05, 0.1, 0.2]): g[f"C|{c['algo']}|f{f}|e{e}"] = dict(c, fading=f, eps=e)
        g["C|ucb_ew|f0.1|d0.5"] = dict(kind="C", algo="ucb_ew", fading=0.1, delta=0.5)
        g["C|ucb_mean|d0.5"] = dict(kind="C", algo="ucb_mean", delta=0.5)
    elif p == "C2":
        c = sel("C2")
        for S, M in itertools.product([25, 50, 100], [1, 4, 16]): g[f"C2|S{S}|M{M}"] = dict(c, guard=[S, M])
        for e in (0.05, 0.1): g[f"C2|S{c['guard'][0]}|M{c['guard'][1]}|e{e}"] = dict(c, eps=e)
    elif p == "D":
        d = sel("D")
        ex = [5, 20, 100] if d["algo"] == "squarecb" else [0.05, 0.2]
        for lr, e, ug in itertools.product([0.01, 0.05, 0.2], ex, [True, False]):
            g[f"D|{d['algo']}|lr{lr}|x{e}|grp{int(ug)}"] = dict(d, lr=lr, expl=e, use_group=ug)
    return g
def job(a):
    lab, spec, scen, seed = a
    try:
        r = run_one(make_scenario("heldout", scen, seed), make_policy(spec, seed)); r["label"] = lab; r["policy_spec"] = spec
    except Exception:
        import traceback; r = dict(label=lab, scenario=scen, seed=seed, error=traceback.format_exc())
    return r
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("policy"); ap.add_argument("--seeds", type=int, default=5); ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    cfg = grids(a.policy)
    jobs = [(l, s, sc, 3000 + i) for l, s in cfg.items() for sc in HELDOUT_NAMES for i in range(a.seeds)]
    t0 = time.time()
    with Pool(a.workers) as p: res = p.map(job, jobs, chunksize=4)
    os.makedirs(os.path.join(ROOT, "results", "sensitivity"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "sensitivity", f"{a.policy}.json"), "x") as f:
        json.dump(dict(note="DESCRIPTIVE sensitivity; not used for selection", configs=cfg, runs=res), f, default=float)
    print(a.policy, len(cfg), "configs", len(res), "runs", sum("error" in r for r in res), "errors", "%.0fs" % (time.time() - t0))
