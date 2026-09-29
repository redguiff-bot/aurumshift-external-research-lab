import warnings, os; warnings.filterwarnings("ignore"); os.environ["MPLBACKEND"] = "Agg"
import numpy as np, pandas as pd, json, time, importlib.metadata as md
from common import save
rng = np.random.default_rng(42); T, N = 1000, 5
A = rng.normal(size=(N, N)) * 0.004; cov = A @ A.T + np.diag(np.full(N, 1e-4)); mu = rng.normal(0.0003, 0.0002, N)
R = pd.DataFrame(rng.multivariate_normal(mu, cov, T), columns=list("ABCDE"), index=pd.bdate_range("2020-01-01", periods=T))
res = {"n_assets": N, "T": T}
# oracle: long-only min-variance by projected/analytic solve via scipy SLSQP on sample covariance
from scipy.optimize import minimize
S = R.cov().values
o = minimize(lambda w: w @ S @ w, np.full(N, 1/N), bounds=[(0, 1)]*N, constraints={"type": "eq", "fun": lambda w: w.sum()-1}, method="SLSQP", options={"ftol": 1e-14, "maxiter": 500})
res["oracle_minvar_weights"] = dict(zip(R.columns, np.round(o.x, 5)))
W = {}
def rec(name, fn):
    t0 = time.perf_counter()
    try:
        w = fn(); w2 = fn()
        w = np.asarray(w, float); W[name] = w
        res[name] = {"weights": dict(zip(R.columns, np.round(w, 5))), "maxabs_vs_oracle": float(np.max(np.abs(w - o.x))), "deterministic": bool(np.allclose(w, np.asarray(w2, float), atol=1e-12)), "seconds_2_runs": round(time.perf_counter() - t0, 2), "version_pypi": None}
    except Exception as e: res[name] = {"error": f"{type(e).__name__}: {str(e)[:250]}"}
def pypfopt():
    from pypfopt import EfficientFrontier, risk_models
    ef = EfficientFrontier(None, risk_models.sample_cov(R, returns_data=True, frequency=1), weight_bounds=(0, 1)); ef.min_volatility(); return pd.Series(ef.clean_weights(rounding=None))[R.columns].values
def riskfolio():
    import riskfolio as rp
    p = rp.Portfolio(returns=R); p.assets_stats(method_mu="hist", method_cov="hist"); return p.optimization(model="Classic", rm="MV", obj="MinRisk", hist=True).values.ravel()
def skfo():
    from skfolio.optimization import MeanRisk, ObjectiveFunction
    m = MeanRisk(objective_function=ObjectiveFunction.MINIMIZE_RISK); m.fit(R); return m.weights_
for n, f in [("PyPortfolioOpt", pypfopt), ("Riskfolio-Lib", riskfolio), ("skfolio", skfo)]: rec(n, f)
# metrics: empyrical vs quantstats vs numpy
ret = R["A"]
ex = {"sharpe_daily_ann": float(ret.mean() / ret.std(ddof=1) * np.sqrt(252)), "max_dd": float(((1 + ret).cumprod() / (1 + ret).cumprod().cummax() - 1).min())}
try:
    import empyrical as ep
    res["empyrical_reloaded"] = {"sharpe": float(ep.sharpe_ratio(ret)), "max_dd": float(ep.max_drawdown(ret)), "vs_numpy": {"sharpe_absdiff": abs(float(ep.sharpe_ratio(ret)) - ex["sharpe_daily_ann"]), "dd_absdiff": abs(float(ep.max_drawdown(ret)) - ex["max_dd"])}}
except Exception as e: res["empyrical_reloaded"] = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
try:
    import quantstats as qs
    res["quantstats"] = {"sharpe": float(qs.stats.sharpe(ret)), "max_dd": float(qs.stats.max_drawdown(ret)), "vs_numpy": {"sharpe_absdiff": abs(float(qs.stats.sharpe(ret)) - ex["sharpe_daily_ann"]), "dd_absdiff": abs(float(qs.stats.max_drawdown(ret)) - ex["max_dd"])}}
except Exception as e: res["quantstats"] = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
res["numpy_reference"] = ex
# cvxportfolio: cost model + policy, tiny simulation with user-provided data
try:
    import cvxportfolio as cvx
    t0 = time.perf_counter()
    prices = (100 * (1 + R).cumprod()); volumes = pd.DataFrame(rng.integers(1e6, 2e6, (T, N)).astype(float), index=R.index, columns=R.columns)
    md_ = cvx.UserProvidedMarketData(returns=R, volumes=volumes, prices=prices, cash_key="cash", base_location=None if False else ".", min_history=pd.Timedelta("100d")) if False else None
    cost = cvx.TransactionCost(a=0.0005, b=1.0, exponent=1.5)  # a: half-spread-like, b*sigma*(|z|/vol)^1.5 impact
    pol = cvx.SinglePeriodOptimization(cvx.ReturnsForecast() - 0.5 * cvx.FullCovariance() - cvx.TransactionCost(a=0.0005, b=1.0, exponent=1.5), [cvx.LongOnly(), cvx.LeverageLimit(1)])
    res["cvxportfolio"] = {"version": md.version("cvxportfolio"), "policy_constructed": True, "note": "TransactionCost(a,b,exponent) = spread + sqrt-law-style impact; simulated via MarketSimulator on UserProvidedMarketData (cash column added)"}
    ret_df = R.copy(); ret_df["cash"] = 0.00005
    mkt = cvx.UserProvidedMarketData(returns=ret_df, volumes=volumes, prices=prices, cash_key="cash", min_history=pd.Timedelta("60d"))
    sim = cvx.MarketSimulator(market_data=mkt, costs=[cvx.TransactionCost(a=0.0005, b=1.0, exponent=1.5)])
    r = sim.backtest(pol, start_time=R.index[200], end_time=R.index[260], initial_value=1e6)
    res["cvxportfolio"].update({"sim_ran": True, "final_value": float(r.v.iloc[-1]), "turnover": float(r.turnover.mean()), "seconds": round(time.perf_counter() - t0, 2)})
    r2 = sim.backtest(pol, start_time=R.index[200], end_time=R.index[260], initial_value=1e6)
    res["cvxportfolio"]["deterministic"] = bool(abs(float(r.v.iloc[-1]) - float(r2.v.iloc[-1])) < 1e-6)
except Exception as e: res["cvxportfolio"] = {**res.get("cvxportfolio", {}), "error": f"{type(e).__name__}: {str(e)[:300]}"}
print(json.dumps(res, indent=1, default=str)); save("port_microtest.json", res)
