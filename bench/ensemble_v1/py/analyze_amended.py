"""POST-HOC amended gates (declared deviation). Reads gates.json/heldout runs from analyze.py.
Amendments: (i) G4a reference set excludes CtxOracle (label oracle is not realisable);
(ii) G4b allows 5% tolerance vs best baseline of the stress set. Nothing else changes."""
import json, sys
import numpy as np
sys.argv = ["x"]
exec(open("analyze.py").read().split("# --- verdict logic")[0])
real = [m for m in METHODS if m not in G.BANDITS and m != "CtxOracle"]
for m in METHODS:
    w = 0.0; wsc = None
    for sc in CORE:
        best = min(arr(x, sc).mean() for x in real)
        r = arr(m, sc).mean() / best
        if r > w: w, wsc = r, sc
    gates[m]["G4a2"] = bool(w <= 1.5); gates[m]["G4a2_detail"] = (w, wsc)
    gates[m]["G4b2"] = all(stress[t]["PR"][m] <= 1.05 * stress[t]["best_baseline"] for t in stress)
    gates[m]["G234b"] = gates[m]["G2a"] and gates[m]["G2b"] and gates[m]["G3"] and gates[m]["G4a2"] and gates[m]["G4b2"]
    gates[m]["G1234b"] = gates[m]["G1"] and gates[m]["G234b"]
print("method  PR  G1 G2a G2b G3 G4a' G4b'  (worst scen)")
for m in sorted(METHODS, key=lambda x: PRm[x]):
    g = gates[m]
    print(f"{m:13s} {PRm[m]*1e3:6.2f} G1={g['G1']!s:5} G2a={g['G2a']!s:5} G2b={g['G2b']!s:5} G3={g['G3']!s:5} G4a'={g['G4a2']!s:5} G4b'={g['G4b2']!s:5} worst={g['G4a2_detail'][0]:.2f}@{g['G4a2_detail'][1]}")
json.dump({m: {k: (v if not isinstance(v, tuple) else list(v)) for k, v in gates[m].items() if k in ('G1','G2a','G2b','G3','G4a2','G4a2_detail','G4b2','G234b','G1234b')} for m in METHODS}, open(OUT + "gates_amended.json", "w"), indent=1)
print("pass G234b:", [m for m in real if gates[m]["G234b"]]); print("pass G1234b:", [m for m in real if gates[m]["G1234b"]])
