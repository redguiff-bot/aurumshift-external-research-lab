"""Fetch daily histories used by the incremental-information tests. Window fixed: 2023-10-01 .. 2026-09-27 (UTC).
Every dataset written to data/<name>.csv with columns: date (UTC day the value refers to / as-of), value cols..., plus fetch log."""
import io, json, sys, time, zipfile, datetime as dt, concurrent.futures as cf
import pandas as pd, numpy as np
from lib import *
START, END = "2023-10-01", "2026-09-27"
LOG = {}
def rec(name, df, o=None, note=""):
    if df is not None and len(df):
        df.to_csv(os.path.join(DATA, name + ".csv"))
    LOG[name] = {"rows": 0 if df is None else int(len(df)), "first": None if df is None or not len(df) else str(df.index.min())[:10],
                 "last": None if df is None or not len(df) else str(df.index.max())[:10], "note": note,
                 "http": None if o is None else {k: o.get(k) for k in ("status", "ms", "bytes", "hdr", "attempts", "err")}}
    print(name, LOG[name]["rows"], LOG[name]["first"], LOG[name]["last"], note, flush=True)
def ts_to_day(s): return pd.to_datetime(s, unit="s", utc=True).dt.tz_localize(None).dt.normalize()
def window(df): return df.loc[START:END]

def run(fn):
    try: fn()
    except Exception as e: LOG[fn.__name__] = {"error": repr(e)[:300]}; print("ERR", fn.__name__, repr(e)[:200], flush=True)

# ---------- BTC spot daily (Binance public mirror) ----------
def btc_spot():
    rows = []; end = int(pd.Timestamp("2026-09-28", tz="UTC").timestamp() * 1000); st = int(pd.Timestamp("2023-06-01", tz="UTC").timestamp() * 1000)
    while st < end:
        o = get("https://data-api.binance.vision/api/v3/klines", {"symbol": "BTCUSDT", "interval": "1d", "startTime": st, "limit": 1000})
        b = o["body"]; rows += b; st = b[-1][0] + 86400000
        if len(b) < 1000: break
    df = pd.DataFrame(rows).iloc[:, :9]; df.columns = ["t", "open", "high", "low", "close", "volume", "ct", "qvol", "ntrades"]
    df.index = pd.to_datetime(df.t, unit="ms").dt.normalize(); df = df[["open", "high", "low", "close", "volume", "qvol", "ntrades"]].astype(float)
    rec("btc_spot_1d", df.loc["2023-06-01":END], o)
# ---------- Yahoo (unofficial) daily for gold / crude / natgas ----------
def yahoo():
    for sym, nm in (("GC=F", "gold"), ("CL=F", "crude"), ("NG=F", "natgas")):
        o = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}", {"range": "5y", "interval": "1d"})
        r = o["body"]["chart"]["result"][0]; q = r["indicators"]["quote"][0]
        df = pd.DataFrame(q, index=pd.to_datetime(r["timestamp"], unit="s").normalize()).dropna(subset=["close"])
        df = df[~df.index.duplicated(keep="last")]
        rec(f"{nm}_fut_1d", df.loc["2023-06-01":END], o, note="Yahoo unofficial front-month continuous; roll-adjusted? NO (raw continuous)")
# ---------- Binance Vision: funding + OI metrics (futures UM) ----------
def bv_funding():
    fr = []
    for ym in pd.period_range("2023-09", "2026-08", freq="M"):
        u = f"https://data.binance.vision/data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-{ym}.zip"
        o = get(u, raw=True)
        if o["ok"]:
            z = zipfile.ZipFile(io.BytesIO(o["body"])); fr.append(pd.read_csv(z.open(z.namelist()[0])))
    d = pd.concat(fr); d["day"] = pd.to_datetime(d.calc_time, unit="ms").dt.normalize()
    df = d.groupby("day").last_funding_rate.sum().to_frame("funding_day"); rec("btc_funding_daily", df, note="Binance Vision monthly fundingRate; sum of prints per UTC day")
def bv_oi():
    days = pd.date_range("2023-09-01", END)
    def one(d):
        u = f"https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-{d:%Y-%m-%d}.zip"
        o = get(u, raw=True, retries=1)
        if not o["ok"]: return None
        z = zipfile.ZipFile(io.BytesIO(o["body"])); m = pd.read_csv(z.open(z.namelist()[0]))
        return {"day": d, "oi": m.sum_open_interest.iloc[-1], "oi_value": m.sum_open_interest_value.iloc[-1],
                "toptrader_ls_pos": m.sum_toptrader_long_short_ratio.iloc[-1], "ls_ratio": m.count_long_short_ratio.iloc[-1],
                "taker_ls_vol": m.sum_taker_long_short_vol_ratio.mean(), "n5m": len(m)}
    with cf.ThreadPoolExecutor(8) as ex: res = [r for r in ex.map(one, days) if r]
    df = pd.DataFrame(res).set_index("day"); rec("btc_oi_metrics_daily", df, note=f"Binance Vision daily metrics; {len(days)-len(df)} days missing")
# ---------- on-chain ----------
def onchain():
    cols = {}
    for ch in ("n-transactions", "n-unique-addresses", "hash-rate", "difficulty", "avg-block-size", "mempool-size", "mempool-count",
               "median-confirmation-time", "transaction-fees", "transaction-fees-usd", "estimated-transaction-volume-usd", "cost-per-transaction",
               "miners-revenue", "output-volume", "n-transactions-excluding-popular", "utxo-count", "total-bitcoins", "market-cap"):
        o = get("https://api.blockchain.info/charts/" + ch, {"timespan": "1300days", "format": "json", "sampled": "false"}, retries=2)
        if not o["ok"] or not isinstance(o["body"], dict): LOG["bc_" + ch] = {"error": o.get("status") or o.get("err")}; continue
        v = pd.DataFrame(o["body"]["values"]); v["day"] = ts_to_day(v.x)
        s = v.groupby("day").y.mean(); cols[ch] = s
        LOG["bc_" + ch] = {"rows": len(s), "period": o["body"].get("period"), "ms": o["ms"], "hdr": o["hdr"]}
        time.sleep(0.4)
    df = pd.DataFrame(cols); rec("btc_onchain_blockchaininfo", df)
def mempool_space():
    o = get("https://mempool.space/api/v1/mining/blocks/fees/3y"); b = pd.DataFrame(o["body"]); b["day"] = ts_to_day(b.timestamp)
    fees = b.groupby("day").avgFees.mean().to_frame("avg_fees_sat_per_block")
    o2 = get("https://mempool.space/api/v1/mining/blocks/sizes-weights/3y"); s = o2["body"]
    sz = pd.DataFrame(s["sizes"]); sz["day"] = ts_to_day(sz.timestamp); wt = pd.DataFrame(s["weights"]); wt["day"] = ts_to_day(wt.timestamp)
    df = fees.join(sz.groupby("day").avgSize.mean().rename("avg_block_size")).join(wt.groupby("day").avgWeight.mean().rename("avg_block_weight"))
    o3 = get("https://mempool.space/api/v1/mining/hashrate/3y"); h = pd.DataFrame(o3["body"]["hashrates"]); h["day"] = ts_to_day(h.timestamp)
    df = df.join(h.groupby("day").avgHashrate.mean().rename("hashrate_ms"))
    rec("btc_mempoolspace_blocks", df, o)
# ---------- stablecoins / DeFi (DefiLlama) ----------
def llama():
    o = get("https://stablecoins.llama.fi/stablecoincharts/all"); b = o["body"]
    df = pd.DataFrame({"date": [pd.to_datetime(int(x["date"]), unit="s") for x in b], "stable_mcap": [x["totalCirculatingUSD"].get("peggedUSD") for x in b]}).set_index("date")
    rec("stablecoin_total_mcap", df, o, note="DefiLlama total pegged-USD circulating; mcap of USD-pegged")
    o = get("https://api.llama.fi/v2/historicalChainTvl"); b = o["body"]
    df = pd.DataFrame({"date": [pd.to_datetime(x["date"], unit="s") for x in b], "defi_tvl_usd": [x["tvl"] for x in b]}).set_index("date")
    rec("defi_tvl_total", df, o, note="USD-denominated (includes token prices)")
# ---------- CFTC ----------
def cftc():
    def pull(ds, where):
        rows = []; off = 0
        while True:
            o = get(f"https://publicreporting.cftc.gov/resource/{ds}.json", {"$where": where, "$limit": 1000, "$offset": off, "$order": "report_date_as_yyyy_mm_dd"})
            b = o["body"]; rows += b
            if len(b) < 1000: break
            off += 1000
        return pd.DataFrame(rows), o
    d, o = pull("gpe5-46if", "market_and_exchange_names like 'BITCOIN - CHICAGO MERCANTILE%' AND report_date_as_yyyy_mm_dd >= '2023-06-01'")
    d["date"] = pd.to_datetime(d.report_date_as_yyyy_mm_dd).dt.normalize()
    for c in ("open_interest_all", "lev_money_positions_long", "lev_money_positions_short", "asset_mgr_positions_long", "asset_mgr_positions_short", "dealer_positions_long_all", "dealer_positions_short_all"): d[c] = d[c].astype(float)
    df = pd.DataFrame({"oi": d.open_interest_all, "lev_net": d.lev_money_positions_long - d.lev_money_positions_short,
                       "am_net": d.asset_mgr_positions_long - d.asset_mgr_positions_short, "dealer_net": d.dealer_positions_long_all - d.dealer_positions_short_all}).set_index(d.date)
    df["lev_net_pct_oi"] = df.lev_net / df.oi; df["am_net_pct_oi"] = df.am_net / df.oi
    rec("cftc_btc_cme_tff", df, o, note="TFF futures-only; report_date = as-of Tuesday; NO publication timestamp per row")
    d, o = pull("72hh-3qpy", "market_and_exchange_names like 'GOLD - COMMODITY EXCHANGE%' AND report_date_as_yyyy_mm_dd >= '2023-06-01'")
    d["date"] = pd.to_datetime(d.report_date_as_yyyy_mm_dd).dt.normalize()
    for c in ("open_interest_all", "m_money_positions_long_all", "m_money_positions_short_all", "swap_positions_long_all", "swap__positions_short_all"): d[c] = d[c].astype(float)
    df = pd.DataFrame({"oi": d.open_interest_all, "mm_net": d.m_money_positions_long_all - d.m_money_positions_short_all,
                       "swap_net": d.swap_positions_long_all - d.swap__positions_short_all}).set_index(d.date); df["mm_net_pct_oi"] = df.mm_net / df.oi
    rec("cftc_gold_comex_disagg", df, o, note="Disaggregated futures-only, COMEX gold")
    d, o = pull("72hh-3qpy", "market_and_exchange_names like 'CRUDE OIL, LIGHT SWEET-WTI - ICE FUTURES EUROPE%' AND report_date_as_yyyy_mm_dd >= '2023-06-01'")
    d["date"] = pd.to_datetime(d.report_date_as_yyyy_mm_dd).dt.normalize()
    for c in ("open_interest_all", "m_money_positions_long_all", "m_money_positions_short_all"): d[c] = d[c].astype(float)
    df = pd.DataFrame({"oi": d.open_interest_all, "mm_net": d.m_money_positions_long_all - d.m_money_positions_short_all}).set_index(d.date); df["mm_net_pct_oi"] = df.mm_net / df.oi
    rec("cftc_wti_ice_disagg", df, o, note="WTI ICE Europe managed money (NYMEX WTI would be preferable; kept simple)")
# ---------- Treasury DTS (TGA) ----------
def tga():
    rows = []; page = 1
    while True:
        o = get("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance",
                {"filter": "record_date:gte:2023-06-01,account_type:eq:Treasury General Account (TGA) Closing Balance", "page[size]": 1000, "page[number]": page, "sort": "record_date"})
        b = o["body"]["data"]; rows += b
        if len(b) < 1000: break
        page += 1
    df = pd.DataFrame(rows); 
    if not len(df):  # fallback: opening balance rows
        return
    df["date"] = pd.to_datetime(df.record_date); v = pd.to_numeric(df.open_today_bal, errors="coerce").fillna(pd.to_numeric(df.close_today_bal, errors="coerce"))
    rec("tga_balance", pd.DataFrame({"tga_musd": v.values}, index=df.date), o, note="DTS TGA closing balance ($M) by record_date")
# ---------- GitHub activity via ClickHouse public playground (GH Archive mirror) ----------
def ghdev():
    repos = ["bitcoin/bitcoin", "ethereum/go-ethereum", "lightningnetwork/lnd", "paradigmxyz/reth", "solana-labs/solana", "anza-xyz/agave", "MystenLabs/sui"]
    q = f"""SELECT toDate(created_at) d, repo_name, countIf(event_type='PushEvent') push, countIf(event_type='PullRequestEvent' AND action='closed' AND merged=1) merged_pr,
      countIf(event_type='WatchEvent') stars, countIf(event_type='IssuesEvent' AND action='opened') issues_opened, uniqExactIf(actor_login, event_type IN ('PushEvent','PullRequestEvent','IssueCommentEvent')) actors
      FROM github_events WHERE repo_name IN ({",".join("'"+r+"'" for r in repos)}) AND created_at >= '2023-06-01' AND created_at < '2026-09-28'
      GROUP BY d, repo_name ORDER BY d FORMAT CSVWithNames"""
    o = get("https://play.clickhouse.com/", {"user": "play", "query": q}, timeout=120, raw=True)
    df = pd.read_csv(io.BytesIO(o["body"])); df["d"] = pd.to_datetime(df.d)
    rec("gh_events_daily_by_repo", df.set_index("d"), o, note="ClickHouse playground github_events (GH Archive); event created_at time")
    # aggregate crypto-dev proxies
    core = df[df.repo_name.isin(["bitcoin/bitcoin", "ethereum/go-ethereum", "lightningnetwork/lnd", "paradigmxyz/reth"])].groupby("d")[["push", "merged_pr", "issues_opened", "actors"]].sum()
    star = df[df.repo_name == "bitcoin/bitcoin"].set_index("d").stars.rename("btc_stars")
    rec("gh_crypto_dev_agg", core.join(star), None, note="sum of 4 core repos; stars = bitcoin/bitcoin WatchEvents (attention)")
    # freshness probe
    o2 = get("https://play.clickhouse.com/", {"user": "play", "query": "SELECT max(created_at), now() FROM github_events FORMAT TSV"})
    LOG["gh_freshness_probe"] = o2["body"]
# ---------- attention / social ----------
def wiki():
    out = {}
    for art in ("Bitcoin", "Cryptocurrency", "Gold", "Inflation"):
        o = get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{art}/daily/20230601/20260927", retries=5, backoff=10)
        if o["ok"]:
            out[art] = pd.Series({pd.to_datetime(i["timestamp"][:8]): i["views"] for i in o["body"]["items"]})
        else: LOG["wiki_" + art] = {"status": o.get("status"), "err": o.get("err")}
        time.sleep(3)
    if out: rec("wikipedia_pageviews", pd.DataFrame(out), None, note="user agent only, en.wikipedia")
def feargreed():
    o = get("https://api.alternative.me/fng/", {"limit": 0, "format": "json"}); b = o["body"]["data"]
    df = pd.DataFrame({"date": [pd.to_datetime(int(x["timestamp"]), unit="s") for x in b], "fng": [float(x["value"]) for x in b]}).set_index("date").sort_index()
    rec("fear_greed", df, o, note="composite: volatility, momentum/volume, social, dominance, trends (documented)")
def hn():
    days = pd.date_range("2023-10-01", END)
    def one(d):
        a = int(d.timestamp()); o = get("https://hn.algolia.com/api/v1/search_by_date", {"query": "bitcoin", "tags": "story", "numericFilters": f"created_at_i>={a},created_at_i<{a+86400}", "hitsPerPage": 0}, retries=2, backoff=2)
        return (d, o["body"].get("nbHits")) if o["ok"] and isinstance(o["body"], dict) else (d, None)
    with cf.ThreadPoolExecutor(6) as ex: r = list(ex.map(one, days))
    s = pd.Series(dict(r)).rename("hn_bitcoin_stories"); rec("hn_bitcoin_daily", s.to_frame(), None, note=f"Algolia nbHits/day; {int(s.isna().sum())} failures")
# ---------- real economy ----------
def eia():
    for code, nm in (("WCESTUS1w", "crude_stocks_ex_spr"), ("NW2_EPG0_SWO_R48_BCF", "natgas_storage_lower48")):
        base = "pet/hist_xls/WCESTUS1w.xls" if code.startswith("WCE") else "ng/hist_xls/NW2_EPG0_SWO_R48_BCFw.xls"
        o = get("https://www.eia.gov/dnav/" + base, raw=True)
        if not o["ok"]: LOG["eia_" + nm] = {"status": o.get("status")}; continue
        x = pd.read_excel(io.BytesIO(o["body"]), sheet_name="Data 1", skiprows=2)
        x.columns = ["date", "value"]; x["date"] = pd.to_datetime(x["date"]); x = x.dropna().set_index("date")
        rec("eia_" + nm, x.loc["2023-06-01":END], o, note="week-ending date; final values only (no vintages)")
def portwatch():
    base = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
    o = get(base, {"where": "date >= DATE '2023-06-01'", "outFields": "date,portname,n_total,n_tanker,capacity", "orderByFields": "date", "resultRecordCount": 2000, "f": "json"}, timeout=60)
    LOG["portwatch_probe"] = {"status": o.get("status"), "keys": list(o["body"].keys()) if isinstance(o["body"], dict) else None, "err": o.get("err")}
    rows = []; off = 0
    while True:
        o = get(base, {"where": "date >= DATE '2023-06-01' AND portname IN ('Strait of Hormuz','Suez Canal','Bab el-Mandeb Strait','Panama Canal')", "outFields": "date,portname,n_total,n_tanker",
                       "orderByFields": "date", "resultOffset": off, "resultRecordCount": 2000, "f": "json"}, timeout=60)
        b = o["body"].get("features", []) if isinstance(o["body"], dict) else []
        rows += [f["attributes"] for f in b]
        if not b or not o["body"].get("exceededTransferLimit"): break
        off += len(b)
    if not rows: return
    df = pd.DataFrame(rows); df["date"] = pd.to_datetime(df["date"], unit="ms")
    w = df.pivot_table(index="date", columns="portname", values="n_tanker" if "n_tanker" in df else "n_total")
    rec("portwatch_chokepoints_tankers", w, o, note="IMF PortWatch daily transit calls (AIS-derived, tankers); nowcast, revised historically (documented)")
def weather():
    pts = {"NYC": (40.71, -74.0), "CHI": (41.88, -87.63), "DAL": (32.78, -96.8), "ATL": (33.75, -84.39), "LA": (34.05, -118.24)}; out = {}
    for k, (la, lo) in pts.items():
        o = get("https://archive-api.open-meteo.com/v1/archive", {"latitude": la, "longitude": lo, "start_date": "2023-06-01", "end_date": END, "daily": "temperature_2m_mean", "timezone": "UTC"}, retries=3, backoff=8)
        if o["ok"]: out[k] = pd.Series(o["body"]["daily"]["temperature_2m_mean"], index=pd.to_datetime(o["body"]["daily"]["time"]))
        else: LOG["wx_" + k] = {"status": o.get("status")}
        time.sleep(1)
    if out:
        t = pd.DataFrame(out); hdd = (18.3 - t).clip(lower=0).mean(axis=1).rename("hdd_us5"); cdd = (t - 18.3).clip(lower=0).mean(axis=1).rename("cdd_us5")
        rec("weather_hdd_cdd_us5", pd.concat([hdd, cdd], axis=1), None, note="Open-Meteo ERA5 reanalysis (archive); NOT point-in-time")

if __name__ == "__main__":
    which = sys.argv[1:] or ["btc_spot", "yahoo", "bv_funding", "bv_oi", "onchain", "mempool_space", "llama", "cftc", "tga", "ghdev", "feargreed", "wiki", "hn", "eia", "portwatch", "weather"]
    for n in which: run(globals()[n])
    old = {}
    p = os.path.join(RES, "fetch_log.json")
    if os.path.exists(p): old = json.load(open(p))
    old.update(LOG); jdump(old, "fetch_log.json")
