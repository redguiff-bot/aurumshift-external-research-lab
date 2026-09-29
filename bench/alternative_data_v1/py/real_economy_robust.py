"""Robustness for the one strongly significant real-economy result (EIA crude inventory surprise -> WTI release-day return):
placebo release offsets, sub-periods, Brent cross-check, plus BH-FDR over the primary real-economy test family."""
import os, numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
from real_economy import *
RES = os.path.join(os.path.dirname(__file__), "..", "results")
P = eia("PET.zip", ["PET.WCESTUS1.W", "PET.RWTC.D", "PET.RBRTE.D"])
st = P["PET.WCESTUS1.W"]; sur = seasonal_surprise(st.diff())
wti = P["PET.RWTC.D"]; wti = wti[wti > 0]; brent = P["PET.RBRTE.D"]; brent = brent[brent > 0]
rows = []
for off, tag in ((3, "placebo_Mon(-2d)"), (4, "placebo_Tue(-1d)"), (5, "true_Wed"), (7, "placebo_Fri(+2d)"), (12, "placebo_Mon_next_wk")):
    for r in event_test("crude_surprise_vs_WTI|" + tag, wti, sur, off):
        if r["target"] == "release_day:y": rows.append(dict(r, offset_days=off, series="WTI"))
for a, b, tag in (("2007-01-01", "2014-12-31", "2007-2014"), ("2015-01-01", "2020-12-31", "2015-2020"), ("2021-01-01", "2026-12-31", "2021-2026")):
    for r in event_test("crude_surprise_vs_WTI|" + tag, wti, sur, 5, start=a, end=b):
        if r["target"] == "release_day:y":
            rows.append(dict(r, offset_days=5, series="WTI")) if True else None
# restrict subperiod rows to their end date
out = pd.DataFrame(rows)
rb = event_test("crude_surprise_vs_BRENT", brent, sur, 5)
for r in rb:
    if r["target"] == "release_day:y": out = pd.concat([out, pd.DataFrame([dict(r, offset_days=5, series="Brent")])])
out.to_csv(os.path.join(RES, "crude_robustness.csv"), index=False)
main_res = pd.read_csv(os.path.join(RES, "real_economy_results.csv"))
main_res["q_bh"] = bh(main_res.p_incr.values)
main_res.to_csv(os.path.join(RES, "real_economy_results.csv"), index=False)
pd.set_option("display.width", 220)
print(out[["cand", "series", "offset_days", "n", "first", "last", "coef_s", "t_s", "p_incr"]].round(4).to_string())
print(main_res[["cand", "target", "coef_s", "p_incr", "q_bh", "oos_gain_pct", "dm_p_onesided"]].round(4).to_string())
