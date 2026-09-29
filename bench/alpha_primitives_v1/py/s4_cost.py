"""Cost sensitivity. UNKNOWN_COST != ZERO_COST. Gross and net reported separately."""
from common import *
P = load_panel(); NAMES = list(X.PRIMS); out = {}
for k in NAMES:
    W = weights(k, P); r = {"mult": {}, "uniform_bps": {}}
    for m in [0, 0.5, 1, 1.5, 2, 3]:
        B = bt(k, P, W=W, cost_mult=m)
        r["mult"][str(m)] = {"full": L.summarize(B), "holdout": L.summarize(B, start=L.SPLIT)}
    for b in [0, 2, 5, 8, 12, 20, 30]:
        cm = {s: float(b) for s in L.SYMS}; B = bt(k, P, W=W, cost_map=cm)
        f = L.summarize(B); h = L.summarize(B, start=L.SPLIT)
        r["uniform_bps"][str(b)] = {"net_sharpe": f["net_sharpe"], "net_ann": f["net_ann"], "ho_net_sharpe": h["net_sharpe"]}
    B = bt(k, P, W=W, cost_map={}); f = L.summarize(B)    # every asset UNKNOWN -> 15 bps/side
    r["all_unknown_15bps"] = {"net_sharpe": f["net_sharpe"], "net_ann": f["net_ann"]}
    B = bt(k, P, W=W, funding=False); f = L.summarize(B)  # funding excluded (would be wrong for perps): shows funding contribution
    r["no_funding_net_sharpe"] = f["net_sharpe"]
    b1 = L.summarize(bt(k, P, W=W))
    r["gross_to_cost_ratio"] = float(b1["gross_ann"] / b1["cost_ann"]) if b1["cost_ann"] > 0 else None
    out[k] = r; print(k, round(b1["net_sharpe"], 2), r["gross_to_cost_ratio"], flush=True)
jd(out, "s4_cost.json")
