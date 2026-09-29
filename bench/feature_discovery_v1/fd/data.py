"""Real-market data: Binance spot 1h klines via the public data-api.binance.vision mirror.

Frozen window (reproducibility): 2021-01-01T00:00Z .. 2026-09-01T00:00Z (exclusive).
Source is OBSERVED (fetched in-session); historical klines are immutable exchange records.
"""
import gzip, hashlib, io, json, os, sys, time, urllib.request
import numpy as np, pandas as pd

BASE = "https://data-api.binance.vision/api/v3/klines"
START_MS = 1609459200000
END_MS = 1788220800000
HOUR = 3600_000
DISCOVERY_MARKETS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
UNSEEN_MARKETS = ["XRPUSDT", "ADAUSDT", "DOGEUSDT", "LINKUSDT", "PAXGUSDT"]
COLS = ["open_time", "open", "high", "low", "close", "volume", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote"]
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa
            time.sleep(2 ** min(i, 4))
    raise RuntimeError("fetch failed " + url)


def fetch_symbol(sym):
    rows, t = [], START_MS
    while t < END_MS:
        k = _get(f"{BASE}?symbol={sym}&interval=1h&startTime={t}&endTime={END_MS - 1}&limit=1000")
        if not k:
            break
        rows += [[r[0], r[1], r[2], r[3], r[4], r[5], r[7], r[8], r[9], r[10]] for r in k]
        t = k[-1][0] + HOUR
        if len(k) < 2:
            break
    df = pd.DataFrame(rows, columns=COLS).drop_duplicates("open_time").sort_values("open_time")
    for c in COLS[1:]:
        df[c] = pd.to_numeric(df[c])
    return df.reset_index(drop=True)


def path(sym):
    return os.path.join(DATA_DIR, f"{sym}_1h.csv.gz")


def load(sym):
    df = pd.read_csv(path(sym))
    df.index = pd.to_datetime(df.pop("open_time"), unit="ms", utc=True)
    return df


def sha(sym):
    return hashlib.sha256(open(path(sym), "rb").read()).hexdigest()


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    man = {}
    for s in DISCOVERY_MARKETS + UNSEEN_MARKETS:
        if not os.path.exists(path(s)):
            df = fetch_symbol(s)
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as g:
                g.write(df.to_csv(index=False, float_format="%.10g").encode())
            open(path(s), "wb").write(buf.getvalue())
        d = load(s)
        man[s] = dict(rows=len(d), first=str(d.index[0]), last=str(d.index[-1]), sha256=sha(s),
                      gaps=int((d.index.to_series().diff().dropna() != pd.Timedelta(hours=1)).sum()))
        print(s, man[s], flush=True)
    json.dump(dict(source=BASE, start_ms=START_MS, end_ms=END_MS, files=man),
              open(os.path.join(DATA_DIR, "MANIFEST.json"), "w"), indent=1)
