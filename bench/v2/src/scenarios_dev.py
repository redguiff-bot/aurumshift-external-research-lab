"""TRAIN and VALIDATION scenario generators (used for tuning / selection ONLY).

Composite scenarios with parameter values that differ from the held-out generators
(scenarios_heldout.py).  This module never imports scenarios_heldout.
"""
import numpy as np
from scenario_core import *  # noqa

DEV_SPECS = {
    "train": ["T1_mixed_abrupt", "T2_mixed_drift_gap", "T3_churn_lowinfo", "T4_dormancy_rare"],
    "validation": ["V1_coldstart_outage", "V2_abrupt_then_drift", "V3_silence_rare_lowinfo"],
}


def _t1(b, T):
    est = b.add(80, 0)
    new = b.add(40, b.tau(0), mode="new")
    # group-level abrupt change at tau=120
    order = np.argsort(b.gm)
    down_g, up_g = order[-2:], order[:2]
    grp = np.asarray(b.group)
    down = est[np.isin(grp[est], down_g)]
    up = np.concatenate([est[np.isin(grp[est], up_g)], new[:8]])
    b.step(down, b.tau(120), np.maximum(0.03, np.asarray(b.p0)[down] - 0.4))
    b.step(up, b.tau(120), b.rng.uniform(0.55, 0.8, len(up)))
    b.meta.update(change_t=b.tau(120), target=up.tolist(), degraded=down.tolist(), new_ids=new.tolist())


def _t2(b, T):
    est = b.add(90, 0)
    p0 = np.asarray(b.p0)
    rising = est[np.argsort(p0[est])[:15]]
    falling = est[np.argsort(-p0[est])[:15]]
    b.ramp(rising, b.tau(50), b.tau(200), b.rng.uniform(0.55, 0.8, 15))
    b.ramp(falling, b.tau(50), b.tau(200), 0.06)
    rest = np.setdiff1d(est, np.concatenate([rising, falling]))
    sil = b.rng.choice(rest, 25, replace=False)
    for c in sil:
        s = b.tau(int(b.rng.integers(20, 200)))
        b.silence([c], s, s + 50)
    b.meta.update(change_t=b.tau(50), target=rising.tolist(), degraded=falling.tolist(), new_ids=[])


def _t3(b, T):
    est = b.add(30, 0)
    low = b.add(20, 0, mode="low")
    ids = list(est) + list(low)
    for w in range(0, 275, 25):
        new = b.add(8, b.tau(w), mode="new")
        ids += list(new)
        alive = [i for i in ids if b.death[i] > b.tau(w) and b.birth[i] <= b.tau(w) - 30]
        if len(alive) > 8:
            b.retire(b.rng.choice(alive, 6, replace=False), b.tau(w))
    b.meta.update(change_t=None, target=[], degraded=[], new_ids=[i for i in range(30 + 20, b.n)])


def _t4(b, T):
    est = b.add(100, 0)
    rare = b.add(5, 0, p=0.05, mag=MAG_RARE, rare=True)
    pool = np.setdiff1d(est, [])
    dorm = b.rng.choice(pool, 15, replace=False)
    b.silence(dorm, b.tau(30), b.tau(150))
    b.step(dorm, b.tau(150), np.clip(np.asarray(b.p0)[dorm] + 0.3, 0.05, 0.85))
    b.meta.update(change_t=b.tau(150), target=dorm.tolist(), degraded=[], new_ids=[])


def _v1(b, T):
    est = b.add(40, 0)
    new = b.add(70, b.tau(0), mode="new")
    prov = b.rng.choice(b.G, 2, replace=False)
    grp = np.asarray(b.group)
    out = np.where(np.isin(grp, prov))[0]
    b.silence(out, b.tau(80), b.tau(180))
    b.meta.update(change_t=None, target=[], degraded=[], new_ids=new.tolist())


def _v2(b, T):
    est = b.add(110, 0)
    p0 = np.asarray(b.p0)
    order = np.argsort(b.gm)
    down_g, up_g = order[-1:], order[:1]
    grp = np.asarray(b.group)
    down, up = est[np.isin(grp[est], down_g)], est[np.isin(grp[est], up_g)]
    b.step(down, b.tau(90), 0.06)
    b.step(up, b.tau(90), b.rng.uniform(0.6, 0.8, len(up)))
    rest = np.setdiff1d(est, np.concatenate([down, up]))
    ris = rest[np.argsort(p0[rest])[:10]]
    b.ramp(ris, b.tau(160), b.tau(300), 0.7)
    b.meta.update(change_t=b.tau(90), target=up.tolist(), degraded=down.tolist(), new_ids=[])


def _v3(b, T):
    est = b.add(50, 0)
    low = b.add(40, 0, mode="low")
    rare = b.add(6, 0, p=0.05, mag=MAG_RARE, rare=True)
    ids = np.concatenate([est, low])
    for c in b.rng.choice(ids, 30, replace=False):
        s = b.tau(int(b.rng.integers(20, 240)))
        b.silence([c], s, s + 60)
    b.meta.update(change_t=None, target=[], degraded=[], new_ids=[])


_BUILD = {"T1_mixed_abrupt": _t1, "T2_mixed_drift_gap": _t2, "T3_churn_lowinfo": _t3, "T4_dormancy_rare": _t4,
          "V1_coldstart_outage": _v1, "V2_abrupt_then_drift": _v2, "V3_silence_rare_lowinfo": _v3}


def make_dev_scenario(split, name, seed):
    assert split in DEV_SPECS, f"dev generator refuses split={split!r}"
    idx = DEV_SPECS[split].index(name)
    g, o, log_seed = streams(split, idx, seed)
    b = Builder(g)
    _BUILD[name](b, None)
    return b.finalize(name, split, seed, o, log_seed)
