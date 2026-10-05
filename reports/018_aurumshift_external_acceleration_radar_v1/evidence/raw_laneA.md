# raw_laneA — Expérience causale quorum + inférence sur données dépendantes

Mission AURUMSHIFT_EXTERNAL_ACCELERATION_RADAR_V1, lane A. Date sandbox 2026-10-05. Recherche externe uniquement :
aucun code, base, credential ou chemin d'exécution AurumShift lu ni touché. Ce document ne dit PAS qu'un candidat est
compatible avec AurumShift ; l'arbitrage final se fait contre le dépôt réel.

Étiquettes : VERIFIED_FACT (source primaire lue, URL), MEASURED_BY_THIS_MISSION (exécuté ici), UPSTREAM_BENCHMARK,
PAPER_RESULT, VENDOR_CLAIM, INFERENCE, UNKNOWN.

## 0. Ce qui existe déjà au labo (ne pas refaire)

- LAB_PRIOR 015 : bootstrap circulaire par blocs de 48 barres codé à la main, Holm sur famille gelée, nulle par décalage circulaire.
- LAB_PRIOR 011 : t de Newey-West net + BH-q sur 15 tests primaires (implémentation maison).
- LAB_PRIOR 013/014 : bootstrap apparié sur seeds (synthétique, iid par construction).
- LAB_PRIOR 017 : `arch` listé PARK (NCSA, « hors des gaps testés », non exécuté).
- LAB_PRIOR 012 : conformal/ACI ; marginal coverage ≠ fiabilité de décision.

Apport nouveau ici : (1) `arch` exécuté et ré-classé pour l'endpoint quorum ; (2) oracle indépendant `tsbootstrap` de la
longueur de bloc ; (3) premier essai réel des confidence sequences (confseq) et de leur coût en largeur, y compris la
dépendance à une borne déclarée ; (4) statut licence/maintenance actuel de toute la pile causale/séquentielle.

## 1. Cadrage statistique de l'endpoint (INFERENCE)

Sur le MÊME DecisionInput gelé, A (quorum=2), B (quorum=1, shadow) et C (single-family, shadow) produisent chacun une
décision déterministe. C'est un **design apparié intra-input**, pas une expérience randomisée ni un problème de propension :
la « traitement » (quorum) est une fonction déterministe de l'input, et l'on observe les deux bras de décision pour chaque input.
Le seul contrefactuel est l'**Outcome** de B (et C) quand A ne trade pas : il n'est pas exécuté.

Endpoint naturel : pour chaque candidat i ∈ QUORUM_ONLY_SUPPRESSED, `d_i = net_outcome_B(i) − 0` (A s'abstient) ; même chose
pour QUORUM_PLUS_OTHER_GATE ; contraste = E[d | QUORUM_ONLY] − E[d | QUORUM_PLUS_OTHER]. Donc l'inférence se réduit à
**une moyenne (ou différence de moyennes) d'une série de P&L nets autocorrélés, indexée par le temps de décision, petit n**.
Conséquences :
1. Les outils causaux génériques (DML, meta-learners, propensity, OPE) répondent à une question qui n'est pas posée ici
   (confusion / politique de logging stochastique). Ils sont surdimensionnés (§5).
2. Le vrai risque de biais est l'**honnêteté du shadow outcome** (fill, coûts, sortie, interaction avec les limites de position),
   pas l'estimateur. Aucune bibliothèque d'inférence ne le résout (§6).
3. La dépendance vient de : chevauchement des horizons de détention (P&L de décisions voisines partagent le même chemin de prix),
   régimes, et corrélation BTC/DOGE simultanée → HAC avec lag ≥ horizon de détention max en unités de décision, ou bootstrap
   par blocs, ou cluster/Driscoll-Kraay par horodatage.
4. Si l'opérateur regarde les résultats en continu (forward PAPER), un IC à n fixe devient invalide (peeking) → soit
   plan préenregistré à n fixé, soit confidence sequence (CS) anytime-valid. Le coût de la CS est mesuré en §4.

## 2. Hands-on — commandes et environnement

- venv : `uv venv -p 3.11 venvs/laneA` (scratchpad) ; script reproductible `bench/laneA/setup_venv.sh`.
- Installation séquentielle dans un venv commun (MEASURED_BY_THIS_MISSION, cache uv chaud, secondes) : numpy/scipy/pandas 1.6 ;
  arch 0.9 ; pingouin 0.55 ; arviz 0.30 ; recombinator 2.0 ; tsbootstrap 0.47 ; doubleml 1.1 ; econml 0.8 ; dowhy 2.6 ;
  causalml 5.0 ; spotify-confidence 2.6 ; quantstats 0.76. **Échecs** : confseq (rc=1), expectation (rc=1, requiert Python ≥3.12),
  obp (rc=1, `pyyaml==5.4.1` épinglé via obp 0.5.5 ne compile plus : `AttributeError: 'build_ext' object has no attribute 'cython_sources'`).
- Venv commun final : 172 paquets, 2,0 Go (dominé par causalml/econml/shap/xgboost/lightgbm).
- Empreinte par bibliothèque, venv neuf Python 3.11 (MEASURED_BY_THIS_MISSION, `bench/laneA/install_footprint.tsv`,
  cache uv probablement partiellement chaud → temps indicatifs) :

| paquet | s install | taille venv | nb paquets |
|---|---|---|---|
| arch | 1.6 | 265 Mo | 14 |
| statsmodels | 2.0 | 262 Mo | 13 |
| tsbootstrap | 1.8 | 182 Mo | 10 |
| pingouin | 3.3 | 380 Mo | 29 |
| arviz (0.23.4) | 3.4 | 318 Mo | 21 |
| recombinator | 5.2 | 447 Mo | 30 |
| quantstats | 3.9 | 349 Mo | 35 |
| spotify-confidence | 5.2 | 443 Mo | 67 |
| doubleml | 4.2 | 500 Mo | 40 |
| econml | 5.3 | 523 Mo | 25 |
| causalpy | 6.6 | 658 Mo | 76 |
| dowhy | 7.9 | 846 Mo | 48 |
| causalml | 12.2 | 1 317 Mo | 48 |

(Le venv vide + pip pèse ~150–180 Mo : numpy/scipy/pandas expliquent l'essentiel du socle.)

### confseq : réparation (≈10 min, dans la limite de 15 min)
- `uv pip install confseq` → échec CMake `Could NOT find Boost` (MEASURED). Après `apt-get install libboost-dev` → échec C++ :
  `invalid use of incomplete type 'PyFrameObject'` — le `pyproject.toml` épingle `pybind11~=2.6.0`, incompatible Python 3.11.
- Patch 1 : `pybind11>=2.11` → build OK (12 s). Patch 2 : `np.float_` (supprimé en NumPy 2) → `np.float64` (5 occurrences,
  `misc.py`, `types.py`). Patch total 6 lignes : `bench/laneA/confseq_py311_numpy2.patch`, commit amont `5ffe733`.
- Constat : la partie « betting » (WSR 2024) est **Python pur** (`betting.py` 981 lignes + `betting_strategies.py`, `misc.py`,
  `predmix.py` ; numpy/scipy/matplotlib/multiprocess). Seules les bornes Howard et al. (`boundaries`, `quantiles`) sont en C++/Boost.
  → vendorisation MIT de ~1,2 k lignes Python possible sans toolchain C++ (INFERENCE).

## 3. L1 smoke (MEASURED_BY_THIS_MISSION, `bench/laneA/l1_smoke.py` → `l1_smoke_results.json`)

Toutes rc=0 après fix. Temps du premier énoncé d'import en sous-processus frais, 2e exécution (pyc chauds) :
arch 1.96 s (1re exécution 4.6 s, compilation numba/pyc) ; statsmodels 1.61 ; pingouin 1.67 ; arviz 2.64 ; tsbootstrap 1.24 ;
recombinator 0.37 ; doubleml 2.38 ; econml (LinearDML) 3.10 ; dowhy 2.83 ; causalml (meta) 3.28 ; spotify_confidence 1.53 ;
quantstats 1.71. (confseq : le premier énoncé mesuré est `import numpy` → 0.14 s, non représentatif.)
Appels triviaux OK : `arch.optimal_block_length`, OLS HAC + `multipletests`, `confseq.betting.betting_cs`, `pingouin.tost`,
`arviz.ess`, `quantstats.stats.probabilistic_sharpe_ratio`.

## 4. L2 — intervalles sur différences appariées AR(1) φ=0,3 (MEASURED_BY_THIS_MISSION)

Script `bench/laneA/l2_paired_diff_intervals.py` → `l2_results.json`. d_t = μ + e_t, e AR(1) φ=0,3, innovations Student-t(4)
standardisées, variance marginale ≈ 1 ; n ∈ {60, 200}, μ ∈ {0 ; 0,25}. Seeds 20261005+i. Niveau 95 %.

### 4.1 Intervalles (une réalisation par cas)

| cas | naive t | HAC NW (statsmodels) | Stationary bootstrap opt (arch) | CBB opt (arch) | CS betting K=8 (confseq) | CI betting n fixe |
|---|---|---|---|---|---|---|
| n=60 μ=0 | [-0.348, 0.042] w .390 | [-0.368, 0.062] w .430 | [-0.345, 0.056] w .401 | [-0.347, 0.057] w .404 | [-1.056, 0.784] w 1.84 | w 2.10 |
| n=60 μ=.25 | [0.269, 0.734] w .464 | [0.175, 0.828] w .653 | [0.182, 0.827] w .645 | [0.185, 0.823] w .639 | [-0.480, 1.376] w 1.86 | w 2.10 |
| n=200 μ=0 | w .250 | [-0.266, 0.038] w .304 | [-0.255, 0.024] w .279 | w .284 | [-0.432, 0.192] w .624 | w .656 |
| n=200 μ=.25 | w .281 | [-0.066, 0.277] w .343 | [-0.059, 0.266] w .326 | w .345 | [-0.224, 0.416] w .640 | w .672 |

- HAC et bootstrap stationnaire concordent (écarts de bornes ≤ 0,03 sd) → cohérents.
- Longueurs de bloc optimales (Politis-White 2004 + correction Patton-Politis-White 2009) : b_SB 1,6–3,7 ; b_CB 1,9–4,2.
  NW maxlags = floor(4(n/100)^(2/9)) = 3 (n=60), 4 (n=200).
- **Déterminisme** : arch SB avec `seed=np.random.default_rng(s)` → IC identique bit-à-bit en ré-exécution ; seed différent → écart
  ≤ 0,01. confseq betting_cs : déterministe (pas d'aléa). tsbootstrap `random_state` → identique en ré-exécution.
- Temps (n ≤ 200, après warm-up) : HAC 0,5 ms ; optimal_block_length 0,7 ms ; SB B=2000 40–56 ms ; CBB ~45 ms ;
  betting_cs 150–200 ms ; ESS acf 0,2 ms ; arviz.ess 0,8 ms. Premier appel : HAC 0,46 s, optimal_block_length 0,67 s,
  arviz.ess 1,7 s (coûts d'initialisation). Exécution complète du script (4 cas + démo SPA) : 7,0 s.
- La CS est un intervalle **anytime-valid** : on peut la regarder après chaque Outcome. Son prix : ×4,3 (n=60) à ×1,9 (n=200)
  la largeur HAC avec K=8 sd.

### 4.2 Sensibilité de la CS à la borne déclarée (`l2_cs_bound_sensitivity.py`)
La CS betting exige des données bornées ; un P&L net n'est borné que si l'on déclare une borne a priori (stop, taille, horizon).
Ratio largeur CS / largeur HAC :

| cas | K=3 | K=4 | K=8 | K=16 |
|---|---|---|---|---|
| n=60 μ=0 | 1.79 | 2.27 | 4.28 | 8.49 |
| n=60 μ=.25 | 1.24 (2 % clippé) | 1.52 | 2.84 | 5.59 |
| n=200 μ=0 | 1.10 (1 % clippé) | 1.29 | 2.05 | 3.89 |
| n=200 μ=.25 | 1.10 | 1.19 | 1.87 | 3.55 |

→ À petit n, la largeur est ~proportionnelle à K. Une borne serrée mais violée (clip) biaise la moyenne ; une borne lâche
rend la CS inutile. La CS n'est pertinente que si AurumShift peut **déclarer contractuellement** une borne de P&L par candidat
(INFERENCE).

### 4.3 Mini-contrôle de couverture (R=200, μ=0 ; PAS le grand bench de l'orchestrateur) — `l2_mini_coverage.json`
Erreur Monte Carlo ≈ ±0,015–0,02.

| n | naive t | HAC NW (t, correction) | SB opt (B=499) | CS betting K=8 | CS betting sur moyennes de lots |
|---|---|---|---|---|---|
| 60 | 0.885 (w .487) | 0.930 (w .581) | 0.885 (w .524) | 1.000 (w 1.86) | 1.000 (w 3.39) |
| 200 | 0.845 (w .268) | 0.930 (w .338) | 0.915 (w .321) | 1.000 (w .624) | 1.000 (w 2.16) |

- Naive t sous-couvre (0,85–0,89) : l'autocorrélation φ=0,3 n'est pas négligeable.
- **Le bootstrap stationnaire avec bloc optimal sous-couvre à n=60 (0,885, comme le naïf)** : le sélecteur PW choisit des blocs
  courts (b≈1,6–3) à petit n. HAC t corrigé est le plus proche du nominal (0,93) aux deux tailles.
- La CS sur-couvre (1,000) : très conservatrice à ce K. La version « moyennes de lots » (pour atténuer la violation
  d'hypothèse de dépendance) est inutilisable à ces n (×6 la largeur HAC).
- Hypothèse de la CS : validité pour des observations dont la moyenne **conditionnelle** est constante (cadre martingale) — un
  AR(1) sur d la viole formellement (E[d_t|passé] ≠ μ). La sur-couverture observée ici ne prouve pas la validité en général
  (INFERENCE ; Waudby-Smith & Ramdas traitent iid/sans remise, abstract arXiv 2010.09686 lu ; le cadre exact de dépendance
  autorisée n'a pas été relu dans le corps du papier → UNKNOWN pour la formulation précise).

### 4.4 ESS
| cas | ESS acf (statsmodels, troncature 1er ρ≤0) | arviz.ess | théorie AR(1) n(1−φ)/(1+φ) |
|---|---|---|---|
| n=60 μ=0 | 43.8 | 44.8 | 32.3 |
| n=60 μ=.25 | 23.9 | 18.7 | 32.3 |
| n=200 μ=0 | 120.8 | 116.8 | 107.7 |
| n=200 μ=.25 | 117.8 | 123.7 | 107.7 |
Les deux estimateurs concordent entre eux mais sont bruités à n=60 (±40 % autour de la théorie). ESS = diagnostic, pas une décision.

### 4.5 TOST / équivalence
`statsmodels.stats.weightstats.ttost_paired` et `pingouin.tost` supposent l'indépendance (MEASURED : p_iid 0,088–0,093 à n=200 μ=0/0,25,
marge ±0,2). Version dépendance-robuste = « IC HAC 90 % inclus dans la marge » (équivalence TOST ↔ inclusion d'IC à 1−2α),
3 lignes avec statsmodels. Aucune des 4 réalisations n'établit l'équivalence à ±0,2 sd (attendu à ces n).

### 4.6 Sharpe probabiliste / déflaté / MinTRL
- PSR maison (formule Bailey & López de Prado, 6 lignes) vs `quantstats.stats.probabilistic_sharpe_ratio` 0.0.86 :
  0.0723/0.07268 ; 1.0000/0.99997 ; 0.0383/0.03834 ; 0.9230/0.92295 → **accord ≤ 4e-4** (MEASURED). Le code quantstats contient un
  commentaire de correction récente (« kurtosis() returns excess kurtosis … convert rather than subtracting 3 a second time ») →
  un bug historique y a existé (VERIFIED_FACT, source installée `quantstats/stats.py` l.1349).
- quantstats n'a ni DSR ni MinTRL ; SR* fixé à 0 (VERIFIED_FACT, source). DSR seuil SR0 et MinTRL codés en ~10 lignes.
  Exemple n=200 μ=0,25 : SR/obs 0,105 → MinTRL ≈ 266 observations à 95 % (MEASURED) — ordre de grandeur utile pour annoncer
  « N nécessaire » au forward PAPER.
- Limite : PSR/DSR supposent iid (non-normal mais indépendant) ; avec autocorrélation il faut la variante d'Opdyke (2007) ou
  un bootstrap — non implémenté (INFERENCE).

### 4.7 Comparaisons multiples A/B/C (démo fonctionnelle, `spa_stepm_mcs_demo`)
arch `SPA` (Hansen 2005), `StepM` (Romano-Wolf 2005), `MCS` (Hansen-Lunde-Nason 2011) sur 3 bras synthétiques n=200 (B meilleur
de 0,15/obs) : SPA p=0 (0,04 s), StepM retient B, MCS(10 %) garde B seul. statsmodels `multipletests` : BH/BY/Holm
fonctionnels (MEASURED). Pour 2–3 bras et 2 strates (QUORUM_ONLY vs QUORUM_PLUS_OTHER), Holm suffit ; SPA/StepM utiles seulement
si l'on explore une grille de quorums/seuils (INFERENCE).

### 4.8 Oracle croisé tsbootstrap vs arch (`l2_oracle_crosscheck.py`)
- Longueurs de bloc SB/CB : **identiques à 1e-15** entre arch 8.0.0 et tsbootstrap 0.7.3 (ré-implémentation PW+PPW indépendante,
  `tsbootstrap/block/pwsd.py`) (MEASURED).
- IC SB (B=2000) : arch [-0.350, 0.060] vs tsbootstrap [-0.350, 0.042] (n=60 μ=0) ; [-0.0526, 0.2582] vs [-0.0560, 0.2562] (n=200 μ=.25).
  Écart attribuable à l'aléa et au fait que **tsbootstrap n'accepte qu'un bloc moyen ENTIER** (pydantic rejette 1.64 ; « auto » arrondit
  au plafond), arch accepte un réel. Différence sémantique à connaître (MEASURED).

## 5. Fiches candidats

### 5.1 arch 8.0.0 — ADOPT_NOW (MODULE d'inférence, aucune autorité)
- VERIFIED_FACT : licence NCSA (texte « University of Illinois/NCSA » — `LICENSE.md` : « deal with the Software without restriction …
  Neither the names of Kevin Sheppard … ») ; PyPI 8.0.0 du 2025-10-21, Python ≥3.10 ; dépôt actif : dernier commit 2026-09-27,
  76 commits / 8 auteurs sur 12 mois (git clone, MEASURED). https://github.com/bashtage/arch | https://pypi.org/project/arch/
- Fournit : IID/Stationary/Circular/MovingBlock bootstrap, `optimal_block_length` (PW 2004 + PPW 2009), `conf_int` (percentile,
  basic, studentized, norm, bc, bca), SPA/RealityCheck, StepM, MCS (VERIFIED_FACT, source installée).
- Remplace : le bootstrap circulaire maison de LAB_PRIOR 015 et le sélecteur de bloc ; SPA/StepM/MCS non triviaux à recoder.
- Red-team : à petit n le bloc optimal est court → SB sous-couvre (0,885 à n=60, MEASURED) ; ne pas l'utiliser seul comme verdict à n<100.

### 5.2 statsmodels 0.15.0 — ADOPT_NOW
- VERIFIED_FACT : BSD-3-Clause, PyPI 0.15.0 du 2026-08-27. Fournit OLS `cov_type='HAC'` (Newey-West, `use_correction`),
  `'hac-groupsum'` (Driscoll-Kraay), `'cluster'`, `multipletests` (bonferroni, holm, holm-sidak, fdr_bh, fdr_by, fdr_tsbh…),
  `ttost_paired`, `acf` (source installée). https://pypi.org/project/statsmodels/
- Rôle : estimateur primaire (HAC t corrigé = meilleure couverture du mini-contrôle, 0,93). Régime : régression de d sur
  indicatrices de régime avec HAC ou Driscoll-Kraay par horodatage (BTC/DOGE simultanés).
- Red-team : la sous-couverture résiduelle (0,93 vs 0,95) à petit n ; le choix du lag doit couvrir l'horizon de détention.

### 5.3 tsbootstrap 0.7.3 — SHADOW (oracle de arch)
- VERIFIED_FACT : MIT ; PyPI 0.7.3 du 2026-09-29 ; 237 commits / 3 auteurs sur 12 mois (très actif, API mouvante : README
  annonce adaptateurs, « fused statistics », MCP). UPSTREAM_BENCHMARK : « 4.7x to 33x » plus rapide qu'arch à n=2000 — non pertinent à n≤200.
- MEASURED : bloc optimal identique à arch ; IC SB cohérent ; déterministe ; bloc moyen entier uniquement.
- Rôle : oracle indépendant de non-régression pour la couche bootstrap. Red-team : churn d'API (0.x), bus factor ~1–3.

### 5.4 confseq 0.0.11 — BENCH_NOW (moniteur séquentiel, vendorisé)
- VERIFIED_FACT : MIT (`LICENSE`, « Copyright (c) 2021 confseq developers ») ; dernière release PyPI 2023-01-26 (sdist seul) ;
  dernier commit 2026-01-06 (CI), sinon 2024 ; 191/227 commits par I. Waudby-Smith (bus factor ~1).
  https://github.com/gostevehoward/confseq | https://pypi.org/project/confseq/
- MEASURED : ne s'installe pas tel quel (Boost + pybind11 2.6 + NumPy 2) ; 6 lignes de patch ; ensuite déterministe, 0,15–0,2 s
  par CS à n≤200 ; largeur ×1,1–×8,5 HAC selon K.
- Papiers : Howard, Ramdas, McAuliffe, Sekhon, « Time-uniform, nonparametric, nonasymptotic confidence sequences »,
  Annals of Statistics 49(2), 2021 (arXiv 1810.08240, VERIFIED_FACT) ; Waudby-Smith & Ramdas, « Estimating means of bounded random
  variables by betting », JRSSB 2024, doi 10.1093/jrsssb/qkad009 (arXiv 2010.09686, VERIFIED_FACT).
- Rôle proposé : moniteur « arrêt pour nuisance/futilité » anytime-valid en parallèle d'une analyse primaire à n préenregistré.
- Red-team : exige une borne de P&L déclarée ; hypothèse de moyenne conditionnelle constante violée par l'autocorrélation.

### 5.5 expectation 0.6.1 — REJECT (licence)
- VERIFIED_FACT : PyPI `GPL-3.0-only AND LicenseRef-AI-Training-Prohibited`, Python ≥3.12 ; `README_AI_NOTICE.md` : « You may NOT use
  this code to train, fine-tune, or develop AI/ML models » ; terme additionnel dans `LICENSE` (levée seulement par écrit). Actif
  (116 commits/12 mois, 4 auteurs). Fonctions intéressantes (e-processus, e-BH, CS). https://github.com/jakorostami/expectation
- Install MEASURED : échec sur Python 3.11. Rejet : copyleft + restriction additionnelle juridiquement ambiguë pour un système de
  décision algorithmique.

### 5.6 savvi 0.3.1 — PARK
- VERIFIED_FACT : MIT, Python ≥3.11, dernier commit 2024-11-04 (0 commit/12 mois). Docs : « confidence intervals and p-values that are
  valid at all sample sizes », cite Ramdas et al. 2023 « Game-theoretic statistics and SAVI ». https://github.com/assuncaolfi/savvi
- Non exécuté (dormant ; confseq couvre le besoin).

### 5.7 safestats (R) 0.8.9 — PARK
- VERIFIED_FACT : CRAN 0.8.9 publié 2026-10-05, LGPL (≥3), mainteneur A. Ly. Tests e-value « safe » t/z/proportions. R → hors pile Python ;
  oracle possible pour un t-test séquentiel. https://cran.r-project.org/package=safestats

### 5.8 spotify-confidence 4.1.0 — PARK
- VERIFIED_FACT : Apache-2.0, PyPI 2026-02-26, 41 commits/12 mois ; README : « non-inferiority margins », « Group sequential tests »
  (spending function, exige `final_expected_sample_size` — source `experiment.py`). 67 paquets / 443 Mo (MEASURED).
- Group-sequential ≠ anytime-valid : il faut planifier N. Conçu pour A/B de proportions/moyennes iid utilisateurs, pas séries dépendantes.

### 5.9 pingouin 0.7.0 — REJECT (redondant + GPL-3.0)
- VERIFIED_FACT : GPL-3.0 (`LICENSE`), PyPI 2026-09-26, Python ≥3.11, actif (41 commits). `tost(paired=True)` iid seulement.
  Redondant avec statsmodels `ttost_paired` (BSD). Le copyleft n'empêche pas l'usage interne de recherche mais n'apporte rien ici.

### 5.10 arviz (0.23.4 installé ; 1.3.0 actuel) — SHADOW (oracle ESS)
- VERIFIED_FACT : Apache-2.0 ; 1.3.0 (2026-08-11) exige Python ≥3.12 → uv a résolu 0.23.4 sur 3.11 (MEASURED). 318 Mo / 21 paquets.
- `arviz.ess` concorde avec l'ESS acf maison (MEASURED). Utile comme oracle ; trop lourd (xarray) pour un simple diagnostic.

### 5.11 recombinator 0.0.6.1 — REJECT
- VERIFIED_FACT : MIT, dernier commit 2022-03-14, 0 commit/12 mois ; 447 Mo / 30 paquets (numba) pour ce que fait arch.

### 5.12 DoubleML 0.11.4 / EconML 0.17.0 / CausalML 0.17.0 / DoWhy 0.14 / CausalPy 0.9.0 — PARK (CausalML : REJECT)
- VERIFIED_FACT (PyPI + git) : DoubleML BSD-3, 495 commits/12 mois, 12 auteurs ; EconML MIT, 35 commits, 6 auteurs ; CausalML Apache-2.0,
  109 commits, 19 auteurs ; DoWhy MIT, 169 commits, 25 auteurs, Python <3.14 ; CausalPy Apache-2.0, 383 commits, 24 auteurs (PyMC).
- MEASURED : empreintes 500 Mo – 1,3 Go ; import 2,4–3,3 s.
- Évaluation honnête (INFERENCE) : l'effet du quorum sur un input donné est **observé pour la décision** (A et B évalués sur le même input),
  il n'y a pas de confusion à corriger ; l'hétérogénéité d'intérêt est sur 2 strates prédéfinies (QUORUM_ONLY vs QUORUM_PLUS_OTHER) et
  quelques régimes → moyennes par strate + HAC suffisent. DML/CATE à n = dizaines–centaines = surapprentissage garanti des effets
  hétérogènes. Seule idée réutilisable : les **réfutations DoWhy** (placebo treatment, random common cause, data subset) → à faire en
  10 lignes : placebo = permutation circulaire du label de strate ; sous-échantillon = par régime/période.
- CausalPy (ITS / synthetic control bayésien) : utile si un jour on compare périodes avant/après changement de quorum ; pas pour ce design.

### 5.13 Open Bandit Pipeline (obp 0.5.7) — REJECT
- VERIFIED_FACT : Apache-2.0, dernier commit 2022-11-04, release PyPI 2023-04-14. MEASURED : installation échoue sur Python 3.11
  (pyyaml 5.4.1 épinglé). INFERENCE : l'OPE (IPS/DR) corrige une politique de logging stochastique ; ici politiques déterministes et
  appariées → les estimateurs IPS sont indéfinis (propension 0/1). Le « shadow outcome » relève d'un rejeu déterministe + coûts, pas d'OPE.

### 5.14 quantstats 0.0.86 — SHADOW (oracle PSR)
- VERIFIED_FACT : Apache-2.0 ; PyPI 2026-09-27 ; 22 commits/12 mois, 3 auteurs. PSR conforme (MEASURED, ≤4e-4). Pas de DSR/MinTRL.
- Rôle : oracle de non-régression du PSR maison. Ne pas l'importer dans le cœur (35 paquets, matplotlib/seaborn, rapports HTML).

### 5.15 mlfinlab — REJECT
- VERIFIED_FACT : dépôt public = suivi de bugs uniquement, dernier commit 2021-12-01, licence propriétaire « Copyright Protection Notice
  and Licensing Agreement » ; pas sur PyPI (404). VENDOR_CLAIM (hudsonthames.org/mlfinlab) : Business « £100 (+VAT) per month, per user »,
  Enterprise sur devis → TIER_B ; inclut « deflated and haircut sharpe ratios … minimum track record length ».
- Rejet : formules publiques (Bailey & López de Prado, JPM 40(5) 2014, SSRN 2460551, VERIFIED_FACT) implémentées en ~20 lignes ici.

### 5.16 multipy 0.16 — REJECT
- VERIFIED_FACT : BSD-3 révisée, release 2019-04-18, dernier commit 2020-10-27. statsmodels couvre BH/BY/Holm.

### 5.17 e-BH (méthode) — WATCH
- PAPER_RESULT : Wang & Ramdas, « False discovery rate control with e-values », JRSSB 84 (2022) 822–852, arXiv 2009.02824 :
  e-BH contrôle le FDR sous dépendance arbitraire entre e-values. Pertinent seulement si de nombreux tests séquentiels simultanés
  (grille de quorums × régimes × actifs). Implémentation = 5 lignes ; aucune lib nécessaire.

### 5.18 mSPRT / always-valid p-values — PARK
- INFERENCE : le mSPRT à mélange normal (Johari et al., « Always valid inference », plateformes A/B) correspond à
  `confseq.boundaries.normal_mixture_bound` (C++) ; hypothèse sous-gaussienne de variance connue → fragile pour P&L à queues épaisses.
  Référence non relue ici (UNKNOWN : version/journal exacts non vérifiés dans cette session).

### 5.19 R boot 1.3-32 / tseries 0.10-63 / np 0.70-5 / blocklength 0.2.2 — PARK (oracles R éventuels)
- VERIFIED_FACT (CRAN) : boot 1.3-32 (2025-08-29, « Unlimited ») ; tseries 0.10-63 (2026-08-11, GPL-2|3, `tsbootstrap()`) ;
  np 0.70-5 (2026-07-15, GPL, `b.star()` = sélecteur PW) ; blocklength 0.2.2 (2025-03-08, GPL). Inutile tant que tsbootstrap sert d'oracle Python.

### 5.20 Préregistration / reproductibilité
- **Motif retenu (ADOPT_NOW, custom trivial)** : plan d'analyse en Markdown (endpoint, strates, N cible, estimateur primaire HAC,
  lag, règle d'arrêt CS, marge TOST, correction Holm) → `sha256sum` → commit git signé/horodaté AVANT le premier Outcome ;
  le hash est recopié dans chaque RetexV1. Zéro dépendance.
- OSF Registries — ADOPT_NOW optionnel (témoin externe) : VERIFIED_FACT (help.osf.io) « frozen version … can never be edited or
  deleted », embargo « up to four years ». Prix non affiché sur la page lue (UNKNOWN_PRICE ; réputé gratuit, non vérifié).
- AsPredicted — PARK : VERIFIED_FACT « Pre-registration remains private until an author makes it public » ; prix non affiché (UNKNOWN_PRICE) ;
  formulaire orienté psychologie.
- DVC 3.67.1 (Apache-2.0, 2026-03-31) / DataLad 1.6.5 (MIT, 2026-09-30) — REJECT pour ce besoin : versionnage de données lourd
  (git-annex pour DataLad) alors que l'autorité de lignée existe déjà côté AurumShift (risque de 2e autorité de provenance).

## 6. Shadow outcome honnête (ce qu'aucune lib d'inférence ne fait) — INFERENCE
1. Le P&L de B sur un candidat supprimé par A doit être calculé par le **même** moteur de coûts (COST_CONTRACT_V1) et la même règle de
   sortie, sur données PIT postérieures à la décision ; UNKNOWN_COST → exclure ou borner, jamais 0.
2. Isolation : chaque candidat shadow évalué en « position isolée » (pas d'interaction avec les limites de portefeuille de A), sinon
   l'Outcome de B dépend de l'ordre — à préenregistrer.
3. Biais de fill : B shadow suppose un fill que A n'a pas testé ; l'oracle de coûts (autre lane) doit fournir une borne pessimiste ; analyser
   l'endpoint sous coût central ET pessimiste.
4. Contrôle négatif : appliquer le même pipeline shadow à des trades que A a **réellement** exécutés ; écart shadow vs réel = biais du
   simulateur, à soustraire/rapporter (calibration du shadow).
5. Dépendance : indexer d par temps de décision ; lag HAC ≥ horizon max de détention ; Driscoll-Kraay si BTC et DOGE simultanés.

## 7. Recommandation de pile (INFERENCE)
- Primaire (n fixe préenregistré) : statsmodels OLS HAC (t, correction) sur d ~ strate (+ régime) ; robustesse : arch SB/CBB à bloc
  optimal ET bloc imposé ≥ horizon de détention ; Holm sur ≤ 4 contrastes.
- Moniteur séquentiel : CS betting (confseq vendorisé) sur P&L borné déclaré, uniquement pour arrêt anticipé « nuisance » ; pas pour
  déclarer un gain.
- Annonce de N : MinTRL / PSR (code maison 20 l., oracle quantstats) ; ESS (statsmodels acf, oracle arviz).
- Oracles de non-régression : tsbootstrap (bloc + IC), quantstats (PSR), arviz (ESS).
- Code custom restant : ~80–120 lignes (endpoint, strates, TOST-HAC, PSR/DSR/MinTRL, ESS, e-BH éventuel, placebo).

## 8. UNKNOWN
- Couverture réelle sur P&L crypto avec chevauchement d'horizons et changements de régime (grand bench = orchestrateur).
- Formulation exacte de l'hypothèse de dépendance autorisée par WSR 2024 (corps du papier non relu).
- Prix OSF/AsPredicted (non affiché sur les pages lues).
- Comportement de confseq hors grille (`breaks=1000` → résolution 2K/1000) sur des P&L très asymétriques.
- Disponibilité d'une implémentation maintenue de PSR sous autocorrélation (Opdyke 2007) — non trouvée dans ce temps.
