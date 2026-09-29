"""usage: python run_batch.py {synth|null|real} [procs]   -> results/<mode>/run_<seed>.json (+ lock file written BEFORE held-out eval)"""
import sys, os, json, warnings, time
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from multiprocessing import Pool
import pipeline as pl
from panels import real_panel, null_panel, synth_panel, PLANTED

RES = os.path.join(os.path.dirname(__file__), "..", "results")
J = lambda o: json.dumps(o, default=lambda x: x.item() if hasattr(x, "item") else str(x))

def job(args):
    mode, seed = args
    os.makedirs(f"{RES}/{mode}", exist_ok=True); logf = open(f"{RES}/{mode}/run_{seed}.log", "w")
    def log(m): logf.write(m + "\n"); logf.flush()
    def on_lock(l): open(f"{RES}/{mode}/lock_{seed}.json", "w").write(J(l))
    if mode == "synth":
        pan, terms = synth_panel(seed, T=19000, beta=0.06); extra = {}
    elif mode == "null":
        base, _ = real_panel(); pan = null_panel(base, seed); extra = {}
    else:
        pan, t = real_panel(); extra = dict(t0=int(t[0]), t1=int(t[-1]), T=int(len(t)))
    r = pl.run(pan, seed % 1000, log=log, on_lock=on_lock)
    r["mode"], r["run_seed"], r["extra"], r["access_order"] = mode, seed, extra, pan.access[:12]
    if mode == "synth":   # ground-truth match on TEST segment (evaluation of the *method*, not of markets)
        from pipeline import Cand
        te = pan.sl["test"]; D = pan.disc; match = {}
        # re-evaluate is not possible without objects; matching done from val_vec-free info: use key strings
        match = {k: any(_key_matches(h["key"], k) for h in r["heldout"] if h["stable"] and h["nonredundant"]) for k in ("f1*f2", "f3*|f4|")}
        r["planted_recovered"] = match
    open(f"{RES}/{mode}/run_{seed}.json", "w").write(J(r))
    return seed, r["counts"], r["runtime_s"]

def _key_matches(key, planted):
    """structural match (commutative) on interpretable library keys; symbolic expressions matched in analysis via correlation"""
    k = key.replace(" ", "")
    if planted == "f1*f2": return k in ("prod:(f1*f2)", "prod:(f2*f1)")
    if planted == "f3*|f4|": return k == "gate:(f3*|f4|)"
    return False

if __name__ == "__main__":
    mode = sys.argv[1]; procs = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    P = json.load(open(os.path.join(os.path.dirname(__file__), "..", "configs", "protocol.json")))["seeds"]
    seeds = {"synth": P["synthetic"], "null": P["null"], "real": P["discovery"]}[mode]
    t = time.time()
    with Pool(procs) as p:
        for s, c, rt in p.imap_unordered(job, [(mode, s) for s in seeds]): print(mode, s, c, f"{rt:.0f}s", flush=True)
    print("total", time.time() - t)
