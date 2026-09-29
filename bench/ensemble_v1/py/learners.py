"""Online ensemble learners over a roster of K strategy 'experts' with sleeping semantics.

Interface
  weights(alloc, ctx) -> w (K,), w>=0, sum(w)=1, support inside alloc
  update(alloc, obs, r, exist, ctx)   obs subset of exist; r valid only where obs
Feedback is full-information among observed experts (shadow returns), except bandit variants.
Losses: l = 1 - r, r in [0,1].

Semantics ("correct" mode): learner state of an expert is touched ONLY when that expert is observed.
INACTIVE / ABSTAIN / GAP / NOT_EXIST rounds leave its state frozen.  The runner's "naive_zero" mode
instead feeds r=0 (worst) for every existing expert that was not observed - the failure mode
'missing evidence == negative evidence' - to measure what that semantic error costs.
"""
import numpy as np


def _norm(v, mask):
    x = np.where(mask, v, 0.0)
    s = x.sum()
    if s <= 0 or not np.isfinite(s):
        return mask / max(mask.sum(), 1)
    return x / s


def _softmax(score, mask):
    z = np.where(mask, score, -np.inf)
    z = z - z[mask].max()
    e = np.exp(z)
    e[~mask] = 0.0
    return e / e.sum()


def bound(w, alloc, floor=0.0, cap=1.0):
    """Bounded adaptive weighting: mix with uniform (floor as fraction of the uniform share) and
    cap each weight (water-filling)."""
    n = alloc.sum()
    if floor > 0:
        w = (1 - floor) * w + floor * alloc / n
    if cap * n < 1.0 or cap >= 1.0:
        return w
    for _ in range(8):
        over = w > cap
        if not over.any():
            break
        excess = (w[over] - cap).sum()
        w = np.where(over, cap, w)
        free = alloc & ~over
        if not free.any():
            break
        w = w + excess * w * free / w[free].sum()
    return w


class Base:
    name = "base"

    def __init__(self, K, **hp):
        self.K = K
        self.hp = hp
        self.seen = np.zeros(K, bool)

    def _register(self, exist):
        new = exist & ~self.seen
        if new.any():
            self.on_new(new)
            self.seen |= new

    def on_new(self, new):
        pass

    def weights(self, alloc, ctx):
        raise NotImplementedError

    def update(self, alloc, obs, r, exist, ctx):
        raise NotImplementedError

    def fingerprint(self):
        """State snapshot used by the semantics unit tests."""
        out = []
        for k, v in sorted(self.__dict__.items()):
            if isinstance(v, np.ndarray):
                out.append(v.copy())
        return out


# ---------------------------------------------------------------- baselines
class Equal(Base):
    name = "Equal"

    def weights(self, alloc, ctx):
        return alloc / alloc.sum()

    def update(self, alloc, obs, r, exist, ctx):
        pass


class _Score(Base):
    """Per-expert EWMA score initialised at cohort mean when first seen (no optimism, no penalty)."""

    def __init__(self, K, a=0.05, **hp):
        super().__init__(K, **hp)
        self.a = a
        self.s = np.full(K, 0.5)
        self.got = np.zeros(K, bool)      # has any observation

    def _cohort(self):
        return self.s[self.got].mean() if self.got.any() else 0.5

    def _score_update(self, obs, r):
        for i in np.where(obs)[0]:
            if not self.got[i]:
                self.s[i] = self._cohort()
                self.got[i] = True
            self.s[i] += self.a * (r[i] - self.s[i])

    def _eff(self, alloc):
        s = self.s.copy()
        s[~self.got] = self._cohort()
        return s


class EWMA(_Score):
    name = "EWMA"

    def __init__(self, K, a=0.05, beta=30.0, **hp):
        super().__init__(K, a=a, **hp)
        self.beta = beta

    def weights(self, alloc, ctx):
        return _softmax(self.beta * self._eff(alloc), alloc)

    def update(self, alloc, obs, r, exist, ctx):
        self._register(exist)
        self._score_update(obs, r)


class WTA(_Score):
    name = "WTA"

    def weights(self, alloc, ctx):
        s = np.where(alloc, self._eff(alloc), -np.inf)
        w = np.zeros(self.K)
        w[int(np.argmax(s))] = 1.0
        return w

    def update(self, alloc, obs, r, exist, ctx):
        self._register(exist)
        self._score_update(obs, r)


class Static(Base):
    """Weights fixed after a calibration window (equal weights during it)."""
    name = "Static"

    def __init__(self, K, C=250, kappa=20.0, **hp):
        super().__init__(K, **hp)
        self.C, self.kappa = C, kappa
        self.t = 0
        self.sum = np.zeros(K)
        self.n = np.zeros(K)
        self.w = None

    def weights(self, alloc, ctx):
        if self.w is None:
            return alloc / alloc.sum()
        w = self.w.copy()
        w[~self.fixed] = w[self.fixed].mean() if self.fixed.any() else 1.0
        return _norm(w, alloc)

    def update(self, alloc, obs, r, exist, ctx):
        self.t += 1
        if self.w is None:
            self.sum[obs] += r[obs]
            self.n[obs] += 1
            if self.t >= self.C:
                have = self.n > 0
                m = np.where(have, self.sum / np.maximum(self.n, 1), 0)
                m0 = m[have].mean() if have.any() else 0.5
                m = np.where(have, m, m0)
                self.fixed = have
                self.w = np.exp(self.kappa * (m - m.max()))
                self.w /= self.w.sum()


# ---------------------------------------------------------------- expert-advice family
class HedgePlain(Base):
    """Classic Hedge on cumulative loss; unobserved rounds simply add nothing.
    Known flaw (the point of specialists): totals over different exposure lengths are compared."""
    name = "HedgePlain"

    def __init__(self, K, eta=5.0, **hp):
        super().__init__(K, **hp)
        self.eta = eta
        self.L = np.zeros(K)

    def on_new(self, new):
        old = self.seen
        self.L[new] = self.L[old].mean() if old.any() else 0.0

    def weights(self, alloc, ctx):
        return _softmax(-self.eta * self.L, alloc)

    def update(self, alloc, obs, r, exist, ctx):
        self._register(exist)
        self.L[obs] += 1.0 - r[obs]


class SleepHedge(Base):
    """Specialist / sleeping-expert Hedge with optional fixed-share (Freund et al. 1997 update:
    only observed experts move, total observed mass is preserved). alpha>0 => sleeping fixed-share.
    B (log-weight bound) and floor/cap implement bounded adaptive weighting."""
    name = "SleepHedge"

    def __init__(self, K, eta=10.0, alpha=0.0, B=None, floor=0.0, cap=1.0, gamma=1.0, dorm="freeze", **hp):
        super().__init__(K, **hp)
        self.eta, self.alpha, self.B, self.floor, self.cap = eta, alpha, B, floor, cap
        self.gamma, self.dorm = gamma, dorm
        self.lp = np.zeros(K)          # log persistent weights (over all seen experts)
        self.ex = np.zeros(K, bool)

    def on_new(self, new):
        if self.seen.any():
            m = self.lp[self.seen]
            init = m.max() + np.log(np.exp(m - m.max()).sum()) - np.log(self.seen.sum())
        else:
            init = 0.0
        self.lp[new] = init

    def weights(self, alloc, ctx):
        w = _softmax(self.lp, alloc)
        if self.floor > 0 or self.cap < 1.0:
            w = bound(w, alloc, self.floor, self.cap)
        return w

    def _specialist_step(self, obs, r):
        if not obs.any():
            return
        idx = np.where(obs)[0]
        old = self.lp[idx]
        new = old - self.eta * (1.0 - r[idx])
        # preserve observed mass
        lo = old.max() + np.log(np.exp(old - old.max()).sum())
        ln = new.max() + np.log(np.exp(new - new.max()).sum())
        self.lp[idx] = new - ln + lo

    def update(self, alloc, obs, r, exist, ctx):
        self._register(exist)
        self.ex = exist.copy()
        self._specialist_step(obs, r)
        self._post(obs, exist)

    def _post(self, obs, exist):
        seen = self.seen & self.ex
        if self.gamma < 1.0:
            m = self.lp[seen].mean()
            self.lp[seen] -= m
            tgt = seen if self.dorm == "amnesty" else obs
            self.lp[tgt] *= self.gamma
        if self.alpha > 0:
            p = np.exp(self.lp[seen] - self.lp[seen].max())
            p /= p.sum()
            p = (1 - self.alpha) * p + self.alpha / seen.sum()
            self.lp[seen] = np.log(p)
        if self.B is not None:
            mx = self.lp[seen].max()
            self.lp[seen] = np.maximum(self.lp[seen], mx - self.B)


class SleepEG(SleepHedge):
    """Exponentiated Gradient (Kivinen-Warmuth / Helmbold et al.) on reward with specialist mass
    preservation: gradient g_i = r_i / (w.r) over the observed set."""
    name = "SleepEG"

    def _specialist_step(self, obs, r):
        if not obs.any():
            return
        idx = np.where(obs)[0]
        old = self.lp[idx]
        w = np.exp(old - old.max())
        w /= w.sum()
        yhat = max((w * r[idx]).sum(), 1e-6)
        new = old + self.eta * r[idx] / yhat
        lo = old.max() + np.log(np.exp(old - old.max()).sum())
        ln = new.max() + np.log(np.exp(new - new.max()).sum())
        self.lp[idx] = new - ln + lo


class BMA(Base):
    """Gaussian-conjugate posterior-mean averaging with forgetting (DMA-style).
    theta_i ~ N(m0, s0^2) prior, shrunk towards the cohort mean; evidence count n_i is discounted
    per OBSERVATION (dormant experts are frozen); opt>0 adds an optimism bonus opt/sqrt(n+n0)."""
    name = "BMA"

    def __init__(self, K, kappa=30.0, lam=0.98, n0=10.0, opt=0.0, **hp):
        super().__init__(K, **hp)
        self.kappa, self.lam, self.n0, self.opt = kappa, lam, n0, opt
        self.n = np.zeros(K)
        self.S = np.zeros(K)

    def _theta(self):
        have = self.n > 0
        raw = np.where(have, self.S / np.maximum(self.n, 1e-9), 0.5)
        m0 = raw[have].mean() if have.any() else 0.5
        th = (self.S + self.n0 * m0) / (self.n + self.n0)
        return th + self.opt / np.sqrt(self.n + self.n0)

    def weights(self, alloc, ctx):
        return _softmax(self.kappa * self._theta(), alloc)

    def update(self, alloc, obs, r, exist, ctx):
        self._register(exist)
        self.n[obs] = self.lam * self.n[obs] + 1.0
        self.S[obs] = self.lam * self.S[obs] + r[obs]


class CtxMix(Base):
    """Context-conditioned mixture: per-context SleepHedge weights blended with a global vector;
    the blend trusts a context after ~n0 rounds of evidence in it. ctx_key selects the label."""
    name = "CtxMix"

    def __init__(self, K, eta=10.0, n0=60.0, ctx_key="regime", nctx=4, alpha=0.0, **hp):
        super().__init__(K, **hp)
        self.g = SleepHedge(K, eta=eta, alpha=alpha)
        self.c = [SleepHedge(K, eta=eta, alpha=alpha) for _ in range(nctx)]
        self.nc = np.zeros(nctx)
        self.n0, self.key = n0, ctx_key

    def _label(self, ctx):
        return int(ctx[self.key])

    def weights(self, alloc, ctx):
        c = self._label(ctx)
        lam = self.nc[c] / (self.nc[c] + self.n0)
        return (1 - lam) * self.g.weights(alloc, ctx) + lam * self.c[c].weights(alloc, ctx)

    def update(self, alloc, obs, r, exist, ctx):
        self._register(exist)
        c = self._label(ctx)
        self.g.update(alloc, obs, r, exist, ctx)
        self.c[c].update(alloc, obs, r, exist, ctx)
        if obs.any():
            self.nc[c] += 1

    def fingerprint(self):
        return self.g.fingerprint() + sum((x.fingerprint() for x in self.c), []) + [self.nc.copy()]


class Div(Base):
    """Diversity-aware wrapper: divide the base weights by a crowding factor built from online
    pairwise correlation of co-observed rewards (only pairs above tau count)."""
    name = "Div"

    def __init__(self, K, base, tau=0.5, a=0.02, minco=40, **hp):
        super().__init__(K, **hp)
        self.base, self.tau, self.a, self.minco = base, tau, a, minco
        self.m = np.zeros(K)
        self.C = np.zeros((K, K))
        self.co = np.zeros((K, K))
        self.have = np.zeros(K, bool)

    def weights(self, alloc, ctx):
        w = self.base.weights(alloc, ctx)
        d = np.sqrt(np.maximum(np.diag(self.C), 1e-12))
        rho = self.C / np.outer(d, d)
        rho = np.where(self.co >= self.minco, rho, 0.0)
        pen = np.clip((rho - self.tau) / (1 - self.tau), 0, None)
        np.fill_diagonal(pen, 1.0)
        crowd = (pen * alloc[None, :]).sum(1)
        return _norm(w / np.maximum(crowd, 1.0), alloc)

    def update(self, alloc, obs, r, exist, ctx):
        self._register(exist)
        self.base.update(alloc, obs, r, exist, ctx)
        for i in np.where(obs & ~self.have)[0]:
            self.m[i] = r[i]
            self.have[i] = True
        dm = np.where(obs, r - self.m, 0.0)
        M = np.outer(obs, obs)
        self.C = np.where(M, self.C + self.a * (np.outer(dm, dm) - self.C), self.C)
        self.co += M
        self.m = np.where(obs, self.m + self.a * (r - self.m), self.m)

    def fingerprint(self):
        return self.base.fingerprint() + [self.m.copy(), self.C.copy(), self.co.copy()]


# ---------------------------------------------------------------- bandit comparators
class SleepEXP3(Base):
    """EXP3 with sleeping availability (renormalise over awake), fixed-share; bandit feedback:
    only the sampled expert's reward is used.  weights() returns the sampling distribution."""
    name = "SleepEXP3"

    def __init__(self, K, eta=0.05, gamma=0.05, alpha=0.002, **hp):
        super().__init__(K, **hp)
        self.eta, self.gamma, self.alpha = eta, gamma, alpha
        self.lp = np.zeros(K)
        self.q = None

    def on_new(self, new):
        self.lp[new] = self.lp[self.seen].max() if self.seen.any() else 0.0   # optimistic newcomer

    def weights(self, alloc, ctx):
        n = alloc.sum()
        self.q = (1 - self.gamma) * _softmax(self.lp, alloc) + self.gamma * alloc / n
        return self.q

    def update(self, alloc, obs, r, exist, ctx):
        self._register(exist)
        a = ctx["rng"].choice(self.K, p=self.q)
        if obs[a]:
            self.lp[a] += self.eta * r[a] / max(self.q[a], 1e-3)
        seen = self.seen & exist
        if self.alpha > 0:
            p = np.exp(self.lp[seen] - self.lp[seen].max())
            p /= p.sum()
            p = (1 - self.alpha) * p + self.alpha / seen.sum()
            self.lp[seen] = np.log(p)
        self.lp -= self.lp[seen].max()


class DUCB(Base):
    """Discounted UCB with sleeping availability; hard choice (one expert)."""
    name = "DUCB"

    def __init__(self, K, gamma=0.99, c=0.15, **hp):
        super().__init__(K, **hp)
        self.gamma, self.c = gamma, c
        self.N = np.zeros(K)
        self.S = np.zeros(K)
        self.choice = 0

    def weights(self, alloc, ctx):
        tot = max(self.N.sum(), 1.0)
        idx = np.where(self.N < 1e-9, np.inf,
                       self.S / np.maximum(self.N, 1e-9) + self.c * np.sqrt(np.log(tot + 1) / np.maximum(self.N, 1e-9)))
        idx = np.where(alloc, idx, -np.inf)
        self.choice = int(np.argmax(idx))
        w = np.zeros(self.K)
        w[self.choice] = 1.0
        return w

    def update(self, alloc, obs, r, exist, ctx):
        self._register(exist)
        a = self.choice
        # discount only the pulled arm's statistics (frozen otherwise) to keep dormancy neutral
        if obs[a]:
            self.N[a] = self.gamma * self.N[a] + 1
            self.S[a] = self.gamma * self.S[a] + r[a]
