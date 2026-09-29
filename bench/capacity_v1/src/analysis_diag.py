import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import common as C
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
R = f"{C.ROOT}/results/diagnostics"; A = f"{C.ROOT}/results/analysis"; M1 = "net_per_avail_slot_hour"
KEEP = ["FIFO", "RANDOM", "ROUND_ROBIN", "FIFO_SCREEN", "SCORE_RANK", "SLOTHOUR", "SLOTHOUR_SHADOW", "UNCERTAINTY_LCB", "CORR_AWARE", "LINTS", "OLDEST_SLOT", "EQUAL_QUOTA", "ORACLE_GREEDY_UB"]
def piv(df, idx, val=M1): return df.groupby([idx, "policy"])[val].mean().unstack("policy")[KEEP]
def main():
    out = {}
    d1 = pd.read_csv(f"{R}/D1_robustness.csv"); d1["fam"] = d1.tag.str.split("|").str[1]; d1["lvl"] = d1.tag.str.split("|").str[2]
    t = d1.groupby(["fam", "lvl", "policy"])[M1].mean().unstack("policy")[KEEP]
    # gap vs FIFO and vs SLOTHOUR
    t["best_impl_minus_FIFO"] = t[KEEP[:-2] + ["OLDEST_SLOT"]].max(axis=1) - t["FIFO"]
    t["LCB_minus_SLOTHOUR"] = t["UNCERTAINTY_LCB"] - t["SLOTHOUR"]
    t.to_csv(f"{A}/D1_robustness_table.csv"); print(t.round(2).to_string())
    d2 = pd.read_csv(f"{R}/D2_score_quality.csv"); d2["lvl"] = d2.tag.str.split("|").str[1]
    t2 = d2.groupby(["lvl", "policy"])[M1].mean().unstack("policy")[KEEP]; t2.to_csv(f"{A}/D2_score_quality_table.csv"); print(t2.round(2).to_string())
    # score-noise sensitivity slope (tau_mult family in D1)
    sn = d1[d1.fam == "score_noise"].groupby(["lvl", "policy"])[M1].mean().unstack("policy")[KEEP]
    sn.index = sn.index.astype(float); sn = sn.sort_index(); sn.to_csv(f"{A}/D1_score_noise_curve.csv")
    d3 = pd.read_csv(f"{R}/D3_cost.csv"); d3["cm"] = d3.tag.str.split("|").str[1].astype(float); d3["bel"] = d3.tag.str.split("|").str[2]
    t3 = d3.groupby(["scen", "bel", "cm", "policy"])[[M1, "n_admit"]].mean().reset_index()
    t3p = t3.pivot_table(index=["scen", "bel", "cm"], columns="policy", values=M1)[KEEP]; t3p.to_csv(f"{A}/D3_cost_table.csv"); print(t3p.round(2).to_string())
    d4 = pd.read_csv(f"{R}/D4_failure_modes.csv")
    d4a = d4[~d4.tag.str.startswith("D4i")]
    keys = [M1, "hq_capture", "top_inst_share", "hhi_group", "starve_soft_rate", "max_denial_hours", "churn_reentry_frac", "occ_std", "pnl_std", "worst_24h", "max_drawdown", "top_inst_admit_share", "mean_hold", "rej_rate_instw", "idle_slot_hours"]
    f4 = d4a.groupby(["scen", "policy"])[keys].mean(); f4.to_csv(f"{A}/D4_failure_modes_all_metrics.csv")
    print(d4a.groupby(["scen", "policy"])[M1].mean().unstack("policy")[KEEP].round(2).to_string())
    d4i = d4[d4.tag.str.startswith("D4i")].copy(); d4i["ing"] = d4i.tag.str.split("|").str[1]
    si = d4i.groupby(["ing", "policy"])[[M1, "top_inst_admit_share", "rej_rate_instw", "n_admit"]].mean(); si.to_csv(f"{A}/D4_spam_ingest_S10.csv")
    d5 = pd.read_csv(f"{R}/D5_param_sensitivity.csv")
    t5 = d5.groupby(["policy", "params"])[M1].mean(); t5.to_csv(f"{A}/D5_param_sensitivity_table.csv"); print(t5.round(3).to_string())
    # paired spam-ingest effect (S10, validation seeds 7000-7009): RAW vs other semantics
    rows = []
    rng = np.random.default_rng(5)
    for p in ("FIFO", "SLOTHOUR", "SCORE_RANK", "UNCERTAINTY_LCB", "FIFO_SCREEN", "ROUND_ROBIN"):
        raw = d4i[(d4i.ing == "RAW") & (d4i.policy == p)].sort_values("seed")
        for ing in ("DEDUP_LATEST", "COOLDOWN", "SCORE_UPDATE"):
            o = d4i[(d4i.ing == ing) & (d4i.policy == p)].sort_values("seed")
            for m in (M1, "top_inst_admit_share"):
                d = (o[m].values - raw[m].values); bs = d[rng.integers(0, len(d), (2000, len(d)))].mean(1)
                rows.append(dict(policy=p, ingest=ing, metric=m, diff_vs_RAW=d.mean(), lo=np.quantile(bs, .025), hi=np.quantile(bs, .975)))
    pd.DataFrame(rows).to_csv(f"{A}/D4_spam_paired_vs_RAW.csv", index=False); print(pd.DataFrame(rows).round(3).to_string())
if __name__ == "__main__":
    main()
