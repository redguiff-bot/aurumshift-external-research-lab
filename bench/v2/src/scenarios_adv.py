"""POST-HOC adversarial scenarios X1..X5 (written AFTER the held-out run, to try to falsify the apparent winners).
They are NOT held-out scenarios, were never used for selection, and are reported separately (09)."""
import numpy as np
from scenario_core import *  # noqa

ADV_NAMES = ["X1_PERMANENT_SILENCE", "X2_OSCILLATING_REGIME", "X3_NO_SIGNAL", "X4_HIGH_CHURN", "X5_FLAKY_HIGH_VALUE"]


def x1(b):
    est = b.add(120, 0)
    b.silence(b.rng.choice(est, 60, replace=False), b.tau(40), R)          # half the fleet silent forever
    b.meta.update(change_t=None, target=[], degraded=[], new_ids=[])


def x2(b):
    est = b.add(120, 0)
    osc = b.rng.choice(est, 30, replace=False)
    hi, lo = np.full(30, 0.75), np.full(30, 0.05)
    for k, ta in enumerate(range(b.tau(20), R, 40)):
        b.step(osc, ta, hi if k % 2 == 0 else lo)
    b.meta.update(change_t=None, target=[], degraded=[], new_ids=[])


def x3(b):
    b.add(120, 0, p=0.15)                                                   # no information gradient at all
    b.meta.update(change_t=None, target=[], degraded=[], new_ids=[])


def x4(b):
    est = b.add(60, 0)
    ids, new_ids = list(est), []
    for w in range(0, 311, 10):
        new = b.add(20, b.tau(w), mode="new"); ids += list(new); new_ids += list(new)
        alive = [i for i in ids if b.death[i] > b.tau(w) and b.birth[i] <= b.tau(w) - 15]
        if len(alive) > 20:
            b.retire(b.rng.choice(alive, 20, replace=False), b.tau(w))     # cells live ~40 cycles
    b.meta.update(change_t=None, target=[], degraded=[], new_ids=new_ids)


def x5(b):
    est = b.add(120, 0, mode="est")
    p0 = np.asarray(b.p0)
    top = est[np.argsort(-p0[est])[:30]]
    b.meta.update(change_t=None, target=[], degraded=[], new_ids=[], flaky=top.tolist())
    b._flaky = top


_BUILD = dict(zip(ADV_NAMES, [x1, x2, x3, x4, x5]))


def make_adv_scenario(name, seed):
    idx = ADV_NAMES.index(name)
    g, o, log_seed = streams("adversarial", idx, seed)
    b = Builder(g)
    _BUILD[name](b)
    sc = b.finalize(name, "adversarial", seed, o, log_seed)
    if name == "X5_FLAKY_HIGH_VALUE":       # each attempt on a top cell returns nothing with prob 0.5 (independent per (t,c))
        flake = np.random.default_rng([seed, 55]).random((R, sc.n)) < 0.5
        cols = np.array(b._flaky)
        sc.silent[T0:, cols] = flake[T0:, cols]
    return sc
