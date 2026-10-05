"""L2e (bonus, court) — IC de l'espérance nette sur outcomes autocorrélés : t-test iid vs arch.bootstrap.

Contexte : l'endpoint quorum (espérance nette incrémentale de QUORUM_ONLY_SUPPRESSED) portera sur peu d'outcomes,
probablement autocorrélés (positions qui se chevauchent, régimes). Simulation : n=150 outcomes AR(1) phi=0.4,
bruit t(4), vraie moyenne 0 ; 300 réplications. Couverture nominale 95 %.
Méthodes : IC t iid ; arch StationaryBootstrap (bloc = optimal_block_length) percentile ; arch CircularBlockBootstrap.
Aussi : smoke de arch.bootstrap.SPA / StepM / MCS sur 3 « variantes » (A/B/C) de même moyenne.
"""
import json, time, warnings
import numpy as np
from scipy import stats
warnings.filterwarnings("ignore")
from arch.bootstrap import StationaryBootstrap, CircularBlockBootstrap, optimal_block_length, SPA, MCS

rng = np.random.default_rng(2026); R, n, phi = 300, 150, 0.4
cov = {"t_iid": 0, "stationary_bs": 0, "circular_bs": 0}; t0 = time.perf_counter()
for r in range(R):
    e = rng.standard_t(4, n + 50); x = np.zeros(n + 50)
    for t in range(1, n + 50):
        x[t] = phi * x[t - 1] + e[t]
    x = x[50:]
    m, se = x.mean(), x.std(ddof=1) / np.sqrt(n); q = stats.t.ppf(0.975, n - 1)
    cov["t_iid"] += (m - q * se <= 0 <= m + q * se)
    bl = max(1.0, float(optimal_block_length(x).loc[0, "stationary"]))
    for name, B in [("stationary_bs", StationaryBootstrap(bl, x, seed=r)), ("circular_bs", CircularBlockBootstrap(int(np.ceil(bl)), x, seed=r))]:
        lo, hi = B.conf_int(np.mean, reps=500, method="percentile").ravel()
        cov[name] += (lo <= 0 <= hi)
out = {k: v / R for k, v in cov.items()}; out["sec"] = round(time.perf_counter() - t0, 1)
# smoke SPA / MCS : 3 variantes, pertes iid même moyenne -> SPA ne doit pas rejeter, MCS doit tout garder
L = rng.standard_normal((300, 3))
spa = SPA(L[:, 0], L[:, 1:], reps=500, seed=1); spa.compute()
mcs = MCS(L, size=0.05, reps=500, seed=1); mcs.compute()
out["SPA_pvalues_null"] = {k: round(float(v), 3) for k, v in spa.pvalues.items()}
out["MCS_included_null"] = list(map(int, mcs.included))
# déterminisme
b1 = StationaryBootstrap(5, x, seed=7).conf_int(np.mean, reps=200).ravel().tolist()
b2 = StationaryBootstrap(5, x, seed=7).conf_int(np.mean, reps=200).ravel().tolist()
out["deterministic_seeded"] = b1 == b2
print(json.dumps(out, indent=1)); json.dump(out, open("l2e_results.json", "w"), indent=1)
