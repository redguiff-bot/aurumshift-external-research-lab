"""ulib: metrics, calibrators, abstention, conformal, detectors, synthetic world.
External research only. numpy/scipy/sklearn. Deterministic given seeds."""
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import expit, logit
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression

EPS = 1e-6
def clip(p): return np.clip(p, EPS, 1 - EPS)

# ---------------------------------------------------------------- metrics
def brier(p, y): return float(np.mean((p - y) ** 2))
def logloss(p, y):
    p = clip(p); return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))

def ece_top(p, y, bins=15):
    """top-label ECE, equal-mass bins."""
    conf = np.maximum(p, 1 - p); corr = ((p >= .5).astype(int) == y).astype(float)
    o = np.argsort(conf); n = len(p); e = 0.0
    for idx in np.array_split(o, min(bins, max(1, n // 20))):
        if len(idx): e += len(idx) / n * abs(conf[idx].mean() - corr[idx].mean())
    return float(e)

def ece_pos(p, y, bins=15):
    o = np.argsort(p); n = len(p); e = 0.0
    for idx in np.array_split(o, min(bins, max(1, n // 20))):
        if len(idx): e += len(idx) / n * abs(p[idx].mean() - y[idx].mean())
    return float(e)

def reliability(p, y, bins=10):
    o = np.argsort(p); out = []
    for idx in np.array_split(o, bins):
        out.append((float(p[idx].mean()), float(y[idx].mean()), int(len(idx))))
    return out

def decisions(p, tau):
    """+1 BUY if p>=tau, -1 SELL if p<=1-tau, 0 HOLD."""
    d = np.zeros(len(p), int); d[p >= tau] = 1; d[p <= 1 - tau] = -1; return d

def dec_metrics(p, y, act=None, tau=0.5, cost=0.2, conf_thr=0.8):
    """Decision quality. act: optional boolean mask of allowed actions (abstain elsewhere)."""
    pred = (p >= .5).astype(int); conf = np.maximum(p, 1 - p)
    a = (conf >= tau) if tau > .5 else np.ones(len(p), bool)
    if act is not None: a = a & act
    wrong = pred != y; n = len(p)
    tot_wrong = wrong.sum(); tot_right = n - tot_wrong
    cov = a.mean()
    return dict(
        coverage=float(cov), abstention=float(1 - cov),
        selective_risk=float(wrong[a].mean()) if a.any() else float('nan'),
        full_risk=float(wrong.mean()),
        bad_avoided=float(1 - (wrong & a).sum() / max(1, tot_wrong)),
        good_retained=float((~wrong & a).sum() / max(1, tot_right)),
        false_conf_rate=float((wrong & (conf >= conf_thr)).mean()),   # over all rows
        false_conf_cond=float(wrong[conf >= conf_thr].mean()) if (conf >= conf_thr).any() else float('nan'),
        conf_wrong_penalty=float(np.mean((wrong & a) * (2 * conf - 1))),  # confident-wrong loss on acted rows
        utility=float(np.mean(a * (np.where(wrong, -1.0, 1.0) - cost))),   # per opportunity
        n_trades=int(a.sum()))

def risk_coverage(conf, wrong):
    o = np.argsort(-conf); w = wrong[o].astype(float)
    cum = np.cumsum(w) / np.arange(1, len(w) + 1)
    return cum  # risk at coverage k/n
def aurc(conf, wrong): return float(risk_coverage(conf, wrong).mean())

def turnover(d):
    d = np.asarray(d); return float(np.mean(d[1:] != d[:-1])) if len(d) > 1 else float('nan')

def auroc(score, label):
    """AUROC, label 1 = positive (higher score => positive). Rank based."""
    from scipy.stats import rankdata
    label = np.asarray(label).astype(bool); n1 = label.sum(); n0 = (~label).sum()
    if n1 == 0 or n0 == 0: return float('nan')
    r = rankdata(score); return float((r[label].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

def ci95(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 2: return (float(x.mean()) if len(x) else float('nan'), float('nan'))
    return float(x.mean()), float(1.96 * x.std(ddof=1) / np.sqrt(len(x)))

# ---------------------------------------------------------------- calibrators
class Ident:
    name = 'raw'
    def fit(self, p, y): return self
    def __call__(self, p): return clip(p)

class Platt:
    name = 'platt'
    def fit(self, p, y):
        z = logit(clip(p)).reshape(-1, 1)
        if len(np.unique(y)) < 2: self.a, self.b = 1.0, 0.0; return self
        m = LogisticRegression(C=1e4, max_iter=500).fit(z, y); self.a, self.b = float(m.coef_[0, 0]), float(m.intercept_[0]); return self
    def __call__(self, p): return clip(expit(self.a * logit(clip(p)) + self.b))

class Temp:
    name = 'temperature'
    def fit(self, p, y):
        z = logit(clip(p))
        def nll(lt):
            q = clip(expit(z / np.exp(lt))); return -np.mean(y * np.log(q) + (1 - y) * np.log(1 - q))
        self.T = float(np.exp(minimize_scalar(nll, bounds=(-3, 3), method='bounded').x)); return self
    def __call__(self, p): return clip(expit(logit(clip(p)) / self.T))

class Beta:
    """Kull et al. 2017 beta calibration: logit q = a ln p - b ln(1-p) + c (a,b unconstrained here)."""
    name = 'beta'
    def _f(self, p): p = clip(p); return np.c_[np.log(p), -np.log(1 - p)]
    def fit(self, p, y):
        self.m = LogisticRegression(C=1e4, max_iter=500).fit(self._f(p), y); return self
    def __call__(self, p): return clip(self.m.predict_proba(self._f(p))[:, 1])

class Iso:
    name = 'isotonic'
    def fit(self, p, y): self.m = IsotonicRegression(out_of_bounds='clip', y_min=0.02, y_max=0.98).fit(p, y); return self
    def __call__(self, p): return clip(self.m.predict(p))

class BayesBin:
    """Bayesian (BBQ-style, single binning) : equal-mass bins, Beta posterior mean with prior centred on the bin mean score.
    Also returns a 90% credible half-width (epistemic uncertainty of the calibration map)."""
    name = 'bayes_bin'
    def __init__(self, m=10.0, nb=None): self.m = m; self.nb = nb
    def fit(self, p, y):
        n = len(p); nb = self.nb or int(np.clip(np.sqrt(n) / 2, 4, 20)); o = np.argsort(p)
        self.edges, self.mu, self.hw = [], [], []
        from scipy.stats import beta as B
        for idx in np.array_split(o, nb):
            pb = p[idx].mean(); a = self.m * pb + y[idx].sum(); b = self.m * (1 - pb) + (1 - y[idx]).sum()
            self.edges.append(p[idx].max()); self.mu.append(a / (a + b))
            self.hw.append((B.ppf(.95, a, b) - B.ppf(.05, a, b)) / 2)
        self.edges = np.array(self.edges[:-1]); self.mu = np.array(self.mu); self.hw = np.array(self.hw)
        self.mu = np.maximum.accumulate(self.mu) if False else self.mu; return self
    def _bin(self, p): return np.searchsorted(self.edges, p, side='right')
    def __call__(self, p): return clip(self.mu[self._bin(p)])
    def halfwidth(self, p): return self.hw[self._bin(p)]

CALIBRATORS = dict(raw=Ident, platt=Platt, temperature=Temp, beta=Beta, isotonic=Iso, bayes_bin=BayesBin)

# ---------------------------------------------------------------- online calibrators (label-delay aware)
class OnlinePlattSGD:
    """Online logistic recalibration a*z+b via SGD on revealed labels only."""
    def __init__(self, a0, b0, lr=0.02): self.a, self.b, self.lr = a0, b0, lr
    def __call__(self, p): return clip(expit(self.a * logit(clip(p)) + self.b))
    def update(self, p, y):
        z = logit(clip(p)); q = expit(self.a * z + self.b); g = q - y
        self.a -= self.lr * g * z; self.b -= self.lr * g

def run_online(p, y, kind, t0, h=10, refit=250, W=1000, lr=0.02, c0=0):
    """Sequentially calibrate raw scores p[t0:], label y_t revealed at time t+h (PIT-safe).
    kind: static_platt | static_iso | expand_platt | window_platt | window_iso | sgd | leak_block | leak_global
    Returns calibrated q[t0:], per-step Platt slope path (nan if n/a), and an audit max_label_time <= t check."""
    T = len(p); q = np.full(T, np.nan); slope = np.full(T, np.nan)
    init = Platt().fit(p[c0:t0], y[c0:t0]); iso0 = Iso().fit(p[c0:t0], y[c0:t0])   # c0 = start of the calibration block (train rows are in-sample for the base model and must never be used)
    cur = init; sgd = OnlinePlattSGD(init.a, init.b, lr); audit_ok = True
    gl = Platt().fit(p[t0:], y[t0:]) if kind == 'leak_global' else None
    for s in range(t0, T, refit):
        e = min(T, s + refit)
        known_end = s - h + 1          # labels y_j with j+h <= s  -> j <= s-h
        if kind == 'static_platt': cur = init
        elif kind == 'static_iso': cur = iso0
        elif kind in ('expand_platt', 'window_platt', 'window_iso'):
            lo = c0 if kind == 'expand_platt' else max(c0, known_end - W)
            hi = known_end; audit_ok &= (hi - 1 + h <= s)
            if hi - lo >= 100 and len(np.unique(y[lo:hi])) == 2:
                cur = (Iso if kind == 'window_iso' else Platt)().fit(p[lo:hi], y[lo:hi])
        elif kind == 'leak_block': cur = Platt().fit(p[s:e], y[s:e])       # LOOKAHEAD: fit on the block it then predicts
        elif kind == 'leak_global': cur = gl                                # LOOKAHEAD: fit on whole future stream
        if kind == 'sgd':
            for t in range(s, e):
                q[t] = sgd(p[t]); slope[t] = sgd.a
                j = t - h
                if j >= t0: sgd.update(p[j], y[j])       # only labels revealed by t
            continue
        q[s:e] = cur(p[s:e]); slope[s:e] = getattr(cur, 'a', np.nan)
    return q[t0:], slope[t0:], audit_ok

# ---------------------------------------------------------------- conformal
def lac_scores(q, y): return 1 - np.where(y == 1, q, 1 - q)
def wquantile(s, w, level):
    """weighted conformal quantile with mass at +inf (weights include test point weight = max(w)... simple version: total weight+1)."""
    o = np.argsort(s); s = s[o]; w = w[o]; cw = np.cumsum(w) / (w.sum() + w.max())
    i = np.searchsorted(cw, level, side='left')
    return np.inf if i >= len(s) else s[i]

def conformal_stream(q, y, t0, alpha=0.2, method='split', h=10, W=1000, gamma=0.005, lam=0.998, ncal0=None):
    """Sequential set-valued conformal on calibrated probs q (LAC score). Returns per-step sets as (in0,in1) bool arrays.
    Scores of step j usable at t>=j+h. method: split | rolling | weighted | aci | aci_h0 (label feedback with h=0, textbook, NOT deployable)."""
    T = len(q); s_all = lac_scores(q, y)
    in0 = np.zeros(T, bool); in1 = np.zeros(T, bool)
    cal_end = t0                                    # initial calibration block = [t0-ncal0, t0)
    ncal0 = ncal0 or 2000; base_s = s_all[max(0, t0 - ncal0):t0]
    a_t = alpha; errs = []
    for t in range(t0, T):
        known_hi = t - h + 1                         # steps j with j+h<=t are usable
        if method == 'split': pool = base_s; w = np.ones(len(pool))
        else:
            lo = max(t0, known_hi - W) if method in ('rolling', 'aci') else max(t0, known_hi - 3000)
            live = s_all[lo:known_hi] if known_hi > lo else np.array([])
            pool = np.r_[base_s, live] if method in ('weighted',) else (np.r_[base_s[-max(0, W - len(live)):], live] if len(live) < W else live)
            if method == 'weighted':
                age = np.r_[np.arange(len(base_s), 0, -1) + (known_hi - t0 if known_hi > t0 else 0), np.arange(len(live), 0, -1)]
                w = lam ** age
            else: w = np.ones(len(pool))
        if method.startswith('aci'):
            lvl = float(np.clip(1 - a_t, 0.0, 1.0))
            if lvl >= 1: qh = np.inf
            elif lvl <= 0: qh = -np.inf
            else: qh = np.quantile(pool, min(1.0, lvl * (1 + 1.0 / len(pool))))
        else:
            qh = wquantile(pool, w, 1 - alpha)
        in1[t] = (1 - q[t]) <= qh; in0[t] = q[t] <= qh
        if method.startswith('aci'):
            hh = 0 if method == 'aci_h0' else h
            j = t - hh                                # feedback error for step j
            if j >= t0:
                err = float(not (in1[j] if y[j] == 1 else in0[j])); a_t = a_t + gamma * (alpha - err)
    cov = np.where(y[t0:] == 1, in1[t0:], in0[t0:])
    return in0[t0:], in1[t0:], cov

def set_stats(in0, in1, y, cov, alpha, win=500):
    both = in0 & in1; single = in0 ^ in1; empty = ~(in0 | in1)
    roll = np.convolve(cov.astype(float), np.ones(win) / win, mode='valid')
    sp = np.where(in1 & ~in0, 1, 0)[single]; acc = float((sp == y[single]).mean()) if single.any() else float('nan')
    return dict(coverage=float(cov.mean()), target=1 - alpha, gap=float(cov.mean() - (1 - alpha)),
                min_roll_cov=float(roll.min()), frac_win_below=float((roll < 1 - alpha - 0.05).mean()),
                singleton=float(single.mean()), both=float(both.mean()), empty=float(empty.mean()), singleton_acc=acc)

def conformal_reg_stream(pred, y, t0, alpha=0.2, method='split', h=10, W=500, gamma=0.005, ncal0=1500):
    T = len(y); r = np.abs(y - pred); half = np.full(T, np.nan); base = r[max(0, t0 - ncal0):t0]; a_t = alpha
    for t in range(t0, T):
        kh = t - h + 1
        if method == 'split': pool = base
        else:
            live = r[max(t0, kh - W):kh] if kh > t0 else np.array([]); pool = np.r_[base[-max(0, W - len(live)):], live] if len(live) < W else live
        lvl = (1 - a_t) if method == 'aci' else (1 - alpha)
        lvl = float(np.clip(lvl, 0, 1)); half[t] = np.quantile(pool, min(1.0, lvl * (1 + 1.0 / len(pool)))) if lvl < 1 else np.inf
        if method == 'aci':
            j = t - h
            if j >= t0: a_t += gamma * (alpha - float(r[j] > half[j]))
    cov = r[t0:] <= half[t0:]; return half[t0:], cov

# ---------------------------------------------------------------- synthetic world
D = 8
def make_world(rng):
    w = rng.normal(size=4); w = w / np.linalg.norm(w) * 1.6
    return dict(w=w, g=0.7, c=0.0)

def gen_x(rng, n, phi=0.7, d=D):
    x = np.zeros((n, d)); x[0] = rng.normal(size=d); sd = np.sqrt(1 - phi ** 2)
    e = rng.normal(size=(n, d)) * sd
    for t in range(1, n): x[t] = phi * x[t - 1] + e[t]
    return x

def true_p(x, W, w_override=None, snr=1.0, gate=True):
    w = W['w'] if w_override is None else w_override
    s = x[:, :4] @ w + W['g'] * x[:, 0] * x[:, 1] + W['c']
    s = s * snr
    if gate: s = np.where(x[:, 7] > 1.0, 0.0, s)       # NO_SIGNAL region: outcome independent of features
    return expit(s)

def sample_y(rng, p): return (rng.random(len(p)) < p).astype(int)

def maha_fit(X):
    mu = X.mean(0); S = np.cov(X.T) + 1e-6 * np.eye(X.shape[1]); return mu, np.linalg.inv(S)
def maha(X, mu, Si):
    d = X - mu; return np.einsum('ij,jk,ik->i', d, Si, d)

def psi(a, b, bins=10):
    qs = np.quantile(a, np.linspace(0, 1, bins + 1)[1:-1]); ca = np.bincount(np.searchsorted(qs, a), minlength=bins) / len(a)
    cb = np.bincount(np.searchsorted(qs, b), minlength=bins) / len(b); ca = np.clip(ca, 1e-4, None); cb = np.clip(cb, 1e-4, None)
    return float(np.sum((cb - ca) * np.log(cb / ca)))
