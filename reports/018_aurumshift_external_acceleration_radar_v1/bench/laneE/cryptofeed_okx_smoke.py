"""Lane E — L1 smoke cryptofeed 3.0.x (AGPL, py>=3.13) sur OKX, ~DUR s.
Compte les callbacks par canal, vérifie présence exchange ts + receipt ts. Port 8443 réécrit en 443 (egress sandbox)."""
import json, sys, time, asyncio, threading, os, signal
from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES, L2_BOOK, FUNDING, OPEN_INTEREST, LIQUIDATIONS, TICKER
from cryptofeed.exchanges import OKX
import cryptofeed
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 25
for ep in OKX.websocket_endpoints:
    ep.address = ep.address.replace(":8443", "")
stats = {}
def mk(ch):
    async def cb(obj, receipt_timestamp):
        d = stats.setdefault(ch, {"n": 0, "lag_ms": []})
        d["n"] += 1
        ts = getattr(obj, "timestamp", None)
        if d["n"] == 1:
            d["first"] = {"type": type(obj).__name__, "symbol": getattr(obj, "symbol", None), "exchange_ts": ts, "receipt_ts": receipt_timestamp,
                          "fields": [f for f in dir(obj) if not f.startswith("_")][:40]}
        if ts: d["lag_ms"].append((receipt_timestamp - ts) * 1000)
    return cb
fh = FeedHandler(config={"log": {"filename": os.devnull, "level": "WARNING"}})
fh.add_feed(OKX(symbols=["BTC-USDT-PERP", "BTC-USDT"], channels=[TRADES, L2_BOOK, TICKER], callbacks={TRADES: mk("trades"), L2_BOOK: mk("l2"), TICKER: mk("ticker")}))
fh.add_feed(OKX(symbols=["BTC-USDT-PERP", "DOGE-USDT-PERP"], channels=[FUNDING, OPEN_INTEREST, LIQUIDATIONS], callbacks={FUNDING: mk("funding"), OPEN_INTEREST: mk("oi"), LIQUIDATIONS: mk("liq")}))
def stop():
    time.sleep(DUR); os.kill(os.getpid(), signal.SIGINT)
threading.Thread(target=stop, daemon=True).start()
t0 = time.time()
try:
    fh.run()
except (KeyboardInterrupt, SystemExit):
    pass
out = {"cryptofeed": cryptofeed.__version__ if hasattr(cryptofeed, "__version__") else "3.0.x", "duration_s": round(time.time() - t0, 1)}
for ch, d in stats.items():
    lag = sorted(d.pop("lag_ms"))
    d["lag_ms_p50"] = round(lag[len(lag)//2], 1) if lag else None
    d["lag_ms_min"] = round(lag[0], 1) if lag else None
out["channels"] = stats
print(json.dumps(out, indent=1, default=str))
