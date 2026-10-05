"""L2c — sanity skfolio HRP vs equal-weight (laneFGH, mission 018). Synthétique, 10 graines.

Univers A (5 actifs) : 2 « majors » corrélés (vol 3 %/j, rho 0.8), 2 « alts » (vol 6 %/j, rho 0.6 avec majors),
1 actif calme (vol 1 %/j, rho 0.1) ; innovations t(4) ; drift nul (aucun alpha : on ne compare que le risque).
Univers B (2 actifs, forme AurumShift BTC/DOGE) : vol 3 % et 6 %, rho 0.7.
Walk-forward : estimation sur 250 obs glissantes, rebalancement toutes les 20 obs, 1 500 obs hors échantillon.
Méthodes : EW, InverseVolatility (skfolio), HRP (skfolio), HRP (riskfolio-lib, contrôle croisé), MinVariance+LedoitWolf (skfolio).
Mesures : vol réalisée OOS (annualisée sqrt(365)), max drawdown, turnover moyen par rebalancement ; rejeu déterministe.
Usage : python l2c_portfolio.py (écrit l2c_results.json)
"""
import json, time, warnings
import numpy as np, pandas as pd

warnings.filterwarnings("ignore")
W, REB, NOOS = 250, 20, 1500


def make(seed, univ):
    rng = np.random.default_rng(seed)
    if univ == "A5":
        vol = np.array([0.03, 0.03, 0.06, 0.06, 0.01])
        C = np.array([[1, .8, .6, .6, .1], [.8, 1, .6, .6, .1], [.6, .6, 1, .7, .1], [.6, .6, .7, 1, .1], [.1, .1, .1, .1, 1]])
    else:
        vol = np.array([0.03, 0.06]); C = np.array([[1, .7], [.7, 1]])
    L = np.linalg.cholesky(C)
    n = W + NOOS
    z = rng.standard_t(4, (n, len(vol))) / np.sqrt(2)
    return pd.DataFrame((z @ L.T) * vol, columns=[f"a{i}" for i in range(len(vol))])


def weights(method, X):
    if method == "EW":
        return np.full(X.shape[1], 1 / X.shape[1])
    if method == "InvVol_skfolio":
        from skfolio.optimization import InverseVolatility
        return InverseVolatility().fit(X).weights_
    if method == "HRP_skfolio":
        from skfolio.optimization import HierarchicalRiskParity
        return HierarchicalRiskParity().fit(X).weights_
    if method == "HRP_riskfolio":
        import riskfolio as rp
        return rp.HCPortfolio(returns=X).optimization(model="HRP", codependence="pearson", rm="MV", linkage="single").values.ravel()
    if method == "MinVar_LW_skfolio":
        from skfolio.optimization import MeanRisk, ObjectiveFunction
        from skfolio.prior import EmpiricalPrior
        from skfolio.moments import LedoitWolf
        return MeanRisk(objective_function=ObjectiveFunction.MINIMIZE_RISK,
                        prior_estimator=EmpiricalPrior(covariance_estimator=LedoitWolf())).fit(X).weights_
    raise ValueError(method)


METHODS = ["EW", "InvVol_skfolio", "HRP_skfolio", "HRP_riskfolio", "MinVar_LW_skfolio"]


def backtest(R, method):
    pnl, prev, turn, ws = [], None, [], []
    t_fit = 0.0
    for t0 in range(W, len(R), REB):
        t1 = time.perf_counter(); w = np.asarray(weights(method, R.iloc[t0 - W:t0]), float); t_fit += time.perf_counter() - t1
        ws.append(w)
        if prev is not None:
            turn.append(float(np.abs(w - prev).sum()))
        prev = w
        pnl.extend((R.iloc[t0:t0 + REB].values @ w).tolist())
    p = np.array(pnl); eq = np.cumsum(p); dd = float(np.max(np.maximum.accumulate(eq) - eq))
    return {"vol_ann": float(p.std() * np.sqrt(365)), "maxdd_sum": dd, "turnover": float(np.mean(turn)) if turn else 0.0,
            "w_mean": np.round(np.mean(ws, 0), 3).tolist(), "fit_ms": 1000 * t_fit / len(ws)}


def main():
    out = {}
    for univ in ["A5", "B2_btc_doge_like"]:
        out[univ] = {}
        per = {m: [] for m in METHODS}
        for s in range(10):
            R = make(s, univ)
            for m in METHODS:
                try:
                    per[m].append(backtest(R, m))
                except Exception as e:  # échec mesuré (ex. HRP skfolio à 2 actifs)
                    out[univ][m] = {"ERROR": f"{type(e).__name__}: {e}"[:200]}
        for m in METHODS:
            v = per[m]
            if not v:
                print(univ, m, out[univ][m], flush=True); continue
            out[univ][m] = {k: round(float(np.mean([x[k] for x in v])), 4) for k in ["vol_ann", "maxdd_sum", "turnover", "fit_ms"]}
            out[univ][m]["w_mean_seed0"] = v[0]["w_mean"]
            out[univ][m]["vol_ratio_vs_EW_mean"] = round(float(np.mean([a["vol_ann"] / b["vol_ann"] for a, b in zip(v, per["EW"])])), 3)
            print(univ, m, out[univ][m], flush=True)
    R = make(0, "A5").iloc[:W]
    out["deterministic_HRP_skfolio"] = bool(np.array_equal(weights("HRP_skfolio", R), weights("HRP_skfolio", R)))
    out["deterministic_MinVar_LW_skfolio"] = bool(np.allclose(weights("MinVar_LW_skfolio", R), weights("MinVar_LW_skfolio", R), atol=0, rtol=0))
    out["HRP_skfolio_vs_riskfolio_maxabsdiff_seed0"] = float(np.max(np.abs(weights("HRP_skfolio", R) - weights("HRP_riskfolio", R))))
    json.dump(out, open("l2c_results.json", "w"), indent=1)


if __name__ == "__main__":
    main()
