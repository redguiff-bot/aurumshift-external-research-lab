"""ALFRED / FRED vintage semantics, executed keylessly via the public web CSV endpoints.
NOTE: the official FRED *API* (api.stlouisfed.org) needs a key we don't have -> not executed with data."""
import re, csv, io, time, bisect
from common import *
B = "https://alfred.stlouisfed.org/graph/alfredgraph.csv"
def vint_list(sid):
    r = get(f"https://alfred.stlouisfed.org/series/downloaddata?seid={sid}", name=f"alfred_vintages_{sid}.html", save=False)
    h = r["body"].decode("utf8", "replace")
    v = sorted(set(re.findall(r'<option value="(\d{4}-\d\d-\d\d)">', h)))
    return v, r
def at(sid, T, cosd=None, coed=None):
    q = f"{B}?id={sid}&vintage_date={T}" + (f"&cosd={cosd}" if cosd else "") + (f"&coed={coed}" if coed else "")
    r = get(q, save=False)
    txt = r["body"].decode("utf8", "replace")
    rows = list(csv.reader(io.StringIO(txt)))
    ok = r["status"] == 200 and rows and rows[0][0] == "observation_date"
    d = {}
    if ok:
        for x in rows[1:]:
            if len(x) > 1 and x[1] not in ("", "."): d[x[0]] = float(x[1])
    return {"ok": ok, "col": rows[0][1] if ok and len(rows[0]) > 1 else None, "obs": d, "status": r["status"], "receipt": r["receipt_time_utc"], "raw": txt[:200] if not ok else None}
def latest(sid):
    r = get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", save=False)
    txt = r["body"].decode("utf8", "replace")
    if not txt.startswith("observation_date"): return None, r["receipt_time_utc"]
    rows = list(csv.reader(io.StringIO(txt)))
    return {x[0]: float(x[1]) for x in rows[1:] if len(x) > 1 and x[1] not in ("", ".")}, r["receipt_time_utc"]

SERIES = {  # sid: (label, T dates for lookahead test)
 "GDPC1":   ("Real GDP", ["2009-02-15", "2011-08-15", "2013-08-15", "2018-08-15"]),
 "PAYEMS":  ("Nonfarm payrolls", ["2009-01-12", "2009-03-12", "2014-10-10", "2020-05-11"]),
 "CPIAUCSL":("CPI SA", ["2009-01-20", "2015-03-01", "2022-07-15", "2024-03-15"]),
 "CPIAUCNS":("CPI NSA (never-revised control)", ["2009-01-20", "2022-07-15"]),
 "INDPRO":  ("Industrial production", ["2009-01-20", "2012-05-01", "2019-06-10", "2022-08-01"]),
 "UNRATE":  ("Unemployment rate", ["2009-01-12", "2010-03-01", "2020-05-11"]),
 "WCESTUS1":("Weekly US crude stocks (EIA) - NOT on FRED/ALFRED (HTML error page returned)", ["2020-05-01"]),
 "DCOILWTICO":("WTI spot daily (EIA-sourced)", ["2015-01-15", "2022-07-15"]),
 "PCEPI":   ("PCE price index", ["2012-05-01", "2022-07-15"]),
 "DFF":     ("Fed funds effective (control)", ["2015-01-15", "2022-07-15"]),
}
def main():
    out = {"run_utc": utcnow(), "series": {}}
    for sid, (label, Ts) in SERIES.items():
        v, r = vint_list(sid)
        lat, lrec = latest(sid)
        if v == [] or lat is None:
            out["series"][sid] = {"label": label, "unavailable": True, "n_vintages": len(v), "latest_receipt": lrec}; print(sid, "UNAVAILABLE"); continue
        s = {"label": label, "n_vintages": len(v), "first_vintage": v[0] if v else None, "last_vintage": v[-1] if v else None,
             "vintage_list_receipt": r["receipt_time_utc"], "latest_receipt": lrec, "lookahead_tests": []}
        for T in Ts:
            if v and T < v[0]:
                s["lookahead_tests"].append({"T": T, "skip": f"before first vintage {v[0]}"}); continue
            a = at(sid, T, cosd=(f"{int(T[:4])-2}-01-01"))
            time.sleep(0.2)
            if not a["ok"] or not a["obs"]:
                s["lookahead_tests"].append({"T": T, "fail": a["raw"] or "empty"}); continue
            last_obs = max(a["obs"]); asof_val = a["obs"][last_obs]
            # asof vintage actually used = last vintage <= T
            i = bisect.bisect_right(v, T) - 1
            n_rev = sum(1 for k, x in a["obs"].items() if k in lat and abs(lat[k] - x) > 1e-9)
            diffs = [(k, x, lat[k]) for k, x in a["obs"].items() if k in lat and abs(lat[k] - x) > 1e-9]
            ks = sorted(a["obs"]); prev = ks[-2] if len(ks) > 1 else None
            g_T = (a["obs"][last_obs]/a["obs"][prev]-1)*100 if prev else None
            g_L = (lat[last_obs]/lat[prev]-1)*100 if prev and last_obs in lat and prev in lat else None
            s["lookahead_tests"].append({"growth_pct_known_at_T": g_T, "growth_pct_latest": g_L, "T": T, "asof_vintage_used": v[i] if i >= 0 else None, "last_obs_known_at_T": last_obs,
                "value_known_at_T": asof_val, "latest_value_same_obs": lat.get(last_obs),
                "abs_diff": None if last_obs not in lat else round(lat[last_obs] - asof_val, 4),
                "n_obs_in_2y_window": len(a["obs"]), "n_obs_revised_vs_latest": n_rev,
                "first_3_revised": diffs[:3], "col": a["col"], "receipt": a["receipt"]})
        out["series"][sid] = s
        print(sid, s["n_vintages"], s["first_vintage"], s["last_vintage"])
        for t in s["lookahead_tests"]: print("   ", {k: t[k] for k in t if k in ("T","asof_vintage_used","last_obs_known_at_T","value_known_at_T","latest_value_same_obs","abs_diff","n_obs_revised_vs_latest","growth_pct_known_at_T","growth_pct_latest","skip","fail")})
    dump(out, "alfred_lookahead.json")

if __name__ == "__main__": main()
