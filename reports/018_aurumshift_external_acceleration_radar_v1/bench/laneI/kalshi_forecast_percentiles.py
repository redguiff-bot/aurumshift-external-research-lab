"""laneI — Kalshi 'forecast_percentile_history' = consensus implicite marché (PIT, horodaté) pour CPI/NFP/chômage."""
import requests, time, json, datetime as dt
K="https://api.elections.kalshi.com/trade-api/v2"; now=int(time.time()); o={"run_utc":dt.datetime.now(dt.timezone.utc).isoformat()}
for s,ev in (("KXCPI","KXCPI-26SEP"),("KXPAYROLLS","KXPAYROLLS-26OCT"),("KXU3","KXU3-26OCT")):
    meta=requests.get(f"{K}/events/{ev}",timeout=30).json().get("event",{})
    r=requests.get(f"{K}/series/{s}/events/{ev}/forecast_percentile_history",
        params=[("percentiles",p) for p in (2500,5000,7500)]+[("start_ts",now-3*86400),("end_ts",now),("period_interval",60)],timeout=30)
    body=r.json() if r.headers.get("content-type","").startswith("application/json") else r.text[:300]
    h=body.get("forecast_history",[]) if isinstance(body,dict) else []
    o[ev]=dict(status=r.status_code,title=meta.get("title"),sub_title=meta.get("sub_title"),strike_date=meta.get("strike_date"),
               n_points=len(h),first=h[:1],last=h[-1:],err=None if r.ok else body)
    time.sleep(0.5)
open("results/kalshi_forecast_percentiles.json","w").write(json.dumps(o,indent=1)); print(json.dumps(o,indent=1)[:3500])
