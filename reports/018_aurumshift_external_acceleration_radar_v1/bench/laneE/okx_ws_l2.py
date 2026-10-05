"""Lane E — L2 WS : ccxt.pro (inclus dans le paquet ccxt MIT) sur OKX pendant ~DUR s.
- watchOrderBook (canal 'books', 400 niveaux) BTC/USDT spot + BTC/USDT:USDT swap,
  watchTrades, watchBidsAsks (bbo-tbt) ;
- hook sur handle_order_book : on capture le message brut + horodatage de réception local,
  on maintient un carnet de RÉFÉRENCE en chaînes, on vérifie le checksum CRC32 OKX
  (25 niveaux entrelacés bid:sz:ask:sz, signé 32 bits) et on compare le top-25 du carnet ccxt ;
- coupure forcée du websocket à mi-parcours pour observer la reconnexion.
Usage : python okx_ws_l2.py [DUR] > okx_ws_l2.json"""
import asyncio, json, os, sys, time, zlib, statistics as st
import ccxt.pro as pro

CA = os.environ.get("SSL_CERT_FILE", "/root/.ccr/ca-bundle.crt")
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 30
SYMS = ["BTC/USDT", "BTC/USDT:USDT"]
now_ms = lambda: time.time_ns() / 1e6


def crc(bids, asks):
    parts = []
    for i in range(25):
        if i < len(bids): parts += [bids[i][0], bids[i][1]]
        if i < len(asks): parts += [asks[i][0], asks[i][1]]
    v = zlib.crc32(":".join(parts).encode()) & 0xFFFFFFFF
    return v - (1 << 32) if v >= (1 << 31) else v


class RefBook:
    def __init__(self): self.b, self.a = {}, {}
    def apply(self, side, levels):
        for lv in levels:
            px, sz = lv[0], lv[1]
            if float(sz) == 0: side.pop(px, None)
            else: side[px] = sz
    def top(self, n=25):
        b = sorted(self.b.items(), key=lambda x: -float(x[0]))[:n]
        a = sorted(self.a.items(), key=lambda x: float(x[0]))[:n]
        return b, a


STATS = {"ob_msgs": {}, "crc_ok": {}, "crc_fail": {}, "crc_missing": {}, "ccxt_vs_ref_top25_equal": {}, "ccxt_vs_ref_checked": {},
         "ob_lag_ms": {}, "snapshots": {}, "seq_gap": {}}
REFS = {}


class OKX(pro.okx):
    def handle_order_book(self, client, message):
        recv = now_ms()
        arg = message.get("arg", {}); inst = arg.get("instId"); action = message.get("action")
        res = super().handle_order_book(client, message)
        if arg.get("channel") == "books":
            for d in message.get("data", []):
                k = inst
                for dct in STATS.values(): dct.setdefault(k, 0 if dct is not STATS["ob_lag_ms"] else [])
                STATS["ob_msgs"][k] += 1
                if action == "snapshot":
                    REFS[k] = RefBook(); STATS["snapshots"][k] += 1
                ref = REFS.get(k)
                if ref is None: continue
                ref.apply(ref.b, d.get("bids", [])); ref.apply(ref.a, d.get("asks", []))
                tb, ta = ref.top()
                if "checksum" in d and int(d["checksum"]) == 0:
                    STATS.setdefault("crc_zero", {}).setdefault(k, 0); STATS["crc_zero"][k] += 1
                elif "checksum" in d:
                    if crc(tb, ta) == int(d["checksum"]): STATS["crc_ok"][k] += 1
                    else: STATS["crc_fail"][k] += 1
                else: STATS["crc_missing"][k] += 1
                sq, psq = d.get("seqId"), d.get("prevSeqId")
                if action != "snapshot" and getattr(ref, "last_seq", None) is not None and psq != ref.last_seq: STATS["seq_gap"][k] += 1
                ref.last_seq = sq
                STATS["ob_lag_ms"][k].append(recv - int(d["ts"]))
                # carnet ccxt (floats) vs référence (chaînes) sur 25 niveaux
                sym = self.safe_symbol(inst)
                ob = self.orderbooks.get(sym)
                if ob is not None:
                    cb = [(float(p), float(s)) for p, s, *_ in ob["bids"][:25]]
                    ca = [(float(p), float(s)) for p, s, *_ in ob["asks"][:25]]
                    rb = [(float(p), float(s)) for p, s in tb]; ra = [(float(p), float(s)) for p, s in ta]
                    STATS["ccxt_vs_ref_checked"][k] += 1
                    STATS["ccxt_vs_ref_top25_equal"][k] += int(cb == rb and ca == ra)
        return res


def pct(xs, q):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None


async def loop_watch(ex, fn, sym, sink, deadline, errs):
    while time.time() < deadline:
        try:
            r = await getattr(ex, fn)(sym)
            sink.append((now_ms(), r))
        except (Exception, asyncio.CancelledError) as e:  # client.close() annule les futures en attente
            errs.append({"fn": fn, "sym": sym, "t": now_ms(), "err": f"{type(e).__name__}: {str(e)[:160]}"})
            await asyncio.sleep(0.5)


async def main():
    ex = OKX({"aiohttp_trust_env": True, "cafile": CA})
    # l'egress du sandbox coupe le port 8443 (cf. LAB_PRIOR 005 ws_okx_retry.json) : on force le port 443
    ex.urls["api"]["ws"] = "wss://ws.okx.com/ws/v5"
    await ex.load_markets()
    deadline = time.time() + DUR
    errs, sinks = [], {}
    tasks = []
    for s in SYMS:
        for fn in ("watch_order_book", "watch_trades", "watch_bids_asks"):
            sinks[(fn, s)] = []
            arg = [s] if fn == "watch_bids_asks" else s
            tasks.append(asyncio.create_task(loop_watch(ex, fn, arg, sinks[(fn, s)], deadline, errs)))
    # coupure forcée à mi-parcours
    await asyncio.sleep(DUR / 2)
    kill_t = now_ms(); closed = []
    for url, client in list(ex.clients.items()):
        try:
            await client.close(); closed.append(url)
        except Exception as e:
            closed.append(f"{url}: {e}")
    await asyncio.gather(*tasks)
    out = {"ccxt_version": pro.__version__ if hasattr(pro, "__version__") else None, "duration_s": DUR,
           "forced_close_at_ms": kill_t, "closed_clients": closed, "errors": errs[:20], "n_errors": len(errs)}
    per = {}
    for (fn, s), v in sinks.items():
        d = {"updates": len(v)}
        after = [t for t, _ in v if t > kill_t]
        d["first_update_after_kill_ms"] = round(min(after) - kill_t) if after else None
        if fn == "watch_trades" and v:
            trs = [tr for _, batch in v for tr in batch]
            ids = [tr["id"] for tr in trs]
            d["trades_total"] = len(trs); d["dup_ids_in_cache_views"] = len(ids) - len(set(ids))
            d["receipt_stamp_in_trade"] = any(k in trs[0] for k in ("receipt", "localTimestamp"))
            lag = [t - batch[-1]["timestamp"] for t, batch in v if batch]
            d["lag_ms_p50"] = round(st.median(lag), 1); d["lag_ms_p95"] = round(pct(lag, .95), 1)
        if fn == "watch_bids_asks" and v:
            ts = [list(r.values())[0] for _, r in v]
            d["sample_keys"] = sorted(k for k in ts[0].keys() if k != "info")
            d["timestamp_none_count"] = sum(1 for x in ts if x.get("timestamp") is None)
            lag = [t - list(r.values())[0]["timestamp"] for t, r in v if list(r.values())[0].get("timestamp")]
            d["lag_ms_p50"] = round(st.median(lag), 1) if lag else None
        if fn == "watch_order_book" and v:
            d["nonce_present"] = v[-1][1].get("nonce") is not None
            d["ts_present"] = v[-1][1].get("timestamp") is not None
        per[f"{fn}:{s}"] = d
    out["per_stream"] = per
    lag = STATS.pop("ob_lag_ms")
    out["orderbook_hook"] = STATS
    out["orderbook_lag_ms"] = {k: {"p50": round(st.median(x), 1), "p95": round(pct(x, .95), 1), "min": round(min(x), 1)} for k, x in lag.items() if x}
    await ex.close()
    print(json.dumps(out, indent=1, default=str))

asyncio.run(main())
