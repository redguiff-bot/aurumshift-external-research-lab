"""Online combiners, vectorised over seeds. Every learner sees, per round:
   p[S,K] forecasts (valid only where awake), awake[S,K], observed[S,K] (awake AND score feedback present), ctx[S], y[S].
Interface: w = L.weights(awake, ctx)  -> (S,K) rows sum to 1 over awake (0 if none awake)
           L.update(p, y, awake, observed, w, ctx)
Sleeping semantics: asleep experts are absent from the mixture and receive NO update (unless a deliberate 'neg' ablation flag is set).
"""
import numpy as np
NEG = 0.5   # penalty loss used ONLY by the deliberate 'missing-as-negative' ablations

def brier(p, y): return (p - y[:, None]) ** 2
def logloss(p, y):
    pp = np.where(y[:, None] > 0.5, p, 1 - p); return -np.log(np.clip(pp, 1e-6, 1))
def _norm(x, mask):
    x = np.where(mask, x, 0.0); s = x.sum(1, keepdims=True)
    return np.where(s > 0, x / np.where(s > 0, s, 1), 0.0)
def _softmax_masked(lw, mask):
    m = np.where(mask, lw, -np.inf).max(1, keepdims=True); m = np.where(np.isfinite(m), m, 0)
    return _norm(np.exp(np.where(mask, lw - m, -np.inf)), mask)


def _keep_mass(lw, known, U, m0):
    """Shift the log-weights of the updated block U by the constant c that restores its posterior mass to m0 (exact specialist normalisation):
    e^c = m0 (1-m1) / ((1-m0) m1), with m1 the block mass after the raw update. No-op if the block is the whole known set or empty."""
    v = _softmax_masked(lw, known); m1 = np.where(U, v, 0).sum(1, keepdims=True)
    ok = U.any(1, keepdims=True) & (m0 > 1e-12) & (m0 < 1 - 1e-12) & (m1 > 1e-12) & (m1 < 1 - 1e-12)
    c = np.log(np.where(ok, m0, .5) * np.where(ok, 1 - m1, .5)) - np.log(np.where(ok, 1 - m0, .5) * np.where(ok, m1, .5))
    return np.where(U & ok, lw + c, lw)


class Base:
    name = "base"
    def __init__(self, S, K, **kw):
        self.S, self.K = S, K; self.__dict__.update(kw); self.known = np.zeros((S, K), bool); self.t = 0
    def report(self, w): return w
    def weights(self, awake, ctx): raise NotImplementedError
    def update(self, p, y, awake, observed, w, ctx): self.t += 1


class Equal(Base):
    name = "EQUAL"
    def weights(self, awake, ctx): return _norm(awake.astype(float), awake)


class Static(Base):
    """Fixed weights frozen after a calibration prefix; unknown-at-calibration experts get the mean weight."""
    name = "STATIC"
    def __init__(self, S, K, kappa=30., Tcal=800, **kw):
        super().__init__(S, K, kappa=kappa, Tcal=Tcal); self.sl = np.zeros((S, K)); self.n = np.zeros((S, K)); self.fw = None
    def weights(self, awake, ctx):
        if self.fw is None: return _norm(awake.astype(float), awake)
        return _norm(self.fw, awake)
    def update(self, p, y, awake, observed, w, ctx):
        self.t += 1
        if self.fw is None:
            self.sl += np.where(observed, brier(p, y), 0); self.n += observed
            if self.t >= self.Tcal:
                m = np.where(self.n > 0, self.sl / np.maximum(self.n, 1), np.nan); best = np.nanmin(m, 1, keepdims=True)
                fw = np.exp(-self.kappa * (m - best)); avg = np.nanmean(fw, 1, keepdims=True)
                self.fw = np.where(np.isnan(fw), avg, fw)


class WTA(Base):
    """Follow-the-leader on mean observed loss, prior 5 pseudo-observations at loss 0.25 (chance)."""
    name = "WTA"
    def __init__(self, S, K, **kw):
        super().__init__(S, K); self.sl = np.full((S, K), 5 * 0.25); self.n = np.full((S, K), 5.0)
    def weights(self, awake, ctx):
        m = np.where(awake, self.sl / self.n, np.inf); j = m.argmin(1)
        w = np.zeros((self.S, self.K)); w[np.arange(self.S), j] = 1; return np.where(awake.any(1)[:, None], w, 0)
    def update(self, p, y, awake, observed, w, ctx):
        self.t += 1; self.sl += np.where(observed, brier(p, y), 0); self.n += observed


class EWMA(Base):
    name = "EWMA"
    def __init__(self, S, K, alpha=0.03, beta=20., inactive_neg=False, missing_neg=False, **kw):
        super().__init__(S, K, alpha=alpha, beta=beta, inactive_neg=inactive_neg, missing_neg=missing_neg); self.m = np.full((S, K), 0.25)
    def weights(self, awake, ctx): return _softmax_masked(-self.beta * self.m, awake)
    def update(self, p, y, awake, observed, w, ctx):
        self.t += 1; l = brier(p, y); upd = observed.copy()
        l = np.where(observed, l, NEG)
        if self.inactive_neg: upd |= ~awake
        if self.missing_neg: upd |= (awake & ~observed)
        self.m = np.where(upd, (1 - self.alpha) * self.m + self.alpha * l, self.m)


class HedgeCum(Base):
    """Naive masked Hedge: softmax of -eta * cumulative observed loss (NOT sleeping-safe: fewer observations => smaller sum)."""
    name = "HEDGE_CUM"
    def __init__(self, S, K, eta=3., **kw):
        super().__init__(S, K, eta=eta); self.L = np.zeros((S, K))
    def weights(self, awake, ctx):
        new = awake & ~self.known
        if new.any():
            kn = self.known; mean = np.where(kn.any(1), (self.L * kn).sum(1) / np.maximum(kn.sum(1), 1), 0)
            self.L = np.where(new, mean[:, None], self.L); self.known |= awake
        return _softmax_masked(-self.eta * self.L, awake)
    def update(self, p, y, awake, observed, w, ctx):
        self.t += 1; self.L += np.where(observed, brier(p, y), 0)


class SleepHedge(Base):
    """Specialist/sleeping-experts multiplicative weights (Freund et al. 1997 abstention trick; Blum-Mansour relative update).
    Persistent log-weights; asleep experts frozen; unobserved-awake experts frozen; loss centred on the mixture of the updated set.
    Optional: fixed-share alpha, discount gamma (clock vs awake), mixing-past-posteriors, loss 'brier'|'log', centring, neg-ablations."""
    name = "SLEEP_HEDGE"
    def __init__(self, S, K, eta=10., alpha=0., gamma=1., disc="awake", mpp=0., loss="brier", centre=True,
                 inactive_neg=False, missing_neg=False, kappa=None, floor=0., keepmass=True, **kw):
        super().__init__(S, K, eta=eta, alpha=alpha, gamma=gamma, disc=disc, mpp=mpp, loss=loss, centre=centre,
                         inactive_neg=inactive_neg, missing_neg=missing_neg, floor=floor, keepmass=keepmass)
        self.lw = np.zeros((S, K)); self.vbar = np.zeros((S, K)); self.nb = 0
        if kappa is not None: self.eta = kappa
    def _enter(self, awake):
        new = awake & ~self.known
        if new.any():
            kn = self.known; cnt = kn.sum(1)
            mean = np.where(cnt > 0, (self.lw * kn).sum(1) / np.maximum(cnt, 1), 0.0)     # geometric-mean entry
            self.lw = np.where(new, mean[:, None], self.lw); self.known |= awake
    def weights(self, awake, ctx):
        self._enter(awake); w = _softmax_masked(self.lw, awake)
        if self.floor > 0:
            n = awake.sum(1, keepdims=True); w = np.where(awake, (1 - self.floor) * w + self.floor / np.maximum(n, 1), 0)
        return w
    def _loss(self, p, y): return brier(p, y) if self.loss == "brier" else logloss(p, y)
    def update(self, p, y, awake, observed, w, ctx):
        self.t += 1; l = self._loss(p, y); U = observed.copy()
        pen = NEG if self.loss == "brier" else -np.log(0.25)
        l = np.where(observed, l, pen)
        if self.inactive_neg: U |= ~awake
        if self.missing_neg: U |= (awake & ~observed)
        wu = np.where(observed, w, 0.0); sw = wu.sum(1, keepdims=True)
        lhat = np.where(sw > 0, (wu * l).sum(1, keepdims=True) / np.where(sw > 0, sw, 1), 0.0)
        if not self.centre: lhat = 0.0
        vk = _softmax_masked(self.lw, self.known)
        m0 = np.where(U, vk, 0).sum(1, keepdims=True)
        lw = np.where(U, self.lw - self.eta * (l - lhat), self.lw)
        if self.centre and (self.inactive_neg or self.missing_neg) is False:
            pass
        # keep the updated block's total posterior mass fixed (specialist normalisation)
        if self.keepmass: lw = _keep_mass(lw, self.known, U, m0)
        if self.gamma < 1:                                   # decay toward uniform-over-known (log-weights centred)
            kn = self.known; c = (lw * kn).sum(1, keepdims=True) / np.maximum(kn.sum(1, keepdims=True), 1)
            dec = self.known if self.disc == "clock" else U
            lw = np.where(dec, c + self.gamma * (lw - c), lw)
        if self.alpha > 0 or self.mpp > 0:
            v = _softmax_masked(lw, self.known); kk = np.maximum(self.known.sum(1, keepdims=True), 1)
            if self.alpha > 0: v = (1 - self.alpha) * v + self.alpha * self.known / kk
            if self.mpp > 0 and self.nb > 0: v = (1 - self.mpp) * v + self.mpp * self.vbar
            lw = np.where(self.known, np.log(np.maximum(v, 1e-300)), lw)
            self.vbar = (self.vbar * self.nb + v) / (self.nb + 1); self.nb += 1
        self.lw = lw - np.where(self.known, lw, -np.inf).max(1, keepdims=True).clip(-1e9)


class EG(Base):
    """Exponentiated Gradient on the mixture Brier loss (gradient 2(yhat-y)p_i), sleeping-adapted; centred (default) or raw."""
    name = "EG"
    def __init__(self, S, K, eta=1., centre=True, keepmass=True, **kw):
        super().__init__(S, K, eta=eta, centre=centre, keepmass=keepmass); self.h = SleepHedge(S, K, eta=1.0)
    def weights(self, awake, ctx): return self.h.weights(awake, ctx)
    def update(self, p, y, awake, observed, w, ctx):
        h = self.h; h.t += 1; wu = np.where(observed, w, 0.0); sw = wu.sum(1, keepdims=True)
        yhat = np.where(sw > 0, (wu * p).sum(1, keepdims=True) / np.where(sw > 0, sw, 1), 0.5)
        g = 2 * (yhat - y[:, None]) * p
        gbar = np.where(sw > 0, (wu * g).sum(1, keepdims=True) / np.where(sw > 0, sw, 1), 0.0) if self.centre else 0.0
        U = observed; vk = _softmax_masked(h.lw, h.known); m0 = np.where(U, vk, 0).sum(1, keepdims=True)
        lw = np.where(U, h.lw - self.eta * (g - gbar), h.lw)
        if self.keepmass: lw = _keep_mass(lw, h.known, U, m0)
        h.lw = lw - np.where(h.known, lw, -np.inf).max(1, keepdims=True).clip(-1e9)


class ContextMix(Base):
    """Product-of-experts weights: global log-weight + per-context offset (context = observable, 10%-corrupted regime label)."""
    name = "CONTEXT_MIX"
    def __init__(self, S, K, eta_g=3., eta_c=10., nctx=4, **kw):
        super().__init__(S, K, eta_g=eta_g, eta_c=eta_c); self.lwg = np.zeros((S, K)); self.lwc = np.zeros((S, nctx, K)); self.ar = np.arange(S)
    def _tot(self, ctx): return self.lwg + self.lwc[self.ar, ctx]
    def weights(self, awake, ctx):
        new = awake & ~self.known
        if new.any():
            kn = self.known; cnt = kn.sum(1); mean = np.where(cnt > 0, (self.lwg * kn).sum(1) / np.maximum(cnt, 1), 0.0)
            self.lwg = np.where(new, mean[:, None], self.lwg); self.known |= awake
        return _softmax_masked(self._tot(ctx), awake)
    def update(self, p, y, awake, observed, w, ctx):
        self.t += 1; l = brier(p, y); wu = np.where(observed, w, 0.0); sw = wu.sum(1, keepdims=True)
        lhat = np.where(sw > 0, (wu * l).sum(1, keepdims=True) / np.where(sw > 0, sw, 1), 0.0); d = np.where(observed, l - lhat, 0.0)
        self.lwg = self.lwg - self.eta_g * d; self.lwc[self.ar, ctx] = self.lwc[self.ar, ctx] - self.eta_c * d
        self.lwg -= np.where(self.known, self.lwg, -np.inf).max(1, keepdims=True).clip(-1e9)


class Diversity(Base):
    """Base sleeping learner (fixed-share) + redundancy discount w_i /= n_i^theta, n_i = sum_j awake sim_ij, sim = clip(corr of forecast residuals)^2.
    Uses only forecasts (label-free), so unaffected by missing evidence."""
    name = "DIVERSITY"
    def __init__(self, S, K, eta=10., alpha=0.01, theta=1., beta=0.01, **kw):
        super().__init__(S, K, theta=theta, beta=beta); self.base = SleepHedge(S, K, eta=eta, alpha=alpha)
        self.C = np.zeros((S, K, K)); self.Cn = np.zeros((S, K, K))
    def _n(self, awake):
        d = np.sqrt(np.maximum(np.einsum("skk->sk", self.C), 1e-9)); corr = self.C / (d[:, :, None] * d[:, None, :])
        sim = np.clip(corr, 0, 1) ** 2; m = awake[:, :, None] & awake[:, None, :]
        sim = np.where(m, sim, 0); idx = np.arange(self.K); sim[:, idx, idx] = 1.0
        return np.where(awake, np.where(m, sim, 0).sum(2), 1.0)
    def weights(self, awake, ctx):
        w = self.base.weights(awake, ctx)
        if self.theta > 0 and self.t > 50: w = _norm(w / self._n(awake) ** self.theta, awake)
        return w
    def update(self, p, y, awake, observed, w, ctx):
        self.t += 1
        # base learner is updated with ITS OWN weights so that its posterior is not distorted by the discount
        wb = self.base.weights(awake, ctx); self.base.update(p, y, awake, observed, wb, ctx)
        lg = np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4))); n = awake.sum(1, keepdims=True)
        mu = np.where(n > 0, (lg * awake).sum(1, keepdims=True) / np.maximum(n, 1), 0); r = np.where(awake, lg - mu, 0)
        pm = awake[:, :, None] & awake[:, None, :]; upd = r[:, :, None] * r[:, None, :]
        self.C = np.where(pm, (1 - self.beta) * self.C + self.beta * upd, self.C)


class BMA(SleepHedge):
    """Bayesian model averaging with abstention-as-mixture predictive (= specialist Bayes): posterior update on log-loss, tempering kappa."""
    name = "BMA"
    def __init__(self, S, K, kappa=1., **kw): super().__init__(S, K, eta=kappa, loss="log")


class Exp3(Base):
    """Bandit comparison: EXP3 restricted to awake set, one expert sampled per round, importance-weighted loss feedback for that expert only."""
    name = "EXP3"
    def __init__(self, S, K, eta=1., gamma=0.05, seed=0, **kw):
        super().__init__(S, K, eta=eta, gamma=gamma); self.lw = np.zeros((S, K)); self.rng = np.random.default_rng(seed); self.pi = None
    def weights(self, awake, ctx):
        pi = _softmax_masked(self.lw, awake); n = np.maximum(awake.sum(1, keepdims=True), 1)
        pi = np.where(awake, (1 - self.gamma) * pi + self.gamma / n, 0); self.pi = pi
        u = self.rng.random((self.S, 1)); j = np.minimum((np.cumsum(pi, 1) < u).sum(1), self.K - 1)
        w = np.zeros((self.S, self.K)); w[np.arange(self.S), j] = 1; self.j = j
        return np.where(awake.any(1)[:, None], w, 0)
    def report(self, w): return self.pi
    def update(self, p, y, awake, observed, w, ctx):
        self.t += 1; a = np.arange(self.S); ok = observed[a, self.j] & awake.any(1); l = brier(p, y)[a, self.j]
        est = np.where(ok, l / np.maximum(self.pi[a, self.j], 1e-3), 0.0)
        self.lw[a, self.j] -= self.eta * est; self.lw -= self.lw.max(1, keepdims=True)


class EpsGreedy(Base):
    name = "EPS_GREEDY"
    def __init__(self, S, K, eps=0.1, alpha=0.05, seed=0, **kw):
        super().__init__(S, K, eps=eps, alpha=alpha); self.m = np.full((S, K), 0.25); self.rng = np.random.default_rng(seed)
    def weights(self, awake, ctx):
        j = np.where(awake, self.m, np.inf).argmin(1); n = awake.sum(1)
        rj = np.minimum((self.rng.random(self.S) * np.maximum(n, 1)).astype(int), np.maximum(n, 1) - 1)
        ridx = np.array([np.flatnonzero(a)[r] if a.any() else 0 for a, r in zip(awake, rj)])
        j = np.where(self.rng.random(self.S) < self.eps, ridx, j); self.j = j
        w = np.zeros((self.S, self.K)); w[np.arange(self.S), j] = 1; return np.where(awake.any(1)[:, None], w, 0)
    def update(self, p, y, awake, observed, w, ctx):
        self.t += 1; a = np.arange(self.S); ok = observed[a, self.j]; l = brier(p, y)[a, self.j]
        self.m[a, self.j] = np.where(ok, (1 - self.alpha) * self.m[a, self.j] + self.alpha * l, self.m[a, self.j])


class Oracle(Base):
    """Reference only (uses the true noise sd): inverse-variance weights over awake experts. Not a candidate."""
    name = "ORACLE"
    def __init__(self, S, K, sdt=None, **kw): super().__init__(S, K); self.sdt = sdt
    def weights(self, awake, ctx): return _norm(np.where(awake, 1 / np.nan_to_num(self.sdt, nan=1.0) ** 2, 0), awake)
