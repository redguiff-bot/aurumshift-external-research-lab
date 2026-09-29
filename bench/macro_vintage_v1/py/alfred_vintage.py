"""Step 2: real ALFRED vintage retrieval + revision + lookahead tests.
Endpoint (keyless): https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=S&vintage_date=YYYY-MM-DD
Returns the series as it existed on vintage_date (single vintage per call)."""
import csv, io, json, re, time, datetime as dt
from common import fetch, text, RES

BASE = "https://alfred.stlouisfed.org"
_calls = 0

def vintages(series):
    r = fetch(f"{BASE}/series/downloaddata?seid={series}", f"alfred/{series}_downloaddata.html")
    return re.findall(r'<option value="(\d{4}-\d{2}-\d{2})">\1</option>', text(r))

def release_id(series):
    r = fetch(f"{BASE}/series?seid={series}", f"alfred/{series}_series.html")
    m = re.search(r"release\?rid=(\d+)", text(r))
    return int(m.group(1)) if m else None

def release_dates(rid):
    r = fetch(f"{BASE}/release/downloaddates?rid={rid}&ff=txt", f"alfred/release_dates_{rid}.txt")
    return re.findall(r"^(\d{4}-\d{2}-\d{2})\s*$", text(r), re.M)

def snap(series, vintage, cosd, coed):
    """{obs_date: float|None} as known on `vintage`."""
    global _calls
    name = f"alfred/{series}_v{vintage}_{cosd}_{coed}.csv"
    r = fetch(f"{BASE}/graph/alfredgraph.csv?id={series}&cosd={cosd}&coed={coed}&vintage_date={vintage}", name)
    if not r.get("cached"):
        time.sleep(0.25)
    rows = list(csv.reader(io.StringIO(text(r))))
    out = {}
    for row in rows[1:]:
        if len(row) >= 2:
            out[row[0]] = None if row[1] in (".", "") else float(row[1])
    return out

def first_vintage_with(series, obs, vlist):
    """Smallest vintage in vlist whose snapshot contains a value for obs (bisect; appearance is monotone)."""
    cand = [v for v in vlist if v >= obs]
    lo, hi = 0, len(cand) - 1
    if not cand or snap(series, cand[-1], obs, obs).get(obs) is None:
        return None
    while lo < hi:
        mid = (lo + hi) // 2
        if snap(series, cand[mid], obs, obs).get(obs) is not None:
            hi = mid
        else:
            lo = mid + 1
    return cand[lo]

def revision_path(series, obs, vlist, extra_years=(1, 3)):
    v0 = first_vintage_with(series, obs, vlist)
    if v0 is None:
        return None
    i = vlist.index(v0)
    picks = [v0] + [v for v in vlist[i + 1:i + 6]]
    for y in extra_years:
        t = str(int(v0[:4]) + y) + v0[4:]
        nxt = [v for v in vlist if v >= t]
        if nxt: picks.append(nxt[0])
    picks.append(vlist[-1])
    picks = sorted(set(picks))
    path = [{"vintage": v, "value": snap(series, v, obs, obs).get(obs)} for v in picks]
    return {"series": series, "obs": obs, "first_vintage": v0, "path": path,
            "n_distinct_values": len({p["value"] for p in path}),
            "first_print": path[0]["value"], "latest": path[-1]["value"]}

CASES = {
 "GDPC1": ["2008-10-01", "2020-04-01", "2022-01-01"],
 "GDP": ["2020-04-01"],
 "PAYEMS": ["2020-04-01", "2022-12-01", "2019-03-01"],
 "INDPRO": ["2020-04-01", "2022-03-01"],
 "CPIAUCSL": ["2021-06-01", "2022-06-01"],
 "UNRATE": ["2020-04-01"],
 "DGS10": [],   # control: market series, expected no revision
}

def main():
    out = {"revision_paths": [], "meta": {}}
    for s, obss in CASES.items():
        vl = vintages(s)
        rid = release_id(s)
        out["meta"][s] = {"n_vintages": len(vl), "first_vintage": vl[0] if vl else None,
                          "last_vintage": vl[-1] if vl else None, "release_id": rid}
        for o in obss:
            rp = revision_path(s, o, vl)
            print(s, o, json.dumps(rp)[:400])
            out["revision_paths"].append(rp)
    json.dump(out, open(RES + "/alfred_revision_paths.json", "w"), indent=1)

if __name__ == "__main__":
    main()
