"""Policy-visible observable state (identical for every policy).

The ledger is maintained by the harness from typed outcomes only.  It never contains ground truth
(no p, no silence flag, no change points).  `time_since_last_evidence` and `time_since_last_attempt`
are tracked separately (V1 contract, report 06 s1).
"""
import numpy as np
from scenario_core import K, FRESH, T0

NEVER = -10 ** 6
ALPHA_SLOW_MIN, ALPHA_FAST_MIN = 0.05, 0.20


class Ledger:
    def __init__(self, sc):
        n = sc.n
        self.K, self.FRESH = K, FRESH
        self.group = sc.group.copy()
        self.birth = sc.birth.copy()          # creation is announced at birth
        self.pit_unverified = sc.pit0.copy()
        self.n_att = np.zeros(n, int)
        self.n_ev = np.zeros(n, int)
        self.last_att = np.full(n, NEVER)
        self.last_ev = np.full(n, NEVER)
        self.cons_noev = np.zeros(n, int)     # consecutive ATTEMPTED_NO_EVIDENCE
        self.m_slow = np.zeros(n)
        self.m_fast = np.zeros(n)
        self.elig = np.array([], int)
        self.warm_shift = sc.warm_shift

    def begin(self, t, eligible_mask):
        self.t = t
        self.elig = np.flatnonzero(eligible_mask)

    def stamp(self, t):
        return t - self.warm_shift if t < T0 else t

    def age_since_evidence(self, t):
        """cycles since last EVIDENCE; never-evidenced cells age from birth."""
        ref = np.where(self.n_ev > 0, self.last_ev, self.birth)
        return t - ref

    def age_since_attempt(self, t):
        ref = np.where(self.n_att > 0, self.last_att, self.birth)
        return t - ref

    def record(self, t, cell, kind, value):
        s = self.stamp(t)
        self.n_att[cell] += 1
        self.last_att[cell] = s
        if kind == "EVIDENCE":
            self.n_ev[cell] += 1
            self.last_ev[cell] = s
            self.cons_noev[cell] = 0
            n = self.n_ev[cell]
            if n == 1:
                self.m_slow[cell] = self.m_fast[cell] = value
            else:
                self.m_slow[cell] += max(1.0 / n, ALPHA_SLOW_MIN) * (value - self.m_slow[cell])
                self.m_fast[cell] += max(1.0 / n, ALPHA_FAST_MIN) * (value - self.m_fast[cell])
            if n >= 3:
                self.pit_unverified[cell] = False
        else:
            # ATTEMPTED_NO_EVIDENCE: NO change to any value statistic.
            self.cons_noev[cell] += 1
