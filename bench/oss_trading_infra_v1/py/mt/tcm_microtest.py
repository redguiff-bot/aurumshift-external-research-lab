"""cvxportfolio simulator cost model: does the realised cost follow the documented form? spread term linear in |z|; impact term with exponent 1.5 -> x4 size => x8 cost."""
import warnings, json, sys, os; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, cvxportfolio as cvx
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import save
rng = np.random.default_rng(1); T, N = 300, 4
R = pd.DataFrame(rng.normal(0, 0.01, (T, N)), columns=list("ABCD"), index=pd.bdate_range("2022-01-03", periods=T)); R["cash"] = 0.0
V = pd.DataFrame(np.full((T, N), 5e6), index=R.index, columns=list("ABCD")); P = 100 * (1 + R.drop(columns="cash")).cumprod()
def loss(capital, a, b):
    mkt = cvx.UserProvidedMarketData(returns=R, volumes=V, prices=P, cash_key="cash", min_history=pd.Timedelta("60d"))
    sim = cvx.MarketSimulator(market_data=mkt, costs=[cvx.TransactionCost(a=a, b=b, exponent=1.5)] if (a or b) else [])
    st = R.index[100]; en = R.index[101]
    r = sim.backtest(cvx.Uniform(), start_time=st, end_time=en, initial_value=capital)
    return float(r.v.iloc[0] - r.v.iloc[-1]), r
res = {"version": cvx.__version__}
try:
    base1, r0 = loss(1e6, 0, 0); base4, _ = loss(4e6, 0, 0)
    sp1, _ = loss(1e6, 0.001, 0); sp4, _ = loss(4e6, 0.001, 0)
    im1, _ = loss(1e6, 0, 1.0); im4, _ = loss(4e6, 0, 1.0)
    # gross of market moves: subtract zero-cost run
    c = lambda x, b: x - b
    res["spread_only_a=10bps"] = {"cost_1M": c(sp1, base1), "cost_4M": c(sp4, base4), "ratio_4M_over_1M": (c(sp4, base4) / c(sp1, base1)) if c(sp1, base1) else None, "expected_ratio": 4.0, "expected_cost_1M_if_10bps_on_traded_notional": 0.001 * 1e6}
    res["impact_only_b=1"] = {"cost_1M": c(im1, base1), "cost_4M": c(im4, base4), "ratio_4M_over_1M": (c(im4, base4) / c(im1, base1)) if c(im1, base1) else None, "expected_ratio_exponent_1.5": 8.0}
except Exception as e: res["error"] = f"{type(e).__name__}: {str(e)[:300]}"
print(json.dumps(res, indent=1)); save("tcm_microtest.json", res)
