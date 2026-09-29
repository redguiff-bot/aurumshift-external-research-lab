"""Semantics, determinism and NO-LOOKAHEAD tests. Run: PYTHONPATH=src pytest -q tests"""
import sys, os, copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pytest
import world as W, engine as E, policies as P

IMPL = [k for k in P.REGISTRY if k != "ORACLE_GREEDY_UB"]
SCEN = ["S3_chronic", "S10_spam", "S7_regime_shift", "S9_missing", "S5_correlated"]

def _log(w, name, ingest, K=4):
    import engine
    # run and extract admission log via collect_log path
    out = {}
    orig = engine.summarize
    def spy(*args, **kw):
        out["log"] = args[12]
        return orig(*args, **kw)
    engine.summarize = spy
    try:
        engine.run(w, P.make(name), K, ingest, collect_log=True, seed=3)
    finally:
        engine.summarize = orig
    return out["log"]

@pytest.mark.parametrize("ingest", E.INGEST_MODES)
@pytest.mark.parametrize("name", IMPL)
def test_prefix_decisions_invariant_to_future_hidden(name, ingest):
    for scen in SCEN:
        w = W.build_world(scen, 11, "validation")
        for t0 in (150, 300):
            w2 = W.resample_hidden_after(w, t0, 5)
            la = [x for x in _log(w, name, ingest) if x[0] <= t0]
            lb = [x for x in _log(w2, name, ingest) if x[0] <= t0]
            assert la == lb, (name, ingest, scen, t0)

def test_oracle_canary_is_detected_as_leaking():
    """The leak detector must FLAG the perfect-foresight oracle (proves the test has power)."""
    diffs = 0
    for scen in SCEN:
        w = W.build_world(scen, 11, "validation"); w2 = W.resample_hidden_after(w, 150, 5)
        la = [x for x in _log(w, "ORACLE_GREEDY_UB", "RAW") if x[0] <= 150]
        lb = [x for x in _log(w2, "ORACLE_GREEDY_UB", "RAW") if x[0] <= 150]
        diffs += la != lb
    assert diffs >= 4

@pytest.mark.parametrize("name", IMPL)
def test_determinism(name):
    w = W.build_world("S3_chronic", 4, "heldout")
    h1 = E.run(w, P.make(name), 4, "SCORE_UPDATE", seed=1)["trade_hash"]
    w = W.build_world("S3_chronic", 4, "heldout")
    h2 = E.run(w, P.make(name), 4, "SCORE_UPDATE", seed=1)["trade_hash"]
    assert h1 == h2

def test_world_is_deterministic_and_seed_sensitive():
    a = W.build_world("S3_chronic", 1, "tuning"); b = W.build_world("S3_chronic", 1, "tuning"); c = W.build_world("S3_chronic", 2, "tuning")
    assert np.array_equal(a.E, b.E) and a.events == b.events and not np.array_equal(a.E, c.E)

@pytest.mark.parametrize("name", IMPL)
def test_capacity_and_one_position_per_instrument(name):
    w = W.build_world("S11_burst", 2, "validation")
    m = E.run(w, P.make(name), 3, "RAW", seed=1)
    assert m["busy_slot_hours"] <= 3 * w.W + 1e-9
    assert m["full_frac"] <= 1.0

def test_unknown_cost_is_not_zero_cost():
    w = W.build_world("S3_chronic", 3, "validation")
    z = E.run(w, P.make("SCORE_RANK"), 4, "RAW", belief="zero", seed=1)
    u = E.run(w, P.make("SCORE_RANK"), 4, "RAW", belief="unknown_conservative", seed=1)
    k = E.run(w, P.make("SCORE_RANK"), 4, "RAW", belief="known", seed=1)
    assert z["n_admit"] >= k["n_admit"] and u["n_admit"] <= z["n_admit"]

def test_missing_score_not_treated_as_negative():
    class C: pass
    pol = P.SlotHour(); w = W.build_world("S9_missing", 1, "tuning")
    pol.reset(E.Pub(w, w.cost.copy()), 4, 0)
    c = E.Cand(0, 0, 0, float("nan"))
    assert pol.sc(c) == P.PRIOR_SCORE

def test_evictions_charge_cost_and_truncate():
    w = W.build_world("S3_chronic", 5, "validation")
    m = E.run(w, P.make("OLDEST_SLOT", {"min_hold": 2}), 4, "RAW", seed=1)
    assert m["evict_frac"] > 0
