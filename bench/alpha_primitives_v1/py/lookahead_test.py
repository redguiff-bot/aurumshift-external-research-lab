"""Empirical forward-safety test: signal at rows <= T computed on data truncated at T must equal the full-data signal. Any difference => LOOKAHEAD_RISK."""
import json, sys, numpy as np, pandas as pd, lib, primitives as pr
assets = [a for a in lib.CORE if __import__("os").path.exists(f"{lib.D}/{a}_metrics5m.parquet")]
P = lib.load_panel(assets); res = {}
rng = np.random.default_rng(7); cuts = sorted(rng.choice(np.arange(3000, len(lib.IDX) - 5000), 6, replace=False))
for n in pr.REG:
    worst = 0.0; nchk = 0
    for H in ([4, 24] if n == "P13_SEASON_HOD" else [None]):
        full = pr.signal(n, P, H=H)
        for T in cuts:
            Pt = {k: v.iloc[:T + 1] for k, v in P.items()}
            st = pr.signal(n, Pt, H=H)
            a = full.iloc[T - 300:T + 1]; b = st.iloc[T - 300:T + 1]
            both = a.notna() & b.notna(); mism = (a.notna() != b.notna()).values.sum()
            d = float((a - b).where(both).abs().max().max()) if both.values.any() else 0.0
            worst = max(worst, d if d == d else 0.0); nchk += int(both.values.sum()) 
            if mism: worst = max(worst, 1.0)
    res[n] = dict(max_abs_diff=worst, cells_compared=nchk, verdict="PASS" if worst < 1e-9 else "FAIL")
    print(n, res[n], flush=True)
# negative control: a deliberately leaky signal MUST fail
leak = lambda P_: np.log(P_["c"].shift(-1) / P_["c"])
full = leak(P); worst = 0.0
for T in cuts:
    Pt = {k: v.iloc[:T + 1] for k, v in P.items()}; a = full.iloc[T - 300:T + 1]; b = leak(Pt).iloc[T - 300:T + 1]
    worst = max(worst, float(((a - b).abs().where(a.notna() & b.notna())).max().max()), 1.0 if (a.notna() != b.notna()).values.any() else 0.0)
res["CONTROL_LEAK_shift(-1)"] = dict(max_abs_diff=worst, verdict="FAIL (expected: test detects lookahead)" if worst >= 1e-9 else "PASS (test is BLIND - bug)")
print(res["CONTROL_LEAK_shift(-1)"])
json.dump(res, open("../results/lookahead_test.json", "w"), indent=1)
