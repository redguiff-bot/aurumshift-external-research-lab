"""Scale-free lookahead metric: compare the period-over-period % change of the newest observation
as known at first release vs as known today. Immune to base-year re-referencing of levels."""
import json, statistics as st
from common import RES
d = json.load(open(RES + "/lookahead_latest_vs_firstprint.json"))
out = {}
for s, v in d.items():
    diffs, flips, n = [], 0, 0
    for r in v["rows"]:
        if r["chg_first_asof_v"] is None or r["chg_latest"] is None: continue
        base_f = r["first_print"] - r["chg_first_asof_v"]; base_l = r["latest"] - r["chg_latest"]
        if not base_f or not base_l: continue
        pf, pl = 100 * r["chg_first_asof_v"] / base_f, 100 * r["chg_latest"] / base_l
        diffs.append(abs(pl - pf)); n += 1; flips += (pf * pl < 0)
    out[s] = {"n": n, "median_abs_diff_pct_change_pp": st.median(diffs), "mean_abs_diff_pp": st.mean(diffs),
              "max_abs_diff_pp": max(diffs), "share_diff_gt_0.05pp": sum(x > 0.05 for x in diffs) / n,
              "sign_flips_first_vs_latest": flips}
    print(s, json.dumps(out[s]))
json.dump(out, open(RES + "/lookahead_scalefree.json", "w"), indent=1)
