"""Lane E — L3 différentiel « même trade, trois chemins » sur OKX BTC-USDT-SWAP et BTC-USDT :
(1) tardis-machine live (ws-stream-normalized, local) ; (2) ccxt.fetch_trades ; (3) REST natif OKX /market/trades.
Jointure sur trade id ; compare prix, quantité (unités !), côté, timestamp exchange ; mesure localTimestamp - timestamp.
Pré-requis : tardis-machine lancé sur localhost:8073 (npx tardis-machine --port=8072).
Usage : python trade_id_differential.py > trade_id_differential.json"""
import asyncio, json, time, urllib.parse, os, ssl, aiohttp, websockets
import ccxt.async_support as ccxt
CA = "/root/.ccr/ca-bundle.crt"
INST = {"BTC-USDT-SWAP": ("okex-swap", "BTC/USDT:USDT"), "BTC-USDT": ("okex", "BTC/USDT")}


async def tardis(dur=12):
    opts = [{"exchange": ex, "symbols": [i], "dataTypes": ["trade"]} for i, (ex, _) in INST.items()]
    url = "ws://localhost:8073/ws-stream-normalized?options=" + urllib.parse.quote(json.dumps(opts))
    got = {}
    async with websockets.connect(url) as ws:
        t0 = time.time()
        while time.time() - t0 < dur:
            try: m = json.loads(await asyncio.wait_for(ws.recv(), 3))
            except asyncio.TimeoutError: continue
            got[(m["symbol"], m["id"])] = m
    return got


async def main():
    tm = await tardis()
    ex = ccxt.okx({"aiohttp_trust_env": True, "cafile": CA}); await ex.load_markets()
    out = {"tardis_trades": len(tm), "per_symbol": {}}
    async with aiohttp.ClientSession(trust_env=True, connector=aiohttp.TCPConnector(ssl=ssl.create_default_context(cafile=CA))) as s:
        for inst, (_, sym) in INST.items():
            async with s.get(f"https://www.okx.com/api/v5/market/trades?instId={inst}&limit=500") as r:
                nat = {d["tradeId"]: d for d in (await r.json())["data"]}
            cc = {t["id"]: t for t in await ex.fetch_trades(sym, limit=500)}
            ids = [k[1] for k in tm if k[0] == inst and k[1] in nat and k[1] in cc]
            res = {"joined": len(ids), "price_eq": 0, "ts_eq_native": 0, "ts_eq_ccxt": 0, "side_eq": 0,
                   "amount_tardis_eq_native_sz": 0, "amount_ccxt_eq_native_sz": 0, "amount_tardis_eq_ccxt": 0, "receipt_minus_exchange_ms": []}
            for i in ids:
                t, n, c = tm[(inst, i)], nat[i], cc[i]
                tts = int(round(__import__("datetime").datetime.fromisoformat(t["timestamp"].replace("Z", "+00:00")).timestamp() * 1000))
                lts = __import__("datetime").datetime.fromisoformat(t["localTimestamp"].replace("Z", "+00:00")).timestamp() * 1000
                res["price_eq"] += t["price"] == float(n["px"]) == c["price"]
                res["ts_eq_native"] += tts == int(n["ts"]); res["ts_eq_ccxt"] += tts == c["timestamp"]
                res["side_eq"] += t["side"] == n["side"] == c["side"]
                res["amount_tardis_eq_native_sz"] += abs(t["amount"] - float(n["sz"])) < 1e-12
                res["amount_ccxt_eq_native_sz"] += abs(c["amount"] - float(n["sz"])) < 1e-12
                res["amount_tardis_eq_ccxt"] += abs(t["amount"] - c["amount"]) < 1e-12
                res["receipt_minus_exchange_ms"].append(round(lts - tts, 1))
            if ids:
                ex_ = tm[(inst, ids[0])]; res["example"] = {"tardis": ex_, "native": nat[ids[0]], "ccxt_amount": cc[ids[0]]["amount"], "contractSize": ex.market(sym).get("contractSize")}
            r = sorted(res.pop("receipt_minus_exchange_ms")); res["receipt_lag_ms_p50"] = r[len(r)//2] if r else None
            out["per_symbol"][inst] = res
    await ex.close()
    print(json.dumps(out, indent=1))

asyncio.run(main())
