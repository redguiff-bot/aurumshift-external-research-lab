import warnings; warnings.filterwarnings("ignore")
import json, os, numpy as np, pandas as pd, lib
rows = {}; A = lib.CORE + lib.HOLD
for a in A:
    k = pd.read_parquet(f"{lib.D}/{a}_kl.parquet"); f = pd.read_parquet(f"{lib.D}/{a}_fund.parquet"); m = pd.read_parquet(f"{lib.D}/{a}_metrics5m.parquet"); p = pd.read_parquet(f"{lib.D}/{a}_prem.parquet")
    ki = k.reindex(lib.IDX); r = dict(kl_first=str(k.index[0]), kl_missing_bars=int(ki.close.isna().sum()), zero_vol_bars=int((k.volume == 0).sum()), fund_rows=len(f), fund_intervals_h=sorted(f.interval_h.unique().tolist()), prem_zero_vol_note="premium index klines carry no volume", metrics_rows=len(m), metrics_first=str(m.index[0]),
                                       metrics_5min_gap_share=float((m.index.to_series().diff().dropna() > pd.Timedelta("5min")).mean()), oi_zero_rows=int((m.sum_open_interest == 0).sum()))
    if os.path.exists(f"{lib.D}/{a}_hl_fund.parquet"): h = pd.read_parquet(f"{lib.D}/{a}_hl_fund.parquet"); r["hl_first"] = str(h.index[0]); r["hl_rows"] = len(h)
    if os.path.exists(f"{lib.D}/{a}_cb.parquet"): c = pd.read_parquet(f"{lib.D}/{a}_cb.parquet"); r["cb_rows"] = len(c); r["cb_first"] = str(c.index[0]); r["cb_missing_hours_2025_01_to_2026_08"] = int(c.reindex(pd.date_range("2025-01-01", "2026-08-31 23:00", freq="h")).close.isna().sum())
    rows[a] = r
for d in ("BTC", "ETH"):
    v = pd.read_parquet(f"{lib.D}/{d}_dvol.parquet"); rows[d]["dvol_rows"] = len(v); rows[d]["dvol_first"] = str(v.index[0]); rows[d]["dvol_last"] = str(v.index[-1])
# cross-venue price sanity: Binance perp vs Coinbase spot hourly close correlation of returns / median abs diff
xs = {}
for a in ("BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "LINK", "AVAX", "LTC"):
    b = pd.read_parquet(f"{lib.D}/{a}_kl.parquet").close; c = pd.read_parquet(f"{lib.D}/{a}_cb.parquet").close
    j = pd.concat([b, c], axis=1, keys=["bn", "cb"]).dropna().loc["2025-01-01":]; rr = np.log(j).diff().dropna()
    xs[a] = dict(ret_corr=float(rr.bn.corr(rr.cb)), median_abs_close_diff_bps=float(((j.bn / j.cb - 1).abs().median()) * 1e4), n=len(j))
json.dump(dict(per_asset=rows, cross_venue_bn_perp_vs_cb_spot=xs), open("../results/data_audit.json", "w"), indent=1)
print(json.dumps(xs)); print(rows["BTC"]); print(rows["ADA"]); print({a: rows[a]["kl_missing_bars"] for a in A})
