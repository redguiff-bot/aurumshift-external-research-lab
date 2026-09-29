"""Supplementary (descriptive) analyses on the held-out run. Anything here that re-reads the pre-registered gates is labelled POST-HOC."""
import os, json, numpy as np, pandas as pd
from scipy import stats
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results")
df = pd.read_csv(os.path.join(RES, "heldout_raw.csv.gz")); df = df[df.cfg.isin(["tuned", "tuned+ablation", "{}"])]
SC = sorted(df.scenario.unique()); out = {}
def pv(col): return df.pivot_table(index=["scenario", "seed"], columns="method", values=col)
M = pv("mse")
def paired(s, a, b):
    m = M.loc[s]; span = (m["EQUAL"] - m["ORACLE"]).mean(); d = (m[a] - m[b]) / span; mu = d.mean(); h = stats.t.ppf(.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d)); return round(float(mu), 3), round(float(mu - h), 3), round(float(mu + h), 3)
for a, b in [("EG", "EWMA"), ("FIXED_SHARE", "EWMA"), ("SLEEP_HEDGE", "EWMA"), ("SLEEP_HEDGE", "EQUAL"), ("EG", "SLEEP_HEDGE"), ("FIXED_SHARE", "SLEEP_HEDGE"), ("DIVERSITY", "FIXED_SHARE"), ("CONTEXT_MIX", "EWMA")]:
    r = {s: paired(s, a, b) for s in SC}
    out[f"{a}_minus_{b}"] = dict(per_scenario=r, better=[s for s, x in r.items() if x[2] < 0], worse=[s for s, x in r.items() if x[1] > 0], mean_of_scenarios=round(float(np.mean([x[0] for x in r.values()])), 3))
# concentration / diversity in S6 and elsewhere
g = df.groupby(["scenario", "method"])[["cluster_share", "eff_n", "max_w"]].mean()
out["S6_concentration"] = {m: g.loc[("S6_CORRELATED", m)].round(3).to_dict() for m in ["EQUAL", "EWMA", "SLEEP_HEDGE", "EG", "FIXED_SHARE", "DIVERSITY", "CONTEXT_MIX", "ORACLE", "WTA"]}
out["S6_cluster_share_second_half_note"] = "cluster (experts 1,2,8,9) is good in the first half (sd 0.6) and bad in the second (sd 1.6); ORACLE cluster share is the reference"
# starvation summary
sv = df.groupby(["scenario", "method"])[["share8_250", "share8_450", "spec5_share_rare_late", "mse_rare_early", "mse_rare_late", "mse_re_m", "mse_pre_m"]].mean()
out["S4a_share8"] = {m: sv.loc[("S4a_NEW_GOOD", m)][["share8_250", "share8_450"]].round(3).to_dict() for m in ["ORACLE", "EQUAL", "EWMA", "SLEEP_HEDGE", "EG", "FIXED_SHARE", "MPP", "DISC_AWAKE", "CONTEXT_MIX", "WTA"]}
out["S8_rare"] = {m: sv.loc[("S8_RARE_SPECIALIST", m)][["spec5_share_rare_late", "mse_rare_early", "mse_rare_late"]].round(4).to_dict() for m in ["ORACLE", "EQUAL", "EWMA", "SLEEP_HEDGE", "EG", "FIXED_SHARE", "MPP", "DISC_AWAKE", "CONTEXT_MIX", "WTA"]}
# S7 time to recover / S9 (blocks of 50 rounds)
def blk(s, m): z = np.load(os.path.join(RES, f"blocks_{s}.npz")); return z[f"{m}__e"]
def ttr(scen, m, pre, start, post_max, tol=0.15):
    e, eo, eq = blk(scen, m), blk(scen, "ORACLE"), blk(scen, "EQUAL"); nr = (e - eo) / np.maximum(eq - eo, 1e-12)   # (S,nb) per-block
    base = nr[:, pre[0]:pre[1]].mean(1); res = []
    sm = np.stack([nr[:, i:i + 3].mean(1) for i in range(nr.shape[1] - 2)], 1)   # 150-round smoothing
    for s in range(nr.shape[0]):
        ok = np.flatnonzero(sm[s, start:start + post_max] <= base[s] + tol); res.append(int(ok[0]) * 50 if len(ok) else post_max * 50)
    return dict(median_rounds=float(np.median(res)), frac_never=float(np.mean(np.array(res) >= post_max * 50)))
out["S7_time_to_recover"] = {m: ttr("S7_TEMP_UNDERPERF", m, (30, 40), 60, 30) for m in ["EWMA", "SLEEP_HEDGE", "EG", "FIXED_SHARE", "MPP", "DISC_AWAKE", "HEDGE_CUM"]}
out["S9_time_to_recover"] = {m: ttr("S9_LONG_GAP", m, (23, 33), 58, 30) for m in ["EWMA", "SLEEP_HEDGE", "EG", "FIXED_SHARE", "MPP", "DISC_AWAKE", "DISC_CLOCK", "HEDGE_CUM"]}
# POST-HOC sensitivity of the verdict rules (NOT the verdict): who passes with relaxed thresholds
a = json.load(open(os.path.join(RES, "adjudication.json"))); NR = pd.DataFrame(a["nrm_by_scenario"]).T
allm = ["EQUAL", "STATIC", "WTA", "EWMA", "HEDGE_CUM", "SLEEP_HEDGE", "EG", "BMA", "SLEEP_FLOOR", "FIXED_SHARE", "DISC_AWAKE", "DISC_CLOCK", "MPP", "CONTEXT_MIX", "DIVERSITY"]
best = NR[allm].min(axis=1); gap = (NR[allm].sub(best, axis=0)).max()
out["posthoc_worst_gap"] = gap.round(3).to_dict(); out["posthoc_mean_nrm"] = NR[allm].mean().round(3).sort_values().to_dict()
out["posthoc_rank_by_mean"] = list(NR[allm].mean().sort_values().index)
json.dump(out, open(os.path.join(RES, "extras.json"), "w"), indent=1)
print(json.dumps(out, indent=1)[:9000])
