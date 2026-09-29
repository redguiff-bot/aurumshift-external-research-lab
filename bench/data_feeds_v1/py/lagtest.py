import json,math,statistics as st
a=json.load(open("../raw/bars_t2.json"));S,E=a["start"],a["end"]
def cl(v): return {x[0]:x[4] for x in a["venues"][v]["bars"] if S<=x[0]<E}
ref=cl("kraken_spot_XBTUSD")
out={}
for v in a["venues"]:
    c=cl(v)
    if len(c)<100: continue
    res={}
    for lag in range(-3,4):
        ts=[t for t in sorted(c) if t+lag*60000 in ref and t+lag*60000-60000 in ref and t-60000 in c]
        r1=[math.log(c[t]/c[t-60000]) for t in ts];r2=[math.log(ref[t+lag*60000]/ref[t+lag*60000-60000]) for t in ts]
        try:res[lag]=round(st.correlation(r1,r2),3)
        except: pass
    best=max(res,key=res.get);out[v]={"best_lag_min":best,"corr_by_lag":res}
    print(f"{v:30s} best_lag={best:+d} corr@0={res.get(0)} corr@best={res[best]}")
json.dump(out,open("../results/lag_test_vs_kraken.json","w"),indent=1)
