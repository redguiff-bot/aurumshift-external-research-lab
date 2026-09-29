"""Allocation policies.  Implementable policies only ever receive View/OView tuples,
feedback at position close (`on_close`) and past instrument returns (`on_returns`).
Oracle / canary policies receive the World and are flagged implementable=False."""
from __future__ import annotations
import math
from collections import deque
import numpy as np

NAN = float("nan")
isnan = math.isnan


class Policy:
    name = "BASE"
    implementable = True
    needs_world = False
    family = "baseline"

    def reset(self, cap, seed, N, cl):
        self.cap, self.N, self.cl = cap, N, np.asarray(cl)
        self.rng = np.random.default_rng(12345 + seed)

    def on_returns(self, t, r): pass
    def on_close(self, rec): pass
    def decide(self, t, pend, openp, free, cap): return [], []
    def diag(self): return {}


# ============================ mandatory baselines ==============================
class FIFO(Policy):
    name, family = "FIFO", "baseline"

    def decide(self, t, pend, openp, free, cap):
        order = sorted(pend, key=lambda v: (-v.age, v.cid))
        return [v.cid for v in order[:max(free, 0)]], []


class RoundRobin(Policy):
    name, family = "ROUND_ROBIN", "baseline"

    def reset(self, cap, seed, N, cl):
        super().reset(cap, seed, N, cl); self.ptr = 0

    def decide(self, t, pend, openp, free, cap):
        by = {}
        for v in sorted(pend, key=lambda v: (-v.age, v.cid)):
            by.setdefault(v.inst, []).append(v.cid)
        out = []
        i = self.ptr
        for _ in range(self.N):
            if len(out) >= free: break
            if i in by:
                out.append(by[i][0]); self.ptr = (i + 1) % self.N
            i = (i + 1) % self.N
        return out, []


class RandomPolicy(Policy):
    name, family = "RANDOM_SEEDED", "baseline"

    def decide(self, t, pend, openp, free, cap):
        if not pend or free <= 0: return [], []
        ids = [v.cid for v in pend]
        k = min(free, len(ids))
        return list(self.rng.choice(ids, size=k, replace=False)), []


class EqualQuota(Policy):
    """Equal opportunity: least-admitted instrument first (ties FIFO)."""
    name, family = "EQUAL_QUOTA", "baseline"

    def reset(self, cap, seed, N, cl):
        super().reset(cap, seed, N, cl); self.cnt = np.zeros(N)

    def decide(self, t, pend, openp, free, cap):
        out = []
        cnt = self.cnt.copy()
        left = list(pend)
        while left and len(out) < free:
            v = min(left, key=lambda v: (cnt[v.inst], -v.age, v.cid))
            out.append(v.cid); cnt[v.inst] += 1; left.remove(v)
        for c in out:
            pass
        for v in pend:
            if v.cid in out: self.cnt[v.inst] += 1
        return out, []


class OldestSlot(Policy):
    """Turnover-neutral: FIFO admission; when full, force-close the oldest slot
    (if held >= min_hold) to admit the oldest waiting candidate."""
    name, family = "OLDEST_SLOT", "baseline"

    def __init__(self, min_hold=6): self.min_hold = min_hold

    def decide(self, t, pend, openp, free, cap):
        order = sorted(pend, key=lambda v: (-v.age, v.cid))
        out, ev = [], []
        oldest = sorted(openp, key=lambda o: -o.held)
        f = free
        for v in order:
            if f > 0:
                out.append(v.cid); f -= 1
            elif oldest and oldest[0].held >= self.min_hold:
                ev.append(oldest.pop(0).cid); out.append(v.cid)
            else:
                break
        return out, ev


class FifoNetPos(Policy):
    """FIFO restricted to candidates whose estimated net edge is positive
    (separates 'filtering' from 'ranking')."""
    name, family = "FIFO_NETPOS", "control"

    def reset(self, cap, seed, N, cl):
        super().reset(cap, seed, N, cl); self.s_sum = 0.0; self.s_n = 0; self.c_sum = 0.0; self.c_n = 0; self.seen = set()

    def decide(self, t, pend, openp, free, cap):
        for v in pend:
            if v.cid in self.seen: continue
            self.seen.add(v.cid)
            if not isnan(v.score): self.s_sum += v.score; self.s_n += 1
            if not isnan(v.cost): self.c_sum += v.cost; self.c_n += 1
        sm = self.s_sum / self.s_n if self.s_n else 0.0
        cm = self.c_sum / self.c_n if self.c_n else 0.0
        ok = [v for v in pend if (sm if isnan(v.score) else v.score) - (cm if isnan(v.cost) else v.cost) > 0]
        order = sorted(ok, key=lambda v: (-v.age, v.cid))
        return [v.cid for v in order[:max(free, 0)]], []


# ============================ shared estimation helpers ========================
class Stats:
    """Online, causal population statistics used by value-based policies."""

    def init_stats(self, N):
        self.s_n = 0; self.s_sum = 0.0; self.s_sq = 0.0
        self.c_n = 0; self.c_sum = 0.0
        self.seen = set()
        self.lam = 0.3            # EMA new-opps per step
        self.hold_ema = 12.0
        self.dur_inst = np.full(N, np.nan)
        self.dens_buf = deque(maxlen=300)
        self.cov_n = 0
        self.cov_mean = np.zeros(N)
        self.cov = np.eye(N) * 40.0
        self.entry = {}

    def observe(self, pend):
        new = 0
        for v in pend:
            if v.cid in self.seen: continue
            self.seen.add(v.cid); new += 1
            if not isnan(v.score):
                self.s_n += 1; self.s_sum += v.score; self.s_sq += v.score ** 2
            if not isnan(v.cost):
                self.c_n += 1; self.c_sum += v.cost
        self.lam += 0.02 * (new - self.lam)

    @property
    def s_mean(self): return self.s_sum / self.s_n if self.s_n else 0.0
    @property
    def s_sd(self):
        if self.s_n < 5: return 10.0
        return max(self.s_sq / self.s_n - self.s_mean ** 2, 1.0) ** 0.5
    @property
    def c_mean(self): return self.c_sum / self.c_n if self.c_n else 8.0

    def dur_prior(self, inst):
        d = self.dur_inst[inst]
        return self.hold_ema if isnan(d) else d

    def upd_close(self, rec):
        h = max(rec["held"], 1)
        self.hold_ema += 0.05 * (h - self.hold_ema)
        i = rec["inst"]
        if not rec["evicted"]:
            self.dur_inst[i] = h if isnan(self.dur_inst[i]) else self.dur_inst[i] + 0.15 * (h - self.dur_inst[i])

    def on_returns(self, t, r):
        a = 0.01
        self.cov_n += 1
        d = r - self.cov_mean
        self.cov_mean += a * d
        if self.cov_n < 30:
            return
        self.cov = (1 - a) * self.cov + a * np.outer(d, d)

    def corr_hat(self, delta=0.2):
        S = (1 - delta) * self.cov + delta * np.diag(np.diag(self.cov))
        sd = np.sqrt(np.diag(S)); return S, S / np.outer(sd, sd)


class Calib:
    """Hierarchical Bayesian linear calibration net_realised ~ a + b*x with prior (0,1)."""

    def __init__(self, N, kappa=25.0):
        self.N, self.kappa = N, kappa
        self.X = [[] for _ in range(N)]; self.Y = [[] for _ in range(N)]
        self.pool_m = np.array([0.0, 1.0]); self.m = [np.array([0.0, 1.0])] * N
        self.Linv = [np.eye(2) * 1e-4] * N; self.sig2 = 60.0 ** 2; self.n = 0

    def add(self, i, x, y):
        self.X[i].append(x); self.Y[i].append(y); self.n += 1
        if self.n % 5 == 0: self._fit()

    def _fit(self):
        allx = np.array([x for l in self.X for x in l]); ally = np.array([y for l in self.Y for y in l])
        A = np.c_[np.ones_like(allx), allx]
        k0 = 20.0
        Lam = k0 * np.eye(2) + A.T @ A / self.sig2
        self.pool_m = np.linalg.solve(Lam, k0 * np.array([0.0, 1.0]) + A.T @ ally / self.sig2)
        res = ally - A @ self.pool_m
        self.sig2 = max(float(np.mean(res ** 2)), 25.0)
        for i in range(self.N):
            if not self.X[i]:
                self.m[i] = self.pool_m; self.Linv[i] = np.linalg.inv(Lam); continue
            a = np.c_[np.ones(len(self.X[i])), np.array(self.X[i])]
            L = self.kappa * np.eye(2) + a.T @ a / self.sig2
            Li = np.linalg.inv(L)
            self.m[i] = Li @ (self.kappa * self.pool_m + a.T @ np.array(self.Y[i]) / self.sig2)
            self.Linv[i] = Li

    def predict(self, i, x):
        phi = np.array([1.0, x])
        return float(phi @ self.m[i]), float(math.sqrt(max(phi @ self.Linv[i] @ phi, 0.0)))


# ============================ configurable value engine ========================
class Engine(Policy, Stats):
    """One engine, many published ideas.  Options:
      raw            rank by raw score (ignore cost)
      unk_cost       'prior' | 'zero'          (UNKNOWN_COST handling)
      missing        'neutral' | 'reject'      (missing score handling)
      calib          None | dict(k, kappa)     Bayesian calibration + LCB
      hazard_tau     None | float              staleness discount exp(-score_age/tau)
      h0             None | float              density = v / (dur_hat + h0)
      shadow         None | dict(eta, target)  bid-price v - lam*dur   (dual ascent)
      thr            None | ('knap',L,U) | ('fluid',s)
      reserve        None | (r, q)             trunk reservation
      cap_frac       None | f                  per-cluster cap ceil(f*cap)
      corr           None | (mode, param)      'pen' | 'marg' | 'hard'
      evict          None | (min_hold, M)      swap-out worst open position
    """
    family = "ranking"

    def __init__(self, name, family="ranking", **o):
        self.name, self.family, self.o = name, family, o

    def reset(self, cap, seed, N, cl):
        Policy.reset(self, cap, seed, N, cl); self.init_stats(N)
        c = self.o.get("calib")
        self.cal = Calib(N, c.get("kappa", 25.0)) if c else None
        self.lam_sh = 0.0
        self.lam_hist = []
        self.thr_hist = []

    def on_returns(self, t, r): Stats.on_returns(self, t, r)

    def on_close(self, rec):
        self.upd_close(rec)
        e = self.entry.pop(rec["cid"], None)
        if e is not None and self.cal is not None and not rec["evicted"]:
            self.cal.add(rec["inst"], e["x"], rec["realized"])

    # ---- per-candidate estimate -----------------------------------------------
    def est(self, v):
        o = self.o
        miss = isnan(v.score)
        if miss and o.get("missing") == "reject": return None
        s = self.s_mean if miss else v.score
        if o.get("hazard_tau") and not miss:
            s = s * math.exp(-v.score_age / o["hazard_tau"])
        if isnan(v.cost):
            c = 0.0 if o.get("unk_cost") == "zero" else self.c_mean
        else:
            c = v.cost
        dur = self.dur_prior(v.inst) if isnan(v.dur_hat) else v.dur_hat
        dur = max(dur, 1.0)
        if o.get("raw"): net = s
        else: net = s - c
        x = net
        if self.cal is not None:
            mu, se = self.cal.predict(v.inst, x)
            unc = se + (0.0 if not miss else 0.5 * self.s_sd * abs(self.cal.pool_m[1]))
            net = mu - o["calib"].get("k", 0.5) * unc
        return net, dur, x

    def decide(self, t, pend, openp, free, cap):
        o = self.o
        self.observe(pend)
        cand = {}
        for v in pend:
            e = self.est(v)
            if e is None: continue
            net, dur, x = e
            if o.get("h0") is not None: key = net / (dur + o["h0"])
            elif o.get("shadow"): key = net - self.lam_sh * dur
            else: key = net
            dens = net / (dur + (o.get("h0") or 0.0) + 1e-9)
            cand[v.cid] = (v, net, dur, key, x)
            if v.age == 0:
                self.dens_buf.append(net / (dur + (o.get("h0") or 0.0)))
        # threshold
        thr_kind = o.get("thr")
        thr_val = 0.0
        if thr_kind and thr_kind[0] == "fluid" and len(self.dens_buf) >= 30:
            demand = self.lam * self.hold_ema
            if demand > cap:
                q = 1.0 - min(1.0, thr_kind[1] * cap / demand)
                thr_val = max(0.0, float(np.quantile(np.array(self.dens_buf), q)))
        self.thr_hist.append(thr_val)
        hi_thr = None
        if o.get("reserve") and len(self.dens_buf) >= 30:
            hi_thr = float(np.quantile(np.array(self.dens_buf), o["reserve"][1]))
        S = Rho = None
        corr = o.get("corr")
        if corr:
            S, Rho = self.corr_hat()
            sbar = float(np.sqrt(np.mean(np.diag(S))))
        cap_lim = math.ceil(o["cap_frac"] * cap) if o.get("cap_frac") else None
        cl_cnt = np.zeros(int(self.cl.max()) + 1, int)
        pos = []      # (inst, side) of open + selected
        for op in openp:
            cl_cnt[op.cluster] += 1; pos.append((op.inst, op.side))
        out = []
        left = dict(cand)
        f = free
        while f > 0 and left:
            best, bk = None, -1e18
            for cid, (v, net, dur, key, x) in left.items():
                if cap_lim is not None and cl_cnt[v.cluster] >= cap_lim: continue
                k = key
                if corr and self.cov_n >= 60:
                    cross = sum(v.side * sd * S[v.inst, j] for j, sd in pos)
                    mode, par = corr
                    if mode == "pen": k = key - par * dur * cross / sbar / (dur + (o.get("h0") or 0.0) if o.get("h0") is not None else 1.0)
                    elif mode == "marg": k = key - par * dur * (S[v.inst, v.inst] + 2 * cross) / (2 * sbar) / (dur + (o.get("h0") or 0.0) if o.get("h0") is not None else 1.0)
                    elif mode == "hard":
                        if any(v.side * sd * Rho[v.inst, j] >= par for j, sd in pos): continue
                if k > bk: best, bk = cid, k
            if best is None: break
            v, net, dur, key, x = left[best]
            # admission thresholds
            if bk <= thr_val or net <= 0: break
            occ_after = 1.0 - (f - 1) / cap
            if thr_kind and thr_kind[0] == "knap":
                L, U = thr_kind[1], thr_kind[2]
                z = (cap - f) / cap
                psi = (U * math.e / L) ** z * (L / math.e)
                dens_b = net / (dur + (o.get("h0") or 0.0))
                if dens_b < psi: break
            if o.get("reserve") and hi_thr is not None:
                dens_b = net / (dur + (o.get("h0") or 0.0))
                if dens_b < hi_thr and (f - 1) < o["reserve"][0]:
                    del left[best]; continue
            out.append(best); f -= 1
            cl_cnt[v.cluster] += 1; pos.append((v.inst, v.side))
            self.entry[best] = dict(x=x, dens=net / (dur + (o.get("h0") or 0.0)), net=net)
            del left[best]
        ev = []
        if o.get("evict") and f == 0 and left and openp:
            mh, M = o["evict"]
            cid, (v, net, dur, key, x) = max(left.items(), key=lambda kv: kv[1][3])
            cd = net / (dur + (o.get("h0") or 0.0))
            cands = [op for op in openp if op.held >= mh and op.cid in self.entry]
            if cands and net > 0:
                w = min(cands, key=lambda op: self.entry[op.cid]["dens"])
                od = self.entry[w.cid]["dens"]
                if cd >= od * (1 + M) + 0.25 * M:
                    ev.append(w.cid); out.append(cid)
                    self.entry[cid] = dict(x=x, dens=cd, net=net)
        if o.get("shadow"):
            sh = o["shadow"]
            util = (cap - free + len(out) - len(ev)) / cap
            self.lam_sh = max(0.0, self.lam_sh + sh["eta"] * (util - sh["target"]))
            self.lam_hist.append(self.lam_sh)
        return out, ev

    def diag(self):
        d = {}
        h = self.lam_hist if self.o.get("shadow") else self.thr_hist
        if len(h) > 10:
            a = np.array(h); d["thr_cv"] = float(a.std() / (abs(a.mean()) + 1e-6)); d["thr_flip"] = float((np.diff(a) != 0).mean())
        return d


# ============================ secretary (irrevocable) ==========================
class Secretary(Policy, Stats):
    name, family = "SECRETARY_1_OVER_E", "online_selection"

    def __init__(self, n_w=20): self.n_w = n_w

    def reset(self, cap, seed, N, cl):
        Policy.reset(self, cap, seed, N, cl); self.init_stats(N)
        self.i = 0; self.mx = -1e9

    def on_returns(self, t, r): pass
    def on_close(self, rec): self.upd_close(rec)

    def decide(self, t, pend, openp, free, cap):
        out = []
        r = int(self.n_w / math.e)
        for v in sorted([v for v in pend if v.age == 0], key=lambda v: v.cid):
            s = self.s_mean if isnan(v.score) else v.score
            c = self.c_mean if isnan(v.cost) else v.cost
            d = self.dur_prior(v.inst) if isnan(v.dur_hat) else v.dur_hat
            dens = (s - c) / max(d, 1.0)
            if self.i < r:
                self.mx = max(self.mx, dens)
            elif dens > self.mx and dens > 0 and len(out) < free:
                out.append(v.cid)
            self.i += 1
            if self.i >= self.n_w: self.i = 0; self.mx = -1e9
        self.seen.update(v.cid for v in pend)
        return out, []


# ============================ bandits ==========================================
class LinBandit(Policy, Stats):
    family = "bandit"

    def __init__(self, name, mode="ucb", alpha=0.3, reg=10.0):
        self.name, self.mode, self.alpha, self.reg = name, mode, alpha, reg

    def reset(self, cap, seed, N, cl):
        Policy.reset(self, cap, seed, N, cl); self.init_stats(N)
        self.d = 6
        self.A = np.eye(self.d) * self.reg; self.b = np.zeros(self.d); self.Ainv = np.eye(self.d) / self.reg
        self.th = np.zeros(self.d)

    def on_returns(self, t, r): pass

    def feat(self, v):
        miss = isnan(v.score)
        s = self.s_mean if miss else v.score
        c = self.c_mean if isnan(v.cost) else v.cost
        d = self.dur_prior(v.inst) if isnan(v.dur_hat) else v.dur_hat
        return np.array([1.0, s / 10.0, c / 10.0, d / 12.0, 1.0 if miss else 0.0, (s - c) / 10.0 / max(d / 12.0, 0.25)])

    def on_close(self, rec):
        self.upd_close(rec)
        x = self.entry.pop(rec["cid"], None)
        if x is None or rec["evicted"]: return
        y = rec["realized"] / max(rec["held"], 1) / 5.0
        y = float(np.clip(y, -3, 3))
        self.A += np.outer(x, x); self.b += y * x
        self.Ainv = np.linalg.inv(self.A); self.th = self.Ainv @ self.b

    def decide(self, t, pend, openp, free, cap):
        self.observe(pend)
        if free <= 0 or not pend: return [], []
        th = self.th
        if self.mode == "ts":
            th = self.rng.multivariate_normal(self.th, (self.alpha ** 2) * self.Ainv)
        sc = []
        for v in pend:
            x = self.feat(v)
            if self.mode == "ucb": val = float(th @ x + self.alpha * math.sqrt(x @ self.Ainv @ x))
            else: val = float(th @ x)
            sc.append((val, -v.cid, v, x))
        sc.sort(key=lambda z: (-z[0], -z[1]))
        out = []
        for val, _, v, x in sc[:free]:
            if val > 0:
                out.append(v.cid); self.entry[v.cid] = x
        return out, []


# ============================ sleeping experts (Hedge over instruments) ========
class SleepingHedge(Policy, Stats):
    name, family = "SLEEPING_HEDGE", "sleeping_experts"

    def __init__(self, eta=0.1, zeta=6.0): self.eta, self.zeta = eta, zeta

    def reset(self, cap, seed, N, cl):
        Policy.reset(self, cap, seed, N, cl); self.init_stats(N)
        self.logw = np.zeros(N)

    def on_returns(self, t, r): pass

    def on_close(self, rec):
        self.upd_close(rec)
        if rec["evicted"]: return
        loss = -float(np.clip(rec["realized"] / max(rec["held"], 1) / 5.0, -1, 1))
        self.logw[rec["inst"]] = float(np.clip(self.logw[rec["inst"]] - self.eta * loss, -3, 3))

    def decide(self, t, pend, openp, free, cap):
        self.observe(pend)
        if free <= 0 or not pend: return [], []
        awake = sorted({v.inst for v in pend})
        mlw = float(np.mean(self.logw[awake]))
        sc = []
        for v in pend:
            s = self.s_mean if isnan(v.score) else v.score
            c = self.c_mean if isnan(v.cost) else v.cost
            sc.append(((s - c) + self.zeta * (self.logw[v.inst] - mlw), v))
        sc.sort(key=lambda z: (-z[0], z[1].cid))
        return [v.cid for val, v in sc[:free] if (val > 0)], []


# ============================ oracles (NOT implementable) ======================
class OracleBase(Policy):
    implementable = False
    needs_world = True
    family = "oracle"

    def attach(self, W): self.W = W

    def val(self, v, t):
        W = self.W
        a = t - int(W.arr[v.cid])
        return float(W.edge[v.cid]) * math.exp(-a / W.tau) - float(W.cost_true[v.cid])


class OracleScore(OracleBase):
    name = "ORACLE_SCORE_NOT_IMPLEMENTABLE"

    def decide(self, t, pend, openp, free, cap):
        sc = sorted(((self.val(v, t), v.cid) for v in pend), reverse=True)
        return [c for val, c in sc[:free] if val > 0], []


class OracleDensity(OracleBase):
    name = "ORACLE_DENSITY_NOT_IMPLEMENTABLE"

    def decide(self, t, pend, openp, free, cap):
        sc = sorted(((self.val(v, t) / float(self.W.dur[v.cid]), self.val(v, t), v.cid) for v in pend), reverse=True)
        return [c for d, val, c in sc[:free] if val > 0], []


class LeakyCanary(OracleBase):
    """Deliberately leaky: FIFO but peeks at the realised outcome. Exists ONLY to prove the
    leakage tests can detect leakage."""
    name = "LEAKY_CANARY_NOT_IMPLEMENTABLE"

    def decide(self, t, pend, openp, free, cap):
        W = self.W
        out = []
        for v in sorted(pend, key=lambda v: (-v.age, v.cid)):
            if len(out) >= free: break
            a = t - int(W.arr[v.cid]); i = int(W.inst[v.cid]); d = int(W.dur[v.cid])
            real = W.edge[v.cid] + v.side * (W.CR[min(t + d, len(W.CR) - 1), i] - W.CR[t, i]) - W.cost_true[v.cid]
            if real > 0: out.append(v.cid)
        return out, []


# ============================ registry =========================================
def default_configs():
    """name -> factory(params) ; params are the tunable knobs (defaults = untuned guess)."""
    E = Engine
    reg = {
        "FIFO": lambda p: FIFO(),
        "ROUND_ROBIN": lambda p: RoundRobin(),
        "RANDOM_SEEDED": lambda p: RandomPolicy(),
        "EQUAL_QUOTA": lambda p: EqualQuota(),
        "OLDEST_SLOT": lambda p: OldestSlot(**p),
        "FIFO_NETPOS": lambda p: FifoNetPos(),
        "RANK_SCORE_RAW": lambda p: E("RANK_SCORE_RAW", raw=True),
        "RANK_NET": lambda p: E("RANK_NET"),
        "RANK_NET_UNKCOST_ZERO": lambda p: E("RANK_NET_UNKCOST_ZERO", unk_cost="zero"),
        "RANK_NET_MISSING_REJECT": lambda p: E("RANK_NET_MISSING_REJECT", missing="reject"),
        "UNCERTAINTY_LCB": lambda p: E("UNCERTAINTY_LCB", "uncertainty", calib=dict(k=p["k"], kappa=p["kappa"])),
        "SLOTHOUR_DENSITY": lambda p: E("SLOTHOUR_DENSITY", "turnover", h0=p["h0"]),
        "SLOTHOUR_HAZARD": lambda p: E("SLOTHOUR_HAZARD", "turnover", h0=p["h0"], hazard_tau=p["tau"]),
        "SHADOW_PRICE": lambda p: E("SHADOW_PRICE", "shadow_price", shadow=dict(eta=p["eta"], target=p["target"])),
        "ONLINE_KNAPSACK_PSI": lambda p: E("ONLINE_KNAPSACK_PSI", "knapsack", h0=1.0, thr=("knap", p["L"], p["U"])),
        "FLUID_QUANTILE": lambda p: E("FLUID_QUANTILE", "queueing_fluid", h0=p["h0"], thr=("fluid", p["s"])),
        "TRUNK_RESERVATION": lambda p: E("TRUNK_RESERVATION", "queueing_admission", h0=1.0, reserve=(p["r"], p["q"])),
        "SECRETARY_1_OVER_E": lambda p: Secretary(),
        "CLUSTER_CAP": lambda p: E("CLUSTER_CAP", "diversification", cap_frac=p["f"]),
        "CORR_PENALTY": lambda p: E("CORR_PENALTY", "diversification", corr=("pen", p["g"])),
        "MARGINAL_RISK": lambda p: E("MARGINAL_RISK", "diversification", corr=("marg", p["g"])),
        "CORR_HARD_REJECT": lambda p: E("CORR_HARD_REJECT", "diversification", corr=("hard", p["rho"])),
        "EVICT_SWAP": lambda p: E("EVICT_SWAP", "turnover", h0=2.0, evict=(p["mh"], p["M"])),
        "LINUCB": lambda p: LinBandit("LINUCB", "ucb", p["alpha"]),
        "LIN_TS": lambda p: LinBandit("LIN_TS", "ts", p["alpha"]),
        "SLEEPING_HEDGE": lambda p: SleepingHedge(p["eta"], p["zeta"]),
        "COMPOSED": lambda p: E("COMPOSED", "composed", calib=dict(k=p["k"], kappa=25.0), h0=p["h0"], hazard_tau=p["tau"],
                               corr=("pen", p["g"]) if p["g"] > 0 else None, thr=("fluid", p["s"])),
        "ORACLE_SCORE_NOT_IMPLEMENTABLE": lambda p: OracleScore(),
        "ORACLE_DENSITY_NOT_IMPLEMENTABLE": lambda p: OracleDensity(),
    }
    return reg


GRIDS = {
    "OLDEST_SLOT": [dict(min_hold=m) for m in (3, 6, 12)],
    "UNCERTAINTY_LCB": [dict(k=k, kappa=ka) for k in (0.0, 0.5, 1.0) for ka in (25.0, 100.0)],
    "SLOTHOUR_DENSITY": [dict(h0=h) for h in (0.0, 2.0, 6.0)],
    "SLOTHOUR_HAZARD": [dict(h0=2.0, tau=t) for t in (3.0, 6.0, 12.0)],
    "SHADOW_PRICE": [dict(eta=e, target=t) for e in (0.02, 0.1) for t in (0.8, 0.95)],
    "ONLINE_KNAPSACK_PSI": [dict(L=L, U=U) for L in (0.25, 1.0) for U in (4.0, 10.0, 25.0)],
    "FLUID_QUANTILE": [dict(h0=2.0, s=s) for s in (0.6, 0.8, 1.0, 1.3)],
    "TRUNK_RESERVATION": [dict(r=r, q=q) for r in (1, 2) for q in (0.5, 0.75)],
    "CLUSTER_CAP": [dict(f=f) for f in (0.34, 0.5, 0.75)],
    "CORR_PENALTY": [dict(g=g) for g in (0.05, 0.15, 0.4, 1.0)],
    "MARGINAL_RISK": [dict(g=g) for g in (0.05, 0.15, 0.4, 1.0)],
    "CORR_HARD_REJECT": [dict(rho=r) for r in (0.2, 0.4, 0.6)],
    "EVICT_SWAP": [dict(mh=m, M=M) for m in (0, 6, 12) for M in (0.5, 1.5)],
    "LINUCB": [dict(alpha=a) for a in (0.05, 0.2, 0.6)],
    "LIN_TS": [dict(alpha=a) for a in (0.05, 0.2, 0.6)],
    "SLEEPING_HEDGE": [dict(eta=e, zeta=z) for e in (0.05, 0.3) for z in (3.0, 8.0)],
    "COMPOSED": [dict(k=k, h0=2.0, tau=6.0, g=g, s=s) for k in (0.0, 0.5) for g in (0.0, 0.15) for s in (0.8, 1.2)],
}
