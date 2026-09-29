import json,time,statistics as st,math
from datetime import datetime,timezone
from probe_lib import call
R={}
def G(n,u,p=None,**k): 
    o=call(n,u,p,save=False,**k); time.sleep(0.25); return o.get("json") if o.get("ok") else None
now=int(time.time()*1000);d7=now-7*86400000
# ---- FUNDING (last 7d, BTC perp) ----
F={}
x=G("f_okx","https://www.okx.com/api/v5/public/funding-rate-history",{"instId":"BTC-USDT-SWAP","limit":"30"})
F["okx_BTC-USDT-SWAP"]={int(r["fundingTime"]):float(r["fundingRate"]) for r in x["data"]} if x else {}
x=G("f_okxr","https://www.okx.com/api/v5/public/funding-rate-history",{"instId":"BTC-USDT-SWAP","limit":"30"})
F["okx_realized_field"]={int(r["fundingTime"]):float(r["realizedRate"]) for r in x["data"]} if x else {}
x=G("f_gate","https://api.gateio.ws/api/v4/futures/usdt/funding_rate",{"contract":"BTC_USDT","limit":"30"})
F["gate_BTC_USDT"]={int(r["t"])*1000:float(r["r"]) for r in x} if x else {}
x=G("f_bg","https://api.bitget.com/api/v2/mix/market/history-fund-rate",{"symbol":"BTCUSDT","productType":"usdt-futures","pageSize":"30"})
F["bitget_BTCUSDT"]={int(r["fundingTime"]):float(r["fundingRate"]) for r in x["data"]} if x else {}
x=G("f_ku","https://api-futures.kucoin.com/api/v1/contract/funding-rates",{"symbol":"XBTUSDTM","from":str(d7),"to":str(now)})
F["kucoin_XBTUSDTM"]={int(r["timepoint"]):float(r["fundingRate"]) for r in x["data"]} if x else {}
x=G("f_hl","https://api.hyperliquid.xyz/info",method="POST",body={"type":"fundingHistory","coin":"BTC","startTime":d7})
F["hyperliquid_BTC(1h)"]={int(r["time"]):float(r["fundingRate"]) for r in x} if x else {}
x=G("f_dx","https://indexer.dydx.trade/v4/historicalFunding/BTC-USD",{"limit":"200"})
F["dydx_BTC-USD(1h)"]={int(datetime.strptime(r["effectiveAt"][:19],"%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()*1000):float(r["rate"]) for r in x["historicalFunding"]} if x else {}
x=G("f_kf","https://futures.kraken.com/derivatives/api/v4/historicalfundingrates",{"symbol":"PF_XBTUSD"})
F["krakenfut_PF_XBTUSD(1h,relative)"]={int(datetime.strptime(r["timestamp"][:19],"%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()*1000):r for r in (x["rates"][-200:] if x else [])}
x=G("f_dr","https://www.deribit.com/api/v2/public/get_funding_rate_history",{"instrument_name":"BTC-PERPETUAL","start_timestamp":str(d7),"end_timestamp":str(now)})
F["deribit_BTC-PERPETUAL(1h)"]={int(r["timestamp"]):r for r in x["result"]} if x else {}
x=G("f_bx","https://www.bitmex.com/api/v1/funding",{"symbol":"XBTUSDT","count":"30","reverse":"true"})
F["bitmex_XBTUSDT"]={int(datetime.strptime(r["timestamp"][:19],"%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()*1000):float(r["fundingRate"]) for r in x} if x else {}
summ={}
for k,v in F.items():
    ts=sorted(v);gaps=sorted({(b-a)//60000 for a,b in zip(ts,ts[1:])})
    summ[k]={"n":len(ts),"first":ts[0] if ts else None,"last":ts[-1] if ts else None,"gap_minutes_set":gaps[:6],"sample":list(v.items())[:1] if ts else None}
R["funding_summary"]=summ
# 8h boundary comparison
bd=[t for t in F["okx_BTC-USDT-SWAP"] if t%(8*3600000)==0]
cmp=[]
for t in sorted(bd)[-15:]:
    row={"t":t,"okx":F["okx_BTC-USDT-SWAP"].get(t),"okx_realized":F["okx_realized_field"].get(t),"gate":F["gate_BTC_USDT"].get(t),"bitget":F["bitget_BTCUSDT"].get(t),"kucoin":F["kucoin_XBTUSDTM"].get(t),"bitmex_usdt":F["bitmex_XBTUSDT"].get(t)}
    hl=[F["hyperliquid_BTC(1h)"][k] for k in F["hyperliquid_BTC(1h)"] if t-8*3600000<k<=t+60000]
    row["hl_sum8h"]=sum(hl) if len(hl)>=7 else None;row["hl_n"]=len(hl)
    cmp.append(row)
R["funding_8h_compare"]=cmp
# ---- OI snapshot (BTC) ----
oi={}
x=G("oi_okx","https://www.okx.com/api/v5/public/open-interest",{"instType":"SWAP","instId":"BTC-USDT-SWAP"});oi["okx_BTC-USDT-SWAP_btc"]=float(x["data"][0]["oiCcy"]);oi["okx_ts"]=x["data"][0]["ts"]
x=G("oi_bg","https://api.bitget.com/api/v2/mix/market/open-interest",{"symbol":"BTCUSDT","productType":"usdt-futures"});oi["bitget_BTCUSDT_btc"]=float(x["data"]["openInterestList"][0]["size"]);oi["bitget_ts"]=x["data"].get("ts")
x=G("oi_dr","https://www.deribit.com/api/v2/public/get_book_summary_by_instrument",{"instrument_name":"BTC-PERPETUAL"});oi["deribit_perp_usd"]=x["result"][0]["open_interest"]
x=G("oi_hl","https://api.hyperliquid.xyz/info",method="POST",body={"type":"metaAndAssetCtxs"});
if x:
    i=[k for k,u in enumerate(x[0]["universe"]) if u["name"]=="BTC"][0];oi["hyperliquid_btc"]=float(x[1][i]["openInterest"])
x=G("oi_kf","https://futures.kraken.com/derivatives/api/v3/tickers")
if x:
    for t in x["tickers"]:
        if t["symbol"]=="PF_XBTUSD": oi["krakenfut_PF_XBTUSD"]=t.get("openInterest")
x=G("oi_gt","https://api.gateio.ws/api/v4/futures/usdt/contracts/BTC_USDT")
if x: oi["gate_position_size_contracts"]=x["position_size"];oi["gate_quanto_multiplier"]=x["quanto_multiplier"]
x=G("oi_bf","https://api-pub.bitfinex.com/v2/status/deriv",{"keys":"tBTCF0:USTF0"})
if x: oi["bitfinex_row"]=x[0]
x=G("oi_dx","https://indexer.dydx.trade/v4/perpetualMarkets",{"ticker":"BTC-USD"})
if x: oi["dydx_btc"]=x["markets"]["BTC-USD"]["openInterest"]
x=G("oi_okxh","https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-history",{"instId":"BTC-USDT-SWAP","period":"5m","limit":"100"})
oi["okx_oi_hist_rows"]=len(x["data"]) if x else None;oi["okx_oi_hist_span_h"]=(int(x["data"][0][0])-int(x["data"][-1][0]))/3.6e6 if x else None
x=G("oi_gs","https://api.gateio.ws/api/v4/futures/usdt/contract_stats",{"contract":"BTC_USDT","interval":"1h","limit":"100"});oi["gate_stats_rows"]=len(x) if x else None
oi["snapshot_ms"]=int(time.time()*1000)
R["oi_snapshot"]=oi
# ---- Options IV: Deribit vs OKX ----
dsum=G("o_dr","https://www.deribit.com/api/v2/public/get_book_summary_by_currency",{"currency":"BTC","kind":"option"})["result"]
osum=G("o_okx","https://www.okx.com/api/v5/public/opt-summary",{"uly":"BTC-USD"})["data"]
def dparse(n):
    p=n.split("-");return p[1],float(p[2]),p[3]
dm={}
for r in dsum:
    e,k,c=dparse(r["instrument_name"]);dm[(e,k,c)]=r
om={}
mon={m:i+1 for i,m in enumerate(["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"])}
def dexp(e):
    import re;m=re.match(r"(\d+)([A-Z]{3})(\d+)",e);return int(m.group(3))+2000,mon[m.group(2)],int(m.group(1))
for r in osum:
    p=r["instId"].split("-");y=int("20"+p[2][:2]);mo=int(p[2][2:4]);dd=int(p[2][4:]);om[((y,mo,dd),float(p[3]),p[4])]=r
common=[]
for (e,k,c),r in dm.items():
    key=(dexp(e),k,c)
    if key in om and r.get("mark_iv") and om[key].get("markVol"):
        common.append((dexp(e),k,c,r["mark_iv"],float(om[key]["markVol"])*100,r.get("underlying_price"),float(om[key].get("fwdPx") or 0),r.get("open_interest")))
R["opt_counts"]={"deribit_btc_options":len(dsum),"okx_btc_usd_options":len(osum),"common_instruments":len(common)}
diffs=[a[3]-a[4] for a in common]
R["opt_iv_diff_pts"]={"median":st.median(diffs),"mean":st.mean(diffs),"p05":sorted(diffs)[int(len(diffs)*.05)],"p95":sorted(diffs)[int(len(diffs)*.95)],"abs_median":st.median([abs(d) for d in diffs])} if diffs else None
# ATM-ish per expiry
by={}
for a in common:
    by.setdefault(a[0],[]).append(a)
atm=[]
for e,l in sorted(by.items())[:8]:
    u=l[0][5];best=min(l,key=lambda a:abs(a[1]-u)) if u else l[0]
    atm.append({"exp":e,"strike":best[1],"cp":best[2],"deribit_iv":best[3],"okx_iv":round(best[4],2)})
R["atm_by_expiry"]=atm
# DVOL
x=G("dvol","https://www.deribit.com/api/v2/public/get_volatility_index_data",{"currency":"BTC","start_timestamp":str(now-86400000*3),"end_timestamp":str(now),"resolution":"3600"})
R["dvol_rows"]=len(x["result"]["data"]) if x else None
# ---- Basis: Deribit futures & OKX futures ----
fut=G("b_dr","https://www.deribit.com/api/v2/public/get_book_summary_by_currency",{"currency":"BTC","kind":"future"})["result"]
R["deribit_futures"]=[{"n":r["instrument_name"],"mark":r["mark_price"],"est_delivery":r.get("estimated_delivery_price"),"oi":r["open_interest"]} for r in fut]
okf=G("b_okx","https://www.okx.com/api/v5/public/instruments",{"instType":"FUTURES","uly":"BTC-USD"})
R["okx_future_instruments"]=[{"id":r["instId"],"exp":r["expTime"],"listTime":r["listTime"]} for r in okf["data"]] if okf else None
kf=G("b_kf","https://futures.kraken.com/derivatives/api/v3/tickers")
R["kraken_fut_fixed_maturity"]=[{k:t.get(k) for k in("symbol","markPrice","last","openInterest","lastTime")} for t in kf["tickers"] if t["symbol"].startswith("FI_XBT")] if kf else None
# ---- Liquidations REST depth ----
x=G("l_okx","https://www.okx.com/api/v5/public/liquidation-orders",{"instType":"SWAP","uly":"BTC-USDT","state":"filled"})
ts=[int(d["time"]) for r in x["data"] for d in r["details"]];R["liq_okx"]={"n":len(ts),"span_min":(max(ts)-min(ts))/6e4 if ts else None}
x=G("l_gt","https://api.gateio.ws/api/v4/futures/usdt/liq_orders",{"contract":"BTC_USDT","limit":"100"});ts=[int(r["time"]) for r in x] if x else [];R["liq_gate"]={"n":len(ts),"span_min":(max(ts)-min(ts))/60 if ts else None}
x=G("l_bf","https://api-pub.bitfinex.com/v2/liquidations/hist",{"limit":"500"});ts=[r[0][2] for r in x] if x else [];R["liq_bitfinex_all_symbols"]={"n":len(ts),"span_min":(max(ts)-min(ts))/6e4 if ts else None}
x=G("l_bx","https://www.bitmex.com/api/v1/liquidation",{"count":"100","reverse":"true"});R["liq_bitmex_now"]={"n":len(x) if x else None}
json.dump(R,open("../results/derivs_analysis.json","w"),indent=1,default=str)
print(json.dumps(R,indent=1,default=str)[:6500])
