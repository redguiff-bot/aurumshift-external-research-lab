"""Targeted paired comparisons (diversification, turnover, complexity) on heldout H1 + failure battery D4."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import common as C
pd.set_option("display.width", 250)
A = f"{C.ROOT}/results/analysis"; rng = np.random.default_rng(11)
h1 = pd.read_csv(f"{C.ROOT}/results/heldout/H1_primary.csv"); d4 = pd.read_csv(f"{C.ROOT}/results/diagnostics/D4_failure_modes.csv"); d4 = d4[~d4.tag.str.startswith("D4i")]
def pair(df, a, b, scen, m):
    x = df[(df.policy == a) & (df.scen == scen)].sort_values("seed")[m].values; y = df[(df.policy == b) & (df.scen == scen)].sort_values("seed")[m].values
    d = x - y; bs = d[rng.integers(0, len(d), (2000, len(d)))].mean(1)
    return d.mean(), np.quantile(bs, .025), np.quantile(bs, .975)
rows = []
PAIRS = [("SLOTHOUR", "SCORE_RANK"), ("SLOTHOUR_SHADOW", "SLOTHOUR"), ("OLDEST_SLOT", "FIFO"), ("OLDEST_SLOT", "FIFO_SCREEN"), ("CORR_AWARE", "SLOTHOUR"),
         ("UNCERTAINTY_LCB", "SLOTHOUR"), ("LINTS", "SLOTHOUR"), ("ROUND_ROBIN", "FIFO"), ("EQUAL_QUOTA", "FIFO"), ("SCORE_RANK", "FIFO_SCREEN")]
for src, df in (("H1", h1), ("D4", d4)):
    for (a, b) in PAIRS:
        for s in sorted(df.scen.unique()):
            for m in ("net_per_avail_slot_hour", "pnl_std", "worst_24h", "max_drawdown", "hhi_group", "churn_reentry_frac", "idle_slot_hours", "hq_capture", "starve_soft_rate", "max_denial_hours", "rej_rate_instw"):
                d, lo, hi = pair(df, a, b, s, m)
                rows.append(dict(src=src, a=a, b=b, scen=s, metric=m, diff=d, lo=lo, hi=hi))
out = pd.DataFrame(rows); out.to_csv(f"{A}/targeted_pairs.csv", index=False)
M = out[out.metric == "net_per_avail_slot_hour"]
for (a, b) in PAIRS:
    sub = M[(M.a == a) & (M.b == b) & (M.src == "H1")]
    print(a, "-", b, "| sig+ :", list(sub[sub.lo > 0].scen.str.split("_").str[0]), "| sig- :", list(sub[sub.hi < 0].scen.str.split("_").str[0]))
print("\nDIVERSIFICATION CORR_AWARE - SLOTHOUR")
for src in ("H1", "D4"):
    sub = out[(out.a == "CORR_AWARE") & (out.b == "SLOTHOUR") & (out.src == src) & (out.scen.isin(["S5_correlated", "S5b_corr_benign", "F_corr_collapse"]))]
    print(sub.pivot(index=["scen", "metric"], columns=[], values=["diff", "lo", "hi"]).round(2).to_string() if False else sub[["scen", "metric", "diff", "lo", "hi"]].round(2).to_string())
