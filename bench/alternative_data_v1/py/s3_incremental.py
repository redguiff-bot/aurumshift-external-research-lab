"""Incremental-information tests. Pre-specified (no tuning): see PROTOCOL below. Writes results/incremental.json + incremental.csv.
PROTOCOL (fixed before looking at results):
 decision time = end of trading day d. target_{d} = next trading day's (a) return, (b) |return|, (c) log(volume_{d+1}/mean volume d-6..d).
 baseline X_d = r_d..r_{d-6}, |r_d|,|r_{d-1}|,|r_{d-2}|, log(v_d/mean28 v), log rv7  [+ funding_d, dlog OI_d for BTC].
 feature = z-score (trailing window, current obs excluded) of the change over 1 week; usable from as-of date + conservative publication lag; forward-filled (limit 10 d).
 tests: in-sample OLS coef of feature added to baseline (Newey-West 5 lags); expanding-window OOS (first 50% train, refit every 5 d) DeltaR2_oos vs baseline with Clark-West p (one-sided);
        BH-FDR q=0.10 across ALL feature x target tests. CANDIDATE needs: BH pass AND in-sample NW p<0.05 AND DeltaR2_oos>0 AND same in-sample sign in both halves AND price-side R2adj<0.40 AND not price-by-construction.
 independence diagnostic: adj-R2 of the native (as-of-date) feature on a contemporaneous price-side matrix (1d ret, 7d ret, prior 7d ret, |7d ret|, log rv7, vol ratio, [funding7, dOI7]).
 naive_lag0 variant: same test with availability lag 0 to measure look-ahead inflation for scheduled/aggregated releases."""
import json, warnings
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
from lib import *
warnings.filterwarnings("ignore")
D = lambda n: pd.read_csv(os.path.join(DATA, n + ".csv"), index_col=0, parse_dates=True)
CAL = lambda idx: pd.date_range(idx.min(), idx.max(), freq="D")

# ------------------------------------------------------------------ assets
def asset_btc():
    p = D("btc_spot_1d"); f = D("btc_funding_daily"); o = D("btc_oi_metrics_daily") if os.path.exists(os.path.join(DATA, "btc_oi_metrics_daily.csv")) else None
    ex = pd.DataFrame(index=p.index); ex["funding"] = f.funding_day.reindex(p.index)
    if o is not None: ex["doi"] = np.log(o.oi).diff().reindex(p.index)
    return p.close, p.volume, ex
def asset_fut(nm):
    p = D(nm + "_fut_1d"); c = p.close; v = p.volume.replace(0, np.nan)
    return c, v, pd.DataFrame(index=p.index)
ASSETS = {"BTC": asset_btc, "GOLD": lambda: asset_fut("gold"), "CRUDE": lambda: asset_fut("crude"), "NATGAS": lambda: asset_fut("natgas")}

def build_target_baseline(c, v, ex, winsor):
    r = c.pct_change()
    if winsor: lo, hi = r.quantile([.005, .995]); r = r.clip(lo, hi)
    X = pd.DataFrame(index=c.index)
    for k in range(7): X[f"r{k}"] = r.shift(k)
    for k in range(3): X[f"a{k}"] = r.abs().shift(k)
    lv = np.log(v / v.rolling(28, min_periods=14).mean()); X["lv"] = lv
    X["lrv"] = np.log(r.rolling(7).std().clip(lower=1e-6))
    for col in ex.columns: X[col] = ex[col]
    Y = pd.DataFrame({"ret": r.shift(-1), "abs": r.abs().shift(-1), "vol": np.log(v.shift(-1) / v.rolling(7, min_periods=4).mean())}, index=c.index)
    X = X.replace([np.inf, -np.inf], np.nan); Y = Y.replace([np.inf, -np.inf], np.nan)
    return r, X, Y

def price_side(c, v, ex):
    cal = pd.date_range(c.index.min(), c.index.max(), freq="D"); cc = c.reindex(cal).ffill(); vv = v.reindex(cal).ffill()
    r1 = cc.pct_change(); r7 = cc.pct_change(7); P = pd.DataFrame({"r1": r1, "r7": r7, "r7p": r7.shift(7), "ar7": r7.abs(), "lrv": np.log(r1.rolling(7).std().clip(lower=1e-6)), "vr": np.log(vv.rolling(7).mean() / vv.rolling(28).mean())})
    for col in ex.columns:
        e = ex[col].reindex(cal); P[col + "7"] = e.rolling(7, min_periods=4).mean()
    return P

# ------------------------------------------------------------------ feature registry
# (id, asset, dataset, column, kind('daily'|'weekly'), transform('ldiff'|'diff'|'ldiff_sum7'|'lsum7_ratio'|'level'), publication lag days, price_by_construction, note)
F = []
def f(id, asset, ds, col, kind, tr, lag, byc=False, note="", cat=""): F.append(dict(id=id, asset=asset, ds=ds, col=col, kind=kind, tr=tr, lag=lag, byc=byc, note=note, cat=cat))
for col, tr, byc in (("n-transactions", "ldiff", False), ("n-unique-addresses", "ldiff", False), ("hash-rate", "ldiff", False), ("avg-block-size", "ldiff", False), ("mempool-size", "ldiff", False),
                     ("mempool-count", "ldiff", False), ("median-confirmation-time", "ldiff", False), ("transaction-fees", "ldiff", False), ("utxo-count", "ldiff", False),
                     ("transaction-fees-usd", "ldiff", True), ("estimated-transaction-volume-usd", "ldiff", True), ("cost-per-transaction", "ldiff", True), ("market-cap", "ldiff", True), ("miners-revenue", "ldiff", True)):
    f("bc_" + col, "BTC", "btc_onchain_blockchaininfo", col, "daily", tr, 2, byc, "USD-denominated => contains BTC price" if byc else "", "on-chain")
for col in ("avg_fees_sat_per_block", "avg_block_weight"):
    f("ms_" + col, "BTC", "btc_mempoolspace_blocks", col, "daily", "ldiff", 2, False, "", "mempool")
f("stable_mcap", "BTC", "stablecoin_total_mcap", "stable_mcap", "daily", "ldiff", 2, False, "USD-pegged supply; history recomputed by adapters", "on-chain")
f("defi_tvl_usd", "BTC", "defi_tvl_total", "defi_tvl_usd", "daily", "ldiff", 2, True, "TVL in USD includes token prices", "on-chain")
for col in ("lev_net_pct_oi", "am_net_pct_oi"): f("cftc_btc_" + col, "BTC", "cftc_btc_cme_tff", col, "weekly", "diff", 6, False, "as-of Tue, published Fri (+holiday risk)", "cftc")
f("cftc_btc_oi", "BTC", "cftc_btc_cme_tff", "oi", "weekly", "ldiff", 6, False, "", "cftc")
f("tga_btc", "BTC", "tga_balance", "tga_musd", "daily", "diff", 2, False, "DTS T+1", "gov")
f("gh_push", "BTC", "gh_crypto_dev_agg", "push", "daily", "lsum7_ratio", 2, False, "4 core repos; gaps in source", "dev")
f("gh_merged_pr", "BTC", "gh_crypto_dev_agg", "merged_pr", "daily", "lsum7_ratio", 2, False, "", "dev")
f("gh_actors", "BTC", "gh_crypto_dev_agg", "actors", "daily", "lsum7_ratio", 2, False, "", "dev")
f("gh_btc_stars", "BTC", "gh_crypto_dev_agg", "btc_stars", "daily", "lsum7_ratio", 2, False, "attention proxy", "dev")
f("fear_greed", "BTC", "fear_greed", "fng", "daily", "diff", 1, True, "composite incl. volatility/momentum/volume", "search/trend")
f("hn_btc", "BTC", "hn_bitcoin_daily", "hn_bitcoin_stories", "daily", "lsum7_ratio", 2, False, "", "social")
for col in ("Bitcoin", "Cryptocurrency"): f("wiki_" + col, "BTC", "wikipedia_pageviews", col, "daily", "lsum7_ratio", 2, False, "", "search/trend")
for col in ("toptrader_ls_pos", "ls_ratio", "taker_ls_vol"): f("bn_" + col, "BTC", "btc_oi_metrics_daily", col, "daily", "diff", 0, col == "taker_ls_vol", "taker buy/sell volume ratio is a volume derivative" if col == "taker_ls_vol" else "same-source as OI baseline", "exchange")
f("tga_gold", "GOLD", "tga_balance", "tga_musd", "daily", "diff", 2, False, "", "gov"); f("cftc_gold_mm", "GOLD", "cftc_gold_comex_disagg", "mm_net_pct_oi", "weekly", "diff", 6, False, "", "cftc")
f("wiki_gold", "GOLD", "wikipedia_pageviews", "Gold", "daily", "lsum7_ratio", 2, False, "", "search/trend")
f("cftc_wti_mm", "CRUDE", "cftc_wti_ice_disagg", "mm_net_pct_oi", "weekly", "diff", 6, False, "ICE WTI mm", "cftc")
f("eia_crude", "CRUDE", "eia_crude_stocks_ex_spr", "value", "weekly", "ldiff", 7, False, "WPSR Wed, conservative Thu-next", "energy")
for col in ("Strait of Hormuz", "Suez Canal", "Bab el-Mandeb Strait"): f("pw_" + col.split()[0] + "_" + col.split()[1], "CRUDE", "portwatch_chokepoints_tankers", col, "daily", "lsum7_ratio", 10, False, "AIS nowcast revised later", "shipping")
f("eia_gas", "NATGAS", "eia_natgas_storage_lower48", "value", "weekly", "ddiff", 7, False, "storage weekly change minus previous weekly change", "energy")
f("hdd_us5", "NATGAS", "weather_hdd_cdd_us5", "hdd_us5", "daily", "wx_anom", 7, False, "ERA5 reanalysis, NOT PIT: upper-bound test", "weather")
f("cdd_us5", "NATGAS", "weather_hdd_cdd_us5", "cdd_us5", "daily", "wx_anom", 7, False, "", "weather")

def native_feature(spec):
    p = os.path.join(DATA, spec["ds"] + ".csv")
    if not os.path.exists(p): return None
    d = D(spec["ds"])
    if spec["col"] not in d.columns: return None
    s = d[spec["col"]].astype(float).dropna(); s = s[~s.index.duplicated()]
    if len(s) < 30: return None
    tr = spec["tr"]
    if spec["kind"] == "weekly":
        w = 26
        if tr == "ldiff": ch = np.log(s).diff()
        elif tr == "diff": ch = s.diff()
        elif tr == "ddiff": ch = s.diff().diff()
    else:
        w = 90; cal = pd.date_range(s.index.min(), s.index.max(), freq="D")
        if spec["ds"] in ("tga_balance", "fear_greed", "stablecoin_total_mcap", "defi_tvl_total", "btc_onchain_blockchaininfo", "btc_mempoolspace_blocks", "portwatch_chokepoints_tankers", "wikipedia_pageviews", "weather_hdd_cdd_us5"):
            s = s.reindex(cal).ffill(limit=5)
        else: s = s.reindex(cal)   # keep gaps (GitHub, HN, Binance)
        if tr == "ldiff": ch = np.log(s.clip(lower=1e-9)).diff(7)
        elif tr == "diff": ch = s.diff(7)
        elif tr == "lsum7_ratio": s7 = s.rolling(7, min_periods=7).sum(); ch = np.log((s7 + 1) / (s.rolling(28, min_periods=28).sum().shift(7) / 4 + 1))
        elif tr == "wx_anom": ch = s.rolling(7, min_periods=7).mean() - s.rolling(7, min_periods=7).mean().shift(364)
    mu = ch.rolling(w, min_periods=max(10, w // 3)).mean().shift(1); sd = ch.rolling(w, min_periods=max(10, w // 3)).std().shift(1)
    z = ((ch - mu) / sd.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).clip(-5, 5)
    return z.dropna()

def to_daily(z, lag, kind, days):
    avail = z.copy(); avail.index = avail.index + pd.Timedelta(days=lag)
    avail = avail[~avail.index.duplicated(keep="last")]
    cal = pd.date_range(min(avail.index.min(), days.min()), days.max(), freq="D")
    return avail.reindex(cal).ffill(limit=10 if kind == "weekly" else 5).reindex(days)

# ------------------------------------------------------------------ stats
def nw_p(y, X, j):
    m = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5}); return m.params[j], m.tvalues[j], m.pvalues[j]
def ols(y, X): return np.linalg.lstsq(X, y, rcond=None)[0]
def oos(y, Xb, Xf, frac=0.5, step=5, min_train=200):
    n = len(y); s0 = max(int(n * frac), min_train); e1, e2, dd = [], [], []
    yy, XB, XF = y.values, Xb.values, Xf.values
    for t in range(s0, n, step):
        b1 = ols(yy[:t], XB[:t]); b2 = ols(yy[:t], XF[:t]); sl = slice(t, min(t + step, n))
        p1 = XB[sl] @ b1; p2 = XF[sl] @ b2; e1 += list(yy[sl] - p1); e2 += list(yy[sl] - p2); dd += list((yy[sl] - p1) ** 2 - (yy[sl] - p2) ** 2 + (p1 - p2) ** 2)
    e1, e2, dd = map(np.array, (e1, e2, dd))
    if len(dd) < 50: return None
    m = sm.OLS(dd, np.ones(len(dd))).fit(cov_type="HAC", cov_kwds={"maxlags": 5}); tcw = m.tvalues[0]
    return dict(dr2=float(1 - (e2 ** 2).sum() / (e1 ** 2).sum()), cw_t=float(tcw), cw_p=float(1 - stats.norm.cdf(tcw)), n_oos=len(dd))

def run_feature(spec, ctx, lag=None):
    z = native_feature(spec)
    if z is None: return {"id": spec["id"], "status": "NO_DATA"}
    c, v, ex, r, X, Y = ctx["c"], ctx["v"], ctx["ex"], ctx["r"], ctx["X"], ctx["Y"]
    lg = spec["lag"] if lag is None else lag
    fd = to_daily(z, lg, spec["kind"], X.index).rename("f")
    out = {"id": spec["id"], "asset": spec["asset"], "lag": lg, "byc": spec["byc"], "cat": spec["cat"], "note": spec["note"], "tests": {}}
    Xall = X.join(fd)
    # independence diagnostic on native dates
    P = ctx["P"]; zz = z.reindex(P.index).dropna(); Pm = P.reindex(zz.index).dropna(); zz = zz.reindex(Pm.index)
    if len(zz) > 60:
        m = sm.OLS(zz.values, sm.add_constant(Pm.values)).fit(); out["price_side_r2adj"] = float(m.rsquared_adj); out["n_indep"] = int(len(zz))
        out["corr_r1"] = float(np.corrcoef(zz, Pm.r1.reindex(zz.index).fillna(0))[0, 1]); out["corr_ar7"] = float(np.corrcoef(zz, Pm.ar7)[0, 1])
    for tn in ("ret", "abs", "vol"):
        d = Xall.join(Y[tn].rename("y")).replace([np.inf, -np.inf], np.nan).dropna()
        if len(d) < 250: out["tests"][tn] = {"status": "INSUFFICIENT_SAMPLE", "n": int(len(d))}; continue
        base = [cn for cn in X.columns]; Xb = sm.add_constant(d[base], has_constant="add"); Xf = Xb.join(d["f"])
        b, t, p = nw_p(d.y.values, Xf.values, Xf.shape[1] - 1)
        h = len(d) // 2; s1 = np.sign(nw_p(d.y.values[:h], Xf.values[:h], Xf.shape[1] - 1)[0]); s2 = np.sign(nw_p(d.y.values[h:], Xf.values[h:], Xf.shape[1] - 1)[0])
        o = oos(d.y, Xb, Xf)
        out["tests"][tn] = dict(n=int(len(d)), coef=float(b), nw_t=float(t), nw_p=float(p), sign_consistent=bool(s1 == s2), **(o or {"status": "OOS_TOO_SHORT"}))
    return out

def main():
    res = []; naive = []
    for an, loader in ASSETS.items():
        c, v, ex = loader(); r, X, Y = build_target_baseline(c, v, ex, winsor=an != "BTC"); P = price_side(c, v, ex)
        ctx = dict(c=c, v=v, ex=ex, r=r, X=X, Y=Y, P=P)
        for spec in [s for s in F if s["asset"] == an]:
            o = run_feature(spec, ctx); res.append(o); print(an, spec["id"], o.get("status", ""), {k: (round(x["dr2"] * 100, 3) if "dr2" in x else x.get("status")) for k, x in o.get("tests", {}).items()}, "R2p", round(o.get("price_side_r2adj", float("nan")), 3), flush=True)
            if spec["lag"] > 0 and o.get("tests"):
                naive.append(run_feature(spec, ctx, lag=0))
    # BH across all valid primary tests
    rows = [(o["id"], tn, tt["cw_p"]) for o in res for tn, tt in o.get("tests", {}).items() if "cw_p" in tt]
    ps = np.array([x[2] for x in rows]); order = np.argsort(ps); m = len(ps)
    adj = np.empty(m); run = 1.0
    for k in range(m - 1, -1, -1):
        i = order[k]; run = min(run, ps[i] * m / (k + 1)); adj[i] = run
    q = {(rows[i][0], rows[i][1]): float(adj[i]) for i in range(m)}
    for o in res:
        for tn, tt in o.get("tests", {}).items():
            if "cw_p" in tt: tt["bh_q"] = q[(o["id"], tn)]
    # classification
    for o in res:
        if o.get("status") == "NO_DATA": o["class"] = "NOT_TESTABLE_NO_DATA"; continue
        valid = {tn: t for tn, t in o["tests"].items() if "cw_p" in t}
        r2 = o.get("price_side_r2adj", np.nan)
        if not valid: o["class"] = "NOT_TESTABLE_INSUFFICIENT_SAMPLE"; continue
        if o["byc"] or (r2 == r2 and r2 >= 0.40): o["class"] = "PRICE_DERIVATIVE_ONLY_REJECT"; continue
        passing = [tn for tn, t in valid.items() if t["bh_q"] < 0.10 and t["nw_p"] < 0.05 and t["dr2"] > 0 and t["sign_consistent"]]
        o["passing_targets"] = passing
        o["class"] = "INCREMENTAL_INFORMATION_CANDIDATE" if passing else ("PRICE_LINKED_PARTIAL_NO_INCREMENTAL" if (r2 == r2 and r2 >= 0.15) else "INDEPENDENT_NO_INCREMENTAL_EVIDENCE")
    jdump({"features": res, "naive_lag0": naive, "n_tests": m, "protocol": __doc__}, "incremental.json")
    flat = []
    for o in res:
        for tn, t in o.get("tests", {}).items(): flat.append({"id": o["id"], "asset": o.get("asset"), "cat": o.get("cat"), "lag": o.get("lag"), "class": o["class"], "price_r2adj": o.get("price_side_r2adj"), "target": tn, **{k: t.get(k) for k in ("n", "coef", "nw_t", "nw_p", "dr2", "cw_p", "bh_q", "sign_consistent", "status")}})
    pd.DataFrame(flat).to_csv(os.path.join(RES, "incremental.csv"), index=False)
    from collections import Counter; print(Counter(o["class"] for o in res))
if __name__ == "__main__": main()
