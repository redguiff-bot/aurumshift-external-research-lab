"""Power / minimum-detectable-effect: inject a synthetic feature with known partial R2 into the BTC baseline and see how often the SAME gate
(CW p < 0.10/120 [BH-equivalent for a lone true effect among 120 tests] AND NW p<0.05 AND DeltaR2_oos>0) fires. Same n, same OOS scheme."""
import numpy as np, pandas as pd, statsmodels.api as sm
from s3_incremental import *
rng = np.random.default_rng(20260929)
c, v, ex = asset_btc(); r, X, Y = build_target_baseline(c, v, ex, False)
out = {}; THR = 0.10 / 120
for tn in ("ret", "abs", "vol"):
    d = X.join(Y[tn].rename("y")).replace([np.inf, -np.inf], np.nan).dropna()
    Xb = sm.add_constant(d[list(X.columns)], has_constant="add"); res = sm.OLS(d.y.values, Xb.values).fit().resid; e = (res - res.mean()) / res.std()
    out[tn] = {"n": int(len(d))}
    for rho in (0.0025, 0.005, 0.01, 0.02, 0.04):
        hit = 0; reps = 80
        for _ in range(reps):
            w = rng.standard_normal(len(d)); w -= np.dot(w, e) / np.dot(e, e) * e; w /= w.std()
            cc = np.sqrt(rho); fz = cc * e + np.sqrt(1 - cc ** 2) * w
            Xf = Xb.copy(); Xf["f"] = fz
            o = oos(pd.Series(d.y.values, index=d.index), Xb, Xf); b, t, p = nw_p(d.y.values, Xf.values, Xf.shape[1] - 1)
            hit += int(o["cw_p"] < THR and p < 0.05 and o["dr2"] > 0)
        out[tn][str(rho)] = hit / reps; print(tn, rho, hit / reps, flush=True)
jdump(out, "power_btc.json")
