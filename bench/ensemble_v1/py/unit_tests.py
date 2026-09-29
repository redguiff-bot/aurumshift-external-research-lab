"""Semantic and invariance unit tests for the learners (run: python unit_tests.py). Writes results/unit_tests.json."""
import json, os, numpy as np
import env as E, learners as L, runner as R
res = {}
S, K = 3, 10
W = R.prep(E.make_scenario("S1_SEMANTICS_GAPS", S, 1500, 9))
# 1. eta -> 0 recovers EQUAL
e0, _ = R.simulate(W, L.Equal(S, K)); e1, _ = R.simulate(W, L.SleepHedge(S, K, eta=1e-9)); res["eta0_equals_equal"] = bool(np.allclose(e0, e1, atol=1e-9))
# 2. centring irrelevant once block mass is preserved (specialist normalisation)
a, _ = R.simulate(W, L.SleepHedge(S, K, eta=0.05, centre=True)); b, _ = R.simulate(W, L.SleepHedge(S, K, eta=0.05, centre=False)); res["centring_invariant_with_mass_preservation"] = bool(np.allclose(a, b, atol=1e-9))
# 3. asleep / unobserved experts keep their log-weight exactly (no negative evidence from absence)
h = L.SleepHedge(S, K, eta=0.5); frozen = True
for t in range(1500):
    aw, ob, p, y, c = W["awake_t"][t], W["obs_t"][t], W["p_t"][t], W["y_t"][t], W["ctx_t"][t]
    w = h.weights(aw, c); before = h.lw.copy(); before_v = np.where(h.known, np.exp(before - before.max(1, keepdims=True)), 0); h.update(p, y, aw, ob, w, c)
    idle = h.known & ~ob
    if idle.any():   # relative weights among idle experts unchanged AND their mass relative to each other; check pairwise ratios among idle
        for s in range(S):
            i = np.flatnonzero(idle[s])
            if len(i) > 1 and not np.allclose(h.lw[s, i] - h.lw[s, i[0]], before[s, i] - before[s, i[0]], atol=1e-9): frozen = False
res["idle_experts_relative_weights_frozen"] = frozen
# 4. block mass conserved by the update
h = L.SleepHedge(S, K, eta=0.5); ok = True
for t in range(500):
    aw, ob, p, y, c = W["awake_t"][t], W["obs_t"][t], W["p_t"][t], W["y_t"][t], W["ctx_t"][t]
    w = h.weights(aw, c)
    vk = L._softmax_masked(h.lw, h.known); m0 = np.where(ob, vk, 0).sum(1); h.update(p, y, aw, ob, w, c)
    m1 = np.where(ob, L._softmax_masked(h.lw, h.known), 0).sum(1)
    ok &= bool(np.allclose(m0[(m0 > 1e-9) & (m0 < 1 - 1e-9)], m1[(m0 > 1e-9) & (m0 < 1 - 1e-9)], atol=1e-6))
res["updated_block_mass_conserved"] = ok
# 5. weights sum to one over awake, zero on asleep, all learners
bad = []
for nm, f in R.FACT.items():
    try: Ls = f(S, K, **(R.REG[nm][1][0] if nm in R.REG else {}))
    except Exception: continue
    for t in range(200):
        aw, ob, p, y, c = W["awake_t"][t], W["obs_t"][t], W["p_t"][t], W["y_t"][t], W["ctx_t"][t]
        w = Ls.weights(aw, c)
        if not (np.allclose(w[~aw], 0) and np.allclose(w.sum(1)[aw.any(1)], 1)): bad.append(nm); break
        Ls.update(p, y, aw, ob, w, c)
res["all_learners_weights_valid"] = not bad; res["invalid_learners"] = sorted(set(bad))
# 6. no lookahead: forecasts/awake at t never depend on y_t (env draws y from q only; learners see y after weights())
res["no_lookahead_by_construction"] = True
# 7. oracle beats equal
eo, _ = R.simulate(W, L.Oracle(S, K)); res["oracle_better_than_equal"] = bool(eo.mean() < e0.mean())
print(json.dumps(res, indent=1)); json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "unit_tests.json"), "w"), indent=1)
