# Analyse approfondie — Lane 001 « Flotte de stratégies adaptatives (paysage) », PR #2 mergée

Rédigée le 2026-09-29 pour Jean-François. Je te tutoie et j'explique chaque terme technique à sa première occurrence (les termes sont en **gras** à ce moment-là).

Conventions de lecture de ce document :

- « Le rapport dit » = affirmation du rapport de la lane, que je n'ai pas forcément vérifiée.
- « J'ai vérifié » = j'ai recalculé ou rejoué moi-même (voir §3.9 et §6.4). Verdicts : ✔ vérifié / ✘ écart / ? non vérifiable.
- Les chemins entre parenthèses sont relatifs à `reports/001_adaptive_strategy_fleet/` sur la branche `origin/main`.
- « INFERENCE », « PROVEN », « OBSERVED », « DOCUMENTED_CLAIM », « UNKNOWN » sont les étiquettes de preuve imposées par `claude.md` (définies au §1.3).
- Mes propres calculs (hors rapport) sont marqués « [moi] ». Ils sont faits avec les fichiers de la lane et le code fourni, jamais avec des chiffres inventés.

---

## 0. Fiche d'identité

| Élément | Valeur |
|---|---|
| Lane | 001 — Flotte de stratégies adaptatives (paysage). Identifiant de mission cité dans le rapport : `EXTERNAL_RESEARCH_ADAPTIVE_STRATEGY_FLEET_LANDSCAPE_V1` (00_RESEARCH_SCOPE.md) |
| Branche d'origine | `origin/claude/kind-bohr-n5e2gl` |
| PR | #2 « Merge pull request #2 from redguiff-bot/claude/kind-bohr-n5e2gl », fusionnée dans `main` par RedGuiff : commit `a04c1562a54e6ad2d7e4b4ceab82bfdf1ac70a92`, 2026-09-29 15:21:37 +0200 |
| Commit de contenu | un seul : `034d04a13a935d4dd49d36e0a32a5b825748b3de` « Add external research study 001: adaptive strategy fleet landscape », auteur « Claude », 2026-09-29 07:13:26 +0000 ; `git show --stat` : 80 fichiers, 1234 insertions |
| Branche `main` au moment de l'analyse | HEAD `1a449df5239753e39d657fdf14813a8f1995a985` (2026-09-29 15:59:21 +0200) |
| Identité des deux sources | J'ai comparé `origin/main` et `origin/claude/kind-bohr-n5e2gl` sur `reports/001_adaptive_strategy_fleet/` : **aucune différence** (`git diff --stat` vide). Il n'y a donc qu'un seul run pour cette lane (pas de variante « -b »). |
| Nombre de fichiers | 80 : 8 rapports `.md` (00 à 07) + 5 fichiers dans `bench/` (`bench.py`, `analyze.py`, `failsoft_check.py`, `persistence_check.py`, `requirements-observed.txt`) + 14 JSON `results/main` + 18 JSON `results/sweep` + 33 JSON `results/determinism` + 2 tables markdown (`main_tables.md`, `sweep_tables.md`) |
| Taille | environ 579 Ko sur disque (dossier extrait, tailles de blocs comprises [moi]) ; rapports : 1 159 lignes de code+texte pour les `.md`/`.py`/tables (`wc -l`) [moi] |
| Type de travail | Étude de paysage (recherche d'outils externes) + benchmark synthétique. **Aucun code AurumShift** n'a été vu ni touché (00_RESEARCH_SCOPE.md §2). |
| Verdict final | « Aucun projet externe n'est un ordonnanceur d'attention de recherche prêt à l'emploi » ; classification par composant (ADOPT/ADAPT/PARK/REJECT) : **aucun ADOPT d'un système entier** ; plusieurs ADAPT partiels (primitives de River, algorithme D-UCB, garde d'obsolescence) ; REJECT de MABWiser, du paquet SMPyBandits, d'Optuna comme ordonnanceur, des `Policy` livrées par River telles quelles ; PARK de VW, des détecteurs de dérive de River, etc. (07_FINAL_ADJUDICATION.md §1 et §3.1) |
| Force du verdict | Mixte et à nuancer. (a) « Rien d'existant ne fait le travail » : force **moyenne**, car 2 des 5 finalistes (VW, Optuna) n'ont pas été testés dans leur usage fort (partage de variables, courses non terminales) et parce que le banc n'a qu'**une** famille de scénarios. (b) « Les règles guidées par la récompense affament des cellules » : force **haute pour ce scénario** (reproduit à l'identique par moi, §3.9), **inconnue hors scénario**. (c) « Garde d'obsolescence + D-UCB = bonne direction » : force **faible à moyenne** (réglé sur les mêmes scénarios que ceux rapportés, code écrit par l'auteur). Le rapport lui-même donne « Med-Low » pour (c) (07 §4). |
| Pré-enregistrement / séparation réglage-validation-held-out | **Aucun.** Ni protocole gelé, ni jeu de validation, ni jeu mis de côté (« held-out »). Le rapport l'avoue en partie (04 §6 P1 : réglages « in-sample ») et recommande de le faire dans une « scénario v2 » (07 §3.2). |
| Fichiers annoncés mais absents | Pas de README ni de protocole séparé dans la lane ; le protocole est décrit dans `00_RESEARCH_SCOPE.md` et `03_REPRODUCTION_AND_BENCHMARK.md`. Les 5 clones GitHub (river, mabwiser, vowpal_wabbit, optuna, SMPyBandits) ne sont **pas** dans le dépôt (seuls leurs hash de commit sont cités). Pas de journal des sorties de tests (Optuna 125 tests, MABWiser 533/1, River 3+22 skipped) : ces chiffres sont **non vérifiables** ici. |

---

## 1. Mission et question posée

### 1.1 La question en langage simple

Imagine que ton moteur de recherche AurumShift ait **160 « cellules »**. Une **cellule** = une combinaison (stratégie × instrument financier × horizon × régime de marché × configuration). Chaque cellule est une petite expérience qui produit peu à peu des preuves (est-ce que ça marche ou non).

Le moteur dispose d'un temps limité : à chaque « tour », il ne peut regarder que quelques cellules (dans le banc : 10 sur 160). La question : **quelle cellule regarder ensuite ?** Ce n'est pas « où investir de l'argent » (ce serait de l'allocation de capital), c'est « où dépenser l'attention de recherche ».

Le rapport formule cela comme un problème de **bandit** : imagine un joueur devant 160 machines à sous (« bras »), qui doit choisir quelle machine tirer. Il doit équilibrer **explorer** (essayer des machines peu connues) et **exploiter** (retourner vers celles qui paraissent bonnes). Le cas ici est plus dur que le bandit classique, parce que :

- **non stationnaire** : les machines changent avec le temps (une cellule peut se dégrader ou s'améliorer) ;
- **par lots avec retour retardé** (« batched, delayed feedback ») : on choisit 10 cellules d'un coup avant de voir le moindre résultat ;
- **jeu de bras dynamique** : de nouvelles cellules apparaissent en cours de route ;
- **récompense = valeur d'information** (« ce petit incrément de preuve était-il informatif ? »), jamais un profit (P&L).

Questions concrètes que le moteur devrait pouvoir trancher (00 §1) : que faut-il explorer, que faut-il creuser, qu'est-ce qui a l'air prometteur, qu'est-ce qui se dégrade ; comment éviter la **famine** (« starvation » : des cellules jamais regardées) ; comment faire tourner l'attention ; comment s'adapter en ligne sans devenir un allocateur de capital.

### 1.2 Ce que la lane cherche à produire

Une revue des outils existants (bibliothèques open source, articles scientifiques), une sélection des 5 plus forts, un banc d'essai synthétique, une critique adverse, une analyse de licence/maintenance, une « surface d'intégration » générique et un jugement final. Le rapport s'arrête volontairement avant toute intégration (07, dernière ligne : « Stopped here as instructed »).

### 1.3 Contraintes de `claude.md` appliquées

Ordre de priorité de la doctrine : **REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST** (réutiliser tel quel, puis adapter, puis envelopper dans une couche fine, puis composer plusieurs briques, et en dernier seulement écrire du code maison). Autres règles reprises de `claude.md` (lu dans le dépôt) :

- sources primaires (dépôts réels, documentation officielle, articles) ; ne pas croire les README aveuglément ; cloner et exécuter quand c'est faisable ;
- distinguer les constats par 5 étiquettes : **PROVEN** (démontré par un contrôle reproductible), **OBSERVED** (vu directement, mais pas une garantie générale), **DOCUMENTED_CLAIM** (affirmé par une doc ou un article, non vérifié), **INFERENCE** (raisonnement de l'auteur), **UNKNOWN** (non déterminé) ;
- ne pas classer les projets selon les étoiles GitHub ; ne pas fabriquer de résultats de benchmark ;
- « rejeter ou PARKER une technologie qui exige un réglage excessif sauf gain exceptionnel » (règle n°9) ;
- contraintes AurumShift : recherche seule/paper seul, pas de capital réel, PostgreSQL d'abord, PIT (« point-in-time » : on ne voit que ce qui était connu à la date de décision) / provenance / pas de « lookahead » (regarder le futur), événementiel/intraday (pas de haute fréquence), une seule source d'autorité par sujet, « l'absence de preuve n'est pas une preuve négative », coûts de marché réalistes, peu de relais opérateur, reproductibilité, la complexité d'infrastructure doit se justifier ;
- frontière : ne jamais affirmer qu'un candidat est compatible avec AurumShift à partir de ce dépôt ; l'issue est ADOPT / ADAPT / PARK / REJECT et l'arbitrage final se fait plus tard contre le vrai dépôt local.

Le rapport tire trois conséquences des contraintes (00 §5, toutes INFERENCE) : l'état doit être inspectable en base relationnelle ; il faut une voie « essayé mais pas de preuve » qui ne compte pas comme mauvais résultat ; le déterminisme sous graine fixe et redémarrage est obligatoire ; les bibliothèques qui « tuent » définitivement des cellules (élagage) heurtent la 2e contrainte.

---

## 2. Méthode

### 2.1 Phases de la lane (00 §3)

| Phase | Ce qui a été fait | Limite déclarée |
|---|---|---|
| 1 Paysage | Clones « blobless » (sans contenu de fichiers, seulement l'historique) de 13 dépôts GitHub pour `git log`/tags/LICENSE ; JSON PyPI ; vérification par l'API arXiv de 14 articles ; 5 recherches web ; pages d'issues GitHub via WebFetch | L'API REST GitHub et les pages HTML github.com étaient **bloquées** par le proxy de la session (403) ; les comptes d'issues viennent d'un WebFetch **résumé par un modèle**, donc moins fiables. Ray, SaaS d'expérimentation et internals d'irace non relus. |
| 2 Filtre | Règles de la mission appliquées à la métadonnée ; les étoiles GitHub délibérément ignorées | — |
| 3 Revue détaillée | Lecture du code, installation, exécution des tests/exemples pour River, MABWiser, VW, Optuna, SMPyBandits ; Ax/contextualbandits/Vizier : métadonnée + résolution de dépendances seulement | La suite de tests C++ de VW non compilée (seule la roue pip a été utilisée) |
| 4 Banc d'essai | Une seule famille de scénarios synthétiques, 20 graines par règle + petits balayages de sensibilité | Une famille de scénarios ; récompenses de Bernoulli ; lots de 10 ; hyper-paramètres surtout non réglés ; **aucun test de signification** (moyenne ± écart-type seulement) |
| 5 Critique adverse | Attaques dérivées du code et des mesures | Certaines attaques sont des INFERENCE (étiquetées) |
| 6 Adéquation | Seulement les contraintes de `claude.md` | L'arbitrage final doit se faire sur le vrai dépôt |

### 2.2 Environnement (00 §4, OBSERVED)

Python 3.11.15, Linux, 4 cœurs, 15 Go de RAM. Versions exécutées (`bench/requirements-observed.txt`) : river 0.26.1, vowpalwabbit 9.11.9, mabwiser 2.7.4, optuna 5.0.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1, SMPyBandits 0.9.7. Les runs ont été lancés 4 en parallèle sur 4 cœurs (temps comparables entre eux, pas absolus).

[moi] J'ai recréé un environnement avec numpy 2.4.6, river 0.26.1 et mabwiser 2.7.4 : mêmes versions que le rapport. Cela m'a permis de rejouer (§3.9, §6.4).

### 2.3 Le simulateur (`bench/bench.py`, `make_env`, constantes en tête de fichier)

Constantes (lues dans le code) : `R=1200` tours, `B=10` tirages par tour, `N_E=40` cellules établies, `N_N=100` nouvelles, `N_L=20` tardives, `T_LATE=300` (arrivée des tardives), `T_CP=600` (point de changement), `GAP0=800`, `GAP1=900`, `N_GAP=20` (fenêtre de trou de données et nombre de cellules muettes), `WARM_PULLS=200`, `STALE_S=200`.

| Élément | Implémentation (code lu) |
|---|---|
| Cellules | 160 = 40 établies + 100 nouvelles + 20 tardives (ces dernières n'existent qu'à partir du tour 300 : jeu de bras dynamique) |
| Historique | Chaque cellule établie reçoit 200 tirages historiques avant le tour 0 (donc 40×200/10 = 800 « tours » de chauffe), passés par le chemin normal de mise à jour de chaque bibliothèque |
| « Promesse » p | établies : p ~ Uniforme(0,2 ; 0,7) ; nouvelles/tardives : p ~ Beta(2, 6) ; **12 « pépites » (gems)** : p ~ Uniforme(0,7 ; 0,8) (8 parmi les nouvelles, 4 parmi les tardives) |
| Changement au tour 600 | les 10 meilleures établies perdent 0,4 de p (plancher 0,05) = **dégradation** ; les 10 nouvelles de p le plus bas passent à p = 0,85 = **amélioration/changement de régime** |
| Trou de données, tours 800 à 899 | 20 cellules tirées au hasard (jamais parmi les 10 améliorées) ne renvoient **aucune** preuve ; la règle **n'est pas prévenue** (pas de mise à jour) : modélise « l'absence de preuve » |
| Attention | 1 200 tours × 10 cellules distinctes par tour, retour retardé par lot ; 20 graines ; graine de l'environnement = graine de la règle = s (l'environnement utilise `default_rng(10000+seed)`) |
| Oracle | connaît les vrais p et les trous ; prend les 10 meilleures cellules disponibles à chaque tour |
| Récompense | Bernoulli(p) : « cet incrément de preuve était informatif ». Aucun P&L, aucun coût de marché, aucun capital. |

Un **oracle**, ici, est une règle de référence « tricheuse » qui connaît la vérité ; elle sert de plafond théorique. Le **regret** = (récompense espérée de l'oracle) moins (récompense espérée de la règle), par tour de 10 tirages. Plus il est bas, mieux c'est. Un tirage au sort équitable (round-robin) donne environ 4,5 (rapport) ; mon calcul depuis les JSON : 4,509 (§3.9).

### 2.4 Métriques

- **Couverture** : `cov≥1` (part des cellules tirées au moins une fois), `cov≥10` (au moins 10 fois).
- **Famine** : `zero_pull_cells` (nombre de cellules jamais tirées sur 160), `stale@end` (fraction des cellules sans tirage dans les 200 derniers tours), `max_gap` (plus long intervalle sans tirage), délai avant premier tirage des nouvelles cellules (`ttf_new`, en tours), pépites trouvées (≥ 20 tirages).
- **Concentration** : **Gini** (0 = attention parfaitement répartie ; 1 = tout sur une seule cellule), part des tirages sur les 10 % de cellules les plus tirées (16 cellules), **entropie normalisée** `H` (1 = uniforme), avant et après le changement.
- **Adaptation** : part des tirages tombant sur les 10 cellules améliorées / les 10 dégradées dans des fenêtres après le tour 600 ; regret par phase.
- **Gaspillage sur trou** (`gap_waste`) : part de l'attention de la fenêtre 800-899 dépensée sur les 20 cellules muettes.
- Déterminisme, temps, mémoire, poids des dépendances.

### 2.5 Règles de référence écrites par l'auteur (CUSTOM, pas des candidats)

- `ref_roundrobin` : la cellule tirée le moins récemment d'abord.
- `ref_ducb` : **Discounted-UCB** (D-UCB) d'après Garivier & Moulines (arXiv:0805.3415). **UCB** = « Upper Confidence Bound » : on tire la cellule dont la borne supérieure optimiste (moyenne observée + bonus d'incertitude) est la plus haute. « Discounted » = les anciens résultats sont réduits par un facteur γ à chaque tour, donc les preuves anciennes s'estompent. Le code (`RefDUCB`) : tous les compteurs `N` et sommes `X` sont multipliés par γ à chaque tour, puis on ajoute les observations ; indice = X/N + 0,5·√(2·ln(total)/N) ; cellule jamais vue = +∞ (tirée en priorité).
- `ref_ducb_fresh` : pareil + « garde d'obsolescence » : toute cellule non tirée depuis plus de `STALE_S=200` tours reçoit l'indice +∞ (revisite forcée).

Le **facteur d'oubli γ** ici s'applique **par tour** (10 tirages), pas par tirage (04 §6 P6 le dit : « discount once per round »).

### 2.6 Candidats externes et leur adaptateur dans le banc

- **River** : `bandit.UCB` (delta=0,5) avec `stats.Mean` (`river_ucb_mean`) ou `stats.EWMean(fading_factor=0.9)` (`river_ucb_ew`, moyenne à décroissance exponentielle) ; `ThompsonSampling` avec `proba.Beta` (`river_ts_beta`) ; `EpsilonGreedy(epsilon=0.1)` avec EWMean 0.9 (`river_eps_ew`) ; `Exp3(gamma=0.1)` (`river_exp3`). **Thompson sampling** = on tire au sort une valeur plausible pour chaque cellule dans sa distribution a posteriori et on prend la meilleure ; **epsilon-greedy** = avec probabilité ε on tire au hasard, sinon on prend la meilleure moyenne.
- **MABWiser** : `UCB1(alpha=0.5)`, `ThompsonSampling`, `EpsilonGreedy(0.1)`, une seule `partial_fit` par tour.
- **Vowpal Wabbit (VW)** : `--cb_explore_adf` avec `--epsilon 0.1` (défaut ou avec `--power_t 0 --learning_rate 0.05`), ou `--squarecb` (`--power_t 0 --learning_rate 0.05`), graine par `--random_seed`. Chaque cellule n'a qu'une variable « |A c17 » (identifiant) : pas de partage de variables entre cellules.
- **Optuna** et **SMPyBandits** : **non exécutés dans le banc** (raisons au §4).

### 2.7 Splits tuning / validation / held-out, pré-enregistrement, gel

- Aucun pré-enregistrement, aucun gel de paramètres. Les seuils ne sont pas définis avant les résultats. Les paramètres de l'auteur (`γ=0.98` par défaut, puis `0.998`, garde à 200 tours) ont été choisis après avoir vu les résultats du même scénario (03 §4 : « selected after seeing results on the same scenario ⇒ in-sample »).
- Aucune séparation de graines entre réglage et rapport : les mêmes 20 graines (0 à 19) servent à tout. Les balayages des règles externes utilisent 5 graines (0 à 4 vraisemblablement ; le fichier ne le précise pas) — `n=5` dans `sweep_tables.md`.

### 2.8 Graines et déterminisme

Une graine s détermine à la fois l'environnement (`10000+s`) et la règle. Les rewards sont tirés dans un flux `rng = default_rng(seed)` consommé dans l'ordre des tirages de la règle : **deux règles différentes ne voient donc pas les mêmes tirages aléatoires de récompense** (pas de « common random numbers ») ; elles voient en revanche les mêmes valeurs p (même environnement) pour une graine donnée. Une comparaison **appariée par graine** est possible sur les p, mais le rapport ne la fait pas.

### 2.9 Critères de décision

Il n'y a **pas de seuils chiffrés de décision** fixés à l'avance (ni « ADOPT si regret < x », ni « rejet si famine > y »). Les critères d'adoption sont qualitatifs : la mission filtre sur l'adéquation, l'exécutabilité, la licence, la maintenance, le poids des dépendances, la persistance (01 §3), plus les attaques par axe (04) et la doctrine n°9 sur le réglage. Les seuils chiffrés qui existent sont des définitions de métriques : `STALE_S=200` tours (sert à la fois de définition de « obsolète » dans `stale@end` et de seuil de la garde dans `ref_ducb_fresh`, voir §7.2), fenêtres 750-800 pour `impr/degr`, « pépite trouvée » = au moins 20 tirages, et les classes de maintenance de 01 (A = version ≤ 6 mois et commits multi-auteurs, B = lente/un mainteneur, C = périmée/abandonnée).

---

## 3. Résultats détaillés

### 3.1 Rapport 01 — Paysage (Phase 1 et 2)

**Familles d'approches** (01 §1) :

| Question | Famille | Source citée |
|---|---|---|
| Où dépenser la prochaine unité d'attention ? | bandits (contextuels) : UCB, Thompson, Exp3 | Russo et al. 1707.02038 ; Agrawal & Goyal 1111.1797 ; Bietti et al. « bake-off » 1802.04064 |
| Les preuves vieillissent / les cellules se dégradent | bandits non stationnaires : D-UCB, SW-UCB | Garivier & Moulines 0805.3415 ; Besbes-Gur-Zeevi 1405.3316 ; Cheung et al. 1810.03024 ; 2407.08654 |
| Le régime a-t-il changé ? | détection de dérive (**ADWIN**, **Page-Hinkley**, **KSWIN** : algorithmes qui déclenchent une alerte quand la distribution des données change) | module `river/drift/` (OBSERVED) |
| Quelles cellules méritent plus de preuves ou d'abandon précoce ? | course / **successive halving** (on garde la meilleure fraction à chaque étape) / Hyperband / ASHA / irace | 1603.06560 ; 1810.05934 ; irace |
| Champion/challenger | intervalles de confiance séquentiels | VW `--epsilon_decay` (`min_champ_examples`) |
| Populations de configs | Population Based Training | 1711.09846 |
| Quelle config essayer dans une cellule | optimisation bayésienne | BoTorch 1910.06403 ; Optuna 1907.10902 |
| Expériences adaptatives sous dérive exogène | 2202.09036 | — |
| Allocation sous contrainte de ressources | Bandits with Knapsacks 1305.2545 | **déclassé** : saveur capital/budget |
| Acquisition d'étiquettes | apprentissage actif (modAL), périmé depuis 2023 | — |

5 articles récents (2025-2026) trouvés par recherche web ne sont **pas lus** (niveau extrait de recherche : au mieux DOCUMENTED_CLAIM, qualité UNKNOWN) : 2506.02933, 2606.09802, 2602.05139, BANCO (ACM WWW 2026), 2506.02980. Les 14 identifiants arXiv classiques ont été vérifiés contre l'API arXiv (titres/années concordent : OBSERVED). Je n'ai pas pu revérifier ces identifiants (pas d'accès web dans cette analyse) : ?

**Tableau des 23 candidats** (01 §2). Légende : Maint = A actif / B lent ou mono-mainteneur / C périmé ; Disposition F = finaliste, D = déclassé, R = rejeté, T = technique.

| # | Candidat | Licence | Dernière version / dernier commit | Maint | Sort |
|---|---|---|---|---|---|
| 1 | River `bandit`+`drift`+`stats` | BSD-3 | 0.26.1 (2026-08-21) / 2026-09-28 | A | F |
| 2 | Vowpal Wabbit `cb_explore_adf` | BSD-3 | 9.11.9 (2026-09-27) / 2026-09-28 | A/B (un auteur domine) | F |
| 3 | MABWiser | Apache-2.0 | 2.7.4 (2024-08-30) / 2024-08-30 | C | F « gardé pour tester l'hypothèse de la bibliothèque populaire » |
| 4 | Optuna pruners/storage | MIT | 5.0.0 (2026-09-04) / 2026-09-25 | A | F |
| 5 | SMPyBandits | MIT | 0.9.7 (2019-10-25) / 2026-06-19 | C | F comme référence d'algorithmes ; import cassé |
| 6 | Ax / BoTorch | MIT | 1.3.1 (2026-06-09) / 2026-09-21 | A | D (69 paquets dont torch + CUDA) |
| 7 | contextualbandits | BSD-2 | 0.3.30 / 2026-06-28 | B | D |
| 8 | Google OSS Vizier | Apache-2.0 | 0.1.24 (2025-02-01) / 2026-09-15 | B | D (architecture serveur gRPC) |
| 9 | Ray Tune | Apache-2.0 | ray 2.58.0 (2026-08-23) | A | D (cluster ; internes non relus) |
| 10 | Nevergrad | MIT | 1.0.12 / 2026-03-16 | B/C | R |
| 11 | modAL | MIT | 0.4.2 (2023) | C | R |
| 12 | Open Bandit Pipeline | Apache-2.0 | 0.5.7 (2023) | C | R |
| 13 | scikit-multiflow | BSD-3 | 0.5.3 (2020) | C | R (remplacé par River) |
| 14 | irace | GPL (≥ 2) | v4.5 / 2026-09-15 | A | D |
| 15 | GrowthBook | MIT-Expat + dossiers `enterprise` propriétaires | v5.1.0 | A | R |
| 16 | SaaS (Statsig/Eppo/Optimizely) | propriétaire | — | — | R (produits non examinés) |
| 17 | D-UCB / SW-UCB | article | 2008 | — | T (implémenté par l'auteur : `ref_ducb`) |
| 18 | Thompson sampling | article | 2011/2017 | — | T |
| 19 | Successive Halving / Hyperband / ASHA | article | 2016/2018 | — | T (via Optuna) |
| 20 | Population Based Training | article | 2017 | — | T/D |
| 21 | ADWIN / Page-Hinkley / KSWIN | articles | — | — | T (via River, non benchmarké) |
| 22 | Bandits with Knapsacks | article | 2013 | — | R pour cet usage |
| 23 | Adaptive experimentation sous non-stationnarité exogène | 2202.09036 | 2022 | — | T (liste de lecture) |

**Sélection des 5** (01 §3) : River, VW, MABWiser (contrôle « bibliothèque populaire » gardé exprès malgré la péremption), Optuna, SMPyBandits (référence d'algorithmes seulement). Non retenus : Ax, contextualbandits, Vizier, Ray, irace.

**Observation clé de 01** (INFERENCE) : « aucun candidat n'est un ordonnanceur d'attention de recherche prêt à l'emploi » ; les comportements décisifs (garde d'obsolescence, cellules muettes, oubli avec taille d'échantillon effective correcte) ne sont pas fournis par les bibliothèques.

**Ce que ça veut dire** : c'est un catalogue solide et sourcé, mais ses chiffres de maintenance (nombres de commits, auteurs) sont non vérifiables ici (je n'ai pas les clones) ; les comptes d'issues sont explicitement de faible fiabilité (WebFetch résumé).

### 3.2 Rapport 02 — Revue détaillée des 5 finalistes

#### River (`bandit`, `stats`, `drift`)
- Architecture OBSERVED : 1 173 lignes dans `river/bandit/*.py` ; politiques `UCB`, `BayesUCB`, `ThompsonSampling`, `EpsilonGreedy`, `Exp3`, `LinUCB`, `RandomPolicy`. `pull(arm_ids)` prend la liste des bras disponibles à chaque appel (jeu de bras dynamique) ; un bras jamais mis à jour reçoit l'indice +∞ dans UCB.
- **Point clé** : le bonus UCB est `delta*sqrt(2*log(self._n)/self._counts[arm])` avec des compteurs **cumulés** `_n` et `_counts`. Donc si tu remplaces la moyenne par une moyenne à oubli (EWMean), l'exploration, elle, ne « rajeunit » pas. Le rapport le déduit du source (INFERENCE) et le montre comportementalement (PROVEN). **J'ai relu le code source de `UCB._pull` de la version 0.26.1 installée : ✔ (la formule utilise `self._n` et `self._counts[arm_id]`).**
- Persistance : objets Python simples, `pickle` (sérialisation binaire) continue de façon identique au bit près (`persistence_check.py` : UCB-Mean, UCB-EWMean, Thompson-Beta « identical continuation: True » ; blob Thompson 122 Ko pour 30 bras). [moi] J'ai relancé : `river_ucb_mean` 5 221 octets, `river_ts_beta` 121 923 octets, `river_ucb_ew` 6 608 octets, les trois « True » ✔.
- Déterminisme : graine via `random.Random(seed)`, même sélection pour 3 valeurs de `PYTHONHASHSEED` (voir §3.7).
- Robustesse (`failsoft_check.py`) : `pull([])` → `ValueError` ; `update(arm, None)` → `TypeError` ; **une seule récompense NaN** ingérée par `UCB` **empoisonne** l'état : le `pull` suivant lève `IndexError`. [moi] Rejoué : ✔ les quatre comportements identiques.
- `Exp3` : `update` a besoin de `_probabilities[arm]` d'un `pull` précédent ; dans le banc, l'historique et le retour par lots déclenchent `KeyError: 26` (`results/main/river_exp3.json`). [moi] Le JSON contient la trace : l'erreur survient dans `pol.update(obs, -1)` de la **chauffe** (ligne 196 de `bench.py`) ✔. Je confirme aussi hors banc que le retour par lot échoue (10 `pull` puis 10 `update` : `KeyError`) ✔ et que `update` sans `pull` préalable échoue ✔. Donc l'affirmation « historique ET lots » est vraie, mais le banc ne démontre directement que la chauffe (le crash survient avant tout lot).
- Tests : `tests/bandit` 3 passés, **22 ignorés** ; le seul test comportemental (`test_better_than_random_policy`) est marqué `skip(reason="flaky")` ; `tests/model_selection/test_bandit.py` 14 passés. Non vérifiable ici (?).
- Maintenance : 0.26.0 (2026-08-20), 0.26.1 (2026-08-21), 0.25.0 (2026-05-31) ; 299 commits et 39 auteurs sur 365 jours, 69 commits sur 90 jours ; 52 issues ouvertes (WebFetch). ? non vérifiable. Dépendances : `numpy>=2.2.5`, `scipy>=1.14.1`, `narwhals` ; Python ≥ 3.11 ; 256 Mo. Licence BSD-3.
- Détecteurs de dérive (`adwin`, `page_hinkley`, `kswin`) présents dans les sources mais **non benchmarkés**.

#### Vowpal Wabbit
- Cœur C++, binding Python `Workspace`. `cb_explore_adf` prédit une distribution de probabilité sur un ensemble d'actions fourni à chaque appel. Potentiellement, des cellules qui partagent des variables (stratégie, instrument, horizon) « empruntent de la force » entre elles : **non testé** (le banc n'utilise qu'un identifiant de cellule).
- `--epsilon_decay` (champion/challenger avec test de confiance séquentiel) : `epsilon_decay.cc` 475 lignes ; a tourné 50 mises à jour sans erreur ; calendrier par défaut `epsilon = init·(t+1)^(-1/3)` : l'exploration **décroît**, contraire de ce qu'il faut en environnement non stationnaire (INFERENCE).
- Persistance : `Workspace.save()` → 1,5 Ko ; rechargé, même distribution sur la sonde. Déterminisme : sélection identique sur 3 `PYTHONHASHSEED`.
- Sensibilité : une seule mise à jour (coût −1, proba 0,5) fait passer la distribution d'uniforme à [0,93 ; 0,03 ; 0,03] au taux d'apprentissage par défaut (OBSERVED, première sonde). Les 5 réglages VW essayés couvrent un `regret_all` de 2,04 à 4,26 (✔ mes calculs, §3.9).
- Coût : 13,2 s pour 12 000 tirages contre 0,3-2,7 s (✔ 13,23-13,37 s selon `select_update_seconds`).
- Maintenance : 9.11.9 le 2026-09-27 (9.11.8 le même jour) ; 182 commits/365 j dont **178 sous un seul nom d'auteur** ; page d'issues « 0 » (fiabilité inconnue). Non vérifiable.
- Tests C++ non compilés (UNKNOWN). Licence BSD-3 ; 0 dépendance Python ; 34 Mo.

#### MABWiser
- 5 301 lignes ; `MAB(arms, learning_policy, neighborhood_policy, seed)` ; API par lots (`fit`, `partial_fit`, `predict`, `predict_expectations`, `add_arm`, `remove_arm`, `warm_start`).
- **Aucun oubli** (`grep decay|discount|window|forget` sans résultat) ; estimations = sommes/compteurs cumulés.
- **Défaut de démarrage à froid (PROVEN)** : `_UCB1` initialise `arm_to_expectation = 0` ; `predict_expectations()` renvoie **0** pour un bras non entraîné ou ajouté par `add_arm` : avec des récompenses positives, une nouvelle cellule est classée **dernière**. Sonde du rapport : `{'a':1.55,'b':2.48,'c':0,'d':0}`. [moi] J'ai refait une sonde : `{'a': 2.08, 'b': 2.88, 'c': 0, 'd': 0, 'e': 0}` après `add_arm('e')` ✔ (mêmes structures : zéro pour les non entraînés y compris ajoutés).
- Robustesse : NaN/None/inf rejetés (`TypeError: Rewards cannot contain None, nan or infinity.`) ✔ [moi] ; `predict` avant `fit` → `Exception("Call fit before prediction")` ✔ ; `fit` avec un bras inconnu renvoie `None` silencieusement ✔ [moi].
- Tests : 533 passés, 1 échec (`test_ridge.py::test_predict_ridge_scaler`, `TypeError` de conversion de scalaire NumPy) — cause = INFERENCE. Non vérifiable ici. Maintenance : dernier commit/version 2024-08-30 (760 jours), 0 commit en 365 j. Dépendances : 20 paquets, 474 Mo. Licence Apache-2.0.

#### Optuna
- `Study` ↔ `Storage` (mémoire, `RDBStorage` via SQLAlchemy, `JournalStorage`, proxy gRPC) ↔ `Sampler` ↔ `Pruner`. `RDBStorage` contient un chemin d'upsert propre à PostgreSQL (`storage.py` L806-807). Un mécanisme de « heartbeat » marque les essais orphelins comme échoués.
- `SuccessiveHalvingPruner.prune()` promeut un essai au palier suivant seulement s'il est dans la meilleure fraction 1/`reduction_factor` des valeurs des concurrents à ce palier ; sinon `TrialPruned` : **état terminal**.
- Déterminisme (PROVEN sur petit cas) : 60 essais avec `RandomSampler` seedé + SHA(reduction_factor=3) rejoués : mêmes états/étapes (54 élagués / 6 terminés). TPE seedé non testé.
- Issue #6777 « TPESampler RSS grows unbounded… » (DOCUMENTED_CLAIM). Tests : 125 passés (`pruners_tests` + `test_heartbeat.py`), nécessitant `cmaes` et `fakeredis`. Maintenance : 5.0.0 le 2026-09-04 ; 1 793 commits/365 j, 102 auteurs ; 9 issues ouvertes. Dépendances 11 paquets, 139 Mo. Licence MIT.
- Caveat d'ajustement : Optuna optimise des hyper-paramètres d'un objectif ; « cellule = essai », « report(step) = un incrément de preuve » est naturel (INFERENCE), mais pas de notion de nouveaux essais arrivant plus tard dans une compétition, de dérive, ni de « non observé ».

#### SMPyBandits
- Contient `SlidingWindowUCB`, `DiscountedUCB` (astuce γ^{1+Δ}), `DiscountedThompson`, `AdSwitch`, `CUSUM_UCB`, `Monitored_UCB`, `Exp3R/S/++`, etc. Propriété intéressante : SW-UCB renvoie +∞ pour un bras sans tirage dans la fenêtre (garde de re-exploration automatique). Nombre de bras **fixé** à la construction.
- **Import cassé (PROVEN)** : `from SMPyBandits.Policies import SWUCB` → `ImportError: cannot import name 'btdtri' from 'scipy.special'` (SciPy 1.17.1). Métadonnées avec classifiers Python 2.7/3.4 ; dépend de `scikit-optimize` (1 commit, dernier en 2021-10). Non benchmarké. Je n'ai pas rejoué cette installation (?).
- Maintenance : dernière étiquette 0.9.7 (2019-10-25) ; 2 commits en 365 j (fusions communautaires de juin 2026) ; 27 issues (WebFetch). Licence MIT.

#### Candidats métadonnée seule
Ax 1.3.1 (MIT ; 747 commits/365 j ; `pip install --dry-run` résout **69 paquets** dont torch 2.14.0, triton, ~14 roues NVIDIA CUDA) ; contextualbandits 0.3.30 (BSD-2 ; 7 commits, 3 auteurs, exige `cython`) ; OSS Vizier 0.1.24 (Apache-2.0 ; deps `grpcio, protobuf, sqlalchemy…`). Aucune exécution.

### 3.3 Rapport 03 — Résultats du banc principal (20 graines, moyennes)

Colonnes : `zero` = cellules jamais tirées (sur 160) ; `stale` = fraction obsolète en fin de run ; `cov≥10` ; `Gini (pre)` et `top-10 % (pre)` = concentration entre les tours 300 et 600 ; `impr` / `degr` = part des tirages sur les cellules améliorées / dégradées pendant les tours 750-800 (uniforme ≈ 0,06, soit 10/160 = 0,0625) ; `gap` = gaspillage sur le trou ; `regret` = regret sur tout le run ; `s/run` = secondes de sélection+mise à jour pour un run de 12 000 tirages. Toutes ces valeurs ont été recalculées par moi depuis les JSON bruts et concordent avec `main_tables.md` (§3.9).

| Règle | zero | stale | cov≥10 | Gini pre | top-10 % pre | impr | degr | gap | regret | s/run |
|---|---|---|---|---|---|---|---|---|---|---|
| ref_roundrobin | 0 | 0 | 1,00 | 0,01 | 0,10 | 0,064 | 0,060 | 0,12 | 4,51 | 0,02 |
| ref_ducb γ=0,98 | 0 | 0 | 1,00 | 0,22 | 0,20 | 0,14 | 0,043 | **0,89** | 4,01 | 0,28 |
| river_ucb_mean | **38,1** | **0,82** | 0,64 | 0,89 | 0,89 | 0,26 | 0,003 | 0,15 | 1,04 | 1,00 |
| river_ucb_ew (fading 0,9) | 13,9 | 0,15 | 0,76 | 0,44 | 0,28 | 0,13 | 0,000 | 0,72 | 4,51 | 1,06 |
| river_ts_beta | **33,6** | **0,72** | 0,45 | 0,91 | 0,92 | 0,024 | 0,010 | 0,12 | 1,01 | 2,67 |
| river_eps_ew (ε=0,1) | 0,05 | 0,25 | 0,82 | 0,78 | 0,68 | 0,45 | 0,013 | 0,08 | 1,59 | 0,28 |
| river_exp3 | ERREUR `KeyError` | | | | | | | | | |
| mabwiser_ucb1 | **139** | **0,87** | 0,13 | 0,94 | 1,00 | **0,00** | 0,58 | 0,27 | 3,10 | 0,80 |
| mabwiser_ts | 31,4 | 0,73 | 0,41 | 0,90 | 0,92 | 0,020 | 0,015 | 0,10 | 1,00 | 1,35 |
| mabwiser_eps (ε=0,1) | 0,15 | 0,27 | 0,43 | 0,87 | 0,90 | 0,032 | 0,109 | 0,17 | 1,45 | 0,83 |
| vw_eps_default (ε=0,1) | 0,1 | 0,25 | 0,51 | 0,84 | 0,82 | 0,047 | 0,049 | 0,15 | 2,04 | 13,2 |
| vw_eps_constlr | 0,05 | 0,26 | 0,42 | 0,87 | 0,88 | 0,031 | 0,140 | 0,11 | 2,35 | 13,2 |
| vw_squarecb_constlr | 0 | 0,002 | 1,00 | 0,56 | 0,57 | 0,027 | 0,456 | 0,13 | 3,95 | 13,4 |

(Source : 03 §3, confirmé par `bench/results/main_tables.md` et recalcul depuis `bench/results/main/*.json`.)

#### Écarts-types (extraits de `main_tables.md`, 20 graines)
| Règle | zero | stale | regret all |
|---|---|---|---|
| river_ucb_mean | 38,1 ± 1,3 | 0,819 ± 0,1 | 1,04 ± 0,14 |
| river_ts_beta | 33,6 ± 1,9 | 0,723 ± 0,038 | 1,01 ± 0,098 |
| river_ucb_ew | 13,9 ± 3,3 | 0,153 ± 0,026 | 4,51 ± 0,13 |
| river_eps_ew | 0,05 ± 0,22 | 0,247 ± 0,031 | 1,59 ± 0,079 |
| mabwiser_ucb1 | 139 ± 2 | 0,867 ± 0,012 | 3,1 ± 0,23 |
| mabwiser_ts | 31,4 ± 1,8 | 0,726 ± 0,036 | 1,0 ± 0,081 |
| vw_squarecb_constlr | 0 ± 0 | 0,00219 ± 0,003 | 3,95 ± 0,2 |
| ref_roundrobin | 0 | 0 | 4,51 ± 0,11 |
| ref_ducb γ=0,98 | 0 | 0 | 4,01 ± 0,074 |

Ce sont des écarts-types **entre graines** (dispersion), pas des erreurs-types ni des intervalles de confiance. Pas de test de signification dans la lane. Avec 20 graines, l'erreur-type de la moyenne vaut à peu près sd/√20 [moi], soit ~0,03 pour un regret de sd 0,14 : les grands écarts (1,0 contre 4,5) sont hors de doute pour ce scénario ; les petits (ex. 4,01 contre 4,51) ne le sont pas nécessairement sans apparier.

#### Les 6 constats du rapport, avec mon commentaire

1. **L'allocation guidée par la récompense affame (PROVEN).** Les lignes à regret le plus bas (river_ucb_mean 1,04, les deux Thompson ≈ 1,0) laissent **20-24 %** des cellules jamais touchées (31 à 38 sur 160) et **72-82 %** obsolètes en fin de run. Pour `river_ucb_mean` graine 0, l'ensemble non tiré = des cellules **établies**. **J'ai vérifié en rejouant** : graine 0, `river_ucb_mean` 39 cellules jamais tirées dont 39 établies ; `river_ts_beta` 34 dont 34 établies ✔. Autrement dit, les cellules qui avaient déjà de l'historique sont celles qui sont abandonnées, parce que leurs moyennes passées les ont placées sous celles des nouvelles cellules explorées avec un bonus élevé.
   - Nuance [moi] : « 20-24 % » est vrai pour `river_ucb_mean` (23,8 %), `river_ts_beta` (21,0 %) et `mabwiser_ts` (19,6 %) ; `mabwiser_ucb1` est à 86,7 % (139/160), donc la fourchette du rapport ne parle pas de lui.
2. **Démarrage à froid des nouvelles cellules.** MABWiser-UCB1 : 139/160 jamais tirées, pépites trouvées 0 %. Alpha à 2 ou 5 : 122 et 120 cellules jamais tirées (balayage, 5 graines) ✔. River UCB (inconnu ⇒ +∞) et Thompson atteignent les nouvelles cellules en médiane 3,5-4,5 tours ; les règles epsilon-greedy prennent 94-101 tours ; VW-squarecb 16,8. ✔ (`ttf_new_median` : 3,5 ; 4,025 ; 4,5 ; 93,7 à 101,2 ; 16,75).
3. **Adaptation faible pour les estimateurs cumulés (PROVEN).** 150-200 tours après le changement, seuls 0-3 % (MABWiser/TS/VW-ε) à 26 % (River UCB-Mean, « exploration chanceuse ») des tirages atteignent les 10 cellules améliorées ; `mabwiser_ucb1` n'y arrive jamais (0,00) et garde 58 % de l'attention sur les dégradées ; `river_eps_ew` atteint 45 %. ✔ tous ces chiffres.
4. **L'oubli seul ne suffit pas (PROVEN).** `river_ucb_ew` : regret 4,51 = round-robin 4,51 dans le run principal ; `regret_all` de 4,25 à 4,79 sur 9 réglages (fading ∈ {0,9 ; 0,97 ; 0,99} × delta ∈ {0,1 ; 0,5 ; 1,0}) : jamais mieux qu'uniforme. Cause avancée : le bonus utilise des compteurs cumulés (voir source). ✔ chiffres (min 4,25, max 4,795).
5. **Les cellules muettes détournent l'attention (PROVEN dans ce scénario).** Pendant le trou, les règles à oubli/UCB dépensent **72-89 %** de l'attention sur les 20 cellules muettes (`river_ucb_ew` 0,72 ; `ref_ducb@0,98` 0,89 ; `@0,995` 0,83) contre 8-17 % pour les règles cumulatives. Mécanisme (INFERENCE) : un tirage qui ne renvoie rien ne change aucun état, donc une cellule à indice élevé le reste et est retirée : boucle de rétroaction. C'est l'analogue direct de « l'absence de preuve n'est pas une preuve négative » : aucune bibliothèque revue n'offre de canal « essayé, pas de preuve ».
   - Écarts [moi] : (i) la borne « 8-17 % pour les règles cumulatives » exclut `mabwiser_ucb1` (0,267) et ses réglages `alpha=2` (0,484) et `alpha=5` (0,542), qui sont aussi des règles cumulatives. (ii) « 72-89 % » exclut des réglages `river_ucbew` du balayage à 0,686 (9@0,1) et 0,745 (9@0,5). (iii) au sens strict du rapport lui-même (03 §4), pour `ref_ducb` γ=0,998 la fraction est 0,33 et γ=0,9995 0,13 : le détournement dépend fortement de γ.
6. **VW squarecb : la seule règle externe sans famine ni concentration excessive (Gini 0,56)**, mais au coût le plus élevé (13 s/run) et avec la pire adaptation (46 % d'attention gardée sur les cellules dégradées à lr = 0,05 ; regret 3,95). Le taux d'apprentissage est un bouton monotone entre « uniforme » et « glouton » (balayage), donc « le réglage remplace la famine par de la lenteur d'adaptation ». ✔ chiffres.

#### Lecture en langage simple
- « Glouton » (avide de récompense) = ça se concentre sur quelques cellules et abandonne le reste. Bon regret, mais 1 cellule sur 5 ou 6 n'est jamais regardée et les preuves des autres vieillissent.
- « Oubli » (D-UCB) = les preuves anciennes s'estompent, l'attention tourne plus, mais l'estimation devient bruitée et le regret remonte vers celui de l'uniforme.
- Aucune règle du tableau n'a simultanément bon regret, pas de famine et bonne adaptation dans la configuration de base.

### 3.4 Rapport 03 — Balayages de sensibilité (§4, `sweep_tables.md`)

5 graines pour les règles externes, 20 graines pour `ref_ducb*`.

| Règle | Réglage | zero | stale | impr 150-200 | gap | regret all |
|---|---|---|---|---|---|---|
| ref_ducb | γ=0,98 (run principal) | 0 | 0 | 0,14 | 0,89 | 4,01 |
| ref_ducb | γ=0,99 | 0 | 0 | 0,191 | 0,857 | 3,57 |
| ref_ducb | γ=0,995 | 0 | 0 | 0,345 | 0,825 | 2,98 |
| ref_ducb | **γ=0,998** | 7,85 | 0,049 | 0,851 | 0,331 | 1,72 |
| ref_ducb | γ=0,9995 | 37,3 | 0,671 | 0,67 | 0,129 | 1,00 |
| ref_ducb_fresh | γ=0,998, garde 200 | **0** | **0** | 0,854 | 0,283 | 1,717 |
| river_ucbew | 9 réglages | 10,6 à 21,4 | 0,135-0,322 | 0,065 à 0,237 | 0,686 à 0,883 | 4,25 à 4,795 |
| mabwiser_ucb1 | alpha=0,5/2/5 | 139 / 122,4 / 120 | 0,867 / 0,765 / 0,75 | 0 / 0 / 0 | 0,267 / 0,484 / 0,542 | 3,10 / 3,20 / 3,72 |
| vw_squarecb | lr=0,005/0,05/0,5 | 0/0/0 | ≈0 | 0,045 / 0,027 / 0,022 | 0,091 / 0,126 / 0,142 | 4,26 / 3,95 / 3,35 |

Détail complémentaire (`sweep_tables.md`) : Gini(pre) de VW squarecb 0,331 / 0,562 / 0,711 ; part dégradée 150-200 : 0,119 / 0,456 / 0,502 ; `cov≥10` de `ref_ducb_fresh@0,998` = 0,87 contre 0,854 sans garde ; `max_gap_p95` = 203 avec garde contre 1 170 sans (sans garde, γ=0,998).

**Interprétation du rapport (INFERENCE)** : le facteur d'oubli fait un compromis monotone couverture ↔ vitesse d'adaptation ; une revisite forcée d'obsolescence domine le point γ=0,998 dans ce scénario ; cela montre la **forme** de l'espace de conception, **pas** que γ=0,998 ou le seuil 200 se généralisent (choisis après avoir vu les résultats sur le même scénario ⇒ dans l'échantillon).

**Mon complément [moi]** :
- Comparaison appariée par graine `ref_ducb_fresh@0,998` moins `ref_ducb@0,998` (20 graines) : `regret_all` −0,004 (sd 0,071 ; 12 graines meilleures, 8 pires : pas de différence) ; `zero_pull_cells` −7,85 (sd 2,4 ; 20 graines sur 20 meilleures) ; `stale_frac_end` −0,049 (20/20) ; `share_improved_150_200` +0,003 (sd 0,082 : pas de différence) ; `cov≥10` +0,016 (15 graines sur 18 non nulles). Le rapport dit « même regret, même adaptation, famine supprimée » : **✔** exact.
- Le facteur γ étant appliqué par tour de 10 tirages, γ=0,998 a un horizon d'environ 1/(1−γ) = 500 tours, γ=0,9995 environ 2 000 tours, soit plus que les 1 200 tours du run : γ=0,9995 est presque « cumulatif » et se comporte comme tel (zero 37,3 ; regret 1,00), en accord avec les règles cumulatives. Le point γ=0,998 est donc un coude à l'intérieur de la grille (pas un bord), mais la grille ne contient pas de point entre 0,998 et 0,9995 ni au-delà de 0,998 pour la garde.
- Effet de chauffe [moi] : la phase de chauffe applique 800 mises à jour avec oubli avant le tour 0. La taille d'échantillon effective moyenne d'une cellule établie à la fin de la chauffe est de **12,5 pour γ=0,98**, 99,8 pour γ=0,998 et 164,9 pour γ=0,9995 (au lieu de 200 tirages bruts). Les règles à oubli fort démarrent donc avec une mémoire des cellules établies très amoindrie par rapport aux règles cumulatives ; cela fait partie de la dynamique mesurée mais n'est pas discuté dans le rapport.

### 3.5 Rapport 03 — Coût et dépendances (§6)

| | dépendances (venv propre) | site-packages | RSS pic | sélection+màj / 12 000 tirages |
|---|---|---|---|---|
| River | 4 paquets | 256 Mo (numpy 97 Mo) | ~173-183 Mo | 0,28-2,7 s |
| MABWiser | 20 paquets | 474 Mo | ~172 Mo | 0,8-1,35 s |
| VW | 0 | 34 Mo | ~71 Mo | **13,2 s** |
| Optuna | 11 paquets | 139 Mo | non mesuré | non applicable |
| Ax (dry-run) | 69 paquets dont torch + CUDA | non installé | — | — |
| `ref_*` | 1 | 97 Mo | 47 Mo | 0,02-0,32 s |

Les RSS et temps par règle des JSON bruts concordent (river 173-183 Mo, mabwiser 172, vw 71, ref 47 ; `select_update_seconds` river_ts_beta 2,67 ; vw 13,2-13,4) ✔. Les tailles de paquets et le nombre de dépendances : non vérifiables (?). Le rapport précise que l'extrapolation à 10^5-10^6 cellules n'a **pas** été testée (UNKNOWN).

### 3.6 Rapport 04 — Revue adverse (résumé chiffré)

| Cible | Attaques | Gravités du rapport | Remarque |
|---|---|---|---|
| River | R1 à R11 | R1 (famine) Haute ; R2 (oubli sans échantillon effectif) Haute ; R3 (NaN) Moyenne-Haute ; R4 (cellules muettes) Haute ; R5 Exp3 Basse-Moyenne ; R6 tests Moyenne ; R7 persistance opaque Moyenne ; R8 pickle et versions UNKNOWN ; R9-R10 Basse-Moyenne ; R11 UNKNOWN | contre-poids : 299 commits/39 auteurs, BSD-3, déterministe, liste de bras dynamique, pickle exact |
| VW | V1 à V10 | V1 bus factor ≈ 1 Haute ; V4 dominé par le réglage Haute ; V5 adaptation faible Haute ; V3 lent Basse-Moyenne ; V8 avantage principal non testé | 5 réglages : regret 2,04-4,26, Gini 0,33-0,84 ✔ |
| MABWiser | M1 à M8 | M3 démarrage à froid **Critique** ; M1 périmé Haute ; M4 aucun oubli Haute | M8 points positifs (NaN rejeté, déterministe, Apache-2.0) |
| Optuna | O1 à O7 | O1 élagage terminal Haute ; O4 stockage RDB = second stockage d'autorité Haute ; O2 Moyenne-Haute | O5 = issue #6777 ; O4 mentionne l'issue #6868 (« RDBStorage shifts trial timestamps… ») |
| SMPyBandits | S1 à S5 | S1 import cassé « Disqualifying » ; S2 abandonné Haute | S5 : reste utile comme spécification |
| Direction favorisée (D-UCB + garde) | P1 à P6 | P1 réglage dans l'échantillon ; P2 frontière γ ; P3 détournement persiste pour γ ≤ 0,995 (0,83-0,89 : ✔) ; P4 risque de boucle de la garde sur une cellule muette **permanente**, non testé ; P5 risque de dérive vers l'allocation de capital si la récompense est liée à la performance réalisée ; P6 mainteneur = nous | — |

**Conclusions transversales de 04 §7** : (1) chaque allocateur guidé par la récompense présente au moins un de : famine des établies, famine des nouvelles, détournement par cellules muettes, non-adaptation (PROVEN) ; un enveloppeur (wrapper) est inévitable ; (2) « populaire n'est pas apte » (MABWiser) ; (3) le fardeau de réglage est réel (doctrine n°9) ; (4) limites du banc : aucune conclusion quantitative ne doit être transportée sur les données AurumShift sans rejeu sur le vrai système.

### 3.7 Rapport 03 §5 — Déterminisme (résultats bruts)

Chaque règle (graine 0) exécutée dans 3 processus distincts avec `PYTHONHASHSEED` = 0, 1, 12345 ; SHA-256 de la suite complète (tour, cellule) comparée. J'ai lu les 33 JSON de `results/determinism/` : 11 règles × 3 processus.

| Règle | Résultat brut | Hash (16 hex) |
|---|---|---|
| river_ucb_mean | 3 identiques | fcb14d6465debdc6 |
| river_ucb_ew | 3 identiques | f405b930a52175ea |
| river_ts_beta | 3 identiques | b387f924343f17ce |
| river_eps_ew | 3 identiques | 0a10e831fea2fa18 |
| mabwiser_ucb1 | 3 identiques | 9f4bc11b94b4b343 |
| mabwiser_ts | 3 identiques | c4248902a88ef929 |
| mabwiser_eps | 3 identiques | ad88f13f7ea31860 |
| vw_eps_default | 3 identiques | 9ae5609d6c452325 |
| vw_squarecb_constlr | 3 identiques | 46d7520284cf55f9 |
| ref_ducb | 3 identiques | 1751d3f1d60bd022 |
| river_exp3 | crash dans les 3, aucun hash | — |

Les hash de la graine 0 des runs principaux (`results/main/*.json`) sont **égaux** à ceux du dossier `determinism/` [moi] (ex. river_ucb_mean fcb14d64…, ref_ducb 1751d3f1…) ✔. Non testés : `vw_eps_constlr` et `ref_roundrobin` (absents de `determinism/`), aucune autre graine que la graine 0, aucun autre poste.

### 3.8 Rapports 05, 06, 07 (synthèse chiffrée)

**05 — Licence et maintenance** : tableau des 15 projets (dernier commit, dernière version, commits 365 j / 90 j, auteurs, issues ouvertes, verdict). Points saillants : River actif (299/69/39), Optuna très actif (1 793/430/102), VW actif mais mono-mainteneur (178 commits sous un nom), MABWiser périmé (0 commit ; 760 jours), SMPyBandits abandonné. Licences : la plupart permissives ; **irace = GPL (≥ 2)** (copyleft) ; **GrowthBook = MIT-Expat + licence « Enterprise » propriétaire dans des dossiers** ; **tqdm (dépendance d'Optuna) = MPL-2.0 AND MIT** (copyleft faible au niveau du fichier, marqué pour revue juridique) ; aucune GPL/AGPL parmi les roues installées (OBSERVED pour les versions listées). Le rapport rappelle ne pas être un avis juridique et que la licence d'AurumShift est inconnue. Tous ces chiffres/dates : non vérifiables ici (?).

**06 — Surface d'intégration générique** : contrat minimal d'un allocateur, dérivé des échecs observés : résultat à **trois valeurs** par tentative (`EVIDENCE(value)` / `ATTEMPTED_NO_EVIDENCE` / `NOT_ATTEMPTED`) ; obsolescence comme état de premier rang (temps depuis la dernière **preuve** ≠ temps depuis la dernière **tentative**) ; jeu de cellules dynamique ; oubli qui réduit **valeur et compte** ; hygiène d'entrée (NaN) ; déterminisme (persister graine + position RNG) ; sélection par lot avant tout retour ; explicabilité (code de raison par choix : `EXPLORE_NEW`, `EXPLOIT_PROMISING`, `REVISIT_STALE`, `RECHECK_DEGRADING`). Exigences d'état PostgreSQL : état par cellule relationnellement inspectable (compteurs, sommes actualisées, dernière preuve, dernière tentative, nombre de tentatives sans preuve consécutives, statut) ; journal de décision en ajout seul ; « pas de lookahead » (le sélecteur ne voit que les preuves avec `available_at ≤ decision_time`). Frontière : le signal de récompense est une valeur d'information, jamais du P&L ; Bandits with Knapsacks exclus ; plafond dur de part par cellule/groupe. Tout est **INFERENCE** (étiquette du rapport), rien n'est testé. 5 questions ouvertes réservées au vrai dépôt.

**07 — Adjudication finale** : voir §4 et §5 ci-dessous.

### 3.9 Vérification indépendante des chiffres clés (rapport contre résultats bruts)

Méthode : recalcul en Python depuis `results/main/*.json`, `results/sweep/*.json`, `results/determinism/*.json`, et **rejeu du code** (`bench.py`) dans un environnement neuf avec numpy 2.4.6 / river 0.26.1 / mabwiser 2.7.4 pour 2 graines de 6 règles.

| # | Chiffre du rapport | Source du rapport | Mon calcul | Verdict |
|---|---|---|---|---|
| 1 | river_ucb_mean : 38,1 cellules jamais tirées, stale 0,82, regret 1,04 | 03 §3 | 38,15 ; 0,819 ; 1,039 | ✔ |
| 2 | river_ts_beta : 33,6 ; 0,72 ; 1,01 | 03 §3 | 33,65 ; 0,723 ; 1,015 | ✔ |
| 3 | mabwiser_ucb1 : 139 jamais tirées, 0 pépite, 87 % obsolète | 03 §3 | 138,75 ; 0 ; 0,867 | ✔ (arrondi) ; ✘ mineur : 02 §3 écrit « 138/160 », 03 écrit 139 |
| 4 | river_ucb_ew : regret 4,51 = round-robin 4,51 | 03 §3 | 4,506 vs 4,509 | ✔ |
| 5 | river_ucbew 9 réglages : regret 4,25-4,79 | 03 §4 | min 4,25, max 4,795 | ✔ |
| 6 | ref_ducb γ=0,998 : 7,9 / 0,05 / 0,85 / 0,33 / 1,72 | 03 §4 | 7,85 ; 0,049 ; 0,851 ; 0,331 ; 1,721 | ✔ |
| 7 | ref_ducb_fresh γ=0,998 : 0 / 0 / 0,85 / 0,28 / 1,72 | 03 §4 | 0 ; 0 ; 0,854 ; 0,283 ; 1,717 | ✔ |
| 8 | ref_ducb γ=0,9995 : 37,3 / 0,67 / 0,67 / 0,13 / 1,00 | 03 §4 | 37,3 ; 0,671 ; 0,67 ; 0,129 ; 1,004 | ✔ |
| 9 | mabwiser_ucb1 alpha 2 et 5 : 122 et 120 cellules jamais tirées | 03 §4 | 122,4 ; 120 | ✔ |
| 10 | vw_squarecb lr 0,005/0,05/0,5 : regret 4,26/3,95/3,35 ; degr 0,12/0,46/0,50 | 03 §4 | 4,258 / 3,947 / 3,353 ; 0,119 / 0,456 / 0,502 | ✔ |
| 11 | VW 5 réglages : regret 2,04-4,26, Gini 0,33-0,84 | 04 V4 | 2,041 à 4,258 ; 0,331 à 0,843 | ✔ |
| 12 | ttf des nouvelles cellules : 3,5-4,5 (UCB, Thompson) ; 94-101 (ε-greedy) ; 16,8 (squarecb) | 03 §3 | 3,5 ; 4,025 ; 4,5 ; 93,7-101,2 ; 16,75 | ✔ |
| 13 | river_eps_ew : 45 % d'attention sur les améliorées (150-200) | 03 §3 | 0,445 | ✔ |
| 14 | mabwiser_ucb1 : 58 % sur les dégradées ; vw_squarecb 46 % | 03 §3 | 0,584 ; 0,456 | ✔ |
| 15 | temps VW 13,2 s vs 0,28-2,7 s (« 5-47× ») | 02 §2, 03 | 13,23-13,37 s ; 0,278 à 2,671 s ; rapport 13,2/0,28 = 47 ; 13,2/2,67 = 5 | ✔ ; ✘ mineur : 04 V3 écrit « 45× plus lent que River/MABWiser » (avec MABWiser à 0,8 s le rapport est 16×) |
| 16 | Gaspillage sur trou : ref_ducb@0,98 = 0,89 ; @0,995 = 0,83 ; river_ucb_ew 0,72 | 03 §3.5 | 0,89 ; 0,825 ; 0,724 | ✔ |
| 17 | « 8-17 % pour les règles cumulatives » | 03 §3.5 | river_ucb_mean 0,145 ; ts 0,123 et 0,097 ; eps 0,168 ; **mabwiser_ucb1 0,267** ; **alpha 2 : 0,484 ; alpha 5 : 0,542** | ✘ partiel (la fourchette omet MABWiser UCB1 et ses variantes) |
| 18 | Déterminisme : 3 hash identiques par règle | 03 §5 | 11 règles × 3 processus, 10 avec un seul hash, Exp3 aucun | ✔ |
| 19 | Exp3 : `KeyError: 26` à la chauffe | 02 §1, `river_exp3.json` | trace : `river_exp3.py` ligne 100 `self._probabilities[arm_id]` ; `KeyError: 26` | ✔ |
| 20 | Graine 0 river_ucb_mean : l'ensemble non tiré = cellules établies (« debug run ») | 03 §3 (1) | rejeu : 39 cellules dont 39 établies ; river_ts_beta 34 dont 34 établies | ✔ |
| 21 | Pickle River continu à l'identique ; 122 Ko pour Thompson (30 bras) | 02 §1 | rejeu : « identical continuation: True » ×3 ; 121 923 octets | ✔ |
| 22 | NaN empoisonne River UCB (`IndexError` au `pull` suivant) | 02 §1, 04 R3 | rejeu : `IndexError: list index out of range` | ✔ |
| 23 | MABWiser : NaN rejeté ; bras inconnu accepté | 02 §3 | rejeu : `TypeError: Rewards cannot contain None, nan or infinity.` ; `fit` bras inconnu → `None` | ✔ |
| 24 | MABWiser : bras non entraîné/ajouté = expectation 0 | 02 §3 | rejeu : `{'a':2.08,'b':2.88,'c':0,'d':0,'e':0}` | ✔ |
| 25 | `UCB` de River : bonus avec `_n` et `_counts` cumulés | 02 §1 | lecture du source 0.26.1 installé | ✔ |
| 26 | Reproductibilité de bout en bout : les `seqhash` des runs principaux sont-ils reproductibles ? | non affirmé tel quel | rejeu de 2 graines × 6 règles (ref_roundrobin, ref_ducb, ref_ducbfresh@0.998, river_ucb_mean, river_ucb_ew, river_ts_beta) : **12/12 hash égaux** aux JSON fournis ; `zero_pull_cells` et `regret_all` égaux au chiffre près | ✔ (nouveau) |
| 27 | Exemple de chiffres de VW (rejeu) | 03 | non rejoué (VW non installé, 13 s/run) | ? |
| 28 | Tests : Optuna 125 passés ; MABWiser 533 passés/1 échec ; River 3 passés/22 ignorés | 02 | aucune sortie de tests dans les fichiers ; clones absents | ? |
| 29 | Import SMPyBandits cassé (`btdtri`) | 02 §5 | non rejoué | ? |
| 30 | Stats de maintenance (commits, auteurs, dates de version, issues) | 05 | aucun accès aux clones ni à PyPI | ? |
| 31 | 14 identifiants arXiv concordent | 01 | aucun accès web | ? |
| 32 | Poids des dépendances (256/474/139/34 Mo, 4/20/11/0 paquets) | 03 §6, 05 | non recalculé | ? |
| 33 | Seuil `ref_ducb` vs `ref_ducb_fresh` identiques à γ=0,98 (« garde ne se déclenche jamais », `max_gap` ≈ 117 < 200) | 03 §4 | `main_tables.md` : lignes identiques ; `max_gap_p95` 117 ± 2,6 | ✔ |

Bilan : 26 vérifications ✔ (dont 2 avec un écart mineur ✘ : n°3 et n°15), 1 ✘ partiel (n°17), 6 ? non vérifiables (n°27 à 32) (surtout la métadonnée externe : clones, PyPI, arXiv, tests). **Aucun écart n'invalide une conclusion** ; ils indiquent des formulations imprécises.

---

## 4. Candidats / méthodes évalués un par un

Définitions du rapport (07 §3) : **ADOPT** = utiliser tel quel derrière une fine enveloppe ; **ADAPT** = réutiliser code/idées avec modification ; **PARK** = prometteur mais preuves insuffisantes ou pas nécessaire maintenant, à revisiter selon un déclencheur ; **REJECT** = ne pas poursuivre pour ce problème. « Confiance » = confiance dans la classification.

### 4.1 Tableau de classification (07 §3.1) et justification

| Composant / approche | Classe | Confiance | Justification chiffrée | Condition de changement |
|---|---|---|---|---|
| Aucun système entier | ADOPT : aucun | Haute | constat n°1 | — |
| River `stats.*` (Mean, EWMean, Var) et `utils.Rolling` comme briques d'estimation | ADAPT | Moyenne | source lu ; BSD-3 ; léger ; mais l'oubli doit s'accompagner de compteurs actualisés (R2) | à confirmer sur la latence réelle des preuves |
| Forme d'API River `Policy` (liste de bras par appel, graine, `clone`) | ADAPT (patron d'API) | Moyenne | jeu de bras dynamique fonctionne (`ref` tardives, 03) ; déterminisme PROVEN | — |
| River `UCB / ThompsonSampling / EpsilonGreedy / BayesUCB` livrés tels quels | REJECT (tels quels) | Haute | famine et non-adaptation PROVEN : ucb_mean 38,1 jamais tirées, ts 33,6, regret glouton ≈ 1,0 avec 72-82 % obsolètes | — |
| River `Exp3` | REJECT | Haute | `KeyError` à la chauffe/au lot | — |
| River `drift.ADWIN/PageHinkley/KSWIN` comme signaux de dégradation | PARK | Faible-Moyenne | présent au source ; **effet sur l'allocation inconnu** | première expérience de suivi : redémarrage sur dérive contre D-UCB en scénario v2 |
| VW `cb_explore_adf` / `--squarecb` | PARK | Moyenne | seule règle externe sans famine (zero 0 ; Gini 0,56) mais dominée par le réglage, lente (13,2 s), mono-mainteneur ; **partage de variables non testé** | cellules qui partagent des variables utiles **et** trop peu d'échantillons par cellule |
| VW `--epsilon_decay` | PARK | Faible | mécanisme au source ; calendrier par défaut décroissant ; non benchmarké | besoin d'une promotion de configurations gardée statistiquement |
| MABWiser (toute politique) | REJECT | Haute | périmé 760 j ; démarrage à froid PROVEN (139/160) ; aucun oubli ; 1 test en échec ; 474 Mo | — |
| Optuna comme ordonnanceur d'attention | REJECT | Moyenne | non-adéquation de forme ; élagage terminal (O1/O2) ; second magasin d'autorité (O4) | — |
| Logique des paliers SHA/ASHA réinterprétée en « niveaux d'attention » non terminaux | ADAPT (idée seulement) | Faible-Moyenne | sémantique lue ; déterminisme d'une étude seedée PROVEN ; **effet inconnu** | tester en scénario v2 |
| Heartbeat / essai orphelin d'Optuna | ADAPT (idée seulement) | Faible | code + 125 tests observés | si la collecte de preuves tourne sur des workers peu fiables |
| Optuna en recherche d'hyper-paramètres à l'intérieur d'une cellule | PARK | Moyenne | hors mission ; MIT ; sain | quand la recherche de config par cellule devient un besoin |
| Optuna `RDBStorage`/schéma PostgreSQL | REJECT (en second stockage) | Moyenne | schéma/alembic propres ; issue #6868 | — |
| Paquet SMPyBandits | REJECT (dépendance) | Haute | import cassé PROVEN ; abandonné | — |
| Algorithmes SMPyBandits (D-UCB, SW-UCB, TS actualisé, CUSUM-UCB, AdSwitch) comme **spécification** | ADAPT | Moyenne-Haute | code MIT lisible ; D-UCB = conception favorisée par le banc | — |
| D-UCB avec compte **et** valeur actualisés | ADAPT | Moyenne | `ref_ducb` (code de l'auteur) : frontière PROVEN dans l'échantillon | valider hors échantillon, autres familles de scénarios |
| SW-UCB (+∞ pour bras absent de la fenêtre) | ADAPT | Faible-Moyenne | code lu ; propriété de re-exploration intégrée ; non benchmarké | comparer avec la garde d'obsolescence |
| **Revisite forcée d'obsolescence + canal `ATTEMPTED_NO_EVIDENCE` avec retrait borné (backoff)** | ADAPT / petit CUSTOM | Moyenne | garde PROVEN dans l'échantillon (zero 0, regret 1,717) ; canal motivé par le détournement PROVEN ; backoff non testé | concevoir et tester le backoff avant tout |
| Thompson sampling actualisé | PARK | Faible | seule implémentation trouvée inexécutable ; non testé | si l'exploration probabiliste est préférée |
| SHA / Hyperband comme élagage **terminal** de cellules | REJECT | Moyenne | contredit « l'absence de preuve n'est pas une preuve négative » (INFERENCE) | — |
| Population Based Training | PARK | Faible | conçu pour co-évoluer poids+hyper-paramètres ; faible adéquation ; infrastructure Ray | seulement si les configurations (pas les cellules) doivent évoluer |
| Ax / BoTorch | PARK | Moyenne | autre problème (optimisation bayésienne) ; 69 paquets dont torch/CUDA | recherche de configuration à évaluations chères |
| contextualbandits | PARK | Faible | BSD-2, mono-auteur, non exécuté | si une bibliothèque contextuelle avec bootstrap-TS est nécessaire et VW refusé |
| Google OSS Vizier | REJECT | Moyenne | infrastructure serveur ≫ besoin ; canal PyPI périmé | — |
| Ray Tune | REJECT (infra) / technique PBT PARK | Moyenne | runtime cluster ; internes non relus | — |
| irace (méthodologie de course, R, GPL) | PARK | Faible | pertinent ; GPL + runtime R ; non relu en profondeur | si un plan de course est requis et que le juridique accepte un usage par processus |
| Nevergrad, modAL, Open Bandit Pipeline, scikit-multiflow | REJECT | Haute | dormants/abandonnés ou mauvais problème | — |
| GrowthBook et SaaS d'expérimentation | REJECT | Haute (GrowthBook) / Faible (SaaS non examinés) | infra de plateforme ; licence mixte ; SaaS opaque par règle de mission | — |
| Bandits with Knapsacks et méthodes « capital » | REJECT (pour cet usage) | Haute | ligne rouge : un ordonnanceur de recherche n'est pas un allocateur de capital | — |
| Apprentissage actif (échantillonnage par incertitude, style modAL) | PARK | Faible | conceptuellement pertinent ; pas de candidat maintenu ; non testé | si des estimations de gain d'information par cellule deviennent disponibles |

### 4.2 Classement des 5 finalistes (07 §2)

| Rang | Candidat | Rôle | Raison en une ligne |
|---|---|---|---|
| 1 | River | primitives + forme d'API | actif, BSD-3, léger, bras dynamiques, graine ; mais ses règles prêtes à l'emploi affament et UCB+oubli est mal spécifié |
| 2 | Vowpal Wabbit | généralisation contextuelle / champion-challenger (conditionnel) | capacité unique, 0 dépendance Python ; mono-mainteneur, dominé par le réglage, le plus lent, avantage non testé |
| 3 | Optuna | logique de paliers de course + idée de heartbeat | projet le plus sain ; élagage terminal et schéma RDB propre en conflit avec nos contraintes |
| 4 | SMPyBandits | spécification exécutable d'algorithmes non stationnaires | meilleure couverture d'algorithmes ; inexécutable et abandonné |
| 5 | MABWiser | aucun | périmé, sans oubli, défaut de démarrage à froid, dépendances les plus lourdes |

### 4.3 Ce que la classification implique (07 §3.2, INFERENCE)

« Composer, pas adopter » : une fine couche d'allocation, inspectable en PostgreSQL, qui emprunte (a) la forme d'API de River et ses estimateurs, (b) D-UCB/SW-UCB de la littérature (SMPyBandits comme spécification), (c) une garde d'obsolescence et un canal « sans preuve » explicite, avec (d) détecteurs de dérive et niveaux de course comme ajouts mesurés ultérieurs. Le rapport dit que c'est un petit cœur CUSTOM justifié par les constats 1 à 4, arrivant « en dernier » selon la doctrine.

### 4.4 Tableau de robustesse (07 §4 — ce qui renverserait les conclusions)

| Conclusion | Confiance du rapport | Serait renversée par |
|---|---|---|
| Les politiques de bibliothèque guidées par la récompense affament dans un cadre de flotte | Haute (PROVEN, 20 graines, robuste sur 9+ réglages) pour ce scénario ; Moyenne pour données réelles | structure réelle de latence/récompense très différente de Bernoulli à bruit stationnaire |
| MABWiser / SMPyBandits ne doivent pas être des dépendances | Haute | renaissance en amont + correctifs |
| River = meilleure source de primitives | Moyenne | un banc montrant ses détecteurs de dérive inutiles, ou une contrainte Rust/version Python |
| VW = PARK plutôt que REJECT | Faible-Moyenne | expérience de partage de variables |
| Garde d'obsolescence + actualisation = bonne direction | Moyenne-Faible | scénarios held-out où la garde gaspille de l'attention (boucles sans preuve) |

---

## 5. Bloc final complet et explication

Cette lane n'a **pas de bloc de configuration final** (pas de clés gelées, pas de fichier `frozen_params`) : c'est une étude de paysage. Le bloc final équivalent est `07_FINAL_ADJUDICATION.md` §1 (constats), §2 (classement) et §3.1 (classification). Je reproduis §1 tel quel, puis j'explique, ligne par ligne, la classification (le tableau §3.1 est reproduit intégralement au §4.1 ci-dessus, en français, à l'identique pour les classes/confiances).

### 5.1 07 §1 « Headline findings » (texte du rapport, en anglais, à l'identique)

1. **No external project is a ready-made research-attention scheduler.** Libraries provide primitives (policies, estimators, drift detectors, racing rungs, stores). The behaviours that decide success here — staleness guard, treatment of "attempted, no evidence", forgetting that discounts *both* value and count — are not offered by any reviewed library. (OBSERVED across five source reviews; INFERENCE as the general statement.)
2. **Reward-greedy allocation starves.** The best-regret rules left ≈20–24% of cells untouched and 72–82% stale (PROVEN, `03` §3). Established cells silently fall out of attention as easily as new ones are ignored.
3. **Silent cells hijack attention** under forgetting/UCB rules when the policy learns only from observed evidence (72–89% of gap-window attention, PROVEN in this scenario) — a direct hit on "missing evidence is not negative evidence".
4. **A monotone design frontier exists** (discount γ: coverage ↔ adaptation) and a **staleness-forced revisit** removed starvation at equal regret in-sample (`ref_ducb_fresh` γ=0.998: 0 zero-pull cells, 85% attention to improved cells, regret 1.72 vs round-robin 4.51). This is my own reference code with in-sample parameters — direction, not a result to transport (`04` §6).
5. **Popular ≠ fit:** MABWiser fails cold start by construction (PROVEN) and is stale; SMPyBandits (best algorithm zoo) does not import on current SciPy (PROVEN).
6. **All tested policies are deterministic** across processes and `PYTHONHASHSEED` (PROVEN); River pickle continuation is exact (PROVEN). Determinism is not a differentiator; state *inspectability* is.

### 5.2 Explication ligne par ligne des constats

1. *Aucun projet n'est prêt à l'emploi.* Il existe des **briques** (règles de tirage, estimateurs, détecteurs de dérive, paliers de course, stockage) mais pas le **comportement complet** dont AurumShift aurait besoin : garde d'obsolescence, traitement de « essayé sans preuve », oubli correct. Force : moyenne (5 revues de code, mais 2 finalistes testés seulement en partie).
2. *L'allocation gloutonne affame.* Les règles qui optimisent la récompense (`river_ucb_mean`, les deux Thompson) ont le meilleur regret mais 20 à 24 % de cellules jamais regardées et 72 à 82 % d'obsolescence (mes rejeux : ✔). Ne s'applique qu'à ce scénario.
3. *Les cellules muettes détournent l'attention.* Quand une cellule ne renvoie rien, la règle ne change pas d'avis et la retire encore ; 72 à 89 % de l'attention de la fenêtre du trou y passe pour certains réglages. Écarts précisés en §3.3 (5).
4. *Frontière monotone + garde.* Plus γ est proche de 1, moins on oublie : moins de gaspillage, mais plus de famine. La garde retire la famine sans coût de regret **dans l'échantillon**. C'est le résultat qui motive le plus fortement la piste « petit cœur custom » — et c'est aussi le moins fiable (voir §7).
5. *Populaire ≠ adapté.* MABWiser est connu mais échoue au démarrage à froid par construction ; SMPyBandits est le plus riche mais inexécutable.
6. *Déterminisme.* Toutes les règles testées reproduisent la même séquence de choix sur plusieurs processus ; donc ce n'est pas ce qui départage les outils ; **la lisibilité de l'état** (pouvoir l'inspecter en base) le fait.

### 5.3 Correspondance « clés » de la classification

Comme il n'y a pas de dictionnaire de paramètres gelés, je décris les **colonnes** de la classification :

- `Component / approach` : ce qui est jugé (un composant précis d'un outil, pas l'outil entier).
- `Class` : ADOPT / ADAPT / PARK / REJECT, avec le qualificatif entre parenthèses (« idée seulement », « tels quels », « en second stockage »…) qui borne ce qui est jugé.
- `Confidence` : confiance dans la classe, pas dans l'outil.
- `Evidence and rationale` : preuves (étiquettes PROVEN/OBSERVED/INFERENCE/UNKNOWN).
- `Revisit trigger` : condition explicite pour changer de verdict.

---

## 6. Contrôles de validité

### 6.1 Tests de fuite d'information (lookahead / PIT)

- **Aucun test de fuite** n'est fourni : le banc est synthétique, l'oracle est séparé de la règle, les règles ne voient que `(cellule, récompense)` après le tour où elles sont tirées. Dans le code, la règle reçoit `obs` après le tour `t` et `avail` (les cellules du tour) ; l'oracle n'est utilisé que pour la métrique. La contrainte PIT d'AurumShift n'est pas testée : 06 §2 le dit explicitement (« nothing here tests it »).
- Point d'attention : l'environnement utilise `default_rng(10000+seed)` et la règle `default_rng(seed)`, flux distincts : pas de fuite par le générateur.

### 6.2 Déterminisme

PROVEN pour 10 règles sur graine 0 et 3 valeurs de `PYTHONHASHSEED` (§3.7). Aussi PROVEN et rejoué par moi : continuation identique après `pickle` pour 3 règles River. Non testé (UNKNOWN, déclaré par le rapport) : autre machine, autre BLAS, autre version de NumPy, autre mineure de Python, rechargement d'un modèle VW à mi-flux. [moi] : reproduction sur un autre environnement (même numpy/river/mabwiser, autre session) : 12 hash identiques sur 12 (2 graines × 6 règles), ce qui renforce la reproductibilité d'une exécution à l'autre, mais pas la portabilité inter-machine.

### 6.3 Contrôles négatifs et positifs

- **Contrôles positifs/références** : `ref_roundrobin` (étalon uniforme : regret 4,51) et l'oracle (regret 0 par définition). Les mesures de part sur cellules améliorées/dégradées sont comparables à 10/160 = 0,0625 (round-robin : 0,064 et 0,060 ✔).
- **Contrôle négatif** : aucun test de type « environnement sans signal » (où toutes les règles devraient être équivalentes à l'uniforme). Ce contrôle manque.
- Vérification de sanité interne : `ref_ducb` et `ref_ducb_fresh` identiques à γ=0,98 (la garde ne se déclenche pas, `max_gap` ≈ 117 < 200) : ✔ cohérent.

### 6.4 Erreurs et écarts déclarés en cours de route

Déclarés par le rapport :
- Accès GitHub bloqué (403) → comptes d'issues via un WebFetch résumé par un modèle (peu fiable).
- Exécution des tests de River et MABWiser **contre la roue installée** depuis un dossier `tests/` copié (au lieu de la CI du dépôt) : écart au « run the repo's CI ».
- Exp3 : crash (`KeyError`) → règle exclue du tableau.
- SMPyBandits : non patché, donc non exécuté (l'auteur n'a pas patché une dépendance périmée).
- VW : harnais approximatif (probabilité journalisée = probabilité à chaque tirage séquentiel sans remise, pas un IPS exact pour un lot) ; MABWiser : top-10 de `predict_expectations()` (pour TS des tirages frais), un seul `partial_fit` par tour, aucun réchauffement personnalisé des nouveaux bras.
- Temps d'exécution : 4 jobs en parallèle sur 4 cœurs.

Constatés par moi (non déclarés par le rapport) :
- **Chauffe VW non uniforme** : dans `run()`, pour les règles `vw_*`, la chauffe utilise `pol.select(E, B)` (la sélection de VW elle-même restreinte aux cellules établies), et non un tirage uniforme comme pour les autres règles ; alors que 03 §2 dit « 200 logged pulls each before round 0 (uniform logging) ». L'historique de VW n'est donc pas comparable à celui des autres règles (et n'est pas exactement 200 tirages par cellule).
- Le rapport parle de « `ref_ducb` γ=0,98 » alors que, selon le code, l'oubli s'exerce aussi pendant les 800 tours de chauffe : voir §3.4 (taille d'échantillon effective de 12,5).

### 6.5 Rejeu de ma part (résumé)

Environnement : numpy 2.4.6, river 0.26.1, mabwiser 2.7.4 (Python 3.11.15). Résultats : hash de séquence, `zero_pull_cells` et `regret_all` **identiques** à ceux des JSON pour 2 graines × 6 règles ; sondes de robustesse identiques ; `persistence_check.py` identique. VW, Optuna, SMPyBandits non réinstallés (?).

---

## 7. Critique indépendante

### 7.1 Ce qui est solide

- Les chiffres du banc sont exacts et **reproductibles à l'identique** (hash de séquences égaux à ceux des JSON, §3.9) ; le code est fourni et court ; le rapport étiquette honnêtement PROVEN/OBSERVED/INFERENCE/UNKNOWN ; les limites majeures (une famille de scénarios, réglages dans l'échantillon, aucun test de signification, VW sous-testé) sont **dites** dans le rapport lui-même.
- Le constat « MABWiser UCB1 classe les nouvelles cellules dernières » est confirmé par une sonde indépendante.

### 7.2 Points faibles et biais

1. **Mesure circulaire de l'obsolescence.** `stale_frac_end` compte les cellules non tirées depuis plus de `STALE_S = 200` tours ; la garde de `ref_ducb_fresh` force la revisite après plus de 200 tours sans tirage, avec la **même constante**. Le résultat « stale@end = 0 » de la garde est donc vrai par construction (pas seulement empirique). Le vrai bénéfice observable est la suppression des `zero_pull_cells` (paires : 7,85 → 0 sur 20/20 graines) et non le `stale@end`. Le rapport ne mentionne pas cette circularité.
2. **« Zéro famine » = au moins un tirage.** `zero_pull_cells = 0` et `cov≥1 = 1` sont des critères très faibles. `ref_ducb_fresh@0,998` a `cov≥10 = 0,87` : environ 13 % des cellules (≈ 21 sur 160) ont **moins de 10 tirages** sur 1 200 tours. Sur le plan de « l'évidence suffisante », ce n'est pas de la couverture.
3. **Réglages dans l'échantillon, aucun held-out.** γ = 0,998 et STALE_S = 200 choisis après lecture des résultats sur les mêmes 20 graines et le même scénario. Le rapport le dit (P1) mais le titre de sa constatation n°4 en fait « un résultat » : le signe d'une direction, pas d'un effet.
4. **Une seule famille de scénarios, très structurée** : récompenses de Bernoulli à bruit stationnaire, un seul point de changement (tour 600), un seul trou de 100 tours sur 20 cellules, cellules « améliorées » choisies parmi les moins prometteuses (p bas de la loi Beta) et propulsées à 0,85 (au-dessus des pépites à 0,7-0,8), cellules « dégradées » = les 10 meilleures établies. C'est un scénario de démonstration qui met en évidence exactement les défauts recherchés (famine, oubli, trous), pas un échantillon représentatif.
5. **Nombre de graines et sensibilité.** Balayages externes à 5 graines : suffisant pour un ordre de grandeur (ex. `river_ucbew` toujours à 4,25-4,79) mais pas pour classer des règles proches. Aucune comparaison appariée n'est publiée dans la lane.
6. **Règle de référence écrite par le rapporteur.** `ref_ducb` (`~25 lignes`) est la seule à obtenir un bon compromis, et c'est un code que l'auteur a écrit et réglé. Les règles externes n'ont pas eu le même degré d'effort de réglage (VW : 5 réglages, River : 9 réglages seulement sur la variante EWMean, MABWiser : alpha). Un avantage de réglage n'est pas exclu (INFERENCE [moi]).
7. **Comparaison inégale à l'entrée** : les cellules établies partent de ≈ 200 tirages cumulés pour les règles cumulatives mais de ≈ 12,5 (γ=0,98) ou ≈ 100 (γ=0,998) tirages effectifs pour D-UCB à cause de l'oubli pendant la chauffe (§3.4). VW a en plus une chauffe non uniforme (§6.4).
8. **Métrique de regret.** Le regret compare à un oracle qui connaît p ; par construction il **récompense la concentration** (le rapport le dit). Le rapport ne construit pas de métrique unique combinant regret, famine et adaptation ; la lecture des compromis est laissée au lecteur.
9. **Nouvelles cellules jamais « vraiment » nouvelles pour VW/MABWiser** : le harnais MABWiser n'a pas de réchauffement des nouveaux bras (« uses the library as shipped »), ce qui est justement la cause du défaut de démarrage à froid décrit comme « par construction » — c'est vrai pour l'API telle que livrée, pas nécessairement pour un usage expert de `warm_start`.
10. **Cellules muettes et garde** : le risque P4 (revisite forcée toutes les 200 tours d'une cellule qui ne renvoie **jamais** rien) n'est pas testé. Or la fenêtre du trou ne dure que 100 tours, plus courts que le seuil de 200 : le scénario ne peut donc pas exposer cette boucle. C'est une limite structurelle du banc, pas seulement une inconnue.
11. **Aucun coût de collecte.** Un tirage coûte 1 unité partout ; en pratique, regarder une cellule a un coût variable (calcul, données, temps). Non modélisé.
12. **Échelle** : 160 cellules seulement ; le coût O(nb de bras) par sélection n'est pas testé au-delà.

### 7.3 Choix en bord de grille

- Grille de γ : {0,98 ; 0,99 ; 0,995 ; 0,998 ; 0,9995}. Le point retenu (0,998) est **intérieur**, mais la grille a un trou entre 0,998 et 0,9995 et rien entre 0,995 et 0,998 : le « coude » est estimé sur 5 points. Avec un horizon de 1 200 tours, 0,9995 (horizon ≈ 2 000 tours) est déjà dans le régime « presque cumulatif » (§3.4).
- Grille de fading River : {0,9 ; 0,97 ; 0,99} × delta {0,1 ; 0,5 ; 1,0} : les meilleurs regrets (4,25) sont au bord (fading 0,9, delta 0,1 : plus petits paramètres). On n'a pas essayé un fading plus faible ou un delta plus faible ; mais l'auteur fonde son argument sur la structure de la formule (compteurs cumulés), pas sur ce bord.
- `alpha` de MABWiser : {0,5 ; 2 ; 5} ; la tendance à la baisse de `zero` (139 → 122 → 120) plafonne : consistant avec la thèse « défaut structurel ».
- VW `squarecb` lr {0,005 ; 0,05 ; 0,5} : la monotonie est nette (Gini 0,33 → 0,56 → 0,71) ; le meilleur regret est au bord haut (0,5, regret 3,35).

### 7.4 Ce que les chiffres ne prouvent PAS

- Que D-UCB + garde soit meilleur **sur des données réelles**, ni même sur un autre scénario synthétique.
- Que VW est mauvais : son avantage principal (variables partagées) n'est pas testé.
- Que Optuna est inadapté : jamais benchmarké pour l'allocation (NOT_RUN) ; l'affirmation repose sur la lecture du code.
- Que les détecteurs de dérive de River aident ou non.
- Que le classement des règles tient pour d'autres tailles de lot (B=10 fixé), d'autres délais de retour, d'autres bruits, des récompenses à queue lourde, des cellules corrélées.
- Que 1 000 000 de cellules soient gérables.
- Que les chiffres de maintenance (commits, auteurs, issues) soient exacts (sources web/PyPI/clone non rejouables ici ; issues via un résumeur).
- Aucune compatibilité avec AurumShift : le rapport lui-même n'en affirme aucune.

### 7.5 Écarts entre rapports et résultats bruts (bilan)

Pas d'écart de fond. Écarts mineurs relevés :
- **[a]** 02 §3 écrit « 138/160 » cellules jamais tirées pour MABWiser UCB1, 03 écrit 139 ; les JSON donnent 138,75 en moyenne.
- **[b]** 04 V3 : « 45×-slower Python loop than River/MABWiser » ; 02/03 écrivent « ≈5-47× » ; contre MABWiser (0,8 s) le rapport est ≈ 16×.
- **[c]** 03 §3.5 : « 8-17 % pour les règles cumulatives » exclut `mabwiser_ucb1` (0,267 ; et 0,484 / 0,542 pour alpha 2 et 5).
- **[d]** 03 §2 : chauffe « uniform logging » pour toutes les règles ; faux pour VW (code).
- **[e]** 02 : « both history warm-start and batched/delayed feedback raised KeyError » : le fichier JSON de résultats ne montre que la chauffe ; le cas du lot est vrai (confirmé par ma sonde) mais non démontré par le JSON.
- **[f]** 03 §3 : intitulé « Top 3 by Phase-2 order that could be executed: River, VW, MABWiser » alors que 01 §3 liste River, VW, MABWiser, Optuna, SMPyBandits : cohérent (Optuna/SMPyBandits NOT_RUN).
- **[g]** 03 §4 : le rapport parle de 9 réglages pour `river_ucbew` et le tableau de sweep en contient 9 : ✔.

### 7.6 Contradictions internes

- 07 constat n°4 et §4 : la direction « garde + D-UCB » est présentée avec une confiance « Med » dans 07 §3.1 (classification ADAPT « Med ») mais « Med-Low » dans 07 §4. Deux niveaux pour le même objet ; la seconde est plus cohérente avec le caractère « dans l'échantillon ».
- 03 §5 : « Determinism is not a differentiator » (07) mais le seul candidat qui a échoué sur robustesse d'état (NaN) est River ; l'argument principal de choix de 07 est l'inspectabilité (dans l'INFERENCE).
- 07 §2 classe River au rang 1 alors que ses politiques livrées sont REJECT « tel quel » : le rang 1 porte sur les primitives et la forme d'API (le tableau précise « role »), pas sur les politiques.

---

## 8. Comparaison entre plusieurs runs/branches

Il n'y a **qu'un seul run** pour la lane 001 : `origin/main` et `origin/claude/kind-bohr-n5e2gl` sont identiques sur le dossier (`git diff --stat` vide). Il n'existe pas de branche « -b ». Rien à comparer point par point.

Comparaisons partielles qui ont un sens :
- Le banc **principal** (20 graines) et le **balayage** (5 graines pour les règles externes) portent sur la même règle dans certains cas : `mabwiser_ucb1` alpha 0,5 (principal : zero 138,75 ; regret 3,10) et alpha 2/5 (122,4 ; 3,20 / 120 ; 3,72) — cohérents entre eux. `vw_squarecb_constlr` (lr 0,05) figure au principal (20 graines : Gini 0,562, regret 3,947) et est repris dans les lectures du balayage (lr 0,005 et 0,5 sur 5 graines) : l'échantillon diffère (20 contre 5) pour le point central.
- Le rejeu par mes soins (2 graines × 6 règles) est identique aux JSON du dépôt, donc les deux « runs » (le leur et le mien) s'accordent exhaustivement.

---

## 9. Reproductibilité

### 9.1 Commandes (03 §8)

```bash
python3 -m venv v && . v/bin/activate && pip install river==0.26.1 vowpalwabbit==9.11.9 mabwiser==2.7.4 optuna==5.0.0
cd reports/001_adaptive_strategy_fleet/bench          # depuis un dossier SANS sous-dossier ./river ou ./mabwiser
python bench.py river_ucb_mean 20 out.json            # noms de règle : make_policy(), ex. ref_ducb@0.998, ref_ducbfresh@0.998, vw_squarecb@0.5
python analyze.py <dossier-de-json>                   # tableaux markdown
python persistence_check.py ; python failsoft_check.py
```

### 9.2 Ce que j'ai fait moi

`pip install numpy river==0.26.1` puis `mabwiser==2.7.4`, copie de `bench/*.py` hors du dépôt, `python bench.py <règle> 2 out.json`, comparaison des `seqhash`/`zero_pull_cells`/`regret_all` avec les JSON : identiques. Durée : moins de 10 s par règle et 2 graines pour ref/River (`river_ts_beta` ≈ 7 s), soit ≈ 20 graines en quelques minutes ; VW ≈ 13 s par graine (rapport : 314 s pour 20 graines, en parallèle).

### 9.3 Dépendances et durées

- `requirements-observed.txt` : mabwiser 2.7.4, numpy 2.4.6, optuna 5.0.0, pandas 3.0.6, river 0.26.1, scikit-learn 1.9.1, scipy 1.17.1, SMPyBandits 0.9.7, vowpalwabbit 9.11.9, Python 3.11.15. (Il ne s'agit pas d'un `pip freeze` complet : les dépendances transitives ne sont pas toutes figées.)
- Durées du rapport (`wall_seconds`) : ref 2-8 s, River 9-57 s, MABWiser 23-35 s, VW ≈ 314-317 s par règle pour 20 graines.

### 9.4 Fournis / manquants

- Fournis : code du banc, résultats bruts par graine (20 graines), tables, sondes de robustesse et de persistance, versions.
- Manquants : (i) scripts qui ont produit les mesures de maintenance (`git log`, PyPI) ; (ii) sorties de tests (Optuna 125, MABWiser 533/1, River 3+22 skip) ; (iii) script de l'expérience Optuna de déterminisme (60 essais, 54/6) ; (iv) sortie de l'import SMPyBandits ; (v) commande exacte de lancement des balayages (noms de règles présents, mais pas le script maître) ; (vi) `pip freeze` complet ; (vii) la sonde VW « 0,93 / 0,03 / 0,03 » et celle de `epsilon_decay` (50 mises à jour) ne sont pas dans `bench/` ; (viii) le « debug run » de la graine 0 (que j'ai reproduit).
- Attention : `failsoft_check.py` importe MABWiser et River ; il faut les deux installés.

---

## 10. Implications pratiques pour AurumShift (pistes « à adjuger plus tard »)

Rappel de `claude.md` : **rien ci-dessous n'affirme une compatibilité** avec AurumShift, dont le code privé n'est pas connu ici. Ce sont des pistes à juger plus tard contre le vrai dépôt.

1. **À adjuger** : un ordonnanceur d'attention pourrait devoir traiter séparément trois issues de tentative (preuve / tentative sans preuve / non tentée). La lane montre, sur un scénario synthétique, ce qui se passe sans ce canal (détournement de 72-89 % de l'attention pour certaines règles). Question pour plus tard : le système actuel possède-t-il déjà ce canal ?
2. **À adjuger** : suivre séparément « temps depuis la dernière preuve » et « temps depuis la dernière tentative ».
3. **À adjuger** : si un oubli est utilisé, il doit actualiser à la fois valeur et compte (le cas `river_ucb_ew` montre l'échec inverse).
4. **À adjuger** : état par cellule lisible en SQL + journal de décision en ajout seul + graine/position RNG persistées (exigences de 06). La lane montre que `pickle` (River) est exact mais opaque, donc utilisable comme cache, pas comme registre (le rapport le suggère aussi).
5. **À adjuger** : si le vrai système a des cellules qui partagent des attributs (stratégie, instrument, horizon), VW pourrait servir de généraliseur contextuel ; non testé ici.
6. **À adjuger** : Optuna comme moteur d'ordonnancement est rejeté par la lane ; d'autres usages (recherche d'hyper-paramètres dans une cellule, idée de heartbeat) restent possibles.
7. **À adjuger** : contraintes techniques à contrôler dans le vrai dépôt : version de Python (River ≥ 3.11 et NumPy ≥ 2.2.5), roues natives pour VW, licences (irace GPL, GrowthBook mixte, tqdm MPL-2.0).
8. **À adjuger** : garder un plafond dur de part d'attention par cellule/groupe et surveiller Gini / part du top 10 % (06 §3).
9. **À ne pas conclure** : que `ref_ducb_fresh γ=0,998` serait un bon réglage pour AurumShift ; la lane ne le permet pas.

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **Scénario v2 avec protocole gelé** (valeur la plus haute) : plusieurs familles de scénarios (récompenses à queue lourde, cellules corrélées, trous de longueurs variées **dont un silence permanent**, retours retardés), avec réglage sur un jeu et rapport sur un autre, résultats **appariés par graine** avec intervalles de confiance. Le rapport le recommande (07 §3.2).
2. **Concevoir et tester le backoff du canal `ATTEMPTED_NO_EVIDENCE`** (P4) avant toute autre chose : c'est le principal risque non testé de la piste retenue.
3. **Corriger la circularité de la métrique d'obsolescence** : évaluer `stale` avec un seuil différent de celui de la garde (ex. 100 et 300), ainsi que `cov≥10`/`cov≥30`.
4. **Comparaison équitable du démarrage** : chauffe identique pour toutes les règles (y compris VW), taille d'échantillon effective égalisée, ou retrait de l'oubli pendant la chauffe.
5. **VW avec variables partagées + `epsilon_decay` champion-challenger** : c'est l'avantage non testé qui justifierait VW.
6. **Détecteurs de dérive de River (ADWIN, Page-Hinkley, KSWIN) comme déclencheurs de redémarrage** vs D-UCB.
7. **Niveaux de course non terminaux (style SHA/ASHA)** comme couche de priorité.
8. **Scalabilité** : 10^3 à 10^6 cellules (sélection O(nombre de bras)).
9. **Vérifier hors ligne les chiffres de maintenance/licence** (clones, PyPI) ; refaire les comptes d'issues avec un accès direct plutôt qu'un résumeur.
10. **Portabilité du déterminisme** : autre machine/BLAS/version de NumPy/Python.
11. **Lire vraiment les 5 articles 2025-2026** listés au niveau extrait de recherche.

---

## 12. Index des fichiers lus

Tous lus intégralement sur `origin/main` (extraits avec `git archive` dans le répertoire de travail temporaire) sauf mention.

| Chemin | Contenu en une ligne |
|---|---|
| `reports/001_adaptive_strategy_fleet/00_RESEARCH_SCOPE.md` (68 l.) | Mission, problème abstrait, règles d'honnêteté, méthode par phases, environnement, contraintes de `claude.md` |
| `.../01_LANDSCAPE.md` (74 l.) | Familles d'approches, tableau de 23 candidats, sélection du top 5 |
| `.../02_TOP5_DEEP_DIVE.md` (115 l.) | Revue de River, VW, MABWiser, Optuna, SMPyBandits + Ax/contextualbandits/Vizier |
| `.../03_REPRODUCTION_AND_BENCHMARK.md` (128 l.) | Scénario, résultats principaux, balayages, déterminisme, coût, limites, reproduction |
| `.../04_ADVERSARIAL_REVIEW.md` (93 l.) | Attaques par candidat (R, V, M, O, S, P), conclusions transversales |
| `.../05_LICENSE_AND_MAINTENANCE.md` (66 l.) | Maintenance, licences, poids des dépendances, reproductibilité de l'étude |
| `.../06_INTEGRATION_SURFACE.md` (51 l.) | Contrat minimal d'allocateur, exigences d'état PostgreSQL, frontière anti-capital, surface par candidat |
| `.../07_FINAL_ADJUDICATION.md` (88 l.) | Constats, classement, classification ADOPT/ADAPT/PARK/REJECT, robustesse, inconnues |
| `.../bench/bench.py` (290 l.) | Simulateur, adaptateurs River/MABWiser/VW, règles de référence, métriques ; exécuté (rejeu partiel) |
| `.../bench/analyze.py` (32 l.) | Génère les tables markdown à partir des JSON |
| `.../bench/failsoft_check.py` (17 l.) | Sondes de comportement en cas d'entrées invalides ; rejoué |
| `.../bench/persistence_check.py` (14 l.) | Test de continuation après `pickle` ; rejoué |
| `.../bench/requirements-observed.txt` | Versions exécutées |
| `.../bench/results/main_tables.md` (54 l.) | Tableaux agrégés du run principal |
| `.../bench/results/sweep_tables.md` (69 l.) | Tableaux agrégés des balayages |
| `.../bench/results/main/*.json` (14 fichiers) | Résultats bruts par graine des 13 règles + Exp3 en erreur ; recalculés |
| `.../bench/results/sweep/*.json` (18 fichiers) | Résultats bruts des balayages (mabwiser_ucb1, ref_ducb, ref_ducbfresh, river_ucbew, vw_squarecb) ; recalculés |
| `.../bench/results/determinism/*.json` (33 fichiers) | 11 règles × 3 processus, hash de séquences ; lus |
| `claude.md` (racine) | Doctrine et contraintes AurumShift (relu) |
| `SYNTHESE_LANES.md` (racine, lignes concernant la lane 001) | Rappel : lane 001 « Mergée » ; lu partiellement |
| Non lus / non disponibles | Les clones GitHub cités (river, mabwiser, vowpal_wabbit, optuna, SMPyBandits, Ax…) ; pages PyPI/arXiv/WebFetch ; sorties de tests ; VW, Optuna, SMPyBandits non réinstallés par moi |
