import numpy as np
from scipy.special import softmax
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import HistGradientBoostingClassifier as HGB
import warnings; warnings.filterwarnings("ignore")


def feats(X):
    return np.hstack([X, X ** 2])


def impute(X, mu):
    X = X.copy(); m = np.isnan(X); X[m] = np.broadcast_to(mu, X.shape)[m]; return X


class Base:
    """Multinomial LR on [x, x^2] + bootstrap ensemble (epistemic proxy) + ridge regressor."""
    def __init__(self, n_ens=8, seed=0, C=1.0, kind="lr"): self.n_ens, self.seed, self.C, self.kind = n_ens, seed, C, kind
    def _mk(self, i=0):
        if self.kind == "lr": return LogisticRegression(C=self.C, max_iter=500)
        # deliberately over-fit, over-confident learner (no early stopping, many iterations)
        return HGB(max_iter=100, learning_rate=0.3, max_leaf_nodes=31, min_samples_leaf=5, early_stopping=False, random_state=self.seed + i)
    def fit(self, X, y, r=None):
        self.mu = np.nanmean(X, 0); Xi = impute(X, self.mu); F = feats(Xi)
        self.clf = self._mk().fit(F, y)
        rng = np.random.default_rng(self.seed); self.ens = []
        for j in range(self.n_ens):
            i = rng.integers(0, len(y), len(y))
            while len(np.unique(y[i])) < 3: i = rng.integers(0, len(y), len(y))
            self.ens.append(self._mk(j + 1).fit(F[i], y[i]))
        self.Sigma_inv = np.linalg.inv(np.cov(Xi.T) + 1e-6 * np.eye(X.shape[1]))
        self.mahal_ref = None
        if r is not None:
            self.reg = Ridge(alpha=1.0).fit(Xi, r)
            self.reg_ens = []
            for _ in range(self.n_ens):
                i = rng.integers(0, len(y), len(y)); self.reg_ens.append(Ridge(alpha=1.0).fit(Xi[i], r[i]))
        return self
    def logits(self, X):
        F = feats(impute(X, self.mu))
        if self.kind == "lr": return self.clf.decision_function(F)
        return np.log(np.clip(self.clf.predict_proba(F), 1e-6, 1))
    def proba(self, X): return softmax(self.logits(X), 1)
    def ens_proba(self, X):
        F = feats(impute(X, self.mu)); return np.stack([m.predict_proba(F) for m in self.ens])
    def epistemic(self, X):
        """mutual information = H(mean p) - mean H(p)."""
        E = self.ens_proba(X); pm = E.mean(0)
        H = lambda p: -(p * np.log(p + 1e-12)).sum(-1)
        return H(pm) - H(E).mean(0)
    def mahal(self, X):
        Xi = impute(X, self.mu) - self.mu
        return np.einsum("ij,jk,ik->i", Xi, self.Sigma_inv, Xi)
    def reg_pred(self, X): return self.reg.predict(impute(X, self.mu))
    def reg_ens_pred(self, X):
        Xi = impute(X, self.mu); return np.stack([m.predict(Xi) for m in self.reg_ens])


def repeat_flag(X):
    """stale detector: row identical to previous row on some feature (continuous data never repeats)."""
    f = np.zeros(X.shape, bool); f[1:] = X[1:] == X[:-1]; return f
