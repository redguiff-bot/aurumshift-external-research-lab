"""Slot-constrained admission simulator. Policies see only a View of observables."""
import math, time, hashlib
import numpy as np
from world import PAD

INGEST_MODES = ("RAW", "DEDUP_LATEST", "COOLDOWN", "SCORE_UPDATE")
COOLDOWN_STEPS = 3
PRIOR_COST = 10.0  # public conservative prior used when cost is UNKNOWN (not zero)


class Cand:
    __slots__ = ("inst", "group", "t_first", "t_last", "score", "n")
    def __init__(self, inst, group, t, score):
        self.inst, self.group, self.t_first, self.t_last, self.score, self.n = inst, group, t, t, score, 1


class Pub:
    """Public, decision-time-available information."""
    def __init__(self, w, cost_est):
        self.N, self.G = w.N, w.G
        self.group = w.group.copy()
        self.sigma_pub = w.sigma_pub.copy()
        self.cost_est = cost_est


class View:
    __slots__ = ("t", "free", "open", "cands")


class Open:
    __slots__ = ("inst", "group", "t_in", "h", "net", "gross", "score", "feat", "id")


def cost_belief(w, mode, mult):
    if mode == "known":
        return w.cost * mult
    if mode == "zero":
        return np.zeros(w.N)
    if mode == "unknown_conservative":
        return np.full(w.N, PRIOR_COST)
    raise ValueError(mode)


def run(world, policy, K, ingest="RAW", cost_mult=1.0, belief="known", ttl=None, seed=0, collect_log=False,
        oracle_ok=True):
    w = world
    N, W = w.N, w.W
    ttl = w.meta["ttl"] if ttl is None else ttl
    cost_true = w.cost * cost_mult
    cbel = cost_belief(w, belief, cost_mult)
    pub = Pub(w, cbel)
    policy.reset(pub, K, seed)
    pool = []                       # list[Cand]
    last_acc = np.full(N, -10**6)
    opens = []                      # list[Open]
    open_inst = set()
    oid = 0
    trades = []                     # dicts
    rejected = []
    emits = np.zeros(N, int); admits = np.zeros(N, int)
    den_start = [None] * N; max_deny = np.zeros(N)
    pnl_series = np.zeros(W + PAD + 2); occ = np.zeros(W, int)
    last_exit = np.full(N, -10**6)
    reentry = 0
    idle_backlog = 0
    dropped = superseded = 0
    sel_time = 0.0
    log = []
    is_oracle = not getattr(policy, "IMPLEMENTABLE", True)
    if is_oracle:
        policy.attach(lambda i, t: w.gross(i, t, w.hold(i, t)) - cost_true[i], lambda i, t: w.hold(i, t))

    def settle(i, t, h):
        g = w.gross(i, t, h)
        return g, g - cost_true[i]

    for t in range(W):
        # 1. closings
        still = []
        for o in opens:
            if o.t_in + o.h == t:
                open_inst.discard(o.inst); last_exit[o.inst] = t
                policy.on_close(o.inst, o.h, o.net, o.gross, o.feat, t)
            else:
                still.append(o)
        opens = still
        # 2. emissions
        for (i, s) in w.events[t]:
            emits[i] += 1
            if den_start[i] is None:
                den_start[i] = t
            policy.on_emit(t, i, s)
            if ingest == "RAW":
                pool.append(Cand(i, int(w.group[i]), t, s))
            elif ingest == "DEDUP_LATEST":
                pool = [c for c in pool if c.inst != i]
                pool.append(Cand(i, int(w.group[i]), t, s))
            elif ingest == "COOLDOWN":
                if t - last_acc[i] >= COOLDOWN_STEPS:
                    pool.append(Cand(i, int(w.group[i]), t, s)); last_acc[i] = t
                else:
                    dropped += 1
            elif ingest == "SCORE_UPDATE":
                ex = [c for c in pool if c.inst == i]
                if ex:
                    c = ex[0]; c.t_last = t; c.n += 1
                    if not math.isnan(s):
                        c.score = s
                else:
                    pool.append(Cand(i, int(w.group[i]), t, s))
        # 3. expiry
        keep = []
        for c in pool:
            if t - c.t_last > ttl:
                blocked = c.inst in open_inst
                h = w.hold(c.inst, c.t_last)
                g, net = settle(c.inst, c.t_last, h)
                rejected.append((c.inst, c.t_last, net, net / h, blocked))
            else:
                keep.append(c)
        pool = keep
        # 4. decisions (evictions first for policies that use them)
        def make_view():
            v = View(); v.t = t; v.free = K - len(opens); v.open = opens
            v.cands = sorted([c for c in pool if c.inst not in open_inst], key=lambda c: (c.t_first, c.inst))
            return v
        v = make_view()
        t0 = time.perf_counter()
        if v.free == 0 and v.cands and hasattr(policy, "evictions"):
            for idx in policy.evictions(t, v):
                o = opens[idx]
                hh = t - o.t_in
                if hh >= 1:
                    g, net = settle(o.inst, o.t_in, hh)
                    o.h, o.gross, o.net = hh, g, net  # truncated realised outcome (cost charged in full)
                    tr = next(x for x in trades if x["id"] == o.id)
                    tr.update(h=hh, gross=g, net=net, evicted=True)
                    open_inst.discard(o.inst); last_exit[o.inst] = t
                    policy.on_close(o.inst, hh, net, g, o.feat, t)
            opens = [o for o in opens if o.inst in open_inst]
            v = make_view()
        chosen = policy.select(t, v) if v.free > 0 and v.cands else []
        sel_time += time.perf_counter() - t0
        used = set()
        for c in chosen[: v.free]:
            if c.inst in open_inst or c.inst in used:
                continue
            used.add(c.inst)
            i = c.inst
            h = w.hold(i, t)
            g, net = settle(i, t, h)
            o = Open(); o.inst, o.group, o.t_in, o.h, o.gross, o.net = i, c.group, t, h, g, net
            o.score = c.score; o.feat = getattr(policy, "last_feat", {}).get(id(c)); o.id = oid; oid += 1
            opens.append(o); open_inst.add(i); admits[i] += 1
            if t - last_exit[i] <= 6:
                reentry += 1
            if den_start[i] is not None:
                max_deny[i] = max(max_deny[i], t - den_start[i]); den_start[i] = None
            trades.append(dict(id=o.id, t=t, inst=i, h=h, gross=g, net=net, score=c.score, evicted=False,
                               exp_edge=float(w.E[i, t]), tau_age=t - c.t_first))
            if collect_log:
                log.append((t, i))
        if used:
            pool = [c for c in pool if c.inst not in used]  # remaining copies superseded by admission
        # bookkeeping
        occ[t] = len(opens)
        free_now = K - len(opens)
        if free_now > 0:
            el = len({c.inst for c in pool if c.inst not in open_inst})
            idle_backlog += min(free_now, el)
    for i in range(N):
        if den_start[i] is not None:
            max_deny[i] = max(max_deny[i], W - den_start[i])
    return summarize(w, K, trades, rejected, emits, admits, max_deny, occ, reentry, idle_backlog,
                     dropped, sel_time, log, ingest)


def _hhi(x):
    s = x.sum()
    return float(((x / s) ** 2).sum()) if s > 0 else float("nan")


def summarize(w, K, trades, rejected, emits, admits, max_deny, occ, reentry, idle_backlog, dropped, sel_time, log, ingest):
    W, N = w.W, w.N
    n = len(trades)
    net = np.array([x["net"] for x in trades]) if n else np.zeros(0)
    h = np.array([x["h"] for x in trades], float) if n else np.zeros(0)
    inst = np.array([x["inst"] for x in trades], int) if n else np.zeros(0, int)
    tin = np.array([x["t"] for x in trades], int) if n else np.zeros(0, int)
    avail = K * W
    # busy slot-hours within window (clip at W); per-step pnl series (net spread evenly over hold)
    busy_by_inst = np.zeros(N)
    pnl = np.zeros(W + PAD + 2)
    for k in range(n):
        hh = int(h[k]); t0 = int(tin[k])
        busy_by_inst[inst[k]] += min(hh, W - t0)
        pnl[t0:t0 + hh] += net[k] / hh
    busy = float(busy_by_inst.sum())
    grp_busy = np.bincount(w.group, weights=busy_by_inst, minlength=w.G)
    cum = np.cumsum(pnl[:W])
    dd = float((np.maximum.accumulate(cum) - cum).max()) if W else 0.0
    roll = np.convolve(pnl[:W], np.ones(24), "valid") if W >= 24 else np.zeros(1)
    m = dict(
        n_admit=n, net_total=float(net.sum()),
        net_per_avail_slot_hour=float(net.sum() / avail),
        net_per_busy_slot_hour=float(net.sum() / busy) if busy > 0 else float("nan"),
        net_per_trade=float(net.mean()) if n else float("nan"),
        busy_slot_hours=busy, idle_slot_hours=float(avail - busy), idle_with_backlog=float(idle_backlog),
        turnover_per_slot_hour=float(n / avail), churn_reentry_frac=float(reentry / n) if n else float("nan"),
        mean_hold=float(h.mean()) if n else float("nan"),
        hhi_inst=_hhi(busy_by_inst), top_inst_share=float(busy_by_inst.max() / busy) if busy > 0 else float("nan"),
        hhi_group=_hhi(grp_busy),
        pnl_std=float(pnl[:W].std()), max_drawdown=dd, worst_24h=float(roll.min()),
        occ_std=float(occ.std() / K), full_frac=float((occ >= K).mean()), evict_frac=float(np.mean([x["evicted"] for x in trades])) if n else 0.0,
        dropped_by_cooldown=dropped, sel_time_s=sel_time,
    )
    # starvation
    ok = emits >= 5
    m["starve_inst_rate"] = float(((admits == 0) & ok).sum() / max(1, ok.sum()))
    mean_adm = admits[ok].mean() if ok.any() else 0
    m["starve_soft_rate"] = float(((admits < 0.25 * mean_adm) & ok).sum() / max(1, ok.sum())) if ok.any() else float("nan")
    m["max_denial_hours"] = float(max_deny[ok].max()) if ok.any() else 0.0
    m["top_inst_admit_share"] = float(admits.max() / max(1, admits.sum()))
    m["n_emit"] = int(emits.sum())
    # rejected-opportunity quality (exclude blocked-by-own-position); raw and instrument-weighted
    rj = [r for r in rejected if not r[4]]
    m["n_rejected"] = len(rj)
    if rj:
        m["rej_net_raw"] = float(np.mean([r[2] for r in rj]))
        m["rej_rate_raw"] = float(np.mean([r[3] for r in rj]))
        per = {}
        for r in rj:
            per.setdefault(r[0], []).append(r[3])
        m["rej_rate_instw"] = float(np.mean([np.mean(v) for v in per.values()]))
    else:
        m["rej_net_raw"] = m["rej_rate_raw"] = m["rej_rate_instw"] = float("nan")
    m["adm_rate"] = float(np.mean(net / h)) if n else float("nan")
    # high-quality capture: units=(inst, 12h block); HQ = unit best rate >= 75th pct of unit-best over all pool candidates
    units = {}
    for x in trades:
        units.setdefault((x["inst"], x["t"] // 12), []).append((x["net"] / x["h"], True))
    for r in rejected:
        if not r[4]:
            units.setdefault((r[0], r[1] // 12), []).append((r[3], False))
    if units:
        best = {k: max(v, key=lambda z: z[0]) for k, v in units.items()}
        thr = np.quantile([b[0] for b in best.values()], 0.75)
        hq = [k for k, b in best.items() if b[0] >= thr]
        cap = sum(1 for k in hq if any(a for (_, a) in units[k]))
        m["hq_units"] = len(hq); m["hq_capture"] = cap / max(1, len(hq)); m["hq_missed_units"] = len(hq) - cap
        m["hq_thr"] = float(thr)
    else:
        m["hq_units"] = m["hq_capture"] = m["hq_missed_units"] = 0; m["hq_thr"] = float("nan")
    m["trade_hash"] = hashlib.sha1(np.round(net, 6).tobytes() + inst.tobytes() + tin.tobytes()).hexdigest()[:12]
    m["_admits"] = admits.tolist()
    return m
