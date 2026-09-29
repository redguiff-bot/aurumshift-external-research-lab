import warnings; warnings.filterwarnings("ignore")
import pandas as pd, json, exchange_calendars as xc, pandas_market_calendars as pmc, holidays, time
from common import save
res = {"versions": {"exchange_calendars": xc.__version__, "pandas_market_calendars": pmc.__version__, "holidays": holidays.__version__}}
a, b = "2020-01-02", "2026-12-30"
xn = xc.get_calendar("XNYS", start=a, end=b); pn = pmc.get_calendar("NYSE")
xs = set(xn.sessions_in_range(a, b).strftime("%Y-%m-%d"))
ps = set(pn.valid_days(a, b).strftime("%Y-%m-%d"))
res["XNYS_sessions"] = {"xc": len(xs), "pmc": len(ps), "only_xc": sorted(xs - ps)[:10], "only_pmc": sorted(ps - xs)[:10]}
# early closes & special closures
for d in ["2025-01-09", "2024-07-03", "2024-11-29", "2024-12-24", "2025-04-18", "2026-07-03"]:
    row = {"xc_is_session": xn.is_session(d)}
    if xn.is_session(d): row["xc_close_utc"] = str(xn.session_close(d))
    sched = pn.schedule(d, d)
    row["pmc_is_session"] = len(sched) > 0
    if len(sched): row["pmc_close_utc"] = str(sched.market_close.iloc[0])
    res.setdefault("spot_checks", {})[d] = row
# early-close counts
xe = list(xn.early_closes.strftime("%Y-%m-%d")); res["XNYS_early_closes_2020_2026_xc"] = [d for d in xe if a <= d <= b]
try:
    pe = pn.early_closes(pn.schedule(a, b)); res["XNYS_early_closes_2020_2026_pmc"] = list(pe.index.strftime("%Y-%m-%d"))
except Exception as e: res["pmc_early_closes_err"] = str(e)
# 24h calendars & lunch breaks
for code in ("CMES", "XLON", "XTKS", "XHKG", "IEPA", "24/7"):
    try:
        c = xc.get_calendar(code, start="2024-01-05", end="2024-12-30") if code != "24/7" else None
        if c is None: continue
        s = c.sessions_in_range("2024-01-05", "2024-12-30")
        res.setdefault("other_calendars_xc", {})[code] = {"sessions_2024": len(s), "has_break": bool(c.has_break if hasattr(c, 'has_break') else False), "example_open_close_utc": [str(c.session_open(s[10])), str(c.session_close(s[10]))]}
    except Exception as e: res.setdefault("other_calendars_xc", {})[code] = f"error {e}"
res["crypto_24_7_calendar"] = "24/7 not a registered code in exchange_calendars" if "24/7" not in xc.get_calendar_names() else "present"
res["n_calendars"] = {"xc": len(xc.get_calendar_names(include_aliases=False)), "pmc": len(pmc.get_calendar_names())}
# DST correctness: NYSE close 16:00 local = 20:00 UTC (EDT) vs 21:00 UTC (EST)
res["dst_close_utc"] = {"2024-03-08_EST": str(xn.session_close("2024-03-08")), "2024-03-11_EDT": str(xn.session_close("2024-03-11"))}
# perf
t0 = time.perf_counter(); c = xc.get_calendar("XNYS"); res["xc_load_default_seconds"] = round(time.perf_counter() - t0, 3)
t0 = time.perf_counter(); xn.minutes_in_range("2024-01-02", "2024-06-30"); res["xc_minutes_2024H1_seconds"] = round(time.perf_counter() - t0, 3)
# advance-knowledge: sessions declared far ahead
res["xc_default_bounds"] = [str(c.first_session), str(c.last_session)]
# deps
import importlib.metadata as md
res["requires_xc"] = md.requires("exchange-calendars"); res["requires_pmc"] = md.requires("pandas-market-calendars")
print(json.dumps(res, indent=1, default=str)); save("cal_microtest.json", res)
