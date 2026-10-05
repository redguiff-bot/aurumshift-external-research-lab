"""LANE A — sensibilité de la largeur de la CS betting à la borne déclarée K (|d|<=K, en unités de sd marginal)."""
import json
import numpy as np
from l2_paired_diff_intervals import gen_series, cs_betting, hac_nw
out = []
for i, (n, mu) in enumerate([(60, 0.0), (60, 0.25), (200, 0.0), (200, 0.25)]):
    d = gen_series(n, mu, 20261005 + i)
    lo, hi, _ = hac_nw(d)
    row = {"n": n, "mu": mu, "hac_width": hi - lo, "max_abs_d": float(np.abs(d).max())}
    for K in (3.0, 4.0, 8.0, 16.0):
        l, u = cs_betting(d, K)
        row[f"cs_K{int(K)}"] = [l, u]
        row[f"cs_K{int(K)}_width_ratio_vs_hac"] = (u - l) / (hi - lo)
        row[f"cs_K{int(K)}_clipped_frac"] = float(np.mean(np.abs(d) > K))
    out.append(row)
json.dump(out, open("l2_cs_bound_sensitivity.json", "w"), indent=1)
for r in out:
    print(r["n"], r["mu"], "max|d| %.2f" % r["max_abs_d"], {k: round(v, 2) for k, v in r.items() if "ratio" in k or "clipped" in k})
