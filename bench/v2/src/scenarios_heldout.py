"""HELD-OUT scenario generators S1..S10 (and pilot seeds for harness validation).

FROZEN before any policy other than the fixed reference (A) and round-robin was executed on them.
Its sha256 is recorded in configs/freeze_manifest.json.  Tuning code (tune.py) must never import it.
"""
import numpy as np
from scenario_core import *  # noqa

HELDOUT_NAMES = ["S1_MASSIVE_COLD_START", "S2_ABRUPT_REGIME_CHANGE", "S3_SLOW_DRIFT", "S4_TEMPORARY_SILENCE",
                 "S5_PROVIDER_DATA_GAP", "S6_STALE_BUT_VALID", "S7_GENUINELY_LOW_INFORMATION",
                 "S8_RARE_HIGH_INFORMATION", "S9_LONG_DORMANCY_RETURN", "S10_DYNAMIC_POPULATION"]


def _meta(b, change_t=None, target=(), degraded=(), new_ids=()):
    b.meta.update(change_t=change_t, target=[int(i) for i in target], degraded=[int(i) for i in degraded],
                  new_ids=[int(i) for i in new_ids])


def s1(b):
    est = b.add(30, 0)
    w1 = b.add(90, b.tau(0), mode="new")
    w2 = b.add(60, b.tau(120), mode="new")
    _meta(b, new_ids=np.concatenate([w1, w2]))


def s2(b):
    est = b.add(120, 0)
    order = np.argsort(b.gm)
    down_g, up_g = order[-2:], order[:2]
    grp = np.asarray(b.group)
    down, up = est[np.isin(grp[est], down_g)], est[np.isin(grp[est], up_g)]
    b.step(down, b.tau(100), np.maximum(0.03, np.asarray(b.p0)[down] - 0.45))
    b.step(up, b.tau(100), b.rng.uniform(0.6, 0.8, len(up)))
    _meta(b, change_t=b.tau(100), target=up, degraded=down)


def s3(b):
    est = b.add(120, 0)
    p0 = np.asarray(b.p0)
    rising = est[np.argsort(p0[est])[:20]]
    falling = est[np.argsort(-p0[est])[:20]]
    b.ramp(rising, b.tau(40), b.tau(240), b.rng.uniform(0.6, 0.8, 20))
    b.ramp(falling, b.tau(40), b.tau(240), b.rng.uniform(0.05, 0.10, 20))
    _meta(b, change_t=b.tau(40), target=rising, degraded=falling)


def s4(b):
    est = b.add(120, 0)
    for c in b.rng.choice(est, 36, replace=False):
        s = b.tau(int(b.rng.integers(30, 231)))
        b.silence([c], s, s + 40)
    _meta(b)


def s5(b):
    est = b.add(120, 0)
    prov = b.rng.choice(b.G, 3, replace=False)
    out = est[np.isin(np.asarray(b.group)[est], prov)]
    b.silence(out, b.tau(80), b.tau(220))
    _meta(b)


def s6(b):
    b.add(120, 0)
    _meta(b)  # warm_shift handled in make_heldout_scenario


def s7(b):
    b.add(70, 0, mode="low")
    b.add(35, 0)
    b.add(15, 0, mode="good")
    _meta(b)


def s8(b):
    b.add(110, 0, mag=MAG)
    b.add(10, 0, p=0.05, mag=MAG_RARE, rare=True)
    _meta(b)


def s9(b):
    est = b.add(120, 0)
    dorm = b.rng.choice(est, 25, replace=False)
    b.silence(dorm, b.tau(30), b.tau(230))
    b.step(dorm, b.tau(230), np.clip(np.asarray(b.p0)[dorm] + 0.35, 0.05, 0.85))
    _meta(b, change_t=b.tau(230), target=dorm)


def s10(b):
    est = b.add(60, 0)
    ids = list(est)
    new_ids = []
    for w in range(0, 281, 20):
        new = b.add(12, b.tau(w), mode="new")
        ids += list(new); new_ids += list(new)
        alive = [i for i in ids if b.death[i] > b.tau(w) and b.birth[i] <= b.tau(w) - 30]
        b.retire(b.rng.choice(alive, 10, replace=False), b.tau(w))
    _meta(b, new_ids=new_ids)


_BUILD = dict(zip(HELDOUT_NAMES, [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10]))


def make_heldout_scenario(name, seed, split="heldout"):
    assert split in ("heldout", "pilot")
    idx = HELDOUT_NAMES.index(name)
    g, o, log_seed = streams(split, idx, seed)
    b = Builder(g)
    _BUILD[name](b)
    warm = 100 if name.startswith("S6_") else 0
    return b.finalize(name, split, seed, o, log_seed, warm_shift=warm)
