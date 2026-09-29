"""Pairwise interaction discovery over ALL feature pairs (no heredity assumption; multiplicity handled by the
shift-null on the max statistic). Controls = screened main effects."""
import itertools
import numpy as np
from . import expr as E
from .screening import gauss


def candidates(mains):
    out = []
    for a, b in itertools.combinations(mains, 2):
        out += [f"mul({a}, {b})", f"mul({a}, sgn({b}))", f"mul({b}, sgn({a}))"]
    return out


def screen(cols_by_mkt, y_by_mkt, pool, controls, rng, top=10, n_null=50, q=0.95, min_shift=500):
    """Partial correlation of each interaction with y given all main effects (Gaussian-copula space),
    pooled over markets; requires same sign in all markets and |r| above the shift-null max quantile."""
    cands = candidates(pool)
    if not cands:
        return []
    per_m, R = [], []
    for m, cols in cols_by_mkt.items():
        Mc = np.column_stack([np.ones(len(y_by_mkt[m]))] + [gauss(cols[k]) for k in controls])
        V = gauss(np.column_stack([E.evaluate(c, cols) + 1e-9 * rng.standard_normal(len(Mc)) for c in cands]))
        gy = gauss(y_by_mkt[m])
        proj = np.linalg.lstsq(Mc, np.column_stack([V, gy]), rcond=None)[0]
        Res = np.column_stack([V, gy]) - Mc @ proj
        Res -= Res.mean(0)
        Res /= (np.linalg.norm(Res, axis=0) + 1e-12)
        per_m.append(Res)
    # pooled r = mean of per-market r; null via circular shift of y-residual in each market
    r_m = np.array([R_[:, :-1].T @ R_[:, -1] for R_ in per_m])   # (M, ncand)
    r = r_m.mean(0)
    nulls = []
    N = per_m[0].shape[0]
    for _ in range(n_null):
        s = int(rng.integers(min_shift, N - min_shift))
        rr = np.mean([R_[:, :-1].T @ np.roll(R_[:, -1], s) for R_ in per_m], axis=0)
        nulls.append(np.abs(rr).max())
    thr = np.quantile(nulls, q)
    same = np.all(np.sign(r_m) == np.sign(r)[None, :], axis=0)
    keep = np.where((np.abs(r) > thr) & same)[0]
    keep = keep[np.argsort(-np.abs(r[keep]))][:top]
    return [(cands[i], float(r[i]), float(thr)) for i in keep]
