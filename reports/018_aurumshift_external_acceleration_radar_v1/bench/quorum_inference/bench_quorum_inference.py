"""BENCH Q1 — inférence sur l'espérance nette des candidats QUORUM_ONLY_SUPPRESSED.

MEASURED_BY_THIS_MISSION. Données 100 % synthétiques (aucune donnée AurumShift).

Question : quels composants externes (statsmodels HAC, arch block bootstrap,
confseq betting CS) donnent une inférence valide sur la moyenne d'une suite
temporelle de PnL nets (bps) autocorrélés et à queues épaisses, aux petits N
d'un canari forward, et que coûte le « peeking » opérateur ?

DGP : x_t = mu + e_t, e_t = phi * e_{t-1} + s_t * eta_t, eta_t ~ Student-t(4)
normalisé, s_t = sigma (homo) ou sigma x 3 sur un bloc de 20 % (regime).
Écart-type marginal fixé à SIGMA_MARG bps pour comparer les phi.

Environnement : Python 3.10, numpy<2 (confseq 0.0.11 ne s'installe pas en 3.11
et casse avec numpy 2 : voir BENCHMARKS.md).
Usage : python bench_quorum_inference.py [--quick]
"""
import json
import sys
import time
from multiprocessing import Pool

import numpy as np
from arch.bootstrap import CircularBlockBootstrap, StationaryBootstrap, optimal_block_length
from confseq.betting import betting_ci, betting_cs
from scipy import stats
import statsmodels.api as sm

SIGMA_MARG = 50.0       # bps, écart-type marginal du PnL net par décision
K_CLIP = 300.0          # borne pré-enregistrée pour mapper vers [0,1] (betting CS)
ALPHA = 0.05
B_BOOT = 499
QUICK = "--quick" in sys.argv
REPS = 200 if QUICK else 1000
REPS_CS = 100 if QUICK else 400


def simulate(rng, n, mu, phi, regime):
    eta = rng.standard_t(4, size=n) / np.sqrt(4 / 2)  # var 1
    s = np.ones(n)
    if regime:
        a = rng.integers(0, int(0.8 * n))
        s[a:a + max(1, int(0.2 * n))] = 3.0
        s /= np.sqrt(np.mean(s ** 2))
    innov = SIGMA_MARG * np.sqrt(1 - phi ** 2) * s * eta
    e = np.empty(n)
    e[0] = SIGMA_MARG * s[0] * eta[0]
    for t in range(1, n):
        e[t] = phi * e[t - 1] + innov[t]
    return mu + e


def ci_naive(x):
    n = len(x)
    m, se = x.mean(), x.std(ddof=1) / np.sqrt(n)
    q = stats.t.ppf(1 - ALPHA / 2, n - 1)
    return m - q * se, m + q * se


def ci_hac(x):
    n = len(x)
    lags = int(np.floor(4 * (n / 100) ** (2 / 9)))
    res = sm.OLS(x, np.ones(n)).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    lo, hi = res.conf_int(alpha=ALPHA)[0]
    return lo, hi


def ci_boot(x, kind, seed):
    obl = optimal_block_length(x)
    if kind == "stationary":
        b = max(1.0, float(obl.loc[0, "stationary"]))
        bs = StationaryBootstrap(b, x, seed=seed)
    else:
        b = max(1, int(round(float(obl.loc[0, "circular"]))))
        bs = CircularBlockBootstrap(b, x, seed=seed)
    ci = bs.conf_int(np.mean, reps=B_BOOT, method="percentile", size=1 - ALPHA)
    return float(ci[0, 0]), float(ci[1, 0])


def to_unit(x):
    return (np.clip(x, -K_CLIP, K_CLIP) + K_CLIP) / (2 * K_CLIP)


def from_unit(v):
    return v * 2 * K_CLIP - K_CLIP


def ci_betting(x, anytime):
    u = to_unit(x)
    if anytime:
        l, h = betting_cs(u, alpha=ALPHA, breaks=200)
        return from_unit(l[-1]), from_unit(h[-1])
    l, h = betting_ci(u, alpha=ALPHA, breaks=200)
    return from_unit(l), from_unit(h)


METHODS = {
    "naive_t": lambda x, s: ci_naive(x),
    "hac_newey_west": lambda x, s: ci_hac(x),
    "arch_stationary_bootstrap": lambda x, s: ci_boot(x, "stationary", s),
    "arch_circular_block_bootstrap": lambda x, s: ci_boot(x, "circular", s),
    "confseq_betting_ci_fixed_n": lambda x, s: ci_betting(x, False),
    "confseq_betting_cs_anytime": lambda x, s: ci_betting(x, True),
}
CS_METHODS = {"confseq_betting_ci_fixed_n", "confseq_betting_cs_anytime"}


def clipped_mean(mu, phi, regime):
    rng = np.random.default_rng(999)
    x = np.concatenate([simulate(rng, 2000, mu, phi, regime) for _ in range(200)])
    return float(np.clip(x, -K_CLIP, K_CLIP).mean())


def run_cell(cell):
    n, mu, phi, regime = cell
    out = {}
    mu_clip = clipped_mean(mu, phi, regime)
    for name, f in METHODS.items():
        reps = REPS_CS if name in CS_METHODS else REPS
        target = mu_clip if name in CS_METHODS else mu
        cover = rej = 0
        widths = []
        t0 = time.time()
        for r in range(reps):
            rng = np.random.default_rng([n, int(mu), int(phi * 10), int(regime), r])
            x = simulate(rng, n, mu, phi, regime)
            lo, hi = f(x, r)
            cover += lo <= target <= hi
            rej += (lo > 0) or (hi < 0)
            widths.append(hi - lo)
        out[name] = {
            "reps": reps,
            "coverage": cover / reps,
            "reject_H0_mu0": rej / reps,
            "mean_width_bps": float(np.mean(widths)),
            "sec_per_call": (time.time() - t0) / reps,
        }
    return {"n": n, "mu": mu, "phi": phi, "regime": regime, "results": out}


def run_peeking(args):
    """Taux de faux positifs sous H0 si l'opérateur regarde tous les 10 outcomes."""
    phi, n_max, reps = args
    looks = list(range(20, n_max + 1, 10))
    fp = {"naive_t": 0, "hac_newey_west": 0, "confseq_betting_cs_anytime": 0}
    mu_c = clipped_mean(0.0, phi, False)
    for r in range(reps):
        rng = np.random.default_rng([7, int(phi * 10), r])
        x = simulate(rng, n_max, 0.0, phi, False)
        hit = {k: False for k in fp}
        for n in looks:
            for k, f in (("naive_t", ci_naive), ("hac_newey_west", ci_hac)):
                if not hit[k]:
                    lo, hi = f(x[:n])
                    hit[k] = (lo > 0) or (hi < 0)
        # CS : une seule passe, l'intervalle courant à chaque t
        l, h = betting_cs(to_unit(x), alpha=ALPHA, breaks=200)
        lo_t, hi_t = from_unit(l), from_unit(h)
        idx = np.array(looks) - 1
        hit["confseq_betting_cs_anytime"] = bool(np.any((lo_t[idx] > mu_c) | (hi_t[idx] < mu_c)))
        for k in fp:
            fp[k] += hit[k]
    return {"phi": phi, "n_max": n_max, "looks_every": 10, "reps": reps,
            "familywise_false_positive": {k: v / reps for k, v in fp.items()}}


if __name__ == "__main__":
    t0 = time.time()
    ns = [30, 60, 120, 250, 500]
    cells = [(n, mu, phi, reg) for n in ns for mu in (0.0, 10.0) for phi in (0.0, 0.3, 0.6)
             for reg in (False, True) if not (reg and phi == 0.6)]
    with Pool(4) as p:
        res = p.map(run_cell, cells)
        peek = p.map(run_peeking, [(phi, 500, 100 if QUICK else 300) for phi in (0.0, 0.3)])
    meta = {"label": "MEASURED_BY_THIS_MISSION", "quick": QUICK, "reps": REPS, "reps_cs": REPS_CS,
            "B_boot": B_BOOT, "sigma_marg_bps": SIGMA_MARG, "k_clip_bps": K_CLIP, "alpha": ALPHA,
            "elapsed_sec": time.time() - t0,
            "libs": {"arch": __import__("arch").__version__, "statsmodels": sm.__version__ if hasattr(sm, "__version__") else __import__("statsmodels").__version__,
                     "numpy": np.__version__, "confseq": "0.0.11"}}
    out = {"meta": meta, "cells": res, "peeking": peek}
    path = "results_quick.json" if QUICK else "results.json"
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print("written", path, round(time.time() - t0, 1), "s")
