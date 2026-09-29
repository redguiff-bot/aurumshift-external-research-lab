"""Official release calendars: what fields they carry (schedule-only vs values)."""
import re
from common import *
R = {"run_utc": utcnow()}
def txt(n): return open(os.path.join(RAW, n), encoding="utf8", errors="replace").read()
def strip(h): return re.sub(r"\s+", " ", re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", h, flags=re.S))
r = get("https://www.bea.gov/news/schedule/ics/online-calendar-subscription.ics", name="bea_ics_real")
b = r["body"].decode("utf8", "replace")
ev = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", b, re.S)
def f(e, k):
    m = re.search(rf"^{k}[^:\r\n]*:([^\r\n]*)", e, re.M); return m.group(1) if m else None
R["bea_ics"] = {"status": r["status"], "n_events": len(ev), "sample": [{"dtstart": f(e, "DTSTART"), "summary": f(e, "SUMMARY"), "tz": re.search(r"DTSTART;([^:]*)", e).group(1) if re.search(r"DTSTART;([^:]*)", e) else "UTC/none"} for e in ev[:6]],
    "gdp_events": [{"dtstart": f(e, "DTSTART"), "summary": f(e, "SUMMARY")} for e in ev if re.search(r"GDP|Gross Domestic", f(e, "SUMMARY") or "")][:8]}
bls = txt("bls_schedule_ics")
R["bls_ics"] = {"n_events": bls.count("BEGIN:VEVENT"), "fields": ["DTSTART(ET tz)", "SUMMARY", "UID", "SEQUENCE"], "has_actual_previous_forecast": bool(re.search(r"forecast|consensus|previous|actual", bls, re.I))}
def kw(n):
    t = strip(txt(n)); return {"bytes": len(t), "forecast": bool(re.search(r"forecast|consensus", t, re.I)), "previous": bool(re.search(r"previous", t, re.I)), "actual": bool(re.search(r"\bactual\b", t, re.I)), "has_times": len(re.findall(r"\b\d{1,2}:\d\d\s?(?:a\.m\.|p\.m\.|AM|PM|ET|CET|CEST|GMT)", t, re.I))}
for n in ["bls_schedule_html", "bea_schedule_html", "eia_schedule_wpsr", "fred_release_calendar_html", "ecb_calendar", "eurostat_release_cal", "fed_g17_calendar", "census_econ_indicators_cal"]:
    R[n] = kw(n)
# EIA WPSR schedule sample
t = strip(txt("eia_schedule_wpsr"))
R["eia_wpsr_sample"] = t[t.find("Schedule") : t.find("Schedule") + 600]
t = strip(txt("fred_release_calendar_html"))
R["fred_calendar_sample"] = t[t.find("Release Calendar"): t.find("Release Calendar") + 700]
dump(R, "calendars.json"); print(json.dumps(R, indent=1)[:6000])
