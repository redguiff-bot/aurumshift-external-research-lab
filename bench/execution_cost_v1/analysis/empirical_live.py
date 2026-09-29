"""Empirical analysis of the live public capture (OKX, Coinbase, Kraken) — no private data.
python analysis/empirical_live.py [data/live] [tag]"""
import gzip, json, os, sys, glob, time
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "live")
TAG = sys.argv[2] if len(sys.argv) > 2 else "live"
RES = os.path.join(ROOT, "results")
NOTIONALS = [1e3, 1e4, 1e5, 3e5, 1e6, 3e6]
HORIZ = [2, 4, 10, 30]


def read(fn):
    rows = []
    try:
        with gzip.open(fn, "rt") as f:
            for line in f:
                try: rows.append(json.loads(line))
                except Exception: break
    except (EOFError, OSError):
        pass
    return rows


VENUES = {  # venue -> [(asset, book_file_stem, trade_file_stem)]
    "okx": [("BTC", "okx_book_BTC-USDT", "okx_trades_BTC-USDT"), ("ETH", "okx_book_ETH-USDT", "okx_trades_ETH-USDT"), ("SOL", "okx_book_SOL-USDT", "okx_trades_SOL-USDT")],
    "coinbase": [("BTC", "cb_book_BTC-USD", "cb_trades_BTC-USD"), ("ETH", "cb_book_ETH-USD", "cb_trades_ETH-USD"), ("SOL", "cb_book_SOL-USD", "cb_trades_SOL-USD")],
    "kraken": [("BTC", "kr_book_XBTUSD", "kr_trades_XBTUSD"), ("ETH", "kr_book_ETHUSD", "kr_trades_ETHUSD"), ("SOL", "kr_book_SOLUSD", "kr_trades_SOLUSD")],
}


def load_book(stem):
    rows = read(f"{DATA}/{stem}.jsonl.gz")
    if not rows: return None
    t = np.array([(r["t0"] + r["t1"]) / 2 for r in rows]); rtt = np.array([r["t1"] - r["t0"] for r in rows])
    bids = [np.array([[float(a), float(b)] for a, b in [x[:2] for x in r["b"]]]) for r in rows]
    asks = [np.array([[float(a), float(b)] for a, b in [x[:2] for x in r["a"]]]) for r in rows]
    return dict(t=t, rtt=rtt, bids=bids, asks=asks)


def load_trades(stem, venue):
    rows = read(f"{DATA}/{stem}.jsonl.gz")
    if not rows: return None
    if venue == "okx":
        df = pd.DataFrame([dict(ts=r["ts"] / 1e3, px=float(r["px"]), sz=float(r["sz"]), side=r["side"]) for r in rows])
    elif venue == "coinbase":
        df = pd.DataFrame([dict(ts=pd.Timestamp(r["time"]).timestamp(), px=float(r["price"]), sz=float(r["size"]), side=r["side"]) for r in rows])
    else:
        df = pd.DataFrame([dict(ts=float(r["ts"]), px=float(r["px"]), sz=float(r["sz"]), side="buy" if r["side"] == "b" else "sell") for r in rows])
    return df.sort_values("ts").reset_index(drop=True)


def walk_cost(side_levels, mid, N):
    """buy walk vs mid in bps for notional N over visible levels; nan if visible depth insufficient."""
    px, q = side_levels[:, 0], side_levels[:, 1]
    notion = px * q; cum = np.cumsum(notion)
    if cum[-1] < N: return np.nan
    k = int(np.searchsorted(cum, N)); prev = cum[k - 1] if k > 0 else 0.0
    qty = (q[:k].sum() + (N - prev) / px[k])
    avg = N / qty
    return (avg / mid - 1) * 1e4


def analyse(venue, asset, bstem, tstem):
    B = load_book(bstem); T = load_trades(tstem, venue)
    if B is None or len(B["t"]) < 50: return None
    n = len(B["t"])
    bb = np.array([b[0, 0] for b in B["bids"]]); aa = np.array([a[0, 0] for a in B["asks"]])
    mid = (bb + aa) / 2; spr = (aa - bb) / mid * 1e4
    tick = np.min(np.abs(np.diff(np.unique(np.concatenate([[b[0, 0] for b in B["bids"]], [b[1, 0] for b in B["bids"]]]))))) if n > 0 else np.nan
    tick = float(np.min([np.min(np.abs(np.diff(b[:, 0]))) for b in B["bids"][:200]]))
    out = dict(venue=venue, asset=asset, n_snap=int(n), duration_s=float(B["t"][-1] - B["t"][0]), rtt_ms_p50=float(np.median(B["rtt"]) * 1e3),
               rtt_ms_p95=float(np.percentile(B["rtt"], 95) * 1e3), sampling_gap_s_p50=float(np.median(np.diff(B["t"]))),
               crossed_or_locked_frac=float(np.mean(aa <= bb)),
               tick_bps=float(tick / np.median(mid) * 1e4), spread_bps=dict(mean=float(spr.mean()), p50=float(np.median(spr)), p95=float(np.percentile(spr, 95)), max=float(spr.max()),
                                                                    one_tick_frac=float(np.mean(np.isclose(aa - bb, tick, rtol=0.01)))))
    # visible depth
    vis_lo = np.array([min(b[-1, 0], 1e18) for b in B["bids"]]); vis_hi = np.array([a[-1, 0] for a in B["asks"]])
    out["visible_depth_bps_ask"] = dict(p50=float(np.median((vis_hi / mid - 1) * 1e4)), n_levels=int(len(B["asks"][0])))
    cum_notional = lambda a, d: float((a[a[:, 0] <= a[0, 0] * (1 + d / 1e4), 0] * a[a[:, 0] <= a[0, 0] * (1 + d / 1e4), 1]).sum())
    out["ask_depth_usd_within_bps_from_touch"] = {str(d): float(np.median([cum_notional(a, d) for a in B["asks"]])) for d in (1, 2, 5, 10)}
    # power-law exponent of cumulative depth vs distance from touch (beta)
    betas = []
    for a, m in zip(B["asks"][::5], mid[::5]):
        d = (a[:, 0] / a[0, 0] - 1) * 1e4 + max(1e-3, 0)
        c = np.cumsum(a[:, 0] * a[:, 1]); ok = d > 0
        if ok.sum() >= 8 and d[ok].max() > 3 * d[ok].min():
            betas.append(np.polyfit(np.log(d[ok]), np.log(c[ok]), 1)[0])
    out["depth_exponent_beta"] = dict(median=float(np.median(betas)) if betas else None, p10=float(np.percentile(betas, 10)) if betas else None,
                                      p90=float(np.percentile(betas, 90)) if betas else None)
    # walk cost distribution by notional (vs mid, includes half-spread) + coverage of visible depth
    walk = {}
    W = {N: np.array([walk_cost(a, m, N) for a, m in zip(B["asks"], mid)]) for N in NOTIONALS}
    for N, w in W.items():
        walk[str(int(N))] = dict(coverage=float(np.mean(~np.isnan(w))), mean=float(np.nanmean(w)) if np.any(~np.isnan(w)) else None,
                                 p95=float(np.nanpercentile(w, 95)) if np.any(~np.isnan(w)) else None)
    out["walk_bps_vs_mid"] = walk
    # ---- staleness test: predict walk at t+dt using snapshot t (dt via time index) ----
    dts = {}
    for h in HORIZ:
        j = np.searchsorted(B["t"], B["t"] + h)
        ok = j < n
        i = np.arange(n)[ok]; j = j[ok]
        res = {}
        for N in NOTIONALS:
            e = W[N][j] - W[N][i]
            if np.isfinite(e).sum() > 30:
                res[str(int(N))] = dict(n=int(np.isfinite(e).sum()), mean_err=float(np.nanmean(e)), sd_err=float(np.nanstd(e)), mae=float(np.nanmean(np.abs(e))),
                                        p95_abs=float(np.nanpercentile(np.abs(e), 95)), cost_mean=float(np.nanmean(W[N][j])))
        dts[str(h)] = res
    out["stale_walk_error"] = dts
    # ---- baseline models vs next-snapshot walk (half sample calibration -> other half test) ----
    half = n // 2
    sig = float(np.std(np.diff(np.log(mid))) / np.sqrt(np.median(np.diff(B["t"]))) * 1e4)      # bps / sqrt(s)
    dur = B["t"][-1] - B["t"][0]
    Vday = float(T.px.mul(T.sz).sum() / max(T.ts.max() - T.ts.min(), 1) * 86400) if T is not None and len(T) > 10 else np.nan
    out["sigma_bps_sqrt_s"] = sig; out["Vday_proxy_usd"] = Vday
    # vol <-> liquidity coupling (does cost rise with local realised vol?)  Spearman over the capture
    from scipy.stats import spearmanr
    rv = pd.Series(np.diff(np.log(mid), prepend=np.nan) * 1e4).rolling(30).std().values
    cpl = {}
    for nm, arr in (("spread", spr), ("walk_1e4", W[1e4]), ("walk_1e5", W[1e5])):
        ok = np.isfinite(rv) & np.isfinite(arr)
        if ok.sum() > 50 and np.std(arr[ok]) > 0:
            r_, p_ = spearmanr(rv[ok], arr[ok]); cpl[nm] = dict(rho=float(r_), p=float(p_), n=int(ok.sum()))
    out["vol_liquidity_coupling_spearman"] = cpl
    hz = 4
    j = np.searchsorted(B["t"], B["t"] + hz); okj = j < n
    base = {}
    for N in NOTIONALS:
        tgt = np.full(n, np.nan); tgt[np.where(okj)[0]] = W[N][j[okj]]
        tr = slice(0, half); te = slice(half, n)
        if np.isfinite(tgt[te]).sum() < 30 or np.isfinite(tgt[tr]).sum() < 30: continue
        m_c = np.nanmean(tgt[tr])                                   # fixed bps
        k_sp = np.nanmean(tgt[tr]) / np.mean(spr[tr] / 2); Y = np.nanmean((tgt[tr] - spr[tr] / 2) / (sig * np.sqrt(86400) * np.sqrt(N / Vday))) if np.isfinite(Vday) else np.nan
        preds = {"fixed_bps(train mean)": np.full(n, m_c), "half_spread_only": spr / 2, "spread_prop(k train)": k_sp * spr / 2,
                 "sqrt(Y train)": spr / 2 + Y * sig * np.sqrt(86400) * np.sqrt(N / Vday) if np.isfinite(Y) else np.full(n, np.nan),
                 "book_walk(snapshot t)": W[N]}
        rowb = {}
        for name, p in preds.items():
            e = (p - tgt)[te]
            if np.isfinite(e).sum() > 30:
                rowb[name] = dict(bias=float(np.nanmean(e)), mae=float(np.nanmean(np.abs(e))), rmse=float(np.sqrt(np.nanmean(e ** 2))))
        rowb["_target_mean"] = float(np.nanmean(tgt[te])); rowb["_Y_fit"] = float(Y) if np.isfinite(Y) else None
        base[str(int(N))] = rowb
    out["baseline_vs_next_book_walk_dt4s"] = base
    # ---- mid drift over horizon (latency perturbation) ----
    dr = {}
    for h in (1, 2, 4, 10, 30):
        j = np.searchsorted(B["t"], B["t"] + h); ok = j < n
        d = (mid[j[ok]] / mid[np.arange(n)[ok]] - 1) * 1e4
        dr[str(h)] = dict(sd_bps=float(d.std()), mean_bps=float(d.mean()), sd_over_half_spread=float(d.std() / (np.mean(spr) / 2)), p99_abs=float(np.percentile(np.abs(d), 99)),
                          sqrt_scaling_pred=float(sig * np.sqrt(h)))
    out["mid_drift_by_horizon_s"] = dr
    # ---- trades: aggressor by quote rule, effective / realized spread, tape estimators ----
    if T is not None and len(T) > 50:
        tt = T.ts.values
        idx = np.clip(np.searchsorted(B["t"], tt) - 1, 0, n - 1)     # last snapshot BEFORE trade (receive-time axis; clock skew ignored)
        okt = (tt >= B["t"][0]) & (tt <= B["t"][-1] + 5)
        m0 = mid[idx]; px = T.px.values
        sign_q = np.where(px > m0, 1, np.where(px < m0, -1, 0))
        listed = np.where(T.side.values == "buy", 1, -1)
        # mapping check: agreement of the venue's side flag with the quote rule
        nz = (sign_q != 0) & okt
        agree = float(np.mean(sign_q[nz] == listed[nz])) if nz.any() else np.nan
        out["trade_side_flag_agreement_with_quote_rule"] = agree
        s_use = listed if agree >= 0.5 else -listed
        eff = 2 * s_use * (px - m0) / m0 * 1e4
        real = {}
        for h in (5, 30):
            j2 = np.clip(np.searchsorted(B["t"], tt + h) - 1, 0, n - 1)
            valid = okt & (tt + h <= B["t"][-1])
            real[str(h)] = float(np.mean((2 * s_use * (px - mid[j2]) / m0 * 1e4)[valid])) if valid.any() else None
        out["effective_spread_bps_mean"] = float(np.mean(eff[okt])); out["effective_spread_bps_median"] = float(np.median(eff[okt]))
        out["realized_spread_bps_mean"] = real
        out["n_trades"] = int(okt.sum())
        # tape-only estimators from 1-min OHLC of trade prices
        T["bar"] = (T.ts // 60).astype(int)
        g = T.groupby("bar").px.agg(["first", "max", "min", "last"]); g.columns = ["O", "H", "L", "C"]
        if len(g) >= 10:
            sys.path.insert(0, os.path.join(ROOT, "models")); import models as M
            cs, neg = M.corwin_schultz(g.H.values, g.L.values); ar = M.abdi_ranaldo(g.C.values, g.H.values, g.L.values)
            out["ohlc_proxies_1m_bps"] = dict(n_bars=int(len(g)), corwin_schultz=cs * 1e4, cs_negative_frac=neg, abdi_ranaldo=ar * 1e4,
                                              roll=M.roll(g.C.values) / float(np.mean(g.C.values)) * 1e4, hl_range_proxy=M.hl_range_proxy(g.H.values, g.L.values) * 1e4,
                                              quoted_spread_mean_bps=float(spr.mean()), effective_spread_mean_bps=float(np.mean(eff[okt])))
        # passive fill bounds for a hypothetical BUY at best bid, horizon Hh
        fills = {}
        for Hh in (30, 60):
            up = []; lo = []; thr = []; mk = []; mk_all = []; adv_i = []; opp_nf = []; opp_f = []
            for i in range(0, n - 1, 3):
                t0 = B["t"][i]; b0 = bb[i]; q0 = B["bids"][i][0, 1]
                if t0 + Hh + 30 > B["t"][-1]: break
                a, bnd = np.searchsorted(tt, t0), np.searchsorted(tt, t0 + Hh)
                w = slice(a, bnd)
                sells = (px[w] <= b0) if bnd > a else np.array([], bool)
                up.append(bool(sells.any()))                               # front-of-queue optimistic
                thr.append(bool((px[w] < b0).any()) if bnd > a else False)  # trade strictly through our price
                vol_at = float((T.sz.values[w][px[w] <= b0]).sum()) if bnd > a else 0.0
                lo.append(bool(vol_at >= q0))                               # back-of-queue: must consume displayed queue (no cancels)
                adv_i.append(np.nan)
                jH = np.clip(np.searchsorted(B["t"], t0 + Hh) - 1, 0, n - 1)
                (opp_f if up[-1] else opp_nf).append((mid[jH] / mid[i] - 1) * 1e4)      # mid drift over the waiting horizon
                if up[-1]:
                    kf = a + int(np.argmax(sells)); tf = tt[kf]
                    j3 = np.clip(np.searchsorted(B["t"], tf + 30) - 1, 0, n - 1)
                    mk.append((b0 - mid[j3]) / b0 * 1e4)                  # positive = mid fell below our fill (adverse for buyer)
                    adv_i[-1] = mk[-1]
                j4 = np.clip(np.searchsorted(B["t"], t0 + 30) - 1, 0, n - 1); mk_all.append((mid[i] - mid[j4]) / mid[i] * 1e4)
            adv_i = np.array(adv_i); mka = np.array(mk_all)
            diff = np.nanmean(adv_i) - mka.mean() if np.isfinite(adv_i).any() else np.nan
            rng_ = np.random.default_rng(5); ci = [np.nan, np.nan]
            if np.isfinite(adv_i).sum() > 30:
                bl = 20; nb = int(np.ceil(len(mka) / bl)); ds = []
                for _ in range(400):
                    idx_ = np.concatenate([np.arange(k * bl, min((k + 1) * bl, len(mka))) for k in rng_.integers(0, nb, nb)])
                    ai = adv_i[idx_]; ds.append(np.nanmean(ai) - mka[idx_].mean() if np.isfinite(ai).any() else np.nan)
                ci = [float(np.nanpercentile(ds, 2.5)), float(np.nanpercentile(ds, 97.5))]
            fills[str(Hh)] = dict(drift_over_H_if_no_fill_bps=float(np.mean(opp_nf)) if opp_nf else None, drift_over_H_if_fill_bps=float(np.mean(opp_f)) if opp_f else None, n_nofill=len(opp_nf), adverse_diff_cond_minus_uncond=float(diff), adverse_diff_ci95_block_bootstrap=ci, n=len(up), p_fill_upper_front_of_queue=float(np.mean(up)), p_fill_price_through=float(np.mean(thr)),
                                  p_fill_lower_back_of_queue=float(np.mean(lo)), adverse_markout30s_bps_given_fill=float(np.mean(mk)) if mk else None,
                                  adverse_markout30s_unconditional=float(np.mean(mk_all)), n_fill_upper=int(np.sum(up)))
        out["passive_fill_bounds"] = fills
    out["_series"] = None
    return out, dict(t=B["t"], mid=mid, spr=spr, bb=bb, aa=aa)


if __name__ == "__main__":
    results = []; series = {}
    for venue, lst in VENUES.items():
        for asset, b, t in lst:
            r = analyse(venue, asset, b, t)
            if r is None:
                print("skip", venue, asset); continue
            o, s = r; results.append(o); series[(venue, asset)] = s
            print(venue, asset, "n", o["n_snap"], "spread mean %.3f bps" % o["spread_bps"]["mean"], "tick %.4f bps" % o["tick_bps"], "beta", o["depth_exponent_beta"]["median"])
    # cross-venue: mid dispersion and locked/crossed opportunities (bid_A > ask_B)
    cross = {}
    for asset in ("BTC", "ETH", "SOL"):
        vs = [(v, series[(v, asset)]) for v in VENUES if (v, asset) in series]
        if len(vs) < 2: continue
        base_t = vs[0][1]["t"]
        aligned = {}
        for v, s_ in vs:
            j = np.clip(np.searchsorted(s_["t"], base_t) - 1, 0, len(s_["t"]) - 1)
            age = base_t - s_["t"][j]
            aligned[v] = dict(bb=s_["bb"][j], aa=s_["aa"][j], mid=s_["mid"][j], ok=(age >= 0) & (age < 3.0))
        pair = {}
        names = list(aligned)
        for i in range(len(names)):
            for k in range(i + 1, len(names)):
                a, b = aligned[names[i]], aligned[names[k]]
                ok = a["ok"] & b["ok"]
                d = (a["mid"] / b["mid"] - 1) * 1e4
                usdt = "okx" in (names[i], names[k])
                dm = d[ok].mean() if usdt else 0.0            # remove the constant USDT/USD basis for OKX pairs (not tradable edge)
                # edge if a crossing existed after removing basis and requiring quotes <1.5s apart (still stale-quote prone)
                e1 = ((a["bb"] - b["aa"]) / b["aa"] * 1e4 - dm)[ok]; e2 = ((b["bb"] - a["aa"]) / a["aa"] * 1e4 + dm)[ok]
                pair[f"{names[i]}-{names[k]}"] = dict(n=int(ok.sum()), mid_diff_bps_mean=float(d[ok].mean()), mid_diff_bps_sd=float(d[ok].std()),
                                                       basis_removed=bool(usdt), frac_crossed_after_basis=float(np.mean((e1 > 0) | (e2 > 0))),
                                                       p99_cross_edge_bps=float(np.percentile(np.maximum(e1, e2), 99)))
        cross[asset] = pair
    json.dump(dict(per_venue_asset=results, cross_venue=cross, note="quote currency differs: OKX USDT vs Coinbase/Kraken USD (mid_diff includes USDT basis)"),
              open(f"{RES}/empirical_{TAG}.json", "w"), indent=1, default=str)
    print("written", f"{RES}/empirical_{TAG}.json")
