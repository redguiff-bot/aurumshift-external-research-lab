"""alpha_primitives_v1 — panel loader, portfolio simulator, statistics. External research only.

Timing convention (hourly rows labelled by bar OPEN time):
  row t holds bar [t, t+1h). Everything at row t is known at decision instant t+1h.
  Decision at row t -> fill at open[t+1+delay] (delay=0 base; delay=1 = one extra bar of latency).
"""
import numpy as np, pandas as pd, os
D = os.path.join(os.path.dirname(__file__), "..", "data")
IDX = pd.date_range("2022-10-01", "2026-08-31 23:00", freq="h")
CORE = ["BTC","ETH","SOL","XRP","BNB","DOGE","ADA","LINK","AVAX","LTC"]
HOLD = ["DOT","ATOM","NEAR","TRX","BCH","ETC"]
# generic per-side cost (bps): taker fee ~5 + half-spread/slippage (BTC/ETH 1, other large 3, holdout small 5). UNKNOWN impact/tiering NOT zero -> stress multipliers.
SIDE_BPS = {**{a: 6.0 for a in ("BTC","ETH")}, **{a: 8.0 for a in CORE if a not in ("BTC","ETH")}, **{a: 10.0 for a in HOLD}}
SPLITS = {"DEV": ("2023-01-01", "2024-12-31 23:00"), "TEST": ("2025-01-01", "2026-08-31 23:00"), "FULL": ("2023-01-01", "2026-08-31 23:00")}
FIELDS = ["o","h","l","c","v","qv","tbq","prem","fund_ph","fund_chg","hlf","oi","dvol"]

def _rd(p):
    f = os.path.join(D, p)
    return pd.read_parquet(f) if os.path.exists(f) else None

def load_panel(assets, venue="bn"):
    P = {k: {} for k in FIELDS}
    for a in assets:
        if venue == "cb":
            k = _rd(f"{a}_cb.parquet")
            if k is None: continue
            k = k.reindex(IDX)
            P["o"][a], P["h"][a], P["l"][a], P["c"][a], P["v"][a] = k.open, k.high, k.low, k.close, k.volume
            P["qv"][a] = k.volume * k.close
            continue
        k = _rd(f"{a}_kl.parquet")
        if k is None: continue
        k = k.reindex(IDX)
        P["o"][a], P["h"][a], P["l"][a], P["c"][a], P["v"][a], P["qv"][a], P["tbq"][a] = k.open, k.high, k.low, k.close, k.volume, k.quote_volume, k.taker_buy_quote_volume
        pr = _rd(f"{a}_prem.parquet")
        P["prem"][a] = pr.close.reindex(IDX) if pr is not None else np.nan
        f = _rd(f"{a}_fund.parquet")
        if f is not None:
            fl = f.copy(); fl.index = fl.index.floor("h")
            fl = fl[~fl.index.duplicated(keep="last")]
            ph = (fl.rate / fl.interval_h)             # per-hour rate, known at settlement stamp (floored) -> visible at row T (decision T+1h)
            P["fund_ph"][a] = ph.reindex(IDX).ffill()
            chg = pd.Series(0.0, index=IDX)            # funding paid by a long for holding through instant T = charged to bar row T-1h
            chg.loc[chg.index.intersection(fl.index - pd.Timedelta(hours=1))] = fl.rate.values[[fl.index.get_loc(i + pd.Timedelta(hours=1)) for i in chg.index.intersection(fl.index - pd.Timedelta(hours=1))]]
            P["fund_chg"][a] = chg
        m = _rd(f"{a}_metrics5m.parquet")
        if m is not None:
            oi = m.sum_open_interest.replace(0, np.nan).resample("h").last().reindex(IDX)
            P["oi"][a] = oi.shift(1)                   # conservative extra 1-bar receipt lag on bulk 5-min snapshot
        h = _rd(f"{a}_hl_fund.parquet")
        if h is not None:
            hh = h.fundingRate.copy(); hh.index = hh.index.floor("h"); hh = hh[~hh.index.duplicated(keep="last")]
            P["hlf"][a] = hh.reindex(IDX)              # HL hourly rate stamped at hour; visible at row T (decision T+1h)
    for d in ("BTC", "ETH"):
        v = _rd(f"{d}_dvol.parquet")
        if v is not None and d in assets: P["dvol"][d] = v.close.reindex(IDX).shift(1)   # lag 1 bar (candle stamping convention unverified -> conservative)
    return {k: pd.DataFrame(v, index=IDX).reindex(columns=assets) for k, v in P.items() if len(v)}

def fwd_ret(P, H, delay=0):
    o = P["o"]; return np.log(o.shift(-(1 + H + delay)) / o.shift(-(1 + delay)))

def rstd(x, n): return x.rolling(n, min_periods=max(24, n // 4)).std()

def to_weights(S, mode, minN=None):
    """signal -> target weights (gross<=1). TS: clip(s/rolling-std,±1)/N. CS: demeaned clipped z, gross 1."""
    z = (S / rstd(S, 720)).clip(-3, 3)
    n = S.shape[1]; minN = minN or max(4, int(0.6 * n))
    if mode == "TS":
        return (z.clip(-1, 1) / n).fillna(0.0)
    valid = z.notna(); cnt = valid.sum(1)
    x = z.sub(z.mean(1), axis=0).where(valid)
    g = x.abs().sum(1)
    W = x.div(g.where(g > 0), axis=0).fillna(0.0)
    W[cnt < minN] = 0.0
    return W

def simulate(P, S, mode, H, delay=0, cost_mult=1.0, funding=True, truth=None):
    """Overlapping-tranche portfolio (1/H new tranche per hour). Returns hourly DataFrame gross/net/cost/fund/turn."""
    T = truth or P
    W = to_weights(S, mode)
    Wf = W.rolling(H, min_periods=1).mean() if H > 1 else W
    o = T["o"]; bret = (o.shift(-1) / o - 1).fillna(0.0)          # bar r: open[r] -> open[r+1]
    Wp = Wf.shift(1 + delay)                                       # weights decided at t applied to bar t+1(+delay)
    gross = (Wp * bret).sum(1)
    side = pd.Series({a: SIDE_BPS.get(a, 10.0) for a in W.columns}) * cost_mult / 1e4
    turn_a = Wf.diff().abs().fillna(0.0).shift(delay)
    cost = (turn_a * side).sum(1)
    fund = (Wp * T["fund_chg"].reindex_like(bret).fillna(0.0)).sum(1) if (funding and "fund_chg" in T) else pd.Series(0.0, index=W.index)
    net = gross - cost - fund
    return pd.DataFrame({"gross": gross, "net": net, "cost": cost, "fund": fund, "turn": turn_a.sum(1), "gexp": Wp.abs().sum(1)})

def nw_t(x, lags):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    if n < 100 or x.std() == 0: return np.nan
    xm = x - x.mean(); g0 = (xm * xm).sum() / n; v = g0
    for l in range(1, lags + 1):
        w = 1 - l / (lags + 1); v += 2 * w * (xm[l:] * xm[:-l]).sum() / n
    return x.mean() / np.sqrt(v / n)

def nw_se(x, lags):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    if n < 100: return np.nan
    xm = x - x.mean(); v = (xm * xm).sum() / n
    for l_ in range(1, lags + 1): v += 2 * (1 - l_ / (lags + 1)) * (xm[l_:] * xm[:-l_]).sum() / n
    return float(np.sqrt(max(v, 0) / n))

def stats(r, H, split="FULL", scale=1.0):
    a, b = SPLITS[split]; x = r.loc[a:b]
    n = len(x)
    if n < 200: return None
    mu = x.mean() * 8760; sd = x.std() * np.sqrt(8760)
    eq = (1 + x).cumprod(); dd = (eq / eq.cummax() - 1).min()
    return dict(ann_ret=float(mu), ann_vol=float(sd), sharpe=float(mu / sd) if sd > 0 else np.nan, t_nw=float(nw_t(x.values, max(2 * H, 24))), maxdd=float(dd), n=int(n))

def summarize(sim, H, split):
    out = {}
    for k in ("gross", "net"):
        out[k] = stats(sim[k], H, split)
    a, b = SPLITS[split]; s = sim.loc[a:b]
    out["turn_per_day"] = float(s.turn.mean() * 24); out["cost_ann"] = float(s.cost.mean() * 8760); out["fund_ann"] = float(s.fund.mean() * 8760); out["gexp"] = float(s.gexp.mean())
    return out

def cs_ic(S, F, step):
    """mean cross-sectional Spearman IC, sampled every `step` rows (non-overlapping), with t-stat."""
    Sr = S.iloc[::step].rank(axis=1); Fr = F.iloc[::step].rank(axis=1)
    ok = S.iloc[::step].notna() & F.iloc[::step].notna()
    Sr = Sr.where(ok); Fr = Fr.where(ok)
    ic = Sr.corrwith(Fr, axis=1).dropna()
    return float(ic.mean()), float(ic.mean() / (ic.std() / np.sqrt(len(ic)))) if len(ic) > 30 else np.nan, int(len(ic))

def regimes(P):
    """Past-only regime labels at decision row t (applied to PnL of bar t+1): BTC 168h realised-vol tercile vs trailing 365d; BTC 30d trend sign."""
    lr = np.log(P["c"]["BTC"]).diff(); rv = lr.rolling(168, min_periods=100).std()
    pct = rv.rolling(8760, min_periods=2000).rank(pct=True)
    vol = pd.Series(np.where(pct < 1 / 3, "LOWVOL", np.where(pct > 2 / 3, "HIGHVOL", "MIDVOL")), index=P["c"].index).where(pct.notna())
    tr = np.log(P["c"]["BTC"]).diff(720)
    trend = pd.Series(np.where(tr > 0, "UPTREND", "DOWNTREND"), index=P["c"].index).where(tr.notna())
    return vol, trend
