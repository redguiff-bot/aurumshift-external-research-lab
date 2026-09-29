"""Robustness classification from results/sensitivity/*.json (descriptive).  Writes results/sensitivity_summary.{json,md}."""
import json, os, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THR = json.load(open(os.path.join(ROOT, "configs", "protocol.json")))["practical_thresholds"]
SIL = ["S4_TEMPORARY_SILENCE", "S5_PROVIDER_DATA_GAP", "S9_LONG_DORMANCY_RETURN"]
ADP = ["S2_ABRUPT_REGIME_CHANGE", "S3_SLOW_DRIFT", "S9_LONG_DORMANCY_RETURN"]
NEW = ["S1_MASSIVE_COLD_START", "S10_DYNAMIC_POPULATION"]
CHOSEN = {"A": "A|floor0.05"}
for k in ("B", "C", "C2", "D"):
    sp = json.load(open(os.path.join(ROOT, "configs", f"selected_{k}.json")))["spec"]
    if k == "B": CHOSEN[k] = f"B|g{sp['gamma']}|S{sp['S']}|M{sp['M']}"
    if k == "C": CHOSEN[k] = f"C|{sp['algo']}|f{sp['fading']}|e{sp['eps']}"
    if k == "C2": CHOSEN[k] = f"C2|S{sp['guard'][0]}|M{sp['guard'][1]}"
    if k == "D": CHOSEN[k] = f"D|{sp['algo']}|lr{sp['lr']}|x{sp['expl']}|grp{int(sp['use_group'])}"
def agg(runs):
    by = {}
    for r in runs: by.setdefault(r["label"], {}).setdefault(r["scenario"], []).append(r)
    out = {}
    for lab, sc in by.items():
        f = lambda m, ss: float(np.nanmean([np.nanmean([r[m] for r in sc[s]]) for s in ss if s in sc]))
        allS = list(sc)
        out[lab] = dict(info_ratio=f("info_ratio", allS), starvation_rate=f("starvation_rate", allS), stale_rate=f("stale_rate", allS),
                        silent_excess=f("silent_excess", SIL), adapt_delay=f("adapt_delay", ADP), new_ttfa_median=f("new_ttfa_median", NEW),
                        coverage_W=f("coverage_W", allS), max_starvation_duration=f("max_starvation_duration", allS), turnover=f("turnover", allS),
                        policy_seconds=f("policy_seconds", allS))
    return out
res, md = {}, []
for k in ("A", "B", "C", "C2", "D"):
    p = os.path.join(ROOT, "results", "sensitivity", f"{k}.json")
    if not os.path.exists(p): continue
    d = json.load(open(p)); assert not any("error" in r for r in d["runs"])
    a = agg(d["runs"]); ch = a[CHOSEN[k]]
    ok = []
    for lab, m in a.items():
        if lab == CHOSEN[k] or lab.endswith("BEYOND_GRID"): continue
        good = (ch["info_ratio"] - m["info_ratio"] <= 2 * THR["info_ratio"] and m["starvation_rate"] - ch["starvation_rate"] <= 2 * THR["starvation_rate"]
                and m["stale_rate"] - ch["stale_rate"] <= 2 * THR["stale_rate"] and m["silent_excess"] - ch["silent_excess"] <= 2 * THR["silent_excess"])
        ok.append(good)
    frac = float(np.mean(ok))
    cls = "ROBUST" if frac >= 0.75 else ("SENSITIVE" if frac >= 0.35 else "BRITTLE")
    rng = {m: [min(v[m] for v in a.values()), max(v[m] for v in a.values())] for m in ("info_ratio", "starvation_rate", "stale_rate", "silent_excess", "adapt_delay", "new_ttfa_median")}
    res[k] = dict(chosen=CHOSEN[k], n_configs=len(a), acceptable_fraction=frac, classification=cls, ranges=rng, table=a)
    md.append(f"\n### {k} — {cls} (acceptable fraction {frac:.2f} of {len(ok)} alternative configs; chosen `{CHOSEN[k]}`)\n")
    md.append("| config | info_ratio | starvation | stale | silent_excess | adapt_delay | new_ttfa | coverage | max_starv | policy_s |\n|---|---|---|---|---|---|---|---|---|---|")
    for lab, m in sorted(a.items()):
        star = " **(chosen)**" if lab == CHOSEN[k] else ""
        md.append(f"| `{lab}`{star} | {m['info_ratio']:.3f} | {m['starvation_rate']:.3f} | {m['stale_rate']:.3f} | {m['silent_excess']:+.3f} | {m['adapt_delay']:.0f} | {m['new_ttfa_median']:.1f} | {m['coverage_W']:.3f} | {m['max_starvation_duration']:.0f} | {m['policy_seconds']:.1f} |")
json.dump(res, open(os.path.join(ROOT, "results", "sensitivity_summary.json"), "w"), indent=1)
open(os.path.join(ROOT, "results", "sensitivity_summary.md"), "w").write("\n".join(md))
for k, v in res.items(): print(k, v["classification"], round(v["acceptable_fraction"], 2), v["ranges"])
