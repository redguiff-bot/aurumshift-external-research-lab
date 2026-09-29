"""Observed data-latency snapshot: newest row timestamp vs wall clock + provider Last-Modified where exposed."""
import time, datetime as dt, requests, pandas as pd, io, zipfile
from lib import *
now = dt.datetime.now(dt.timezone.utc); out = {"now_utc": now.isoformat(timespec="seconds")}
def age(ts): return round((now - ts).total_seconds() / 3600, 1)
u = lambda ms: dt.datetime.fromtimestamp(ms, dt.timezone.utc)
o = get("https://api.blockchain.info/charts/n-transactions", {"timespan": "5days", "format": "json", "sampled": "false"}); v = o["body"]["values"]; out["blockchain_info_ntx"] = {"newest_x": u(v[-1]["x"]).isoformat(), "age_h": age(u(v[-1]["x"])), "last_modified": o["hdr"].get("last-modified")}
o = get("https://mempool.space/api/blocks"); out["mempool_space_tip"] = {"tip_block_time": u(o["body"][0]["timestamp"]).isoformat(), "age_min": round(age(u(o["body"][0]["timestamp"])) * 60, 1)}
o = get("https://publicreporting.cftc.gov/resource/gpe5-46if.json", {"$where": "market_and_exchange_names like 'BITCOIN - CHICAGO MERCANTILE%'", "$order": "report_date_as_yyyy_mm_dd DESC", "$limit": 1}); out["cftc_btc"] = {"newest_report_date": o["body"][0]["report_date_as_yyyy_mm_dd"], "dataset_last_modified": o["hdr"].get("last-modified")}
o = get("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance", {"page[size]": 1, "sort": "-record_date"}); out["treasury_dts"] = {"newest_record_date": o["body"]["data"][0]["record_date"]}
for d in (1, 2, 3):
    day = (now - dt.timedelta(days=d)).strftime("%Y-%m-%d"); r = requests.head(f"https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-{day}.zip", headers=UA, timeout=20)
    out[f"binance_vision_metrics_{day}"] = {"status": r.status_code, "last_modified": r.headers.get("last-modified")}
o = get("https://play.clickhouse.com/", {"user": "play", "query": "SELECT toDate(created_at) d, count() c FROM github_events WHERE created_at >= today()-6 GROUP BY d ORDER BY d FORMAT TSV"}); out["gh_playground_last6d"] = o["body"]
o = get("https://play.clickhouse.com/", {"user": "play", "query": "SELECT max(created_at), count() FROM github_events WHERE created_at > '2026-07-03' FORMAT TSV"}); out["gh_playground_after_0702"] = o["body"]
o = get("https://hn.algolia.com/api/v1/search_by_date", {"query": "bitcoin", "tags": "story", "hitsPerPage": 1}); out["hn_newest_bitcoin_story"] = {"created": o["body"]["hits"][0]["created_at"]}
o = get("https://stablecoins.llama.fi/stablecoincharts/all"); out["defillama_stable"] = {"newest": u(int(o["body"][-1]["date"])).isoformat(), "last_modified": o["hdr"].get("last-modified")}
o = get("https://www.eia.gov/dnav/pet/hist_xls/WCESTUS1w.xls", raw=True); out["eia_wpsr_xls"] = {"last_modified": o["hdr"].get("last-modified"), "newest_week_ending": str(pd.read_excel(io.BytesIO(o["body"]), sheet_name="Data 1", skiprows=2).iloc[-1, 0])}
o = get("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Bitcoin/daily/20260920/20260929", retries=5, backoff=10); out["wikipedia_newest"] = o["body"]["items"][-1]["timestamp"] if o["ok"] else o.get("status")
o = get("https://api.alternative.me/fng/", {"limit": 1}); out["fear_greed_newest"] = u(int(o["body"]["data"][0]["timestamp"])).isoformat()
o = get("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query", {"where": "1=1", "outFields": "date", "orderByFields": "date DESC", "resultRecordCount": 1, "f": "json"}); out["portwatch_newest"] = [f["attributes"] for f in o["body"]["features"]]; out["portwatch_last_modified"] = o["hdr"].get("last-modified")
jdump(out, "latency_snapshot.json"); print(json.dumps(out, indent=1, default=str) if (json:=__import__("json")) else "")
