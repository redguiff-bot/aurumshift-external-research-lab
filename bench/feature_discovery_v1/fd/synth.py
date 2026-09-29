"""Synthetic falsification arena: known ground truth, realistic-ish low SNR, heteroskedastic noise."""
import numpy as np
from . import expr as E

NAMES = [f"f{i:02d}" for i in range(14)]
PHI = np.array([.98, .95, .9, .8, .7, .95, .9, .6, .9, .5, .97, .85, .7, .92])


def _feat(rng, n, common):
    Z = np.zeros((n, 14)); eps = rng.standard_normal((n, 14))
    for j in range(14):
        e = 0.6 * eps[:, j] + 0.4 * common[:, j % 3] * 1.0
        for t in range(1, n):
            Z[t, j] = PHI[j] * Z[t - 1, j] + np.sqrt(1 - PHI[j] ** 2) * e[t] / 0.72
    Z = (Z - Z.mean(0)) / Z.std(0)
    Z[:, 6] = 0.0  # placeholder for near-duplicate of f00
    return Z


def make_panel(scn, seed, n_tr=6000, n_va=3000, n_ho=4000, m_disc=3, m_unseen=3, r2=0.006):
    rng = np.random.default_rng(seed)
    n = n_tr + n_va + n_ho
    common = rng.standard_normal((n, 3))
    for j in range(3):   # persistent common factors
        for t in range(1, n):
            common[t, j] = 0.9 * common[t - 1, j] + 0.44 * common[t, j]
    common /= common.std(0)
    mk = [f"D{i}" for i in range(m_disc)] + [f"U{i}" for i in range(m_unseen)]
    a = np.sqrt(r2)
    tr, va, ho, truth = {}, {}, {}, {}
    for mi, m in enumerate(mk):
        Z = _feat(rng, n, common)
        Z[:, 6] = Z[:, 0] + 0.15 * rng.standard_normal(n)
        h = np.zeros(n)
        for t in range(1, n):
            h[t] = 0.97 * h[t - 1] + 0.24 * rng.standard_normal()
        noise = np.exp(0.5 * h) * rng.standard_normal(n); noise /= noise.std()
        comps = {"c1_linear": Z[:, 0], "c2_interaction": Z[:, 1] * Z[:, 2] / 1.0,
                 "c3_square": (Z[:, 3] ** 2 - 1) / np.sqrt(2),
                 "c4_market_specific": Z[:, 4] * (1.0 if mi in (0, 1) else 0.0),
                 "c5_decaying": Z[:, 5] * np.clip(1 - (np.arange(n) - n_tr / 2) / (n_tr / 2 + n_va), 0, 1)}
        for k in comps:
            comps[k] = comps[k] / max(comps[k].std(), 1e-9) if k in ("c1_linear", "c2_interaction", "c3_square") else comps[k]
        y = noise.copy()
        if scn == "MIXED":
            for k, c in comps.items():
                y = y + a * c
        y = (y - y.mean()) / y.std()
        sl = {"tr": slice(0, n_tr), "va": slice(n_tr + 168, n_tr + n_va), "ho": slice(n_tr + n_va + 168, n)}
        if m.startswith("D"):
            tr[m] = (Z[sl["tr"]], y[sl["tr"]]); va[m] = (Z[sl["va"]], y[sl["va"]])
        ho[m] = (Z[sl["ho"]], y[sl["ho"]])
        truth[m] = {k: c[sl["ho"]] for k, c in comps.items()}
    return tr, va, ho, truth, [m for m in mk if m.startswith("U")]
