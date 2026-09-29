"""Deribit DVOL (BTC/ETH hourly) and Coinbase spot 1h candles (wrong-venue test). Public endpoints, no keys."""
import requests, time, pandas as pd, datetime as dt
S = requests.Session()
def j(url, params=None):
    for i in range(5):
        try:
            r = S.get(url, params=params, timeout=30)
            if r.status_code == 200: return r.json()
            if r.status_code == 429: time.sleep(2 + i)
        except Exception: time.sleep(1 + i)
    return None
def dvol(cur):
    rows = []; t0 = int(pd.Timestamp("2022-10-01").timestamp() * 1000); end = int(pd.Timestamp("2026-09-28").timestamp() * 1000)
    step = 40 * 86400_000
    while t0 < end:
        r = j("https://www.deribit.com/api/v2/public/get_volatility_index_data", dict(currency=cur, start_timestamp=t0, end_timestamp=min(t0 + step, end), resolution=3600))
        if r and "result" in r: rows += r["result"]["data"]
        t0 += step
    d = pd.DataFrame(rows, columns=["t","open","high","low","close"]); d["ts"] = pd.to_datetime(d.t, unit="ms")
    d = d.drop_duplicates("ts").set_index("ts").sort_index().drop(columns="t"); d.to_parquet(f"../data/{cur}_dvol.parquet"); print(cur, len(d), d.index[0], d.index[-1], flush=True)
def coinbase(sym):
    rows = []; t0 = pd.Timestamp("2024-12-01"); end = pd.Timestamp("2026-09-01")
    while t0 < end:
        t1 = t0 + pd.Timedelta(hours=299)
        r = j(f"https://api.exchange.coinbase.com/products/{sym}-USD/candles", dict(granularity=3600, start=t0.isoformat(), end=t1.isoformat()))
        if r: rows += r
        t0 = t1 + pd.Timedelta(hours=1); time.sleep(0.15)
    d = pd.DataFrame(rows, columns=["t","low","high","open","close","volume"]); d["ts"] = pd.to_datetime(d.t, unit="s")
    d = d.drop_duplicates("ts").set_index("ts").sort_index().drop(columns="t"); d.to_parquet(f"../data/{sym}_cb.parquet"); print(sym, len(d), flush=True)
if __name__ == "__main__":
    for c in ("BTC","ETH"): dvol(c)
    for s in ["BTC","ETH","SOL","XRP","DOGE","ADA","LINK","AVAX","LTC"]: coinbase(s)
