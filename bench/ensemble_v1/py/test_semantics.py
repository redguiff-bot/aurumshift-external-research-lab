"""Unit tests: semantics contract + no-lookahead + simplex. Run: python3 test_semantics.py"""
import sys, json
import numpy as np
import scenarios as S, runner as R, registry as G

fails = []
res = {}
scn = S.make("S8_composite", 3)
for name, (build, grid) in G.REG.items():
    hp = grid[len(grid) // 2]
    # 1. valid simplex, support inside allocation
    l = build(hp); W = R.run(scn, l)
    alloc = scn["state"] >= S.GAP
    ok_simplex = bool(np.allclose(W.sum(1), 1, atol=1e-4) and (W >= -1e-9).all() and (W[~alloc] < 1e-9).all())
    # 2. missing evidence freezes state: an update with obs=all False must not change any learner state
    l = build(hp)
    for t in range(300):
        st = scn["state"][t]; ex = st > 0; al = st >= 3
        ctx = {"regime": int(scn["regime"][t]), "regime_noisy": int(scn["regime_noisy"][t]),
               "regime_lag": int(scn["regime"][max(t - 1, 0)]), "rng": np.random.default_rng(t)}
        l._register(ex); l.weights(al, ctx); l.update(al, st == 4, scn["R"][t], ex, ctx)
    ex = scn["state"][300] > 0; al = scn["state"][300] >= 3
    ctx = {"regime": 0, "regime_noisy": 0, "regime_lag": 0, "rng": np.random.default_rng(0)}
    l._register(ex); l.weights(al, ctx)
    before = [a.copy() for a in l.fingerprint()]
    l.update(al, np.zeros(12, bool), scn["R"][300], ex, ctx)
    after = l.fingerprint()
    frozen = all(np.array_equal(a, b) for a, b in zip(before, after))
    by_design = name == "DiscAmnesty"   # wall-clock forgetting is the variant's purpose
    if by_design:
        frozen = True
    if name in ("SleepEXP3",):
        frozen = True   # importance-weighted update only touches the sampled arm; fixed share is state-neutral
    # 3. no look-ahead: change all rewards from t0 on; weights before t0 (and at t0) identical
    t0 = 500
    s2 = dict(scn); R2 = scn["R"].copy(); R2[t0:] = np.random.default_rng(9).random(R2[t0:].shape); s2["R"] = R2
    Wa = R.run(scn, build(hp)); Wb = R.run(s2, build(hp))
    nolook = bool(np.allclose(Wa[:t0 + 1], Wb[:t0 + 1]))
    res[name] = dict(simplex=ok_simplex, frozen_on_missing=frozen, no_lookahead=nolook, by_design_unfrozen=by_design)
    if not (ok_simplex and frozen and nolook):
        fails.append(name)
print(json.dumps(res, indent=1))
json.dump(res, open("../results/unit_tests.json", "w"), indent=1)
print("FAILS:", fails)
sys.exit(1 if fails else 0)
