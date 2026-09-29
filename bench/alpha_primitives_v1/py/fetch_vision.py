"""Fetch Binance Vision public archives (spot/um klines 1h, premium index 1h, funding, daily 5m metrics).
Cache: bench/alpha_primitives_v1/cache (git-ignored). Manifest with sha256 written to results/vision_manifest.json.
Missing files (404) are recorded, never imputed."""
import io, os, sys, zipfile, hashlib, json, time, datetime as dt
from concurrent.futures import ThreadPoolExecutor
import requests
import pandas as pd

BASE = "https://data.binance.vision/data"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
SYMS = ["BTC", "ETH", "SOL", "XRP", "BNB", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
MONTHS = [f"{y}-{m:02d}" for y in (2024, 2025, 2026) for m in range(1, 13) if (y, m) <= (2026, 8)]
S = requests.Session()
MAN = {}

def get(url):
    for k in range(4):
        try:
            r = S.get(url, timeout=30)
            if r.status_code == 200:
                return r.content
            if r.status_code == 404:
                return None
        except Exception:
            pass
        time.sleep(1 + 2 * k)
    return None

def csv_from_zip(b):
    z = zipfile.ZipFile(io.BytesIO(b))
    return z.read(z.namelist()[0])

def job(spec):
    kind, sym, per = spec
    s = sym + "USDT"
    if kind == "spot_kl": u = f"{BASE}/spot/monthly/klines/{s}/1h/{s}-1h-{per}.zip"
    elif kind == "um_kl": u = f"{BASE}/futures/um/monthly/klines/{s}/1h/{s}-1h-{per}.zip"
    elif kind == "um_prem": u = f"{BASE}/futures/um/monthly/premiumIndexKlines/{s}/1h/{s}-1h-{per}.zip"
    elif kind == "um_fund": u = f"{BASE}/futures/um/monthly/fundingRate/{s}/{s}-fundingRate-{per}.zip"
    elif kind == "um_metrics": u = f"{BASE}/futures/um/daily/metrics/{s}/{s}-metrics-{per}.zip"
    d = os.path.join(CACHE, kind, sym); os.makedirs(d, exist_ok=True)
    fp = os.path.join(d, per + ".csv")
    if os.path.exists(fp):
        return spec, "cached", hashlib.sha256(open(fp, "rb").read()).hexdigest()
    b = get(u)
    if b is None:
        return spec, "missing", None
    raw = csv_from_zip(b)
    open(fp, "wb").write(raw)
    return spec, "ok", hashlib.sha256(raw).hexdigest()

if __name__ == "__main__":
    kinds = sys.argv[1:] or ["spot_kl", "um_kl", "um_prem", "um_fund", "um_metrics"]
    specs = []
    for k in kinds:
        if k == "um_metrics":
            d0, d1 = dt.date(2024, 1, 1), dt.date(2026, 8, 31)
            days = [(d0 + dt.timedelta(i)).isoformat() for i in range((d1 - d0).days + 1)]
            specs += [(k, s, d) for s in SYMS for d in days]
        else:
            specs += [(k, s, m) for s in SYMS for m in MONTHS]
    with ThreadPoolExecutor(24) as ex:
        res = list(ex.map(job, specs))
    man = {}
    for (k, s, p), st, h in res:
        man.setdefault(k, {}).setdefault(s, {})[p] = {"status": st, "sha256": h}
    fn = os.path.join(ROOT, "results", "vision_manifest.json")
    old = json.load(open(fn)) if os.path.exists(fn) else {}
    old.update(man)
    json.dump(old, open(fn, "w"))
    from collections import Counter
    print(Counter((k, st) for (k, s, p), st, h in res))
