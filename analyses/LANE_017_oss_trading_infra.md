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
