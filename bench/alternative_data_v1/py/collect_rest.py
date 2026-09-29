"""Second collection pass: Wikipedia pageviews, npm downloads, Deribit DVOL (rate-limited endpoints, patient backoff)."""
import time, os, pandas as pd, requests
from collect import *
def slow(url, params=None):
    for i in range(6):
        r = S.get(url, params=params, timeout=60)
        if r.status_code == 200: return r
        time.sleep(int(r.headers.get("retry-after", 15)) + 5)
    r.raise_for_status()
today = pd.Timestamp.utcnow().tz_localize(None).normalize(); last_full = today - pd.Timedelta(days=1)
for art in ["Bitcoin", "Ethereum"]:
    r = slow(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{art}/daily/{START.replace('-','')}/{last_full.strftime('%Y%m%d')}").json()
    w = pd.Series({pd.to_datetime(x["timestamp"], format="%Y%m%d%H"): x["views"] for x in r["items"]}, name=f"wiki_{art}")
    w.to_frame().to_csv(os.path.join(D, f"wiki_{art}.csv")); rec(f"wiki_{art}", rows=len(w)); time.sleep(3)
for pk in ["ethers", "web3", "bitcoinjs-lib", "@solana/web3.js"]:
    parts = []
    for a, b in [("2020-09-01", "2022-02-28"), ("2022-03-01", "2023-08-31"), ("2023-09-01", "2025-02-28"), ("2025-03-01", str(last_full.date()))]:
        parts += slow(f"https://api.npmjs.org/downloads/range/{a}:{b}/{pk}").json().get("downloads", []); time.sleep(1)
    s = pd.Series({pd.Timestamp(x["day"]): x["downloads"] for x in parts}, name="npm_" + pk.replace("@", "").replace("/", "_"))
    s.to_frame().to_csv(os.path.join(D, f"npm_{s.name}.csv")); rec(f"npm_{pk}", rows=len(s))
out = []; st = int(pd.Timestamp(START, tz="UTC").timestamp() * 1000); end = int(time.time() * 1000)
while st < end:
    r = slow("https://www.deribit.com/api/v2/public/get_volatility_index_data", {"currency": "BTC", "start_timestamp": st, "end_timestamp": min(end, st + 900 * 86400 * 1000), "resolution": 86400}).json()["result"]["data"]
    out += r; st += 900 * 86400 * 1000
dv = pd.DataFrame(out, columns=["ts", "o", "h", "l", "c"]).drop_duplicates("ts"); dv["date"] = pd.to_datetime(dv.ts, unit="ms").dt.normalize()
dv.set_index("date")[["o", "h", "l", "c"]].to_csv(os.path.join(D, "deribit_dvol_1d.csv")); rec("deribit_dvol", rows=len(dv), first=str(dv.date.min()), last=str(dv.date.max()))
print("rest done")
