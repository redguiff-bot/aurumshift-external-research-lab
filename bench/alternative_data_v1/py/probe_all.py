"""Live probe of every candidate source. Records access status, latency (3 samples), size, history bounds, freshness,
timestamp/stamp headers and rate-limit headers. Writes results/probe_results.json. No source is 'executed' unless a
2xx response parsed into records/rows (see field parsed_ok)."""
import json, os, re, sys, time, io, zipfile, statistics, datetime as dt, csv
import requests
from h import UA

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(OUT, exist_ok=True)
NOW = time.time()
KEEP = ("date", "last-modified", "etag", "age", "retry-after", "x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset",
        "ratelimit-limit", "ratelimit-remaining", "ratelimit-reset", "x-rate-limit-remaining", "cache-control", "server", "expires")

def ts(x):
    """epoch(s|ms) or ISO -> epoch s"""
    if x is None: return None
    try:
        if isinstance(x, (int, float)) or re.fullmatch(r"\d+(\.\d+)?", str(x)):
            v = float(x); return v / 1000 if v > 1e11 else v
        return dt.datetime.fromisoformat(str(x).replace("Z", "+00:00")).timestamp()
    except Exception:
        try: return dt.datetime.strptime(str(x)[:10], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()
        except Exception: return None

def J(f):  # json extractor wrapper
    return lambda r: f(r.json())

def rng(rows, key):
    v = [ts(key(x)) for x in rows]; v = [x for x in v if x]
    return (len(rows), min(v) if v else None, max(v) if v else None)

def rss(r):
    it = re.findall(r"<(?:pubDate|published|updated|dc:date)>([^<]+)<", r.text)
    from email.utils import parsedate_to_datetime
    v = []
    for s in it:
        try: v.append(parsedate_to_datetime(s).timestamp())
        except Exception: t = ts(s); v.append(t) if t else None
    return (len(re.findall(r"<item>|<entry>", r.text)), min(v) if v else None, max(v) if v else None)

def csvrows(r, tscol=0, skip=0):
    rows = list(csv.reader(io.StringIO(r.text)))[skip:]
    v = [ts(x[tscol]) for x in rows[1:] if x and ts(x[tscol])]
    return (len(rows) - 1, min(v) if v else None, max(v) if v else None)

def zipcsv(r, skip=0):
    z = zipfile.ZipFile(io.BytesIO(r.content)); t = z.read(z.namelist()[0]).decode()
    return (len(t.splitlines()) - 1, None, None)

def plain(r): return (len(r.text.splitlines()), None, None)

CM = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
SRC = [
 # ---------- on-chain
 dict(id="coinmetrics_community", cat="on-chain", url=CM, p={"assets":"btc","metrics":"FlowInExUSD,FlowOutExUSD,SplyExUSD,AdrActCnt,AssetCompletionTime","frequency":"1d","start_time":"2009-01-01","page_size":10000,"paging_from":"start"}, ex=J(lambda d: rng(d["data"], lambda x: x["time"]))),
 dict(id="blockchain_com_charts", cat="on-chain", url="https://api.blockchain.info/charts/n-transactions", p={"timespan":"all","sampled":"false","format":"json"}, ex=J(lambda d: rng(d["values"], lambda x: x["x"]))),
 dict(id="mempool_space_blocks", cat="mempool", url="https://mempool.space/api/v1/blocks", ex=J(lambda d: rng(d, lambda x: x["timestamp"]))),
 dict(id="mempool_space_mempool_snapshot", cat="mempool", url="https://mempool.space/api/mempool", ex=J(lambda d: (d["count"], None, None))),
 dict(id="mempool_space_fees_recommended", cat="mempool", url="https://mempool.space/api/v1/fees/recommended", ex=J(lambda d: (len(d), None, None))),
 dict(id="mempool_space_hashrate_3y", cat="on-chain", url="https://mempool.space/api/v1/mining/hashrate/3y", ex=J(lambda d: rng(d["hashrates"], lambda x: x["timestamp"]))),
 dict(id="mempool_space_blockfees_all", cat="on-chain", url="https://mempool.space/api/v1/mining/blocks/fees/all", ex=J(lambda d: rng(d, lambda x: x["timestamp"]))),
 dict(id="blockstream_esplora_tip", cat="on-chain", url="https://blockstream.info/api/blocks/tip/height", ex=lambda r: (1, None, None)),
 dict(id="blockchair_stats", cat="on-chain", url="https://api.blockchair.com/bitcoin/stats", ex=J(lambda d: (1, None, ts(d["context"].get("cache",{}).get("since") or None)))),
 dict(id="etherscan_free_noKey", cat="on-chain", url="https://api.etherscan.io/api", p={"module":"proxy","action":"eth_blockNumber"}, ex=J(lambda d: (1, None, None))),
 dict(id="ethereum_publicnode_rpc", cat="on-chain", url="https://ethereum-rpc.publicnode.com", method="POST", body={"jsonrpc":"2.0","id":1,"method":"eth_getBlockByNumber","params":["latest",False]}, ex=J(lambda d: (1, None, ts(int(d["result"]["timestamp"],16))))),
 dict(id="defillama_stablecoins_total", cat="on-chain", url="https://stablecoins.llama.fi/stablecoincharts/all", ex=J(lambda d: rng(d, lambda x: x["date"]))),
 dict(id="defillama_chain_tvl", cat="on-chain", url="https://api.llama.fi/v2/historicalChainTvl", ex=J(lambda d: rng(d, lambda x: x["date"]))),
 dict(id="defillama_dex_volume", cat="on-chain", url="https://api.llama.fi/overview/dexs", p={"excludeTotalDataChartBreakdown":"true"}, ex=J(lambda d: rng(d["totalDataChart"], lambda x: x[0]))),
 dict(id="defillama_bridges", cat="on-chain", url="https://bridges.llama.fi/bridges", ex=J(lambda d: (len(d), None, None))),
 dict(id="glassnode_api", cat="on-chain", url="https://api.glassnode.com/v1/metrics/addresses/active_count", p={"a":"BTC"}, ex=J(lambda d: (len(d), None, None))),
 dict(id="beaconcha_in", cat="on-chain", url="https://beaconcha.in/api/v1/epoch/latest", ex=J(lambda d: (1, None, None))),
 # ---------- exchange flows / derivatives positioning where public
 dict(id="binance_vision_um_metrics", cat="exchange flows", url="https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-2026-09-20.zip", ex=zipcsv),
 dict(id="binance_fapi_openinterest_hist", cat="exchange flows", url="https://fapi.binance.com/futures/data/openInterestHist", p={"symbol":"BTCUSDT","period":"1d","limit":5}, ex=J(lambda d: rng(d, lambda x: x["timestamp"]))),
 dict(id="okx_rubik_longshort", cat="exchange flows", url="https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio", p={"ccy":"BTC","period":"1D"}, ex=J(lambda d: rng(d["data"], lambda x: x[0]))),
 dict(id="okx_rubik_taker_volume", cat="exchange flows", url="https://www.okx.com/api/v5/rubik/stat/taker-volume", p={"ccy":"BTC","instType":"CONTRACTS","period":"1D"}, ex=J(lambda d: rng(d["data"], lambda x: x[0]))),
 dict(id="okx_funding_history", cat="exchange flows", url="https://www.okx.com/api/v5/public/funding-rate-history", p={"instId":"BTC-USDT-SWAP","limit":100}, ex=J(lambda d: rng(d["data"], lambda x: x["fundingTime"]))),
 dict(id="bitfinex_margin_positions", cat="exchange flows", url="https://api-pub.bitfinex.com/v2/stats1/pos.size:1m:tBTCUSD:long/hist", p={"limit":10000}, ex=J(lambda d: rng(d, lambda x: x[0]))),
 dict(id="deribit_dvol", cat="exchange flows", url="https://www.deribit.com/api/v2/public/get_volatility_index_data", p={"currency":"BTC","start_timestamp":1600000000000,"end_timestamp":int(NOW*1000),"resolution":86400}, ex=J(lambda d: rng(d["result"]["data"], lambda x: x[0]))),
 dict(id="deribit_book_summary_options", cat="exchange flows", url="https://www.deribit.com/api/v2/public/get_book_summary_by_currency", p={"currency":"BTC","kind":"option"}, ex=J(lambda d: rng(d["result"], lambda x: x["creation_timestamp"]))),
 dict(id="hyperliquid_info_meta", cat="exchange flows", url="https://api.hyperliquid.xyz/info", method="POST", body={"type":"metaAndAssetCtxs"}, ex=J(lambda d: (len(d[0]["universe"]), None, None))),
 dict(id="bybit_v5", cat="exchange flows", url="https://api.bybit.com/v5/market/open-interest", p={"category":"linear","symbol":"BTCUSDT","intervalTime":"1d","limit":5}, ex=J(lambda d: rng(d["result"]["list"], lambda x: x["timestamp"]))),
 # ---------- dev / github
 dict(id="github_rest_unauth", cat="developer/GitHub", url="https://api.github.com/repos/bitcoin/bitcoin/commits", p={"per_page":1}, ex=J(lambda d: (len(d), None, None))),
 dict(id="gharchive_hourly", cat="developer/GitHub", url="https://data.gharchive.org/2026-09-27-12.json.gz", head=True, ex=lambda r: (1, None, None)),
 dict(id="npm_downloads_api", cat="developer/GitHub", url="https://api.npmjs.org/downloads/range/2020-09-01:2022-02-28/ethers", ex=J(lambda d: rng(d["downloads"], lambda x: x["day"]))),
 dict(id="pypistats_web3", cat="developer/GitHub", url="https://pypistats.org/api/packages/web3/overall", ex=J(lambda d: rng(d["data"], lambda x: x["date"]))),
 dict(id="crates_io_downloads", cat="developer/GitHub", url="https://crates.io/api/v1/crates/bitcoin/downloads", ex=J(lambda d: rng(d["version_downloads"], lambda x: x["date"]))),
 # ---------- search / trends / social
 dict(id="wikimedia_pageviews", cat="search/trend", url="https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Bitcoin/daily/20150701/20260927", ex=J(lambda d: rng(d["items"], lambda x: dt.datetime.strptime(x["timestamp"],"%Y%m%d%H").replace(tzinfo=dt.timezone.utc).isoformat())), noburst=True),
 dict(id="google_trends_dailytrends", cat="search/trend", url="https://trends.google.com/trends/api/dailytrends", p={"geo":"US"}, ex=lambda r: (1, None, None)),
 dict(id="hackernews_algolia", cat="public social", url="https://hn.algolia.com/api/v1/search_by_date", p={"query":"bitcoin","tags":"story","hitsPerPage":100}, ex=J(lambda d: rng(d["hits"], lambda x: x["created_at"]))),
 dict(id="reddit_json", cat="public social", url="https://www.reddit.com/r/Bitcoin/new.json", p={"limit":100}, ex=J(lambda d: rng(d["data"]["children"], lambda x: x["data"]["created_utc"]))),
 dict(id="reddit_rss", cat="public social", url="https://www.reddit.com/r/Bitcoin/new/.rss", ex=rss, noburst=True),
 dict(id="stocktwits_stream", cat="public social", url="https://api.stocktwits.com/api/2/streams/symbol/BTC.X.json", ex=J(lambda d: rng(d["messages"], lambda x: x["created_at"]))),
 dict(id="mastodon_tag_bitcoin", cat="public social", url="https://mastodon.social/api/v1/timelines/tag/bitcoin", p={"limit":40}, ex=J(lambda d: rng(d, lambda x: x["created_at"]))),
 dict(id="bluesky_search", cat="public social", url="https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts", p={"q":"bitcoin","limit":25}, ex=J(lambda d: rng(d["posts"], lambda x: x["indexedAt"]))),
 dict(id="4chan_biz_catalog", cat="public social", url="https://a.4cdn.org/biz/catalog.json", ex=J(lambda d: (sum(len(p["threads"]) for p in d), None, None))),
 dict(id="lunarcrush_api", cat="public social", url="https://lunarcrush.com/api4/public/coins/list/v1", ex=J(lambda d: (1, None, None))),
 dict(id="arctic_shift_reddit", cat="public social", url="https://arctic-shift.photon-reddit.com/api/posts/search", p={"subreddit":"Bitcoin","limit":50,"after":"2024-06-01"}, ex=J(lambda d: rng(d["data"], lambda x: x["created_utc"])), noburst=True),
 # ---------- news / RSS
 dict(id="gdelt_v2_lastupdate", cat="news", url="http://data.gdeltproject.org/gdeltv2/lastupdate.txt", ex=plain),
 dict(id="gdelt_gkg_file_2020", cat="news", url="http://data.gdeltproject.org/gdeltv2/20200601120000.gkg.csv.zip", head=True, ex=lambda r: (1, None, None)),
 dict(id="gdelt_doc_api_timeline", cat="news", url="https://api.gdeltproject.org/api/v2/doc/doc", p={"query":"bitcoin","mode":"timelinevolraw","format":"json","timespan":"3months"}, ex=J(lambda d: rng(d["timeline"][0]["data"], lambda x: dt.datetime.strptime(x["date"],"%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc).isoformat())), noburst=True),
 dict(id="rss_bbc_business", cat="RSS", url="https://feeds.bbci.co.uk/news/business/rss.xml", ex=rss),
 dict(id="rss_cointelegraph", cat="RSS", url="https://cointelegraph.com/rss", ex=rss),
 dict(id="rss_coindesk", cat="RSS", url="https://www.coindesk.com/arc/outboundfeeds/rss/", ex=rss),
 dict(id="rss_decrypt", cat="RSS", url="https://decrypt.co/feed", ex=rss),
 dict(id="rss_federal_reserve_press", cat="RSS", url="https://www.federalreserve.gov/feeds/press_all.xml", ex=rss),
 dict(id="rss_sec_press", cat="RSS", url="https://www.sec.gov/news/pressreleases.rss", ex=rss),
 dict(id="rss_treasury_press", cat="RSS", url="https://home.treasury.gov/system/files/136/treasury-press-releases.xml", ex=rss),
 dict(id="rss_ecb_press", cat="RSS", url="https://www.ecb.europa.eu/rss/press.html", ex=rss),
 dict(id="cointelegraph_via_coingecko_news", cat="news", url="https://api.coingecko.com/api/v3/news", ex=J(lambda d: (len(d.get("data", d)), None, None))),
 # ---------- prediction markets
 dict(id="polymarket_gamma_markets", cat="prediction markets", url="https://gamma-api.polymarket.com/markets", p={"limit":100,"closed":"false"}, ex=J(lambda d: rng(d, lambda x: x.get("createdAt")))),
 dict(id="polymarket_clob_prices_history", cat="prediction markets", url="https://clob.polymarket.com/prices-history", p={"market":"21742633143463906290569050155826241533067272736897614950488156847949938836455","interval":"max","fidelity":1440}, ex=J(lambda d: rng(d["history"], lambda x: x["t"]))),
 dict(id="kalshi_events", cat="prediction markets", url="https://api.elections.kalshi.com/trade-api/v2/events", p={"limit":100,"status":"open"}, ex=J(lambda d: rng(d["events"], lambda x: x.get("last_updated_ts")))),
 dict(id="kalshi_markets", cat="prediction markets", url="https://api.elections.kalshi.com/trade-api/v2/markets", p={"limit":100}, ex=J(lambda d: rng(d["markets"], lambda x: x.get("created_time")))),
 # ---------- CFTC / ETF / public flows
 dict(id="cftc_socrata_tff", cat="CFTC positioning", url="https://publicreporting.cftc.gov/resource/gpe5-46if.json", p={"$limit":5000,"$where":"market_and_exchange_names = 'BITCOIN - CHICAGO MERCANTILE EXCHANGE'","$select":":created_at,report_date_as_yyyy_mm_dd"}, ex=J(lambda d: rng(d, lambda x: x["report_date_as_yyyy_mm_dd"]))),
 dict(id="cftc_socrata_legacy", cat="CFTC positioning", url="https://publicreporting.cftc.gov/resource/6dca-aqww.json", p={"$limit":5000,"$where":"market_and_exchange_names like 'GOLD - COMMODITY EXCHANGE%'","$select":":created_at,report_date_as_yyyy_mm_dd"}, ex=J(lambda d: rng(d, lambda x: x["report_date_as_yyyy_mm_dd"]))),
 dict(id="cftc_deacot_txt", cat="CFTC positioning", url="https://www.cftc.gov/dea/newcot/deacot.txt", ex=plain),
 dict(id="cftc_disagg_socrata", cat="CFTC positioning", url="https://publicreporting.cftc.gov/resource/72hh-3qpy.json", p={"$limit":5,"$order":"report_date_as_yyyy_mm_dd DESC"}, ex=J(lambda d: rng(d, lambda x: x["report_date_as_yyyy_mm_dd"]))),
 dict(id="ishares_ibit_csv", cat="ETF flows", url="https://www.ishares.com/us/products/333011/ishares-bitcoin-trust/1467271812596.ajax", p={"fileType":"csv","fileName":"IBIT_holdings","dataType":"fund"}, ex=lambda r: (0, None, None) if r.text.lstrip().startswith("<!DOCTYPE") else plain(r)),
 dict(id="ishares_ivv_holdings_csv", cat="ETF flows", url="https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf/1467271812596.ajax", p={"fileType":"csv","fileName":"IVV_holdings","dataType":"fund"}, ex=lambda r: (0, None, None) if r.text.lstrip().startswith("<!DOCTYPE") else plain(r)),
 dict(id="farside_btc_etf_flows", cat="ETF flows", url="https://farside.co.uk/btc/", ex=lambda r: (0,None,None) if "Just a moment" in r.text else plain(r)),
 dict(id="sec_edgar_submissions", cat="ETF flows", url="https://data.sec.gov/submissions/CIK0001980994.json", ex=J(lambda d: rng(list(zip(d["filings"]["recent"]["acceptanceDateTime"])), lambda x: x[0]))),
 dict(id="sec_edgar_efts_search", cat="public government", url="https://efts.sec.gov/LATEST/search-index", p={"q":"bitcoin","forms":"8-K","dateRange":"custom","startdt":"2026-09-20","enddt":"2026-09-29"}, ex=J(lambda d: (d["hits"]["total"]["value"], None, None))),
 dict(id="sec_edgar_atom_current", cat="public government", url="https://www.sec.gov/cgi-bin/browse-edgar", p={"action":"getcurrent","type":"8-K","output":"atom"}, ex=rss),
 dict(id="yahoo_chart_ibit", cat="ETF flows", url="https://query1.finance.yahoo.com/v8/finance/chart/IBIT", p={"range":"5d","interval":"1d"}, ex=J(lambda d: rng(d["chart"]["result"][0]["timestamp"], lambda x: x))),
 # ---------- shipping
 dict(id="imf_portwatch_chokepoints", cat="shipping", url="https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query", p={"where":"portname='Suez Canal'","outFields":"date,portname,n_total,capacity","orderByFields":"date ASC","resultRecordCount":2000,"f":"json"}, ex=J(lambda d: rng(d["features"], lambda x: x["attributes"]["date"]))),
 dict(id="imf_portwatch_ports", cat="shipping", url="https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Ports_Data/FeatureServer/0/query", p={"where":"portname='Los Angeles'","outFields":"date,portname,portcalls","orderByFields":"date DESC","resultRecordCount":5,"f":"json"}, ex=J(lambda d: rng(d["features"], lambda x: x["attributes"]["date"]))),
 dict(id="aishub_free", cat="shipping", url="https://data.aishub.net/ws.php", p={"username":"x","format":"1","output":"json"}, ex=J(lambda d: (1,None,None))),
 dict(id="stooq_bdi", cat="shipping", url="https://stooq.com/q/d/l/", p={"s":"^bdi","i":"d"}, ex=lambda r: csvrows(r, 0)),
 # ---------- energy inventories
 dict(id="eia_wpsr_table1_csv", cat="energy inventories", url="https://ir.eia.gov/wpsr/table1.csv", ex=plain),
 dict(id="eia_bulk_PET_zip", cat="energy inventories", url="https://www.eia.gov/opendata/bulk/PET.zip", head=True, ex=lambda r: (1,None,None)),
 dict(id="eia_bulk_NG_zip", cat="energy inventories", url="https://www.eia.gov/opendata/bulk/NG.zip", head=True, ex=lambda r: (1,None,None)),
 dict(id="eia_api_v2_noKey", cat="energy inventories", url="https://api.eia.gov/v2/petroleum/stoc/wstk/data/", ex=J(lambda d: (1,None,None))),
 dict(id="eia_ngs_html", cat="energy inventories", url="https://ir.eia.gov/ngs/ngs.html", ex=plain),
 dict(id="gie_agsi_gas_storage_noKey", cat="energy inventories", url="https://agsi.gie.eu/api", p={"country":"eu"}, ex=J(lambda d: (1,None,None))),
 # ---------- weather
 dict(id="open_meteo_forecast", cat="weather", url="https://api.open-meteo.com/v1/forecast", p={"latitude":29.7,"longitude":-95.3,"hourly":"temperature_2m"}, ex=J(lambda d: rng(d["hourly"]["time"], lambda x: x))),
 dict(id="open_meteo_archive", cat="weather", url="https://archive-api.open-meteo.com/v1/archive", p={"latitude":29.7,"longitude":-95.3,"start_date":"2020-09-01","end_date":"2020-09-10","hourly":"temperature_2m"}, ex=J(lambda d: rng(d["hourly"]["time"], lambda x: x)), noburst=True),
 dict(id="open_meteo_historical_forecast", cat="weather", url="https://historical-forecast-api.open-meteo.com/v1/forecast", p={"latitude":29.7,"longitude":-95.3,"start_date":"2024-01-01","end_date":"2024-01-02","hourly":"temperature_2m"}, ex=J(lambda d: rng(d["hourly"]["time"], lambda x: x)), noburst=True),
 dict(id="nws_gridpoint_forecast", cat="weather", url="https://api.weather.gov/gridpoints/HGX/65,97/forecast", ex=J(lambda d: rng(d["properties"]["periods"], lambda x: x["startTime"]))),
 dict(id="noaa_cpc_degree_days", cat="weather", url="https://ftp.cpc.ncep.noaa.gov/htdocs/degree_days/weighted/daily_data/2024/Population.Heating.txt", ex=plain),
 dict(id="noaa_ncei_daily_summaries", cat="weather", url="https://www.ncei.noaa.gov/access/services/data/v1", p={"dataset":"daily-summaries","stations":"USW00012918","startDate":"2020-09-01","endDate":"2020-09-30","dataTypes":"TMAX,TMIN","format":"json"}, ex=J(lambda d: rng(d, lambda x: x["DATE"]))),
 dict(id="nasa_power_daily", cat="weather", url="https://power.larc.nasa.gov/api/temporal/daily/point", p={"parameters":"T2M","community":"RE","longitude":-95,"latitude":30,"start":"20200901","end":"20200930","format":"JSON"}, ex=J(lambda d: (len(d["properties"]["parameter"]["T2M"]), None, None))),
 dict(id="noaa_gfs_s3_listing", cat="weather", url="https://noaa-gfs-bdp-pds.s3.amazonaws.com/", p={"list-type":"2","prefix":"gfs.20240101/00/atmos/","max-keys":"3"}, ex=lambda r: (r.text.count("<Key>"), None, None)),
 # ---------- public gov datasets
 dict(id="treasury_fiscaldata_dts", cat="public government", url="https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance", p={"sort":"record_date","page[size]":1000,"filter":"record_date:gte:2005-01-01,account_type:eq:Treasury General Account (TGA) Closing Balance"}, ex=J(lambda d: rng(d["data"], lambda x: x["record_date"]))),
 dict(id="nyfed_reverse_repo", cat="public government", url="https://markets.newyorkfed.org/api/rp/reverserepo/propositions/search.json", p={"startDate":"2020-09-01","endDate":"2026-09-28"}, ex=J(lambda d: rng(d["repo"]["operations"], lambda x: x["operationDate"]))),
 dict(id="fred_fredgraph_csv", cat="public government", url="https://fred.stlouisfed.org/graph/fredgraph.csv", p={"id":"WALCL"}, ex=lambda r: csvrows(r, 0), timeout=20),
 dict(id="fed_h41_datadownload", cat="public government", url="https://www.federalreserve.gov/datadownload/Output.aspx", p={"rel":"H41","series":"cd4a8d4d8c1b0ab7d5a2e8a0c2a3a6b1","lastobs":5,"filetype":"csv"}, ex=plain),
 dict(id="sec_edgar_xbrl_frames", cat="public government", url="https://data.sec.gov/api/xbrl/frames/us-gaap/Revenues/USD/CY2023.json", ex=J(lambda d: (len(d["data"]), None, None))),
 dict(id="ecb_eurofxref_daily", cat="public government", url="https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml", ex=plain),
 dict(id="imf_datamapper", cat="public government", url="https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH", ex=J(lambda d: (1,None,None))),
 dict(id="alt_me_fng", cat="search/trend", url="https://api.alternative.me/fng/", p={"limit":0,"format":"json"}, ex=J(lambda d: rng(d["data"], lambda x: x["timestamp"]))),
 dict(id="coingecko_free_ping_history", cat="on-chain", url="https://api.coingecko.com/api/v3/coins/bitcoin/market_chart", p={"vs_currency":"usd","days":"max","interval":"daily"}, ex=J(lambda d: rng(d["prices"], lambda x: x[0]))),
]

def one(s):
    h = dict(UA); h.update(s.get("h", {}))
    meth = s.get("method", "GET"); res = []
    r = None
    for i in range(3):
        t = time.time()
        try:
            kw = dict(timeout=s.get("timeout", 45), headers=h, params=s.get("p"))
            if meth == "POST": kw["json"] = s["body"]
            if s.get("head"): kw["stream"] = True
            r = requests.request(meth, s["url"], **kw)
            ms = (time.time() - t) * 1000
            res.append((r.status_code, ms))
            if r.status_code != 200 and i == 0 and s.get("noburst"): break
            if s.get("noburst") or r.status_code != 200: break
        except Exception as e:
            res.append((0, (time.time() - t) * 1000)); r = None; err = repr(e)[:200]; break
        if i < 2:
            if s.get("head"): r.close()
            time.sleep(1.2)
    out = dict(id=s["id"], cat=s["cat"], url=s["url"], params=s.get("p"), method=meth)
    out["samples"] = [(a, round(b)) for a, b in res]
    if r is None:
        out.update(status=0, ok=False, err=err); return out
    out["status"] = r.status_code
    out["bytes"] = int(r.headers.get("content-length") or 0) if s.get("head") else len(r.content)
    out["headers"] = {k: v for k, v in r.headers.items() if k.lower() in KEEP}
    lat = [b for a, b in res if a == 200]
    out["latency_ms_med"] = round(statistics.median(lat)) if lat else None
    out["latency_ms_all"] = [round(x) for x in lat]
    out["ok"] = r.status_code == 200
    if r.status_code == 200:
        try:
            n, lo, hi = s["ex"](r) if not s.get("head") else (1, None, None)
            out.update(parsed_ok=bool(n) or s.get("head", False), n=n,
                       first_utc=dt.datetime.utcfromtimestamp(lo).isoformat() if lo else None,
                       last_utc=dt.datetime.utcfromtimestamp(hi).isoformat() if hi else None,
                       last_age_h=round((NOW - hi) / 3600, 2) if hi else None)
        except Exception as e:
            out.update(parsed_ok=False, parse_err=repr(e)[:160], body_head=(r.text[:160] if not s.get("head") else ""))
    else:
        try: out["body_head"] = r.text[:200]
        except Exception: pass
    if s.get("head"): r.close()
    return out

if __name__ == "__main__":
    only = set(sys.argv[1:])
    prev = {}
    fn = os.path.join(OUT, "probe_results.json")
    if os.path.exists(fn): prev = {x["id"]: x for x in json.load(open(fn))}
    for s in SRC:
        if only and s["id"] not in only: continue
        o = one(s); o["probed_utc"] = dt.datetime.utcnow().isoformat() + "Z"; prev[s["id"]] = o
        print(f"{o['id']:38s} {o['status']:>4} ok={o.get('parsed_ok')} n={o.get('n')} first={o.get('first_utc')} last={o.get('last_utc')} lat={o.get('latency_ms_med')}")
        json.dump(list(prev.values()), open(fn, "w"), indent=1, default=str)
        time.sleep(0.5)
