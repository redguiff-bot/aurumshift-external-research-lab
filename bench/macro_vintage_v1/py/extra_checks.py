import re, csv, json
from common import *
from alfred_test import vint_list
out = {"run_utc": utcnow()}
b = open(os.path.join(RAW, "bea_ics_real"), encoding="utf8", errors="replace").read()
ev = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", b, re.S)
gdp = []
for e in ev:
    s = re.search(r"SUMMARY:([^\r\n]*)", e).group(1); d = re.search(r"DTSTART[^:]*:(\d{8}T\d{6}Z?)", e).group(1)
    if s.startswith("Gross Domestic Product\\,") and "State" not in s: gdp.append((d, s))
v, _ = vint_list("GDPC1")
past = [(d, s) for d, s in gdp if d[:8] <= "20260928"]
rows = []
for d, s in past:
    iso = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    rows.append({"bea_ics_utc": d, "summary": s[:70], "alfred_vintage_same_day": iso in v})
out["bea_gdp_vs_alfred"] = {"n": len(rows), "same_day": sum(r["alfred_vintage_same_day"] for r in rows), "rows": rows}
r = list(csv.DictReader(open(os.path.join(RAW, "oecd_stes_revisions_USA_PRVM.csv"))))
eds = sorted({x["EDITION"] for x in r})
tp = "2020-03"; ex = sorted((x["EDITION"], x["OBS_VALUE"]) for x in r if x["TIME_PERIOD"] == tp)
out["oecd_stes_revisions"] = {"rows": len(r), "n_editions": len(eds), "first_edition": eds[0], "last_edition": eds[-1], "key": "USA.M.PRVM.IX.BTE", "obs_2020-03_by_edition_first12": ex[:12], "distinct_values_2020-03": sorted({v for _, v in ex})[:10]}
dump(out, "extra_checks.json"); print(json.dumps(out, indent=1)[:2500])
