"""Builds reports/006_execution_cost_intelligence/*.md from report_templates/*.md by substituting @@table_name@@ with
tables generated directly from results/*.json|csv (so no number in a table is hand-typed).
python build_reports.py"""
import json, os, glob, re
import numpy as np, pandas as pd

ROOT = os.path.dirname(__file__)
RES = f"{ROOT}/results"
OUT = os.path.join(ROOT, "..", "..", "reports", "006_execution_cost_intelligence")
os.makedirs(OUT, exist_ok=True)


def md(df, fmt="{:.2f}", index=True):
    df = df.copy()
    if index: df = df.reset_index()
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        cells = []
        for v in r.values:
            if isinstance(v, (float, np.floating)):
                cells.append("n/a" if np.isnan(v) else fmt.format(v))
            elif isinstance(v, (list, tuple)):
                cells.append(str(v))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


T = {}
so = pd.read_csv(f"{RES}/single_orders.csv")
par = json.load(open(f"{RES}/single_params_timing.json"))
order = ["E1_mid_fill", "fixed_5bps_default", "fixed_bps_calibrated", "half_spread_only(E3)", "spread_prop", "vol_scaled", "size_depth(L1+D1bp)",
         "sqrt_law(OHLCV-only)", "sqrt_law(L1 spread)", "book_walk_L2_top20(20bps)", "book_walk_L2_top20+sqrt_fallback", "book_walk_L2(100bps)"]
reg = so.groupby("model").regime.first()
g = so.groupby(["model", "split"]).bias.apply(lambda x: x.abs().mean()).unstack()
r2 = so.groupby(["model", "split"]).rmse.mean().unstack()
ex = so[(so.split == "test") & ~so.scenario.isin(["gap", "withdraw"])].groupby("model").bias.apply(lambda x: x.abs().mean())
tail = so[so.scenario.isin(["gap", "withdraw"])].groupby("model").bias.apply(lambda x: x.abs().mean())
tab = pd.DataFrame({"data regime": reg, "mean |bias| train": g["train"], "mean |bias| TEST": g["test"], "TEST excl. gap+withdraw": ex, "gap+withdraw only": tail, "RMSE train": r2["train"], "RMSE TEST": r2["test"],
                    "us/pred": pd.Series(par["timing_us_per_pred"])}).loc[order]
tab.index.name = "model"
T["single_summary"] = md(tab)
piv = so[so.split == "test"].pivot_table(index="model", columns="scenario", values="bias", aggfunc=lambda x: x.abs().mean()).loc[order]
T["single_by_scenario"] = md(piv)
piv2 = so[so.scenario.isin(["base", "shallow", "concave_book"])].pivot_table(index=["scenario", "model"], columns="N", values="bias")
T["single_by_size"] = md(piv2.loc[[(s, m) for s in ["base", "shallow", "concave_book"] for m in ["half_spread_only(E3)", "sqrt_law(L1 spread)", "book_walk_L2_top20(20bps)", "book_walk_L2(100bps)"]]])
P = par["params"]
T["single_params"] = md(pd.DataFrame([dict(model=k, **{kk: vv for kk, vv in v.items()}) for k, v in P.items() if v]).set_index("model"), fmt="{:.4f}")
dec = pd.read_csv(f"{RES}/truth_decomposition.csv")
sel = dec[dec.scenario.isin(["base", "shallow", "trend", "gap", "withdraw"]) & dec.N.isin([1e4, 1e6, 1e7])].copy()
sel["scenario_N"] = sel.scenario + " / " + sel.N.map(lambda x: f"{x:.0e}")
T["truth_decomp"] = md(sel.set_index("scenario_N")[["IS", "drift", "half_spread", "walk", "impact", "filled", "IS_se", "identity_maxabs"]])

sl = json.load(open(f"{RES}/sliced.json"))
sd = pd.DataFrame(sl["rows"])
T["sliced_summary"] = md(sd.groupby(["model", "split"]).bias.apply(lambda x: x.abs().mean()).unstack())
x = sd[(sd.scenario == "sl_highimpact") & (sd.N == 5e6)][["slices", "model", "truth_ex_drift", "pred", "bias"]]
T["sliced_detail"] = md(x, index=False)
rk = pd.DataFrame(sl["ranking"])
T["sliced_rank"] = md(rk.groupby("model").agg(mean_regret_bps=("regret_bps", "mean"), share_correct_best=("regret_bps", lambda v: (v < 1e-9).mean())))
T["sliced_params"] = "```\n" + json.dumps(sl["params"], indent=1) + "\n```"
cp = pd.DataFrame(json.load(open(f"{RES}/competing.json")))
T["competing"] = md(cp[["kind", "k", "gap_s", "N", "naive_independent", "truth_avg_cost_per_order"]].assign(underestimate_x=cp.truth_avg_cost_per_order / cp.naive_independent), index=False)
lt = pd.DataFrame(json.load(open(f"{RES}/latency_fragmentation.json")))
T["latency"] = md(lt[lt.regime != "fragmentation"][["regime", "lat", "mean_drift", "sd_drift", "sqrt_lat_sigma", "ratio_sd_to_half_spread"]], index=False)
T["fragmentation"] = md(lt[lt.regime == "fragmentation"][["n_venues", "truth_routed_all", "single_venue_walk_estimate"]], index=False)

sp = pd.DataFrame(json.load(open(f"{RES}/spread_estimators_synth.json")))
sp["tick"] = sp.tick.map({0.0: "none", 1.0: "1bp"})
T["spread_synth"] = md(sp.groupby(["spread", "sigma", "tick"])[["eff_spread_truth", "roll", "corwin_schultz", "abdi_ranaldo", "hl_range_proxy"]].mean().round(2))
try:
    ed = pd.DataFrame(json.load(open(f"{RES}/oss_bidask_edge.json"))["synthetic"]); ed["tick"] = ed.tick.map({0.0: "none", 1.0: "1bp"})
    T["spread_edge"] = md(ed.groupby(["spread", "sigma", "tick"])[["eff_truth", "edge_bps"]].mean())
    T["spread_edge_real"] = md(pd.DataFrame(json.load(open(f"{RES}/oss_bidask_edge.json"))["real_binance_klines"]).T)
    T["edge_live"] = md(pd.DataFrame(json.load(open(f"{RES}/oss_bidask_edge.json"))["live_trade_bars"]).T[["n_bars", "edge_bps", "quoted_spread_mean_bps"]].astype({"n_bars": int, "edge_bps": float, "quoted_spread_mean_bps": float}))
except Exception as e:
    T["spread_edge"] = T["spread_edge_real"] = T["edge_live"] = f"(missing: {e})"

lf = json.load(open(f"{RES}/limit_fills.json"))
fr = pd.DataFrame(lf["fill_rows"])
T["fill_models"] = md(fr.groupby("model").err.agg(bias="mean", MAE=lambda x: x.abs().mean(), RMSE=lambda x: np.sqrt((x ** 2).mean())))
T["decision"] = md(pd.DataFrame(lf["decision"]).T.rename_axis("model|drift-knowledge"))
gg = pd.DataFrame(lf["grid"])
T["maker_grid"] = md(gg.groupby("drift")[["ff", "IS_maker", "IS_taker", "adverse"]].mean().rename(columns={"ff": "fill_frac", "IS_maker": "IS_maker_bps", "IS_taker": "IS_taker_bps", "adverse": "post-fill adverse (bps)"}))
T["maker_grid_fee"] = md(gg.groupby(["fee_m", "fee_t"])[["IS_maker", "IS_taker"]].mean())
T["maker_grid_q"] = md(gg.groupby("queue_frac")[["ff", "IS_maker", "IS_taker"]].mean())
T["maker_shares"] = f"maker better in {lf['truth_share_maker_better']:.1%} of grid cells; mean regret always-maker {lf['always_maker_regret']:.2f} bps, always-taker {lf['always_taker_regret']:.2f} bps ({len(gg)} cells)"

tm = json.load(open(f"{RES}/threat_matrix_and_contract_tests.json"))
th = pd.DataFrame(tm["threats"])
T["threat"] = md(th[["id", "name", "naive", "correct", "error", "unit"]], index=False)
T["contract_tests"] = "```json\n" + json.dumps(tm["contract_tests"], indent=1) + "\n```"

fb = json.load(open(f"{RES}/funding_borrow_roll.json"))
rows = []
for k in ("binance_vision_BTCUSDT", "binance_vision_ETHUSDT"):
    v = fb[k]
    for d in ("1d", "7d", "30d"):
        h = v["hold"][f"{d}_long_pays_bps"]
        rows.append(dict(series=k.replace("binance_vision_", "Binance "), hold=d, mean=h["mean"], p05=h["p05"], p50=h["p50"], p95=h["p95"], min=h["min"], max=h["max"]))
T["funding_hold"] = md(pd.DataFrame(rows), index=False)
T["funding_meta"] = md(pd.DataFrame([{k: v[k] for k in ("n", "t0", "t1", "mean_bps_per_8h", "sd", "frac_positive", "annualised_mean_pct")} | {"series": k} for k, v in fb.items() if k.startswith("binance")]).set_index("series"))
T["funding_xvenue"] = md(pd.DataFrame([{k2: v[k2] for k2 in ("n", "n_overlap_binance", "corr_okx_binance", "mean_abs_diff_bps", "binance_minus_okx_mean_bps", "realized_vs_announced_maxabs_diff_bps")} | {"series": k} for k, v in fb.items() if k.startswith("okx_") and isinstance(v, dict) and "n_overlap_binance" in v]).set_index("series"))
cv = pd.DataFrame(fb["okx_btcusd_dated_curve"]["curve"])
T["roll_curve"] = md(cv[["inst", "dte", "mid", "spread_bps", "basis_bps", "annualised_basis_pct", "vol24h_ct"]], index=False)
T["roll_pairs"] = md(pd.DataFrame(fb["okx_btcusd_dated_curve"]["rolls"]), index=False)
T["borrow"] = md(pd.DataFrame(fb["okx_public_borrow_basic"]).T.rename_axis("ccy"))

try:
    ss = json.load(open(f"{RES}/single_seed_stability.json"))
    T["seed_stability"] = md(pd.DataFrame({m: dict(TEST_mean=np.mean([x["test_abs_bias"] for x in v]), TEST_min=np.min([x["test_abs_bias"] for x in v]), TEST_max=np.max([x["test_abs_bias"] for x in v]),
                                                      train_mean=np.mean([x["train_abs_bias"] for x in v]), fitted_param_sd=np.std([x["Y_or_k"] for x in v])) for m, v in ss.items()}).T.loc[order].rename_axis("model"))
except Exception as e:
    T["seed_stability"] = f"(missing {e})"
ofm = open(f"{ROOT}/oss_probe/oss_findings.md").read()
T["oss_full"] = ofm[ofm.index("## zipline-reloaded slippage models"):]
T["oss_table"] = ofm[ofm.index("| Candidate |"):ofm.index("## zipline-reloaded slippage models")]
T["landscape_notes"] = open(f"{ROOT}/oss_probe/landscape_notes.md").read().split("\n", 3)[3]
ff = pd.DataFrame(json.load(open(f"{RES}/fullfill.json")))
T["fullfill"] = md(ff[["A", "N", "N_over_depth", "filled", "naive_full_fill_cost", "truth_cost_filled_part", "unfilled_notional"]], fmt="{:.3g}", index=False)
T["fullfill_share"] = f"cells with fill < 99 %: {(ff.filled < 0.99).mean():.0%} of {len(ff)} (thin-book grid); those cells have N/depth > {ff[ff.filled < 0.99].N_over_depth.min():.2g}; cells with N/depth < 0.1 all fill 100 %: {(ff[ff.N_over_depth < 0.1].filled > 0.999).all()}"
_g = so.copy()
_b = _g[(_g.N == 1e6) & _g.scenario.isin(["base", "hivol", "lovol", "deep", "shallow"])].pivot_table(index="model", columns="scenario", values=["truth", "pred"])
sens = {}
for m in order:
    row = {}
    for sc_ in ["hivol", "lovol", "deep", "shallow"]:
        tr = _b["truth"][sc_][m] / _b["truth"]["base"][m]; pr = _b["pred"][sc_][m] / _b["pred"]["base"][m]
        row[f"{sc_}: truth x"] = tr; row[f"{sc_}: model x"] = pr
    sens[m] = row
T["sensitivity"] = md(pd.DataFrame(sens).T.rename_axis("model"))
gl_ = pd.DataFrame(json.load(open(f"{RES}/limit_fills.json"))["grid"])
T["passive_fullfill"] = f"passive at the touch, {len(gl_)} cells: mean fill fraction {gl_.ff.mean():.2f}; share of cells with fill fraction < 0.95: {(gl_.ff < 0.95).mean():.0%}; < 0.5: {(gl_.ff < 0.5).mean():.0%}; min {gl_.ff.min():.2f}"
fxj = json.load(open(f"{RES}/fx_gold_ohlc.json"))
T["fxgold"] = md(pd.DataFrame([dict(instrument=k, bars=v["n_bars"], hours_per_week=v["hours_per_week_present"], sigma_bps_per_sqrt_s=v["sigma_bps_sqrt_s"], ann_vol_pct=v["annualised_vol_pct"],
                                    gaps_gt3h=v["n_gaps_gt3h"], mean_abs_gap_bps=v["gap_abs_bps_mean"], gap_over_sigma_hour=v["gap_over_sigma_hour"], sd_bps_at_L_2s=v["latency_sd_bps"]["2"], sd_bps_at_L_10s=v["latency_sd_bps"]["10"],
                                    CS_1h_bps=v["corwin_schultz_1h_bps"], AR_1h_bps=v["abdi_ranaldo_1h_bps"], volume=v["volume_available"]) for k, v in fxj.items()]), fmt="{:.2f}", index=False)
# ---- live / vision empirical
el = f"{RES}/empirical_live.json"
if os.path.exists(el):
    E = json.load(open(el))["per_venue_asset"]
    T["live_overview"] = md(pd.DataFrame([dict(venue=o["venue"], asset=o["asset"], n_snap=o["n_snap"], dur_min=o["duration_s"] / 60, rtt_ms_p50=o["rtt_ms_p50"], gap_s_p50=o["sampling_gap_s_p50"],
                                               tick_bps=o["tick_bps"], spread_mean=o["spread_bps"]["mean"], spread_p95=o["spread_bps"]["p95"], one_tick_frac=o["spread_bps"]["one_tick_frac"],
                                               vis_depth_bps=o["visible_depth_bps_ask"]["p50"], beta=o["depth_exponent_beta"]["median"], sigma=o["sigma_bps_sqrt_s"], n_trades=o.get("n_trades")) for o in E]), fmt="{:.3f}", index=False)
    T["live_depth"] = md(pd.DataFrame([dict(venue=o["venue"], asset=o["asset"], **{f"USD<= {d}bps": v for d, v in o["ask_depth_usd_within_bps_from_touch"].items()}) for o in E]), fmt="{:,.0f}", index=False)
    rows = []
    for o in E:
        for N, w in o["walk_bps_vs_mid"].items():
            rows.append(dict(venue=o["venue"], asset=o["asset"], N=int(N), coverage=w["coverage"], mean_bps=w["mean"] if w["mean"] is not None else np.nan, p95_bps=w["p95"] if w["p95"] is not None else np.nan))
    wd = pd.DataFrame(rows)
    T["live_walk"] = md(wd.pivot_table(index=["venue", "asset"], columns="N", values="mean_bps"), fmt="{:.2f}")
    T["live_walk_cov"] = md(wd.pivot_table(index=["venue", "asset"], columns="N", values="coverage"), fmt="{:.2f}")
    rows = []
    for o in E:
        for h in ("4", "30"):
            for N, e in o["stale_walk_error"].get(h, {}).items():
                rows.append(dict(venue=o["venue"], asset=o["asset"], stale_s=int(h), N=int(N), n=e["n"], mean_err=e["mean_err"], mae=e["mae"], p95_abs=e["p95_abs"], mean_cost=e["cost_mean"]))
    T["live_stale"] = md(pd.DataFrame(rows)[lambda d: d.N.isin([1e4, 1e5, 1e6])], fmt="{:.3f}", index=False)
    rows = []
    for o in E:
        for N, b in o["baseline_vs_next_book_walk_dt4s"].items():
            if int(N) not in (10000, 100000, 1000000): continue
            for m, v in b.items():
                if m.startswith("_"): continue
                rows.append(dict(venue=o["venue"], asset=o["asset"], N=int(N), model=m, bias=v["bias"], mae=v["mae"]))
    bl = pd.DataFrame(rows)
    T["live_baselines_mae"] = md(bl.pivot_table(index=["venue", "asset", "N"], columns="model", values="mae"), fmt="{:.3f}")
    T["live_baselines_bias"] = md(bl.pivot_table(index=["venue", "asset", "N"], columns="model", values="bias"), fmt="{:.3f}")
    T["live_spreadmeas"] = md(pd.DataFrame([dict(venue=o["venue"], asset=o["asset"], quoted_mean=o["spread_bps"]["mean"], effective_mean=o.get("effective_spread_bps_mean"),
                                                 effective_median=o.get("effective_spread_bps_median"), realized_5s=(o.get("realized_spread_bps_mean") or {}).get("5"), realized_30s=(o.get("realized_spread_bps_mean") or {}).get("30"),
                                                 side_flag_agree=o.get("trade_side_flag_agreement_with_quote_rule")) for o in E]), fmt="{:.3f}", index=False)
    T["live_ohlc"] = md(pd.DataFrame([dict(venue=o["venue"], asset=o["asset"], **o["ohlc_proxies_1m_bps"]) for o in E if "ohlc_proxies_1m_bps" in o]), fmt="{:.3f}", index=False)
    rows = []
    for o in E:
        for H, v in (o.get("passive_fill_bounds") or {}).items():
            rows.append(dict(venue=o["venue"], asset=o["asset"], H_s=int(H), n=v["n"], P_upper_front=v["p_fill_upper_front_of_queue"], P_through=v["p_fill_price_through"], P_lower_back=v["p_fill_lower_back_of_queue"],
                             adverse_given_fill=v["adverse_markout30s_bps_given_fill"], adverse_uncond=v["adverse_markout30s_unconditional"], diff=v["adverse_diff_cond_minus_uncond"], ci_lo=v["adverse_diff_ci95_block_bootstrap"][0], ci_hi=v["adverse_diff_ci95_block_bootstrap"][1]))
    T["live_fill"] = md(pd.DataFrame(rows), fmt="{:.3f}", index=False)
    from scipy.stats import norm as _n
    rows2 = []
    for o in E:
        for H, v in (o.get("passive_fill_bounds") or {}).items():
            pred = 2 * _n.sf(o["tick_bps"] / (o["sigma_bps_sqrt_s"] * np.sqrt(int(H))))
            rows2.append(dict(venue=o["venue"], asset=o["asset"], H_s=int(H), observed_P_through=v["p_fill_price_through"], model_price_through_BM=pred, err=pred - v["p_fill_price_through"],
                              P_upper_front=v["p_fill_upper_front_of_queue"], P_lower_back=v["p_fill_lower_back_of_queue"], bracket_width=v["p_fill_upper_front_of_queue"] - v["p_fill_lower_back_of_queue"]))
    _d = pd.DataFrame(rows2)
    T["live_fill_model"] = md(_d, fmt="{:.3f}", index=False)
    rows3 = []
    for o in E:
        for H, v in (o.get("passive_fill_bounds") or {}).items():
            if int(H) != 30 or v.get("drift_over_H_if_no_fill_bps") is None: continue
            X = v["drift_over_H_if_no_fill_bps"]; hs = o["spread_bps"]["mean"] / 2
            row = dict(venue=o["venue"], asset=o["asset"], half_spread=hs, drift_if_nofill_30s=X, drift_if_fill_30s=v["drift_over_H_if_fill_bps"], n_nofill=v["n_nofill"], P_lower=v["p_fill_lower_back_of_queue"], P_upper=v["p_fill_upper_front_of_queue"])
            for df_ in (0.0, 1.0, 2.0, 5.0):
                row[f"P*(fee gap {df_:g}bps)"] = min(1.0, max(X, 0) / (max(X, 0) + 2 * hs + df_)) if (max(X, 0) + 2 * hs + df_) > 0 else np.nan
            rows3.append(row)
    T["live_breakeven"] = md(pd.DataFrame(rows3), fmt="{:.3f}", index=False)
    T["live_fill_model_summary"] = f"price-through Brownian model: mean error {_d.err.mean():+.3f}, MAE {_d.err.abs().mean():.3f} (n={len(_d)} series×horizons); observed [lower,upper] bracket width mean {_d.bracket_width.mean():.2f}, min {_d.bracket_width.min():.2f}, max {_d.bracket_width.max():.2f}"
    rows = []
    for o in E:
        for h, v in o["mid_drift_by_horizon_s"].items():
            rows.append(dict(venue=o["venue"], asset=o["asset"], horizon_s=int(h), sd_bps=v["sd_bps"], sd_over_half_spread=v["sd_over_half_spread"], sqrt_scaling_pred=v["sqrt_scaling_pred"], mean_bps=v["mean_bps"]))
    T["live_drift"] = md(pd.DataFrame(rows)[lambda d: (d.asset != "SOL") & (d.horizon_s >= 4)], fmt="{:.3f}", index=False)
    T["live_coupling"] = md(pd.DataFrame([dict(venue=o["venue"], asset=o["asset"], **{f"rho({k})": v["rho"] for k, v in o.get("vol_liquidity_coupling_spearman", {}).items()}) for o in E]), fmt="{:.2f}", index=False)
    cvx = json.load(open(el))["cross_venue"]
    T["live_cross"] = md(pd.DataFrame([dict(asset=a, pair=p, **v) for a, d in cvx.items() for p, v in d.items()]), fmt="{:.3f}", index=False)
for _tag in ("live", "deep"):
    _f = f"{RES}/transport_loo_{_tag}.json"
    if os.path.exists(_f):
        _r = json.load(open(_f))["loo"]
        _rows = [dict(N=int(N), n_series=v["n_series"], model=m, median_abs_rel_err=x["median_abs_rel_err"], mean_signed_rel_err=x["mean_signed_rel_err"], worst_factor=x["worst_factor"], mae_bps=x["mae_bps"]) for N, v in _r.items() for m, x in v.items() if m != "n_series"]
        T[f"transport_{_tag}"] = md(pd.DataFrame(_rows), fmt="{:.2f}", index=False)
ev = f"{RES}/empirical_vision.json"
if os.path.exists(ev):
    V = json.load(open(ev))
    rows = []
    for s in ("BTCUSDT", "ETHUSDT"):
        o = V[s]
        rows.append(dict(sym=s, days=len(o["days"]), agg_trades=o["n_aggtrades"], V_day_usd_bn=np.mean(list(o["V_day_usd"].values())) / 1e9, tick_bps=o["tick_bps"], flip_spread_median_bps=o["flip_spread_bps"]["median"],
                         flip_spread_mean_bps=o["flip_spread_bps"]["mean"], flip_frac_zero=o["flip_spread_bps"]["frac_zero"]))
    T["vision_overview"] = md(pd.DataFrame(rows), fmt="{:.4f}", index=False)
    rows = []
    for s in ("BTCUSDT", "ETHUSDT"):
        for m, v in V[s]["ohlc_1m_proxies_by_month_bps"].items():
            rows.append(dict(sym=s, file=m.replace("klines_", "").replace(".zip", ""), **v))
    T["vision_ohlc"] = md(pd.DataFrame(rows), fmt="{:.3f}", index=False)
    rows = []
    for s in ("BTCUSDT", "ETHUSDT"):
        for bar in (60, 300):
            i = V[s][f"impact_{bar}s"]
            rows.append(dict(sym=s, bar_s=bar, n_bars=i["n_bars"], lambda_bps_per_musd=i["lambda_bps_per_musd"], R2=i["r2"], loglog_slope=i["loglog_slope_delta"], oos_rmse_zero=i["oos_rmse_zero"], oos_rmse_linear=i["oos_rmse_linear"], oos_rmse_sqrt=i["oos_rmse_sqrt"]))
    T["vision_impact"] = md(pd.DataFrame(rows), fmt="{:.3f}", index=False)
    rows = []
    for s in ("BTCUSDT", "ETHUSDT"):
        for h, v in V[s]["last_trade_drift_by_horizon_s"].items():
            rows.append(dict(sym=s, horizon_s=float(h), sd_bps=v["sd_bps"], sd_over_sqrt_h=v["sd_over_sqrt_h"], p99_abs=v["p99_abs"], mean_bps=v["mean_bps"], momentum_after_top_quartile_flow=v["momentum_after_top_quartile_flow_bps"]))
    T["vision_drift"] = md(pd.DataFrame(rows), fmt="{:.3f}", index=False)
ed = f"{RES}/empirical_deep.json"
if os.path.exists(ed):
    E2 = json.load(open(ed))["per_venue_asset"]
    rows = []
    for o in E2:
        for N, w in o["walk_bps_vs_mid"].items():
            rows.append(dict(venue=o["venue"], asset=o["asset"], N=int(N), coverage=w["coverage"], mean_bps=w["mean"] if w["mean"] is not None else np.nan))
    wd2 = pd.DataFrame(rows)
    T["deep_walk"] = md(wd2.pivot_table(index=["venue", "asset"], columns="N", values="mean_bps"), fmt="{:.2f}")
    T["deep_cov"] = md(wd2.pivot_table(index=["venue", "asset"], columns="N", values="coverage"), fmt="{:.2f}")
    T["deep_overview"] = md(pd.DataFrame([dict(venue=o["venue"], asset=o["asset"], n_snap=o["n_snap"], vis_depth_bps=o["visible_depth_bps_ask"]["p50"], levels=o["visible_depth_bps_ask"]["n_levels"],
                                               beta_p10=o["depth_exponent_beta"]["p10"], beta_med=o["depth_exponent_beta"]["median"], beta_p90=o["depth_exponent_beta"]["p90"]) for o in E2]), fmt="{:.2f}", index=False)
    rows = []
    for o in E2:
        for N, b in o["baseline_vs_next_book_walk_dt4s"].items():
            for m, v in b.items():
                if m.startswith("_"): continue
                rows.append(dict(venue=o["venue"], asset=o["asset"], N=int(N), model=m, mae=v["mae"], bias=v["bias"]))
    b2 = pd.DataFrame(rows)
    if len(b2):
        T["deep_baselines_mae"] = md(b2[b2.N.isin([1e5, 1e6, 3e6])].pivot_table(index=["venue", "asset", "N"], columns="model", values="mae"), fmt="{:.3f}")

_rows13 = [l for l in open(f"{ROOT}/report_templates/13_ADJUDICATION.md").read().splitlines() if re.match(r"^\| \d+ \|", l)]
_v = [l.split("|")[5].strip() for l in _rows13]; _x = [l.split("|")[4].strip() for l in _rows13]
T["n_models"] = str(len(_rows13)); T["n_exec"] = str(sum(1 for x in _x if x.startswith("Yes")))
for _k, _n in (("adopt", "ADOPT_REFERENCE"), ("adapt", "ADAPT_CANDIDATE"), ("park", "PARK"), ("reject", "REJECT")):
    T[f"n_{_k}"] = str(sum(1 for v in _v if v.startswith(_n)))
_cnt = []
for _tag in ("live", "deep"):
    _f = f"{RES}/empirical_{_tag}.json"
    if not os.path.exists(_f): continue
    for o in json.load(open(_f))["per_venue_asset"]:
        for N, bb in o["baseline_vs_next_book_walk_dt4s"].items():
            if "book_walk(snapshot t)" in bb and "fixed_bps(train mean)" in bb:
                _cnt.append(dict(tag=_tag, N=int(N), walk=bb["book_walk(snapshot t)"]["mae"], fixed=bb["fixed_bps(train mean)"]["mae"], sqrt=bb.get("sqrt(Y train)", {}).get("mae", np.nan), hs=bb["half_spread_only"]["mae"],
                                 walk_bias=bb["book_walk(snapshot t)"]["bias"], fixed_bias=bb["fixed_bps(train mean)"]["bias"]))
_c = pd.DataFrame(_cnt)
if len(_c):
    T["walk_vs_const"] = (f"cells (series × N × run): {len(_c)}. Walk MAE < calibrated-constant MAE in {(_c.walk < _c.fixed).sum()} cells ({(_c.walk < _c.fixed).mean():.0%}); walk MAE < half-spread-only MAE in {(_c.walk < _c.hs).sum()} ({(_c.walk < _c.hs).mean():.0%}). "
                          f"Mean |bias|: walk {_c.walk_bias.abs().mean():.3f} bps vs constant {_c.fixed_bias.abs().mean():.3f} bps. By notional (share of cells where walk beats constant): "
                          + ", ".join(f"{int(N):,}: {(g.walk < g.fixed).mean():.0%} (n={len(g)})" for N, g in _c.groupby("N")))
for f in sorted(glob.glob(f"{ROOT}/report_templates/*.md")):
    s = open(f).read()
    for k in set(re.findall(r"@@(\w+)@@", s)):
        s = s.replace(f"@@{k}@@", T.get(k, f"**[MISSING TABLE {k}]**"))
    open(f"{OUT}/{os.path.basename(f)}", "w").write(s)
    miss = re.findall(r"MISSING TABLE (\w+)", s)
    print(os.path.basename(f), "OK" if not miss else f"MISSING {miss}")
json.dump(list(T), open(f"{RES}/_table_names.json", "w"))
print(len(T), "tables")
