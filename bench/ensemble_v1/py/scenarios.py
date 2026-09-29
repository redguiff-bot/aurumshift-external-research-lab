"""Synthetic scenario generator for the sleeping-experts ensemble study.

Reward convention: r in [0,1], centred near 0.5; true mean = 0.5 + edge.
Per (t, expert) state codes (semantics contract, see reports/014 04_SLEEPING_EXPERTS.md):
  NOT_EXIST  expert not (yet / any more) part of the roster
  INACTIVE   regime makes the strategy invalid            -> not allocated, no update
  ABSTAIN    strategy eligible but declines to act        -> not allocated, no update
  GAP        allocated, reward realised but NOT observed  -> allocated, no update
  OBS        allocated and reward observed                -> allocated, update
"""
import zlib
import numpy as np

NOT_EXIST, INACTIVE, ABSTAIN, GAP, OBS = 0, 1, 2, 3, 4
NAMES = ["TREND", "MREV", "CARRY", "DUD", "VOLSPEC", "RARE", "BRK", "LATE",
         "CLN0", "CLN1", "CLN2", "SPARE"]
K = len(NAMES)
TREND, MREV, CARRY, DUD, VOLSPEC, RARE, BRK, LATE, CLN0, CLN1, CLN2, SPARE = range(K)
NREG = 4

# edge above 0.5 per regime R0..R3 (nan => strategy invalid in that regime)
NAN = np.nan
PROFILES = {
    TREND:   [0.08, -0.04, 0.02, -0.03],
    MREV:    [-0.03, 0.07, 0.00, 0.01],
    CARRY:   [0.02, 0.02, 0.02, 0.02],
    DUD:     [-0.03, -0.03, -0.03, -0.03],
    VOLSPEC: [NAN, NAN, 0.10, NAN],
    RARE:    [NAN, NAN, NAN, 0.15],
    BRK:     [0.05, NAN, 0.04, NAN],
    LATE:    [0.06, 0.06, 0.06, 0.06],
}
SIG_COMMON, SIG_IDIO = 0.10, 0.10


def regime_path(rng, T, script=None):
    P = np.zeros((NREG, NREG))
    for r in range(3):
        P[r, r] = 0.97
        P[r, 3] = 0.003
        others = [x for x in range(3) if x != r]
        for o in others:
            P[r, o] = (1 - 0.97 - 0.003) / 2
    P[3, 3] = 0.95
    for o in range(3):
        P[3, o] = 0.05 / 3
    z = np.zeros(T, int)
    z[0] = rng.integers(3)
    u = rng.random(T)
    for t in range(1, T):
        z[t] = np.searchsorted(np.cumsum(P[z[t - 1]]), u[t])
    z = np.minimum(z, 3)
    if script is not None:  # script: list of (t0,t1) windows forced to R3; R3 removed elsewhere
        z[z == 3] = rng.integers(0, 3, size=(z == 3).sum())
        for a, b in script:
            z[a:b] = 3
    return z


def make(name, seed, T=1200, snr=1.0, noise=1.0):
    """Build a scenario dict. snr scales all edges, noise scales all sigmas (stress knobs)."""
    rng = np.random.default_rng(1_000_003 * seed + zlib.crc32(name.encode()) % 9973)
    prof = {k: np.array(v, float) * snr for k, v in PROFILES.items()}
    script = None
    ex_from = {}      # expert -> first existing t
    ex_to = {}        # expert -> last existing t (exclusive)
    events, segments, targets = {}, [], []
    clones_of = {}
    gap_p = 0.0
    gap_burst = None
    mnar = False
    abst_p = 0.05
    abst_informative = False
    edge_shift = None   # list of (t, permutation of generalist profiles)
    patch = None        # (expert, t0, t1, edge)
    unlucky = None      # (expert, n_obs, edge)
    core = [TREND, MREV, CARRY, DUD, VOLSPEC, RARE, BRK]

    roster = list(core)
    if name != "S3_new_expert" and name != "S8_composite":
        roster.append(LATE)                    # LATE present from start
    if name == "S0_base":
        segments = [("all", 0, T)]
    elif name == "S1_leadership":
        # generalist profiles rotate among TREND/MREV/CARRY/LATE at T/4,T/2,3T/4
        edge_shift = [(T // 4, 1), (T // 2, 2), (3 * T // 4, 3)]
        segments = [("a", 0, T // 4), ("b", T // 4, T // 2), ("c", T // 2, 3 * T // 4), ("d", 3 * T // 4, T)]
    elif name == "S2_dormancy":
        script = [(150, 230), (1070, 1150)]   # rare regime returns after ~840 rounds
        targets = [RARE]
        segments = [("ep1", 150, 230), ("dorm", 230, 1070), ("ep2", 1070, 1150)]
    elif name == "S3_new_expert":
        t0 = T // 3
        ex_from[LATE] = t0
        roster.append(LATE)
        targets = [LATE]
        events["intro"] = (LATE, t0)
        segments = [("pre", 0, t0), ("first200", t0, t0 + 200), ("late", t0 + 200, T)]
    elif name == "S4_disappears":
        ex_to[TREND] = T // 2
        targets = [TREND]
        segments = [("pre", 0, T // 2), ("post100", T // 2, T // 2 + 100), ("post", T // 2 + 100, T)]
        events["gone"] = (TREND, T // 2)
    elif name in ("S5a_clones_of_bad", "S5b_clones_of_best"):
        src = DUD if name == "S5a_clones_of_bad" else LATE
        for c in (CLN0, CLN1, CLN2):
            clones_of[c] = src
            roster.append(c)
        targets = [src, CLN0, CLN1, CLN2]
        segments = [("all", 0, T)]
    elif name == "S6a_gap_mcar":
        gap_p = 0.30
        segments = [("all", 0, T)]
    elif name == "S6b_gap_burst":
        gap_burst = (TREND, T // 3, T // 3 + 350)     # best-ish regime-0 generalist unobserved 350 rounds
        targets = [TREND]
        segments = [("pre", 0, T // 3), ("gap", T // 3, T // 3 + 350), ("post", T // 3 + 350, T)]
    elif name == "S6c_gap_mnar":
        gap_p = 0.0
        mnar = True                                   # outcomes below 0.40 go missing with p=0.7
        segments = [("all", 0, T)]
    elif name == "S6d_abstain_informative":
        abst_informative = True                       # generalists abstain when their reward would be < 0.45
        segments = [("all", 0, T)]
    elif name == "S7_temp_underperf":
        patch = (LATE, T // 2, T // 2 + 150, -0.10)   # best generalist 150-round bad patch
        unlucky = (RARE, 15, -0.10)                   # rare specialist: first 15 obs unlucky
        script = [(100, 180), (600, 680), (1000, 1080)]
        targets = [LATE, RARE]
        segments = [("pre", 0, T // 2), ("patch", T // 2, T // 2 + 150), ("rec100", T // 2 + 150, T // 2 + 250),
                    ("after", T // 2 + 250, T)]
    elif name == "S8_composite":
        script = [(120, 190), (520, 590), (1000, 1070)]
        ex_from[LATE] = T // 3
        roster.append(LATE)
        ex_to[TREND] = 2 * T // 3
        gap_p = 0.10
        edge_shift = [(T // 2, 1)]
        targets = [LATE, RARE]
        segments = [("all", 0, T)]
    else:
        raise ValueError(name)

    z = regime_path(rng, T, script)
    f = rng.standard_normal(T)
    E = rng.standard_normal((T, K))
    MU = np.full((T, K), 0.5)
    valid = np.zeros((T, K), bool)
    gens = [TREND, MREV, CARRY, LATE]
    for t in range(T):
        # profile rotation for generalists
        shift = 0
        if edge_shift is not None:
            done = [sh for (ts, sh) in edge_shift if t >= ts]
            shift = done[-1] if done else 0
        perm = {g: gens[(gens.index(g) + shift) % len(gens)] for g in gens}
        for k in roster:
            if k in clones_of:
                continue
            p = prof[perm.get(k, k)] if k in gens else prof[k]
            e = p[z[t]]
            if not np.isnan(e):
                valid[t, k] = True
                MU[t, k] = 0.5 + e
    if patch is not None:
        k, a, b, e = patch
        MU[a:b, k] = np.where(valid[a:b, k], 0.5 + e, MU[a:b, k])
    for c, s in clones_of.items():
        valid[:, c] = valid[:, s]
        MU[:, c] = MU[:, s]
    exist = np.zeros((T, K), bool)
    for k in roster:
        exist[ex_from.get(k, 0):ex_to.get(k, T), k] = True
    valid &= exist
    idio = SIG_IDIO * noise * E
    for c, s in clones_of.items():
        idio[:, c] = idio[:, s] + 0.03 * noise * rng.standard_normal(T)
    R = np.clip(MU + SIG_COMMON * noise * f[:, None] + idio, 0.0, 1.0)
    if unlucky is not None:
        k, nobs, e = unlucky
        # first nobs valid rounds have the wrong sign
        idx = np.where(valid[:, k])[0][:nobs]
        MU[idx, k] = 0.5 + e
        R[idx, k] = np.clip(MU[idx, k] + SIG_COMMON * noise * f[idx] + idio[idx, k], 0, 1)

    state = np.full((T, K), NOT_EXIST, np.int8)
    state[exist] = INACTIVE
    state[valid] = OBS
    # abstention
    ab = rng.random((T, K)) < abst_p
    ab[:, CARRY] = False                     # guarantee at least one voter
    if abst_informative:
        ab = ab | ((R < 0.45) & np.isin(np.arange(K)[None, :], gens) & (rng.random((T, K)) < 0.8))
        ab[:, CARRY] = False
    m = valid & ab
    state[m] = ABSTAIN
    # data gaps (only on allocated=OBS rounds)
    g = np.zeros((T, K), bool)
    if gap_p > 0:
        g = rng.random((T, K)) < gap_p
    if mnar:
        g = (R < 0.40) & (rng.random((T, K)) < 0.7)
    if gap_burst is not None:
        k, a, b = gap_burst
        g[a:b, k] = True
    state[(state == OBS) & g] = GAP

    ctx_noisy = z.copy()
    flip = rng.random(T) < 0.20
    ctx_noisy[flip] = rng.integers(0, NREG, size=flip.sum())
    return dict(name=name, seed=seed, T=T, K=K, state=state, R=R, MU=MU, regime=z,
                regime_noisy=ctx_noisy, segments=segments, targets=targets, events=events,
                script=script)


CORE = ["S0_base", "S1_leadership", "S2_dormancy", "S3_new_expert", "S4_disappears",
        "S5a_clones_of_bad", "S5b_clones_of_best", "S6a_gap_mcar", "S6b_gap_burst",
        "S6d_abstain_informative", "S7_temp_underperf", "S8_composite"]
STRESS = ["S6c_gap_mnar"]          # unavoidable-bias stress, reported but not gated
ALL = CORE + STRESS
