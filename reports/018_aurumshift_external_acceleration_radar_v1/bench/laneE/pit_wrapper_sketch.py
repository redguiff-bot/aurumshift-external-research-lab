"""Lane E — esquisse de la couche RÉSIDUELLE custom au-dessus de ccxt (ce que la réutilisation ne supprime pas).
Enveloppe d'observation PIT : provenance, exchange_ts, receipt_ts (send/recv), hash du brut, version lib ;
drop de la barre en formation ; restauration du ts funding OKX depuis info ; OI normalisé en base ; détection de trous.
Ce n'est PAS du code AurumShift ; sert à mesurer la taille du résiduel (wc -l) et à l'exécuter une fois sur OKX."""
import asyncio, hashlib, json, time
import ccxt.async_support as ccxt

TF_MS = {"1m": 60_000, "5m": 300_000}


def envelope(venue, method, symbol, payload, t_send, t_recv, exchange_ts, lib):
    raw = json.dumps(payload.get("info") if isinstance(payload, dict) else payload, sort_keys=True, default=str)
    return {"venue": venue, "method": method, "symbol": symbol, "exchange_ts": exchange_ts,
            "receipt_send_ms": t_send, "receipt_recv_ms": t_recv, "lib": lib,
            "raw_sha256": hashlib.sha256(raw.encode()).hexdigest()[:16], "payload": payload}


async def call(ex, method, *a, **k):
    t0 = int(time.time() * 1000); r = await getattr(ex, method)(*a, **k); return r, t0, int(time.time() * 1000)


def closed_bars(bars, tf, recv_ms):
    """garde uniquement les barres dont la fin <= instant de réception (aucun flag 'confirm' exposé par ccxt)."""
    return [b for b in bars if b[0] + TF_MS[tf] <= recv_ms]


def gaps(bars, tf):
    return [(a[0], b[0]) for a, b in zip(bars, bars[1:]) if b[0] - a[0] != TF_MS[tf]]


def funding_ts(ex, fr):
    if fr.get("timestamp") is None and ex.id == "okx":  # ccxt 4.5.85 met None ; le ts natif est dans info
        return int(fr["info"]["ts"])
    return fr.get("timestamp")


def oi_base(ex, sym, oi):
    cs = ex.market(sym).get("contractSize") or 1
    return oi["openInterestAmount"] * cs if oi.get("openInterestAmount") is not None else None


async def main():
    ex = ccxt.okx({"aiohttp_trust_env": True, "cafile": "/root/.ccr/ca-bundle.crt"}); await ex.load_markets()
    lib = f"ccxt {ccxt.__version__}"; sym = "BTC/USDT:USDT"; out = []
    bars, s, r = await call(ex, "fetch_ohlcv", sym, "1m", limit=30)
    cb = closed_bars(bars, "1m", r)
    out.append(envelope("okx", "fetch_ohlcv", sym, {"n_raw": len(bars), "n_closed": len(cb), "gaps": gaps(cb, "1m")}, s, r, cb[-1][0] if cb else None, lib))
    fr, s, r = await call(ex, "fetch_funding_rate", sym)
    out.append(envelope("okx", "fetch_funding_rate", sym, fr, s, r, funding_ts(ex, fr), lib))
    oi, s, r = await call(ex, "fetch_open_interest", sym)
    out.append(envelope("okx", "fetch_open_interest", sym, {"oi_contracts": oi["openInterestAmount"], "oi_base": oi_base(ex, sym, oi), "info": oi["info"]}, s, r, oi["timestamp"], lib))
    await ex.close()
    for o in out:
        o["payload"] = {k: v for k, v in (o["payload"].items() if isinstance(o["payload"], dict) else []) if k in ("n_raw", "n_closed", "gaps", "fundingRate", "oi_contracts", "oi_base")}
    print(json.dumps(out, indent=1))

if __name__ == "__main__":
    asyncio.run(main())
