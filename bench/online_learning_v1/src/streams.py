"""Synthetic non-stationary streams with KNOWN ground truth.

No market data is used. Every stream exposes the noise-free signal s_t and the
noise scale sigma_t so that *excess risk against the oracle* is measurable
exactly (no label-noise floor in the metric).

Common random numbers: for a given seed, coefficient vectors, features and
noise draws are identical across scenarios, so scenario comparisons are paired.
"""
import zlib
import numpy as np
from scipy.special import ndtr

D = 5
T = 4000
WARMUP = 500          # steps excluded from headline "overall" metrics


def _unit(rng):
    v = rng.standard_normal(D)
    return v / np.linalg.norm(v)


class Stream:
    pass


SCENARIOS = [
    "stationary", "abrupt", "gradual", "recurring", "shock", "false_drift",
    "missing_random", "missing_blackout", "delayed_50", "delayed_200",
    "nonlinear_abrupt",
]


def make_stream(scenario, seed, noise=2.0, T=T):
    assert scenario in SCENARIOS, scenario
    rw = np.random.default_rng([seed, 1])
    rx = np.random.default_rng([seed, 2])
    re = np.random.default_rng([seed, 3])
    rm = np.random.default_rng([seed, 4])
    A, B, C = _unit(rw), _unit(rw), _unit(rw)
    X = rx.standard_normal((T, D))
    eps = re.standard_normal(T)
    keep_u = rm.random(T)

    W = np.tile(A, (T, 1))            # per-step coefficient vector
    inter = np.zeros(T)               # per-step interaction coefficient
    xscale = np.ones(T)
    sigma = np.full(T, float(noise))
    avail = np.ones(T, bool)
    delay = 0
    changes = []                      # steps where a real concept change starts/ends
    notes = ""

    if scenario in ("abrupt", "missing_random", "missing_blackout",
                    "delayed_50", "delayed_200"):
        W[2000:] = B
        changes = [2000]
    if scenario == "gradual":
        a = np.clip((np.arange(T) - 1500) / 1000.0, 0, 1)[:, None]
        W = (1 - a) * A + a * B
        changes = [2500]              # end of ramp (recovery measured after it)
    if scenario == "recurring":
        for k, (a, b) in enumerate([(1000, 2000), (3000, 4000)]):
            W[a:b] = B
        changes = [1000, 2000, 3000]
    if scenario == "shock":
        W[2000:2100] = B
        changes = [2000, 2100]
    if scenario == "false_drift":
        sigma[1800:2000] = 3 * noise          # noise burst, same concept
        xscale[2600:2800] = 2.0               # covariate scale burst, same concept
        changes = []
    if scenario == "missing_random":
        avail = keep_u < 0.3
    if scenario == "missing_blackout":
        avail[1900:2500] = False
        changes = [2000, 2500]
    if scenario == "delayed_50":
        delay = 50
    if scenario == "delayed_200":
        delay = 200
    if scenario == "nonlinear_abrupt":
        W = 0.8 * np.tile(A, (T, 1))
        W[2000:] = 0.8 * B
        inter[:2000] = 0.8
        inter[2000:] = -0.8
        changes = [2000]

    X = X * xscale[:, None]
    s = (W * X).sum(1) + inter * X[:, 0] * X[:, 1]
    z = s + sigma * eps
    S = Stream()
    S.name, S.seed, S.noise, S.T, S.delay = scenario, seed, noise, T, delay
    S.X, S.s, S.sigma, S.z = X, s, sigma, z
    S.lab = (z > 0).astype(float)
    S.p_true = ndtr(s / sigma)
    S.avail = avail
    S.changes = changes
    return S


def make_alternating(seed, pattern="ABAB", seglen=1000, noise=2.0, test=False):
    """Regime sequence stream (e.g. 'ABABAB'); changes at every boundary.
    test=True draws fresh features/noise (held-out) with the same regimes."""
    rw = np.random.default_rng([seed, 1])
    A, B = _unit(rw), _unit(rw)
    T_ = seglen * len(pattern)
    rx = np.random.default_rng([seed, 12 if test else 2])
    re = np.random.default_rng([seed, 13 if test else 3])
    X = rx.standard_normal((T_, D)); eps = re.standard_normal(T_)
    W = np.zeros((T_, D))
    for i, ch in enumerate(pattern):
        W[i * seglen:(i + 1) * seglen] = A if ch == "A" else B
    S = Stream()
    S.name, S.seed, S.noise, S.T, S.delay = "alt_" + pattern, seed, noise, T_, 0
    S.X = X; S.s = (W * X).sum(1); S.sigma = np.full(T_, float(noise))
    S.z = S.s + S.sigma * eps; S.lab = (S.z > 0).astype(float)
    S.p_true = ndtr(S.s / S.sigma); S.avail = np.ones(T_, bool)
    S.changes = [seglen * i for i in range(1, len(pattern))]
    S.A, S.B = A, B
    return S


def regime_test_set(S, regime, n=2000, seed_off=99):
    """Held-out samples generated under regime 'A' or 'B' of an alternating stream."""
    r = np.random.default_rng([S.seed, seed_off])
    X = r.standard_normal((n, D))
    w = S.A if regime == "A" else S.B
    s = X @ w
    return X, s, ndtr(s / S.noise)
