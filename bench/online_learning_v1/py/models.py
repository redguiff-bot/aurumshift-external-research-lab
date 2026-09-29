"""Common interface: predict(x)->float (C: P(y=1); R: mean), learn(x,y,now), state_bytes(), replay-safe (all RNG seeded).
x is a 1-D numpy array. `now` is the harness clock at which the label became available (update timestamp)."""
import pickle, copy, functools, numpy as np
from river import linear_model, optim, tree, forest, ensemble, drift
from sklearn.linear_model import LogisticRegression as SkLR

D = 8
def _d(x): return {i: float(v) for i, v in enumerate(x)}
def _sig(z): return 1 / (1 + np.exp(-np.clip(z, -30, 30)))
def _clip(p): return min(max(p, 1e-4), 1 - 1e-4)

class Base:
    kind = "?"; last_update = -1
    def state_bytes(self): return len(pickle.dumps(self, protocol=4))
    def learn(self, x, y, now): self.last_update = now; self._learn(x, y, now)

# ---------------- simple references -----------------------------------------------------------------
class Frozen(Base):
    """fit once on the first n0 labelled samples, never updated."""
    def __init__(s, kind, n0=500, **_): s.kind = kind; s.n0 = n0; s.X = []; s.y = []; s.w = None; s.b = 0.0; s.done = False
    def _fit(s):
        X = np.array(s.X); y = np.array(s.y)
        if s.kind == "C":
            m = SkLR(C=1.0, max_iter=200).fit(X, y); s.w = m.coef_[0]; s.b = m.intercept_[0]
        else: s.w = np.linalg.solve(X.T @ X + 1.0 * np.eye(D), X.T @ y)
        s.done = True; s.X = []; s.y = []
    def _learn(s, x, y, now):
        if s.done: return
        s.X.append(x); s.y.append(y)
        if len(s.y) >= s.n0: s._fit()
    def predict(s, x):
        if s.w is None: return 0.5 if s.kind == "C" else 0.0
        z = float(s.w @ x + s.b); return _clip(_sig(z)) if s.kind == "C" else z

class BatchRefit(Base):
    """refit on labelled buffer every `period` steps (now-clock). window=None -> expanding (periodic batch retrain);
    window=W -> bounded rolling window refit (state bounded to W samples)."""
    def __init__(s, kind, period=500, window=None, **_):
        s.kind = kind; s.period = period; s.window = window; s.X = []; s.y = []; s.w = None; s.b = 0.0; s.next = period; s.n_fit = 0
    def _learn(s, x, y, now):
        s.X.append(x); s.y.append(y)
        if s.window and len(s.y) > s.window: del s.X[0]; del s.y[0]
        if now >= s.next and len(s.y) >= 30 * 1:
            s._fit(); s.next = now + s.period
    def _fit(s):
        X = np.array(s.X); y = np.array(s.y); s.n_fit += 1
        if s.kind == "C":
            if len(set(y.tolist())) < 2: return
            m = SkLR(C=1.0, max_iter=200).fit(X, y); s.w = m.coef_[0]; s.b = m.intercept_[0]
        else: s.w = np.linalg.solve(X.T @ X + 1.0 * np.eye(D), X.T @ y)
    predict = Frozen.predict

# ---------------- own numpy recursive estimators (regression) ---------------------------------------------
class RLS(Base):
    kind = "R"
    def __init__(s, lam=0.995, delta=10.0, **_): s.lam = lam; s.P = np.eye(D) * delta; s.w = np.zeros(D); s.delta = delta
    def reset(s): s.P = np.eye(D) * s.delta; s.w = np.zeros(D)
    def _learn(s, x, y, now):
        Px = s.P @ x; k = Px / (s.lam + x @ Px); e = y - s.w @ x
        s.w = s.w + k * e; s.P = (s.P - np.outer(k, Px)) / s.lam
        s.P = (s.P + s.P.T) / 2            # keep symmetric; guards against forgetting-induced blow-up
    def predict(s, x): return float(s.w @ x)

class Kalman(Base):
    """random-walk coefficient Kalman filter: w_t = w_{t-1}+N(0,qI), y = w.x + N(0,R), R fixed = 0.25 (assumed noise var)."""
    kind = "R"
    def __init__(s, q=1e-3, R=0.25, **_): s.q = q; s.R = R; s.P = np.eye(D) * 10.0; s.w = np.zeros(D)
    def _learn(s, x, y, now):
        P = s.P + s.q * np.eye(D); Px = P @ x; k = Px / (x @ Px + s.R)
        s.w = s.w + k * (y - s.w @ x); s.P = P - np.outer(k, Px)
    def predict(s, x): return float(s.w @ x)

# ---------------- OSS river wrappers -------------------------------------------------------------------
class RiverWrap(Base):
    def __init__(s, kind, model): s.kind = kind; s.m = model
    def _learn(s, x, y, now): s.m.learn_one(_d(x), bool(y) if s.kind == "C" else y)
    def predict(s, x):
        if s.kind == "R": return float(s.m.predict_one(_d(x)) or 0.0)
        p = s.m.predict_proba_one(_d(x)); return _clip(float(p.get(True, 0.5)))

class PAWrap(RiverWrap):
    """PAClassifier gives a margin, not a probability -> optional online Platt calibration (own 2-param SGD logistic)."""
    def __init__(s, C=0.1, platt=True, lr=0.02):
        super().__init__("C", linear_model.PAClassifier(C=C)); s.platt = platt; s.a = 1.0; s.b = 0.0; s.lr = lr
    def _margin(s, x): return sum(s.m.weights.get(i, 0.0) * v for i, v in enumerate(x)) + s.m.intercept
    def _learn(s, x, y, now):
        if s.platt:  # calibrator updated BEFORE model sees the label (prequential order)
            z = s._margin(x); p = _sig(s.a * z + s.b); g = p - y; s.a -= s.lr * g * z; s.b -= s.lr * g
        s.m.learn_one(_d(x), bool(y))
    def predict(s, x):
        z = s._margin(x); return _clip(_sig(s.a * z + s.b)) if s.platt else _clip(_sig(z))

class PlattLR(RiverWrap):
    """river LogisticRegression + online Platt recalibration on its logit."""
    def __init__(s, lr=0.03, platt=True, l2=0.0):
        super().__init__("C", linear_model.LogisticRegression(optimizer=optim.SGD(lr), l2=l2)); s.platt = platt; s.a = 1.0; s.b = 0.0; s.plr = 0.02
    def _logit(s, x):
        p = _clip(RiverWrap.predict(s, x)); return float(np.log(p / (1 - p)))
    def _learn(s, x, y, now):
        if s.platt:
            z = s._logit(x); p = _sig(s.a * z + s.b); g = p - y; s.a -= s.plr * g * z; s.b -= s.plr * g
        s.m.learn_one(_d(x), bool(y))
    def predict(s, x): return _clip(_sig(s.a * s._logit(x) + s.b)) if s.platt else RiverWrap.predict(s, x)

class DriftReset(Base):
    """base online model + ADWIN on its own prequential error; on detection: fresh model warm-started from the last `warm`
    labelled samples (bounded buffer).  `factory()` builds the base model (must expose predict/learn/kind)."""
    def __init__(s, factory, delta=0.002, warm=150):
        s.f = factory; s.m = factory(); s.kind = s.m.kind; s.det = drift.ADWIN(delta=delta); s.warm = warm; s.buf = []; s.n_reset = 0
    def _err(s, x, y):
        p = s.m.predict(x); return float(abs(p - y) > 0.5) if s.kind == "C" else float((p - y) ** 2)
    def _learn(s, x, y, now):
        s.det.update(s._err(x, y)); s.buf.append((x, y))
        if len(s.buf) > s.warm: del s.buf[0]
        if s.det.drift_detected:
            s.m = s.f(); s.n_reset += 1
            for xb, yb in s.buf: s.m.learn(xb, yb, now)
        else: s.m.learn(x, y, now)
    def predict(s, x): return s.m.predict(x)

class Bank(Base):
    """recurring-regime memory (CUSTOM, added only to test whether memory earns its place): bounded bank of frozen snapshots
    of the active model; ADWIN reset as in DriftReset; snapshot = lagged copy (taken every `snap_every` labelled steps) so it is
    not contaminated by the post-drift data; each labelled step compares EWMA logloss/sqerr of active vs bank; swap if bank member
    is clearly better."""
    def __init__(s, factory, K=3, delta=0.002, warm=150, snap_every=100, thr=0.85, alpha=0.03):
        s.f = factory; s.m = factory(); s.kind = s.m.kind; s.det = drift.ADWIN(delta=delta); s.K = K; s.warm = warm
        s.bank = []; s.ew = []; s.buf = []; s.lag = None; s.n = 0; s.snap_every = snap_every; s.thr = thr; s.alpha = alpha
        s.ea = None; s.n_reset = 0; s.n_swap = 0
    def _loss(s, m, x, y):
        p = m.predict(x)
        return float(-(y * np.log(p) + (1 - y) * np.log(1 - p))) if s.kind == "C" else float((p - y) ** 2)
    def _learn(s, x, y, now):
        s.n += 1
        la = s._loss(s.m, x, y); s.ea = la if s.ea is None else (1 - s.alpha) * s.ea + s.alpha * la
        for i, b in enumerate(s.bank): s.ew[i] = (1 - s.alpha) * s.ew[i] + s.alpha * s._loss(b, x, y)
        err = float(abs(s.m.predict(x) - y) > 0.5) if s.kind == "C" else la
        s.det.update(err); s.buf.append((x, y))
        if len(s.buf) > s.warm: del s.buf[0]
        if s.n % s.snap_every == 0: s.lag = copy.deepcopy(s.m)      # lagged snapshot
        if s.det.drift_detected:
            if s.lag is not None:
                s.bank.append(s.lag); s.ew.append(s.ea if s.ea is not None else 1.0)
                if len(s.bank) > s.K: s.bank.pop(0); s.ew.pop(0)
            s.m = s.f(); s.n_reset += 1
            for xb, yb in s.buf: s.m.learn(xb, yb, now)
            s.ea = np.mean([s._loss(s.m, xb, yb) for xb, yb in s.buf]) if s.buf else None
        else: s.m.learn(x, y, now)
        if s.bank and s.ea is not None:
            j = int(np.argmin(s.ew))
            if s.ew[j] < s.thr * s.ea:
                s.bank[j], s.m = s.m, s.bank[j]; s.ew[j], s.ea = s.ea, s.ew[j]; s.n_swap += 1
    def predict(s, x): return s.m.predict(x)

# ---------------- factories -------------------------------------------------------------------------------
def build(name, kind, **hp):
    if name == "frozen": return Frozen(kind)
    if name == "batch": return BatchRefit(kind, period=hp.get("period", 500))
    if name == "rolling": return BatchRefit(kind, period=hp.get("period", 25), window=hp.get("window", 300))
    if name == "rls": return RLS(lam=hp.get("lam", 0.995))
    if name == "kalman": return Kalman(q=hp.get("q", 1e-3))
    if name == "sgd_lin": return RiverWrap("R", linear_model.LinearRegression(optimizer=optim.SGD(hp.get("lr", 0.01)), intercept_lr=0.0))
    if name == "par_reg": return RiverWrap("R", linear_model.PARegressor(C=hp.get("C", 0.1), learn_intercept=False))
    if name == "blr": return RiverWrap("R", linear_model.BayesianLinearRegression(alpha=1, beta=4, smoothing=hp.get("smoothing")))
    if name == "hat":
        return RiverWrap(kind, tree.HoeffdingAdaptiveTreeRegressor(grace_period=hp.get("grace", 50), seed=1) if kind == "R" else
                         tree.HoeffdingAdaptiveTreeClassifier(grace_period=hp.get("grace", 50), seed=1))
    if name == "ht": return RiverWrap("C", tree.HoeffdingTreeClassifier(grace_period=hp.get("grace", 50)))
    if name == "arf":
        return RiverWrap(kind, forest.ARFRegressor(n_models=5, grace_period=hp.get("grace", 50), seed=1) if kind == "R" else
                         forest.ARFClassifier(n_models=5, grace_period=hp.get("grace", 50), seed=1))
    if name == "adwin_bag": return RiverWrap("C", ensemble.ADWINBaggingClassifier(tree.HoeffdingTreeClassifier(grace_period=hp.get("grace", 50)), n_models=5, seed=1))
    if name == "sgd_log": return PlattLR(lr=hp.get("lr", 0.03), platt=False)
    if name == "sgd_log_platt": return PlattLR(lr=hp.get("lr", 0.03), platt=True)
    if name == "pa_platt": return PAWrap(C=hp.get("C", 0.1), platt=True)
    if name == "pa_raw": return PAWrap(C=hp.get("C", 0.1), platt=False)
    if name in ("reset_rls", "reset_sgd_log", "bank_rls", "bank_sgd_log"):
        base_name = "rls" if name.endswith("rls") else "sgd_log"
        k = "R" if base_name == "rls" else "C"
        fac = functools.partial(build, base_name, k, **hp)   # partial (not lambda) so the whole model stays picklable/checkpointable
        if name.startswith("reset"): return DriftReset(fac, delta=hp.get("delta", 0.002), warm=hp.get("warm", 150))
        return Bank(fac, K=hp.get("K", 3), delta=hp.get("delta", 0.002), warm=hp.get("warm", 150))
    raise ValueError(name)

# (name, track) -> list of hyper-parameter dicts for tuning; index 0 = default. Small grids on purpose.
GRID = {
 ("frozen","R"):[{}], ("frozen","C"):[{}],
 ("batch","R"):[{"period":p} for p in (250,500,1000)], ("batch","C"):[{"period":p} for p in (250,500,1000)],
 ("rolling","R"):[{"window":w,"period":25} for w in (150,300,600)], ("rolling","C"):[{"window":w,"period":25} for w in (150,300,600)],
 ("rls","R"):[{"lam":l} for l in (0.98,0.99,0.995,0.999)],
 ("kalman","R"):[{"q":q} for q in (1e-5,1e-4,1e-3,1e-2)],
 ("sgd_lin","R"):[{"lr":l} for l in (0.003,0.01,0.03)],
 ("par_reg","R"):[{"C":c} for c in (0.01,0.1,1.0)],
 ("blr","R"):[{"smoothing":s} for s in (None,0.995,0.98)],
 ("hat","R"):[{"grace":g} for g in (50,200)], ("hat","C"):[{"grace":g} for g in (50,200)],
 ("arf","R"):[{"grace":50}], ("arf","C"):[{"grace":50}],
 ("ht","C"):[{"grace":g} for g in (50,200)],
 ("adwin_bag","C"):[{"grace":50}],
 ("sgd_log","C"):[{"lr":l} for l in (0.01,0.03,0.1)],
 ("sgd_log_platt","C"):[{"lr":l} for l in (0.03,)],
 ("pa_raw","C"):[{"C":c} for c in (0.01,0.1,1.0)], ("pa_platt","C"):[{"C":c} for c in (0.01,0.1,1.0)],
 ("reset_rls","R"):[{"lam":0.999,"delta":d} for d in (0.002,0.05)],
 ("reset_sgd_log","C"):[{"lr":0.03,"delta":d} for d in (0.002,0.05)],
 ("bank_rls","R"):[{"lam":0.999,"delta":0.002}], ("bank_sgd_log","C"):[{"lr":0.03,"delta":0.002}],
}
