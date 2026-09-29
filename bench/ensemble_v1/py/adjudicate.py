"""PRE-REGISTERED adjudication (rules fixed in reports/014_strategy_ensemble/03_PROTOCOL.md BEFORE the held-out run).
Reads results/heldout_raw.csv.gz, results/blocks_*.npz, results/tuning_table.csv; writes results/adjudication.json and results/summary_tables.md."""
import os, json, numpy as np, pandas as pd
from scipy import stats
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results")
DELTA, DELTA_R = 0.05, 0.15
BASE = ["EQUAL", "STATIC", "WTA", "EWMA"]
CORE = ["SLEEP_HEDGE", "EG", "BMA", "SLEEP_FLOOR"]           # plain sleeping/specialist multiplicative weights
TRACK = ["FIXED_SHARE", "DISC_AWAKE", "MPP"]                  # sleeping + tracking / memory
FAMS = {"core": CORE, "tracking": TRACK, "context": ["CONTEXT_MIX"], "diversity": ["DIVERSITY"]}
CAND = CORE + TRACK + ["CONTEXT_MIX", "DIVERSITY", "DISC_CLOCK", "HEDGE_CUM"]
BAND = ["EXP3", "EPS_GREEDY"]
ABL = ["EWMA_INACTIVE_NEG", "EWMA_MISSING_NEG", "SLEEP_INACTIVE_NEG", "SLEEP_MISSING_NEG", "EG_NOMASS", "SLEEP_NOMASS"]

df = pd.read_csv(os.path.join(RES, "heldout_raw.csv.gz")); df = df[df.cfg.isin(["tuned", "tuned+ablation", "{}"])]
SC = sorted(df.scenario.unique()); NBLK = 100
def piv(col): return df.pivot_table(index=["scenario", "seed"], columns="method", values=col)
mse = piv("mse")
def nrm_seed(col="mse", eq="EQUAL"):
    m = piv(col); den = (m[eq] - m["ORACLE"]).replace(0, np.nan); return m.sub(m["ORACLE"], axis=0).div(den, axis=0)
N = nrm_seed()                                     # per-seed nrm (ratio of means is used for aggregation below)
def agg_nrm(col="mse"):
    m = piv(col).groupby("scenario").mean(); return m.sub(m["ORACLE"], axis=0).div((m["EQUAL"] - m["ORACLE"]), axis=0).drop(columns="ORACLE")
NR = agg_nrm()
def paired(scen, a, b, col="mse"):
    """paired seed difference of squared error to truth, normalised by the scenario equal-oracle span; returns mean, ci95"""
    m = piv(col).loc[scen]; span = (m["EQUAL"] - m["ORACLE"]).mean(); d = (m[a] - m[b]) / span
    mu = d.mean(); se = d.std(ddof=1) / np.sqrt(len(d)); h = stats.t.ppf(0.975, len(d) - 1) * se; return float(mu), float(mu - h), float(mu + h)

allm = BASE + CAND; best_s = NR[allm].min(1)
out = {"delta": DELTA, "delta_R": DELTA_R, "nrm_by_scenario": NR.round(3).to_dict("index")}
rows = []
for m in allm + BAND + ABL:
    if m not in NR: continue
    gap = (NR[m] - best_s).max(); worse_eq = [s for s in SC if NR.loc[s, m] > 1 and paired(s, m, "EQUAL")[1] > 0]
    rows.append(dict(method=m, mean_nrm=NR[m].mean(), median_nrm=NR[m].median(), worst_nrm=NR[m].max(), worst_gap_to_best=gap if m in allm else np.nan, worse_than_equal=";".join(worse_eq)))
S = pd.DataFrame(rows).set_index("method")

# -------- gates ---------------------------------------------------------------------------------------------------
def blk(scen, meth): z = np.load(os.path.join(RES, f"blocks_{scen}.npz")); return z[f"{meth}__e"], z[f"{meth}__w"].astype(float)
def win_nrm(scen, meth, a, b):     # normalised excess in blocks [a,b) per seed
    e, _ = blk(scen, meth); eo, _ = blk(scen, "ORACLE"); eq, _ = blk(scen, "EQUAL")
    return ((e[:, a:b].mean(1) - eo[:, a:b].mean(1)) / np.maximum(eq[:, a:b].mean(1) - eo[:, a:b].mean(1), 1e-12))
G = {}
for m in allm:
    g = {}
    # G_new: new good expert takes >=50% of oracle share by half+250 (S4a) and does not cost more than equal weights when bad (S4b)
    r = df[(df.scenario == "S4a_NEW_GOOD")]; sh = r[r.method == m].share8_250.mean(); so = r[r.method == "ORACLE"].share8_250.mean()
    g["new_share_ratio"] = float(sh / so); g["G_new"] = bool(sh >= 0.5 * so and NR.loc["S4b_NEW_BAD", m] <= 1.0)
    # G_rare: later occurrences of the rare regime recover >=50% of the equal->oracle span and specialist holds >=50% of oracle share
    R = df[df.scenario == "S8_RARE_SPECIALIST"]; mm = R.groupby("method")[["mse_rare_late", "spec5_share_rare_late"]].mean()
    nr = (mm.loc[m, "mse_rare_late"] - mm.loc["ORACLE", "mse_rare_late"]) / (mm.loc["EQUAL", "mse_rare_late"] - mm.loc["ORACLE", "mse_rare_late"])
    g["rare_nrm"] = float(nr); g["rare_share_ratio"] = float(mm.loc[m, "spec5_share_rare_late"] / mm.loc["ORACLE", "spec5_share_rare_late"])
    g["G_rare"] = bool(nr <= 0.5 and g["rare_share_ratio"] >= 0.5)
    # G_under (S7): after the window, excess returns to <= pre-window level + 0.15 span within 300 rounds (6 blocks)
    pre = win_nrm("S7_TEMP_UNDERPERF", m, 30, 40).mean(); post = win_nrm("S7_TEMP_UNDERPERF", m, 60, 66).mean()
    g["under_pre"], g["under_post"] = float(pre), float(post); g["G_under"] = bool(post - pre <= 0.15)
    # G_dorm: S9 post-gap vs pre-gap (blocks) ; S3 re-entry nrm
    g0, g1 = int(1666 / 50), int(2916 / 50)
    pre = win_nrm("S9_LONG_GAP", m, g0 - 10, g0).mean(); post = win_nrm("S9_LONG_GAP", m, g1, g1 + 6).mean()
    g["dorm_pre"], g["dorm_post"] = float(pre), float(post)
    S3 = df[df.scenario == "S3_RECURRENCE"].groupby("method")[["mse_re_m"]].mean()
    g["reentry_nrm"] = float((S3.loc[m, "mse_re_m"] - S3.loc["ORACLE", "mse_re_m"]) / (S3.loc["EQUAL", "mse_re_m"] - S3.loc["ORACLE", "mse_re_m"]))
    g["G_dorm"] = bool(post - pre <= 0.15 and g["reentry_nrm"] <= 0.6)
    g["G_noworse"] = bool(S.loc[m, "worse_than_equal"] == "")
    g["gap_ok"] = bool(S.loc[m, "worst_gap_to_best"] <= DELTA_R)
    g["ROBUST"] = bool(all(g[k] for k in ["G_new", "G_rare", "G_under", "G_dorm", "G_noworse", "gap_ok"]))
    G[m] = g
GD = pd.DataFrame(G).T; S = S.join(GD)

# -------- semantic ablations (paired) ---------------------------------------------------------------------------------
sem = {}
for a, b in [("EWMA_INACTIVE_NEG", "EWMA"), ("EWMA_MISSING_NEG", "EWMA"), ("SLEEP_INACTIVE_NEG", "SLEEP_HEDGE"), ("SLEEP_MISSING_NEG", "SLEEP_HEDGE"),
             ("EG_NOMASS", "EG"), ("SLEEP_NOMASS", "SLEEP_HEDGE")]:
    sem[a] = {s: paired(s, a, b) for s in SC}                      # positive = ablation harms
out["semantic_ablation_paired_delta_nrm(mean,lo,hi)"] = sem
# -------- verdict tree --------------------------------------------------------------------------------------------------
tun = pd.read_csv(os.path.join(RES, "tuning_table.csv")); tb = tun.groupby("method")["mean"].min()
common = [m for m in allm if m in tb.index]; rho = stats.spearmanr(tb[common], NR.mean()[common])[0]
Rset = [m for m in allm if G[m]["ROBUST"]]; Rc = [m for m in Rset if m in CAND and m != "HEDGE_CUM"]; Rb = [m for m in Rset if m in BASE]
def fam(m): return next((f for f, v in FAMS.items() if m in v), "other")
needed = {}
for f, ms in FAMS.items():
    others = [m for m in allm if m not in ms]; hit = []
    for s in SC:
        fb = NR.loc[s, ms].idxmin(); ob = NR.loc[s, others].idxmin()
        mu, lo, hi = paired(s, fb, ob)
        if hi < -DELTA: hit.append(s)
    needed[f] = hit
best_base = NR[BASE].mean().idxmin(); best_c = NR[CAND].mean().idxmin()
if rho < 0.6: verdict = "STUDY_INCONCLUSIVE"
elif not Rset: verdict = "NO_ROBUST_ENSEMBLE_METHOD"
elif not Rc or (Rb and NR.mean()[best_base] - NR.mean()[Rc].min() <= DELTA): verdict = "STATIC_OR_EWMA_SUFFICIENT"
else:
    mstar = NR.mean()[Rc].idxmin(); core_R = [m for m in CORE if m in Rc]; gap_star = S.loc[mstar, "worst_gap_to_best"]
    if core_R and NR.mean()[core_R].min() - NR.mean()[mstar] <= DELTA and (gap_star <= DELTA or sum(1 for f in FAMS if needed[f]) < 2): verdict = "SLEEPING_EXPERT_REFERENCE_SUPPORTED"
    elif sum(1 for f in FAMS if needed[f]) >= 2: verdict = "MULTIPLE_ENSEMBLE_METHODS_SUPPORTED"
    else: verdict = "SLEEPING_EXPERT_REFERENCE_SUPPORTED"
out.update(dict(spearman_tuning_vs_heldout=float(rho), robust_set=Rset, families_needed=needed, best_baseline=best_base, best_candidate=best_c, verdict=verdict))
out["mean_nrm"] = NR.mean().round(3).to_dict()
json.dump(out, open(os.path.join(RES, "adjudication.json"), "w"), indent=1, default=float)
with open(os.path.join(RES, "summary_tables.md"), "w") as f:
    f.write("## nrm by scenario (0 = oracle, 1 = equal weights; lower better)\n\n" + NR.round(2).T.to_markdown() + "\n\n## method summary and gates\n\n" + S.round(3).to_markdown() + "\n")
print(S.round(3).to_string()); print(json.dumps({k: out[k] for k in ["spearman_tuning_vs_heldout", "robust_set", "families_needed", "best_baseline", "best_candidate", "verdict"]}, indent=1))
