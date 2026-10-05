"""L2b — intervalles conformes en mode séries temporelles sous saut de volatilité (laneFGH, mission 018).

Série : r_t ~ N(0, s_t^2) (ou t4 normalisé), s=1 sur train(600)+test[0,500), s=3 sur test[500,1000).
Features causales (calculées sur r_{<t}) : r_{t-1}, mean|r| sur 5 et 20 obs. Cible y_t = r_t. Modèle LinearRegression.
Train = 600 premières obs (les 300 dernières = bloc de calibration pour les méthodes split/prefit). Test = 1000 obs,
traitées strictement une par une : prédire l'intervalle avec l'info <= t-1, PUIS révéler y_t et mettre à jour.
Cible de couverture 90 %. Méthodes :
  split_static_MAPIE        : mapie SplitConformalRegressor(prefit) — jamais mis à jour (référence invalide sous drift)
  enbpi_MAPIE_update        : mapie TimeSeriesRegressor(method='enbpi', BlockBootstrap) + update() à chaque pas
  aci_MAPIE_g0.01/_g0.05    : mapie TimeSeriesRegressor(method='aci', cv='prefit') + adapt_conformal_inference + update
  aci_custom_g0.01          : ACI Gibbs&Candès ~10 LOC sur fenêtre glissante 300 de |résidus| (contrôle croisé de MAPIE)
  rolling_crepes_w300       : crepes ConformalRegressor refit sur les 300 derniers résidus à chaque pas
  normalized_crepes_static  : crepes ConformalRegressor normalisé (sigma = EWMA(|r|) causal), calibré une fois
Mesures : couverture globale, pré-saut, 100 obs post-saut, largeur moyenne ; 10 graines ; rejeu déterministe graine 0.
Usage : python l2b_conformal.py  (écrit l2b_results.json)
"""
import json, time, warnings
import numpy as np

warnings.filterwarnings("ignore")
NTR, NTE, JUMP, ALPHA = 600, 1000, 500, 0.10


def make(seed, noise="gauss"):
    rng = np.random.default_rng(seed)
    n = NTR + NTE + 21
    e = rng.standard_normal(n) if noise == "gauss" else rng.standard_t(4, n) / np.sqrt(2)
    s = np.ones(n); s[21 + NTR + JUMP:] = 3.0
    r = e * s
    X, y, sig = [], [], []
    ew = 1.0
    for t in range(21, n):
        past = r[:t]
        X.append([past[-1], np.abs(past[-5:]).mean(), np.abs(past[-20:]).mean()])
        y.append(r[t])
        ew = 0.94 * ew + 0.06 * abs(past[-1]); sig.append(ew)  # EWMA causal de |r|
    return np.array(X), np.array(y), np.array(sig)


def summarize(lo, hi, y):
    cov = (y >= lo) & (y <= hi)
    w = hi - lo
    return {"cov_all": round(float(cov.mean()), 3), "cov_pre": round(float(cov[:JUMP].mean()), 3),
            "cov_post100": round(float(cov[JUMP:JUMP + 100].mean()), 3), "cov_post_last400": round(float(cov[JUMP + 100:].mean()), 3),
            "width_pre": round(float(np.median(w[:JUMP])), 3), "width_post": round(float(np.median(w[JUMP + 100:])), 3),
            "n_inf": int(np.sum(~np.isfinite(w)))}


def run_seed(seed, noise="gauss"):
    from sklearn.linear_model import LinearRegression
    from mapie.regression import SplitConformalRegressor, TimeSeriesRegressor
    from mapie.subsample import BlockBootstrap
    from crepes import ConformalRegressor
    X, y, sig = make(seed, noise)
    Xtr, ytr, Xte, yte = X[:NTR], y[:NTR], X[NTR:], y[NTR:]
    Xfit, yfit, Xcal, ycal = Xtr[:300], ytr[:300], Xtr[300:], ytr[300:]
    est = LinearRegression().fit(Xfit, yfit)
    out, timing = {}, {}

    t0 = time.perf_counter()
    sc = SplitConformalRegressor(est, confidence_level=1 - ALPHA, prefit=True).conformalize(Xcal, ycal)
    _, b = sc.predict_interval(Xte)
    out["split_static_MAPIE"] = summarize(b[:, 0, 0], b[:, 1, 0], yte); timing["split_static_MAPIE"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    enb = TimeSeriesRegressor(LinearRegression(), method="enbpi", cv=BlockBootstrap(n_resamplings=20, length=30, overlapping=True, random_state=0),
                              agg_function="mean", random_state=0).fit(Xtr, ytr)
    lo, hi = np.empty(NTE), np.empty(NTE)
    for t in range(NTE):
        _, b = enb.predict(Xte[t:t + 1], ensemble=True, confidence_level=1 - ALPHA, allow_infinite_bounds=True)
        lo[t], hi[t] = b[0, 0, 0], b[0, 1, 0]
        enb.update(Xte[t:t + 1], yte[t:t + 1], ensemble=True)
    out["enbpi_MAPIE_update"] = summarize(lo, hi, yte); timing["enbpi_MAPIE_update"] = time.perf_counter() - t0

    for g in [0.01, 0.05]:
        t0 = time.perf_counter()
        aci = TimeSeriesRegressor(est, method="aci", cv="prefit").fit(Xcal, ycal)
        lo, hi = np.empty(NTE), np.empty(NTE)
        for t in range(NTE):
            _, b = aci.predict(Xte[t:t + 1], confidence_level=1 - ALPHA, allow_infinite_bounds=True)
            lo[t], hi[t] = b[0, 0, 0], b[0, 1, 0]
            aci.adapt_conformal_inference(Xte[t:t + 1], yte[t:t + 1], gamma=g, confidence_level=1 - ALPHA)
            aci.update(Xte[t:t + 1], yte[t:t + 1])
        out[f"aci_MAPIE_g{g}"] = summarize(lo, hi, yte); timing[f"aci_MAPIE_g{g}"] = time.perf_counter() - t0

    # ACI custom (Gibbs & Candès 2021) : alpha_{t+1} = alpha_t + g*(alpha - err_t), quantile des 300 derniers |résidus|
    t0 = time.perf_counter()
    res = list(np.abs(ycal - est.predict(Xcal))); a_t = ALPHA; lo, hi = np.empty(NTE), np.empty(NTE)
    for t in range(NTE):
        p = est.predict(Xte[t:t + 1])[0]; R = np.array(res[-300:]); n = len(R)
        q = np.inf if a_t <= 0 else (np.quantile(R, min(1.0, np.ceil((n + 1) * (1 - a_t)) / n), method="higher") if a_t < 1 else 0.0)
        lo[t], hi[t] = p - q, p + q
        err = float(not (lo[t] <= yte[t] <= hi[t])); a_t = a_t + 0.01 * (ALPHA - err)
        res.append(abs(yte[t] - p))
    out["aci_custom_g0.01"] = summarize(lo, hi, yte); timing["aci_custom_g0.01"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    res = list(np.abs(ycal - est.predict(Xcal))); lo, hi = np.empty(NTE), np.empty(NTE)
    for t in range(NTE):
        p = est.predict(Xte[t:t + 1]); cr = ConformalRegressor().fit(residuals=np.array(res[-300:]))
        iv = cr.predict_int(y_hat=p, confidence=1 - ALPHA); lo[t], hi[t] = iv[0]
        res.append(abs(yte[t] - p[0]))
    out["rolling_crepes_w300"] = summarize(lo, hi, yte); timing["rolling_crepes_w300"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    sg_cal, sg_te = sig[300:NTR], sig[NTR:]
    crn = ConformalRegressor().fit(residuals=ycal - est.predict(Xcal), sigmas=sg_cal)
    iv = crn.predict_int(y_hat=est.predict(Xte), sigmas=sg_te, confidence=1 - ALPHA)
    out["normalized_crepes_static"] = summarize(iv[:, 0], iv[:, 1], yte); timing["normalized_crepes_static"] = time.perf_counter() - t0
    return out, timing


def main():
    agg = {}
    for noise in ["gauss", "t4"]:
        per = [run_seed(s, noise) for s in range(10)]
        for m in per[0][0]:
            vals = [p[0][m] for p in per]
            agg.setdefault(noise, {})[m] = {k: round(float(np.mean([v[k] for v in vals])), 3) for k in vals[0]}
            agg[noise][m]["ms_per_step"] = round(1000 * float(np.mean([p[1][m] for p in per])) / NTE, 3)
            print(noise, m, agg[noise][m], flush=True)
    a, _ = run_seed(0); b, _ = run_seed(0)
    agg["deterministic_replay_seed0"] = a == b
    json.dump(agg, open("l2b_results.json", "w"), indent=1)


if __name__ == "__main__":
    main()
