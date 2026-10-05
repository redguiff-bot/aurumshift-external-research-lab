"""laneI — L1 follow-up: profondeur d'historique Polymarket prices-history (depuis création du marché) et
Kalshi KXFED-26OCT (champs *_fp/*_dollars, chandeliers 1 min sur 3 jours, endpoints historical/*), + un marché clos
(Polymarket fed-decision-in-october 2025) pour tester l'historique après résolution.
"""
import json, time, datetime as dt, pathlib, statistics
import requests
ROOT = pathlib.Path(__file__).parent
S = requests.Session(); S.headers["User-Agent"] = "research-lab/0.1"
out = {"run_utc": dt.datetime.now(dt.timezone.utc).isoformat()}

def iso(t): return dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat() if t else None

def summ(ts):
    d = [b - a for a, b in zip(ts, ts[1:])]
    return dict(n=len(ts), first=iso(ts[0]) if ts else None, last=iso(ts[-1]) if ts else None,
                median_step_s=statistics.median(d) if d else None, max_step_s=max(d) if d else None)

def ph(token, **p):
    r = S.get("https://clob.polymarket.com/prices-history", params=dict(market=token, **p), timeout=30)
    h = r.json().get("history", []) if r.ok else []
    return dict(status=r.status_code, err=None if r.ok else r.text[:200], **summ([x["t"] for x in h]))

# Polymarket open market ("no change", Oct 2026), created 2026-06-17
tok_open = "111061902544814266207267295505639408607400625795891618462682726460921782993748"
created = int(dt.datetime(2026, 6, 18, tzinfo=dt.timezone.utc).timestamp()); now = int(time.time())
pmo = {}
for fid in (60, 720, 1440):
    pmo[f"start_creation_fid{fid}"] = ph(tok_open, startTs=created, endTs=now, fidelity=fid); time.sleep(0.4)
pmo["start_creation_to_plus20d_fid1"] = ph(tok_open, startTs=created, endTs=created + 20 * 86400, fidelity=1); time.sleep(0.4)
pmo["interval_all_fid1440"] = ph(tok_open, interval="all", fidelity=1440); time.sleep(0.4)
out["polymarket_open_no_change_oct2026"] = pmo
# Polymarket closed market (Oct 2025 "25 bps cut", resolved YES)
r = S.get("https://gamma-api.polymarket.com/events", params=dict(slug="fed-decision-in-october"), timeout=30)
m = [x for x in r.json()[0]["markets"] if "25 bps" in x["question"] and "decrease" in x["question"].lower()][0]
tok_c = json.loads(m["clobTokenIds"])[0]
t0 = int(dt.datetime(2025, 9, 1, tzinfo=dt.timezone.utc).timestamp()); t1 = int(dt.datetime(2025, 10, 31, tzinfo=dt.timezone.utc).timestamp())
out["polymarket_closed_oct2025_25bp_cut"] = dict(question=m["question"], closedTime=m.get("closedTime"), umaResolutionStatus=m.get("umaResolutionStatus"),
    fid60=ph(tok_c, startTs=t0, endTs=t1, fidelity=60), fid1_lastday=ph(tok_c, startTs=t1 - 3 * 86400, endTs=t1, fidelity=1))

# Kalshi
K = "https://api.elections.kalshi.com/trade-api/v2"
r = S.get(f"{K}/events/KXFED-26OCT", params=dict(with_nested_markets="true"), timeout=30)
ev = r.json(); ms = ev.get("markets") or ev.get("event", {}).get("markets", [])
keys = sorted(ms[0].keys()) if ms else []
top = max(ms, key=lambda m: float(m.get("volume_fp") or 0)) if ms else None
ks = dict(market_keys=keys, n_markets=len(ms), top=None if not top else {k: top.get(k) for k in
     ("ticker", "yes_sub_title", "open_time", "close_time", "expected_expiration_time", "volume_fp", "open_interest_fp",
      "last_price_dollars", "yes_bid_dollars", "yes_ask_dollars", "updated_time", "status")})
if top:
    for pi, days in ((1, 3), (60, 60), (1440, 400)):
        r = S.get(f"{K}/series/KXFED/markets/{top['ticker']}/candlesticks", params=dict(start_ts=now - days * 86400, end_ts=now, period_interval=pi), timeout=30)
        c = r.json().get("candlesticks", []) if r.ok else []
        ks[f"candles_{pi}m_{days}d"] = dict(status=r.status_code, err=None if r.ok else r.text[:200], **summ([x["end_period_ts"] for x in c]))
        time.sleep(0.4)
    r = S.get(f"{K}/markets/trades", params=dict(ticker=top["ticker"], limit=1000), timeout=30)
    tr = r.json().get("trades", []) if r.ok else []
    ks["trades_live_page"] = dict(status=r.status_code, n=len(tr), newest=tr[0]["created_time"] if tr else None, oldest=tr[-1]["created_time"] if tr else None,
                                  cursor_present=bool(r.json().get("cursor")) if r.ok else None)
    r = S.get(f"{K}/historical/trades", params=dict(ticker=top["ticker"], limit=100), timeout=30)
    tr = r.json().get("trades", []) if r.ok else []
    ks["trades_historical_page"] = dict(status=r.status_code, err=None if r.ok else r.text[:200], n=len(tr),
                                        newest=tr[0]["created_time"] if tr else None, oldest=tr[-1]["created_time"] if tr else None)
out["kalshi_KXFED_26OCT"] = ks
(ROOT / "results" / "prediction_depth.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
