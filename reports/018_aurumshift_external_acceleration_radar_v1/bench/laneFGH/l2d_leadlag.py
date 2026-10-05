"""L2d (bonus, court) — falsification lead/lag & cointégration (lane H, mission 018). Synthétique, 50 réplications.

Scénarios (n=1000 obs, ex. barres 1 min) :
  LEAD   : b_t = 0.5 a_{t-1} + e   (vrai lead a->b à lag 1)
  NULL   : a, b indépendants
  CONF   : facteur caché commun f ; a_t = f_t + e, b_t = 0.8 f_t + e (aucun lien causal a<->b), mais a est
           horodaté un pas trop tard (a_obs_t = a_{t-1}) -> lead apparent b->a (piège horodatage/latence venue)
  COINT  : spot p_t marche aléatoire ; perp q_t = p_t + basis_t, basis AR(1) phi=0.95 -> cointégrés
  RW     : deux marches aléatoires indépendantes (nulle de cointégration)
Tests : Granger (statsmodels, lag 1..3, F-test, alpha 5 %), PCMCI ParCorr (tigramite, tau_max 3, alpha 5 %),
Engle-Granger coint (statsmodels) et Johansen trace (statsmodels VECM) à 5 %.
Mesure : taux de rejet (= puissance sous LEAD/COINT, faux positifs sous NULL/RW, direction trompeuse sous CONF).
"""
import json, time, warnings
import numpy as np

warnings.filterwarnings("ignore")
N, REPS = 1000, 50


def gen(kind, rng):
    e = rng.standard_normal((N + 1, 2))
    if kind == "LEAD":
        a = e[:, 0]; b = np.r_[0, 0.5 * a[:-1]] + e[:, 1]; return a[1:], b[1:]
    if kind == "NULL":
        return e[1:, 0], e[1:, 1]
    if kind == "CONF":
        f = rng.standard_normal(N + 1); a = f + 0.5 * e[:, 0]; b = 0.8 * f + 0.5 * e[:, 1]
        return a[:-1], b[1:]  # a horodaté 1 pas trop tard : a_obs_t = a_{t-1}
    if kind == "COINT":
        p = np.cumsum(e[:, 0]); bs = np.zeros(N + 1)
        for t in range(1, N + 1):
            bs[t] = 0.95 * bs[t - 1] + 0.3 * e[t, 1]
        return p[1:], (p + bs)[1:]
    if kind == "RW":
        return np.cumsum(e[1:, 0]), np.cumsum(e[1:, 1])


def granger(x_cause, y, maxlag=3):
    from statsmodels.tsa.stattools import grangercausalitytests
    r = grangercausalitytests(np.c_[y, x_cause], maxlag=maxlag)  # statsmodels 0.15 : kwarg verbose supprimé
    return min(r[l][0]["ssr_ftest"][1] for l in r) * maxlag  # Bonferroni sur les lags


def pcmci(a, b):
    from tigramite import data_processing as pp
    from tigramite.pcmci import PCMCI
    from tigramite.independence_tests.parcorr import ParCorr
    r = PCMCI(dataframe=pp.DataFrame(np.c_[a, b], var_names=["a", "b"]), cond_ind_test=ParCorr(), verbosity=0).run_pcmci(tau_max=3, pc_alpha=0.05)
    p = r["p_matrix"]
    return {"a->b": bool((p[0, 1, 1:] < 0.05).any()), "b->a": bool((p[1, 0, 1:] < 0.05).any())}


def main():
    from statsmodels.tsa.stattools import coint
    from statsmodels.tsa.vector_ar.vecm import coint_johansen
    rng = np.random.default_rng(12345); out = {}
    t0 = time.perf_counter()
    for kind in ["LEAD", "NULL", "CONF"]:
        g_ab = g_ba = p_ab = p_ba = 0
        for _ in range(REPS):
            a, b = gen(kind, rng)
            g_ab += granger(a, b) < 0.05; g_ba += granger(b, a) < 0.05
            pc = pcmci(a, b); p_ab += pc["a->b"]; p_ba += pc["b->a"]
        out[kind] = {"granger_a->b": g_ab / REPS, "granger_b->a": g_ba / REPS, "pcmci_a->b": p_ab / REPS, "pcmci_b->a": p_ba / REPS}
    for kind in ["COINT", "RW"]:
        eg = jo = 0
        for _ in range(REPS):
            p, q = gen(kind, rng)
            eg += coint(p, q)[1] < 0.05
            j = coint_johansen(np.c_[p, q], det_order=0, k_ar_diff=1); jo += j.lr1[0] > j.cvt[0, 1]
        out[kind] = {"engle_granger_reject": eg / REPS, "johansen_trace_r0_reject": jo / REPS}
    out["wall_sec"] = round(time.perf_counter() - t0, 1)
    print(json.dumps(out, indent=1))
    json.dump(out, open("l2d_results.json", "w"), indent=1)


if __name__ == "__main__":
    main()
