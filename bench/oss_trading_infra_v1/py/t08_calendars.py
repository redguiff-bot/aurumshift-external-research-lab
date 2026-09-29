"""T08 — market calendars: exchange_calendars vs pandas_market_calendars vs known-answer facts.
Known answers (NYSE, from official NYSE holiday/early-close schedules; independent of both libs):
 2024 full holidays: 01-01,01-15,02-19,03-29,05-27,06-19,07-04,09-02,11-28,12-25 ; early close 13:00 ET: 2024-07-03, 2024-11-29, 2024-12-24
 2025 full holidays: 01-01,01-09(National Day of Mourning for Carter),01-20,02-17,04-18,05-26,06-19,07-04,09-01,11-27,12-25 ; early: 2025-07-03, 2025-11-28, 2025-12-24
 DST: open 09:30 ET = 14:30 UTC before 2024-03-10 (EST) and 13:30 UTC after (EDT)."""
import json, warnings, time; warnings.filterwarnings("ignore")
import pandas as pd
import exchange_calendars as xc, pandas_market_calendars as pmc
hol = {2024: "2024-01-01 2024-01-15 2024-02-19 2024-03-29 2024-05-27 2024-06-19 2024-07-04 2024-09-02 2024-11-28 2024-12-25".split(),
       2025: "2025-01-01 2025-01-09 2025-01-20 2025-02-17 2025-04-18 2025-05-26 2025-06-19 2025-07-04 2025-09-01 2025-11-27 2025-12-25".split()}
early = "2024-07-03 2024-11-29 2024-12-24 2025-07-03 2025-11-28 2025-12-24".split()
res = {}
t = time.perf_counter(); x = xc.get_calendar("XNYS"); tx = time.perf_counter()-t
t = time.perf_counter(); p = pmc.get_calendar("NYSE"); tp = time.perf_counter()-t
res["load_seconds"] = dict(exchange_calendars=round(tx, 3), pandas_market_calendars=round(tp, 3))
for name, get_sessions in (("exchange_calendars", lambda a, b: x.sessions_in_range(a, b)),
                           ("pandas_market_calendars", lambda a, b: pd.DatetimeIndex(p.valid_days(a, b)).tz_localize(None).normalize())):
    r = {}
    for y, hs in hol.items():
        s = get_sessions(f"{y}-01-01", f"{y}-12-31"); s = pd.DatetimeIndex(s).tz_localize(None) if getattr(s, "tz", None) is not None else pd.DatetimeIndex(s)
        allb = pd.bdate_range(f"{y}-01-01", f"{y}-12-31"); missing = sorted(set(allb.strftime("%Y-%m-%d")) - set(s.strftime("%Y-%m-%d")))
        r[y] = dict(n_sessions=len(s), holidays_expected=len(hs), holidays_matched=len(set(missing) & set(hs)), extra_closures=sorted(set(missing)-set(hs)), missing_expected=sorted(set(hs)-set(missing)))
    r["early_closes_detected"] = None
    res[name] = r
# early closes
sch = p.schedule("2024-01-01", "2025-12-31"); e_p = sorted(sch.index[(sch["market_close"] - sch["market_open"]) < pd.Timedelta(hours=6)].strftime("%Y-%m-%d"))
e_x = sorted(pd.DatetimeIndex(x.early_closes[(x.early_closes >= "2024-01-01") & (x.early_closes <= "2025-12-31")]).strftime("%Y-%m-%d"))
res["exchange_calendars"]["early_closes_detected"] = e_x; res["pandas_market_calendars"]["early_closes_detected"] = e_p
res["early_closes_expected"] = early
# DST open times in UTC
def open_utc_x(d): return str(x.session_open(d))
def open_utc_p(d): return str(p.schedule(d, d)["market_open"].iloc[0])
res["open_utc"] = {d: dict(exchange_calendars=open_utc_x(d), pandas_market_calendars=open_utc_p(d)) for d in ["2024-03-08", "2024-03-11", "2024-11-01", "2024-11-04"]}
# 24/7 and FX/futures coverage
res["calendar_names"] = dict(exchange_calendars_n=len(xc.get_calendar_names(include_aliases=False)), pandas_market_calendars_n=len(pmc.get_calendar_names()),
   has_24_7=("24/7" in pmc.get_calendar_names()), has_cme_or_futures=[n for n in pmc.get_calendar_names() if "CME" in n.upper() or "CBOT" in n.upper()][:6],
   has_forex=[n for n in pmc.get_calendar_names() if "forex" in n.lower() or "fx" in n.lower()][:5],
   xc_names_sample=[n for n in xc.get_calendar_names(include_aliases=False) if n in ("XNYS","XLON","XCME","CMES","XTKS","XHKG","24/7","XNAS")])
# does exchange_calendars offer a bounded default range (forward) ?
res["xc_default_bounds"] = dict(first=str(x.first_session.date()), last=str(x.last_session.date()))
res["pmc_schedule_forward_2035"] = int(len(p.schedule("2035-01-01", "2035-12-31")))
print(json.dumps(res, default=str))
