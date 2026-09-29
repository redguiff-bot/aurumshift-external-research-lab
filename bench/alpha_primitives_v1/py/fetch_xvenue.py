"""Cross-venue public data (OKX, Coinbase, Gate, Kraken, Hyperliquid, Deribit DVOL) for falsification. No API keys."""
import os, sys, json, time, datetime as dt
import requests
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = os.path.join(ROOT, "cache", "xv"); os.makedirs(C, exist_ok=True)
S = requests.Session()
T0 = int(dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc).timestamp())
T1 = int(dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc).timestamp())
A = ["BTC", "ETH", "SOL", "XRP", "DOGE"]
LOG = {}

def j(method, url, **kw):
    for k in range(5):
        try:
            r = S.request(method, url, timeout=30, **kw)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429: time.sleep(2 + 2 * k)
        except Exception as e:
            time.sleep(1 + k)
    return None

def okx(a):
    out, after = [], T1 * 1000
    while True:
        d = j("GET", "https://www.okx.com/api/v5/market/history-candles", params={"instId": f"{a}-USDT-SWAP", "bar": "1H", "after": after, "limit": 100})
        if not d or not d.get("data"): break
        rows = d["data"]; out += rows; after = int(rows[-1][0])
        if after < T0 * 1000: break
        time.sleep(0.12)
    df = pd.DataFrame(out, columns=["ts", "o", "h", "l", "c", "vol", "volccy", "volquote", "conf"]).astype(float)
    return df[df.ts >= T0 * 1000].drop_duplicates("ts").sort_values("ts")

def coinbase(a):
    out = []; s = T0
    while s < T1:
        e = min(s + 300 * 3600, T1)
        d = j("GET", f"https://api.exchange.coinbase.com/products/{a}-USD/candles", params={"granularity": 3600, "start": dt.datetime.fromtimestamp(s, dt.timezone.utc).isoformat(), "end": dt.datetime.fromtimestamp(e, dt.timezone.utc).isoformat()})
        if d: out += d
        s = e; time.sleep(0.15)
    df = pd.DataFrame(out, columns=["ts", "l", "h", "o", "c", "vol"]).astype(float)
    df["ts"] *= 1000
    return df.drop_duplicates("ts").sort_values("ts")

def gate(a):
    out = []; s = T0
    while s < T1:
        e = min(s + 990 * 3600, T1)
        d = j("GET", "https://api.gateio.ws/api/v4/spot/candlesticks", params={"currency_pair": f"{a}_USDT", "interval": "1h", "from": s, "to": e})
        if d: out += d
        s = e; time.sleep(0.15)
    df = pd.DataFrame(out).iloc[:, :6]; df.columns = ["ts", "quote_vol", "c", "h", "l", "o"]
    df = df.astype(float); df["ts"] *= 1000
    return df.drop_duplicates("ts").sort_values("ts")

def hl_candles(a):
    e = T1 * 1000
    d = j("POST", "https://api.hyperliquid.xyz/info", json={"type": "candleSnapshot", "req": {"coin": a, "interval": "1h", "startTime": T0 * 1000, "endTime": e}})
    if not d: return pd.DataFrame()
    df = pd.DataFrame(d)[["t", "o", "h", "l", "c", "v"]].astype(float).rename(columns={"t": "ts"})
    return df.drop_duplicates("ts").sort_values("ts")

def hl_funding(a):
    out, s = [], T0 * 1000
    while s < T1 * 1000:
        d = j("POST", "https://api.hyperliquid.xyz/info", json={"type": "fundingHistory", "coin": a, "startTime": s})
        if not d: break
        out += d; ns = d[-1]["time"] + 1
        if ns <= s or len(d) < 500: break
        s = ns; time.sleep(0.1)
    df = pd.DataFrame(out)
    if len(df): df["fundingRate"] = df.fundingRate.astype(float); df["premium"] = df.premium.astype(float)
    return df

def kraken(a):
    p = {"BTC": "XBTUSD", "ETH": "ETHUSD", "SOL": "SOLUSD", "XRP": "XRPUSD", "DOGE": "DOGEUSD"}[a]
    d = j("GET", "https://api.kraken.com/0/public/OHLC", params={"pair": p, "interval": 60})
    if not d or d.get("error"): return pd.DataFrame()
    k = [v for kk, v in d["result"].items() if kk != "last"][0]
    df = pd.DataFrame(k, columns=["ts", "o", "h", "l", "c", "vwap", "vol", "n"]).astype(float); df["ts"] *= 1000
    return df

def dvol(cur):
    out, s = [], T0
    while s < T1:
        e = min(s + 40 * 86400, T1)
        d = j("GET", "https://www.deribit.com/api/v2/public/get_volatility_index_data", params={"currency": cur, "start_timestamp": s * 1000, "end_timestamp": e * 1000, "resolution": 3600})
        if d and "result" in d: out += d["result"]["data"]
        s = e; time.sleep(0.2)
    df = pd.DataFrame(out, columns=["ts", "o", "h", "l", "c"]).astype(float)
    return df.drop_duplicates("ts").sort_values("ts")

if __name__ == "__main__":
    for name, fn, args in [("dvol", dvol, ["BTC", "ETH"]), ("okx", okx, A), ("coinbase", coinbase, A), ("gate", gate, A), ("hl_c", hl_candles, A), ("hl_f", hl_funding, A), ("kraken", kraken, A)]:
        for a in args:
            fp = os.path.join(C, f"{name}_{a}.csv")
            if os.path.exists(fp): continue
            try:
                df = fn(a)
            except Exception as e:
                print(name, a, "ERR", e); continue
            df.to_csv(fp, index=False)
            LOG[f"{name}_{a}"] = {"rows": len(df), "first": None if not len(df) else str(df.iloc[0, 0]), "last": None if not len(df) else str(df.iloc[-1, 0])}
            print(name, a, len(df), flush=True)
    json.dump(LOG, open(os.path.join(ROOT, "results", "xvenue_manifest.json"), "w"), indent=1)
