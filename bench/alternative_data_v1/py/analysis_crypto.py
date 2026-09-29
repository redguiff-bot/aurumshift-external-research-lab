"""Incremental-information test of alternative-data blocks over a price/volume/volatility/funding/OI baseline.
Pre-declared decision rules (written before running; see 07_INCREMENTAL_INFORMATION.md):
  INCREMENTAL_CANDIDATE  : HAC-Wald p<0.05 on the block in the baseline+block model for >=1 target, BH-FDR q<0.10 across all
                           non-control tests, AND expanding-window OOS MSE gain >0 with one-sided DM p<0.10, AND block
                           coefficient sign-stable across two halves, AND price-reactivity R2 < 0.40.
  PRICE_DERIVATIVE_ONLY  : price-reactivity R2 (same-day price+range+5 lags) >= 0.40 OR univariate predictive content
                           disappears once baseline is included (subsumed), AND not INCREMENTAL_CANDIDATE.
  INDEPENDENT_NO_EVIDENCE: neither (informationally distinct from price, but no predictive evidence -> NOT negative evidence).
"""
import os, json, warnings, numpy as np, pandas as pd
import statsmodels.api as sm
from scipy import stats
from panel import *
warnings.filterwarnings("ignore")
RES = os.path.join(D, "..", "results"); os.makedirs(RES, exist_ok=True)
START = pd.Timestamp("2021-01-01")   # CM 2020 rows are back-filled years later (see PIT report)
MIN_TRAIN, STEP, HAC = 400, 10, 5

def hac_wald(y, X, cols):
    Xc = sm.add_constant(X, has_constant="add")
    m = sm.OLS(y, Xc).fit(cov_type="HAC", cov_kwds={"maxlags": HAC})
    idx = [list(Xc.columns).index(c) for c in cols]
    R = np.zeros((len(idx), Xc.shape[1]));
    for i, j in enumerate(idx): R[i, j] = 1
    w = m.wald_test(R, use_f=False, scalar=True)
    return float(w.pvalue), m

def oos(y, X0, X1):
    n = len(y); e0 = np.full(n, np.nan); e1 = np.full(n, np.nan); em = np.full(n, np.nan)
    for s in range(MIN_TRAIN, n, STEP):
        te = slice(s, min(n, s + STEP)); tr = slice(0, s)
        for X, e in ((X0, e0), (X1, e1)):
            A = np.c_[np.ones(s), X[tr]]; b = np.linalg.lstsq(A, y[tr], rcond=None)[0]
            e[te] = y[te] - np.c_[np.ones(te.stop - te.start), X[te]] @ b
        em[te] = y[te] - y[tr].mean()
    ok = ~np.isnan(e0)
    d = (e0 ** 2 - e1 ** 2)[ok]
    dm = d.mean(); v = np.var(d, ddof=0)
    for L in range(1, HAC + 1):
        w = 1 - L / (HAC + 1); v += 2 * w * np.mean((d[L:] - dm) * (d[:-L] - dm))
    t = dm / np.sqrt(max(v, 1e-30) / len(d))
    mse0, mse1, msem = np.mean(e0[ok] ** 2), np.mean(e1[ok] ** 2), np.mean(em[ok] ** 2)
    return dict(oos_n=int(ok.sum()), oos_r2_base=1 - mse0 / msem, oos_r2_full=1 - mse1 / msem, oos_gain_pct=100 * (1 - mse1 / mse0), dm_t=float(t), dm_p_onesided=float(1 - stats.norm.cdf(t)))

def r2(y, X):
    m = sm.OLS(y, sm.add_constant(X, has_constant="add")).fit(); return m.rsquared_adj

def react(blk_raw, raw):
    """price reactivity of the block measured on OBSERVATION dates: same-day ret, |ret|, range + 5 lags of ret/range."""
    P = pd.concat([raw.r, raw.absr, raw.lr] + [raw.r.shift(i) for i in range(1, 6)] + [raw.lr.shift(i) for i in range(1, 6)] + [raw.absr.shift(i) for i in range(1, 6)], axis=1)
    P.columns = [f"p{i}" for i in range(P.shape[1])]
    Pp = P.iloc[:, 3:]  # past only (lags >=1)
    out = {}
    for tag, PP in (("ctmp", P), ("past", Pp)):
        v = []
        for c in blk_raw.columns:
            d = pd.concat([blk_raw[c].rename("x"), PP], axis=1).dropna(); d = d[d.index >= START]
            if len(d) < 300: continue
            v.append(r2(d.x.values, d.drop(columns="x").values))
        out[f"react_{tag}"] = max(v) if v else np.nan
    return out

def evaluate(name, blk, blk_raw, xb, tg, raw, price_only, asset, klass):
    rows = []
    for tgt in ["ret", "lrange", "absret"]:
        d = pd.concat([tg[tgt].rename("y"), xb, blk], axis=1).dropna(); d = d[d.index >= START]
        if len(d) < 800: rows.append(dict(cand=name, asset=asset, target=tgt, n=len(d), status="INSUFFICIENT_N")); continue
        y = d.y.values; Xb = d[xb.columns].values; Xa = d.drop(columns="y").values; bc = list(blk.columns)
        p_incr, m1 = hac_wald(d.y, d.drop(columns="y"), bc)
        p_uni, _ = hac_wald(d.y, d[bc], bc)
        o = oos(y, Xb, Xa)
        h = len(d) // 2; cs = []
        for sl in (slice(0, h), slice(h, None)):
            mm = sm.OLS(d.y.values[sl], sm.add_constant(d.drop(columns="y").values[sl])).fit()
            cs.append(mm.params[-len(bc):] * d[bc].values[sl].std(0))
        cos = float(np.dot(cs[0], cs[1]) / (np.linalg.norm(cs[0]) * np.linalg.norm(cs[1]) + 1e-12))
        red_base = max(r2(d[c].values, d[xb.columns].values) for c in bc)
        red_price = max(r2(d[c].values, d[price_only].values) for c in bc)
        rows.append(dict(cand=name, asset=asset, target=tgt, n=len(d), first=str(d.index[0].date()), last=str(d.index[-1].date()), klass=klass,
                         p_incr=p_incr, p_univ=p_uni, sign_cos=cos, red_base=red_base, red_price_lagged=red_price, **o, **react(blk_raw, raw)))
    return rows

def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); q = np.empty(n)
    q[o] = np.minimum.accumulate((p[o] * n / (np.arange(n) + 1))[::-1])[::-1]
    return np.minimum(q, 1)

def cftc_block():
    c = rd("cftc_tff_btc_cme.csv"); c["rep"] = pd.to_datetime(c.report_date_as_yyyy_mm_dd).dt.normalize()
    c["created"] = pd.to_datetime(c[":created_at"], utc=True).dt.tz_localize(None)
    rule = c.rep + pd.Timedelta(days=3, hours=19, minutes=30)  # Tuesday as-of -> Friday 15:30 ET (~19:30 UTC; DST ignored)
    c["avail"] = np.where(c.created > pd.Timestamp("2022-09-14"), np.maximum(rule, c.created), rule)
    c["avail"] = pd.to_datetime(c["avail"])
    oi = c.open_interest_all.astype(float)
    f = pd.DataFrame({"lev_net": (c.lev_money_positions_long.astype(float) - c.lev_money_positions_short.astype(float)) / oi,
                      "am_net": (c.asset_mgr_positions_long.astype(float) - c.asset_mgr_positions_short.astype(float)) / oi,
                      "dl_net": (c.dealer_positions_long_all.astype(float) - c.dealer_positions_short_all.astype(float)) / oi})
    out = pd.DataFrame(index=c.avail.dt.normalize() + pd.Timedelta(days=1))  # first decision day at/after release
    z = {}
    for k in f.columns:
        s = f[k].values; sr = pd.Series(s)
        z[f"cftc_{k}_z"] = ((sr - sr.rolling(52).mean()) / sr.rolling(52).std()).values
        z[f"cftc_{k}_dw"] = sr.diff().values
    out = pd.DataFrame(z, index=out.index); out = out[~out.index.duplicated(keep="last")]
    raw = out.copy()
    daily = out.reindex(pd.date_range(out.index.min(), pd.Timestamp.utcnow().tz_localize(None).normalize())).ffill()
    return daily[[c for c in daily.columns if c.startswith("cftc_lev") or c.startswith("cftc_am")]], raw

def build_candidates(asset):
    sym = f"{asset}USDT"; cmf = f"cm_{asset.lower()}.csv"
    cm = rd(cmf, index_col=0, parse_dates=True)
    C = {}
    def add(name, blk, klass, raw_series_for_react=None):
        C[name] = (blk, klass)
    net = (cm.FlowInExUSD - cm.FlowOutExUSD)
    scale = (cm.FlowInExUSD + cm.FlowOutExUSD).rolling(30).mean()
    b = pd.DataFrame({"cmflow_net_scaled": net / scale, "cmflow_vol_z": zs(np.log(cm.FlowInExUSD + cm.FlowOutExUSD))})
    C["cm_exchange_flows"] = (b, 2, "on-chain exchange flows (labelled clusters)")
    sply = np.log(cm.SplyExUSD)  # USD-denominated supply is price-contaminated -> use native-like change in share of supply
    C["cm_active_addresses"] = (block("cm_adr", cm.AdrActCnt, 0)[["cm_adr_z", "cm_adr_d1"]], 2, "on-chain activity")
    C["cm_tx_count"] = (block("cm_tx", cm.TxCnt, 0), 2, "on-chain activity")
    if asset == "BTC":
        C["cm_hashrate"] = (block("cm_hr", cm.HashRate, 0), 2, "mining")
        C["cm_mvrv_CONTROL_price_derived"] = (block("cm_mvrv", cm.CapMVRVCur, 0, kind="lin"), 2, "control")
    bc = rd("blockchain_com.csv", index_col=0, parse_dates=True)
    if asset == "BTC":
        C["bc_tx_count"] = (block("bc_tx", bc["n-transactions"], 0), 2, "on-chain activity (lookahead-risk source)")
        C["bc_mempool_size"] = (block("bc_mp", bc["mempool-size"].clip(lower=1), 0), 2, "mempool congestion")
        C["bc_tx_fees_btc"] = (block("bc_fee", bc["transaction-fees"].clip(lower=1e-3), 0), 2, "fees")
        C["bc_unique_addresses"] = (block("bc_ua", bc["n-unique-addresses"], 0), 2, "on-chain activity")
        dv = rd("deribit_dvol_1d.csv", index_col=0, parse_dates=True) if os.path.exists(os.path.join(D, "deribit_dvol_1d.csv")) else None
        if dv is not None: C["deribit_dvol_CONTROL_implied_vol"] = (block("dvol", dv.c, 0), 1, "control")
        cd, craw = cftc_block(); C["cftc_tff_btc_cme"] = (cd, 0, "positioning")
    st = rd("llama_stables.csv", index_col=0, parse_dates=True).stable_total_usd
    sb = pd.DataFrame({"stab_d1": np.log(st).diff(), "stab_d7": np.log(st).diff(7)}); C["llama_stablecoin_supply"] = (sb, 2, "stablecoin liquidity (restated history)")
    dx = rd("llama_dex.csv", index_col=0, parse_dates=True).dex_vol_usd
    C["llama_dex_volume"] = (block("dex", dx.clip(lower=1), 0), 2, "DeFi activity (USD, price-linked)")
    fg = rd("fng.csv", index_col=0, parse_dates=True).fng.astype(float)
    C["alternative_me_fear_greed"] = (pd.DataFrame({"fng_lvl": (fg - 50) / 25, "fng_d1": fg.diff() / 10}), 1, "sentiment composite")
    tga = rd("treasury_tga.csv"); tga = pd.Series(pd.to_numeric(tga.open_today_bal, errors="coerce").values, index=pd.to_datetime(tga.record_date)); tga = tga[tga > 0]
    C["treasury_tga_liquidity"] = (block("tga", tga, 0), 3, "public gov liquidity")
    rr = rd("nyfed_rrp.csv"); rr = pd.Series(pd.to_numeric(rr.totalAmtAccepted, errors="coerce").values / 1e9, index=pd.to_datetime(rr.operationDate)).sort_index()
    rr = rr[~rr.index.duplicated()].asfreq("D").ffill(limit=4)
    b = pd.DataFrame({"rrp_z": zs(np.log1p(rr)), "rrp_d1": np.log1p(rr).diff()}); C["nyfed_reverse_repo"] = (b, 1, "public gov liquidity")
    for art in ["Bitcoin" if asset == "BTC" else "Ethereum"]:
        fn = f"wiki_{art}.csv"
        if os.path.exists(os.path.join(D, fn)):
            C[f"wikipedia_pageviews_{art}"] = (block("wiki", rd(fn, index_col=0, parse_dates=True).iloc[:, 0], 0), 2, "attention")
    for fn in sorted(os.listdir(D)):
        if fn.startswith("npm_") and fn.endswith(".csv") and asset == ("ETH" if "ethers" in fn or "web3.csv" in fn else "BTC" if "bitcoinjs" in fn else "ETH"):
            s = rd(fn, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
            C[f"npm_downloads_{fn[4:-4]}"] = (block("npm", s.clip(lower=1), 0), 2, "developer ecosystem")
    # public exchange positioning stats (same venue as baseline OI/funding)
    xb, tg, po, raw, df = baseline(sym)
    ls = pd.DataFrame({"lsr_all_z": zs(np.log(df.lsr_all)), "lsr_top_pos_z": zs(np.log(df.lsr_top_pos)), "taker_z": zs(np.log(df.taker_ratio))})
    C["binance_um_positioning_ratios"] = (ls, 1, "exchange positioning (public)")
    # controls
    rng = np.random.default_rng(7); idx = df.index
    C["CONTROL_noise_A"] = (pd.DataFrame(rng.standard_normal((len(idx), 2)), index=idx, columns=["nA1", "nA2"]), 1, "control")
    C["CONTROL_noise_B"] = (pd.DataFrame(rng.standard_normal((len(idx), 2)), index=idx, columns=["nB1", "nB2"]), 1, "control")
    C["CONTROL_price_derived_drawdown_mom"] = (pd.DataFrame({"dd60": np.log(df.c / df.c.rolling(60).max()), "mom30": np.log(df.c / df.c.shift(30))}, index=idx), 1, "control")
    return C, (xb, tg, po, raw, df)

def main():
    allrows = []
    for asset in ["BTC", "ETH"]:
        C, (xb, tg, po, raw, df) = build_candidates(asset)
        for name, (blk, lag, klass) in C.items():
            blk = blk.copy(); blk.index = pd.to_datetime(blk.index)
            lagged_blk = blk.apply(lambda c: lagged(c, lag)).reindex(xb.index)
            raw_blk = blk.copy()
            r = evaluate(name, lagged_blk, raw_blk.reindex(raw.index), xb, tg, raw, po, asset, dict(lag=lag, klass=klass))
            for x in r: x["lag_days"] = lag; x["family"] = klass
            allrows += r
            print(asset, name, [(x["target"], round(x.get("p_incr", np.nan), 3)) for x in r], flush=True)
    # sensitivity: optimistic availability (one day less lag) for sources whose lag was set conservatively
    for asset in ["BTC", "ETH"]:
        C, (xb, tg, po, raw, df) = build_candidates(asset)
        for name, (blk, lag, klass) in C.items():
            if lag >= 2 and not name.startswith("CONTROL"):
                blk = blk.copy(); blk.index = pd.to_datetime(blk.index)
                lb = blk.apply(lambda c: lagged(c, lag - 1)).reindex(xb.index)
                r = evaluate(name, lb, blk.reindex(raw.index), xb, tg, raw, po, asset, dict(lag=lag - 1))
                for x in r: x["lag_days"] = lag - 1; x["family"] = klass; x["sens"] = "optimistic_lag"
                allrows += r
    R = pd.DataFrame(allrows)
    R["is_control"] = R.cand.str.contains("CONTROL")
    R["sens"] = R.get("sens").fillna("primary") if "sens" in R else "primary"
    ok = R.p_incr.notna() & ~R.is_control & (R.sens == "primary")
    R.loc[ok, "q_bh"] = bh(R.loc[ok, "p_incr"].values)
    R.to_csv(os.path.join(RES, "incremental_results_no_calendar.csv" if NO_CAL else "incremental_results.csv"), index=False)
    print("saved", len(R))

if __name__ == "__main__":
    main()
