#!/usr/bin/env python3
"""laneCD — recoupement funding : Tardis derivative_ticker (échantillon gratuit) vs sources officielles.

- OKX : /api/v5/public/funding-rate-history (≈ 3 mois glissants, public, sans clé).
- Binance USDⓈ-M : data.binance.vision monthly fundingRate (fapi direct = 451 depuis ce sandbox).
Usage : python funding_crosscheck.py DATA_DIR OUT_JSON   (télécharge ce qui manque, volumes < 5 Mo)
"""
import csv, io, json, sys, urllib.request, zipfile
from pathlib import Path
import polars as pl

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def tardis_settled(path):
    df = pl.read_csv(path).filter(pl.col("funding_timestamp").is_not_null() & pl.col("funding_rate").is_not_null())
    s = (df.sort("local_timestamp").filter(pl.col("timestamp") < pl.col("funding_timestamp"))
         .group_by("funding_timestamp").agg(pl.col("funding_rate").last()).sort("funding_timestamp"))
    return {int(t // 1000): float(r) for t, r in s.iter_rows()}

def main():
    data, outp = Path(sys.argv[1]), Path(sys.argv[2])
    out = {}
    # OKX, 2026-10-01
    for inst in ["BTC-USDT-SWAP", "DOGE-USDT-SWAP"]:
        td = tardis_settled(data / f"okex-swap_derivative_ticker_2026-10-01_{inst}.csv.gz")
        api = json.loads(get(f"https://www.okx.com/api/v5/public/funding-rate-history?instId={inst}&limit=100"))["data"]
        apim = {int(r["fundingTime"]): float(r["realizedRate"] or r["fundingRate"]) for r in api}
        rows = [{"funding_time_ms": t, "tardis_last_before": v, "okx_api_realized": apim.get(t),
                 "abs_diff": (abs(v - apim[t]) if t in apim else None)} for t, v in td.items()]
        out[f"okex-swap:{inst}:2026-10-01"] = rows
    # Binance, 2026-09-01 (Vision mensuel disponible pour septembre)
    for sym in ["BTCUSDT", "DOGEUSDT"]:
        p = data / f"binance-futures_derivative_ticker_2026-09-01_{sym}.csv.gz"
        if not p.exists():
            p.write_bytes(get(f"https://datasets.tardis.dev/v1/binance-futures/derivative_ticker/2026/09/01/{sym}.csv.gz"))
        td = tardis_settled(p)
        z = zipfile.ZipFile(io.BytesIO(get(
            f"https://data.binance.vision/data/futures/um/monthly/fundingRate/{sym}/{sym}-fundingRate-2026-09.zip")))
        rd = list(csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode())))
        vm = {}
        for r in rd:
            t = int(r["calc_time"])
            vm[t] = float(r["last_funding_rate"])
        rows = []
        for t, v in td.items():
            # calc_time Vision peut différer de quelques ms de l'échéance théorique
            near = [k for k in vm if abs(k - t) < 60_000]
            vv = vm[near[0]] if near else None
            rows.append({"funding_time_ms": t, "tardis_last_before": v, "vision_last_funding_rate": vv,
                         "vision_calc_time_ms": near[0] if near else None,
                         "abs_diff": (abs(v - vv) if vv is not None else None)})
        out[f"binance-futures:{sym}:2026-09-01"] = rows
    outp.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(json.dumps(out, indent=1, sort_keys=True))

if __name__ == "__main__":
    main()
