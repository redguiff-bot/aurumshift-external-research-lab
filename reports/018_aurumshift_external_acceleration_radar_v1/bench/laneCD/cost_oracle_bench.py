#!/usr/bin/env python3
"""laneCD — L3 bench « oracle de coût indépendant » sur échantillons gratuits Tardis.dev.

Oracle = marche dans le carnet (walk-the-book) sur book_snapshot_25, as-of PIT sur local_timestamp.
Modèles comparés : (a) fixe 5 bps, (b) demi-spread seul, (c) demi-spread + loi racine carrée (Y=1,
sigma et volume journaliers estimés de façon causale sur l'heure glissante précédente).
Markouts : mid à +1 s / +10 s / +60 s (instants échantillonnés + agresseurs acheteurs publics >= 10 kUSDT).
Commissions EXCLUES (ligne séparée du COST_CONTRACT) : coûts en bps vs mid au moment de décision.

Usage : python cost_oracle_bench.py DATA_DIR OUT_JSON
Déterministe : aucune graine aléatoire, grille temporelle fixe ; sortie JSON triée.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

DATE = "2026-10-01"
NOTIONALS = [100, 1_000, 10_000, 100_000, 1_000_000]
HORIZONS_S = [1, 10, 60]
STEP_S = 300
WARMUP_S = 3600
FIXED_BPS = 5.0
Y_SQRT = 1.0
US = 1_000_000

INSTRUMENTS = [
    # (label, exchange-prefix, symbol, kind)
    ("binance_spot_BTCUSDT", "binance", "BTCUSDT", "spot"),
    ("binance_spot_DOGEUSDT", "binance", "DOGEUSDT", "spot"),
    ("okex_spot_BTC-USDT", "okex", "BTC-USDT", "spot"),
    ("okex_spot_DOGE-USDT", "okex", "DOGE-USDT", "spot"),
    ("binancefut_perp_DOGEUSDT", "binance-futures", "DOGEUSDT", "perp"),
]


def q(a, ps=(50, 90, 99)):
    a = np.asarray(a, dtype=float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return None
    out = {f"p{p}": round(float(np.percentile(a, p)), 4) for p in ps}
    out["mean"] = round(float(a.mean()), 4)
    out["n"] = int(a.size)
    return out


def ts_semantics(df):
    ts = df["timestamp"].to_numpy()
    lt = df["local_timestamp"].to_numpy()
    lag_ms = (lt - ts) / 1000.0
    return {
        "rows": int(len(ts)),
        "share_ts_eq_local": round(float(np.mean(ts == lt)), 6),
        "lag_local_minus_exchange_ms": q(lag_ms, (1, 50, 99, 99.9)),
        "n_negative_lag": int(np.sum(lag_ms < 0)),
        "n_local_ts_non_monotonic": int(np.sum(np.diff(lt) < 0)),
        "n_exchange_ts_non_monotonic": int(np.sum(np.diff(ts) < 0)),
    }


def load_book(path):
    df = pl.read_csv(path)
    lt = df["local_timestamp"].to_numpy()
    ap = np.stack([df[f"asks[{i}].price"].to_numpy() for i in range(25)], axis=1).astype(float)
    aq = np.stack([df[f"asks[{i}].amount"].to_numpy() for i in range(25)], axis=1).astype(float)
    bp0 = df["bids[0].price"].to_numpy().astype(float)
    return df.select(["timestamp", "local_timestamp"]), lt, ap, aq, bp0


def walk(ap_row, aq_row, notional):
    """Marche le carnet côté ask pour un BUY de `notional` (quote). Retourne (vwap, insufficient, visible_notional)."""
    ok = np.isfinite(ap_row) & np.isfinite(aq_row) & (aq_row > 0)
    p, a = ap_row[ok], aq_row[ok]
    lvl_notional = p * a
    cum = np.cumsum(lvl_notional)
    visible = float(cum[-1]) if cum.size else 0.0
    if visible < notional:
        base = float(a.sum())
        return (visible / base if base > 0 else np.nan), True, visible
    k = int(np.searchsorted(cum, notional, side="left"))
    prev = cum[k - 1] if k > 0 else 0.0
    base = float(a[:k].sum()) + (notional - prev) / p[k]
    return notional / base, False, visible


def run_instrument(data, label, ex, sym, kind):
    bpath = data / f"{ex}_book_snapshot_25_{DATE}_{sym}.csv.gz"
    tpath = data / f"{ex}_trades_{DATE}_{sym}.csv.gz"
    if not bpath.exists():
        return {"status": "MISSING_BOOK"}
    tsdf, lt, ap, aq, bp0 = load_book(bpath)
    mid = (ap[:, 0] + bp0) / 2.0
    res = {"kind": kind, "book_ts_semantics": ts_semantics(tsdf)}

    trades = None
    if tpath.exists():
        tr = pl.read_csv(tpath, schema_overrides={"id": pl.String})
        res["trades_ts_semantics"] = ts_semantics(tr)
        trades = tr
    t_lt = trades["local_timestamp"].to_numpy() if trades is not None else None
    t_px = trades["price"].to_numpy().astype(float) if trades is not None else None
    t_amt = trades["amount"].to_numpy().astype(float) if trades is not None else None
    t_side = trades["side"].to_numpy() if trades is not None else None
    t_ts = trades["timestamp"].to_numpy() if trades is not None else None
    t_cum_notional = np.cumsum(t_px * t_amt) if trades is not None else None

    day0 = int(lt[0] // (86400 * US) * 86400 * US)
    grid = np.arange(day0 + WARMUP_S * US, day0 + 86400 * US - 60 * US, STEP_S * US)
    # mid 1-min (as-of PIT) pour sigma causal
    minute_grid = np.arange(day0, day0 + 86400 * US + 1, 60 * US)
    mi = np.searchsorted(lt, minute_grid, side="right") - 1
    mid_min = np.where(mi >= 0, mid[np.clip(mi, 0, None)], np.nan)

    cells = {n: {"walk": [], "insuff": 0, "hs": [], "sqrt": [], "fixed_err": [], "hs_err": [], "sqrt_err": [],
                 "partial_lower_bound": []} for n in NOTIONALS}
    staleness_ms, spreads_bps, vis_depth = [], [], []
    mk = {h: [] for h in HORIZONS_S}
    mk_vwap_1e5 = {h: [] for h in HORIZONS_S}
    for t in grid:
        i = int(np.searchsorted(lt, t, side="right") - 1)
        if i < 0:
            continue
        staleness_ms.append((t - lt[i]) / 1000.0)
        m = mid[i]
        hs_bps = (ap[i, 0] - m) / m * 1e4
        spreads_bps.append(2 * hs_bps)
        # sigma journalier causal : rendements log 1-min sur [t-1h, t]
        k1 = int((t - day0) // (60 * US))
        w = mid_min[max(0, k1 - 60): k1 + 1]
        r = np.diff(np.log(w[np.isfinite(w)]))
        sigma_d = float(np.std(r, ddof=1) * np.sqrt(1440)) if r.size > 10 else np.nan
        if trades is not None:
            j1 = np.searchsorted(t_lt, t, side="right")
            j0 = np.searchsorted(t_lt, t - 3600 * US, side="right")
            v1h = float(t_cum_notional[j1 - 1] - (t_cum_notional[j0 - 1] if j0 > 0 else 0.0)) if j1 > 0 else 0.0
            v_d = v1h * 24.0
        else:
            v_d = np.nan
        vwap_cache = {}
        for n in NOTIONALS:
            vwap, insuff, vis = walk(ap[i], aq[i], n)
            if n == NOTIONALS[-1]:
                vis_depth.append(vis)
            c = (vwap / m - 1) * 1e4
            sq = hs_bps + Y_SQRT * sigma_d * np.sqrt(n / v_d) * 1e4 if v_d and v_d > 0 else np.nan
            cell = cells[n]
            if insuff:
                cell["insuff"] += 1
                cell["partial_lower_bound"].append(c)
                continue
            vwap_cache[n] = vwap
            cell["walk"].append(c)
            cell["hs"].append(hs_bps)
            cell["sqrt"].append(sq)
            cell["fixed_err"].append(FIXED_BPS - c)
            cell["hs_err"].append(hs_bps - c)
            cell["sqrt_err"].append(sq - c)
        for h in HORIZONS_S:
            ih = int(np.searchsorted(lt, t + h * US, side="right") - 1)
            mk[h].append((mid[ih] / m - 1) * 1e4)
            if 100_000 in vwap_cache:
                mk_vwap_1e5[h].append((mid[ih] - vwap_cache[100_000]) / m * 1e4)

    out = {}
    for n, c in cells.items():
        tot = len(c["walk"]) + c["insuff"]
        out[str(n)] = {
            "n_instants": tot,
            "share_INSUFFICIENT_VISIBLE_DEPTH": round(c["insuff"] / tot, 4) if tot else None,
            "walk_cost_bps": q(c["walk"]),
            "partial_visible_cost_lower_bound_bps": q(c["partial_lower_bound"]),
            "model_halfspread_bps": q(c["hs"]),
            "model_sqrt_bps": q(c["sqrt"]),
            "err_fixed5_minus_walk_bps": q(c["fixed_err"]),
            "err_halfspread_minus_walk_bps": q(c["hs_err"]),
            "err_sqrt_minus_walk_bps": q(c["sqrt_err"]),
            "mae_bps": {k: (round(float(np.nanmean(np.abs(c[k]))), 4) if c[k] else None)
                        for k in ("fixed_err", "hs_err", "sqrt_err")},
        }
    res["by_notional_usdt"] = out
    res["snapshot_staleness_at_decision_ms"] = q(staleness_ms, (50, 90, 99))
    res["quoted_spread_bps"] = q(spreads_bps)
    res["visible_ask_depth_25lvl_usdt"] = q(vis_depth, (1, 10, 50, 90))
    res["mid_drift_after_decision_bps"] = {f"+{h}s": q(v, (1, 50, 99)) for h, v in mk.items()}
    res["markout_buy_1e5_vs_vwap_bps"] = {f"+{h}s": q(v, (1, 50, 99)) for h, v in mk_vwap_1e5.items()}

    # Agresseurs acheteurs publics agrégés par timestamp d'échange, notionnel >= 10 kUSDT
    if trades is not None:
        tb = (pl.DataFrame({"ts": t_ts, "lt": t_lt, "side": t_side, "n": t_px * t_amt})
              .filter(pl.col("side") == "buy").group_by("ts").agg(pl.col("lt").min(), pl.col("n").sum())
              .filter(pl.col("n") >= 10_000).sort("ts"))
        agg = {h: [] for h in HORIZONS_S}
        for ts_i, lt_i in zip(tb["ts"].to_numpy(), tb["lt"].to_numpy()):
            i0 = int(np.searchsorted(lt, lt_i, side="left") - 1)  # dernier carnet reçu AVANT le trade
            if i0 < 0:
                continue
            for h in HORIZONS_S:
                ih = int(np.searchsorted(lt, lt_i + h * US, side="right") - 1)
                if ih >= len(lt) - 1:
                    continue
                agg[h].append((mid[ih] / mid[i0] - 1) * 1e4)
        res["public_buy_aggressor_ge10k_mid_markout_bps"] = {"n_events": int(tb.height),
                                                             **{f"+{h}s": q(v, (10, 50, 90)) for h, v in agg.items()}}
    return res


def funding(data):
    out = {}
    for ex, sym in [("binance-futures", "BTCUSDT"), ("binance-futures", "DOGEUSDT"),
                    ("okex-swap", "BTC-USDT-SWAP"), ("okex-swap", "DOGE-USDT-SWAP")]:
        p = data / f"{ex}_derivative_ticker_{DATE}_{sym}.csv.gz"
        if not p.exists():
            continue
        df = pl.read_csv(p).filter(pl.col("funding_timestamp").is_not_null() & pl.col("funding_rate").is_not_null())
        df = df.sort("local_timestamp")
        # taux « courant » juste avant chaque échéance funding_timestamp (dernier vu avant l'échéance)
        settled = (df.filter(pl.col("timestamp") < pl.col("funding_timestamp"))
                   .group_by("funding_timestamp").agg(pl.col("funding_rate").last(), pl.col("local_timestamp").last())
                   .sort("funding_timestamp"))
        out[f"{ex}:{sym}"] = {
            "settlements_seen": [
                {"funding_time_utc_us": int(r[0]), "last_rate_before": float(r[1])}
                for r in settled.select(["funding_timestamp", "funding_rate"]).iter_rows()],
            "ts_semantics": ts_semantics(df),
        }
    return out


def main():
    data = Path(sys.argv[1])
    outp = Path(sys.argv[2])
    res = {"date": DATE, "notionals_usdt": NOTIONALS, "step_s": STEP_S, "warmup_s": WARMUP_S,
           "fixed_bps": FIXED_BPS, "Y_sqrt": Y_SQRT,
           "pit_rule": "as-of on local_timestamp (receipt); exchange timestamp never used for selection",
           "instruments": {}}
    for label, ex, sym, kind in INSTRUMENTS:
        res["instruments"][label] = run_instrument(data, label, ex, sym, kind)
    res["funding"] = funding(data)
    txt = json.dumps(res, sort_keys=True, indent=1, default=float)
    outp.write_text(txt)
    print(hashlib.sha256(txt.encode()).hexdigest())


if __name__ == "__main__":
    main()
