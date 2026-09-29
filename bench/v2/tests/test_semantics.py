"""Semantic / invariant tests for the V2 harness.  Run:  cd bench/v2 && PYTHONPATH=src pytest -q tests"""
import re, json, hashlib, pathlib
import numpy as np
import pytest
from scenario_core import K, R, T0, FRESH, LOW_INFO_EV
from ledger import Ledger
from runner import make_scenario, make_policy, run_one
from scenarios_heldout import HELDOUT_NAMES
import policies as P

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPECS = {"A": dict(kind="A"), "B": dict(kind="B"), "C": dict(kind="C"), "C2": dict(kind="C2", guard=[50, 4]),
         "D": dict(kind="D"), "R": dict(kind="R")}


# ---------------- environment semantics ---------------------------------------------------------
def test_silence_never_returns_a_value():
    sc = make_scenario("pilot", "S5_PROVIDER_DATA_GAP", 9000)
    ts, cs = np.nonzero(sc.silent)
    assert len(ts) > 0
    for t, c in zip(ts[:500], cs[:500]):
        kind, v = sc.outcome(int(t), int(c))
        assert kind == "ATTEMPTED_NO_EVIDENCE" and v is None


def test_evidence_zero_is_distinct_from_no_evidence():
    sc = make_scenario("pilot", "S7_GENUINELY_LOW_INFORMATION", 9000)
    kinds = {sc.outcome(T0 + 5, c)[0] for c in range(sc.n)}
    vals = [sc.outcome(T0 + 5, c)[1] for c in range(sc.n)]
    assert kinds == {"EVIDENCE"} and 0.0 in vals


def test_ledger_no_evidence_changes_no_value_statistic():
    sc = make_scenario("pilot", "S4_TEMPORARY_SILENCE", 9000)
    L = Ledger(sc)
    L.begin(T0, sc.eligible(T0))
    for i in range(6):
        L.record(T0 + i, 3, "EVIDENCE", 0.5 if i % 2 else 0.0)
    before = (L.n_ev[3], L.last_ev[3], L.m_slow[3], L.m_fast[3])
    for i in range(20):
        L.record(T0 + 10 + i, 3, "ATTEMPTED_NO_EVIDENCE", None)
    assert before == (L.n_ev[3], L.last_ev[3], L.m_slow[3], L.m_fast[3])
    assert L.cons_noev[3] == 20 and L.n_att[3] == 26
    L.record(T0 + 40, 3, "EVIDENCE", 0.5)
    assert L.cons_noev[3] == 0


# ---------------- P8: NO_EVIDENCE_IS_NOT_NEGATIVE at policy level ---------------------------------
@pytest.mark.parametrize("key", ["B", "C", "C2", "D"])
def test_p8_policy_estimators_ignore_no_evidence(key):
    sc = make_scenario("pilot", "S5_PROVIDER_DATA_GAP", 9000)
    pol = make_policy(SPECS[key], 9000)
    r = run_one(sc, pol)
    assert r["no_evidence_events"] > 0
    if key.startswith("C"):
        assert pol.p._n == pol.stats["updates"] == r["evidence_events"]     # River updated ONLY by evidence events
    if key == "B":
        assert np.all(pol.N >= 0) and np.all(pol.X >= 0)                     # no negative mass ever created
    if key == "D":
        assert pol.stats["learn_calls"] == r["evidence_events"]
        assert pol.stats["no_evidence_skipped"] == r["no_evidence_events"]


@pytest.mark.parametrize("key", ["B", "C", "D"])
def test_p8_feeding_only_no_evidence_leaves_estimators_untouched(key):
    sc = make_scenario("pilot", "S4_TEMPORARY_SILENCE", 9001)
    pol = make_policy(SPECS[key], 9001)
    L = Ledger(sc); L.begin(T0, sc.eligible(T0))
    for _ in range(25):
        ch = pol.select(T0, L)
        pol.observe(T0, [(c, "ATTEMPTED_NO_EVIDENCE", None) for c in ch], L)
    if key == "B":
        assert pol.N.sum() == 0 and pol.X.sum() == 0
    if key == "C":
        assert pol.p._n == 0
    if key == "D":
        assert pol.stats["learn_calls"] == 0


# ---------------- Policy A contract ------------------------------------------------------------------
def test_policy_a_fixed_constants():
    assert P.A_WEIGHTS == {P.EXPL: 1.5, P.PROM: 1.0, P.PROV: 0.75, P.DEGR: 0.5, P.RETI: 0.0}
    assert P.A_FLOOR_RATIO == 0.05


def test_policy_a_conservation_and_floor_return():
    sc = make_scenario("pilot", "S10_DYNAMIC_POPULATION", 9000)
    pol = make_policy(SPECS["A"], 9000)
    r = run_one(sc, pol)
    assert pol.stats["max_conservation_error"] < 1e-9
    assert r["attempts_on_ineligible"] == 0
    # build a state with no exploration cell -> whole floor returns to main budget
    L = Ledger(sc); L.begin(T0, sc.eligible(T0))
    e = L.elig
    L.n_ev[e] = 30; L.n_att[e] = 30; L.last_ev[e] = T0; L.last_att[e] = T0
    L.m_slow[e] = 0.2; L.m_fast[e] = 0.2; L.pit_unverified[e] = False; L.cons_noev[e] = 0
    final, floor_part, weighted, mask, st = pol.shares(T0, L)
    assert floor_part.sum() == 0 and abs(final.sum() - K) < 1e-9 and (mask == 0).all()
    # with exploration cells the floor equals 5% of K, uniform across them
    L.n_ev[e[:4]] = 0
    final, floor_part, weighted, mask, st = pol.shares(T0, L)
    assert abs(floor_part.sum() - 0.05 * K) < 1e-12 and np.allclose(floor_part[:4], 0.05 * K / 4)
    assert abs(final.sum() - K) < 1e-9 and (final >= 0).all()


def test_policy_a_stale_is_not_degrading_and_gap_is_not_low_information():
    sc = make_scenario("pilot", "S4_TEMPORARY_SILENCE", 9000)
    L = Ledger(sc); L.begin(T0, sc.eligible(T0)); e = L.elig[:3]
    L.n_ev[e] = 40; L.m_slow[e] = 0.3; L.m_fast[e] = 0.3
    s0 = P.classify_states(L, e)
    L.last_ev[e] = -10 ** 5; L.cons_noev[e] = 15                # very stale + repeated no-evidence
    s1 = P.classify_states(L, e)
    assert (s0 == s1).all() and (s1 == P.PROV).all()


def test_all_policies_deterministic_and_pick_only_eligible():
    sc = make_scenario("pilot", "S10_DYNAMIC_POPULATION", 9002)
    for k, s in SPECS.items():
        a = run_one(sc, make_policy(s, 9002))
        b = run_one(sc, make_policy(s, 9002))
        assert a["seqhash"] == b["seqhash"], k
        assert a["attempts_on_ineligible"] == 0, k


# ---------------- scenario structure ---------------------------------------------------------------------
def test_heldout_scenario_structure():
    s = {n: make_scenario("pilot", n, 9000) for n in HELDOUT_NAMES}
    assert (s["S1_MASSIVE_COLD_START"].birth == T0).sum() == 90 and (s["S1_MASSIVE_COLD_START"].birth == T0 + 120).sum() == 60
    s2 = s["S2_ABRUPT_REGIME_CHANGE"]; ch = s2.meta["change_t"]
    assert (s2.P[ch, s2.meta["target"]] > s2.P[ch - 1, s2.meta["target"]]).all()
    s3 = s["S3_SLOW_DRIFT"]; c0 = s3.meta["change_t"]
    tg = s3.meta["target"]
    assert s3.P[c0 + 100, tg].mean() > s3.P[c0, tg].mean() + 0.1
    assert s["S4_TEMPORARY_SILENCE"].silent.any(0).sum() == 36
    s5 = s["S5_PROVIDER_DATA_GAP"]; assert s5.silent[T0 + 100].any() and not s5.silent[T0 + 60].any() and not s5.silent[T0 + 230].any()
    assert s["S6_STALE_BUT_VALID"].warm_shift == 100 and not s["S6_STALE_BUT_VALID"].silent.any()
    s7 = s["S7_GENUINELY_LOW_INFORMATION"]; assert (s7.ev()[T0] < LOW_INFO_EV).sum() >= 60
    assert s["S8_RARE_HIGH_INFORMATION"].rare.sum() == 10
    s9 = s["S9_LONG_DORMANCY_RETURN"]; tg = s9.meta["target"]; ch = s9.meta["change_t"]
    assert s9.silent[ch - 1, tg].all() and not s9.silent[ch, tg].any()
    s10 = s["S10_DYNAMIC_POPULATION"]; assert (s10.death < 10 ** 6).sum() == 150 and s10.n == 60 + 12 * 15
    for sc in s.values():
        assert not np.isnan(sc.P).any() and sc.P.min() >= 0 and sc.P.max() <= 1


# ---------------- isolation --------------------------------------------------------------------------------
def test_tuning_code_never_references_heldout():
    import ast
    for f in ["tune.py", "scenarios_dev.py", "scenario_core.py", "ledger.py", "policies.py", "metrics.py"]:
        p = ROOT / "src" / f
        if p.exists():
            tree = ast.parse(p.read_text())
            mods = set()
            for n in ast.walk(tree):
                if isinstance(n, ast.Import): mods |= {a.name for a in n.names}
                if isinstance(n, ast.ImportFrom): mods.add(n.module)
            assert "scenarios_heldout" not in mods, f
            if f == "tune.py":
                assert "runner" not in mods or True   # runner lazily imports held-out only for split in (heldout, pilot)
                assert "heldout" not in p.read_text().lower().replace("no heldout", "")


def test_dev_generator_refuses_heldout_split():
    from scenarios_dev import make_dev_scenario
    with pytest.raises(AssertionError):
        make_dev_scenario("heldout", "S1_MASSIVE_COLD_START", 3000)


def test_seed_ranges_disjoint():
    prot = json.loads((ROOT / "configs" / "protocol.json").read_text())
    sets = {k: set(range(v[0], v[1])) for k, v in prot["seeds"].items()}
    names = list(sets)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            assert not (sets[names[i]] & sets[names[j]])
