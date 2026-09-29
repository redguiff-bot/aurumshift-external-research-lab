# Lane 017 — Infrastructure OSS pour la recherche en trading : analyse approfondie des deux runs

Analyse rédigée le 2026-09-29 (horloge du bac à sable) pour Jean-François. Elle porte sur deux exécutions indépendantes de la même mission (PR #16 : 54 projets ; PR #18 : 67 projets), toutes deux conclues `MULTIPLE_OSS_COMPONENTS_SUPPORTED`.

**Conventions de lecture.**
- « Run 1 » = PR #16, branche `origin/claude/oss-trading-research-infra-v1`. « Run 2 » = PR #18, branche `origin/claude/amazing-wozniak-bwjdfp`.
- Pour chaque chiffre clé, le chemin du fichier est donné entre parenthèses. Les chemins commençant par `reports/` ou `bench/` existent sur les DEUX branches sauf mention contraire (les deux runs écrivent dans les mêmes dossiers, ce qui fait que les deux PR entrent en collision si on fusionne les deux).
- Marques de vérification : **✔ vérifié** (j'ai recalculé ou relu le fichier de résultat brut et il concorde), **✘ écart** (le rapport et le fichier brut ne concordent pas), **? non vérifiable** (le fichier brut nécessaire n'est pas dans la branche).
- Les étiquettes du dépôt (`claude.md`) sont conservées : PROVEN (preuve avec vérité indépendante), OBSERVED (constaté en exécutant ou en inspectant), DOCUMENTED_CLAIM (affirmé par une documentation), INFERENCE (déduit), UNKNOWN (inconnu).
- Je n'ai rien exécuté d'autre que : (a) l'extraction des deux branches dans un dossier temporaire (sans checkout ni modification de branche), (b) un recalcul en pandas des défauts injectés du test qualité de données du run 2, (c) le téléchargement du code source de la bibliothèque `ta` 0.11.0 pour vérifier un mécanisme de fuite (voir 7.1). Rien n'a été poussé.

**Petit lexique dès maintenant (les autres termes sont expliqués à leur première occurrence).**
- **OSS** (open source software) : logiciel dont le code est publié et réutilisable selon une licence.
- **Microtest** : petit essai ciblé et reproductible d'une bibliothèque (une question, un résultat attendu connu).
- **Oracle** : une réponse de référence, calculée autrement (à la main, avec numpy, etc.), à laquelle on compare la bibliothèque testée.
- **Lookahead / fuite du futur** : un calcul qui utilise, sans le dire, une information qui n'était pas encore connue à la date simulée (ex. la moyenne de toute la série pour remplir le début). Cela rend un backtest trop beau pour être vrai.
- **PIT (point-in-time)** : donnée « telle qu'on la connaissait à cette date-là », sans révisions ultérieures.
- **Backtest** : rejouer une stratégie sur des données passées pour voir ce qu'elle aurait fait.
- **Carnet d'ordres (order book, L2)** : la liste des offres d'achat et de vente par niveau de prix ; « L2 » = agrégé par prix.
- **Bus factor** : nombre de personnes dont le départ bloquerait le projet ; ici approximé par le nombre d'auteurs nécessaires pour couvrir 50 % des commits (modifications) des 12 derniers mois.

---

## 0. Fiche d'identité

| | Run 1 | Run 2 |
|---|---|---|
| PR | #16, brouillon (draft), ouverte, titre « research(017): OSS trading research infra discovery (54 projects, 32 executed) » | #18, brouillon, ouverte, titre « research(017): external OSS trading-research infra discovery V1 (67 screened, 41 executed) » |
| Branche | `claude/oss-trading-research-infra-v1` | `claude/amazing-wozniak-bwjdfp` |
| Commit unique | `bb1371a78d4b25caf573f9887898adad321aebff`, 2026-09-29 18:21:10 UTC | `930e880bc64ff374a500cf483d41c6d60a1272fc`, 2026-09-29 18:52:03 UTC |
| Base | `1a449df` (main) | `1a449df` (main) |
| Session Claude | `session_01TE71zBiokn6WbeP18D2xfy` | `session_01Az3ce41PxQDY1woZ9hhCPg` |
| Fichiers de la lane | 87 fichiers dans `reports/017_oss_trading_infra` + `bench/oss_trading_infra_v1` ; 206 359 octets (git ls-tree) ; PR : 87 fichiers, +2 449 lignes | 78 fichiers ; 333 948 octets ; PR : 78 fichiers, +7 687 lignes |
| Rapports | 10 rapports `00` à `09` (43 630 octets) | 10 rapports `00` à `09` (78 473 octets) |
| Projets découverts / exécutés | 54 / 32 (31 microtests complets + 1 partiel : databento-dbn) | 67 / 41 (+ 3 installés/importés seulement, 23 sur métadonnées seulement) |
| Microtests | 16 (T01 à T16), 12 environnements virtuels isolés, 3 versions de Python (3.9, 3.12, 3.13) | 18 scripts de microtest dans `py/mt/` (+ `common.py`, `naut_lib.py`) et 2 fichiers SQL ; registre T1 à T21 dans le rapport 06 ; 1 instance PostgreSQL 16 + TimescaleDB 2.30.2 + pg_partman 5.0.1 ; empreinte d'installation isolée pour 33 candidats ; Python 3.9/3.11/3.12 |
| Verdict final | `FINAL_VERDICT=MULTIPLE_OSS_COMPONENTS_SUPPORTED` | `FINAL_VERDICT=MULTIPLE_OSS_COMPONENTS_SUPPORTED` |
| Répartition | ADOPT_REFERENCE 9 · ADAPT_CANDIDATE 5 · PARK 32 · REJECT 8 | ADOPT_REFERENCE 14 · ADAPT_CANDIDATE 10 · PARK 36 · REJECT 7 |
| Deuxième service / datastore | 5 / 7 (aucun exécuté) | 5 / 8 |
| Composant « drop-in » | OUI (niveau bibliothèque : exchange_calendars, pandas_market_calendars) | OUI (étroit : exchange_calendars, river, hdrhistogram/ddsketch, TA-Lib, pyarrow, DuckDB/polars en calcul seul) |

**Force du verdict.** Le verdict `MULTIPLE_OSS_COMPONENTS_SUPPORTED` signifie « plusieurs composants open source sont soutenus par des preuves » ; il ne désigne pas une « meilleure plateforme » (les deux runs le disent explicitement : `reports/017_oss_trading_infra/08_ADJUDICATION.md`). Force réelle : **modérée**. Elle repose sur des données synthétiques (générées par ordinateur, avec graine fixe), une configuration par test et des oracles écrits par le testeur lui-même (voir sections 6 et 7). Pour les petites bibliothèques pures (calendriers, statistiques en ligne, optimiseurs de portefeuille), la preuve est solide sur ce qui a été testé. Pour les moteurs de rejeu/backtest, elle est solide sur l'arithmétique mais ne dit rien sur des marchés réels. La compatibilité avec AurumShift est **UNKNOWN par construction** (frontière de `claude.md` : aucun code privé lu).

Sur GitHub : la description de la PR #18 précise que les deux runs écrivent dans les mêmes chemins et qu'« un seul doit être fusionné ». Cette analyse les compare ; la décision de fusion t'appartient (sections 8 et 11).

---

## 1. Mission et question posée

**Mission (identifiant repris des deux runs) :** `AURUMSHIFT_EXTERNAL_OSS_TRADING_RESEARCH_INFRA_DISCOVERY_V1` (`reports/017_oss_trading_infra/00_EXECUTIVE_SUMMARY.md`, les deux branches).

**Question reformulée simplement.** Avant de recoder soi-même la « plomberie » d'un laboratoire de trading (récupérer des données de marché, connaître les jours ouvrés des bourses, contrôler la qualité des données, rejouer un carnet d'ordres, simuler des exécutions avec des frais réalistes, calculer des indicateurs et des mesures de risque), existe-t-il des projets open source déjà écrits, fiables et faciles à maintenir, qu'on pourrait réutiliser ? Et lesquels ont vraiment été **vérifiés en les faisant tourner**, plutôt que jugés sur leur page de présentation ou leur nombre d'étoiles GitHub ?

**Treize classes de composants** ciblées (rapport `01_LANDSCAPE.md` du run 2, tableau « Component classes ») : collecteurs de données de marché, téléchargeurs d'historique, bibliothèques de carnet d'ordres, moteurs de rejeu / simulateurs d'événements, modèles de coûts de transaction, calcul de caractéristiques (features, indicateurs), statistiques en ligne, portefeuille/risque, moteurs de backtest, calendriers de marché, cadres de qualité de données, stockage de séries temporelles.

**Contraintes de `claude.md` (dépôt racine) appliquées :**
- Doctrine **REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST** : d'abord réutiliser tel quel, puis adapter, puis envelopper, puis composer, et écrire du code sur mesure seulement en dernier. Ne pas classer un projet d'après ses étoiles GitHub. Ne pas fabriquer de résultats de benchmark.
- Étiquettes de preuve : PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN.
- Verdicts possibles : ADOPT / ADAPT / PARK / REJECT. Ici ils sont déclinés en ADOPT_REFERENCE (utilisable comme bibliothèque, oracle ou spécification, avec peu de couplage), ADAPT_CANDIDATE (utile mais demande enveloppe/adaptation/version figée), PARK (à revoir si une condition change), REJECT (pas pour cet usage).
- **Frontière** : ne jamais affirmer qu'un candidat est compatible avec AurumShift à partir de ce seul dépôt ; l'adjudication finale se fait plus tard, contre le vrai dépôt local d'AurumShift.
- Contraintes AurumShift à garder en tête : recherche seule / papier seul (pas de capital réel), PostgreSQL d'abord, PIT/provenance/absence de lookahead critiques, événementiel/intrajournalier plutôt que haute fréquence, **une seule source d'autorité par sujet** (donc éviter un second datastore ou service), l'absence de preuve n'est pas une preuve négative, coûts de marché réalistes, faible charge pour l'opérateur, reproductibilité scientifique.

---

## 2. Méthode

### 2.1 Découverte et criblage

| | Run 1 | Run 2 |
|---|---|---|
| Sources de découverte | Écosystème connu + métadonnées PyPI + 3 recherches web ; l'API de recherche GitHub était bloquée (« sessions are bound to their configured repositories ») (`reports/017_oss_trading_infra/01_LANDSCAPE.md`) | Catalogue écrit à la main (`bench/oss_trading_infra_v1/py/catalog.py`, 67 entrées) « INFERENCE from prior knowledge » puis contrôlé sur l'état amont réel ; l'API REST de GitHub a répondu 403 (`01_LANDSCAPE.md`) |
| Historique git | Clones « nus sans blobs » (bare blobless) de 36 dépôts (`results/repo_health.json` contient 36 entrées ; le rapport dit 35 : voir 7.1), calcul sur les 12 derniers mois depuis 2025-09-29 (`py/repo_health.py`) | Clones nus sans blobs, `--shallow-since=2025-09-29` (`py/screen.py`) ; 67 lignes dans `results/screen.json` (ClickHouse et pandas-ta sans statistiques : clone trop long / dépôt inaccessible) |
| Indicateurs de maintenance | Dernier commit, commits sur 12 mois, auteurs distincts sur 12 mois, part du premier auteur, bus factor (auteurs pour 50 % des commits) | Les mêmes + releases PyPI sur 12 mois, présence de CI, `requires_dist`, en-tête du fichier de licence |
| Fichiers de tests | Comptage par arbre git (`results/repo_tests.json`, 30+ dépôts) | Comptage par expression régulière de chemins (dans `screen.py`) |
| Étoiles GitHub | Non utilisées | Non utilisées |

**Note importante** : les indicateurs de maintenance des deux runs proviennent du même type de calcul sur les mêmes dépôts et concordent presque à l'identique (voir 8.5) ; les comptes de fichiers de tests, eux, divergent fortement (les deux expressions régulières ne sont pas les mêmes).

### 2.2 Univers d'essai et données

Tous les essais de moteurs, carnets, indicateurs, portefeuilles et qualité de données utilisent des **données synthétiques à graine fixe** (une graine = point de départ du générateur aléatoire, qui rend l'essai identique à chaque exécution). Exceptions réseau : les essais de collecte (ccxt, cryptofeed, yfinance, tardis-python, binance-public-data) touchent des serveurs réels (`results/t11_*` du run 1, `results/coll_microtest.json` du run 2) et leur résultat dépend de l'horloge et de la sortie réseau du bac à sable.

Générateurs de données principaux :
- Run 1 : `py/common.py` (600 barres journalières, `make_bars(n=600, seed=3)`, avec écart entre clôture et ouverture suivante) ; `py/dq_data.py` (200 000 barres d'une minute, graine 11, 12 variantes à un défaut chacune) ; flux de 200 000 événements de carnet pour T01 (graine 7, tick 0,5, milieu 20 000).
- Run 2 : `py/mt/common.py` (`synth(n=5000, seed=7)`, barres d'une minute) ; flux L2 écrit à la main pour le rejeu ; 3 millions de ticks, 20 symboles pour PostgreSQL (`sql/tss_microtest.sql`) ; 50 000 trades × 200 000 cotations pour les jointures « ASOF » (`py/mt/store_microtest.py`).

### 2.3 Simulateur ou protocole

Il n'y a pas de simulateur de stratégie de trading ici : le protocole est celui d'une **batterie de microtests avec oracle** :
1. On fixe une situation dont on connaît la bonne réponse (réponse calculée à la main, par formule fermée, par numpy/scipy, ou par une autre bibliothèque).
2. On lance la bibliothèque dans un environnement virtuel isolé.
3. On compare, on note l'écart, on classe.

Les tests du run 1 portent les identifiants T01 à T16 (`06_COMPONENT_TESTS.md`). Ceux du run 2 T1 à T21. La table des correspondances de sujets est en 3.0.

### 2.4 Splits tuning / validation / held-out, pré-enregistrement, gel des paramètres

**Non applicable au sens quantitatif habituel** : il n'y a aucun paramètre appris ni sélection de modèle sur données ; donc pas de découpage entraînement/validation/test « held-out » (jeu réservé, jamais regardé pendant le réglage). Points de vigilance à noter :
- **Pas de préenregistrement** (préenregistrement = fixer par écrit, avant de lancer, les critères et seuils) : aucun des deux runs n'en mentionne. Les seuils sont implicites (« égalité à 1e-9 », « 12/12 défauts détectés »), et les classes ADOPT/ADAPT/PARK/REJECT sont attribuées après coup par jugement. Le run 2 formule quatre règles d'adjudication dans `08_ADJUDICATION.md` (voir 2.5) ; le run 1 ne formule pas de règles explicites (seulement des définitions de classes).
- **Gel** : les versions de bibliothèques sont figées dans `bench/oss_trading_infra_v1/env/freeze_*.txt` (run 2 : 15 fichiers + `system.txt`) ; le run 1 n'en publie pas (il a `setup_envs.sh` qui installe « la dernière version », donc non figé). Conséquence : reproduire le run 1 plus tard peut donner d'autres versions (voir 9).
- **Graines** : toutes fixes (listées en 2.2). Le rapport 09 du run 1 insiste : « results in bench/.../results are from the final versions of the scripts ».

### 2.5 Critères de décision (seuils exacts)

**Run 1** (`reports/017_oss_trading_infra/08_ADJUDICATION.md`) : définitions de classes seulement :
- ADOPT_REFERENCE = « safe to use as library/oracle/spec with little coupling » ;
- ADAPT_CANDIDATE = « useful, needs wrapping/adaptation/data conversion or a pinned version » ;
- PARK = « revisit on trigger » ; REJECT = « not for this purpose ».
- Aucun seuil chiffré. « Drop-in » (final block) = « library-level only, no wrapper beyond `pip install`, known-answer pass, permissive licence, no service ».

**Run 2** (même fichier), quatre règles explicites :
1. ADOPT/ADAPT seulement si un microtest a reproduit le comportement central ; un candidat non exécuté ne peut pas dépasser PARK.
2. Un datastore ou serveur séparé sans lacune testée qu'il est seul à combler → PARK (doctrine).
3. Amont gelé, dépendances non déclarées ou releases cassées font descendre d'un cran mais ne provoquent pas à eux seuls un REJECT.
4. Licences copyleft/non-OSI = **drapeaux** visibles qui ne changent pas la classe, sauf non-OSI + orienté cloud (soda-core) → REJECT pour une mission « OSS seulement ».

Étiquette PROVEN : réservée (run 2) aux cas où existe un oracle indépendant (numpy/scipy, formule fermée, dérivation manuelle, égalité entre bibliothèques, dates connues). Le run 1 emploie surtout OBSERVED et n'utilise pas PROVEN dans ses tableaux.

**Seuils de test typiques** (implicites, à retenir pour la lecture) : égalité « exacte » ≤ 1e-9 à 1e-15 pour les moteurs de backtest, journée de test = « 100 % » pour les calendriers, « N/N défauts détectés » pour la qualité de données, « identique d'une exécution à l'autre » (hash identique) pour le déterminisme.

---

## 3. Résultats détaillés

### 3.0 Correspondance des expériences entre les deux runs

| Sujet | Run 1 | Run 2 |
|---|---|---|
| Carnet L2 exact | T01 (200 000 événements) | inclus dans hft/naut (pas de test de carnet aléatoire séparé) |
| Rejeu déterministe, latence, remplissage | T02, T02b, T12c (nautilus) ; T12a (hftbacktest) | `hft_microtest.py`, `naut_microtest.py` (+ probes) |
| Moteurs de backtest vs calcul manuel | T03 (6 moteurs, ordres fixes, frais et glissement) | `bt_engines.py` (5 moteurs, règle SMA 20/50, zéro frais) |
| Causalité des moteurs | T04 (invariance au préfixe + témoin qui fuit) | `leak_probe.py` (sonde d'accès au futur) |
| Causalité des indicateurs | T05 (toutes les colonnes de ta, pandas-ta, vectorbt, tsfresh) | `feat_microtest.py` (RSI/ATR/EMA seulement) |
| Statistiques en ligne | T06 river | `stats_microtest.py` (river, tdigest, ddsketch, hdrhistogram, talipp) |
| Portefeuille / métriques | T07 (6 actifs, 1 500 obs) | `port_microtest.py` (5 actifs, 1 000 jours, long seulement) |
| Calendriers | T08 | `cal_microtest.py` |
| Qualité de données | T09 (200 000 lignes, 12 défauts) | `dq_microtest.py` (3 000 lignes, 8 familles de défauts) |
| Stockage | T10 (ArcticDB, DuckDB/Parquet) | `store_microtest.py`, `sql/tss_microtest.sql`, `sql/clickhouse_local_asof.sql` |
| Collecte | T11 | `coll_microtest.py`, `misc_microtest.py`, binance-public-data |
| Simulateur agents (ABIDES) | T13 | `abides_microtest.py` |
| Format DBN | T14 (partiel) | — (databento non exécuté) |
| Almgren–Chriss | T15 | — |
| Moteur d'appariement | T16 nanobook | `orderbook_microtest.py` (dyn4mik3) |
| Modèle de coûts (impact) | T12b zipline ; T15 | `tcm_microtest.py` (cvxportfolio) |

### 3.1 Run 1 — résultats par expérience

Toutes les valeurs ci-dessous viennent des fichiers `bench/oss_trading_infra_v1/results/` de la branche du run 1 ; la marque ✔/✘ est ma vérification contre ces fichiers.

#### T01 — exactitude du carnet L2 (`results/t01_orderbook.jsonl`)

200 000 événements « fixer/supprimer un niveau de prix » (graine 7). Empreinte SHA-256 du carnet complet comparée à un dictionnaire de référence (`ref_digest 1562bcb6e7a38941`, 46 niveaux acheteurs, 38 vendeurs).

| Candidat | Empreinte identique | Événements/s (avec surcoût Python) |
|---|---|---|
| sortedcontainers (ligne de base) | oui | 1 725 926 ✔ (rapport « 1,73 M ») |
| nautilus_trader `OrderBook` L2_MBP | oui | 736 965 ✔ (« 0,74 M ») |
| hftbacktest `HashMapMarketDepthBacktest` | oui | 1 958 857 ✔ (« 1,96 M ») |

Sens en langage simple : les trois structures reconstruisent exactement le même carnet final. Les débits ne sont pas comparables entre eux (hftbacktest avale un tableau numpy déjà préparé, nautilus reçoit des objets Python un par un) ; le rapport le dit lui-même. Le rapport avoue aussi qu'un premier passage hftbacktest avait échoué à cause de la boucle de lecture du testeur, pas de la bibliothèque (`06_COMPONENT_TESTS.md`).

#### T02 / T02b — rejeu nautilus_trader (`results/t02_nautilus_run1.json`, `run2.json`, `t02b_*`)

100 000 cotations (quotes), un ordre au marché toutes les 50 cotations, deux processus distincts.
- Empreinte des exécutions **identique** `0cfe9174d9e0352c` dans les deux processus, 2 000 exécutions, commission totale 425,478672 ✔ ; 19 216 et 18 926 cotations/s ✔ (« 19 k »).
- Sémantique par défaut : 2 000/2 000 ordres exécutés **sur la même cotation** que celle où l'ordre a été soumis, au prix du meilleur côté (ask/bid) ✔ (`fills_at_submit_ts 2000`, `fill_px_equals_touch_at_submit 2000`). Traduction : par défaut, nautilus suppose une exécution instantanée au prix affiché, ce qui est optimiste.
- Avec un `LatencyModel` de 250 ms et des cotations espacées de 1 s (20 000 cotations, 399 exécutions) : délai moyen d'exécution 1 000 ms ✔, prix égal au meilleur prix à la soumission dans 4 cas sur 399 ✔ (`fill_px_equals_touch_at_submit 4`). La latence n'est donc pas active par défaut.
- Frais : « `MakerTakerFeeModel` : 0,2000 sur 2 000 de notionnel » (rapport 04). Le fichier montre une commission de 0,200081 sur un ordre de 2 000,81 ✔ (l'arrondi du rapport est acceptable).

#### T12c — nautilus parcourt un carnet L2 (`results/t12c_nautilus_bookwalk.json`)

Un ordre d'achat au marché de 3 lots exécute 1 lot à 100,50, 1 à 101,00, 1 à 101,50 ; prix moyen 101,00 ✔ (identique à l'attendu). Piège relevé : des `OrderBookDelta` isolés donnent « no market » ; enveloppés dans `OrderBookDeltas` ils fonctionnent (rapport 03 ; non observable dans le JSON, qui ne contient que le résultat final : **?**).

#### T12a — hftbacktest, position dans la file (`results/t12a_hft_queue.json`, `py/t12a_hft_queue.py`)

Situation : file d'attente de 10 lots devant nous au meilleur prix acheteur 100,0 ; on dépose un achat de 1 lot ; ventes agressives de 4 lots (t = 10 000), puis 7 (t = 20 000), puis 1 (t = 30 000). Attendu (FIFO prudent) : pas d'exécution après les 4 premiers lots, exécution une fois cumul > 10.
- Aux instants 5 000 et 12 000 : statut 1 (NEW) ; à 22 000 et 40 000 : statut 3 (FILLED), position 1, frais −0,01 ✔ pour les **quatre** modèles (risk-adverse, power-prob 2, power-prob 3, log-prob).
- Frais : `trading_value_fee_model(-0.0001, 0.0004)` ⇒ −1 point de base × 100 × 1 = −0,01 ✔ (rebate du preneur passif).
- Limite avouée : la situation ne départage pas les modèles probabilistes. Je le confirme : les quatre traces sont identiques.

#### T03 / T03z — moteurs de backtest contre le calcul manuel (`results/t03_*.json`, `py/common.py`)

Ordres fixes : ACHAT 100 titres à la décision barre 100, VENTE 100 à la barre 200 ; frais 10 points de base par côté (`FEE = 0.001`) ; glissement adverse 5 points de base (`SLIP = 0.0005`). PnL analytique : **1 793,77** (exécution à la clôture de la barre de décision), **1 802,22** (à l'ouverture de la barre suivante). Le rapport ajoute 1 796,46 pour « clôture de la barre suivante » (résultat zipline).

| Moteur | Convention d'exécution | PnL du fichier | Écart vs analytique | Vérif. |
|---|---|---|---|---|
| vectorbt (`price=Close`) | clôture même barre | 1 793,769867567793 | ≈ 1e-12 | ✔ |
| vectorbt (`price=Open`, ordres décalés +1) | ouverture suivante | 1 802,2202439016128 | ≈ 1e-12 | ✔ |
| backtrader | ouverture suivante | 1 802,2202438116074 | 9e-8 | ✔ (le rapport écrit « exact ») |
| zipline-reloaded (quotidien) | clôture suivante | 1 796,463713645935 (prix 94,034 et 112,205 ; commission 20,6239) | — | ✔ |
| backtesting.py `trade_on_close=False` | ouverture suivante | 1 807,8155 | **+5,5953** | ✔ (« +5,6 ») |
| backtesting.py `trade_on_close=True` | clôture même barre | 1 799,3622 | +5,5923 (vs 1 793,7699) | ✔ |
| bt | clôture, sans paramètre de glissement, 99 titres au lieu de 100 | 1 786,0120 (vs 1 804,0525 analytique sans glissement) | non comparable | ✔ |

Le rapport dit « ≤ 1e-9 » pour vectorbt/backtrader/zipline dans son résumé exécutif : sur backtrader l'écart réel est de 9,0e-8 en valeur absolue (≈ 5e-11 en relatif). Cela reste « exact » pour l'usage mais la borne « 1e-9 » écrite en absolu est légèrement fausse (**écart mineur**).

Explication de backtesting.py (écart +5,6) : l'entrée est exacte (93,7334), mais le prix de sortie 112,017 est l'ouverture brute ; le paramètre `spread` n'a pas été appliqué à la sortie. Le rapport 04 précise que cela peut dépendre du chemin d'ordre (`position.close()`) et que ce n'est pas prouvé pour d'autres chemins ; le rapport 06 admet aussi qu'un premier essai avait mal traduit le glissement (`spread = 2·slip`). Je ne peux pas départager « défaut de la bibliothèque » et « mauvaise configuration par le testeur » sans exécuter (**?**).

#### T04 — causalité des moteurs (`results/t04_causality.jsonl`)

Règle : moyenne mobile 10/30, frais 10 pb. L'équité calculée sur `data[:400]` doit égaler l'équité du calcul complet restreint à `[:400]`.
- vectorbt, vectorbt (MA native), backtesting.py, bt : écart max 0,0, 0 barre différente ✔. backtrader : `n=370`, écart 0,0 ✔ (le rapport ne précise pas la taille 370).
- Témoins qui fuient volontairement (signal = clôture 5 barres plus loin) : vectorbt **5** barres différentes, écart max 2 490,87 ✔ (« 2 491 ») ; bt **4** barres, écart max 609,47 ✔ (« 609 »).
- Puissance du test : le premier essai avec `shift(-1)` (fuite d'une seule barre) ne différait que sur la dernière barre, donc invisible ; d'où le témoin de 5 barres (rapport 06, point 3).

#### T05 — causalité des indicateurs (résultat phare du run 1)

Principe : la valeur d'un indicateur à la ligne t, calculée sur les 400 premières lignes, doit être égale à celle calculée sur 600 lignes (invariance au préfixe).

| Bibliothèque | Colonnes | Causales | Fuyantes | Colonnes fuyantes | Vérif. |
|---|---|---|---|---|---|
| ta 0.11.0 (`add_all_ta_features`) | 91 | 86 | **5** | `trend_kst`, `trend_kst_sig`, `trend_kst_diff`, `trend_visual_ichimoku_a`, `trend_visual_ichimoku_b` | ✔ (`results/t05_prefix_ta.json`) |
| pandas-ta 0.4.71b0 (`AllStudy`) | 271 | 262 | **9** | `DPO_20`, `ICS_26`, `TOS_STDEVALL_LR`, `_L_1`, `_U_1`, `_L_2`, `_U_2`, `_L_3`, `_U_3` | ✔ (`results/t05_prefix_pandas_ta.json`) |
| vectorbt 1.1.1 (MA, MSTD, BBANDS, RSI, STOCH, MACD, ATR, OBV) | 8 indicateurs | tous | 0 | — | ✔ |
| tsfresh 0.21.2 (fenêtres roulantes 19) | 10 | 10 | 0 | — | ✔ |

- Sens : ces colonnes changent quand on ajoute du futur. Pour `ta`, la fuite concerne le tout début de la série (lignes 0-25 pour Ichimoku, 14-43 pour KST ; ces plages viennent du rapport, non présentes dans le JSON : **?**). **Mécanisme (que j'ai vérifié dans le code source de ta 0.11.0)** : le début est rempli avec `fill_value = moyenne de toute la série` (`series.mean()`), donc une valeur qui dépend du futur. Le rapport dit à tort « back-filled with the first valid (future) value » (voir 7.1).
- Comparaison à la main du RSI(14) de Wilder : écart max 5,34e-3 (`rsi14_max_abs_diff_vs_hand_wilder`) ✔ (rapport « ≤ 5,3e-3 »).
- Durées : tsfresh 0,66 s dans le rapport vs **0,694 s** dans le fichier (✘ mineur) ; pandas-ta « ~10 s pour 600 lignes » dans le rapport vs **0,786 s** dans `seconds_full` (✘ écart réel, facteur 12 ; peut venir d'un autre passage, non traçable).

#### T06 — river, statistiques en ligne (`results/t06_river.json`)

200 000 points décalés de 1e9, σ = 0,01. Le décalage énorme est un test dur : la formule naïve Σx² s'y effondre.
- Erreur relative de la moyenne 5,0e-15 ✔ ; variance 6,9e-6 ✔ ; covariance 2,7e-6 ✔ ; formule naïve de la variance : **2,57e6** ✔ (catastrophique).
- Variance glissante (fenêtre 100) : erreur relative max 3,19e-4 vs variance exacte de la fenêtre ✔ ; **identique à celle de pandas** (`pandas_rolling_var_max_rel_err_vs_exact_window_for_comparison` = même valeur) ✔. Sens : ni river ni pandas ne sont précis quand les valeurs sont grandes devant leur dispersion (niveaux de prix, pas rendements).
- Instantané pickle (sérialisation Python) : reprise identique, 248 octets ✔ ; deux exécutions identiques ✔ ; 560 668 mises à jour/s ✔.
- Détecteurs de dérive (changement de moyenne de 1,5σ à t = 2000) : ADWIN détecte à t = 2015 (+15), 0 fausse alarme ✔ ; PageHinkley t = 2019 (+19), 1 fausse alarme ✔ ; KSWIN t = 2161 (+161), 3 fausses alarmes ✔. Un seul scénario synthétique.
- `EWMean` : écart max vs pandas `ewm(adjust=False)` 0,0376 à niveau 1e9 ✔ (rapport « 0,038 ») : transitoire d'initialisation (~4e-11 relatif selon le rapport, **?** non recalculé).

#### T07 — portefeuille et métriques (`results/t07_*.json`)

6 actifs, 1 500 observations, variance minimale sans contrainte (formule fermée sur la covariance de l'échantillon).

| Bibliothèque | Erreur max sur les poids | Vérif. | Remarque |
|---|---|---|---|
| PyPortfolioOpt 1.6.0 | 3,38e-10 | ✔ | `HRPOpt` plante : `AttributeError ... '_LINKAGE_METHODS'` avec le SciPy installé ✔ |
| riskfolio-lib 7.3.0 | 3,04e-6 | ✔ | CVaR min-risque OK ✔ |
| skfolio 1.4.9 | 7,56e-5 | ✔ | HRP OK ✔ |

Métriques : empyrical-reloaded égal au calcul manuel (Sharpe 1,0693213484575252 vs 1,0693213484575246, écart 6e-16 ✔). quantstats : VaR 0,017558 et CVaR 0,022209 (paramétriques) contre historiques 0,017926 et 0,022408 ✔ (rapport 0,01756/0,02221 vs 0,01793/0,02241). VaR = perte maximale « normale » à 95 % ; CVaR = perte moyenne au-delà.
Note : les deux fichiers `t07_metrics_core.json` et `t07_metrics_misc.json` contiennent chacun une erreur d'import (`quantstats` absent du premier, `empyrical` absent du second) ; les deux blocs utiles sont dans des fichiers différents, sans incohérence.

#### T08 — calendriers (`results/t08_calendars.json`)

Jeu de référence NYSE 2024-2025 : 21 jours fériés (10 + 11), 6 fermetures anticipées, 4 dates d'heure d'été (changement d'heure US). Les deux bibliothèques : 21/21 jours fériés retrouvés ✔, 0 fermeture en trop ✔, 6/6 fermetures anticipées ✔ (`2024-07-03`, `2024-11-29`, `2024-12-24`, `2025-07-03`, `2025-11-28`, `2025-12-24`), ouvertures UTC identiques : 14:30 le 2024-03-08 (heure d'hiver) puis 13:30 le 2024-03-11 (heure d'été) ✔. Noms de calendriers : 71 (exchange_calendars) et 211 (pandas_market_calendars) ✔ ; fenêtre par défaut 2006-09-29 → 2027-09-29 ✔.
Attention : la liste attendue a été « compilée par le testeur d'après les calendriers NYSE publiés, non re-téléchargés » (rapport 02), et **les deux bibliothèques ne sont pas indépendantes** (voir 7.1 et 8).

#### T09 — cadres de qualité de données (`results/t09_dq_*.json`, `py/dq_data.py`)

200 000 barres d'une minute (graine 11), une barre propre + 12 variantes, chacune avec un seul défaut : timestamp dupliqué, timestamps non monotones, high < low, close > high, volume négatif, close nul, changement d'unité ms → µs à partir de la ligne 150 000, 10 minutes manquantes, série plate à volume nul (60 barres), pic ×10, timestamp dans le futur (2035), barres répétées « périmées » (30 barres).

| Cadre | Barre propre passe | Défauts détectés | Durée sur 200 k lignes (rapport / fichier) | Vérif. |
|---|---|---|---|---|
| pandera 0.33.1 | oui | 12/12 | 0,11 s / 0,08 s | détection ✔ ; durée ✘ mineur |
| great_expectations 1.23.2 | oui | 12/12 | 0,23 s / 0,29 s | ✔ / ✘ mineur |
| pointblank 0.27.0 | oui | 12/12 | 1,33 s / 1,41 s | ✔ / ✘ mineur |
| frictionless 5.19.1 | oui | **5/12** (null, unicité, plages ; manqués : non monotone, high<low, close>high, minutes manquantes, série plate, pic, barre périmée) | 4,76 s / 4,51 s | ✔ / ✘ mineur |

Point clé : les colonnes dérivées (écart de temps, |rendement|, longueurs de séries plates) sont calculées **une fois hors de tous les cadres** (rapport 02). Donc le « 12/12 » mesure la capacité à exprimer des règles sur des colonnes déjà préparées, pas la détection « prête à l'emploi » de continuité temporelle.

#### T10 — stockage (`results/t10_arcticdb.json`, `t10_duckdb_parquet.json`)

1 million de lignes × 5 colonnes.
- ArcticDB 6.26.0 (LMDB) : écriture 0,105 s (rapport 0,114 ✘ mineur), lecture 0,013 s (rapport 0,014 ✘ mineur), 41,8 Mo ✔. `roundtrip_equal_strict: false`, égal en ignorant l'attribut `freq` de l'index ✔. Versionnage : 2 versions après mise à jour ; lecture `as_of=0` ou horodatage avant la correction renvoie l'original ; horodatage après renvoie la correction ✔. Points négatifs vérifiés dans le JSON : `prune_previous_versions_removes_history: true`, `delete_is_available_to_any_writer: true`, `write_has_timestamp_param: false`, LMDB « single writer (documented) ». `version_timestamp_source` est étiqueté INFERENCE dans le fichier même.
- DuckDB + Parquet : écriture 0,134 s ✔, lecture 0,223 s ✔, 34,7 Mo ✔, pas de versionnage natif.

#### T11 — collecte réseau (`results/t11_*.json`, horloge du bac à sable 2026-09-29)

- **ccxt REST** (4.5.84), `fetch_ohlcv('1m', limit=60)` : succès sur 6/8 places (Kraken, Coinbase, OKX, Bitstamp, Gate, KuCoin) ✔ ; 60 lignes, 6 colonnes, 0 doublon, pas de 60 000 ms ✔ ; **la dernière barre est toujours en cours de formation** (âge d'ouverture entre 9,7 s et 58,6 s) ✔ (rapport « 10–58 s ») ; aucun horodatage de réception (`has_receipt_ts false`) ✔. Binance : HTTP 451 ; Bybit : 403 (blocage de sortie réseau, pas un verdict sur la bibliothèque) ✔.
- **ccxt WebSocket** : Kraken 27 trades/12 s ✔, Coinbase 171 ✔, OKX délai dépassé ✔.
- **cryptofeed 2.5.0** : le rapport dit « 25 trades et 3 991 mises à jour L2, trade timestamp 4,1 ms avant la réception ». Le fichier dit **26 trades, 3 438 mises à jour de carnet, retard de 28,4 ms et 24,6 ms** sur les deux échantillons, et `stopped_by: KeyboardInterrupt` ✘ (écart réel ; probablement un autre passage que celui archivé).
- **yfinance 1.7.0** : BTC-USD 1 081 lignes ✔, SPY 5 lignes ✔.

#### T13 — ABIDES-JPM (`results/t13_abides.json`)

Python 3.9 obligatoire (numpy 1.22, pandas 1.2.4, pomegranate 0.14.5). Configuration `rmsc04`, 1 117 agents. Graine 1 deux fois : même empreinte `b3c88046989f2e9a`, 3,53 s et 3,83 s ✔ (rapport « ≈ 3,5–4 s ») ; graine 2 : empreinte différente `4278e89145dab97b` ✔. Dépôt inactif depuis 2023-12-13 (18 commits au total).

#### T14 — databento-dbn (`results/t14_dbn.json`)

Champs de `MBOMsg` observés : `ts_event`, `ts_recv`, `ts_in_delta`, `ts_out`, `sequence`, `flags` ✔. Aller-retour d'encodage/décodage non terminé : `TypeError: Metadata.__new__() got an unexpected keyword argument 'stop'` ✔ (donc PARTIEL, comme dit).

#### T15 — Almgren–Chriss via wraquant (`results/t15_almgren_chriss.json`)

(Almgren–Chriss = modèle classique de découpage d'un gros ordre pour équilibrer coût d'impact et risque de prix.) λ = 0 : calendrier linéaire exact (écart 0,0) ✔ ; λ > 0 : trajectoires égales à la formule continue en sinh (écart 0,0) ✔ ; premier lot 524,42 → 722,45 → 1 814,04 → 4 687,14 sur 10 000 pour λ = 0,001 ; 0,01 ; 0,1 ; 1 ✔. La bibliothèque n'offre aucune calibration des coefficients d'impact (rapport).

#### T16 — nanobook (`results/t16_nanobook.json`)

20 000 ordres GTC (valables jusqu'à annulation) : 15 149 transactions identiques à la référence FIFO (prix et quantités) ✔, meilleurs bid/ask 10 001 / 10 005 ✔, rejeu du journal d'événements identique ✔, 1 194 407 ordres/s ✔.

#### T12b — zipline VolumeShareSlippage (`results/t12b_zipline_volshare.json`)

Ordre de 500 titres, `volume_limit = 0,025`, `price_impact = 0,1`. Les remplissages s'étalent sur 8 barres : 106, 32, 74, 37, 68, 58, 117, 8 = 500 ✔ ; quantités identiques à l'attendu sur les 8 ✔ ; écart de prix maximal **1,42e-14** ✔ (rapport « 1,4e-14 »), à condition d'arrondir la clôture à 3 décimales (stockage des bundles par défaut). Attention : le commentaire du script dit que l'arrondi a été introduit après avoir vu un résidu de 4,5e-4 (« OBSERVED: 4.5e-4 residual disappears »), alors que le rapport 06 (point 6) dit « pas ajusté après coup » : voir 7.1.

#### Maintenance et santé des dépôts (`results/repo_health.json`, `repo_tests.json`, `footprint.json`)

- Vérifié sur `repo_health.json` : parmi les 26 projets exécutés avec historique cloné (les 27 clés exécutées moins databento), 16 ont un bus factor de 1 et 3 n'ont aucun commit en 12 mois (backtrader, empyrical-reloaded, ABIDES) ✔. Le rapport dit « 35 dépôts » mais le fichier en contient **36** (✘ mineur).
- Chiffres du tableau de `01_LANDSCAPE.md` échantillonnés : nautilus 5 529 commits/127 auteurs/85 % ✔ ; hftbacktest 24/5/63 % ✔ (0,625 → « 63 % ») ; zipline 4/1/100 % ✔ ; ta 1/1/100 % ✔.

### 3.2 Run 2 — résultats par expérience

Valeurs vérifiées dans `bench/oss_trading_infra_v1/results/` de la branche du run 2.

#### Rejeu hftbacktest 2.4.4 (`results/hft_microtest.json`, `py/mt/hft_microtest.py`)

Scénario écrit à la main : carnet acheteur 100,0 × 10, vendeur 100,5 × 10 à t = 1 s ; notre achat passif de 1 lot à 100,0 arrive à t = 5 s (10 lots devant) ; ventes agressives de 4 lots à 6 s, 6 lots à 8 s, 6 lots à 9 s ; la quantité affichée à 100,0 passe de 10 à 4 à t = 7 s.
- Modèle « risk-adverse » (prudent : la file devant nous ne diminue que par baisse de la quantité affichée puis par les transactions) : dérivation manuelle ⇒ exécution à 8,0 s. Résultat : `fill_t_s 8.0`, position 1,0, solde −100,0 ✔.
- power-prob ×2, ×3 et log-prob : tous 8,0 s ✔ (le scénario ne les départage pas, dit le rapport).
- Latence d'ordre : 0 s → exécuté à 8,0 s ✔ ; 1,5 s → position 1,0 en fin de flux **sans exécution visible** (`fill_t_s null`) ✔ ; 4 s → aucune exécution, position 0 ✔. L'explication du rapport (la latence de réponse retarde la visibilité) est étiquetée INFERENCE.
- Frais : `trading_value_fee_model(-0.0001, 0.0005)` → frais −0,01 sur une exécution maker de 100,0 ✔.
- Déterminisme : 3 exécutions identiques ✔. Débit : 2 millions d'événements en 0,184 s à chaud, **10 884 616 événements/s** ✔ (rapport « ~11 M » ; l'adjudication écrit « 10,9-11,8 M », seule la valeur 10,9 est dans le fichier : 11,8 **?**).

#### Rejeu nautilus_trader 1.221.0 (`results/naut_microtest.json`)

Même scénario en deltas L2_MBP. Six variantes L2 : trade_execution par défaut, `trade_execution` désactivé, trade à travers la limite à 99,90, `FillModel(prob_fill_on_limit=1.0)` (dans le JSON : `fill_model_prob_touch_1.0` et `_0.0`), latence 1,5 s : **aucune exécution** dans chacune (`fills: []`) ✔. Sonde de croisement de carnet (ask ajouté à 99,90 au-dessous de notre bid 100,00) : `OrderFilled + PositionOpened` ✔. Trois variantes L1 (cotations + trades) : pas d'exécution avec `trade_execution=True` ; exécution à 6,0 s avec `trade_execution=False` (le tick de trade met à jour le carnet L1 ; pas de notion de file) ✔ (texte des sondes dans le JSON). Total 9 configurations sans exécution passive pilotée par les transactions et sensible à la file : ✔ (comptage du rapport). Déterminisme : identique sur 2 exécutions ✔. Débit : 1 M cotations en 2,78 s, 359 906/s ✔ (rapport « 349–360 k » : la borne basse 349 k n'est pas dans le fichier **?**).
Observation à moi : cinq des six configurations L2 renvoient **le même hash** `c3259fa446c1` : les réglages testés n'ont pas changé la trace du tout ; cela peut vouloir dire que ces réglages ne s'appliquent pas à ce type de flux (voir 7.2).

#### ABIDES (`results/abides_microtest.json`)

Python 3.9 + numpy 1.22 + pandas 1.2.4 + pomegranate 0.14.5 + scipy 1.10. `rmsc04`, 1 117 agents, fin 09:45 : graine 1 → hash `1fd2bfa47da1` deux fois (1,8 s et 2,0 s) ✔, graine 2 → `62cfdbb2e89f` (1,6 s) ✔. Rapport « 1,6 s ».

#### Bibliothèque dyn4mik3/OrderBook (`results/orderbook_microtest.json`)

Vente de 12 lots contre A (10) puis B (2) : trades `[A 10, B 2]` ✔ ; `get_volume_at_price` lève `AttributeError` ✔ ; 121 296 ordres/s ✔ (rapport « 121–150 k » : la borne haute vient d'ailleurs **?**). Paquet PyPI 0.1.2 : import cassé (dépendance circulaire) — non retrouvé dans un fichier de résultat (affirmé dans le rapport 03 ; **?**).

#### Moteurs de backtest (`results/bt_engines.json`, `py/mt/bt_engines.py`)

Règle : long quand SMA20 > SMA50, exécution à l'ouverture de la barre suivante, frais 0, 5 000 barres d'une minute. Oracle = boucle numpy de 20 lignes : 57 transactions, équité finale **0,97741** (rendement composé par transaction).

| Moteur | Transactions | Résultat | Durée rapport / fichier | Vérif. |
|---|---|---|---|---|
| backtesting.py 0.6.6 | 57 | équité 0,977346 (Δ 6,4e-5 vs oracle) | 0,65 s / **0,4396 s** | résultat ✔ ; durée ✘ |
| backtrader 1.9.78.123 | 57 | valeur finale 997 776,116329 (mise fixe 1 000 unités) | 0,74 s / 0,7354 s | ✔ |
| vectorbt 1.1.1 | 57 | valeur finale 997 776,1163293 (Δ 7e-9 vs backtrader) | 22,2 s (1er appel) / **6,6171 s** | résultat ✔ ; durée ✘ |
| bt 1.2.3 | — | rebalance clôture-à-clôture, non comparable | 0,85 s / 0,7905 s | ✔ |
| zipline-reloaded | 271 jours | déterministe | 1,1 s / 1,09 s | ✔ (voir plus bas) |
| qstrader | non exécuté (import seul) | — | — | ✔ |

**Écart d'interprétation** : le rapport 03 écrit « Three independent implementations agree with the oracle on trade count and P&L to ≤ 6e-5 ». Or l'oracle donne un rendement composé (0,97741) tandis que backtrader et vectorbt sont comparés en valeur finale d'un portefeuille à mise fixe (997 776) ; `pnl_1000_units` de l'oracle vaut `null` dans le JSON. Donc pour backtrader et vectorbt, l'accord avec l'oracle est vérifié sur le **nombre de transactions** (57), et sur le PnL seulement **entre eux** (7e-9). Voir 7.2.

#### Sonde de lookahead (`results/leak_probe.json`, `py/mt/leak_probe.py`)

(A) Peut-on lire la barre t+1 par l'interface normale ? backtesting.py : non (`IndexError`) ✔ ; backtrader : **oui sur données préchargées** (`["IndexError","leak"]`) ✔ — l'index `close[1]` renvoie la barre suivante partout sauf sur la dernière ; vectorbt : interface par tableaux entiers, futur accessible par construction ✔.
(B) Un signal « à prescience parfaite » fourni comme tableau est-il repéré ? Non par aucun moteur : backtesting.py **+115,8 %** ✔ ; vectorbt valeur finale **1 075 087** pour 1 000 000 de départ, soit **+7,5 %** à zéro frais ✔.
Sens : aucun moteur ne détecte une fuite qui entre comme donnée ; la protection doit venir de la couche de données (jointures « as-of », horodatages de réception).

#### Modèle de coûts cvxportfolio 1.5.1 (`results/tcm_microtest.json`)

Simulation d'un pas depuis la trésorerie vers `Uniform()` sur 4 actifs, volumes constants. Spread seul (a = 0,001) : coût **1 000,0** pour 1 M (= 10 points de base du notionnel échangé) ✔, **4 000,0** pour 4 M (rapport ×4,000) ✔. Impact seul (b = 1, exposant 1,5) : 2 042,447 et 16 339,577, rapport **8,000000000000227** = 4^1,5 ✔. Déterminisme sur 2 exécutions (fichier `port_microtest.json`, `deterministic: true`) ✔. Licence GPL-3.0, un seul auteur (375 commits sur 12 mois, 100 %).

#### Zipline (`results/zl_microtest.json`)

Ingestion csvdir + algorithme quotidien déterministes (2 exécutions égales) ; `ingest_seconds 0,48`, `run_seconds 1,09`, 271 jours, valeur finale 1 007 095,556 ✔. Porte de calendrier : l'ingestion **rejette** les barres de week-end (`AssertionError: Got 30 rows ... expected 21 rows ... Extra sessions`) ✔. Constantes par défaut lues dans le code (commission 0,001 par action, `VolumeShareSlippage(0.025, 0.1)`) : citation du script ; le code source de zipline n'est pas dans la branche (**?**).

#### Statistiques en ligne (`results/stats_microtest.json`)

199 999 log-rendements : river moyenne erreur abs 8,9e-21, variance relative 8,4e-15, 0,72 µs/mise à jour ✔ ; `Rolling(Mean,100)` 5,6e-19 ✔ ; `EWMean(0.05)` vs pandas 1,1e-19 ✔ ; P² p99 estimé 9,217e-4 vs exact 9,227e-4 ⇒ erreur relative 9,8e-4 ✔ ; tdigest p99 9,247e-4 vs 9,245e-4 mais 1,29 s pour 50 000 mises à jour ✔ ; ddsketch (α = 1 %) erreur relative **0,9916 %** ✔ ≤ 1 % annoncé, fusion de deux moitiés donne la même erreur ✔ ; hdrhistogram 5,6e-6 ✔ ; talipp EMA20 vs ta max 2,38e-3 ✔ (graine de l'EMA par une moyenne simple), 7,17e-7 vs pandas après 100 barres ✔ ; RSI14 talipp vs ta 2,84e-6 ✔ ; ATR14 0,0 ✔ ; préfixe RSI de `ta` 0,0 ✔.
(Sketch = résumé compact d'une distribution permettant d'estimer des quantiles avec une erreur bornée.)

#### Indicateurs (`results/feat_microtest_*.json`)

TA-Lib 0.8.1 : cohérence de préfixe 0,0 ✔, RSI 20 000 barres 0,165–0,188 ms ✔. pandas-ta 0.4.71b0 (Python 3.12) sans TA-Lib : RSI moyen 48,787754266123784 (identique à TA-Lib), ATR 0,05013326663026827 (écart 3e-17), cohérence de préfixe 0,0 ✔ ; avec TA-Lib installé il **délègue** à TA-Lib (donc test non indépendant) ✔ (écart 0,0). **Ce test ne regarde que RSI/ATR/EMA** : il ne contredit donc pas les 9 colonnes fuyantes de pandas-ta du run 1, il ne les teste pas (voir 8).

#### Portefeuille (`results/port_microtest.json`)

5 actifs × 1 000 jours, variance minimale long seulement, oracle SLSQP sur la covariance de l'échantillon : PyPortfolioOpt écart 2,6e-9 ✔ ; Riskfolio-Lib 5,14e-7 ✔ ; skfolio 2,98e-5 ✔ ; empyrical-reloaded Sharpe Δ 1,0e-15, drawdown max Δ 0 ✔ ; quantstats Δ 0 ✔ ; cvxportfolio a tourné, valeur finale 986 900,19, rotation 0,003677 ✔.

#### Calendriers (`results/cal_microtest.json`)

NYSE 2020-01-02 à 2026-12-30 : **1 758 sessions** identiques dans les deux bibliothèques, aucune différence ✔ ; 14 fermetures anticipées 2020-2026 identiques ✔ (liste complète dans le fichier) ; 2025-01-09 (journée de deuil national), 2025-04-18 et 2026-07-03 : pas de session ✔ ; clôtures de 17:00, 18:00, 18:00 UTC pour 2024-07-03, 2024-11-29, 2024-12-24 ✔ ; clôture 21:00 UTC (2024-03-08, heure d'hiver) puis 20:00 UTC (2024-03-11) ✔. Autres calendriers : CMES 255 sessions, XLON 250, XTKS 244 (pause déjeuner), XHKG 242, IEPA 255 ✔. `requires_pmc = ["exchange-calendars>=3.3","pandas>=1.1"]` ✔ : pandas_market_calendars **dépend** d'exchange_calendars.

#### Qualité de données (`results/dq_microtest.json`)

3 000 barres d'une minute, défauts injectés : 5 high<low, 3 prix négatifs, 3 NaN, 20 barres plates à volume nul, 2 pics +30 %, 10 minutes manquantes, 4 lignes dupliquées, 1 permutation.
- pandera : 105 « cas d'échec » = unicité 8 + `>0` 3 + non-nul 3 + monotone 1 + `high_is_max` **42** + `low_is_min` **48** ✔ (somme 105). Durée 0,067 s (rapport 0,085 s ✘ mineur).
- great_expectations : unicité 8, `close>0` 3, non nul 3, `high>=low` 5, volume ≥ 0 réussi ; `ExpectColumnValuesToBeIncreasing` en échec **sans compte** (`unexpected_count null`) ✔ ; 0,113 s ✔.
- frictionless : `duplicate-row` 4, `deviated-value` 5 (3σ) ✔ ; 0,206 s ✔.
- pointblank : 3 étapes, 2/1/1 échecs (`misc_microtest.json`) ✔.
- **Ce que j'ai recalculé** : les nombres 42 et 48 semblent énormes face à 5 défauts high<low. En rejouant le même jeu de défauts (mêmes graines, script `dq_microtest.py`) avec du pandas simple, j'obtiens 7 lignes en défaut pour `high_is_max` et 8 pour `low_is_min`. Or 7 × 6 = 42 et 8 × 6 = 48 : pandera compte **une entrée par colonne (6 colonnes) et par ligne en défaut** pour une vérification qui porte sur tout le DataFrame. Donc « 105 cas » n'est pas « 105 défauts » (voir 7.2). Réserve : mon recalcul a tourné avec pandas 3.0.6 alors que le run 2 utilisait pandas 2.3.3 ; les tirages aléatoires numpy sont identiques mais je ne peux pas exclure un écart marginal.

#### Stockage (`results/tss_microtest.txt`, `store_microtest.json`, `clickhouse_local_asof.txt`)

PostgreSQL 16.15, TimescaleDB 2.30.2, pg_partman 5.0.1. 3 millions de ticks, 20 symboles :

| | table simple | partitions natives (sans extension) | hypertable TimescaleDB |
|---|---|---|---|
| Taille non compressée | 275,4 Mo | 276,5 Mo | **397,7 Mo** |
| Agrégat OHLC 1 minute, 1 symbole, 1 jour (EXPLAIN ANALYZE) | 10,091 ms | 10,179 ms | **5,624 ms** |
| Barres identiques aux partitions natives ? | — | — | oui (`bars_equal t`) |
| Après `compress_chunk` (18 chunks) | — | — | **29,4 Mo** |
| Agrégat continu | — | — | 500 001 lignes |

✔ tous ces nombres sont dans `tss_microtest.txt`. `timescaledb.license = timescale` ✔ (donc licence Timescale, pas Apache-2, pour la compression). `pg_partman create_parent(... p_premake := 4)` a créé **10** tables filles ✔. Facteurs : 397,7 / 29,4 = **13,5 ×** ✔ (par rapport à l'hypertable non compressée) ; par rapport à la table simple, 275,4 / 29,4 ≈ **9,4 ×** (mon calcul).
ASOF (jointure « à la dernière valeur connue ») 50 000 trades × 200 000 cotations dont 100 égalités exactes de timestamp : pandas, polars, DuckDB égaux en mode inclusif (≥) et strict (>) ✔ ; 0 violation d'invariant dans DuckDB ✔ ; 21 ms / 5 ms / 61 ms ✔ ; Parquet pyarrow zstd : deux écritures de hash identique ✔, 1,85 Mo ✔ ; DuckDB sur Parquet 4,6 ms ✔ ; DuckDB attaché en lecture seule à PostgreSQL : 3 000 000 lignes vues, 500 001 groupes-minute, 1,95 s ✔ ; ArcticDB lectures `as_of` version / horodatage avant la restatement renvoient l'original ✔. ClickHouse (clickhouse-local) : une ligne à gauche sans correspondance renvoie **0** (`2023-12-31 23:59:59 → 0`) en inclusif comme en strict ✔ ; « exige au moins une colonne d'égalité » : affirmé, non visible dans le fichier (**?**).
Pour polars en mode strict, le test **émule** le strict par un décalage de +1 µs des cotations (script `store_microtest.py`), il ne teste pas une option native.

#### Collecte (`results/coll_microtest.json`, `misc_microtest.json`)

ccxt 4.5.84, 104 échanges dans le registre ✔ ; `fetch_ohlcv` 100 × 1 m : Kraken, Coinbase, OKX, Bitstamp OK ✔ (0,73 à 2,36 s) ; Binance 451, Bybit 403 ✔ ; dernière barre toujours en formation ✔ ; pas d'horodatage de réception dans les trades ✔. cryptofeed 2.4.1, 20 s : Kraken 38 trades ✔, Bitstamp 24 ✔ ; premier trade Kraken : réception locale **34,6 ms avant** l'horodatage échange (1790707225,9131 vs ...,9477) ✔, premier trade Bitstamp : réception **4,84 s après** ✔ ; Coinbase : `401 Unauthorized` ✔. tardis-python : 131 910 lignes, colonnes `exchange, symbol, timestamp, local_timestamp, id, side, price, amount` ✔. yfinance : 5 lignes en 0,7 s ✔ (le 429 sur l'appel direct n'est pas dans un fichier, **?**).

#### Criblage et empreintes

- `results/screen.json` : 67 lignes ✔ ; le tableau du rapport 01 est généré par `py/gen_reports.py` à partir de ce fichier (donc cohérent) ; j'ai comparé les métriques git avec celles du run 1 : voir 8.5.
- Comptes de l'adjudication : j'ai relu le tableau de `08_ADJUDICATION.md` (67 lignes) : ADOPT_REFERENCE 14, ADAPT_CANDIDATE 10, PARK 36, REJECT 7 ✔ ; EXEC 41, INSTALL 3, NO 23 ✔ ; 5 « Y » dans la colonne second service, 8 dans second datastore ✔. Croisement : les 41 EXEC = 14 ADOPT + 10 ADAPT + 15 PARK + 2 REJECT ; les 23 NO = 18 PARK + 5 REJECT ; les 3 INSTALL = 3 PARK.
- Empreinte d'installation isolée (`results/footprint.json`, 33 entrées) : hftbacktest 735 Mo/43 distributions, nautilus_trader 574 Mo/15, ccxt 83 Mo/23, vectorbt 622 Mo/59, Riskfolio-Lib 963 Mo/85, pandera 11 Mo/10 (rapport 07 identique, généré) ✔. PyPortfolioOpt (`packaging`) et empyrical-reloaded (`pytz`) : import impossible en isolement ✔.

### 3.3 Ce que chaque groupe de chiffres signifie, en une phrase

- Les carnets d'ordres (sortedcontainers, nautilus, hftbacktest, nanobook) et les moteurs de backtest « font juste » quand on leur donne des données synthétiques propres ; le vrai risque n'est pas l'arithmétique mais les conventions (à quel prix l'ordre est exécuté) et l'entrée de données.
- Les moteurs de backtest ne repèrent pas un futur qui s'infiltre par les données (run 2), et certaines bibliothèques d'indicateurs en contiennent (run 1).
- Les petites bibliothèques pures (calendriers, river, optimiseurs de portefeuille, pandera) sont précises jusqu'aux erreurs d'arrondi.
- Les choses qui manquent dans l'open source testé : un magasin append-only PIT avec horodatage de réception côté serveur ; une estimation de coûts calibrée sur données ; des indicateurs causaux par construction ; un collecteur temps réel sans licence copyleft pour un Python récent.

---

## 4. Candidats évalués un par un (les deux runs)

Cette section couvre les **76 projets distincts** vus par au moins un run : 45 communs, 9 propres au run 1, 22 propres au run 2 (54 + 67 − 45 = 76). Les tableaux ci-dessous sont générés à partir des tableaux d'adjudication des deux rapports `08_ADJUDICATION.md` (que j'ai parsés : 32 lignes exécutées + listes des 22 non exécutés pour le run 1 ; 67 lignes pour le run 2), puis j'ai vérifié les comptes. « Licence » = licence observée par les rapports (ce n'est pas un avis juridique). « Microtest » = script du run correspondant (les T-numéros du run 1 sont dans le texte de la colonne résultat).

Rappel de lecture des verdicts : ADOPT_REFERENCE (utilisable comme bibliothèque/oracle avec peu de couplage), ADAPT_CANDIDATE (utile mais demande adaptation), PARK (en attente d'un déclencheur), REJECT (pas pour cet usage). Un « non exécuté » ne peut pas dépasser PARK dans le run 2 (règle 1) ; dans le run 1, aucune règle de ce genre n'est écrite (des projets non exécutés y sont classés REJECT ou ADOPT_REFERENCE sur documentation).

### 4.A Les 45 projets présents dans les DEUX runs

Légende : ADOPT_REF = ADOPT_REFERENCE ; ADAPT = ADAPT_CANDIDATE ; « = » verdicts identiques, « ≠ » divergents. Run 1 = PR #16 (branche oss-trading-research-infra-v1) ; Run 2 = PR #18 (branche amazing-wozniak-bwjdfp). Les colonnes « résultat » résument (texte tronqué, […]) la colonne « preuve » de `08_ADJUDICATION.md` de chaque run ; les chiffres sont ceux des rapports (leur vérification est en section 3 et 7).

| Projet | R1 | R2 | | Licence (observée) | Run 1 : test → résultat | Run 2 : test → résultat |
|---|---|---|---|---|---|---|
| abides-jpmc-public | PARK | PARK | = | BSD-3-Clause | T13 reproducible; dormant since 2023-12, py3.9 pins | [EXEC] abides_microtest.py → OBSERVED: runs only on py3.9 with 2020-era pins (numpy 1.22, pandas 1.2.4, pomegranate 0.14.5 has no cp311 wheel); rmsc04 1117 agents, seed-deterministic, seed-sensitive. No commits since 2023-12. |
| alphalens-reloaded | PARK | PARK | = | Apache-2.0 | non exécuté (statut R1 : PARK, preuve limitée aux chiffres de santé du dépôt) | non exécuté : Factor tear sheets; 0 commits/12 m. Not executed. |
| arch | PARK | PARK | = | NCSA | non exécuté (statut R1 : PARK, preuve limitée aux chiffres de santé du dépôt) | non exécuté : Volatility models; healthy; outside the gaps tested. Not executed. |
| ArcticDB | PARK | PARK | = | Business Source License 1.1 (not OSI) (R1 lit : BSL 1.1 (→Apache-2.0 after 2 y/version; no "Database Service")) | T10; BSL 1.1; second datastore; destructive prune/delete; client-side version time | [EXEC] store_microtest.py → OBSERVED: as_of version and as_of timestamp reads return pre-restatement values (native PIT); but separate store (LMDB/S3) and BSL. |
| backtesting.py | PARK | ADOPT_REF | ≠ | AGPL-3.0 (flag) | T03 +5.6 exit; AGPL; single instrument | [EXEC] bt_engines.py + leak_probe.py → PROVEN vs 20-line numpy oracle: same 57 trades, equity 0.977346 vs 0.97741; deterministic; 0.65 s; per-bar API raises IndexError on future index. Use as cross-check oracle only (AGPL, 6 test files). |
| backtrader | REJECT | PARK | ≠ | GPL-3.0+ (flag) | T03 exact, T04 causal; GPL-3.0, no commit since 2023-04 | [EXEC] bt_engines.py + leak_probe.py → OBSERVED: 57 trades, equal to vectorbt/oracle; direct data.close[+1] returns a future bar on preloaded data (leak) except on last bar; last release 2023-04, 0 commits/12 m. |
| binance-public-data | ADOPT_REF | ADOPT_REF | = | no LICENSE file at HEAD (UNKNOWN) | non exécuté (statut R1 : ADOPT_REFERENCE, preuve limitée aux chiffres de santé du dépôt) | [EXEC] script du dépôt lancé dans /tmp (pas de script versionné) → OBSERVED: downloaded BTCUSDT-1m-2025-03 + .CHECKSUM (sha256 matches, verified by us; script only downloads it, never verifies), 44 640 rows, 16-digit (µs) open_time. Use as layout/reference; code reuse blocked by missing licence. |
| bt | PARK | PARK | = | MIT | T04 causal; no slippage; sizing reserve | [EXEC] bt_engines.py → OBSERVED: runs deterministically but rebalances close-to-close, no next-open fill; result not comparable to oracle; 6 test files. |
| ccxt | ADAPT | ADAPT | = | MIT | T11 6/8 venues; drop forming bar; add receipt stamp; CA handling; per-venue quirks (005) | [EXEC] coll_microtest.py → OBSERVED: fetch_ohlcv 100x1m OK on kraken/coinbase/okx/bitstamp (60 s step); binance 451 & bybit 403 = egress. All returned the forming bar; trades carry no receipt stamp. Needs wrapper for receipt time, forming-bar drop, unit normalisation. |
| ClickHouse | PARK | PARK | = | Apache-2.0 | non exécuté (statut R1 : PARK, preuve limitée aux chiffres de santé du dépôt) | [EXEC] sql/clickhouse_local_asof.sql → OBSERVED clickhouse-local 26.10: ASOF JOIN semantics correct (inclusive/strict) but needs >=1 equality key and an unmatched row returns 0, not NULL (join_use_nulls off) — silent missing-evidence-as-zero hazard; 866 MB binary. […] |
| cryptofeed | ADAPT | ADAPT | = | AGPL-3.0-or-later (flag) (R1 lit : 2.5.0: XFree86-1.1 (permissive); 3.0.1: AGPL-3.0+, py≥3.13) | T11; 3.x is AGPL + py3.13; BF 1 | [EXEC] coll_microtest.py → OBSERVED: 20 s live WS: Kraken 38 trades, Bitstamp 24, each callback gets a local `receipt` stamp next to exchange ts. Coinbase symbol discovery 401 (auth now required). Needs event-loop workaround on py3.11+uvloop. 39 commits/12 m, top author 74 %. |
| databento-python | PARK | PARK | = | Apache-2.0 | T14 partial; roundtrip unproven; paid client | non exécuté : Client is OSS, data is paid + key required; not executed (no key). |
| DuckDB | ADOPT_REF | ADOPT_REF | = | MIT | T10; MIT; no versioning; `ASOF JOIN` PIT hazard (004) | [EXEC] store_microtest.py → PROVEN: ASOF join (inclusive and strict) equals pandas.merge_asof and polars.join_asof on 50 k x 200 k rows incl. exact-tie rows; 0 look-ahead violations; queries Parquet in place; read-only ATTACH of the live PG16 (3 M rows) worked. […] |
| empyrical-reloaded | PARK | ADOPT_REF | ≠ | Apache-2.0 | T07 exact; 0 commits in 12 m | [EXEC] port_microtest.py → PROVEN: Sharpe/max-DD equal numpy to 1e-15; undeclared dep `pytz` (isolated import failed); 0 commits/12 m (stable). |
| exchange_calendars | ADOPT_REF | ADOPT_REF | = | Apache-2.0 | T08 100 %; Apache; 62 commits/12 m, 14 authors; rolling ±1 y default window | [EXEC] cal_microtest.py → PROVEN vs known dates: 1758 NYSE sessions 2020-2026 identical to pandas_market_calendars; 14 early closes identical; 2025-01-09 (Carter day) and 2026-07-03 closed; DST closes 21:00Z (EST) / 20:00Z (EDT); 71 calendars; 0.18 s load; 14 authors. |
| freqtrade | REJECT | PARK | ≠ | GPL-3.0 (flag) | non exécuté (statut R1 : REJECT, preuve limitée aux chiffres de santé du dépôt) | non exécuté : DOCUMENTED_CLAIM/INFERENCE: a live-capable bot application with its own sqlite; extracting the data downloader means adopting a runtime with order authority. Not executed. |
| frictionless-py | PARK | PARK | = | MIT | T09 5/12; no sequence/cross-column checks | [EXEC] dq_microtest.py → OBSERVED: duplicate-row (4) and deviated-value (5) found on CSV; safe-path rule requires relative paths; resource-oriented, not time-series aware. |
| great_expectations | PARK | PARK | = | Apache-2.0 | T09 12/12; 35 dists/302 MB; equal detection to lighter tools | [EXEC] dq_microtest.py → OBSERVED: caught dup (8 rows), non-positive (3), null (3), high<low (5); ordering check returned no count; no native gap check; 267 MB / 35 dists; […] |
| hftbacktest | ADAPT | ADAPT | = | MIT | T01, T12a; event-array conversion; last commit 2025-12; 1 Python test file; BF 1 | [EXEC] hft_microtest.py → PROVEN vs hand derivation (risk-adverse queue: fill at 8.0 s); the three probabilistic queue models gave the same 8.0 s in this single scenario (not discriminating); […] |
| hummingbot | REJECT | PARK | ≠ | Apache-2.0 | non exécuté (statut R1 : REJECT, preuve limitée aux chiffres de santé du dépôt) | non exécuté : INFERENCE: live market-making bot + Docker/Gateway runtime (README); order authority is the product. Not executed. |
| LEAN | PARK | PARK | = | Apache-2.0 | non exécuté (statut R1 : PARK, preuve limitée aux chiffres de santé du dépôt) | non exécuté : C#/.NET engine; healthy (441 commits, 35 authors) but a whole second runtime. Not executed. |
| nautilus_trader | ADOPT_REF | ADAPT | ≠ | LGPL-3.0-or-later (flag) (R1 lit : LGPL-3.0+) | T01, T02, T12c; LGPL, 870 MB, top author 85 %, live adapters in wheel; component reuse would be ADAPT | [EXEC] naut_microtest.py (+ probes) → OBSERVED: L2 delta replay OK, deterministic (identical event hash x2), 349-360 k quotes/s, fills when simulated book crosses. A print-driven passive fill with queue position was NOT reproduced in 9 configs (UNKNOWN whether supported). […] |
| pandas-ta | REJECT | REJECT | = | unknown (repo gone) | T05 9/271 leaky incl. full-sample regression; beta; licence metadata empty; upstream repo not resolved | [EXEC] feat_microtest.py → OBSERVED: GitHub repo twopirllc/pandas-ta not reachable (git asks credentials); only pre-release 0.4.71b0 on PyPI needing py>=3.12; when run without TA-Lib it matches TA-Lib means to 1e-16. Provenance risk. |
| pandas_market_calendars | ADOPT_REF | PARK | ≠ | MIT | T08 100 %; 211 calendars; MIT; cross-check against exchange_calendars | [EXEC] cal_microtest.py → OBSERVED: identical NYSE results but it depends on exchange-calendars (requires exchange-calendars>=3.3): redundant layer; 211 calendar names. |
| pandera | ADAPT | ADAPT | = | MIT | T09 12/12, 0.11 s; rules (monotonic, OHLC relations, gaps) must be authored | [EXEC] dq_microtest.py → OBSERVED: lazy validation returned a failure-case table (105 rows) covering uniqueness, positivity, nullability, monotonicity, cross-column OHLC; 11 MB; 56 authors; gap detection needs a custom check. |
| pointblank (python) | PARK | PARK | = | MIT | T09 12/12; 1.33 s/200 k rows; 92 % single author; project < 2 y | [EXEC] misc_microtest.py → OBSERVED: 3 steps reported 2/1/1 failures on a 10-row polars frame; young port (0.27.0), 92 % one author. |
| polars | PARK | ADOPT_REF | ≠ | MIT | non exécuté (statut R1 : PARK, preuve limitée aux chiffres de santé du dépôt) | [EXEC] store_microtest.py → PROVEN: join_asof equals pandas/duckdb on the tie-laden test; fastest of three (5 ms vs 21/61 ms). |
| pyfolio-reloaded | PARK | PARK | = | Apache-2.0 | non exécuté (statut R1 : PARK, preuve limitée aux chiffres de santé du dépôt) | non exécuté : Tear-sheet plotting; 0 commits/12 m. Not executed. |
| PyPortfolioOpt | ADOPT_REF | ADOPT_REF | = | MIT | T07 3e-10; HRP broken on current SciPy | [EXEC] port_microtest.py → PROVEN: long-only min-variance weights equal SLSQP oracle to 2.6e-9; deterministic; undeclared dep `packaging` (import failed in isolated venv). |
| pysystemtrade | PARK | PARK | = | GPL-3.0 (flag) | non exécuté (statut R1 : PARK, preuve limitée aux chiffres de santé du dépôt) | non exécuté : IB-centred futures system (README); 15 authors, active. Not executed. |
| qlib | PARK | PARK | = | MIT | non exécuté (statut R1 : PARK, preuve limitée aux chiffres de santé du dépôt) | non exécuté : ML research platform; 27 commits/12 m; last release 2025-08. Not executed. |
| quantstats | PARK | PARK | = | Apache-2.0 | T07; parametric VaR default; 96 % single author | [EXEC] port_microtest.py → OBSERVED: Sharpe/max-DD identical to numpy (<=1e-15); report/plot oriented (349 MB env); one author 95 %. |
| QuestDB | PARK | PARK | = | Apache-2.0 | non exécuté (statut R1 : PARK, preuve limitée aux chiffres de santé du dépôt) | non exécuté : Separate server + datastore (violates one-authoritative-store doctrine); release download blocked (403) so not executed. |
| Riskfolio-Lib | PARK | ADOPT_REF | ≠ | BSD-3-Clause | T07 3e-6; 1 test file; 88 % single author | [EXEC] port_microtest.py → PROVEN: weights match oracle to 5e-7; deterministic; heavy (85 dists, 963 MB); 4 authors, top 88 %. |
| river | ADOPT_REF | ADOPT_REF | = | BSD-3-Clause | T06; state picklable; BSD; rolling var precision = pandas; API drift (`EWMean`, `Rolling`) | [EXEC] stats_microtest.py → PROVEN: online mean/var equal numpy (mean 9e-21, var rel 8e-15), Rolling(Mean,100) 5.6e-19, EWMean 1e-19; P2 p99 rel err 9.8e-4; deterministic; 0.72 us/update; 299 commits/12 m. |
| skfolio | ADAPT | ADAPT | = | BSD-3-Clause | T07, sklearn API, 25 authors; 7.6e-5 solver tolerance | [EXEC] port_microtest.py → PROVEN: weights match oracle to 3e-5 (looser solver tol); deterministic; strongest maintenance in class (52 releases/12 m, 25 authors, top 31 %). sklearn-style API needs adapter. |
| sortedcontainers | ADOPT_REF | PARK | ≠ | Apache-2.0 | T01 baseline; no releases since 2021 (stable) | [INSTALL] import seul → Used transitively (nautilus, orderbook); no commits since 2024-03, last release 2021; not independently tested. |
| ta | PARK | PARK | = | MIT | T05 5/91 leaky warm-up; 1 commit/12 m; usable only with allow-list | [EXEC] stats_microtest.py / feat_microtest.py → OBSERVED: EMA identical to pandas ewm(adjust=False); RSI/ATR equal to talipp; last release 2023-11, 1 commit/12 m. |
| TA-Lib (python) | PARK | ADOPT_REF | ≠ | BSD-2-Clause | non exécuté (statut R1 : PARK, preuve limitée aux chiffres de santé du dépôt) | [EXEC] feat_microtest.py → OBSERVED: wheel installs in 1 s, causal (prefix-consistency maxabs 0.0), RSI 20 k bars 0.17-0.19 ms; used as parity oracle for ta/pandas-ta (0.0 on RSI). |
| TimescaleDB | PARK | ADAPT | ≠ | Apache-2.0 core + Timescale License features (flag) | non exécuté (statut R1 : PARK, preuve limitée aux chiffres de santé du dépôt) | [EXEC] sql/tss_microtest.sql → OBSERVED on PG16 (2.30.2): hypertable bars byte-equal to native partitioning; 1-min OHLC query 5.6 ms vs 10.1/10.2 ms plain/native; compression 397.7->29.4 MB (13.5x) and continuous aggregate ran with `timescaledb.license=timescale`. […] |
| tsfresh | PARK | PARK | = | MIT | T05 causal; slow; 6 commits/12 m | non exécuté : Batch feature extraction; 6 commits/12 m. Not executed. |
| vectorbt | ADOPT_REF | PARK | ≠ | Apache-2.0 + Commons Clause (not OSI) | T03 exact, T04 causal; Commons Clause; fills at caller-chosen price only | [EXEC] bt_engines.py + leak_probe.py → OBSERVED: SMA20/50 = 57 trades, final value equal to backtrader to 1e-8; 22 s first call (numba JIT), 8 s import; whole-array API exposes future by construction (foresight signal earns +7.5 % at zero fees when handed in as an array). |
| vnpy | PARK | PARK | = | MIT | non exécuté (statut R1 : PARK, preuve limitée aux chiffres de santé du dépôt) | non exécuté : 5 authors, 4 test files; trading-platform oriented. Not executed. |
| yfinance | PARK | PARK | = | Apache-2.0 | T11; unofficial endpoint (report 005) | [EXEC] misc_microtest.py → OBSERVED: 5 daily AAPL rows in 0.7 s; direct curl to the Yahoo chart endpoint returned 429. Unofficial scraper of a consumer site (ToS/stability risk, INFERENCE). |
| zipline-reloaded | PARK | PARK | = | Apache-2.0 | T03z, T12b exact; 4 commits/12 m, 1 author; tz break; 3-dp prices; ingest store | [EXEC] zl_microtest.py → OBSERVED: csvdir ingest + daily algo runs, deterministic; ingest strictly rejects non-session (weekend) bars (calendar gate). Own bundle store, equity/daily orientation; 4 commits/12 m by one author. |

Nombre de verdicts divergents parmi les 45 : **13**. Détail en section 8.

### 4.B Les 9 projets présents UNIQUEMENT dans le run 1

| Projet | Verdict R1 | Licence | Test → résultat (run 1) |
|---|---|---|---|
| dukascopy-node | PARK | non indiqué | non exécuté. Node.js ; téléchargeur ; 23 commits/12 mois, 57 fichiers de tests (`repo_health.json`, `repo_tests.json`) |
| fastquant | REJECT | non indiqué | non exécuté. aucune release depuis 2023-01 (rapport 08, écrit de mémoire) |
| Feast | PARK | non indiqué | non exécuté. magasin de features (rapport 004 externe à cette lane) |
| MACE | PARK | non indiqué | non exécuté. environnements Gymnasium de modèles de coûts, trouvé par recherche web |
| mlfinlab | REJECT | non indiqué | non exécuté. distribution propriétaire (INFERENCE de mémoire) |
| original Quantopian zipline | REJECT | non indiqué | non exécuté. archivé (INFERENCE de mémoire) |
| rqalpha | PARK | non indiqué | non exécuté. moteur orienté marché chinois ; 133 commits/12 mois, 62 fichiers de tests |
| nanobook | PARK | MIT | [EXEC] t16_nanobook.py → T16 exact; young, bundled broker code |
| wraquant | REJECT | MIT | [EXEC] t15_almgren_chriss.py → T15 formula only; py≥3.13, undeclared dep, no calibration, 4 releases |

### 4.C Les 22 projets présents UNIQUEMENT dans le run 2

| Projet | Verdict R2 | Licence (observée) | Test → résultat (run 2) |
|---|---|---|---|
| abides-gym-markets | REJECT | BSD-3-Clause (GT) | non exécuté : Last commit 2020-11; superseded by jpmc fork. Not executed. |
| Apache Arrow (pyarrow) | ADOPT_REF | Apache-2.0 | [EXEC] store_microtest.py → OBSERVED: two Parquet writes of the same frame are byte-identical (sha256); 1.85 MB for 200 k quotes. |
| cvxportfolio | ADAPT | GPL-3.0 (flag) | [EXEC] tcm_microtest.py + port_microtest.py → PROVEN: simulator cost = exactly 10 bps of traded notional for a=0.001 (1000.0 of 1e6), and 4x size -> x4.000 (spread) / x8.000 (impact, exponent 1.5); deterministic. Bus factor 1: one author = 100 % of 375 commits/12 m. Last release 2025-07. |
| findatapy | PARK | Apache-2.0 | non exécuté : 11 commits/12 m, one author. Not executed. |
| hdrhistogram (hdrh) | ADOPT_REF | Apache-2.0 | [EXEC] stats_microtest.py → PROVEN: p99 rel err 5.6e-6 with 3 significant digits; 5 MB; 6 commits/12 m. |
| InfluxDB | PARK | Apache-2.0 (LICENSE-APACHE seen) | non exécuté : Separate server/datastore; not executed. |
| openbb | PARK | Apache-2.0 | non exécuté : Aggregator platform (135 commits/12 m, 73 % one author). Not executed; overlaps with source-level clients. |
| orderbook (dyn4mik3) | REJECT | MIT | [EXEC] orderbook_microtest.py → OBSERVED: PyPI 0.1.2 (2013) fails at import (circular import); GitHub HEAD matches FIFO ground truth but get_volume_at_price raises AttributeError; ~121-150 k orders/s; matching engine only (no feed ingestion/queue tracking/latency/clock). |
| pandas-datareader | PARK | BSD-3-Clause | non exécuté : Thin per-source wrappers, 2 releases/12 m, 86 % one author. Not executed. |
| pg_partman | ADOPT_REF | PostgreSQL License | [EXEC] sql/tss_microtest.sql → OBSERVED: create_parent(p_premake=4) created 10 child tables; packaged in Ubuntu noble; 20 commits/12 m. Native declarative partitioning did the same query with no extension. |
| pydantic | PARK | MIT | non exécuté : Row-level model validation; not executed as a DQ component. |
| python-holidays | PARK | MIT | [INSTALL] import seul → Imported (version check) only; 83 authors, 690 commits/12 m. Not tested. |
| qstrader | PARK | MIT | [INSTALL] bt_engines.py (import seul) → Installed/imported only; no commits since 2024-06; daily-bar oriented (DOCUMENTED_CLAIM). |
| sketches-py (ddsketch) | ADOPT_REF | Apache-2.0 | [EXEC] stats_microtest.py → PROVEN: relative error 0.99 % <= claimed 1 %; merge of two sketches gives same p99 error; 1 MB; last release 2024-04. |
| soda-core | REJECT | Elastic License 2.0 (not OSI) | non exécuté : LICENSE file at HEAD is ELv2; PyPI license field says Proprietary. |
| talipp | ADAPT | MIT | [EXEC] stats_microtest.py → PROVEN vs batch: RSI14 maxabs 2.8e-6, ATR14 0.0 vs `ta`; EMA seeds with SMA (2.4e-3 early, 7e-7 vs pandas ewm after 100 bars) — must be documented in any parity contract; 1 MB, pure python; last release 2025-09. |
| tardis-python | ADAPT | MPL-2.0 | [EXEC] misc_microtest.py → OBSERVED: keyless first-day-of-month sample works: Deribit BTC-PERPETUAL trades 2025-03-01 = 131 910 rows, columns include `timestamp` AND `local_timestamp` (receipt side). Anything beyond free sample is commercial data (DOCUMENTED_CLAIM). […] |
| tcapy | REJECT | Apache-2.0 (per LICENCE file) | non exécuté : README: needs Redis + Celery + Memcached + MongoDB/Arctic/KDB/InfluxDB + MySQL/Postgres; last commit 2022-05. |
| tdigest | PARK | MIT | [EXEC] stats_microtest.py → OBSERVED: p99 on 50 k = 9.247e-4 vs exact 9.245e-4 but 1.29 s for 50 k updates (pure python); last release 2019, last commit 2022. |
| tstables | REJECT | none found | non exécuté : Last commit 2015-10; no licence file. |
| VictoriaMetrics | PARK | Apache-2.0 | non exécuté : Separate metrics server/datastore; not executed. |
| whylogs | REJECT | Apache-2.0 | non exécuté : 0 commits in 12 m, last commit 2025-01-10, last release 2024-12. |

### 4.D Comptes et vérification des tableaux

| | Run 1 | Run 2 |
|---|---|---|
| ADOPT_REFERENCE | 8 exécutés + 1 non exécuté (binance-public-data) = **9** ✔ | **14** (tous exécutés) ✔ |
| ADAPT_CANDIDATE | **5** : hftbacktest, pandera, skfolio, ccxt, cryptofeed ✔ | **10** ✔ |
| PARK | 16 exécutés + 16 non exécutés = **32** ✔ | **36** (15 EXEC + 3 INSTALL + 18 NO) ✔ |
| REJECT | 3 exécutés (backtrader, pandas-ta, wraquant) + 5 non exécutés (hummingbot, freqtrade, fastquant, mlfinlab, Quantopian zipline) = **8** ✔ | **7** (2 EXEC + 5 NO) ✔ |

Les comptes du run 1 sont recalculés depuis le tableau des 32 exécutés et depuis la liste textuelle des 22 non exécutés (1 + 5 + 16 = 22 ✔).

### 4.E Conditions de changement de verdict (celles écrites par les rapports, complétées par mon analyse)

Les rapports ne donnent pas de « déclencheur » chiffré pour chaque PARK, sauf la définition « revisit on trigger ». Voici ce qui, d'après leurs propres arguments, ferait bouger les verdicts les plus importants (marqué INFERENCE quand c'est ma déduction) :

| Projet | Verdict actuel | Ce qui le ferait changer |
|---|---|---|
| nautilus_trader | R1 ADOPT_REF, R2 ADAPT | R2 : si une configuration supportée reproduit un remplissage passif piloté par les trades avec position dans la file (UNKNOWN aujourd'hui) ; dépend aussi de la version (1.231.0 en R1, 1.221.0 en R2, 2.0.0rc5 disponible). Licence LGPL et surface « autorité d'exécution » (adaptateurs live dans le paquet) : constantes. |
| hftbacktest | ADAPT (les deux) | Un test qui départage les modèles de file probabilistes ; des tests Python (1 seul fichier de tests visible) ; reprise d'activité (dernier commit 2025-12-23) ; conversion des flux au format `event_dtype` (INFERENCE : c'est le coût d'adaptation). |
| backtesting.py | R1 PARK, R2 ADOPT_REF | R1 : correction de l'écart de 5,6 sur la sortie avec spread, ou preuve que c'était la configuration du testeur ; R2 : test avec frais non nuls. Licence AGPL : reste un drapeau. |
| vectorbt | R1 ADOPT_REF, R2 PARK | Commons Clause (non OSI) ; interface par tableaux qui expose le futur par construction (R2). |
| pandas_market_calendars | R1 ADOPT_REF, R2 PARK | R2 : redondant car dépend d'exchange_calendars ; R1 le traite comme une seconde opinion indépendante, ce que ses propres métadonnées (2 dépendances dures dont exchange_calendars) contredisent. |
| ta | PARK (les deux) | R1 : usable seulement avec liste blanche par test d'invariance de préfixe ; 1 commit sur 12 mois. |
| pandas-ta | REJECT (les deux) | Provenance (dépôt amont introuvable, seulement une pré-version 0.4.71b0 PyPI, licence vide) ; R1 ajoute 9/271 colonnes fuyantes. Un dépôt amont retrouvé ferait revoir. |
| cryptofeed | ADAPT (les deux) | 3.x est AGPL et exige Python ≥ 3.13 (R1) ; Coinbase demande désormais des identifiants (R2). Le contournement de boucle d'événements en Python 3.11 + uvloop est requis (R2). |
| ccxt | ADAPT (les deux) | Wrapper à écrire : retirer la barre en formation, ajouter l'horodatage de réception, normaliser les unités. |
| ArcticDB | PARK (les deux) | BSL 1.1 ; second datastore ; suppression/purge possible par tout écrivain. Un besoin explicite de versionnage PIT côté bibliothèque le ferait revoir. |
| cvxportfolio (R2 seul) | ADAPT | GPL-3.0 et un seul auteur ; après clarification de licence et de maintenance, ou en réutilisant seulement la forme fonctionnelle du coût. |
| TimescaleDB (R2) | ADAPT | Licence Timescale pour la compression et les agrégats continus ; redémarrage du serveur (`shared_preload_libraries`) ; disponibilité en base gérée UNKNOWN. |
| backtrader | R1 REJECT, R2 PARK | GPL-3.0 et plus aucun commit depuis 2023-04-19 ; R2 relève de plus que `data.close[1]` renvoie le futur sur données préchargées. |
| hummingbot, freqtrade | R1 REJECT, R2 PARK | Frameworks d'autorité d'exécution (ordres réels) ; les deux runs les classent sans les avoir exécutés. |

---

## 5. Bloc final complet et explication ligne par ligne

### 5.1 Run 1 (`reports/017_oss_trading_infra/00_EXECUTIVE_SUMMARY.md`, reproduit tel quel)

```
PROJECTS_DISCOVERED=54
PROJECTS_EXECUTED=32   (31 with a completed microtest, 1 partial: databento-dbn)

ADOPT_REFERENCE_COUNT=9
ADAPT_CANDIDATE_COUNT=5
PARK_COUNT=32
REJECT_COUNT=8

SECOND_SERVICE_REQUIRED_CANDIDATES=5   (QuestDB, ClickHouse, Feast, hummingbot, freqtrade; none executed)
SECOND_DATASTORE_REQUIRED_CANDIDATES=7 (ArcticDB, zipline bundle, QuestDB, ClickHouse, Feast, freqtrade, hummingbot; DuckDB only if persisted)

ANY_DROP_IN_COMPONENT=YES (library level only: exchange_calendars, pandas_market_calendars; AurumShift fit UNKNOWN by boundary)

FINAL_VERDICT=MULTIPLE_OSS_COMPONENTS_SUPPORTED
```

### 5.2 Run 2 (`reports/017_oss_trading_infra/00_EXECUTIVE_SUMMARY.md` et `bench/oss_trading_infra_v1/results/final_block_counts.txt`, reproduit tel quel)

```
PROJECTS_DISCOVERED=67
PROJECTS_EXECUTED=41 (behavioural microtest run); 3 install/import only; 23 screened from metadata only

ADOPT_REFERENCE_COUNT=14
ADAPT_CANDIDATE_COUNT=10
PARK_COUNT=36
REJECT_COUNT=7

SECOND_SERVICE_REQUIRED_CANDIDATES=5 (tcapy, QuestDB, ClickHouse, VictoriaMetrics, InfluxDB)
SECOND_DATASTORE_REQUIRED_CANDIDATES=8 (zipline-reloaded, tcapy, QuestDB, ClickHouse, ArcticDB, VictoriaMetrics, InfluxDB, tstables)

ANY_DROP_IN_COMPONENT=YES (narrow, capability-level: exchange_calendars, river, hdrhistogram/ddsketch, TA-Lib, pyarrow, DuckDB/polars as compute-only — pure libraries, no service, permissive licence, verified by microtest; fit against the real AurumShift code is deliberately not asserted)

FINAL_VERDICT=MULTIPLE_OSS_COMPONENTS_SUPPORTED
```
(Le fichier `final_block_counts.txt` du run 2 contient exactement ces lignes, sans le titre.)

### 5.3 Explication de chaque clé

| Clé | Sens simple | Vérifié ? |
|---|---|---|
| `PROJECTS_DISCOVERED` | Nombre de projets open source recensés dans l'étude, exécutés ou non. R1 : 54, R2 : 67. | R1 : 32 + 22 = 54 ✔ (deux listes du rapport 01) ; R2 : 67 lignes de `screen.json` ✔ |
| `PROJECTS_EXECUTED` | Nombre de projets réellement lancés dans un essai. R1 : 32, dont 31 essais complets et 1 partiel (databento-dbn, aller-retour non terminé) ; R2 : 41 essais comportementaux, 3 installés/importés sans essai, 23 sur métadonnées. Noter que R1 compte parmi les « exécutés » `sortedcontainers` (référence) alors que R2 le classe en « import seul ». | ✔ |
| `ADOPT_REFERENCE_COUNT` | Nombre de projets jugés utilisables tels quels comme bibliothèque, oracle ou spécification, peu couplés. | ✔ (4.D) |
| `ADAPT_CANDIDATE_COUNT` | Nombre de projets utiles mais qui demandent un adaptateur, une conversion de données ou une version figée. | ✔ |
| `PARK_COUNT` | Nombre de projets mis en attente d'un déclencheur (bloqués, non prouvés ou hors lacune testée). | ✔ |
| `REJECT_COUNT` | Nombre de projets écartés (cassés, abandonnés, non ouverts, contraires à la doctrine ou hors sujet). | ✔ |
| `SECOND_SERVICE_REQUIRED_CANDIDATES` | Projets qui exigeraient de faire tourner un **serveur/service supplémentaire** en plus du processus hôte et de PostgreSQL existant. Les deux comptes valent 5 mais les ensembles diffèrent (R1 : QuestDB, ClickHouse, Feast, hummingbot, freqtrade ; R2 : tcapy, QuestDB, ClickHouse, VictoriaMetrics, InfluxDB). Aucun n'est exécuté comme serveur dans R1 ; R2 exécute ClickHouse seulement en `clickhouse-local`. | R2 ✔ (colonne « 2nd service » = 5 « Y ») ; R1 ? (liste dans le rapport 08, non recomptable depuis un tableau) |
| `SECOND_DATASTORE_REQUIRED_CANDIDATES` | Projets qui auraient besoin de leur **propre stockage persistant** pour servir. R1 : 7 ; R2 : 8. Différences : R2 compte tcapy, VictoriaMetrics, InfluxDB, tstables (absents du run 1) ; R1 compte Feast, freqtrade, hummingbot. | R2 ✔ (8 « Y ») ; R1 ? |
| `ANY_DROP_IN_COMPONENT` | Existe-t-il au moins une pièce qu'on peut brancher sans envelopper : bibliothèque pure, sans service, licence permissive, comportement vérifié. Les deux disent OUI en précisant que l'adéquation à AurumShift n'est pas affirmée. La liste du R2 est plus large (6 éléments) que celle du R1 (2). | Non vérifiable au-delà des tests ; « permissive » repose sur les métadonnées de licence |
| `FINAL_VERDICT` | Verdict de synthèse : `MULTIPLE_OSS_COMPONENTS_SUPPORTED` = plusieurs composants sont soutenus par des tests ; ce n'est ni « une plateforme complète » ni « rien n'existe ». Le titre du commit R1 dit « LIMITED→MULTIPLE », c'est-à-dire que le verdict a été relevé en cours de route (commit `bb1371a`), sans que le rapport n'explique le critère de passage. | — |

---

## 6. Contrôles de validité

### 6.1 Tests de fuite / lookahead

| Contrôle | Run 1 | Run 2 |
|---|---|---|
| Invariance au préfixe des **moteurs** (l'équité sur les 400 premières barres = celle du calcul complet restreint) | T04 : 5 moteurs à écart 0,0 ✔ ; **témoins positifs** qui fuient détectés (vectorbt 5 barres, bt 4 barres) ✔ | Non fait |
| Invariance au préfixe des **indicateurs** (toutes les colonnes) | T05 : ta 5/91, pandas-ta 9/271 fuyantes, vectorbt 0/8, tsfresh 0/10 ✔ | Seulement RSI/ATR/EMA : 0,0 pour ta, TA-Lib, pandas-ta ✔ |
| Sonde d'accès au futur via l'interface du moteur | Non | `leak_probe.py` : backtrader préchargé expose `close[1]` ✔ ; tableaux de prescience acceptés par tous ✔ |
| Jointure « as-of » sans lookahead | Signalée comme risque (`ASOF JOIN ignores known_at unless pre-filtered`, `t10_duckdb_parquet.json`) | Invariant vérifié dans DuckDB : 0 violation, inclusif et strict ✔ |
| Puissance du test | Reconnue : un `shift(-1)` ne différait que sur la dernière barre, remplacé par un témoin à 5 barres | Non applicable (pas de témoin) |
| Réception vs événement (PIT) | cryptofeed reçoit un horodatage de réception ; ccxt n'en donne pas ✔ | idem + tardis-python `local_timestamp` ✔ ; R2 note que la réception peut être **avant** l'horodatage de l'échange (-34,6 ms) ou 4,84 s après |

### 6.2 Déterminisme

- R1 : nautilus (2 processus, empreinte identique) ✔ ; hftbacktest « exact » (T01/T12a) ; river (2 exécutions et pickle) ✔ ; ABIDES même graine ⇒ même empreinte ✔ ; optimiseurs de portefeuille (2 exécutions) ✔.
- R2 : hftbacktest 3 exécutions ✔ ; nautilus 2 exécutions ✔ ; ABIDES ✔ ; pyarrow octets identiques ✔ ; cvxportfolio 2 exécutions ✔ ; zipline 2 exécutions ✔.
- Limite (R2, `09_LIMITATIONS.md`) : contrôlé sur 2-3 exécutions, un seul processus/conteneur, jamais sur d'autres machines ou architectures. R1 a au moins un test inter-processus (nautilus T02).

### 6.3 Contrôles négatifs et positifs

- Positifs (la bibliothèque doit avoir raison) : tous les tests à réponse connue.
- Négatifs (le test doit savoir échouer) : R1 a des témoins qui fuient (T04) et un cadre de qualité de données qui échoue sur 12 défauts injectés (T09, dont frictionless 5/12 qui montre que le test peut échouer) ; R2 a la formule naïve de variance (river) comme contre-exemple et l'injection de défauts (dq).
- Absents : ni run ne teste la sensibilité du test en réduisant volontairement une bibliothèque saine (ex. casser exprès un calendrier) ; ni run ne teste le rejeu sur des données réelles de carnet (L2/L3).

### 6.4 Erreurs corrigées en cours de route (déclarées par les rapports)

Run 1 (`06_COMPONENT_TESTS.md`, six points) : (1) T01 hftbacktest, boucle de lecture du testeur fautive ; (2) T03 backtesting.py avait `spread = 2·slip`, bt rebalançait chaque jour ; (3) T04 `shift(-1)` quasi invisible ; (4) T06 la comparaison de variance glissante utilisait pandas comme référence ⇒ remplacée par la variance exacte de la fenêtre ; (5) T09 frictionless, chemin non sûr ⇒ `basepath` ; (6) T12b prix attendu sans arrondi 3 décimales.
Run 2 (`06_COMPONENT_TESTS.md`, « Pitfalls encountered »), cinq points : backtrader sans stratégie enregistrée (0 trade) ; sonde d'index futur de backtesting.py mal formée (index positif = passé absolu) ; comparaison EMA talipp/ta depuis la première barre (l'écart est une convention réelle) ; pandas-ta avec TA-Lib installé non indépendant (il délègue) ; frictionless chemin absolu. À ajouter : première installation de `hdrh` échouée (paquet appelé `hdrhistogram` sur PyPI, `env/stats_install_first_attempt.log`).

### 6.5 Écarts au protocole déclarés

- R1 : découverte non exhaustive (GitHub search bloqué) ; pandas-ta et duckdb sans historique git ; 22 projets non exécutés classés sur preuve limitée ; licences de hummingbot, mlfinlab, zipline original « de mémoire (INFERENCE) ».
- R2 : ClickHouse sans statistiques git (clone trop long) ; TimescaleDB testé seulement en build licence Timescale ; QuestDB non exécuté (téléchargement 403) ; ABIDES et cryptofeed avec contournements d'environnement ; Python différent selon les candidats (3.9/3.11/3.12).
- Communs : pas de préenregistrement, pas de held-out (voir 2.4).

---

## 7. Critique indépendante

### 7.1 Run 1

1. **Le mécanisme de la fuite de `ta` est mal décrit (j'ai vérifié dans le code source).** Le rapport 05 dit que la zone de démarrage est « back-filled with the first valid (future) value ». Dans `ta` 0.11.0 (`ta/trend.py`, que j'ai téléchargé sous forme d'archive source PyPI pour ce contrôle), les décalages utilisent `fill_value = série.mean()` (par exemple `spana.shift(self._window2, fill_value=spana.mean())` lignes 414 et 432 pour Ichimoku « visual », et `self._close.shift(self._r1, fill_value=self._close.mean())` lignes 500-535 pour KST). Donc c'est la **moyenne de toute la série** qui remplit le début, pas « la première valeur valide ». Le constat (fuite du futur dans les lignes de démarrage) et les colonnes sont confirmés, la fenêtre de lignes (0-25 pour Ichimoku, 14-43 pour KST) est cohérente avec ce mécanisme (26 pour la fenêtre `window2` d'Ichimoku ; KST : décalages 10 à 30 plus fenêtres jusqu'à 15), mais le rapport 05 doit être corrigé sur ce point. Portée : elle touche quelques dizaines de lignes de démarrage, celles qu'un praticien écarte en général, ce qui tempère le mot « silently » sans le supprimer (un jeu de features naïf les garde).
2. **pandas-ta : « 9/271 » = en partie des indicateurs conçus pour regarder le futur.** `DPO_20` (« detrended price oscillator » centré), `ICS_26` (chikou de l'Ichimoku, décalé vers l'arrière par définition) et les sept `TOS_STDEVALL_*` (bandes de régression sur tout l'échantillon) sont des indicateurs dont la définition utilise le futur ou la totalité de l'échantillon. Je n'ai pas lu le code de pandas-ta (dépôt amont introuvable) : c'est une INFERENCE de ma part. L'exécutif du R1 écrit « Indicator libraries leak silently » ; pour pandas-ta il serait plus juste de dire « exposent des indicateurs non causaux sans avertissement ».
3. **Écarts rapport / résultat brut relevés (voir 7.5 pour la table)** : cryptofeed (25 trades / 3 991 mises à jour / 4,1 ms dans le rapport ; 26 / 3 438 / 28,4 et 24,6 ms dans le JSON archivé, arrêt par `KeyboardInterrupt`) ; durée pandas-ta (~10 s vs 0,786 s) ; durées T09 et T10 ; « 35 dépôts » vs 36 clés. Ces écarts n'affectent pas les verdicts, mais ils montrent que certains chiffres du rapport viennent d'un passage antérieur et que le dossier `results/` n'est pas exactement le passage cité.
4. **Oracles écrits par le testeur, avec un risque d'ajustement.** L'attendu de T12b (zipline) inclut un arrondi à 3 décimales ajouté après avoir constaté un résidu de 4,5e-4 (commentaire du script : « OBSERVED: 4.5e-4 residual disappears »), alors que le rapport 06 point 6 affirme que les deux corrections sont « derived from source and data, not fitted afterwards ». Les deux textes ne se concilient pas complètement. Le fait que le résidu disparaisse à 1,4e-14 est un bon signe, mais l'hypothèse a été choisie en regardant l'écart.
5. **Le point backtesting.py (+5,6).** Le rapport reconnaît lui-même une première mauvaise traduction du glissement (`spread = 2·slip`). L'écart restant peut venir de la manière de passer le spread ou de fermer une position ; il est étiqueté « pas prouvé pour d'autres chemins ». Sur cette base, classer backtesting.py PARK est prudent ; mais en attribuant le défaut à la bibliothèque sans confirmer avec un second chemin, on risque un faux négatif.
6. **« Order books and replay are solved by OSS, and verified » (exécutif, point 1) est trop fort** : 200 000 événements synthétiques, une configuration, pas de vraies données L2/L3, un scénario de file qui ne départage pas les modèles probabilistes (dit dans le même rapport). « Vérifié sur données synthétiques et cas connus » serait exact.
7. **Indépendance des deux calendriers surestimée.** Le rapport 02 dit « the two libraries are independent implementations and agree ». Les métadonnées montrent que pandas_market_calendars dépend d'exchange_calendars (dépendances dures : 2 dans `footprint.json` du run 1 `hard_requires: 2` ; `requires_pmc = ["exchange-calendars>=3.3","pandas>=1.1"]` dans `cal_microtest.json` du run 2). L'accord n'est donc pas deux avis indépendants pour la NYSE. Conséquence sur la classe : pmc est ADOPT_REFERENCE dans R1 alors qu'il est en partie une couche redondante.
8. **Les tests de qualité de données sont favorables aux cadres riches.** Les colonnes dérivées sont préparées hors des cadres ; plusieurs défauts déclenchent plusieurs règles (le rapport l'admet) ; pointblank/GX/pandera obtiennent 12/12 parce qu'on leur donne des règles qui correspondent aux défauts connus d'avance. frictionless est configuré sans règles de séquence. Le classement est donc surtout un test de « peut-on exprimer la règle », pas de recall sur défauts inconnus.
9. **Seuils de maintenance** : « bus factor 1 » pour 16 projets sur 26 vient d'un proxy (50 % des commits) qui, avec des fusions « squash » (regroupement de commits), des robots ou un historique vendu, se déforme (dit dans 09). Le mot « REJECT » pour backtrader repose sur « GPL-3.0 + aucun commit depuis 2023-04 » alors qu'il a passé tous les tests : c'est un choix de doctrine, pas de mesure.
10. **Verdicts sur projets non exécutés.** hummingbot, freqtrade, fastquant, mlfinlab, zipline original sont classés REJECT alors qu'aucun n'a été lancé ; le rapport avoue que la licence de certains vient « de mémoire ». Le run 2 applique la règle plus prudente « non exécuté ⇒ PARK au plus ». Les deux approches sont défendables, mais elles produisent des chiffres non comparables (8 REJECT vs 7).
11. **Comptes de tests (fichiers) à manier avec précaution** : riskfolio-lib « 1 fichier de tests (4 %) » dans R1 (`repo_tests.json`) contre 357 dans R2 (`screen.json`). Le R1 s'appuie sur cette valeur pour la mention « 1 test file » à côté de riskfolio dans sa table d'adjudication (colonne watch-outs). Les deux expressions régulières ne mesurent pas la même chose ; aucun des deux runs ne prouve que la suite de tests de riskfolio soit faible ou forte.

### 7.2 Run 2

1. **Les « preuves » de l'adjudication sont écrites en dur** (`py/adjudication.py`, dictionnaire `A`) et copiées dans le rapport par `gen_reports.py`. Certains chiffres proviennent donc d'un passage antérieur aux résultats archivés : backtesting.py « 0,65 s » (fichier : 0,4396 s), vectorbt « 22 s first call » (fichier : 6,6171 s), hftbacktest « 10,9-11,8 M events/s » (fichier : 10,88 M), nautilus « 349-360 k » (fichier : 359,9 k), pandera 0,085 s (fichier : 0,067 s). Aucun ne change un verdict, mais le principe « tout chiffre vient d'un fichier de `results/` » n'est pas respecté à la lettre.
2. **« PROVEN » employé pour des oracles écrits par le testeur avec une connaissance du modèle** : la dérivation « risk-adverse ⇒ exécution à 8,0 s » applique la règle propre au modèle testé ; l'égalité 10 pb / ×4 / ×8 de cvxportfolio compare la bibliothèque à sa propre forme fonctionnelle documentée. Ce sont de bonnes vérifications de cohérence, pas des preuves indépendantes de réalisme. Le run 1 est plus prudent (OBSERVED presque partout).
3. **« Three independent implementations agree with the oracle … P&L to ≤ 6e-5 » (rapport 03) est trop fort.** L'oracle donne un rendement composé (0,97741) ; `pnl_1000_units: null` dans `bt_engines.json`. Seul backtesting.py est comparé en équité (Δ 6,4e-5). backtrader et vectorbt le sont en nombre de transactions (57) et **entre eux** (Δ 7e-9), pas au PnL de l'oracle. La conclusion « le calcul arithmétique des moteurs n'est pas le risque » reste plausible mais n'est démontrée que pour un moteur sur les trois.
4. **Nautilus : cinq configurations sur six donnent la même empreinte** (`c3259fa446c1`). Si `trade_execution`, la limite traversée et `FillModel` n'ont eu aucun effet sur la trace, il est possible que ces réglages ne s'appliquent pas à ce type de flux ou que le flux de trades n'ait pas été consommé comme prévu ; le rapport dit lui-même « my setup may be incomplete » (UNKNOWN). Un nom de paramètre diffère entre le JSON (`prob_touch`) et le rapport (`prob_fill_on_limit`). De plus, la version testée (1.221.0, Python 3.11) est plus ancienne que celle du run 1 (1.231.0). Le verdict ADAPT « passive fill UNKNOWN » est honnête ; il ne dit pas que nautilus ne sait pas le faire.
5. **pandera « 105 cas d'échec » est un artefact de comptage** : 42 = 7 lignes × 6 colonnes et 48 = 8 × 6 (mon recalcul, voir 3.2). Le rapport explique les 42+48 par « rows touched by the injected negative/spike values » ; la cause de fond est que pandera consigne une entrée par colonne pour une vérification de DataFrame. La comparaison des cadres n'est pas non plus à armes égales : GX reçoit 6 attentes, frictionless 2 vérifications, pointblank 3 étapes, pandera 8 règles.
6. **TimescaleDB « 1,8 × plus rapide » et « 13,5 × »** : (a) un seul `EXPLAIN ANALYZE` par disposition, sans répétition ni température de cache déclarée ; (b) les requêtes ne sont pas identiques : les plans montrent `date_trunc` + tri sur `(minute, ts)` pour les tables simple/native et `time_bucket` + tri sur le seul bucket pour l'hypertable, et l'hypertable exclut les chunks ; (c) le facteur 13,5 est calculé contre l'hypertable non compressée (397,7 Mo), qui est **44 % plus grosse** que la table simple (275,4 Mo) ; contre la table simple le gain est ≈ 9,4 ×. Les données sont des ticks synthétiques, la compressibilité réelle est UNKNOWN. (d) Licence Timescale pour ces deux fonctions (dit dans le rapport).
7. **Cryptofeed : horloge.** L'échantillon d'un seul premier trade par place ne permet pas d'établir un décalage typique (−34,6 ms pour Kraken, +4,84 s pour Bitstamp). La cause est étiquetée UNKNOWN par le rapport.
8. **Latence d'ordre dans hftbacktest à 4 s** : l'ordre arrive à 9,0 s, exactement à l'instant du dernier trade (6 lots à 9 s) alors que la file devant nous est de 4 lots ; « pas d'exécution » dépend donc de la règle de départage à égalité d'horodatage, non discutée. Le résultat n'est pas faux mais il est fragile au bord.
9. **Absence de test de fuite sur les indicateurs complets.** Le run 2 valide ta et pandas-ta seulement sur RSI/ATR/EMA et conclut que la couche d'indicateurs est « causal in the tested cases » : c'est exact, mais le run 1 montre que le test complet aurait trouvé 14 colonnes fuyantes. Le classement de `ta` (PARK) et `pandas-ta` (REJECT) reste le même, mais TA-Lib est promu ADOPT_REFERENCE sur ce test partiel.
10. **backtesting.py ADOPT_REFERENCE sans frais.** Le test tourne à zéro commission et sans spread (`commission=0`). Le run 1, avec frais et glissement, a vu un écart de 5,6 sur la sortie. Le run 2 ne peut donc pas voir ce que le run 1 a vu ; les deux verdicts ne sont pas contradictoires sur les faits, ils testent des choses différentes.
11. **Catalogue « de mémoire » (INFERENCE)** : 67 noms choisis avant contrôle ; l'absence de projet n'est pas une preuve d'absence (dit dans 09). Les projets trouvés uniquement par R1 (nanobook, wraquant, MACE, Feast, rqalpha, dukascopy-node, fastquant, mlfinlab, zipline original) montrent que chaque catalogue manque des noms de l'autre.
12. **Tests de tiers non exécutés cités comme preuves** : « README (DOCUMENTED_CLAIM) » pour tcapy ; « 22 s » de numba ; « ClickHouse exige au moins une colonne d'égalité » (non visible dans le fichier brut). Ce sont des lectures de documentation, correctement étiquetées.

### 7.3 Points faibles communs aux deux runs

- **Données 100 % synthétiques** pour tout ce qui est moteur, carnet, indicateur, portefeuille, qualité de données : cela prouve l'arithmétique et les conventions, pas le comportement sur marchés réels (rapports 09).
- **Une configuration par test** ; un seul scénario de file d'attente ; un seul jeu de défauts ; un seul scénario de dérive (river).
- **Pas de préenregistrement, pas de barre de succès chiffrée** avant les essais ; les classes sont attribuées par jugement.
- **Choix en bord de grille** : tous les seuils sont implicites ; les cas limites signalés : `≥ / >` en jointure as-of (R2 le teste), égalité d'horodatage entre ordre et trade (R2, hftbacktest), arrondi 3 décimales du prix (R1, zipline), fenêtre par défaut ±1 an d'exchange_calendars (2006-09-29 → 2027-09-29).
- **Hypothèses fragiles** : « bus factor » par commits ; « test files » par regex ; « empreinte » d'un environnement partagé (R1) ou isolé (R2) ; licence lue dans des métadonnées.
- **Ce que les chiffres ne prouvent PAS** : que ces composants fonctionnent sur des données réelles de marché ; qu'ils passent l'audit de sécurité/chaîne d'approvisionnement (non fait) ; qu'ils sont compatibles avec AurumShift (non évalué par construction) ; que des projets non catalogués ne seraient pas meilleurs ; que les licences copyleft sont un obstacle (non interprété) ; que les temps mesurés valent hors de ce bac à sable partagé.

### 7.4 Contradictions internes relevées

- R1 : « les deux bibliothèques [de calendrier] sont des implémentations indépendantes » (02) vs dépendance d'une sur l'autre (métadonnées, footprint R1 lui-même : 2 dépendances dures).
- R1 : rapport 06 point 6 (« pas ajusté après coup ») vs commentaire du script T12b (résidu observé, puis arrondi).
- R2 : le résumé exécutif dit que les calendriers sont « identiques à pandas_market_calendars » (bonne nouvelle) alors que 02/08/09 disent que ce n'est pas un second avis ; les deux affirmations coexistent sans réconciliation dans le résumé.
- R2 : `hftbacktest` « PROVEN » (adjudication) alors que le rapport 04 écrit « PROVEN for the risk-adverse queue on one scenario » : la portée est correcte dans 04, plus forte dans le tableau 08.
- R2 : 03 déclare trois moteurs en accord avec l'oracle ; 06 (T1) dit « 3 of 3 comparable engines agree (57 trades; P&L ≤ 6e-5) » — même surdéclaration.

### 7.5 Vérifications de chiffres (≥ 10 demandés) : tableau récapitulatif

| # | Run | Chiffre du rapport | Fichier brut | Résultat |
|---|---|---|---|---|
| 1 | R1 | ta 5/91, pandas-ta 9/271 colonnes fuyantes | `results/t05_prefix_ta.json`, `t05_prefix_pandas_ta.json` | ✔ |
| 2 | R1 | PnL 1 793,77 / 1 802,22 / 1 796,46 ; backtesting.py +5,6 | `results/t03_*.json` | ✔ |
| 3 | R1 | 200 000 événements, débits 1,73 M / 1,96 M / 0,74 M, empreintes égales | `results/t01_orderbook.jsonl` | ✔ |
| 4 | R1 | nautilus empreinte `0cfe9174d9e0352c`, 2 000 exécutions, commission 425,478672 | `results/t02_nautilus_run1.json`, `run2.json` | ✔ |
| 5 | R1 | river : 5e-15 / 6,9e-6 / 2,7e-6 / 2,6e6 / 3,2e-4 / 0,038 / +15, +19, +161 | `results/t06_river.json` | ✔ |
| 6 | R1 | erreurs poids 3,4e-10 / 3,0e-6 / 7,6e-5 ; VaR quantstats 0,01756 vs 0,01793 | `results/t07_*.json` | ✔ |
| 7 | R1 | 21/21 fériés, 6/6 fermetures anticipées, 71 et 211 calendriers | `results/t08_calendars.json` | ✔ |
| 8 | R1 | DQ 12/12, 12/12, 12/12, 5/12 | `results/t09_dq_*.json` | ✔ détection ; ✘ mineur sur les durées |
| 9 | R1 | zipline 8 remplissages, 1,4e-14 | `results/t12b_zipline_volshare.json` | ✔ (1,42e-14) |
| 10 | R1 | cryptofeed 25 trades, 3 991 mises à jour, 4,1 ms | `results/t11_cryptofeed.json` (26 ; 3 438 ; 28,4/24,6 ms) | ✘ |
| 11 | R1 | pandas-ta AllStudy « ~10 s » | `results/t05_prefix_pandas_ta.json` (`seconds_full 0.786`) | ✘ |
| 12 | R1 | 26 projets, 16 bus factor 1, 3 sans commit ; « 35 dépôts » | `results/repo_health.json` (36 entrées) | ✔ pour 26/16/3 (databento exclu) ; ✘ mineur 35 vs 36 |
| 13 | R1 | Almgren–Chriss 524 → 4 687 | `results/t15_almgren_chriss.json` | ✔ |
| 14 | R1 | ArcticDB écriture 0,114 s, lecture 0,014 s, 41,8 Mo | `results/t10_arcticdb.json` (0,105 ; 0,013 ; 41,8) | ✔ Mo ; ✘ mineur secondes |
| 15 | R2 | 67 candidats, 14/10/36/7, EXEC 41/INSTALL 3/NO 23, 5 services, 8 datastores | `reports/.../08_ADJUDICATION.md` parsé ; `screen.json` (67) | ✔ |
| 16 | R2 | hftbacktest 8,0 s, latence 1,5 s / 4 s, frais −0,01, ~11 M ev/s | `results/hft_microtest.json` (10,88 M) | ✔ |
| 17 | R2 | cvxportfolio 1 000 / 4 000 / ×8,000 | `results/tcm_microtest.json` | ✔ |
| 18 | R2 | river 8,9e-21 / 8,4e-15 / 5,6e-19 / 1,1e-19 ; ddsketch 0,99 % | `results/stats_microtest.json` | ✔ |
| 19 | R2 | 1 758 sessions, 14 fermetures anticipées | `results/cal_microtest.json` | ✔ |
| 20 | R2 | TimescaleDB 397,7 → 29,4 Mo (13,5 ×) ; 5,62 vs 10,09/10,18 ms ; 10 tables pg_partman | `results/tss_microtest.txt` | ✔ |
| 21 | R2 | pandera 105 cas (42+48…) | `results/dq_microtest.json` ; recalcul pandas 7 et 8 lignes × 6 colonnes | ✔ nombre ; interprétation ✘ dans le rapport (artefact de comptage) |
| 22 | R2 | 5 moteurs, 57 transactions, oracle 0,97741 ; durées 0,65 s / 22,2 s | `results/bt_engines.json` (0,4396 s ; 6,6171 s) | ✔ résultats ; ✘ durées ; ✘ portée de « agree with oracle P&L » |
| 23 | R2 | leak_probe +115,8 % ; +7,5 % | `results/leak_probe.json` | ✔ |
| 24 | R2 | cryptofeed Kraken 38, Bitstamp 24, −34 ms / +4,8 s | `results/coll_microtest.json` | ✔ |
| 25 | R2 | métriques git (commits, auteurs, part) | `results/screen.json` vs run 1 `repo_health.json` | ✔ (identiques à ±1 % près pour la plupart, voir 8.5) |
| 26 | R2 | nautilus « 349–360 k quotes/s » | `results/naut_microtest.json` (359 906) | ✔ borne haute ; ? borne basse |
| 27 | R1 | ta : mécanisme « back-filled with first valid value » | code source de `ta` 0.11.0 | ✘ (c'est la moyenne de la série) |

Bilan : 27 contrôles ; ✘ net sur 5 lignes (n°10, 11, 21 pour l'interprétation, 22 pour les durées et la portée, 27 pour le mécanisme) ; ✔ avec un ✘ mineur de détail (durées, 35 vs 36) sur les lignes 8, 12 et 14 ; ? sur les bornes basse/haute non retrouvées (ligne 26, et 11,8 M ev/s de la ligne 16) ; le reste est ✔ sans réserve.

---

## 8. Comparaison point par point des deux runs (section obligatoire)

Les deux runs ont été lancés le même jour (2026-09-29) sur la même mission, avec les mêmes contraintes, depuis le même commit de base `1a449df`. Ils n'ont pas de dépendance l'un envers l'autre (la PR #18 mentionne d'ailleurs qu'elle a découvert après coup l'existence de la branche du run 1 et n'y a pas touché). C'est donc une réplication partielle : mêmes questions, catalogues et batteries de tests différents.

### 8.1 Chiffres d'ensemble côte à côte

| Question | Run 1 (PR #16) | Run 2 (PR #18) | Accord ? |
|---|---|---|---|
| Projets découverts | 54 | 67 | 45 en commun (83 % du R1, 67 % du R2) |
| Projets propres à un run | 9 | 22 | — |
| Projets exécutés | 32 (31 complets + 1 partiel) | 41 (+3 import seul) | — |
| Verdict final | `MULTIPLE_OSS_COMPONENTS_SUPPORTED` | idem | oui |
| ADOPT_REFERENCE / ADAPT / PARK / REJECT | 9 / 5 / 32 / 8 | 14 / 10 / 36 / 7 | ordres de grandeur proches, ADOPT/ADAPT plus nombreux dans R2 (règle « exécuté ») |
| Second service | 5 | 5 | même compte, ensembles différents |
| Second datastore | 7 | 8 | proche |
| Drop-in | 2 (calendriers) | 6 (calendriers, river, hdrhistogram/ddsketch, TA-Lib, pyarrow, DuckDB/polars en calcul) | oui, périmètre différent |
| Environnement de test | 12 venvs partagés par groupes ; 3 Pythons | venv isolé par candidat pour l'empreinte ; PostgreSQL 16 réel | — |
| Versions figées publiées | non | oui (`env/freeze_*.txt`) | — |

### 8.2 Projets présents dans un run et pas dans l'autre

**Uniquement dans le run 1 (9)** : dukascopy-node (PARK, non exécuté), Feast (PARK), MACE (PARK), fastquant (REJECT), mlfinlab (REJECT), zipline Quantopian d'origine (REJECT), rqalpha (PARK), et deux exécutés : **nanobook** (PARK ; appariement FIFO exact sur 20 000 ordres, 1,19 M ordres/s, `results/t16_nanobook.json`) et **wraquant** (REJECT ; Almgren–Chriss = formule de 10 lignes, Python ≥ 3.13, dépendance `polars` non déclarée, `results/t15_almgren_chriss.json`).

**Uniquement dans le run 2 (22)** : abides-gym-markets (REJECT), pyarrow (ADOPT_REF), cvxportfolio (ADAPT), findatapy (PARK), hdrhistogram (ADOPT_REF), InfluxDB (PARK), openbb (PARK), orderbook dyn4mik3 (REJECT ; import PyPI cassé), pandas-datareader (PARK), pg_partman (ADOPT_REF), pydantic (PARK), python-holidays (PARK, import seul), qstrader (PARK, import seul), ddsketch (ADOPT_REF), soda-core (REJECT ; licence Elastic 2.0), talipp (ADAPT), tardis-python (ADAPT), tcapy (REJECT), tdigest (PARK), tstables (REJECT), VictoriaMetrics (PARK), whylogs (REJECT).

**Ce que cela change** :
- Le run 2 couvre des lacunes que le run 1 laisse ouvertes : un **modèle de coûts intégré** vérifié (cvxportfolio : ×4 et ×8), un **stockage dans PostgreSQL** réel (TimescaleDB et partitionnement natif comparés), des **jointures as-of** vérifiées (DuckDB/polars/pandas) avec invariant, des **quantiles en flux** (ddsketch/hdrhistogram), des **indicateurs en flux** (talipp), un **téléchargement en vrac** avec somme de contrôle (binance-public-data), un échantillon de **données de carnet avec horodatage de réception** (tardis-python).
- Le run 1 couvre ce que le run 2 ne regarde pas : **fuite dans toutes les colonnes** d'indicateurs (ta, pandas-ta), **causalité de chaque moteur avec témoin positif**, **conventions de remplissage avec frais et glissement** sur 6 moteurs, **glissement par part de volume** (zipline), **découpage d'ordre Almgren–Chriss**, moteur d'appariement nanobook, format DBN, détecteurs de dérive de river, mesure du précis des variances avec grand décalage.
- Chaque catalogue manque des noms de l'autre : la « découverte » n'est pas exhaustive (les deux le disent) et l'union des deux (76 projets) est plus proche d'une couverture raisonnable que chacun séparément.

### 8.3 Verdicts divergents parmi les 45 projets communs (13)

| Projet | Run 1 | Run 2 | Cause probable (fait, sinon INFERENCE) |
|---|---|---|---|
| backtesting.py | PARK | ADOPT_REFERENCE | R1 : essai avec frais 10 pb et glissement 5 pb, écart +5,6 sur la sortie ; R2 : essai à zéro frais contre oracle numpy à l'ouverture suivante, aucun écart de coût visible ; les deux gardent le drapeau AGPL. Ils ne testent pas la même chose. |
| backtrader | REJECT | PARK | R1 : GPL-3.0 et plus aucun commit depuis 2023-04 ⇒ REJECT malgré tests exacts et causalité OK ; R2 : règle « gelé ≠ cassé, licence = drapeau » ⇒ PARK. Choix de doctrine différent, mêmes faits. |
| empyrical-reloaded | PARK | ADOPT_REFERENCE | R1 : 0 commit sur 12 mois ⇒ PARK ; R2 : Sharpe/drawdown exacts à 1e-15 ⇒ ADOPT alors que l'import isolé échoue (dépendance `pytz` non déclarée). Le R2 n'applique pas ici sa propre règle 3 (« dépendances non déclarées font descendre d'un cran »). |
| freqtrade | REJECT | PARK | R1 : application de bot avec autorité d'exécution + GPL-3.0 ⇒ REJECT sans exécution ; R2 : non exécuté ⇒ PARK au plus (règle 1). |
| hummingbot | REJECT | PARK | Idem (bot de market-making ; licence Apache-2.0 selon R2). |
| nautilus_trader | ADOPT_REFERENCE | ADAPT_CANDIDATE | R1 (v1.231.0) : ordres au marché, parcours de carnet L2, déterminisme inter-processus ; R2 (v1.221.0) : l'ordre passif limité n'est pas exécuté par les trades dans 9 configurations (UNKNOWN). Test de fonctions différentes + versions différentes. |
| pandas_market_calendars | ADOPT_REFERENCE | PARK | R2 lit la dépendance à exchange_calendars et la juge redondante ; R1 la traite comme un deuxième avis indépendant. |
| polars | PARK | ADOPT_REFERENCE | R1 : non exécuté dans cette lane (« used in report 004 ») ; R2 : jointure as-of égale à pandas/DuckDB, la plus rapide (5 ms). |
| Riskfolio-Lib | PARK | ADOPT_REFERENCE | R1 : 88 % d'un seul auteur et « 1 test file » ; R2 : écart à l'oracle 5,1e-7 et jugé oracle croisé ; R2 note lui aussi 88 % d'un auteur mais ne s'en sert pas. |
| sortedcontainers | ADOPT_REFERENCE | PARK | R1 : exécuté comme base de référence dans T01 ; R2 : import seul. |
| TA-Lib | PARK | ADOPT_REFERENCE | R1 : non exécuté (bibliothèque C) ; R2 : exécuté, causal (préfixe 0,0), oracle de parité pour ta/pandas-ta. |
| TimescaleDB | PARK | ADAPT_CANDIDATE | R1 : renvoi au rapport 004 externe, non exécuté ici ; R2 : instance PostgreSQL 16 réelle, barres égales, compression 13,5 ×. |
| vectorbt | ADOPT_REFERENCE | PARK | R1 : exact et causal comme oracle indépendant ; R2 : interface tableau qui expose le futur, JIT numba lourd, Commons Clause (les deux voient la licence). |

Structure : sur les 13 divergences, **8 viennent d'une différence de périmètre d'exécution** (exécuté dans un run, non exécuté ou testé autrement dans l'autre : polars, TA-Lib, TimescaleDB, sortedcontainers, freqtrade, hummingbot, nautilus, backtesting.py), **3 d'une règle de doctrine** (backtrader, empyrical, Riskfolio) et **2 d'un fait d'architecture relu différemment** (pandas_market_calendars, vectorbt). Aucune divergence ne vient d'un désaccord sur un résultat chiffré mesuré sur le même test.

### 8.4 Constats absents d'un run (dont ta / pandas-ta)

| Constat | Run 1 | Run 2 |
|---|---|---|
| **ta : 5 colonnes sur 91 fuient le futur** (KST ×3, Ichimoku a/b visuels) | oui, mesuré (`results/t05_prefix_ta.json`), mécanisme confirmé par la source de `ta` (voir 7.1) | non testé : seul RSI/EMA/ATR vérifiés (0,0) |
| **pandas-ta : 9 colonnes sur 271** (DPO_20, ICS_26, 7 × TOS_STDEVALL) | oui, mesuré (`results/t05_prefix_pandas_ta.json`) | non testé : RSI/ATR seulement (0,0) |
| Colonnes vectorbt (8) et tsfresh (10) sans fuite | oui | non testé |
| Écart de 5,6 de backtesting.py sur la sortie avec frais/spread | oui | non testé (zéro frais) |
| Aucun moteur ne détecte un tableau « de prescience » ; backtrader préchargé expose `close[1]` | non | oui (`results/leak_probe.json`) |
| Défauts d'environnement : PyPortfolioOpt (`packaging`) et empyrical (`pytz`) sans dépendance déclarée | non (venv partagé) | oui (`results/footprint.json`) |
| PyPortfolioOpt `HRPOpt` plante avec SciPy actuel | oui | non testé |
| zipline-reloaded + exchange_calendars 4.13.2 : erreur avec dates tz-aware | oui (rapport 07) | non relevé (R2 ne mentionne pas de dates tz-aware) |
| Quantstats VaR/CVaR paramétriques par défaut | oui | non testé |
| ClickHouse ASOF renvoie 0 au lieu de NULL | non (non exécuté) | oui (`clickhouse_local_asof.txt`) |
| binance-public-data télécharge la somme de contrôle sans la vérifier ; timestamps en µs en 2025 | (renvoi rapport 005, autre lane) | oui, vérifié par le testeur |
| `orderbook` (dyn4mik3) : import PyPI cassé | non | oui |
| talipp : EMA amorcée par SMA (2,4e-3) | non | oui |
| TimescaleDB : licence Timescale, redémarrage | non | oui |
| cryptofeed : Coinbase demande des identifiants ; contournement uvloop Python 3.11 | non | oui |
| Détecteurs de dérive de river ; imprécision de la variance glissante avec grand décalage | oui | non testé |
| Parcours de carnet L2 exact par ordre au marché (nautilus) ; exécution par défaut au meilleur prix à la même cotation | oui | non testé |
| Latence d'ordre de hftbacktest | non | oui |

### 8.5 Mêmes questions, chiffres côte à côte

| Question | Run 1 | Run 2 | Lecture |
|---|---|---|---|
| Métriques git des dépôts communs (commits 12 m, auteurs, part du premier) | ex. nautilus 5 529 / 127 / 85,2 % ; hftbacktest 24 / 5 / 62,5 % ; cryptofeed 39 / 4 / 74,4 % ; zipline 4 / 1 / 100 % ; ccxt 10 125 / 113 / 50,5 % | nautilus 5 529 / 127 / 85,2 % ; hftbacktest 24 / 5 / 62,5 % ; cryptofeed 39 / 4 / 74,4 % ; zipline 4 / 1 / 100 % ; ccxt 10 126 / 113 / 50,5 % | Identiques (34 dépôts comparés) ; écarts ≤ 1 à 2 % pour skfolio (244 vs 235), pysystemtrade (203 vs 189), hummingbot (1 807 vs 1 733), dus à l'heure du clone |
| Fichiers de tests | riskfolio 1, ta 6, yfinance 22, ccxt 1 185, pointblank 83 | riskfolio 357, ta 38, yfinance 105, ccxt 2 173, pointblank 251 | **Divergent** : regex différentes, chiffres non comparables |
| Calendriers NYSE | 21/21 fériés 2024-25 ; 6/6 fermetures anticipées ; 71 et 211 calendriers ; fenêtre 2006-09-29→2027-09-29 | 1 758 sessions 2020-2026 identiques ; 14 fermetures anticipées ; 71 et 211 ; même fenêtre | Accord complet |
| ccxt REST | 6/8 places, 60 lignes, dernière barre en formation partout, pas de réception | 4/6 places (Gate et KuCoin non testés), 100 lignes, idem | Accord |
| cryptofeed réception | JSON : retard 28,4 et 24,6 ms (rapport : 4,1 ms) | −34,6 ms (Kraken) et +4 843 ms (Bitstamp) | Non comparable : échantillons de 1-2 trades ; le signe change |
| cryptofeed licence | 2.5.0 exécutée : XFree86-1.1 ; 3.0.1 : AGPL, Python ≥ 3.13 | 2.4.1 exécutée, étiquetée AGPL (licence du dépôt actuel) | **Divergent** : R2 applique l'étiquette du dépôt à une version plus ancienne (INFERENCE ; je n'ai pas lu la licence de 2.4.1) |
| hftbacktest file d'attente | 4 modèles : NEW après 4 lots, FILLED après cumul 11 > 10 ; frais −0,01 | 4 modèles : exécution à 8,0 s ; frais −0,01 ; latence 4 s : pas d'exécution | Accord ; aucun des deux ne départage les modèles |
| hftbacktest débit | 1,96 M ev/s (tableau prêt, 200 000 événements) | 10,88 M ev/s (2 M événements, boucle numba) | Non comparable |
| nautilus déterminisme | empreinte identique sur 2 processus | hash identique sur 2 exécutions | Accord |
| nautilus débit | 19 k cotations/s (avec stratégie et ordres) | 360 k cotations/s (stratégie passive, 1 M ticks) | Non comparable (charge différente) |
| nautilus remplissage | ordre au marché au meilleur prix de la même cotation ; parcours de carnet exact | ordre passif limité non exécuté par les trades (9 configs) ; exécuté à croisement de carnet | Compatibles (ordres différents) |
| Moteurs de backtest : accord | vectorbt/backtrader/zipline exacts à l'analytique (≤ 1e-7 absolu) selon la convention | 57 transactions identiques pour backtesting.py, backtrader, vectorbt ; Δ 7e-9 entre backtrader et vectorbt | Accord sur l'arithmétique ; `bt` non comparable dans les deux |
| ABIDES | Python 3.9 ; même graine ⇒ même empreinte ; 3,5 à 4 s (20 minutes simulées) | idem ; 1,6 à 2,0 s (fin 09:45) | Accord (horizon différent) |
| river précision | erreur relative variance 6,9e-6 (décalage 1e9) ; EWMean vs pandas 0,038 | 8,4e-15 (log-rendements) ; EWMean 1,1e-19 | Non comparable (données différentes) ; R1 montre la fragilité sur niveaux, R2 la précision sur rendements |
| Portefeuille : écart aux poids de référence | 3,4e-10 / 3,0e-6 / 7,6e-5 (PyPfOpt / Riskfolio / skfolio) | 2,6e-9 / 5,1e-7 / 3,0e-5 | Même ordre de classement ; oracles différents (formule fermée vs SLSQP) |
| Métriques | empyrical ≤ 1e-15 vs main | empyrical Δ 1e-15 vs numpy | Accord |
| DQ pandera / GX / pointblank | 12/12 chacun, 0,08 / 0,29 / 1,41 s (200 000 lignes) | attendus: pandera 105 cas, GX 5 comptes, pointblank 2/1/1 (3 000 lignes) | Pas de mesure commune ; conclusions compatibles (pandera léger, GX lourd) |
| frictionless | 5/12 | 2 vérifications (4 doublons, 5 valeurs déviantes) | Compatible (faible pour la structure temporelle) |
| ArcticDB | versionnage OK ; `prune` détruit l'historique ; suppression possible ; BSL | lecture `as_of` OK ; BSL ; second datastore | Accord |
| Empreinte (Mo) | nautilus 870, vectorbt 678, zipline 503, GX 302, arcticdb 197, backtesting.py 171 (venvs partagés) | 574, 622, 464, 267, 186, 158 (venv isolé) | Non comparable (méthode) ; ordre de grandeur cohérent |
| Comptage `EXEC` du même projet | ex. sortedcontainers « exécuté » | « import seul » | Divergence de définition |

### 8.6 Où ils s'accordent (et pourquoi c'est solide)

- **Verdict** identique, avec le même refus de désigner une « meilleure plateforme ».
- **Lacunes de l'open source** identiques : pas de magasin PIT append-only avec horodatage de réception côté serveur ; pas d'estimation de coûts calibrée sur données ; collecte : la barre en formation n'est pas signalée (ccxt), pas d'horodatage de réception (ccxt), cryptofeed est la seule source native de réception mais avec un risque de licence.
- **Petites bibliothèques pures fiables** : exchange_calendars, river, PyPortfolioOpt, skfolio, pandera, DuckDB.
- **Licences problématiques identifiées de la même façon** : GPL (backtrader, freqtrade), AGPL (backtesting.py, cryptofeed 3.x), BSL (ArcticDB), Commons Clause (vectorbt), LGPL (nautilus).
- **Maintenance** : mêmes dépôts inactifs (backtrader, ABIDES, empyrical-reloaded) et mêmes bus factor.
- **Problèmes d'environnement** : ABIDES ne tourne qu'en Python 3.9 avec des versions de 2020-2022 ; ccxt demande un chemin CA dans le bac à sable ; Binance/Bybit bloqués par la sortie réseau.

### 8.7 Où ils divergent, et pourquoi (synthèse)

1. **Périmètre exécuté** : R2 exécute 9 projets de plus et en ajoute 22 nouveaux ; règle d'adjudication écrite dans R2, implicite dans R1 ⇒ R2 a plus d'ADOPT/ADAPT et moins de REJECT sur non-exécutés.
2. **Nature des tests** : R1 teste des **ordres exacts avec frais et glissement**, la **causalité** des moteurs et des indicateurs ; R2 teste la **sémantique d'un scénario L2 de file d'attente**, la **jointure as-of** et un **stockage PostgreSQL réel**.
3. **Isolation** : R1 partage des venvs par groupe (les défauts de dépendance ne sont pas visibles) ; R2 isole (défauts visibles) mais ne fige pas les mêmes versions (nautilus 1.221.0 vs 1.231.0).
4. **Étiquetage** : R1 = OBSERVED presque partout, R2 = PROVEN pour les oracles écrits par le testeur.
5. **Contradiction factuelle unique** entre les deux : l'indépendance des deux bibliothèques de calendrier (R1 l'affirme, R2 et les métadonnées de R1 la démentent).
6. **Des « ✘ » dans chaque run** : chiffres du rapport non retrouvés dans les fichiers bruts (voir 7.5), sans effet sur les verdicts.

### 8.8 Que faire des deux PR

D'après la PR #18 (« only one should be merged ») et l'état des fichiers : les deux touchent les mêmes chemins (`reports/017_oss_trading_infra/00…09` et `bench/oss_trading_infra_v1/`). Fusionner l'une écraserait l'autre. Ce qu'apporte chacune est **complémentaire** (8.2, 8.4). Une piste à adjuger : conserver le run 2 comme rapport principal (plus complet, versions figées) et verser les tests propres au run 1 (T03, T04, T05) sous un autre nom de dossier ; ou l'inverse. Je ne tranche pas.

---

## 9. Reproductibilité

### 9.1 Run 1

- **Fourni** : `bench/oss_trading_infra_v1/setup_envs.sh` (12 venvs avec `uv`, `EBASE` par défaut `/tmp/e`), `run_all.sh`, `run_t03.sh`, `py/*.py` (un script par test), `py/common.py`, `py/dq_data.py`, `results/` (JSON bruts), `README.md`.
- **Dépendances** : `uv` ; Python 3.9, 3.12, 3.13 ; accès PyPI ; `git clone --depth 1 https://github.com/jpmorganchase/abides-jpmc-public` ; sortie réseau vers Kraken/Coinbase/OKX/Bitstamp/Gate/KuCoin pour T11.
- **Commande** : `bash setup_envs.sh` puis `bash run_all.sh` (avec `EBASE`, `GITBARE`).
- **Durée** : non indiquée (je n'ai pas de mesure ; **UNKNOWN**).
- **Manques** :
  - **Aucune version figée** : `setup_envs.sh` installe « la dernière version » de chaque paquet ; les résultats d'aujourd'hui ne se reproduiront pas nécessairement à l'identique (hors dates).
  - `run_all.sh` lit des clones nus dans `$GITBARE` (par défaut `/tmp/g`) pour `repo_health.py`, mais **aucun script ne crée ces clones** ; `repo_tests.py` de même. Les métriques de maintenance ne sont donc pas relançables telles quelles.
  - `run_t03.sh` renvoie à un `ENVIRONMENT.md` **absent** de la branche.
  - `py/discover_github.py` (recherche GitHub) est fourni mais la recherche était bloquée ; aucun fichier de résultat de découverte.
  - `bench/oss_trading_infra_v1/log/*/summary_log.bz2` (4 fichiers) : des sorties du simulateur ABIDES (objets pandas sérialisés) commités par accident ; non documentés. **À ne pas ouvrir avec `pickle` sans précaution**, comme tout fichier sérialisé venant d'ailleurs.
  - Les tests réseau (T11) sont des instantanés datés et différeront.

### 9.2 Run 2

- **Fourni** : `bench/oss_trading_infra_v1/` avec `README.md`, `env/freeze_*.txt` (15 gels + `system.txt` + journal du premier échec d'installation), `py/catalog.py`, `screen.py`, `footprint.py`, `adjudication.py`, `gen_reports.py`, `py/mt/*` (microtests), `sql/*.sql`, `results/*` (dont `screen.json`, 109 ko). Le rapport `06_COMPONENT_TESTS.md` contient un bloc « Reproduce » (`uv venv ... --python 3.11`, `uv pip install -r ../env/freeze_hft.txt`, exécution avec `PYTHONPATH`).
- **Dépendances** : `uv 0.8.17`, Python 3.11.15 (plus 3.9 pour ABIDES et 3.12 pour pandas-ta), PostgreSQL 16.15 (Ubuntu), `postgresql-16-partman 5.0.1`, `timescaledb-2-postgresql-16 2.30.2` depuis le dépôt apt du fournisseur, `shared_preload_libraries='timescaledb'` + redémarrage, répertoire de données appartenant à l'utilisateur `postgres`, `clickhouse-local 26.10.1.1022` (binaire **non commité**), accès réseau (git, PyPI, échanges, data.binance.vision, Tardis).
- **Commande type** : voir 06 ; `cd bench/oss_trading_infra_v1/py && python screen.py` (réseau) ; puis, par groupe, `python mt/<script>.py` depuis un dossier hors du paquet installé (un `types.py` local masque la bibliothèque standard).
- **Durée** : non indiquée (`screen.py` : 6 fils, délais de 240 à 300 s par clone) ; **UNKNOWN**.
- **Manques** : chemin CA du bac à sable à remplacer (`/root/.ccr/ca-bundle.crt`) ; `binance-public-data` lancé « depuis /tmp » sans script versionné ; aucun script de démarrage PostgreSQL ; les résultats de `screen.py` dépendent de la date d'exécution (fenêtre fixée au 2025-09-29 mais historique amont vivant) ; l'adjudication est écrite à la main dans `adjudication.py`.
- **Points forts** : versions figées, résultats bruts complets, code de génération des tableaux du rapport.

---

## 10. Implications pratiques pour AurumShift (pistes à adjuger plus tard)

**Garde-fou.** Rien ci-dessous n'affirme une compatibilité avec AurumShift : je n'ai pas vu son code. Ce sont des pistes à soumettre à l'adjudication finale contre le dépôt local réel.

1. **Calendriers de marché** : `exchange_calendars` est le candidat le mieux soutenu par les deux runs (accord complet des tests, 62 commits et 14 auteurs sur 12 mois, licence Apache-2.0). Piste : le comparer au calendrier que le système utilise déjà, et figer la version (le run 2 relève que l'historique des calendriers peut changer entre versions, non testé). `pandas_market_calendars` ajoute surtout des noms (211) mais dépend du premier.
2. **Contrôle de qualité de données** : `pandera` (léger, 12/12 défauts en R1, 11 Mo isolé en R2) est une piste pour exprimer des règles de schéma en code ; les règles de continuité temporelle (trous, barre plate à volume nul, changement d'unité ms→µs, barre en formation) restent à écrire (aucun cadre ne les apporte tout seul). À rapprocher de la contrainte « PostgreSQL d'abord » : vérifier si ces règles doivent plutôt vivre en SQL.
3. **Fuite du futur** : deux enseignements transférables. (a) Une bibliothèque d'indicateurs doit passer un **test d'invariance au préfixe** avant emploi (R1) ; `ta` et `pandas-ta` échouent sur 5 et 9 colonnes ; TA-Lib est causal sur ce qui a été testé (RSI, R2). (b) Aucun moteur de backtest testé ne détecte un futur injecté par les données (R2) : la protection doit venir de la couche donnée.
4. **Rejeu / carnet** : `hftbacktest` (MIT, deux horodatages natifs bourse/local, latences séparées) est la piste à examiner pour un rejeu conscient de la file ; à condition de convertir les flux dans son format d'événements. `nautilus_trader` est utile comme oracle sémantique (R1) mais son remplissage passif est non résolu (R2), sa licence est LGPL et il embarque du code d'exécution réelle. Les deux sont « à adjuger » vis-à-vis de la contrainte « événementiel plutôt que haute fréquence ».
5. **Coûts de transaction** : aucune bibliothèque testée n'estime les coûts à partir des données ; seules des formes paramétriques existent (zipline volume-share, cvxportfolio spread + impact 1,5, Almgren–Chriss). La forme fonctionnelle de cvxportfolio est vérifiée (R2) mais la bibliothèque est GPL-3.0 à auteur unique : la piste est d'en reprendre la **formule** comme référence, pas le paquet ; la calibration reste à produire à partir des données de la lane coût d'exécution.
6. **Stockage** : rien ne sert de créer un deuxième magasin autoritaire d'après les deux runs (ArcticDB : BSL, suppression possible, temps de version côté client). Piste R2 : partitionnement natif PostgreSQL ou TimescaleDB (compression, licence Timescale) ; à comparer sur des données réelles, pas des ticks synthétiques.
7. **Collecte** : `ccxt` (MIT) comme client REST derrière une enveloppe qui retire la barre en formation et pose l'horodatage de réception ; `cryptofeed` ≤ 2.x pour la réception native, avec le risque AGPL sur 3.x. Le contrat de provenance (réception, unité) est à écrire côté AurumShift.
8. **Statistiques en ligne** : `river` (BSD-3), état sérialisable, bonne précision sur des rendements, mais précision de la variance glissante limitée sur des niveaux de prix (R1) ; à adjuger si AurumShift maintient des statistiques en flux.
9. **Portefeuille** : `PyPortfolioOpt`, `Riskfolio-Lib`, `skfolio` s'accordent avec un solveur de référence à ≤ 7,6e-5 : utiles comme **oracles croisés**. PyPortfolioOpt HRP est cassé sur le SciPy testé (R1). Rien ne couvre les limites de risque comme gouvernance (R2).
10. **Licences** : à faire examiner par une personne compétente (LGPL, AGPL, GPL, BSL, Commons Clause, Elastic 2.0, Timescale License). Les deux runs refusent d'interpréter.

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **Départager backtesting.py** (PARK vs ADOPT) : refaire le test de coûts de R1 avec plusieurs chemins d'ordre (`position.close()`, `sell()`), et le test de R2 avec frais non nuls. Faible coût, forte valeur pour la cohérence entre runs.
2. **Test de fuite complet de TA-Lib et talipp** avec la méthode de R1 (toutes les colonnes), puis liste blanche d'indicateurs ; et corriger le mécanisme décrit pour `ta` dans le rapport 05 du run 1.
3. **Résoudre la question du remplissage passif de nautilus** (R2 UNKNOWN) : même scénario, versions 1.221.0, 1.231.0 et 2.0.0rc5, ordres LIMIT avec et sans `trade_execution`, et vérifier que les réglages agissent (hash différents).
4. **Réconcilier les deux jeux de résultats** : régénérer les rapports depuis les fichiers `results/` (au moins les durées et les chiffres cryptofeed du R1, les durées du R2) pour que « chaque chiffre vienne d'un fichier ».
5. **Test sur données réelles** : rejouer une journée de carnet L2/L3 réel (un échantillon Tardis) dans hftbacktest et nautilus ; comparer le remplissage passif à des remplissages connus.
6. **Compléter le test de qualité de données à armes égales** : mêmes règles pour tous les cadres, défauts inconnus du testeur (injection par un tiers), mesure de rappel/précision.
7. **Test d'indépendance des calendriers** : comparer exchange_calendars à une source externe (calendriers officiels des bourses) pour un jeu de dates plus large.
8. **Décision sur les deux PR** : choisir le dossier principal et sauvegarder l'autre sous un autre nom (8.8).
9. **Licences** : avis juridique sur l'usage interne de LGPL/AGPL/BSL ; vérifier la licence réelle de cryptofeed 2.4.1/2.5.0.
10. **Étendre la découverte** : ajouter aux catalogues les noms de l'autre run (76 projets) et tenter l'exécution des non exécutés les plus pertinents (QuestDB, vnpy, LEAN en backtest seul) si ces classes intéressent.

---

## 12. Index des fichiers lus

Tous lus intégralement sauf mention.

### Dépôt (racine)
- `/home/user/aurumshift-external-research-lab/claude.md` — doctrine de recherche, étiquettes de preuve, frontière AurumShift (lu jusqu'à « Important boundary »).
- `/home/user/aurumshift-external-research-lab/SYNTHESE_LANES.md` — synthèse générale des lanes (lu seulement l'en-tête et le lexique ; **non lu** au-delà de l'entrée du tableau).

### Run 1 — `origin/claude/oss-trading-research-infra-v1`
Rapports (`reports/017_oss_trading_infra/`) : `00_EXECUTIVE_SUMMARY.md` (résumé, bloc final) ; `01_LANDSCAPE.md` (criblage 32 exécutés + 22 non exécutés) ; `02_DATA.md` (collecteurs, calendriers, DQ, stockage) ; `03_REPLAY.md` (carnets, rejeu) ; `04_EXECUTION.md` (moteurs, coûts) ; `05_FEATURE_RISK.md` (indicateurs, river, portefeuille) ; `06_COMPONENT_TESTS.md` (registre T01-T16, erreurs corrigées) ; `07_OPERATIONAL_COST.md` (empreintes, licences, autorité) ; `08_ADJUDICATION.md` (tableau des classes) ; `09_LIMITATIONS.md`.
Bench (`bench/oss_trading_infra_v1/`) : `README.md` ; `setup_envs.sh`, `run_all.sh`, `run_t03.sh` ; scripts lus en entier ou en grande partie : `py/common.py`, `py/dq_data.py`, `py/repo_health.py`, `py/t01_orderbook.py` (en-tête, flux), `py/t02_nautilus_replay.py` (en-tête), `py/t04_causality.py` (en-tête et moteur vectorbt/backtesting), `py/t05_feature_prefix.py` (comparaison de préfixe), `py/t12a_hft_queue.py`, `py/t12b_zipline_volshare.py`, `py/t03_engine_reconcile.py` (lignes du paramètre spread), `py/discover_github.py` (en-tête), `py/footprint.py` (en-tête) ; **non lus** en détail : `t06`-`t11`, `t13`-`t16`, `repo_tests.py`, `t03z_zipline.py`, `t12c`. Résultats lus : tous les `results/t*.json(l)`, `repo_health.json`, `repo_tests.json` (extraits), `footprint.json` (extrait). `log/*/summary_log.bz2` : en-tête d'un fichier seulement.

### Run 2 — `origin/claude/amazing-wozniak-bwjdfp`
Rapports : les mêmes dix fichiers `00` à `09`, intégralement lus (le `08` contient le tableau des 67 candidats).
Bench : `README.md` ; `py/catalog.py` (début), `py/screen.py`, `py/adjudication.py` (début), `py/gen_reports.py` (début) ; `py/mt/common.py`, `bt_engines.py`, `leak_probe.py`, `dq_microtest.py` (début 80 lignes), `hft_microtest.py`, `tcm_microtest.py`, `naut_lib.py` (début), `naut_microtest.py` (début), `store_microtest.py` (début) ; **non lus** : `abides_microtest.py`, `cal_microtest.py`, `coll_microtest.py`, `feat_microtest.py`, `misc_microtest.py`, `naut_cross_probe.py`, `naut_l1_probe.py`, `orderbook_microtest.py`, `port_microtest.py`, `stats_microtest.py`, `zl_microtest.py`, `footprint.py`, `sql/*.sql`. Résultats lus : `abides_microtest.json`, `bt_engines.json`, `cal_microtest.json`, `coll_microtest.json`, `dq_microtest.json`, `feat_microtest_*.json` (3), `hft_microtest.json`, `leak_probe.json`, `misc_microtest.json`, `naut_microtest.json`, `orderbook_microtest.json`, `port_microtest.json`, `stats_microtest.json`, `store_microtest.json`, `tcm_microtest.json`, `zl_microtest.json`, `tss_microtest.txt`, `clickhouse_local_asof.txt`, `final_block_counts.txt`, `footprint.json` (début), `screen.json` (structure, comparaison de métriques avec le run 1 ; le contenu détaillé des 109 ko n'est pas lu ligne à ligne). `env/system.txt`, `env/stats_install_first_attempt.log`, début de `env/freeze_zl.txt` lus ; les autres `freeze_*` **non lus**.

### Métadonnées GitHub
- PR #16 et PR #18 (`redguiff-bot/aurumshift-external-research-lab`) : titre, description, état (brouillon ouvert), commit tête, nombre de fichiers et de lignes.
- Source externe consultée pour un seul contrôle : archive source `ta-0.11.0.tar.gz` (PyPI), fichiers `ta/trend.py` et `ta/wrapper.py`.
