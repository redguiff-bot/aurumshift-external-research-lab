"""L2a — détection causale d'un saut de volatilité (laneFGH, mission 018).

Série synthétique de rendements : sigma=1 sur [0,1000), sigma=k sur [1000,2000), k in {3, 1.5}.
Bruit gaussien ou Student-t(4) (normalisé à variance 1). Tous les détecteurs voient x[0..t] à l'instant t (causal),
SAUF `ruptures_offline_REF` qui voit toute la série (LOOKAHEAD, seulement comme référence de localisation).

Protocole (pré-déclaré dans ce fichier avant exécution) :
  - calibration : 20 séries nulles (graines 100..119, longueur 1000, sans saut) par famille de bruit ;
    pour chaque détecteur, on choisit sur une grille le réglage le PLUS sensible dont le taux de fausse alarme
    (au moins une alarme après warmup=50) est <= 10 %.
  - test : graines 0..19, saut à t=1000. Mesures : FA = alarme dans [50,1000) ; délai = 1re alarme >=1000 moins 1000 ;
    manqué si aucune alarme dans [1000,2000).
  - déterminisme : chaque détecteur est rejoué deux fois sur la graine 0 ; listes d'alarmes comparées.
  - misspécification : seuils calibrés sur bruit gaussien appliqués à des nulles t(4) -> taux FA.
Usage : python l2a_changepoint.py  (écrit l2a_results.json)
"""
import json, time, warnings
import numpy as np

warnings.filterwarnings("ignore")
WARM, N0, N1, CP = 50, 1000, 1000, 1000
FA_TARGET = 0.10


def series(seed, k, noise, n0=N0, n1=N1):
    rng = np.random.default_rng(seed)
    n = n0 + n1
    if noise == "gauss":
        e = rng.standard_normal(n)
    else:
        e = rng.standard_t(4, n) / np.sqrt(2.0)  # var t4 = 2
    s = np.r_[np.ones(n0), np.full(n1, k)]
    return e * s


# ---------------- détecteurs : fabrique(knob) -> fonction(x) -> liste d'indices d'alarme ----------------
def det_adwin(delta):
    from river.drift import ADWIN
    def run(x):
        d = ADWIN(delta=delta); out = []
        for i, v in enumerate(x):
            d.update(abs(v))
            if d.drift_detected and i >= WARM:
                out.append(i)
        return out
    return run


def det_ph(thr):
    from river.drift import PageHinkley
    def run(x):
        d = PageHinkley(min_instances=30, delta=0.005, threshold=thr, mode="up"); out = []
        for i, v in enumerate(x):
            d.update(v * v)
            if d.drift_detected and i >= WARM:
                out.append(i)
        return out
    return run


def det_kswin(alpha):
    from river.drift import KSWIN
    def run(x):
        d = KSWIN(alpha=alpha, window_size=100, stat_size=30, seed=42); out = []
        for i, v in enumerate(x):
            d.update(abs(v))
            if d.drift_detected and i >= WARM:
                out.append(i)
        return out
    return run


def det_focus(thr):
    from changepoint_online import Focus, Gamma
    def run(x):
        d = Focus(Gamma(shape=0.5), side="right"); out = []  # r^2 ~ Gamma(1/2, 2 sigma^2) si gaussien
        for i, v in enumerate(x):
            d.update(float(v * v) + 1e-12)
            if i >= WARM and d.statistic() > thr:
                out.append(i)
        return out
    return run


def det_bocd_pkg(thr):
    """Paquet `bocd` 0.1.2 (StudentT, moyenne+variance inconnues). Statistique : P(run length <= 10)."""
    from bocd import BayesianOnlineChangePointDetection, ConstantHazard, StudentT
    def run(x):
        b = BayesianOnlineChangePointDetection(ConstantHazard(250), StudentT(mu=0, kappa=1, alpha=1, beta=1)); out = []
        for i, v in enumerate(x):
            b.update(v)
            if i >= WARM and b.belief[:11].sum() > thr:
                out.append(i)
        return out
    return run


def det_bocpd_np(thr, rmax=400, hazard=1 / 250):
    """BOCPD custom ~25 LOC (Adams&MacKay 2007), moyenne connue 0, précision ~ Gamma(a,b), troncature rmax."""
    from scipy.special import gammaln
    def run(x):
        a0, b0 = 1.0, 1.0
        logR = np.array([0.0]); a = np.array([a0]); b = np.array([b0]); out = []
        lh, l1h = np.log(hazard), np.log1p(-hazard)
        for i, v in enumerate(x):
            # prédictive Student-t(2a, 0, b/a)
            lp = gammaln(a + 0.5) - gammaln(a) - 0.5 * np.log(2 * np.pi * b) - (a + 0.5) * np.log1p(v * v / (2 * b))
            growth = logR + lp + l1h
            cp = np.logaddexp.reduce(logR + lp + lh)
            logR = np.r_[cp, growth]
            logR -= np.logaddexp.reduce(logR)
            a = np.r_[a0, a + 0.5]; b = np.r_[b0, b + v * v / 2]
            if len(logR) > rmax:
                logR, a, b = logR[:rmax], a[:rmax], b[:rmax]
                logR -= np.logaddexp.reduce(logR)
            if i >= WARM and np.exp(np.logaddexp.reduce(logR[:11])) > thr:
                out.append(i)
        return out
    return run


def det_ruptures_expanding(pen, step=25, look=200, win=400):
    """ruptures Pelt relancé causalement sur x[max(0,t-win):t] toutes les `step` obs ; alarme si un bkp
    tombe dans les `look` dernières obs. Causal (pas de lookahead) mais coût O(n * win) ; délai >= granularité."""
    import ruptures as rpt
    def run(x):
        out = []
        for t in range(WARM + 50, len(x) + 1, step):
            lo = max(0, t - win)
            seg = x[lo:t].reshape(-1, 1)
            bk = rpt.Pelt(model="normal", min_size=20, jump=5).fit(seg).predict(pen=pen)[:-1]
            if any(b + lo >= t - look for b in bk):
                out.append(t - 1)
        return out
    return run


DETECTORS = {
    # nom : (fabrique, grille du plus sensible au moins sensible)
    "river_ADWIN_absret": (det_adwin, [0.5, 0.2, 0.1, 0.02, 0.002, 1e-4, 1e-6, 1e-9]),
    "river_PageHinkley_sq": (det_ph, [5, 10, 20, 40, 80, 160, 320, 640]),
    "river_KSWIN_absret": (det_kswin, [1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-8]),
    "focus_gamma_sq(changepoint_online)": (det_focus, [5, 8, 10, 12, 15, 20, 30, 50]),
    "bocd_pkg_studentT": (det_bocd_pkg, [0.2, 0.3, 0.5, 0.7, 0.9, 0.97, 0.99]),
    "bocpd_custom_numpy": (det_bocpd_np, [0.2, 0.3, 0.5, 0.7, 0.9, 0.97, 0.99]),
    "ruptures_pelt_expanding_causal": (det_ruptures_expanding, [20, 40, 80, 160]),
}


def calibrate(fac, grid, noise):
    for knob in grid:
        run = fac(knob)
        fa = np.mean([len(run(series(100 + s, 1.0, noise, N0, 0))) > 0 for s in range(20)])
        if fa <= FA_TARGET:
            return knob, float(fa)
    return grid[-1], float(fa)


def evaluate(fac, knob, k, noise):
    run = fac(knob); fa, delays, miss = 0, [], 0
    for s in range(20):
        al = run(series(s, k, noise))
        if any(a < CP for a in al):
            fa += 1
        post = [a for a in al if a >= CP]
        if post:
            delays.append(post[0] - CP)
        else:
            miss += 1
    return {"FA_rate_pre": fa / 20, "miss_rate": miss / 20,
            "delay_median": float(np.median(delays)) if delays else None,
            "delay_p90": float(np.percentile(delays, 90)) if delays else None}


def one(name):
    fac, grid = DETECTORS[name]
    t0 = time.perf_counter(); r = {}
    for noise in ["gauss", "t4"]:
        knob, fa_cal = calibrate(fac, grid, noise)
        r[noise] = {"knob": knob, "FA_calib": fa_cal}
        for k in [3.0, 1.5]:
            r[noise][f"k={k}"] = evaluate(fac, knob, k, noise)
    # misspécification : seuil gaussien appliqué au bruit t4 (nulles)
    run = fac(r["gauss"]["knob"])
    r["FA_gauss_knob_on_t4_null"] = float(np.mean([len(run(series(200 + s, 1.0, "t4", N0, 0))) > 0 for s in range(20)]))
    # déterminisme
    x = series(0, 3.0, "gauss")
    r["deterministic_replay"] = run(x) == fac(r["gauss"]["knob"])(x)
    r["wall_sec_total"] = round(time.perf_counter() - t0, 1)
    t1 = time.perf_counter(); run(x); r["ms_per_obs"] = round(1000 * (time.perf_counter() - t1) / len(x), 4)
    print(name, json.dumps(r), flush=True)
    return name, r


def main():
    from multiprocessing import Pool
    res = {"protocol": __doc__.strip().splitlines()[0], "detectors": {}}
    import ruptures as rpt
    names = sorted(DETECTORS, key=lambda n: not n.startswith("ruptures"))
    with Pool(4) as p:
        for name, r in p.imap_unordered(one, names):
            res["detectors"][name] = r
    # référence offline (LOOKAHEAD) : localisation du saut par ruptures Pelt sur la série entière
    loc = {}
    for noise in ["gauss", "t4"]:
        for k in [3.0, 1.5]:
            errs = []
            for s in range(20):
                bk = rpt.Pelt(model="normal", min_size=20, jump=5).fit(series(s, k, noise).reshape(-1, 1)).predict(pen=30)[:-1]
                errs.append(min([abs(b - CP) for b in bk], default=None) if bk else None)
            ok = [e for e in errs if e is not None]
            loc[f"{noise}_k={k}"] = {"n_found": len(ok), "median_abs_loc_err": float(np.median(ok)) if ok else None}
    res["ruptures_offline_REF_LOOKAHEAD"] = loc
    json.dump(res, open("l2a_results.json", "w"), indent=1)


if __name__ == "__main__":
    main()
