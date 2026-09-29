"""Determinism / replay / leakage test-suite."""
import sys, os, json, pickle, subprocess, tempfile, time, hashlib; sys.path.insert(0, 'src')
import numpy as np
import harness as H, registry as REG, models as M
from streams import make_stream

best = json.load(open("results/tune.json"))["best"]
CASES = [("recurring", 0), ("delayed_50", 1)]


def child(mode, extra=(), hashseed="0", threads="1"):
    env = dict(os.environ, PYTHONHASHSEED=hashseed, OMP_NUM_THREADS=threads,
               OPENBLAS_NUM_THREADS=threads, MKL_NUM_THREADS=threads)
    r = subprocess.run([sys.executable, "replay_child.py", mode, *extra],
                       capture_output=True, text=True, env=env, check=True)
    return json.loads(r.stdout.strip().splitlines()[-1])


def run_batched(model, S, task, B=10, shuffle_seed=None):
    """Labels released in blocks of B steps; order inside a block is fixed or shuffled."""
    y = H.target(S, task); preds = np.zeros(S.T); released = -1
    rng = np.random.default_rng(shuffle_seed) if shuffle_seed is not None else None
    for t in range(S.T):
        if t % B == 0:
            ready = [tp for tp in range(released + 1, t - S.delay) if S.avail[tp]]
            released = t - S.delay - 1
            if rng is not None:
                ready = list(rng.permutation(ready))
            for tp in ready:
                model.observe(S.X[tp], y[tp], int(tp), t)
        preds[t] = model.predict(S.X[t])
    return preds


if __name__ == "__main__":
    t0 = time.time(); res = {}
    # R1 same-process repeat
    ref = {}
    r1 = {}
    for n in REG.R:
        task = REG.R[n]["task"]; ok = True
        for sc, sd in CASES:
            S = make_stream(sc, sd)
            h = [H.phash(H.run(REG.build(n, best[n]["params"], sd), S, task)) for _ in range(2)]
            ok &= h[0] == h[1]
        r1[n] = ok
    res["R1_same_process_repeat"] = r1
    print("R1", time.time() - t0, flush=True)
    # R2 cross-process (hash seed / BLAS threads)
    a = child("hashes", hashseed="0", threads="1")
    b = child("hashes", hashseed="12345", threads="1")
    c = child("hashes", hashseed="random", threads="4")
    res["R2_cross_process_pred"] = {n: all(a[k][0] == b[k][0] == c[k][0] for k in a if k.startswith(n + "|")) for n in REG.R}
    res["R2_cross_process_statebytes"] = {n: all(a[k][1] == b[k][1] == c[k][1] for k in a if k.startswith(n + "|")) for n in REG.R}
    print("R2", time.time() - t0, flush=True)
    # R3 checkpoint at t=2000 -> in-process and cross-process restore
    d = tempfile.mkdtemp()
    r3 = {}; full = {}
    for n in REG.R:
        task = REG.R[n]["task"]
        for sc, sd in CASES:
            S = make_stream(sc, sd)
            m = REG.build(n, best[n]["params"], sd)
            pr = np.zeros(S.T)
            H.run(m, S, task, 0, 2000, pr)
            blob = pickle.dumps(m, protocol=4)
            open(f"{d}/{n}|{sc}|{sd}.pkl", "wb").write(blob)
            m2 = pickle.loads(blob)
            pr2 = pr.copy()
            H.run(m2, S, task, 2000, S.T, pr2)
            H.run(m, S, task, 2000, S.T, pr)
            full[f"{n}|{sc}|{sd}"] = (H.phash(pr[2000:]), hashlib.sha256(pickle.dumps(m, protocol=4)).hexdigest()[:16])
            r3.setdefault(n, True)
            r3[n] &= bool(np.array_equal(pr, pr2)) and m2.meta() == m.meta()
    res["R3_checkpoint_restore_inprocess"] = r3
    rs = child("resume", [d], hashseed="777", threads="2")
    res["R3_checkpoint_restore_crossprocess_pred"] = {n: all(rs[k][0] == full[k][0] for k in full if k.startswith(n + "|")) for n in REG.R}
    res["R3_checkpoint_restore_crossprocess_statebytes"] = {n: all(rs[k][1] == full[k][1] for k in full if k.startswith(n + "|")) for n in REG.R}
    print("R3", time.time() - t0, flush=True)
    # R4 leakage canary (+ positive control)
    r4 = {}
    t_cut = 1500
    for n in list(REG.R) + ["LEAKY_POSITIVE_CONTROL"]:
        task = "reg" if n == "LEAKY_POSITIVE_CONTROL" else REG.R[n]["task"]
        ok = True
        for sc, sd in [("abrupt", 0), ("delayed_50", 1), ("missing_random", 2)]:
            S = make_stream(sc, sd)
            y = H.target(S, task).copy(); y2 = y.copy()
            rg = np.random.default_rng(5)
            y2[t_cut + 1:] = rg.standard_normal(len(y2) - t_cut - 1) * 10 if task == "reg" else rg.integers(0, 2, len(y2) - t_cut - 1)
            def mk(yy):
                if n == "LEAKY_POSITIVE_CONTROL":
                    Sx = make_stream(sc, sd); Sx.z = yy
                    return M.Leaky(Sx)
                return REG.build(n, best[n]["params"], sd)
            m1, m2 = mk(y), mk(y2)
            if n == "LEAKY_POSITIVE_CONTROL":
                def stepper(model):
                    out = np.zeros(S.T)
                    def cb(t, mm): pass
                    for t in range(S.T):
                        model.t = t
                        tp = t - 1 - S.delay
                        if tp >= 0 and S.avail[tp]:
                            model.observe(S.X[tp], 0.0, tp, t)
                        out[t] = model.predict(S.X[t])
                    return out
                p1, p2 = stepper(m1), stepper(m2)
            else:
                p1 = H.run(m1, S, task, y=y); p2 = H.run(m2, S, task, y=y2)
            lim = t_cut + 2 + S.delay
            ok &= bool(np.array_equal(p1[:lim], p2[:lim]))
        r4[n] = ok
    res["R4_leakage_canary_pass"] = r4
    print("R4", time.time() - t0, flush=True)
    # R5 label-arrival-order sensitivity (blocks of 10, shuffled vs in-order)
    r5 = {}
    for n in REG.R:
        task = REG.R[n]["task"]; md, dx = [], []
        for sc, sd in [("recurring", 0), ("delayed_50", 1)]:
            S = make_stream(sc, sd)
            p_o = run_batched(REG.build(n, best[n]["params"], sd), S, task)
            p_s = run_batched(REG.build(n, best[n]["params"], sd), S, task, shuffle_seed=3)
            md.append(float(np.abs(p_o - p_s).mean()))
            dx.append(float(H.excess(S, task, p_s)[500:].mean() - H.excess(S, task, p_o)[500:].mean()))
        r5[n] = dict(mean_abs_pred_diff=float(np.mean(md)), delta_excess=float(np.mean(dx)),
                     identical=bool(max(md) == 0.0))
    res["R5_label_order_sensitivity"] = r5
    json.dump(res, open("results/replay.json", "w"), indent=1)
    print("done", time.time() - t0)
