# raw_laneFGH — Lanes F (online/drift/conformal), G (portefeuille/risque), H (économétrie/causal TS)

Mission AURUMSHIFT_EXTERNAL_ACCELERATION_RADAR_V1 · sous-recherche `laneFGH` · 2026-10-05 (horloge sandbox).
Laboratoire externe : aucun code AurumShift lu ni touché. Étiquettes : VERIFIED_FACT, MEASURED_BY_THIS_MISSION (MBTM),
UPSTREAM_BENCHMARK, PAPER_RESULT, VENDOR_CLAIM, INFERENCE, UNKNOWN.

## 0. Ce sur quoi on s'appuie (LAB_PRIOR, pas refait)

- **LAB_PRIOR 012** (calibration) : split conformal invalide sous drift ; ACI / CP pondéré tiennent la couverture marginale ;
  couverture marginale ≠ fiabilité de décision. **Lacune déclarée par 012 : aucun contrôle croisé vs MAPIE/crepes.** → comblé ici (§2.2).
- **LAB_PRIOR 013** (online learning) : rolling refit = baseline dure ; RLS à oubli / SGD-logistique seuls challengers ;
  River 0.26.1 déterministe ; ADWIN-resets n'apportent rien.
- **LAB_PRIOR 014** (ensembles) : la sémantique « non observé ≠ pire récompense » domine les algorithmes ; EWMA/WTA durs à battre.
- **LAB_PRIOR 015** (features) : 0 identification causale possible sur klines observationnelles ; invariance ≠ causalité.
- **LAB_PRIOR 011** (primitives) : aucun edge net ; P12 lead-lag BTC significatif en rang (IC t 6.6) mais tué par 8.4 tours/jour à 1 h.
- **LAB_PRIOR 008** (risk capacity) : ranking par edge net / slot-hour suffit ; Riskfolio/skfolio/PyPortfolioOpt REJECT pour l'admission de slots.

Ce que cette lane ajoute : versions 2026, nouveaux candidats (changepoint_online/Focus, skchange, crepes normalisé,
arch.bootstrap pour l'endpoint quorum), et 5 micro-benchs MBTM orientés « chemin critique ».

## 1. Environnement et poids des dépendances (MBTM)

venv isolé : `scratchpad/venvs/laneFGH` (uv, Python 3.11). Installés : river 0.26.1, ruptures 1.1.10, mapie 1.5.0,
crepes 0.9.1, skfolio 1.4.11, riskfolio-lib 7.4.0, tigramite 5.2.10.1, statsmodels 0.15.0, arch 8.0.0, skchange 0.18.0,
hmmlearn 0.3.3, venn-abers 1.5.4, filterpy 1.4.5, pyportfolioopt 1.6.0, bocd 0.1.2, changepoint-online 1.2.1,
bayesian-changepoint-detection 0.2.dev1 ; scikit-learn 1.9.1, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6.

Poids d'installation, chaque lib seule dans un venv vierge (`uv pip list | wc -l`, `du -sm site-packages`) — MBTM :

| lib | paquets | Mo | remarque |
|---|---|---|---|
| tigramite | 4 | 172 | numpy/scipy/six seulement |
| ruptures | 3 | 177 | |
| river | 4 | 179 | numpy, scipy, narwhals |
| crepes | 6 | 213 | |
| mapie | 8 | 209 | |
| venn-abers | 11 | 249 | |
| statsmodels | 13 | 262 | |
| arch | 14 | 265 | |
| skfolio | 19 | 358 | cvxpy-base, clarabel, plotly |
| **riskfolio-lib** | **85** | **963** | Requires-Dist en dur : vectorbt, astropy, matplotlib, xlsxwriter, networkx, arch, statsmodels, cvxpy (VERIFIED METADATA) |

(~170 Mo = socle numpy+scipy.) L1 smoke (`bench/laneFGH/l1_smoke.py` → `l1_smoke.json`) : 12/12 imports + appel minimal OK
après deux corrections : `tigramite` n'expose pas `__version__` ; `skchange.change_detectors` est devenu `skchange.detectors`
(API renommée). numba JIT de skchange : ~6 s au premier appel.

Versions/licences/dates : PyPI JSON API (VERIFIED_FACT, URLs `https://pypi.org/pypi/<pkg>/json`) — voir CSV.
GitHub API refusée dans cette session (politique), raw.githubusercontent.com OK : statuts lus dans les README/LICENSE bruts.

## 2. Micro-benchs L2 (MBTM, synthétiques — ne disent rien de la valeur sur marché réel)

Tous rejouables : `cd bench/laneFGH && <venv>/bin/python -W ignore <script>.py`. Résultats JSON à côté.

### 2.1 L2a — détection causale d'un saut de vol (`l2a_changepoint.py` → `l2a_results.json`)

Protocole pré-déclaré dans le docstring : rendements σ=1 sur [0,1000) puis σ=k (k=3 « facile », k=1.5 « dur »),
bruit gaussien ou Student-t(4) normalisé. Chaque détecteur ne voit que x[0..t]. Réglage = le plus sensible d'une grille
dont le taux de fausse alarme (FA) sur 20 nulles de 1000 obs ≤ 10 % (calibré séparément par famille de bruit).
Test sur 20 graines ; FA = alarme avant le saut ; délai = 1re alarme après.

| détecteur (entrée) | gauss k=3 délai méd. | gauss k=1.5 délai méd. / raté | t4 k=3 | t4 k=1.5 délai / raté | FA si seuil gaussien appliqué à t4 | µs/obs |
|---|---|---|---|---|---|---|
| Focus Gamma (changepoint_online, r²) | **4** (FA 0) | **43.5** / 0 % | 16.5 (FA 10 %) | 230 / 0 % | **90 %** | 7 |
| PageHinkley River (r², mode up) | 8 (FA 10 %) | 40.5 / 0 % | 14 (FA 20 %) | 88 / 0 % | 50 % | 3 |
| ADWIN River (|r|) | 23* (FA 10 %) | 55 / 0 % | 23* (FA 20 %) | 55 / 5 % | 15 % | <1 |
| KSWIN River (|r|) | 27 | 59 / **75 %** | 28 | 438 / **90 %** | 5 % | 940 |
| ruptures Pelt relancé causalement (fenêtre 400, pas 25) | 24** (FA 0) | 49 / 5 % | 24 (FA 10 %) | 124 / **65 %** | 80 % | 1 718 |
| bocd 0.1.2 (StudentT, P(r≤10)) | 4 (FA 5 %) | 168 / 0 % | 49 (FA 25 %) | 436 / 15 % | 85 % | 1 492 |
| BOCPD custom numpy (P(r≤10)) | 3 / raté 25 % | 27 / raté 75 % | non calibrable (FA 70 % au seuil max) | — | 95 % | 553 |
| ruptures Pelt **série complète (LOOKAHEAD)** | localisation exacte (err. méd. 0) | err. méd. 12.5 | 0 | 10 | — | — |

\* ADWIN ne teste qu'une fois toutes les `clock=32` obs : délai quantifié. \** granularité = pas de relance (25).
Déterminisme : rejeu identique pour les 7 détecteurs (graine 0). FA mesurée sur 20 graines → intervalle large (±~10 pts).

Lecture :
- **Le problème n° 1 est la queue épaisse, pas l'algorithme** : tout seuil calibré sur une nulle gaussienne explose sous t(4)
  (Focus 90 %, BOCPD 85–95 %, ruptures 80 %, PH 50 %). Sur des rendements crypto, la calibration doit se faire sur une
  nulle réaliste (bootstrap par blocs de la période calme réelle) ou sur une transformée robuste (log r², rangs → NPFocus).
- Focus (Romano et al. 2023, PAPER_RESULT : coût amorti O(log n)) est le meilleur compromis délai/coût en gaussien ;
  PageHinkley est l'option la plus simple ; ruptures n'est pas fait pour l'online (240× plus lent que Focus, et sur série
  complète c'est du lookahead pur → réservé à la segmentation a posteriori dans RetexV1, étiquetée comme telle).
- BOCPD (bocd / custom) : lent, sensible au modèle, non calibrable sous t4 → pas de valeur ajoutée ici.

### 2.2 L2b — conformal séries temporelles sous saut de vol (`l2b_conformal.py` → `l2b_results.json`)

Cible 90 %, 10 graines, 1000 pas de test traités un par un (prédire puis révéler), saut ×3 au pas 500. Moyennes :

| méthode | gauss : couv. globale / 100 post-saut / 400 suivants | t4 : globale / post100 | largeur méd. pré→post | ms/pas |
|---|---|---|---|---|
| split statique (MAPIE SplitConformalRegressor prefit) | 0.643 / 0.401 / 0.39 | 0.689 / 0.472 | 3.23 → 3.23 | ~0 |
| EnbPI MAPIE + update | 0.801 / 0.483 / 0.761 | 0.825 / 0.556 | 3.27 → 7.81 | 8.8 |
| ACI MAPIE γ=0.01 | 0.899 / 0.830 / 0.916 | 0.899 / 0.827 | 3.32 → 10.7 (0.2 bornes ∞ / 1000 pas) | 1.9 |
| ACI MAPIE γ=0.05 | 0.895 / 0.851 / 0.899 | 0.896 / 0.854 | 3.31 → 10.4 (**15.2 bornes ∞** / 1000) | 1.9 |
| **ACI custom γ=0.01 (~10 LOC)** | 0.900 / 0.829 / 0.916 | 0.900 / 0.829 | 3.28 → 11.0 (0 ∞) | 0.26 |
| crepes roulant (300 derniers résidus) | 0.847 / 0.547 / 0.856 | 0.859 / 0.604 | 3.32 → 10.0 | 0.22 |
| **crepes normalisé statique (σ = EWMA causal de |r|)** | 0.891 / **0.845** / 0.887 | 0.899 / **0.858** | 3.40 → 10.4 | ~0 |

Rejeu déterministe graine 0 : identique.

Lecture :
- **Contrôle croisé obtenu** (lacune LAB_PRIOR 012) : ACI MAPIE et ACI maison concordent à ≤0.002 de couverture globale
  et ≤0.002 post-saut ; l'implémentation maison est 7× plus rapide et n'émet pas de bornes infinies.
  MAPIE reste utile comme **oracle de test**, pas comme dépendance de production : `update()` émet un avertissement de changement de
  comportement à chaque appel, `TimeSeriesRegressor` hérite de l'ancienne API (non v1), alpha est arrondi à 2 décimales
  pour servir de clé (VERIFIED code source `mapie/regression/time_series_regression.py`).
- **Normaliser par une vol causale bat l'adaptation** sur ce type de choc : crepes normalisé, sans aucune mise à jour,
  couvre mieux les 100 pas post-saut que toutes les méthodes adaptatives. Pour AurumShift, l'usage direct = bande
  d'incertitude sur le **coût/slippage réalisé** normalisée par la vol/spread du moment (oracle autour de COST_CONTRACT_V1),
  INFERENCE non testée sur données réelles.
- EnbPI : 8.8 ms/pas pour une couverture post-saut de 0.48 → REJECT.

### 2.3 L2c — skfolio HRP vs EW (`l2c_portfolio.py` → `l2c_results.json`)

Walk-forward (fenêtre 250, rebal. 20, 1500 obs OOS, 10 graines, innovations t4, drift nul : on ne compare que le risque).

| univers | méthode | vol ann. OOS | ratio vol vs EW | turnover/rebal. | fit ms |
|---|---|---|---|---|---|
| A5 (2 majors, 2 alts, 1 calme) | EW | 0.603 | 1.00 | 0 | 0.03 |
| | InvVol skfolio | 0.359 | 0.60 | 0.020 | 8 |
| | HRP skfolio | 0.201 | 0.33 | 0.044 | 17 |
| | HRP riskfolio | 0.201 | 0.33 | 0.044 | 28 |
| | MinVar + LedoitWolf skfolio | 0.196 | 0.33 | 0.033 | 26 |
| B2 (forme BTC/DOGE, vol 3 %/6 %, ρ 0.7) | EW | 0.813 | 1.00 | 0 | |
| | InvVol | 0.717 | 0.88 | 0.010 | |
| | **HRP skfolio** | **ValueError** (`argmax of an empty sequence`, `compute_optimal_n_clusters`) | | | |
| | HRP riskfolio | 0.654 | 0.80 | 0.014 | |
| | MinVar LW | 0.592 | 0.73 | 0.008 | (100 % BTC) |

- HRP skfolio et riskfolio identiques à 1.7e-18 (graine 0) ; déterminisme OK.
- **Bug mesuré** : HRP skfolio 1.4.11 par défaut plante avec 2 actifs ; contournement vérifié
  `HierarchicalClustering(max_clusters=1)` → poids 0.802/0.198 = inverse-variance (ce que HRP vaut toujours à N=2).
- Lecture : à 2 actifs BUY-only, « l'optimisation de portefeuille » se réduit à un sizing inverse-vol (3 lignes) ;
  la baisse de vol est mécanique (drift nul). Valeur maintenant ≈ nulle ; valeur future seulement si l'univers PAPER
  dépasse ~5 actifs avec positions simultanées — et alors via le sizing du module risque, jamais comme seconde autorité.

### 2.4 L2d (bonus lane H) — falsification lead/lag & cointégration (`l2d_leadlag.py`, `l2d_pcmci_fdr_check.py`)

n=1000, 50 réplications, taux de rejet à 5 % :

| scénario | Granger a→b | Granger b→a | PCMCI a→b | PCMCI b→a |
|---|---|---|---|---|
| LEAD (vrai a→b lag 1) | 1.00 | 0.00 | 1.00 | 0.16 |
| NULL (indépendants) | 0.08 | 0.02 | **0.30** | 0.08 |
| CONF (facteur commun, a horodaté 1 pas trop tard) | 0.02 | **1.00** | 0.08 | **1.00** |

| scénario | Engle-Granger | Johansen trace r=0 |
|---|---|---|
| COINT (perp = spot + basis AR(1) φ=0.95) | 1.00 | 1.00 |
| RW indépendantes | 0.02 | 0.00 |

Contrôle PCMCI sous NULL (autre graine) : 0.16 sans correction, **0.02 avec `fdr_bh`** (tigramite `get_corrected_pvalues`).
Lecture : les tests standard sont bien dimensionnés, MAIS **un horodatage décalé d'un pas fabrique un lead « certain »**
(100 % pour Granger et PCMCI). Pour C0 (Binance/OKX/Bybit), l'audit d'horodatage (event time vs receive time, PIT)
doit précéder toute étude lead/lag cross-venue ; PCMCI n'apporte rien de plus que Granger+Bonferroni à 2 variables et
exige une correction FDR. statsmodels 0.15 a supprimé le kwarg `verbose` de `grangercausalitytests` (casse d'API mesurée).

### 2.5 L2e (bonus, endpoint quorum) — IC sur outcomes autocorrélés (`l2e_bootstrap_ci.py` → `l2e_results.json`)

AR(1) φ=0.4, bruit t4, n=150 outcomes, moyenne vraie 0, 300 réplications, nominal 95 % :
IC t iid **0.80** ; arch StationaryBootstrap (bloc `optimal_block_length`) **0.89** ; CircularBlockBootstrap 0.88.
SPA (Hansen) et MCS sous nulle : p-values 0.57–0.81, MCS garde les 3 variantes. Bootstrap graine fixée → déterministe.
Lecture : pour l'endpoint « espérance NETTE incrémentale de QUORUM_ONLY_SUPPRESSED », un IC t naïf sur peu d'outcomes
corrélés sur-déclare la significativité ; même le bootstrap par blocs sous-couvre à n=150 → exiger un n minimal pré-déclaré
et rapporter l'IC bootstrap. `arch.bootstrap` (NCSA, 14 paquets) couvre IC par blocs + SPA/StepM/MCS pour comparer A/B/C
sans data-snooping (PAPER_RESULT : Hansen 2005 SPA ; Hansen-Lunde-Nason 2011 MCS).

## 3. Fiches candidats sérieux (détails dans le CSV)

**arch 8.0.0 — `arch.bootstrap`** (H, ORACLE) — VERIFIED PyPI : NCSA, 2025-10-21. MBTM L2e. Rôle : statistique de
l'endpoint quorum (IC par blocs, SPA/MCS pour A/B/C). Aucun risque de seconde autorité (analyse offline sur Outcomes déjà
produits par le cœur). → **ADOPT_NOW** (outil d'analyse labo/Retex, pas dans le chemin d'exécution).

**statsmodels 0.15.0** (H, ORACLE) — VERIFIED BSD-3, 2026-08-27. MBTM L2d. Coint/Johansen/VECM pour basis spot/perp
(surface « basis » du canari C0). Piège : MarkovRegression `.fit()` plein échantillon = paramètres lookahead même avec
`filtered_marginal_probabilities` ; `smoothed_*` = lookahead. → **BENCH_NOW** sur données C0 réelles (basis BTC spot/perp OKX).

**crepes 0.9.1** (F, ORACLE) — VERIFIED BSD, 2026-06-12. MBTM L2b. Conformal normalisé = la meilleure couverture
post-choc mesurée pour un coût ~0. → **BENCH_NOW** comme oracle de bande de coût réalisé.

**MAPIE 1.5.0** (F, ORACLE) — VERIFIED BSD-3, 2026-08-05. MBTM L2b : concordance avec ACI maison. → **BENCH_NOW** (oracle
de test de l'ACI maison) ; EnbPI → REJECT.

**changepoint_online 1.2.1 (Focus)** (F, SHADOW) — VERIFIED GPL-3 (classifier + LICENSE), 2025-01-03 ; auteurs Lancaster
(Romano, Fearnhead, Eckley…). MBTM L2a. → **BENCH_NOW** avec nulle réaliste / NPFocus ; GPL = usage interne seulement.

**River 0.26.1** (F, SHADOW) — VERIFIED BSD-3, 2026-08-21 ; notes de version 0.26.0 (VERIFIED) : covariance online
(EwaCovariance, LedoitWolfCovariance, OAS, EwaPrecision) ajoutées ; correction d'un bug `Pipeline.transform_many` qui
ré-apprenait l'étape finale sur les données transformées (pertinent PIT) ; 0.25 : ADWIN réécrit en Rust, bit-identique
(VENDOR_CLAIM, parity fuzz 3.8k pas). MBTM L2a : PageHinkley utilisable comme moniteur simple. → **SHADOW**
(moniteur de drift sur résidus coût/slippage/latence, jamais gate de décision).

**ruptures 1.1.10** (F) → PARK (offline, RetexV1 a posteriori uniquement, étiqueté LOOKAHEAD).
**skchange 0.18.0** (F) — actif (2026-08), mais uniquement offline ; API renommée → WATCH.
**skfolio 1.4.11** (G) — bug 2 actifs mesuré ; → PARK jusqu'à un univers PAPER multi-actifs.
**Riskfolio-Lib 7.4.0** (G) — 85 paquets/963 Mo, vectorbt en dépendance dure → REJECT (oracle offline au plus).
**tigramite 5.2.10.1** (H) — VERIFIED GPL-3+ ; FP élevés sans FDR ; → PARK.
**hmmlearn 0.3.3** — VERIFIED README « limited-maintenance mode » → REJECT. **filterpy** (2018), **bocd** (2019),
**bayesian_changepoint_detection** (2019 dev), **nonlinshrink** (2019) → REJECT (abandonnés).
L0 seulement (métadonnées PyPI) : sktime 1.2.0, TorchCP 1.2.1 (LGPL-3, VERIFIED LICENSE), puncc 0.9.3, conformal-tights 0.5.0 (MIT),
online-cp 0.3.0, dynamax 1.0.2, NumPyro 0.22.0, PyMC 6.3.2 (py≥3.12), PyPortfolioOpt 1.6.0, cvxpy 1.9.3, cvxportfolio 1.5.1 (GPL-3),
universal-portfolios 0.4.17 (FMIT), causal-learn 0.1.4.8, lingam 1.13.0, linearmodels 7.0, statsforecast 2.1.1,
PyWavelets 1.10.0 (py≥3.12), networkx 3.7 (py≥3.12).

## 4. Red-team (une ligne chacun)

- arch.bootstrap : le bootstrap par blocs sous-couvre encore à petit n (0.89 pour 0.95) — ne remplace pas un n minimal pré-déclaré.
- statsmodels coint/Granger : significatif ≠ exploitable (LAB_PRIOR 011 : lead-lag tué par les coûts) ; horodatages faux = leads faux.
- crepes normalisé : ne vaut que si σ est causal et bon ; une erreur de σ (stale feed) casse la couverture silencieusement.
- MAPIE ACI : bornes infinies possibles (γ élevé) → tout consommateur doit traiter ∞ explicitement (≠ ZERO).
- Focus : excellent en gaussien, 90 % FA sous queues épaisses avec seuil naïf ; GPL.
- River PageHinkley : seuil dépendant de l'échelle → nécessite normalisation ; déclencheurs ≠ régimes économiques.
- skfolio/HRP : à N=2 c'est de l'inverse-vol déguisé ; risque de créer une seconde autorité de sizing.
- tigramite : graphes « causaux » sur données observationnelles = prédictifs au mieux (LAB_PRIOR 015).

## 5. UNKNOWN

- Comportement sur données réelles C0 (queues, microstructure, trous de flux) : rien n'a été exécuté sur marché réel ici.
- NPFocus (variante non paramétrique de changepoint_online) : non benché ; c'est le prochain test logique contre les queues épaisses.
- Agrément MAPIE/crepes vs l'ACI à rétroaction retardée de LAB_PRIOR 012 (ici rétroaction immédiate seulement).
- Activité GitHub (issues, commits) : API GitHub refusée dans cette session ; maintenance inférée des dates PyPI et README bruts.
- Valeur de G (portefeuille) tant que l'univers PAPER = 2 actifs : ~nulle par construction ; seuil d'utilité (nb d'actifs) UNKNOWN.

## 6. Commandes clés exécutées

```
uv venv -p 3.11 venvs/laneFGH
VIRTUAL_ENV=venvs/laneFGH uv pip install river ruptures mapie crepes skfolio riskfolio-lib tigramite statsmodels arch
VIRTUAL_ENV=venvs/laneFGH uv pip install skchange hmmlearn venn-abers filterpy pyportfolioopt bocd changepoint-online bayesian-changepoint-detection
for p in ...; do uv venv depw/$p; uv pip install $p; uv pip list | wc -l; du -sm site-packages; done   # poids deps
curl https://pypi.org/pypi/<pkg>/json                                                                 # versions/licences/dates
python l1_smoke.py ; python l2a_changepoint.py ; python l2b_conformal.py ; python l2c_portfolio.py
python l2d_leadlag.py ; python l2d_pcmci_fdr_check.py ; python l2e_bootstrap_ci.py
```
Durées : L2a ~13 min (4 processus ; ruptures causal 800 s à lui seul), L2b ~5 min, L2c ~1 min, L2d ~6 min, L2e 6 s.
