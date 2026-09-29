"""D6: diversification stress (validation split, seeds 8000-8019). gamma up to 8, incl. a single-group-heavy world (G=2 groups)."""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import common as C, world as W
fz = json.load(open(f"{C.ROOT}/configs/frozen_params.json"))
cells = []
for scen, ov in (("S5_correlated", None), ("S5b_corr_benign", None), ("F_corr_collapse", None), ("S5_correlated", {"rho_g": 0.9}), ("S5b_corr_benign", {"rho_g": 0.9})):
    tag = f"{scen}|{'rho0.9' if ov else 'base'}"
    for sd in range(8000, 8020):
        cells.append(dict(scen=scen, seed=sd, split="validation", policy="SLOTHOUR", params={}, ingest="SCORE_UPDATE", K=4, overrides=ov, tag=tag + "|SLOTHOUR"))
        for g in (0.1, 0.4, 1.0, 2.0, 4.0, 8.0):
            cells.append(dict(scen=scen, seed=sd, split="validation", policy="CORR_AWARE", params={"gamma": g}, ingest="SCORE_UPDATE", K=4, overrides=ov, tag=tag + f"|g{g}"))
rows = C.run_many(cells); C.write_csv(rows, f"{C.ROOT}/results/diagnostics/D6_diversification_stress.csv")
df = pd.DataFrame(rows); df["case"] = df.tag.str.split("|").str[0] + "|" + df.tag.str.split("|").str[1]; df["arm"] = df.tag.str.split("|").str[2]
t = df.groupby(["case", "arm"])[["net_per_avail_slot_hour", "pnl_std", "worst_24h", "max_drawdown", "hhi_group", "hq_capture"]].mean()
t.to_csv(f"{C.ROOT}/results/analysis/D6_diversification_stress_table.csv"); print(t.round(3).to_string())
