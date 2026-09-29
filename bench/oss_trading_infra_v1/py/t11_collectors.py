"""T11 — market-data collectors/downloaders, real network calls from the test egress (2026-09-29).
ccxt REST OHLCV normalisation on 5 venues; ccxt.pro websocket trades; cryptofeed live trades (receipt timestamps); yfinance."""
import sys, json, time, asyncio, warnings, traceback, os; warnings.filterwarnings("ignore")
CA = os.environ.get("SSL_CERT_FILE")  # egress CA bundle; passed explicitly to ccxt (TLS verification stays ON)
which = sys.argv[1]; res = dict(candidate=which, now_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
if which == "ccxt_rest":
    import ccxt
    out = {}
    for ex_id, sym in [("kraken", "BTC/USD"), ("coinbase", "BTC/USD"), ("okx", "BTC/USDT"), ("bitstamp", "BTC/USD"), ("gate", "BTC/USDT"), ("kucoin", "BTC/USDT"), ("binance", "BTC/USDT"), ("bybit", "BTC/USDT")]:
        r = {}
        try:
            ex = getattr(ccxt, ex_id)({"enableRateLimit": True, "timeout": 15000})
            ex.validateServerSsl = CA  # ccxt evaluates verify=self.verify and self.validateServerSsl: a path in verify collapses to True (OBSERVED)
            t = time.perf_counter(); rows = ex.fetch_ohlcv(sym, "1m", limit=60); r["latency_s"] = round(time.perf_counter()-t, 3)
            ts = [x[0] for x in rows]; now_ms = int(time.time()*1000)
            r.update(n=len(rows), cols=len(rows[0]) if rows else 0, monotonic=all(b > a for a, b in zip(ts, ts[1:])), dup=len(ts)-len(set(ts)),
                     step_ms_set=sorted({b-a for a, b in zip(ts, ts[1:])})[:4], last_bar_open_age_s=round((now_ms-ts[-1])/1000, 1) if ts else None,
                     last_bar_is_forming=bool(ts and (now_ms - ts[-1]) < 60_000), has_receipt_ts=False, rate_limit_ms=ex.rateLimit)
        except Exception as e: r["error"] = f"{type(e).__name__}: {str(e)[:110]}"
        out[ex_id] = r
    res["venues"] = out; res["ccxt_version"] = ccxt.__version__
elif which == "ccxt_ws":
    import ccxt.pro as cp
    async def go():
        out = {}
        for ex_id, sym in [("kraken", "BTC/USD"), ("okx", "BTC/USDT"), ("coinbase", "BTC/USD")]:
            r = {}; ex = getattr(cp, ex_id)({"enableRateLimit": True, "aiohttp_trust_env": True}); import ssl; ex.ssl_context = ssl.create_default_context(cafile=CA)
            try:
                t0 = time.time(); n = 0; first = None
                while time.time()-t0 < 12:
                    tr = await asyncio.wait_for(ex.watch_trades(sym), timeout=12)
                    n += len(tr)
                    if first is None and tr: first = tr[0]
                r.update(n_trades_12s=n, keys=sorted(first.keys()) if first else None, has_local_receipt_field=any(k in (first or {}) for k in ("receipt_timestamp", "received", "local_timestamp")))
            except Exception as e: r["error"] = f"{type(e).__name__}: {str(e)[:110]}"
            finally:
                try: await ex.close()
                except Exception: pass
            out[ex_id] = r
        return out
    res["venues"] = asyncio.run(go())
elif which == "cryptofeed":
    from cryptofeed import FeedHandler
    from cryptofeed.defines import TRADES, L2_BOOK
    from cryptofeed.exchanges import Kraken, Coinbase, OKX
    seen = {"trades": [], "book": 0}
    async def trade(t, receipt): 
        if len(seen["trades"]) < 3: seen["trades"].append(dict(sym=t.symbol, ts=t.timestamp, receipt=receipt, delay_ms=round((receipt-t.timestamp)*1000, 1) if t.timestamp else None, fields=[a for a in dir(t) if not a.startswith("_")][:14]))
        seen["n"] = seen.get("n", 0) + 1
    async def book(b, receipt): seen["book"] += 1
    fh = FeedHandler(config={"log": {"disabled": True}})
    fh.add_feed(Kraken(symbols=["BTC-USD"], channels=[TRADES, L2_BOOK], callbacks={TRADES: trade, L2_BOOK: book}))
    import threading, signal
    def stop(): 
        time.sleep(15); import os; os.kill(os.getpid(), signal.SIGINT)
    threading.Thread(target=stop, daemon=True).start()
    try: fh.run(install_signal_handlers=False)
    except BaseException as e: res["stopped_by"] = type(e).__name__
    res.update(n_trades=seen.get("n", 0), n_book_updates=seen["book"], sample=seen["trades"][:2])
elif which == "yfinance":
    import yfinance as yf, pandas as pd
    for sym, kw in [("BTC-USD", dict(period="1d", interval="1m")), ("SPY", dict(period="5d", interval="1d"))]:
        try:
            t = time.perf_counter(); d = yf.download(sym, progress=False, auto_adjust=False, **kw); res[sym] = dict(rows=len(d), seconds=round(time.perf_counter()-t, 2), cols=[str(c) for c in d.columns][:8], last=str(d.index[-1]) if len(d) else None)
        except Exception as e: res[sym] = dict(error=f"{type(e).__name__}: {str(e)[:150]}")
print(json.dumps(res, default=str))
