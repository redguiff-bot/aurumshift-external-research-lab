"""Fetch public Binance Vision USD-M bulk files -> compact hourly parquet (data/). No credentials."""
import io, zipfile, sys, time, datetime as dt, requests, pandas as pd
from concurrent.futures import ThreadPoolExecutor
B = "https://data.binance.vision/data/futures/um"
CORE = ["BTC","ETH","SOL","XRP","BNB","DOGE","ADA","LINK","AVAX","LTC"]
HOLD = ["DOT","ATOM","NEAR","TRX","BCH","ETC"]
MONTHS = [f"{y}-{m:02d}" for y in (2022, 2023, 2024, 2025) for m in range(1, 13)] + [f"2026-{m:02d}" for m in range(1, 9)]
MONTHS = [m for m in MONTHS if m >= "2022-10"]   # 2022-10..2022-12 = warm-up only
S = requests.Session()
def get(url):
    for i in range(4):
        try:
            r = S.get(url, timeout=30)
            if r.status_code == 200: return r.content
            if r.status_code == 404: return None
        except Exception: pass
        time.sleep(1 + i)
    return None
def csv(content, names=None):
    z = zipfile.ZipFile(io.BytesIO(content)); raw = z.read(z.namelist()[0]).decode()
    first = raw.split("\n", 1)[0].split(",")[0]
    return pd.read_csv(io.StringIO(raw), header=0 if not first.lstrip("-").isdigit() and not first[:2].isdigit() else None)
def kl(sym, kind, m):
    c = get(f"{B}/monthly/{kind}/{sym}USDT/1h/{sym}USDT-1h-{m}.zip")
    if c is None: return None
    d = csv(c); d.columns = ["open_time","open","high","low","close","volume","close_time","quote_volume","count","taker_buy_volume","taker_buy_quote_volume","ignore"][:d.shape[1]]
    return d
def fund(sym, m):
    c = get(f"{B}/monthly/fundingRate/{sym}USDT/{sym}USDT-fundingRate-{m}.zip")
    return None if c is None else csv(c)
def metr(sym, day):
    c = get(f"{B}/daily/metrics/{sym}USDT/{sym}USDT-metrics-{day}.zip")
    return None if c is None else csv(c)
def run(sym):
    with ThreadPoolExecutor(8) as ex:
        for kind, name in (("klines", "kl"), ("premiumIndexKlines", "prem")):
            parts = [p for p in ex.map(lambda m: kl(sym, kind, m), MONTHS) if p is not None]
            d = pd.concat(parts); d["ts"] = pd.to_datetime(d.open_time.astype("int64"), unit="ms")
            d = d.drop_duplicates("ts").set_index("ts").sort_index().drop(columns=["open_time","close_time","ignore"]).astype(float)
            d.to_parquet(f"../data/{sym}_{name}.parquet")
        parts = [p for p in ex.map(lambda m: fund(sym, m), MONTHS) if p is not None]
        f = pd.concat(parts); f.columns = ["calc_time","interval_h","rate"]
        f["ts"] = pd.to_datetime(f.calc_time.astype("int64"), unit="ms"); f.set_index("ts").sort_index()[["rate","interval_h"]].to_parquet(f"../data/{sym}_fund.parquet")
        days = [d.strftime("%Y-%m-%d") for d in pd.date_range("2022-10-01", "2026-09-27")]
        parts = [p for p in ex.map(lambda d: metr(sym, d), days) if p is not None]
        m = pd.concat(parts); m["ts"] = pd.to_datetime(m.create_time)
        m = m.set_index("ts").sort_index().drop(columns=["create_time","symbol"]).astype(float)
        m = m[~m.index.duplicated()]
        m.to_parquet(f"../data/{sym}_metrics5m.parquet")
    print(sym, "done", flush=True)
if __name__ == "__main__":
    for s in sys.argv[1:] or CORE + HOLD: run(s)
