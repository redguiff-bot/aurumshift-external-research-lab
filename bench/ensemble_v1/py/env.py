"""Synthetic environment: heterogeneous forecasting experts, regime-dependent validity, explicit availability semantics.
All arrays are vectorised over seeds: shape (S, T, K).

Status codes (per expert, per round):
  ACTIVE=0        forecasts, feedback observed
  INACTIVE=1      structurally invalid in this regime / not yet born / retired  -> asleep
  ABSTAIN=2       valid but chooses not to forecast                            -> asleep
  DATA_GAP=3      input data missing, cannot forecast                          -> asleep
  NO_EVIDENCE=4   forecasts (is in the ensemble) but its score feedback is missing -> awake, unobserved
Bad realised performance is NOT a status: it is a high observed loss on an ACTIVE round.
"""
import numpy as np
ACTIVE, INACTIVE, ABSTAIN, DATA_GAP, NO_EVIDENCE = 0, 1, 2, 3, 4
INF = np.inf
K_MAX = 10
# base experts: sd of logit noise per regime [A trend, B range, C stress, R rare]; INF = structurally inactive
FAMILY = ["generalist", "trend", "trend_clone", "meanrev", "stress_spec", "rare_spec", "junk", "carry", "late_star", "spare"]
BASE_SD = np.array([
    [0.9, 0.9, 0.9, 0.9],       # 0 generalist
    [0.4, 1.6, 1.2, 1.6],       # 1 trend
    [0.4, 1.6, 1.2, 1.6],       # 2 trend clone (cluster with 1)
    [1.6, 0.4, 1.2, 1.6],       # 3 mean-reversion
    [INF, INF, 0.35, INF],      # 4 stress specialist
    [INF, INF, INF, 0.15],      # 5 rare-regime specialist
    [1.5, 1.5, 1.5, 1.5],       # 6 junk always-on
    [0.8, 0.8, 1.4, 1.0],       # 7 carry
    [INF] * 4,                  # 8 late star (not born in base)
    [INF] * 4,                  # 9 spare
])
CLUSTER = np.array([0, 1, 1, 2, 3, 4, 5, 6, 7, 8])   # cluster id per expert (independent unless shared)


def _markov_regimes(S, T, rng, dwell=(80, 80, 80), p_rare=0.002, rare_dwell=25, cycle=None, cycle_dwell=400):
    reg = np.zeros((S, T), dtype=np.int8)
    if cycle is not None:                                  # deterministic recurrence with jittered dwell
        for s in range(S):
            t = 0; i = int(rng.integers(0, len(cycle)))
            while t < T:
                d = int(cycle_dwell * rng.uniform(0.8, 1.2)); reg[s, t:t + d] = cycle[i % len(cycle)]; t += d; i += 1
        return reg
    cur = rng.integers(0, 3, S)
    for t in range(T):
        reg[:, t] = cur
        u = rng.random(S)
        rare = cur == 3
        leave = np.where(rare, u < 1.0 / rare_dwell, u < 1.0 / np.array(dwell)[np.minimum(cur, 2)])
        enter = (~rare) & (rng.random(S) < p_rare)
        nxt = np.where(leave, rng.integers(0, 3, S), cur)
        cur = np.where(enter, 3, nxt)
    return reg


def _bursts(shape_ST, rate, mean_len, rng):
    """boolean (S,T) Poisson-onset bursts of geometric length; long-run coverage ~ rate."""
    S, T = shape_ST; out = np.zeros((S, T), bool)
    if rate <= 0: return out
    onset = rate / mean_len
    starts = rng.random((S, T)) < onset
    for s in range(S):
        for t in np.flatnonzero(starts[s]):
            out[s, t:t + int(rng.geometric(1.0 / mean_len))] = True
    return out


def make_scenario(name, S, T, seed):
    rng = np.random.default_rng(seed)
    K = K_MAX
    sd_tab = np.repeat(BASE_SD[None, :, :], S, axis=0).copy()          # (S,K,4) static base
    kw = dict(cycle=None, p_rare=0.002)
    if name == "S3_RECURRENCE": kw = dict(cycle=[0, 1, 2], p_rare=0.0)
    if name == "S8_RARE_SPECIALIST": kw = dict(cycle=None, p_rare=0.0007)
    reg = _markov_regimes(S, T, rng, **kw)
    if name == "S3_RECURRENCE":   # trend/meanrev/stress become pure specialists (dormant 2/3 of time)
        sd_tab[:, 1, 1:] = INF; sd_tab[:, 1, 0] = 0.35
        sd_tab[:, 2, :] = INF                                           # clone not present
        sd_tab[:, 3, :] = INF; sd_tab[:, 3, 1] = 0.35
        sd_tab[:, 4, 2] = 0.35
    sd = np.take_along_axis(sd_tab, reg[:, None, :].astype(np.int64).repeat(K, 1), axis=2).transpose(0, 2, 1).copy()   # (S,T,K)
    sd = sd.astype(np.float64)
    born = np.zeros((S, T, K), bool)          # explicit unborn/retired mask -> INACTIVE
    rho = np.zeros(K)                          # within-cluster noise correlation
    rho[1] = rho[2] = 0.9
    cluster = CLUSTER.copy()
    half = T // 2
    if name == "S2_LEADERSHIP":
        a, b = T // 3, 2 * T // 3
        sw = sd[:, :, [1, 3]].copy()
        sd[:, a:b, 1], sd[:, a:b, 3] = sw[:, a:b, 1], sw[:, a:b, 0]      # trend<->meanrev swap quality in the middle third
        sd[:, b:, 0] = 0.3; sd[:, b:, 1] = np.where(np.isfinite(sd[:, b:, 1]), sd[:, b:, 1] * 2.5, INF)
        sd[:, b:, 2] = np.where(np.isfinite(sd[:, b:, 2]), sd[:, b:, 2] * 2.5, INF)
        sd[:, b:, 3] = np.where(np.isfinite(sd[:, b:, 3]), sd[:, b:, 3] * 2.5, INF)     # generalist takes leadership at the end
    if name == "S4a_NEW_GOOD":
        sd[:, half:, 8] = 0.25; sd[:, :half, 8] = INF
    if name == "S4b_NEW_BAD":
        sd[:, half:, 8] = 1.9; sd[:, :half, 8] = INF
    if name == "S5_RETIRE_RETURN":
        r1, r2 = T // 2, 3 * T // 4
        sd[:, r1:r2, 3] = INF                                            # meanrev retired
        sd[:, r2:, 3] = np.where(np.isfinite(sd[:, r2:, 3]), 1.7, INF)   # returns degraded
    if name == "S6_CORRELATED":
        rho[:] = 0; rho[[2, 8, 9, 1]] = 0.95; cluster[[1, 2, 8, 9]] = 1   # 4 clones share noise
        sd[:] = INF; sd[:, :, [0, 3]] = 0.85; sd[:, :, 6] = 0.95
        sd[:, :half, [1, 2, 8, 9]] = 0.6; sd[:, half:, [1, 2, 8, 9]] = 1.6
    if name == "S7_TEMP_UNDERPERF":
        w0, w1 = 2 * T // 5, 3 * T // 5
        sd[:, w0:w1, 1] = np.where(np.isfinite(sd[:, w0:w1, 1]), 2.2, INF)
        sd[:, w0:w1, 2] = np.where(np.isfinite(sd[:, w0:w1, 2]), 2.2, INF)
    if name == "S9_LONG_GAP":
        pass                                                             # handled by explicit gap below
    # -- status assignment ----------------------------------------------------------------------------------
    status = np.full((S, T, K), ACTIVE, dtype=np.int8)
    status[~np.isfinite(sd)] = INACTIVE
    gap = np.zeros((S, T, K), bool); noev = np.zeros((S, T, K), bool); abst = np.zeros((S, T, K), bool)
    if name == "S1_SEMANTICS_GAPS":
        for k in range(K):
            gap[:, :, k] = _bursts((S, T), 0.12, 60, rng)
            noev[:, :, k] = _bursts((S, T), 0.30, 120, rng)
            abst[:, :, k] = rng.random((S, T)) < 0.08
    if name == "S9_LONG_GAP":
        g0, g1 = T // 3, T // 3 + T // 4
        sd[:, :, 8] = 0.28                                               # a star that is data-gapped for a quarter of history
        status[:, :, 8] = ACTIVE
        gap[:, g0:g1, 8] = True
        status[~np.isfinite(sd)] = INACTIVE
    else:
        g0 = g1 = 0
    sdf = np.where(np.isfinite(sd), sd, 1.0)
    status[gap & (status == ACTIVE)] = DATA_GAP
    status[abst & (status == ACTIVE)] = ABSTAIN
    status[noev & (status == ACTIVE)] = NO_EVIDENCE
    # -- latent process and forecasts ------------------------------------------------------------------------
    a = np.zeros((S, T)); a[:, 0] = rng.normal(0, 1.2, S)
    eps_a = rng.normal(0, 1.2 * np.sqrt(1 - 0.9 ** 2), (S, T))
    for t in range(1, T): a[:, t] = 0.9 * a[:, t - 1] + eps_a[:, t]
    q = 1 / (1 + np.exp(-a))
    y = (rng.random((S, T)) < q).astype(np.float64)
    shared = rng.normal(size=(S, T, K)); ind = rng.normal(size=(S, T, K))
    nz = np.empty((S, T, K))
    for k in range(K):
        c = cluster[k]; members = np.flatnonzero(cluster == c)
        nz[:, :, k] = np.sqrt(rho[k]) * shared[:, :, members[0]] + np.sqrt(1 - rho[k]) * ind[:, :, k]
    l = a[:, :, None] + sdf * nz
    p = 1 / (1 + np.exp(-l))
    ctx = reg.copy()                                                     # observable context = regime label (noisy)
    flip = rng.random((S, T)) < 0.10
    ctx_obs = np.where(flip, rng.integers(0, 4, (S, T)), ctx).astype(np.int8)
    awake = np.isin(status, [ACTIVE, NO_EVIDENCE])
    observed = status == ACTIVE
    known = ~(sd_is_unborn(sd) if False else np.zeros((S, T, K), bool))
    return dict(name=name, p=p, y=y, q=q, awake=awake, observed=observed, status=status, sd=np.where(np.isfinite(sd), sd, np.nan),
                regime=reg, ctx=ctx_obs, cluster=cluster, K=K, S=S, T=T, gap_window=(g0, g1))


SCENARIOS = ["S0_BASE_CLEAN", "S1_SEMANTICS_GAPS", "S2_LEADERSHIP", "S3_RECURRENCE", "S4a_NEW_GOOD", "S4b_NEW_BAD",
             "S5_RETIRE_RETURN", "S6_CORRELATED", "S7_TEMP_UNDERPERF", "S8_RARE_SPECIALIST", "S9_LONG_GAP"]

def sd_is_unborn(sd): return np.isnan(sd)
