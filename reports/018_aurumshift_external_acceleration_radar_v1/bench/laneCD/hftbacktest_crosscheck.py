#!/usr/bin/env python3
"""laneCD — hftbacktest 2.4.4 comme second oracle (L3) : convertisseur Tardis + ordres MARKET BUY.

1. Convertit binance spot DOGEUSDT 2026-10-01 (trades + incremental_book_L2, gratuits) via
   hftbacktest.data.utils.tardis.convert -> carnet L2 COMPLET (pas limité à 25 niveaux).
2. Rejoue avec HashMapMarketDepthBacktest, latence d'ordre 0, frais 0, et envoie un MARKET BUY de
   notional N toutes les 5 min (après 1 h de chauffe) sous PartialFillExchange et NoPartialFillExchange.
3. Compare le VWAP réalisé par le moteur (delta de balance / qty) à notre walk-the-book calculé
   (a) sur le carnet complet de hftbacktest au même instant, (b) sur book_snapshot_25 Tardis (as-of local_ts).
Usage : python hftbacktest_crosscheck.py DATA_DIR WORK_DIR OUT_JSON [DOGEUSDT|BTCUSDT]
"""
import hashlib, json, sys, time
from pathlib import Path
import numpy as np
import polars as pl
from hftbacktest import BacktestAsset, HashMapMarketDepthBacktest
from hftbacktest.order import MARKET, IOC
from hftbacktest.data.utils import tardis

NOTIONALS = [100, 1_000, 10_000, 100_000, 1_000_000]
SYM = sys.argv[4] if len(sys.argv) > 4 else "DOGEUSDT"
TICK, LOT = {"DOGEUSDT": (0.00001, 1.0), "BTCUSDT": (0.01, 0.00001)}[SYM]
NS = 1_000_000_000


def convert(data, work):
    out = work / f"binance_{SYM}_20261001.npz"
    t0 = time.time()
    if not out.exists():
        tardis.convert([str(data / f"binance_trades_2026-10-01_{SYM}.csv.gz"),
                        str(data / f"binance_incremental_book_L2_2026-10-01_{SYM}.csv.gz")],
                       output_filename=str(out), buffer_size=60_000_000)
    return out, time.time() - t0


def walk_depth(depth, notional, max_ticks=200000):
    best = depth.best_ask_tick
    rem, base, cost = notional, 0.0, 0.0
    for t in range(best, best + max_ticks):
        q = depth.ask_qty_at_tick(t)
        if q <= 0:
            continue
        px = t * TICK
        take = min(q, rem / px)
        base += take
        cost += take * px
        rem -= take * px
        if rem <= 1e-9:
            return cost / base, t - best
    return np.nan, max_ticks


def run(npz, exchange_kind):
    asset = (BacktestAsset().data([str(npz)]).linear_asset(1.0).constant_order_latency(0, 0)
             .risk_adverse_queue_model().tick_size(TICK).lot_size(LOT).trading_value_fee_model(0.0, 0.0))
    asset = asset.partial_fill_exchange() if exchange_kind == "partial" else asset.no_partial_fill_exchange()
    hbt = HashMapMarketDepthBacktest([asset])
    hbt.elapse(1 * NS)
    day0 = hbt.current_timestamp // (86400 * NS) * (86400 * NS)
    grid = np.arange(day0 + 3600 * NS, day0 + 86400 * NS - 60 * NS, 300 * NS)
    rows, oid = [], 1
    for t in grid:
        if hbt.elapse(int(t - hbt.current_timestamp)) != 0:
            break
        depth = hbt.depth(0)
        mid = (depth.best_ask + depth.best_bid) / 2.0
        for n in NOTIONALS:
            own_vwap, ticks = walk_depth(depth, n)
            qty = round(n / depth.best_ask / LOT) * LOT
            sv0 = hbt.state_values(0)
            b0, p0 = sv0.balance, sv0.position
            hbt.submit_buy_order(0, oid, depth.best_ask, qty, IOC, MARKET, False)
            hbt.wait_order_response(0, oid, 5 * NS)
            o = hbt.orders(0).get(oid)
            status = int(o.status) if o is not None else -1
            leaves = float(o.leaves_qty) if o is not None else np.nan
            sv1 = hbt.state_values(0)
            dq = sv1.position - p0
            eng_vwap = (b0 - sv1.balance) / dq if dq > 0 else np.nan
            # recalcul de notre walk sur le carnet du moteur avec la même qty (exacte)
            own_vwap_q, _ = walk_depth(depth, qty * depth.best_ask)
            rows.append({"t": int(t), "N": n, "mid": mid, "qty": qty, "filled_qty": dq, "status": status, "order_leaves_qty": leaves,
                         "engine_vwap": eng_vwap, "own_walk_vwap_fulldepth": own_vwap_q, "ticks_walked": ticks})
            hbt.clear_inactive_orders(0)
            oid += 1
    hbt.close()
    return rows


def snap25_walk(data):
    df = pl.read_csv(data / f"binance_book_snapshot_25_2026-10-01_{SYM}.csv.gz")
    lt = df["local_timestamp"].to_numpy() * 1000
    ap = np.stack([df[f"asks[{i}].price"].to_numpy() for i in range(25)], 1)
    aq = np.stack([df[f"asks[{i}].amount"].to_numpy() for i in range(25)], 1)
    return lt, ap, aq


def summarize(rows, snap):
    lt, ap, aq = snap
    out = {}
    for n in NOTIONALS:
        r = [x for x in rows if x["N"] == n]
        mid = np.array([x["mid"] for x in r])
        eng = (np.array([x["engine_vwap"] for x in r]) / mid - 1) * 1e4
        own = (np.array([x["own_walk_vwap_fulldepth"] for x in r]) / mid - 1) * 1e4
        fill_ratio = np.array([x["filled_qty"] / x["qty"] if x["qty"] else np.nan for x in r])
        s25 = []
        for x in r:
            i = np.searchsorted(lt, x["t"], side="right") - 1
            p, a = ap[i], aq[i]
            cum = np.cumsum(p * a)
            if cum[-1] < n:
                s25.append(np.nan)
                continue
            k = np.searchsorted(cum, n)
            base = a[:k].sum() + (n - (cum[k - 1] if k else 0)) / p[k]
            s25.append((n / base / x["mid"] - 1) * 1e4)
        s25 = np.array(s25)
        d = eng - own
        out[str(n)] = {
            "n": len(r),
            "engine_cost_bps_p50_p90": [round(float(np.nanpercentile(eng, 50)), 4), round(float(np.nanpercentile(eng, 90)), 4)] if np.isfinite(eng).any() else None,
            "own_walk_fulldepth_bps_p50_p90": [round(float(np.nanpercentile(own, 50)), 4), round(float(np.nanpercentile(own, 90)), 4)],
            "snap25_walk_bps_p50_p90": ([round(float(np.nanpercentile(s25, 50)), 4), round(float(np.nanpercentile(s25, 90)), 4)] if np.isfinite(s25).any() else None),
            "share_snap25_insufficient": round(float(np.mean(~np.isfinite(s25))), 4),
            "engine_minus_own_bps_maxabs": round(float(np.nanmax(np.abs(d))), 6) if np.isfinite(d).any() else None,
            "fullbook_minus_snap25_bps_maxabs": (round(float(np.nanmax(np.abs(own - s25))), 6) if np.isfinite(own - s25).any() else None),
            "fill_ratio_min": round(float(np.nanmin(fill_ratio)), 6),
            "max_ticks_walked": int(max(x["ticks_walked"] for x in r)),
            "share_status_FILLED": round(float(np.mean([x["status"] == 3 for x in r])), 4),
            "share_status_EXPIRED": round(float(np.mean([x["status"] == 2 for x in r])), 4),
            "share_own_walk_gt_100_ticks": round(float(np.mean([x["ticks_walked"] > 100 for x in r])), 4),
            "share_FILLED_but_local_position_short": round(float(np.mean(
                [x["status"] == 3 and x["filled_qty"] < x["qty"] - 1e-9 for x in r])), 4),
        }
    return out


def main():
    data, work, outp = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    work.mkdir(parents=True, exist_ok=True)
    npz, conv_s = convert(data, work)
    snap = snap25_walk(data)
    res = {"convert_seconds": round(conv_s, 1), "npz_bytes": npz.stat().st_size,
           "npz_sha256": hashlib.sha256(npz.read_bytes()).hexdigest()}
    for kind in ["partial", "nopartial"]:
        t0 = time.time()
        rows = run(npz, kind)
        res[kind] = {"replay_seconds": round(time.time() - t0, 1),
                     "rows_sha256": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
                     "summary": summarize(rows, snap)}
    outp.write_text(json.dumps(res, indent=1, sort_keys=True))
    print(json.dumps(res, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
