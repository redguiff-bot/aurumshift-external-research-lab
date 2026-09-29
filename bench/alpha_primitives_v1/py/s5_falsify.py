"""Falsification battery: venue, asset, missing/stale data, latency, parameter perturbation, placebo, sub-period."""
from common import *
import warnings; warnings.filterwarnings("ignore")
P = load_panel(); NAMES = list(X.PRIMS); A5 = ["BTC", "ETH", "SOL", "XRP", "DOGE"]
out = {k: {} for k in NAMES}; rng = np.random.default_rng(7)
XV = os.path.join(L.CACHE, "xv")
def S(B, **kw): d = L.summarize(B, **kw); return {"gross_sharpe": d["gross_sharpe"], "net_sharpe": d["net_sharpe"], "gross_ann": d["gross_ann"], "net_ann": d["net_ann"], "turn_ann": d["turn_ann"]}
Wb = {k: weights(k, P) for k in NAMES}; BB = {k: bt(k, P, W=Wb[k]) for k in NAMES}

# ---- 1 latency / stale signal (fills delayed by L bars)
for k in NAMES:
    out[k]["latency"] = {str(l): S(bt(k, P, W=Wb[k], lag=l)) for l in (1, 2, 3, 6)}

# ---- 2 parameter perturbation
def scale(v, f):
    return max(1, int(round(v * f))) if isinstance(v, int) else v * f
for k in NAMES:
    spec = X.PRIMS[k]; rows = []
    for p in spec["scal"]:
        for f in (0.5, 0.75, 1.5, 2.0):
            v = scale(spec["params"][p], f)
            try:
                B = bt(k, P, W=weights(k, P, **{p: v})); s = S(B); s.update({"param": p, "factor": f, "value": v}); rows.append(s)
            except Exception as e:
                rows.append({"param": p, "factor": f, "err": str(e)})
    ok = [r for r in rows if "net_sharpe" in r and r["net_sharpe"] == r["net_sharpe"]]
    out[k]["perturbation"] = {"rows": rows, "n": len(ok), "frac_net_pos": float(np.mean([r["net_sharpe"] > 0 for r in ok])) if ok else None,
                              "frac_gross_pos": float(np.mean([r["gross_sharpe"] > 0 for r in ok])) if ok else None,
                              "median_net_sharpe": float(np.median([r["net_sharpe"] for r in ok])) if ok else None,
                              "min_net_sharpe": float(min(r["net_sharpe"] for r in ok)) if ok else None, "max_net_sharpe": float(max(r["net_sharpe"] for r in ok)) if ok else None}
    print("pert", k, out[k]["perturbation"]["frac_net_pos"], flush=True)

# ---- 3 missing data (flat vs stale-hold) at 5% / 20% random obs, and 10% asset-day feed outages
FIELDS = ["c", "hi", "lo", "qv", "tbqv", "oi", "sc", "prem", "f8"]
def degrade(P, mode, rate, seed):
    r = np.random.default_rng(seed); Q = dict(P)
    if mode == "obs":
        M = pd.DataFrame(r.random(P["c"].shape) < rate, index=P["c"].index, columns=P["c"].columns)
    else:
        days = P["c"].index.floor("D").unique(); Md = pd.DataFrame(r.random((len(days), P["c"].shape[1])) < rate, index=days, columns=P["c"].columns)
        M = Md.reindex(P["c"].index.floor("D")).set_axis(P["c"].index)
    for f in FIELDS: Q[f] = P[f].mask(M)
    Q["lret"] = np.log(Q["c"]).diff(); return Q
def wsafe(k, Q):
    return weights(k, Q)
for k in NAMES:
    res = {}
    for mode, rate in (("obs", 0.05), ("obs", 0.20), ("asset_day", 0.10)):
        agg = {"flat": [], "stale": []}
        for sd in range(3):
            Q = degrade(P, mode, rate, sd); W = wsafe(k, Q)
            agg["flat"].append(S(bt(k, P, W=W))); agg["stale"].append(S(bt(k, P, W=W.reindex(IDX).ffill())))
        res[f"{mode}_{rate}"] = {m: {kk: float(np.mean([a[kk] for a in v])) for kk in ("gross_sharpe", "net_sharpe", "turn_ann")} for m, v in agg.items()}
    out[k]["missing"] = res
    print("missing", k, flush=True)

# ---- 4 placebo. Circular time-shift is contaminated for primitives with expanding-window estimates (wrap-around lets late,
# better-informed estimates hit early returns), so: directional primitives use a block sign-randomisation null (independent +/-1 per asset per
# 24h block: keeps exposure/turnover structure, destroys direction); the delta-neutral carry P07 uses a circular shift (random timing of the 'on' state).
for k in NAMES:
    obs = S(BB[k]); gs, ns = [], []
    W = Wb[k].reindex(IDX).fillna(0.0); nb = len(IDX) // 24 + 1
    for _ in range(200):
        if k == "P07_BASIS_CARRY":
            sh = int(rng.integers(30, 330)) * 24; Wp = pd.DataFrame(np.roll(W.values, sh, axis=0), index=IDX, columns=W.columns)
        else:
            sg = rng.choice([-1.0, 1.0], size=(nb, W.shape[1])); sg = np.repeat(sg, 24, axis=0)[:len(IDX)]
            Wp = W * sg
        s_ = S(bt(k, P, W=Wp)); gs.append(s_["gross_sharpe"]); ns.append(s_["net_sharpe"])
    gs, ns = np.array(gs), np.array(ns)
    out[k]["placebo"] = {"null": "circular_shift" if k == "P07_BASIS_CARRY" else "block_sign_randomisation", "obs_gross": obs["gross_sharpe"], "obs_net": obs["net_sharpe"],
                         "p_gross": float((gs >= obs["gross_sharpe"]).mean()), "p_net": float((ns >= obs["net_sharpe"]).mean()),
                         "placebo_gross_mean": float(np.nanmean(gs)), "placebo_gross_sd": float(np.nanstd(gs))}
    print("placebo", k, out[k]["placebo"]["p_gross"], out[k]["placebo"]["p_net"], flush=True)

# ---- 5 different asset: majors / minors / leave-one-out (weights recomputed on the subset panel)
def asset_run(k, cols):
    if k == "P13_BTC_LEADLAG":
        Pf = P; W = weights(k, Pf); return S(bt(k, Pf, W=W, assets=[c for c in cols if c != "BTC"] or None))
    if k == "P15_RV_IV_VRP":
        Pf = P; W = weights(k, Pf)[["BTC", "ETH"]]; cs = [c for c in cols if c in ("BTC", "ETH")]
        if not cs: return None
        W2 = pd.DataFrame(0.0, index=IDX, columns=L.SYMS); W2[cs] = W[cs] * (2 / len(cs)); return S(bt(k, Pf, W=W2, assets=cs))
    Ps = sub_panel(P, cols); return S(bt(k, Ps))
for k in NAMES:
    r = {}
    for nm, cols in (("majors", L.MAJORS), ("minors", L.MINORS)):
        r[nm] = asset_run(k, cols)
    loo = []
    for a in L.SYMS:
        cols = [c for c in L.SYMS if c != a]
        try:
            s = asset_run(k, cols)
            if s: loo.append(s["net_sharpe"])
        except Exception: pass
    r["leave_one_out_net_sharpe"] = {"min": float(np.nanmin(loo)), "max": float(np.nanmax(loo)), "n": len(loo)} if loo else None
    per = {}
    for a in L.SYMS:                          # single-asset: gross sharpe per asset for directional prims (contribution)
        d = BB[k]  # placeholder for shape
    out[k]["assets"] = r
    print("assets", k, flush=True)

# ---- 6 sub-period stability (calendar quarters)
for k in NAMES:
    g = BB[k].loc[L.EVAL_START:, ["gross", "net"]].resample("1D").sum(); q = g.groupby(g.index.tz_localize(None).to_period("Q")).sum()
    out[k]["quarters"] = {"n": len(q), "frac_gross_pos": float((q.gross > 0).mean()), "frac_net_pos": float((q.net > 0).mean()), "worst_q_net": float(q.net.min()), "best_q_net": float(q.net.max())}
    r90 = g.net.rolling(90).sum().dropna(); out[k]["rolling90_net_pos_frac"] = float((r90 > 0).mean()) if len(r90) else None

# ---- 7 wrong venue / different data provider
def venue_panel(name, cols):
    frames = {}
    for a in cols:
        fp = os.path.join(XV, f"{name}_{a}.csv")
        if not os.path.exists(fp): continue
        d = pd.read_csv(fp)
        if len(d) == 0: continue
        d.index = pd.to_datetime(d.ts, unit="ms", utc=True); frames[a] = d[~d.index.duplicated()].reindex(IDX)
    cs = list(frames)
    Q = {"c": pd.DataFrame({a: frames[a].c for a in cs}), "hi": pd.DataFrame({a: frames[a].h for a in cs}), "lo": pd.DataFrame({a: frames[a].l for a in cs})}
    Q["ret"] = Q["c"].pct_change(fill_method=None); Q["lret"] = np.log(Q["c"]).diff(); Q["fund_bar"] = Q["c"] * 0.0
    Q["sret"] = Q["ret"]; return Q, cs
PRICE_ONLY = ["P01_TSMOM", "P02_XS_RS", "P03_REV_4H", "P04_DONCHIAN", "P05_VOL_SQUEEZE_BREAK", "P13_BTC_LEADLAG", "P14_HOUR_SEASON"]
venues = {"okx_perp": ("okx", 0.0), "coinbase_spot": ("coinbase", 5.0), "gate_spot": ("gate", 5.0)}
vinfo = {}
Pb5 = sub_panel(P, A5)
for vn, (src, extra) in venues.items():
    Q, cs = venue_panel(src, A5); first = Q["c"].dropna(how="all").index[0]; st = max(L.EVAL_START, first + pd.Timedelta(days=100))
    cm = {a: L.COST_BPS[a] + extra for a in cs}
    vinfo[vn] = {"assets": cs, "eval_start": str(st), "rows_valid_frac": float(Q["c"].loc[st:].notna().mean().mean())}
    for k in PRICE_ONLY:
        try:
            Wv = weights(k, Q); Bv = L.backtest(Wv, Q, assets=cs, cost_map=cm, funding=False)
            Wq = weights(k, Pb5); Bq = L.backtest(Wq, Pb5, assets=A5, funding=False, cost_map={a: L.COST_BPS[a] + extra for a in A5})
            out[k].setdefault("venues", {})[vn] = {"venue": S(Bv, start=st), "binance_same_assets_same_window": S(Bq, start=st)}
        except Exception as e:
            out[k].setdefault("venues", {})[vn] = {"err": str(e)}
out_venue_info = vinfo
# signal from Binance-derived microstructure/funding features, PnL realised on OKX prices (wrong-venue execution)
Qo, cso = venue_panel("okx", A5)
FEAT = ["P06_FUND_XS", "P08_SPOT_PERP_BASIS", "P09_OI_PRICE", "P10_LIQ_FLUSH_PROXY", "P11_TAKER_FLOW", "P12_ILLIQ_SHOCK"]
for k in FEAT:
    W = weights(k, Pb5); Pq = dict(Pb5); Pq["ret"] = Qo["ret"][A5]
    out[k].setdefault("venues", {})["binance_signal_okx_prices"] = {"binance_exec": S(L.backtest(W, Pb5, assets=A5)), "okx_exec": S(L.backtest(W, Pq, assets=A5))}
# HL funding as the crowding signal (P06)
hlf = {}
for a in A5:
    d = pd.read_csv(os.path.join(XV, f"hl_f_{a}.csv")); d.index = pd.DatetimeIndex(pd.to_datetime(d.time, unit="ms", utc=True)).floor("h")
    hlf[a] = d.fundingRate.groupby(d.index).last().reindex(IDX)
HL = pd.DataFrame(hlf); f8_hl = (HL.rolling(24, min_periods=18).mean() * 8).ffill(limit=6)
cor = {a: float(pd.concat([f8_hl[a], P["f8"][a]], axis=1).dropna().corr().iloc[0, 1]) for a in A5}
Wh = L.hold_every(L.rank_neutral(-f8_hl), 24); Wb5 = weights("P06_FUND_XS", Pb5)
Pq = dict(Pb5); Pq["ret"] = Qo["ret"][A5]
out["P06_FUND_XS"]["venues"]["hyperliquid_funding_signal"] = {"corr_hl_vs_binance_funding": cor, "hl_signal_okx_prices": S(L.backtest(Wh, Pq, assets=A5)), "binance_signal_okx_prices": S(L.backtest(Wb5, Pq, assets=A5))}
# Kraken sanity: recent-window return correlation vs Binance (data-feed consistency)
kr = {}
for a in A5:
    d = pd.read_csv(os.path.join(XV, f"kraken_{a}.csv")); d.index = pd.to_datetime(d.ts, unit="ms", utc=True)
    r1 = np.log(d.c).diff(); r2 = P["lret"][a].reindex(d.index)
    kr[a] = {"rows": len(d), "first": str(d.index[0]), "ret_corr_vs_binance_perp": float(pd.concat([r1, r2], axis=1).dropna().corr().iloc[0, 1])}
out_kraken = kr
o = {"prims": out, "venue_info": vinfo, "kraken_check": kr}
jd(o, "s5_falsify.json"); print("done")
