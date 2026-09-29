# Lane 015 — Découverte de features (deux runs indépendants) : analyse approfondie

Auteur de l'analyse : agent de recherche (Claude), pour Jean-François. Date de l'analyse : 2026-09-29.
Périmètre : `reports/015_feature_discovery/` et `bench/feature_discovery_v1/` sur deux branches. Rien n'a été modifié dans le dépôt (lecture via `git show` / `git archive` vers un dossier temporaire ; recalculs faits dans des copies jetables).

**Comment lire ce document.**
- Les étiquettes du dépôt sont reprises : PROVEN (prouvé par test ou par construction), OBSERVED (chiffre lu ou recalculé), DOCUMENTED_CLAIM (affirmé par un rapport, non vérifié), INFERENCE (mon raisonnement), UNKNOWN (inconnu).
- « Le rapport affirme » = ce que dit le texte des rapports. « Vérifié » = j'ai retrouvé le chiffre dans un fichier de résultats brut ou je l'ai recalculé moi-même. Marqueurs : ✔ vérifié, ✘ écart, ? non vérifiable.
- Quand je cite un chiffre, le chemin du fichier source est entre parenthèses. Les chemins sont relatifs à la racine de la branche concernée. `R1` = run 1 (branche `claude/feature-discovery-v1`, PR #13). `R2` = run 2 (branche `claude/feature-discovery-v1-b`, PR #20).
- Vocabulaire minimal (chaque terme est ré-expliqué à sa première occurrence dans le texte) : **branche** = copie de travail parallèle du dépôt ; **PR (pull request)** = demande d'intégrer une branche dans `main` ; **commit** = un enregistrement daté des modifications ; **hash SHA-256** = empreinte numérique d'un fichier (si le fichier change d'un octet, l'empreinte change).

---

## 0. Fiche d'identité

| | Run 1 (R1) | Run 2 (R2) |
|---|---|---|
| Branche | `origin/claude/feature-discovery-v1` | `origin/claude/feature-discovery-v1-b` |
| PR | #13, brouillon (draft), ouverte le 2026-09-29 18:12 UTC | #20, brouillon (draft), ouverte le 2026-09-29 18:57 UTC |
| Titre PR | « Feature discovery V1 (symbolic / sparse / interactions / causal boundaries) — LIMITED_STABLE_FEATURES_SUPPORTED » | « 015 feature discovery v1 (independent run): NO_STABLE_NEW_FEATURES » |
| Commit de tête | `fa00dcc5bda8e1714384d9500af113e7f08ebd3c` (18:11:57 UTC) | `4a585703818234a3bd4bb90170e883cdb5b21fb7` (18:57:14 UTC) |
| Nombre de commits propres à la branche | 8 (`c50e99c` → `fa00dcc`) | 7 (`829579c` → `4a58570`) |
| Base commune | `1a449df` (fusion de la PR #6, `main`) | idem |
| Fichiers ajoutés (PR) | 81 fichiers, +11 226 lignes | 101 fichiers, +1 871 lignes |
| Dont fichiers de la lane | 81 (17,49 Mo dont 17,11 Mo de données brutes compressées) | 93 (8,65 Mo) + 8 fichiers `.whl` hors-sujet (62,45 Mo) |
| Rapports | 11 fichiers `reports/015_feature_discovery/00` à `10` | idem, 11 fichiers, beaucoup plus courts (voir §12) |
| Verdict final | `LIMITED_STABLE_FEATURES_SUPPORTED` | `NO_STABLE_NEW_FEATURES` |
| Force du verdict (selon le run) | Le rapport le qualifie lui-même de « faible » et donne une « lecture pratique » = rien à ajouter aux primitives brutes (`reports/015_feature_discovery/00_EXECUTIVE_SUMMARY.md`, `09_ADJUDICATION.md`) | « MODERATE-LOW » (`00_EXECUTIVE_SUMMARY.md`) |
| Ma lecture de la force | Le label est **mécanique et fragile** : il repose sur une seule formule, redondante, sur une cible facile (voir §7 et §8). | Le négatif est **crédible mais peu puissant** : fenêtre courte, une seule cible (voir §7 et §8). |

Blocs finaux côte à côte (reproduits tels quels de `reports/015_feature_discovery/09_ADJUDICATION.md` de chaque branche) :

```
# R1
FEATURES_DISCOVERED=2
FEATURES_HELDOUT_STABLE=1
SYMBOLIC_EXPRESSIONS_STABLE=0
NONREDUNDANT_FEATURES=0
CAUSAL_IDENTIFIED_COUNT=0
COMPLEXITY_JUSTIFIED=NO
FINAL_VERDICT=LIMITED_STABLE_FEATURES_SUPPORTED

# R2
FEATURES_DISCOVERED=80 distinct pre-validation candidates over 5 seeds (18/20/19/22/20 per seed)
FEATURES_HELDOUT_STABLE=0
SYMBOLIC_EXPRESSIONS_STABLE=0
NONREDUNDANT_FEATURES=0
CAUSAL_IDENTIFIED_COUNT=0
COMPLEXITY_JUSTIFIED=NO
FINAL_VERDICT=NO_STABLE_NEW_FEATURES
```

**Fichiers `.whl` hors-sujet dans R2 (à la racine de la branche).** Un `.whl` est un paquet Python précompilé (un « installeur » de bibliothèque), sans rapport avec la recherche. Ils ont été ajoutés par erreur dans le commit `2b03487` (2026-09-29 18:35:36 UTC, « decile profiles, analysis script, README ») (OBSERVED, `git log --diff-filter=A`). Liste exacte (OBSERVED, `git ls-tree -r -l`) :

| Fichier | Octets |
|---|---|
| `cloudpickle-3.1.2-py3-none-any.whl` | 22 228 |
| `gplearn-0.4.3-py3-none-any.whl` | 40 300 |
| `joblib-1.6.0-py3-none-any.whl` | 306 115 |
| `narwhals-2.26.0-py3-none-any.whl` | 474 034 |
| `numpy-2.4.6-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl` | 16 918 164 |
| `scikit_learn-1.9.1-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl` | 9 315 422 |
| `scipy-1.17.1-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl` | 35 349 300 |
| `threadpoolctl-3.7.0-py3-none-any.whl` | 26 362 |
| **Total (8 fichiers)** | **62 451 925 octets (≈ 62,5 Mo, ≈ 59,6 Mio)** |

Ils gonflent la PR #20 et ne sont pas référencés par le code. Détail utile : ils m'ont servi à installer, sans internet, exactement les mêmes versions que R2 pour rejouer les calculs (voir §9). La synthèse `SYNTHESE_LANES.md` recommande déjà de les retirer si la PR #20 était retenue.

Autres éléments d'identité :
- Mission (citée par R1) : `AURUMSHIFT_EXTERNAL_FEATURE_DISCOVERY_SYMBOLIC_CAUSAL_V1`, mode `EXTERNAL_RESEARCH_ONLY / NO_PRIVATE_AURUMSHIFT_CODE / NO_INTEGRATION` (`reports/015_feature_discovery/00_EXECUTIVE_SUMMARY.md`, R1).
- Sessions Claude distinctes (les deux PR citent deux identifiants de session différents) : le run 2 dit explicitement ne pas avoir lu le run 1 (`R2 00_EXECUTIVE_SUMMARY.md` § « Note on a pre-existing branch » ; PR #20 : « I did not read it »). Donc **deux études indépendantes**, ce qui rend leur comparaison informative (§8).
- Données : klines (bougies) 1 heure du marché « spot » Binance, via l'API publique `data-api.binance.vision`. Les deux runs sont **hors AurumShift** : aucun code privé.

---

## 1. Mission et question posée

### 1.1 La question, en langage simple

Imagine que tu donnes à un ordinateur une vingtaine de « mesures » simples calculées sur les prix (rendement sur 24 h, volatilité récente, volume, etc.). On appelle ces mesures des **primitives** ou **features** (« variables explicatives » : des chiffres calculés à l'instant t pour prédire quelque chose sur le futur). La question :

> Un programme automatique peut-il **inventer** de nouvelles features (combinaisons de primitives, formules) qui (a) prédisent vraiment quelque chose sur des données jamais vues, (b) sont courtes et lisibles, (c) apportent quelque chose que les primitives brutes ne donnent pas déjà, et tout cela **sans se raconter d'histoires** (sans « surajustement silencieux », c'est-à-dire sans trouver par hasard une formule qui marche sur le passé et pas ailleurs) ?

Méthodes mises à l'épreuve (les deux runs, avec des variantes) :
- **Information mutuelle (MI) / information mutuelle conditionnelle (CMI)** : mesures de « combien deux quantités se renseignent l'une l'autre » ; la conditionnelle demande « combien en plus, une fois qu'on connaît déjà d'autres variables ».
- **Stability selection** (sélection de stabilité) : on refait une régression parcimonieuse (lasso, qui met à zéro les coefficients inutiles) sur de nombreux sous-échantillons et on ne garde que les variables choisies presque à chaque fois.
- **Recherche d'interactions** : tester des produits de deux variables (a×b).
- **Régression symbolique par programmation génétique (GP)** : un algorithme évolutionniste qui « fait évoluer » des formules mathématiques (bibliothèque `gplearn`).
- **Orthogonalisation** : enlever d'une feature ce que les autres features expliquent déjà, pour tester la nouveauté.
- **Invariance / causalité** (ICP, test Q de Cochran) : tester si une relation reste la même d'un environnement à l'autre, sans jamais conclure « cause » sans expérience.
- **Baselines** (références à battre) : régression ridge sur toutes les primitives, lasso, sélection par importance d'arbre, par importance de permutation, et un GBM (arbres boostés, plafond non parcimonieux).

Deux mesures reviennent partout :
- **IC (coefficient de corrélation d'information)** : corrélation de rang (Spearman) entre la valeur de la feature et le résultat futur. IC = 0 : aucune information ; IC = 0,05 en finance est déjà « intéressant » ; IC = 0,5 est énorme (et en général suspect, voir §3 et §7).
- **R² hors échantillon (OOS R²)** : part de la variance du futur expliquée par un modèle sur des données jamais utilisées pour l'ajuster. Négatif = pire que de prédire une constante (ou zéro).

### 1.2 Contraintes du dépôt (`claude.md`)

Le fichier `claude.md` (identique sur les deux branches, 2 162 octets) impose :
- Doctrine **REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST** : d'abord réutiliser l'existant, puis l'adapter, l'encapsuler, le composer ; ne fabriquer soi-même qu'en dernier.
- Étiquettes de preuve PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN pour toute conclusion ; pas de benchmark fabriqué ; sources primaires ; ne pas se fier aux README.
- Verdicts par candidat : ADOPT / ADAPT / PARK / REJECT ; « rejeter ou parquer une technologie qui exige beaucoup de réglages sauf bénéfice exceptionnel ».
- Contraintes AurumShift à ne pas oublier : recherche seulement (paper-only, pas de capital réel), PostgreSQL d'abord, PIT (point-in-time : n'utiliser que ce qui était connu à l'instant t) / provenance / pas de regard vers le futur (« lookahead »), intraday événementiel (pas HFT), coûts de marché réalistes, complexité d'infrastructure justifiée.
- Frontière : ne jamais affirmer qu'un candidat est compatible avec AurumShift à partir de ce dépôt ; l'adjudication d'intégration se fait plus tard contre le vrai dépôt local (`claude.md`).

Application dans cette lane (OBSERVED) : R1 réutilise `gplearn` (bibliothèque existante) et `scikit-learn`, écrit lui-même les modules de screening/interactions (CUSTOM, faute d'existant équivalent) ; PySR (régression symbolique en Julia) est cité mais **non exécuté** dans les deux runs. Aucun des deux ne teste de code AurumShift.

---

## 2. Méthode

### 2.1 Données, univers, primitives, cibles

| | R1 | R2 |
|---|---|---|
| Source | Binance spot 1 h, `data-api.binance.vision`, fenêtre figée 2021-01-01 → 2026-09-01 (exclu) (`bench/feature_discovery_v1/fd/data.py`) | Idem source ; 20 000 dernières barres/marché avant 2026-09-01 (`src/data.py`) |
| Période brute | 2021-01-01 00:00 → 2026-08-31 23:00, **49 642 lignes/marché**, 7 trous d'1 h par marché (`data/MANIFEST.json`) | 2024-05-20 17:00 → 2026-09-01 00:00, **20 000 lignes/marché**, 0 trou pour BTC (`raw/manifest.json` ; recalcul) |
| Empreintes SHA-256 des données | dans `data/MANIFEST.json` | dans `raw/manifest.json` |
| Vérification des empreintes | ✔ 9/9 fichiers concordent (recalcul par moi) | ✔ 10/10 concordent (recalcul par moi) |
| Marchés « découverte » | BTC, ETH, BNB, SOL (4) | BTC, ETH, BNB, SOL, XRP, ADA (6) |
| Marchés « jamais vus » (unseen) | XRP, ADA, DOGE, LINK, **PAXG** (or tokenisé) (5) | DOGE, LINK, LTC, AVAX (4) |
| Nombre total de marchés | 9 | 10 |
| Primitives | 26 (rendements 1/4/24/72/168 h, log-vol réalisée 6/24/168 h, Parkinson 24 h, amplitude, CLV, volumes, taker-buy, nb de trades, taille moyenne de trade, distance haut/bas 72 h, écarts aux moyennes 24/168 h, Amihud, heure sin/cos, week-end) (`fd/features.py`) | 20 (rendements 1/4/12/24/72 h, vol 24/72 h, amplitude, log-volume relatifs, taker-buy, CLV, distances 24 h, MA24/MA72, Amihud) (`src/features.py`) |
| Standardisation | z-score glissant sur 720 barres passées, borné à ±5 (sauf calendrier) | z-score glissant sur 500 barres, borné à ±6 |
| Cibles | **deux** : `y_ret` (rendement futur 4 h ÷ (vol 168 h × √4), borné ±5) et `y_vol` (log du rapport « vol réalisée future 24 h / vol réalisée passée 24 h », borné ±3) | **une seule** : `y` = rendement futur 4 h ÷ (σ24 × √4), borné ±6 |

Explications :
- Un **marché « jamais vu »** est un actif dont aucune donnée n'entre dans l'entraînement ni la sélection ; il ne sert qu'à l'évaluation finale. C'est le test « est-ce que ça généralise à un autre actif ? ».
- Un **rendement vol-scalé** est le rendement futur divisé par une mesure de la volatilité passée : on le rend comparable entre actifs et périodes.
- `y_vol` est décrite par R1 comme cible « facile » servant de contrôle de puissance (`02_PROTOCOL.md §3`). **Point crucial pour la suite** : la volatilité future ÷ volatilité passée a une relation *mécanique* avec la volatilité passée elle-même (voir §7.2 et §8).

### 2.2 Découpages temporels (tuning / validation / held-out)

Le **held-out** est le bloc de données mis de côté, regardé une seule fois à la fin. La **validation** sert à choisir/filtrer. L'**entraînement (train)** sert à ajuster. Un **embargo** est un trou entre deux blocs pour éviter que des étiquettes qui regardent 4 ou 24 heures en avant ne « débordent » d'un bloc sur l'autre.

| Bloc | R1 (`fd/panel.py`, `02_PROTOCOL.md §2`) | R2 (`src/pipeline.py::Panel`, `configs/protocol.json`) |
|---|---|---|
| Train | départ + 800 barres d'échauffement → 2023-06-30 : 21 050 h/marché (2021-02-03 08:00 → 2023-06-30 23:00) | 0–50 % des lignes communes : 2024-06-03 02:00 → 2025-07-16 22:00 (9 813 h) |
| Embargo | 7 jours | 24 barres |
| Validation | 2023-07-08 → 2024-12-31 : 13 032 h/marché | 50–70 % : 2025-07-18 23:00 → 2025-12-27 21:00 (3 887 h) |
| Embargo | 7 jours | 24 barres |
| Held-out | 2025-01-08 → 2026-08-31 : 14 400 h (y_vol) / 14 420 h (y_ret) par marché, 9 marchés | 70–100 % : 2025-12-29 22:00 → 2026-08-31 20:00 (5 879 h), 10 marchés |
| Durée approx. du held-out | ≈ 20 mois | ≈ 8 mois |

(OBSERVED : R1 `results/discovery_train_val.json`, `results/heldout_results.json` ; R2 : bornes calculées par moi à partir de `results/real/run_11.json › extra` = `t0=1717380000000, t1=1788206400000, T=19675`, en supposant des lignes horaires contiguës, ce qui est cohérent avec `T = (t1−t0)/1 h + 1 = 19 675`.)

Trois faits à retenir :
1. La **fenêtre de R2 est 2,3 ans, celle de R1 5,7 ans**. R1 a 3,4 fois plus de validation et 2,5 fois plus de held-out (en heures par marché) que R2.
2. **Chevauchement temporel** : la période d'entraînement + validation de R2 (2024-06 → 2025-12) recouvre la validation finale et presque toute la première moitié du held-out de R1 (2025-01 → 2025-12). Le held-out de R2 (2025-12-29 → 2026-08-31) est entièrement *à l'intérieur* du held-out de R1. Les deux études ne sont donc pas indépendantes dans le temps, même si leurs pipelines sont indépendants (INFERENCE).
3. Dans R2, XRP et ADA sont des marchés de découverte ; dans R1, ce sont des marchés « jamais vus ». Les univers ne sont pas superposables.

### 2.3 Pré-enregistrement, gel, verrous

Le **pré-enregistrement** consiste à écrire les règles de décision *avant* de voir les résultats, dans un commit daté (un commit est horodaté et son empreinte fait foi de l'ordre).

**R1** :
- Protocole `reports/015_feature_discovery/02_PROTOCOL.md` + code du pipeline committés dans `c50e99c` (2026-09-29 17:54:01 UTC), « before any real-data discovery run ». Comparaison que j'ai faite : entre `c50e99c` et la version finale du protocole, **seule la section 12 (déviations) diffère** (OBSERVED, `git diff`). Les règles de décision (§6 à §10) n'ont donc pas bougé.
- Formules gelées : `results/FROZEN.json` avec un **digest** (empreinte SHA-256 du contenu) `9f32094f0d93b292055750e18b7fd449910fd7129173ddcb47c116c1ce2d0666`, committées dans `9bd0b5b` (17:58:54 UTC) « BEFORE held-out and final arena ». Le script `scripts/05_heldout_once.py` recalcule le digest (`assert dg == P.digest(fro)`) et refuse de tourner si `results/heldout_lock.json` existe. Le verrou porte l'heure `2026-09-29T18:09:08Z` (OBSERVED, `results/heldout_lock.json`) : le held-out a donc été lu 10 minutes après le gel.
- Ordre des commits (OBSERVED, `git log`) : protocole 17:54 → scripts 17:56 → données complètes 17:57 → **gel 17:58:54** → arène 17:59–18:04 → **held-out + adjudication 18:10:08** → rapports 18:11:57.

**R2** :
- Pré-enregistrement `bench/feature_discovery_v1/configs/protocol.json` dans `829579c` (18:27:37 UTC). Il n'a **jamais été modifié depuis** (`git log` sur ce chemin = un seul commit) (OBSERVED). `src/pipeline.py` n'a plus bougé après `77627a9` (18:35:00), c'est-à-dire avant tout résultat synthétique, nul ou réel (OBSERVED).
- Gel : à chaque run, la liste finale (+ orientation, moyenne, écart-type) est hachée en SHA-256 et écrite dans `results/<mode>/lock_<seed>.json` **avant** l'accès au bloc held-out ; l'ordre d'accès est enregistré (`access_order` = `train, val, train, val, train, LOCK, test…`) et testé (`tests/test_isolation.py::test_heldout_untouched_before_lock`) (PROVEN par test ; ✔ `access_order` relu dans les 5 fichiers `real/run_*.json`).
- **Particularité qui compte** : pour les 5 runs réels, la liste gelée est **vide**, donc l'empreinte est celle d'une liste vide et identique partout : `8c7a94b0202c598545c6363886b45d8da993a9b7ce05b2720f19a030fefef102` (✔ lu dans `results/summary.json › real.lock_sha` et `results/real/lock_11.json`). Le « gel avant held-out » est donc, sur les données réelles, une garantie sans objet : il n'y avait aucune formule à protéger (INFERENCE).

### 2.4 Graines (seeds)

Une **graine** fixe le hasard d'un calcul pour qu'il soit rejouable.
- R1 : 5 graines de découverte `{11, 23, 37, 41, 59}` par cible (`fd/pipeline.py::Cfg.seeds`) ; arène synthétique : graines 0–9 pour le développement (4 réplications 0–3 conservées dans `synthetic_arena_dev.json`) puis graines **1000–1039** pour les chiffres finaux (40 NULL + 40 MIXED).
- R2 : découverte `11–15`, nulles `901–908`, synthétiques `7001–7006` (`configs/protocol.json`) ; graines de fumée/débogage (1, 3–6) déclarées non rapportées.

### 2.5 Simulateur / arène de vérité connue

Une **arène synthétique** est un jeu de données fabriqué où l'on sait exactement ce qui est planté. On y lance le pipeline pour vérifier qu'il (a) retrouve ce qui existe et (b) ne trouve rien quand il n'y a rien.
- R1 (`fd/synth.py`) : 14 features AR(1) persistantes, 3 marchés de découverte + 3 jamais vus ; scénario NULL (aucun signal) et MIXED (5 composantes de R² ≈ 0,6 % chacune : linéaire, interaction pure, non-linéaire pure `(z³²−1)`, spécifique à 2 marchés, décroissante ; + quasi-doublon de la composante linéaire) ; bruit hétéroscédastique.
- R2 (`src/panels.py::synth_panel`) : 16 features corrélées (t de Student à 6 degrés de liberté, AR(1)), 10 marchés ; y = b·f0 + b·f1·f2 + b·f3·|f4| + s_m·b·f5 + bruit (f5 change de signe selon le marché = « piège » ; f6 ≈ f0 + bruit = doublon) ; β = 0,06 ; T = 19 000.
- Ordre de grandeur de la force planquée (INFERENCE, mon arithmétique) : R1, R² = 0,006 par composante ⇒ corrélation ≈ √0,006 ≈ 0,077 ; R2 avec β = 0,06 ⇒ ≈ 0,06. Or les IC réels observés sur `y_ret`/`y` sont de l'ordre de 0,005 à 0,02. **Les deux arènes démontrent une puissance pour des signaux 4 à 10 fois plus forts que ce qu'on cherche réellement** (voir §7).

### 2.6 Critères de décision, seuils exacts

**R1** (`02_PROTOCOL.md` §6–§10, code `fd/pipeline.py`) :
- Score de validation = IC_val moyen − 0,0005 × (nb de nœuds) − 0,001 × (nb de constantes ajustées) ; nœuds ≤ 15 (`lam_node=0.0005`, `lam_const=0.001`, `max_nodes=15`).
- **Gate de découverte** (validation) : IC_val > 0 (signe fixé sur train) sur ≥ 75 % des 4 marchés de découverte (`val_sign_frac=0.75`), p bootstrap par blocs de 48 barres < 0,10 (`val_p`, 300 tirages), score pénalisé > 0 ; puis consolidation : famille (corrélation de rang ≥ 0,85, `cluster_corr`) retrouvée dans ≥ 60 % des graines (`min_seed_freq=0.6`, soit 3 sur 5), non redondante (|ρ| < 0,80, `redundancy_corr`). Filtre « primitive triviale » : expression à une seule variable dont le rang est corrélé à > 0,9 avec la primitive → rejetée.
- **STABLE** (held-out, 9 marchés) ⇔ p_Holm < 0,05 (bootstrap circulaire par blocs de 48 barres, B = 2 000, temps partagé entre marchés, correction de Holm sur toute la famille gelée des deux cibles) **et** IC > 0 sur ≥ 75 % des marchés **et** IC > 0 sur la majorité des 5 marchés jamais vus.
  (La **correction de Holm** est une procédure qui rend les seuils plus stricts quand on teste plusieurs choses à la fois, pour limiter les faux positifs.)
- **NON-REDONDANTE** ⇔ STABLE **et** corrélation partielle avec y, contrôlant la prédiction du ridge sur les 26 primitives brutes, significative (Holm 0,05) **et** |ρ| < 0,80 avec les autres formules stables. (La **corrélation partielle** mesure ce qui reste de lien entre deux quantités une fois qu'on a retiré l'effet d'autres variables.)
- **COMPLEXITY_JUSTIFIED** : `YES` si le modèle découvert bat toutes les baselines non-plafond en IC held-out poolé avec la borne basse (quantile 10 % de la différence appariée, `q10`) > 0 **et** ≥ 1 formule non redondante ; `PARTIAL` si `q10 > −0,005` avec ≤ la moitié des paramètres de la meilleure baseline ; sinon `NO` ; agrégat = YES si YES sur une cible, sinon PARTIAL si PARTIAL sur une cible, sinon NO.
- **Validité de l'arène (condition préalable)** : FWER (probabilité d'au moins un faux positif stable sous H0) ≤ 0,10 sur 40 réplications ET puissance sur la composante linéaire ≥ 0,80 ; sinon le verdict est `STUDY_INCONCLUSIVE` quoi qu'il arrive.
- **Verdict (règle mécanique, §10)** : arène invalide → `STUDY_INCONCLUSIVE` ; sinon NON-REDONDANTES ≥ 3 (sur ≥ 2 familles) et COMPLEXITY_JUSTIFIED = YES → `FEATURE_DISCOVERY_REFERENCE_SUPPORTED` ; sinon **≥ 1 formule STABLE** → `LIMITED_STABLE_FEATURES_SUPPORTED` ; sinon `NO_STABLE_NEW_FEATURES`. Le code (`scripts/06_adjudicate.py`) applique exactement cela (✔ relu).

**R2** (`configs/protocol.json`, `src/pipeline.py`, `src/analyze.py`) :
- **Gate de validation** : IC poolé > 0, accord de signe ≥ 70 % des marchés de découverte (`min_market_sign_agreement=0.7`, donc ≥ 5 marchés sur 6), p < 0,10 (**bilatérale**, approximation normale sur l'écart-type d'un bootstrap par blocs de 48 barres, 200 tirages).
- Sélection finale sur validation : glouton avec pénalité BIC (`k_new = 1 + nœuds/4`, ≤ 8 features, n effectif = n/4 sur données réelles).
- **STABLE** (held-out) : IC poolé > 0 de même signe que la validation, |IC| ≥ 0,005, BH q ≤ 0,10 (procédure de Benjamini-Hochberg, contrôle du taux de fausses découvertes) sur la liste gelée, ≥ 70 % des 10 marchés de même signe, IC poolé sur marchés « jamais vus » > 0.
- **Nouveau** = composite/symbolique ET IC partiel vs primitives brutes ≥ 0,003 (p < 0,10). **Non redondant** = |corr| < 0,8 sur validation avec les features déjà retenues. **Invariant** = STABLE et Q de Cochran p ≥ 0,05 et les deux moitiés de la période positives.
- **Consensus entre graines** : une feature doit être choisie dans ≥ 3 graines sur 5 et stable dans la majorité de ses apparitions (`analyze.py::consensus`).
- Validité : rappel des composites plantés ≥ 0,6 et ≤ 1 fausse découverte par run ; sous la nulle, moyenne de features stables ≤ 0,5.
- **Règles de verdict** : REFERENCE_SUPPORTED si ≥ 3 features **nouvelles, non redondantes**, stables, et complexité justifiée ; **LIMITED_STABLE si ≥ 1 feature non redondante stable (composite ou primitive)** ; NO_STABLE_NEW si 0 ; INCONCLUSIVE si validité échoue.
- **Complexité justifiée** : gain de R² OOS de l'ensemble découvert sur le ridge brut > 0 avec borne basse de l'IC 90 % du bootstrap apparié > 0 ET amélioration sur une majorité de marchés.

> Remarque essentielle déjà visible ici : **les deux règles de verdict ne mesurent pas la même chose**. R1 déclenche `LIMITED_STABLE` dès qu'**une** formule est *stable* (même si elle est redondante et inutile). R2 ne le déclenche que si la formule est *stable ET non redondante*. Appliquée à la même formule, la règle de R2 donnerait `NO_STABLE_NEW_FEATURES`. R1 le reconnaît (`09_ADJUDICATION.md` : « Une lecture stricte … donnerait NO_STABLE_NEW_FEATURES »). Voir §8.

---

## 3. Résultats détaillés

### 3.1 Run 1 — rapport par rapport

#### 3.1.1 Rapport 04 : sélection parcimonieuse, stabilité (train + validation seulement)

Stability selection : lasso randomisé, sous-échantillons de blocs de 336 barres, π = 0,7 (seuil de fréquence), q̄ ≤ 6 variables par tirage ; la borne théorique E[V] (espérance du nombre de fausses sélections) vaut ≈ 3,46, ce que le rapport juge « peu informative avec p = 26 » (✔ `stab_EV_bound = 3.46` dans `results/discovery_train_val.json`).

Fréquences moyennes de sélection sur 5 graines (✔ `consolidation.stab_mean`, tableau `results/tables/sparse.md`) :

| Cible | Primitive | Fréquence moyenne | Marchés (sur 4) à freq ≥ 0,7 seuls | Retenue |
|---|---|---|---|---|
| y_ret | mag_24 | 0,63 | 0 | non |
| y_ret | lrv_24 | 0,51 | 0 | oui (via CMI, pas via stabilité) |
| y_ret | lrng_1 / ret_168h | 0,42 | 0 | non |
| y_ret | mag_168 | 0,40 | 0 | non |
| y_vol | lrv_24 | **1,00** | 4 | oui |
| y_vol | lrv_168 | **1,00** | 4 | oui |
| y_vol | lvol_1 | 0,76 | 1 | oui (au pool seulement) |
| y_vol | dhi_72 | 0,44 | 1 | non |

Lecture simple : pour prédire le rendement (`y_ret`), aucune primitive n'est choisie de façon fiable (aucune ≥ 0,7). Pour prédire la volatilité (`y_vol`), la volatilité passée (`lrv_24`, `lrv_168`) est choisie à chaque fois : c'est la propriété bien connue « la volatilité persiste et revient à sa moyenne ».

Information mutuelle conditionnelle gaussienne : ne sélectionne que `lrv_24` (y_ret, 3 graines sur 5 : 11, 41, 37 avec d'autres) et `lrv_24`+`lrv_168` (y_vol, 5 graines sur 5) (✔ `consolidation.cmi_count`). L'estimateur kNN de MI est jugé trop bruité (IC ≈ 0,01) pour décider.

Modèle additif vs interactions (validation, GBM profondeur 1 vs 3) (✔ `results/diagnostics_train_val.json`, `tables/gbm_val.md`) :

| Cible | Profondeur | IC validation | R² validation |
|---|---|---|---|
| y_ret | 1 (additif) | +0,0116 | +0,082 % |
| y_ret | 3 | +0,0173 | −0,223 % |
| y_vol | 1 | +0,5145 | +24,393 % |
| y_vol | 3 | +0,5710 | +32,352 % |

Sens : sur `y_vol`, autoriser des interactions gagne +0,057 d'IC : il existe de la structure non additive ; sur `y_ret` rien d'exploitable (R² négatif).

#### 3.1.2 Rapport 03 : régression symbolique (GP)

Configuration (✔ code `fd/symbolic.py`, `fd/pipeline.py::Cfg`) : gplearn 0,4,3 ; population 300 ; 10 générations ; tournoi 15 ; parcimonie 0,004 ; fonctions add, sub, mul, div protégée, abs, neg, max, min, tanh ; profondeur d'initialisation 2–4 ; constantes ∈ [−1, 1] ; 5 graines ; 20 000 lignes échantillonnées ; top-6 programmes de la dernière génération (≤ 15 nœuds) ; simplification gloutonne ; puis gate.

Résultats par graine (✔ recoupés avec `discovery_train_val.json` ; `tables/seeds.md`). Colonnes : marchés « CMI », interactions passant la nulle par décalage circulaire, celles passant aussi la validation, programmes GP, GP après filtre trivial, GP passant la validation, retenus (non redondants).

| Cible | Graine | CMI | Inter. nulle | …validation | GP | GP filtré | GP validé | Retenus |
|---|---|---|---|---|---|---|---|---|
| y_ret | 11 | lrv_24 | 5 | 5 | 6 | 1 | 1 | 3 |
| y_ret | 23 | — | 8 | 5 | 6 | 0 | 0 | 3 |
| y_ret | 37 | lrv_24, ret_24h, mag_24, ret_4h | 0 | 0 | 6 | 0 | 0 | 0 |
| y_ret | 41 | lrv_24 | 3 | 3 | 6 | 2 | 2 | 4 |
| y_ret | 59 | — | 3 | 3 | 6 | 3 | 3 | 5 |
| y_vol | 11 | lrv_24, lrv_168 | 8 | 8 | 6 | 1 | 1 | 4 |
| y_vol | 23 | lrv_24, lrv_168 | 8 | 5 | 6 | 0 | 0 | 3 |
| y_vol | 37 | lrv_24, lrv_168 | 8 | 3 | 6 | 0 | 0 | 1 |
| y_vol | 41 | lrv_24, lrv_168 | 8 | 5 | 6 | 1 | 1 | 4 |
| y_vol | 59 | lrv_24, lrv_168 | 8 | 5 | 6 | 1 | 1 | 3 |

Constats :
- Aucune famille GP n'est retrouvée dans ≥ 60 % des graines → `SYMBOLIC_EXPRESSIONS_STABLE = 0` (✔).
- Sur `y_vol`, les meilleurs programmes GP ont un IC de validation de 0,40 à 0,50 : `sub(lvol_24, sub(lsz_1, lrv_24))` (0,403), `sub(neg(wknd), lrv_24)` (0,496), `sub(lnt_1, add(lvol_1, lrv_24))` (0,471) (✔ `discovery_train_val.json › seeds[].selected`). Ce sont des **combinaisons linéaires** dont le cœur est `−lrv_24` (moins la log-volatilité récente). Ils n'ont pas été gelés car leurs formes varient d'une graine à l'autre.
- Puissance du GP dans l'arène : composante non linéaire pure retrouvée dans **27,5 %** des 40 réplications MIXED (✔ recalculé : 11/40).
- Effet propre de la simplification gloutonne : non isolé par ablation (UNKNOWN, dit le rapport).

#### 3.1.3 Rapport 05 : interactions, formules gelées, held-out

Recherche exhaustive : 26 primitives → 325 paires × 3 formes (`a·b`, `a·sgn(b)`, `b·sgn(a)`) = 975 candidats par graine et par cible ; corrélation partielle après effets principaux ; seuil = quantile 95 % du maximum sous 50 décalages circulaires de la cible ; même signe sur les 4 marchés de découverte (✔ `fd/interactions.py`, `n_null=50, q=0.95`). Attention : le nombre de pairs est calculé sur `pool` = ensemble des 26 noms (`inter_screen(..., list(names), mains, ...)`) ; les mains servent seulement de contrôles.

Formules gelées (✔ `results/FROZEN.json`, `discovery_train_val.json`, `tables/frozen.md`) :

| Cible | Id | Expression | Type | Nœuds | Fréq. graines | IC train (brut) | IC val (signé, moy. 4 marchés) | p boot val | IC partiel val vs ridge des mains | Signe fixé sur train |
|---|---|---|---|---|---|---|---|---|---|---|
| y_ret | C01 | `mul(ret_24h, wknd)` | interaction | 3 | 0,6 (3/5) | −0,0422 | +0,0301 | 0,0033 | +0,0158 | −1 |
| y_vol | C01 | `mul(ret_72h, sgn(mag_168))` | interaction | 4 | 1,0 (5/5) | −0,0777 | +0,1227 | 0,0033 | **−0,0665** | −1 |

`ret_24h` = log(C_t/C_{t−24}) ; `wknd` = 1 si samedi/dimanche ; `ret_72h` = log(C_t/C_{t−72}) ; `mag_168` = log C_t − log(moyenne des 168 dernières clôtures) ; `sgn` = signe (−1, 0, +1). « Signe fixé sur train : −1 » signifie que la valeur de la feature est multipliée par −1 avant d'être utilisée (sinon l'IC train est négatif). Donc la feature *réellement utilisée* pour `y_vol` est **−ret_72h × sgn(mag_168)** (voir §4 et §8.3).

Résultats held-out, lecture unique (✔ recoupés avec `results/heldout_results.json`, `tables/heldout_candidates.md`) :

| Cible | Id | IC val | **IC held-out** | IC 90 % (bootstrap) | Marchés IC>0 | Jamais vus IC>0 | p brut | **p_Holm** | STABLE | IC partiel vs ridge brut | p_Holm partiel | NON-REDONDANTE | Classe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| y_ret | C01 | +0,0301 | +0,0120 | [−0,0038 ; +0,0277] | 9/9 | 5/5 | 0,1074 | **0,107** | non | +0,0079 | 0,431 | non | NONE |
| y_vol | C01 | +0,1227 | **+0,1043** | [+0,0729 ; +0,1364] | 9/9 | 5/5 | 0,0005 | **0,0010** | **oui** | **−0,0349** | 0,959 | **non** | PREDICTIVE |

Le p brut de `y_vol` (0,0004998) est le plancher du bootstrap à 2 000 tirages (1/2 001) : « 0,0005 » veut dire « aucun tirage sur 2 000 ne dépasse l'observé », pas une valeur précise. La famille gelée n'a que **2 tests** (une formule par cible), donc la correction de Holm est presque symbolique (facteur 2 sur le plus petit p) (✔ `family_size = 2`).

IC par marché en held-out (✔ vérifié par moi : recalcul indépendant depuis les données brutes, voir §6.4) :

| Cible | BTC | ETH | BNB | SOL | XRP | ADA | DOGE | LINK | PAXG |
|---|---|---|---|---|---|---|---|---|---|
| y_ret C01 | +0,014 | +0,016 | +0,001 | +0,002 | +0,017 | +0,022 | +0,018 | +0,013 | +0,004 |
| y_vol C01 | +0,082 | +0,118 | +0,118 | +0,112 | +0,097 | +0,130 | +0,081 | +0,104 | +0,097 |

Explication en mots : sur la cible « volatilité », la formule a un IC de +0,08 à +0,13 sur chacun des 9 marchés, y compris l'or tokenisé (PAXG) et les 5 actifs jamais vus. Sur le rendement, l'IC est positif partout mais minuscule (0,001 à 0,022) et non significatif après correction.

Corrélation partielle négative : une fois qu'on a retiré ce que le ridge sur les 26 primitives prédit déjà, ce qui reste de la formule est *anti*-corrélé à la cible (−0,035). En clair : la formule ne contient pas d'information nouvelle ; c'est une version moins bonne d'information déjà présente.

Cartes d'interprétabilité (✔ `tables/cards.md`) : ablations `y_vol C01` : neutraliser `mag_168` ou `ret_72h` fait perdre +0,1222 d'IC de validation (quasi tout, normal pour un produit) ; historique minimal requis 888 barres (168 + 720) ; modes de défaillance listés (saturation à ±5 écarts-types, estimée sur crypto spot 2021-2024, trous de données). Pour `y_ret C01` : historique minimal 744 barres, fragile au calendrier (UTC, week-end).

#### 3.1.4 Rapport 06 : stabilité (graines × marchés × temps × held-out)

Sélection des familles entre graines : y_ret 11 familles → 1 gardée (3/5 graines) ; y_vol 9 familles → 1 gardée (5/5) (✔ `consolidation.families_all/kept`).

Invariance (test Q de Cochran = « les pentes sont-elles les mêmes dans chaque environnement ? », erreurs robustes HAC décalage 48) (✔ `results/diagnostics_train_val.json`, `heldout_results.json`) :

| Cible | Id | Q p (16 envs marché×année, train+val) | Accord de signe | Q p (9 marchés held-out) | Accord de signe | ICP-lite : acceptés/testés |
|---|---|---|---|---|---|---|
| y_ret | C01 | 0,5028 | 0,625 (10/16) | 0,837 | 0,556 (5/9) | 0/42 |
| y_vol | C01 | **0,0004** | 1,00 | 0,861 | 1,00 | 0/8 |

Lecture : sur `y_vol`, le signe est le même partout (16/16 environnements, 9/9 marchés) mais l'**amplitude** de la pente varie fortement (pentes de 0,012 à 0,113 selon l'environnement, ✔ `betas`) : le test Q rejette l'homogénéité sur train+val. Sur les 9 marchés held-out, il ne rejette pas (p = 0,86) : cela est en partie de la puissance faible (les erreurs standard sont grandes) plutôt qu'une vraie homogénéité (INFERENCE).

Placebo réel : la cible held-out est décalée circulairement (même décalage pour tous les marchés, ce qui préserve l'alignement entre marchés), 20 fois ; part de tirages avec p brut < 0,05 (✔ `per_target.placebo_p_raw`) :

| Cible | Placebos | Part avec p < 0,05 | p minimum |
|---|---|---|---|
| y_ret | 20 | 0/20 = 0,00 | 0,086 |
| y_vol | 20 | 1/20 = 0,05 | 0,027 |

Compatible avec le niveau nominal 5 %, mais 20 tirages = résolution très faible (le rapport le dit).

#### 3.1.5 Rapport 04 (suite) : baselines held-out, lecture unique

Tableau complet (✔ intégralement recoupé avec `results/heldout_results.json › per_target.*.comparison`, `tables/heldout_models.md`) :

| Cible | Modèle | Params | IC poolé held-out | IC 90 % | R² OOS (moy. marchés) | découvert − ce modèle (moy., q10) |
|---|---|---|---|---|---|---|
| y_ret | raw_ridge | 26 | +0,0058 | [−0,0115 ; +0,0227] | −0,281 % | +0,0014 (q10 −0,0149) |
| y_ret | lasso | 20 | +0,0061 | [−0,0113 ; +0,0233] | −0,161 % | +0,0011 (−0,0150) |
| y_ret | tree_top8_ridge | 8 | −0,0019 | [−0,0199 ; +0,0148] | −0,109 % | +0,0092 (−0,0065) |
| y_ret | perm_top8_ridge | 8 | +0,0005 | [−0,0170 ; +0,0177] | −0,255 % | +0,0067 (−0,0095) |
| y_ret | gbm_full_ceiling | 1 200 | −0,0022 | [−0,0165 ; +0,0117] | −0,219 % | +0,0095 (−0,0051) |
| y_ret | **discovered** | 6 | +0,0068 | [−0,0111 ; +0,0257] | −0,074 % | — |
| y_vol | raw_ridge | 26 | **+0,5848** | [+0,5584 ; +0,6105] | +34,405 % | −0,0208 (−0,0282) |
| y_vol | lasso | 24 | +0,5851 | [+0,5586 ; +0,6111] | +34,444 % | −0,0210 (−0,0279) |
| y_vol | tree_top8_ridge | 8 | +0,5752 | [+0,5479 ; +0,6019] | +33,695 % | −0,0112 (−0,0159) |
| y_vol | perm_top8_ridge | 8 | +0,5784 | [+0,5514 ; +0,6048] | +33,834 % | −0,0143 (−0,0203) |
| y_vol | gbm_full_ceiling | 1 200 | +0,5948 | [+0,5680 ; +0,6202] | +35,963 % | −0,0306 (−0,0369) |
| y_vol | **discovered** | 11 | +0,5642 | [+0,5361 ; +0,5914] | +32,136 % | — |

Lecture simple :
- `y_ret` : toutes les méthodes, y compris le GBM à 1 200 paramètres, sont indistinguables de zéro (les intervalles contiennent 0, R² OOS négatifs). C'est le « résultat attendu » sur un rendement 4 h.
- `y_vol` : l'IC de 0,585 est énorme (la volatilité est très prévisible). Le modèle « découvert » (11 paramètres) fait *moins bien* que le ridge brut (−0,021), donc **la complexité n'est pas justifiée** (COMPLEXITY_JUSTIFIED = NO sur les deux cibles, ✔ `complexity_justified`). Le GBM plafond fait mieux de +0,010 : une petite non-linéarité subsiste, non capturée sous forme compacte.
- Le lasso garde 24 coefficients non nuls sur 26 pour `y_vol` : « parcimonieux » n'aide pas.
- Les importances (arbre, permutation) retiennent pour `y_ret` des variables que la stabilité n'a pas retenues (`ret_72h, mag_168, ret_1h, hod_cos, dlo_72`, ✔ `baseline_features`) : elles classent du bruit quand il n'y a pas de signal (INFERENCE).

#### 3.1.6 Rapport 07 : frontières causales

Classes de preuve (`fd/causal.py`) : `NONE` → `PREDICTIVE` (stable au held-out) → `INVARIANT_ASSOCIATION` (Q non rejeté sur les deux jeux d'environnements, signes identiques partout) → `CAUSAL_HYPOTHESIS` (+ ICP-lite l'inclut + mécanisme écrit) → `CAUSAL_IDENTIFIED` (seulement avec un objet « design » : intervention aléatoire, expérience naturelle ou instrument valide, p < 0,01 et réplication ≥ 7/8). Résultats réels : `C01_y_ret` = NONE, `C01_y_vol` = PREDICTIVE ; `CAUSAL_IDENTIFIED_COUNT = 0` (✔ `results/FINAL.json`).

Démonstration sur structures simulées à graphe causal connu (✔ `results/causal_boundaries.json`, `tables/causal.md`) :

| Structure | IC poolé | Q p | Accord signe | ICP accepté | ICP ∩ | effet do(X) | p do(X) | Classe (obs. seule) | Classe (+ design aléatoire) | X cause Y ? |
|---|---|---|---|---|---|---|---|---|---|---|
| A causale, envs décalés | +0,303 | 0,428 | 1,00 | 1/2 | [X] | +0,297 | 0,000 | CAUSAL_HYPOTHESIS | CAUSAL_IDENTIFIED | oui |
| B confondue, envs décalés | +0,186 | 0,000 | 1,00 | 2/2 | [] | −0,011 | 0,017 | PREDICTIVE | PREDICTIVE | non |
| B confondue, envs échangeables | +0,192 | 0,690 | 1,00 | 2/2 | [] | −0,000 | 0,949 | INVARIANT_ASSOCIATION | INVARIANT_ASSOCIATION | non |
| C causalité inverse, échangeables | +0,665 | 0,857 | 1,00 | 2/2 | [] | +0,002 | 0,701 | INVARIANT_ASSOCIATION | INVARIANT_ASSOCIATION | non |
| D confondant qui bascule | −0,002 | 0,000 | 0,50 | 2/2 | [] | −0,011 | 0,022 | NONE | NONE | non |

Sens : une feature « confondue » (qui ne cause rien) peut être aussi invariante et prédictive qu'une vraie cause (cas B échangeable et C). Seule une intervention distingue. Or les marchés crypto sont des environnements *échangeables et corrélés*. Donc l'invariance n'est qu'un critère de robustesse prédictive, pas une preuve causale.
Note sur le cas B décalé : `do(X)` a p = 0,017 alors que l'effet vrai est nul (−0,011) : un faux positif à 1,7 % ; le rapport a durci la règle du design (p < 0,01 et réplication) après un premier faux positif à 5 % (déviation n°4).

#### 3.1.7 Rapport 08 : falsification (arène)

Résultats (✔ recalculés par moi depuis `results/synthetic_arena_final.json` : 40 NULL, 40 MIXED, graines 1000–1039) :

| Métrique | Valeur |
|---|---|
| Réplications NULL / MIXED | 40 / 40 |
| FWER sous H0 (≥ 1 formule stable) | **0/40 = 0,000** (borne haute unilatérale 95 % de Clopper-Pearson = 1 − 0,05^{1/40} = 0,072) |
| Formules gelées sous H0 | 0/40 |
| « Mains » faux positifs sous NULL (variable de bruit retenue par stability selection) | 6/40 = **0,150** (graines 1002, 1013, 1028, 1031, 1035, 1036) |
| Idem sous MIXED | 4/40 = 0,10 |
| Puissance composante linéaire (via mains f00 ou f06) | 1,000 |
| Puissance interaction pure | 1,000 |
| Puissance non-linéaire pure `(z₃²−1)` | **0,275** |
| Composante spécifique à des marchés déclarée stable | 0,000 |
| Composante décroissante déclarée stable | 0,000 |
| Faux stables par réplication MIXED | 0,025 (1/40 : graine 1020, `max(f00, f04)`) |
| Formules gelées / stables par réplication MIXED | 3,2 / 3,2 |
| Doublon quasi identique sélectionné avec son jumeau | 1/40 = 2,5 % |
| Arène valide (FWER ≤ 0,10 et puissance linéaire ≥ 0,80) | **True** |

Tests de sécurité anti-lookahead (`tests/test_forward_safety.py`, 5 tests, ✔ je les ai relancés : `5 passed in 2.72s`) : invariance au préfixe, invariance au brouillage du futur, |corr(feature, cible)| < 0,1, évaluateur d'expressions, ordre et embargo des splits.

#### 3.1.8 Rapports 09 et 10

Adjudication (méthode par méthode) : voir §4. Limites (13 points) : voir §7 où je les confronte aux faits.

### 3.2 Run 2 — rapport par rapport

#### 3.2.1 Rapport 00 / 06 : découverte sur données réelles (5 graines)

Chiffres par graine (✔ `results/summary.json › real.per_seed_counts`, `results/real/run_*.json`) :

| Graine | Candidats découverts (dédupliqués) | Passent la validation | Liste finale | Stables held-out | Clusters GP « stables » (≥ 3 graines GP) |
|---|---|---|---|---|---|
| 11 | 18 | **0** | 0 | 0 | 3 |
| 12 | 20 | 0 | 0 | 0 | 2 |
| 13 | 19 | 0 | 0 | 0 | 4 |
| 14 | 22 | 0 | 0 | 0 | 2 |
| 15 | 20 | 0 | 0 | 0 | 2 |
| Total | 99 (80 distincts ✔) | 0 | 0 | 0 | 13 |

Vérification : 80 expressions distinctes (clés uniques), 99 au total (✔ recalculé). Le chiffre « FEATURES_DISCOVERED=80 » est donc un compte de **candidats avant validation**, pas de features retenues (il faut bien le distinguer du « 2 » de R1, qui compte des formules gelées).

Provenance des candidats par graine (✔ `provenance`) : 10 issues du top-10 MI par graine (50 au total), 1 à 2 issues de la CMI (8 au total), 0 issue de la stability selection, 7 à 11 issues de clusters GP (« SYM_ANY »). Nombre de types de candidats par graine : 6 à 9 « gated » (`a·|b|`), 7 à 11 « sym », 1 à 3 « prod », 0 à 2 « prim » (✔).

**Ce que sont les 13 « clusters symboliques stables »** (✔ recalculé depuis `sym_all`, colonne 3 = nombre de graines GP ≥ 3) : **10 sur 13 sont une seule primitive** (`vol72`, `ma72`, `r72`, `clp`, `rng24`, `vol24`), 1 nœud ; seuls 3 sont de vrais composites : `max(vol72, ma72)` (graine 11, 4 graines GP), `sub(clp, max(vol72, r72))` (graine 13, 4 graines GP), `sub(add(ma72, vol72), clp)` (graine 13, 3 graines GP). Or le rapport 03 décrit ces expressions stables comme « des réarrangements peu profonds de primitives volatilité/tendance, par ex. `max(vol72, ma72)`, `add(vol72, r72)`, `sub(clp, max(vol72, r72))`, `add(ma72, max(vol72, ma72))`, `max(vol72, r72)` ». Vérification : `add(vol72, r72)` n'est vu que par **1** graine GP, `add(ma72, max(vol72, ma72))` par **2**, `max(vol72, r72)` par **2** → elles ne sont **pas** « stables » au sens du rapport lui-même (≥ 3). ✘ écart mineur de description (le résultat, aucune expression ne passe la validation, n'est pas affecté).

Meilleurs candidats en validation (✔ `real/run_*.json › discovered`) :

| Expression | IC train | IC val | p val (bilatéral) | Accord de signe | Verdict du gate |
|---|---|---|---|---|---|
| `sym:vol72` (une primitive trouvée par GP) | +0,0284 | **+0,0301** | 0,191 / 0,197 / 0,236 / 0,262 / 0,237 (selon graine) | 6/6 | non (p > 0,10) |
| `gate:(r4*|vol72|)` | +0,006 | +0,024 | 0,132 | 6/6 | non |
| `gate:(vol72*|r12|)` | +0,0223 | +0,0211 | 0,241 | 5/6 | non |
| `sym:r4` | +0,0076 | +0,0205 | 0,263 | 6/6 | non |
| `sym:sub(add(ma72, vol72), clp)` | +0,0507 | +0,0195 | 0,281 | 5/6 | non |
| `prod:(trd*ma72)` | +0,0174 | +0,019 | 0,248 | 5/6 | non |
| `sym:max(vol72, ma72)` | +0,0459 | +0,0138 | 0,477 | 4/6 | non |

Moyenne sur les 99 lignes : IC train = +0,0243, IC validation = **−0,0043** (✔ recalculé) : ce qui a l'air bon en train s'effondre en validation, signature du surajustement de la recherche (INFERENCE).
Le rapport 03 dit : « every other candidate had IC_val ≤ 0.02 and p ≥ 0.13, or ≤ 83 % sign agreement » : `gate:(r4*|vol72|)` a IC_val = 0,024 (p = 0,132, 6/6), donc légèrement au-dessus du « ≤ 0,02 » annoncé. ✘ écart mineur (arrondi de rédaction).
Observation : pour la même expression (`vol72`), la valeur p varie de 0,19 à 0,26 selon la graine, uniquement à cause du hasard du bootstrap à 200 tirages : la porte de validation a un bruit propre (INFERENCE).

Stability selection : λ choisi pour ≥ 10 coefficients non nuls sur le train, α = 0,0177 à 0,0252 (✔ `stab_alpha`) ; 60 sous-échantillons de 50 % de blocs de 240 barres ; seuil 0,6 ; **0 sur 590 candidats sélectionné dans aucune graine** (✔ aucun `STABSEL` dans `provenance`). Seuil CMI : 2,25e−4 nats (✔ `cmi_thr = 0.000225`).

#### 3.2.2 Rapport 04 : baselines held-out (identiques entre graines car indépendantes de la graine)

(✔ `results/summary.json › real.perf`) R² « zéro-benchmark » = 1 − SSE/Σy² (le modèle de référence prédit 0) :

| Modèle | R² poolé 10 marchés | Marchés de découverte | Marchés jamais vus | IC poolé |
|---|---|---|---|---|
| B1 ridge, 20 primitives (α = 10 000) | −0,0020 | −0,0015 | −0,0028 | +0,0053 |
| B2 LassoCV (6 coefficients non nuls) | −0,0005 | +0,00003 | −0,0014 | +0,0113 |
| B3 top-5 par importance d'arbre → ridge (ma72, rng24, vol24, vol72, r72) | −0,0022 | −0,0017 | −0,0029 | +0,0033 |
| B4 top-5 par permutation → ridge (ma72, trd, vol24, rng24, vol72) | −0,0020 | −0,0015 | −0,0027 | +0,0055 |
| B5 HistGB, 20 primitives | −0,0055 | −0,0047 | −0,0067 | +0,0166 |

R² par marché de B1 : de −0,0047 à +0,0012 (✔ liste `[-0.0024,-0.0047,-0.0043,+0.0012,+0.0003,+0.0010,-0.0010,-0.0030,-0.0037,-0.0037]`). Le rapport note que l'IC positif de B5 (0,0166) avec un R² négatif suggère un signal de rang non calibré en amplitude (INFERENCE ; non testé statistiquement, sans coûts).
Le calcul « complexité » du protocole ne peut pas être mené : la liste finale est vide, donc `results.complexity = {}` (✔ `summary.json › real.complexity` vide).

Point important de comparaison : sur le rendement 4 h, R1 et R2 obtiennent des résultats **cohérents** pour le ridge brut : IC held-out +0,0058 (R1, 9 marchés, 20 mois) vs +0,0053 (R2, 10 marchés, 8 mois). Ils disent la même chose : il n'y a presque rien de linéaire à prendre.

#### 3.2.3 Rapport 05, 03, 04 (stabilité de sélection) — synthétique et nulle

**Arène synthétique (6 graines 7001–7006)** (✔ `summary.json › synth`) : les deux composites plantés (`f1*f2` et `f3*|f4|`) sont retrouvés dans **12/12** cas (rappel moyen 1,0), 0 fausse découverte, liste finale de 2 dans les 6 runs, 2 stables non redondantes ; R² test : ridge brut 0,0072–0,0113, LassoCV 0,0074–0,0114, GBM 0,0091–0,0134, ensemble découvert (brut + 2 composites) 0,0120–0,0181 (✔ le rapport 04 dit les mêmes fourchettes). Invariance : `f1*f2` invariant dans **4/6** (graines 7001, 7002, 7003, 7005), `f3*|f4|` dans 0/6 (Q p ≈ 0 : amplitude variable ±30 % par marché) (✔).
Le piège `f5` (signe qui bascule par marché) n'est retenu dans aucun run, mais le rapport reconnaît que le piège est **non informatif** : `f5` étant une primitive brute déjà dans la baseline, elle ne peut pas être déclarée « nouvelle ».
Le rapport 05 précise que la force du β a été choisie après un run de fumée sur la graine synthétique 1 (déviation n°1), donc « 12/12 » est une démonstration de puissance à un niveau d'effet choisi.

**Nulle (8 graines 901–908)** : cible décalée circulairement (`panels.py::null_panel`) ; par run : découverts 21, 20, 22, 23, 16, 23, 22, 21 ; passent la validation 1, 0, 0, 0, 1, 1, 1, 1 (total **5** ✔ conforme au rapport 05) ; liste finale 0 ; stables held-out 0 sur 8 (✔) ; moyenne 0,0 ≤ seuil 0,5.
Détail non signalé par le rapport : dans `null_panel`, **chaque marché reçoit un décalage aléatoire différent** (`for m in range(y.shape[1]): y[:, m] = np.roll(...)`). Donc la nulle détruit aussi l'alignement temporel *entre marchés* de la cible, alors que dans le vrai marché les cibles de BTC, ETH… sont fortement corrélées entre elles. Le bootstrap "temps partagé entre marchés" est censé refléter cette dépendance ; sous cette nulle la dépendance transversale n'existe plus, ce qui rend la nulle **plus facile à passer** que la réalité (INFERENCE : une nulle qui décalerait tous les marchés du même décalage, comme le fait le placebo de R1, serait plus exigeante).

#### 3.2.4 Rapport 07 / 08 / 09 / 10

Les rapports 07 (frontières causales, tableau de classes, règle de langage « associé à »), 08 (falsification) et 09 (adjudication) sont des textes courts qui reprennent les nombres ci-dessus. Aucun chiffre nouveau non recoupé. Tests : `tests/test_isolation.py`, 6 tests, annoncés « 6 passed » (PR #20) ; je ne les ai pas rejoués tous dans leur version d'origine mais voir §6 et §9 pour ce que j'ai rejoué.

---

## 4. Candidats et méthodes évalués un par un

### 4.1 Les candidats-features (verdict propre à chaque formule)

| Candidat | Run | Cible | Verdict (mon équivalent ADOPT/ADAPT/PARK/REJECT) | Justification chiffrée | Ce qui changerait le verdict |
|---|---|---|---|---|---|
| `−ret_72h·sgn(mag_168)` (C01 y_vol) | R1 | y_vol | **PARK** comme « feature » ; **REJECT** comme apport au-delà des baselines | IC held-out +0,1043 (9/9 marchés) mais IC partiel vs ridge −0,0349 (p_Holm 0,959) ; le modèle qui l'inclut fait −0,021 d'IC de moins que le ridge brut (q10 −0,028) | Preuve qu'un modèle non linéaire (GBM plafond +0,010) capture cette structure en forme compacte ; ou un test sur une cible non mécanique |
| `ret_24h·wknd` (C01 y_ret) | R1 | y_ret | **REJECT** | IC +0,0120, p_Holm 0,107 (non stable), IC partiel +0,0079 (p_Holm 0,431) | Confirmation sur une autre fenêtre avec p corrigé < 0,05 ; l'effet week-end est pré-enregistré comme hypothèse a priori |
| `vol72` (primitive, quasi-candidat) | R2 | y | **REJECT / PARK** (near-miss) | IC val +0,0301, p bilatéral 0,19–0,26, 6/6 marchés ; ne franchit pas 0,10 | Plus de données de validation (puissance) ; le rapport le classe `NOT_STABLE` |
| Clusters GP stables (13) | R2 | y | **REJECT** | 10 sur 13 sont des primitives seules ; 0 franchit la validation ; IC train 0,04–0,05 → val 0,01–0,02 | — |
| Interactions `a·|b|` / `a·b` (590 dans la bibliothèque) | R2 | y | **REJECT** (sur ces primitives/fenêtre) | 0 passe la validation sur 5 graines ; 5 passages sous la nulle | Fenêtre plus longue ; autres primitives |
| Composites plantés `f1*f2`, `f3*|f4|` | R2 | synthétique | démonstration de méthode | rappel 12/12, 0 fausse découverte | — |

### 4.2 Les méthodes (adjudication propre à chaque run)

**R1** (`reports/015_feature_discovery/09_ADJUDICATION.md`, reproduit ; ✔ cohérent avec les chiffres) :

| Méthode | Décision R1 | Raison (preuve) | Mon commentaire |
|---|---|---|---|
| Protocole gelé + verrou held-out + marchés jamais vus + Holm sur la famille | **ADOPT** | seul dispositif qui rende le faux positif mesurable (FWER 0/40) | Justifié, mais le Holm porte sur 2 tests seulement ; la valeur est le gel et le verrou |
| Nulle par décalage circulaire du max (interactions, CMI) | **ADOPT** | contrôle de la multiplicité sans hypothèse i.i.d. | Bon choix ; vérifié dans le code (`shift_null`, `interactions.screen`) |
| Stability selection (blocs) + lasso | **ADAPT** | trouve les mains stables ; borne E[V] non fiable sous dépendance | 15 % de faux « mains » sous NULL (✔) confirme |
| CMI gaussienne / orthogonalisation | **ADAPT** | ajouter un gate de nouveauté vs baseline | Le manque de gate de nouveauté est exactement ce qui a laissé passer C01 y_vol |
| Recherche exhaustive d'interactions | **ADAPT** | 100 % de puissance dans l'arène ; ne pas juger sans test partiel vs baseline | Puissance mesurée sur une interaction plantée forte (§7) |
| Régression symbolique GP | **PARK** | 27,5 % de puissance non-linéaire pure ; 0 expression stable | Cohérent avec R2 (GP n'a rien apporté non plus) |
| Importance d'arbre / permutation pour la sélection | **PARK** | classe du bruit quand pas de signal | ✔ (`baseline_features`) |
| Cochran-Q inter-marchés | **ADAPT** | diagnostic de robustesse, pas d'identification | OK |
| ICP-lite | **PARK** | 0 sous-ensemble accepté ; hypothèses violées | OK |
| Affirmations causales sans design | **REJECT** | cas B échangeable et C imitent A | ✔ |

**R2** (`09_ADJUDICATION.md`) : donne un verdict de processus plutôt qu'un tableau par méthode : « Recommended as a reference design for a local evaluation (ADAPT as protocol; nothing here is code to integrate) » ; ne soutient aucune formule, ni l'idée que la GP apporte de la valeur (« it did not, even on known truth »). Équivalents : protocole (MI/CMI → orthogonalisation → stability selection → gate → BIC → gel) = **ADAPT** ; GP = **PARK** (implicite) ; formules = aucune retenue.

Conditions de changement de verdict communes (INFERENCE) : (i) une cible autre que le rendement 4 h vol-scalé ; (ii) plus de primitives (carnet d'ordres, funding, OI, macro : cités par les deux limites) ; (iii) fenêtre plus longue pour R2 ; (iv) gate de nouveauté avant gel pour R1.

---

## 5. Bloc final complet et explication clé par clé

Reproduit tel quel de R1 (`reports/015_feature_discovery/09_ADJUDICATION.md`) :

```
FEATURES_DISCOVERED=2
FEATURES_HELDOUT_STABLE=1
SYMBOLIC_EXPRESSIONS_STABLE=0
NONREDUNDANT_FEATURES=0

CAUSAL_IDENTIFIED_COUNT=0

COMPLEXITY_JUSTIFIED=NO

FINAL_VERDICT=LIMITED_STABLE_FEATURES_SUPPORTED
```

Reproduit tel quel de R2 (`reports/015_feature_discovery/09_ADJUDICATION.md`) :

```
FEATURES_DISCOVERED=80 distinct pre-validation candidates over 5 seeds (18/20/19/22/20 per seed)
FEATURES_HELDOUT_STABLE=0
SYMBOLIC_EXPRESSIONS_STABLE=0
NONREDUNDANT_FEATURES=0
CAUSAL_IDENTIFIED_COUNT=0
COMPLEXITY_JUSTIFIED=NO
FINAL_VERDICT=NO_STABLE_NEW_FEATURES
```

Explication ligne par ligne, avec la **définition propre à chaque run** (elles diffèrent) :

| Clé | Sens dans R1 | Sens dans R2 | Piège de lecture |
|---|---|---|---|
| `FEATURES_DISCOVERED` | nombre de **familles gelées** après validation + consolidation entre graines, sur les deux cibles : 2 (1 par cible) | nombre d'**expressions distinctes générées avant validation** (80 sur 99 lignes) | **Ne sont pas comparables** : 2 vs 80 ne signifie pas « R2 a plus cherché ». R1 a évalué bien plus (975 interactions × 5 graines × 2 cibles, screenées) ; c'est le point de comptage qui diffère. Pour R2, l'équivalent de « 2 » est **0** (liste finale vide). |
| `FEATURES_HELDOUT_STABLE` | formules gelées qui passent les critères STABLE au held-out (p_Holm < 0,05, ≥ 75 % des marchés, majorité des jamais-vus) : 1 (y_vol C01) | idem sur liste gelée vide : 0 | R1 = 1 est le seul point de désaccord entre les deux runs. |
| `SYMBOLIC_EXPRESSIONS_STABLE` | formules STABLE issues du GP : 0 | idem : 0 (aucune expression GP ne passe la validation) | Accord. |
| `NONREDUNDANT_FEATURES` | STABLE et corrélation partielle vs ridge brut significative : 0 (IC partiel y_vol −0,035) | STABLE, non redondante (|corr| < 0,8 sur validation) ; dans `analyze.py` c'est `n_nonred`, distinct de `new` (IC partiel ≥ 0,003) | La définition de « non redondant » diffère : R1 = *apport incrémental significatif vs le ridge brut* (exigeant) ; R2 = *pas trop corrélé aux autres features retenues* (plus laxiste), l'apport incrémental étant exigé dans « nouveau ». |
| `CAUSAL_IDENTIFIED_COUNT` | 0 : aucun design identifié n'existe dans des données d'observation | 0 (même raison) | Accord ; c'est presque tautologique dans les deux. |
| `COMPLEXITY_JUSTIFIED` | NO : le modèle découvert ne bat aucune baseline non-plafond avec q10 > 0 (et 0 non redondante) | NO : « nothing retained to justify » | R2 : NO par absence d'objet, pas par test. R1 : NO par test. |
| `FINAL_VERDICT` | règle mécanique : arène valide, NON-REDONDANTES = 0 < 3, ≥ 1 formule STABLE (1) → `LIMITED_STABLE_FEATURES_SUPPORTED` | validité OK, 0 feature non redondante stable → `NO_STABLE_NEW_FEATURES` | Voir §8 : la différence de règle (« ≥ 1 stable » vs « ≥ 1 stable non redondante ») suffit à elle seule à inverser l'étiquette pour le cas de R1. |

Vocabulaire des verdicts (ordre croissant de force) : `STUDY_INCONCLUSIVE` (l'étude ne permet pas de conclure) < `NO_STABLE_NEW_FEATURES` (rien de stable et nouveau) < `LIMITED_STABLE_FEATURES_SUPPORTED` (au moins une feature stable, soutien limité) < `FEATURE_DISCOVERY_REFERENCE_SUPPORTED` (méthode de découverte de référence soutenue).

---

## 6. Contrôles de validité

### 6.1 Fuite / regard vers le futur (lookahead)

| Contrôle | R1 | R2 |
|---|---|---|
| Features calculées avec barres ≤ t | test de préfixe (`test_prefix_invariance`) : features à t calculées sur données ≤ t identiques à celles sur la série entière ; test de brouillage du futur (`test_future_perturbation`) — PROVEN par test, ✔ relancé : 5 passed | `test_features_are_causal` : recalcul sur série tronquée identique — PROVEN par test |
| Cible non dans les features | `test_target_uses_future_only_as_label` : |corr| max feature/y_ret < 0,1 | `test_target_not_in_primitives` (vérifie l'absence des colonnes `y`, `fwd_raw` dans `PRIMS`) |
| Splits ordonnés/disjoints/embargo | `test_split_ordering` : embargo ≥ 7 j | `test_splits_are_disjoint_and_ordered` : ≥ 24 barres |
| Held-out intact avant gel | verrou de fichier + digest recalculé | `access_order` + `test_heldout_untouched_before_lock` |
| Standardisation | fenêtre glissante passée de 720 barres, incluant t | fenêtre 500 barres, incluant t (statistiques ≤ t) |
| Un point à surveiller | `y_vol` : la cible contient `rv_past` = √(Σ r² sur 24 barres finissant à t), identique en substance à la primitive `lrv_24` : ce n'est pas du lookahead (la primitive est connue à t) mais une **identité mécanique** entre feature et dénominateur de la cible (voir §7.2) | `amh` utilise `lr.abs()` avec `quote_vol` de la même barre : connu à la clôture de la barre t |

### 6.2 Déterminisme et reproduction (mes propres recalculs)

- **R1 — reproduction complète de la découverte** : j'ai relancé `scripts/02_discovery.py` sur une copie jetable de la branche (versions : numpy 2.4.6, pandas 3.0.6, scipy 1.17.1, scikit-learn 1.9.1, gplearn 0.4.3, Python 3.11.15). Résultat : mêmes formules, mêmes IC de validation, et **digest de gel identique** `9f32094f0d93b292055750e18b7fd449910fd7129173ddcb47c116c1ce2d0666` (OBSERVED, sortie `FROZEN digest`). Le pipeline R1 est donc **déterministe bit à bit** sur la partie découverte, avec ces versions.
- **R1 — tests** : `pytest tests` → 5 passed en 2,72 s (OBSERVED).
- **R1 — held-out** rejoué après suppression du verrou dans ma copie : sorties identiques (IC, p, baselines, placebo). **R2 — découverte réelle** (5 graines) rejouée : sorties identiques, y compris l'empreinte de gel. Détails et durées : §9.

### 6.3 Contrôles négatifs / positifs

- **Négatif (nulle)** : R1 arène NULL 0/40 stables, 0/40 gelées ; placebo réel 0/20 et 1/20. R2 nulle décalée 0/8 stables (5 passages de la porte de validation sur ~170 candidats évalués, tous éliminés par le BIC).
- **Positif (vérité connue)** : R1 linéaire 100 %, interaction 100 %, non-linéaire 27,5 %. R2 12/12 composites.
- **Une asymétrie de taille** : R1 : 80 réplications ; R2 : 6 + 8 runs. La précision statistique sur le FWER est bien meilleure chez R1 (borne haute 7,2 % vs, pour R2, 0/8 ⇒ borne haute unilatérale 95 % ≈ 31 %, calcul mien : 1 − 0,05^{1/8} = 0,312).

### 6.4 Erreurs corrigées en cours de route et écarts au protocole déclarés

**R1** (`02_PROTOCOL.md §12`, 6 déviations, toutes avant le held-out) :
1. Un premier processus de découverte a démarré ~1 min avant que le commit du protocole n'aboutisse (le premier `git add` avait échoué). Aucun résultat consulté. Non vérifiable par moi (?), mais le commit de protocole précède tout fichier de résultat (✔ historique git).
2. Filtre « primitive triviale » ajouté après un premier passage (train/val) où `ret_1h` avait été « découverte » : la découverte a été relancée entièrement, seul le second passage est gelé.
3. Arène : puissance de la composante linéaire mesurée par les « mains » et non par les candidats (seuil inchangé). Le rapport dit « §9 modifié en conséquence » : ✘ la section 9 du fichier n'a pas été modifiée entre `c50e99c` et la version finale (seule la section 12 diffère) ; l'information est seulement dans les déviations.
4. Démo causale durcie (p < 0,01 et réplication ≥ 7/8) après un faux positif à 5 %.
5. **Gate de nouveauté non implémenté** : la corrélation partielle en validation est seulement rapportée ; conséquence : C01 y_vol passe la validation avec −0,067.
6. Résultats de développement de l'arène (graines 0–3) conservés.
Autre écart : l'en-tête du protocole dit « Toute déviation est listée en §11 », mais les déviations sont en §12 (§11 = classification causale) : ✘ erreur de renvoi, sans conséquence.

**R2** (`02_PROTOCOL.md` « Deviations disclosed », 3 déviations) :
1. Après un run de fumée sur la graine synthétique 1 (non rapporté), changement du diviseur d'effectif effectif (réel : 4 ; synthétique : 1) et de la taille/force synthétique (T = 19 000, β = 0,06) ⇒ β réglé sur une graine de fumée.
2. Test Q très sensible avec n_eff en milliers : `f3*|f4|` déclaré non invariant 6/6 malgré un signe constant.
3. Profils par déciles ajoutés au schéma de résultats après le début du batch synthétique (ne change aucune sélection).

### 6.5 Mes vérifications indépendantes (échantillon ≥ 10 chiffres clés)

| # | Chiffre du rapport | Source du contrôle | Statut |
|---|---|---|---|
| 1 | R1 : FINAL block (2/1/0/0/0/NO/LIMITED…) | `results/FINAL.json` | ✔ |
| 2 | R1 : IC held-out y_vol C01 = +0,1043 ; 9/9 marchés ; ICs par marché (0,082 … 0,130) | **recalcul indépendant** depuis `data/*.csv.gz` avec les modules `fd/` de R1 : BTC 0,0816, ETH 0,1179, BNB 0,1177, SOL 0,1123, XRP 0,0968, ADA 0,1300, DOGE 0,0811, LINK 0,1042, PAXG 0,0974, moyenne 0,1043 | ✔ |
| 3 | R1 : IC held-out y_ret C01 = +0,0120 (0,0141 … 0,0224) | même recalcul : BTC 0,0141, ETH 0,0156, BNB 0,0009, SOL 0,0021, XRP 0,0169, ADA 0,0224, DOGE 0,0184, LINK 0,0133, PAXG 0,0043, moyenne 0,0120 | ✔ |
| 4 | R1 : p_Holm y_vol 0,001 ; y_ret 0,107 ; partiel −0,0349 (p 0,959) | `heldout_results.json` | ✔ |
| 5 | R1 : baselines held-out (12 lignes) | `heldout_results.json` | ✔ (à 4 décimales) |
| 6 | R1 : arène FWER 0/40, puissances 1,0/1,0/0,275, faux mains 0,15 | recalcul depuis `synthetic_arena_final.json` | ✔ |
| 7 | R1 : Q p 0,5028 / 0,0004 / 0,837 / 0,861 ; accords de signe | `diagnostics_train_val.json`, `heldout_results.json` | ✔ |
| 8 | R1 : placebo 0/20 (min p 0,086) et 1/20 (min 0,027) | `per_target.*.placebo_p_raw` | ✔ |
| 9 | R1 : digest de gel `9f32094f…` | reproduction complète de la découverte | ✔ |
| 10 | R1 : données SHA-256 (9 fichiers) | recalcul `sha256` | ✔ |
| 11 | R2 : 80 candidats distincts ; 18/20/19/22/20 par graine | `real/run_*.json` | ✔ (99 lignes) |
| 12 | R2 : baselines B1–B5 (R², IC, marchés découverte/jamais vus) | `summary.json › real.perf` | ✔ |
| 13 | R2 : empreinte de gel `8c7a94b0…` identique | `summary.json`, `lock_*.json` | ✔ |
| 14 | R2 : synthétique 12/12, invariance 4/6 et 0/6 ; R² fourchettes | `summary.json › synth` | ✔ |
| 15 | R2 : nulle 0/8 stables ; 5 passages de validation | `summary.json › null` | ✔ |
| 16 | R2 : « 13 clusters stables » et description des expressions | `sym_all` | ✘ partiel (10/13 sont des primitives ; 3 expressions citées n'ont que 1 ou 2 graines) |
| 17 | R2 : « every other candidate IC_val ≤ 0.02 » | `discovered` | ✘ mineur (0,024 pour `gate:(r4*|vol72|)`) |
| 18 | R2 : SHA-256 des 10 fichiers | recalcul | ✔ |
| 19 | R1 : « §9 modifié » (déviation 3) | `git diff` protocole | ✘ mineur (non modifié) |
| 20 | R1/R2 : date/heures des commits, ordre gel → held-out | `git log` | ✔ |
| 22 | R1 : held-out (IC, p_Holm, baselines, placebo) | relance complète du script sur copie | ✔ identique |
| 23 | R2 : découverte réelle 5 graines (candidats, IC/p val, comptes, gel) | relance de `run_batch.py real` sur copie | ✔ identique |
| 21 | Rapports : positions de PR (#13 brouillon ouverte 18:12 ; #20 brouillon 18:57) | API GitHub (lecture des PR) | ✔ |

Aucun écart n'affecte un verdict.

---

## 7. Critique indépendante

### 7.1 Points communs aux deux runs (ce que les chiffres ne prouvent pas)

1. **Un seul type d'actif, un seul lieu, des marchés très corrélés.** Neuf ou dix paires crypto d'une seule plateforme. « 9/9 marchés positifs » ou « 5/5 marchés jamais vus » compte les marchés comme des votes quasi indépendants alors qu'ils bougent ensemble. Le bootstrap avec temps partagé corrige l'erreur standard, **pas** les règles de comptage (« ≥ 75 % des marchés », « majorité des jamais-vus »). Sur une cible de volatilité, où toutes les cryptos partagent les mêmes régimes, 9/9 est attendu (INFERENCE).
2. **Aucun coût, aucune exécution, aucun PnL.** Un IC de 0,01 à 0,02 n'a aucun sens économique établi. Les deux runs le disent.
3. **Puissance des arènes.** Elles montrent qu'un signal *fort* est retrouvé (IC planté ≈ 0,06–0,08, ordre de grandeur, mon calcul en §2.5), pas qu'un signal de l'ordre de 0,01–0,02 le serait. Aucune n'a de courbe de puissance (« minimum detectable effect ») ; R2 l'écrit expressément (`08_FALSIFICATION.md`, « Not done »), R1 non.
4. **Références bibliographiques citées de mémoire** (R1 le dit : DOCUMENTED_CLAIM) ; non vérifiées en ligne par les runs, ni par moi (je n'ai pas cherché à le faire).
5. **Un seul essai de GP par run, petit budget** (population 300, 8 à 10 générations). « GP n'a rien trouvé » ne prouve pas « rien à trouver » (R1 : puissance 27,5 % sur non-linéarité pure).
6. **Un seul horizon (4 h)** pour le rendement.

### 7.2 Run 1 — points faibles

**(a) La cible `y_vol` contient une identité mécanique avec une primitive (INFERENCE forte, appuyée sur le code lu).**
Dans `fd/features.py`, la primitive `lrv_24` vaut `ln( sqrt( Σ_{i<24} r_{t−i}² ) + 1e-9 )` (puis z-score glissant), et la cible `y_vol` vaut `ln(rv_fwd + 1e-9) − ln(rv_past + 1e-9)` avec `rv_past = sqrt( Σ_{i<24} r²)` finissant en t : c'est **la même quantité**, au z-score près. Donc `lrv_24` est, au signe et à la standardisation près, le « dénominateur » de la cible. Cela explique :
- l'IC de 0,585 du ridge brut (le rapport le reconnaît : « dominé par la persistance de la volatilité ») ;
- les IC de validation de 0,40 à 0,50 des programmes GP (`−lrv_24` déguisé) ;
- mon recalcul sur BTC held-out : Spearman(`lrv_24`, `y_vol`) = −0,514 (OBSERVED, mon calcul ; un seul marché).
Le rapport 10 (limite n°4) dit bien que `y_vol` est « un test de puissance, pas une découverte économique ». **Tension** : le verdict `LIMITED_STABLE_FEATURES_SUPPORTED` est *entièrement* porté par cette cible « de contrôle ».

**(b) La formule stable n'est pas « une magnitude de mouvement directionnel récent », c'est plutôt son opposé (OBSERVED sur un marché + INFERENCE).**
La feature utilisée est `−1 × ret_72h × sgn(mag_168)` (le signe −1 est fixé sur train). Quand `ret_72h` et `mag_168` ont le même signe (85 % des lignes sur BTC held-out, mon calcul), `ret_72h × sgn(mag_168)` vaut `|ret_72h|` ; la feature vaut alors `−|ret_72h|`. Mon recalcul BTC held-out : Spearman(feature, |ret_72h|) = **−0,925**. Lecture : *plus le mouvement des 72 dernières heures est petit (marché calme), plus la volatilité des 24 prochaines heures dépasse celle des 24 dernières* — c'est un indicateur de « calme avant la tempête » / retour de la volatilité à sa moyenne. Le rapport 00 écrit « proxy de magnitude de mouvement récent » sans indiquer le sens ; la carte du rapport 05 donne « signe −1 » sans commentaire. Cela ne change pas les chiffres, mais un lecteur pourrait comprendre le contraire.

**(c) Le filtre « primitive triviale » et l'absence de gate de nouveauté sont des ajouts après regard (déviations 2 et 5).**
Le premier avait été ajouté après avoir vu `ret_1h` « découverte » sur train/val ; le second n'a jamais été ajouté. L'asymétrie est parlante : on a filtré la redondance *univariée* (une primitive déguisée) mais pas la redondance *linéaire* (une combinaison de primitives). Résultat : C01 y_vol passe avec une nouveauté négative en validation (−0,067) et le rapport l'écrit lui-même. Il n'y a pas de tricherie (rien ne touche au held-out), mais la conception du filtre est dictée par ce qui a été vu.

**(d) La consolidation par fréquence de graines a sélectionné le moins bon candidat.**
Pour `y_vol`, les trois programmes GP à IC de validation 0,403 / 0,471 / 0,496 ont une nouveauté **positive** (+0,004, +0,101, +0,155 vs le ridge des mains) alors que la formule gelée a 0,123 et −0,067 (✔ `discovery_train_val.json › seeds[].selected`). La règle « famille retrouvée dans ≥ 60 % des graines » favorise la stabilité syntaxique (un produit simple retrouvé 5 fois) plutôt que la valeur prédictive. Ce choix était pré-enregistré ; il n'est pas faux, mais il explique que la seule formule gelée soit la moins utile (INFERENCE).

**(e) La famille de test du held-out est de taille 2.** La correction de Holm est donc presque un simple facteur 2. Le p brut de `y_vol` (0,0005) est le plancher du bootstrap (2 000 tirages). Le vrai contrôle du faux positif repose sur le gel et le verrou, pas sur le Holm.

**(f) « IC > 0 sur 9/9 marchés » et « 5/5 jamais vus »** : voir 7.1.1. Pour `y_vol`, l'erreur standard du test Q (HAC lag 48) est grande sur held-out ; la non-rejection (p = 0,861) informe peu (INFERENCE).

**(g) L'arène de R1** : bruit gaussien hétéroscédastique, features AR(1), cible indépendante des features sous H0 : elle ne reproduit pas le couplage volatilité/cible du vrai marché. Le FWER 0/40 est une mesure sur ce monde-là (le rapport 10, limite n°12, le dit). La puissance « composante linéaire = 100 % » est mesurée par la sélection des *mains* et non par les candidats (déviation 3). Les faux « mains » sous H0 sont à 15 % (6/40), ce qui montre que la borne théorique de la stability selection n'est pas tenue sous dépendance temporelle.

**(h) ICP-lite : 0 sous-ensemble accepté sur 42 et 8.** Un test qui n'accepte jamais n'est pas discriminant ; il est classé PARK à juste titre.

**(i) Écarts de rédaction** (mineurs, §6.4) : renvoi « §11 » au lieu de « §12 » ; « §9 modifié » non reflété dans le fichier.

**(j) Forces réelles à souligner (pour être juste).** Protocole commité avant les résultats et non modifié dans ses règles ; digest de gel vérifié dans le code ; verrou de re-run ; marchés jamais vus dans les vrais fichiers ; **déterminisme reproduit** (digest identique à la relance) ; adjudication honnête qui écrit noir sur blanc que la lecture stricte donne `NO_STABLE_NEW_FEATURES`.

### 7.3 Run 2 — points faibles

**(a) Puissance de la porte de validation trop faible (INFERENCE chiffrée à partir des p publiés).**
Pour `vol72`, IC_val = 0,0301 avec p bilatéral 0,191 (graine 11) à 0,262 (graine 14). On en déduit une erreur standard du IC poolé de ≈ 0,023 à 0,027 (z = IC/se ; p = 0,191 ⇒ z ≈ 1,31 ⇒ se ≈ 0,023 ; p = 0,262 ⇒ z ≈ 1,12 ⇒ se ≈ 0,027). Pour p < 0,10 bilatéral (z ≥ 1,645), il faut donc |IC| ≳ 0,038 à 0,044 sur la validation. Or les IC en jeu (y compris dans R1 sur le même type de cible) sont de l'ordre de 0,01–0,03. Le même calcul pour R1 : la formule `ret_24h·wknd` (IC val 0,0301) a p = 0,0033 (unilatéral) ⇒ z ≈ 2,72 ⇒ se ≈ 0,011 ; le seuil p < 0,10 unilatéral (z ≥ 1,28) correspond à |IC| ≳ 0,014. **La porte de R1 est environ 2,7 à 3 fois plus sensible que celle de R2** (mêmes ordres de grandeur d'erreur, validation 3,4 fois plus longue chez R1 et test unilatéral). Un candidat comme `ret_24h·wknd` (s'il existait dans la bibliothèque de R2) aurait échoué à la porte de R2 (p ≈ 0,2). Le rapport 08 avance « |IC| < ~0,02 indétectable » ; sur la validation c'est plutôt ≈ 0,04 (mon estimation).
Autre détail : la valeur p d'une même expression varie de 0,19 à 0,26 selon la graine seulement à cause du bootstrap (200 tirages), donc la porte est bruitée.

**(b) Une seule cible, la même que celle où R1 ne trouve rien.** Le rendement 4 h vol-scalé est celui pour lequel les baselines ont R² OOS ≤ 0 dans les deux runs. Un résultat nul était le résultat attendu ; le rapport écrit lui-même « Local evaluation should not expect free wins from these primitives » (`09_ADJUDICATION.md`). Le label `NO_STABLE_NEW_FEATURES` peut se lire « rien d'exploitable sur cette cible », pas « la méthode ne trouve jamais rien ».

**(c) Liste finale vide sur données réelles : aucune vérité de terrain sur le pipeline réel au held-out.** Le gel, le verrou et le test d'ordre d'accès restent valides mais ne protègent aucune formule. Il n'y a donc **aucune évidence held-out** sur les quasi-candidats (par exemple `vol72`) ; le rapport le classe `NOT_STABLE` d'après la seule validation.

**(d) Description inexacte des clusters symboliques stables (§3.2.1)** : 10 sur 13 sont une primitive seule, et trois des expressions citées comme « stables » ne le sont pas selon le seuil du rapport (≥ 3 graines GP). Le rapport 06 (« No expression reproduces with the same structure in all 5 seeds ⇒ symbolic stability LOW ») reste juste.

**(e) La nulle décale chaque marché différemment** (§3.2.3) : elle supprime la dépendance entre marchés, donc elle est plus facile à passer que la réalité (INFERENCE). Le rapport 06 signale une autre limite (« does not test predictors with volatility-clustering coupling ») mais pas celle-ci. Avec 8 nulles, la borne haute unilatérale 95 % sur le taux de faux positifs est ≈ 31 % (mon calcul), à comparer à 7,2 % pour R1.

**(f) Stability selection sur 590 candidats très colinéaires** (produits de volatilité avec des valeurs absolues, etc.) : quand plusieurs candidats sont interchangeables, le lasso en choisit un au hasard, la fréquence se dilue et n'atteint jamais 0,6 (INFERENCE ; 0/590 sélectionnés dans les 5 graines). Ce n'est donc pas une preuve d'absence de signal linéaire parcimonieux (les baselines lasso, avec 6 coefficients non nuls sur 20 primitives, donnent R² −0,0005).

**(g) Arène synthétique** : β réglé sur une graine de fumée (déviation 1) ; marchés synthétiques indépendants (la dépendance transversale qui motive le bootstrap à temps partagé n'est donc pas testée) ; piège `f5` non informatif (reconnu) ; le test Q rejette l'invariance de `f3*|f4|` dans 6/6 runs malgré un signe constant (reconnu). La « validité » est donc obtenue à un niveau d'effet choisi, pas démontrée en général.

**(h) « FEATURES_DISCOVERED=80 »** peut tromper : c'est un compte de candidats *avant* validation, sans lien avec « 2 » de R1 (§5).

**(i) Pièces hors-sujet** : 8 fichiers `.whl` (62,45 Mo) dans la PR (§0).

**(j) Forces réelles.** Protocole JSON verrouillé (un seul commit) ; `pipeline.py` figé avant les résultats ; tests d'isolation ; rapports courts mais chiffres cohérents avec les fichiers bruts (6 contrôles sur 8 de mon échantillon ✔, 2 écarts mineurs de description) ; le résumé indique clairement une force de verdict « MODERATE-LOW » et liste ses limites ; indépendance revendiquée (n'a pas lu R1).

### 7.4 Écarts entre rapports et résultats bruts, contradictions internes

| Élément | Où | Nature | Gravité |
|---|---|---|---|
| Expressions « stables » citées (`add(vol72, r72)` etc.) vues par 1 ou 2 graines GP seulement ; 10/13 clusters stables sont des primitives | R2 `03_SYMBOLIC.md`, `06_STABILITY.md` | ✘ description | faible |
| « IC_val ≤ 0,02 » pour tous les autres candidats ; 0,024 pour `gate:(r4*|vol72|)` | R2 `03_SYMBOLIC.md` | ✘ arrondi | très faible |
| « §9 modifié » | R1 `02_PROTOCOL.md §12.3` | ✘ non reflété dans le texte | faible |
| Renvoi « §11 » pour les déviations (c'est §12) | R1 `02_PROTOCOL.md` en-tête | ✘ renvoi | négligeable |
| Le verdict `LIMITED_STABLE…` accompagné de « rien à ajouter » | R1 `00`/`09` | tension interne assumée par le rapport | à connaître |
| « FEATURES_DISCOVERED » de sens différent | R1 vs R2 | définition | moyen pour la comparaison |
| Pas d'écart numérique constaté sur les tableaux principaux (baselines, blocs finaux, arènes, IC par marché) | les deux | ✔ | — |

---

## 8. Comparaison point par point des deux runs (section obligatoire)

### 8.1 En une phrase

> Les deux runs **s'accordent sur tout ce qu'ils ont mesuré en commun** (le rendement 4 h vol-scalé : rien de stable, aucune baseline au-dessus de zéro, GP inutile, causal = 0, complexité non justifiée). Ils **divergent uniquement sur l'étiquette finale**, et cette divergence vient de trois choses qui ne sont pas des contradictions de mesure : (1) R1 a testé une **deuxième cible** (la volatilité) où R2 n'a rien testé ; (2) leurs **règles de verdict** diffèrent (« au moins une formule stable » contre « au moins une formule stable *et non redondante* ») ; (3) leur **puissance statistique** diffère d'environ un facteur 3 à la porte de validation.

### 8.2 Tableau comparatif

| Question | Run 1 | Run 2 | Accord ? |
|---|---|---|---|
| Verdict final | `LIMITED_STABLE_FEATURES_SUPPORTED` | `NO_STABLE_NEW_FEATURES` | **non** |
| Formules stables au held-out | 1 (`−ret_72h·sgn(mag_168)` sur `y_vol`) | 0 (liste vide) | non (mais cible différente) |
| Formules non redondantes | 0 | 0 | **oui** |
| Expressions symboliques stables | 0 | 0 | **oui** |
| Identifications causales | 0 | 0 | **oui** |
| `COMPLEXITY_JUSTIFIED` | NO | NO | **oui** |
| GP utile ? | PARK (27,5 % de puissance, 0 stable) | rien retenu ; « adds nothing beyond a 2-operator library » | **oui** |
| Cible commune (rendement 4 h vol-scalé) : IC held-out du ridge brut | +0,0058 (IC 90 % [−0,0115 ; +0,0227]), 9 marchés, 20 mois | +0,0053, 10 marchés, 8 mois | **oui** (mêmes ordres de grandeur) |
| R² OOS du ridge brut sur cette cible | −0,281 % (moy. marchés, référence = moyenne train+val) | −0,20 % (référence = 0) | **oui** (mêmes signes, définitions de R² différentes) |
| Lasso : IC / R² | +0,0061 / −0,161 % | +0,0113 / −0,054 % | oui (signe et ordre) |
| Top-k par arbre : IC | −0,0019 (k = 8) | +0,0033 (k = 5) | oui (≈ 0) |
| Top-k par permutation : IC | +0,0005 (k = 8) | +0,0055 (k = 5) | oui (≈ 0) |
| GBM plafond : IC / R² | −0,0022 / −0,219 % | **+0,0166** / **−0,55 %** | **divergence légère** : IC de signe différent, R² plus mauvais chez R2 ; tout est dans le bruit (IC 90 % de R1 ≈ ±0,014) |
| Arène : fausses découvertes sous H0 | 0/40 (borne haute 7,2 %) | 0/8 (borne haute ≈ 31 %) | oui, précision très différente |
| Arène : puissance | linéaire 100 %, interaction 100 %, non-linéaire pure 27,5 % | 2 composites planqués (produit, porte) 12/12 | oui (cas différents) |
| Faux « mains » sous H0 | 15 % (6/40) | non mesuré | — |

### 8.3 Pourquoi les verdicts diffèrent — analyse précise

#### (1) Univers

| | R1 | R2 |
|---|---|---|
| Marchés | 9 : BTC, ETH, BNB, SOL (découverte) ; XRP, ADA, DOGE, LINK, PAXG (jamais vus) | 10 : BTC, ETH, BNB, SOL, XRP, ADA (découverte) ; DOGE, LINK, LTC, AVAX (jamais vus) |
| Communs | 8 marchés en commun (BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LINK), mais **XRP et ADA changent de rôle** (jamais vus chez R1, découverte chez R2) | |
| Spécifiques | PAXG (or tokenisé, seul non-crypto pur) | LTC, AVAX |
| Fenêtre | 2021-01 → 2026-08 (5,7 ans, 49 642 h) | 2024-05 → 2026-09 (2,3 ans, 20 000 h) |
| Train / val / held-out (h par marché) | 21 050 / 13 032 / ≈ 14 400 | 9 813 / 3 887 / 5 879 |
| Régimes vus à l'entraînement | 2021-02 → 2023-06 (marché haussier 2021, baissier 2022) | 2024-06 → 2025-07 |

Effet : R1 entraîne sur des régimes très variés et valide sur 13 000 h ; R2 tout sur 2,3 ans. Le held-out de R2 est *inclus* dans celui de R1 ; l'entraînement/validation de R2 recouvre le held-out de R1 (§2.2). Sur les mêmes mois, des données servent d'entraînement dans un run et de test dans l'autre. Ce n'est pas une réplication temporelle indépendante.

#### (2) Cibles

| | R1 | R2 |
|---|---|---|
| Cibles | `y_ret` : log-rendement futur 4 h ÷ (σ168 h·√4), borné ±5 ; **`y_vol`** : log(vol future 24 h ÷ vol passée 24 h), borné ±3 | `y` : log-rendement futur 4 h ÷ (σ24 h·√4), borné ±6 |
| Résultat sur le rendement 4 h | rien de stable ; formule `ret_24h·wknd` non significative (p_Holm 0,107) | rien de stable |
| Résultat sur la volatilité | **1 formule stable**, IC 0,104 | **non testé** |

Point décisif : **la seule formule stable de R1 vit sur `y_vol`, une cible que R2 n'a jamais évaluée.** Sur l'unique cible commune, les deux runs concluent la même chose. R2 ne pouvait pas « contredire » R1 sur `y_vol`.

Complément que j'ai calculé moi-même (hors dépôt, exploratoire, non pré-enregistré, sur les données de R2 avec ses propres primitives, Spearman moyen sur les 10 marchés ; « nb + » = nombre de marchés de signe positif) :

| Quantité | Train (2024-06 → 2025-07) | Val (2025-07 → 2025-12) | Test (2025-12 → 2026-08) |
|---|---|---|---|
| IC de la primitive `vol24` (z-score) vs cible de type `y_vol` (24 h) | −0,474 (0 marché +) | −0,558 (0 +) | −0,509 (0 +) |
| IC de `−(r72·sgn(ma72))` (analogue de la formule R1) vs cible `y_vol` | +0,083 (10 +) | +0,151 (10 +) | +0,051 (9 +) |
| IC de `−(r72·sgn(ma72))` vs cible `y` de R2 | −0,023 (0 +) | −0,017 (2 +) | +0,004 (6 +) |

Lecture : (i) sur une cible de type volatilité, **la primitive brute `vol24` a un IC de −0,47 à −0,56 dans les trois segments**, c'est-à-dire qu'*aucun* pipeline ne peut ne pas la trouver (c'est l'identité mécanique de §7.2.a) ; (ii) l'analogue de la formule R1 (avec la MA 72 h de R2 à la place de la MA 168 h) donne un IC positif de +0,05 à +0,15 sur les trois segments, dans 9 à 10 marchés sur 10 : **l'effet observé par R1 n'est pas propre à sa fenêtre ni à ses marchés**, à une réserve près (recouvrement temporel avec le held-out de R1, §2.2) ; (iii) cette même formule est sans lien clair avec le rendement 4 h (−0,02 à +0,00) : ce n'est pas un signal directionnel. (Code de ce contrôle : `scratchpad/verify2.py`, non versionné.)

#### (3) Portes et seuils

| | R1 | R2 |
|---|---|---|
| Test de validation | IC signé > 0 sur ≥ 75 % des 4 marchés de découverte (≥ 3/4) ; p unilatéral bootstrap (blocs 48, 300 tirages) < 0,10 ; score pénalisé > 0 | IC poolé > 0 ; ≥ 70 % des 6 marchés de découverte (soit ≥ 5/6, 4/6 échoue) ; p **bilatéral** (approx. normale, bootstrap 200) < 0,10 |
| Sensibilité estimée | IC minimal ≈ 0,014 | IC minimal ≈ 0,038 à 0,044 (§7.3.a) |
| Consolidation | famille (corr. rang ≥ 0,85) retrouvée dans ≥ 3/5 graines, non redondante (\|ρ\| < 0,80) | consensus ≥ 3/5 graines + sélection BIC finale sur validation |
| Held-out | p_Holm < 0,05 (unilatéral, B = 2 000) ; ≥ 75 % marchés IC>0 ; majorité des jamais-vus ; famille de taille 2 | BH q ≤ 0,10 ; \|IC\| ≥ 0,005 ; ≥ 70 % des 10 marchés ; IC jamais-vus > 0 |
| Non redondance | **exigeante** : corrélation partielle vs ridge sur 26 primitives significative (Holm 0,05) | **laxiste** : \|corr\| < 0,8 avec les autres features retenues ; l'apport incrémental (≥ 0,003, p<0,10) est requis seulement pour « nouveau » |
| Filtre « primitive triviale » | oui (> 0,9 de corrélation de rang avec une primitive) | non (les primitives sont dans la bibliothèque, catégorie « prim » ; « nouveau » exclut les primitives) |
| Règle `LIMITED_STABLE` | **≥ 1 formule STABLE** | **≥ 1 formule STABLE ET non redondante** (primitive ou composite) |

Le dernier point est le plus important. **Contre-factuel** (INFERENCE) :
- Si R1 avait appliqué la règle de R2 (stable *et* non redondante), sa formule `y_vol` (stable mais partielle −0,035) n'aurait pas compté : verdict `NO_STABLE_NEW_FEATURES`, identique à R2. R1 le note (« Une lecture stricte … donnerait NO_STABLE_NEW_FEATURES »).
- Si R2 avait testé `y_vol` avec sa propre règle, une primitive mécanique comme `vol24` (IC −0,5 à −0,56) aurait vraisemblablement été « stable » et « non redondante » (première retenue) et déclenché `LIMITED_STABLE` de façon triviale. Le filtre « primitive triviale » de R1 est ce qui écarte ce cas (INFERENCE : je n'ai pas exécuté le pipeline de R2 sur une autre cible).

#### (4) Bibliothèques de candidats

| | R1 | R2 |
|---|---|---|
| Primitives | 26 dont week-end, heure (sin/cos), ret 168 h, MA 168 h (`mag_168`), lrv 6/24/168 | 20 ; pas de calendrier ; MA 24/72 seulement ; vol 24/72 |
| Formes d'interaction | `a·b`, `a·sgn(b)`, `b·sgn(a)` sur **toutes** les 325 paires (975 candidats) | `a·b` (190) et `a·\|b\|` (380) ; total 590 avec les 20 primitives |
| Étage de pré-sélection | seuil par nulle du maximum (décalage circulaire) + même signe sur les 4 marchés + top-8 | top-30 par MI kNN (top-10 dans le pool), CMI gaussienne, stability selection, clusters GP |
| Candidats évalués en validation par graine | 0 à 9 (par cible) | 18 à 22 (données réelles) |

Conséquence précise : **la formule de R1 n'est pas dans l'espace de R2.** `ret_72h·sgn(mag_168)` exige un opérateur `sgn` (absent de R2, qui a `abs` et `max/min`) et la moyenne mobile 168 h (R2 : MA 72 h). De même `ret_24h·wknd` de R1 (y_ret) exige une variable calendaire absente de R2. Même sur la cible commune, R2 ne pouvait pas retrouver `ret_24h·wknd`.

#### (5) Graines

R1 : {11, 23, 37, 41, 59} (arène 1000–1039). R2 : 11–15 (nulle 901–908, synthétique 7001–7006). Les graines sont des réglages du hasard et n'ont pas d'influence conceptuelle sur l'écart ; on note en revanche que R1 a **80** réplications d'arène contre **14** (6+8) pour R2 : la précision sur les taux de faux positifs est très inégale (§6.3).

#### (6) gplearn

Les deux utilisent gplearn 0.4.3 ; ils concluent tous les deux que le GP ne fait pas mieux qu'un simple modèle linéaire/une bibliothèque de produits.

| | R1 | R2 |
|---|---|---|
| Population / générations | 300 / 10 | 300 / 8 |
| Parcimonie | 0,004 (unique) | {0,001 ; 0,01 ; 0,05} |
| Graines / ajustements | 5 (un ajustement par graine) | 5 × 3 = 15 ajustements par graine de découverte |
| Fonctions | add, sub, mul, div, abs, neg, max, min, **tanh** | add, sub, mul, div, neg, abs, max, min |
| Profondeur initiale, constantes | 2–4, [−1, 1] | 2–3, défaut |
| Lignes | 20 000 | 10 000 |
| Programmes conservés | top-6 par fitness, ≤ 15 nœuds, simplification gloutonne | top-2 distincts par ajustement |
| Constat | sur `y_vol`, `−lrv_24` déguisés (IC val 0,40–0,50) ; sur `y_ret` IC val 0,025–0,05 non retrouvé d'une graine à l'autre | 10/13 clusters stables sont des primitives seules ; IC train 0,04–0,05 → val 0,01–0,02 |
| Issue | 0 expression gelée | 0 expression validée |

Accord fort et indépendant : dans les deux cas, ce que le GP trouve est soit une primitive, soit une combinaison linéaire déguisée, et n'est pas reproductible d'une graine à l'autre.

### 8.4 Discussion : la formule `ret_72h·sgn(mag_168)` de R1 face à R2

**Ce que la formule est** (OBSERVED + INFERENCE, §7.2.b) : une variable de « calme récent » : `−ret_72h·sgn(mag_168)` ≈ `−|ret_72h|` dans ~85 % des lignes (BTC held-out). Elle prédit que la volatilité des 24 h à venir dépassera celle des 24 h passées quand les 72 dernières heures ont été calmes.

**Ce que les chiffres de R1 disent** : IC held-out 0,1043 (9/9 marchés, ✔ recalculé), p_Holm 0,001, IC partiel vs ridge brut −0,0349 (p_Holm 0,959), Cochran-Q train+val p = 0,0004 (pente variable de 0,012 à 0,113). Le modèle « mains + C01 » (11 paramètres) fait −0,0208 d'IC par rapport au ridge brut (q10 −0,0282).

**Face à R2**, quatre lectures compatibles avec tous les faits :
1. *R2 n'a pas de quoi contredire cette formule* : cible absente, opérateur `sgn` absent, MA 168 h absente. Le silence de R2 n'est pas un démenti.
2. *La formule est un effet réel, mais pas neuf*. Mon contrôle complémentaire (§8.3.2) montre qu'un analogue existe aussi dans la fenêtre de R2 (IC +0,05 à +0,15, 9–10/10 marchés). Mais l'IC partiel négatif de R1 dit qu'un ridge sur les primitives brutes capte déjà plus que cela. Autrement dit : réel, robuste dans le temps et l'espace… et sans valeur ajoutée sur ces primitives.
3. *Le label `LIMITED_STABLE` est sur-interprétable* : il correspond à « une formule stable existe » sur une cible qui contient une identité mécanique avec une primitive (§7.2.a). Sous la règle de R2, le label serait `NO_STABLE_NEW_FEATURES`. Le meilleur résumé commun des deux études est : *« rien de nouveau au-delà des primitives brutes ; la seule structure trouvée est un proxy connu de la persistance de la volatilité »*.
4. *Ce que R2 aurait pu apporter et n'a pas apporté* : un test de la même formule sur une fenêtre disjointe. Les fenêtres se recouvrent (§2.2) ; le held-out de R2 (2025-12 → 2026-08) est *inclus* dans celui de R1. Une vraie réplication indépendante demanderait de nouvelles données (après 2026-08) ou un autre lieu d'échange/type d'actif.

**Verdict de comparaison (mon jugement, INFERENCE).** Les deux verdicts ne se contredisent pas : ils répondent à des questions différentes avec des règles différentes. Si on devait harmoniser : *R1 sous la règle « stable + non redondant » = `NO_STABLE_NEW_FEATURES`* (accord avec R2). La force de ce verdict commun reste modérée-faible pour les raisons de §7 (crypto seulement, fenêtre courte chez R2, puissance faible chez R2, cible mécanique chez R1).

### 8.5 Où les deux runs divergent aussi (hors verdict) et pourquoi probable

| Divergence | Cause probable (INFERENCE) |
|---|---|
| `FEATURES_DISCOVERED` 2 vs 80 | comptage de familles gelées vs candidats bruts |
| GBM plafond : IC −0,0022 (R1) vs +0,0166 (R2) | bruit d'échantillon (IC 90 % ≈ ±0,014) ; hyperparamètres HGB différents (R1 : `min_samples_leaf=300`, `l2=10`, 9 marchés ; R2 : défaut, 6 marchés d'apprentissage, fenêtre courte) |
| Nombre de candidats évalués par graine (R1 0–9 ; R2 16–23) | R1 filtre par nulle du max et sign-agreement avant validation ; R2 valide tout le pool (18 à 22 candidats) |
| Nombre de marchés d'apprentissage 4 vs 6 | choix de conception |
| Périodes d'apprentissage disjointes | R1 2021-2023 ; R2 2024-2025 |
| Rédaction | R1 : 11 rapports détaillés (+ 11 gabarits, tableaux auto-générés) ; R2 : rapports courts, tableaux dans `summary.json` |

---

## 9. Reproductibilité

### 9.1 Ce que j'ai rejoué moi-même

Environnement : Python 3.11.15, numpy 2.4.6, pandas 3.0.6, scipy 1.17.1, scikit-learn 1.9.1, gplearn 0.4.3 (les versions listées par R2 dans `logs/requirements.txt`), machine à 4 cœurs, **partagée avec d'autres tâches** (charge moyenne ≈ 12), donc mes durées sont supérieures à celles des runs d'origine. Je travaille sur des copies jetables ; je n'ai touché à aucune branche.

| Vérification | Résultat |
|---|---|
| R1 `pytest tests` | 5 passed en 2,72 s |
| R1 `scripts/02_discovery.py` (2 cibles × 5 graines) | même formule gelée pour chaque cible, **digest identique** `9f32094f…d0666`. Durée : 151 s (y_ret) + 133 s (y_vol) sous charge, contre 61 s + 62 s dans le log d'origine (`results/discovery.log`) |
| R1 `scripts/04_diagnostics_train_val.py` | sorties identiques (ex. Q = 40,2373, p = 0,000418, accord de signe 1,0 ; R²(C01 sur mains) = 0,1994 ; GBM profondeur 3 : IC 0,5710) |
| R1 `scripts/05_heldout_once.py` | après suppression du verrou dans ma copie : **résultats identiques à la décimale** (IC held-out 0,10431471504986341 et 0,011984843336322666 ; p_Holm 0,000999… et 0,10744… ; IC partiel −0,034926… ; les 12 lignes de baselines ; placebo 0/20 et 1/20). Durée : ≈ 26 min sous forte charge (le log d'origine place le held-out dans une fenêtre de ~10 min avec l'arène) |
| R1 IC held-out par marché (recalcul indépendant, sans passer par le script) | identiques à 4 décimales (§6.5) |
| R2 relance | `python run_batch.py real 2` (5 graines de découverte, 2 processus) : pour les 5 graines, **liste des candidats, IC et p de validation, comptes, empreinte de gel et R² des baselines identiques** au fichier d'origine (comparaison programmatique). Durée 1 656 s au total sous charge (contre ≈ 257 s dans `logs/real.out`). Non rejoués : lots synthétique (6 graines) et nul (8 graines) de R2, arène de R1 (40+40 réplications) |

### 9.2 Comment relancer

**R1** (depuis `bench/feature_discovery_v1/`) :
1. `pip install numpy pandas scipy scikit-learn gplearn joblib pytest` (versions exactes de R2 conseillées ; R1 ne fournit pas de fichier de versions — UNKNOWN pour ses versions d'origine, mais mon rejeu avec les versions ci-dessus reproduit le digest).
2. Données : déjà fournies (`data/*_1h.csv.gz`, empreintes dans `data/MANIFEST.json`). Pour re-télécharger : `python -m fd.data` (API Binance, non déterministe si l'exchange révise ; la fenêtre est figée).
3. `python scripts/02_discovery.py` (~2 min avec 4 cœurs) → `results/discovery_train_val.json`, `FROZEN.json`.
4. `python scripts/04_diagnostics_train_val.py`.
5. `python scripts/05_heldout_once.py` (refuse de tourner si `results/heldout_lock.json` existe ; il faut supprimer le verrou dans une copie).
6. `python scripts/03_synthetic_arena.py 40 1000 final` (≈ 5 min, log d'origine : 315,6 s).
7. `python scripts/06_adjudicate.py`, `07_causal_boundaries.py`, `07_build_reports.py`, `08_fill_reports.py`.
Fourni : code, données, empreintes, résultats agrégés, tableaux, rapports. Manque : fichier de dépendances, description des versions d'origine, script de lancement global (il faut connaître l'ordre des scripts).

**R2** (depuis `bench/feature_discovery_v1/`) : `pip install numpy scipy pandas scikit-learn gplearn pytest` ; `cd src && python run_batch.py synth|null|real` ; `python analyze.py` ; `pytest -q tests`. Durées d'origine (`logs/*.out`) : réel 257 s pour 5 graines en parallèle (≈ 128 s par graine), nulle 261 s pour 8, synthétique 693 s pour 6. Fourni : README, protocole JSON, données brutes avec empreintes, tous les JSON de résultats, `requirements.txt` exact. Manque : pas de commande unique globale, pas de tableaux Markdown générés (les rapports sont rédigés à la main à partir de `summary.json`), les 8 `.whl` inutiles, le journal de la « graine de fumée 1 ».

Déterminisme : R1 reproduit le digest exact (PROVEN par mon rejeu, mêmes versions). R2 déclare « deterministic per seed given these versions (not bit-checked across machines) » (`10_LIMITATIONS.md` n°12).

---

## 10. Implications pratiques pour AurumShift (pistes à adjuger plus tard — aucune compatibilité affirmée)

Rien de ce qui suit ne dit que quoi que ce soit est compatible avec AurumShift ; l'adjudication se fera contre le vrai dépôt local (`claude.md`).

1. **Le dispositif d'évaluation vaut plus que les formules.** Les deux runs fournissent (à adjuger) un *protocole de contrôle du surajustement de recherche* : règles pré-enregistrées avant les données, gel horodaté d'une liste de formules, verrou de lecture unique du held-out, marchés jamais vus, nulle par décalage circulaire, arène de vérité connue. À examiner plus tard pour un processus PIT/no-lookahead ; cela rejoint la contrainte « provenance / PIT » du dépôt.
2. **Ne pas attendre de gain d'un « moteur de features automatique » sur OHLCV 1 h crypto.** Sur le rendement 4 h, les deux runs trouvent des IC held-out de +0,005 à +0,006 pour un ridge brut et des R² OOS négatifs pour toutes les baselines. Piste à adjuger : investir plutôt dans de nouvelles *sources* (carnet d'ordres, funding, OI, macro : les deux limites les citent) que dans de la recherche symbolique.
3. **Régression symbolique (GP) : PARK** dans les deux runs. Si AurumShift a déjà un jeu de primitives, un lasso/ridge suffit à ce niveau de signal.
4. **Trois éléments techniques réutilisables à évaluer (REUSE/ADAPT)** : (i) nulle par décalage circulaire du maximum statistique (multiplicité sans hypothèse i.i.d.), (ii) bootstrap circulaire par blocs à temps partagé entre marchés, (iii) stability selection par blocs de 336 barres (avec la réserve : 15 % de faux « mains » en arène).
5. **Si une cible « volatilité » est envisagée** : attention à l'identité mécanique entre volatilité passée et cible (§7.2.a) ; définir la cible sans dénominateur commun avec une primitive, ou retirer la primitive correspondante, avant de compter des « features stables ».
6. **Règle de verdict à harmoniser** pour toute lane future : définir dès le protocole si `LIMITED_STABLE` exige la non-redondance. Cette lane montre qu'un seul mot de la règle inverse l'étiquette.
7. **Ne pas fusionner les deux PR** (`SYNTHESE_LANES.md` : elles écrivent dans les mêmes dossiers). Si une seule doit être retenue comme référence documentaire : R1 est plus complète et plus précise statistiquement, mais son verdict est plus fragile à lire ; R2 est plus prudente mais moins puissante et alourdie par les `.whl`. C'est une décision d'opérateur, pas la mienne.

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **[Haute] Rejouer la formule de R1 hors de tout recouvrement.** Tester `−ret_72h·sgn(mag_168)` sur des données postérieures à 2026-08, ou sur un autre échange/actif (actions, FX), avec une cible de volatilité dont le dénominateur n'est pas une primitive (par ex. vol future ÷ vol passée moyenne sur 30 jours, ou vol future seule avec la vol passée en régresseur explicite).
2. **[Haute] Test de nouveauté avant gel** (déviation 5 de R1) : ajouter à la porte de validation l'exigence « corrélation partielle > 0 vs ridge sur toutes les primitives brutes » ; relancer l'arène et la découverte. Résultat attendu : `NO_STABLE_NEW_FEATURES` sur cette lane (INFERENCE).
3. **[Haute] Courbe de puissance.** Dans les deux arènes, faire varier le signal planté (IC 0,01 ; 0,02 ; 0,04 ; 0,06) et mesurer le rappel ; déduire le plus petit IC détectable de chaque porte. Sans cela, « aucune feature » ne veut pas dire « aucune feature d'IC ≥ X ».
4. **[Haute] Harmoniser les deux portes de validation** (unilatérale vs bilatérale, 4 vs 6 marchés, 300 vs 200 bootstraps) et rejouer les deux bibliothèques sur les **mêmes données** et les **mêmes cibles** (rendement 4 h et volatilité). Cela sépare enfin l'effet « pipeline » de l'effet « données ».
5. **[Moyenne] Nulle plus exigeante pour R2** : même décalage pour tous les marchés (comme le placebo de R1) ; 40 réplications.
6. **[Moyenne] Ajouter `sgn` et une MA 168 h à la bibliothèque de R2, et `wknd` aux primitives**, pour vérifier si les formules de R1 y émergent.
7. **[Moyenne] Enrichir les primitives** (funding, OI, carnet d'ordres, macro) : c'est la conclusion commune des deux runs sur le rendement.
8. **[Moyenne] Évaluer le GP avec plus de budget / PySR** (Julia) seulement si un signal non linéaire est démontré ailleurs (l'arène donne 27,5 % de puissance à petit budget).
9. **[Basse] Nettoyage** : retirer les 8 `.whl` de la branche `-b` si elle est retenue ; corriger les renvois de §11/§12 et la mention « §9 modifié » de R1 ; corriger la description des clusters stables de R2.
10. **[Basse] Coûts et exécution** : un IC de 0,01 n'a de sens qu'avec un modèle de coûts (hors périmètre des deux runs).

---

## 12. Index des fichiers lus

### Racine et transversaux
- `claude.md` (lu, identique sur les deux branches) : doctrine de recherche et contraintes AurumShift.
- `SYNTHESE_LANES.md` (lu partiellement : lignes concernant la lane 015 et le lexique) : synthèse de l'ensemble des lanes.
- PR GitHub #13 et #20 (lues via l'API) : titre, état (brouillon), date, commit de tête, nombre de fichiers.

### Run 1 — `origin/claude/feature-discovery-v1`
Rapports (`reports/015_feature_discovery/`), tous lus en entier :
- `00_EXECUTIVE_SUMMARY.md` : question, résultat, lecture honnête, bloc final.
- `01_METHODS.md` : tableau des méthodes et choix de conception.
- `02_PROTOCOL.md` : protocole pré-enregistré, splits, gates, règle de verdict, déviations §12.
- `03_SYMBOLIC.md` : GP, table par graine, puissance 27,5 %.
- `04_SPARSE.md` : stability selection, baselines held-out.
- `05_INTERACTIONS.md` : formules gelées, résultats held-out, cartes d'interprétabilité.
- `06_STABILITY.md` : graines, invariance Q, placebo.
- `07_CAUSAL_BOUNDARIES.md` : classes de preuve et structures simulées.
- `08_FALSIFICATION.md` : arène, tests forward-safety.
- `09_ADJUDICATION.md` : bloc final et tableau ADOPT/ADAPT/PARK/REJECT.
- `10_LIMITATIONS.md` : 13 limites.
Code et scripts (`bench/feature_discovery_v1/`), lus en entier sauf mention : `fd/data.py`, `fd/panel.py`, `fd/features.py`, `fd/expr.py`, `fd/causal.py`, `fd/metrics.py`, `fd/pipeline.py`, `fd/screening.py`, `fd/sparse.py`, `fd/symbolic.py`, `fd/interactions.py`, `fd/invariance.py`, `fd/baselines.py`, `fd/synth.py`, `fd/cards.py` ; `scripts/02_discovery.py`, `03_synthetic_arena.py`, `04_diagnostics_train_val.py`, `05_heldout_once.py`, `06_adjudicate.py`, `07_causal_boundaries.py` ; `scripts/07_build_reports.py` (début seulement) et `scripts/08_fill_reports.py` ; `tests/test_forward_safety.py`.
Résultats lus : `results/FINAL.json`, `FROZEN.json`, `heldout_lock.json`, `heldout_results.json` (analyse complète par python), `discovery_train_val.json` (résumés + par graine), `diagnostics_train_val.json`, `synthetic_arena_final.json` (recalcul), `synthetic_arena_dev.json` (comptes), `causal_boundaries.json` (clés), `arena.log`, `discovery.log`, `download.log`, `tables/*.md` (12 fichiers lus), `data/MANIFEST.json`.
Non lus : `report_templates/*.md` (sauf l'en-tête du 00 : gabarits des rapports) ; contenu des fichiers `data/*.csv.gz` (utilisés seulement par calcul).

### Run 2 — `origin/claude/feature-discovery-v1-b`
Rapports (`reports/015_feature_discovery/`), tous lus en entier : `00_EXECUTIVE_SUMMARY.md`, `01_METHODS.md`, `02_PROTOCOL.md`, `03_SYMBOLIC.md`, `04_SPARSE.md`, `05_INTERACTIONS.md`, `06_STABILITY.md`, `07_CAUSAL_BOUNDARIES.md`, `08_FALSIFICATION.md`, `09_ADJUDICATION.md`, `10_LIMITATIONS.md`.
Bench (`bench/feature_discovery_v1/`) : `README.md`, `configs/protocol.json`, `logs/{null,real,synth}.out`, `logs/requirements.txt`, `raw/manifest.json`, `src/data.py`, `src/features.py`, `src/panels.py`, `src/pipeline.py`, `src/run_batch.py`, `src/analyze.py`, `tests/test_isolation.py` (tous lus en entier).
Résultats lus : `results/summary.json` (complet, via python), `results/real/run_11…15.json` (comptes, candidats, provenance, clusters GP, baselines), `results/real/lock_11.json`, `results/real/run_11.log`, `results/synth/lock_7001.json`, `results/null/lock_901.json`, `results/synth/run_700x.json` et `results/null/run_90x.json` (via `summary.json` uniquement ; non ouverts un à un, sauf comptes) ; profils par déciles (`dec_val`, `dec_test`) : non lus.
Hors-sujet : 8 fichiers `.whl` à la racine (listés au §0 ; contenu non lu, ce sont des paquets binaires).

### Scripts de vérification produits par moi (non versionnés, dans le dossier temporaire de session)
`verify1.py` (recalcul des IC held-out de R1 sur données brutes), `verify2.py` (contrôle complémentaire sur données de R2), copies jetables `repro1/` (rejeu de R1), `repro2/` (rejeu de R2).
