"""Funding / borrow / roll: what can actually be observed from free public endpoints."""
import glob, zipfile, io, json, time, os, requests, numpy as np, pandas as pd
D = os.path.join(os.path.dirname(__file__), "..", "data", "vision"); R = os.path.join(os.path.dirname(__file__), "..", "results")
out = {}
# ---- Binance Vision funding history (USD-M) ----
fr = {}
for sym in ["BTCUSDT", "ETHUSDT"]:
    dfs = [pd.read_csv(zipfile.ZipFile(f).open(zipfile.ZipFile(f).namelist()[0])) for f in sorted(glob.glob(f"{D}/fund_{sym}_2026-0*.zip"))]
    df = pd.concat(dfs).sort_values("calc_time").reset_index(drop=True)
    df["t"] = pd.to_datetime(df.calc_time, unit="ms")
    fr[sym] = df
    r = df.last_funding_rate.values * 1e4                     # bps per 8h period
    hold = {}
    for days in (1, 7, 30):
        k = days * 3
        roll = pd.Series(r).rolling(k).sum().dropna().values
        hold[f"{days}d_long_pays_bps"] = dict(mean=float(roll.mean()), p05=float(np.percentile(roll, 5)), p50=float(np.percentile(roll, 50)),
                                              p95=float(np.percentile(roll, 95)), min=float(roll.min()), max=float(roll.max()))
    out[f"binance_vision_{sym}"] = dict(n=int(len(df)), t0=str(df.t.iloc[0]), t1=str(df.t.iloc[-1]),
        interval_hours_values=sorted(df.funding_interval_hours.unique().tolist()), mean_bps_per_8h=float(r.mean()), sd=float(r.std()),
        frac_positive=float((r > 0).mean()), annualised_mean_pct=float(r.mean() * 3 * 365 / 100), hold=hold,
        gaps_not_8h=int((np.diff(df.calc_time.values) > 8.1 * 3600e3).sum()))
# ---- OKX funding history, cross-venue difference ----
def okx_hist(inst, pages=5):
    rows = []; after = None
    for _ in range(pages):
        p = dict(instId=inst, limit=100)
        if after: p["after"] = after
        j = requests.get("https://www.okx.com/api/v5/public/funding-rate-history", params=p, timeout=10).json()
        if not j.get("data"): break
        rows += j["data"]; after = j["data"][-1]["fundingTime"]; time.sleep(0.3)
    return pd.DataFrame(rows)
for inst, sym in [("BTC-USDT-SWAP", "BTCUSDT"), ("ETH-USDT-SWAP", "ETHUSDT")]:
    o = okx_hist(inst); o["t"] = pd.to_datetime(o.fundingTime.astype(np.int64), unit="ms"); o["realized_bps"] = o.realizedRate.astype(float) * 1e4
    o["fund_bps"] = o.fundingRate.astype(float) * 1e4
    b = fr[sym].copy(); b["tk"] = b.t.dt.round("h"); o["tk"] = o.t.dt.round("h")
    m = o.merge(b[["tk", "last_funding_rate"]], on="tk"); m["b_bps"] = m.last_funding_rate * 1e4
    out[f"okx_{inst}"] = dict(n=int(len(o)), t0=str(o.t.min()), t1=str(o.t.max()), mean_realized_bps=float(o.realized_bps.mean()),
        realized_vs_announced_maxabs_diff_bps=float((o.realized_bps - o.fund_bps).abs().max()), n_overlap_binance=int(len(m)),
        corr_okx_binance=float(np.corrcoef(m.realized_bps, m.b_bps)[0, 1]) if len(m) > 5 else None,
        mean_abs_diff_bps=float((m.realized_bps - m.b_bps).abs().mean()) if len(m) else None,
        binance_minus_okx_mean_bps=float((m.b_bps - m.realized_bps).mean()) if len(m) else None)
cur = requests.get("https://www.okx.com/api/v5/public/funding-rate", params=dict(instId="BTC-USDT-SWAP"), timeout=10).json()["data"][0]
out["okx_current_fields"] = {k: cur[k] for k in cur if k in ("fundingRate", "nextFundingRate", "settFundingRate", "settState", "method", "formulaType", "maxFundingRate", "minFundingRate", "interestRate", "premium")}
# ---- OKX public margin borrow rates ----
b = requests.get("https://www.okx.com/api/v5/public/interest-rate-loan-quota", timeout=10).json()["data"][0]["basic"]
out["okx_public_borrow_basic"] = {x["ccy"]: dict(rate=x["rate"], quota=x["quota"]) for x in b if x["ccy"] in ("BTC", "ETH", "USDT", "USDC", "SOL")}
out["okx_public_borrow_note"] = "rate unit (per hour vs per day) is a DOCUMENTED_CLAIM to verify; endpoint gives venue-quoted base rate, tier/VIP and realised interest not observable"
# ---- Roll: OKX dated inverse futures curve ----
ins = requests.get("https://www.okx.com/api/v5/public/instruments", params=dict(instType="FUTURES", instFamily="BTC-USD"), timeout=10).json()["data"]
tk = requests.get("https://www.okx.com/api/v5/market/tickers", params=dict(instType="FUTURES", instFamily="BTC-USD"), timeout=10).json()["data"]
idx = float(requests.get("https://www.okx.com/api/v5/market/index-tickers", params=dict(instId="BTC-USD"), timeout=10).json()["data"][0]["idxPx"])
now_ms = int(time.time() * 1000)
tkd = {t["instId"]: t for t in tk}
curve = []
for i in sorted(ins, key=lambda x: int(x["expTime"])):
    t = tkd.get(i["instId"])
    if not t: continue
    bid, ask = float(t["bidPx"] or 0), float(t["askPx"] or 0)
    if not bid or not ask: continue
    mid = (bid + ask) / 2; dte = (int(i["expTime"]) - now_ms) / 86400e3
    curve.append(dict(inst=i["instId"], dte=dte, mid=mid, spread_bps=(ask - bid) / mid * 1e4, basis_bps=(mid / idx - 1) * 1e4,
                      annualised_basis_pct=((mid / idx - 1) * 365 / dte) * 100, vol24h_ct=t["vol24h"]))
rolls = []
for a, b_ in zip(curve[:-1], curve[1:]):
    cal = (b_["mid"] / a["mid"] - 1) * 1e4     # calendar spread paid when rolling long from a to b (bps of price)
    rolls.append(dict(frm=a["inst"], to=b_["inst"], calendar_spread_bps=cal, leg_half_spreads_bps=a["spread_bps"] / 2 + b_["spread_bps"] / 2,
                      roll_all_in_bps_long=cal + a["spread_bps"] / 2 + b_["spread_bps"] / 2, days_between=b_["dte"] - a["dte"]))
out["okx_btcusd_dated_curve"] = dict(index=idx, curve=curve, rolls=rolls)
json.dump(out, open(f"{R}/funding_borrow_roll.json", "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in out.items() if k.startswith("binance") or k.startswith("okx_BTC")}, indent=1, default=str)[:3500])
print(pd.DataFrame(curve).round(2)); print(pd.DataFrame(rolls).round(2)); print(out["okx_public_borrow_basic"])
