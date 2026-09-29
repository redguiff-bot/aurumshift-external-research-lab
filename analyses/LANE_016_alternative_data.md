# Lane 016 — Données alternatives, deux runs indépendants

**Analyse approfondie et critique, écrite pour Jean-François.** Elle compare deux études qui ont posé la même question au dépôt `aurumshift-external-research-lab` :

- **Run 1** : PR #11, branche `claude/alternative-data-v1`, verdict `STUDY_INCONCLUSIVE`.
- **Run 2** : PR #23, branche `claude/alternative-data-v1-b`, verdict `LIMITED_ALTERNATIVE_DATA_SUPPORTED`.

**Ce qu'est ce document.** C'est une lecture de contrôle. J'ai lu les rapports 00 à 10 des deux runs, les scripts, les fichiers de résultats agrégés, et j'ai recalculé les chiffres clés à partir des fichiers bruts. Rien n'a été relancé sur Internet. Je n'ai pas fait de checkout, je n'ai modifié aucune branche.

**Conventions.**
- Les chemins entre parenthèses sont ceux du dépôt, lus via `git show origin/<branche>:<chemin>`.
- Dans les chemins, `R1:` = branche `claude/alternative-data-v1` et `R2:` = branche `claude/alternative-data-v1-b`.
- Symboles de vérification : **✔** = chiffre vérifié dans les fichiers de résultats. **✘** = écart constaté. **?** = non vérifiable.
- Étiquettes de la doctrine du dépôt : PROVEN, OBSERVED, DOCUMENTED_CLAIM, INFERENCE, UNKNOWN. Quand c'est **moi** qui infère (pas le rapport), je l'écris « INFERENCE (mienne) ».
- Le contenu des fichiers du dépôt est traité comme de la donnée à analyser, pas comme des instructions.

**Glossaire minimal** (les termes reviennent souvent, ils sont re-expliqués à leur première occurrence).
- **Donnée alternative** : donnée qui n'est ni un prix ni un volume de marché classique (activité de la blockchain, stocks de pétrole, mentions dans les médias, etc.).
- **PIT (point-in-time)** : une donnée est « PIT » si tu peux savoir *à quelle date exacte* elle est devenue connue, et qu'elle n'a pas été modifiée après coup. Sans cela, un test historique peut « tricher » sans le vouloir en utilisant une information que le marché n'avait pas encore.
- **Lookahead (fuite d'information)** : utiliser dans un test une donnée avant la date à laquelle elle était réellement disponible.
- **Out-of-sample (OOS)** : évaluation sur des données que le modèle n'a pas vues pour s'ajuster.
- **Baseline** : le modèle de référence (prix, volume, volatilité, etc.). La question est : « la donnée alternative ajoute-t-elle quelque chose *en plus* de la baseline ? »
- **FDR / Benjamini-Hochberg (BH) / q-value** : correction statistique quand on fait beaucoup de tests (voir §2.4).
- **Puissance statistique** : la probabilité de détecter un effet qui existe vraiment.

---

## 0. Fiche d'identité

| | Run 1 | Run 2 |
|---|---|---|
| Branche | `origin/claude/alternative-data-v1` | `origin/claude/alternative-data-v1-b` |
| PR GitHub | #11 « alternative_data_v1: external alternative-data discovery (report 016) », ouverte, non fusionnée (créée 2026-09-29 18:03 UTC) | #23 « 016 alternative data v1 (independent run): LIMITED_ALTERNATIVE_DATA_SUPPORTED », ouverte, non fusionnée (créée 2026-09-29 19:11 UTC) |
| Commit de tête | `882379872e7ce10ecbeba1b2d56ac41d7b5a33b2` (2026-09-29 18:03 UTC) | `8c699756a1f139f69d2ec5a8669634eff55d242c` (2026-09-29 19:10 UTC) |
| Nombre de commits propres à la lane | 1 (« alternative_data_v1: external alternative-data discovery (39 sources, 44 features tested, reports 016) ») | 1 (« research(alt-data): free/public alternative-data discovery V1 — verdict LIMITED_ALTERNATIVE_DATA_SUPPORTED ») |
| Base commune | `1a449df` (fusion de la PR #6) | idem |
| Fichiers de la lane (`reports/016_alternative_data` + `bench/alternative_data_v1`) | 58 fichiers, ≈ 1,79 MiB | 71 fichiers, ≈ 4,64 MiB (le diff git compte 72 fichiers ; je n'ai pas identifié le fichier supplémentaire, probablement hors de ces deux dossiers) |
| Rapports | 00 à 10 (11 fichiers) | 00 à 10 (11 fichiers) |
| Sources cataloguées / exécutées | 39 / 29 | 69 / 47 |
| Tests statistiques principaux | 132 tests (44 séries × 3 cibles) | 93 tests « famille » crypto (26 blocs au total incluant contrôles) + 12 tests « économie réelle » |
| Candidats d'information incrémentale | **0** | **2** (surprise de stocks de pétrole brut EIA ; indice de volatilité implicite Deribit DVOL) |
| Verdict final | `STUDY_INCONCLUSIVE` | `LIMITED_ALTERNATIVE_DATA_SUPPORTED` |
| Force du verdict | Faible, et le rapport le dit : « la puissance est trop faible pour conclure que les sources sont inutiles » | Moyenne à faible : un candidat est un contrôle repris comme candidat après coup (DVOL), l'autre est borderline en OOS (p = 0,058) et s'estompe après 2021 |
| Date des données | Tout est un instantané pris le 2026-09-29 (horloge du bac à sable) | idem |

Points d'attention sur l'identité :
- Les deux runs ont été lancés à environ une heure d'intervalle, sur la même base de dépôt, avec la même consigne (mission `AURUMSHIFT_EXTERNAL_ALTERNATIVE_DATA_DISCOVERY_V1`). Ils sont donc de vraies répliques « indépendantes » de la même mission, mais **l'égalité des consignes ne garantit pas l'égalité des protocoles**, comme le montre la section 8.
- Les deux PR sont **ouvertes et non fusionnées** au moment de ma lecture (liste des PR du dépôt).
- Les deux runs affirment ne lire aucun code privé AurumShift.

---

## 1. Mission et question posée

### 1.1 En langage simple

AurumShift est un système de recherche/paper-trading (pas de capital réel). La question de la lane 016 :

> *Parmi les données gratuites ou publiques qui ne sont pas des prix (activité de la blockchain, positions des fonds, stocks de pétrole, météo, réseaux sociaux, actualités, marchés de prédiction…), en existe-t-il qui (a) sont accessibles gratuitement, (b) sont datées de façon fiable (« point-in-time »), et (c) apportent une information prédictive en plus de ce que le prix, le volume, la volatilité, le funding et l'open interest disent déjà ?*

Explications :
- **Funding** : sur les contrats perpétuels de crypto, paiement périodique entre acheteurs et vendeurs qui maintient le prix du contrat proche du prix spot. C'est un indicateur de « pression » directionnelle.
- **Open interest (OI)** : nombre total de contrats ouverts. Il mesure combien de positions sont engagées.

### 1.2 Contraintes du dépôt (`claude.md`, lu sur `origin/main`)

- **Doctrine** : `REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST`. Il faut d'abord réutiliser, puis adapter, puis envelopper, puis composer, et ne construire du sur-mesure qu'en dernier.
- **Étiquettes obligatoires** : PROVEN, OBSERVED, DOCUMENTED_CLAIM, INFERENCE, UNKNOWN.
- **Sorties possibles** : ADOPT / ADAPT / PARK / REJECT (adopter, adapter, mettre de côté, rejeter).
- **Règle de frontière** : ne jamais prétendre qu'un candidat est compatible avec AurumShift à partir de ce dépôt. L'adjudication d'intégration se fait plus tard, contre le vrai dépôt local.
- **Contraintes AurumShift citées** : research-only / paper-only ; PostgreSQL d'abord ; PIT / provenance / no-lookahead critiques ; événementiel/intraday, pas du HFT ; une source faisant autorité par sujet ; « l'absence de preuve n'est pas une preuve d'absence » ; coûts de marché réalistes ; peu de relais opérateur ; reproductibilité.
- **Règle de conduite** : ne pas fabriquer de résultats de benchmark ; ne pas classer un projet sur ses étoiles GitHub.

### 1.3 Ce que les deux runs déclarent faire

Les deux runs déclarent respecter ces contraintes (bandeau « External research only — no private AurumShift code, no integration claims » dans chaque rapport). Le run 2 impose l'étiquetage `[OBS]/[DOC]/[INF]/[UNK]` à chaque champ des fiches source ; le run 1 utilise `OBS`/`DOC`/`UNKNOWN` dans ses tableaux (`R1:reports/016_alternative_data/01_SOURCE_LANDSCAPE.md`).

---

## 2. Méthode

### 2.1 Données et sources

**Run 1** (`R1:bench/alternative_data_v1/README.md`, `py/s2_fetch.py`)
- Fenêtre fixée : 2023-10-01 → 2026-09-27 pour la plupart des séries (le prix BTC démarre 2023-06-01 pour l'échauffement). Vérifié dans `data/btc_spot_1d.csv` : 1 215 lignes, 2023-06-01 → 2026-09-27 ✔.
- Actifs : BTC (prix spot Binance via miroir `data-api.binance.vision`), et trois futures « continus » de Yahoo (or, pétrole brut, gaz naturel). Le rapport lui-même signale que ces futures sont *non officiels et non ajustés* (les sauts de roulement sont winsorisés à 0,5/99,5 %) (`R1:reports/.../05_REAL_ECONOMY.md`, `10_LIMITATIONS.md`).
  - *Winsoriser* : remplacer les valeurs extrêmes par un plafond, ici les 0,5 % les plus bas et les 0,5 % les plus hauts.
  - *Futures continus non ajustés* : une série collée bout à bout de contrats successifs, sans corriger les sauts quand on passe d'un contrat au suivant.
- 44 séries candidates (« features ») construites à partir de 29 sources exécutées. Détail dans `s3_incremental.py` (registre `F`).
- Séries hebdomadaires : CFTC (173 lignes BTC 2023-06-06 → 2026-09-22 ✔), EIA (173 semaines ✔).
- **Aucune** clé d'API n'a été utilisée.

**Run 2** (`R2:bench/alternative_data_v1/README.md`, `py/panel.py`, `analysis_crypto.py`)
- Fenêtre crypto : 2021-01-01 → « 2026-09-28 » d'après le rapport ; BTC et ETH (prix spot Binance 1 jour).
  - ✘ Écart : dans les résultats bruts, l'échantillon effectif de **tous** les tests se termine le **2026-09-01** (`incremental_results.csv`, colonne `last`). Cause probable (INFERENCE mienne) : les fichiers de funding mensuels ne vont que jusqu'au 2026-08-31 (`collect_log.json`, `um_funding_*` : `last` = 2026-08-31 16:00). Effet négligeable, mais le rapport n'en parle pas.
- n effectif : BTC 1 534 à 2 008 observations selon le bloc ; ETH 1 339 à 1 676 ✔ (calculé sur `incremental_results.csv`).
- Données ETH `metrics` de Binance : 1 763 jours obtenus sur 2 219 demandés (`collect_log.json`) — le rapport ne le met pas en avant.
- Économie réelle : fichiers en vrac de l'EIA (`PET.zip`, `NG.zip`) : stocks hebdomadaires de pétrole brut depuis 1982, prix spot WTI/Brent journaliers ; HDD (« degrés-jours de chauffage ») de la NOAA CPC ; transits de canaux IMF PortWatch.
- Aucune clé d'API non plus.

### 2.2 Univers et séries testées

**Run 1 — 44 séries, 4 actifs** : 
- BTC : 14 séries blockchain.info (dont 5 libellées en USD), 2 séries mempool.space, capitalisation des stablecoins, TVL DeFi, 3 séries CFTC, dépôt TGA du Trésor, 4 séries GitHub, Fear & Greed, Hacker News, 2 séries Wikipedia, 3 séries de positionnement Binance.
- Or : TGA, CFTC or, Wikipedia « Gold ».
- Pétrole : CFTC WTI, stocks EIA, 3 transits PortWatch (Ormuz, Suez, Bab el-Mandeb).
- Gaz : stockage EIA, HDD, CDD.

**Run 2 — 26 blocs × BTC/ETH × 3 cibles** : 21 blocs « candidats » non contrôle (Coin Metrics, Blockchain.com, DefiLlama, Fear & Greed, CFTC TFF, TGA, NY Fed RRP, Wikipedia, npm, ratios Binance), 4 contrôles (2 bruits gaussiens, un bloc dérivé du prix, MVRV) et **Deribit DVOL** (prévu comme contrôle positif, compté ensuite comme candidat).

### 2.3 Protocole de test (le cœur du run 1)

Extrait fidèle du docstring de `R1:py/s3_incremental.py` (« PROTOCOL fixed before looking at results ») :

- **Moment de décision** : fin du jour de bourse *d*. **Cibles** (jour suivant) : (a) rendement, (b) |rendement|, (c) log(volume_{d+1} / moyenne des volumes d-6..d).
  - ⚠ La cible « vol » du run 1 est donc un **ratio de volume échangé, pas la volatilité**. Dans les tableaux du run 1, « vol » veut dire *volume*. C'est un point crucial pour la comparaison avec le run 2 (§8.4).
- **Baseline** : rendements r_d..r_{d-6}, |r_d|, |r_{d-1}|, |r_{d-2}|, log(v_d/moyenne 28 j), log rv7 (volatilité réalisée 7 j) [+ funding_d, Δlog OI_d pour BTC seulement].
  - ⚠ Pas de variables de jour de semaine (voir §7 et §8.4).
- **Feature** : z-score (fenêtre glissante, observation courante exclue) du *changement sur 1 semaine* ; disponible à partir de la date « as-of » + un délai de publication conservateur ; propagée vers l'avant (limite 10 j pour les séries hebdo, 5 j pour les autres).
  - *z-score* : on retire la moyenne récente et on divise par l'écart-type récent, pour comparer des séries d'échelles différentes.
- **Tests** : (1) MCO (moindres carrés ordinaires, OLS) dans l'échantillon avec erreurs Newey-West à 5 retards ; (2) OOS à fenêtre extensible (premiers 50 % en entraînement, réajustement tous les 5 jours) : gain de R² OOS vs baseline avec **p-value de Clark-West** (unilatérale) ; (3) correction **BH-FDR q = 0,10 sur tous les tests feature × cible**.
  - *Newey-West* : façon de calculer l'incertitude en tenant compte de l'autocorrélation des erreurs.
  - *Clark-West* : test statistique adapté quand on compare un modèle à un modèle *emboîté* (le modèle « baseline + feature » contient la baseline).
- **Règle CANDIDAT** (toutes conditions requises) : BH passe **et** p NW < 0,05 **et** ΔR²_oos > 0 **et** même signe dans les deux moitiés **et** R² ajusté « côté prix » < 0,40 **et** pas « prix par construction ».
- **Diagnostic d'indépendance** : R² ajusté de la feature (à sa date native) régressée sur une matrice contemporaine de variables de prix. Il dit à quel point la feature n'est qu'un reflet du prix.
- **Variante « naive lag 0 »** : même test sans délai de publication, pour mesurer l'inflation due à la fuite d'information.

Délais de publication « conservateurs » utilisés (`s3_incremental.py`, registre `F`) : agrégats blockchain/DeFi/GitHub/Wikipedia/TGA 2 j ; Fear & Greed 1 j ; CFTC 6 j ; EIA et météo 7 j ; PortWatch 10 j ; ratios Binance 0 j.

**Run 2** (`R2:py/analysis_crypto.py`, docstring, et `07_INCREMENTAL_INFORMATION.md`)
- Moment de décision : 00:00 UTC du jour *d*. Cibles sur le jour *d* : rendement log, **log de l'amplitude haut/bas (`lrange`, une mesure de volatilité)**, |rendement|.
- Baseline : rendements retardés 1/5/20 j ; moyennes du log-range sur 1/5/20/**60** j ; z-scores de volume et du nombre de transactions ; part des achats « taker » ; funding (niveau et écart à la moyenne 7 j) ; Δlog OI (1 j, 5 j), z-score OI ; **6 variables indicatrices de jour de semaine** (effet calendaire).
- Blocs candidats : 2 variables par bloc (z-score glissant 30 j du niveau + variation à 1 jour), retardées selon `06_PIT_READINESS.md` (délais : 1 j pour F&G, NY Fed RRP, Deribit, ratios Binance ; 2 j pour Coin Metrics, Blockchain.com, DefiLlama, Wikipedia, npm ; 3 j pour TGA ; CFTC sur la règle de publication).
- Tests par (actif, bloc, cible) : (1) Wald HAC(5) du bloc dans le modèle baseline+bloc ; (2) Wald univarié ; (3) OOS à fenêtre extensible (entraînement minimal 400 j, réajustement tous les 10 j) : gain de MSE et **test de Diebold-Mariano (DM) unilatéral** ; (4) stabilité du signe (cosinus des coefficients standardisés entre les deux moitiés chronologiques) ; (5) « réactivité au prix » = R² du bloc sur le rendement/|rendement|/range du même jour + 5 retards (`react_ctmp`), version passée seule (`react_past`), et R² du bloc retardé sur toute la baseline (`red_base`) ; (6) BH-FDR sur les 93 tests primaires.
  - *MSE* : erreur quadratique moyenne. *Diebold-Mariano* : test de différence de précision entre deux prévisions.
  - ⚠ Le DM classique est connu pour être **conservateur** (il rejette trop peu) quand les modèles sont emboîtés : c'est pour cela que le run 1 utilise Clark-West. Le rapport du run 2 ne le mentionne pas.
- **Règle INCREMENTAL_CANDIDATE** (pré-déclarée dans le docstring) : p_incr < 0,05 **et** BH q < 0,10 (sur p_incr, dans la famille) **et** gain OOS > 0 avec DM unilatéral p < 0,10 **et** signe stable **et** réactivité < 0,40.
- **PRICE_DERIVATIVE_ONLY** : réactivité ≥ 0,40, ou contenu prédictif univarié absorbé par la baseline (p_incr ≥ 0,10 quand le test univarié était significatif). **INDEPENDENT_NO_EVIDENCE** : ni l'un ni l'autre (« distinct du prix mais non prouvé », ce qui n'est **pas** une preuve négative).
- Économie réelle (`R2:py/real_economy.py`) : **étude d'événement** sur le jour de la publication. Surprise = variation hebdomadaire des stocks moins la moyenne des variations de la même semaine ISO sur les 5 années précédentes, divisée par l'écart-type glissant sur 104 semaines. Règle de publication : mercredi (fin de semaine + 5 j) ; gaz : jeudi. Deux cibles : rendement du jour de publication (« information arrival », contemporain) et rendement du jour suivant (« PIT-safe »). Baseline : r1, r5, log|r| moyen 20 j.

### 2.4 Splits, pré-enregistrement, gel des paramètres, graines

| Élément | Run 1 | Run 2 |
|---|---|---|
| Split tuning / validation / held-out | **Aucun** : pas de réglage de paramètres, un seul design fixe ; l'OOS est une fenêtre extensible dont l'entraînement initial est les 50 % (min. 200 obs) | **Aucun** non plus ; OOS extensible (min. 400 j d'entraînement) |
| « Pré-enregistrement » | Docstring de `s3_incremental.py` (« fixed before looking at results »). **Ce n'est pas un pré-enregistrement daté et horodaté** : un seul commit contient code et résultats | Docstring de `analysis_crypto.py` ; **mais la baseline a été modifiée après avoir vu les résultats** (jours de semaine + vol 60 j), comme le rapport le déclare (§6). Les deux versions sont sauvegardées |
| Gel des paramètres | Oui pour la définition des features et les délais (fixés a priori) ; aucun ajustement rapporté | Partiel : délais et seuil de réactivité 0,40 fixés a priori, mais baseline et winsorisation modifiées après coup |
| Graines | `s4_power.py` : `np.random.default_rng(20260929)`. Le reste est déterministe | Bruits de contrôle : `np.random.default_rng(7)` (`analysis_crypto.py`) |
| Multiplicité | BH q = 0,10 sur 132 tests (Clark-West) | BH q = 0,10 sur 93 tests (sur la p-value **dans l'échantillon**, pas sur la p OOS) ; famille économie réelle : BH séparé sur 12 tests |

### 2.5 Critères de décision — seuils exacts

- **Run 1** : voir §2.3. Rappel : BH q < 0,10 **sur la p Clark-West**, NW p < 0,05, ΔR²_oos > 0, signe constant, R² côté prix < 0,40, non dérivé du prix par construction. Rejet automatique « dérivé du prix » si `byc` (prix par construction) **ou** R² ajusté ≥ 0,40.
- **Run 2** : voir §2.3. Rappel : p_incr < 0,05, q_fam < 0,10, gain OOS > 0, DM p < 0,10, `sign_cos` > 0, `react_ctmp` < 0,40.
- **Doctrine ADOPT/ADAPT/PARK/REJECT** : dans les deux runs, « ADAPT » signifie « mérite une capture forward point-in-time ou une étude externe plus poussée », **pas** « à intégrer ».
- **Définitions PIT** (identiques dans l'esprit) : `PIT_NATIVE` (chaque ligne porte un horodatage d'événement/publication non révisable), `LOOKAHEAD_RISK` (lignes historiques sans horodatage de publication), `PIT_ADAPTABLE` (utilisable en point-in-time si tu captures toi-même les données avec ton horodatage de réception), `SNAPSHOT_ONLY` (run 2 seulement : pas d'historique du tout).

---

## 3. Résultats détaillés

### 3.1 Run 1 — rapport par rapport

#### 3.1.1 Rapport 00 (synthèse) — `R1:reports/016_alternative_data/00_EXECUTIVE_SUMMARY.md`

Affirmations du rapport, avec mon statut de vérification :

| Affirmation | Statut |
|---|---|
| 39 sources cataloguées (2 payantes), 29 exécutées | ✔ (`results/source_records.csv` : 39 lignes, `executed` = 29 vrai/10 faux, `free` = 37/2) |
| 44 séries, 132 tests | ✔ (`incremental.csv` : 132 lignes, 44 identifiants) |
| 0 candidat ; 5 tests nominalement p < 0,05 contre ≈ 7 attendus ; plus petit q BH = 0,66 | ✔ : 5 tests CW p < 0,05 (dont `bc_mempool-size` à 0,0497), attendu 6,6, q min 0,6637 |
| « La plupart des ΔR² OOS sont négatifs » | ✔ : 98 tests sur 132 (74 %) ont ΔR²_oos < 0 |
| 9 séries « dérivées du prix » rejetées | ✔ (`incremental.csv` : 9 identifiants de classe `PRICE_DERIVATIVE_ONLY_REJECT`) |
| 35 séries « distinctes du prix mais non prouvées » | ✔ : 29 « INDEPENDENT_NO_INCREMENTAL_EVIDENCE » + 6 « PRICE_LINKED_PARTIAL » = 35 |
| PIT_NATIVE 9 sur 39 ; le reste LOOKAHEAD_RISK | ✔ (`source_records.csv`) — voir la critique §7 sur la classification |
| Inflation par datation naïve : |t| augmente de plus de 1 pour 9 séries sur 41 ; tests significatifs 4 → 6 | ✔ (recalculé sur `incremental.json`, `naive_lag0`) |
| Adjudication : ADOPT 0 · ADAPT 11 · PARK 24 · REJECT 4 | ✔ |

**Chiffres complémentaires calculés par moi sur `incremental.csv`** :
- Tests significatifs dans l'échantillon (NW p < 0,05) : **16 sur 132** (attendu ≈ 6,6). Les 16 ont un signe cohérent entre moitiés. Cela signale que le test dans l'échantillon **sur-rejette** (2,4 fois plus que prévu), alors que le test Clark-West OOS est bien calibré (5 contre 6,6). C'est précisément pourquoi la règle de candidature exige aussi le test OOS.
- Aucun des 16 ne passe BH (q ≥ 0,66).

#### 3.1.2 Rapport 01 — paysage des sources (`01_SOURCE_LANDSCAPE.md`)

Fiche à 10 attributs par source (accès/coût, historique, latence, sémantique d'horodatage, sémantique de révision, licence, couverture, limites de débit, stabilité opérationnelle). 39 sources en 16 catégories. Chaque sonde = 3 appels espacés d'au moins 2,5 s.

Exemples chiffrés (tous tirés du rapport ; non re-mesurés) :
- Blockchain.com Charts : 6/6 appels HTTP 200, latence médiane 590 ms ; `Last-Modified` = heure de la requête (donc sans information de publication).
- GDELT DOC 2.0 : 1/3 appels 200 (les deux autres 429), latence médiane 24 405 ms ; limite serveur « 1 requête toutes les 5 s ».
- Reddit `.json` : 0/3 (403). Google Trends : 0/3 (404). Farside : 0/3 (403, défi Cloudflare). GitHub REST : 0/3 (403 — bloqué par la politique de périmètre de la session, pas par le fournisseur).
- Open-Meteo : 0/6 (429, quota journalier). **Mais** l'archive Open-Meteo a bien été récupérée (`weather_hdd_cdd_us5`, 1 215 lignes dans `fetch_log.json`), donc « exécuté » est vrai malgré 0/6 dans la sonde.

#### 3.1.3 Rapport 02 — on-chain, mempool, flux d'échange, activité développeurs

- **Mempool** (file d'attente des transactions non confirmées) : mempool.space n'expose l'état du mempool qu'en direct, sans historique ; seule une capture « forward » (à partir de maintenant, avec tes propres horodatages) permettrait un jour de tester des signaux de mempool.
- **Instabilité ClickHouse playground** (le « terrain de jeu » public de ClickHouse qui héberge une copie de GH Archive) : deux requêtes identiques à 14 minutes d'intervalle ont renvoyé des min/max globaux différents (2011-02-12 → 2026-09-29 puis 2023-01-13 → 2026-07-02) ✔ (`results/gh_playground_stability.json`) ; trou 2024-06-06 → 2025-08 ; aucune ligne après 2026-07-02.
- **Résultat le plus « bas » de l'étude** : `gh_merged_pr` (nombre de pull requests fusionnées, 4 dépôts) contre |rendement| : CW p = 0,005, ΔR²_oos = +4,38 %, mais n = 259 jours (≈ 130 jours OOS), BH q = 0,66 ✔ (`incremental.csv`).

Tableau on-chain/mempool/DeFi/GitHub reproduit (extrait, cible « meilleure » = p CW minimale ; à lire comme *optimiste*) :

| Feature | R² côté prix | Cible | n | ΔR²oos | t NW | p CW | q BH | Classe |
|---|---|---|---|---|---|---|---|---|
| `bc_n-transactions` | 0,02 | abs | 1091 | −0,47 % | −1,61 | 0,479 | 0,97 | indépendante, sans preuve |
| `bc_hash-rate` | 0,00 | ret | 1091 | −0,02 % | 1,15 | 0,373 | 0,97 | idem |
| `bc_mempool-size` | 0,01 | abs | 1091 | +0,35 % | 2,07 | 0,050 | 0,93 | idem |
| `bc_mempool-count` | 0,04 | abs | 1091 | +0,51 % | 1,90 | 0,012 | 0,81 | idem |
| `bc_market-cap` | 0,86 | ret | 1091 | −0,08 % | −0,51 | 0,655 | 0,97 | dérivé du prix |
| `stable_mcap` | 0,28 | ret | 1091 | +0,39 % | 1,75 | 0,105 | 0,97 | lié au prix, partiel |
| `defi_tvl_usd` | 0,64 | ret | 1091 | +0,02 % | −0,84 | 0,337 | 0,97 | dérivé du prix |
| `gh_push` | 0,11 | vol (=volume) | 489 | +1,00 % | −2,35 | 0,032 | 0,93 | indépendante |
| `gh_merged_pr` | 0,05 | abs | 259 | +4,38 % | 2,32 | 0,005 | 0,66 | indépendante |
| `gh_btc_stars` | 0,18 | vol (=volume) | 488 | +0,89 % | −2,46 | 0,051 | 0,93 | lié au prix, partiel |

(✔ ces lignes correspondent à `incremental.csv`. Les 14 séries `bc_*` complètes sont dans `07_INCREMENTAL_INFORMATION.md`.)

#### 3.1.4 Rapport 03 — actualités, réseaux sociaux, recherche, marchés de prédiction

| Feature | R² côté prix | Cible | n | ΔR²oos | p CW | q BH | Classe |
|---|---|---|---|---|---|---|---|
| `fear_greed` | 0,49 | vol (volume) | 1091 | +0,12 % | 0,180 | 0,97 | dérivé du prix |
| `hn_btc` | 0,08 | vol (volume) | 996 | +0,27 % | 0,100 | 0,97 | indépendante |
| `wiki_Bitcoin` | 0,34 | vol (volume) | 1091 | +0,62 % | 0,037 | 0,93 | lié au prix, partiel |
| `wiki_Cryptocurrency` | 0,20 | ret | 1091 | +0,05 % | 0,261 | 0,97 | lié au prix, partiel |
| `wiki_gold` | 0,07 | vol (volume) | 777 | +0,55 % | 0,144 | 0,97 | indépendante |

Message du rapport : les flux d'actualités/RSS n'ont **pas d'historique gratuit profond** via leurs points d'accès en direct (RSS ≈ 30 éléments ; GDELT DOC = fenêtre glissante ~3 mois et 429). Les marchés de prédiction (Polymarket, Kalshi) sont la classe la plus propre en horodatage mais **non testée** faute d'historique long. Donc : *non testé = preuve manquante, pas preuve négative*.

#### 3.1.5 Rapport 04 — positionnement et flux (CFTC, ETF, positionnement public d'échange)

- **Observation de publication CFTC** : le dernier enregistrement BTC a la date « as-of » 2026-09-22 (un mardi) ; `Last-Modified` du jeu de données = vendredi 2026-09-25 19:30:07-08 GMT, soit 3 j 19,5 h après la date as-of ✔ (`results/cftc_headers.json`). C'est cohérent avec la règle documentée « publication le vendredi 15h30 ET », mais c'est un horodatage *du jeu de données entier*, écrasé à chaque publication : il ne peut pas dater les lignes historiques. Les tests supposent donc « disponible = as-of + 6 jours ».
- Résultats :

| Feature | R² côté prix | Cible | n | ΔR²oos | p CW | q BH | Classe |
|---|---|---|---|---|---|---|---|
| `cftc_btc_lev_net_pct_oi` | 0,18 | vol | 1091 | +0,06 % | 0,204 | 0,97 | lié au prix, partiel |
| `cftc_btc_am_net_pct_oi` | 0,14 | vol | 1091 | +0,03 % | 0,129 | 0,97 | indépendante |
| `cftc_btc_oi` | 0,24 | ret | 1091 | +0,48 % | 0,054 | 0,93 | lié au prix, partiel |
| `bn_toptrader_ls_pos` | 0,07 | ret | 1055 | +0,24 % | 0,154 | 0,97 | indépendante |
| `bn_ls_ratio` | 0,46 | abs | 1055 | +0,58 % | 0,126 | 0,97 | dérivé du prix (R² ≥ 0,40) |
| `bn_taker_ls_vol` | 0,10 | abs | 1055 | −0,14 % | 0,662 | 0,97 | dérivé du prix (par construction) |
| `cftc_gold_mm` | 0,07 | ret | 768 | −0,19 % | 0,433 | 0,97 | indépendante |
| `cftc_wti_mm` | −0,01 | vol | 763 | −0,61 % | 0,694 | 0,97 | indépendante |

- L'adjudication (09) cite « lev net BTC ret ΔR² −0,74 % » pour le CFTC ✔ (`incremental.csv` : −0,0074 pour `cftc_btc_lev_net_pct_oi`/`ret`) ; c'est la cible rendement, différente de la « meilleure cible » du tableau.

#### 3.1.6 Rapport 05 — économie réelle (transits, stocks EIA, météo, TGA)

| Feature | Actif | Délai | R² côté prix | Cible | n | ΔR²oos | t NW | p CW | q BH |
|---|---|---|---|---|---|---|---|---|---|
| `tga_btc` | BTC | 2 j | 0,05 | abs | 1091 | +0,10 % | −2,33 | 0,106 | 0,97 |
| `tga_gold` | Or | 2 j | 0,03 | abs | 803 | +0,19 % | 1,75 | 0,156 | 0,97 |
| **`eia_crude`** | Pétrole | **7 j** | −0,01 | ret | 769 | +0,49 % | 1,81 | 0,089 | 0,97 |
| `pw_Strait_of` (Ormuz) | Pétrole | 10 j | 0,07 | ret | 778 | +0,16 % | 1,85 | 0,216 | 0,97 |
| `pw_Suez_Canal` | Pétrole | 10 j | 0,06 | ret | 778 | +0,30 % | −1,88 | 0,129 | 0,97 |
| `pw_Bab_el-Mandeb` | Pétrole | 10 j | 0,03 | abs | 778 | −0,03 % | 0,82 | 0,558 | 0,97 |
| `eia_gas` | Gaz | 7 j | 0,03 | vol | 760 | −0,10 % | 0,56 | 0,580 | 0,97 |
| `hdd_us5` | Gaz | 7 j | 0,02 | ret | 549 | −0,72 % | −0,05 | 0,775 | 0,97 |
| `cdd_us5` | Gaz | 7 j | 0,03 | vol | 544 | −0,11 % | −0,79 | 0,463 | 0,97 |

Vérifié ✔ pour `eia_crude` (n = 769, R² ajusté côté prix = −0,0146, ΔR²oos meilleure cible ret = +0,49 %, t NW = +1,81, CW p = 0,089).

À retenir sur `eia_crude` du run 1 : la feature est utilisable **7 jours après** la date de fin de semaine (délai « conservateur »), puis on regarde le rendement du **lendemain**. Le rendement du jour de publication, où l'information arrive vraiment, n'est **jamais regardé**. Le signe du coefficient (t = +1,81) est d'ailleurs l'opposé du run 2 (t = −5,32) : c'est du bruit sur une information périmée. Voir §8.3.

Bug corrigé en cours de route (§6) : la pagination ArcGIS de PortWatch était tronquée silencieusement à 250 lignes ; corrigé, 1 215 lignes ✔ (`data/portwatch_chokepoints_tankers.csv` : 1 216 lignes avec l'en-tête).

#### 3.1.7 Rapport 06 — PIT et fuite

- **Comptes** sur 39 sources : PIT_NATIVE 9 ; LOOKAHEAD_RISK pour l'historique 30, dont 23 « PIT_ADAPTABLE en avant » et 7 « NOT_READY » ✔ (`source_records.csv`).
- **Test de re-fetch (révision)** : même fenêtre récupérée deux fois à ≈ 170 s d'intervalle ; 0 ligne modifiée dans les 6 séries (Blockchain.info 51 lignes, DefiLlama stablecoins 3 225, CFTC BTC 198, Fear & Greed 88, Treasury TGA 118, Hacker News 1) ✔ (`results/revision_test.json`). Le rapport précise honnêtement : une fenêtre de 3 minutes ne peut pas détecter des révisions lentes ; 0 changement **n'est pas** une preuve d'immutabilité.
- **Latence observée** (instantané 2026-09-29 17:57 UTC) : dernière ligne Blockchain.info âgée de 42,0 h ; bloc de tête mempool.space âgé de 6,0 min ; CFTC BTC dernière date 2026-09-22 ; fichiers Binance Vision publiés ≈ 7 h après minuit UTC (`Last-Modified` 07:18 le 29/09 pour la journée du 28/09) ✔ (`latency_snapshot.json`).
- **Démonstration de fuite** (délai conservateur vs délai 0) : sur 41 séries à délai, |t NW| augmente de plus de 1,0 pour 9 séries (max +1,72 pour `ms_avg_fees_sat_per_block`) ✔ ; tests significatifs à la fois en Clark-West et Newey-West (p < 0,05 non corrigé) : **4 avec délai conservateur contre 6 avec délai 0** ✔ ; exemple `gh_btc_stars` contre volume : t = −2,46 → −3,24 ✔ (−2,455 → −3,240).

#### 3.1.8 Rapport 07 — information incrémentale (protocole, puissance, table complète)

- Fenêtre : 2023-10 → 2026-09 ; BTC ≈ 1 090 observations quotidiennes ; futures ≈ 830 jours de bourse ; séries hebdo ≈ 170 obs ; GitHub 260 à 490 jours.
- Résultats : 44 séries testées (0 non testable), 132 tests ; **0 candidat** ; classes : 29 « indépendantes sans preuve », 9 « dérivées du prix », 6 « liées au prix, partielles » ✔.
- **Puissance** (BTC, n = 1 091 ; caractéristique synthétique de R² partiel connu injectée dans la baseline ; 80 répétitions, 3 cibles) — tableau du rapport, vérifié dans `results/power_btc.json` ✔ :

| Cible | n | 0,25 % | 0,5 % | 1 % | 2 % | 4 % |
|---|---|---|---|---|---|---|
| ret | 1091 | 0 % | 0 % | 2,5 % (arrondi à 2 % dans le rapport) | 33,75 % (→ 34 %) | 90 % |
| abs | 1091 | 0 % | 0 % | 5 % | 22,5 % (→ 22 %) | 77,5 % (→ 78 %) |
| vol | 1091 | 0 % | 0 % | 7,5 % (→ 8 %) | 43,75 % (→ 44 %) | 96,25 % (→ 96 %) |

  - Ce que signifie un « R² partiel de 4 % » : la feature, une fois la baseline retirée, expliquerait 4 % de la variance restante du rendement du lendemain. C'est *énorme* pour une donnée quotidienne de crypto.
  - Le rapport conclut : « puissance de 80 % à 3-4 % de R² partiel ». Sur la cible |rendement| (abs), la puissance à 4 % est de 77,5 %, donc l'effet détectable à 80 % est un peu **au-dessus de 4 %** pour cette cible (petite surestimation de puissance dans la formulation « 3-4 % »).
  - **Portillon utilisé pour la puissance** (`s4_power.py`) : CW p < 0,10/120 (≈ 0,00083) **et** NW p < 0,05 **et** ΔR²_oos > 0 — soit un seuil très sévère. Il ne reproduit pas exactement la règle BH (qui dépend de la distribution des autres p), et n'exige pas la cohérence de signe.
- Rejet des dérivés du prix (9) : tableau du rapport, R² côté prix : `bc_market-cap` 0,86 ✔, `defi_tvl_usd` 0,64 ✔ (0,639), `fear_greed` 0,49 ✔ (0,487), `bn_ls_ratio` 0,46 ✔ (0,458). Test de bon sens : le diagnostic classe correctement une série 100 % prix.

#### 3.1.9 Rapports 08, 09, 10

- **08 Licence et coût** : toutes les sources exécutées sont gratuites au point d'usage. Comptage du risque commercial : UNKNOWN 7, low-moderate 15, HIGH 8, low 9 (total 39). Non revu juridiquement.
- **09 Adjudication** : voir §4.
- **10 Limites** : 11 points listés (puissance faible, un seul design linéaire jour-suivant, asymétrie de baseline, délais supposés, sujets non testés, effets du point de sortie réseau, instabilité des données, multiplicité, licences documentaires, échantillon de stabilité minuscule, connecteurs CoinGecko/TipRanks indisponibles).

### 3.2 Run 2 — rapport par rapport

#### 3.2.1 Rapport 00 (synthèse) — `R2:reports/016_alternative_data/00_EXECUTIVE_SUMMARY.md`

Verdict `LIMITED_ALTERNATIVE_DATA_SUPPORTED`, deux candidats :

| Candidat | Ce que c'est | Chiffres du rapport | Statut PIT |
|---|---|---|---|
| Surprise des stocks hebdomadaires de pétrole brut US (EIA) → rendement WTI/Brent le jour de la publication | Donnée de l'économie physique, indépendante du prix (R² passé = 0,028) | t HAC = −5,32, q < 0,001, gain MSE OOS 2,50 % (DM unilatéral p = 0,058) ; Brent réplique (t = −6,03) ; placebos nuls sauf mardi (p = 0,038) ; **effet s'estompe après 2021 (p = 0,27)** | LOOKAHEAD_RISK (fichiers en vrac sans millésimes) ; PIT_ADAPTABLE seulement par capture forward |
| Deribit DVOL (volatilité implicite BTC des options) → log-range du lendemain | Information d'un *second marché* (options) | p HAC < 0,001, gain MSE OOS 2,29 % (DM p = 0,005) | PIT_NATIVE (barres d'indice immuables — affirmation [INF]) ; dérivée du marché, pas « alternative » au sens non-marché |

Quatre constats mis en avant :
1. **Les effets calendaires simulent un alpha « alternatif ».** Sans variables de jour de semaine : 29/90 blocs avec p < 0,05 dans l'échantillon et 8 avec DM OOS p < 0,10 (les téléchargements npm « améliorent » le range du lendemain de 1,9 à 3,6 %, DM p ≤ 0,027). Avec 6 jours de semaine + mémoire de vol 60 j : tout disparaît ✔.
2. **« L'historique gratuit est surtout de l'historique réécrit »** : Coin Metrics 2 067/2 219 lignes recalculées en 2026-04 (2 024 plus de 30 jours après leur horodatage de complétion) ✔ ; Binance Vision `metrics` : 33 fichiers anciens sur 40 échantillonnés ré-uploadés (médiane 371 j après leur jour) ✔ ; CFTC : 231/442 lignes BTC portent un seul horodatage de chargement en masse (2022-09-13) ✔.
3. **Les sources vraiment PIT-natives ne sont pas celles auxquelles on pense** : fichiers GDELT 15 min, fichiers horaires GH Archive, historiques Kalshi/Polymarket, `acceptanceDateTime` SEC EDGAR, fichiers NOAA GFS, barres Deribit. Presque toutes **non testées** pour leur valeur d'information.
4. **Catégories entières impossibles à tester** gratuitement aujourd'hui : flux d'ETF, Google Trends, actualités/RSS/social/mempool (peu de rétention), prévisions météo (quota Open-Meteo épuisé).

**Bloc de comptes** : 69 / 47 / 62 (54 sans clé + 8 avec clé gratuite) ✔ ; PIT_NATIVE 7, PIT_ADAPTABLE 6, LOOKAHEAD_RISK 17, SNAPSHOT_ONLY 17 (sources exécutées) ✔ (recalculé depuis `py/catalog.py`).

#### 3.2.2 Rapport 07 — information incrémentale (crypto)

**Contrôles de calibration** (`07_INCREMENTAL_INFORMATION.md`, vérifié dans `incremental_results.csv`/`candidate_summary.csv` ✔) :

| Bloc | Classe | p_incr min | Gain OOS max | Réactivité max | nb p<0,05 / tests |
|---|---|---|---|---|---|
| deribit_dvol (contrôle positif) | INCREMENTAL_CANDIDATE | 0,000 | +2,292 % | 0,190 | 3/3 |
| CONTROL_noise_A | INDEPENDENT_NO_EVIDENCE | 0,071 | +0,154 % | 0,008 | 0/6 |
| CONTROL_noise_B | INDEPENDENT_NO_EVIDENCE | 0,196 | −0,176 % | −0,000 | 0/6 |
| CONTROL_price_derived_drawdown_mom | PRICE_DERIVATIVE_ONLY | 0,057 | +0,068 % | 0,332 | 0/6 |
| cm_mvrv (contrôle dérivé du prix) | PRICE_DERIVATIVE_ONLY | 0,177 | −0,303 % | 0,875 | 0/3 |

Bruits : 0/12 avec p < 0,05 et 0/12 avec DM p < 0,10 ✔ (calculé sur les résultats bruts).

**Résultats par bloc** (extrait du tableau du rapport, reproduit fidèlement) :

| Bloc | Classe | Tests | nb p<0,05 | p_incr min | q_fam min | Meilleure cible | Gain OOS (%) | DM p |
|---|---|---|---|---|---|---|---|---|
| deribit_dvol | CANDIDAT | 3 | 3 | 0,000 | 0,000 | BTC:lrange | 2,292 | 0,005 |
| treasury_tga_liquidity | indépendant | 6 | 1 | 0,012 | 0,213 | BTC:absret | −0,642 | 0,799 |
| binance_um_positioning_ratios | indépendant | 6 | 1 | 0,019 | 0,213 | BTC:absret | −0,009 | 0,506 |
| nyfed_reverse_repo | indépendant | 6 | 2 | 0,024 | 0,213 | BTC:lrange | 0,060 | 0,451 |
| wikipedia_pageviews_Bitcoin | indépendant | 3 | 1 | 0,031 | 0,213 | BTC:lrange | −0,219 | 0,670 |
| cm_tx_count | indépendant | 6 | 1 | 0,031 | 0,213 | ETH:ret | −0,055 | 0,552 |
| cm_hashrate | indépendant | 3 | 1 | 0,033 | 0,213 | BTC:ret | −0,542 | 0,882 |
| npm_downloads_npm_web3 | indépendant | 3 | 0 | 0,067 | 0,307 | ETH:lrange | −0,218 | 0,749 |
| bc_tx_fees_btc | indépendant | 3 | 0 | 0,098 | 0,381 | BTC:ret | −0,792 | 0,917 |
| bc_mempool_size | indépendant | 3 | 0 | 0,230 | 0,509 | BTC:ret | −0,463 | 0,901 |
| npm_downloads_npm_ethers | dérivé du prix | 3 | 1 | 0,006 | 0,189 | ETH:ret | −0,777 | 0,864 |
| llama_dex_volume | dérivé du prix | 6 | 1 | 0,013 | 0,213 | BTC:lrange | 0,204 | 0,339 |
| cm_exchange_flows | dérivé du prix | 6 | 1 | 0,024 | 0,213 | BTC:lrange | 0,292 | 0,241 |
| alternative_me_fear_greed | dérivé du prix | 6 | 1 | 0,026 | 0,213 | BTC:absret | −0,200 | 0,640 |
| npm_downloads_npm_solana_web3.js | dérivé du prix | 3 | 1 | 0,034 | 0,213 | ETH:ret | −0,479 | 0,771 |
| cm_active_addresses | dérivé du prix | 6 | 0 | 0,051 | 0,298 | ETH:absret | −0,248 | 0,702 |
| llama_stablecoin_supply | dérivé du prix | 6 | 0 | 0,096 | 0,381 | ETH:lrange | 0,200 | 0,078 |
| npm_downloads_npm_bitcoinjs-lib | dérivé du prix | 3 | 0 | 0,124 | 0,428 | BTC:ret | −1,577 | 0,913 |
| bc_unique_addresses | dérivé du prix | 3 | 0 | 0,166 | 0,473 | BTC:lrange | −0,194 | 0,789 |
| bc_tx_count | dérivé du prix | 3 | 0 | 0,175 | 0,473 | BTC:absret | −0,130 | 0,741 |
| cftc_tff_btc_cme | dérivé du prix | 3 | 0 | 0,260 | 0,538 | BTC:lrange | −0,628 | 0,971 |
| wikipedia_pageviews_Ethereum | dérivé du prix | 3 | 0 | 0,551 | 0,751 | ETH:lrange | −0,260 | 0,875 |

(+ les 3 contrôles non DVOL cités plus haut.) ✔ correspond à `candidate_summary.csv`/tableau du rapport.

**Détail du candidat DVOL** (calculé par moi sur `incremental_results.csv`, ✔) :

| Actif | Cible | n | Période | p_incr | Gain OOS % | DM t | DM p | cos signe | R² OOS baseline → complète | n OOS |
|---|---|---|---|---|---|---|---|---|---|---|
| BTC | log-range | 1 896 | 2021-04-23 → 2026-09-01 | 0,0000 | 2,2916 | 2,5458 | 0,0055 | 0,947 | 0,5226 → 0,5336 | 1 496 |
| BTC | \|rendement\| | 1 896 | idem | 0,0001 | 0,4232 | 0,3785 | 0,3525 | 0,669 | 0,1555 → 0,1591 | 1 496 |
| BTC | rendement | 1 896 | idem | 0,0240 | −0,1616 | −0,2932 | 0,6153 | 0,398 | −0,0426 → −0,0443 | 1 496 |

Lecture en langage simple : la baseline explique déjà 52 % de la variance du range du lendemain en OOS ; ajouter DVOL la monte à 53,4 %, soit +1,1 point de R² (« gain de 2,29 % de MSE »). Le gain est réel et statistiquement net **uniquement sur la volatilité** ; il n'existe pas sur le rendement (signe négatif), et pas de manière significative sur |rendement|.

**Statistiques globales** (`summary.json`, ✔) : 93 tests primaires ; 15 avec p < 0,05 (attendu 4,65) ; q min hors DVOL = 0,2572 ; classes : 14 dérivés du prix (dont 2 contrôles), 11 indépendants (dont 2 bruits), 1 candidat. Gain OOS sur les tests primaires : médiane −0,32 %, moyenne −0,49 %, **93,5 % des tests de la famille ont un gain OOS négatif** (calcul mien sur `incremental_results.csv`). Seuls 2 tests sur 93 ont DM p < 0,10 (DVOL/log-range 0,0055 et `llama_stablecoin_supply` ETH/log-range 0,078).

**Artefact calendaire** (✔ `incremental_results_no_calendar.csv`) : baseline sans jour de semaine ni vol 60 j → 90 tests hors contrôles : 29 avec p < 0,05, 11 avec p < 0,001, 8 avec DM p < 0,10. Les six tests forts (p < 0,001 et OOS > 0 et DM p < 0,10) : npm `bitcoinjs-lib` BTC log-range (gain 3,577 %, DM p 0,0001), npm `solana_web3.js` ETH (2,427 %, 0,0075), Coin Metrics exchange flows ETH (1,067 %, 0,0081), Blockchain.com unique addresses BTC (1,355 %, 0,0121), npm `web3` ETH (1,934 %, 0,0238), npm `ethers` ETH (1,911 %, 0,0269). Tous disparaissent avec les contrôles calendaires.

**Sensibilité « disponibilité optimiste »** (un jour de délai en moins pour les délais ≥ 2 j) : 72 tests supplémentaires ; 6 avec p < 0,05 ; 0 passent p < 0,05 + OOS > 0 + DM p < 0,10 (114 lignes « primary » + 72 « optimistic_lag » = 186 lignes dans `incremental_results.csv` ✔).

#### 3.2.3 Rapport 05 — économie réelle (EIA, gaz, météo, PortWatch)

Tableau de résultats principal (`real_economy_results.csv`, ✔ ligne à ligne) :

| Test | Cible | n | Période | coef | t | p_incr | q BH (12 tests) | Gain OOS % | DM p |
|---|---|---|---|---|---|---|---|---|---|
| **Stocks brut vs WTI** | **jour de publication : rendement** | 1 026 | 2007-01-03 → 2026-09-16 | −0,0042 | **−5,320** | 1e-7 | 0,000 | **2,496** | **0,0584** |
| idem | jour de publication : \|rend.\| | 1 026 | idem | −0,0003 | −0,453 | 0,650 | 0,839 | −0,190 | 0,777 |
| idem | lendemain : rendement | 1 026 | 2007-01-04 → 2026-09-17 | −0,0001 | −0,175 | 0,861 | 0,863 | −0,205 | 0,771 |
| idem | lendemain : \|rend.\| | 1 026 | idem | 0,0002 | 0,386 | 0,699 | 0,839 | −0,284 | 0,844 |
| Stockage gaz vs Henry Hub | jour de publ. : rend. | 661 | 2014-01-09 → 2026-09-17 | +0,0060 | 2,234 | 0,0255 | 0,076 | 1,437 | 0,134 |
| idem | jour de publ. : \|rend.\| | 661 | idem | 0,0009 | 0,556 | 0,578 | 0,839 | −0,118 | 0,670 |
| idem | lendemain : rend. | 661 | idem | 0,0018 | 0,612 | 0,540 | 0,839 | −0,394 | 0,999 |
| idem | lendemain : \|rend.\| | 661 | idem | −0,0051 | −2,442 | 0,0146 | 0,076 | 1,305 | 0,173 |
| Anomalie HDD vs Henry Hub | jour de publ. : rend. | 902 | 2007-04-09 → 2026-09-21 | −0,0098 | −2,346 | 0,0190 | 0,076 | 1,680 | 0,0755 |
| idem | jour de publ. : \|rend.\| | 902 | idem | 0,0039 | 1,480 | 0,139 | 0,333 | 0,318 | 0,315 |
| idem | lendemain : rend. | 902 | idem | −0,0034 | −1,346 | 0,178 | 0,357 | 0,047 | 0,446 |
| idem | lendemain : \|rend.\| | 902 | idem | −0,0003 | −0,172 | 0,863 | 0,863 | −0,878 | 0,907 |

Chiffres complémentaires du fichier brut (`crude_robustness.csv`, ✔) :
- OOS pour le test principal : R² OOS baseline = −0,0053, R² OOS complet = +0,0198 (626 observations OOS). Autrement dit, la baseline seule fait *moins bien qu'une simple moyenne* en OOS, et le modèle avec surprise atteint 2 % de R².

**Robustesse du candidat EIA** (`crude_robustness.csv`, ✔) :

| Variante | n | Période | coef | t | p |
|---|---|---|---|---|---|
| placebo lundi (−2 j) | 1 027 | 2007-01-02 → 2026-09-21 | −0,0002 | −0,204 | 0,839 |
| placebo mardi (−1 j) | 1 027 | 2007-01-02 → 2026-09-22 | −0,0016 | −2,071 | **0,038** |
| **vrai mercredi** | 1 026 | 2007-01-03 → 2026-09-16 | −0,0042 | −5,320 | ≈ 1e-7 |
| placebo vendredi (+2 j) | 1 026 | 2007-01-05 → 2026-09-18 | +0,0004 | 0,514 | 0,607 |
| placebo lundi suivant | 1 026 | idem | +0,0009 | 1,056 | 0,291 |
| sous-période 2007-2014 | 417 | → 2014-12-31 | −0,0044 | −4,111 | 3,9e-5 |
| sous-période 2015-2020 | 312 | 2015-01-07 → 2020-12-30 | −0,0072 | −4,454 | 8,4e-6 |
| **sous-période 2021-2026** | 297 | 2021-01-13 → 2026-09-16 | −0,0015 | **−1,114** | **0,265** |
| Brent | 1 026 | 2007-01-03 → 2026-09-16 | −0,0040 | −6,028 | 1,7e-9 (gain OOS 2,609 %, DM p = 0,0465) |

PortWatch (transits vs WTI hebdomadaire, délai 2 semaines) : coefficient 0,189, p = 0,157, n = 381 ✔ (`portwatch_result.csv`). Le rapport écrit « p = 0,16 » ✔.

Variante sans winsorisation (`real_economy_results_raw_returns.csv`, ✔) : t = −4,605, gain OOS 0,888 %, DM p = 0,2206. Le rapport (10) cite « 0,89 %, p = 0,22, t = −4,61 » ✔. **La winsorisation (0,5/99,5 %) a été introduite après avoir vu ce résultat brut** : l'écart de gain OOS 0,89 % → 2,50 % et de DM p 0,22 → 0,058 est donc le fruit d'un choix post hoc, ce que le rapport déclare (10, point 1b).

Informations de fraîcheur EIA (`eia_series_last_updated.json`, ✔) : `PET.WCESTUS1.W_updated` = 2026-09-23T18:02:54-04:00 ; c'est le seul « vintage-like » disponible.

#### 3.2.4 Rapport 06 — PIT

- Comptes des sources exécutées : PIT_NATIVE 7, PIT_ADAPTABLE 6, LOOKAHEAD_RISK 17, SNAPSHOT_ONLY 17 ✔. Pour les 69 : LOOKAHEAD_RISK 21, SNAPSHOT_ONLY 17, PIT_ADAPTABLE 9, UNKNOWN 14, PIT_NATIVE 8 ✔ (`catalog.py`).
- **Coin Metrics** (`pit_probes.json`, ✔) : `AssetCompletionTime` : délai médian par année après la fin du jour = 2020 : 2 807,19 h (rétro-remplissage), 2021 : 4,0 h, 2022 : 5,43 h, 2023 : 5,21 h, 2024 : 3,72 h, 2025 : 3,0 h, 2026 : 3,0 h ; 178/2 219 lignes complétées plus de 72 h en retard ; tous les statuts = `flash` ; `status-time` : 2026-04 pour 2 067 lignes ; 2 024 lignes recalculées plus de 30 jours après complétion.
  - ⚠ Nuance de logique : un `status-time` récent prouve qu'une ligne a été *retraitée*, pas que ses *valeurs* ont changé. Le rapport en déduit « les valeurs servies ≠ valeurs publiées à l'origine » — c'est une INFERENCE, non une observation directe des valeurs (aucune comparaison de valeurs avec un ancien millésime n'a été possible : Wayback bloqué en 429).
- **Binance Vision** (✔ `binance_vision_lastmodified_scan.csv`, `pit_probes.json`) : klines 1 jour spot : 40 fichiers échantillonnés, 4 ré-uploadés (>3 j), délai médian −0,3 j, max 943 j ; `um_metrics` : 40 échantillonnés, **33 ré-uploadés**, délai médian 371,45 j, max 1 897,48 j. Exemple : le fichier du 2021-01-05 porte `Last-Modified` 2026-03-18.
- **CFTC** : 442 lignes TFF BTC CME, 231 avec `:created_at` de chargement en masse (2022-09-13), 211 avec de vrais horodatages (183 un vendredi ; délai médian 3,81 j, p90 6,85 j, max 50,85 j) ✔.
- **GDELT** : `Last-Modified` moins l'horodatage nominal du lot = [−9,4 ; −4,5 ; −5,4 ; −8,2 ; −10,1 ; −10,0 ; −10,0] minutes pour 7 fichiers 2016-2026 ✔ : les fichiers sont écrits juste *avant* leur horodatage nominal.
- **GH Archive** : 122 625 événements dans le fichier du 2026-09-27 12:00 ; `created_at` 12:00:00 → 12:59:57 ; `Last-Modified` 13:05:08, soit +5,1 min après la fin de l'heure ✔. **Un seul fichier échantillonné.**
- **Kalshi** : champs `open_time`, `close_time`, `settlement_ts`, `updated_time` ; 316 bougies pour le contrat `KXFED-26SEP-T5.25` du 2025-08-06 au 2026-09-16 ✔.
- **Wayback** (comparaison de millésimes qui aurait mesuré la réécriture de DefiLlama et Fear & Greed) : **bloquée** (HTTP 429).
- **EIA** : seul un `last_updated` au niveau série ; le `Last-Modified` du CSV WPSR = 13:37 UTC le jour de publication, avant l'heure habituelle de 10h30 ET = 14h30 UTC : « le tampon de fichier n'est pas utilisable comme heure de publication ».
- Tableau des délais de disponibilité utilisés : voir §2.3.

#### 3.2.5 Rapports 01, 02, 03, 04, 08, 09, 10 (run 2)

- **01** : index de 69 sources avec latence et fraîcheur ; blocages observés (géo/WAF : Binance fapi 451, Bybit 403, Bluesky 403, Reddit `.json` 403, IMF DataMapper 403, sec.gov HTML 403, Farside Cloudflare ; quotas : Open-Meteo, GDELT DOC 429 à ≥ 1 appel/20 s, Wikimedia, Wayback, Kalshi 429 une fois, Yahoo 429 ; clés : EIA API v2, Etherscan V2, GIE AGSI, beaconcha.in, Glassnode, LunarCrush, CoinGecko ; FRED/ALFRED et Stooq injoignables).
- **02** : cartes de fiches on-chain/mempool/échanges/développeurs. Constat clé : les flux d'échange de Coin Metrics sont expliqués à 41 % par les mouvements de prix du jour (réactivité 0,41 ✔ : `react_ctmp` 0,397 BTC / 0,414 ETH).
- **03** : actualités/social : rétention des flux (Cointelegraph 30 éléments = 32,2 h ; CoinDesk 25 = 32,9 h ; Decrypt 56 = 6 578 h ≈ 274 j ; BBC 52 = 2 178 h ≈ 91 j ; SEC press 25 = 1 464 h ≈ 61 j ; Reddit RSS 25 = 22,6 h ; StockTwits 30 = 0,5 h ; Mastodon 40 = 14,9 h ; HN 100 = 1 940 h ≈ 81 j) ✔ (`pit_probes.json`). GDELT brut : fichiers de 3,7 à 11,9 Mo, 96 par jour ≈ 0,17 To/an (96 × 5 Mo × 365 = 175 Go ✔ cohérent).
- **04** : CFTC (absorbé par la baseline : p univarié < 0,01 → p_incr = 0,26 ; gain OOS −0,63 % ✔), ratios Binance (meilleur DM p = 0,51 ✔ 0,506), flux d'ETF (aucune source gratuite accessible).
- **08** : 54 sans clé, 8 avec clé gratuite, 2 payantes (Glassnode, LunarCrush), 5 « pratiquement indisponibles » (Google Trends, Bluesky, Farside, iShares, Yahoo) ✔ (54+8+5+2 = 69). Licences : `licenses.py` a récupéré 50 pages de 31 fournisseurs (fichier `license_evidence.json` a 31 entrées ✔ ; le nombre de 50 pages ? non vérifié).
- **09** : tableau d'adjudication **par famille de sources** (pas source par source) ; pas de comptage ADOPT/ADAPT/PARK/REJECT explicite.
- **10** : 11 limites (forking paths déclarés, résolution journalière, échantillon d'un seul cycle, portée de la baseline, non testé ≠ rejeté, environnement, licences par mots-clés, restatement mesuré seulement là où les horodatages le permettaient, horloge du bac à sable, aucun code AurumShift).

### 3.3 Fichiers de résultats agrégés fournis

- Run 1 : `results/incremental.csv` (132 lignes) et `incremental.json` (avec les variantes « naive lag 0 »), `power_btc.json`, `revision_test.json`, `latency_snapshot.json`, `source_records.csv/json` (39 lignes), `probe_results.json` (39 sources), `fetch_log.json`, `gh_playground_stability.json`, `cftc_headers.json`, `final_block.txt`.
- Run 2 : `results/incremental_results.csv` (186 lignes), `incremental_results_no_calendar.csv`, `candidate_summary.csv`, `summary.json`, `real_economy_results.csv`, `real_economy_results_raw_returns.csv`, `crude_robustness.csv`, `portwatch_result.csv`, `pit_probes.json`, `binance_vision_lastmodified_scan.csv`, `license_evidence.json`, `probe_results.json`, `eia_series_last_updated.json`, `collect_log.json`, plusieurs `.log`.

---

## 4. Candidats / méthodes évalués un par un

### 4.1 Run 1 — les 39 sources

Verdict par source (`R1:reports/.../09_ADJUDICATION.md` ; comptes vérifiés ✔ : ADOPT 0, ADAPT 11, PARK 24, REJECT 4). « ADAPT » = capture forward / étude externe complémentaire, pas intégration.

**ADAPT (11)** — condition de changement de verdict : *dépend de captures futures*.
- `mempool_space` : seul accès à l'état LIVE du mempool (aucun historique n'existe). Les agrégats de minage sont nuls dans les tests.
- `blockstream` : données de registre PIT-natives ; agrégation propre pour éviter les millésimes des API de graphiques. Valeur non prouvée.
- `defillama_stable` : capitalisation stablecoins, R² côté prix 0,28 ; ΔR²oos +0,39 %, q 0,97. Historique recalculé quand les adaptateurs changent (DOC/INFERENCE).
- `hn_algolia` : horodatages d'items PIT-natifs, indépendante du prix (R² 0,08), testée nulle.
- `polymarket` et `kalshi` : PIT-natifs, indépendants par construction ; contrats de courte durée, non testés ; panier fixe à capturer.
- `cftc_cot` : positionnement institutionnel indépendant du prix (R² 0,14-0,24), nul au test. Une datation naïve « mardi » fuirait de 3-4 jours.
- `fiscal_dts` (TGA) : R² 0,05, nul pour BTC/or.
- `gharchive` : fichiers horaires immuables (≈ 100 Mo/heure).
- `eia_files` : R² ≈ 0, nul pour le WTI **dans ce design** (173 semaines seulement).
- `binance_vision` : fichiers immuables (affirmation contredite par le run 2, voir §8).

**PARK (24)** : `bc_charts` (agrégats sans millésimes, 14 séries testées, aucune significative), `blockchair`, `gdelt_doc` (limite 1 req/5 s, fenêtre de 3 mois), `rss_crypto`, `rss_fed`, `stocktwits`, `bluesky`, `wikipedia_pv`, `etf_farside`, `etf_ssga_gld`, `sec_edgar` (« source la plus PIT mais basse fréquence, non testée »), `nyfed`, `github_rest`, `npm_pypi`, `portwatch`, `eia_api`, `gie_agsi`, `openmeteo`, `nws`, `noaa_ndbc`, **`deribit_dvol`** (« la volatilité implicite est dérivée du prix par construction »), `exchange_reserves`, `baltic_shipping`, `ais_open`.

**REJECT (4)** : `reddit_json` (403 + conditions restrictives), `gtrends` (pas d'API officielle, rééchantillonnage à chaque requête), `fear_greed` (49 % expliqué par le prix), `gh_playground` (contenu instable, trous, arrêt au 2026-07-02).

**Rejets au niveau des séries** (« dérivées du prix ») : `bc_transaction-fees-usd`, `bc_estimated-transaction-volume-usd`, `bc_cost-per-transaction`, `bc_market-cap`, `bc_miners-revenue`, `defi_tvl_usd`, `fear_greed`, `bn_ls_ratio`, `bn_taker_ls_vol` (9).

**Conditions de changement de verdict** (du rapport 09) : constituer 6-12 mois de millésimes propres (mempool, CFTC/EIA/TGA/PortWatch, DefiLlama, Polymarket/Kalshi, GDELT en vrac, RSS) ; re-tester à horizon multi-jours/hebdomadaire et avec des modèles non linéaires/de régimes ; ajouter des actifs transversaux (plus de coins, actions/ETF) pour augmenter la puissance.

### 4.2 Run 2 — familles de sources

Verdicts (`R2:reports/.../09_ADJUDICATION.md`) :

| Source / famille | Décision | Justification chiffrée / conditions |
|---|---|---|
| EIA stocks brut/gaz (fichiers en vrac + fichiers de publication) | **ADAPT** | Seul candidat hors marché (t ≈ −5, OOS +2,5 %, Brent réplique, indépendant du prix). Ingestion sur l'horloge de publication avec horodatages de réception propres ; test intraday ; attendre des limites d'exécutabilité (fade post-2021). Domaine public |
| Deribit DVOL / carnet d'options | **ADAPT** | Passe l'OOS sur le range (+2,3 %). Dérivé du marché des options : chevauche les entrées de volatilité qu'un système possède déjà — le recouvrement ne peut se juger que contre le vrai dépôt |
| Coin Metrics community | PARK | Aucun gain ; flux d'échange réactifs au prix (0,41). Candidat à la capture forward (champs de complétion/statut) ; historique recalculé (2 067/2 219). Variante de licence CC à confirmer |
| mempool.space / Blockstream / RPC ETH | PARK | Seule source d'état mempool/frais, mais snapshot only ; valeur inconnue avant 6-12 mois de capture propre |
| GDELT 2.0 fichiers bruts | PARK | PIT-natif, gratuit y compris commercial ; ≈ 0,17 To/an ; ingestion filtrée par thèmes nécessaire |
| Kalshi / Polymarket | PARK | PIT-natifs ; besoin d'une étude par événements (FOMC…) ; les contrats de seuil BTC sont dérivés du prix (REJECT pour ceux-là) |
| GH Archive | PARK | PIT-natif ; aucune série de dépôts crypto construite ; proxys npm/PyPI sans gain |
| CFTC COT | PARK | PIT à règle (horodatages natifs seulement après 2022-09) ; positionnement absorbé par la baseline pour BTC ; peut valoir pour matières premières/FX (non testé) |
| Treasury TGA, NY Fed RRP | PARK | Indépendants du prix mais sans gain pour BTC/ETH ; non testés sur taux/or/FX |
| Fear & Greed | **REJECT** | Composite ; réactivité 0,43 ; aucun gain ; pas de millésimes |
| DefiLlama stablecoins / volume DEX | **REJECT** | Libellés en USD, historique réécrit, subsumés par la baseline |
| Blockchain.com, npm/PyPI/crates, Wikipedia | **REJECT** | Aucun gain après contrôles calendaires ; LOOKAHEAD_RISK ; conditions restrictives ou floues (Blockchain.com) |
| Ratios long/short et taker Binance, stats OKX/Bitfinex | PARK | Même place de marché ; pas de gain OOS ; OKX/Bitfinex ne gardent que semaines-mois |
| Flux RSS | PARK | Zéro historique ; capture forward triviale |
| Réseaux sociaux publics (Reddit RSS, StockTwits, Mastodon, HN, 4chan) | **REJECT** | Restrictions ToS ou minuscule/bruité ; rétention de quelques heures |
| Flux d'ETF | PARK | Aucune source gratuite accessible |
| Météo (CPC, NWS, NCEI, NASA POWER) | REJECT (réalisé) / PARK (prévision) | Les anomalies réalisées sont déjà dans les prix ; Open-Meteo historical-forecast et NOAA GFS = voie PIT mais bloqués/non testés |
| PortWatch | PARK | Données physiques, mais AIS révisé ; pas d'effet sur WTI hebdomadaire (p = 0,16, n = 381) |
| Google Trends, Bluesky, Reddit JSON, Glassnode, LunarCrush, FRED/ALFRED | PARK | Bloqués/à clé : preuve manquante |

**Conditions de changement de verdict** (rapport 00) : passage à un verdict de type `MULTIPLE_…` demanderait au moins une autre source PIT-propre, indépendante du prix, avec gain OOS confirmé (pistes : thèmes GDELT GKG, probabilités macro Kalshi/Polymarket, mempool capturé ≥ 12 mois, Open-Meteo historical-forecast vs Henry Hub). Rétrogradation si l'effet EIA est entièrement absorbé intraday avant tout horodatage exécutable.

**Pourquoi `STUDY_INCONCLUSIVE` n'est pas retenu par le run 2** (rapport 09) : « les familles testées ont donné des réponses calibrées et tranchées (contrôles bruit 0/12 ; contrôles dérivés du prix bien classés ; contrôle positif réussi) ». Voir la critique §7 sur la solidité de cet argument.

---

## 5. Blocs finaux (reproduits tels quels) et explication ligne par ligne

### 5.1 Bloc final du run 1 (`R1:bench/alternative_data_v1/results/final_block.txt`, identique à la fin de `00_EXECUTIVE_SUMMARY.md`)

```
SOURCES_DISCOVERED=39
SOURCES_EXECUTED=29
FREE_SOURCES=37 (free at point of use incl. 3 needing a free key/account and non-commercial-only terms; 29 executed, none with a key)

PIT_NATIVE=9
PIT_ADAPTABLE=23   # LOOKAHEAD_RISK for historical rows, PIT-usable via forward capture / release rule

INCREMENTAL_INFORMATION_CANDIDATES=0
PRICE_DERIVATIVE_ONLY_REJECTS=9

FINAL_VERDICT=STUDY_INCONCLUSIVE
```

| Clé | Signification | Vérification |
|---|---|---|
| `SOURCES_DISCOVERED=39` | Nombre de sources cataloguées | ✔ 39 lignes dans `source_records.csv` |
| `SOURCES_EXECUTED=29` | Sources dont au moins une sonde a renvoyé HTTP 200 ou dont des données ont été tirées | ✔ 29 vrai/10 faux |
| `FREE_SOURCES=37 (…)` | Gratuites au point d'usage ; la parenthèse dit que 3 exigent une clé/compte gratuit et des conditions non commerciales, que 29 ont été exécutées, sans clé | ✔ pour 37/39 ; ? pour « 3 nécessitant une clé » (non recompté ; le rapport 08 cite EIA API v2, GIE AGSI comme à clé) |
| `PIT_NATIVE=9` | Sources dont chaque ligne historique porte un horodatage d'événement/publication non révisable | ✔ 9 (mais voir critique : la liste contient Hacker News et le ClickHouse playground jugé instable) |
| `PIT_ADAPTABLE=23` | Historique en LOOKAHEAD_RISK mais utilisable en PIT par capture propre en avant ou règle de publication | ✔ 23 (colonne `pit_forward`) |
| `INCREMENTAL_INFORMATION_CANDIDATES=0` | Séries passant la règle complète | ✔ 0 |
| `PRICE_DERIVATIVE_ONLY_REJECTS=9` | Séries rejetées car dérivées du prix | ✔ 9 |
| `FINAL_VERDICT=STUDY_INCONCLUSIVE` | Ni « aucune donnée utile », ni « soutenue » : le rapport dit que la puissance est trop faible et que de nombreuses catégories ne sont pas testables | Verdict du rapport |

Remarque : le bloc final ne contient **pas** `LOOKAHEAD_RISK`, `SNAPSHOT_ONLY` comme comptes ; les 7 sources `NOT_READY` (non prêtes) n'y figurent pas non plus (23 + 9 + 7 = 39).

### 5.2 Bloc final du run 2 (`R2:reports/.../00_EXECUTIVE_SUMMARY.md`)

```
SOURCES_DISCOVERED=69
SOURCES_EXECUTED=47
FREE_SOURCES=62   # zero-cost route (no key: 54; free key required: 8); executed & free: 47

PIT_NATIVE=7   # executed sources; +1 documented but unreachable (FRED/ALFRED)
PIT_ADAPTABLE=6   # executed sources
LOOKAHEAD_RISK=17   # executed sources (historical rows without publication timestamps)
SNAPSHOT_ONLY=17   # executed sources with no history to replay (forward capture only)

INCREMENTAL_INFORMATION_CANDIDATES=2   # EIA weekly crude-inventory surprise (real economy); Deribit DVOL (options-implied vol, market-derived)
PRICE_DERIVATIVE_ONLY_REJECTS=12   # feature blocks (excludes 2 built-in controls); across 7 sources — see 07

FINAL_VERDICT=LIMITED_ALTERNATIVE_DATA_SUPPORTED
```

| Clé | Signification | Vérification |
|---|---|---|
| `SOURCES_DISCOVERED=69` | Sources cataloguées | ✔ `catalog.py` : 69 |
| `SOURCES_EXECUTED=47` | Sources avec au moins un tirage réel de données parsé et journalisé (les points d'accès injoignables ou répondant par une erreur d'authentification ne comptent pas) | ✔ 47 |
| `FREE_SOURCES=62` | Voie à coût nul : 54 sans clé + 8 avec clé gratuite ; toutes les 47 exécutées sont gratuites | ✔ 62 / 54 / 8 / 47 |
| `PIT_NATIVE=7` | Sources *exécutées* PIT-natives (+ FRED/ALFRED documenté mais injoignable) | ✔ 7 exécutées ; 8 sur les 69 |
| `PIT_ADAPTABLE=6` | Sources exécutées adaptables | ✔ 6 |
| `LOOKAHEAD_RISK=17` | Sources exécutées à historique sans horodatage de publication | ✔ 17 |
| `SNAPSHOT_ONLY=17` | Sources exécutées sans historique rejouable | ✔ 17 |
| `INCREMENTAL_INFORMATION_CANDIDATES=2` | EIA et DVOL | ✔ EIA (calcul manuel/robustesse) ; DVOL (`candidate_summary.csv` classe `INCREMENTAL_CANDIDATE`) |
| `PRICE_DERIVATIVE_ONLY_REJECTS=12` | Blocs « dérivés du prix », hors 2 contrôles intégrés, répartis sur 7 sources | ✔ 12 blocs (14 − 2 contrôles) |
| `FINAL_VERDICT=LIMITED_ALTERNATIVE_DATA_SUPPORTED` | Deux candidats, mais l'un est marché-dérivé et l'autre borderline/faisant l'objet d'un fade | Verdict du rapport |

Différence de définition : **le PIT_NATIVE du run 1 (9) est compté sur les 39 sources, celui du run 2 (7) sur les seules sources exécutées**. Les chiffres ne sont donc pas directement comparables (voir §8).

---

## 6. Contrôles de validité

### 6.1 Tests de fuite / lookahead

**Run 1**
- Délais de publication *conservateurs* posés a priori pour chaque série (§2.3).
- Test de fuite explicite « naive lag 0 » sur 41 séries à délai : inflation modeste et de signe mixte (|t| augmente de plus de 1 pour 9 séries ; tests significatifs 4 → 6) ✔. Le rapport le formule bien : « un délai trop court ne peut pas créer de signal à partir de rien, il ajoute seulement du bruit contemporain ».
- Test de re-fetch de révision : 0 changement sur 6 séries, fenêtre de 3 minutes, donc peu concluant ✔.
- Diagnostic d'indépendance vis-à-vis du prix (§2.3).
- Cas connus : ERA5 (météo) = réanalyse, pas PIT → test signalé comme « borne supérieure » (`hdd_us5`, `cdd_us5`).

**Run 2**
- Délais de disponibilité explicités (tableau §3.2.4) et sensibilité « optimiste » (−1 jour) : 0 test passe.
- **Mesures directes de réécriture** : Coin Metrics (2 024/2 219), Binance Vision (33/40), CFTC (231/442). C'est un apport net par rapport au run 1.
- Contrôles négatifs : 2 blocs de bruit gaussien (0/12 p < 0,05), 1 bloc dérivé du prix, MVRV. Contrôle positif : DVOL.
- Diagnostic de « réactivité au prix » mesuré aux dates d'observation.
- Placebos de date de publication pour l'EIA (lundi, mardi, vendredi, lundi suivant) + sous-périodes + Brent.

### 6.2 Déterminisme

- Run 1 : un script dédié à chaque étape, graine fixée pour la simulation de puissance (`20260929`) ; tout le reste est déterministe. Les données sont « à un instant donné » : une relance peut donner d'autres chiffres (historiques recalculés) — le rapport le dit (10, point 7).
- Run 2 : graine `7` pour les bruits ; le reste déterministe, sensible à l'IP de sortie et à la date. Les fichiers de 5 minutes `um_metrics_5m_*.csv.gz` (40 Mo) et `data/raw/` (≈ 60 Mo) sont **exclus du dépôt** (gitignorés) : seules les agrégations quotidiennes sont fournies (README).

### 6.3 Erreurs corrigées en cours de route

- Run 1 : pagination PortWatch tronquée à 250 lignes → corrigée (1 215) ✔ ; import `xlrd` manquant lors de la première récupération EIA (`fetch_log.json`, clé `eia` : `ImportError`) puis données EIA présentes (173 semaines) ✔ ; ClickHouse playground jugé instable et rejeté comme flux.
- Run 2 : **baseline révisée** après avoir vu 29/90 tests à p < 0,05 (ajout des jours de semaine et de la vol 60 j) ; **winsorisation des rendements** introduite après le résultat brut (gain OOS 0,89 %, DM p 0,22) ; **filtre de signe économique** appliqué après coup pour écarter gaz/météo (« classé INCONCLUSIVE, pas retenu ») ; `parsed_ok=True` non fiable pour 3 extracteurs factices (AISHub, GIE AGSI, Etherscan V1, qui renvoient des erreurs d'authentification), corrigé par le catalogue ; DVOL prévu comme contrôle positif puis compté comme candidat (« relabel post hoc, déclaré »).

### 6.4 Écarts au protocole déclarés

- Run 2 : liste complète en `10_LIMITATIONS.md` point 1 (a à d). Le run 2 est plus transparent que le run 1 sur ses « forking paths » (choix faits après avoir vu les données).
- Run 1 : aucun écart déclaré (protocole unique, pas d'ajustement) ; en revanche le protocole n'a pas été horodaté indépendamment (un seul commit).

---

## 7. Critique indépendante

### 7.1 Points faibles communs

1. **Le « pré-enregistrement » n'est pas vérifiable.** Dans les deux runs, il s'agit d'un docstring dans un script commité *avec* les résultats. Rien ne prouve que la règle a été écrite avant le premier résultat. Le run 2 admet lui-même avoir changé la baseline après coup.
2. **Aucun jeu de test « gelé » (held-out).** Les deux runs utilisent des fenêtres extensibles dans le même échantillon. Aucun ne réserve une période jamais regardée.
3. **Le test dans l'échantillon (Newey-West / HAC à 5 retards) sur-rejette.** Run 1 : 16 tests à p < 0,05 sur 132 (attendu 6,6). Run 2 : 15 sur 93 (attendu 4,65). Des ordres de grandeur similaires : environ 2,4 à 3,2 fois trop de « succès » dans l'échantillon. Le run 2 le reconnaît (« sur-rejet léger ») ; le run 1 ne le commente pas. Les deux s'en protègent par l'exigence OOS, mais cela affaiblit toute lecture de « p < 0,001 dans l'échantillon » (DVOL, EIA) comme preuve à elle seule.
4. **Un seul cycle de marché**, une seule horloge (2026-09-29), instantané des fournisseurs. Les sources réécrivent leurs historiques ; les résultats ne sont pas rejouables à l'identique.
5. **Information, pas tradabilité.** Aucun des deux ne teste les coûts, l'exécution ou la capacité. Un gain de R² de 1 point n'est pas un gain de PnL.
6. **Les heures de publication sont supposées, non observées**, pour presque toutes les séries historiques (lags fixés a priori).

### 7.2 Points faibles spécifiques au run 1

- **Cible « vol » = volume, pas volatilité.** Le rapport écrit « vol » et parle de « volatilité » dans le résumé (« price/volume/volatility ») ; en réalité l'une des trois cibles est le ratio de volume. La **volatilité du lendemain n'est jamais une cible** (seule |rendement| s'en approche, mesure bruitée). Or c'est *précisément* la cible sur laquelle le run 2 trouve DVOL.
- **Baseline sans effets de jour de semaine.** Le run 2 montre que ces effets suffisent à créer des faux positifs sur les cibles de volume/volatilité. Les résultats « nuls » du run 1 ne sont pas biaisés vers le haut par cet effet, mais la baseline est plus faible qu'elle n'aurait dû l'être — les nombres d'OOS positifs (25 % des tests) sont peut-être en partie des effets de calendrier, non des effets réels.
- **Transformation unique** : variation sur 1 semaine, puis z-score 90 jours (26 semaines pour l'hebdo). Elle détruit l'information de *niveau* — or la volatilité implicite est un prédicteur de niveau. INFERENCE (mienne) : cette transformation aurait très probablement empêché de détecter un effet type DVOL, même si la série avait été testée.
- **DVOL rejeté sans test.** L'adjudication de `deribit_dvol` dit : « la volatilité implicite est dérivée du prix par construction ». C'est une hypothèse énoncée, pas mesurée, et le run 2 montre qu'elle ne tient pas (réactivité mesurée de DVOL : 0,19, sous le seuil de 0,40).
- **Contradiction interne** : l'adjudication `deribit_dvol` mentionne « une sonde a rencontré un 502 gateway CONNECT rejection » alors que le rapport 01 indique 6/6 appels HTTP 200, et `probe_results.json` ne montre que des 200 pour Deribit ✘ (peut provenir du rapport 005 d'une autre lane ; non retrouvé dans les résultats de cette lane).
- **Classification PIT_NATIVE discutable** : la liste des 9 inclut `hn_algolia` (dont les décomptes changent rétroactivement par suppression/flag, comme le rapport lui-même le note), le `gh_playground` (rejeté ensuite pour instabilité et trous), `binance_vision` (dont le run 2 montre la ré-écriture de 33 fichiers sur 40) et `deribit_dvol` (sur la seule base de l'existence d'horodatages de trades). Le libellé « PIT_NATIVE » y est donc plus généreux que la définition stricte du rapport.
- **Puissance annoncée un peu optimiste.** La phrase « 80 % de puissance à 3-4 % de R² partiel » ne tient pas pour la cible |rendement| (77,5 % à 4 %). Et le seuil de la simulation (CW p < 0,10/120) est plus sévère que la règle réelle, donc la puissance réelle pourrait différer dans les deux sens (le test réel exige aussi la cohérence de signe, ce que la simulation n'exige pas).
- **Séries courtes.** GitHub : 259 à 489 jours ; hebdomadaire : ~173 semaines (mais `n` = 769 lignes quotidiennes après propagation de la valeur hebdomadaire : ce `n` gonfle l'apparente taille d'échantillon, les vraies observations indépendantes étant ≈ 173).
- **Baseline asymétrique** (funding/OI pour BTC seulement), **futures Yahoo non ajustés**.
- **Couvre tout mais teste peu** : 29 sources exécutées, mais seulement une douzaine de sources ont fourni des séries quotidiennes utilisables sur 3 ans.

### 7.3 Points faibles spécifiques au run 2

- **DVOL n'est pas une donnée alternative au sens de la mission.** C'est un indice de volatilité implicite issu du marché des options. Le rapport le dit, mais le compte des « candidats » l'inclut. Il a d'abord été défini comme **contrôle positif** (« le test doit trouver ça »), puis relabellisé candidat après qu'il ait passé la règle : c'est une décision post hoc. Sans ce relabel, il resterait **1** candidat (EIA), et le rationnel du verdict (« exactement deux ») changerait.
- **DVOL est en partie redondant avec la baseline (`red_base` = 0,42)** et ne peut pas être « jugé » sans savoir quelles entrées de volatilité AurumShift possède déjà. Le rapport le reconnaît (09).
- **La règle de passage OOS est peu exigeante en multiplicité.** La p-value in-sample est corrigée par BH, mais le critère OOS est « DM p < 0,10 », **non corrigé** pour les 93 tests. Si l'on appliquait un BH sur les p DM de la famille, DVOL aurait un q ≈ 0,507 (calcul mien) : il **ne passerait pas** une règle du type de celle du run 1. Pour l'EIA, avec 12 tests dans la famille, un BH sur DM p = 0,058 donnerait q ≈ 0,70 (calcul mien, INFERENCE). Autrement dit, la différence de verdict entre les deux runs tient en partie à la **sévérité de la règle**, pas seulement aux données.
- **DM sur modèles emboîtés** : test conservateur (voir §2.3). Le résultat est favorable au run 2 (moins de faux positifs), mais il sous-estime la puissance : 2 tests sur 93 seulement ont DM p < 0,10, ce qui est inférieur à la fréquence attendue sous H0 (≈ 9) — signe d'un test lui-même conservateur.
- **EIA — l'essentiel de la « preuve » est dans l'échantillon, et elle est contemporaine.**
  - La cible est le rendement du **jour de publication** (fermeture à fermeture), donc c'est une étude d'événement (« l'information est-elle intégrée au prix ce jour-là ? »), pas une prévision. Elle ne dit rien sur un gain exploitable *avant* la publication ; à la publication (mercredi 10h30 ET) le marché réagit en minutes — le rapport le dit lui-même (« event-clock »).
  - Le rendement du lendemain, seule cible sans ambiguïté PIT, est nul (p = 0,861).
  - Le OOS n'est que borderline : DM p = 0,058 (winsorisé) ; 0,22 sans winsorisation ✘ (ce que le résumé exécutif présente comme « OOS MSE gain 2,50 % (one-sided DM p = 0,058) » sans mentionner en 00 la version brute, qui n'apparaît qu'en 10). Le rapport 10 corrige : « à traiter comme borderline ».
  - La winsorisation est un choix post hoc, fait après avoir vu le résultat brut.
  - Le « surprise » est calculé contre une **norme saisonnière sur 5 ans**, pas contre le consensus des analystes (que le marché regarde vraiment). C'est un proxy ; le t = −5,3 dit que ce proxy est corrélé au rendement, non que l'on aurait pu le prévoir.
  - Les valeurs EIA utilisées sont celles du fichier **en vrac courant** (aucun millésime) : LOOKAHEAD_RISK par la définition même du rapport.
  - **Fade** : sous-période 2021-2026 : t = −1,11, p = 0,265 (n = 297). Sur la période la plus récente et la plus proche de l'usage réel, l'effet n'est pas détecté.
  - Le résultat de sous-période OOS n'est pas exploitable : `oos_n` = 17 pour 2007-2014 (gain 14,2 % sur 17 observations !), 0 pour 2015-2020, absent pour 2021-2026 (`crude_robustness.csv`) : l'entraînement minimal de 400 observations dépasse la taille de chaque sous-période. Ces chiffres ne sont pas cités dans les rapports, c'est bien, mais le fichier brut ne doit pas être mal lu.
  - Le placebo « mardi » est significatif (p = 0,038), lu comme une fuite du rapport API de la veille au soir [INF] — hypothèse plausible, non testée.
  - Brent « réplique » : Brent et WTI bougent ensemble ; c'est une confirmation faible (même variable de surprise, quasi même événement), pas une réplique indépendante.
  - Le BH pour l'EIA porte sur une **famille de 12 tests** distincte de la famille des 93. Choisir la famille est une liberté du chercheur.
- **Gaz et météo écartés sur un critère post hoc (signe économique).** L'argument est raisonnable, mais un critère appliqué après avoir vu les résultats reste un choix ouvert (le rapport le déclare).
- **Pas d'analyse de puissance.** Le run 2 s'appuie sur un contrôle positif très fort (DVOL) et des contrôles bruit. Cela prouve que la machinerie détecte un effet *énorme* (p ≈ 0) et ne fabrique pas de faux positifs sur 12 tests de bruit, pas qu'elle détecterait un effet de 0,5 %. Avec 12 tests de bruit, 0 rejet à 5 % n'a rien d'improbable (0,95^12 ≈ 54 %). En extrapolant la puissance du run 1 (INFERENCE mienne, non simulée) : avec n ≈ 2 000 au lieu de 1 091 l'effet minimal détectable serait grossièrement réduit de moitié, soit de l'ordre de 1,5 à 2 % de R² partiel — toujours élevé.
- **`STUDY_INCONCLUSIVE` écarté avec des arguments fragiles.** « Les familles testées ont donné des réponses calibrées et tranchées » repose surtout sur des tests **nuls sans puissance connue**. Un verdict plus prudent aurait pu être retenu.
- **Écarts rapport vs résultats bruts** :
  - ✘ « 16 catégories » : le catalogue du run 2 contient **15** catégories distinctes (calcul sur `catalog.py`).
  - ✘ Période d'analyse « → 2026-09-28 » vs résultats qui s'arrêtent le 2026-09-01.
  - ✘ Le tableau des blocs donne un « gain OOS max » de −0,281 % pour `cm_hashrate` en 02 et une « meilleure cible » à −0,542 % en 07 : ce sont deux colonnes différentes (maximum vs meilleure cible par p), pas une contradiction, mais la présentation prête à confusion.
  - La classification PIT_NATIVE de DVOL, GH Archive, GDELT repose sur des **étiquettes [INF]** (« barres d'indice immuables », « fichiers statiques par lot »), pas sur une observation de non-réécriture ; les fichiers GDELT et GH Archive n'ont été échantillonnés qu'en 7 et **1** exemplaires.
  - Binance Vision est classé LOOKAHEAD_RISK (réécriture de 33/40 fichiers) **alors que le funding et l'OI de la baseline en proviennent** et sont utilisés avec 1 jour de délai comme si les valeurs étaient celles vues en temps réel. La baseline des deux runs partage donc ce risque : ses variables « OI/funding » sont issues de fichiers dont l'historique a pu être réécrit. Aucun des deux runs ne quantifie l'effet sur ses résultats.
  - ✘ Le run 2 attribue 12 blocs « PRICE_DERIVATIVE_ONLY » dont des blocs sur les npm ayant p_incr < 0,05 : la logique « absorbé par la baseline » est un choix de classification, non un test.
- **Ce que les chiffres du run 2 ne prouvent pas** : que l'EIA soit exploitable ; que DVOL apporte quoi que ce soit *par rapport à un système qui a déjà une mesure de volatilité implicite* ; que les 21 autres blocs soient inutiles (ils sont « sans preuve » avec puissance inconnue) ; que les sources non testées (GDELT, Kalshi, GH Archive, mempool) soient sans valeur.

### 7.4 Ce que les chiffres du run 1 ne prouvent pas

- Ils **ne prouvent pas** que les sources sont inutiles : puissance faible, un seul design, cible volume et pas volatilité, feature sans niveau, fenêtre de 3 ans, données souvent fragmentaires.
- Ils **ne prouvent pas** l'absence d'effet EIA : le design testé n'observe pas le jour de publication (§8.3).
- Ils **ne prouvent pas** que Deribit/DVOL soit « dérivé du prix » : jamais testé.

### 7.5 Choix en bord de grille et hypothèses fragiles

- Run 1 : seuil de R² côté prix à 0,40 (les classes changent selon ce seuil : `bn_ls_ratio` à 0,458, `fear_greed` à 0,487 sont juste au-dessus, `wiki_Bitcoin` à 0,336 est juste en dessous) ; un R² de 0,15 sépare « indépendante » et « liée, partielle ». Le seuil 0,40 est identique dans le run 2, ce qui suggère qu'il vient de la consigne de mission.
- `bc_mempool-size` : CW p = 0,0497 est compté « significatif » de justesse.
- Run 2 : seuil DM p < 0,10 (très permissif pour un test unilatéral) ; `sign_cos > 0` (tout signe cohérent, sans seuil de magnitude) ; réactivité < 0,40.
- Les deux : délais de publication supposés ; z-scores et fenêtres (90 j, 30 j, 26 semaines, 104 semaines) choisis a priori sans sensibilité.

### 7.6 Contradictions internes détectées

- Run 1 : Deribit 502 vs 6/6 HTTP 200 (✘ ci-dessus) ; PIT_NATIVE attribué à `gh_playground` et rejeté ensuite ; « executed » Open-Meteo avec 0/6 en sonde.
- Run 2 : DVOL « contrôle » et « candidat » à la fois ; « 16 catégories » vs 15 ; rapport 09 sans comptes ADOPT/ADAPT/PARK/REJECT alors que la doctrine les demande.

---

## 8. Comparaison point par point des deux runs (section obligatoire)

### 8.1 Catalogue de sources côte à côte : 39 contre 69

#### 8.1.1 Comptes globaux

| Indicateur | Run 1 | Run 2 | Commentaire |
|---|---|---|---|
| Sources cataloguées | 39 ✔ | 69 ✔ | Le run 2 catalogue presque 1,8 fois plus de sources |
| Sources exécutées | 29 (74 %) ✔ | 47 (68 %) ✔ | Définitions proches (≥ 1 tirage de données ou 200) mais pas identiques : le run 2 exclut explicitement les réponses 200 qui sont des erreurs d'authentification |
| Gratuites | 37 ✔ | 62 ✔ (54 sans clé + 8 avec clé gratuite) | Le run 1 ne détaille pas 54/8 dans son bloc final |
| Payantes ou restreintes | 2 payantes (Baltic, réserves d'échange) | 2 payantes/à clé (Glassnode, LunarCrush) + 5 « restreintes » (Google Trends, Bluesky, Farside, iShares, Yahoo) | |
| Catégories | 16 (`source_records.csv`) ✔ | 15 dans le catalogue réel (le rapport dit 16) ✘ | Le run 1 a « GitHub ecosystem » et « developer activity » séparées, et « ETF/public flow » à 2 |
| PIT natif | 9 sur 39 (23 %) | 8 sur 69 (12 %), dont 7 sur 47 exécutées (15 %) | Définitions plus strictes dans le run 2 ; le run 1 range dans « natif » des sources que le run 2 déclasse |
| Adaptable | 23 (« en avant ») | 9 sur 69 (6 sur les exécutées) | Classes différentes : le run 2 sépare « adaptable » de « snapshot only » (17) |
| Sources testées statistiquement | 21 sources environ (44 séries, dont certaines de la même source) | 14 sources (TESTED_* : 11 sans gain, 2 candidats, 1 dérivé du prix) | |
| Adjudication | ADOPT 0 / ADAPT 11 / PARK 24 / REJECT 4 | tableau par familles, pas de comptes | |

#### 8.1.2 Répartition par catégorie (comptages vérifiés dans `source_records.csv` du run 1 et `catalog.py` du run 2)

| Catégorie | Run 1 (cat. / exéc.) | Run 2 (cat. / exéc.) |
|---|---|---|
| On-chain | 4 / 4 | 10 / 6 |
| Mempool | 1 / 1 | 1 / 1 |
| Échanges (flux publics) | 3 / 2 | 7 / 5 |
| Développeurs / GitHub | 4 (2 « GitHub ecosystem » + 2 « developer activity ») / 3 | 5 / 4 |
| Actualités | 1 / 1 | 2 / 1 |
| RSS | 2 / 2 | 8 / 7 |
| Réseaux sociaux publics | 4 / 3 | 8 / 6 |
| Recherche/tendance | 3 / 2 | 3 / 2 |
| Marchés de prédiction | 2 / 2 | 2 / 2 |
| CFTC | 1 / 1 | 1 / 1 |
| Flux d'ETF | 2 / 0 | 3 / 0 |
| Administrations publiques | 3 / 3 | 7 / 4 |
| Transport maritime | 3 / 1 | 3 / 1 |
| Énergie (stocks) | 3 / 1 | 3 / 1 |
| Météo | 3 / 3 | 6 / 6 |
| **Total** | **39 / 29** | **69 / 47** |

(Les totaux : run 1 = 4+1+3+4+1+2+4+3+2+1+2+3+3+3+3 = 39 ✔ ; run 2 = 10+1+7+5+2+8+8+3+2+1+3+7+3+3+6 = 69 ✔. Le run 1 a 16 catégories parce qu'il compte « GitHub ecosystem » et « developer activity » séparément ; ici je les ai fusionnées pour pouvoir comparer.)

#### 8.1.3 D'où viennent les 30 sources en plus

Mon appariement par nom (INFERENCE mienne, non fourni par les rapports) :
- **Les deux runs partagent environ 36 des 39 sources du run 1** : par ex. Blockchain.com, mempool.space, Blockstream, Blockchair, DefiLlama, GDELT DOC, RSS Cointelegraph, RSS Fed, Hacker News, StockTwits, Reddit, Bluesky, Google Trends, Wikipedia, Fear & Greed, Polymarket, Kalshi, CFTC, Farside, SEC EDGAR, Treasury TGA, NY Fed, GH Archive, GitHub REST, npm/PyPI, PortWatch, Baltic (Stooq), AIS (AISHub), EIA fichiers/API, GIE AGSI, Open-Meteo, NWS, Deribit, Binance Vision, réserves d'échange (Glassnode).
- **Seulement dans le run 1** : SPDR GLD (holdings de l'émetteur), ClickHouse playground `github_events`, NOAA NDBC (bouées).
- **Seulement dans le run 2 (environ 30 entrées)** :
  - on-chain : **Coin Metrics community**, JSON-RPC Ethereum public, Etherscan, beaconcha.in, CoinGecko ;
  - échanges : Binance fapi, **OKX**, **Bitfinex**, **Hyperliquid**, Bybit ;
  - développeurs : crates.io ;
  - social : Arctic Shift (archive Reddit), Mastodon, 4chan /biz/, LunarCrush ;
  - actualités/RSS : GDELT 2.0 **fichiers bruts 15 minutes**, CoinDesk, Decrypt, BBC business, SEC press, ECB press, Treasury press ;
  - ETF/marché : iShares, Yahoo Finance ;
  - météo : CPC degree-days, NCEI (GHCN), NASA POWER, **NOAA GFS sur AWS** ;
  - administrations : FRED/ALFRED, Fed H.4.1, taux de change ECB, IMF DataMapper.
- **Conséquence** : les deux sources qui « comptent » dans les résultats du run 2 sont l'EIA (présente des deux côtés) et Deribit (présente des deux côtés). Donc la divergence de verdict **ne vient pas** du fait que le run 2 aurait trouvé des sources absentes du run 1. Le catalogue plus large du run 2 élargit surtout la liste des candidats PIT-natifs *non testés* (GDELT brut, GFS) et des sources à capture forward, pas les positifs.
- **Séries effectivement testées** : le run 1 teste plus d'actifs (BTC, or, pétrole, gaz) et plus de séries individuelles (44), avec des données de 2023 ; le run 2 teste BTC et ETH (26 blocs) sur 2021-2026, plus l'EIA/HDD sur 2007-2026.

#### 8.1.4 Sources classées différemment dans les deux runs

| Source | Run 1 | Run 2 | Raison probable |
|---|---|---|---|
| Binance Vision | PIT_NATIVE, ADAPT (fichiers immuables) | LOOKAHEAD_RISK, PARK (33/40 fichiers anciens ré-uploadés) | Le run 2 a **mesuré** (scan `Last-Modified` de 80 fichiers) ; le run 1 a inféré de fichiers récents |
| Deribit | PARK, jamais testé (« dérivé du prix ») | ADAPT, candidat DVOL | Le run 2 a mesuré |
| EIA | ADAPT, test nul | ADAPT, candidat | Design différent (§8.3) |
| CFTC | ADAPT (test nul) | PARK (positionnement absorbé) | Mêmes résultats nuls, décision différente : marge d'appréciation |
| TGA | ADAPT (« coût faible de garder la capture ») | PARK | idem |
| DefiLlama stablecoins | ADAPT | REJECT | Le run 1 y voit un besoin de capture ; le run 2 y voit historique réécrit + gain nul |
| Hacker News | ADAPT, PIT_NATIVE | Non testé, REJECT (dans « réseaux sociaux publics ») | Le run 1 l'a testé (n = 996) |
| mempool.space | ADAPT | PARK | Même constat (pas d'historique), verdict plus prudent |
| Polymarket / Kalshi | ADAPT | PARK | idem |
| GH Archive | ADAPT | PARK | idem |
| Fear & Greed | REJECT | REJECT | ✔ Accord (R² côté prix 0,49 vs réactivité 0,426) |
| Blockchain.com | PARK | REJECT | Le run 2 ajoute la restriction de licence « non commercial » |
| Wikipedia | PARK | REJECT | idem, effet calendaire |
| Google Trends | REJECT | PARK (bloqué) | Le run 2 traite « bloqué » comme preuve manquante |
| Bluesky | 2/3 HTTP 200 (PARK) | 403, non exécuté | Point de sortie réseau et heure différents |
| Reddit | `.json` 403, REJECT | RSS 200 (exécuté), classé social REJECT | Points d'accès testés différents |
| Open-Meteo | PARK | PARK (forecast) | Quota épuisé des deux côtés |
| PortWatch | PARK | PARK | ✔ Accord |
| NY Fed | PARK | PARK | ✔ Accord |
| Farside | PARK | PARK | ✔ Accord (403) |

### 8.2 Les deux protocoles statistiques côte à côte

| Point | Run 1 | Run 2 |
|---|---|---|
| Univers d'actifs | BTC + or + WTI + gaz naturel | BTC + ETH (crypto), + WTI/Brent/Henry Hub (événements EIA/HDD) |
| Période | 2023-10 → 2026-09 (≈ 3 ans) | 2021-01 → 2026-09-01 (≈ 5,7 ans) ; EIA 2007 → 2026 |
| n BTC | 1 091 (996-1 091 pour la plupart) | 1 534 à 2 008 (DVOL : 1 896) |
| Cibles | rendement ; \|rendement\| ; **volume relatif** | rendement ; **log range (volatilité)** ; \|rendement\| |
| Baseline | 7 rendements retardés, 3 \|rend.\|, volume relatif, log vol réalisée 7 j (+ funding, ΔOI pour BTC) | rendements 1/5/20 j, log-range 1/5/20/60 j, volume/nb de trades z, taker share, funding, ΔOI, z OI, **6 dummies jour de semaine** |
| Feature | variation sur 1 semaine → z-score 90 j (26 sem.) | z-score 30 j du niveau + variation 1 jour (2 variables par bloc) |
| Test OOS | MCO extensible, 50 % d'entraînement (min 200), réajustement tous les 5 j, **Clark-West** | MCO extensible, min 400 j, réajustement tous les 10 j, **Diebold-Mariano** (conservateur en modèles emboîtés) |
| Test dans l'échantillon | NW(5), 1 coefficient | Wald HAC(5) sur le bloc (2 variables) |
| Multiplicité | BH q = 0,10 sur 132 tests, sur la **p Clark-West (OOS)** | BH q = 0,10 sur 93 tests, sur la **p_incr (dans l'échantillon)** ; DM p < 0,10 non corrigée |
| Règle de candidature | BH OOS **et** NW p < 0,05 **et** ΔR²oos > 0 **et** signe stable **et** R² prix < 0,40 **et** non par construction | p_incr < 0,05 **et** q < 0,10 **et** gain OOS > 0 **et** DM p < 0,10 **et** signe stable **et** réactivité < 0,40 |
| Contrôles | Aucun contrôle négatif/positif injecté ; simulation de puissance séparée | Bruit ×2, dérivé du prix ×1, MVRV, DVOL comme contrôle positif |
| Puissance | Simulée : 80 % à ~4 % de R² partiel | Non mesurée |
| Fuite | Comparaison délai conservateur / naïf (41 séries) | Sensibilité −1 jour (72 tests) + mesures directes de réécriture |
| Effets de calendrier | Absents de la baseline | Ajoutés après coup (trouvés nécessaires) |
| Économie réelle | Même cadre que le reste (prédiction du jour suivant, délai 7 j) | **Étude d'événement** au jour de publication (rendement contemporain) |
| Winsorisation | 0,5/99,5 % pour les futures uniquement | 0,5/99,5 % pour EIA (post hoc) |

### 8.3 Pourquoi le run 2 trouve 2 candidats et le run 1 zéro

**Constat central.** Les deux candidats du run 2 sont exactement ceux que le run 1 a soit *pas testés*, soit *testés sous une forme qui ne pouvait pas les voir*. Le contraste n'oppose donc pas deux mesures d'un même effet, il oppose deux plans d'expérience. Le tableau ci-dessous décompose les causes.

**A. Deribit DVOL**
1. **Jamais testé dans le run 1.** Aucune des 44 séries n'est issue de Deribit (registre `F` de `s3_incremental.py`). L'adjudication dit « dérivé du prix par construction » (hypothèse non testée). ✔ vérifié dans le registre.
2. **Cible adaptée dans le run 2** : DVOL passe sur le log-range (volatilité du lendemain), pas sur le rendement ni de façon significative sur |rendement|. Le run 1 n'a ni cible « range » ni cible « volatilité ».
3. **Transformation adaptée dans le run 2** : niveau + variation à 1 jour ; le run 1 n'utilise que la variation sur 1 semaine, qui perd l'information de niveau (INFERENCE mienne).
4. **Baseline avec dummies** dans le run 2 (sans elle, DVOL aurait un p tout aussi bas ; l'apport des dummies est ailleurs : supprimer les faux positifs).
5. **Longueur de l'échantillon** : 1 896 observations dans le run 2 contre ≈ 1 090 dans le run 1 ; DVOL n'existe qu'à partir de 2021-03-24.
6. **Sévérité de la règle** : sous une règle « BH sur p OOS » comme celle du run 1, DVOL aurait un q ≈ 0,507 (calcul mien) et ne passerait pas. Sa force est surtout dans l'échantillon (p ≈ 0) plus une OOS DM p = 0,0055. Donc *même avec les bonnes données*, le run 1 aurait pu conclure « non candidat » selon sa règle.

**B. Stocks de pétrole brut EIA**
1. **Design de dates différent.** Run 1 : la surprise est disponible 7 jours après la fin de semaine ; on prédit le rendement du **lendemain** d'un jour où la feature est déjà périmée d'une semaine. Le jour de publication (mercredi) n'est **jamais regardé**. Le run 2 regarde justement le rendement du jour de publication. Un effet contemporain (« le marché réagit le jour de la publication ») est **invisible par construction** dans le design du run 1. Le fait que le run 2 trouve un effet nul sur le lendemain (p = 0,861) est cohérent avec ce diagnostic.
2. **Définition de la « surprise »** : run 1 = variation hebdomadaire des stocks (log-différence, z-scorée sur 26 semaines) ; run 2 = variation moins la moyenne saisonnière des 5 années précédentes, divisée par l'écart-type sur 104 semaines. La saisonnalité des stocks de pétrole est forte ; ne pas l'ôter noie la surprise.
3. **Fenêtre** : run 1 = 2023-06 → 2026 (173 semaines) ; run 2 = 2007 → 2026 (1 026 publications). Le run 2 lui-même montre que, sur 2021-2026 (297 publications), l'effet n'est plus détecté (t = −1,11, p = 0,265). INFERENCE mienne : **même avec le bon design, une fenêtre 2023-2026 n'aurait probablement pas détecté l'effet**. Le fait que le run 1 ait ses 3 ans les plus récents explique donc une partie de la divergence.
4. **Signe** : le t du run 1 pour `eia_crude` est **+1,81** (meilleure cible ret, feature périmée), à l'opposé du run 2 (−5,32) — signe que le run 1 mesure autre chose (du bruit).
5. **Prix utilisé** : run 1 = futures Yahoo continus non ajustés, run 2 = prix spot WTI/Brent de l'EIA (série `RWTC`/`RBRTE`) — plus propres.
6. **Winsorisation** : le run 2 doit une partie de son résultat OOS (DM p 0,22 → 0,058) à une winsorisation décidée après coup.

**C. Ce qui, à l'inverse, joue contre le run 2 et le rapproche du run 1**
- **Aucun des 21 autres blocs** n'a passé chez le run 2 (min q_fam hors DVOL = 0,26), comme chez le run 1 (min q = 0,66).
- Les deux runs concluent que le calendrier/le prix expliquent la plupart des faux positifs.

**D. Effets différents de l'« indépendance vis-à-vis du prix »**
- Run 1 : R² de la feature sur des variables de prix (à sa date native) < 0,40. Run 2 : R² sur le prix du **même jour** + 5 retards. Les seuils numériques se ressemblent, les définitions non ; `fear_greed` : 0,487 (run 1) vs 0,426 (run 2), `cm_exchange_flows` 0,41 (run 2) ; Wikipedia Bitcoin 0,336 (run 1, « PRICE_LINKED_PARTIAL ») vs 0,126 (run 2, « INDEPENDENT »).

### 8.4 Comparaison des puissances

| Aspect | Run 1 | Run 2 |
|---|---|---|
| Analyse de puissance | **Oui** : simulation à 80 répétitions, cibles ret/abs/vol, n = 1 091 | **Non** |
| Effet minimal détectable annoncé | ≈ 3-4 % de R² partiel à 1 jour (80 % de puissance) | Non chiffré |
| Mesures de puissance associées | 4 % → 90 % (ret), 77,5 % (abs), 96,25 % (vol) ; 2 % → 33,75 % / 22,5 % / 43,75 % ; ≤ 1 % → ≤ 7,5 % | Contrôle positif DVOL : p ≈ 0, gain 2,29 % ; 12 tests de bruit : 0 faux positif |
| Puissance des séries hebdomadaires | « bien plus faible » (≈ 170 observations) | Économie réelle : 300 à 1 000 événements ; pas de calcul |
| Taille d'échantillon | BTC 1 091 ; GitHub 259-489 ; hebdo 173 | BTC 2 008 (1 896 DVOL) ; ETH 1 339-1 676 ; EIA 1 026 |
| Correction de multiplicité | Sévère (132 tests, sur OOS) → grande perte de puissance | Modérée (93 tests, in-sample) + seuils OOS non corrigés |
| Biais de puissance | Portillon CW p < 0,00083 dans la simulation : très sévère ; règle réelle : BH sur 132 | Test DM conservateur (sous-puissant) ; règle réelle moins stricte que celle du run 1 |

**Lecture.**
- Le run 1 est **plus transparent sur ce qu'il ne peut pas voir** (il chiffre son effet minimal détectable), mais il conclut « inconclusive » à juste titre : son test aurait manqué presque tout effet inférieur à 2 %.
- Le run 2 a **plus de données et un meilleur design pour la volatilité**, ce qui explique en partie ses deux détections, mais il ne mesure pas sa propre puissance ; son verdict « limited supported » a donc un fondement moins clair sur ce qui n'est *pas* détecté.
- INFERENCE (mienne, non simulée) : à n ≈ 2 000 et à famille de 93 tests, l'effet minimal détectable du run 2 se situerait grossièrement autour de 1,5-2 % de R² partiel, encore élevé. Un effet réel de 0,5 % passerait probablement inaperçu dans **les deux** runs.

### 8.5 Où les deux runs s'accordent

- Aucun bloc crypto « alternatif » (on-chain, DeFi, attention, positionnement Binance, CFTC, TGA, NY Fed, GitHub/npm) ne montre d'information incrémentale OOS robuste (run 1 : q min 0,66 ; run 2 : q min 0,26 hors DVOL).
- La plupart des gains OOS sont négatifs (run 1 : 74 % des tests ; run 2 : 93,5 % des 93 tests).
- Fear & Greed est dérivé du prix (0,49 / 0,43).
- Les flux d'échange, actifs on-chain USD et TVL sont soit dérivés du prix soit sans gain.
- Le régime PIT de presque toutes les sources gratuites est « historique sans horodatage de publication » ; la capture forward est la seule route.
- Le mempool n'a pas d'historique gratuit.
- Les catégories ETF, Google Trends, RSS/news/social, prédiction (historique court) restent non testables gratuitement.
- Le test d'inflation par datation naïve est cité par le run 1 ; le run 2 le remplace par la mesure directe de réécriture. Les deux montrent que la datation compte.
- Les deux recommandent une capture forward (mempool, RSS, Kalshi/Polymarket, NWS, EIA/CFTC), un re-test aux horizons multi-jours ou par événement, et davantage d'actifs pour la puissance.
- Le CFTC est vu, dans les deux, comme publié le vendredi pour la date de mardi (règle de +3 j 19h30 UTC ; horodatages natifs seulement après 2022-09 dans le run 2).

### 8.6 Où elles divergent et pourquoi

| Divergence | Explication probable | Niveau de confiance |
|---|---|---|
| Candidats : 0 contre 2 | DVOL non testé dans le run 1 ; EIA testé avec un design qui ne voit pas l'effet de jour de publication ; fenêtre plus courte ; règle OOS plus sévère | Élevé pour DVOL (vérifié : absent du registre) ; élevé pour le design EIA (vérifié dans le code) |
| Binance Vision PIT-native contre LOOKAHEAD_RISK | Le run 2 a mesuré 33/40 fichiers ré-uploadés | Élevé (chiffres dans `binance_vision_lastmodified_scan.csv`) |
| Verdict INCONCLUSIVE contre LIMITED | Le run 1 s'appuie sur la puissance faible ; le run 2 sur les contrôles calibrés | Divergence d'interprétation |
| Nombre de sources | Portée : le run 2 a ajouté ≈ 30 entrées (plateformes d'échange, RSS, météo, admin.) | Élevé |
| Décisions ADAPT/PARK sur les mêmes sources nulles (CFTC, TGA, mempool, Polymarket) | Politique de tri : le run 1 garde en ADAPT tout ce qui est PIT-adaptable, le run 2 met en PARK ce qui n'a rien montré | Moyen |
| Wikipedia Bitcoin : R² prix 0,336 contre réactivité 0,126 | Définition du diagnostic (matrice de 6 à 8 variables à la date native vs 16 variables de prix du jour + retards) | Moyen |
| Hacker News | Le run 1 y trouve 996 jours de séries et le teste ; le run 2 ne l'utilise qu'en snapshot (100 items = 81 jours) | Élevé |
| Bluesky et Reddit | Accessibilité au moment de la sonde / point d'accès différent | Moyen |
| Comptes PIT (9/39 vs 7/47 exécutées) | Définitions et périmètre différents | Élevé |

**Aucune des deux ne réplique l'autre au sens strict.** Le seul résultat « en commun » est que l'EIA a été jugé digne de capture forward (ADAPT) et que le résultat sur EIA est discordant.

---

## 9. Reproductibilité

### 9.1 Run 1 (`R1:bench/alternative_data_v1/README.md`)

- Dépendances : `pip install pandas numpy scipy statsmodels requests xlrd`.
- Commandes (depuis `py/`) : `python3 s2_fetch.py`, `s1_probe.py`, `s2b_revision.py`, `s5_latency.py`, `s3_incremental.py`, `s4_power.py`, `gen_reports.py`.
- Durée : non documentée (`s4_power.py` = 3 cibles × 5 niveaux × 80 répétitions, chacune avec un OOS complet : probablement long ; non mesuré, ?).
- Fournis : 23 fichiers de données (`data/*.csv`, 58 fichiers au total pour la lane, 1,79 MiB), tous les résultats agrégés, les scripts, le catalogue.
- Manquants / limites : **dépend de l'accès réseau et de la date** (« les données sont des instantanés du 2026-09-29 ; une relance peut différer »). Les sondes 429/403 dépendent de l'IP de sortie. `gen_reports.py` écrit les rapports depuis les résultats (« les nombres sont lus dans `results/`, non tapés ») : les tableaux sont donc reproductibles, mais les notes de prose du catalogue sont manuelles. `probe_results.json` (22 Ko) et `fetch_log.json` sont fournis.

### 9.2 Run 2 (`R2:bench/alternative_data_v1/README.md`)

- Dépendances : `pip install requests pandas numpy scipy statsmodels`.
- Commandes : `python collect.py && python collect_rest.py && python fetch_eia.py`, puis `python probe_all.py && python pit_probes.py && python licenses.py`, puis `python analysis_crypto.py && ALT_NO_CALENDAR=1 python analysis_crypto.py && python summarize.py`, puis `ALT_NO_WINSOR=1 python real_economy.py && python real_economy.py && python real_economy_robust.py`, puis `python gen_reports.py`.
- Durée : non documentée (le téléchargement de ≈ 4 400 fichiers Binance et le retrait de GDELT/GH Archive prendraient probablement longtemps ; ?).
- Fournis : 71 fichiers, 4,64 MiB ; données quotidiennes et résultats ; variantes « sans calendrier » et « sans winsorisation » (le run 2 permet de reproduire ses propres forking paths avec des variables d'environnement).
- **Manquants** : `data/um_metrics_5m_*.csv.gz` (40 Mo) et `data/raw/` (≈ 60 Mo : zips EIA `PET.zip`, `NG.zip`) **ne sont pas dans le dépôt** ; `real_economy.py` et `real_economy_robust.py` ne sont donc pas exécutables sans `fetch_eia.py`, ce qui nécessite d'accéder à `eia.gov` au moment de la relance, sur des fichiers **susceptibles d'avoir changé** (`last_updated` 2026-09-23). Les résultats EIA ne sont pas vérifiables à partir du dépôt seul : je n'ai pu vérifier que les tableaux de résultats, pas recalculer la surprise (? non vérifiable).
- Un avertissement `Pandas4Warning` (`Timestamp.utcnow` déprécié) apparaît dans les journaux : sans conséquence, mais dépendant de la version de pandas.

### 9.3 Ce que j'ai fait, moi

Relecture de tous les rapports 00-10 des deux runs ; lecture de `s3_incremental.py`, `s4_power.py`, `lib.py`, `pit.py`, `adjudication.py`, `s5_latency.py` (run 1) et `analysis_crypto.py`, `panel.py`, `summarize.py`, `real_economy.py`, `real_economy_robust.py`, `catalog.py` (run 2) ; recalcul en Python (pandas) sur les CSV/JSON de résultats (aucune relance réseau). Les chiffres marqués ✔ ont été recalculés ainsi.

### 9.4 Tableau de vérification (chiffres rapport vs fichiers)

| # | Chiffre du rapport | Fichier | Statut |
|---|---|---|---|
| 1 | R1 : 132 tests, 44 séries, 0 candidat, q min 0,66 | `R1:results/incremental.csv` | ✔ (q min 0,6637) |
| 2 | R1 : 5 tests p CW < 0,05 contre ≈ 6,6 attendus | idem | ✔ (5 ; 6,6) |
| 3 | R1 : classes 29 / 9 / 6 | idem | ✔ |
| 4 | R1 : 9 sur 41 séries avec |t| > +1 en délai 0 ; 4 → 6 tests significatifs | `R1:results/incremental.json` | ✔ |
| 5 | R1 : puissance 4 % → 90/78/96 % | `R1:results/power_btc.json` | ✔ (90 ; 77,5 ; 96,25) |
| 6 | R1 : PIT 9 / 23 / 7 ; ADAPT 11, PARK 24, REJECT 4 | `R1:results/source_records.csv` | ✔ |
| 7 | R1 : trou ClickHouse et instabilité | `R1:results/gh_playground_stability.json` | ✔ |
| 8 | R1 : `gh_merged_pr` p 0,005, ΔR² +4,38 %, q 0,66, n 259 | `incremental.csv` | ✔ |
| 9 | R1 : re-fetch, 0 changement sur 6 séries | `revision_test.json` | ✔ |
| 10 | R1 : Deribit « 6/6 HTTP 200 » vs « une sonde 502 » | `probe_results.json` | ✘ (seulement des 200) |
| 11 | R2 : 69 / 47 / 62 / 54 / 8 ; PIT 7-6-17-17 | `R2:py/catalog.py` | ✔ |
| 12 | R2 : « 16 catégories » | `catalog.py` | ✘ (15) |
| 13 | R2 : 93 tests, 15 p<0,05, 4,7 attendus, q min hors DVOL 0,26, bruit 0/12 | `summary.json`, `incremental_results.csv` | ✔ |
| 14 | R2 : DVOL gain OOS 2,29 %, DM p 0,005 | `incremental_results.csv` | ✔ (2,2916 ; 0,0055) |
| 15 | R2 : EIA t −5,32, OOS 2,50 %, DM p 0,058 | `real_economy_results.csv` | ✔ (−5,320 ; 2,496 ; 0,0584) |
| 16 | R2 : Brent t −6,03 ; mardi p 0,038 ; 2021-2026 p 0,27 | `crude_robustness.csv` | ✔ (−6,028 ; 0,0383 ; 0,265) |
| 17 | R2 : sans winsorisation gain 0,89 %, DM p 0,22, t −4,61 | `real_economy_results_raw_returns.csv` | ✔ (0,888 ; 0,2206 ; −4,605) |
| 18 | R2 : sans calendrier 29/90, 11 à p<0,001, 8 DM<0,10 | `incremental_results_no_calendar.csv` | ✔ |
| 19 | R2 : Coin Metrics 2 067 / 2 024 sur 2 219 | `pit_probes.json` | ✔ (attention : « valeurs recalculées » est une inférence) |
| 20 | R2 : Binance Vision 33/40, médiane 371 j | `binance_vision_lastmodified_scan.csv` | ✔ |
| 21 | R2 : CFTC 231/442, 211 avec horodatage réel, 183 vendredis | `pit_probes.json` | ✔ |
| 22 | R2 : PortWatch p 0,16, n 381 | `portwatch_result.csv` | ✔ (0,157) |
| 23 | R2 : période « 2021-01-01 → 2026-09-28 » | `incremental_results.csv` | ✘ (jusqu'au 2026-09-01) |
| 24 | R2 : 50 pages de licence, 31 fournisseurs | `license_evidence.json` | ? 31 entrées ✔, 50 pages non recomptées |
| 25 | R2 : EIA `last_updated` et calcul de la surprise | données brutes (`data/raw`, non fournies) | ? non vérifiable |

---

## 10. Implications pratiques pour AurumShift (pistes « à adjuger plus tard »)

Rappel : **rien ici n'affirme une compatibilité avec AurumShift**. Ce sont des pistes à juger plus tard contre le vrai dépôt local.

1. **Une capture forward, horodatée et append-only, de quelques flux « sans historique »** (état mempool, RSS, marchés Kalshi/Polymarket, prévisions NWS, publications EIA/CFTC, Coin Metrics avec ses champs de complétion) est la seule voie que les deux runs jugent capable de convertir du LOOKAHEAD_RISK en PIT. C'est cohérent avec la contrainte « PIT / provenance critiques ». Coût et faisabilité à juger. Piste à adjuger plus tard.
2. **Piste EIA** : si un jour AurumShift traite du pétrole, l'effet de la surprise de stocks est *contemporain* et non prévisible depuis un pas de temps quotidien ; les deux runs suggèrent qu'un test à horodatage intraday serait nécessaire pour savoir s'il existe une fenêtre exécutable. À adjuger plus tard ; vu le fade post-2021, aucune attente de valeur ne peut être posée.
3. **Piste volatilité implicite (DVOL)** : l'information d'un second marché (options) semble prédire la volatilité du lendemain au-delà du prix/volume/vol/funding/OI. Son intérêt dépend entièrement de ce qu'AurumShift possède déjà comme entrée de volatilité — impossible à savoir ici. À adjuger plus tard.
4. **Piste « ne pas se fier aux historiques gratuits »** : les mesures du run 2 (réécriture massive des fichiers Coin Metrics et Binance `metrics`) plaident pour un versionnage systématique de toute donnée externe ingérée. Compatible avec l'esprit « une source faisant autorité par sujet ; provenance ». À adjuger.
5. **Piste licences** : plusieurs sources ont des conditions non commerciales ou floues (Blockchain.com, Open-Meteo, CoinGecko, Reddit, StockTwits, Yahoo, Coin Metrics variante CC à confirmer). Tant que le projet reste research/paper-only, c'est tolérable ; cela rouvrirait à toute étape commerciale. À adjuger.
6. **Piste hygiène de test** : le contrôle par variables de jour de semaine du run 2 (qui a supprimé 8 faux positifs OOS) est une leçon transférable à toute évaluation de feature. Je ne prétends pas que ce contrôle manque chez AurumShift, je ne le sais pas.

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **Réconcilier les deux protocoles en un seul** : rerunner le run 1 avec (a) les cibles « range » et « volume » séparées, (b) des dummies de jour de semaine, (c) niveau + variation, (d) DVOL en candidat, (e) une correction de multiplicité identique pour toutes les règles, (f) un test Clark-West au lieu de DM. Valeur : élevée ; c'est la seule façon de savoir si la divergence tient à la donnée ou au plan d'expérience. Coût : modéré, tout le code est fourni.
2. **Mesurer la puissance du run 2** : appliquer la simulation de `s4_power.py` à la règle du run 2 (n ≈ 2 000, DM). Valeur : élevée, faible coût.
3. **Étude EIA à l'échelle intraday** avec prix horodatés (première fenêtre après 10h30 ET) et une « surprise » alignée sur le consensus, ainsi que le placebo du mardi (rapport API). Permet de dire si un effet exécutable existe. Valeur : élevée si le pétrole intéresse ; moyenne sinon.
4. **Sensibilité de la winsorisation et du fade** : reprendre l'EIA avec plusieurs seuils et des fenêtres glissantes de 5 ans (pas des sous-périodes fixes), en rapportant les OOS sur des blocs assez longs (les sous-périodes actuelles n'ont pas assez d'observations OOS). Valeur : moyenne.
5. **Mesurer l'effet de la réécriture de Binance Vision sur la baseline** (OI/funding), commun aux deux runs, en comparant fichiers récents et anciens ré-uploadés. Valeur : moyenne.
6. **Lancer la capture forward** décrite ci-dessus (6 à 12 mois) puis retester. Valeur : élevée à long terme, coût opérationnel réel.
7. **Tester les sources PIT-natives non testées** : GDELT GKG filtré par thèmes (≈ 0,17 To/an en brut), Kalshi/Polymarket par événements macro, GH Archive (dépôts crypto), Open-Meteo historical-forecast et GFS vs Henry Hub, EDGAR (13F/Form 4). Valeur : élevée en potentiel, coût variable.
8. **Étendre l'univers** (plus de coins, ETF/actions, futures ajustés) pour la puissance. Valeur : moyenne à élevée.
9. **Analyse Clark-West vs DM** sur les mêmes données : chiffrer l'écart de sévérité. Valeur : faible-moyenne, coût faible.
10. **Vérifier les points ✘** : Deribit 502 (run 1), 16 vs 15 catégories et période effective (run 2). Valeur : faible (hygiène de rapport).

---

## 12. Index des fichiers lus

### 12.1 Rapports run 1 (`origin/claude/alternative-data-v1:reports/016_alternative_data/`)

| Fichier | Contenu |
|---|---|
| `00_EXECUTIVE_SUMMARY.md` | Synthèse, 7 constats, comptes d'adjudication, bloc final |
| `01_SOURCE_LANDSCAPE.md` | Fiches de 39 sources en 16 catégories (tableaux à 10 attributs) |
| `02_ONCHAIN.md` | On-chain/mempool/développeurs, instabilité ClickHouse, table de résultats |
| `03_NEWS_SOCIAL.md` | Actualités/RSS/social/tendances/prédiction, résultats F&G, HN, Wikipedia |
| `04_POSITIONING_FLOWS.md` | CFTC, ETF, positionnement Binance, observation de publication |
| `05_REAL_ECONOMY.md` | PortWatch, EIA, météo, TGA, résultats |
| `06_PIT_READINESS.md` | Règle de classification, comptes, re-fetch, latence, démonstration de fuite |
| `07_INCREMENTAL_INFORMATION.md` | Protocole, puissance, rejets « prix », table complète des 44 séries |
| `08_LICENSE_COST.md` | Coût et licence de 39 sources, comptage du risque |
| `09_ADJUDICATION.md` | ADOPT/ADAPT/PARK/REJECT par source, étapes suivantes |
| `10_LIMITATIONS.md` | 11 limites |

### 12.2 Fichiers `bench/alternative_data_v1` du run 1 lus

| Fichier | Contenu |
|---|---|
| `README.md` | Description des scripts et de la reproduction |
| `py/s3_incremental.py` | Protocole complet, registre des 44 séries, tests, classification (lu intégralement) |
| `py/s4_power.py` | Simulation de puissance (lu intégralement) |
| `py/lib.py` | Utilitaire HTTP (lu intégralement) |
| `py/pit.py`, `py/adjudication.py` | Classification PIT et adjudication (lus) |
| `py/s5_latency.py`, `py/s1_probe.py`, `py/s2b_revision.py`, `py/s2_fetch.py`, `py/catalog.py`, `py/gen_reports.py` | Instantané de latence, sondes, révision, tirage de données, catalogue, génération des rapports (en-têtes et parties clés) |
| `results/incremental.csv`, `incremental.json` | 132 tests ; variantes naïves |
| `results/power_btc.json` | Puissance |
| `results/source_records.csv/.json`, `probe_results.json`, `fetch_log.json` | 39 sources, sondes, journal de tirage |
| `results/revision_test.json`, `latency_snapshot.json`, `cftc_headers.json`, `gh_playground_stability.json`, `final_block.txt` | Observations manuelles et bloc final |
| `data/portwatch_chokepoints_tankers.csv`, `eia_crude_stocks_ex_spr.csv`, `cftc_btc_cme_tff.csv`, `gh_crypto_dev_agg.csv`, `btc_spot_1d.csv` | Échantillonnés (nombre de lignes, dates) |

Non lus en détail : les autres CSV de données du run 1 (`btc_funding_daily.csv`, `btc_oi_metrics_daily.csv`, etc.) — non lus.

### 12.3 Rapports run 2 (`origin/claude/alternative-data-v1-b:reports/016_alternative_data/`)

| Fichier | Contenu |
|---|---|
| `00_EXECUTIVE_SUMMARY.md` | Verdict, 2 candidats, 4 constats, bloc final |
| `01_SOURCE_LANDSCAPE.md` | Index des 69 sources, blocages observés |
| `02_ONCHAIN.md` | Fiches on-chain/mempool/échanges/développeurs (lu en grande partie) |
| `03_NEWS_SOCIAL.md` | Fiches RSS/actualités/social/prédiction, rétention des flux (lu en grande partie) |
| `04_POSITIONING_FLOWS.md` | CFTC, ETF, Binance |
| `05_REAL_ECONOMY.md` | EIA (tableau principal, robustesse), gaz, météo, PortWatch, fiches gouvernement |
| `06_PIT_READINESS.md` | Définitions, preuves gathered, délais, registre |
| `07_INCREMENTAL_INFORMATION.md` | Design, contrôles, résultats, artefact calendaire, sensibilité |
| `08_LICENSE_COST.md` | Coût, licences par mots-clés |
| `09_ADJUDICATION.md` | Verdict et décisions par famille |
| `10_LIMITATIONS.md` | 11 limites |

Les fichiers `01_METHODS.md`, `02_PROTOCOL.md`, etc. présents dans mon répertoire de travail appartiennent à d'autres lanes et n'ont pas été utilisés.

### 12.4 Fichiers `bench/alternative_data_v1` du run 2 lus

| Fichier | Contenu |
|---|---|
| `README.md` | Description, commandes de reproduction |
| `py/analysis_crypto.py`, `panel.py`, `summarize.py`, `real_economy.py`, `real_economy_robust.py` | Protocole, panneau, classification, événement EIA, robustesse (lus intégralement) |
| `py/catalog.py` | Catalogue des 69 sources (exécuté pour compter) |
| `py/probe_all.py`, `collect.py`, `collect_rest.py`, `fetch_eia.py`, `licenses.py`, `pit_probes.py`, `h.py`, `gen_reports.py` | En-têtes et parties clés |
| `results/summary.json`, `candidate_summary.csv`, `incremental_results.csv`, `incremental_results_no_calendar.csv` | Résultats crypto |
| `results/real_economy_results.csv`, `real_economy_results_raw_returns.csv`, `crude_robustness.csv`, `portwatch_result.csv`, `eia_series_last_updated.json`, `real_economy_robust.log` | Résultats économie réelle |
| `results/pit_probes.json`, `binance_vision_lastmodified_scan.csv`, `license_evidence.json`, `collect_rest.log`, `probe_stdout.txt` (début), `analysis_crypto.log` (début) | PIT, licences, journaux |
| `data/collect_log.json`, `data/deribit_dvol_1d.csv` (début/fin), `data/klines_1d_BTCUSDT.csv` (début/fin) | Journal de collecte, échantillons |

Non lus : `results/probe_results.json` (72 Ko) en dehors de ce qu'en cite le rapport — non lu intégralement ; les CSV de données lourds (Coin Metrics, funding, npm, etc.) — non lus ; `results/analysis_crypto_no_calendar.log`, `real_economy.log`, `real_economy_raw_returns.log` — non lus (doublons des CSV) ; `results/real_economy_robust.log` lu.

### 12.5 Autres

- `claude.md` (sur `origin/main`) : doctrine du dépôt.
- Liste des pull requests du dépôt `redguiff-bot/aurumshift-external-research-lab` (numéros, dates, statut) via l'API GitHub.
