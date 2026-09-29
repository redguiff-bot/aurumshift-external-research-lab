import json, glob, sys, os, numpy as np
d = sys.argv[1]
rows = {}
for f in sorted(glob.glob(os.path.join(d, "*.json"))):
    j = json.load(open(f))
    if "runs" not in j or not j["runs"]: continue
    rows[j["policy"]] = j
cols = [("cov1","cov≥1"),("cov10","cov≥10"),("zero_pull_cells","zero-pull cells"),("stale_frac_end","stale@end"),
        ("max_gap_p95","maxgap p95"),("ttf_new_median","ttf-new med"),("gems_found20","gems≥20"),
        ("gini_pre","Gini pre"),("top10pct_share_pre","top10% pre"),("entropy_pre","H pre"),
        ("gini_post","Gini post"),("top10pct_share_post","top10% post")]
cols2 = [("share_improved_0_50","impr 0-50"),("share_improved_50_150","impr 50-150"),("share_improved_150_200","impr 150-200"),
         ("share_degraded_pre","degr pre"),("share_degraded_0_50","degr 0-50"),("share_degraded_150_200","degr 150-200"),
         ("regret_pre","regret pre"),("regret_cp0_100","regret cp+0..100"),("regret_cp100_200","regret cp+100..200"),
         ("gap_waste_share","gap waste"),("regret_all","regret all")]
def table(cs, title):
    print(f"\n### {title}\n")
    print("| policy | " + " | ".join(c[1] for c in cs) + " |")
    print("|---|" + "---|"*len(cs))
    for p, j in rows.items():
        r = j["runs"]
        cells = []
        for k, _ in cs:
            v = np.array([x[k] for x in r], float)
            cells.append(f"{v.mean():.3g}±{v.std():.2g}")
        print(f"| {p} (n={len(r)}) | " + " | ".join(cells) + " |")
table(cols, "Coverage / starvation / concentration (mean±sd over seeds)")
table(cols2, "Adaptation (shares of pulls; regret = oracle_expected_reward − policy_expected_reward per round, B=10)")
print("\n### Cost\n\n| policy | wall s (all seeds, incl. import; runs in parallel jobs) | select+update s / run | maxrss MB | errors |\n|---|---|---|---|---|")
for p, j in rows.items():
    s = np.mean([x["select_update_seconds"] for x in j["runs"]])
    print(f"| {p} | {j['wall_seconds']:.1f} | {s:.2f} | {j['maxrss_mb']:.0f} | {bool(j['error'])} |")
