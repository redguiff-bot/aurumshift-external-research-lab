"""Per-venue deviation from within-group consensus (median of OTHER venues' close per minute). Consensus is a reference for comparison only, NOT ground truth."""
import json,statistics as st
a=json.load(open("../raw/bars_t2.json"));S,E=a["start"],a["end"]
G={"USD_spot":["kraken_spot_XBTUSD","coinbase_BTC-USD","bitstamp_btcusd","bitfinex_tBTCUSD","gemini_btcusd"],
   "USDT_spot":["okx_spot_BTCUSDT","kucoin_BTC-USDT","gate_BTC_USDT","bitget_BTCUSDT","mexc_BTCUSDT","htx_btcusdt","binance_dataapi_BTCUSDT"],
   "perp":["okx_swap_BTC-USDT-SWAP","hyperliquid_perp_BTC","deribit_perp_BTC-PERPETUAL","dydx_perp_BTC-USD"]}
B={v:{x[0]:x for x in a["venues"][v]["bars"] if S<=x[0]<E} for v in a["venues"]}
out={}
for g,vs in G.items():
    for v in vs:
        dev=[];vr=[]
        for t in B[v]:
            oth=[B[o][t][4] for o in vs if o!=v and t in B[o]]
            ov=[B[o][t][5] for o in vs if o!=v and t in B[o] and B[o][t][5]>0]
            if len(oth)>=2:
                m=st.median(oth);dev.append((B[v][t][4]-m)/m*1e4)
            if ov and B[v][t][5]>0: vr.append(B[v][t][5]/st.median(ov))
        ad=sorted(abs(d) for d in dev)
        out[v]={"group":g,"n":len(dev),"signed_med_bps":round(st.median(dev),2),"abs_med_bps":round(st.median(ad),2),"abs_p95_bps":round(ad[int(len(ad)*.95)-1],2),"vol_vs_group_med":round(st.median(vr),3) if vr else None}
json.dump(out,open("../results/consensus_dev.json","w"),indent=1)
for v,r in out.items(): print(v,r)
