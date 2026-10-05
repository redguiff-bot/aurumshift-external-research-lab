"""Lane E — L2 REST : ccxt (unifié) vs appel natif OKX v5, BTC/DOGE spot + swap.
Pour chaque méthode : latence, champs PIT (timestamp exchange / None), fidélité parse vs `info` brut,
et comparaison avec un appel natif OKX brut fait juste après (aiohttp direct).
Usage : python okx_rest_l2.py > okx_rest_l2.json   (volumes modestes : ~40 requêtes publiques)."""
import asyncio, json, time, os, aiohttp, ssl
import ccxt.async_support as ccxt

CA = os.environ.get("SSL_CERT_FILE", "/root/.ccr/ca-bundle.crt")
BASE = "https://www.okx.com"
SPOT = ["BTC/USDT", "DOGE/USDT"]
SWAP = ["BTC/USDT:USDT", "DOGE/USDT:USDT"]
now_ms = lambda: int(time.time() * 1000)


async def native(sess, path):
    t0 = time.perf_counter()
    async with sess.get(BASE + path) as r:
        j = await r.json()
    return j, round((time.perf_counter() - t0) * 1000, 1), now_ms()


async def timed(coro):
    t_send = now_ms(); t0 = time.perf_counter()
    try:
        res = await coro
        err = None
    except Exception as e:  # on note l'échec, pas de conclusion négative
        res, err = None, f"{type(e).__name__}: {str(e)[:200]}"
    return res, round((time.perf_counter() - t0) * 1000, 1), t_send, now_ms(), err


def pit(obj):
    """Extrait les champs temporels unifiés et signale l'absence."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: obj.get(k) for k in ("timestamp", "datetime", "fundingTimestamp", "nextFundingTimestamp", "nonce") if k in obj}
    return None


async def main():
    ex = ccxt.okx({"aiohttp_trust_env": True, "cafile": CA, "enableRateLimit": True})
    sslctx = ssl.create_default_context(cafile=CA)
    out = {"ccxt_version": ccxt.__version__, "venue": "okx", "run_utc_ms": now_ms(), "tests": []}
    async with aiohttp.ClientSession(trust_env=True, connector=aiohttp.TCPConnector(ssl=sslctx)) as s:
        t0 = time.perf_counter(); await ex.load_markets(); out["load_markets_ms"] = round((time.perf_counter() - t0) * 1000)
        # horloge : fetchTime vs local
        r, lat, ts, tr, err = await timed(ex.fetch_time())
        out["clock"] = {"exchange_ms": r, "local_send": ts, "local_recv": tr, "offset_ms_mid": (r - (ts + tr) / 2) if r else None, "rtt_ms": lat}

        for sym in SPOT + SWAP:
            m = ex.market(sym); inst = m["id"]
            rec = {"symbol": sym, "instId": inst, "type": m["type"], "contractSize": m.get("contractSize")}
            # --- ticker / BBO
            t, lat, *_ , err = await timed(ex.fetch_ticker(sym))
            nj, nlat, _ = await native(s, f"/api/v5/market/ticker?instId={inst}")
            raw = t["info"] if t else {}
            rec["ticker"] = {"lat_ms": lat, "native_lat_ms": nlat, "err": err, "pit": pit(t),
                             "bid": t and t["bid"], "ask": t and t["ask"], "bidVolume": t and t["bidVolume"],
                             "parse_fidelity": bool(t) and t["bid"] == float(raw["bidPx"]) and t["ask"] == float(raw["askPx"]) and t["timestamp"] == int(raw["ts"]),
                             "info_keys_equal_native_keys": bool(t) and sorted(raw.keys()) == sorted(nj["data"][0].keys()),
                             "native_ts_minus_ccxt_ts_ms": int(nj["data"][0]["ts"]) - (t["timestamp"] if t else 0),
                             "native_bid_minus_ccxt_bid": float(nj["data"][0]["bidPx"]) - (t["bid"] if t else 0),
                             "receipt_ts_in_ccxt_obj": any(k in (t or {}) for k in ("receipt", "localTimestamp", "receiptTimestamp"))}
            # --- carnet
            ob, lat, *_ , err = await timed(ex.fetch_order_book(sym, 20))
            nj, nlat, _ = await native(s, f"/api/v5/market/books?instId={inst}&sz=20")
            rec["orderbook"] = {"lat_ms": lat, "native_lat_ms": nlat, "err": err, "pit": pit(ob), "levels": ob and (len(ob["bids"]), len(ob["asks"])),
                                "level_width": ob and len(ob["bids"][0]),
                                "native_level_fields": len(nj["data"][0]["bids"][0]),
                                "native_has_seqId": "seqId" in nj["data"][0], "native_ts": nj["data"][0]["ts"]}
            # --- barres (barre en formation ?)
            bars, lat, ts_send, _, err = await timed(ex.fetch_ohlcv(sym, "1m", limit=5))
            nj, nlat, _ = await native(s, f"/api/v5/market/candles?instId={inst}&bar=1m&limit=5")
            last_native = nj["data"][0]  # OKX : plus récent en premier, champ confirm en dernier
            rec["ohlcv"] = {"lat_ms": lat, "native_lat_ms": nlat, "err": err, "row_width_ccxt": bars and len(bars[-1]),
                            "row_width_native": len(last_native), "native_last_confirm": last_native[-1],
                            "ccxt_last_bar_open_ts": bars and bars[-1][0], "ccxt_last_bar_age_ms": bars and ts_send - bars[-1][0],
                            "ccxt_last_bar_is_forming": bars and (ts_send - bars[-1][0]) < 60000,
                            "ccxt_exposes_confirm": False if bars and len(bars[-1]) == 6 else None,
                            "same_ts_as_native": bars and bars[-1][0] == int(last_native[0])}
            # --- trades
            tr, lat, *_ , err = await timed(ex.fetch_trades(sym, limit=50))
            rec["trades"] = {"lat_ms": lat, "err": err, "n": tr and len(tr), "pit_first": tr and pit(tr[0]),
                             "unified_keys": tr and sorted(k for k in tr[0].keys() if k != "info"),
                             "info_kept": tr and "info" in tr[0], "has_id": tr and tr[0]["id"] is not None}
            if m["swap"]:
                fr, lat, *_ , err = await timed(ex.fetch_funding_rate(sym))
                nj, nlat, _ = await native(s, f"/api/v5/public/funding-rate?instId={inst}")
                rec["funding"] = {"lat_ms": lat, "err": err, "pit": pit(fr), "fundingRate": fr and fr["fundingRate"],
                                  "native_fundingRate": float(nj["data"][0]["fundingRate"]),
                                  "native_keys": sorted(nj["data"][0].keys()),
                                  "ccxt_timestamp_is_None": fr is not None and fr.get("timestamp") is None,
                                  "interval": fr and fr.get("interval"), "markPrice": fr and fr.get("markPrice"), "indexPrice": fr and fr.get("indexPrice")}
                fh, lat, *_ , err = await timed(ex.fetch_funding_rate_history(sym, limit=10))
                rec["funding_history"] = {"lat_ms": lat, "err": err, "n": fh and len(fh), "pit_last": fh and pit(fh[-1]),
                                          "step_ms": fh and len(fh) > 1 and fh[-1]["timestamp"] - fh[-2]["timestamp"],
                                          "realized_in_info": fh and "realizedRate" in fh[-1]["info"]}
                oi, lat, *_ , err = await timed(ex.fetch_open_interest(sym))
                nj, nlat, _ = await native(s, f"/api/v5/public/open-interest?instType=SWAP&instId={inst}")
                rec["open_interest"] = {"lat_ms": lat, "err": err, "pit": pit(oi),
                                        "openInterestAmount": oi and oi.get("openInterestAmount"), "openInterestValue": oi and oi.get("openInterestValue"),
                                        "baseVolume": oi and oi.get("baseVolume"), "native": nj["data"][0]}
                oih, lat, *_ , err = await timed(ex.fetch_open_interest_history(sym, "5m", limit=10))
                rec["open_interest_history"] = {"lat_ms": lat, "err": err, "n": oih and len(oih), "pit_last": oih and pit(oih[-1]),
                                                "last": oih and {k: oih[-1].get(k) for k in ("openInterestAmount", "openInterestValue", "baseVolume", "quoteVolume")},
                                                "info_last": oih and oih[-1]["info"]}
                mp, lat, *_ , err = await timed(ex.fetch_mark_price(sym))
                rec["mark_price"] = {"lat_ms": lat, "err": err, "pit": pit(mp), "markPrice": mp and mp.get("markPrice"), "indexPrice": mp and mp.get("indexPrice")}
                ix, lat, *_ , err = await timed(ex.fetch_index_ohlcv(sym, "1m", limit=3))
                rec["index_ohlcv"] = {"lat_ms": lat, "err": err, "last": ix and ix[-1]}
                lq, lat, *_ , err = await timed(ex.fetch_liquidations(sym))
                nj, nlat, _ = await native(s, f"/api/v5/public/liquidation-orders?instType=SWAP&uly={m['base']}-USDT&state=filled&limit=5")
                rec["liquidations"] = {"ccxt_err": err, "native_code": nj.get("code"), "native_n": len(nj.get("data", [])),
                                       "native_first_details_n": len(nj["data"][0]["details"]) if nj.get("data") else None,
                                       "native_detail_keys": sorted(nj["data"][0]["details"][0].keys()) if nj.get("data") and nj["data"][0]["details"] else None}
            out["tests"].append(rec)
        # basis BTC : perp mark vs index vs spot mid (snapshot)
        t_sp = await ex.fetch_ticker("BTC/USDT"); mp = await ex.fetch_mark_price("BTC/USDT:USDT")
        out["basis_snapshot"] = {"spot_mid": (t_sp["bid"] + t_sp["ask"]) / 2, "perp_mark": mp["markPrice"], "index": mp["indexPrice"],
                                 "mark_minus_index_bps": (mp["markPrice"] / mp["indexPrice"] - 1) * 1e4 if mp["indexPrice"] else None,
                                 "ts_spot": t_sp["timestamp"], "ts_mark": mp["timestamp"]}
    await ex.close()
    print(json.dumps(out, indent=1, default=str))

asyncio.run(main())
