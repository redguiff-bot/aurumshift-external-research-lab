"""LANE A — L2 oracle croisé : tsbootstrap (MIT, ré-implémentation indépendante Politis-White/PPW) vs arch.

Vérifie sur les mêmes séries synthétiques AR(1) phi=0.3 (n=60, 200) :
  - longueur de bloc optimale (stationnaire, circulaire) : arch.optimal_block_length vs tsbootstrap pwsd
  - IC percentile 95 % du bootstrap stationnaire (moyenne), B=2000, seed fixe : arch vs tsbootstrap
  - déterminisme tsbootstrap (même random_state => même IC)
Sortie : l2_oracle_crosscheck.json
"""
import json
import time

import numpy as np

from l2_paired_diff_intervals import gen_series

from arch.bootstrap import StationaryBootstrap, optimal_block_length as arch_obl
from tsbootstrap import StationaryBlock, bootstrap_reduce
from tsbootstrap.block.pwsd import _pwsd_1d

rows = []
for i, (n, mu) in enumerate([(60, 0.0), (60, 0.25), (200, 0.0), (200, 0.25)]):
    d = gen_series(n, mu, 20261005 + i)
    a = arch_obl(d)
    t_sb, t_cb = _pwsd_1d(np.asfortranarray(d.reshape(-1, 1))[:, 0])
    blk = float(a["stationary"].iloc[0])
    t0 = time.perf_counter()
    ci_a = StationaryBootstrap(blk, d, seed=np.random.default_rng(1)).conf_int(np.mean, reps=2000, method="percentile")
    ta = time.perf_counter() - t0

    def ts_ci(seed):
        r = bootstrap_reduce(d, method=StationaryBlock(avg_block_length="auto"), statistic="mean",
                             n_bootstraps=2000, random_state=seed)
        v = np.asarray(getattr(r, "values", None) if getattr(r, "values", None) is not None else getattr(r, "statistics", getattr(r, "replicates", None))).ravel()
        return float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))

    t0 = time.perf_counter()
    try:
        ci_t = ts_ci(1)
        ci_t2 = ts_ci(1)
        err = None
    except Exception as exc:  # noqa: BLE001
        ci_t = ci_t2 = (None, None)
        err = repr(exc)
    tt = time.perf_counter() - t0
    rows.append({
        "n": n, "mu": mu,
        "arch_b_sb": blk, "arch_b_cb": float(a["circular"].iloc[0]),
        "tsb_b_sb": float(t_sb), "tsb_b_cb": float(t_cb),
        "arch_ci": [float(ci_a[0, 0]), float(ci_a[1, 0])], "arch_s": round(ta, 4),
        "tsb_ci": ci_t, "tsb_ci_rerun_identical": ci_t == ci_t2, "tsb_s_two_runs": round(tt, 4), "tsb_error": err,
    })
json.dump(rows, open("l2_oracle_crosscheck.json", "w"), indent=1)
for r in rows:
    print(r)
