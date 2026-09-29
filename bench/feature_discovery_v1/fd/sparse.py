"""Sparse regression + stability selection (Meinshausen & Buhlmann 2010, randomised lasso, block subsampling)."""
import numpy as np
from sklearn.linear_model import lasso_path, LassoCV, Ridge, Lasso

BLOCK_SUB = 336


def _blocks(sizes, block=BLOCK_SUB):
    """list of (start,stop) row blocks over concatenated markets."""
    out, o = [], 0
    for n in sizes:
        for s in range(0, n - block + 1, block):
            out.append((o + s, o + s + block))
        o += n
    return out


def stability_selection(X, y, sizes, rng, B=60, qmax=6, pi=0.7, frac=0.5):
    n, p = X.shape
    blocks = _blocks(sizes)
    amax = np.abs(X.T @ (y - y.mean())).max() / n
    alphas = amax * np.logspace(0, -1.5, 15)
    cnt = np.zeros((p, len(alphas)))
    for _ in range(B):
        pick = rng.choice(len(blocks), int(len(blocks) * frac), replace=False)
        idx = np.concatenate([np.arange(*blocks[i]) for i in pick])
        w = rng.uniform(0.5, 1.0, p)
        _, co, _ = lasso_path(X[idx] * w, y[idx] - y[idx].mean(), alphas=alphas)
        cnt += (co != 0)
    freq = cnt / B
    ok = freq.sum(0) <= qmax
    use = ok if ok.any() else np.arange(len(alphas)) == 0
    stab = freq[:, use].max(1)
    ev = qmax ** 2 / ((2 * pi - 1) * p)   # expected # false selections upper bound (needs exchangeability/shape assumptions)
    return stab, ev


def lasso_fit_val(Xtr, ytr, Xva, yva):
    """Lasso with alpha picked on the validation split (IC), returns model and alpha."""
    from .metrics import spearman
    amax = np.abs(Xtr.T @ (ytr - ytr.mean())).max() / len(ytr)
    best = None
    for a in amax * np.logspace(-0.3, -2.5, 10):
        m = Lasso(alpha=a, max_iter=5000).fit(Xtr, ytr)
        ic = spearman(m.predict(Xva), yva) if np.any(m.coef_ != 0) else -1
        if best is None or ic > best[0]:
            best = (ic, a, m)
    return best[2], best[1]
