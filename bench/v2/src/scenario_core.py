"""Scenario core for the V2 cell-attention benchmark (external research, synthetic).

A *cell* is an abstract unit that can receive research attention.  An *attempt* on a cell in a cycle
returns exactly one of two outcomes (V1 semantics, see reports/003.../01_EXPERIMENTAL_DESIGN.md):

  EVIDENCE(value)          value in [0,1] = information value (0.0 = "evidence arrived, uninformative")
  ATTEMPTED_NO_EVIDENCE    the cell could not produce evidence at that time (silence / data gap / dormancy)

A cell that is not attempted produces NOT_ATTEMPTED (no event at all).  Silence NEVER produces a value.

Nothing financial is modelled.  The information metric is scenario-defined and independent of PnL.
This module is shared by dev (train/validation) and held-out generators; it contains NO scenario
parameters, only the builder and the frozen global constants.
"""
from dataclasses import dataclass, field
import numpy as np

# ---- frozen global constants (identical for every split) -------------------------------------
K = 10            # attention units (distinct cells attempted) per cycle
R = 400           # total cycles
T0 = 80           # burn-in cycles under a common, policy-independent uniform logging policy
FRESH = 60        # freshness threshold (cycles) used by metrics and by policy A's exploration rule
H_STARVE = 80     # starvation horizon (cycles)
W_COV = 40        # coverage window (cycles)
GROUPS = 10       # number of generic descriptor groups (static metadata visible at birth)
BIG = 10 ** 6
MAG = 0.5         # information value of an informative event for ordinary cells
MAG_RARE = 1.0    # information value of an informative event for "rare high information" cells
LOW_INFO_EV = 0.05  # ground-truth threshold on expected information for "genuinely low information"
PIT_FRACTION = 0.10  # fraction of cells born with pit_unverified=True (cleared after 3 evidence events)

SPLIT_CODE = {"train": 1, "validation": 2, "heldout": 3, "pilot": 4, "adversarial": 5}


@dataclass
class Scenario:
    name: str
    split: str
    seed: int
    n: int
    birth: np.ndarray            # (n,) absolute cycle of creation (0 = established)
    death: np.ndarray            # (n,) absolute cycle of retirement (BIG = never)
    group: np.ndarray            # (n,)
    pit0: np.ndarray             # (n,) bool
    mag: np.ndarray              # (n,)
    rare: np.ndarray             # (n,) bool
    P: np.ndarray                # (R, n) probability that an attempt is informative
    silent: np.ndarray           # (R, n) bool: cell cannot produce evidence at this cycle (hidden)
    U: np.ndarray                # (R, n) common random numbers for outcomes
    log_seed: int
    warm_shift: int = 0
    meta: dict = field(default_factory=dict)   # ground-truth annotations for metrics only

    # hidden ground truth --------------------------------------------------------------------
    def eligible(self, t):
        return (self.birth <= t) & (t < self.death)

    def outcome(self, t, c):
        """(kind, value). Silence -> ATTEMPTED_NO_EVIDENCE, never a value."""
        if self.silent[t, c]:
            return "ATTEMPTED_NO_EVIDENCE", None
        v = float(self.mag[c]) if self.U[t, c] < self.P[t, c] else 0.0
        return "EVIDENCE", v

    def ev(self):
        """(R, n) expected information of an attempt (0 for non-existent cells)."""
        return self.P * self.mag[None, :]


class Builder:
    def __init__(self, rng, R_=R, T0_=T0, n_groups=GROUPS):
        self.rng, self.R, self.T0, self.G = rng, R_, T0_, n_groups
        self.gm = rng.uniform(0.12, 0.60, n_groups)   # group-level information probability
        self.birth, self.death, self.group, self.mag, self.rare, self.p0 = [], [], [], [], [], []
        self.mods = []
        self.meta = {}

    @property
    def n(self):
        return len(self.birth)

    def tau(self, x):
        """eval-relative cycle -> absolute cycle"""
        return self.T0 + int(x)

    def add(self, n, birth, death=BIG, mode="est", mag=MAG, rare=False, group=None, p=None):
        rng, first = self.rng, self.n
        g = rng.integers(0, self.G, n) if group is None else np.asarray(group)
        if p is not None:
            pv = np.broadcast_to(np.asarray(p, float), (n,)).copy()
        elif mode == "est":
            pv = np.clip(self.gm[g] + rng.normal(0, 0.10, n), 0.03, 0.85)
        elif mode == "new":
            pv = np.clip(0.6 * self.gm[g] + 0.4 * rng.beta(2, 6, n) + rng.normal(0, 0.05, n), 0.02, 0.85)
            gem = rng.random(n) < 0.10
            pv[gem] = rng.uniform(0.6, 0.8, gem.sum())
        elif mode == "low":
            pv = rng.uniform(0.01, 0.06, n)
        elif mode == "good":
            pv = rng.uniform(0.55, 0.80, n)
        else:
            raise ValueError(mode)
        for i in range(n):
            self.birth.append(int(birth)); self.death.append(int(death)); self.group.append(int(g[i]))
            self.mag.append(mag); self.rare.append(bool(rare)); self.p0.append(float(pv[i]))
        return np.arange(first, first + n)

    # modifications applied in order ---------------------------------------------------------
    def step(self, ids, t_abs, p_to):
        self.mods.append(("step", np.asarray(ids), int(t_abs), np.broadcast_to(np.asarray(p_to, float), (len(ids),)).copy()))

    def ramp(self, ids, ta, tb, p_to):
        self.mods.append(("ramp", np.asarray(ids), int(ta), int(tb), np.broadcast_to(np.asarray(p_to, float), (len(ids),)).copy()))

    def silence(self, ids, ta, tb):
        self.mods.append(("silent", np.asarray(ids), int(ta), int(tb)))

    def retire(self, ids, t_abs):
        for i in ids:
            self.death[int(i)] = int(t_abs)

    def finalize(self, name, split, seed, rng_out, log_seed, warm_shift=0):
        n = self.n
        P = np.tile(np.asarray(self.p0, float)[None, :], (self.R, 1))
        S = np.zeros((self.R, n), bool)
        for m in self.mods:
            if m[0] == "step":
                _, ids, t, pto = m
                P[t:, ids] = pto[None, :]
            elif m[0] == "ramp":
                _, ids, ta, tb, pto = m
                start = P[ta, ids].copy()
                for t in range(ta, tb):
                    f = (t - ta + 1) / (tb - ta)
                    P[t, ids] = start + f * (pto - start)
                P[tb:, ids] = pto[None, :]
            elif m[0] == "silent":
                _, ids, ta, tb = m
                S[ta:tb, ids] = True
        pit0 = self.rng.random(n) < PIT_FRACTION
        U = rng_out.random((self.R, n))
        return Scenario(name=name, split=split, seed=seed, n=n,
                        birth=np.asarray(self.birth), death=np.asarray(self.death),
                        group=np.asarray(self.group), pit0=pit0, mag=np.asarray(self.mag, float),
                        rare=np.asarray(self.rare), P=P, silent=S, U=U, log_seed=log_seed,
                        warm_shift=warm_shift, meta=self.meta)


def streams(split, scen_idx, seed):
    """Independent RNG streams: generator / outcomes / logging policy."""
    ss = np.random.SeedSequence([SPLIT_CODE[split], scen_idx, seed])
    a, b, c = ss.spawn(3)
    return np.random.default_rng(a), np.random.default_rng(b), int(c.generate_state(1)[0])
