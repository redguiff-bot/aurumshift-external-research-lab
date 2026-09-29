import json,time,statistics as st
from probe_lib import call
E={
"okx_candles":("https://www.okx.com/api/v5/market/candles",{"instId":"BTC-USDT","bar":"1m","limit":"100"},"GET",None),
"kraken_ohlc":("https://api.kraken.com/0/public/OHLC",{"pair":"XBTUSD","interval":"1"},"GET",None),
"coinbase_candles":("https://api.exchange.coinbase.com/products/BTC-USD/candles",{"granularity":"60"},"GET",None),
"bitstamp_ohlc":("https://www.bitstamp.net/api/v2/ohlc/btcusd/",{"step":"60","limit":"100"},"GET",None),
"deribit_ticker":("https://www.deribit.com/api/v2/public/ticker",{"instrument_name":"BTC-PERPETUAL"},"GET",None),
"hyperliquid_info_meta":("https://api.hyperliquid.xyz/info",None,"POST",{"type":"meta"}),
"kucoin_candles":("https://api.kucoin.com/api/v1/market/candles",{"symbol":"BTC-USDT","type":"1min"},"GET",None),
"gate_candles":("https://api.gateio.ws/api/v4/spot/candlesticks",{"currency_pair":"BTC_USDT","interval":"1m","limit":"100"},"GET",None),
"bitget_candles":("https://api.bitget.com/api/v2/spot/market/candles",{"symbol":"BTCUSDT","granularity":"1min","limit":"100"},"GET",None),
"dydx_candles":("https://indexer.dydx.trade/v4/candles/perpetualMarkets/BTC-USD",{"resolution":"1MIN","limit":"100"},"GET",None),
"binance_dataapi":("https://data-api.binance.vision/api/v3/klines",{"symbol":"BTCUSDT","interval":"1m","limit":"100"},"GET",None),
"frankfurter_latest":("https://api.frankfurter.dev/v1/latest",{"base":"EUR","symbols":"USD"},"GET",None),
"ecb_sdmx":("https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A",{"lastNObservations":"3","format":"jsondata"},"GET",None),
"nyfed_sofr":("https://markets.newyorkfed.org/api/rates/secured/sofr/last/2.json",None,"GET",None),
}
out={}
for n,(u,p,m,b) in E.items():
    L=[];S=[];errs=0;hd=None
    for i in range(10):
        o=call("lat",u,p,method=m,body=b,save=False,timeout=25);S.append(o.get("status"))
        if o.get("ok"): L.append(o["ms"])
        else: errs+=1
        hd=o.get("hdr") or hd;time.sleep(1.0)
    out[n]={"ok":len(L),"fail":errs,"status":sorted(set(S),key=str),"ms_med":round(st.median(L),1) if L else None,"ms_p90":sorted(L)[int(len(L)*.9)-1] if L else None,"ms_max":max(L) if L else None,"hdrs":hd}
    print(n,out[n]["ok"],out[n]["status"],out[n]["ms_med"],out[n]["ms_max"])
# bounded bursts, well under documented limits
def burst(name,u,p,n,dur):
    r=[];t0=time.time()
    for i in range(n):
        t=time.time();o=call("b",u,p,save=False,timeout=15);r.append((o.get("status"),o.get("ms"),o.get("hdr")))
        rem=(t0+(i+1)*dur/n)-time.time()
        if rem>0: time.sleep(rem)
    return {"n":n,"target_window_s":dur,"actual_s":round(time.time()-t0,2),"statuses":sorted({str(x[0]) for x in r}),"ms_med":st.median([x[1] for x in r]),"last_hdr":r[-1][2]}
out["_burst_okx_candles_20_in_4s(doc:40/2s)"]=burst("okx","https://www.okx.com/api/v5/market/candles",{"instId":"BTC-USDT","bar":"1m","limit":"10"},20,4)
out["_burst_coinbase_candles_8_in_2s(doc:10/s)"]=burst("cb","https://api.exchange.coinbase.com/products/BTC-USD/candles",{"granularity":"60"},8,2)
out["_burst_deribit_ticker_20_in_4s(doc numeric: see docs_facts)"]=burst("dr","https://www.deribit.com/api/v2/public/ticker",{"instrument_name":"BTC-PERPETUAL"},20,4)
print({k:v for k,v in out.items() if k.startswith("_")})
json.dump(out,open("../results/latency_ratelimit.json","w"),indent=1)
