"""Public-data live capture (OKX, Coinbase, Kraken). No credentials, no private code.
Polls REST L2 books (top-N) + recent trades; records local receive time and request RTT.
Usage: python live_capture.py <duration_s> <outdir>
"""
import sys, time, json, threading, gzip, os, requests

DUR = float(sys.argv[1]); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
T_END = time.time() + DUR
S = requests.Session()
NLEV = int(os.environ.get("NLEV", "25"))
LOCK = threading.Lock()
FILES = {}
def w(name, rec):
    with LOCK:
        f = FILES.get(name)
        if f is None:
            f = FILES[name] = gzip.open(os.path.join(OUT, name + ".jsonl.gz"), "at")
        f.write(json.dumps(rec, separators=(",", ":")) + "\n")

def get(url, params=None):
    t0 = time.time()
    try:
        r = S.get(url, params=params, timeout=8)
        t1 = time.time()
        return t0, t1, r.status_code, r.json() if r.status_code == 200 else None
    except Exception as e:
        return t0, time.time(), -1, None

def okx_loop(insts, swaps):
    seen = {}
    last_slow = 0
    while time.time() < T_END:
        c0 = time.time()
        for inst in insts + swaps:
            t0, t1, sc, j = get("https://www.okx.com/api/v5/market/books", {"instId": inst, "sz": NLEV})
            if j and j.get("data"):
                d = j["data"][0]
                w("okx_book_" + inst, {"t0": t0, "t1": t1, "ts": int(d["ts"]),
                    "b": [[x[0], x[1]] for x in d["bids"]], "a": [[x[0], x[1]] for x in d["asks"]]})
        if c0 - last_slow >= 3:
            last_slow = c0
            for inst in insts + swaps:
                t0, t1, sc, j = get("https://www.okx.com/api/v5/market/trades", {"instId": inst, "limit": 100})
                if j and j.get("data"):
                    for x in j["data"]:
                        k = (inst, x["tradeId"])
                        if k in seen: continue
                        seen[k] = 1
                        w("okx_trades_" + inst, {"t1": t1, "id": x["tradeId"], "ts": int(x["ts"]), "px": x["px"], "sz": x["sz"], "side": x["side"]})
        if c0 % 60 < 3:
            for inst in swaps:
                t0, t1, sc, j = get("https://www.okx.com/api/v5/public/funding-rate", {"instId": inst})
                if j: w("okx_funding_" + inst, {"t1": t1, "d": j["data"]})
                t0, t1, sc, j = get("https://www.okx.com/api/v5/public/mark-price", {"instType": "SWAP", "instId": inst})
                if j: w("okx_mark_" + inst, {"t1": t1, "d": j["data"]})
        time.sleep(max(0, 2.0 - (time.time() - c0)))

def cb_loop(prods):
    seen = set(); last_slow = 0
    while time.time() < T_END:
        c0 = time.time()
        for p in prods:
            t0, t1, sc, j = get(f"https://api.exchange.coinbase.com/products/{p}/book", {"level": 2})
            if j:
                w("cb_book_" + p, {"t0": t0, "t1": t1, "b": [[x[0], x[1]] for x in j["bids"][:NLEV]], "a": [[x[0], x[1]] for x in j["asks"][:NLEV]]})
            t0, t1, sc, j = get(f"https://api.exchange.coinbase.com/products/{p}/ticker")
            if j: w("cb_ticker_" + p, {"t0": t0, "t1": t1, "d": j})
        if c0 - last_slow >= 3:
            last_slow = c0
            for p in prods:
                t0, t1, sc, j = get(f"https://api.exchange.coinbase.com/products/{p}/trades", {"limit": 100})
                if j:
                    for x in j:
                        k = (p, x["trade_id"])
                        if k in seen: continue
                        seen.add(k)
                        w("cb_trades_" + p, {"t1": t1, **x})
        time.sleep(max(0, 2.0 - (time.time() - c0)))

def kr_loop(pairs):
    since = {}
    last_slow = 0
    while time.time() < T_END:
        c0 = time.time()
        for p in pairs:
            t0, t1, sc, j = get("https://api.kraken.com/0/public/Depth", {"pair": p, "count": NLEV})
            if j and j.get("result"):
                d = list(j["result"].values())[0]
                w("kr_book_" + p, {"t0": t0, "t1": t1, "b": [[x[0], x[1], x[2]] for x in d["bids"]], "a": [[x[0], x[1], x[2]] for x in d["asks"]]})
        if c0 - last_slow >= 4:
            last_slow = c0
            for p in pairs:
                prm = {"pair": p}
                if p in since: prm["since"] = since[p]
                t0, t1, sc, j = get("https://api.kraken.com/0/public/Trades", prm)
                if j and j.get("result"):
                    since[p] = j["result"]["last"]
                    for k, v in j["result"].items():
                        if k == "last": continue
                        for x in v: w("kr_trades_" + p, {"t1": t1, "px": x[0], "sz": x[1], "ts": x[2], "side": x[3], "ot": x[4], "id": x[6]})
        time.sleep(max(0, 2.0 - (time.time() - c0)))

ths = [threading.Thread(target=okx_loop, args=(["BTC-USDT", "ETH-USDT", "SOL-USDT"], ["BTC-USDT-SWAP", "ETH-USDT-SWAP"])),
       threading.Thread(target=cb_loop, args=(["BTC-USD", "ETH-USD", "SOL-USD"],)),
       threading.Thread(target=kr_loop, args=(["XBTUSD", "ETHUSD", "SOLUSD"],))]
for t in ths: t.start()
for t in ths: t.join()
for f in FILES.values(): f.close()
print("done", time.time())
