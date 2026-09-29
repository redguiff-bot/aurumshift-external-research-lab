"""Deterministic synthetic world for capacity-allocation research (external, generic).

A World holds (a) OBSERVABLE streams (candidate emission events with scores, public instrument info)
and (b) HIDDEN latent arrays (true edge E, duration D, idiosyncratic Z, factor paths) that are only
used to settle trades AFTER admission. Policies never receive the hidden arrays.

Units: time step = 1 hour; edge/cost/pnl in bps (generic net-outcome abstraction).
gross(i,t,h) = (E[i,t]/D[i,t])*h + sigma_i*( rho_g*dCg + rho_m(t)*dCm + sqrt(1-rho_g^2-rho_m^2)*sqrt(h)*Z[i,t] )
net = gross - cost_i          (cost is charged once per admission; UNKNOWN cost != 0 is a POLICY-belief matter)
"""
import math, zlib
from dataclasses import dataclass
import numpy as np

PAD = 48  # max duration (hours) and settlement padding


@dataclass
class World:
    name: str
    seed: int
    N: int
    G: int
    W: int
    T: int
    group: np.ndarray
    sigma: np.ndarray
    sigma_pub: np.ndarray
    dmean: np.ndarray
    cost: np.ndarray
    rho_g: np.ndarray
    rho_m: np.ndarray
    E: np.ndarray
    D: np.ndarray
    Z: np.ndarray
    Cg: np.ndarray   # (G,T+1) cumulative group factor increments
    Cm: np.ndarray   # (T+1,)  cumulative market factor increments
    events: list     # events[t] = list of (inst, score)   -- OBSERVABLE
    meta: dict

    def hold(self, i, t):
        return int(min(PAD, max(1, math.ceil(self.D[i, t]))))

    def gross(self, i, t, h):
        D = self.D[i, t]
        h = int(h)
        g = self.group[i]
        rg, rm = self.rho_g[g], self.rho_m[t]
        idio = math.sqrt(max(1e-9, 1.0 - rg * rg - rm * rm))
        r = self.E[i, t] / D
        return (r * h + self.sigma[i] * (rg * (self.Cg[g, t + h] - self.Cg[g, t])
                + rm * (self.Cm[t + h] - self.Cm[t]) + idio * math.sqrt(h) * self.Z[i, t]))


# --------------------------------------------------------------------------------------
SPLITS = {  # structural variation between splits (so heldout is not the tuning world re-seeded)
    "tuning":     dict(N=10, G=5, edge=(6, 36), sig=(8, 20), dm=(3, 12), cost=(4, 9), tau=8.0, cv=0.6, ar_sd=5.0, ttl=4),
    "validation": dict(N=12, G=4, edge=(6, 36), sig=(8, 20), dm=(3, 12), cost=(4, 9), tau=9.0, cv=0.8, ar_sd=5.5, ttl=4),
    "heldout":    dict(N=15, G=5, edge=(5, 38), sig=(9, 22), dm=(3, 14), cost=(4, 10), tau=10.0, cv=0.7, ar_sd=6.0, ttl=4),
}
W_DEFAULT = 600

# Scenario overrides (multiplicative/absolute) on top of split base.
SCENARIOS = {
    "S1_sparse":        dict(load=0.4),
    "S2_moderate":      dict(load=1.2),
    "S3_chronic":       dict(load=3.5),
    "S4_late_hq":       dict(load=3.5, late_hq=True),
    "S5_correlated":    dict(load=3.0, rho_g=0.8, hi_group0=True, crisis=True),
    "S5b_corr_benign":  dict(load=3.0, rho_g=0.8, hi_group0=True, crisis=False),
    "S6_short_vs_long": dict(load=3.5, s6=True),
    "S7_regime_shift":  dict(load=3.0, flip=True),
    "S8_noisy_rank":    dict(load=3.0, tau_mult=2.5),
    "S9_missing":       dict(load=3.0, p_miss=0.5),
    "S10_spam":         dict(load=3.0, spam=True),
    "S11_burst":        dict(load=2.5, burst=True),
    "S12_near_equal":   dict(load=3.0, equal=True),
}
# Failure-mode extras (validation-split diagnostics only, never heldout)
FAILURE_SCENARIOS = {
    "F_score_gaming":     dict(load=3.0, gamer=True),
    "F_corr_collapse":    dict(load=3.0, rho_g=0.5, collapse=True),
    "F_inversion":        dict(load=3.0, cal="invert"),
    "F_poor_cal":         dict(load=3.0, cal="poor"),
    "F_stale":            dict(load=3.0, p_stale=0.6),
    "F_starve_skew":      dict(load=4.0, skew=True),
    "F_short_churn_cost": dict(load=3.5, s6=True, cost_mult=1.8),
}


def _rng(name, seed, split):
    return np.random.default_rng(zlib.crc32(f"{name}|{split}".encode()) + 1000003 * seed)


def build_world(name, seed, split="heldout", overrides=None, W=W_DEFAULT):
    sp = dict(SPLITS[split])
    spec = dict(SCENARIOS.get(name) or FAILURE_SCENARIOS.get(name) or {})
    if overrides:
        spec.update(overrides)
    rng = _rng(name, seed, split)
    N, G = sp["N"], sp["G"]
    T = W + PAD
    per = N // G
    group = np.minimum(np.arange(N) // per, G - 1)
    # static instrument attributes
    mu = rng.uniform(*sp["edge"], N)
    sigma = rng.uniform(*sp["sig"], N)
    dmean = rng.uniform(*sp["dm"], N)
    cost = rng.uniform(*sp["cost"], N) * spec.get("cost_mult", 1.0)
    ar_sd = sp["ar_sd"]
    tau = sp["tau"] * spec.get("tau_mult", 1.0)
    cv = spec.get("cv", sp["cv"])
    rho_g = np.full(G, spec.get("rho_g", 0.35))
    if spec.get("hi_group0"):
        mu[group == 0] = rng.uniform(28, 38, (group == 0).sum())
        mu[group != 0] = rng.uniform(6, 22, (group != 0).sum())
    if spec.get("s6"):
        short = np.arange(N) % 2 == 0
        mu = np.where(short, 14.0, 45.0) + rng.normal(0, 1.5, N)
        dmean = np.where(short, 2.0, 16.0)
        cost = np.where(short, 5.0, 5.0) * spec.get("cost_mult", 1.0)
        ar_sd = 3.0
    if spec.get("late_hq"):
        hq = np.arange(N) % 2 == 1
        mu = np.where(hq, rng.uniform(34, 42, N), rng.uniform(8, 14, N))
        dmean = np.where(hq, 6.0, 14.0)
    if spec.get("equal"):
        mu = 20 + rng.normal(0, 0.4, N)
        dmean[:] = 6.0; sigma[:] = 12.0; cost[:] = 6.0; ar_sd = 0.5
    if spec.get("skew"):
        mu = np.sort(mu)[::-1] * np.linspace(1.6, 0.5, N)
    sigma_pub = sigma * np.exp(rng.normal(0, 0.2, N))

    # regimes (hidden): Markov mult vector per regime; S7 = hard flip at W/2
    p_sw = spec.get("regime_p", 1 / 300)
    n_reg_max = 12
    M = np.exp(rng.normal(0, 0.25, (n_reg_max, N)))
    reg = np.zeros(T, int); r = 0
    for t in range(1, T):
        if rng.random() < p_sw:
            r = min(r + 1, n_reg_max - 1)
        reg[t] = r
    Emat = mu[:, None] * M[reg].T
    if spec.get("flip"):
        tf = W // 2
        flipped = (mu.max() + mu.min() - mu)
        Emat[:, tf:] = flipped[:, None] * M[reg[tf:]].T
    # AR(1) instrument-level opportunity state
    phi = 0.9
    u = np.zeros((N, T)); u[:, 0] = rng.normal(0, ar_sd, N)
    for t in range(1, T):
        u[:, t] = phi * u[:, t - 1] + math.sqrt(1 - phi * phi) * ar_sd * rng.normal(size=N)
    E = Emat + u
    # durations
    dist = spec.get("dist", "lognormal")
    if dist == "pareto":
        a = 2.2
        Dm = (rng.pareto(a, (N, T)) + 1) * (dmean[:, None] * (a - 1) / a)
    else:
        s2 = math.log(1 + cv * cv)
        Dm = np.exp(rng.normal(np.log(dmean)[:, None] - s2 / 2, math.sqrt(s2), (N, T)))
    D = np.clip(Dm, 1.0, PAD)
    Z = rng.normal(size=(N, T))
    # factors (hidden). increments N(drift,1)
    fg = rng.normal(size=(G, T)); fm = rng.normal(size=T)
    rho_m = np.full(T, spec.get("rho_m", 0.15))
    if spec.get("crisis"):
        a, b = int(W * 0.30), int(W * 0.60)
        fg[0, a:b] += -0.6
    if spec.get("collapse"):
        a, b = int(W * 0.35), int(W * 0.60)
        rho_m[a:b] = 0.7
        fm[a:b] += -0.6
        rho_g = np.full(G, 0.3)
    Cg = np.concatenate([np.zeros((G, 1)), np.cumsum(fg, 1)], 1)
    Cm = np.concatenate([[0.0], np.cumsum(fm)])

    # arrivals (observable). offered candidate load = total_rate * mean(D)/K_ref
    w = np.exp(rng.normal(0, 0.5, N))
    if spec.get("spam"):
        w = np.ones(N); w[:2] = 20.0
        mu_spam = np.median(mu)  # spam instruments have mediocre edge
        Emat_s = E.copy(); E[:2] = mu_spam + u[:2] * 0.0 + rng.normal(0, 2, (2, T)); del Emat_s
    w = w / w.sum()
    K_ref = 4
    total_rate = spec.get("load", 3.0) * K_ref / float(np.mean(dmean))
    prof = np.ones((N, T))
    tt = np.arange(T)
    if spec.get("late_hq"):
        hq = np.arange(N) % 2 == 1
        ph = tt % 40
        prof[~hq] = np.where(ph < 8, 6.0, 0.15)[None, :]
        prof[hq] = np.where((ph >= 12) & (ph < 20), 6.0, 0.15)[None, :]
    if spec.get("burst"):
        ph = tt % 60
        prof[:] = np.where(ph < 4, 15.0, 0.15)[None, :]
    rate_it = total_rate * w[:, None] * prof
    # renormalise so time-averaged total rate == total_rate
    rate_it *= total_rate / rate_it.sum(0).mean()
    cnt = rng.poisson(rate_it)
    # scores
    cal = spec.get("cal", "good")
    b_g = np.ones(G); a_i = np.zeros(N)
    if cal == "poor":
        b_g[:] = 0.35; a_i = rng.normal(0, 6, N)
    elif cal == "invert":
        b_g[:] = 1.0; b_g[G // 2:] = -0.6
        a_i = np.where(group >= G // 2, 40.0, 0.0)
    if spec.get("gamer"):
        gm = np.arange(N) < max(2, N // 5)
        a_i = np.where(gm, 30.0, 0.0)
        E[gm] = np.minimum(E[gm], 10.0)
    p_miss, p_stale = spec.get("p_miss", 0.0), spec.get("p_stale", 0.0)
    last_score = np.full(N, np.nan)
    events = [[] for _ in range(T)]
    for t in range(W):
        for i in range(N):
            for _ in range(cnt[i, t]):
                s = a_i[i] + b_g[group[i]] * E[i, t] + tau * rng.normal()
                if rng.random() < p_stale and not np.isnan(last_score[i]):
                    s = last_score[i]
                else:
                    last_score[i] = s
                if rng.random() < p_miss:
                    s = float("nan")
                events[t].append((i, s))
    meta = dict(spec=spec, split=split, tau=tau, ttl=sp["ttl"], K_ref=K_ref)
    return World(name, seed, N, G, W, T, group, sigma, sigma_pub, dmean, cost, rho_g, rho_m,
                 E, D, Z, Cg, Cm, events, meta)


def resample_hidden_after(w: World, t0: int, seed: int) -> World:
    """Leak-test twin: identical OBSERVABLES (events, scores, public info); hidden latents at index >= t0 redrawn."""
    rng = np.random.default_rng(seed + 777)
    import copy
    w2 = copy.copy(w)
    w2.E = w.E.copy(); w2.D = w.D.copy(); w2.Z = w.Z.copy()
    n = w.T - t0
    w2.E[:, t0:] = rng.uniform(-30, 80, (w.N, n))
    w2.D[:, t0:] = np.clip(np.exp(rng.normal(math.log(8), 0.8, (w.N, n))), 1, PAD)
    w2.Z[:, t0:] = rng.normal(size=(w.N, n))
    fg = rng.normal(-0.3, 2.0, (w.G, w.T)); fm = rng.normal(0.3, 2.0, w.T)
    inc_g = np.diff(w.Cg, axis=1); inc_m = np.diff(w.Cm)
    inc_g[:, t0:] = fg[:, t0:]; inc_m[t0:] = fm[t0:]
    w2.Cg = np.concatenate([np.zeros((w.G, 1)), np.cumsum(inc_g, 1)], 1)
    w2.Cm = np.concatenate([[0.0], np.cumsum(inc_m)])
    return w2
