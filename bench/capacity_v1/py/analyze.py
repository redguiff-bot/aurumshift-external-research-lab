"""Analysis.  Usage: python3 analyze.py validation|heldout|robust|failure   (writes results/*.json|csv)"""
import sys, json, os
import numpy as np, pandas as pd

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
CAPS = (3, 4, 6, 10)
rng = np.random.default_rng(20260929)


def boot_ci(x, n=2000):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 2: return (np.nan, np.nan)
    idx = rng.integers(0, len(x), (n, len(x)))
    m = x[idx].mean(1)
    return float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def paired(df, ref="FIFO", metric="lat_per_slot_hour", norm="dens0_sd"):
    key = ["family", "variant", "seed", "cap"]
    r = df[df.policy == ref].set_index(key)[[metric, norm]].rename(columns={metric: "ref", norm: "scale"})
    d = df[df.policy != ref].join(r, on=key)
    d["dz"] = (d[metric] - d.ref) / d.scale
    d["dabs"] = d[metric] - d.ref
    return d


def cell_table(d):
    """One row per (policy, family, cap): mean paired dz over variants x seeds, with bootstrap CI."""
    rows = []
    for (p, f, c), g in d.groupby(["policy", "family", "cap"]):
        lo, hi = boot_ci(g.dz.values, 500)
        rows.append(dict(policy=p, family=f, cap=c, dz=g.dz.mean(), lo=lo, hi=hi, dabs=g.dabs.mean(), n=len(g)))
    return pd.DataFrame(rows)


def summarise(df, ref="FIFO"):
    d = paired(df, ref)
    ct = cell_table(d)
    out = []
    for p, g in ct.groupby("policy"):
        allz = d[d.policy == p]
        # pooled: equal weight per (family,cap) cell -> mean of cell dz; CI by bootstrap over (variant,seed) blocks per cell
        pooled = g.dz.mean()
        # block bootstrap over seed-level pooled values (mean over cells within seed x variant)
        sv = allz.groupby(["family", "variant", "seed"]).dz.mean().values
        lo, hi = boot_ci(sv, 1000)
        out.append(dict(policy=p, pooled_dz=pooled, ci_lo=lo, ci_hi=hi,
                        frac_cells_pos=float((g.lo > 0).mean()), frac_cells_neg=float((g.hi < 0).mean()),
                        frac_cells_material_pos=float(((g.dz >= 0.15) & (g.lo > 0)).mean()),
                        frac_cells_material_neg=float(((g.dz <= -0.15) & (g.hi < 0)).mean()),
                        **{f"pooled_dz_cap{c}": g[g.cap == c].dz.mean() for c in CAPS}))
    return pd.DataFrame(out).sort_values("pooled_dz", ascending=False), ct


def main_table(df):
    """Absolute averages per policy (all metrics), equal weight per cell."""
    cols = ["lat_per_slot_hour", "real_per_slot_hour", "ret_to_risk", "utilisation", "hq_missed_frac", "hq_missed_capacity",
            "hhi_cluster", "starved_pos_inst", "mean_hold", "admit_per_slot_hour", "n_evict", "long_slot_hour_share", "pnl_day_sd", "max_drawdown",
            "spam_admit_share", "full_toggle_rate", "diag_thr_cv"]
    return df.groupby("policy")[cols].mean().sort_values("lat_per_slot_hour", ascending=False)


if __name__ == "__main__":
    phase = sys.argv[1]
    f = {"validation": "validation_raw.csv.gz", "heldout": "heldout_raw.csv.gz", "robust": "robustness_raw.csv.gz", "failure": "failure_raw.csv.gz"}[phase]
    df = pd.read_csv(f"{RES}/{f}")
    if phase in ("validation", "heldout"):
        s, ct = summarise(df)
        s.to_csv(f"{RES}/{phase}_summary_vs_FIFO.csv", index=False)
        ct.to_csv(f"{RES}/{phase}_cells_vs_FIFO.csv", index=False)
        s2, ct2 = summarise(df, "FIFO_NETPOS")
        s2.to_csv(f"{RES}/{phase}_summary_vs_FIFO_NETPOS.csv", index=False)
        main_table(df).to_csv(f"{RES}/{phase}_main_table.csv")
        pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
        print(s.round(3).to_string(index=False))
        print(s2.round(3).head(12).to_string(index=False))
