"""Contract property tests + E1..E15 threat matrix (naive PAPER accounting vs synthetic truth / reference contract)."""
import sys, os, json
H = os.path.dirname(__file__)
sys.path[:0] = [os.path.join(H, "..", "synthetic"), os.path.join(H, "..", "models"), H]
import numpy as np
from dataclasses import replace
from synth import *
from cost_contract import *
import models as M
sys.path.insert(0, os.path.join(H, "..", "synthetic")); import run_synth as R
RES = os.path.join(H, "..", "results")
fbr = json.load(open(f"{RES}/funding_borrow_roll.json"))
res = {"contract_tests": {}, "threats": []}

# ---------------------------------------------------------------- contract tests
def t_identity():
    worst = 0.0
    for name, sc in R.SCEN.items():
        for N in [1e4, 1e6, 1e7]:
            r = simulate_market(sc, N, 100, 5)
            worst = max(worst, np.abs(r["IS"] - (r["drift"] + r["half_spread"] + r["walk"] + r["impact"])).max())
    for s in (1, 5, 20):
        r = simulate_market(replace(Scenario(), A=1.5e5), 1e6, 100, 6, slices=s, horizon=600.0)
        worst = max(worst, np.abs(r["IS"] - (r["drift"] + r["half_spread"] + r["walk"] + r["impact"])).max())
    return worst

def t_basis_no_double_count():
    """PAPER fill at basis b + contract lines == truth IS for every basis when lines are set per ownership; overcharge is refused."""
    sc = R.SCEN["base"]; N = 1e6
    r = simulate_market(sc, N, 400, 8)
    truth = (r["half_spread"] + r["walk"]).mean()      # timing zero-mean here, impact 0 for a single child
    out = {}
    for basis, paper_fill in [("MID", 0.0), ("TOUCH", sc.spread / 2 - sc.spread / 2 + 0.0), ("BOOK_VWAP", truth)]:
        # PAPER fill price relative to mid already contains: MID:none, TOUCH:+half spread (we model fill at touch), VWAP: spread+walk
        embedded = {"MID": 0.0, "TOUCH": r["half_spread"].mean(), "BOOK_VWAP": truth}[basis]
        L = Ledger(basis)
        if basis == "MID":
            L.put(Line("spread", State.MEASURED, r["half_spread"].mean(), source="quote"))
            L.put(Line("slippage", State.ESTIMATED, r["walk"].mean(), source="book_walk_L2"))
        elif basis == "TOUCH":
            L.put(Line("slippage", State.ESTIMATED, r["walk"].mean(), source="book_walk_L2"))
        L.seal()
        charged = L.total()["known_bps"]
        out[basis] = dict(embedded_in_fill=float(embedded), contract_extra=float(charged), total=float(embedded + charged), truth=float(truth),
                          abs_err=float(abs(embedded + charged - truth)))
    # overcharge attempt is refused
    refused = False
    try:
        L = Ledger("BOOK_VWAP"); L.put(Line("spread", State.ESTIMATED, 0.5, source="x"))
    except ValueError:
        refused = True
    out["overcharge_refused"] = refused
    # naive stacking of three models each including the spread: what it charges
    p = R.SCEN["base"]
    sq = M.m_sqrt(dict(N=N, spread=p.spread, sigma=p.sigma, V_day=p.V_day), dict(Y=0.117))
    stack = p.spread + 1.0 + sq          # full spread + 1bp 'slippage' + sqrt model (which itself adds half-spread)
    out["naive_stack_bps"] = float(stack); out["truth_bps"] = float(truth); out["overcharge_ratio"] = float(stack / truth)
    return out

def t_unknown_not_zero():
    L = Ledger("BOOK_VWAP"); L.put(Line("fee", State.MEASURED, 5.0, source="fill")); L.seal()
    t = L.total(); n = L.net_outcome_bps(20.0)
    ok1 = "funding" in t["unknown"] and "borrow" in t["unknown"] and not t["complete"]
    ok2 = n["net_bps_if_unknown_were_zero"] is None
    L2 = Ledger("BOOK_VWAP"); L2.put(Line("fee", State.MEASURED, 5.0, source="fill"))
    for c in ("funding", "borrow", "roll", "timing", "impact"): L2.put(Line(c, State.NOT_APPLICABLE))
    L2.seal(); ok3 = L2.total()["complete"]
    L3 = Ledger("MID")
    try:
        L3.put(Line("funding", State.ZERO_PROVEN, 0.0)); ok4 = False       # missing source -> must be rejected
    except AssertionError:
        ok4 = True
    return dict(unknown_listed=ok1, net_withheld=ok2, complete_when_all_resolved=ok3, zero_proof_needs_source=ok4)

res["contract_tests"]["ladder_identity_max_abs_residual_bps"] = float(t_identity())
res["contract_tests"]["basis_no_double_count"] = t_basis_no_double_count()
res["contract_tests"]["unknown_not_zero"] = t_unknown_not_zero()

# ---------------------------------------------------------------- threat matrix
def IS(sc, N, seed=5, **kw):
    r = simulate_market(sc, N, 300, seed, **kw); return r, float(r["IS"].mean())
B = R.SCEN["base"]
def add(id_, name, naive, correct, unit, expected, contract_state, note=""):
    res["threats"].append(dict(id=id_, name=name, naive=naive, correct=correct, error=None if (naive is None or correct is None) else float(naive - correct),
                               unit=unit, expected_behavior=expected, contract_state=contract_state, note=note))
r, x = IS(B, 1e5); add("E1", "mid-price fill fantasy", 0.0, x, "bps", "charge at least half-spread + walk at executable price", "spread/slippage: ESTIMATED or EMBEDDED_BY_BASIS, never absent")
add("E2", "zero spread", 0.0, B.spread / 2, "bps", "spread line must exist; unknown spread => UNKNOWN not 0", "spread: UNKNOWN when no quote")
r, x = IS(B, 1e6); add("E3", "zero slippage (spread only)", B.spread / 2, x, "bps", "size-dependent walk charged (1M USD)", "slippage: ESTIMATED(book_walk) / UNKNOWN(OHLCV)")
sh = replace(B, A=3e3, V_day=1e7); r, x = IS(sh, 5e7)
add("E4", "infinite liquidity (fill at touch)", sh.spread / 2, x, "bps", "walk beyond depth, cap fill", "fill fraction reported", f"filled={float(r['filled'].mean()):.2f}")
tr = R.SCEN["trend"]; r, x = IS(tr, 1e5); add("E5", "fill at stale quote (trend, lat 3s)", 0.0, float(r["drift"].mean()), "bps", "price at arrival time, not at observation time", "timing: ESTIMATED with latency model")
gp = R.SCEN["gap"]; r, x = IS(gp, 1e5); add("E5b", "stale quote across gap", 0.0, float(r["drift"].mean()), "bps", "gap risk is a tail; cannot be ex-ante estimated", "timing: UNKNOWN/tail flag", "no ex-ante model recovers this (see single_orders.csv gap)")
add("E6", "full fill though depth insufficient", 1.0, float(r["filled"].mean()) if False else simulate_market(sh, 5e7, 100, 3)["filled"].mean(), "filled_fraction", "partial fill / reject; unfilled not charged as cost but reported as opportunity", "filled_fraction < 1 propagated")
gl = json.load(open(f"{RES}/limit_fills.json"))["grid"]
g0 = [g for g in gl if g["drift"] == 0.1 and g["info"] == 0.5 and g["queue_frac"] == 1.0 and g["fee_m"] == 2.0 and g["spread"] == 1.0 and g["sigma"] == 0.9 and g["V"] == 2000][0]
add("E7", "no adverse selection (passive always fills at touch)", g0["bid0"] + g0["fee_m"], g0["IS_maker"], "bps", "fill prob<1 and chase cost on misses; markout of fills", "slippage/timing ESTIMATED; fill_prob reported",
    f"truth ff={g0['ff']:.2f}, adverse markout={g0['adverse']:.2f}bps")
bj = fbr["binance_vision_BTCUSDT"]["hold"]["7d_long_pays_bps"]
add("E8", "funding omitted (perp long held 7d, BTC, May-Aug 2026 rolling windows)", 0.0, bj["mean"], "bps", "accrue funding at settlement times; p05/p95 shown", "funding: MEASURED (settled) / ESTIMATED (forward)", f"p05={bj['p05']:.1f} p95={bj['p95']:.1f} min={bj['min']:.1f} max={bj['max']:.1f}")
bo = fbr["okx_public_borrow_basic"]["BTC"]
add("E9", "borrow unknown treated as zero", 0.0, None, "bps", "UNKNOWN_COST; net outcome withheld or bounded; never 0", "borrow: UNKNOWN (public venue base rate exists but realised/tier not observable)",
    f"OKX public base rate BTC={bo['rate']} (unit to verify); inference only")
rl = fbr["okx_btcusd_dated_curve"]["rolls"][1]
add("E10", "roll ignored (OKX BTC-USD 261127->261225, long)", 0.0, rl["roll_all_in_bps_long"], "bps", "calendar spread + 2 leg half-spreads at roll", "roll: MEASURED at roll, ESTIMATED forward", f"cal spread={rl['calendar_spread_bps']:.1f}bps legs={rl['leg_half_spreads_bps']:.1f}bps")
lt = json.load(open(f"{RES}/latency_fragmentation.json")); l1 = [x for x in lt if x.get("regime") == "rw" and x.get("lat") == 5][0]
add("E11", "latency ignored (random walk, lat 5s)", 0.0, l1["sd_drift"], "bps (1 sd of drift; mean~0)", "add zero-mean noise / band, not a bias, unless drift/adverse flow", "timing: ESTIMATED band", f"mean={l1['mean_drift']:.2f}")
wd = R.SCEN["withdraw"]; r, x = IS(wd, 1e6); r0, x0 = IS(B, 1e6)
add("E12", "quote disappears before execution (depth x0.15, spread x3)", x0, x, "bps", "stale-snapshot risk: widen with stress band", "slippage: ESTIMATED + band")
r, x = IS(B, 1e7); add("E13", "market order crosses many levels (10M USD)", B.spread / 2, x, "bps", "walk all crossed levels", "slippage: ESTIMATED(book_walk)")
comp = json.load(open(f"{RES}/competing.json"))
c = [x for x in comp if x["kind"] == "E14_simultaneous" and x["k"] == 5 and x["N"] == 5e5][0]
add("E14", "5 correlated simultaneous orders (500k each) priced independently", c["naive_independent"], c["truth_avg_cost_per_order"], "bps/order", "aggregate flow walks one book", "impact/slippage on netted aggregate")
c = [x for x in comp if x["kind"] == "E15_sequential_recovery" and x.get("gap_s") == 1.0][0]
add("E15", "5 repeated orders 1s apart (depletion, rho=0.05/s)", c["naive_independent"], c["truth_avg_cost_per_order"], "bps/order", "book depletion + recovery memory", "impact: ESTIMATED with memory")
json.dump(res, open(f"{RES}/threat_matrix_and_contract_tests.json", "w"), indent=1, default=float)
print(json.dumps(res["contract_tests"], indent=1, default=float))
for t in res["threats"]: print(t["id"], t["name"][:50], "naive", t["naive"], "correct", None if t["correct"] is None else round(t["correct"], 2), "err", None if t["error"] is None else round(t["error"], 2))
