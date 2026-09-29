"""IC, block bootstrap (time-aligned across markets), Holm."""
import numpy as np
from scipy.stats import rankdata, norm

BLOCK = 48  # >= 2x the longest target horizon (24)


def rank01(x):
    r = rankdata(x, nan_policy="omit") if np.isnan(x).any() else rankdata(x)
    r = r - r.mean()
    return r / (np.sqrt((r ** 2).sum()) + 1e-12)


def spearman(a, b):
    return float(rank01(a) @ rank01(b))


def pearson(a, b):
    a = a - a.mean(); b = b - b.mean()
    return float(a @ b / (np.sqrt((a @ a) * (b @ b)) + 1e-12))


def block_idx(n, rng, B, block=BLOCK):
    """B x n index matrix of a circular block bootstrap."""
    nb = int(np.ceil(n / block))
    st = rng.integers(0, n, size=(B, nb))
    idx = (st[:, :, None] + np.arange(block)[None, None, :]) % n
    return idx.reshape(B, -1)[:, :n]


def boot_ic(pred_by_mkt, y_by_mkt, B=1000, seed=0, block=BLOCK):
    """pred/y: dict market -> aligned 1-D arrays of equal length (common time grid).
    Returns per-market IC, and bootstrap draws of per-market IC (B x M) sharing time blocks."""
    ms = list(pred_by_mkt)
    n = len(next(iter(pred_by_mkt.values())))
    rng = np.random.default_rng(seed)
    idx = block_idx(n, rng, B, block)
    ic = np.zeros(len(ms)); bt = np.zeros((B, len(ms)))
    for j, m in enumerate(ms):
        p, y = rank01(pred_by_mkt[m]), rank01(y_by_mkt[m])
        ic[j] = p @ y
        pi, yi = p[idx], y[idx]
        pi = pi - pi.mean(1, keepdims=True); yi = yi - yi.mean(1, keepdims=True)
        bt[:, j] = (pi * yi).sum(1) / (np.sqrt((pi ** 2).sum(1) * (yi ** 2).sum(1)) + 1e-12)
    return ms, ic, bt


def boot_p_greater(draws, obs):
    """One-sided p for H0: mean<=0, via centred bootstrap."""
    d = draws - draws.mean() + 0.0
    return float((1 + (d >= obs).sum()) / (len(d) + 1))


def holm(pvals, alpha=0.05):
    p = np.asarray(pvals, float); k = len(p)
    order = np.argsort(p); adj = np.empty(k); run = 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (k - r) * p[i])); adj[i] = run
    return adj


def r2_oos(pred, y, base):
    return 1 - ((y - pred) ** 2).sum() / ((y - base) ** 2).sum()
