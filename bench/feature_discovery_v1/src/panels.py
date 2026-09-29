import numpy as np, pandas as pd
from data import load
from features import build, PRIMS
from pipeline import Panel, PROTO

MK = PROTO["markets"]

def real_panel():
    frames = {s: build(load(s)) for s in MK["discovery"] + MK["unseen"]}
    common = None
    for f in frames.values(): common = set(f._t) if common is None else common & set(f._t)
    common = sorted(common)
    names = MK["discovery"] + MK["unseen"]; prims = list(PRIMS)
    P = np.stack([frames[s].set_index("_t").loc[common, prims].values for s in names], 1)
    y = np.stack([frames[s].set_index("_t").loc[common, "y"].values for s in names], 1)
    t = np.array(common)
    return Panel(P, y, prims, names, list(range(len(MK["discovery"])))), t

def null_panel(panel, seed):
    """Null: circularly shift each market's target by a random offset >= 25% of T (keeps y marginal + dynamics, breaks feature-target link)."""
    rng = np.random.default_rng(seed); T = panel.y.shape[0]; y = panel.y.copy()
    for m in range(y.shape[1]): y[:, m] = np.roll(y[:, m], int(rng.integers(T // 4, 3 * T // 4)))
    return Panel(panel.P, y, panel.prims, panel.markets, panel.disc)

PLANTED = {"f0": ("prim", "f0"), "f1*f2": ("prod", "f1*f2"), "f3*|f4|": ("gate", "f3*|f4|")}

def synth_panel(seed, T=9000, M=10, n_disc=6, p=16, beta=0.055):
    """Known-truth generator. y = b*f0 + b*f1*f2 + b*f3*|f4| + s_m*b*f5 + noise. f5's sign flips by market (non-invariant).
    f6 = f0 + noise (redundant proxy). f7..f15 pure noise. Features: correlated t(6) AR(1). Returns panel + planted term arrays."""
    rng = np.random.default_rng(seed); prims = [f"f{i}" for i in range(p)]
    L = np.linalg.cholesky(0.3 * np.ones((p, p)) + 0.7 * np.eye(p))
    P = np.zeros((T, M, p)); y = np.zeros((T, M)); terms = {k: np.zeros((T, M)) for k in PLANTED}
    for m in range(M):
        e = rng.standard_t(6, (T, p)) / np.sqrt(6 / 4); X = np.zeros((T, p))
        for t in range(1, T): X[t] = 0.5 * X[t - 1] + np.sqrt(1 - 0.25) * e[t]
        X = X @ L.T
        X[:, 6] = X[:, 0] + 0.3 * rng.standard_normal(T)
        X = np.clip((X - X.mean(0)) / X.std(0), -6, 6)
        s = 1.0 if m % 2 == 0 else -1.0
        strength = beta * (0.7 + 0.6 * rng.random())
        terms["f0"][:, m] = X[:, 0]; terms["f1*f2"][:, m] = X[:, 1] * X[:, 2]; terms["f3*|f4|"][:, m] = X[:, 3] * np.abs(X[:, 4])
        y[:, m] = strength * (X[:, 0] + X[:, 1] * X[:, 2] + X[:, 3] * np.abs(X[:, 4]) + s * X[:, 5]) + rng.standard_t(5, T) / np.sqrt(5 / 3)
        P[:, m, :] = X
    return Panel(P, np.clip(y, -6, 6), prims, [f"S{i}" for i in range(M)], list(range(n_disc)), neff_div=1.0), terms
