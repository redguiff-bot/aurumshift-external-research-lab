"""LANE A — L2 : intervalles pour la moyenne d'une série de DIFFÉRENCES APPARIÉES autocorrélées.

Forme AurumShift visée (INFERENCE, pas de code AurumShift lu) : pour chaque candidat QUORUM_ONLY_SUPPRESSED,
d_t = net_outcome_B(t) - net_outcome_A(t) (A ne trade pas => 0 ; B shadow => outcome contrefactuel net de coûts).
On veut un intervalle honnête sur E[d] avec observations dépendantes et petit n.

Série synthétique : d_t = mu + e_t, e_t = phi*e_{t-1} + s*u_t, u_t ~ Student-t(4) standardisé, phi = 0.3.
n in {60, 200}, mu in {0, 0.25*sd(d)}. Seeds fixes. Aucune donnée réelle.

Méthodes comparées (toutes niveau 95 % bilatéral sauf mention) :
  naive_t        : t de Student iid (référence, ignore l'autocorrélation)
  hac_nw         : statsmodels OLS(const) cov HAC, Newey-West, maxlags = floor(4*(n/100)^(2/9)), correction petits échantillons
  sb_opt         : arch StationaryBootstrap, bloc = optimal_block_length (Politis-White 2004 + Patton-Politis-White 2009), B=2000, percentile
  cbb_opt        : arch CircularBlockBootstrap, bloc = b_cb, B=2000, percentile
  cs_betting     : confseq.betting.betting_cs (Waudby-Smith & Ramdas 2024), CS anytime-valid lue au temps n,
                   données ramenées dans [0,1] avec borne DÉCLARÉE a priori |d| <= K (K = 8 sd ici, clip sinon)
  cs_betting_bm  : idem sur MOYENNES DE LOTS non chevauchants (taille = ceil(b_sb)) => dépendance réduite
  ci_betting     : confseq.betting.betting_ci (IC à n fixe, non séquentiel) — pour isoler le coût de l'anytime-validity
Plus : ESS (arviz.ess, acf statsmodels tronquée), TOST HAC vs ttost_paired iid, SPA/StepM arch (3 bras),
PSR/DSR/MinTRL (formules Bailey & López de Prado, implémentation 20 lignes) vs quantstats PSR.

Usage : <venv>/bin/python l2_paired_diff_intervals.py [--mini-coverage R]
Sortie : l2_results.json (+ l2_mini_coverage.json si --mini-coverage)
"""
from __future__ import annotations

import argparse
import json
import math
import time
import warnings

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

PHI = 0.3
ALPHA = 0.05
B_BOOT = 2000


def gen_series(n: int, mu: float, seed: int, phi: float = PHI) -> np.ndarray:
    rng = np.random.default_rng(seed)
    burn = 200
    u = rng.standard_t(4, size=n + burn) / math.sqrt(2.0)  # var(t4)=2 -> variance 1
    e = np.empty(n + burn)
    e[0] = u[0]
    for t in range(1, n + burn):
        e[t] = phi * e[t - 1] + u[t]
    e = e[burn:] * math.sqrt(1 - phi**2)  # variance marginale ~1
    return mu + e


# ---------------------------------------------------------------- méthodes
def naive_t(d):
    n = len(d)
    m, s = d.mean(), d.std(ddof=1)
    h = stats.t.ppf(1 - ALPHA / 2, n - 1) * s / math.sqrt(n)
    return m - h, m + h


def nw_lags(n):
    return int(math.floor(4 * (n / 100) ** (2 / 9)))


def hac_nw(d, alpha=ALPHA):
    import statsmodels.api as sm
    n = len(d)
    res = sm.OLS(d, np.ones(n)).fit(cov_type="HAC", cov_kwds={"maxlags": nw_lags(n), "use_correction": True},
                                    use_t=True)
    lo, hi = res.conf_int(alpha=alpha)[0]
    return float(lo), float(hi), float(res.bse[0])


def block_lengths(d):
    from arch.bootstrap import optimal_block_length
    ob = optimal_block_length(d)
    return float(ob["stationary"].iloc[0]), float(ob["circular"].iloc[0])


def boot_ci(d, kind: str, block: float, seed: int, reps: int = B_BOOT):
    from arch.bootstrap import CircularBlockBootstrap, StationaryBootstrap
    rng = np.random.default_rng(seed)
    cls = StationaryBootstrap if kind == "sb" else CircularBlockBootstrap
    blk = block if kind == "sb" else max(1, int(round(block)))
    bs = cls(blk, d, seed=rng)
    ci = bs.conf_int(np.mean, reps=reps, method="percentile", size=1 - ALPHA)
    return float(ci[0, 0]), float(ci[1, 0])


def to_unit(x, K):
    return (np.clip(x, -K, K) + K) / (2 * K)


def from_unit(v, K):
    return v * 2 * K - K


def cs_betting(d, K):
    from confseq.betting import betting_cs
    l, u = betting_cs(to_unit(d, K), alpha=ALPHA, running_intersection=True, parallel=False)
    return float(from_unit(l[-1], K)), float(from_unit(u[-1], K))


def ci_betting(d, K):
    from confseq.betting import betting_ci
    l, u = betting_ci(to_unit(d, K), alpha=ALPHA, parallel=False)
    return float(from_unit(l, K)), float(from_unit(u, K))


def batch_means(d, size):
    m = len(d) // size
    return d[: m * size].reshape(m, size).mean(axis=1)


# ---------------------------------------------------------------- ESS
def ess_acf(d):
    """n / (1 + 2 sum rho_k), troncature au premier rho_k <= 0 (Geyer simplifié)."""
    from statsmodels.tsa.stattools import acf
    n = len(d)
    r = acf(d, nlags=min(n - 1, 50), fft=True)
    s = 0.0
    for k in range(1, len(r)):
        if r[k] <= 0:
            break
        s += r[k]
    return n / (1 + 2 * s)


def ess_arviz(d):
    import arviz as az
    return float(az.ess(d.reshape(1, -1)))


# ---------------------------------------------------------------- Sharpe probabiliste
def psr(x, sr_star=0.0):
    n = len(x)
    sr = x.mean() / x.std(ddof=1)
    g3 = stats.skew(x)
    g4 = stats.kurtosis(x, fisher=False)
    se = math.sqrt((1 - g3 * sr + (g4 - 1) / 4 * sr**2) / (n - 1))
    return float(stats.norm.cdf((sr - sr_star) / se)), sr, g3, g4


def dsr_sr_star(n_trials, var_sr_trials):
    """Seuil SR0 du Deflated Sharpe Ratio (Bailey & López de Prado 2014, eq. espérance du max)."""
    emc = 0.5772156649
    z1 = stats.norm.ppf(1 - 1 / n_trials)
    z2 = stats.norm.ppf(1 - 1 / (n_trials * math.e))
    return math.sqrt(var_sr_trials) * ((1 - emc) * z1 + emc * z2)


def min_trl(sr, g3, g4, sr_star=0.0, alpha=ALPHA):
    z = stats.norm.ppf(1 - alpha)
    return 1 + (1 - g3 * sr + (g4 - 1) / 4 * sr**2) * (z / (sr - sr_star)) ** 2 if sr > sr_star else float("inf")


# ---------------------------------------------------------------- main
def run_case(n, mu_sd, seed):
    d = gen_series(n, mu_sd, seed)
    out = {"n": n, "mu_true": mu_sd, "seed": seed, "mean": float(d.mean()), "sd": float(d.std(ddof=1))}
    K = 8.0  # borne déclarée a priori (8 sd marginaux) — en réel : borne de risque/position déclarée AVANT
    out["clipped_frac"] = float(np.mean(np.abs(d) > K))
    t = {}

    def timed(name, f, *a):
        t0 = time.perf_counter()
        r = f(*a)
        t[name] = round(time.perf_counter() - t0, 4)
        return r

    out["naive_t"] = timed("naive_t", naive_t, d)
    lo, hi, se = timed("hac_nw", hac_nw, d)
    out["hac_nw"] = (lo, hi)
    out["hac_nw_lags"] = nw_lags(n)
    b_sb, b_cb = timed("opt_block", block_lengths, d)
    out["b_sb"], out["b_cb"] = b_sb, b_cb
    out["sb_opt"] = timed("sb_opt", boot_ci, d, "sb", b_sb, seed + 1)
    out["sb_opt_rerun_same_seed"] = boot_ci(d, "sb", b_sb, seed + 1)
    out["sb_opt_other_seed"] = boot_ci(d, "sb", b_sb, seed + 999)
    out["cbb_opt"] = timed("cbb_opt", boot_ci, d, "cbb", b_cb, seed + 1)
    out["cs_betting"] = timed("cs_betting", cs_betting, d, K)
    out["cs_betting_rerun"] = cs_betting(d, K)
    bsz = max(1, math.ceil(b_sb))
    bm = batch_means(d, bsz)
    out["batch_size"], out["n_batches"] = bsz, len(bm)
    out["cs_betting_bm"] = timed("cs_betting_bm", cs_betting, bm, K)
    out["ci_betting"] = timed("ci_betting", ci_betting, d, K)
    out["ess_acf"] = timed("ess_acf", ess_acf, d)
    out["ess_arviz"] = timed("ess_arviz", ess_arviz, d)
    out["ess_theory_ar1"] = n * (1 - PHI) / (1 + PHI)
    # TOST : marge d'équivalence ±0.2 sd ; TOST(alpha=5%) <=> IC 90 % inclus dans la marge
    from statsmodels.stats.weightstats import ttost_paired
    margin = 0.2
    p_iid = ttost_paired(d, np.zeros_like(d), -margin, margin)[0]
    lo90, hi90, _ = hac_nw(d, alpha=0.10)
    out["tost_margin"] = margin
    out["tost_iid_p"] = float(p_iid)
    out["tost_hac_ci90"] = (lo90, hi90)
    out["tost_hac_equiv"] = bool(lo90 > -margin and hi90 < margin)
    # PSR / MinTRL sur d (vu comme P&L incrémental par décision)
    p, sr, g3, g4 = psr(d)
    out["psr_custom"] = p
    out["sr_per_obs"] = sr
    out["min_trl_obs"] = min_trl(sr, g3, g4)
    out["dsr_sr0_for_3_arms_var0.01"] = dsr_sr_star(3, 0.01)
    try:
        import quantstats as qs
        s = pd.Series(d, index=pd.date_range("2026-01-01", periods=n, freq="h"))
        out["psr_quantstats"] = float(qs.stats.probabilistic_sharpe_ratio(s))
    except Exception as exc:  # noqa: BLE001
        out["psr_quantstats"] = f"ERR {exc!r}"
    for k in ("naive_t", "hac_nw", "sb_opt", "cbb_opt", "cs_betting", "cs_betting_bm", "ci_betting"):
        lo, hi = out[k]
        out[k + "_width"] = hi - lo
    out["timings_s"] = t
    return out


def spa_demo(seed=7, n=200):
    """3 bras (A quorum=2, B quorum=1, C single-family) : pertes = -P&L net ; benchmark = A."""
    from arch.bootstrap import SPA, StepM, MCS
    rng = np.random.default_rng(seed)
    common = gen_series(n, 0.0, seed)
    la = -(0.00 + common * 0.5 + rng.normal(0, 0.5, n))
    lb = -(0.15 + common * 0.5 + rng.normal(0, 0.5, n))  # B meilleur de 0.15 par obs
    lc = -(-0.05 + common * 0.5 + rng.normal(0, 0.5, n))
    models = np.column_stack([lb, lc])
    t0 = time.perf_counter()
    spa = SPA(la, models, block_size=5, reps=1000, seed=np.random.default_rng(seed))
    spa.compute()
    t_spa = time.perf_counter() - t0
    stepm = StepM(la, models, size=0.05, block_size=5, reps=1000, seed=np.random.default_rng(seed))
    stepm.compute()
    mcs = MCS(np.column_stack([la, lb, lc]), size=0.10, block_size=5, reps=1000, seed=np.random.default_rng(seed))
    mcs.compute()
    from statsmodels.stats.multitest import multipletests
    pv = [float(spa.pvalues["consistent"]), 0.03, 0.20]
    return {
        "spa_pvalues": {k: float(v) for k, v in spa.pvalues.items()},
        "spa_seconds": round(t_spa, 3),
        "stepm_superior_cols": [int(c) for c in stepm.superior_models] if stepm.superior_models is not None else [],
        "mcs_included": [int(c) for c in mcs.included],
        "bh_example_reject": multipletests(pv, method="fdr_bh")[0].tolist(),
        "by_example_reject": multipletests(pv, method="fdr_by")[0].tolist(),
        "holm_example_reject": multipletests(pv, method="holm")[0].tolist(),
    }


def mini_coverage(R, ns=(60, 200), mu=0.0):
    """Mini-contrôle de cohérence (PAS le grand bench de l'orchestrateur)."""
    res = {}
    for n in ns:
        hits = {"naive_t": 0, "hac_nw": 0, "sb_opt": 0, "cs_betting": 0, "cs_betting_bm": 0}
        widths = {k: [] for k in hits}
        for r in range(R):
            d = gen_series(n, mu, 10_000 + r)
            b_sb, _ = block_lengths(d)
            ints = {
                "naive_t": naive_t(d),
                "hac_nw": hac_nw(d)[:2],
                "sb_opt": boot_ci(d, "sb", b_sb, r, reps=499),
                "cs_betting": cs_betting(d, 8.0),
                "cs_betting_bm": cs_betting(batch_means(d, max(1, math.ceil(b_sb))), 8.0),
            }
            for k, (lo, hi) in ints.items():
                hits[k] += lo <= mu <= hi
                widths[k].append(hi - lo)
        res[str(n)] = {k: {"coverage": hits[k] / R, "median_width": float(np.median(widths[k]))} for k in hits}
    return {"R": R, "mu": mu, "phi": PHI, "results": res}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mini-coverage", type=int, default=0)
    a = ap.parse_args()
    t0 = time.perf_counter()
    cases = [run_case(n, mu, 20261005 + i) for i, (n, mu) in enumerate([(60, 0.0), (60, 0.25), (200, 0.0), (200, 0.25)])]
    import arch, statsmodels, confseq, arviz  # noqa: E401
    out = {
        "versions": {"arch": arch.__version__, "statsmodels": statsmodels.__version__,
                     "confseq": "0.0.11+laneA_patch", "arviz": arviz.__version__, "numpy": np.__version__},
        "cases": cases,
        "spa_stepm_mcs_demo": spa_demo(),
        "total_seconds": None,
    }
    out["total_seconds"] = round(time.perf_counter() - t0, 2)
    with open("l2_results.json", "w") as f:
        json.dump(out, f, indent=1, default=float)
    if a.mini_coverage:
        t1 = time.perf_counter()
        mc = mini_coverage(a.mini_coverage)
        mc["seconds"] = round(time.perf_counter() - t1, 1)
        with open("l2_mini_coverage.json", "w") as f:
            json.dump(mc, f, indent=1)
    print("done", out["total_seconds"])
