"""Mechanical adjudication from stored results (protocol §10). Writes results/FINAL.json and results/tables/*.md"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from fd import causal, expr as E

RES = os.path.join(os.path.dirname(__file__), "..", "results"); TAB = os.path.join(RES, "tables"); os.makedirs(TAB, exist_ok=True)
ho = json.load(open(os.path.join(RES, "heldout_results.json")))
disc = json.load(open(os.path.join(RES, "discovery_train_val.json")))
dia = json.load(open(os.path.join(RES, "diagnostics_train_val.json")))
arena = json.load(open(os.path.join(RES, "synthetic_arena_final.json")))
fz = {c["id"] + "_" + t: (t, c) for t in ("y_ret", "y_vol") for c in disc[t]["frozen"]}
recs = ho["records"]


def md(rows, head):
    s = "| " + " | ".join(head) + " |\n|" + "|".join("---" for _ in head) + "|\n"
    return s + "\n".join("| " + " | ".join(str(x) for x in r) + " |" for r in rows) + "\n"


# arena validity
Rn = [r for r in arena if r["scn"] == "NULL"]; Rm = [r for r in arena if r["scn"] == "MIXED"]
fwer = float(np.mean([r["n_stable"] > 0 for r in Rn])); pow_c1 = float(np.mean([r["c1_main_recovered"] for r in Rm]))
arena_valid = bool(fwer <= 0.10 and pow_c1 >= 0.80)
arena_sum = dict(reps_null=len(Rn), reps_mixed=len(Rm), fwer_null=fwer, frozen_any_null=float(np.mean([r["n_frozen"] > 0 for r in Rn])),
                 false_mains_null=float(np.mean([len(r["false_mains"]) > 0 for r in Rn])),
                 power_c1_main=pow_c1, power_c2_interaction=float(np.mean(["c2_interaction" in r["recovered"] for r in Rm])),
                 power_c3_square=float(np.mean(["c3_square" in r["recovered"] for r in Rm])),
                 c4_market_specific_stable=float(np.mean(["c4_market_specific" in r["nonpersistent_stable"] for r in Rm])),
                 c5_decaying_stable=float(np.mean(["c5_decaying" in r["nonpersistent_stable"] for r in Rm])),
                 false_stable_per_rep_mixed=float(np.mean([r["false_stable"] for r in Rm])),
                 frozen_per_rep_mixed=float(np.mean([r["n_frozen"] for r in Rm])), stable_per_rep_mixed=float(np.mean([r["n_stable"] for r in Rm])),
                 valid=arena_valid)
# classification
cls = {}
for r in recs:
    t, c = fz[r["id"] + "_" + r["target"]]
    inv_tv = dia[t]["invariance_train_val"][c["id"]]; inv_ho = ho["per_target"][t]["invariance_heldout"][c["id"]]
    icp = dia[t]["icp_lite"]; inter = icp.get("intersection") or []
    inc = bool(set(E.variables(E.parse(c["expr"]))) & set(inter))
    p = min(inv_tv["p"], inv_ho["p"]); sa = min(inv_tv["sign_agree"], inv_ho["sign_agree"])
    cls[r["id"] + "_" + r["target"]] = dict(label=causal.classify(r["stable"], p, sa, inc, mechanism_documented=False, design=None),
                                            inv_p_trainval=inv_tv["p"], inv_p_heldout=inv_ho["p"], sign_agree=sa, icp_includes=inc)
n_disc = len(recs); n_stable = sum(r["stable"] for r in recs); n_novel = sum(r["novel_vs_baseline"] for r in recs)
n_sym = sum(1 for r in recs if r["stable"] and fz[r["id"] + "_" + r["target"]][1]["kind"] == "symbolic")
n_ci = sum(1 for v in cls.values() if v["label"] == "CAUSAL_IDENTIFIED")
cj = ho["complexity_justified"]["aggregate"]
if not arena_valid:
    verdict = "STUDY_INCONCLUSIVE"
elif n_novel >= 3 and cj == "YES":
    verdict = "FEATURE_DISCOVERY_REFERENCE_SUPPORTED"
elif n_stable >= 1:
    verdict = "LIMITED_STABLE_FEATURES_SUPPORTED"
else:
    verdict = "NO_STABLE_NEW_FEATURES"
final = dict(FEATURES_DISCOVERED=n_disc, FEATURES_HELDOUT_STABLE=n_stable, SYMBOLIC_EXPRESSIONS_STABLE=n_sym, NONREDUNDANT_FEATURES=n_novel,
             CAUSAL_IDENTIFIED_COUNT=n_ci, COMPLEXITY_JUSTIFIED=cj, COMPLEXITY_PER_TARGET=ho["complexity_justified"]["per_target"],
             FINAL_VERDICT=verdict, arena=arena_sum, classification=cls)
json.dump(final, open(os.path.join(RES, "FINAL.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in final.items() if k not in ("classification",)}, indent=1))

# ---- tables
rows = []
for r in recs:
    t, c = fz[r["id"] + "_" + r["target"]]
    rows.append([r["target"], r["id"], f"`{c['expr']}`", c["kind"], c["nodes"], f"{c['seed_freq']:.1f}", f"{c['val_ic_mean']:+.4f}", f"{r['ic_mean']:+.4f}",
                 f"[{r['ic_ci90'][0]:+.4f}, {r['ic_ci90'][1]:+.4f}]", f"{r['frac_pos']:.2f}", f"{r['unseen_pos']}/{r['n_unseen']}",
                 f"{r['p_holm']:.3f}", "yes" if r["stable"] else "no", f"{r['partial_ic_mean']:+.4f}", f"{r['p_partial_holm']:.3f}", "yes" if r["novel_vs_baseline"] else "no",
                 cls[r["id"] + "_" + r["target"]]["label"]])
open(os.path.join(TAB, "heldout_candidates.md"), "w").write(md(rows, ["target", "id", "expression", "kind", "nodes", "seed freq", "IC val", "IC held-out", "IC 90% CI", "markets IC>0", "unseen IC>0", "p_Holm", "STABLE", "partial IC vs raw-ridge", "p_Holm partial", "NON-REDUNDANT", "evidence class"]))
rows = []
for t, d in ho["per_target"].items():
    for k, v in d["comparison"].items():
        dm = v.get("disc_minus_this")
        rows.append([t, k, v["params"], f"{v['ic_mean']:+.4f}", f"[{v['ic_ci90'][0]:+.4f}, {v['ic_ci90'][1]:+.4f}]", f"{v['r2_oos_mean']*100:+.3f}%",
                     "" if dm is None else f"{dm['mean']:+.4f} (q10 {dm['q10']:+.4f})"])
open(os.path.join(TAB, "heldout_models.md"), "w").write(md(rows, ["target", "model", "params", "pooled IC held-out", "IC 90% CI", "OOS R² (mean over markets)", "discovered − this (mean, q10)"]))
sa = arena_sum
open(os.path.join(TAB, "arena.md"), "w").write(md([[k, f"{v:.3f}" if isinstance(v, float) else v] for k, v in sa.items()], ["metric", "value"]))
