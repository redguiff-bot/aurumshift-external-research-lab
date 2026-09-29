"""Fills report templates with numbers/tables from results/ -> reports/015_feature_discovery/*.md"""
import os, json, re, glob
B = os.path.join(os.path.dirname(__file__), ".."); R = os.path.join(B, "results")
out = os.path.join(B, "..", "..", "reports", "015_feature_discovery")
fin = json.load(open(f"{R}/FINAL.json"))
vals = {k: str(fin[k]) for k in ("FEATURES_DISCOVERED", "FEATURES_HELDOUT_STABLE", "SYMBOLIC_EXPRESSIONS_STABLE", "NONREDUNDANT_FEATURES", "CAUSAL_IDENTIFIED_COUNT", "COMPLEXITY_JUSTIFIED", "FINAL_VERDICT")}
a = fin["arena"]
vals["arena"] = "| métrique | valeur |\n|---|---|\n" + "\n".join(f"| {k} | {v:.3f} |" if isinstance(v, float) else f"| {k} | {v} |" for k, v in a.items()) + "\n"
for t in glob.glob(f"{R}/tables/*.md"):
    vals.setdefault(os.path.basename(t)[:-3], open(t).read())
for f in sorted(glob.glob(os.path.join(B, "report_templates", "*.md"))):
    s = open(f).read()
    s = re.sub(r"\{\{(\w+)\}\}", lambda m: vals[m.group(1)], s)
    open(os.path.join(out, os.path.basename(f)), "w").write(s)
    print("wrote", os.path.basename(f))
