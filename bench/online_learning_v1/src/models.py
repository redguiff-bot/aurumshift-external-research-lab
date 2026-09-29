"""Model wrappers with one interface: predict(x) / observe(x, y, label_t, now).

Every model carries update metadata (n_updates, last_label_t, last_update_t)
that lives INSIDE the pickled state, so a checkpoint is self-describing.
"""
import collections
import numpy as np
from scipy.special import expit
from river import linear_model, tree, forest, ensemble, drift, optim
from sklearn.linear_model import LogisticRegression

D = 5
PCLIP = 1e-4
STATE_VERSION = "olv1"


def _p(p):
    return float(min(max(p, PCLIP), 1 - PCLIP))


def _logit(p):
    p = _p(p)
    return float(np.log(p / (1 - p)))


def ridge_fit(X, y, alpha=1.0):
    X = np.asarray(X); y = np.asarray(y)
    return np.linalg.solve(X.T @ X + alpha * np.eye(X.shape[1]), X.T @ y)


def logit_fit(X, y, C=1.0):
    X = np.asarray(X); y = np.asarray(y)
    if y.min() == y.max():
        return None
    m = LogisticRegression(C=C, fit_intercept=False, max_iter=200)
    m.fit(X, y)
    return m.coef_[0].copy()


class Base:
    task = "reg"

    def __init__(self):
        self.state_version = STATE_VERSION
        self.n_updates = 0
        self.last_label_t = -1
        self.last_update_t = -1
        self.n_refits = 0
        self.n_resets = 0

    def observe(self, x, y, label_t, now):
        self._learn(x, y)
        self.n_updates += 1
        self.last_label_t = label_t
        self.last_update_t = now

    def meta(self):
        return dict(version=self.state_version, n_updates=self.n_updates,
                    last_label_t=self.last_label_t,
                    last_update_t=self.last_update_t,
                    n_refits=self.n_refits, n_resets=self.n_resets)


class Null(Base):
    def __init__(self, task):
        super().__init__(); self.task = task

    def predict(self, x):
        return 0.0 if self.task == "reg" else 0.5

    def _learn(self, x, y):
        pass


class BatchModel(Base):
    """frozen | periodic (expanding window) | rolling (bounded window),
    optionally with ADWIN-triggered window truncation."""

    def __init__(self, task, kind, n0=500, R=250, W=400, K=25,
                 drift_delta=None, wmax=1000, keep=100, C=1.0, alpha=1.0):
        super().__init__()
        self.task, self.kind = task, kind
        self.n0, self.R, self.W, self.K = n0, R, W, K
        self.C, self.alpha = C, alpha
        self.keep, self.wmax = keep, wmax
        self.n_arr = 0
        self.w = None
        self.done = False
        cap = {"rolling": W, "rolling_drift": wmax}.get(kind)
        self.X = collections.deque(maxlen=cap)
        self.y = collections.deque(maxlen=cap)
        self.det = drift.ADWIN(delta=drift_delta) if drift_delta else None

    def predict(self, x):
        if self.w is None:
            return 0.0 if self.task == "reg" else 0.5
        v = float(self.w @ x)
        return v if self.task == "reg" else _p(expit(v))

    def _fit(self):
        Xa, ya = list(self.X), list(self.y)
        if self.task == "reg":
            self.w = ridge_fit(Xa, ya, self.alpha)
        else:
            w = logit_fit(Xa, ya, self.C)
            if w is not None:
                self.w = w
        self.n_refits += 1

    def _err(self, x, y):
        p = self.predict(x)
        return abs(p - y) if self.task == "reg" else float((p > 0.5) != (y > 0.5))

    def _learn(self, x, y):
        self.n_arr += 1
        if self.kind == "frozen":
            if self.done:
                return
            self.X.append(x.copy()); self.y.append(y)
            if len(self.X) >= self.n0:
                self._fit(); self.done = True
                self.X.clear(); self.y.clear()
            return
        drifted = False
        if self.det is not None:
            self.det.update(self._err(x, y))
            drifted = self.det.drift_detected
        self.X.append(x.copy()); self.y.append(y)
        if drifted:
            keep = min(self.keep, len(self.X))
            X, y_ = list(self.X)[-keep:], list(self.y)[-keep:]
            self.X.clear(); self.y.clear()
            self.X.extend(X); self.y.extend(y_)
            self.n_resets += 1
            self.det = drift.ADWIN(delta=self.det.delta)
            if len(self.X) >= 20:
                self._fit()
            return
        n = len(self.X)
        if self.kind == "periodic":
            if self.n_arr % self.R == 0 and n >= 20:
                self._fit()
        else:  # rolling / rolling_drift
            if self.n_arr % self.K == 0 and n >= min(20, self.W):
                self._fit()


class RLS(Base):
    """Recursive least squares with exponential forgetting (regression)."""
    task = "reg"

    def __init__(self, lam=0.998, p0=100.0):
        super().__init__(); self.lam = lam
        self.w = np.zeros(D); self.P = p0 * np.eye(D)

    def predict(self, x):
        return float(self.w @ x)

    def _learn(self, x, y):
        Px = self.P @ x
        k = Px / (self.lam + x @ Px)
        self.w = self.w + k * (y - self.w @ x)
        P = (self.P - np.outer(k, Px)) / self.lam
        self.P = (P + P.T) / 2


class KalmanRW(Base):
    """Random-walk coefficient Kalman filter; measurement noise from an EWMA."""
    task = "reg"

    def __init__(self, q=1e-3, p0=10.0, r0=4.0):
        super().__init__(); self.q, self.r = q, r0
        self.w = np.zeros(D); self.P = p0 * np.eye(D)

    def predict(self, x):
        return float(self.w @ x)

    def _learn(self, x, y):
        P = self.P + self.q * np.eye(D)
        e = y - self.w @ x
        Px = P @ x
        S = x @ Px + self.r
        K = Px / S
        self.w = self.w + K * e
        P = P - np.outer(K, Px)
        self.P = (P + P.T) / 2
        self.r = 0.99 * self.r + 0.01 * e * e


class EKFLogit(Base):
    """Recursive Bayesian/EKF logistic regression with forgetting (P/=lam)."""
    task = "clf"

    def __init__(self, lam=0.998, p0=1.0):
        super().__init__(); self.lam = lam
        self.m = np.zeros(D); self.P = p0 * np.eye(D)

    def predict(self, x):
        mu = self.m @ x; s2 = x @ self.P @ x
        return _p(expit(mu / np.sqrt(1 + np.pi * s2 / 8)))

    def _learn(self, x, y):
        P = self.P / self.lam
        p = expit(self.m @ x)
        Wt = max(p * (1 - p), 1e-3)
        Px = P @ x
        P = P - Wt * np.outer(Px, Px) / (1 + Wt * (x @ Px))
        self.P = (P + P.T) / 2
        self.m = self.m + (self.P @ x) * (y - p)


class RiverWrap(Base):
    def __init__(self, task, make):
        super().__init__(); self.task = task; self.m = make()  # make() is called once; not stored

    @staticmethod
    def _d(x):
        return dict(enumerate(x.tolist()))

    def predict(self, x):
        if self.task == "reg":
            v = self.m.predict_one(self._d(x))
            return float(v) if np.isfinite(v) else 0.0
        pr = self.m.predict_proba_one(self._d(x))
        return _p(pr.get(True, 0.5)) if pr else 0.5

    def _learn(self, x, y):
        self.m.learn_one(self._d(x), y if self.task == "reg" else bool(y > 0.5))


class Reset(Base):
    """Drift-triggered hard reset of a base model (ADWIN on prequential error)."""

    def __init__(self, factory, delta, task):
        super().__init__(); self.task = task
        self.factory, self.delta = factory, delta
        self.base = factory(); self.det = drift.ADWIN(delta=delta)

    def predict(self, x):
        return self.base.predict(x)

    def _learn(self, x, y):
        p = self.base.predict(x)
        err = abs(p - y) if self.task == "reg" else float((p > 0.5) != (y > 0.5))
        self.det.update(err)
        if self.det.drift_detected:
            self.base = self.factory(); self.det = drift.ADWIN(delta=self.delta)
            self.n_resets += 1
        self.base._learn(x, y)


class Platt(Base):
    """Online Platt recalibration of a base probability forecaster."""
    task = "clf"

    def __init__(self, base, lr=0.02):
        super().__init__(); self.base, self.lr = base, lr
        self.a, self.b = 1.0, 0.0

    def predict(self, x):
        return _p(expit(self.a * _logit(self.base.predict(x)) + self.b))

    def _learn(self, x, y):
        l = _logit(self.base.predict(x))
        g = expit(self.a * l + self.b) - y
        self.a -= self.lr * g * l
        self.b -= self.lr * g
        self.base._learn(x, y)


class Bank(Base):
    """CUSTOM composite: bounded bank of frozen snapshots + one active learner.
    On ADWIN drift, recall the stored snapshot that best fits the last B
    labelled points, else spawn a warm-started fresh learner."""

    def __init__(self, factory, delta, task, K=4, B=50, ratio=0.8):
        super().__init__(); self.task = task
        self.factory, self.delta, self.K, self.B, self.ratio = factory, delta, K, B, ratio
        self.active = factory(); self.stored = []
        self.buf = collections.deque(maxlen=B)
        self.det = drift.ADWIN(delta=delta)
        self.n_recalls = 0

    def predict(self, x):
        return self.active.predict(x)

    def _loss(self, m):
        tot = 0.0
        for x, y in self.buf:
            p = m.predict(x)
            tot += (p - y) ** 2 if self.task == "reg" else -(y * np.log(_p(p)) + (1 - y) * np.log(1 - _p(p)))
        return tot / max(len(self.buf), 1)

    def _learn(self, x, y):
        p = self.active.predict(x)
        err = abs(p - y) if self.task == "reg" else float((p > 0.5) != (y > 0.5))
        self.det.update(err)
        self.buf.append((x.copy(), y))
        self.active._learn(x, y)
        if self.det.drift_detected and len(self.buf) >= 20:
            self.n_resets += 1
            self.det = drift.ADWIN(delta=self.delta)
            la = self._loss(self.active)
            ls = [self._loss(m) for m in self.stored]
            if ls and min(ls) < self.ratio * la:
                i = int(np.argmin(ls))
                new = self.stored.pop(i); self.n_recalls += 1
            else:
                new = self.factory()
                for xb, yb in self.buf:
                    new._learn(xb, yb)
            self.stored.append(self.active)
            if len(self.stored) > self.K - 1:
                self.stored.pop(0)
            self.active = new


class Leaky(Base):
    """POSITIVE CONTROL for the leakage canary: cheats by reading the stream."""
    task = "reg"

    def __init__(self, S):
        super().__init__(); self.S = S; self.t = 0

    def predict(self, x):
        v = 0.5 * self.S.z[self.t]   # peeks at the current label
        return float(v)

    def _learn(self, x, y):
        pass
