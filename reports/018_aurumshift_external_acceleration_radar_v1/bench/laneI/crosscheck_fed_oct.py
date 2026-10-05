"""laneI — cross-check P(hausse Fed oct-2026) Polymarket vs Kalshi + limite de fenêtre prices-history."""
import requests, time, json, datetime as dt
o={"run_utc":dt.datetime.now(dt.timezone.utc).isoformat()}
e=requests.get("https://gamma-api.polymarket.com/events",params=dict(slug="fed-decision-in-october-20260617190323537"),timeout=30).json()[0]
o["polymarket"]={m["question"]:dict(bid=m.get("bestBid"),ask=m.get("bestAsk"),last=m.get("lastTradePrice"),updatedAt=m.get("updatedAt")) for m in e["markets"]}
r=requests.get("https://api.elections.kalshi.com/trade-api/v2/events/KXFED-26OCT",params=dict(with_nested_markets="true"),timeout=30).json()
ms=r.get("markets") or r["event"]["markets"]
o["kalshi"]={m["ticker"]:dict(bid=m["yes_bid_dollars"],ask=m["yes_ask_dollars"],last=m["last_price_dollars"],updated_time=m["updated_time"]) for m in ms}
tok=json.loads([m for m in e["markets"] if "no change" in m["question"]][0]["clobTokenIds"])[0]
now=int(time.time()); lim={}
for days in (15,18,21):
    rr=requests.get("https://clob.polymarket.com/prices-history",params=dict(market=tok,startTs=now-days*86400,endTs=now,fidelity=60),timeout=30)
    lim[days]=rr.status_code; time.sleep(0.3)
o["prices_history_window_status_by_days"]=lim
open("results/crosscheck_fed_oct.json","w").write(json.dumps(o,indent=1)); print(json.dumps(o,indent=1))
