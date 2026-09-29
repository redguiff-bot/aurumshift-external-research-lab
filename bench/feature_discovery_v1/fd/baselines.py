"""Baselines: raw primitive ridge, linear sparse (lasso), tree-importance top-k, permutation-importance top-k,
full GBM (non-parsimonious ceiling). Hyper-parameters chosen on validation only; refit on train+val."""
import numpy as np
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from .metrics import spearman
from .sparse import lasso_fit_val

ALPHAS = (1, 10, 100, 1000, 10000, 100000)


def _cat(P, stride=1):
    return (np.vstack([P[m][0][::stride] for m in P]), np.concatenate([P[m][1][::stride] for m in P]))


def _ridge_val(Xtr, ytr, Xva, yva):
    best = max(((spearman(Ridge(alpha=a).fit(Xtr, ytr).predict(Xva), yva), a) for a in ALPHAS))
    return best[1]


def _hgb(seed):
    return HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=150, min_samples_leaf=300,
                                         l2_regularization=10.0, random_state=seed)


def fit_baselines(tr, va, names, seed=0, k=8):
    Xtr, ytr = _cat(tr, 2); Xva, yva = _cat(va, 2)
    Xall, yall = _cat({m: (np.vstack([tr[m][0], va[m][0]]), np.concatenate([tr[m][1], va[m][1]])) for m in tr}, 2)
    out = {}
    a = _ridge_val(Xtr, ytr, Xva, yva)
    out["raw_ridge"] = dict(model=Ridge(alpha=a).fit(Xall, yall), ix=list(range(len(names))), params=len(names))
    lm, la = lasso_fit_val(Xtr, ytr, Xva, yva)
    lm = Lasso(alpha=la, max_iter=5000).fit(Xall, yall)
    out["lasso"] = dict(model=lm, ix=list(range(len(names))), params=int((lm.coef_ != 0).sum()))
    rf = RandomForestRegressor(n_estimators=150, max_depth=6, min_samples_leaf=300, max_features=0.5, n_jobs=4,
                               random_state=seed).fit(Xtr[::2], ytr[::2])
    top = list(np.argsort(-rf.feature_importances_)[:k])
    a = _ridge_val(Xtr[:, top], ytr, Xva[:, top], yva)
    out["tree_top8_ridge"] = dict(model=Ridge(alpha=a).fit(Xall[:, top], yall), ix=top, params=k,
                                  features=[names[i] for i in top])
    g = _hgb(seed).fit(Xtr, ytr)
    pi = permutation_importance(g, Xva[::2], yva[::2], n_repeats=3, random_state=seed, scoring="neg_mean_squared_error")
    top = list(np.argsort(-pi.importances_mean)[:k])
    a = _ridge_val(Xtr[:, top], ytr, Xva[:, top], yva)
    out["perm_top8_ridge"] = dict(model=Ridge(alpha=a).fit(Xall[:, top], yall), ix=top, params=k,
                                  features=[names[i] for i in top])
    out["gbm_full_ceiling"] = dict(model=_hgb(seed).fit(Xall, yall), ix=list(range(len(names))), params=150 * 8)
    return out


def predict(b, X):
    return b["model"].predict(X[:, b["ix"]])


def fit_discovered(tr, va, names, mains, frozen, cand_value):
    """Ridge on [stable mains + frozen candidates]; alpha on validation; refit on train+val."""
    def feats(X):
        cols = [X[:, names.index(n)] for n in mains] + [cand_value(c, X, names) for c in frozen]
        return np.column_stack(cols) if cols else np.zeros((len(X), 0))
    Ftr = np.vstack([feats(tr[m][0]) for m in tr]); ytr = np.concatenate([tr[m][1] for m in tr])
    Fva = np.vstack([feats(va[m][0]) for m in va]); yva = np.concatenate([va[m][1] for m in va])
    if Ftr.shape[1] == 0:
        return None
    a = _ridge_val(Ftr, ytr, Fva, yva)
    mdl = Ridge(alpha=a).fit(np.vstack([Ftr, Fva]), np.concatenate([ytr, yva]))
    params = len(mains) + sum(c["nodes"] for c in frozen) + Ftr.shape[1]
    return dict(model=mdl, feats=feats, params=params)
