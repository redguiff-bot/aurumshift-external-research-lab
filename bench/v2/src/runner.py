"""Single-run harness + CLI worker.

run_one(sc, policy) -> dict
  * cycles 0..T0-1: COMMON uniform logging policy (policy independent; every policy sees the same logged events)
  * cycles T0..R-1: policy selects K distinct eligible cells; outcomes are typed (EVIDENCE / ATTEMPTED_NO_EVIDENCE)
  * feedback is batched: all K picks are made before any outcome is observed
"""
import sys, os, json, time, hashlib, resource, argparse
import numpy as np
from scenario_core import K, R, T0
from ledger import Ledger
import metrics as M


def run_one(sc, pol, check=True):
    L = Ledger(sc)
    log_rng = np.random.default_rng(sc.log_seed)
    n = sc.n
    att = np.zeros((R, n), bool); evd = np.zeros((R, n), bool); val = np.zeros((R, n))
    picks = -np.ones((R, K), int)
    n_evidence_events = n_noev_events = 0
    t_pol = 0.0
    for t in range(R):
        L.begin(t, sc.eligible(t))
        e = L.elig
        if t < T0:
            k = min(K, len(e))
            ch = [int(c) for c in log_rng.choice(e, k, replace=False)]      # draw order preserved
        else:
            t0 = time.perf_counter()
            ch = [int(c) for c in pol.select(t, L)]
            t_pol += time.perf_counter() - t0
            if check:
                assert len(ch) == len(set(ch)) == min(K, len(e)), f"{pol.name}: bad pick count t={t}"
                assert set(ch) <= set(e.tolist()), f"{pol.name}: picked ineligible cell t={t}"
        events = []
        for c in ch:
            kind, v = sc.outcome(t, c)
            events.append((c, kind, v))
            att[t, c] = True
            if kind == "EVIDENCE":
                evd[t, c] = True; val[t, c] = v; n_evidence_events += 1
            else:
                n_noev_events += 1
        picks[t, :len(ch)] = ch
        t0 = time.perf_counter()
        pol.observe(t, events, L, logged=(t < T0))
        t_pol += time.perf_counter() - t0
        for c, kind, v in events:
            L.record(t, c, kind, v)
    m = M.compute(sc, att, evd, val, picks)
    m.update(policy=pol.name, scenario=sc.name, split=sc.split, seed=sc.seed,
             seqhash=hashlib.sha256(picks[T0:].tobytes()).hexdigest()[:16],
             policy_seconds=t_pol, evidence_events=n_evidence_events, no_evidence_events=n_noev_events)
    if hasattr(pol, "stats"):
        m["policy_stats"] = json.loads(json.dumps(pol.stats, default=float))
    return m


def make_scenario(split, name, seed):
    if split in ("train", "validation"):
        from scenarios_dev import make_dev_scenario
        return make_dev_scenario(split, name, seed)
    if split == "adversarial":
        from scenarios_adv import make_adv_scenario
        return make_adv_scenario(name, seed)
    from scenarios_heldout import make_heldout_scenario
    return make_heldout_scenario(name, seed, split)


def make_policy(spec, seed):
    """spec: dict(kind=..., **params)"""
    from policies import (AurumShiftLifecycleWeightedReference as A, DUCBGuard, RiverPolicy, VWPolicy, RoundRobin,
                          CLS, CLS_ALT)
    p = dict(spec); kind = p.pop("kind")
    if kind == "A": return A(seed)
    if kind == "A_altcls": return A(seed, low_to_degrading=False, tag="A_altcls")
    if kind == "A_floor": return A(seed, floor_ratio=p["floor"], tag=f"A_floor{p['floor']}")
    if kind == "A_w":     # sensitivity only: alternative weights (fixed reference A is unchanged)
        from policies import EXPL, PROM, PROV, DEGR, RETI
        w = p["weights"]
        return A(seed, weights={EXPL: w[0], PROM: w[1], PROV: w[2], DEGR: w[3], RETI: 0.0}, tag=p["tag"])
    if kind == "R": return RoundRobin(seed)
    if kind == "B": return DUCBGuard(seed, **p)
    if kind == "C": return RiverPolicy(seed, **p)
    if kind == "C2":
        g = p.pop("guard"); return RiverPolicy(seed, guard=tuple(g), **p)
    if kind == "D": return VWPolicy(seed, **p)
    raise ValueError(kind)


def worker(jobs, out_path):
    """jobs: list of dict(split, scenario, seed, policy=<spec>, label)"""
    res = []
    t0 = time.time()
    for j in jobs:
        sc = make_scenario(j["split"], j["scenario"], j["seed"])
        pol = make_policy(j["policy"], j["seed"])
        try:
            r = run_one(sc, pol)
            r["label"] = j["label"]; r["policy_spec"] = j["policy"]
        except Exception as ex:                # never hide failures
            import traceback
            r = dict(label=j["label"], scenario=j["scenario"], seed=j["seed"], split=j["split"], error=traceback.format_exc(),
                     policy_spec=j["policy"])
        res.append(r)
    with open(out_path, "w") as f:
        json.dump(dict(wall_seconds=time.time() - t0, maxrss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                       runs=res), f, default=float)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs_json"); ap.add_argument("out_json")
    a = ap.parse_args()
    worker(json.load(open(a.jobs_json)), a.out_json)
