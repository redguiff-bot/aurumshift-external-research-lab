"""15 executed primitives. Every function: (P, params) -> weights DataFrame (index IDX, cols SYMS), decided AFTER bar i using data <= i.
Parameters are pre-registered defaults (no tuning). `SCALABLE` lists params perturbed in falsification."""
import numpy as np, pandas as pd
from alpha_lib import (IDX, SYMS, vol_est, zscore, hold_every, rank_neutral, dir_weights, MAJORS)

def _z(P, n, sigw=168):
    lr = P["lret"]; sig = vol_est(lr, sigw)
    Rn = lr.rolling(n, min_periods=n).sum()
    return Rn / (sig * np.sqrt(n)), Rn

def _hold_event(ev, K):
    e = ev.replace(0, np.nan)
    return e.ffill(limit=K - 1).fillna(0.0)

def p01_tsmom(P, n=72, R=6):
    z, _ = _z(P, n); return hold_every(dir_weights(z.clip(-1, 1)), R)

def p02_xsrs(P, n=168, R=24):
    _, Rn = _z(P, n); return hold_every(rank_neutral(Rn), R)

def p03_rev(P, n=4, R=4):
    z, _ = _z(P, n); return hold_every(dir_weights(-(z / 2).clip(-1, 1)), R)

def p04_donch(P, N=48, M=24):
    c, hi, lo = P["c"], P["hi"], P["lo"]
    hh = hi.rolling(N).max().shift(1); ll = lo.rolling(M).min().shift(1)
    hh2 = hi.rolling(M).max().shift(1); ll2 = lo.rolling(N).min().shift(1)
    up = (c > hh).values; dn = (c < ll2).values      # entry: break N-bar extreme
    exl = (c < ll).values; exs = (c > hh2).values    # exit: M-bar opposite extreme
    pos = np.zeros(c.shape)
    for j in range(c.shape[1]):
        p = 0.0
        for i in range(c.shape[0]):
            if p >= 0 and dn[i, j]: p = -1.0
            elif p <= 0 and up[i, j]: p = 1.0
            elif p > 0 and exl[i, j]: p = 0.0
            elif p < 0 and exs[i, j]: p = 0.0
            pos[i, j] = p
    return dir_weights(pd.DataFrame(pos, index=c.index, columns=c.columns))

def p05_vcb(P, q=0.2, n=6, zb=1.0, R=12, look=12):
    lr = P["lret"]; sq = lr.rolling(24, min_periods=24).std() / vol_est(lr, 168)
    pct = sq.rolling(2160, min_periods=720).rank(pct=True)
    comp = pct.rolling(look, min_periods=look).min() < q
    z, Rn = _z(P, n)
    s = np.sign(Rn) * ((z.abs() > zb) & comp)
    return hold_every(dir_weights(s.where(comp.notna() & z.notna())), R)

def p06_fund_xs(P, R=24):
    return hold_every(rank_neutral(-P["f8"]), R)   # fade crowded funding: short highest, long lowest

def p07_basis_carry(P, thr=3e-4, R=8):
    on = (P["f8"] >= thr).astype(float).where(P["f8"].notna())
    on = hold_every(on, R)
    n = on.shape[1]; return on / n      # capital-per-asset weights: long spot / short perp (special backtest)

def p08_spot_perp_basis(P, w=720, R=12):
    b = P["c"] / P["sc"] - 1.0
    z = zscore(b, w, 240)
    return hold_every(dir_weights(-(z / 2).clip(-1, 1)), R)   # perp rich vs spot -> short

def _doi(P, n):
    return np.log(P["oi"] / P["oi"].shift(n))

def p09_oi_px(P, n=24, R=12):
    zr, _ = _z(P, n); zo = zscore(_doi(P, n), 720, 240)
    s = zr.clip(-1, 1) * np.sign(zo)      # OI building -> follow price; OI unwinding -> fade
    return hold_every(dir_weights(s), R)

def p10_liq_flush(P, n=4, zt=2.5, oik=1.5, K=4):
    z, Rn = _z(P, n); d = _doi(P, n); thr = oik * d.rolling(720, min_periods=240).std()
    ev = -np.sign(Rn) * ((z.abs() > zt) & (d < -thr))
    return dir_weights(_hold_event(ev, K))

def p11_flow(P, m=6, R=4):
    imb = 2 * P["tbqv"] / P["qv"] - 1.0
    z = zscore(imb.rolling(m, min_periods=m).mean(), 720, 240)
    return hold_every(dir_weights((z / 2).clip(-1, 1)), R)

def p12_illiq(P, zt=1.75, K=4):
    lr = P["lret"]; ill = np.log(lr.abs() + 1e-5) - np.log(P["qv"])
    z = zscore(ill, 720, 240)
    ev = -np.sign(lr) * (z > zt)
    return dir_weights(_hold_event(ev, K))

def p13_leadlag(P, n=2, R=2):
    z, _ = _z(P, n)
    s = ((z["BTC"].values[:, None] - z) / 2).clip(-1, 1)
    s["BTC"] = np.nan
    return hold_every(dir_weights(s), R)

def p14_season(P, minobs=90, tthr=0.0):
    lr = P["lret"]; ix = lr.index; out = pd.DataFrame(0.0, index=ix, columns=lr.columns)
    hrs = ix.hour
    for h in range(24):
        sub = lr[hrs == h]
        m = sub.expanding(min_periods=minobs).mean().shift(1)
        sd = sub.expanding(min_periods=minobs).std().shift(1)
        n = sub.expanding(min_periods=minobs).count().shift(1)
        t = m / (sd / np.sqrt(n))
        t.index = t.index - pd.Timedelta(hours=1)     # value for bar j is placed at decision index j-1 (uses obs < j)
        t = t.reindex(ix)
        sel = (hrs == (h - 1) % 24)
        out.loc[sel] = t.loc[sel].fillna(0.0).values
    s = (out / 2).clip(-1, 1)
    s = s.where(out.abs() > tthr, 0.0)
    return dir_weights(s)

def p15_rviv(P, R=24):
    dv = P["dvol"]                           # BTC, ETH hourly close, available 1h after candle start
    lr = P["lret"][["BTC", "ETH"]]; rv = lr.rolling(168, min_periods=168).std() * np.sqrt(8760) * 100
    vrp = dv - rv
    z = zscore(vrp, 720, 240)
    w = pd.DataFrame(0.0, index=P["c"].index, columns=P["c"].columns)
    w[["BTC", "ETH"]] = (z.clip(-1, 1) / 2.0)   # capital split over 2 assets; long when IV rich vs RV (risk premium reward) - pre-registered sign
    return hold_every(w, R)

PRIMS = {
    "P01_TSMOM":      dict(fn=p01_tsmom,      family="momentum/trend",                 R=6,  params=dict(n=72, R=6),  scal=["n"],  H=6),
    "P02_XS_RS":      dict(fn=p02_xsrs,       family="cross-sectional relative strength", R=24, params=dict(n=168, R=24), scal=["n"], H=24),
    "P03_REV_4H":     dict(fn=p03_rev,        family="mean reversion",                 R=4,  params=dict(n=4, R=4),   scal=["n"],  H=4),
    "P04_DONCHIAN":   dict(fn=p04_donch,      family="breakout persistence",           R=1,  params=dict(N=48, M=24), scal=["N", "M"], H=24),
    "P05_VOL_SQUEEZE_BREAK": dict(fn=p05_vcb, family="volatility compression/expansion", R=12, params=dict(q=0.2, n=6, zb=1.0, R=12, look=12), scal=["q", "zb", "look"], H=12),
    "P06_FUND_XS":    dict(fn=p06_fund_xs,    family="funding divergence / carry (crowding fade)", R=24, params=dict(R=24), scal=["R"], H=24),
    "P07_BASIS_CARRY":dict(fn=p07_basis_carry, family="carry / basis (delta-neutral)", R=8,  params=dict(thr=3e-4, R=8), scal=["thr", "R"], H=8),
    "P08_SPOT_PERP_BASIS": dict(fn=p08_spot_perp_basis, family="basis (spot-perp z-score)", R=12, params=dict(w=720, R=12), scal=["w", "R"], H=12),
    "P09_OI_PRICE":   dict(fn=p09_oi_px,      family="open-interest / price divergence", R=12, params=dict(n=24, R=12), scal=["n"], H=12),
    "P10_LIQ_FLUSH_PROXY": dict(fn=p10_liq_flush, family="liquidation pressure (OI-flush proxy)", R=1, params=dict(n=4, zt=2.5, oik=1.5, K=4), scal=["zt", "oik", "K"], H=4),
    "P11_TAKER_FLOW": dict(fn=p11_flow,       family="volume imbalance",               R=4,  params=dict(m=6, R=4),   scal=["m"],  H=4),
    "P12_ILLIQ_SHOCK":dict(fn=p12_illiq,      family="liquidity shock",                R=1,  params=dict(zt=1.75, K=4), scal=["zt", "K"], H=4),
    "P13_BTC_LEADLAG":dict(fn=p13_leadlag,    family="cross-asset lead/lag",           R=2,  params=dict(n=2, R=2),   scal=["n"],  H=2),
    "P14_HOUR_SEASON":dict(fn=p14_season,     family="intraday seasonality",           R=1,  params=dict(minobs=90, tthr=0.0), scal=["minobs"], H=1),
    "P15_RV_IV_VRP":  dict(fn=p15_rviv,       family="realized vs implied vol (BTC/ETH only)", R=24, params=dict(R=24), scal=["R"], H=24),
}
