"""Normalized 1m bar fetchers. Each returns (bars, meta) ; bar=[open_ts_ms,o,h,l,c,base_vol,closed_flag_or_None]
Fetch window [start_ms,end_ms) of minute-open timestamps. No retries beyond one; polite spacing."""
import time, json
from datetime import datetime, timezone
from probe_lib import call

def f(x): return float(x)
def iso(ms): return datetime.fromtimestamp(ms/1000,timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def okx(inst,s,e):
    bars=[];after=str(e);calls=[];
    for _ in range(6):
        r=call("tmp_okx",f"https://www.okx.com/api/v5/market/history-candles" if False else "https://www.okx.com/api/v5/market/candles",{"instId":inst,"bar":"1m","limit":"100","after":after},save=False);calls.append(r)
        d=r.get("json",{}).get("data",[]) if r.get("ok") else []
        if not d: break
        for x in d: bars.append([int(x[0]),f(x[1]),f(x[2]),f(x[3]),f(x[4]),f(x[5]),x[8]=="1"])
        after=d[-1][0]
        if int(after)<=s: break
        time.sleep(0.3)
    return bars,calls
def okx_hist(inst,s,e):
    bars=[];after=str(e);calls=[]
    for _ in range(6):
        r=call("tmp",f"https://www.okx.com/api/v5/market/history-candles",{"instId":inst,"bar":"1m","limit":"100","after":after},save=False);calls.append(r)
        d=r.get("json",{}).get("data",[]) if r.get("ok") else []
        if not d: break
        for x in d: bars.append([int(x[0]),f(x[1]),f(x[2]),f(x[3]),f(x[4]),f(x[5]),x[8]=="1"])
        after=d[-1][0]
        if int(after)<=s: break
        time.sleep(0.3)
    return bars,calls
def kraken(pair,s,e):
    r=call("tmp","https://api.kraken.com/0/public/OHLC",{"pair":pair,"interval":"1","since":str(s//1000-60)},save=False)
    res=r.get("json",{}).get("result",{}) if r.get("ok") else {}
    k=[v for kk,v in res.items() if kk!="last"]
    d=k[0] if k else []
    return [[int(x[0])*1000,f(x[1]),f(x[2]),f(x[3]),f(x[4]),f(x[6]),None] for x in d],[r]
def coinbase(prod,s,e):
    bars=[];calls=[];cur=s
    while cur<e:
        nxt=min(cur+300*60000,e)
        r=call("tmp",f"https://api.exchange.coinbase.com/products/{prod}/candles",{"granularity":"60","start":iso(cur),"end":iso(nxt)},save=False);calls.append(r)
        for x in (r.get("json") or []) if r.get("ok") else []: bars.append([int(x[0])*1000,f(x[3]),f(x[2]),f(x[1]),f(x[4]),f(x[5]),None])
        cur=nxt;time.sleep(0.3)
    return bars,calls
def bitstamp(pair,s,e):
    r=call("tmp",f"https://www.bitstamp.net/api/v2/ohlc/{pair}/",{"step":"60","limit":"1000","start":str(s//1000),"end":str(e//1000)},save=False)
    d=r.get("json",{}).get("data",{}).get("ohlc",[]) if r.get("ok") else []
    return [[int(x["timestamp"])*1000,f(x["open"]),f(x["high"]),f(x["low"]),f(x["close"]),f(x["volume"]),None] for x in d],[r]
def bitfinex(sym,s,e):
    r=call("tmp",f"https://api-pub.bitfinex.com/v2/candles/trade:1m:{sym}/hist",{"start":str(s),"end":str(e),"limit":"1000","sort":"1"},save=False)
    d=r.get("json") if r.get("ok") else []
    return [[int(x[0]),f(x[1]),f(x[3]),f(x[4]),f(x[2]),f(x[5]),None] for x in d],[r]
def kucoin(sym,s,e):
    r=call("tmp","https://api.kucoin.com/api/v1/market/candles",{"symbol":sym,"type":"1min","startAt":str(s//1000),"endAt":str(e//1000)},save=False)
    d=r.get("json",{}).get("data",[]) if r.get("ok") else []
    return [[int(x[0])*1000,f(x[1]),f(x[3]),f(x[4]),f(x[2]),f(x[5]),None] for x in d],[r]
def gemini(sym,s,e):
    r=call("tmp",f"https://api.gemini.com/v2/candles/{sym}/1m",save=False)
    d=r.get("json") if r.get("ok") else []
    return [[int(x[0]),f(x[1]),f(x[2]),f(x[3]),f(x[4]),f(x[5]),None] for x in d if s<=x[0]<e],[r]
def gate(pair,s,e):
    r=call("tmp","https://api.gateio.ws/api/v4/spot/candlesticks",{"currency_pair":pair,"interval":"1m","from":str(s//1000),"to":str(e//1000)},save=False)
    d=r.get("json") if r.get("ok") else []
    return [[int(x[0])*1000,f(x[5]),f(x[3]),f(x[4]),f(x[2]),f(x[6]),x[7]=="true"] for x in d],[r]
def bitget(sym,s,e):
    r=call("tmp","https://api.bitget.com/api/v2/spot/market/candles",{"symbol":sym,"granularity":"1min","startTime":str(s),"endTime":str(e),"limit":"1000"},save=False)
    d=r.get("json",{}).get("data",[]) if r.get("ok") else []
    return [[int(x[0]),f(x[1]),f(x[2]),f(x[3]),f(x[4]),f(x[5]),None] for x in d],[r]
def mexc(sym,s,e):
    r=call("tmp","https://api.mexc.com/api/v3/klines",{"symbol":sym,"interval":"1m","startTime":str(s),"endTime":str(e),"limit":"1000"},save=False)
    d=r.get("json") if r.get("ok") else []
    return [[int(x[0]),f(x[1]),f(x[2]),f(x[3]),f(x[4]),f(x[5]),None] for x in d],[r]
def htx(sym,s,e):
    r=call("tmp","https://api.huobi.pro/market/history/kline",{"symbol":sym,"period":"1min","size":"300"},save=False)
    d=r.get("json",{}).get("data",[]) if r.get("ok") else []
    return [[int(x["id"])*1000,f(x["open"]),f(x["high"]),f(x["low"]),f(x["close"]),f(x["amount"]),None] for x in d if s<=x["id"]*1000<e],[r]
def binance_like(base,sym,s,e):
    r=call("tmp",base+"/api/v3/klines",{"symbol":sym,"interval":"1m","startTime":str(s),"endTime":str(e),"limit":"1000"},save=False)
    d=r.get("json") if r.get("ok") else []
    return [[int(x[0]),f(x[1]),f(x[2]),f(x[3]),f(x[4]),f(x[5]),None] for x in d],[r]
def hyperliquid(coin,s,e):
    r=call("tmp","https://api.hyperliquid.xyz/info",method="POST",body={"type":"candleSnapshot","req":{"coin":coin,"interval":"1m","startTime":s,"endTime":e}},save=False)
    d=r.get("json") if r.get("ok") else []
    return [[int(x["t"]),f(x["o"]),f(x["h"]),f(x["l"]),f(x["c"]),f(x["v"]),None] for x in d],[r]
def dydx(mkt,s,e):
    r=call("tmp",f"https://indexer.dydx.trade/v4/candles/perpetualMarkets/{mkt}",{"resolution":"1MIN","limit":"1000","fromISO":iso(s),"toISO":iso(e)},save=False)
    d=r.get("json",{}).get("candles",[]) if r.get("ok") else []
    out=[]
    for x in d:
        ts=int(datetime.strptime(x["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).timestamp()*1000)
        out.append([ts,f(x["open"]),f(x["high"]),f(x["low"]),f(x["close"]),f(x["baseTokenVolume"]),None])
    return out,[r]
def deribit(inst,s,e):
    r=call("tmp","https://www.deribit.com/api/v2/public/get_tradingview_chart_data",{"instrument_name":inst,"resolution":"1","start_timestamp":str(s),"end_timestamp":str(e)},save=False)
    d=r.get("json",{}).get("result") if r.get("ok") else None
    if not d: return [],[r]
    return [[d["ticks"][i],d["open"][i],d["high"][i],d["low"][i],d["close"][i],d["volume"][i],None] for i in range(len(d["ticks"]))],[r]
def bitmex(sym,s,e):
    r=call("tmp","https://www.bitmex.com/api/v1/trade/bucketed",{"binSize":"1m","symbol":sym,"count":"500","startTime":iso(s),"endTime":iso(e),"partial":"false"},save=False)
    d=r.get("json") if r.get("ok") else []
    out=[]
    for x in d:
        ts=int(datetime.strptime(x["timestamp"],"%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).timestamp()*1000)
        out.append([ts,x["open"],x["high"],x["low"],x["close"],x["homeNotional"],None])
    return out,[r]
