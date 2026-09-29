"""Reference cost-accounting contract (external research artifact; NOT AurumShift code).

Price ladder for a BUY (mirror for SELL via `side`):
   decision_mid --(timing)--> exec_mid --(spread)--> touch --(slippage/walk)--> avg_fill --(fee)--> net
   plus  impact  : displacement of exec_mid at later child fills caused by OWN earlier fills (propagator memory)
   plus  holding : funding / borrow / roll  (time-based, accrue while position is held, not part of the price ladder)
Each price displacement is owned by exactly ONE line -> no double counting by construction.
A PAPER *fill basis* says which rungs are already embedded in the simulated fill price; those lines must be
recorded as EMBEDDED_BY_BASIS (value 0 added, provenance kept) and must never be re-charged.
UNKNOWN is a first-class state and is never coerced to 0.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict

class State(str, Enum):
    MEASURED = "measured"                # observed from real fills / exchange statements
    ESTIMATED = "estimated"              # model output; carries model id + data regime
    EMBEDDED_BY_BASIS = "embedded_by_basis"
    ZERO_PROVEN = "zero_cost_proven"     # rate/fee schedule shows zero (needs source)  -- distinct from UNKNOWN
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"

COMPONENTS = ["fee", "timing", "spread", "slippage", "impact", "funding", "borrow", "roll"]
# rung ownership of each fill basis: components whose effect is ALREADY inside the simulated fill price
BASIS_EMBEDS = {
    "MID":        set(),
    "TOUCH":      {"spread"},
    "BOOK_VWAP":  {"spread", "slippage"},
    "LAST_TRADE": set(),                 # last print: spread is embedded only in expectation -> treat as NOT known-embedded
    "BAR_CLOSE":  set(),                 # unknown relation to executable price -> nothing provably embedded
    "REAL_FILL":  {"spread", "slippage", "timing", "impact"},   # measured broker/exchange fill embeds all price rungs
}

@dataclass
class Line:
    component: str
    state: State
    bps: Optional[float] = None          # signed cost, positive = cost to the trader
    lo: Optional[float] = None
    hi: Optional[float] = None
    source: str = ""                     # data source / model id (mandatory for ESTIMATED, MEASURED, ZERO_PROVEN)

    def validate(self):
        assert self.component in COMPONENTS, self.component
        if self.state in (State.MEASURED, State.ESTIMATED):
            assert self.bps is not None, f"{self.component}: {self.state} needs a value"
        if self.state in (State.MEASURED, State.ESTIMATED, State.ZERO_PROVEN):
            assert self.source, f"{self.component}: {self.state} needs a source"
        if self.state == State.ZERO_PROVEN:
            assert self.bps in (None, 0.0)
        if self.state in (State.UNKNOWN, State.NOT_APPLICABLE, State.EMBEDDED_BY_BASIS):
            assert self.bps in (None, 0.0), f"{self.component}: {self.state} must not carry a charge"

@dataclass
class Ledger:
    basis: str
    lines: Dict[str, Line] = field(default_factory=dict)

    def put(self, line: Line):
        line.validate()
        if line.component in BASIS_EMBEDS[self.basis] and line.state in (State.MEASURED, State.ESTIMATED):
            raise ValueError(f"DOUBLE_COUNT: {line.component} is already embedded by basis {self.basis}")
        self.lines[line.component] = line

    def seal(self, applicable_holding=("funding",), ):
        """Fill unspecified components: embedded -> EMBEDDED_BY_BASIS, otherwise UNKNOWN (never 0)."""
        for c in COMPONENTS:
            if c not in self.lines:
                st = State.EMBEDDED_BY_BASIS if c in BASIS_EMBEDS[self.basis] else State.UNKNOWN
                self.lines[c] = Line(c, st)
        return self

    def total(self):
        known = 0.0; lo = 0.0; hi = 0.0; unknown = []
        for c, l in self.lines.items():
            if l.state in (State.MEASURED, State.ESTIMATED):
                known += l.bps; lo += l.lo if l.lo is not None else l.bps; hi += l.hi if l.hi is not None else l.bps
            elif l.state == State.UNKNOWN:
                unknown.append(c)
        return dict(known_bps=known, lo_bps=lo, hi_bps=hi, unknown=unknown, complete=not unknown)

    def net_outcome_bps(self, gross_bps: float):
        t = self.total()
        return dict(net_bps_if_unknown_were_zero=None,           # deliberately withheld
                    net_upper_bound_bps=gross_bps - t["lo_bps"], net_known_only_bps=gross_bps - t["known_bps"],
                    complete=t["complete"], unknown=t["unknown"])
