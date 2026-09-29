"""Pre-registered heldout analysis. Emits results/analysis/*.csv|json (tables are quoted by the reports)."""
import json, os, sys, itertools
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import common as C

OUT = f"{C.ROOT}/results/analysis"; os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(20260929)
M1 = "net_per_avail_slot_hour"
SIMPLE = ["FIFO_SCREEN", "SCORE_RANK", "SLOTHOUR", "ROUND_ROBIN"]
COMPLEX = ["SLOTHOUR_SHADOW", "UNCERTAINTY_LCB", "CORR_AWARE", "LINTS"]
CAND = ["SCORE_RANK", "SLOTHOUR", "SLOTHOUR_SHADOW", "UNCERTAINTY_LCB", "CORR_AWARE", "LINTS"]
IMPL = ["FIFO", "ROUND_ROBIN", "RANDOM", "EQUAL_QUOTA", "OLDEST_SLOT", "FIFO_SCREEN", "SCORE_RANK", "SLOTHOUR",
        "SLOTHOUR_SHADOW", "UNCERTAINTY_LCB", "CORR_AWARE", "LINTS"]
NB = 2000

def mat(df, pol, metric=M1):
    d = df[df.policy == pol].pivot(index="scen", columns="seed", values=metric).sort_index()
    return d

def paired_boot(a, b):
    """a,b: (scen x seed) matrices. returns per-scen (mean,lo,hi) and macro (mean,lo,hi) of a-b."""
    diff = a.values - b.values; S, n = diff.shape
    per = []
    for s in range(S):
        idx = RNG.integers(0, n, (NB, n)); bs = diff[s][idx].mean(1)
        per.append((diff[s].mean(), *np.quantile(bs, [0.025, 0.975])))
    idx = RNG.integers(0, n, (S, NB, n))
    macro_bs = np.mean([diff[s][idx[s]].mean(1) for s in range(S)], axis=0)
    return dict(zip(a.index, per)), (diff.mean(), *np.quantile(macro_bs, [0.025, 0.975]))

def main():
    h1 = pd.read_csv(f"{C.ROOT}/results/heldout/H1_primary.csv")
    scen = sorted(h1.scen.unique())
    res = {}
    # ---- macro table of all metrics ----
    keys = [M1, "net_total", "net_per_busy_slot_hour", "turnover_per_slot_hour", "idle_slot_hours", "idle_with_backlog", "hhi_inst",
            "hhi_group", "top_inst_share", "starve_inst_rate", "starve_soft_rate", "max_denial_hours", "top_inst_admit_share",
            "rej_rate_instw", "rej_rate_raw", "adm_rate", "hq_capture", "pnl_std", "worst_24h", "max_drawdown", "churn_reentry_frac",
            "occ_std", "full_frac", "mean_hold", "n_admit", "evict_frac", "sel_time_s"]
    macro = h1.groupby(["policy", "scen"])[keys].mean().groupby("policy").mean()
    orc = macro.loc["ORACLE_GREEDY_UB", M1]
    macro["regret_vs_oracle_M1"] = orc - macro[M1]
    macro.to_csv(f"{OUT}/H1_macro_all_metrics.csv")
    perscen = h1.groupby(["policy", "scen"])[keys].mean()
    perscen.to_csv(f"{OUT}/H1_perscenario_all_metrics.csv")
    # ---- paired comparisons ----
    fifo, fscr = mat(h1, "FIFO"), mat(h1, "FIFO_SCREEN")
    rows = []; perrows = []
    for p in IMPL:
        if p == "FIFO":
            continue
        for ref, refm in (("FIFO", fifo), ("FIFO_SCREEN", fscr)):
            if p == ref: continue
            per, mac = paired_boot(mat(h1, p), refm)
            rows.append(dict(policy=p, ref=ref, macro_diff=mac[0], lo=mac[1], hi=mac[2],
                             wins=int(sum(v[0] > 0 for v in per.values())), n=len(per)))
            for s, v in per.items():
                perrows.append(dict(policy=p, ref=ref, scen=s, diff=v[0], lo=v[1], hi=v[2]))
    pd.DataFrame(rows).to_csv(f"{OUT}/H1_paired_macro.csv", index=False)
    per = pd.DataFrame(perrows); per.to_csv(f"{OUT}/H1_paired_perscenario.csv", index=False)
    # ---- rules: FIFO failure / equivalence ----
    rules = {}
    for delta in (0.1, 0.25, 0.5):
        out = {}
        for ref in ("FIFO", "FIFO_SCREEN"):
            fail, eq = [], []
            for s in scen:
                sub = per[(per.ref == ref) & (per.scen == s) & (per.policy.isin(CAND))]
                (fail if (sub.lo > delta).any() else eq).append(s)
            out[ref] = dict(failure=fail, equivalent=eq)
        rules[str(delta)] = out
    res["rules"] = rules
    # ---- verdict machinery ----
    mm = macro[M1]
    best_impl = mm[IMPL].idxmax()
    perm = pd.DataFrame(rows)
    B = [p for p in IMPL if p != "FIFO" and (lambda r: r.macro_diff > 0.25 and r.lo > 0)(perm[(perm.policy == p) & (perm.ref == "FIFO")].iloc[0])]
    T = [p for p in IMPL if mm[p] >= mm[best_impl] - 0.25]
    T = [p for p in T if p == "FIFO" or perm[(perm.policy == p) & (perm.ref == "FIFO")].iloc[0].wins >= 8]
    best_simple = mm[SIMPLE].idxmax(); best_complex = mm[COMPLEX].idxmax()
    cj = {}
    for p in COMPLEX:
        per_, mac = paired_boot(mat(h1, p), mat(h1, best_simple))
        cj[p] = dict(macro_diff=mac[0], lo=mac[1], hi=mac[2], wins=int(sum(v[0] > 0 for v in per_.values())),
                     justified=bool(mac[0] > 0.25 and mac[1] > 0 and sum(v[0] > 0 for v in per_.values()) >= 8))
    rnd = perm[(perm.policy == "RANDOM")]
    res["verdict_machinery"] = dict(best_implementable=best_impl, B=B, T=T, best_simple=best_simple, best_complex=best_complex,
                                    complexity=cj, macro_M1={k: float(v) for k, v in mm.items()})
    # extra pairwise (diagnostic; also vs best_simple) for all implementables with CI
    rows2 = []
    for p in IMPL:
        if p == best_simple: continue
        per_, mac = paired_boot(mat(h1, p), mat(h1, best_simple))
        rows2.append(dict(policy=p, ref=best_simple, macro_diff=mac[0], lo=mac[1], hi=mac[2], wins=int(sum(v[0] > 0 for v in per_.values()))))
    pd.DataFrame(rows2).to_csv(f"{OUT}/H1_vs_best_simple.csv", index=False)
    # vs RANDOM
    rows3 = []
    for p in IMPL:
        if p == "RANDOM": continue
        per_, mac = paired_boot(mat(h1, p), mat(h1, "RANDOM"))
        rows3.append(dict(policy=p, macro_diff_vs_random=mac[0], lo=mac[1], hi=mac[2]))
    pd.DataFrame(rows3).to_csv(f"{OUT}/H1_vs_random.csv", index=False)
    # ---- regret & FIFO dims per scenario ----
    fr = perscen.loc["FIFO"][[M1, "hq_capture", "top_inst_share", "hhi_inst", "rej_rate_instw", "net_per_busy_slot_hour"]]
    br = perscen.loc[best_simple][[M1, "hq_capture", "top_inst_share", "hhi_inst", "rej_rate_instw", "net_per_busy_slot_hour"]]
    orr = perscen.loc["ORACLE_GREEDY_UB"][M1]
    fd = pd.concat({"FIFO": fr, best_simple: br}, axis=1); fd["regret_FIFO"] = orr - fr[M1]; fd["regret_" + best_simple] = orr - br[M1]
    fd.to_csv(f"{OUT}/H1_fifo_dims.csv")
    # ---- H2 ingest matrix ----
    h2 = pd.read_csv(f"{C.ROOT}/results/heldout/H2_ingest_matrix.csv")
    a = h2.groupby(["policy", "ingest", "scen"])[[M1, "top_inst_admit_share", "starve_inst_rate", "max_denial_hours", "rej_rate_instw", "hhi_inst", "n_admit", "dropped_by_cooldown"]].mean()
    a.groupby(["policy", "ingest"]).mean().to_csv(f"{OUT}/H2_macro_by_ingest.csv")
    a.xs("S10_spam", level="scen").to_csv(f"{OUT}/H2_S10_by_ingest.csv")
    # ---- H3 capacity ----
    h3 = pd.read_csv(f"{C.ROOT}/results/heldout/H3_capacity_sweep.csv")
    c = h3.groupby(["policy", "K", "scen"])[[M1, "net_total", "idle_slot_hours", "full_frac", "hhi_inst", "top_inst_share", "starve_inst_rate", "net_per_busy_slot_hour", "occ_std"]].mean().groupby(["policy", "K"]).mean()
    c.to_csv(f"{OUT}/H3_macro_by_K.csv")
    ck = h3.groupby(["K", "scen", "policy"])[M1].mean().unstack("policy")
    gap = pd.DataFrame({"FIFO_to_best_impl_gap": ck[IMPL].max(1) - ck["FIFO"], "FIFO_to_screen_gap": ck["FIFO_SCREEN"] - ck["FIFO"],
                        "oracle_minus_best_impl": ck["ORACLE_GREEDY_UB"] - ck[IMPL].max(1)}).groupby("K").mean()
    gap.to_csv(f"{OUT}/H3_gaps_by_K.csv")
    # capacity paired bootstrap of best complex vs FIFO per K
    kr = []
    for K in (3, 4, 6, 10):
        sub = h3[h3.K == K]
        for p in ("SLOTHOUR", "UNCERTAINTY_LCB", "FIFO_SCREEN"):
            per_, mac = paired_boot(mat(sub, p), mat(sub, "FIFO"))
            kr.append(dict(K=K, policy=p, macro_diff_vs_FIFO=mac[0], lo=mac[1], hi=mac[2]))
    pd.DataFrame(kr).to_csv(f"{OUT}/H3_paired_vs_FIFO.csv", index=False)
    json.dump(res, open(f"{OUT}/H1_rules_and_verdict_machinery.json", "w"), indent=2, default=float)
    print(json.dumps(res, indent=1, default=float))

if __name__ == "__main__":
    main()
