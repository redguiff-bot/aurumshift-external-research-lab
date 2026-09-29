"""Dev-period-only selection for two primitives whose first pre-registered trigger was mis-specified:
P07 thr sat on the funding clamp (1e-4 = Binance default) -> flip-flop; P12 log-Amihud z>2 almost never fires (thin-tailed).
Selection uses DEV window ONLY (EVAL_START..SPLIT). Holdout is evaluated afterwards, untouched by selection."""
from common import *
P = load_panel(); out = {}
def grid(name, key, vals):
    rows = []
    for v in vals:
        B = bt(name, P, W=weights(name, P, **{key: v}))
        d = L.summarize(B, end=L.SPLIT)
        rows.append({key: v, "dev_net_sharpe": d["net_sharpe"], "dev_gross_sharpe": d["gross_sharpe"], "dev_turn_ann": d["turn_ann"], "dev_net_ann": d["net_ann"]})
    best = max(rows, key=lambda r: (r["dev_net_sharpe"] if r["dev_net_sharpe"] == r["dev_net_sharpe"] else -9))
    return rows, best
out["P07_BASIS_CARRY"] = grid("P07_BASIS_CARRY", "thr", [1e-4, 1.5e-4, 2e-4, 3e-4, 5e-4])
out["P12_ILLIQ_SHOCK"] = grid("P12_ILLIQ_SHOCK", "zt", [1.25, 1.5, 1.75, 2.0])
for k, (rows, best) in out.items():
    print(k); [print("  ", r) for r in rows]; print("  BEST(dev)", best)
jd({k: {"grid": r, "selected": b} for k, (r, b) in out.items()}, "s0_tune.json")
