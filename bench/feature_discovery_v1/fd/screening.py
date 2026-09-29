"""MI / conditional MI screening and orthogonalisation (Gaussian-copula CMI + kNN MI)."""
import numpy as np
from scipy.stats import norm, rankdata


def gauss(x):
    """rank -> N(0,1) marginals (Gaussian copula)."""
    x = np.asarray(x, float)
    if x.ndim == 1:
        return norm.ppf((rankdata(x) - 0.5) / len(x))
    return np.column_stack([gauss(x[:, j]) for j in range(x.shape[1])])


def partial_corr(a, b, Z=None):
    if Z is not None and Z.shape[1] > 0:
        Zc = np.column_stack([np.ones(len(a)), Z])
        a = a - Zc @ np.linalg.lstsq(Zc, a, rcond=None)[0]
        b = b - Zc @ np.linalg.lstsq(Zc, b, rcond=None)[0]
    a = a - a.mean(); b = b - b.mean()
    return float(a @ b / (np.sqrt((a @ a) * (b @ b)) + 1e-12))


def cmi_gauss(x, y, Z=None):
    r = np.clip(partial_corr(x, y, Z), -0.999999, 0.999999)
    return -0.5 * np.log(1 - r ** 2)


def shift_null(x, y, Z, rng, n=30, min_shift=500):
    """Null CMI draws by circularly shifting y relative to (x, Z) (keeps autocorrelation)."""
    N = len(y); out = []
    for _ in range(n):
        s = int(rng.integers(min_shift, N - min_shift))
        out.append(cmi_gauss(x, np.roll(y, s), Z))
    return np.array(out)


def knn_mi(X, y, rng, n_neighbors=5, sub=6000):
    from sklearn.feature_selection import mutual_info_regression
    if len(y) > sub:
        i = np.sort(rng.choice(len(y), sub, replace=False)); X, y = X[i], y[i]
    return mutual_info_regression(X, y, n_neighbors=n_neighbors, random_state=int(rng.integers(1 << 30)))


def cmi_forward(G, gy, names, rng, max_k=8, alpha_q=0.95, n_null=30):
    """Greedy conditional-MI forward selection (CMIM-style; each step conditional on selected set);
    stops when best CMI does not beat the shift-null (alpha_q quantile of max-over-candidates null)."""
    sel, order = [], []
    cand = list(range(G.shape[1]))
    while cand and len(sel) < max_k:
        Z = G[:, sel] if sel else None
        sc = np.array([cmi_gauss(G[:, j], gy, Z) for j in cand])
        j = cand[int(sc.argmax())]
        # null of the max over candidates: shift y, recompute max
        nulls = []
        for _ in range(n_null):
            s = int(rng.integers(500, len(gy) - 500)); yy = np.roll(gy, s)
            nulls.append(max(cmi_gauss(G[:, c], yy, Z) for c in cand))
        thr = np.quantile(nulls, alpha_q)
        if sc.max() <= thr:
            break
        sel.append(j); order.append((names[j], float(sc.max()), float(thr))); cand.remove(j)
    return [names[j] for j in sel], order


def orthogonalise(v, B, fit_slice=None):
    """Residualise v on columns of B (with intercept). Returns residual and coef (fit on fit_slice)."""
    Bc = np.column_stack([np.ones(len(v)), B]) if B.shape[1] else np.ones((len(v), 1))
    fs = slice(None) if fit_slice is None else fit_slice
    beta = np.linalg.lstsq(Bc[fs], v[fs], rcond=None)[0]
    return v - Bc @ beta, beta
