"""Controlled synthetic worlds for BUY/SELL/HOLD uncertainty research.

Classes: 0=DOWN(SELL) 1=FLAT(HOLD) 2=UP(BUY).  Latent return r = w.x + sigma_t*eps,
y = UP if r>theta, DOWN if r<-theta else FLAT.  Features AR(1) (non-iid), volatility
follows a hidden 2-state Markov chain (clustering => non-exchangeable), 1% "rare cluster"
rows with a different mapping.  Oracle posteriors are exact.
Timeline (one continuous series per seed): train | calib | val | held-out.
Shifts are applied to OBSERVED features / dynamics only from ONSET (index inside held-out).
"""
import numpy as np
from scipy.stats import norm

D = 6
W0 = np.array([.8, -.6, .5, 0., 0., 0.])
WB = np.array([-.8, .6, -.5, 0., 0., 0.])       # rare-cluster mapping (flipped)
THETA = 0.6
SIG = (0.9, 1.6)
RHO = 0.7
N_TRAIN, N_CAL, N_VAL, N_HOLD, ONSET = 4000, 3000, 3000, 4500, 1500
SCENARIOS = ["none", "vol_jump", "regime_transition", "feature_shift",
             "missing_features", "stale_features", "venue_change", "rare_cluster"]
CAUSES = ["NORMAL", "NO_SIGNAL", "DATA_GAP", "MODEL_UNCERTAINTY", "OUT_OF_DISTRIBUTION"]


def oracle_post(m, sigma):
    up = 1 - norm.cdf((THETA - m) / sigma)
    dn = norm.cdf((-THETA - m) / sigma)
    return np.stack([dn, 1 - up - dn, up], 1)


def make_world(seed, scenario="none", mag=1.0, n_train=N_TRAIN, n_cal=N_CAL, n_val=N_VAL,
               n_hold=N_HOLD, onset=ONSET, iid=False):
    """mag scales shift magnitude (tuning seeds use mag<1, held-out mag=1)."""
    rng = np.random.default_rng(seed)
    N = n_train + n_cal + n_val + n_hold
    T0 = n_train + n_cal + n_val + onset
    x = np.zeros((N, D)); x[0] = rng.standard_normal(D)
    rho = 0.0 if iid else RHO; stay = 0.5 if iid else 0.985
    eta = rng.standard_normal((N, D)); s = np.sqrt(1 - rho ** 2)
    for t in range(1, N):
        x[t] = rho * x[t - 1] + s * eta[t]
    st = np.zeros(N, int)
    for t in range(1, N):
        st[t] = st[t - 1] if rng.random() < stay else 1 - st[t - 1]
    sigma = np.array(SIG)[st].astype(float)
    pB = np.full(N, 0.01)
    post = np.arange(N) >= T0
    if scenario == "rare_cluster":
        pB[post] = 0.01 + 0.07 * mag
    clB = rng.random(N) < pB
    x[clB, :3] += 1.2
    w = np.tile(W0, (N, 1)); w[clB] = WB
    if scenario == "vol_jump":
        sigma[post] *= 1 + 1.5 * mag
    if scenario == "regime_transition":   # mapping rotates gradually over 1000 steps
        ang = np.pi * (2 / 3) * mag * np.clip((np.arange(N) - T0) / 1000, 0, 1)
        c, sn = np.cos(ang), np.sin(ang)
        nb = ~clB
        w[nb, 0] = c[nb] * W0[0] - sn[nb] * W0[1]; w[nb, 1] = sn[nb] * W0[0] + c[nb] * W0[1]
    eps = rng.standard_normal(N)
    m = (w * x).sum(1)
    r = m + sigma * eps
    y = np.where(r > THETA, 2, np.where(r < -THETA, 0, 1))
    P = oracle_post(m, sigma)
    xo = x.copy()
    cause = np.array(["NORMAL"] * N, dtype=object)
    idx = np.where(post)[0]
    if scenario == "feature_shift":       # covariate shift, P(y|x) unchanged
        xo[idx, :] += 1.5 * mag * np.array([1, 1, 1, 1, 0, 0])
        xo[idx, :] *= 1 + 0.3 * mag
        # keep the world consistent: labels stay generated from the ORIGINAL latent x
        cause[idx] = "OUT_OF_DISTRIBUTION"
    if scenario == "venue_change":         # different venue: scaled/offset/noisy sensors of same latents
        xo[idx, :] = (1 - 0.3 * mag) * x[idx, :] + 0.5 * mag + 0.8 * mag * rng.standard_normal((len(idx), D))
        cause[idx] = "OUT_OF_DISTRIBUTION"
    if scenario == "missing_features":
        miss = rng.random((N, D)) < (0.4 * mag * np.array([1, 1, 1, 0, 0, 0]))
        miss[~post] = False
        xo[miss] = np.nan
        cause[miss[:, :3].any(1)] = "DATA_GAP"
    if scenario == "stale_features":
        k = max(2, int(round(10 * mag)))
        for t in idx:
            ph = (t - T0) % k
            if ph > 0:
                xo[t, :3] = x[t - ph, :3]
                cause[t] = "DATA_GAP"
    if scenario == "rare_cluster":
        cause[clB & post] = "MODEL_UNCERTAINTY"
    # NO_SIGNAL: in-distribution rows whose oracle max posterior is low
    nosig = (cause == "NORMAL") & (P.max(1) < 0.5)
    cause[nosig] = "NO_SIGNAL"
    sl = dict(train=slice(0, n_train), cal=slice(n_train, n_train + n_cal),
              val=slice(n_train + n_cal, n_train + n_cal + n_val),
              hold=slice(n_train + n_cal + n_val, N))
    return dict(x_true=x, x=xo, y=y, r=r, P=P, sigma=sigma, cause=cause, clB=clB, sl=sl,
                onset_abs=T0, onset_rel=onset, scenario=scenario, seed=seed)
