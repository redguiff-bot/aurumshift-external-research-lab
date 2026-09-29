import time, json, importlib.metadata as md, os, asyncio, sys
from common import save
CA = "/root/.ccr/ca-bundle.crt"   # egress-proxy CA in this sandbox; ccxt passes verify=(verify and validateServerSsl) so a CA path must go through validateServerSsl; TLS verification stays ON
res = {"versions": {"ccxt": md.version("ccxt"), "cryptofeed": md.version("cryptofeed")}}
t0 = time.perf_counter(); import ccxt; res["ccxt_import_seconds"] = round(time.perf_counter() - t0, 2)
res["ccxt_n_exchanges"] = len(ccxt.exchanges)
out = {}
for ex_id, sym in (("kraken", "BTC/USD"), ("coinbase", "BTC/USD"), ("okx", "BTC/USDT"), ("bitstamp", "BTC/USD"), ("binance", "BTC/USDT"), ("bybit", "BTC/USDT")):
    try:
        ex = getattr(ccxt, ex_id)({"enableRateLimit": True, "timeout": 15000, "validateServerSsl": CA}); t0 = time.perf_counter()
        rows = ex.fetch_ohlcv(sym, "1m", limit=100); dt = time.perf_counter() - t0
        ts = [r[0] for r in rows]
        out[ex_id] = {"ok": True, "n": len(rows), "seconds": round(dt, 2), "first_ts": ts[0], "step_ms_unique": sorted(set(b - a for a, b in zip(ts, ts[1:])))[:3], "last_bar_is_forming": bool(ts[-1] > time.time()*1000 - 60_000)}
    except Exception as e: out[ex_id] = {"ok": False, "error": f"{type(e).__name__}: {str(e)[:120]}"}
res["ccxt_fetch_ohlcv"] = out
# trades pagination + timestamps: does ccxt expose server timestamp vs local receipt?
try:
    ex = ccxt.kraken({"enableRateLimit": True, "validateServerSsl": CA}); tr = ex.fetch_trades("BTC/USD", limit=5)
    res["ccxt_trade_fields"] = sorted(tr[0].keys())
    res["ccxt_trade_has_receipt_ts"] = False if "receipt_ts" not in tr[0] and "received" not in tr[0] else True
except Exception as e: res["ccxt_trade_fields"] = f"error {e}"
# cryptofeed: 20 s live trades, one exchange per run (no keys)
def cf_run(name):
    import subprocess, textwrap
    code = textwrap.dedent(f"""
        import asyncio, json, time, sys, threading
        from cryptofeed import FeedHandler
        from cryptofeed.defines import TRADES
        from cryptofeed.exchanges import {name}
        cnt = {{"n": 0, "first": None}}
        async def on_trade(t, receipt):
            cnt["n"] += 1
            if cnt["first"] is None: cnt["first"] = {{"exchange": t.exchange, "symbol": t.symbol, "ts": t.timestamp, "receipt": receipt, "id": t.id}}
        fh = FeedHandler()
        asyncio.set_event_loop(asyncio.new_event_loop())   # required workaround: cryptofeed 2.4.1 + uvloop 0.22 on py3.11 -> 'no current event loop' otherwise
        sym = "BTC-USD"
        fh.add_feed({name}(symbols=[sym], channels=[TRADES], callbacks={{TRADES: on_trade}}))
        fh.run(start_loop=False)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.sleep(20))
        print(json.dumps(cnt)); sys.stdout.flush(); import os; os._exit(0)
    """)
    try:
        p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
        last = [l for l in p.stdout.splitlines() if l.startswith("{")]
        return json.loads(last[-1]) if last else {"error": (p.stderr.strip().splitlines() or ["no output"])[-1][:200]}
    except Exception as e: return {"error": f"{type(e).__name__}: {e}"}
res["cryptofeed_20s_live"] = {n: cf_run(n) for n in ("Kraken", "Bitstamp", "Coinbase")}
print(json.dumps(res, indent=1, default=str)); save("coll_microtest.json", res)
os._exit(0)
