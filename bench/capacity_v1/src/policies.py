"""Allocation policies. All implementable policies use ONLY View + Pub + their own feedback history.
Score semantics: score = estimate of total gross edge (bps) if held for the full (unknown) duration."""
import math
import numpy as np

PRIOR_HOLD = 6.0
PRIOR_SCORE = 15.0


class Base:
    IMPLEMENTABLE = True
    name = "base"
    def __init__(self, **p):
        self.p = p
    def reset(self, pub, K, seed):
        self.pub, self.K = pub, K
        N = pub.N
        self.rng = np.random.default_rng(seed + 424242)
        self.h_est = np.full(N, PRIOR_HOLD); self.h_n = np.zeros(N)
        self.s_sum = 0.0; self.s_n = 0
        self.m_i = np.full(N, np.nan); self.n_i = np.zeros(N)
        self.admits = np.zeros(N)
        self.last_feat = {}
    # ---- feedback (public / realised-after-close) ----
    def on_emit(self, t, i, s):
        if not math.isnan(s):
            self.s_sum += s; self.s_n += 1
            self.m_i[i] = s if math.isnan(self.m_i[i]) else 0.8 * self.m_i[i] + 0.2 * s
            self.n_i[i] += 1
    def on_close(self, i, hold, net, gross, feat, t):
        self.h_n[i] += 1
        a = max(0.2, 1.0 / (self.h_n[i] + 1))
        self.h_est[i] = (1 - a) * self.h_est[i] + a * hold
    # ---- helpers ----
    def gmean(self):
        return self.s_sum / self.s_n if self.s_n else PRIOR_SCORE
    def sc(self, c):
        return c.score if not math.isnan(c.score) else self.gmean()   # missing != negative: neutral imputation
    def val(self, c):
        return self.sc(c) - self.pub.cost_est[c.inst]
    def rate(self, c):
        return self.val(c) / self.h_est[c.inst]
    def fill(self, view, order, ok=None):
        out, used = [], {o.inst for o in view.open}
        for c in order:
            if len(out) >= view.free:
                break
            if c.inst in used or (ok is not None and not ok(c)):
                continue
            out.append(c); used.add(c.inst)
        for c in out:
            self.admits[c.inst] += 1
        return out


class FIFO(Base):
    name = "FIFO"
    def select(self, t, view):
        return self.fill(view, view.cands)   # view.cands already sorted by first emission


class RoundRobin(Base):
    name = "ROUND_ROBIN"
    def reset(self, pub, K, seed):
        super().reset(pub, K, seed); self.ptr = 0
    def select(self, t, view):
        by = {}
        for c in view.cands:
            by.setdefault(c.inst, c)
        out = []; N = self.pub.N; used = {o.inst for o in view.open}
        for _ in range(view.free):
            for k in range(N):
                i = (self.ptr + k) % N
                if i in by and i not in used:
                    out.append(by[i]); used.add(i); self.ptr = (i + 1) % N; break
        for c in out: self.admits[c.inst] += 1
        return out


class RandomFixedSeed(Base):
    name = "RANDOM"
    def select(self, t, view):
        idx = self.rng.permutation(len(view.cands))
        return self.fill(view, [view.cands[k] for k in idx])


class EqualQuota(Base):
    name = "EQUAL_QUOTA"
    def select(self, t, view):
        order = sorted(view.cands, key=lambda c: (self.admits[c.inst], c.t_first, c.inst))
        return self.fill(view, order)


class OldestSlot(Base):
    """Turnover-neutral reference: FIFO admission; when full and candidates wait, evict oldest slot if age>=min_hold."""
    name = "OLDEST_SLOT"
    def evictions(self, t, view):
        mh = self.p.get("min_hold", 4)
        n_wait = len({c.inst for c in view.cands})
        cand = sorted([(t - o.t_in, k) for k, o in enumerate(view.open) if t - o.t_in >= mh], reverse=True)
        return [k for _, k in cand[:n_wait]]
    def select(self, t, view):
        return self.fill(view, view.cands)


class FIFOScreen(Base):
    name = "FIFO_SCREEN"
    def select(self, t, view):
        return self.fill(view, view.cands, ok=lambda c: self.val(c) > 0)


class ScoreRank(Base):
    name = "SCORE_RANK"
    def select(self, t, view):
        return self.fill(view, sorted(view.cands, key=lambda c: -self.val(c)), ok=lambda c: self.val(c) > 0)


class SlotHour(Base):
    name = "SLOTHOUR"
    def select(self, t, view):
        return self.fill(view, sorted(view.cands, key=lambda c: -self.rate(c)), ok=lambda c: self.val(c) > 0)


class SlotHourShadow(Base):
    """Admit only if predicted net/hold-hour >= theta * lambda, lambda = EWMA of predicted rate of admitted trades (opportunity cost)."""
    name = "SLOTHOUR_SHADOW"
    def reset(self, pub, K, seed):
        super().reset(pub, K, seed); self.lam = 0.0; self.lam_n = 0
    def select(self, t, view):
        th = self.p.get("theta", 0.75)
        thr = th * self.lam
        out = self.fill(view, sorted(view.cands, key=lambda c: -self.rate(c)),
                        ok=lambda c: self.val(c) > 0 and self.rate(c) >= thr)
        for c in out:
            self.lam_n += 1
            a = max(0.05, 1.0 / self.lam_n)
            self.lam = (1 - a) * self.lam + a * self.rate(c)
        return out


class UncertaintyLCB(Base):
    """Shrink score toward instrument score history (omega), rank by lower-confidence net rate (kappa * trade sd); missing => extra variance."""
    name = "UNCERTAINTY_LCB"
    def lcb(self, c):
        om, ka = self.p.get("omega", 0.3), self.p.get("kappa", 0.1)
        i = c.inst; hh = self.h_est[i]
        mi = self.m_i[i] if not math.isnan(self.m_i[i]) else self.gmean()
        if math.isnan(c.score):
            e = mi; extra = 15.0 ** 2
        else:
            e = (1 - om) * c.score + om * mi; extra = 0.0
        v = e - self.pub.cost_est[i]
        sd = math.sqrt(self.pub.sigma_pub[i] ** 2 * hh + extra)
        return (v - ka * sd) / hh, v
    def select(self, t, view):
        sc = {id(c): self.lcb(c) for c in view.cands}
        return self.fill(view, sorted(view.cands, key=lambda c: -sc[id(c)][0]), ok=lambda c: sc[id(c)][1] > 0)


class CorrAware(Base):
    """Greedy slot-hour rank with marginal-concentration penalty for positions in the same (public) group."""
    name = "CORR_AWARE"
    def select(self, t, view):
        g = self.p.get("gamma", 0.1); rho = 0.6
        sb = float(np.mean(self.pub.sigma_pub))
        load = {}
        for o in view.open:
            load[o.group] = load.get(o.group, 0.0) + self.pub.sigma_pub[o.inst] / sb
        out, used = [], {o.inst for o in view.open}
        rest = [c for c in view.cands if self.val(c) > 0]
        while rest and len(out) < view.free:
            best, bs = None, -1e18
            for c in rest:
                if c.inst in used:
                    continue
                pen = g * rho * (self.pub.sigma_pub[c.inst] / sb) * load.get(c.group, 0.0) * 5.0
                s = self.rate(c) - pen
                if s > bs:
                    best, bs = c, s
            if best is None:
                break
            out.append(best); used.add(best.inst)
            load[best.group] = load.get(best.group, 0.0) + self.pub.sigma_pub[best.inst] / sb
            rest = [c for c in rest if c is not best]
        for c in out: self.admits[c.inst] += 1
        return out


class LinTS(Base):
    """Linear Thompson sampling on delayed reward = realised net per hold-hour (feedback only at close; censored to admitted)."""
    name = "LINTS"
    D = 6
    def reset(self, pub, K, seed):
        super().reset(pub, K, seed)
        lam0 = self.p.get("prior_prec", 20.0)
        self.A = lam0 * np.eye(self.D); w0 = np.zeros(self.D); w0[1] = 1.0
        self.b = lam0 * w0
    def feats(self, c, view):
        i = c.inst; v = self.val(c); hh = self.h_est[i]
        gl = sum(1 for o in view.open if o.group == c.group) / self.K
        return np.array([1.0, v / hh / 5.0, v / 20.0, 1.0 if math.isnan(c.score) else 0.0, gl, math.log(hh) / 3.0])
    def select(self, t, view):
        a = self.p.get("alpha", 0.3)
        Ai = np.linalg.inv(self.A); mu = Ai @ self.b
        Sg = (Ai + Ai.T) / 2
        w = self.rng.multivariate_normal(mu, (a ** 2) * Sg)
        fs = {id(c): self.feats(c, view) for c in view.cands}
        sc = {k: float(x @ w) for k, x in fs.items()}
        out = self.fill(view, sorted(view.cands, key=lambda c: -sc[id(c)]), ok=lambda c: self.val(c) > 0)
        self.last_feat = {id(c): fs[id(c)] for c in out}
        return out
    def on_close(self, i, hold, net, gross, feat, t):
        super().on_close(i, hold, net, gross, feat, t)
        if feat is not None:
            y = max(-30.0, min(30.0, net / hold)) / 5.0
            self.A += np.outer(feat, feat); self.b += y * feat


class OracleGreedy(Base):
    """NOT IMPLEMENTABLE. Perfect-foresight greedy upper reference (realised net per hold-hour at entry). Also the leak-test canary."""
    IMPLEMENTABLE = False
    name = "ORACLE_GREEDY_UB"
    def attach(self, net_fn, hold_fn):
        self.net_fn, self.hold_fn = net_fn, hold_fn
    def select(self, t, view):
        r = {id(c): self.net_fn(c.inst, t) / self.hold_fn(c.inst, t) for c in view.cands}
        return self.fill(view, sorted(view.cands, key=lambda c: -r[id(c)]), ok=lambda c: r[id(c)] > 0)


REGISTRY = {
    "FIFO": FIFO, "ROUND_ROBIN": RoundRobin, "RANDOM": RandomFixedSeed, "EQUAL_QUOTA": EqualQuota,
    "OLDEST_SLOT": OldestSlot, "FIFO_SCREEN": FIFOScreen, "SCORE_RANK": ScoreRank, "SLOTHOUR": SlotHour,
    "SLOTHOUR_SHADOW": SlotHourShadow, "UNCERTAINTY_LCB": UncertaintyLCB, "CORR_AWARE": CorrAware, "LINTS": LinTS,
    "ORACLE_GREEDY_UB": OracleGreedy,
}
GRIDS = {
    "FIFO": [{}], "ROUND_ROBIN": [{}], "RANDOM": [{}], "EQUAL_QUOTA": [{}], "FIFO_SCREEN": [{}],
    "SCORE_RANK": [{}], "SLOTHOUR": [{}],
    "OLDEST_SLOT": [{"min_hold": m} for m in (2, 4, 8)],
    "SLOTHOUR_SHADOW": [{"theta": x} for x in (0.25, 0.5, 0.75, 1.0, 1.25)],
    "UNCERTAINTY_LCB": [{"omega": o, "kappa": k} for o in (0.0, 0.3, 0.6) for k in (0.0, 0.1, 0.3)],
    "CORR_AWARE": [{"gamma": g} for g in (0.02, 0.05, 0.1, 0.2, 0.4)],
    "LINTS": [{"alpha": a} for a in (0.1, 0.3, 0.6)],
}
def make(name, params=None):
    return REGISTRY[name](**(params or {}))
