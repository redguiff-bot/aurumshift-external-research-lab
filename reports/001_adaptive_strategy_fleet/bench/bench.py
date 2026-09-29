"""Synthetic 'strategy fleet' attention-allocation benchmark (research-only).

Abstraction: an arm is a cell; a pull is one unit of research attention; reward is
Bernoulli(p_cell) = "this evidence increment was informative/promising".
NOT a financial reward. No capital allocation is modelled.

Usage: python bench.py <policy_name> <n_seeds> <out.json>
"""
import sys, json, time, hashlib, random, resource, warnings
import numpy as np
warnings.filterwarnings("ignore")

R, B = 1200, 10                 # rounds, pulls per round (batch, delayed feedback)
N_E, N_N, N_L = 40, 100, 20      # established, new, late-arriving cells
T_LATE, T_CP = 300, 600          # late arrival round, change-point round
GAP0, GAP1, N_GAP = 800, 900, 20 # data-gap window
WARM_PULLS = 200                 # historical pulls per established cell
STALE_S = 200                    # staleness threshold (rounds)

def make_env(seed):
    r = np.random.default_rng(10_000 + seed)
    n = N_E + N_N + N_L
    p0 = np.empty(n)
    p0[:N_E] = r.uniform(0.2, 0.7, N_E)
    p0[N_E:N_E+N_N] = r.beta(2, 6, N_N)
    p0[N_E+N_N:] = r.beta(2, 6, N_L)
    gems = list(r.choice(np.arange(N_E, N_E+N_N), 8, replace=False)) + \
           list(r.choice(np.arange(N_E+N_N, n), 4, replace=False))
    p0[gems] = r.uniform(0.7, 0.8, len(gems))
    # change point: top-10 established degrade, 10 lowest-p 'new' cells become strong
    degraded = list(np.argsort(-p0[:N_E])[:10])
    newc = np.arange(N_E, N_E+N_N)
    improved = list(newc[np.argsort(p0[newc])[:10]])
    p1 = p0.copy()
    p1[degraded] = np.maximum(0.05, p0[degraded] - 0.4)
    p1[improved] = 0.85
    pool = [c for c in range(n) if c not in improved]
    gapset = set(int(x) for x in r.choice(pool, N_GAP, replace=False))
    return dict(p0=p0, p1=p1, degraded=degraded, improved=improved, gems=[int(g) for g in gems],
                gap=gapset, n=n)

def p_at(env, t):  return env["p1"] if t >= T_CP else env["p0"]
def cells_at(env, t):
    return list(range(N_E + N_N + (N_L if t >= T_LATE else 0)))

# ---------------------------------------------------------------- adapters
class Uniform:
    """Round-robin (least-recently-pulled-first). Reference baseline, not a candidate."""
    name = "ref_roundrobin"
    def __init__(s, seed): s.last = {}; s.k = 0
    def add(s, cs): pass
    def select(s, avail, k):
        return sorted(avail, key=lambda c: (s.last.get(c, -1), c))[:k]
    def update(s, obs, t):
        for c, r in obs: s.last[c] = t
    def touched(s, chosen, t):
        for c in chosen: s.last[c] = t

class RiverP:
    def __init__(s, seed, kind):
        from river import bandit, stats, proba
        s.kind = kind
        if kind.startswith("ucbew@"):
            _, f, d = kind.split("@")
            s.p = bandit.UCB(delta=float(d), reward_obj=stats.EWMean(fading_factor=float(f)), seed=seed)
        elif kind == "ucb_mean":   s.p = bandit.UCB(delta=0.5, reward_obj=stats.Mean(), seed=seed)
        elif kind == "ucb_ew":   s.p = bandit.UCB(delta=0.5, reward_obj=stats.EWMean(fading_factor=0.9), seed=seed)
        elif kind == "ts_beta":  s.p = bandit.ThompsonSampling(reward_obj=proba.Beta(), seed=seed)
        elif kind == "exp3":     s.p = bandit.Exp3(gamma=0.1, seed=seed)
        elif kind == "eps_ew":   s.p = bandit.EpsilonGreedy(epsilon=0.1, reward_obj=stats.EWMean(fading_factor=0.9), seed=seed)
        s.name = "river_" + kind
    def add(s, cs): pass
    def select(s, avail, k):
        rem, out = list(avail), []
        for _ in range(k):
            a = s.p.pull(rem); out.append(a); rem.remove(a)
        return out
    def update(s, obs, t):
        for c, r in obs: s.p.update(c, float(r))
    def touched(s, chosen, t): pass

class MabwiserP:
    def __init__(s, seed, kind):
        from mabwiser.mab import MAB, LearningPolicy
        s.kind, s.seed = kind, seed
        s.LP, s.MAB = LearningPolicy, MAB
        s.name = "mabwiser_" + kind
        s.m = None; s.rng = np.random.default_rng(seed); s.pending = []
    def _lp(s):
        LP = s.LP
        if s.kind.startswith("ucb1@"): return LP.UCB1(alpha=float(s.kind.split("@")[1]))
        return {"ucb1": LP.UCB1(alpha=0.5), "ts": LP.ThompsonSampling(),
                "eps": LP.EpsilonGreedy(epsilon=0.1)}[s.kind]
    def add(s, cs):
        if s.m is None:
            s.m = s.MAB(arms=list(cs), learning_policy=s._lp(), seed=s.seed); s.fitted = False
        else:
            for c in cs:
                if c not in s.m.arms: s.m.add_arm(c)
    def select(s, avail, k):
        if not s.fitted:                       # MABWiser cannot predict before first fit
            return list(s.rng.choice(avail, k, replace=False))
        ex = s.m.predict_expectations()
        items = [(float(ex[c]), s.rng.random(), c) for c in avail]
        items.sort(reverse=True)
        return [c for _, _, c in items[:k]]
    def update(s, obs, t):
        if not obs: return
        dec = [c for c, _ in obs]; rew = [float(r) for _, r in obs]
        if not s.fitted: s.m.fit(dec, rew); s.fitted = True
        else: s.m.partial_fit(dec, rew)
    def touched(s, chosen, t): pass

class VWP:
    def __init__(s, seed, kind):
        import vowpalwabbit as vw
        s.kind, s.seed = kind, seed
        if kind.startswith("squarecb@"):
            args = "--cb_explore_adf --squarecb --power_t 0 --learning_rate " + kind.split("@")[1]
        else: args = None
        args = args or {"eps_default": "--cb_explore_adf --epsilon 0.1",
                "eps_constlr": "--cb_explore_adf --epsilon 0.1 --power_t 0 --learning_rate 0.05",
                "squarecb_constlr": "--cb_explore_adf --squarecb --power_t 0 --learning_rate 0.05"}[kind]
        s.vw = vw.Workspace(args + f" --quiet --random_seed {seed}")
        s.name = "vw_" + kind; s.rng = random.Random(seed); s.log = []
    def add(s, cs): pass
    def _ex(s, cells): return [f"|A c{c}" for c in cells]
    def select(s, avail, k):
        rem, out = list(avail), []
        for _ in range(k):
            pmf = s.vw.predict(s._ex(rem))
            pmf = [max(float(x), 0.0) for x in pmf]
            i = s.rng.choices(range(len(rem)), weights=pmf)[0]
            s.log.append((list(rem), i, pmf[i] / sum(pmf)))
            out.append(rem.pop(i))
        return out
    def update(s, obs, t):
        rew = {c: r for c, r in obs}
        for rem, i, prob in s.log:
            c = rem[i]
            if c not in rew: continue
            lines = s._ex(rem); lines[i] = f"0:{-float(rew[c])}:{max(prob,1e-3)} " + lines[i]
            s.vw.learn(lines)
        s.log = []
    def touched(s, chosen, t): pass

class RefDUCB:
    """CUSTOM reference implementation of Discounted-UCB (Garivier & Moulines 2008,
    arXiv:0805.3415) with optional staleness-forced revisit. Written by the reviewer for
    comparison only; it is NOT an external candidate."""
    def __init__(s, seed, gamma=0.98, fresh=False):
        s.g, s.fresh, s.rng = gamma, fresh, np.random.default_rng(seed)
        s.N, s.X, s.last = {}, {}, {}; s.name = "ref_ducb" + ("_fresh" if fresh else "") + f"@{gamma}"
    def add(s, cs): pass
    def select(s, avail, k, t=0):
        tot = sum(s.N.values()) + 1
        sc = []
        for c in avail:
            n = s.N.get(c, 0.0)
            v = float("inf") if n <= 0 else s.X[c]/n + 0.5*np.sqrt(2*np.log(max(tot,2))/n)
            if s.fresh and (t - s.last.get(c, -1)) > STALE_S: v = float("inf")
            sc.append((v, s.rng.random(), c))
        sc.sort(reverse=True)
        return [c for _, _, c in sc[:k]]
    def update(s, obs, t):
        for c in list(s.N):
            s.N[c] *= s.g; s.X[c] *= s.g
        for c, r in obs:
            s.N[c] = s.N.get(c, 0.0) + 1; s.X[c] = s.X.get(c, 0.0) + r
    def touched(s, chosen, t):
        for c in chosen: s.last[c] = t

def make_policy(name, seed):
    if name == "ref_roundrobin": return Uniform(seed)
    if name == "ref_ducb": return RefDUCB(seed)
    if name.startswith("ref_ducb@"): return RefDUCB(seed, gamma=float(name.split("@")[1]))
    if name.startswith("ref_ducbfresh@"): return RefDUCB(seed, gamma=float(name.split("@")[1]), fresh=True)
    if name == "ref_ducb_fresh": return RefDUCB(seed, fresh=True)
    fam, kind = name.split("_", 1)
    return {"river": RiverP, "mabwiser": MabwiserP, "vw": VWP}[fam](seed, kind)

# ---------------------------------------------------------------- run
def gini(x):
    x = np.sort(np.asarray(x, float)); n = len(x)
    if x.sum() == 0: return 0.0
    return float((2*np.arange(1, n+1) - n - 1).dot(x) / (n * x.sum()))
def ent(x):
    x = np.asarray(x, float); s = x.sum()
    if s == 0: return 0.0
    p = x[x > 0] / s
    return float(-(p*np.log(p)).sum() / np.log(len(x)))

def run(name, seed):
    env = make_env(seed); rng = np.random.default_rng(seed)
    pol = make_policy(name, seed)
    n = env["n"]
    # warm history for established cells (uniform logging), fed through the normal update path
    pol.add(list(range(N_E)))
    E = list(range(N_E))
    for w in range(N_E * WARM_PULLS // B):
        ch = list(rng.choice(E, B, replace=False))
        if name.startswith("vw_"):     # VW needs logged probs: route via its own select w/ restricted set
            ch = pol.select(E, B)
        obs = [(int(c), int(rng.random() < env["p0"][c])) for c in ch]
        pol.update(obs, -1)
    pol.add(list(range(N_E + N_N)))
    seq = []                       # (t, cell) chosen
    counts = np.zeros((R, n), int)
    lastev = np.full(n, -1); firstseen = {}
    reward_eff = np.zeros(R); oracle = np.zeros(R); waste = np.zeros(R)
    t_sel = 0.0
    for t in range(R):
        if t == T_LATE: pol.add(list(range(N_E + N_N, n)))
        avail = cells_at(env, t)
        p = p_at(env, t)
        t0 = time.perf_counter()
        if name.startswith("ref_ducb"): ch = pol.select(avail, B, t)
        else: ch = pol.select(avail, B)
        t_sel += time.perf_counter() - t0
        ch = [int(c) for c in ch]
        assert len(set(ch)) == B
        obs = []
        for c in ch:
            counts[t, c] += 1; seq.append((t, c))
            firstseen.setdefault(c, t)
            gap = (GAP0 <= t < GAP1) and (c in env["gap"])
            if gap: waste[t] += 1; continue          # no evidence returned; policy is NOT told
            obs.append((c, int(rng.random() < p[c]))); lastev[c] = t
            reward_eff[t] += p[c]
        t0 = time.perf_counter(); pol.update(obs, t); pol.touched(ch, t); t_sel += time.perf_counter() - t0
        ok = [c for c in avail if not ((GAP0 <= t < GAP1) and (c in env["gap"]))]
        oracle[t] = np.sort(p[ok])[-B:].sum()
    tot = counts.sum(0)
    pres = np.arange(n)
    def share(cells, a, b): return float(counts[a:b][:, cells].sum() / max(counts[a:b].sum(), 1))
    imp, deg = env["improved"], env["degraded"]
    last_touch = np.full(n, -1)
    for t, c in seq: last_touch[c] = t
    stale_end = float(np.mean([(R - 1 - last_touch[c]) > STALE_S for c in pres]))
    # max inter-pull gap per cell (rounds), cells present from their start
    maxgap = []
    for c in pres:
        ts = [t for t in range(R) if counts[t, c]]
        start = T_LATE if c >= N_E + N_N else 0
        pts = [start] + ts + [R]
        maxgap.append(max(b - a for a, b in zip(pts, pts[1:])))
    newcells = list(range(N_E, n))
    ttf = []
    for c in newcells:
        start = T_LATE if c >= N_E + N_N else 0
        ttf.append(firstseen.get(c, R) - start)
    gemtouch = [int(tot[g] >= 20) for g in env["gems"]]
    seqhash = hashlib.sha256(json.dumps(seq).encode()).hexdigest()[:16]
    W = lambda a, b: float(np.mean(oracle[a:b] - reward_eff[a:b]))
    out = dict(
        policy=pol.name, seed=seed, seqhash=seqhash,
        cov1=float(np.mean(tot > 0)), cov10=float(np.mean(tot >= 10)), zero_pull_cells=int((tot == 0).sum()),
        stale_frac_end=stale_end, max_gap_median=float(np.median(maxgap)), max_gap_p95=float(np.percentile(maxgap, 95)),
        max_gap_max=int(max(maxgap)),
        ttf_new_median=float(np.median(ttf)), ttf_new_p95=float(np.percentile(ttf, 95)),
        gems_found20=float(np.mean(gemtouch)),
        gini_pre=gini(counts[T_LATE:T_CP].sum(0)), gini_post=gini(counts[T_CP+100:].sum(0)),
        top10pct_share_pre=float(np.sort(counts[T_LATE:T_CP].sum(0))[-16:].sum() / counts[T_LATE:T_CP].sum()),
        top10pct_share_post=float(np.sort(counts[T_CP+100:].sum(0))[-16:].sum() / counts[T_CP+100:].sum()),
        entropy_pre=ent(counts[T_LATE:T_CP].sum(0)), entropy_post=ent(counts[T_CP+100:].sum(0)),
        share_improved_pre=share(imp, T_LATE, T_CP),
        share_improved_0_50=share(imp, T_CP, T_CP+50), share_improved_50_150=share(imp, T_CP+50, T_CP+150),
        share_improved_150_200=share(imp, T_CP+150, GAP0),
        share_degraded_pre=share(deg, T_LATE, T_CP),
        share_degraded_0_50=share(deg, T_CP, T_CP+50), share_degraded_150_200=share(deg, T_CP+150, GAP0),
        regret_pre=W(T_LATE, T_CP), regret_cp0_100=W(T_CP, T_CP+100), regret_cp100_200=W(T_CP+100, GAP0),
        regret_all=W(0, R),
        gap_waste_share=float(waste[GAP0:GAP1].sum() / (B * (GAP1-GAP0))),
        regret_gap=W(GAP0, GAP1), regret_post_gap=W(GAP1, R),
        select_update_seconds=t_sel,
    )
    return out

if __name__ == "__main__":
    name, ns, outp = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    t0 = time.time(); res = []
    err = None
    try:
        for s in range(ns): res.append(run(name, s))
    except Exception as e:
        import traceback; err = traceback.format_exc()
    json.dump(dict(policy=name, wall_seconds=time.time()-t0,
                   maxrss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                   error=err, runs=res), open(outp, "w"))
    print(name, "runs", len(res), "err", bool(err), f"{time.time()-t0:.1f}s")
