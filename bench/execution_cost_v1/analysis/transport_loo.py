"""Leave-one-series-out test: does a calibrated cost constant / sqrt-law Y transport across venue-asset series?
Target = mean book-walk cost (bps vs mid) at notional N from the live capture (visible depth must cover N in >= 95 % of snapshots)."""
import json, os, sys, numpy as np, pandas as pd
ROOT = os.path.join(os.path.dirname(__file__), ".."); tag = sys.argv[1] if len(sys.argv) > 1 else "live"
E = json.load(open(f"{ROOT}/results/empirical_{tag}.json"))["per_venue_asset"]
rows = []
for N in (1e4, 1e5, 1e6):
    S = []
    for o in E:
        w = o["walk_bps_vs_mid"][str(int(N))]
        if w["coverage"] < 0.95 or w["mean"] is None: continue
        hs = o["spread_bps"]["mean"] / 2; sd = o["sigma_bps_sqrt_s"] * np.sqrt(86400); V = o["Vday_proxy_usd"]
        S.append(dict(key=f'{o["venue"]}-{o["asset"]}', cost=w["mean"], hs=hs, sd=sd, V=V, y=(w["mean"] - hs) / (sd * np.sqrt(N / V))))
    if len(S) < 4: continue
    df = pd.DataFrame(S)
    for i, r in df.iterrows():
        oth = df.drop(i)
        pred_fixed = oth.cost.mean()
        pred_sqrt = r.hs + oth.y.mean() * r.sd * np.sqrt(N / r.V)
        pred_sp = r.hs * (oth.cost.sum() / oth.hs.sum())
        rows.append(dict(N=N, key=r.key, truth=r.cost, fixed=pred_fixed, sqrt=pred_sqrt, spread_prop=pred_sp, half_spread_only=r.hs))
d = pd.DataFrame(rows)
res = {}
for N, g in d.groupby("N"):
    res[str(int(N))] = {m: dict(mean_signed_rel_err=float(((g[m] - g.truth) / g.truth).mean()), median_abs_rel_err=float(((g[m] - g.truth).abs() / g.truth).median()),
                                worst_factor=float(np.max(np.maximum(g[m] / g.truth, g.truth / np.maximum(g[m], 1e-9)))), mae_bps=float((g[m] - g.truth).abs().mean())) for m in ("fixed", "sqrt", "spread_prop", "half_spread_only")} | dict(n_series=int(len(g)))
json.dump(dict(loo=res, rows=rows), open(f"{ROOT}/results/transport_loo_{tag}.json", "w"), indent=1)
for N, r in res.items():
    print(N, r["n_series"], {m: (round(v["median_abs_rel_err"], 2), round(v["worst_factor"], 1)) for m, v in r.items() if m != "n_series"})
