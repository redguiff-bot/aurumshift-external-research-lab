"""Targeted PIT/revision probes that go beyond 'is the endpoint alive':
 1. GDELT GKG raw files: file Last-Modified vs nominal 15-min stamp across years; record schema/date semantics
 2. GH Archive hourly file: event created_at vs file Last-Modified (receipt) latency
 3. Binance Vision: Last-Modified restatement scan (are old daily files re-uploaded?)
 4. CFTC Socrata: :created_at distribution (bulk-load vs real release stamps)
 5. Coin Metrics: AssetCompletionTime vs day-end by year; status-time recompute date
 6. Kalshi/Polymarket: history depth for settled macro markets (trade-time semantics)
 7. RSS: retention depth (oldest item age) per feed  (from probe_results.json)
 8. Wayback Machine: attempt an actual vintage comparison for restated series
"""
import io, os, re, json, gzip, time, zipfile, datetime as dt, requests, pandas as pd, numpy as np
from email.utils import parsedate_to_datetime
from h import UA
OUT = os.path.join(os.path.dirname(__file__), "..", "results"); D = os.path.join(os.path.dirname(__file__), "..", "data")
S = requests.Session(); S.headers.update(UA)
res = {}

def lm(r): 
    v = r.headers.get("last-modified"); return parsedate_to_datetime(v).replace(tzinfo=None) if v else None

# 1 GDELT
g = []
for stamp in ["20160101120000", "20180601120000", "20200601120000", "20220601120000", "20240601120000", "20260601120000", "20260928120000"]:
    url = f"http://data.gdeltproject.org/gdeltv2/{stamp}.gkg.csv.zip"
    r = S.get(url, timeout=120)
    if r.status_code != 200: g.append(dict(stamp=stamp, status=r.status_code)); continue
    z = zipfile.ZipFile(io.BytesIO(r.content)); txt = z.read(z.namelist()[0]).decode("utf8", "ignore"); lines = txt.splitlines()
    nominal = dt.datetime.strptime(stamp, "%Y%m%d%H%M%S")
    dates = set(l.split("\t")[1] for l in lines if l.count("\t") > 3)
    btc = sum(1 for l in lines if re.search(r"bitcoin|crypto|CRYPTO", l))
    g.append(dict(stamp=stamp, status=200, rows=len(lines), last_modified=str(lm(r)), lm_minus_nominal_min=round((lm(r) - nominal).total_seconds() / 60, 1),
                  distinct_V21DATE=sorted(dates)[:3], crypto_mention_rows=btc, bytes=len(r.content), first_col_sample=lines[0].split("\t")[:2]))
    time.sleep(1)
res["gdelt_gkg"] = g

# 2 GH Archive one hour
url = "https://data.gharchive.org/2026-09-27-12.json.gz"
r = S.get(url, timeout=300)
if r.status_code == 200:
    lmt = lm(r); n = 0; lo = hi = None; types = {}; push = 0
    for line in gzip.GzipFile(fileobj=io.BytesIO(r.content)):
        o = json.loads(line); n += 1; c = o["created_at"]; lo = c if lo is None or c < lo else lo; hi = c if hi is None or c > hi else hi
        types[o["type"]] = types.get(o["type"], 0) + 1
    res["gharchive"] = dict(events=n, first_created=lo, last_created=hi, last_modified=str(lmt), lm_minus_hour_end_min=round((lmt - dt.datetime(2026, 9, 27, 13)).total_seconds() / 60, 1), types=dict(sorted(types.items(), key=lambda x: -x[1])[:6]), bytes=len(r.content))
else:
    res["gharchive"] = dict(status=r.status_code)

# 3 Binance vision restatement scan (metrics + klines): sample 40 dates
rows = []
for d in pd.date_range("2021-01-05", "2026-09-20", periods=40):
    ds = d.strftime("%Y-%m-%d")
    for kind, url in (("um_metrics", f"https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-{ds}.zip"), ("spot_kline_1d", f"https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-{ds}.zip")):
        r = S.head(url, timeout=30)
        if r.status_code == 200:
            l = parsedate_to_datetime(r.headers["last-modified"]).replace(tzinfo=None)
            rows.append(dict(kind=kind, day=ds, lm=str(l), lag_days=round((l - (d + pd.Timedelta(days=1)).to_pydatetime()).total_seconds() / 86400, 2)))
bv = pd.DataFrame(rows); bv["restated"] = bv.lag_days > 3
res["binance_vision"] = {k: dict(n=int(len(v)), restated_gt3d=int(v.restated.sum()), median_lag_days=float(v.lag_days.median()), max_lag_days=float(v.lag_days.max())) for k, v in bv.groupby("kind")}
bv.to_csv(os.path.join(OUT, "binance_vision_lastmodified_scan.csv"), index=False)

# 4 CFTC created_at
c = pd.read_csv(os.path.join(D, "cftc_tff_btc_cme.csv")); ca = pd.to_datetime(c[":created_at"], utc=True).dt.tz_localize(None); rep = pd.to_datetime(c.report_date_as_yyyy_mm_dd)
bulk = ca.dt.date == dt.date(2022, 9, 13)
lagd = (ca - rep).dt.total_seconds() / 86400
res["cftc"] = dict(rows=len(c), bulk_loaded_rows=int(bulk.sum()), first_real_stamp_row_date=str(rep[~bulk].min().date()), real_rows=int((~bulk).sum()),
                   real_lag_days_median=float(lagd[~bulk].median()), real_lag_days_p90=float(lagd[~bulk].quantile(.9)), real_lag_days_max=float(lagd[~bulk].max()),
                   weekday_of_created=ca[~bulk].dt.day_name().value_counts().to_dict())

# 5 Coin Metrics completion
cm = pd.read_csv(os.path.join(D, "cm_btc.csv"), index_col=0, parse_dates=True)
lag = (pd.to_datetime(cm.AssetCompletionTime, unit="s") - (cm.index + pd.Timedelta(days=1))).dt.total_seconds() / 3600
st = pd.to_datetime(cm["FlowInExUSD-status-time"], utc=True).dt.tz_localize(None)
res["coinmetrics"] = dict(completion_lag_h_median_by_year=lag.groupby(cm.index.year).median().round(2).to_dict(), backfilled_rows_lag_gt_72h=int((lag > 72).sum()), rows=len(cm),
                          status_values=cm["FlowInExUSD-status"].value_counts().to_dict(), status_time_month_counts=st.dt.to_period("M").astype(str).value_counts().sort_index().to_dict(),
                          rows_recomputed_after_completion_gt_30d=int(((st - pd.to_datetime(cm.AssetCompletionTime, unit="s")).dt.days > 30).sum()))

# 6 prediction markets
pm = {}
r = S.get("https://api.elections.kalshi.com/trade-api/v2/markets", params={"series_ticker": "KXFED", "status": "settled", "limit": 100}, timeout=30).json()
mk = r.get("markets", []); pm["kalshi_kxfed_settled_markets_first_page"] = len(mk)
if mk:
    m = mk[0]; t = m["ticker"]; o = pd.Timestamp(m["open_time"]); cl = pd.Timestamp(m["close_time"])
    rr = S.get(f"https://api.elections.kalshi.com/trade-api/v2/series/KXFED/markets/{t}/candlesticks", params={"start_ts": int(o.timestamp()), "end_ts": int(cl.timestamp()), "period_interval": 1440}, timeout=30)
    pm["kalshi_candles"] = dict(status=rr.status_code, n=len(rr.json().get("candlesticks", [])) if rr.status_code == 200 else None, open=str(o), close=str(cl), ticker=t)
    try: pm["kalshi_market_keys_time"] = {k: m[k] for k in m if "time" in k or "ts" in k}
    except Exception: pass
r = S.get("https://gamma-api.polymarket.com/public-search", params={"q": "fed rate decision", "limit_per_type": 5}, timeout=30).json()
ev = r.get("events", []); pm["polymarket_fed_events"] = len(ev)
for e in ev:
    if e.get("closed") and e.get("markets"):
        mm = e["markets"][0]; tok = json.loads(mm["clobTokenIds"])[0] if isinstance(mm.get("clobTokenIds"), str) else None
        if tok:
            for fid in (60, 1440):
                h = S.get("https://clob.polymarket.com/prices-history", params={"market": tok, "interval": "max", "fidelity": fid}, timeout=30)
                pm[f"polymarket_history_fidelity_{fid}"] = dict(status=h.status_code, n=len(h.json().get("history", [])) if h.status_code == 200 else None, title=e["title"][:70])
            break
res["prediction_markets"] = pm

# 7 RSS retention
pr = {x["id"]: x for x in json.load(open(os.path.join(OUT, "probe_results.json")))}
rt = {}
for k, v in pr.items():
    if k.startswith("rss_") or k in ("reddit_rss", "hackernews_algolia", "stocktwits_stream", "mastodon_tag_bitcoin"):
        if v.get("first_utc") and v.get("last_utc"):
            rt[k] = dict(items=v.get("n"), span_hours=round((pd.Timestamp(v["last_utc"]) - pd.Timestamp(v["first_utc"])).total_seconds() / 3600, 1))
        else: rt[k] = dict(items=v.get("n"), status=v.get("status"), note="no parsable timestamps or blocked")
res["rss_retention"] = rt

# 8 Wayback vintage attempt
wb = {}
for name, url in (("fng", "api.alternative.me/fng/?limit=0"), ("llama_stables", "stablecoins.llama.fi/stablecoincharts/all?stablecoin=1")):
    time.sleep(8)
    r = S.get("https://archive.org/wayback/available", params={"url": url, "timestamp": "20240601"}, timeout=30)
    wb[name] = dict(status=r.status_code, body=r.text[:250])
res["wayback"] = wb
json.dump(res, open(os.path.join(OUT, "pit_probes.json"), "w"), indent=1, default=str)
print(json.dumps(res, indent=1, default=str)[:6000])
