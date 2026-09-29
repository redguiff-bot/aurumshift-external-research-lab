import json,statistics as st,itertools,math
import sys
T1=sys.argv[1] if len(sys.argv)>1 else "t1"
a=json.load(open("../raw/bars_t0.json"));b=json.load(open(f"../raw/bars_{T1}.json"))
S,E=a["start"],a["end"]
OS,OE=b["start"],a["end"]  # overlap window of both fetches
def win(bars,s,e): return [x for x in bars if s<=x[0]<e]
def per(v,vb0,vb1):
    raw=vb0["bars"];w=win(raw,S,E)
    ts=[x[0] for x in w];u=set(ts)
    exp=(E-S)//60000
    r={"raw_rows":len(raw),"in_window":len(w),"unique":len(u),"dupes":len(ts)-len(u),"expected":exp,"missing":exp-len(u),
       "aligned_60s":all(t%60000==0 for t in ts),"monotonic":ts==sorted(ts) or ts==sorted(ts,reverse=True),
       "order":"asc" if ts==sorted(ts) else ("desc" if ts==sorted(ts,reverse=True) else "mixed"),
       "zero_vol_bars":sum(1 for x in w if x[5]==0),"flat_bars":sum(1 for x in w if x[1]==x[2]==x[3]==x[4])}
    # t1 revision on window closed bars (window is inside t0 closed range)
    d1={x[0]:x for x in win(vb1["bars"],OS,OE)};d0={x[0]:x for x in win(raw,OS,OE)}
    common=set(d0)&set(d1)
    ch={"ohlc":0,"vol":0}
    for t in common:
        if any(abs(d0[t][i]-d1[t][i])>1e-9*max(1,abs(d0[t][i])) for i in (1,2,3,4)): ch["ohlc"]+=1
        if abs(d0[t][5]-d1[t][5])>1e-9*max(1,abs(d0[t][5])): ch["vol"]+=1
    r["t1_common"]=len(common);r["revised_ohlc_bars"]=ch["ohlc"];r["revised_vol_bars"]=ch["vol"]
    r["late_arrivals(missing t0, present t1)"]=len(set(d1)-set(d0));r["disappeared(t0 not t1)"]=len(set(d0)-set(d1))
    # bars inside t0 fetch after 'end' (forming) flags
    r["closed_flag_false_in_window"]=sum(1 for x in w if x[6] is False)
    r["lat_ms_first_call"]=vb0.get("lat_ms",[None])[0]
    return r,d0
rows={};D={}
for v,vb in a["venues"].items():
    rows[v],D[v]=per(v,vb,b["venues"][v])
print(json.dumps(rows,indent=0)[:200]);
# pairwise
groups={"spot_usdt":["okx_spot_BTCUSDT","kucoin_BTC-USDT","gate_BTC_USDT","bitget_BTCUSDT","mexc_BTCUSDT","htx_btcusdt","binance_dataapi_BTCUSDT"],
"spot_usd":["kraken_spot_XBTUSD","coinbase_BTC-USD","bitstamp_btcusd","bitfinex_tBTCUSD","gemini_btcusd","binance_us_BTCUSDT"],
"perp":["okx_swap_BTC-USDT-SWAP","hyperliquid_perp_BTC","dydx_perp_BTC-USD","deribit_perp_BTC-PERPETUAL"]}
allv=[v for g in groups.values() for v in g]
def bps(x,y): return abs(x-y)/y*1e4
pair={}
for v1,v2 in itertools.combinations(allv,2):
    c=sorted(set(D[v1])&set(D[v2]))
    if len(c)<30: continue
    dc=[bps(D[v1][t][4],D[v2][t][4]) for t in c]
    do=[bps(D[v1][t][1],D[v2][t][1]) for t in c]
    dh=[bps(D[v1][t][2],D[v2][t][2]) for t in c];dl=[bps(D[v1][t][3],D[v2][t][3]) for t in c]
    ex=sum(1 for t in c if all(D[v1][t][i]==D[v2][t][i] for i in (1,2,3,4)))
    vr=[D[v1][t][5]/D[v2][t][5] for t in c if D[v2][t][5]>0 and D[v1][t][5]>0]
    # signed close diff (v1-v2) for offset
    sd=st.median([(D[v1][t][4]-D[v2][t][4])/D[v2][t][4]*1e4 for t in c])
    r1=[math.log(D[v1][c[i]][4]/D[v1][c[i-1]][4]) for i in range(1,len(c))];r2=[math.log(D[v2][c[i]][4]/D[v2][c[i-1]][4]) for i in range(1,len(c))]
    try: cor=st.correlation(r1,r2)
    except Exception: cor=None
    pair[f"{v1}|{v2}"]={"n":len(c),"close_bps_med":round(st.median(dc),2),"close_bps_p95":round(sorted(dc)[int(len(dc)*.95)-1],2),"open_bps_med":round(st.median(do),2),"high_bps_med":round(st.median(dh),2),"low_bps_med":round(st.median(dl),2),"signed_close_bps_med":round(sd,2),"exact_ohlc_match":ex,"vol_ratio_med":round(st.median(vr),3) if vr else None,"ret_corr":round(cor,4) if cor else None}
json.dump({"per_venue":rows,"pairs":pair,"window":{"start":S,"end":E,"t0_fetch":a["fetched_utc_ms"],"t1_fetch":b["fetched_utc_ms"]}},open(f"../results/bars_analysis_{T1}.json","w"),indent=1)
for v,r in rows.items(): print(f"{v:30s} rows={r['raw_rows']:4d} inwin={r['in_window']:3d} miss={r['missing']:3d} dup={r['dupes']} ord={r['order']} zero={r['zero_vol_bars']:3d} flat={r['flat_bars']:3d} revOHLC={r['revised_ohlc_bars']} revV={r['revised_vol_bars']} late={r['late_arrivals(missing t0, present t1)']} gone={r['disappeared(t0 not t1)']}")
print("gap t1-t0 s:",(b["fetched_utc_ms"]-a["fetched_utc_ms"])/1000)
