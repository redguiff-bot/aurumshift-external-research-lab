"""Hyperliquid public hourly funding history (POST /info fundingHistory) -> data/{SYM}_hl_fund.parquet"""
import requests, time, pandas as pd
CORE = ["BTC","ETH","SOL","XRP","BNB","DOGE","ADA","LINK","AVAX","LTC"]
for s in CORE:
    rows = []; t = int(pd.Timestamp("2023-06-01").timestamp() * 1000); end = int(pd.Timestamp("2026-09-28").timestamp() * 1000)
    while t < end:
        r = requests.post("https://api.hyperliquid.xyz/info", json={"type": "fundingHistory", "coin": s, "startTime": t}, timeout=30)
        if r.status_code != 200: time.sleep(2); continue
        d = r.json()
        if not d: break
        rows += d; t = d[-1]["time"] + 1
        if len(d) < 500: break
        time.sleep(0.1)
    if not rows: print(s, "none"); continue
    d = pd.DataFrame(rows); d["ts"] = pd.to_datetime(d.time, unit="ms")
    d = d.drop_duplicates("ts").set_index("ts")[["fundingRate","premium"]].astype(float); d.to_parquet(f"../data/{s}_hl_fund.parquet"); print(s, len(d), d.index[0], d.index[-1], flush=True)
