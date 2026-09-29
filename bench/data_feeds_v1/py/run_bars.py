import json,time,sys,statistics
from bars_lib import *
tag=sys.argv[1]
now=int(time.time()*1000); end=(now//60000)*60000-60000   # exclude the forming minute and the last one
start=end-240*60000
G={
 "okx_spot_BTCUSDT":lambda:okx("BTC-USDT",start,end+60000),
 "kraken_spot_XBTUSD":lambda:kraken("XBTUSD",start,end),
 "coinbase_BTC-USD":lambda:coinbase("BTC-USD",start,end),
 "bitstamp_btcusd":lambda:bitstamp("btcusd",start,end),
 "bitfinex_tBTCUSD":lambda:bitfinex("tBTCUSD",start,end),
 "kucoin_BTC-USDT":lambda:kucoin("BTC-USDT",start,end),
 "gemini_btcusd":lambda:gemini("btcusd",start,end),
 "gate_BTC_USDT":lambda:gate("BTC_USDT",start,end),
 "bitget_BTCUSDT":lambda:bitget("BTCUSDT",start,end),
 "mexc_BTCUSDT":lambda:mexc("BTCUSDT",start,end),
 "htx_btcusdt":lambda:htx("btcusdt",start,end),
 "binance_dataapi_BTCUSDT":lambda:binance_like("https://data-api.binance.vision","BTCUSDT",start,end),
 "binance_us_BTCUSDT":lambda:binance_like("https://api.binance.us","BTCUSDT",start,end),
 "hyperliquid_perp_BTC":lambda:hyperliquid("BTC",start,end),
 "dydx_perp_BTC-USD":lambda:dydx("BTC-USD",start,end),
 "deribit_perp_BTC-PERPETUAL":lambda:deribit("BTC-PERPETUAL",start,end),
 "okx_swap_BTC-USDT-SWAP":lambda:okx("BTC-USDT-SWAP",start,end+60000),
 "bitmex_XBTUSD":lambda:bitmex("XBTUSD",start,end),
}
out={"tag":tag,"fetched_utc_ms":int(time.time()*1000),"start":start,"end":end,"venues":{}}
for n,fn in G.items():
    t0=time.time()
    try:
        bars,calls=fn()
        out["venues"][n]={"bars":bars,"n_calls":len(calls),"status":[c.get("status") for c in calls],"lat_ms":[c.get("ms") for c in calls],"err":[c.get("err") for c in calls if c.get("err")],"recv_ms":int(time.time()*1000)}
    except Exception as ex:
        out["venues"][n]={"bars":[],"exception":repr(ex)}
    v=out["venues"][n]; print(n,len(v["bars"]),v.get("status"),v.get("lat_ms"),v.get("exception",""))
    time.sleep(0.4)
json.dump(out,open(f"../raw/bars_{tag}.json","w"))
