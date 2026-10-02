"""Calibrators (numpy, no lookahead: every fit takes explicit arrays)."""
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import logit, expit, softmax
from sklearn.isotonic import IsotonicRegression

EPS = 1e-6


def _clip(c):
    return np.clip(c, EPS, 1 - EPS)


def fit_logistic(F, y, w=None, l2=1e-4, iters=50):
    """Newton logistic regression with intercept. F: (n,k)."""
    n, k = F.shape
    A = np.hstack([F, np.ones((n, 1))])
    w = np.ones(n) if w is None else w
    b = np.zeros(k + 1); b[0] = 1.0 if k >= 1 else 0.0
    R = l2 * np.eye(k + 1); R[-1, -1] = 0
    for _ in range(iters):
        p = expit(A @ b)
        g = A.T @ (w * (p - y)) + R @ (b - np.r_[np.ones(1), np.zeros(k)][:k + 1] * 0)
        H = (A * (w * p * (1 - p))[:, None]).T @ A + R + 1e-9 * np.eye(k + 1)
        step = np.linalg.solve(H, g)
        step = np.clip(step, -3, 3)
        b -= step
        if np.abs(step).max() < 1e-7:
            break
    return b


class Identity:
    name = "raw"
    def fit(self, p, y, w=None): return self
    def conf(self, c): return c
    def transform(self, p): return p


class TopLabel:
    """Top-label calibration of the max-probability; other classes rescaled proportionally."""
    name = "?"
    def fit(self, p, y, w=None):
        c = _clip(p.max(1)); ok = (p.argmax(1) == y).astype(float)
        self._fit(c, ok, w); return self
    def transform(self, p):
        c = _clip(p.max(1)); c2 = _clip(self.conf(c))
        k = p.argmax(1); q = p.copy(); q[np.arange(len(p)), k] = 0; q /= q.sum(1, keepdims=True) + 1e-12
        c2 = np.maximum(c2, q.max(1) / (1 + q.max(1)) * 1.001)   # argmax-preserving floor
        out = q * (1 - c2)[:, None]; out[np.arange(len(p)), k] = c2
        return out


class Platt(TopLabel):
    name = "platt"
    def _fit(self, c, ok, w): self.b = fit_logistic(logit(c)[:, None], ok, w)
    def conf(self, c): return expit(self.b[0] * logit(_clip(c)) + self.b[1])


class Beta(TopLabel):
    """Kull et al. 2017 beta calibration: logistic on [ln c, -ln(1-c)]."""
    name = "beta"
    def _fit(self, c, ok, w): self.b = fit_logistic(np.stack([np.log(c), -np.log(1 - c)], 1), ok, w)
    def conf(self, c):
        c = _clip(c); return expit(self.b[0] * np.log(c) - self.b[1] * np.log(1 - c) + self.b[2])


class Isotonic(TopLabel):
    name = "isotonic"
    def _fit(self, c, ok, w):
        self.iso = IsotonicRegression(y_min=0.02, y_max=0.98, out_of_bounds="clip").fit(c, ok, sample_weight=w)
    def conf(self, c): return self.iso.predict(c)


class BayesBin(TopLabel):
    """Bayesian binning (BBQ-lite): Beta(a,b)-prior histogram posterior means, averaged over bin counts."""
    name = "bayes_bin"
    def __init__(self, bins=(4, 8, 16), prior=2.0): self.bins, self.prior = bins, prior
    def _fit(self, c, ok, w):
        w = np.ones(len(c)) if w is None else w
        self.tabs = []
        for B in self.bins:
            edges = np.quantile(c, np.linspace(0, 1, B + 1)); edges[0], edges[-1] = 0, 1
            edges = np.unique(edges); idx = np.clip(np.searchsorted(edges, c, side="right") - 1, 0, len(edges) - 2)
            nb = len(edges) - 1
            s = np.bincount(idx, w * ok, nb); n = np.bincount(idx, w, nb)
            base = np.average(ok, weights=w)
            self.tabs.append((edges, (s + self.prior * base) / (n + self.prior)))
    def conf(self, c):
        out = 0
        for edges, mu in self.tabs:
            out = out + mu[np.clip(np.searchsorted(edges, c, side="right") - 1, 0, len(mu) - 1)]
        return out / len(self.tabs)


class Temperature:
    """Guo et al. 2017 temperature scaling on full logits."""
    name = "temperature"
    def fit(self, logits, y, w=None):
        w = np.ones(len(y)) if w is None else w
        def nll(T):
            lp = np.log(softmax(logits / T, 1)[np.arange(len(y)), y] + 1e-12)
            return -(w * lp).sum() / w.sum()
        self.T = minimize_scalar(nll, bounds=(0.2, 20), method="bounded").x; return self
    def transform(self, logits): return softmax(logits / self.T, 1)


CALS = {"platt": Platt, "beta": Beta, "isotonic": Isotonic, "bayes_bin": BayesBin}
NAMES = ["raw", "temperature", "platt", "beta", "isotonic", "bayes_bin"]


def make(name):
    return {"raw": Identity, "temperature": Temperature, **CALS}[name]()


def fit_apply(name, logits_fit, y_fit, w=None):
    """returns function logits->probs. raw/top-label variants use softmax(logits) as input."""
    cal = make(name)
    if name == "temperature":
        cal.fit(logits_fit, y_fit, w); return cal.transform
    cal.fit(softmax(logits_fit, 1), y_fit, w)
    return lambda L: cal.transform(softmax(L, 1))
