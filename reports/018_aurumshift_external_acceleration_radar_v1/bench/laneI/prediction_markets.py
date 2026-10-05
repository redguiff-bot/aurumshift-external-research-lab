"""laneI — L1 prediction markets: Polymarket (gamma + CLOB prices-history) & Kalshi (series KXFED, markets, candlesticks, trades).
Writes results/prediction_markets.json. Keyless, ~15 requests au total.
"""
import json, time, datetime as dt, pathlib, statistics
import requests

ROOT = pathlib.Path(__file__).parent
(ROOT / "results").mkdir(exist_ok=True)
S = requests.Session(); S.headers["User-Agent"] = "research-lab/0.1"
out = {"run_utc": dt.datetime.now(dt.timezone.utc).isoformat()}


def get(url, **params):
    t0 = time.time(); r = S.get(url, params=params, timeout=30)
    return r, round((time.time() - t0) * 1000)


def gaps(ts):
    d = [b - a for a, b in zip(ts, ts[1:])]
    return {"n": len(ts), "first": ts[0] if ts else None, "last": ts[-1] if ts else None,
            "median_step_s": statistics.median(d) if d else None, "min_step_s": min(d) if d else None,
            "max_step_s": max(d) if d else None}

# ---------- Polymarket ----------
pm = {}
r, lat = get("https://gamma-api.polymarket.com/public-search", q="fed decision october", limit_per_type=5)
ev = [e for e in r.json().get("events", []) if e["slug"].startswith("fed-decision-in-october") and not e.get("closed")]
pm["search_latency_ms"] = lat
if ev:
    slug = ev[0]["slug"]
    r, lat = get("https://gamma-api.polymarket.com/events", slug=slug)
    e = r.json()[0]
    pm["event"] = {k: e.get(k) for k in ("id", "slug", "title", "startDate", "endDate", "createdAt", "updatedAt", "closed", "resolutionSource")}
    pm["event_latency_ms"] = lat
    mk = []
    for m in e["markets"]:
        tok = json.loads(m["clobTokenIds"])[0]
        rec = {k: m.get(k) for k in ("id", "question", "conditionId", "outcomes", "outcomePrices", "volume", "lastTradePrice",
                                      "bestBid", "bestAsk", "updatedAt", "umaResolutionStatus")}
        rec["yes_token"] = tok
        mk.append(rec)
    pm["markets"] = mk
    # choose highest-volume market
    top = max(mk, key=lambda m: float(m.get("volume") or 0))
    pm["history"] = {}
    for label, params in {"interval_max_fidelity_60": dict(interval="max", fidelity=60),
                          "interval_1d_fidelity_1": dict(interval="1d", fidelity=1),
                          "startTs_7d_fidelity_1": dict(startTs=int(time.time()) - 7 * 86400, endTs=int(time.time()), fidelity=1)}.items():
        r, lat = get("https://clob.polymarket.com/prices-history", market=top["yes_token"], **params)
        h = r.json().get("history", []) if r.ok else []
        ts = [p["t"] for p in h]
        pm["history"][label] = {"status": r.status_code, "latency_ms": lat, "body_head": r.text[:200] if not r.ok else None,
                                **gaps(ts), "sample": h[:2] + h[-2:]}
        time.sleep(0.5)
    r, lat = get("https://clob.polymarket.com/book", token_id=top["yes_token"])
    b = r.json() if r.ok else {}
    pm["book"] = {"status": r.status_code, "latency_ms": lat, "timestamp": b.get("timestamp"), "hash": b.get("hash"),
                  "n_bids": len(b.get("bids", [])), "n_asks": len(b.get("asks", []))}
    r, lat = get("https://data-api.polymarket.com/trades", market=top["conditionId"], limit=5)
    pm["trades"] = {"status": r.status_code, "latency_ms": lat, "sample": r.json()[:2] if r.ok else r.text[:200]}
out["polymarket"] = pm

# ---------- Kalshi ----------
K = "https://api.elections.kalshi.com/trade-api/v2"
ks = {}
r, lat = get(f"{K}/series/KXFED"); ks["series"] = {"status": r.status_code, "latency_ms": lat, "body": r.json() if r.ok else r.text[:200]}
r, lat = get(f"{K}/events", series_ticker="KXFED", status="open", with_nested_markets="true", limit=5)
evs = r.json().get("events", []) if r.ok else []
ks["open_events"] = [{"event_ticker": e["event_ticker"], "title": e.get("title"), "n_markets": len(e.get("markets", []))} for e in evs]
if evs:
    e = sorted(evs, key=lambda e: e["event_ticker"])[0]
    ms = e.get("markets", [])
    ks["event_used"] = e["event_ticker"]
    ks["markets_sample"] = [{k: m.get(k) for k in ("ticker", "subtitle", "yes_sub_title", "open_time", "close_time", "last_price",
                                                     "yes_bid", "yes_ask", "volume", "open_interest", "status", "rules_primary")}
                            for m in ms[:3]]
    top = max(ms, key=lambda m: m.get("volume") or 0)
    now = int(time.time())
    ks["candles"] = {}
    for pi in (1, 60, 1440):
        r, lat = get(f"{K}/series/KXFED/markets/{top['ticker']}/candlesticks", start_ts=now - 7 * 86400, end_ts=now, period_interval=pi)
        c = r.json().get("candlesticks", []) if r.ok else []
        ks["candles"][f"period_{pi}m"] = {"status": r.status_code, "latency_ms": lat, "body_head": None if r.ok else r.text[:200],
                                          **gaps([x["end_period_ts"] for x in c]), "sample": c[-1:] }
        time.sleep(0.5)
    r, lat = get(f"{K}/markets/trades", ticker=top["ticker"], limit=5)
    ks["trades"] = {"status": r.status_code, "latency_ms": lat, "sample": r.json().get("trades", [])[:2] if r.ok else r.text[:200]}
    r, lat = get(f"{K}/markets/{top['ticker']}/orderbook")
    ks["orderbook"] = {"status": r.status_code, "latency_ms": lat, "head": r.text[:300]}
r, lat = get(f"{K}/historical/cutoff"); ks["historical_cutoff"] = {"status": r.status_code, "body": r.text[:300]}
out["kalshi"] = ks

(ROOT / "results" / "prediction_markets.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str)[:6000])
