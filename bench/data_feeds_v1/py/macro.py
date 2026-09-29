import json,time,csv,io,statistics as st
from datetime import datetime,timezone
from probe_lib import call
R={}
def G(n,u,p=None,timeout=45,**k): 
    o=call(n,u,p,save=False,timeout=timeout,**k);time.sleep(0.3);return o
# FRED / ALFRED retry
for n,u in [("fred_dgs10","https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"),("alfred_gdpc1_2020-01-30","https://alfred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1&vintage_date=2020-01-30"),("fred_api_v1_doc","https://api.stlouisfed.org/fred/series?series_id=GDPC1&api_key=abcdefghijklmnopqrstuvwxyz012345&file_type=json"),("fred_dgs10_www","https://fred.stlouisfed.org/data/DGS10.txt"),("fred_series_page","https://fred.stlouisfed.org/series/DGS10")]:
    o=G(n,u,timeout=40);R[n]={k:o.get(k) for k in("status","ms","bytes","err")};R[n]["head"]=(o.get("text") or json.dumps(o.get("json"))or"")[:200]
# Treasury yields vs NYFed
t=G("tsy","https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2026/all?type=daily_treasury_yield_curve&field_tdr_date_value=2026&page&_format=csv").get("text","")
rows=list(csv.DictReader(io.StringIO(t)));R["treasury_yield_csv"]={"rows":len(rows),"first":rows[0]["Date"],"last":rows[-1]["Date"],"cols":list(rows[0].keys())[:6],"latest_10y":rows[0]["10 Yr"]}
# Treasury older vintage: year 1990
t2=G("tsy90","https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/1990/all?type=daily_treasury_yield_curve&field_tdr_date_value=1990&page&_format=csv").get("text","");R["treasury_1990_rows"]=len(t2.splitlines())-1
# ECB SDMX revisions: fetch same series twice + updatedAfter probe
e=G("ecbx","https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?startPeriod=2026-09-20&format=csvdata").get("text","")
R["ecb_csv"]={"rows":len(e.splitlines())-1,"cols":e.splitlines()[0][:220]}
e2=G("ecbu","https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?updatedAfter=2026-09-01T00:00:00Z&startPeriod=2026-08-01&format=csvdata");R["ecb_updatedAfter"]={"status":e2.get("status"),"rows":len((e2.get("text") or "").splitlines())-1}
e3=G("ecbh","https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?startPeriod=1999-01-04&endPeriod=1999-01-08&format=csvdata").get("text","");R["ecb_1999"]=e3.splitlines()[1][-60:] if e3 else None
# NYFed
n=G("nyfed","https://markets.newyorkfed.org/api/rates/secured/sofr/last/5.json").get("json");R["nyfed_sofr"]={"latest":n["refRates"][0]["effectiveDate"],"pct":n["refRates"][0]["percentRate"],"keys":list(n["refRates"][0].keys())[:12]}
n2=G("nyfed_search","https://markets.newyorkfed.org/api/rates/secured/sofr/search.json?startDate=2018-04-03&endDate=2018-04-05").get("json");R["nyfed_sofr_2018"]=n2["refRates"][:1] if n2 else None
# BLS
b=G("bls","https://api.bls.gov/publicAPI/v1/timeseries/data/CUUR0000SA0").get("json");R["bls_v1"]={"status":b.get("status"),"msg":b.get("message")}
b2=G("bls2","https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0").get("json");R["bls_v2_nokey"]={"status":b2.get("status"),"msg":b2.get("message")}
# Eurostat
es=G("es","https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?geo=EA&coicop=CP00&lastTimePeriod=3").get("json");R["eurostat"]={"updated":es.get("updated"),"value":es.get("value"),"time":es["dimension"]["time"]["category"]["index"]}
# BoC
bc=G("boc","https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=3").get("json");R["boc"]=bc["observations"]
# BoE csv done; CFTC
c=G("cftc","https://publicreporting.cftc.gov/resource/6dca-aqww.json?$limit=2&$order=report_date_as_yyyy_mm_dd DESC&$where=market_and_exchange_names like '%25GOLD%25'").get("json");R["cftc_gold"]=[{k:x.get(k) for k in("market_and_exchange_names","report_date_as_yyyy_mm_dd","open_interest_all","cftc_contract_market_code")} for x in c] if c else None
c2=G("cftc_old","https://publicreporting.cftc.gov/resource/6dca-aqww.json?$limit=1&$order=report_date_as_yyyy_mm_dd ASC").get("json");R["cftc_oldest"]=c2[0]["report_date_as_yyyy_mm_dd"] if c2 else None
# World Bank
w=G("wb","https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD?format=json&per_page=3").get("json");R["worldbank"]={"meta":w[0],"first":w[1][0]["date"]}
# LBMA
l=G("lbma","https://prices.lbma.org.uk/json/gold_am.json").get("json");R["lbma_gold_am"]={"n":len(l),"first":l[0],"last":l[-1],"keys":list(l[0].keys())}
# ForexFactory calendar twice
f1=G("ff1","https://nfs.faireconomy.media/ff_calendar_thisweek.json");time.sleep(2);f2=G("ff2","https://nfs.faireconomy.media/ff_calendar_thisweek.json")
j=f1["json"];R["ff_calendar"]={"events":len(j),"keys":list(j[0].keys()),"impacts":sorted({x["impact"] for x in j}),"countries":sorted({x["country"] for x in j})[:12],"with_actual":sum(1 for x in j if x.get("actual")),"identical_two_fetches":f1["json"]==f2["json"],"hdr":f1.get("hdr"),"sample":j[0]}
ffn=G("ffn","https://nfs.faireconomy.media/ff_calendar_nextweek.json");R["ff_nextweek"]={"status":ffn.get("status"),"n":len(ffn.get("json") or [])}
ffl=G("ffl","https://nfs.faireconomy.media/ff_calendar_lastweek.json");R["ff_lastweek"]={"status":ffl.get("status")}
# Yahoo commodities
for nm,sym in [("wti","CL=F"),("brent","BZ=F"),("natgas","NG=F"),("copper","HG=F"),("silver","SI=F"),("dxy","DX-Y.NYB"),("spx","^GSPC")]:
    y=G("y"+nm,"https://query1.finance.yahoo.com/v8/finance/chart/"+sym,{"interval":"1h","range":"5d"})
    R["yahoo_"+nm]={"status":y.get("status"),"n":len(y["json"]["chart"]["result"][0]["timestamp"]) if y.get("ok") and y["json"]["chart"]["result"] else None}
# Fear&greed, mempool, blockchain.info
R["fear_greed_rows"]=len(G("fg","https://api.alternative.me/fng/?limit=0").get("json",{}).get("data",[]))
json.dump(R,open("../results/macro_tests.json","w"),indent=1,default=str)
print(json.dumps(R,indent=1,default=str)[:7000])
