"""FX / gold / commodity: public OHLC ONLY (Yahoo chart endpoint, unofficial) -> volatility scaling, range proxies, session-gap sensitivity.
NO quote/book data => execution-cost models needing quotes are MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA for these classes."""
import requests, json, os, sys, numpy as np, pandas as pd
ROOT = os.path.join(os.path.dirname(__file__), ".."); sys.path.insert(0, f"{ROOT}/models")
import models as M
SYMS = {"XAU (COMEX GC=F futures)": "GC=F", "EURUSD": "EURUSD=X", "USDJPY": "USDJPY=X", "WTI (CL=F futures)": "CL=F", "BTC-USD (control)": "BTC-USD"}
out = {}
for name, sym in SYMS.items():
    j = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}", params=dict(interval="1h", range="6mo"), headers={"User-Agent": "Mozilla/5.0"}, timeout=20).json()
    r = j["chart"]["result"][0]; q = r["indicators"]["quote"][0]
    df = pd.DataFrame(dict(t=pd.to_datetime(r["timestamp"], unit="s"), O=q["open"], H=q["high"], L=q["low"], C=q["close"], V=q["volume"])).dropna(subset=["C", "H", "L", "O"])
    df.to_csv(f"{ROOT}/data/ohlc/{sym.replace('=', '_')}_1h.csv", index=False)
    ret = np.log(df.C).diff()
    dt_h = df.t.diff().dt.total_seconds() / 3600
    within = ret[(dt_h > 0.9) & (dt_h < 1.1)]
    sig_h = within.std()                                    # per-hour log-return sd (contiguous hours only)
    sig_sqrt_s = sig_h / np.sqrt(3600) * 1e4                # bps / sqrt(s)
    gaps = ret[dt_h > 3]                                    # session gaps (weekend/rollover/holiday)
    cs, neg = M.corwin_schultz(df.H.values, df.L.values)
    ar = M.abdi_ranaldo(df.C.values, df.H.values, df.L.values)
    out[name] = dict(symbol=sym, n_bars=int(len(df)), t0=str(df.t.iloc[0]), t1=str(df.t.iloc[-1]), sigma_hour_bps=float(sig_h * 1e4), sigma_bps_sqrt_s=float(sig_sqrt_s),
                     annualised_vol_pct=float(sig_h * np.sqrt(24 * 365) * 100) if "BTC" in name else float(sig_h * np.sqrt(24 * 252) * 100),
                     hours_per_week_present=float(len(df) / (len(df.t.dt.to_period("W").unique()))),
                     n_gaps_gt3h=int(len(gaps)), gap_abs_bps_mean=float(gaps.abs().mean() * 1e4) if len(gaps) else None, gap_abs_bps_p95=float(gaps.abs().quantile(.95) * 1e4) if len(gaps) else None,
                     gap_over_sigma_hour=float(gaps.abs().mean() / sig_h) if len(gaps) else None,
                     latency_sd_bps={str(L): float(sig_sqrt_s * np.sqrt(L)) for L in (0.5, 2, 10, 60)},
                     hl_range_proxy_bps_1h=float(M.hl_range_proxy(df.H.values, df.L.values) * 1e4), corwin_schultz_1h_bps=float(cs * 1e4), cs_zero_frac=float(neg), abdi_ranaldo_1h_bps=float(ar * 1e4),
                     volume_available=bool(np.nansum(df.V.values) > 0))
json.dump(out, open(f"{ROOT}/results/fx_gold_ohlc.json", "w"), indent=1)
print(pd.DataFrame(out).T[["n_bars", "hours_per_week_present", "sigma_bps_sqrt_s", "annualised_vol_pct", "n_gaps_gt3h", "gap_abs_bps_mean", "gap_over_sigma_hour", "corwin_schultz_1h_bps", "abdi_ranaldo_1h_bps", "volume_available"]].round(3).to_string())
