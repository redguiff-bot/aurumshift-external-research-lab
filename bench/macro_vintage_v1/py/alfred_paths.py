"""Edge semantics + revision paths + trap demos + calendar alignment. Keyless ALFRED/FRED web CSV endpoints."""
import re, time, bisect
from common import *
from alfred_test import at, vint_list, latest, B
out = {"run_utc": utcnow()}
# 1 before first vintage
out["before_first_vintage"] = {}
for sid, T in [("GDPC1", "1985-01-01"), ("GDPC1", "1991-12-01"), ("PAYEMS", "1950-01-01")]:
    a = at(sid, T); out["before_first_vintage"][f"{sid}@{T}"] = {"ok": a["ok"], "n_obs": len(a["obs"]), "status": a["status"], "raw": a["raw"], "col": a["col"]}
# 2 as-of on non-vintage day == last vintage <= T
out["asof_equivalence"] = []
for sid, T in [("GDPC1", "2009-02-15"), ("PAYEMS", "2014-10-10"), ("CPIAUCSL", "2022-07-15"), ("INDPRO", "2019-06-10")]:
    v, _ = vint_list(sid); i = bisect.bisect_right(v, T) - 1
    a = at(sid, T, cosd="2005-01-01"); b = at(sid, v[i], cosd="2005-01-01"); nxt = v[i+1] if i+1 < len(v) else None
    c = at(sid, nxt, cosd="2005-01-01") if nxt else None
    out["asof_equivalence"].append({"sid": sid, "T": T, "vintage_le_T": v[i], "next_vintage": nxt,
        "equal_to_last_vintage_le_T": a["obs"] == b["obs"], "differs_from_next_vintage": (a["obs"] != c["obs"]) if c else None})
# 3 revision paths
PATHS = [("GDPC1", "2008-10-01"), ("PAYEMS", "2008-12-01"), ("INDPRO", "2008-12-01"), ("CPIAUCSL", "2022-06-01"), ("UNRATE", "2020-04-01"), ("PAYEMS", "2020-04-01")]
out["paths"] = {}
for sid, ob in PATHS:
    v, _ = vint_list(sid); lat, _ = latest(sid)
    path = []; first = None
    for d in [x for x in v if x >= ob]:
        a = at(sid, d, cosd=ob, coed=ob); time.sleep(0.15)
        val = a["obs"].get(ob) if a["ok"] else None
        if val is None:
            continue
        if first is None: first = d
        if not path or path[-1]["value"] != val: path.append({"vintage": d, "value": val, "receipt": a["receipt"]})
        if len(path) >= 12: break
    out["paths"][f"{sid}:{ob}"] = {"first_vintage_with_obs": first, "distinct_values_first_scan": len(path), "path": path, "latest_value": lat.get(ob)}
    print(sid, ob, first, [(p["vintage"], p["value"]) for p in path][:6], "latest", lat.get(ob))
# 4 traps
tr = {}
r = get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1&cosd=2008-07-01&coed=2009-01-01&vintage_date=2009-01-30", save=False)
tr["fredgraph_vintage_date_ignored"] = r["body"].decode()[:300]
r = get("https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=GDPC1&cosd=2008-07-01&coed=2009-01-01&realtime_start=2009-01-30&realtime_end=2009-01-30", save=False)
tr["alfredgraph_realtime_params"] = r["body"].decode()[:300]
r = get("https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=GDPC1&cosd=2008-07-01&coed=2009-07-01&vintage_date=2009-01-30,2009-02-27,2009-03-26", save=False)
tr["alfredgraph_multi_vintage_comma"] = r["body"].decode()[:400]
r = get("https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=GDPC1&cosd=2008-07-01&coed=2009-07-01&vintage_date=2009-01-30&vintage_date=2009-02-27", save=False)
tr["alfredgraph_multi_vintage_repeat"] = r["body"].decode()[:400]
r = get("https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=GDPC1&cosd=2008-07-01&coed=2009-07-01&vintage_date=2026-12-31", save=False)
tr["alfredgraph_future_vintage"] = r["body"].decode()[:200]
out["traps"] = tr
# 5 vintage date vs official BLS calendar (2025-2026 events, US-Eastern)
ics = open(os.path.join(RAW, "bls_schedule_ics"), encoding="utf8", errors="replace").read()
ev = re.findall(r"DTSTART;TZID=US-Eastern:(\d{8})T(\d{6})\r?\nDURATION:PT0M\r?\nSUMMARY:([^\r\n]+)", ics)
cal = {}
for d, t, s in ev: cal.setdefault(s, []).append((f"{d[:4]}-{d[4:6]}-{d[6:]}", f"{t[:2]}:{t[2:4]}"))
out["bls_ics_summary"] = {"n_events": len(ev), "date_range": [min(x[0] for x in ev), max(x[0] for x in ev)] , "titles": sorted(cal)[:80]}
def align(sid, title):
    v, _ = vint_list(sid); dates = {d for d, _ in cal[title]}
    past = [d for d in sorted(dates) if d <= "2026-09-28" and d >= "2025-01-01"]
    hit = [d for d in past if d in v]
    near = {d: [x for x in v if abs((datetime.date.fromisoformat(x) - datetime.date.fromisoformat(d)).days) <= 3] for d in past if d not in v}
    vint_2025on = [x for x in v if x >= "2025-01-01"]
    return {"series": sid, "bls_title": title, "bls_past_events": len(past), "vintage_date_equals_calendar_date": len(hit), "times": sorted({t for d, t in cal[title]}),
            "calendar_dates_without_same_day_vintage": near, "alfred_vintages_since_2025": len(vint_2025on), "alfred_vintages_not_on_a_bls_date": [x for x in vint_2025on if x not in dates]}
out["calendar_alignment"] = [align("PAYEMS", "Employment Situation"), align("UNRATE", "Employment Situation"), align("CPIAUCSL", "Consumer Price Index")]
dump(out, "alfred_paths.json")
for k in ("before_first_vintage", "asof_equivalence", "traps"): print(k, json.dumps(out[k], indent=1)[:1800])
print(json.dumps(out["calendar_alignment"], indent=1)[:2500])
