"""laneI — analyse des snapshots calendrier : fuseaux, JSON vs XML ForexFactory, FF vs BEA (horaires UTC),
couverture banques centrales, diffs entre snapshots, doublons, identifiants.
Usage: python analyze_calendars.py  -> results/calendar_compare.json
"""
import json, re, html, glob, pathlib, datetime as dt, collections, xml.etree.ElementTree as ET
from icalendar import Calendar

R = pathlib.Path(__file__).parent / "raw"
UTC = dt.timezone.utc
out = {}


def ff_json(tag):
    p = R / f"{tag}_ff_json.json"
    try:
        d = json.loads(p.read_text())
    except Exception:
        return None
    for x in d:
        x["utc"] = dt.datetime.fromisoformat(x["date"]).astimezone(UTC)
    return d


def ff_xml(tag):
    p = R / f"{tag}_ff_xml.xml"
    if not p.exists():
        return None
    root = ET.fromstring(p.read_bytes())
    ev = []
    for e in root.findall("event"):
        g = lambda k: (e.findtext(k) or "").strip()
        d, t = g("date"), g("time")
        try:
            ts = dt.datetime.strptime(f"{d} {t}", "%m-%d-%Y %I:%M%p").replace(tzinfo=UTC)
        except ValueError:
            ts = None  # "All Day" / "Tentative"
        url = g("url"); m = re.search(r"/calendar/(\d+)-", url)
        ev.append(dict(title=g("title"), country=g("country"), utc=ts, raw_time=t, impact=g("impact"),
                       forecast=g("forecast"), previous=g("previous"), url=url, series_id=m.group(1) if m else None,
                       tags=sorted({c.tag for c in e})))
    return ev


j1, x1 = ff_json("s1"), ff_xml("s1")
out["ff_json_fields"] = sorted({k for x in j1 for k in x if k != "utc"})
out["ff_xml_fields"] = sorted({t for x in x1 for t in x["tags"]})
out["ff_n_events"] = {"json": len(j1), "xml": len(x1)}
out["ff_json_offsets"] = dict(collections.Counter(x["date"][-6:] for x in j1))
# JSON vs XML alignment (same order)
mism, untimed = [], []
for a, b in zip(j1, x1):
    if b["utc"] is None:
        untimed.append((b["title"], b["raw_time"])); continue
    if a["title"] != b["title"] or a["utc"] != b["utc"]:
        mism.append((a["title"], a["date"], b["title"], b["raw_time"]))
out["ff_json_vs_xml_time_mismatch"] = mism
out["ff_xml_untimed"] = untimed
out["ff_xml_is_utc"] = len(mism) == 0
# duplicates (title,country,utc) and near-duplicates (same title within 5 min)
key = collections.Counter((x["title"], x["country"], x["utc"]) for x in j1)
out["ff_exact_duplicates"] = [str(k) for k, v in key.items() if v > 1]
near = []
for a, b in zip(j1, j1[1:]):
    if a["title"] == b["title"] and a["country"] == b["country"] and abs((b["utc"] - a["utc"]).total_seconds()) <= 300 and a["utc"] != b["utc"]:
        near.append((a["title"], a["date"], b["date"], a["previous"], b["previous"]))
out["ff_near_duplicates"] = near
out["ff_impact_counts"] = dict(collections.Counter(x["impact"] for x in j1))
out["ff_has_actual_field"] = any("actual" in x for x in j1) or any("actual" in x["tags"] for x in x1)
out["ff_past_events_with_actual"] = 0
# series ids: unique per (title,country)?
sid = collections.defaultdict(set)
for x in x1:
    sid[x["series_id"]].add((x["title"], x["country"]))
out["ff_series_id_unique_titles"] = sum(1 for v in sid.values() if len(v) == 1)
out["ff_series_id_shared"] = {k: sorted(map(str, v)) for k, v in sid.items() if len(v) > 1}
out["ff_series_ids_n"] = len(sid)
out["ff_occurrence_id_present"] = False

# BEA ICS + JSON
cal = Calendar.from_ical((R / "s1_bea_ics.ics").read_bytes())
bea = []
for c in cal.walk("VEVENT"):
    s = c.decoded("DTSTART")
    bea.append(dict(summary=str(c.get("SUMMARY")), utc=s.astimezone(UTC) if isinstance(s, dt.datetime) else s,
                    uid=str(c.get("UID")), dtstamp=str(c.decoded("DTSTAMP")) if c.get("DTSTAMP") else None, seq=c.get("SEQUENCE")))
out["bea_ics_n"] = len(bea)
out["bea_ics_range"] = [str(min(b["utc"] for b in bea)), str(max(b["utc"] for b in bea))]
out["bea_ics_uid_unique"] = len({b["uid"] for b in bea}) == len(bea)
bj = json.loads((R / "s1_bea_json.json").read_text())
flat = [(k, t) for k, v in bj.items() if isinstance(v, dict) for t in v.get("release_dates", [])] if isinstance(bj, dict) else []
out["bea_json_releases"] = sum(isinstance(v, dict) for v in bj.values()); out["bea_json_file_last_updated"] = bj.get("file_last_updated"); out["bea_json_dates"] = len(flat)
out["bea_json_duplicate_dates"] = sum(v for v in collections.Counter(flat).values() if v > 1) - sum(1 for v in collections.Counter(flat).values() if v > 1)
# FF(US) vs BEA for this week
wk0, wk1 = min(x["utc"] for x in j1), max(x["utc"] for x in j1)
bea_wk = [b for b in bea if isinstance(b["utc"], dt.datetime) and wk0 <= b["utc"] <= wk1]
bj_wk = [(k, t) for k, t in flat if wk0 <= dt.datetime.fromisoformat(t) <= wk1]
out["bea_events_this_week"] = [(b["summary"], b["utc"].isoformat()) for b in bea_wk]
out["bea_json_events_this_week"] = bj_wk
matches = []
for b in bea_wk:
    ff = [x for x in j1 if x["country"] == "USD" and x["utc"] == b["utc"]]
    matches.append(dict(bea=b["summary"], bea_utc=b["utc"].isoformat(), ff_same_instant=[(x["title"], x["impact"]) for x in ff]))
out["ff_vs_bea_this_week"] = matches

# Central banks: next meetings from official pages vs FF this week
def text(p):
    t = (R / p).read_text(encoding="utf8", errors="ignore")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
fed = text("s1_fed_fomc.html"); i = fed.find("2026 FOMC Meetings")
out["fed_2026_meetings"] = re.findall(r"(January|March|April|June|July|September|October|December) (\d{1,2}-\d{1,2})\*?", fed[i:i + 3000])
out["fed_page_has_time_of_day"] = bool(re.search(r"2:00 p\.m\.|14:00", fed[i:i + 3000]))
ecb = text("s1_ecb_mp.html")
out["ecb_2026_mp_meetings"] = sorted(set(re.findall(r"(\d{2}/\d{2}/2026) Governing Council of the ECB: monetary policy meeting", ecb)))
boe = text("s1_boe_mpc.html"); i = boe.find("2026 confirmed dates")
out["boe_2026_dates"] = re.findall(r"Thursday (\d{1,2} \w+)", boe[i:i + 800])
boj = text("s1_boj_mpm.html"); i = boj.find("Table : 2026")
out["boj_2026_snippet"] = boj[i:i + 400]
out["ff_central_bank_events_this_week"] = [(x["title"], x["country"], x["impact"], x["utc"].isoformat()) for x in j1
                                           if re.search(r"FOMC|Fed|ECB|BOJ|BOE|Monetary|Rate|Gov|President|Lagarde|Powell|Ueda|Bailey", x["title"])]

# snapshot diffs (s1 vs s2/s3/s4)
diffs = {}
for name, ext in (("ff_json", "json"), ("ff_xml", "xml"), ("bea_ics", "ics"), ("bea_json", "json"), ("fed_fomc", "html")):
    metas = sorted(glob.glob(str(R / f"s*_{name}.meta.json")))
    rows = []
    for m in metas:
        mm = json.loads(open(m).read())
        rows.append(dict(tag=pathlib.Path(m).name.split("_")[0], status=mm["status"], sha=mm["sha256"][:12],
                         last_modified=mm["headers"].get("last-modified") or mm["headers"].get("Last-Modified"),
                         receipt=mm["receipt_time_utc"]))
    diffs[name] = rows
out["snapshot_hashes"] = diffs
# field-level diff of FF json between first and last successful snapshot
ok = [r["tag"] for r in diffs["ff_json"] if r["status"] == 200]
if len(ok) >= 2:
    a, b = ff_json(ok[0]), ff_json(ok[-1])
    ka = {(x["title"], x["country"], x["date"]): (x["forecast"], x["previous"], x["impact"]) for x in a}
    kb = {(x["title"], x["country"], x["date"]): (x["forecast"], x["previous"], x["impact"]) for x in b}
    out["ff_field_diff"] = dict(first=ok[0], last=ok[-1], added=[str(k) for k in kb.keys() - ka.keys()],
                                removed=[str(k) for k in ka.keys() - kb.keys()],
                                changed=[(str(k), ka[k], kb[k]) for k in ka.keys() & kb.keys() if ka[k] != kb[k]])
(pathlib.Path(__file__).parent / "results" / "calendar_compare.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str)[:9000])

# field-level diff of FF XML between first and last successful snapshot (added after s4)
okx = [r["tag"] for r in out["snapshot_hashes"]["ff_xml"] if r["status"] == 200]
if len(okx) >= 2:
    a, b = ff_xml(okx[0]), ff_xml(okx[-1])
    ka = {(x["title"], x["country"], str(x["utc"])): (x["forecast"], x["previous"], x["impact"]) for x in a}
    kb = {(x["title"], x["country"], str(x["utc"])): (x["forecast"], x["previous"], x["impact"]) for x in b}
    out["ff_xml_field_diff"] = dict(first=okx[0], last=okx[-1], n=(len(a), len(b)),
                                    added=[str(k) for k in kb.keys() - ka.keys()], removed=[str(k) for k in ka.keys() - kb.keys()],
                                    changed=[(str(k), ka[k], kb[k]) for k in ka.keys() & kb.keys() if ka[k] != kb[k]])
    (pathlib.Path(__file__).parent / "results" / "calendar_compare.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out["ff_xml_field_diff"], indent=1, default=str))
