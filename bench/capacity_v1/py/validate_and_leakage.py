"""Simulator validation + explicit no-lookahead / leakage tests.  Writes results/validation.json"""
import sys, json, math, time, inspect, re
sys.path.insert(0, ".")
import numpy as np
from env import make_world, run, perturb_future, perturb_rejected_latent, BASE, View
from policies import default_configs, GRIDS
import policies as PM
import scenarios as SCN

OUT = {}
reg = default_configs()


# ---------------------------------------------------------------- Erlang-B check
def erlang_b(E, c):
    b = 1.0
    for k in range(1, c + 1):
        b = E * b / (k + E * b)
    return b


rows = []
for cap in (3, 4, 6):
    for load in (0.5, 1.0, 2.0):
        P = dict(BASE, T=20000, ttl=0, load=load, p_cost_unk=0.0, mu_mean=50, q_sd=1, mu_sd=0, score_sd=1)
        W = make_world(P, 7)
        from policies import FIFO
        m = run(W, FIFO(), cap)
        E = W.n / W.T * float(W.dur.mean())     # empirical offered load (Erlang) from generated arrivals/durations
        blk = 1 - m["n_admit"] / m["n_opps"]
        rows.append(dict(cap=cap, load_ref4=load, offered_erlang=E, sim_block=blk, erlang_b=erlang_b(E, cap), abs_err=abs(blk - erlang_b(E, cap))))
OUT["erlang_b_check"] = rows
OUT["erlang_b_max_abs_err"] = max(r["abs_err"] for r in rows)
print("Erlang-B max abs err:", OUT["erlang_b_max_abs_err"])

# ---------------------------------------------------------------- matroid greedy == MILP
from scipy.optimize import milp, LinearConstraint, Bounds, linear_sum_assignment
rng = np.random.default_rng(5)
ok_m = 0; ok_l = 0; K = 200
for _ in range(K):
    n = int(rng.integers(3, 14)); free = int(rng.integers(1, 5)); ncl = 3
    cl = rng.integers(0, ncl, n); v = rng.normal(5, 10, n)
    lim = rng.integers(1, 3, ncl); openc = rng.integers(0, 2, ncl)
    room = np.maximum(lim - openc, 0)
    # greedy (positive values, cardinality<=free, per-cluster room)
    used = np.zeros(ncl, int); sel = 0; g = 0.0
    for i in np.argsort(-v):
        if sel >= free or v[i] <= 0: break
        if used[cl[i]] < room[cl[i]]:
            used[cl[i]] += 1; sel += 1; g += v[i]
    A = [np.ones(n)] + [(cl == c).astype(float) for c in range(ncl)]
    ub = [free] + list(room)
    res = milp(-v, constraints=LinearConstraint(np.array(A), -np.inf, np.array(ub, float)), integrality=np.ones(n), bounds=Bounds(0, 1))
    ok_m += abs(-res.fun - g) < 1e-6
    # assignment with identical slots == top-k
    k = min(free, n)
    cost = -np.tile(v[:, None], (1, k))
    r, c = linear_sum_assignment(cost)
    ok_l += abs(-cost[r, c].sum() - np.sort(v)[::-1][:k].sum()) < 1e-9
OUT["greedy_equals_milp_laminar"] = f"{ok_m}/{K}"
OUT["assignment_identical_slots_equals_topk"] = f"{ok_l}/{K}"
print("greedy==MILP", ok_m, K, " LSA==topk", ok_l, K)

# ---------------------------------------------------------------- leakage tests
LEAK = {}
policy_names = [n for n in reg if "NOT_IMPLEMENTABLE" not in n]
cases = [("S3_chronic", 0), ("S5_correlated", 1), ("S9_missing_quality", 2), ("S7_regime_shift", 0), ("S10_spam", 1)]
t0 = 400
fails = []
tested = 0
for name in policy_names:
    p = GRIDS.get(name, [{}])[0]
    for sc, vi in cases:
        P = SCN.variants(sc, "TUNING")[vi]
        W = make_world(P, 4242)
        base = run(W, reg[name](p), 4, seed=4242, log_decisions=True)
        # T1: counterfactual latent of never-admitted opps scrambled -> identical decisions everywhere
        W1 = perturb_rejected_latent(W, base["_admitted_ids"], 99)
        m1 = run(W1, reg[name](p), 4, seed=4242, log_decisions=True)
        same1 = base["_log"] == m1["_log"]
        # T2: everything knowable only after t0 scrambled -> decisions at t <= t0 identical
        W2 = perturb_future(W, t0, 77)
        m2 = run(W2, reg[name](p), 4, seed=4242, log_decisions=True)
        same2 = [l for l in base["_log"] if l[0] <= t0] == [l for l in m2["_log"] if l[0] <= t0]
        tested += 1
        if not (same1 and same2):
            fails.append((name, sc, same1, same2))
LEAK["policies_tested"] = policy_names
LEAK["cases"] = [c[0] for c in cases]
LEAK["runs"] = tested
LEAK["failures"] = fails
print("leak failures:", fails)

# T3: canary must be DETECTED (test has power)
det = []
for sc, vi in cases:
    P = SCN.variants(sc, "TUNING")[vi]
    W = make_world(P, 4242)
    can = PM.LeakyCanary()
    b = run(W, can, 4, seed=4242, log_decisions=True)
    W2 = perturb_future(W, t0, 77)
    m2 = run(W2, PM.LeakyCanary(), 4, seed=4242, log_decisions=True)
    d2 = [l for l in b["_log"] if l[0] <= t0] != [l for l in m2["_log"] if l[0] <= t0]
    W1 = perturb_rejected_latent(W, b["_admitted_ids"], 99)
    m1 = run(W1, PM.LeakyCanary(), 4, seed=4242, log_decisions=True)
    d1 = b["_log"] != m1["_log"]
    det.append(dict(case=sc, detected_by_future_test=bool(d2), detected_by_counterfactual_test=bool(d1)))
LEAK["canary_detection"] = det
print("canary:", det)

# T4: static structural audit of the implementable policy source
src = inspect.getsource(PM)
impl_src = src.split("# ============================ oracles")[0]
forbidden = [r"\bW\.edge\b", r"\bW\.dur\b", r"\bcost_true\b", r"\.CR\b", r"needs_world\s*=\s*True", r"\battach\(", r"\bworld\b"]
hits = {p: len(re.findall(p, impl_src)) for p in forbidden}
LEAK["static_audit_forbidden_token_hits_in_implementable_policies"] = hits
fields = list(View._fields)
LEAK["view_fields"] = fields
LEAK["view_contains_latent"] = any(f in ("edge", "dur", "cost_true", "realized") for f in fields)
print("static audit", hits, fields)

LEAK["NO_LOOKAHEAD_PROVEN_within_tested_scope"] = (not fails) and all(d["detected_by_future_test"] or d["detected_by_counterfactual_test"] for d in det) and sum(hits.values()) == 0 and not LEAK["view_contains_latent"]
OUT["leakage"] = LEAK
json.dump(OUT, open("../results/validation.json", "w"), indent=1, default=str)
print("NO_LOOKAHEAD_PROVEN:", LEAK["NO_LOOKAHEAD_PROVEN_within_tested_scope"])
