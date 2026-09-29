import json,time,lzma,struct,io,zipfile,csv,statistics as st,hashlib,os
from datetime import datetime,timezone,timedelta
from probe_lib import call,RAW
R={}
def G(n,u,p=None,save=False,**k):
    o=call(n,u,p,save=save,**k);time.sleep(0.3);return o
# ---- Binance Vision bulk ----
day=(datetime.now(timezone.utc)-timedelta(days=3)).strftime("%Y-%m-%d")
base="https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1m/"
import requests
def dl(u):
    t0=time.time();r=requests.get(u,headers={"User-Agent":"aurumshift-research"},timeout=60);return r,round((time.time()-t0)*1000)
r,ms=dl(f"{base}BTCUSDT-1m-{day}.zip");rc,_=dl(f"{base}BTCUSDT-1m-{day}.zip.CHECKSUM")
z=zipfile.ZipFile(io.BytesIO(r.content));rows=list(csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]))))
sha=hashlib.sha256(r.content).hexdigest();exp=rc.text.split()[0]
bv={"day":day,"status":r.status_code,"ms":ms,"bytes":len(r.content),"rows":len(rows),"checksum_ok":sha==exp,"first":rows[0],"last":rows[-1],"cols":len(rows[0])}
ts=[int(x[0]) for x in rows];bv["dupes"]=len(ts)-len(set(ts));bv["missing_minutes"]=1440-len(set(ts));bv["ts_unit_digits"]=len(str(ts[0]))
# compare to data-api same day
s=int(datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
api=[]
for k in range(2):
    o=G("bv_api","https://data-api.binance.vision/api/v3/klines",{"symbol":"BTCUSDT","interval":"1m","startTime":str(s+k*720*60000),"limit":"720"});api+=o["json"]
da={int(x[0]):x for x in api};dv={int(x[0]):x for x in rows}
diff=sum(1 for t in dv if t in da and any(abs(float(dv[t][i])-float(da[t][i]))>1e-9 for i in range(1,6)))
bv["api_vs_bulk"]={"common":len(set(da)&set(dv)),"ohlcv_differs":diff}
# futures metrics (OI/LSR) + fundingRate + liquidationSnapshot listing
for nm,u in [("um_metrics",f"https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-{day}.zip"),("um_fundingRate_monthly","https://data.binance.vision/data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2026-08.zip"),("um_klines_1m",f"https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/1m/BTCUSDT-1m-{day}.zip"),("um_bookTicker_maybe",f"https://data.binance.vision/data/futures/um/daily/bookTicker/BTCUSDT/BTCUSDT-bookTicker-{day}.zip"),("um_liqsnap",f"https://data.binance.vision/data/futures/um/daily/liquidationSnapshot/BTCUSDT/BTCUSDT-liquidationSnapshot-{day}.zip"),("cm_premiumIndexKlines",f"https://data.binance.vision/data/futures/um/daily/premiumIndexKlines/BTCUSDT/1m/BTCUSDT-1m-{day}.zip"),("spot_trades",f"https://data.binance.vision/data/spot/daily/trades/BTCUSDT/BTCUSDT-trades-{day}.zip"),("spot_oldest","https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2017-08.zip")]:
    try:
        r2,ms2=dl(u);info={"status":r2.status_code,"ms":ms2,"bytes":len(r2.content)}
        if r2.status_code==200 and u.endswith(".zip"):
            z2=zipfile.ZipFile(io.BytesIO(r2.content));txt=z2.open(z2.namelist()[0]).read().decode().splitlines();info["rows"]=len(txt);info["head"]=txt[:2]
        bv[nm]=info
    except Exception as e: bv[nm]={"err":repr(e)[:150]}
R["binance_vision"]=bv
# ---- Dukascopy decode ----
o=requests.get("https://datafeed.dukascopy.com/datafeed/XAUUSD/2024/00/02/10h_ticks.bi5",timeout=60)
raw=lzma.decompress(o.content);n=len(raw)//20
tk=[struct.unpack(">IIIff",raw[i*20:(i+1)*20]) for i in range(n)]
R["dukascopy"]={"status":o.status_code,"compressed_bytes":len(o.content),"ticks":n,"first":tk[0],"last":tk[-1],"note":"ms offset from hour start, ask*1e3?, bid, askvol, bidvol"}
o2=requests.get("https://datafeed.dukascopy.com/datafeed/EURUSD/2026/08/01/10h_ticks.bi5",timeout=60)
R["dukascopy_recent_2026"]={"status":o2.status_code,"bytes":len(o2.content)}
o3=requests.get("https://datafeed.dukascopy.com/datafeed/XAUUSD/2003/04/01/BID_candles_min_1.bi5",timeout=60)
R["dukascopy_old_candle"]={"status":o3.status_code,"bytes":len(o3.content)}
o4=requests.get("https://datafeed.dukascopy.com/datafeed/XAUUSD/2026/07/10/BID_candles_min_1.bi5",timeout=60)
R["dukascopy_2026_candle_1m"]={"status":o4.status_code,"bytes":len(o4.content)}
# ---- XAU spot-ish comparison snapshot ----
x={}
def px(n,fn):
    try: x[n]=fn()
    except Exception as e: x[n]=f"ERR {e!r}"[:80]
px("gold-api_XAU",lambda:G("g","https://api.gold-api.com/price/XAU")["json"]["price"])
px("gold-api_updatedAt",lambda:G("g","https://api.gold-api.com/price/XAU")["json"]["updatedAt"])
px("swissquote_std_bid_ask",lambda:[(p["bid"],p["ask"]) for p in G("s","https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD")["json"][0]["spreadProfilePrices"] if p["spreadProfile"]=="standard"][0])
px("okx_XAUT-USDT_last",lambda:G("o","https://www.okx.com/api/v5/market/ticker",{"instId":"XAUT-USDT"})["json"]["data"][0]["last"])
px("kraken_PAXGUSD_last",lambda:G("k","https://api.kraken.com/0/public/Ticker",{"pair":"PAXGUSD"})["json"]["result"]["PAXGUSD"]["c"][0])
px("kraken_XAUTUSD_last",lambda:G("k","https://api.kraken.com/0/public/Ticker",{"pair":"XAUTUSD"})["json"]["result"]["XAUTUSD"]["c"][0])
px("coinbase_PAXG-USD",lambda:G("c","https://api.exchange.coinbase.com/products/PAXG-USD/ticker")["json"]["price"])
px("deribit_PAXG_USDC-PERP",lambda:G("d","https://www.deribit.com/api/v2/public/ticker",{"instrument_name":"PAXG_USDC-PERPETUAL"})["json"]["result"]["last_price"])
def yh(sym,rng="1d",iv="1m"):
    j=G("y","https://query1.finance.yahoo.com/v8/finance/chart/"+sym,{"interval":iv,"range":rng})["json"]["chart"]["result"][0];return j
try:
    j=yh("GC=F");x["yahoo_GC=F_last"]=j["meta"]["regularMarketPrice"];x["yahoo_GC=F_time"]=j["meta"]["regularMarketTime"];R["yahoo_GC"]={"bars":len(j["timestamp"]),"keys":list(j["indicators"]["quote"][0].keys()),"nulls":sum(1 for v in j["indicators"]["quote"][0]["close"] if v is None)}
    j=yh("XAUUSD=X");x["yahoo_XAUUSD=X"]=j["meta"]["regularMarketPrice"]
except Exception as e: x["yahoo_err"]=repr(e)[:100]
px("hl_xyz_GOLD",lambda:[v for k,v in G("h","https://api.hyperliquid.xyz/info",method="POST",body={"type":"allMids","dex":"xyz"})["json"].items() if "GOLD" in k.upper()])
x["snapshot_utc"]=datetime.now(timezone.utc).isoformat()
R["xau_snapshot"]=x
# ---- FX EURUSD daily comparison over last 10 days ----
fx={}
e=G("e","https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?lastNObservations=8&format=csvdata").get("text","")
fx["ecb_sdmx"]={r["TIME_PERIOD"]:float(r["OBS_VALUE"]) for r in csv.DictReader(e.splitlines())} if e else {}
fr=G("f","https://api.frankfurter.dev/v1/"+(datetime.now(timezone.utc)-timedelta(days=14)).strftime("%Y-%m-%d")+"..?base=EUR&symbols=USD")["json"]
fx["frankfurter"]={d:v["USD"] for d,v in fr["rates"].items()}
b=G("b","https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Sep/2026&Dateto=now&SeriesCodes=XUDLUSS,XUDLERS&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N").get("text","")
fx["boe_raw"]=b[:600]
y=yh("EURUSD=X","1mo","1d");fx["yahoo_EURUSD=X_daily"]={datetime.fromtimestamp(t,timezone.utc).strftime("%Y-%m-%d"):c for t,c in zip(y["timestamp"],y["indicators"]["quote"][0]["close"])}
av=G("a","https://www.alphavantage.co/query",{"function":"FX_DAILY","from_symbol":"EUR","to_symbol":"USD","apikey":"demo"})["json"]
fx["alphavantage_demo_keys"]=list(av.keys())[:3];fx["alphavantage_demo_latest"]=list(av.get("Time Series FX (Daily)",{}).items())[:2]
td=G("t","https://api.twelvedata.com/time_series",{"symbol":"EUR/USD","interval":"1day","apikey":"demo","outputsize":"5"})["json"];fx["twelvedata_demo"]=td.get("values",td)[:2] if isinstance(td.get("values"),list) else td
er=G("er","https://open.er-api.com/v6/latest/EUR")["json"];fx["open_er_api"]={"EURUSD":er["rates"]["USD"],"time_last_update_utc":er["time_last_update_utc"],"time_next":er["time_next_update_utc"]}
R["fx"]=fx
json.dump(R,open("../results/fxgold_bulk.json","w"),indent=1,default=str)
print(json.dumps({k:v for k,v in R.items() if k!="fx"},indent=1,default=str)[:5500]);print(json.dumps(R["fx"],default=str)[:2500])
