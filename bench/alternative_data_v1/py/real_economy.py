"""Real-economy tests: EIA inventories (crude, gas storage) vs spot returns; CPC weather anomaly; IMF PortWatch chokepoints.
Timing is rule-based (EIA WPSR Wed 10:30 ET, gas storage Thu 10:30 ET) because bulk data carry NO per-row publication
stamps -> historical rows are LOOKAHEAD_RISK by mission definition; results are upper-bound evidence, flagged."""
import os, io, json, zipfile, time, warnings, numpy as np, pandas as pd, requests
import statsmodels.api as sm
from analysis_crypto import hac_wald, oos, r2, bh
from h import UA
warnings.filterwarnings("ignore")
D = os.path.join(os.path.dirname(__file__), "..", "data"); RES = os.path.join(D, "..", "results")

def eia(zipname, ids):
    z = zipfile.ZipFile(os.path.join(D, "raw", zipname)); out = {}
    for line in z.open(z.namelist()[0]):
        try: o = json.loads(line)
        except Exception: continue
        if o.get("series_id") in ids:
            out[o["series_id"]] = pd.Series({pd.to_datetime(a, format="%Y%m%d"): b for a, b in o["data"] if b is not None}).sort_index()
            out[o["series_id"] + "_updated"] = o.get("last_updated")
    return out

def seasonal_surprise(s_delta, years=5):
    """delta minus mean of same-week deltas in previous `years` years (uses only past data), scaled by trailing 104w std."""
    df = pd.DataFrame({"d": s_delta}); df["wk"] = df.index.isocalendar().week.values; df["yr"] = df.index.year
    sur = []
    for i, (t, row) in enumerate(df.iterrows()):
        past = df[(df.wk == row.wk) & (df.yr < row.yr) & (df.yr >= row.yr - years)].d
        sur.append(row.d - past.mean() if len(past) >= 3 else np.nan)
    s = pd.Series(sur, index=df.index)
    return s / s.rolling(104, min_periods=52).std().shift(1)

def event_test(name, price, surprise, release_offset_days, extra=None, start="2007-01-01", end="2100-01-01"):
    """Regress spot log-return on next trading day after (or on) release, with baseline = lagged returns/vol.
    tgt0 = release-day return (information-arrival check, contemporaneous), tgt1 = next trading day (PIT-safe)."""
    r = np.log(price).diff().dropna()
    lo_, hi_ = r.quantile(0.005), r.quantile(0.995); r = r if os.environ.get('ALT_NO_WINSOR') == '1' else r.clip(lo_, hi_)   # winsorise 0.5%/99.5% (2020 oil dislocation dominates squared errors)
    rows = []
    rel = surprise.dropna().copy(); rel.index = rel.index + pd.Timedelta(days=release_offset_days)
    for tag, shift in (("release_day", 0), ("next_day", 1)):
        recs = []
        for t, s in rel.items():
            tt = r.index[r.index.get_indexer([t], method="bfill")[0]] if t <= r.index[-1] else None
            if tt is None: continue
            i = r.index.get_loc(tt) + shift
            if i >= len(r) or i < 25: continue
            d = r.index[i]
            base = r.iloc[:i]  # info before day d ("release_day": before market moves that day -- see caveat)
            recs.append(dict(date=d, y=r.iloc[i], s=s, r1=base.iloc[-1], r5=base.iloc[-5:].mean(), vol20=np.log(base.iloc[-20:].abs().mean() + 1e-6), absy=abs(r.iloc[i])))
        E = pd.DataFrame(recs).set_index("date"); E = E[(E.index >= start) & (E.index <= end)].dropna()
        for tgt in ("y", "absy"):
            X0 = E[["r1", "r5", "vol20"]]; X1 = E[["r1", "r5", "vol20", "s"]]
            p_incr, m = hac_wald(E[tgt], X1, ["s"]); p_uni, mu = hac_wald(E[tgt], E[["s"]], ["s"])
            o = oos(E[tgt].values, X0.values, X1.values) if len(E) > 300 else {}
            rows.append(dict(cand=name, target=f"{tag}:{tgt}", n=len(E), first=str(E.index[0].date()), last=str(E.index[-1].date()),
                             coef_s=float(m.params["s"]), t_s=float(m.tvalues["s"]), p_incr=p_incr, p_univ=p_uni,
                             react_past=r2(E.s.values, E[["r1", "r5", "vol20"]].values), **o))
    return rows

def cpc_hdd():
    parts = []
    for y in range(2005, 2027):
        r = requests.get(f"https://ftp.cpc.ncep.noaa.gov/htdocs/degree_days/weighted/daily_data/{y}/Population.Heating.txt", headers=UA, timeout=60)
        if r.status_code != 200: continue
        rows = [l.split("|") for l in r.text.splitlines() if l.startswith("CONUS") or l.startswith("Region|")]
        hdr, val = rows[0][1:], rows[1][1:]
        parts.append(pd.Series([float(v) for v in val], index=pd.to_datetime(hdr, format="%Y%m%d")))
        time.sleep(0.3)
    s = pd.concat(parts).sort_index(); s.to_csv(os.path.join(D, "cpc_hdd_conus_daily.csv")); return s

def portwatch():
    fn = os.path.join(D, "portwatch_chokepoints.csv")
    if os.path.exists(fn): return pd.read_csv(fn, parse_dates=["date"])
    frames = []
    for port in ["Suez Canal", "Strait of Hormuz", "Bab el-Mandeb Strait", "Panama Canal", "Malacca Strait"]:
        off = 0
        while True:
            r = requests.get("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query", headers=UA, timeout=60,
                             params={"where": f"portname='{port}'", "outFields": "date,portname,n_total,capacity", "orderByFields": "date ASC", "resultOffset": off, "resultRecordCount": 1000, "f": "json"}).json()
            f = r.get("features", [])
            frames += [x["attributes"] for x in f]
            if len(f) < 1000: break
            off += 1000
    df = pd.DataFrame(frames); df["date"] = pd.to_datetime(df.date, unit="ms") if df.date.dtype != object else pd.to_datetime(df.date)
    df.to_csv(fn, index=False); return df

def main():
    rows = []
    P = eia("PET.zip", ["PET.WCESTUS1.W", "PET.RWTC.D", "PET.RBRTE.D"])
    N = eia("NG.zip", ["NG.NW2_EPG0_SWO_R48_BCF.W", "NG.RNGWHHD.D"])
    info = {k: v for k, v in list(P.items()) + list(N.items()) if k.endswith("_updated")}
    # 1 crude inventories
    st = P["PET.WCESTUS1.W"]; sur = seasonal_surprise(st.diff())
    wti = P["PET.RWTC.D"]; wti = wti[wti > 0]
    rows += event_test("eia_crude_stock_surprise_vs_WTI", wti, sur, 5)
    # 2 gas storage
    gs = N["NG.NW2_EPG0_SWO_R48_BCF.W"]; gsur = seasonal_surprise(gs.diff()); hh = N["NG.RNGWHHD.D"]; hh = hh[hh > 0]
    rows += event_test("eia_gas_storage_surprise_vs_HenryHub", hh, gsur, 6)
    # 3 weather anomaly (CPC population-weighted HDD, observed) vs Henry Hub next-week return
    hdd = cpc_hdd(); doy = hdd.index.dayofyear
    clim = hdd.groupby(doy).apply(lambda x: x.rolling(10, min_periods=5).mean().shift(1)) if False else None
    wk = hdd.resample("W-FRI").sum(); wk = wk[wk.index >= "2006-01-01"]
    wkn = pd.DataFrame({"h": wk}); wkn["w"] = wkn.index.isocalendar().week.values; wkn["y"] = wkn.index.year
    an = []
    for t, r in wkn.iterrows():
        past = wkn[(wkn.w == r.w) & (wkn.y < r.y) & (wkn.y >= r.y - 10)].h
        an.append(r.h - past.mean() if len(past) >= 5 else np.nan)
    an = pd.Series(an, index=wkn.index)
    an = an / an.rolling(260, min_periods=100).std().shift(1)
    an[~an.index.month.isin([11, 12, 1, 2, 3])] = 0.0   # heating season only (summer HDD ~ 0)
    rows += event_test("cpc_hdd_weekly_anomaly_vs_HenryHub", hh, an, 3)  # available after Friday week close; next day ~ Monday-ish
    pd.DataFrame(rows).to_csv(os.path.join(RES, "real_economy_results_raw_returns.csv" if os.environ.get("ALT_NO_WINSOR") == "1" else "real_economy_results.csv"), index=False)
    # 4 PortWatch
    try:
        pw = portwatch(); pw["date"] = pd.to_datetime(pw["date"]); last = pw.date.max()
        piv = pw.pivot_table(index="date", columns="portname", values="n_total"); piv = piv.asfreq("D")
        res = []
        tot = piv.sum(axis=1, min_count=1)
        an = np.log(tot.rolling(7).mean() / tot.rolling(56).mean())
        # lag 10 days (weekly publication + revisions -> conservative)
        wti_r = np.log(wti).diff().dropna()
        wr = wti.resample("W-FRI").last(); y = np.log(wr).diff().shift(-1)  # next-week return after feature week
        f = an.resample("W-FRI").last().shift(2)  # 2-week lag (>=10d) conservative
        E = pd.concat([y.rename("y"), f.rename("s"), np.log(wr).diff().rename("r1"), np.log(wr).diff(4).rename("r4")], axis=1).dropna(); E = E[E.index >= "2019-06-01"]
        p, m = hac_wald(E.y, E[["r1", "r4", "s"]], ["s"]); pu, _ = hac_wald(E.y, E[["s"]], ["s"])
        pd.DataFrame([dict(cand="imf_portwatch_chokepoint_anomaly_vs_WTI_weekly", n=len(E), coef=float(m.params["s"]), p_incr=p, p_univ=pu, last_data=str(last.date()), lag_weeks=2)]).to_csv(os.path.join(RES, "portwatch_result.csv"), index=False)
    except Exception as e:
        json.dump({"portwatch_error": repr(e)}, open(os.path.join(RES, "portwatch_error.json"), "w"))
    json.dump(info, open(os.path.join(RES, "eia_series_last_updated.json"), "w"), indent=1)
    print(pd.DataFrame(rows).round(4).to_string())

if __name__ == "__main__":
    main()
