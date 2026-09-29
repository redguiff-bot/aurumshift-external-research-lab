"""Synthetic capacity-constrained admission environment (external research only).

Time is discrete (1 step = 1 hour).  Opportunities ("opps") arrive, wait at most
`ttl` steps in a pending pool, and an allocator may admit at most `free` of them
into `cap` identical slots.  An admitted opp occupies its slot for a stochastic
duration.  Everything the allocator may see is in the OBS arrays / View tuples.
Everything else (true edge, true duration, true cost, future returns) is LATENT
and is only touched by the simulator after admission (or by oracle policies that
are flagged NOT IMPLEMENTABLE).

Net-outcome abstraction (generic, no private formulas):
    net = edge_at_admission (bps, realised pro-rata over the hold)
        + side * sum(instrument returns over the hold)      # market noise
        - cost_true                                          # explicit, always > 0
        - evict_extra (only if force-closed early)
UNKNOWN_COST is *observed* as NaN; the true cost is never zero.
"""
from __future__ import annotations
import math
from typing import NamedTuple
import numpy as np

N_INST = 12
NAN = float("nan")

BASE = dict(
    T=1000, N=N_INST, NCL=4, cap_ref=4, load=1.0,
    arrival="poisson", mmpp_hi=2.4, mmpp_lo=0.3, mmpp_stay=0.97,
    burst=None,            # (period, length, mult)
    wave=None,             # dict(period, frac_low, mu_low, mu_high, load_low, load_high)
    dur_base=12.0, dur_het=0.5, dur_sd=0.55, dur_dist="lognorm",
    mu_mean=10.0, mu_sd=6.0, q_sd=14.0, edge_dur_k=0.0, cl_bonus=None,
    sig_i=6.0, sig_het=0.3, sig_c=6.0, beta=1.0, corr_scale=1.0,
    fee_lo=4.0, fee_hi=8.0, slip_lo=1.0, slip_hi=3.0, p_cost_unk=0.1, evict_extra=3.0,
    tau=8.0, ttl=3,
    score_sd=10.0, score_het=0.4, score_a=0.0, score_b=1.0, refresh=True, p_miss=0.0,
    rho_d=0.3, dh_sd=0.25, p_miss_dur=0.05,
    regime=None,           # dict(t_frac, perm_mu, b_after, sig_c_mult, mu_shift)
    spam=None,             # dict(rate, mu, bias, inst)
    fast_slow=None,        # dict(dur_fast, dur_slow, mu_fast, mu_slow)
)


class View(NamedTuple):
    """Everything an allocator may see about a pending opportunity at time t."""
    cid: int
    inst: int
    cluster: int
    side: int
    age: int          # steps since first seen
    score: float      # NaN = missing evidence
    score_age: int    # age of the information behind `score` (0 = fresh)
    cost: float       # NaN = UNKNOWN_COST (never zero)
    dur_hat: float    # NaN = missing


class OView(NamedTuple):
    """An open position as visible to the allocator (no realised duration/PnL)."""
    cid: int
    inst: int
    cluster: int
    side: int
    held: int


class World:
    pass


def _lomax_mean_one(rng, a, size):
    return rng.pareto(a, size) * (a - 1.0)


def make_world(P: dict, seed: int) -> World:
    P = {**BASE, **P}
    ss = np.random.SeedSequence([int(seed), 20260929])
    r_struct, r_arr, r_lat, r_obs, r_mkt = [np.random.default_rng(s) for s in ss.spawn(5)]
    T, N, NCL, ttl = P["T"], P["N"], P["NCL"], P["ttl"]
    H = 100
    W = World()
    W.P = P
    W.T = T
    W.cl = np.repeat(np.arange(NCL), N // NCL)[:N]

    # ---- instrument structure -------------------------------------------------
    z = r_struct.standard_normal(N)
    dmean = P["dur_base"] * np.exp(P["dur_het"] * r_struct.standard_normal(N))
    mu_i = P["mu_mean"] + P["mu_sd"] * z
    if P["fast_slow"]:
        fs = P["fast_slow"]
        fast = np.arange(N) % 2 == 0
        dmean = np.where(fast, fs["dur_fast"], fs["dur_slow"]).astype(float)
        mu_i = np.where(fast, fs["mu_fast"], fs["mu_slow"]).astype(float)
    else:
        mu_i = mu_i + P["edge_dur_k"] * np.log(dmean / P["dur_base"])
    if P["cl_bonus"]:
        mu_i = mu_i + np.array(P["cl_bonus"])[W.cl]
    mu_after = mu_i.copy()
    reg = P["regime"]
    t_shift = T + 1
    b_before = np.full(NCL, P["score_b"], float)
    b_after = b_before.copy()
    sigc_mult = 1.0
    if reg:
        t_shift = int(reg["t_frac"] * T)
        if reg.get("perm_mu"):
            perm = np.roll(np.arange(N), N // 2)
            mu_after = mu_i[perm]
        mu_after = mu_after + reg.get("mu_shift", 0.0)
        if reg.get("b_after") is not None:
            b_after = np.array(reg["b_after"], float)
        sigc_mult = reg.get("sig_c_mult", 1.0)
    sig_i = P["sig_i"] * np.exp(P["sig_het"] * r_struct.standard_normal(N))
    fee = r_struct.uniform(P["fee_lo"], P["fee_hi"], N)
    slip = r_struct.uniform(P["slip_lo"], P["slip_hi"], N)
    snoise = P["score_sd"] * np.exp(P["score_het"] * r_struct.standard_normal(N))
    W.dmean, W.mu_i, W.sig_i, W.snoise = dmean, mu_i, sig_i, snoise

    # ---- market returns (observable only up to t-1) ------------------------
    F = r_mkt.standard_normal((T + H, NCL)) * P["sig_c"] * P["corr_scale"]
    if reg and sigc_mult != 1.0:
        F[t_shift:] *= sigc_mult
    eps = r_mkt.standard_normal((T + H, N)) * sig_i
    R = P["beta"] * F[:, W.cl] + eps
    W.R = R
    W.CR = np.vstack([np.zeros((1, N)), np.cumsum(R, axis=0)])   # CR[t] = sum_{u<t} R[u]

    # ---- arrivals -----------------------------------------------------------
    lam0 = P["load"] * P["cap_ref"] / float(np.mean(dmean) * math.exp(P["dur_sd"] ** 2 / 2))
    lam = np.full(T, lam0)
    tt = np.arange(T)
    if P["arrival"] == "mmpp":
        st = 0
        m = np.empty(T)
        for t in range(T):
            if r_arr.random() > P["mmpp_stay"]:
                st = 1 - st
            m[t] = P["mmpp_hi"] if st else P["mmpp_lo"]
        lam = lam * m / m.mean()
    elif P["arrival"] == "periodic":
        lam = lam * (1 + 0.8 * np.sin(2 * np.pi * tt / 24.0))
    if P["burst"]:
        per, ln, mult = P["burst"]
        inb = (tt % per) < ln
        lam = np.where(inb, lam * mult, lam)
    wave_mu = np.zeros(T)
    if P["wave"]:
        w = P["wave"]
        ph = (tt % w["period"]) < w["frac_low"] * w["period"]
        lam = lam * np.where(ph, w["load_low"], w["load_high"])
        wave_mu = np.where(ph, w["mu_low"], w["mu_high"])
    counts = r_arr.poisson(lam)
    arr = np.repeat(tt, counts)
    n = arr.size
    inst = r_arr.integers(0, N, n)
    is_spam = np.zeros(n, bool)
    if P["spam"]:
        sp = P["spam"]
        sc = r_arr.poisson(sp["rate"], T)
        s_arr = np.repeat(tt, sc)
        s_inst = np.full(s_arr.size, sp.get("inst", 0))
        arr = np.concatenate([arr, s_arr])
        inst = np.concatenate([inst, s_inst])
        is_spam = np.concatenate([is_spam, np.ones(s_arr.size, bool)])
        order = np.argsort(arr, kind="stable")
        arr, inst, is_spam = arr[order], inst[order], is_spam[order]
        n = arr.size
    W.n, W.arr, W.inst, W.is_spam = n, arr, inst, is_spam
    W.side = r_arr.choice([-1, 1], n)
    W.cluster = W.cl[inst]
    W.a0 = np.searchsorted(arr, np.arange(T + 1))   # opps arriving at t: a0[t]:a0[t+1]

    # ---- LATENT: edge, duration, cost --------------------------------------
    mu_arr = np.where(arr >= t_shift, mu_after[inst], mu_i[inst]) + wave_mu[arr]
    edge = mu_arr + P["q_sd"] * r_lat.standard_normal(n)
    if P["spam"]:
        sp = P["spam"]
        edge = np.where(is_spam, sp["mu"] + P["q_sd"] * 0.5 * r_lat.standard_normal(n), edge)
    if P["dur_dist"] == "pareto":
        d = dmean[inst] * (0.4 + 0.6 * _lomax_mean_one(r_lat, 2.5, n))
    else:
        d = dmean[inst] * np.exp(P["dur_sd"] * r_lat.standard_normal(n) - P["dur_sd"] ** 2 / 2)
    dur = np.clip(np.rint(d), 1, 96).astype(int)
    cost = fee[inst] + slip[inst]
    W.edge, W.dur, W.cost_true = edge, dur, cost
    W.tau = P["tau"]

    # ---- OBSERVABLES --------------------------------------------------------
    unk = r_obs.random(n) < P["p_cost_unk"]
    W.cost_obs = np.where(unk, np.nan, cost)
    miss = r_obs.random(n) < P["p_miss"]
    persist = 0.5 * snoise[inst] * r_obs.standard_normal(n)
    iid = 0.85 * snoise[inst][:, None] * r_obs.standard_normal((n, ttl + 1))
    bias = np.zeros(n)
    if P["spam"]:
        bias = np.where(is_spam, P["spam"]["bias"], 0.0)
    S = np.empty((n, ttl + 1))
    for a in range(ttl + 1):
        if P["refresh"]:
            t_eval = arr + a
            base = edge * np.exp(-a / P["tau"])
            noise = iid[:, a]
        else:
            t_eval = arr
            base = edge
            noise = iid[:, 0]
        b = np.where(t_eval >= t_shift, b_after[W.cluster], b_before[W.cluster])
        S[:, a] = P["score_a"] + b * base + persist + noise + bias
    S[miss, :] = np.nan
    W.score = S
    W.score_age_fn = (lambda a: a) if not P["refresh"] else (lambda a: 0)
    rho = P["rho_d"]
    dh = np.exp((1 - rho) * np.log(dmean[inst]) + rho * np.log(dur) + P["dh_sd"] * r_obs.standard_normal(n))
    dh[r_obs.random(n) < P["p_miss_dur"]] = np.nan
    W.dur_hat = dh
    return W


def perturb_future(W: World, t0: int, seed: int) -> World:
    """Return a copy in which everything that is only knowable after t0 is scrambled."""
    import copy
    W2 = copy.copy(W)
    rng = np.random.default_rng(seed)
    idx = np.nonzero(W.arr > t0)[0]   # opps arriving at t0 are visible at t0
    for name in ("edge", "dur", "cost_true", "cost_obs", "dur_hat", "side", "inst", "cluster", "is_spam"):
        a = getattr(W, name).copy()
        a[idx] = a[rng.permutation(idx)]
        setattr(W2, name, a)
    S = W.score.copy()
    S[idx] = S[rng.permutation(idx)]
    ages = np.arange(S.shape[1])[None, :]
    fut = (W.arr[:, None] + ages) > t0
    S = np.where(fut, S + rng.normal(0, 10, S.shape), S)
    W2.score = S
    R = W.R.copy()
    R[t0:] = rng.normal(0, 8, R[t0:].shape)
    W2.R = R
    W2.CR = np.vstack([np.zeros((1, R.shape[1])), np.cumsum(R, axis=0)])
    return W2


def perturb_rejected_latent(W: World, admitted_ids, seed: int) -> World:
    """Counterfactual test: scramble latent fields of opps that were never admitted."""
    import copy
    W2 = copy.copy(W)
    rng = np.random.default_rng(seed)
    mask = np.ones(W.n, bool)
    mask[list(admitted_ids)] = False
    idx = np.nonzero(mask)[0]
    for name in ("edge", "dur", "cost_true"):
        a = getattr(W, name).copy()
        if name == "edge":
            a[idx] = rng.normal(0, 40, idx.size)
        elif name == "dur":
            a[idx] = rng.integers(1, 60, idx.size)
        else:
            a[idx] = rng.uniform(3, 30, idx.size)
        setattr(W2, name, a)
    return W2


# ----------------------------------------------------------------------------
def run(W: World, policy, cap: int, seed: int = 0, log_decisions: bool = False):
    P, T, tau, ttl = W.P, W.T, W.tau, W.P["ttl"]
    N = P["N"]
    CR, R = W.CR, W.R
    policy.reset(cap, seed, N, W.cl)
    if getattr(policy, "needs_world", False):
        policy.attach(W)

    pending: list[int] = []
    open_pos: dict[int, list] = {}      # cid -> [ta, end, e_dec, held?]
    n = W.n
    admitted = np.zeros(n, bool)
    ta_arr = np.full(n, -1)
    held_arr = np.zeros(n, int)
    real_arr = np.full(n, np.nan)
    lat_arr = np.full(n, np.nan)
    ever_free = np.zeros(n, bool)
    expired = np.zeros(n, bool)
    evicted_flag = np.zeros(n, bool)
    pnl = np.zeros(T + 1)
    occ = np.zeros(T, int)
    cl_occ = np.zeros((T, P["NCL"]), int)
    log = []
    evals = 0
    n_evict = 0
    ev_extra = P["evict_extra"]

    def close(cid, t, forced):
        nonlocal n_evict
        ta, end, e_dec = open_pos.pop(cid)
        k = t - ta
        d = int(W.dur[cid])
        i = int(W.inst[cid])
        s = int(W.side[cid])
        mk = s * (CR[ta + k, i] - CR[ta, i])
        gross = e_dec * (k / d) + mk
        extra = ev_extra if (forced == "evict") else 0.0
        real = gross - W.cost_true[cid] - extra
        lat = e_dec * (k / d) - W.cost_true[cid] - extra
        if k > 0:
            ar = np.arange(k)
            pnl[ta:ta + k] += e_dec / d + s * R[ta:ta + k, i]
        pnl[ta] -= W.cost_true[cid] + extra
        held_arr[cid] = k
        real_arr[cid] = real
        lat_arr[cid] = lat
        if forced == "evict":
            evicted_flag[cid] = True
            n_evict += 1
        policy.on_close(dict(cid=cid, inst=i, cluster=int(W.cluster[cid]), side=s, held=k,
                             realized=real, evicted=(forced == "evict")))

    for t in range(T):
        for cid in [c for c, p in open_pos.items() if p[1] <= t]:
            close(cid, t, False)
        if t > 0:
            policy.on_returns(t - 1, R[t - 1])
        pending.extend(range(int(W.a0[t]), int(W.a0[t + 1])))
        keep = []
        for k in pending:
            if t - W.arr[k] > ttl:
                expired[k] = True
            else:
                keep.append(k)
        pending = keep
        free = cap - len(open_pos)
        views = []
        for k in pending:
            a = t - int(W.arr[k])
            sc = W.score[k, a]
            views.append(View(k, int(W.inst[k]), int(W.cluster[k]), int(W.side[k]), a,
                              float(sc), a if not P["refresh"] else 0,
                              float(W.cost_obs[k]), float(W.dur_hat[k])))
        evals += len(views)
        oviews = [OView(c, int(W.inst[c]), int(W.cluster[c]), int(W.side[c]), t - p[0])
                  for c, p in open_pos.items()]
        adm, evs = policy.decide(t, views, oviews, free, cap)
        for c in evs:
            if c in open_pos:
                close(c, t, "evict")
        free = cap - len(open_pos)
        pend_set = set(pending)
        done = []
        for c in adm:
            if free <= 0:
                break
            if c not in pend_set or c in done:
                continue
            done.append(c)
            free -= 1
            a = t - int(W.arr[c])
            e_dec = float(W.edge[c]) * math.exp(-a / tau)
            open_pos[c] = [t, t + int(W.dur[c]), e_dec]
            admitted[c] = True
            ta_arr[c] = t
        if free > 0:
            for k in pending:
                if k not in done:
                    ever_free[k] = True
        pending = [k for k in pending if k not in done]
        if log_decisions:
            log.append((t, tuple(sorted(done)), tuple(sorted(evs))))
        occ[t] = len(open_pos)
        for c in open_pos:
            cl_occ[t, W.cluster[c]] += 1
    for c in list(open_pos):
        close(c, T, "end")
    for k in pending:
        expired[k] = True

    return _metrics(W, cap, admitted, ta_arr, held_arr, real_arr, lat_arr, ever_free,
                    expired, evicted_flag, pnl[:T], occ, cl_occ, evals, n_evict, policy, log)


def _metrics(W, cap, admitted, ta_arr, held_arr, real_arr, lat_arr, ever_free, expired,
             evicted, pnl, occ, cl_occ, evals, n_evict, policy, log):
    T, n, N = W.T, W.n, W.P["N"]
    slot_h = cap * T
    used = float(held_arr[admitted].sum())
    real = float(np.nansum(real_arr))
    lat = float(np.nansum(lat_arr))
    # value of each opp had it been admitted on arrival (unique-opportunity accounting)
    v0 = W.edge - W.cost_true
    dens0 = v0 / np.maximum(W.dur, 1)
    m = {}
    m["n_opps"] = int(n)
    m["n_admit"] = int(admitted.sum())
    m["n_evict"] = int(n_evict)
    m["evals_per_opp"] = float(evals / max(n, 1))
    m["real_net"] = real
    m["lat_net"] = lat
    m["real_per_slot_hour"] = real / slot_h
    m["lat_per_slot_hour"] = lat / slot_h
    m["lat_per_used_hour"] = lat / max(used, 1.0)
    m["utilisation"] = used / slot_h
    m["idle"] = 1.0 - used / slot_h
    m["mean_hold"] = float(held_arr[admitted].mean()) if admitted.any() else 0.0
    m["admit_per_slot_hour"] = float(admitted.sum() / slot_h)
    # rejected vs admitted quality (unique opps)
    rej = ~admitted
    m["v0_admitted_mean"] = float(v0[admitted].mean()) if admitted.any() else 0.0
    m["v0_rejected_mean"] = float(v0[rej].mean()) if rej.any() else 0.0
    m["v0_all_mean"] = float(v0.mean()) if n else 0.0
    m["v0_sd"] = float(v0.std()) if n else 1.0
    m["dens0_sd"] = float(dens0.std()) if n else 1.0
    m["dens0_rms"] = float(np.sqrt(dens0.var() + dens0.mean() ** 2)) if n else 1.0
    # missed high-quality: top-quartile-density opps with positive value that expired unadmitted
    if n >= 8:
        thr = np.quantile(dens0, 0.75)
        hq = (dens0 >= thr) & (v0 > 0)
    else:
        hq = np.zeros(n, bool)
    m["n_hq"] = int(hq.sum())
    m["hq_missed_frac"] = float((hq & rej).sum() / max(hq.sum(), 1))
    m["hq_missed_capacity"] = float((hq & rej & ~ever_free).sum() / max(hq.sum(), 1))  # never saw a free slot
    m["hq_declined_with_free_slot"] = float((hq & rej & ever_free).sum() / max(hq.sum(), 1))
    m["opp_cost_missed_value_per_slot_hour"] = float(np.clip(v0[hq & rej], 0, None).sum() / slot_h)
    # concentration / diversification
    tot = cl_occ.sum(1)
    ok = tot > 0
    if ok.any():
        sh = cl_occ[ok] / tot[ok, None]
        hhi = (sh ** 2).sum(1)
        m["hhi_cluster"] = float(hhi.mean())
        m["eff_clusters"] = float((1.0 / hhi).mean())
        m["max_cluster_share"] = float(sh.max(1).mean())
    else:
        m["hhi_cluster"] = m["max_cluster_share"] = m["eff_clusters"] = 0.0
    # portfolio risk from per-step MtM PnL
    day = pnl[: (T // 24) * 24].reshape(-1, 24).sum(1)
    m["pnl_day_sd"] = float(day.std())
    m["pnl_day_mean"] = float(day.mean())
    m["ret_to_risk"] = float(day.mean() / day.std()) if day.std() > 1e-9 else 0.0
    cum = np.cumsum(pnl)
    m["max_drawdown"] = float((np.maximum.accumulate(cum) - cum).max())
    # instrument starvation
    off = np.bincount(W.inst, minlength=N)
    adm = np.bincount(W.inst[admitted], minlength=N)
    offpos = np.bincount(W.inst[v0 > 0], minlength=N)
    m["starved_inst"] = int(((off >= 8) & (adm == 0)).sum())
    m["starved_pos_inst"] = int(((offpos >= 5) & (adm == 0)).sum())
    ratio = np.where(off >= 8, adm / np.maximum(off, 1), np.nan)
    m["min_admit_ratio"] = float(np.nanmin(ratio)) if np.isfinite(ratio).any() else float("nan")
    m["inst_admit_share_max"] = float(adm.max() / max(adm.sum(), 1))
    m["spam_admit_share"] = float(admitted[W.is_spam].sum() / max(admitted.sum(), 1)) if W.is_spam.any() else 0.0
    m["spam_opp_share"] = float(W.is_spam.mean()) if n else 0.0
    # long-slot capture
    if n:
        p75 = np.quantile(W.dur, 0.75)
        lng = W.dur > p75
        m["long_slot_hour_share"] = float(held_arr[admitted & lng].sum() / max(used, 1.0))
        m["long_admit_share"] = float((admitted & lng).sum() / max(admitted.sum(), 1))
        m["short_admit_share"] = float((admitted & (W.dur <= np.quantile(W.dur, 0.25))).sum() / max(admitted.sum(), 1))
    # oscillation
    full = occ >= cap
    m["full_toggle_rate"] = float((full[1:] != full[:-1]).mean())
    m["occ_abs_change"] = float(np.abs(np.diff(occ)).mean() / cap)
    diag = policy.diag() if hasattr(policy, "diag") else {}
    m.update({f"diag_{k}": v for k, v in diag.items()})
    for w in range(4):
        lo, hi = w * T // 4, (w + 1) * T // 4
        sel = admitted & (ta_arr >= lo) & (ta_arr < hi)
        m[f"lat_q{w}"] = float(np.nansum(lat_arr[sel]) / (cap * (hi - lo)))
    m["_admitted_ids"] = np.nonzero(admitted)[0].tolist()
    m["_log"] = log
    return m


# ----------------------------------------------------------------------------
def offline_lp_bound(W: World, cap: int):
    """LP relaxation of hindsight scheduling (true values/durations, admission any time in ttl).
    NOT IMPLEMENTABLE: pure upper-bound reference (per slot-hour, latent net)."""
    from scipy.optimize import linprog
    import scipy.sparse as sp
    T, ttl, tau = W.T, W.P["ttl"], W.tau
    rows, cols, vals, c = [], [], [], []
    opp_rows, opp_cols = [], []
    j = 0
    for k in range(W.n):
        d = int(W.dur[k])
        for a in range(ttl + 1):
            ta = int(W.arr[k]) + a
            if ta >= T:
                continue
            e = W.edge[k] * math.exp(-a / tau)
            end = min(ta + d, T)
            v = e * ((end - ta) / d) - W.cost_true[k]
            if v <= 0:
                continue
            rr = np.arange(ta, end)
            rows.append(rr)
            cols.append(np.full(rr.size, j))
            opp_rows.append(k)
            opp_cols.append(j)
            c.append(-v)
            j += 1
    if j == 0:
        return 0.0
    rows = np.concatenate(rows)
    cols = np.concatenate(cols)
    A1 = sp.csr_matrix((np.ones(rows.size), (rows, cols)), shape=(T, j))
    A2 = sp.csr_matrix((np.ones(j), (opp_rows, opp_cols)), shape=(W.n, j))
    A = sp.vstack([A1, A2]).tocsr()
    b = np.concatenate([np.full(T, cap), np.ones(W.n)])
    res = linprog(c, A_ub=A, b_ub=b, bounds=(0, 1), method="highs")
    return float(-res.fun) / (cap * T)
