"""Build markdown tables for the reports from raw result CSVs.  Usage: python3 report_tables.py heldout|robust|failure"""
import sys, os, json
import numpy as np, pandas as pd

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
TAB = os.path.join(RES, "tables"); os.makedirs(TAB, exist_ok=True)
rng = np.random.default_rng(7)
KEY = ["family", "variant", "seed", "cap"]


def ci(x, n=2000):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 3: return (np.nan, np.nan)
    m = x[rng.integers(0, len(x), (n, len(x)))].mean(1)
    return float(np.quantile(m, .025)), float(np.quantile(m, .975))


def md(df, floatfmt=3):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind == "f": df[c] = df[c].map(lambda v: "" if pd.isna(v) else f"{v:.{floatfmt}f}")
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "|".join(["---"] * len(df.columns)) + "|\n"
    return head + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in df.values) + "\n"


def wide(df, metric):
    return df.pivot_table(index=KEY, columns="policy", values=metric)


def delta(df, a, b, metric, scale=True, by=None, mask=None):
    W = wide(df, metric)
    d = W[a] - W[b]
    if scale:
        d = d / df[df.policy == "FIFO"].set_index(KEY)["dens0_rms"]
    d = d.reset_index(name="d")
    if mask is not None: d = d[mask(d)]
    return d


def summarize(d, by=None):
    blk = d.groupby(["family", "variant", "seed"]).d.mean().values
    lo, hi = ci(blk)
    return blk.mean(), lo, hi


def heldout():
    df = pd.read_csv(f"{RES}/heldout_raw.csv.gz")
    val = json.load(open(f"{RES}/heldout_verdict.json"))
    pols = [p for p in df.policy.unique()]
    order = df.groupby("policy").lat_per_slot_hour.mean().sort_values(ascending=False).index.tolist()
    # ---- T1 main: pooled dz vs FIFO / RANK_NET / FIFO_NETPOS
    rows = []
    for p in order:
        r = dict(policy=p)
        for ref, nm in (("FIFO", "vs FIFO"), ("FIFO_NETPOS", "vs FIFO_NETPOS"), ("RANK_NET", "vs RANK_NET")):
            if p == ref: r[nm] = np.nan; continue
            m, lo, hi = summarize(delta(df, p, ref, "lat_per_slot_hour"))
            r[nm] = f"{m:+.3f} [{lo:+.3f},{hi:+.3f}]"
        rows.append(r)
    t1 = pd.DataFrame(rows)
    open(f"{TAB}/heldout_pooled_dz.md", "w").write(md(t1))
    # ---- T2 slot economics (absolute, mean over all held-out cells)
    cols = ["lat_per_slot_hour", "real_per_slot_hour", "lat_per_used_hour", "utilisation", "idle", "mean_hold", "admit_per_slot_hour",
            "v0_admitted_mean", "v0_rejected_mean", "hq_missed_frac", "hq_missed_capacity", "hq_declined_with_free_slot",
            "opp_cost_missed_value_per_slot_hour", "evals_per_opp"]
    t2 = df.groupby("policy")[cols].mean().loc[order].reset_index()
    open(f"{TAB}/heldout_slot_economics.md", "w").write(md(t2))
    # regret vs LP bound (per slot-hour)
    df["regret_lp"] = df.lp_bound - df.lat_per_slot_hour
    rg = df.pivot_table(index="policy", columns="cap", values="regret_lp").loc[order].reset_index()
    open(f"{TAB}/heldout_regret_vs_lp.md", "w").write(md(rg))
    lp = df[df.policy == "FIFO"].groupby("cap").lp_bound.mean()
    # capture ratio of LP bound
    cap_rows = []
    for p in ["FIFO", "FIFO_NETPOS", "RANK_NET", "COMPOSED", "SHADOW_PRICE", "ONLINE_KNAPSACK_PSI", "ORACLE_DENSITY_NOT_IMPLEMENTABLE"]:
        for c in (3, 4, 6, 10):
            g = df[(df.policy == p) & (df.cap == c)]
            cap_rows.append(dict(policy=p, cap=c, lat_per_slot_hour=g.lat_per_slot_hour.mean(), real_per_slot_hour=g.real_per_slot_hour.mean(),
                                 utilisation=g.utilisation.mean(), hq_missed_frac=g.hq_missed_frac.mean(), lp_bound=g.lp_bound.mean(),
                                 capture_of_lp=g.lat_per_slot_hour.mean() / g.lp_bound.mean()))
    open(f"{TAB}/heldout_capacity_sensitivity.md", "w").write(md(pd.DataFrame(cap_rows)))
    # capacity: pooled dz per cap w/ CI for key policies
    rows = []
    for p in ["FIFO_NETPOS", "RANK_NET", "COMPOSED", "SHADOW_PRICE", "ONLINE_KNAPSACK_PSI", "FLUID_QUANTILE", "EQUAL_QUOTA", "ROUND_ROBIN", "RANDOM_SEEDED"]:
        r = dict(policy=p)
        for c in (3, 4, 6, 10):
            m, lo, hi = summarize(delta(df, p, "FIFO", "lat_per_slot_hour", mask=lambda d, c=c: d.cap == c))
            r[f"cap{c} dz vs FIFO"] = f"{m:+.3f} [{lo:+.3f},{hi:+.3f}]"
        rows.append(r)
    open(f"{TAB}/heldout_capacity_dz.md", "w").write(md(pd.DataFrame(rows)))
    # ---- T3 per-family dz vs FIFO for key policies (caps pooled) and vs RANK_NET
    fams = sorted(df.family.unique()); rows = []
    for f in fams:
        d = df[df.family == f]
        r = dict(family=f)
        for p in ["FIFO_NETPOS", "RANK_NET", "COMPOSED", "SHADOW_PRICE", "ONLINE_KNAPSACK_PSI", "MARGINAL_RISK", "LINUCB", "SLEEPING_HEDGE", "ORACLE_DENSITY_NOT_IMPLEMENTABLE"]:
            r[p] = delta(d, p, "FIFO", "lat_per_slot_hour").d.mean()
        r["COMPOSED-RANK_NET"] = delta(d, "COMPOSED", "RANK_NET", "lat_per_slot_hour").d.mean()
        rows.append(r)
    open(f"{TAB}/heldout_family_dz.md", "w").write(md(pd.DataFrame(rows)))
    # ---- FIFO detail: regret, concentration, hq-missed, efficiency per family
    rows = []
    for f in fams:
        d = df[(df.family == f) & df.cap.isin([4, 6])]
        for p in ["FIFO", "RANK_NET", "COMPOSED"]:
            g = d[d.policy == p]
            rows.append(dict(family=f, policy=p, regret_lp=g.lp_bound.mean() - g.lat_per_slot_hour.mean(), hq_missed_frac=g.hq_missed_frac.mean(),
                             hq_missed_capacity=g.hq_missed_capacity.mean(), hhi_cluster=g.hhi_cluster.mean(), lat_per_slot_hour=g.lat_per_slot_hour.mean(),
                             utilisation=g.utilisation.mean(), mean_hold=g.mean_hold.mean()))
    open(f"{TAB}/heldout_fifo_detail_cap46.md", "w").write(md(pd.DataFrame(rows)))
    # ---- T4 diversification vs RANK_NET
    rows = []
    for p in ["CLUSTER_CAP", "CORR_PENALTY", "MARGINAL_RISK", "CORR_HARD_REJECT", "COMPOSED"]:
        for grp, mask in (("all", lambda d: d.family != ""), ("corr families S5/H1", lambda d: d.family.isin(["S5_correlated", "H1_chronic_corr_regime"]))):
            r = dict(policy=p, families=grp)
            for m_, nm, sc in (("lat_per_slot_hour", "d_lat_dz", True), ("ret_to_risk", "d_ret_to_risk", False), ("pnl_day_sd", "d_pnl_day_sd", False),
                               ("max_drawdown", "d_max_dd", False), ("hhi_cluster", "d_hhi", False), ("hq_missed_frac", "d_hq_missed", False)):
                d = delta(df, p, "RANK_NET", m_, scale=sc, mask=mask)
                mm, lo, hi = summarize(d)
                r[nm] = f"{mm:+.4f} [{lo:+.4f},{hi:+.4f}]"
            rows.append(r)
    open(f"{TAB}/heldout_diversification.md", "w").write(md(pd.DataFrame(rows)))
    # absolute diversification metrics on correlated families
    dd = df[df.family.isin(["S5_correlated", "H1_chronic_corr_regime"]) & df.cap.isin([4, 6])]
    t = dd.groupby("policy")[["lat_per_slot_hour", "ret_to_risk", "pnl_day_sd", "max_drawdown", "hhi_cluster", "eff_clusters", "max_cluster_share", "hq_missed_frac"]].mean().loc[
        [p for p in order if p in dd.policy.unique()]].reset_index()
    open(f"{TAB}/heldout_diversification_abs_corrfam_cap46.md", "w").write(md(t))
    # ---- T5 turnover vs RANK_NET
    rows = []
    for p in ["SLOTHOUR_DENSITY", "SLOTHOUR_HAZARD", "SHADOW_PRICE", "FLUID_QUANTILE", "ONLINE_KNAPSACK_PSI", "TRUNK_RESERVATION", "EVICT_SWAP", "OLDEST_SLOT"]:
        r = dict(policy=p)
        for m_, nm, sc in (("lat_per_slot_hour", "d_lat_dz", True), ("n_evict", "d_n_evict", False), ("admit_per_slot_hour", "d_admit_per_slot_hour", False),
                           ("mean_hold", "d_mean_hold", False), ("utilisation", "d_utilisation", False)):
            mm, lo, hi = summarize(delta(df, p, "RANK_NET", m_, scale=sc))
            r[nm] = f"{mm:+.4f} [{lo:+.4f},{hi:+.4f}]"
        rows.append(r)
    open(f"{TAB}/heldout_turnover.md", "w").write(md(pd.DataFrame(rows)))
    # S6 by variant (short vs long)
    s6 = df[df.family == "S6_short_vs_long"]
    rows = []
    for v in sorted(s6.variant.unique()):
        g = s6[s6.variant == v]
        r = dict(variant=v)
        for p in ["FIFO", "FIFO_NETPOS", "RANK_NET", "SLOTHOUR_DENSITY", "SHADOW_PRICE", "COMPOSED", "ORACLE_DENSITY_NOT_IMPLEMENTABLE"]:
            r[p] = g[g.policy == p].lat_per_slot_hour.mean()
        r["RANK_NET long_slot_hour_share"] = g[g.policy == "RANK_NET"].long_slot_hour_share.mean()
        r["SLOTHOUR_DENSITY long_slot_hour_share"] = g[g.policy == "SLOTHOUR_DENSITY"].long_slot_hour_share.mean()
        rows.append(r)
    open(f"{TAB}/heldout_s6_variants.md", "w").write(md(pd.DataFrame(rows)))
    # ---- T6 failure-mode metrics on heldout
    fm = df[df.cap.isin([4, 6])].groupby("policy")[["starved_pos_inst", "starved_inst", "min_admit_ratio", "inst_admit_share_max", "spam_admit_share",
                                                    "long_slot_hour_share", "long_admit_share", "short_admit_share", "full_toggle_rate", "occ_abs_change",
                                                    "diag_thr_cv", "diag_thr_flip", "n_evict"]].mean().loc[order].reset_index()
    open(f"{TAB}/heldout_failure_metrics_cap46.md", "w").write(md(fm))
    s10 = df[df.family.isin(["S10_spam", "H3_spam_fastslow"]) & df.cap.isin([4, 6])].groupby("policy")[["spam_admit_share", "spam_opp_share", "lat_per_slot_hour", "starved_pos_inst", "hhi_cluster"]].mean().loc[
        [p for p in order if p in df.policy.unique()]].reset_index()
    open(f"{TAB}/heldout_spam.md", "w").write(md(s10))
    # ---- T7 baselines
    b = df[df.policy.isin(["FIFO", "ROUND_ROBIN", "RANDOM_SEEDED", "EQUAL_QUOTA", "OLDEST_SLOT", "FIFO_NETPOS"])].groupby("policy")[
        ["lat_per_slot_hour", "real_per_slot_hour", "utilisation", "hq_missed_frac", "hhi_cluster", "starved_pos_inst", "n_evict", "mean_hold", "ret_to_risk"]].mean().reset_index()
    open(f"{TAB}/heldout_baselines.md", "w").write(md(b))
    # regime lag on S7/H1: lat by quarter
    q = df[df.family.isin(["S7_regime_shift", "H1_chronic_corr_regime"]) & df.cap.isin([4, 6])].groupby("policy")[["lat_q0", "lat_q1", "lat_q2", "lat_q3"]].mean().loc[
        [p for p in order if p in df.policy.unique()]].reset_index()
    open(f"{TAB}/heldout_regime_quarters.md", "w").write(md(q))
    print("ok heldout tables")


def sweep(name, raw, axis_col):
    df = pd.read_csv(f"{RES}/{raw}")
    rows = []
    for (ax, lv), g in df.groupby(["axis", "level"]):
        r = dict(axis=ax, level=lv)
        for p in ["FIFO", "FIFO_NETPOS", "RANK_NET", "COMPOSED", "SHADOW_PRICE", "ONLINE_KNAPSACK_PSI", "MARGINAL_RISK", "CLUSTER_CAP", "LINUCB", "SLEEPING_HEDGE", "EVICT_SWAP", "OLDEST_SLOT", "RANK_NET_UNKCOST_ZERO"]:
            r[p] = g[g.policy == p].lat_per_slot_hour.mean()
        r["COMPOSED-RANK_NET"] = r["COMPOSED"] - r["RANK_NET"]
        r["RANK_NET-FIFO"] = r["RANK_NET"] - r["FIFO"]
        r["FIFO_NETPOS-FIFO"] = r["FIFO_NETPOS"] - r["FIFO"]
        r["best_impl"] = g[~g.policy.str.contains("ORACLE")].groupby("policy").lat_per_slot_hour.mean().idxmax()
        rows.append(r)
    t = pd.DataFrame(rows)
    open(f"{TAB}/{name}_sweep_lat_per_slot_hour.md", "w").write(md(t))
    t.to_csv(f"{TAB}/{name}_sweep.csv", index=False)
    return df


def robust():
    sweep("robust", "robustness_raw.csv.gz", "axis")
    print("ok robust")


def failure():
    df = sweep("failure", "failure_raw.csv.gz", "axis")
    rows = []
    for (ax, lv), g in df[df.cap == 4].groupby(["axis", "level"]):
        for p in ["FIFO", "RANK_NET", "COMPOSED", "SHADOW_PRICE", "ONLINE_KNAPSACK_PSI", "MARGINAL_RISK", "CLUSTER_CAP", "EQUAL_QUOTA", "LINUCB", "SLEEPING_HEDGE"]:
            x = g[g.policy == p]
            rows.append(dict(axis=ax, level=lv, policy=p, lat=x.lat_per_slot_hour.mean(), spam_admit_share=x.spam_admit_share.mean(),
                             starved_pos_inst=x.starved_pos_inst.mean(), hhi=x.hhi_cluster.mean(), long_slot_share=x.long_slot_hour_share.mean(),
                             pnl_day_sd=x.pnl_day_sd.mean(), max_dd=x.max_drawdown.mean(), thr_cv=x.diag_thr_cv.mean(), toggle=x.full_toggle_rate.mean(),
                             lat_q0=x.lat_q0.mean(), lat_q1=x.lat_q1.mean(), lat_q2=x.lat_q2.mean(), lat_q3=x.lat_q3.mean()))
    open(f"{TAB}/failure_detail_cap4.md", "w").write(md(pd.DataFrame(rows)))
    print("ok failure")


if __name__ == "__main__":
    globals()[sys.argv[1]]()
