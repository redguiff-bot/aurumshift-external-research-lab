"""L1 import/smoke for laneFGH libs. Usage: python l1_smoke.py > l1_smoke.json"""
import importlib, time, json, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
res = {}
def t(name, fn):
    t0 = time.perf_counter()
    try:
        out = fn(); ok = True
    except Exception as e:
        out = f"{type(e).__name__}: {e}"[:300]; ok = False
    res[name] = {"ok": ok, "sec": round(time.perf_counter() - t0, 3), "out": out}

rng = np.random.default_rng(0)
x = np.r_[rng.normal(0, 1, 300), rng.normal(0, 3, 300)]

def river_():
    import river; from river import drift
    d = drift.ADWIN(); hits = []
    for i, v in enumerate(x):
        d.update(abs(v))
        if d.drift_detected: hits.append(i)
    return {"version": river.__version__, "adwin_hits": hits[:5]}
def ruptures_():
    import ruptures as rpt
    return {"version": rpt.__version__, "pelt_bkps": rpt.Pelt(model="normal").fit(x.reshape(-1,1)).predict(pen=20)}
def mapie_():
    import mapie; from mapie.regression import TimeSeriesRegressor
    return {"version": mapie.__version__, "has_TimeSeriesRegressor": True}
def crepes_():
    import crepes; from crepes import ConformalRegressor
    cr = ConformalRegressor(); cr.fit(residuals=np.abs(rng.normal(size=200)))
    iv = cr.predict_int(y_hat=np.zeros(3), confidence=0.9)
    return {"version": getattr(crepes, "__version__", "?"), "interval0": iv[0].tolist()}
def skfolio_():
    import skfolio; from skfolio.optimization import HierarchicalRiskParity
    import pandas as pd
    X = pd.DataFrame(rng.normal(0, 0.01, (300, 4)), columns=list("ABCD"))
    m = HierarchicalRiskParity().fit(X); return {"version": skfolio.__version__, "w": np.round(m.weights_, 4).tolist()}
def riskfolio_():
    import riskfolio as rp, pandas as pd
    X = pd.DataFrame(rng.normal(0, 0.01, (300, 4)), columns=list("ABCD"))
    p = rp.HCPortfolio(returns=X); w = p.optimization(model="HRP", codependence="pearson", rm="MV", linkage="single")
    return {"version": rp.__version__, "w": np.round(w.values.ravel(), 4).tolist()}
def tigramite_():
    import tigramite
    from tigramite import data_processing as pp
    from tigramite.pcmci import PCMCI
    from tigramite.independence_tests.parcorr import ParCorr
    n=500; a=rng.normal(size=n); b=np.zeros(n)
    for i in range(1,n): b[i]=0.6*a[i-1]+rng.normal()
    df = pp.DataFrame(np.c_[a,b], var_names=["a","b"])
    r = PCMCI(dataframe=df, cond_ind_test=ParCorr(), verbosity=0).run_pcmci(tau_max=3, pc_alpha=0.05)
    from importlib.metadata import version
    return {"version": version("tigramite"), "p_a_lag1_to_b": float(r["p_matrix"][0,1,1])}
def statsmodels_():
    import statsmodels; from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
    m = MarkovRegression(x, k_regimes=2, switching_variance=True).fit(disp=False)
    fp = m.filtered_marginal_probabilities  # filtered (causal) vs smoothed (lookahead)
    return {"version": statsmodels.__version__, "filtered_p_last": float(np.asarray(fp)[-1, 1])}
def arch_():
    import arch; from arch import arch_model
    r = arch_model(x, vol="GARCH", p=1, q=1).fit(disp="off")
    return {"version": arch.__version__, "params": {k: round(float(v),4) for k,v in r.params.items()}}
def skchange_():
    import pandas as pd; from importlib.metadata import version
    from skchange.detectors import PELT, MovingWindow
    from skchange.interval_scorers import GaussianCost
    d = PELT(cost=GaussianCost()); d.fit(pd.DataFrame(x)); cp = d.predict(pd.DataFrame(x))
    return {"version": version("skchange"), "pelt_out": str(np.asarray(cp).ravel().tolist())[:80]}
def hmmlearn_():
    import hmmlearn; from hmmlearn.hmm import GaussianHMM
    m = GaussianHMM(2, random_state=0, n_iter=50).fit(x.reshape(-1,1)); return {"version": hmmlearn.__version__}
def venn_():
    import venn_abers; return {"ok": True}
for n, f in [("river", river_), ("ruptures", ruptures_), ("mapie", mapie_), ("crepes", crepes_), ("skfolio", skfolio_),
             ("riskfolio", riskfolio_), ("tigramite", tigramite_), ("statsmodels", statsmodels_), ("arch", arch_),
             ("skchange", skchange_), ("hmmlearn", hmmlearn_), ("venn_abers", venn_)]:
    t(n, f)
json.dump(res, sys.stdout, indent=1, default=str)
