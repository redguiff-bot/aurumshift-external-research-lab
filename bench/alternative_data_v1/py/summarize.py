"""Apply the pre-declared classification rules and write results/candidate_summary.csv + results/summary.json"""
import os, json, numpy as np, pandas as pd
from analysis_crypto import bh
RES = os.path.join(os.path.dirname(__file__), "..", "results")
R = pd.read_csv(os.path.join(RES, "incremental_results.csv"))
P = R[(R.sens == "primary") & R.p_incr.notna()].copy()
fam = P[~P.cand.str.contains("CONTROL_noise|CONTROL_price|mvrv")].copy()      # DVOL stays in the family (it is counted as a candidate)
fam["q_fam"] = bh(fam.p_incr.values); P = P.merge(fam[["cand", "asset", "target", "q_fam"]], on=["cand", "asset", "target"], how="left")
P["pass"] = (P.p_incr < 0.05) & (P.q_fam < 0.10) & (P.oos_gain_pct > 0) & (P.dm_p_onesided < 0.10) & (P.sign_cos > 0) & (P.react_ctmp < 0.40)
rows = []
for c, g in P.groupby("cand"):
    us = g[g.p_univ < 0.05]
    subsumed = len(us) > 0 and (us.p_incr >= 0.10).all()
    react = g.react_ctmp.max()
    if g["pass"].any(): cl = "INCREMENTAL_CANDIDATE"
    elif react >= 0.40 or subsumed: cl = "PRICE_DERIVATIVE_ONLY"
    else: cl = "INDEPENDENT_NO_EVIDENCE"
    best = g.sort_values("p_incr").iloc[0]
    rows.append(dict(cand=c, klass=cl, n_tests=len(g), n_p05=int((g.p_incr < 0.05).sum()), min_p_incr=g.p_incr.min(), min_q_fam=g.q_fam.min(), best_target=f"{best.asset}:{best.target}",
                     best_oos_gain_pct=best.oos_gain_pct, best_dm_p=best.dm_p_onesided, max_oos_gain_pct=g.oos_gain_pct.max(), react_ctmp_max=react, react_past_max=g.react_past.max(),
                     red_base_max=g.red_base.max(), n_univ_sig=len(us), subsumed=bool(subsumed), n_pass=int(g["pass"].sum())))
S = pd.DataFrame(rows).sort_values(["klass", "min_p_incr"]); S.to_csv(os.path.join(RES, "candidate_summary.csv"), index=False)
noise = P[P.cand.str.contains("noise")]
info = dict(n_tests_primary=int(len(fam)), n_p05_family=int((fam.p_incr < 0.05).sum()), n_p05_expected_under_null=round(0.05 * len(fam), 1),
            min_q_family_excl_dvol=float(bh(fam[~fam.cand.str.contains("deribit")].p_incr.values).min()),
            noise_tests=int(len(noise)), noise_p05=int((noise.p_incr < 0.05).sum()), noise_dm_p10=int((noise.dm_p_onesided < 0.10).sum()),
            classes=S.klass.value_counts().to_dict())
nc = pd.read_csv(os.path.join(RES, "incremental_results_no_calendar.csv")); nc = nc[(nc.sens == "primary") & nc.p_incr.notna() & ~nc.cand.str.contains("CONTROL")]
info["no_calendar_baseline"] = dict(n_p05=int((nc.p_incr < 0.05).sum()), n_tests=int(len(nc)), n_p001=int((nc.p_incr < 0.001).sum()), n_oos_dm_p10=int((nc.dm_p_onesided < 0.10).sum()),
                                    npm_range_gain_pct=nc[nc.cand.str.startswith("npm") & (nc.target == "lrange")][["cand", "asset", "oos_gain_pct", "dm_p_onesided", "p_incr"]].round(4).to_dict("records"))
json.dump(info, open(os.path.join(RES, "summary.json"), "w"), indent=1, default=float)
pd.set_option("display.width", 250)
print(S.round(3).to_string()); print(json.dumps(info, indent=1, default=float))
