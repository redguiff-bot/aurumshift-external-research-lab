"""Policies for the V2 held-out benchmark.

Interface (all policies):
    select(t, L)            -> list of K distinct eligible cell ids (L = Ledger, observable state only)
    observe(t, events, L, logged=False)
                            -> events = [(cell, kind, value)] in draw order; called BEFORE the ledger is updated
                               with the same events, so L is the pre-update state of that cycle.
NO_OBSERVATION (kind ATTEMPTED_NO_EVIDENCE) is never turned into a reward by any policy.

A  AurumShiftLifecycleWeightedReference : operator-supplied contract, FIXED parameters (not tuned)
B  DUCBGuard                             : discounted UCB + staleness/starvation guard + bounded backoff
C  RiverPolicy                           : River bandit primitives (+ optional guard wrapper = C2)
D  VWPolicy                              : Vowpal Wabbit cb_explore_adf with shared observable features
R  RoundRobin                            : reference (least recently attempted first), not a contender
"""
import math
import random
import numpy as np
from scenario_core import K, FRESH, MAG

EXPL, PROM, PROV, DEGR, RETI = 0, 1, 2, 3, 4
STATE_NAMES = ["EXPLORATION", "PROMISING", "PROVEN", "DEGRADING", "RETIRED"]

# ---------------------------------------------------------------------------------------------
# Policy A -- OPERATOR_SUPPLIED_REFERENCE_CONTRACT (NOT derived from V1).  Fixed, never tuned.
# ---------------------------------------------------------------------------------------------
POLICY_A_VERSION = "A-ref-1.0.0"
A_WEIGHTS = {EXPL: 1.50, PROM: 1.00, PROV: 0.75, DEGR: 0.50, RETI: 0.00}   # operator-supplied
A_FLOOR_RATIO = 0.05                                                          # operator-supplied

# Evidence-derived lifecycle classifier: V2 experimental definition (NOT operator-supplied, NOT tuned).
CLS = dict(n_min=5, n_proven=20, proven_mean=0.15, low_mean=0.06, degr_long=0.10, degr_ratio=0.5)
CLS_ALT = dict(CLS, low_to_degrading=False)   # sensitivity variant: proven low-information stays PROMISING


def classify_states(L, cells, cls=CLS, low_to_degrading=True):
    """Deterministic lifecycle state from OBSERVABLE evidence only.
    STALE (age) never changes the state; ATTEMPTED_NO_EVIDENCE never changes the state."""
    n = L.n_ev[cells]
    ms, mf = L.m_slow[cells], L.m_fast[cells]
    st = np.full(len(cells), PROM, int)
    st[n < cls["n_min"]] = EXPL
    mature = n >= cls["n_proven"]
    degr = mature & (mf < cls["degr_ratio"] * ms) & (ms >= cls["degr_long"])
    if low_to_degrading:
        degr |= mature & (ms < cls["low_mean"])
    proven = mature & (ms >= cls["proven_mean"]) & ~degr
    st[proven] = PROV
    st[degr] = DEGR
    return st


class AurumShiftLifecycleWeightedReference:
    name = "A"

    def __init__(self, seed, cls=CLS, low_to_degrading=True, weights=None, floor_ratio=A_FLOOR_RATIO, tag="A"):
        self.w, self.floor, self.cls, self.ltd, self.name = weights or A_WEIGHTS, floor_ratio, cls, low_to_degrading, tag
        self.credit = None
        self.stats = dict(max_conservation_error=0.0, cycles=0, floor_units_by_mask={}, weighted_units_by_state={},
                          floor_cycles_active=0)

    def shares(self, t, L):
        """Fractional allocation (sums to K).  Returns (final, floor_part, weighted_part, mask, state)."""
        e = L.elig
        st = classify_states(L, e, self.cls, self.ltd)
        w = np.array([self.w[s] for s in st], float)
        mask = (
            (L.n_ev[e] == 0).astype(int) * 1
            + ((L.n_ev[e] > 0) & (L.age_since_evidence(t)[e] > FRESH)).astype(int) * 2
            + (L.cons_noev[e] > 0).astype(int) * 4
            + L.pit_unverified[e].astype(int) * 8
        )
        expl = mask > 0
        floor_budget = K * self.floor
        floor_part = np.zeros(len(e))
        if expl.any():
            floor_part[expl] = floor_budget / expl.sum()
            distributed = floor_budget
        else:
            distributed = 0.0          # whole floor returns to the main budget
        remaining = K - distributed
        weighted = remaining * w / w.sum()
        return floor_part + weighted, floor_part, weighted, mask, st

    def select(self, t, L):
        e = L.elig
        if self.credit is None:
            self.credit = np.zeros(len(L.n_att))
        if len(e) <= K:
            self.credit[e] = 0.0
            return [int(c) for c in e]
        final, floor_part, weighted, mask, st = self.shares(t, L)
        err = abs(final.sum() - K)
        assert final.min() >= 0
        s = self.stats
        s["max_conservation_error"] = max(s["max_conservation_error"], err)
        s["cycles"] += 1
        if floor_part.any():
            s["floor_cycles_active"] += 1
        if t >= 80:   # eval only for logs
            for m in np.unique(mask):
                if m:
                    s["floor_units_by_mask"][int(m)] = s["floor_units_by_mask"].get(int(m), 0.0) + float(floor_part[mask == m].sum())
            for k_ in range(4):
                s["weighted_units_by_state"][STATE_NAMES[k_]] = s["weighted_units_by_state"].get(STATE_NAMES[k_], 0.0) + float(weighted[st == k_].sum())
        self.credit[e] += final
        order = np.lexsort((e, -self.credit[e]))       # highest credit first, ties by id
        pick = e[order[:K]]
        self.credit[pick] -= 1.0
        return [int(c) for c in pick]

    def observe(self, t, events, L, logged=False):
        pass


# ---------------------------------------------------------------------------------------------
class RoundRobin:
    name = "R"

    def __init__(self, seed):
        self.stats = {}

    def select(self, t, L):
        e = L.elig
        ref = np.where(L.n_att[e] > 0, L.last_att[e], L.birth[e])
        order = np.lexsort((e, ref))
        return [int(c) for c in e[order[:K]]]

    def observe(self, t, events, L, logged=False):
        pass


# ---------------------------------------------------------------------------------------------
# Shared staleness / starvation guard (V1 report 06 s1 + 07 s3.1: staleness-forced revisit and an
# ATTEMPTED_NO_EVIDENCE channel with bounded backoff).  Specified independently of any held-out result.
# ---------------------------------------------------------------------------------------------
def guard_sets(t, L, S, M):
    """Returns (forced_cells_in_priority_order, excluded_from_score_path_mask_over_elig)."""
    e = L.elig
    k = L.cons_noev[e]
    mult = np.minimum(2.0 ** k, M) if M > 1 else np.ones(len(e))
    S_k = S * mult
    age = L.age_since_attempt(t)[e]
    overdue = age - S_k
    forced_mask = overdue > 0
    order = np.lexsort((e, -(age / S_k)))
    forced = [int(e[i]) for i in order if forced_mask[i]]
    excl = (k >= 1) & (age <= S_k) if M > 1 else np.zeros(len(e), bool)
    return forced, excl


class DUCBGuard:
    """Policy B.  Discounted UCB (Garivier & Moulines 2008) where the discount applies to value AND count,
    plus an explicit staleness guard and bounded no-evidence backoff.  CUSTOM reference implementation."""
    name = "B"

    def __init__(self, seed, gamma=0.995, S=50, M=4, c=0.5, cap=K // 2, tag="B"):
        self.g, self.S, self.M, self.c, self.cap, self.name = gamma, S, M, c, cap, tag
        self.rng = np.random.default_rng([seed, 202])
        self.N = self.X = None
        self.stats = dict(reason=dict(REVISIT_STALE=0, EXPLORE_NEW=0, EXPLOIT_PROMISING=0, FILL=0))

    def _init(self, L):
        self.N, self.X = np.zeros(len(L.n_att)), np.zeros(len(L.n_att))

    def select(self, t, L):
        if self.N is None:
            self._init(L)
        e = L.elig
        forced, excl = guard_sets(t, L, self.S, self.M)
        picks = forced[: min(self.cap, K)]
        self.stats["reason"]["REVISIT_STALE"] += len(picks)
        taken = set(picks)
        cand = np.array([c for c, x in zip(e, excl) if not x and int(c) not in taken], int)
        need = min(K, len(e)) - len(picks)
        if need > 0 and len(cand):
            n = self.N[cand]
            tot = max(self.N[e].sum() + 1, 2.0)
            with np.errstate(divide="ignore", invalid="ignore"):
                idx = self.X[cand] / n + self.c * np.sqrt(2 * math.log(tot) / n)
            idx = np.where(n <= 1e-12, np.inf, idx)
            tie = self.rng.random(len(cand))
            order = np.lexsort((tie, -idx))
            for i in order[:need]:
                picks.append(int(cand[i]))
                self.stats["reason"]["EXPLORE_NEW" if np.isinf(idx[i]) else "EXPLOIT_PROMISING"] += 1
                taken.add(int(cand[i]))
        need = min(K, len(e)) - len(picks)
        if need > 0:                                   # fill from remaining eligible, oldest attempt first
            rest = [int(c) for c in e if int(c) not in taken]
            ref = np.where(L.n_att[rest] > 0, L.last_att[rest], L.birth[rest])
            for i in np.lexsort((rest, ref))[:need]:
                picks.append(rest[i]); self.stats["reason"]["FILL"] += 1
        return picks

    def observe(self, t, events, L, logged=False):
        if self.N is None:
            self._init(L)
        self.N *= self.g
        self.X *= self.g
        for c, kind, v in events:
            if kind == "EVIDENCE":
                self.N[c] += 1.0
                self.X[c] += v
            # ATTEMPTED_NO_EVIDENCE: NO reward update (not a negative observation)


# ---------------------------------------------------------------------------------------------
class RiverPolicy:
    """Policy C.  Uses River's own bandit classes (river.bandit.*) unmodified.
    Wrapper: input hygiene (finite value, no NaN), dynamic arm list (eligible cells only),
    ATTEMPTED_NO_EVIDENCE -> no update.  With guard=(S,M): C2 = River + the shared guard."""
    name = "C"

    def __init__(self, seed, algo="eps_ew", fading=0.1, eps=0.1, delta=0.5, guard=None, tag=None):
        from river import bandit, stats
        self.algo, self.guard = algo, guard
        rew = stats.Mean() if algo == "ucb_mean" else stats.EWMean(fading_factor=fading)
        if algo.startswith("eps"):
            self.p = bandit.EpsilonGreedy(epsilon=eps, reward_obj=rew, seed=seed)
        else:
            self.p = bandit.UCB(delta=delta, reward_obj=rew, seed=seed)
        self.name = tag or ("C2" if guard else "C")
        self.stats = dict(updates=0, nonfinite_dropped=0, reason=dict(REVISIT_STALE=0, RIVER=0))

    def select(self, t, L):
        e = L.elig
        picks, taken = [], set()
        excl = np.zeros(len(e), bool)
        if self.guard:
            forced, excl = guard_sets(t, L, *self.guard)
            picks = forced[: min(K // 2, K)]
            taken = set(picks)
            self.stats["reason"]["REVISIT_STALE"] += len(picks)
        cands = [int(c) for c, x in zip(e, excl) if not x and int(c) not in taken]
        need = min(K, len(e)) - len(picks)
        while need > 0 and cands:
            a = self.p.pull(cands)
            picks.append(int(a)); cands.remove(a); need -= 1
            self.stats["reason"]["RIVER"] += 1
        if need > 0:
            rest = [int(c) for c in e if int(c) not in set(picks)]
            ref = np.where(L.n_att[rest] > 0, L.last_att[rest], L.birth[rest])
            for i in np.lexsort((rest, ref))[:need]:
                picks.append(rest[i])
        return picks

    def observe(self, t, events, L, logged=False):
        for c, kind, v in events:
            if kind != "EVIDENCE":
                continue                      # no channel for NO_OBSERVATION in River: skip, never 0
            if v is None or not math.isfinite(v):
                self.stats["nonfinite_dropped"] += 1
                continue
            self.p.update(int(c), float(min(max(v, 0.0), 1.0)))
            self.stats["updates"] += 1


# ---------------------------------------------------------------------------------------------
def _bucket(x, edges):
    for i, e in enumerate(edges):
        if x <= e:
            return i
    return len(edges)


class VWPolicy:
    """Policy D.  VW cb_explore_adf.  Actions = eligible cells described ONLY by observable features shared
    across cells (lifecycle-relevant statistics from the ledger + static generic group descriptor).
    No cell-id feature => information is shared; no privileged/future information."""
    name = "D"

    def __init__(self, seed, algo="squarecb", lr=0.05, expl=10.0, use_group=True, tag="D"):
        import vowpalwabbit as vw
        self.name, self.use_group = tag, use_group
        if algo == "squarecb":
            args = f"--cb_explore_adf --squarecb --gamma_scale {expl} --power_t 0 --learning_rate {lr}"
        else:
            args = f"--cb_explore_adf --epsilon {expl} --power_t 0 --learning_rate {lr}"
        self.vw = vw.Workspace(args + f" --quiet --random_seed {seed}")
        self.rng = random.Random(seed)
        self.pending = None
        self.stats = dict(learn_calls=0, no_evidence_skipped=0)

    def line(self, t, L, c):
        ev_age = int(L.age_since_evidence(t)[c]); att_age = int(L.age_since_attempt(t)[c])
        toks = [
            f"nev{_bucket(L.n_ev[c], [0, 4, 19, 49])}",
            "age_none" if L.n_ev[c] == 0 else f"age{_bucket(ev_age, [10, 30, 60, 120])}",
            f"att{_bucket(att_age, [10, 30, 60])}",
            f"gap{int(L.cons_noev[c] > 0)}",
            f"gapk{min(int(L.cons_noev[c]), 4)}",
            f"pit{int(L.pit_unverified[c])}",
            "mean_none" if L.n_ev[c] == 0 else f"mean{_bucket(L.m_slow[c], [0.03, 0.08, 0.15, 0.25])}",
            "trend_none" if L.n_ev[c] < 5 else f"trend{_bucket(L.m_fast[c] - L.m_slow[c], [-0.08, -0.02, 0.02, 0.08])}",
        ]
        s = "|F " + " ".join(toks)
        if L.n_ev[c] > 0:
            s += f" |N ms:{L.m_slow[c]:.4f} mf:{L.m_fast[c]:.4f}"
        if self.use_group:
            s += f" |G g{int(L.group[c])}"
        return s

    def select(self, t, L):
        e = [int(c) for c in L.elig]
        lines_all = {c: self.line(t, L, c) for c in e}
        rem, out, log = list(e), [], []
        for _ in range(min(K, len(e))):
            lines = [lines_all[c] for c in rem]
            pmf = [max(float(x), 0.0) for x in self.vw.predict(lines)]
            i = self.rng.choices(range(len(rem)), weights=pmf)[0]
            log.append((list(rem), i, pmf[i] / sum(pmf)))
            out.append(rem.pop(i))
        self.pending = (lines_all, log)
        return out

    def _learn(self, lines_all, rem, i, prob, value):
        lines = [lines_all[c] for c in rem]
        lines[i] = f"0:{-float(value)}:{max(prob, 1e-3)} " + lines[i]
        self.vw.learn(lines)
        self.stats["learn_calls"] += 1

    def observe(self, t, events, L, logged=False):
        if logged:                                     # common uniform logging policy, exact propensities
            e = [int(c) for c in L.elig]
            lines_all = {c: self.line(t, L, c) for c in e}
            rem = list(e)
            for c, kind, v in events:
                prob = 1.0 / len(rem)
                i = rem.index(c)
                if kind == "EVIDENCE":
                    self._learn(lines_all, rem, i, prob, v)
                else:
                    self.stats["no_evidence_skipped"] += 1
                rem.pop(i)
            return
        lines_all, log = self.pending
        res = {c: (k, v) for c, k, v in events}
        for rem, i, prob in log:
            c = rem[i]
            kind, v = res[c]
            if kind == "EVIDENCE":
                self._learn(lines_all, rem, i, prob, v)
            else:
                self.stats["no_evidence_skipped"] += 1
        self.pending = None
