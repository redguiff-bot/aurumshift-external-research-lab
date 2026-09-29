"""Synthetic non-stationary streams. Latent concept w_t (unit vector) drives both tracks:
   C: P(y=1|x) = sigmoid(KAPPA * s_t * w_t.x)  (s_t = feature scale)     R: y = w_t.x + N(0, (sd_t)^2)
Everything is drawn from a per-(scenario,seed) numpy Generator -> fully reproducible."""
import numpy as np
from dataclasses import dataclass, field

import os
D, T, N0, KAPPA, NOISE_SD = 8, 4000, 500, 3.0, 0.5
if os.environ.get('LOWSNR'): KAPPA, NOISE_SD = 1.0, 1.5   # sensitivity run: ~3x lower signal-to-noise
NAMES = ["stationary", "abrupt", "gradual", "recurring", "shock", "false_drift", "random_walk",
         "abrupt_missing", "abrupt_delayed", "abrupt_nonlinear"]

def _unit(v): return v / np.linalg.norm(v)

@dataclass
class Stream:
    name: str; seed: int; X: np.ndarray; W: np.ndarray; scale: np.ndarray; noise_sd: np.ndarray
    yC: np.ndarray; yR: np.ndarray; pC: np.ndarray; muR: np.ndarray
    delay: int; missing: np.ndarray            # missing[t]=True -> label of sample t never arrives
    change_points: list; probe_times: list; wA: np.ndarray; wB: np.ndarray; nonlinear: bool
    meta: dict = field(default_factory=dict)

def _sig(z): return 1 / (1 + np.exp(-z))

def nl_z(X, which):      # nonlinear concepts (axis-interaction), used for abrupt_nonlinear (track C only)
    return 1.5 * X[:, 0] * X[:, 1] + 0.5 * X[:, 2] if which == 0 else -1.5 * X[:, 0] * X[:, 1] + 0.5 * X[:, 3]

def make(name, seed):
    rng = np.random.default_rng([seed, sum(map(ord, name))])
    wA = _unit(rng.normal(size=D)); wB = _unit(rng.normal(size=D))
    wB = _unit(wB - (wB @ wA) * wA)             # orthogonal to wA: maximal linear disagreement w/o sign-flip trick
    X = rng.normal(size=(T, D)); t = np.arange(T)
    W = np.tile(wA, (T, 1)); scale = np.ones(T); nsd = np.full(T, NOISE_SD)
    cps, probes, delay, nonlin = [], [], 0, False
    missing = np.zeros(T, bool)
    if name in ("abrupt", "abrupt_missing", "abrupt_delayed", "abrupt_nonlinear"):
        W[2000:] = wB; cps = [2000]; probes = [1999, 3999]
        if name == "abrupt_missing": missing[2000:] = rng.random(T - 2000) < 0.7
        if name == "abrupt_delayed": delay = 100
        if name == "abrupt_nonlinear": nonlin = True
    elif name == "gradual":
        for i in range(1500, 2500):
            a = (i - 1500) / 1000; W[i] = wA * np.cos(a * np.pi / 2) + wB * np.sin(a * np.pi / 2)
        W[2500:] = wB; cps = [1500]; probes = [1499, 3999]
    elif name == "recurring":
        W[1000:2000] = wB; W[3000:] = wB; cps = [1000, 2000, 3000]; probes = [999, 1999, 2999, 3999]
    elif name == "shock":
        W[2000:2100] = wB; cps = [2000, 2100]; probes = [1999, 3999]
    elif name == "false_drift":
        scale[2000:2400] = 3.0; nsd[2000:2400] = 3 * NOISE_SD; cps = [2000]; probes = [1999, 3999]
    elif name == "random_walk":
        w = wA.copy()
        for i in range(T):
            W[i] = w; w = _unit(w + 0.01 * rng.normal(size=D))
        wB = W[-1]; probes = [1999, 3999]
    elif name != "stationary": raise ValueError(name)
    Xs = X * scale[:, None]
    if nonlin:
        z = np.where(t < 2000, nl_z(Xs, 0), nl_z(Xs, 1)); pC = _sig(KAPPA * z); muR = z
    else:
        z = np.einsum("ij,ij->i", W, Xs); pC = _sig(KAPPA * z); muR = z
    yC = (rng.random(T) < pC).astype(int); yR = muR + nsd * rng.normal(size=T)
    return Stream(name, seed, Xs, W, scale, nsd, yC, yR, pC, muR, delay, missing, cps, probes, wA, wB, nonlin)

def probe_set(seed, n=300):
    return np.random.default_rng([777, seed]).normal(size=(n, D))

def probe_truth(st, which):        # true P(y=1|x) and mu on probe set under concept A or B
    Xp = probe_set(st.seed)
    if st.nonlinear: z = nl_z(Xp, 0 if which == "A" else 1)
    else: z = Xp @ (st.wA if which == "A" else st.wB)
    return Xp, _sig(KAPPA * z), z
