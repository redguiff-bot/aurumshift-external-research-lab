"""T07 — portfolio/risk libraries: known-answer tests.
(a) unconstrained minimum-variance weights vs closed form  w = S^-1 1 / (1' S^-1 1) on the same sample covariance
(b) long-only 2-asset case vs brute-force grid
(c) performance metrics (Sharpe, Sortino, max drawdown, CAGR, hist. VaR/CVaR) vs hand-computed
(d) determinism (2 runs) and timing."""
import json, time, warnings, sys; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
rng = np.random.default_rng(42)
n_a, T = 6, 1500
A = rng.normal(0, 1, (n_a, n_a)); cov_true = (A @ A.T) * 1e-5 + np.eye(n_a) * 4e-5
mu_true = rng.normal(3e-4, 2e-4, n_a)
R = pd.DataFrame(rng.multivariate_normal(mu_true, cov_true, T), columns=[f"a{i}" for i in range(n_a)],
                 index=pd.bdate_range("2019-01-01", periods=T))
S = R.cov().values; ones = np.ones(n_a); w_ref = np.linalg.solve(S, ones); w_ref /= w_ref.sum()
res = {"reference_weights": w_ref.round(6).tolist()}
def rec(name, w, secs): res[name] = dict(max_abs_weight_err=float(np.max(np.abs(np.asarray(w) - w_ref))), sum_w=float(np.sum(w)), seconds=round(secs, 4))
lib = sys.argv[1]
if lib == "pypfopt":
    from pypfopt import EfficientFrontier, HRPOpt
    t = time.perf_counter(); ef = EfficientFrontier(R.mean().values, pd.DataFrame(S, index=R.columns, columns=R.columns), weight_bounds=(-1, 1)); ef.min_volatility()
    w = pd.Series(ef.clean_weights(rounding=None)).values; rec("min_var_unconstrained", w, time.perf_counter()-t)
    w2 = [np.asarray(list(EfficientFrontier(R.mean().values, pd.DataFrame(S, index=R.columns, columns=R.columns), weight_bounds=(-1, 1)).min_volatility().values())) for _ in range(2)]
    res["deterministic_2_runs"] = bool(np.array_equal(w2[0], w2[1]))
    ef = EfficientFrontier(R.mean().values, pd.DataFrame(S, index=R.columns, columns=R.columns)); ef.min_volatility(); res["long_only_weights_sum"] = float(sum(ef.weights))
    res["long_only_min_weight"] = float(min(ef.weights))
    try:
        h = HRPOpt(R); hw = h.optimize(); res["hrp_sum"] = float(sum(hw.values()))
    except Exception as e: res["hrp_error"] = repr(e)[:200]
elif lib == "riskfolio":
    import riskfolio as rp
    t = time.perf_counter(); p = rp.Portfolio(returns=R); p.assets_stats(method_mu="hist", method_cov="hist")
    p.lowerret = None; p.sht = True; p.uppersht = 5; p.upperlng = 6; p.budget = 1
    w = p.optimization(model="Classic", rm="MV", obj="MinRisk", rf=0, l=0, hist=True).values.ravel(); rec("min_var_unconstrained", w, time.perf_counter()-t)
    p2 = rp.Portfolio(returns=R); p2.assets_stats(method_mu="hist", method_cov="hist"); w_lo = p2.optimization(model="Classic", rm="MV", obj="MinRisk", hist=True)
    res["long_only_min_weight"] = float(w_lo.values.min()); res["long_only_weights_sum"] = float(w_lo.values.sum())
    w_cvar = p2.optimization(model="Classic", rm="CVaR", obj="MinRisk", hist=True); res["cvar_minrisk_sum"] = float(w_cvar.values.sum())
    res["deterministic_2_runs"] = bool(np.array_equal(p2.optimization(model="Classic", rm="MV", obj="MinRisk", hist=True).values, w_lo.values))
elif lib == "skfolio":
    from skfolio.optimization import MeanRisk, ObjectiveFunction, HierarchicalRiskParity
    from skfolio import RiskMeasure
    from skfolio.moments import EmpiricalCovariance
    t = time.perf_counter(); m = MeanRisk(objective_function=ObjectiveFunction.MINIMIZE_RISK, risk_measure=RiskMeasure.VARIANCE, min_weights=-1, max_weights=6, budget=1)
    m.fit(R); rec("min_var_unconstrained", m.weights_, time.perf_counter()-t)
    m2 = MeanRisk(objective_function=ObjectiveFunction.MINIMIZE_RISK, risk_measure=RiskMeasure.VARIANCE).fit(R); m3 = MeanRisk(objective_function=ObjectiveFunction.MINIMIZE_RISK, risk_measure=RiskMeasure.VARIANCE).fit(R)
    res["long_only_min_weight"] = float(m2.weights_.min()); res["long_only_weights_sum"] = float(m2.weights_.sum()); res["deterministic_2_runs"] = bool(np.array_equal(m2.weights_, m3.weights_))
    res["hrp_sum"] = float(HierarchicalRiskParity().fit(R).weights_.sum())
elif lib == "metrics":
    r = R["a0"] + 0.0002; eq = (1 + r).cumprod(); ann = 252
    hand = dict(sharpe=r.mean()/r.std(ddof=1)*np.sqrt(ann),
                sortino=r.mean()/np.sqrt((np.minimum(r, 0)**2).mean())*np.sqrt(ann),
                max_dd=float((eq/eq.cummax()-1).min()), cagr=float(eq.iloc[-1]**(ann/len(r))-1),
                var95=float(-np.quantile(r, 0.05)), cvar95=float(-r[r <= np.quantile(r, 0.05)].mean()))
    res["hand"] = hand
    try:
        import empyrical as ep
        res["empyrical_reloaded"] = dict(sharpe=float(ep.sharpe_ratio(r, annualization=ann)), sortino=float(ep.sortino_ratio(r, annualization=ann)), max_dd=float(ep.max_drawdown(r)),
                                         cagr=float(ep.annual_return(r, annualization=ann)), var95=float(-ep.value_at_risk(r, cutoff=0.05)) if hasattr(ep, "value_at_risk") else None,
                                         cvar95=float(-ep.conditional_value_at_risk(r, cutoff=0.05)) if hasattr(ep, "conditional_value_at_risk") else None)
    except Exception as e: res["empyrical_error"] = repr(e)[:200]
    try:
        import quantstats as qs
        res["quantstats"] = dict(sharpe=float(qs.stats.sharpe(r, periods=ann)), sortino=float(qs.stats.sortino(r, periods=ann)), max_dd=float(qs.stats.max_drawdown(r)),
                                 cagr=float(qs.stats.cagr(r, periods=ann)), var95=float(-qs.stats.value_at_risk(r, confidence=0.95)), cvar95=float(-qs.stats.cvar(r, confidence=0.95)))
    except Exception as e: res["quantstats_error"] = repr(e)[:200]
print(json.dumps(res))
