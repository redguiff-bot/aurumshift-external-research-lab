"""Fetch + cache public hourly klines (Binance Vision public data API). External research only."""
import gzip, hashlib, json, os, sys, time, urllib.request
import numpy as np, pandas as pd

RAW = os.path.join(os.path.dirname(__file__), "..", "raw")
BASE = "https://data-api.binance.vision/api/v3/klines"
COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_vol",
        "trades", "taker_base", "taker_quote", "ignore"]

def fetch(symbol, n_bars=20000, interval="1h", end_ms=None):
    rows, end = [], end_ms
    while len(rows) < n_bars:
        url = f"{BASE}?symbol={symbol}&interval={interval}&limit=1000" + (f"&endTime={end}" if end else "")
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=30) as r:
                    b = json.loads(r.read())
                break
            except Exception:
                time.sleep(2 ** attempt)
        else:
            raise RuntimeError(url)
        if not b:
            break
        rows = b + rows
        end = b[0][0] - 1
        if len(b) < 1000:
            break
    df = pd.DataFrame(rows, columns=COLS).iloc[-n_bars:]
    for c in COLS:
        df[c] = pd.to_numeric(df[c])
    return df.drop(columns=["ignore", "close_time"]).reset_index(drop=True)

def path(sym): return os.path.join(RAW, f"{sym}_1h.csv.gz")

def load(sym):
    return pd.read_csv(path(sym))

if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    # freeze one common end time so all markets share the same window
    end_ms = int(pd.Timestamp("2026-09-01", tz="UTC").timestamp() * 1000)
    manifest = {}
    for s in sys.argv[1:]:
        df = fetch(s, end_ms=end_ms)
        df.to_csv(path(s), index=False, compression="gzip")
        manifest[s] = dict(rows=len(df), first=int(df.open_time.iloc[0]), last=int(df.open_time.iloc[-1]),
                           sha256=hashlib.sha256(open(path(s), "rb").read()).hexdigest())
        print(s, manifest[s], flush=True)
    json.dump(manifest, open(os.path.join(RAW, "manifest.json"), "w"), indent=1)
