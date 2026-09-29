"""Tuning round 2: one pre-registered grid extension for methods whose round-1 optimum sat on a grid
edge. Tuning seeds only. Merges with round-1 rows and writes ../results/tuned_params.json."""
import json, csv, time
import numpy as np
import tune as T, registry as G
from registry import grid

EXT = {
 "CtxOracle": grid(eta=[3, 5, 10, 20], n0=[10, 20, 30, 60]),
 "CtxLag": grid(eta=[3, 5, 10, 20], n0=[10, 20, 30, 60]),
 "CtxNoisy": grid(eta=[3, 5, 10, 20], n0=[10, 20, 30, 60]),
 "DiscFreeze": grid(eta=[30, 60, 100], gamma=[0.95, 0.97, 0.98]),
 "DiscAmnesty": grid(eta=[30, 60, 100], gamma=[0.97, 0.98, 0.99]),
 "SleepHedge": grid(eta=[100, 200, 400]),
 "BMA": grid(kappa=[150, 300, 600], lam=[0.9, 0.95, 0.97], opt=[0.03, 0.06, 0.1]),
 "EWMA": grid(a=[0.03, 0.05, 0.08], beta=[100, 200, 400]),
 "FixedShare": grid(eta=[3, 5, 10], alpha=[0.0005, 0.001, 0.002]),
 "HedgePlain": grid(eta=[30, 100, 300]),
 "DUCB": grid(c=[0.2, 0.5, 1.0], gamma=[0.9, 0.95, 0.98]),
 "EWMA_bounded": grid(a=[0.02, 0.05], beta=[100, 200, 400], floor=[0.02, 0.05, 0.1]),
 "Static": grid(C=[100, 150], kappa=[60, 150, 400]),
 "SH_bounded": grid(eta=[3, 10, 30], B=[4.0, 6.0, 10.0], floor=[0.0, 0.02, 0.05]),
 "SleepEXP3": grid(gamma=[0.1, 0.2, 0.3], eta=[0.05, 0.1, 0.2]),
}
DIV = {"DivEWMA": grid(tau=[0.1, 0.2, 0.3, 0.5, 0.7]), "DivSH": grid(tau=[0.1, 0.2, 0.3, 0.5, 0.7])}

if __name__ == "__main__":
    t0 = time.time()
    rows = []
    with open(T.OUT + "tuning_raw.csv") as f:
        r = csv.reader(f); next(r)
        for m, hp, sc, sd, reg, rew in r:
            if m in DIV:
                continue          # Div rows re-done with the new base parameters
            rows.append((m, hp, sc, int(sd), float(reg), float(rew)))
    rows += T.tune(list(EXT), EXT)
    agg, best = T.summarize(rows)
    G.BASE_HP["EWMA"] = json.loads(best["EWMA"][1]); G.BASE_HP["SleepHedge"] = json.loads(best["SleepHedge"][1])
    T.BASE = {"EWMA": G.BASE_HP["EWMA"], "SleepHedge": G.BASE_HP["SleepHedge"]}
    rows += T.tune(list(DIV), DIV)
    agg, best = T.summarize(rows)
    with open(T.OUT + "tuning_raw_round2.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["method", "hp", "scenario", "seed", "regret", "reward"]); w.writerows(rows)
    tuned, edges = {}, {}
    full_grid = {m: list(G.REG[m][1]) + EXT.get(m, []) + DIV.get(m, []) for m in G.REG}
    for meth, (pr, hp) in best.items():
        hp = json.loads(hp)
        tuned[meth] = {"hp": hp, "pooled_tuning_regret": pr}
        flags = []
        for k in hp:
            vals = sorted({g[k] for g in full_grid[meth]})
            if len(vals) > 1 and hp[k] in (vals[0], vals[-1]):
                flags.append(f"{k}={hp[k]}({'min' if hp[k]==vals[0] else 'max'})")
        edges[meth] = flags
    tuned["_base_for_div"] = T.BASE
    tuned["_grid_edge_flags"] = edges
    json.dump(tuned, open(T.OUT + "tuned_params.json", "w"), indent=1)
    print("done", round(time.time() - t0), "s")
    for m, v in sorted(best.items(), key=lambda kv: kv[1][0]):
        print(f"{m:14s} {v[0]:.5f} {v[1]} edge={edges[m]}")
