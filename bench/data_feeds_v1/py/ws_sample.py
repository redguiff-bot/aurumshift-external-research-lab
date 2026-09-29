import asyncio, json, time, ssl, os, statistics, websockets
PROXY=os.environ.get("HTTPS_PROXY")
DUR=20
async def run(name,url,subs,tsfn,typefn=None,ping=None):
    n=0;lat=[];types={};first=None;err=None;t0=time.time();samples=[]
    try:
        import websockets.asyncio.client as wc
        kw={}
        if PROXY: kw["proxy"]=PROXY
        try:
            ws=await asyncio.wait_for(websockets.connect(url,open_timeout=15,**kw),20)
        except TypeError:
            ws=await asyncio.wait_for(websockets.connect(url,open_timeout=15),20)
        conn=time.time()-t0
        for s in subs: await ws.send(json.dumps(s) if not isinstance(s,str) else s)
        end=time.time()+DUR
        while time.time()<end:
            try: m=await asyncio.wait_for(ws.recv(),timeout=max(0.1,end-time.time()))
            except asyncio.TimeoutError: break
            rx=time.time()*1000
            try: j=json.loads(m)
            except Exception: continue
            n+=1
            k=typefn(j) if typefn else "msg"; types[k]=types.get(k,0)+1
            if len(samples)<3: samples.append(m[:300] if isinstance(m,str) else str(m)[:300])
            try:
                ts=tsfn(j)
                if ts: lat.append(rx-ts)
            except Exception: pass
        await ws.close()
    except Exception as e: err=repr(e)[:200]; conn=None
    r={"name":name,"connect_s":round(conn,2) if conn else None,"msgs":n,"types":types,"err":err,"lat_ms_median":round(statistics.median(lat),1) if lat else None,"lat_ms_p95":round(sorted(lat)[int(len(lat)*.95)-1],1) if len(lat)>3 else None,"lat_n":len(lat),"samples":samples}
    print(json.dumps({k:v for k,v in r.items() if k!="samples"}));return r
async def main():
    jobs=[
     run("okx_trades_tickers","wss://ws.okx.com:8443/ws/v5/public",[{"op":"subscribe","args":[{"channel":"trades","instId":"BTC-USDT"},{"channel":"tickers","instId":"BTC-USDT-SWAP"},{"channel":"funding-rate","instId":"BTC-USDT-SWAP"},{"channel":"liquidation-orders","instType":"SWAP"}]}],
         lambda j:int(j["data"][0]["ts"]) if "data" in j and j["data"] and "ts" in j["data"][0] else None, lambda j:(j.get("arg",{}).get("channel") or j.get("event","?"))),
     run("kraken_trades","wss://ws.kraken.com/v2",[{"method":"subscribe","params":{"channel":"trade","symbol":["BTC/USD"]}}],
         None, lambda j:j.get("channel","?")),
     run("coinbase_matches","wss://ws-feed.exchange.coinbase.com",[{"type":"subscribe","product_ids":["BTC-USD"],"channels":["matches","ticker"]}],
         None, lambda j:j.get("type","?")),
     run("deribit_ws","wss://www.deribit.com/ws/api/v2",[{"jsonrpc":"2.0","id":1,"method":"public/subscribe","params":{"channels":["trades.BTC-PERPETUAL.100ms","ticker.BTC-PERPETUAL.100ms","deribit_price_index.btc_usd"]}}],
         lambda j:j["params"]["data"]["timestamp"] if "params" in j and isinstance(j["params"]["data"],dict) and "timestamp" in j["params"]["data"] else None, lambda j:j.get("params",{}).get("channel","ctl")[:12]),
     run("hyperliquid_ws","wss://api.hyperliquid.xyz/ws",[{"method":"subscribe","subscription":{"type":"trades","coin":"BTC"}},{"method":"subscribe","subscription":{"type":"l2Book","coin":"BTC"}}],
         lambda j:j["data"][0]["time"] if j.get("channel")=="trades" and j["data"] else (j["data"]["time"] if j.get("channel")=="l2Book" else None), lambda j:j.get("channel","?")),
     run("bitstamp_ws","wss://ws.bitstamp.net",[{"event":"bts:subscribe","data":{"channel":"live_trades_btcusd"}}],
         lambda j:int(j["data"]["microtimestamp"])/1000 if j.get("event")=="trade" else None, lambda j:j.get("event","?")),
     run("bitfinex_ws","wss://api-pub.bitfinex.com/ws/2",[{"event":"subscribe","channel":"trades","symbol":"tBTCUSD"}],
         None, lambda j:"data" if isinstance(j,list) else j.get("event","?")),
     run("dydx_ws","wss://indexer.dydx.trade/v4/ws",[{"type":"subscribe","channel":"v4_trades","id":"BTC-USD"}],
         None, lambda j:j.get("type","?")),
     run("gemini_ws","wss://api.gemini.com/v1/marketdata/btcusd?trades=true",[],None,lambda j:j.get("type","?")),
     run("kucoin_ws_needs_token","wss://x",[],None),
     run("binance_ws","wss://stream.binance.com:9443/ws/btcusdt@trade",[],lambda j:j.get("T"),lambda j:j.get("e","?")),
     run("binance_ws_datapub","wss://data-stream.binance.vision/ws/btcusdt@trade",[],lambda j:j.get("T"),lambda j:j.get("e","?")),
     run("bitmex_ws","wss://ws.bitmex.com/realtime?subscribe=trade:XBTUSDT,liquidation",[],None,lambda j:j.get("table","ctl")),
     run("bybit_ws","wss://stream.bybit.com/v5/public/linear",[{"op":"subscribe","args":["publicTrade.BTCUSDT","liquidation.BTCUSDT"]}],lambda j:j.get("ts"),lambda j:j.get("topic","ctl")),
    ]
    res=await asyncio.gather(*jobs)
    json.dump(res,open("../results/ws_sample.json","w"),indent=1)
asyncio.run(main())
