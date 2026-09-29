"""Execute the external OSS components that were considered, on the same synthetic environment.
Writes results/oss_probe.json.  Every entry records what was actually executed (OBSERVED) vs not."""
import sys, json, time, math, warnings, importlib.metadata as md
sys.path.insert(0, ".")
warnings.filterwarnings("ignore")
import numpy as np
from env import make_world, run, BASE
from policies import default_configs, GRIDS, LinBandit, FIFO
import scenarios as SCN

OUT = {"versions": {p: md.version(p) for p in ["scipy", "ortools", "mabwiser", "simpy", "river", "cvxpy", "PyPortfolioOpt", "pulp", "scikit-learn"]}}
reg = default_configs()

# ---- 1. SimPy: independent M/G/c/c cross-check of the FIFO/ttl=0 simulator ----------------------------
import simpy
def simpy_block(lam, dur_sampler, cap, T, seed):
    rng = np.random.default_rng(seed); env = simpy.Environment(); res = simpy.Resource(env, capacity=cap)
    st = dict(n=0, blk=0)
    def job(env):
        yield env.timeout(dur_sampler(rng)); res.release(req)
    def gen(env):
        while True:
            yield env.timeout(rng.exponential(1 / lam)); st["n"] += 1
            if res.count >= cap: st["blk"] += 1; continue
            def run_job(env):
                with res.request() as rq:
                    yield rq; yield env.timeout(dur_sampler(rng))
            env.process(run_job(env))
    env.process(gen(env)); env.run(until=T)
    return st["blk"] / st["n"]
def erlang_b(E, c):
    b = 1.0
    for k in range(1, c + 1): b = E * b / (k + E * b)
    return b
rows = []
for cap, load in [(4, 1.0), (4, 2.0), (6, 2.0)]:
    P = dict(BASE, T=20000, ttl=0, load=load, p_cost_unk=0.0, mu_mean=50, q_sd=1, mu_sd=0, score_sd=1)
    W = make_world(P, 7); m = run(W, FIFO(), cap)
    lam = W.n / W.T; md_ = float(W.dur.mean())
    sp = simpy_block(lam, lambda r: max(1.0, r.lognormal(math.log(md_) - 0.15, 0.55)), cap, 20000, 3)
    rows.append(dict(cap=cap, load=load, offered_erlang=lam * md_, own_sim=1 - m["n_admit"] / m["n_opps"], simpy=sp, erlang_b=erlang_b(lam * md_, cap)))
OUT["simpy_erlang_crosscheck"] = rows

# ---- 2. OR-Tools CP-SAT: batch selection with cluster caps == greedy -------------------------------
from ortools.sat.python import cp_model
rng = np.random.default_rng(11); ok = 0; K = 100; tsum = 0
for _ in range(K):
    n = int(rng.integers(4, 14)); free = int(rng.integers(1, 5)); ncl = 3
    cl = rng.integers(0, ncl, n); v = np.round(rng.normal(5, 10, n) * 100).astype(int); lim = rng.integers(1, 3, ncl)
    mdl = cp_model.CpModel(); x = [mdl.NewBoolVar(f"x{i}") for i in range(n)]
    mdl.Add(sum(x) <= free)
    for c in range(ncl): mdl.Add(sum(x[i] for i in range(n) if cl[i] == c) <= int(lim[c]))
    mdl.Maximize(sum(int(v[i]) * x[i] for i in range(n)))
    s = cp_model.CpSolver(); t = time.time(); s.Solve(mdl); tsum += time.time() - t
    used = np.zeros(ncl, int); sel = 0; g = 0
    for i in np.argsort(-v):
        if sel >= free or v[i] <= 0: break
        if used[cl[i]] < lim[cl[i]]: used[cl[i]] += 1; sel += 1; g += v[i]
    ok += abs(s.ObjectiveValue() - g) < 1e-6
OUT["ortools_cpsat_equals_greedy"] = dict(agree=f"{ok}/{K}", mean_solve_ms=1000 * tsum / K)

# ---- 3. MABWiser LinUCB (arm = instrument, context = candidate features) as an admission policy ------
from mabwiser.mab import MAB, LearningPolicy
class MabwiserLinUCB(LinBandit):
    name = "MABWISER_LINUCB"
    def reset(self, cap, seed, N, cl):
        super().reset(cap, seed, N, cl)
        self.mab = MAB(arms=list(range(N)), learning_policy=LearningPolicy.LinUCB(alpha=self.alpha, l2_lambda=10.0), seed=seed)
        self.buf = []; self.fitted = False
    def on_close(self, rec):
        self.upd_close(rec)
        x = self.entry.pop(rec["cid"], None)
        if x is None or rec["evicted"]: return
        y = float(np.clip(rec["realized"] / max(rec["held"], 1) / 5.0, -3, 3))
        self.buf.append((rec["inst"], y, x))
        if len(self.buf) >= 10:
            d, r, c = zip(*self.buf)
            if not self.fitted: self.mab.fit(list(d), list(r), np.array(c)); self.fitted = True
            else: self.mab.partial_fit(list(d), list(r), np.array(c))
            self.buf = []
    def decide(self, t, pend, openp, free, cap):
        self.observe(pend)
        if free <= 0 or not pend: return [], []
        sc = []
        for v in pend:
            x = self.feat(v)
            val = self.mab.predict_expectations(np.array([x]))[v.inst] if self.fitted else 1.0
            sc.append((float(val), -v.cid, v, x))
        sc.sort(key=lambda z: (-z[0], -z[1])); out = []
        for val, _, v, x in sc[:free]:
            if val > 0: out.append(v.cid); self.entry[v.cid] = x
        return out, []
res = []
t0 = time.time()
for sc in ("S3_chronic", "S9_missing_quality", "S8_noisy_ranking"):
    P = SCN.variants(sc, "VALIDATION")[0]
    for seed in (8001, 8002, 8003):
        W = make_world(P, seed)
        a = run(W, LinBandit("LINUCB", "ucb", 0.2), 4, seed=seed)["lat_per_slot_hour"]
        b = run(W, MabwiserLinUCB("MABWISER_LINUCB", "ucb", 0.2), 4, seed=seed)["lat_per_slot_hour"]
        f = run(W, FIFO(), 4, seed=seed)["lat_per_slot_hour"]
        res.append(dict(scenario=sc, seed=seed, fifo=f, own_linucb=a, mabwiser_linucb=b))
OUT["mabwiser_vs_own_linucb"] = dict(rows=res, seconds=time.time() - t0)

# ---- 4. PyPortfolioOpt / sklearn Ledoit-Wolf: covariance estimation quality (diversification input) ----
import pandas as pd
from pypfopt import risk_models, HRPOpt, EfficientFrontier
from sklearn.covariance import LedoitWolf
P = SCN.variants("S5_correlated", "VALIDATION")[0]
W = make_world(P, 8100)
Rr = W.R[:600]
true_corr = np.corrcoef(W.R[:, :].T)   # long-sample proxy for the truth
from policies import Stats
def ewma_corr(R):
    st = Stats(); st.init_stats(R.shape[1])
    for i, r in enumerate(R): st.on_returns(i, r)
    return st.corr_hat()[1]
errs = {}
for n in (100, 200, 400):
    R = Rr[:n]
    errs[n] = dict(sample=float(np.linalg.norm(np.corrcoef(R.T) - true_corr)),
                   ewma_shrunk_own=float(np.linalg.norm(ewma_corr(R) - true_corr)),
                   ledoit_wolf_sklearn=float(np.linalg.norm(LedoitWolf().fit(R).covariance_ / np.sqrt(np.outer(np.diag(LedoitWolf().fit(R).covariance_), np.diag(LedoitWolf().fit(R).covariance_))) - true_corr)),
                   pypfopt_ledoit_wolf=float(np.linalg.norm(risk_models.CovarianceShrinkage(pd.DataFrame(R), returns_data=True).ledoit_wolf() .values / np.sqrt(np.outer(np.diag(risk_models.CovarianceShrinkage(pd.DataFrame(R), returns_data=True).ledoit_wolf().values), np.diag(risk_models.CovarianceShrinkage(pd.DataFrame(R), returns_data=True).ledoit_wolf().values))) - true_corr)))
OUT["corr_estimation_frobenius_error_vs_long_sample"] = errs
hrp = HRPOpt(pd.DataFrame(Rr) / 100.0); w = hrp.optimize()
OUT["pypfopt_hrp_ran"] = dict(n_weights=len(w), note="HRP returns portfolio weights over a fixed asset set; it does not decide admission of time-stamped opportunities into scarce slots")

# ---- 5. river bandit module presence / smoke ------------------------------------------------------
import river
from river import bandit
try:
    pol = bandit.UCB(delta=0.5, seed=1)
    arms = list(range(12)); r = np.random.default_rng(1)
    for _ in range(200):
        a = pol.pull(arms); pol.update(a, float(r.normal(a * 0.1, 1)))
    OUT["river_bandit_smoke"] = dict(ok=True, classes=[c for c in dir(bandit) if c[0].isupper()][:25], note="context-free / arm-level; no per-candidate contextual admission API used")
except Exception as e:
    OUT["river_bandit_smoke"] = dict(ok=False, err=str(e))

# ---- 6. cvxpy: continuous mean-variance relaxation over instrument weights -------------------------
import cvxpy as cp
S = np.cov(Rr.T) ; mu = np.full(12, 1.0); w = cp.Variable(12, nonneg=True)
prob = cp.Problem(cp.Maximize(mu @ w - 0.5 * cp.quad_form(w, cp.psd_wrap(S))), [cp.sum(w) <= 4])
prob.solve()
OUT["cvxpy_qp_ran"] = dict(status=prob.status, note="QP is a sizing tool; cardinality-constrained selection needs MIQP; not used in the sim")
json.dump(OUT, open("../results/oss_probe.json", "w"), indent=1, default=str)
print(json.dumps(OUT, indent=1, default=str)[:3500])
