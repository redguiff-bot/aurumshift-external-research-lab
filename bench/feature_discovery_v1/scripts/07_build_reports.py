"""Builds the numeric tables embedded in reports/015_feature_discovery from stored results (no hand-typed numbers)."""
import json, os, numpy as np
R = os.path.join(os.path.dirname(__file__), "..", "results"); T = os.path.join(R, "tables"); os.makedirs(T, exist_ok=True)
d = json.load(open(f"{R}/discovery_train_val.json")); g = json.load(open(f"{R}/diagnostics_train_val.json"))
h = json.load(open(f"{R}/heldout_results.json")); f = json.load(open(f"{R}/FINAL.json")); c = json.load(open(f"{R}/causal_boundaries.json"))
a = json.load(open(f"{R}/synthetic_arena_final.json"))


def md(rows, head):
    return "| " + " | ".join(head) + " |\n|" + "|".join("---" for _ in head) + "|\n" + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in rows) + "\n"


def w(name, s):
    open(f"{T}/{name}.md", "w").write(s)

# seeds
rows = []
for t in d:
    for s in d[t]["seeds"]:
        gp = [r for r in s["all"] if r["kind"] == "symbolic"]; it = [r for r in s["all"] if r["kind"] == "interaction"]
        rows.append([t, s["seed"], ", ".join(s["diag"]["cmi_selected"]) or "-", len(s["diag"]["interaction_screen"]), sum(r["gate"] for r in it),
                     len(s["diag"]["gp_programs"]), len(gp), sum(r["gate"] for r in gp), len(s["selected"])])
w("seeds", md(rows, ["target", "seed", "CMI-selected mains", "interactions passing shift-null", "…passing val gate", "GP programs (top)", "GP after trivial-filter", "…passing val gate", "retained (non-redundant)"]))
rows = []
for t in d:
    st = d[t]["consolidation"]["stab_mean"]; sc = g[t]["sparse_consistency"]
    for n, v in sorted(st.items(), key=lambda x: -x[1])[:8]:
        rows.append([t, n, f"{v:.2f}", sc[n]["markets_ge_0p7"], "yes" if sc[n]["both_halves_ge_0p7"] else "no", "yes" if n in d[t]["consolidation"]["mains"] else "no"])
w("sparse", md(rows, ["target", "primitive", "mean stability-selection freq (5 seeds, pooled)", "#markets (of 4) freq>=0.7 alone", "both train halves >=0.7", "retained as stable main"]))
rows = [[t, k, f"{v['ic']:+.4f}", f"{v['r2']*100:+.3f}%"] for t in g for k, v in g[t]["gbm_additive_vs_interaction_val"].items()]
w("gbm_val", md(rows, ["target", "GBM depth (1 = additive)", "validation IC", "validation R²"]))
rows = []
for t in d:
    for cd in d[t]["frozen"]:
        rows.append([t, cd["id"], f"`{cd['expr']}`", cd["kind"], cd["nodes"], cd["consts"], cd["seed_freq"], f"{cd['train_ic']:+.4f}", f"{cd['val_ic_mean']:+.4f}", f"{cd['val_p']:.3f}", f"{cd['novelty_val']:+.4f}", cd["sign"], f"{len(cd['family_members'])} members"])
w("frozen", md(rows, ["target", "id", "expression", "kind", "nodes", "constants", "seed freq", "IC train", "IC val (mean 4 mkts)", "val boot p", "val partial IC vs mains-ridge", "sign fixed on train", "family"]))
rows = []
for t in d:
    for cd in d[t]["frozen"]:
        rows.append([t, cd["id"], g[t]["invariance_train_val"][cd["id"]]["p"], g[t]["invariance_train_val"][cd["id"]]["sign_agree"], h["per_target"][t]["invariance_heldout"][cd["id"]]["p"], h["per_target"][t]["invariance_heldout"][cd["id"]]["sign_agree"], g[t]["icp_lite"]["n_accepted"], g[t]["icp_lite"]["n_subsets"]])
w("invariance", md([[r[0], r[1], f"{r[2]:.4f}", f"{r[3]:.2f}", f"{r[4]:.3f}", f"{r[5]:.2f}", f"{r[6]}/{r[7]}"] for r in rows], ["target", "id", "Cochran-Q p (16 market×year envs, train+val)", "sign agreement", "Cochran-Q p (9 held-out markets)", "sign agreement", "ICP-lite accepted / tested subsets"]))
rows = []
for r in h["records"]:
    rows.append([r["target"], r["id"]] + [f"{v:+.3f}" for v in r["ic"].values()])
w("heldout_by_market", md(rows, ["target", "id"] + list(h["records"][0]["ic"].keys())))
pl = []
for t in h["per_target"]:
    p = np.array(h["per_target"][t]["placebo_p_raw"]); pl.append([t, p.shape[0], f"{(p < 0.05).mean():.2f}", f"{p.min():.3f}"])
w("placebo", md(pl, ["target", "circular-shift placebos (same shift for all markets)", "share with raw p<0.05", "min raw p"]))
rows = [[k, v["pooled_ic"] if False else f"{v['pooled_ic']:+.3f}", f"{v['cochran_Q_p']:.3f}", f"{v['sign_agree']:.2f}", f"{v['icp_n_accepted']}/2", v["icp_intersection"], f"{v['do_effect']:+.3f}", f"{v['do_effect_p']:.3f}", v["class_observational_even_if_mechanism_claimed"], v["class_with_randomised_design"], v["truth_X_causes_Y"]] for k, v in c.items()]
w("causal", md(rows, ["structure", "pooled IC", "Cochran-Q p", "sign agree", "ICP accepted", "ICP ∩", "do(X) effect", "do(X) p", "class (observational only)", "class (+ randomised design)", "truth: X causes Y"]))
cls = [[k, v["label"], f"{v['inv_p_trainval']:.3f}", f"{v['inv_p_heldout']:.3f}", f"{v['sign_agree']:.2f}", v["icp_includes"]] for k, v in f["classification"].items()]
w("classes", md(cls, ["candidate", "evidence class", "Q p train+val", "Q p held-out", "sign agree (min)", "ICP includes vars"]))
# cards
out = ""
for t in d:
    for cd in d[t]["frozen"]:
        k = cd["card"]
        out += f"#### {t} / {cd['id']} — `{k['formula']}` (signe {k['sign']:+.0f})\n\n"
        out += f"- **Formule (préfixe)** : `{k['formula_prefix']}` ; nœuds {k['nodes']}, constantes {k['constants']}\n"
        out += "- **Variables** : " + "; ".join(f"`{v}` = {x['formula']} [{x['raw_unit']}]" for v, x in k["variables"].items()) + "\n"
        out += f"- **Unités** : entrées {k['units']['inputs']} ; sortie {k['units']['output']} ; cible : {k['units']['target']}\n"
        ir = k["input_requirements"]
        out += f"- **Entrées requises** : champs {ir['fields']} ; lookback primitif max {ir['max_primitive_lookback_bars']} barres + fenêtre de standardisation {ir['standardisation_window_bars']} → historique minimal {ir['min_history_bars']} barres 1h fermées\n"
        out += "- **Monotonie attendue** : " + "; ".join(f"`{v}` {m}" for v, m in k["expected_monotonicity"].items()) + "\n"
        out += "- **Ablation (Δ IC validation en neutralisant la variable)** : " + "; ".join(f"`{v}` {x:+.4f}" for v, x in k["variable_ablation_delta_ic_val"].items()) + (f" ; hitchhikers possibles : {k['possible_hitchhikers']}" if k["possible_hitchhikers"] else "") + "\n"
        out += "- **Modes de défaillance** :\n" + "".join(f"  - {m}\n" for m in k["failure_modes"])
        fs = k["forward_safety"]
        out += f"- **Forward-safety** : n'utilise que des barres ≤ t (vérifié : {fs['verified_by']}) ; horizon de label {fs['label_horizon_bars']} barres ; {fs['note']}\n\n"
w("cards", out)
