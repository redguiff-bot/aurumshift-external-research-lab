"""Forgetting experiments: F1 snapshot retention, F2 relearning savings,
F3 long-run state growth, F4 model-seed variance."""
import sys, json, pickle, time; sys.path.insert(0, 'src')
import numpy as np
from multiprocessing import Pool
import harness as H, registry as REG
from streams import make_alternating, regime_test_set

best = json.load(open("results/tune.json"))["best"]
NAMES = list(REG.R)


def eval_snapshot(model, X, s, p, task):
    pr = np.array([model.predict(x) for x in X])
    if task == "reg":
        return float(((pr - s) ** 2).mean())
    class _S: pass
    S = _S(); S.p_true = p
    return float(H.excess(S, task, pr).mean())


def f1(job):
    name, seed = job
    task = REG.R[name]["task"]
    S = make_alternating(seed, "AB", 1500)
    y = H.target(S, task)
    m = REG.build(name, best[name]["params"], seed)
    preds = np.zeros(S.T)
    H.run(m, S, task, 0, 1500, preds)
    XA, sA, pA = regime_test_set(S, "A"); XB, sB, pB = regime_test_set(S, "B")
    snap0 = pickle.loads(pickle.dumps(m))
    eA0 = eval_snapshot(snap0, XA, sA, pA, task)
    H.run(m, S, task, 1500, 3000, preds)
    snap1 = pickle.loads(pickle.dumps(m))
    return dict(model=name, seed=seed, eA0=eA0,
                eA1=eval_snapshot(snap1, XA, sA, pA, task),
                eB1=eval_snapshot(snap1, XB, sB, pB, task),
                eA_null=eval_snapshot(REG.build("null_" + task, {}, 0), XA, sA, pA, task))


def f2(job):
    name, seed = job
    task = REG.R[name]["task"]
    S = make_alternating(seed, "ABABAB", 1000)
    m = REG.build(name, best[name]["params"], seed)
    preds = H.run(m, S, task)
    e = H.excess(S, task, preds)
    win = lambda c: float(e[c:c + 200].mean())
    out = dict(model=name, seed=seed, novel=win(1000),
               returns=[win(3000), win(5000)], a_returns=[win(2000), win(4000)],
               meta=m.meta(), n_recalls=getattr(m, "n_recalls", 0))
    return out


def f3(job):
    name, seed = job
    task = REG.R[name]["task"]
    S = make_alternating(seed, "AB" * 5, 2000)
    m = REG.build(name, best[name]["params"], seed)
    marks = (1000, 2000, 5000, 10000, 20000)
    st, tm = {}, {}
    import time as _t
    t0 = _t.perf_counter()
    def cb(t, mm):
        if t + 1 in marks:
            st[t + 1] = H.state_bytes(mm); tm[t + 1] = _t.perf_counter() - t0
    H.run(m, S, task, on_step=cb)
    return dict(model=name, seed=seed, state=st, elapsed=tm)


def f4(job):
    name, seed, mseed = job
    task = REG.R[name]["task"]
    from streams import make_stream
    S = make_stream("recurring", seed, 2.0)
    m = REG.build(name, best[name]["params"], mseed)
    e = H.excess(S, task, H.run(m, S, task))
    return dict(model=name, seed=seed, mseed=mseed, overall=float(e[500:].mean()))


if __name__ == "__main__":
    t0 = time.time()
    with Pool(4) as p:
        out = {}
        out["f1"] = p.map(f1, [(n, s) for n in NAMES for s in range(20)], chunksize=1)
        print("f1", time.time() - t0, flush=True)
        out["f2"] = p.map(f2, [(n, s) for n in NAMES for s in range(20)], chunksize=1)
        print("f2", time.time() - t0, flush=True)
        out["f3"] = p.map(f3, [(n, s) for n in NAMES for s in range(3)], chunksize=1)
        print("f3", time.time() - t0, flush=True)
        stoch = ["river_arf_reg", "river_arf_clf", "river_adaboost_clf"]
        out["f4"] = p.map(f4, [(n, s, ms) for n in stoch for s in range(5) for ms in range(5)], chunksize=1)
    json.dump(out, open("results/forgetting.json", "w"))
    print("done", time.time() - t0)
