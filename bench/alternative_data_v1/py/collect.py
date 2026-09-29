"""Collect daily research panels from free public sources. Everything is cached under ../data/raw (gitignored
if large) and reduced to small CSVs under ../data. Each collector records receipt time (UTC) in data/collect_log.json.
"""
import io, os, sys, json, time, zipfile, datetime as dt, concurrent.futures as cf
import requests, pandas as pd, numpy as np
from h import UA

D = os.path.join(os.path.dirname(__file__), "..", "data")
RAW = os.path.join(D, "raw")
os.makedirs(RAW, exist_ok=True)
LOG = os.path.join(D, "collect_log.json")
log = json.load(open(LOG)) if os.path.exists(LOG) else {}
S = requests.Session(); S.headers.update(UA)
START = "2020-09-01"

def rec(k, **kw):
    kw["recv_utc"] = dt.datetime.utcnow().isoformat() + "Z"
    log[k] = kw
    json.dump(log, open(LOG, "w"), indent=1, default=str)

def getj(url, params=None, retries=3, **kw):
    for i in range(retries):
        r = S.get(url, params=params, timeout=60, **kw)
        if r.status_code == 200:
            return r
        time.sleep(3 * (i + 1))
    r.raise_for_status()

def klines(sym):
    out = []; start = int(pd.Timestamp(START, tz="UTC").timestamp() * 1000)
    while True:
        r = getj("https://data-api.binance.vision/api/v3/klines", {"symbol": sym, "interval": "1d", "limit": 1000, "startTime": start})
        k = r.json()
        if not k: break
        out += k; start = k[-1][6] + 1
        if len(k) < 1000: break
    df = pd.DataFrame(out, columns="open_time o h l c vol close_time qvol ntrades tbv tbqv ig".split())
    for c in "o h l c vol qvol tbv tbqv".split(): df[c] = df[c].astype(float)
    df["date"] = pd.to_datetime(df.open_time, unit="ms").dt.normalize()
    df = df.drop(columns=["open_time", "close_time", "ig"]).set_index("date")
    df["ntrades"] = df.ntrades.astype(float)
    rec(f"klines_{sym}", rows=len(df), first=str(df.index[0]), last=str(df.index[-1]))
    return df

def vision_zip(url):
    fn = os.path.join(RAW, url.split("/")[-1])
    if os.path.exists(fn):
        return open(fn, "rb").read(), None
    r = S.get(url, timeout=60)
    if r.status_code != 200: return None, r.status_code
    open(fn, "wb").write(r.content)
    return r.content, r.headers.get("last-modified")

def um_metrics(sym, days):
    def one(d):
        b, lm = vision_zip(f"https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{sym}-metrics-{d}.zip")
        if b is None: return None
        z = zipfile.ZipFile(io.BytesIO(b)); df = pd.read_csv(z.open(z.namelist()[0]))
        return df
    frames = []
    with cf.ThreadPoolExecutor(8) as ex:
        for d, df in zip(days, ex.map(one, days)):
            if df is not None and len(df): frames.append(df)
    m = pd.concat(frames)
    m["create_time"] = pd.to_datetime(m.create_time)
    m = m.sort_values("create_time")
    m.to_csv(os.path.join(D, f"um_metrics_5m_{sym}.csv.gz"), index=False)
    rec(f"um_metrics_{sym}", rows=len(m), first=str(m.create_time.iloc[0]), last=str(m.create_time.iloc[-1]), days_requested=len(days), days_ok=len(frames))
    return m

def um_funding(sym, months):
    def one(mo):
        b, _ = vision_zip(f"https://data.binance.vision/data/futures/um/monthly/fundingRate/{sym}/{sym}-fundingRate-{mo}.zip")
        if b is None: return None
        z = zipfile.ZipFile(io.BytesIO(b)); return pd.read_csv(z.open(z.namelist()[0]))
    fr = []
    with cf.ThreadPoolExecutor(6) as ex:
        for df in ex.map(one, months):
            if df is not None: fr.append(df)
    f = pd.concat(fr); f["ts"] = pd.to_datetime(f.calc_time, unit="ms")
    rec(f"um_funding_{sym}", rows=len(f), first=str(f.ts.min()), last=str(f.ts.max()), months_ok=len(fr), months_requested=len(months))
    return f[["ts", "last_funding_rate"]].sort_values("ts")

def cm(asset, metrics, start=START):
    rows = []; url = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
    params = {"assets": asset, "metrics": ",".join(metrics), "frequency": "1d", "start_time": start, "page_size": 10000}
    r = getj(url, params).json(); rows += r["data"]
    while r.get("next_page_url"):
        r = getj(r["next_page_url"]).json(); rows += r["data"]
    df = pd.DataFrame(rows); df["date"] = pd.to_datetime(df.time).dt.tz_localize(None).dt.normalize()
    df = df.drop(columns=["time", "asset"]).set_index("date")
    for c in df.columns:
        if not c.endswith("status") and not c.endswith("status-time"): df[c] = pd.to_numeric(df[c], errors="coerce")
    rec(f"cm_{asset}", rows=len(df), first=str(df.index[0]), last=str(df.index[-1]), metrics=metrics)
    return df

def blockchain(chart):
    r = getj(f"https://api.blockchain.info/charts/{chart}", {"timespan": "all", "sampled": "false", "format": "json", "start": START})
    v = r.json()["values"]
    s = pd.Series({pd.to_datetime(x["x"], unit="s").normalize(): x["y"] for x in v}, name=chart)
    rec(f"bc_{chart}", rows=len(s), first=str(s.index[0]), last=str(s.index[-1]))
    return s

def main():
    today = pd.Timestamp.utcnow().tz_localize(None).normalize()
    last_full = today - pd.Timedelta(days=1)
    days = [d.strftime("%Y-%m-%d") for d in pd.date_range(START, last_full - pd.Timedelta(days=0))]
    months = [d.strftime("%Y-%m") for d in pd.date_range(START, today - pd.Timedelta(days=40), freq="MS")]
    # 1 prices
    for sym in ["BTCUSDT", "ETHUSDT"]:
        klines(sym).to_csv(os.path.join(D, f"klines_1d_{sym}.csv"))
    # 2 futures baseline + positioning stats (public exchange flows)
    for sym in ["BTCUSDT", "ETHUSDT"]:
        um_metrics(sym, days)
        um_funding(sym, months).to_csv(os.path.join(D, f"funding_8h_{sym}.csv"), index=False)
    # 3 coinmetrics community
    mets = ["FlowInExUSD", "FlowOutExUSD", "SplyExUSD", "AdrActCnt", "TxCnt", "HashRate", "FeeTotNtv", "CapMVRVCur", "AssetCompletionTime"]
    cm("btc", mets).to_csv(os.path.join(D, "cm_btc.csv"))
    try: cm("eth", ["FlowInExUSD", "FlowOutExUSD", "SplyExUSD", "AdrActCnt", "TxCnt", "AssetCompletionTime"]).to_csv(os.path.join(D, "cm_eth.csv"))
    except Exception as e: rec("cm_eth", error=repr(e))
    # 4 blockchain.com
    bcs = ["n-transactions", "mempool-size", "avg-block-size", "transaction-fees", "hash-rate", "n-unique-addresses"]
    pd.concat([blockchain(c) for c in bcs], axis=1).to_csv(os.path.join(D, "blockchain_com.csv"))
    # 5 defillama
    r = getj("https://stablecoins.llama.fi/stablecoincharts/all", {"stablecoin": 1}).json()
    r2 = getj("https://stablecoins.llama.fi/stablecoincharts/all").json()
    s = pd.Series({pd.to_datetime(int(x["date"]), unit="s").normalize(): x["totalCirculatingUSD"]["peggedUSD"] for x in r2}, name="stable_total_usd")
    s.to_frame().to_csv(os.path.join(D, "llama_stables.csv")); rec("llama_stables", rows=len(s), first=str(s.index[0]), last=str(s.index[-1]))
    r = getj("https://api.llama.fi/overview/dexs", {"excludeTotalDataChart": "false", "excludeTotalDataChartBreakdown": "true"}).json()
    s = pd.Series({pd.to_datetime(int(x[0]), unit="s").normalize(): x[1] for x in r["totalDataChart"]}, name="dex_vol_usd")
    s.to_frame().to_csv(os.path.join(D, "llama_dex.csv")); rec("llama_dex", rows=len(s), first=str(s.index[0]), last=str(s.index[-1]))
    # 6 fear & greed
    r = getj("https://api.alternative.me/fng/", {"limit": 0, "format": "json"}).json()["data"]
    f = pd.Series({pd.to_datetime(int(x["timestamp"]), unit="s").normalize(): int(x["value"]) for x in r}, name="fng").sort_index()
    f.to_frame().to_csv(os.path.join(D, "fng.csv")); rec("fng", rows=len(f), first=str(f.index[0]), last=str(f.index[-1]))
    # 7 CFTC TFF bitcoin CME (with row-level :created_at)
    sel = ":created_at,report_date_as_yyyy_mm_dd,open_interest_all,lev_money_positions_long,lev_money_positions_short,asset_mgr_positions_long,asset_mgr_positions_short,dealer_positions_long_all,dealer_positions_short_all,other_rept_positions_long,other_rept_positions_short,nonrept_positions_long_all,nonrept_positions_short_all"
    r = getj("https://publicreporting.cftc.gov/resource/gpe5-46if.json", {"$limit": 5000, "$where": "market_and_exchange_names = 'BITCOIN - CHICAGO MERCANTILE EXCHANGE'", "$select": sel, "$order": "report_date_as_yyyy_mm_dd ASC"}).json()
    c = pd.DataFrame(r); c.to_csv(os.path.join(D, "cftc_tff_btc_cme.csv"), index=False); rec("cftc_tff_btc_cme", rows=len(c), first=c.report_date_as_yyyy_mm_dd.iloc[0], last=c.report_date_as_yyyy_mm_dd.iloc[-1])
    # 8 Treasury TGA + NY Fed RRP
    rows = []; page = 1
    while True:
        r = getj("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance", {"filter": f"record_date:gte:{START},account_type:eq:Treasury General Account (TGA) Closing Balance", "sort": "record_date", "page[size]": 1000, "page[number]": page, "fields": "record_date,account_type,open_today_bal,close_today_bal"}).json()
        rows += r["data"]
        if page >= r["meta"]["total-pages"]: break
        page += 1
    t = pd.DataFrame(rows); t.to_csv(os.path.join(D, "treasury_tga.csv"), index=False); rec("treasury_tga", rows=len(t), first=t.record_date.iloc[0], last=t.record_date.iloc[-1])
    r = getj("https://markets.newyorkfed.org/api/rp/reverserepo/propositions/search.json", {"startDate": START, "endDate": str(last_full.date())}).json()
    n = pd.DataFrame(r["repo"]["operations"]); n.to_csv(os.path.join(D, "nyfed_rrp.csv"), index=False); rec("nyfed_rrp", rows=len(n))
    # 9 Wikipedia pageviews (Bitcoin, Ethereum)
    for art in ["Bitcoin", "Ethereum"]:
        r = getj(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{art}/daily/{START.replace('-','')}/{last_full.strftime('%Y%m%d')}").json()
        w = pd.Series({pd.to_datetime(x["timestamp"], format="%Y%m%d%H"): x["views"] for x in r["items"]}, name=f"wiki_{art}")
        w.to_frame().to_csv(os.path.join(D, f"wiki_{art}.csv")); rec(f"wiki_{art}", rows=len(w))
        time.sleep(2)
    # 10 npm downloads (developer ecosystem)
    for pk in ["ethers", "web3", "bitcoinjs-lib", "@solana/web3.js"]:
        parts = []
        for a, b in [("2020-09-01", "2022-02-28"), ("2022-03-01", "2023-08-31"), ("2023-09-01", "2025-02-28"), ("2025-03-01", str(last_full.date()))]:
            r = getj(f"https://api.npmjs.org/downloads/range/{a}:{b}/{pk}").json()
            parts += r.get("downloads", [])
            time.sleep(1)
        s = pd.Series({pd.Timestamp(x["day"]): x["downloads"] for x in parts}, name="npm_" + pk.replace("@", "").replace("/", "_"))
        s.to_frame().to_csv(os.path.join(D, f"npm_{s.name}.csv")); rec(f"npm_{pk}", rows=len(s))
    # 11 Deribit DVOL (control)
    out = []; st = int(pd.Timestamp(START, tz="UTC").timestamp() * 1000); end = int(time.time() * 1000)
    while st < end:
        r = getj("https://www.deribit.com/api/v2/public/get_volatility_index_data", {"currency": "BTC", "start_timestamp": st, "end_timestamp": min(end, st + 900 * 86400 * 1000), "resolution": 86400}).json()["result"]["data"]
        out += r; st += 900 * 86400 * 1000
    dv = pd.DataFrame(out, columns=["ts", "o", "h", "l", "c"]).drop_duplicates("ts"); dv["date"] = pd.to_datetime(dv.ts, unit="ms").dt.normalize()
    dv.set_index("date")[["o", "h", "l", "c"]].to_csv(os.path.join(D, "deribit_dvol_1d.csv")); rec("deribit_dvol", rows=len(dv))

if __name__ == "__main__":
    main()
    print("done")
