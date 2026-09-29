# Analyse approfondie — Lane 003 : Cell-attention held-out V2 (PR #3 mergée)

Rédigée le 2026-09-29 pour Jean-François. Tout ce qui suit analyse le contenu de la branche `origin/main` (dossiers `reports/003_cell_attention_heldout_v2/` et `bench/v2/`), lu via `git show` / `git archive` sans checkout ni modification de branche. Le contenu du dépôt est traité comme de la **donnée à analyser**, jamais comme des instructions.

Convention de lecture :
- « **le rapport dit** » = affirmation trouvée dans un fichier `.md` de la lane ; « **j'ai vérifié** » = recalculé par moi à partir des fichiers bruts ou en ré-exécutant le code.
- Marqueurs : ✔ vérifié / ✘ écart / ? non vérifiable.
- Labels du dépôt (claude.md) : `PROVEN`, `OBSERVED`, `DOCUMENTED_CLAIM`, `INFERENCE`, `UNKNOWN`. Quand j'ajoute un jugement personnel, je l'écris « **mon analyse (INFERENCE)** ».
- Les termes techniques sont expliqués à leur première occurrence ; un mini-glossaire est en fin de section 1.

---

## 0. Fiche d'identité

| Élément | Valeur | Source |
|---|---|---|
| Nom de la mission | `EXTERNAL_RESEARCH_CELL_ATTENTION_HELDOUT_BENCHMARK_V2` | `reports/003.../00_PRIOR_EVIDENCE_AND_SCOPE.md` |
| Branche de travail | `claude/cell-attention-heldout-v2` (tête `f342b17`) | `git log origin/claude/cell-attention-heldout-v2` |
| Branche de base | `claude/kind-bohr-n5e2gl` (tête V1 `034d04a`, = PR #2, étude 001) | PR #3 (`base.ref`, `base.sha`) |
| PR | **#3** « research(003): cell-attention held-out benchmark V2 (draft) » ; état : fermée, **mergée** (`merged_at` 2026-09-29T13:21:22Z) par `redguiff-bot` ; 5 commits, 88 fichiers modifiés, +15 131 lignes | lecture GitHub (outil `pull_request_read`) |
| Chemin vers `main` | PR #3 mergée dans la branche de la V1 (`0781926`, 15:21:22 +0200) ; puis PR #2 (V1 + V2) mergée dans `main` (`a04c156`, 15:21:37 +0200) | `git log --merges origin/main` |
| Commits de la lane (UTC) | `817990f` 07:52:22 (gel des générateurs, protocole, code des politiques) · `3e7958d` 07:52:31 (correction de la déclaration de gel) · `3328e4d` 08:05:08 (résultats de réglage + paramètres gelés + Phase A) · `d98ef1a` 08:08:47 (résultats bruts held-out) · `f342b17` 08:30:22 (analyses, sensibilité, adversarial, rapports 00-11) | `git log` |
| Durée totale de l'étude (vue par les commits) | ≈ 38 minutes (07:52 → 08:30) après la fin de la V1 (07:13) | déduit (INFERENCE simple) |
| Fichiers | 12 rapports `.md` (147 759 octets ≈ 144 Kio) + 75 fichiers dans `bench/v2/` (9 868 992 octets ≈ 9,4 Mio, dont l'essentiel en JSON de résultats bruts) | `git ls-tree -r -l` |
| Volume expérimental | **1 200 runs held-out** (10 scénarios × 20 graines × 6 politiques), 0 erreur, 208 s de calcul | `results/heldout/run_summary.json` ✔ |
| Verdict final | `FINAL_VERDICT=ADAPTIVE_POLICY_SUPPORTED_FOR_LOCAL_EVALUATION` | `11_FINAL_ADJUDICATION.md` §1 |
| Force du verdict | **MODERATE** (modèle synthétique ; 20 graines × 10 scénarios fixes ; classifieur de A défini par V2 ; B sélectionnée en bord de grille) | `11` §1 |
| Autres drapeaux | `HELDOUT_ISOLATION=PASS` ; `ANY_POLICY_DOMINATES_ACROSS_HELDOUT=NO` ; `ANY_SCIENTIFIC_INVALIDATION=NO` ; `BEST_EXTERNAL_REFERENCE=B` ; `BEST_ADAPTIVE_CANDIDATE=C2` | `11` §1 |
| Ma vérification indépendante | Ré-exécution locale (Python 3.11.15, numpy 2.4.6, river 0.26.1, vowpalwabbit 9.11.9 : mêmes versions que l'étude) : 18 tests sur 18 passent ; les 6 politiques sur `S1`, graine 3000, redonnent **exactement** les empreintes (hash) de la séquence de choix stockées dans `determinism.json` | section 6 |

### Traduction en langage simple du verdict

Le verdict signifie : « les preuves justifient d'évaluer *localement* (plus tard, contre le vrai code AurumShift) une politique d'allocation d'attention *adaptative* ». Il ne dit **pas** qu'une politique est bonne pour AurumShift, ni qu'elle « généralise » : c'est un banc d'essai **synthétique** (données simulées par l'auteur).

---

## 1. Mission et question posée

### 1.1 Reformulation simple

Imagine un système de recherche qui surveille beaucoup de « cellules » (une cellule = une petite unité de recherche qui peut produire de l'information : un signal, une source de données, une hypothèse). À chaque « cycle » (un tour de décision), le système n'a la capacité d'examiner que **10 cellules** (`K = 10`). **Comment choisir lesquelles ?** C'est un problème d'*allocation d'attention*.

La V1 (étude 001, lue seulement en contexte) avait trouvé, sur ses propres scénarios, que :
- les algorithmes « qui suivent la récompense » (bandits, voir glossaire) **affament** certaines cellules (elles ne sont plus jamais regardées) ;
- les cellules **muettes** (qui ne répondent plus) peuvent **capturer** l'attention quand on oublie les anciennes valeurs ;
- une idée prometteuse (D-UCB + « garde-fou de fraîcheur ») n'avait été testée que sur les données qui ont servi à la régler (« in-sample »).

La V2 pose donc la question : **ces conclusions tiennent-elles sur des scénarios jamais utilisés pour régler les politiques (« held-out »), avec des règles de test fixées à l'avance ?** Elle compare 4 politiques « candidates » (A, B, C, D), une variante diagnostique (C2) et un repère (R, tourniquet).

### 1.2 Les politiques (résumé ; détails section 4)

| Code | Nom | En une phrase |
|---|---|---|
| **A** | `AURUMSHIFT_LIFECYCLE_WEIGHTED_REFERENCE` | Contrat fourni par l'opérateur : chaque cellule a un état de cycle de vie (EXPLORATION / PROMISING / PROVEN / DEGRADING / RETIRED) avec un poids fixe (1,50 / 1,00 / 0,75 / 0,50 / 0,00) et un plancher d'exploration de 5 %. **Jamais réglée.** |
| **B** | D-UCB + garde de fraîcheur + « backoff » | Bandit à oubli progressif (voir glossaire) écrit sur mesure, plus une règle qui force à revisiter les cellules trop anciennes, plus un délai croissant pour les cellules qui ne répondent pas. |
| **C** | River « tel que livré » | Bandit ε-glouton de la bibliothèque open source River, avec un petit emballage d'hygiène. |
| **C2** | River + garde | C + exactement la même garde que B. Diagnostic (« est-ce River ou la garde qui compte ? »), pas un cinquième candidat. |
| **D** | Vowpal Wabbit (VW) | Bandit contextuel de la bibliothèque VW ; les cellules sont décrites par des caractéristiques observables partagées (pas d'identifiant). |
| **R** | Tourniquet (round-robin) | On regarde la cellule vue le moins récemment. Repère uniforme, pas un concurrent. |

### 1.3 Contraintes du dépôt (`claude.md`, lu intégralement)

- Doctrine : **REUSE → ADAPT → WRAP → COMPOSE → CUSTOM en dernier**. Ici la logique est cohérente : B est un code sur mesure (CUSTOM) justifié par la V1 (« aucune option de réutilisation n'existe » pour la garde et le canal « tenté, sans preuve »).
- Étiquettes de preuve : `PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN` — la V2 précise que tout résultat synthétique est « OBSERVED dans ce modèle », jamais un PROVEN général.
- Contraintes AurumShift pertinentes : recherche seulement / papier (pas de capital réel) ; PIT (« point-in-time » : n'utiliser que ce qui était connu à la date) / provenance / pas de regard vers le futur ; « **l'absence de preuve n'est pas une preuve négative** » (« missing evidence is not negative evidence ») ; reproductibilité scientifique ; complexité d'infrastructure à justifier.
- Frontière : aucune affirmation de compatibilité avec le code privé AurumShift. Le rapport le répète (`00` §3, `11` en-tête).

### 1.4 Mini-glossaire (termes utilisés dans toute l'analyse)

- **Cellule / cycle / tentative** : une cellule est une unité examinable ; un cycle est un tour de décision ; une tentative = examiner une cellule une fois. Une tentative renvoie soit `EVIDENCE(valeur)` (une preuve arrive, valeur entre 0 et 1 ; **0,0 signifie « une preuve est arrivée, mais elle n'apprend rien »**), soit `ATTEMPTED_NO_EVIDENCE` (« on a essayé, rien n'est venu »). Une cellule non examinée ne produit rien (`NOT_ATTEMPTED`).
- **Bandit (à plusieurs bras)** : famille d'algorithmes qui choisissent, tour après tour, parmi des options (« bras » = ici les cellules) en équilibrant *exploiter* (retourner vers ce qui a bien rapporté) et *explorer* (essayer ce qu'on connaît mal).
- **UCB** (Upper Confidence Bound) : règle de bandit qui ajoute un « bonus d'incertitude » à la valeur moyenne estimée ; les options peu essayées ont un gros bonus (une option jamais essayée a un bonus infini). **D-UCB** (UCB « discounted ») : multiplie les anciennes observations par un facteur γ<1 à chaque cycle pour « oublier » progressivement (utile si le monde change). γ proche de 1 = oubli lent.
- **ε-glouton** (epsilon-greedy) : avec probabilité ε on choisit au hasard, sinon on prend la meilleure option connue.
- **Held-out** (« mis de côté ») : scénarios de test jamais utilisés pour choisir les paramètres. **TRAIN** = jeu de réglage ; **VALIDATION** = jeu pour départager les meilleurs réglages.
- **Pré-enregistrement / gel** : écrire les règles du test (et « geler » le code par une empreinte SHA-256, un résumé cryptographique du fichier) **avant** de voir les résultats, pour empêcher de tricher en ajustant après coup.
- **Graine** (seed) : nombre qui fixe le hasard d'une simulation ; deux exécutions avec la même graine donnent le même résultat. **Nombres aléatoires communs (CRN)** : toutes les politiques affrontent exactement le même « hasard » pour une graine donnée → comparaison **appariée** (plus fine).
- **Oracle** : politique idéale, qui connaît la vérité cachée (probabilités réelles) et choisit à chaque cycle les 10 meilleures cellules. Sert de dénominateur : `info_ratio = information obtenue / information de l'oracle`.
- **Écart-type (sd), IC 95 %** : sd mesure la dispersion entre graines ; l'IC 95 % (intervalle de confiance) est la fourchette où la vraie moyenne se trouve « avec 95 % de confiance ».
- **Bootstrap hiérarchique** : on rééchantillonne au hasard les graines (10 000 fois) pour estimer l'IC. **d_z** = différence moyenne appariée / son écart-type (taille d'effet). **Delta de Cliff** : probabilité que X > Y moins probabilité que X < Y (de −1 à +1).
- **Gini** : mesure d'inégalité (0 = attention parfaitement répartie, 1 = tout sur une seule cellule).
- **Censure** : si un événement (ex. « la politique s'est adaptée ») n'arrive jamais avant la fin du test, on note la durée maximale et on marque « censuré ».
- **IPS** : estimation « à propension inversée » utilisée par VW pour apprendre à partir de choix journalisés.

---

## 2. Méthode

### 2.1 Modèle de problème (rapport `01` §1 ; constantes dans `scenario_core.py` et `protocol.json`)

| Paramètre | Valeur | Sens |
|---|---|---|
| `K` | 10 | tentatives par cycle, sur 10 cellules **distinctes** (donc une cellule reçoit au plus 10 % du budget) |
| `R` | 400 | nombre de cycles |
| `T0` (burn-in) | 80 | cycles 0-79 : **politique de journalisation uniforme commune** (identique pour toutes les politiques, indépendante d'elles) ; les métriques ne portent que sur les cycles 80-399 (320 cycles) |
| `FRESH` | 60 | une preuve de plus de 60 cycles est « périmée » (stale) |
| `H_STARVE` | 80 | horizon de la « famine » : cellule éligible sur les 80 derniers cycles sans aucune tentative |
| `W_COV` | 40 | fenêtre de la métrique de couverture |
| `GROUPS` | 10 | descripteur statique « groupe » (visible dès la naissance) |
| `MAG` / `MAG_RARE` | 0,5 / 1,0 | valeur d'une preuve informative (ordinaire / rare-haute) |
| `LOW_INFO_EV` | 0,05 | une cellule est « vraiment peu informative » si son information espérée < 0,05 |
| `PIT_FRACTION` | 0,10 | 10 % des cellules naissent « pit_unverified » (non vérifiées point-in-time), levé après 3 preuves |

- **Retour par lots** : les 10 choix sont faits avant de voir un seul résultat.
- **Valeur d'information** : une tentative sur une cellule non muette est informative avec probabilité `P[t,c]`, et vaut alors `mag`. Information espérée d'une tentative = `P × mag`. Cette métrique est **définie par le scénario** et indépendante de tout PnL (pas de finance ici).
- **Ce que la politique voit** : uniquement un « registre » (`Ledger`) : nombre de tentatives, nombre de preuves, date de dernière tentative et de dernière preuve (suivies **séparément**), nombre de non-réponses consécutives, deux moyennes mobiles des valeurs observées (lente et rapide), drapeau `pit_unverified`, groupe, et l'ensemble éligible annoncé. Jamais `P`, ni les drapeaux de silence, ni les dates de changement (`ledger.py` lu ✔ : aucun accès aux champs cachés).
- **Distinctions sémantiques imposées** (testées) : `NO_OBSERVATION ≠ NEGATIVE_OBSERVATION` ; `DATA_GAP ≠ LOW_INFORMATION` ; `STALE ≠ DEGRADING` ; `NOT_YET_TRIED ≠ TRIED_AND_UNINFORMATIVE`.

### 2.2 Découpage des données (`01` §2 ; `protocol.json`)

| Jeu | Scénarios | Graines | Usage |
|---|---|---|---|
| TRAIN | `T1_mixed_abrupt`, `T2_mixed_drift_gap`, `T3_churn_lowinfo`, `T4_dormancy_rare` | 1000-1004 | régler B, C, C2, D |
| VALIDATION | `V1_coldstart_outage`, `V2_abrupt_then_drift`, `V3_silence_rare_lowinfo` | 2000-2004 | départager les 3 meilleurs réglages de chaque politique |
| **HELD-OUT** | `S1` à `S10` | **3000-3019 (20 graines)** | toutes les comparaisons |
| PILOTE (Phase A) | générateurs held-out | 9000-9002 | validation du banc (invariants seulement) |
| ADVERSARIAL (a posteriori) | `X1` à `X5` | 4000-4019 | essais de falsification ; jamais pour sélectionner |

`protocol.json` code les bornes en « [début, fin) » (ex. `heldout: [3000, 3020]`) ✔ cohérent avec 20 graines.

### 2.3 Les 10 scénarios held-out (`02` ; `scenarios_heldout.py` lu ✔)

| # | Nom | Construction | Défaut testé |
|---|---|---|---|
| S1 | MASSIVE_COLD_START | 30 cellules établies ; **90 nouvelles** au début de l'évaluation et **60 de plus** à τ=120 | nouvelles cellules jamais regardées ; explosion du démarrage à froid |
| S2 | ABRUPT_REGIME_CHANGE | 120 établies ; à τ=100 les 2 groupes les plus forts chutent de 0,45, les 2 plus faibles montent à U(0,6-0,8) | verrouillage sur les gagnants passés ; délai d'adaptation |
| S3 | SLOW_DRIFT | 20 cellules montent, 20 descendent linéairement de τ=40 à τ=240 (choisies individuellement, pas par groupe) | dérive lente |
| S4 | TEMPORARY_SILENCE | 36 cellules muettes 40 cycles chacune, départs étalés sur τ∈[30,230] | capture par cellules muettes ; pathologie d'oubli |
| S5 | PROVIDER_DATA_GAP | 3 groupes entiers (un « fournisseur ») muets simultanément sur τ∈[80,220) | panne corrélée ; `DATA_GAP ≠ LOW_INFORMATION` |
| S6 | STALE_BUT_VALID | 120 cellules stationnaires ; toute la preuve du burn-in est **datée de 100 cycles plus tôt** (donc « périmée » alors qu'elle reste valable) | `STALE ≠ DEGRADING` ; agitation inutile |
| S7 | GENUINELY_LOW_INFORMATION | 70 cellules à P∈U(0,01-0,06), 35 moyennes, 15 bonnes U(0,55-0,80) | attention gaspillée sur le peu informatif |
| S8 | RARE_HIGH_INFORMATION | 110 ordinaires + 10 « rares » (P=0,05, valeur 1,0) | découverte d'événements rares |
| S9 | LONG_DORMANCY_RETURN | 25 cellules muettes τ∈[30,230) (200 cycles) puis **retour avec P+0,35** à τ=230 (90 cycles restants) | retour de dormance |
| S10 | DYNAMIC_POPULATION | 60 établies ; toutes les 20 cycles (15 vagues) 12 naissances + 10 retraits explicites | agitation de population |

### 2.4 Générateur de scénarios

`Builder` (`scenario_core.py`) : chaque cellule a `birth`, `death`, `group`, `pit0`, `mag`, `rare`, une probabilité cachée `P[t,c]` et un drapeau caché `silent[t,c]`. Cellules établies : `P0 = clip(moyenne_du_groupe + N(0;0,10), 0,03; 0,85)` ; moyennes de groupe tirées dans U(0,12; 0,60). Nouvelles : `P0 = clip(0,6·moy_groupe + 0,4·Beta(2,6) + N(0;0,05))`, dont 10 % de « pépites » à U(0,6;0,8). Les flux aléatoires sont indépendants pour générateur / résultats / journalisation via `SeedSequence([split, idx_scénario, graine])`. Résultat d'une tentative = fonction fixe de `(scénario, graine, t, c)` → CRN.

### 2.5 Simulateur et protocole d'exécution (`runner.py` lu ✔)

Cycles 0-79 : la cellule choisie est tirée uniformément (journalisation commune, tous les événements sont transmis aux politiques via `observe(..., logged=True)`). Cycles ≥ 80 : la politique choisit ; le runner vérifie (assert) que les 10 choix sont distincts et éligibles. Puis `observe`, puis mise à jour du registre.

### 2.6 Pré-enregistrement et gel

- `protocol.json` (version v2.0.0) : constantes, découpage, graines, espaces de recherche, objectif J, règle de sélection, seuils pratiques, statistiques.
- `freeze_manifest.json` : SHA-256 de `scenario_core.py`, `scenarios_dev.py`, `scenarios_heldout.py`, `tune.py`, `protocol.json`, date de gel 2026-09-29T07:52:22Z. Amendement daté 08:05:08Z : `tune.py` modifié (règle de départage), nouveau SHA `95fe833f…`. J'ai recalculé les SHA-256 : ils correspondent (`tune.py` = `95fe833f…` ✔, `protocol.json` = `123f3e41…` ✔, `scenarios_heldout.py` = `3080f43e…` ✔).
- `params_lock.json` (verrou des paramètres, écrit en création exclusive **avant** le run held-out) : contient les paramètres, les SHA des 4 fichiers `selected_*.json` (recalculés ✔), du manifeste, du protocole et du générateur held-out.
- Les résultats bruts held-out sont écrits avec `open(..., 'x')` (refus d'écraser) ✔ (code lu).
- **Limite** (voir section 7) : ce pré-enregistrement est *auto-déclaré* (même auteur, même dépôt Git) ; il n'y a pas d'horodatage tiers.

### 2.7 Objectif de réglage J et règle de sélection (seuils exacts)

`J = info_ratio − 1,0·starvation_rate − 0,5·stale_rate − 0,5·max(silent_excess, 0) − 0,25·max(lowinfo_excess, 0)`, moyenne sur les scénarios×graines TRAIN. Les 3 meilleurs réglages par J-TRAIN sont recalculés sur VALIDATION ; on garde le meilleur J-VALIDATION ; **égalité si écart < 0,005 → on prend le plus proche du centre de la grille**. J est « un outil de réglage » : les comparaisons held-out rapportent chaque métrique séparément.

Espaces de recherche (`protocol.json`) :
- **B** : γ ∈ {0,98; 0,99; 0,995; 0,998; 0,9995} × S ∈ {25, 50, 100} × M ∈ {1, 4, 16} = 45 configs (S = intervalle de garde en cycles ; M = plafond du multiplicateur de backoff).
- **C** : eps_ew (fading {0,05; 0,1; 0,3} × ε {0,05; 0,1; 0,2}) = 9 ; ucb_ew (fading × delta {0,1; 0,5; 1,0}) = 9 ; ucb_mean (delta) = 3 → 21.
- **C2** : garde (S × M) sur les 3 meilleures configs de C = 27.
- **D** : squarecb (gamma_scale {5,20,100} × lr {0,01; 0,05; 0,2} × groupe {oui, non}) = 18 ; eps (ε {0,05; 0,2} × lr × groupe) = 12 → 30.
- **A** et **R** : non réglés.

### 2.8 Métriques (`01` §4 et `metrics.py` lu ✔)

`coverage_W` (fraction des cellules éligibles toute la fenêtre de 40 cycles qui ont reçu ≥ 1 tentative) · `starvation_rate` (part des cellules éligibles depuis 80 cycles sans aucune tentative) · `max_starvation_duration` · `stale_rate` (cellules non muettes dont la dernière preuve a > 60 cycles) · `silent_excess` (part d'attention sur cellules muettes − part qu'aurait donnée une allocation uniforme) · `lowinfo_excess` (idem pour cellules à information espérée < 0,05) · `rare_discovery_rate` · `adapt_delay` (cycles après le changement pour que les cellules cibles reçoivent ≥ 2× leur part de population sur 10 cycles ; **censuré**) · `gini_attention_rate`, `turnover` (contexte, ni bon ni mauvais) · `info_ratio` · coût en secondes.

### 2.9 Statistiques (pré-enregistrées ; `08` ; `analysis.py` lu ✔)

Différences appariées par graine ; bootstrap hiérarchique 10 000 rééchantillons (graine de l'analyse 20260929) ; tailles d'effet d_z et delta de Cliff ; seuils pratiques (`protocol.json`) :

| Métrique | Seuil pratique |
|---|---|
| info_ratio | 0,03 |
| starvation_rate | 0,02 |
| stale_rate | 0,03 |
| silent_excess | 0,03 |
| coverage_W | 0,03 |
| adapt_delay | 10 cycles |
| gini_attention_rate | 0,05 |
| turnover | 0,05 |
| new_ttfa_median (délai de première tentative) | 2 cycles |
| rare_discovery_rate | 0,05 |
| lowinfo_excess | 0,03 |
| degraded_excess_post | 0,02 |
| max_starvation_duration | 10 cycles |
| longsilent_share | 0,02 |

Catégories (pas de p-valeurs) : `DISTINGUISHABLE+MEANINGFUL` (IC exclut 0 **et** |Δ| ≥ seuil) · `STATISTICALLY_DISTINGUISHABLE` (IC exclut 0 mais Δ sous le seuil) · `PRACTICALLY_MEANINGFUL(CI includes 0)` · `INCONCLUSIVE`. Aucune correction pour comparaisons multiples (150 comparaisons) : le seuil pratique est le critère contraignant.

### 2.10 Phases d'exécution

Phase A (validation du banc, 306 runs, 53,87 s ✔ `phaseA_raw.json`) → réglage (`tune.py`) → gel des paramètres → Phase B (held-out, 1 200 runs, 207,9 s ✔) → tests de pathologies → sensibilité descriptive (5 graines 3000-3004) → statistiques → scénarios adversariaux post hoc.

---

## 3. Résultats détaillés

Étiquette générale (dite par le rapport, et je la confirme) : **OBSERVED dans ce modèle synthétique** ; jamais un PROVEN général.

### 3.1 Réglage TRAIN / VALIDATION (rapport `04` ; `selected_*.json`, `tuning/*_raw.json`)

Tous les chiffres ci-dessous ✔ vérifiés (fichiers `selected_*.json` ; J-TRAIN de B recalculé depuis `B_raw.json` : 0,69151 ✔ ; J-VALIDATION 0,63244 ✔).

| Politique | Configs | Erreurs | Choisie | J-TRAIN | J-VALID | Écart (train−valid) | Configs ≥ tourniquet (J-train 0,527) | J-TRAIN min / médiane / max |
|---|---|---|---|---|---|---|---|---|
| B | 45 | 0 | γ=0,9995 ; S=25 ; M=4 | 0,692 | 0,632 | +0,059 | 35/45 | 0,418 / 0,588 / 0,692 |
| C | 21 | 0 | eps_ew ; fading 0,1 ; ε=0,2 | 0,561 | 0,514 | +0,047 | **3/21** | 0,018 / 0,355 / 0,580 |
| C2 | 27 | 0 | idem C + garde S=50 ; M=4 | 0,742 | 0,750 | −0,008 | 27/27 | 0,583 / 0,711 / 0,742 |
| D | 30 | 0 | eps ; ε=0,2 ; lr=0,05 ; groupe non | 0,645 | 0,573 | +0,072 | 22/30 | 0,330 / 0,557 / 0,645 |

Références sur le même objectif J : **A** : 0,526 (train) / 0,453 (valid) ; **tourniquet** : 0,527 / 0,458 (✔ recalculé depuis `B_raw.json` : 0,5257 et 0,5272). Donc à ce stade A et R sont indiscernables.

Top-3 par J-TRAIN (avec J-VALID) :
- B : `g0.9995|S25|M4` 0,692/0,632 ; `g0.9995|S25|M16` 0,692/0,632 (identique : le plafond M ne joue jamais sur les données de réglage) ; `g0.998|S25|M4` 0,680/0,608.
- C : `f0.3|e0.2` 0,580/0,511 ; `f0.1|e0.2` 0,561/0,514 ; `f0.05|e0.2` 0,530/0,492.
- C2 : `S50|M4` 0,742/0,750 ; `S50|M16` 0,742/0,750 ; `S25|M4` 0,734/0,691.
- D : `eps|e0.2|lr0.05|grp0` 0,645/0,573 ; `…|grp1` 0,636/0,567 ; `eps|e0.2|lr0.2|grp0` 0,632/0,573.

**Lecture simple** : le réglage « préfère » beaucoup d'exploration uniforme, parce que J punit fortement la famine et la péremption ; **tous les réglages choisis sont au bord de la grille** (B : γ maximal, S minimal ; C, C2 et D : ε=0,2 maximal). C'est un caveat central (voir section 7).

**Deux corrections avant le held-out** (rapport `01` §9) : la règle de départage avait été codée « rang train » au lieu de « plus proche du centre » ; corrigée, tout le réglage refait. Effet annoncé : B passe de M16 à M4, C de fading 0,3 à 0,1. Ma vérification : `tune_BCC2.log` (dans le dépôt) affiche encore les anciens choix (B M16, C f0.3) ✘ — le journal est *périmé* par rapport aux `selected_*.json` (voir 7.6). Et pour C, `selected_C.json` montre que `f0.1` (J-VALID 0,5142) est **le leader strict** devant `f0.3` (0,5112) : la règle « égalité → centre » n'était pas nécessaire pour le choisir (le rapport `01` §9 l'explique par une égalité ; petit ✘ de formulation).

### 3.2 Résultats held-out poolés (rapport `05` §1 ; ✔ tous les chiffres poolés recalculés à partir des 1 200 runs)

Moyenne des 10 scénarios (chaque scénario = moyenne de 20 graines), avec IC 95 % bootstrap hiérarchique du rapport.

| Métrique | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| info_ratio (↑) | 0,508 [0,502; 0,514] | 0,649 [0,645; 0,653] | 0,743 [0,738; 0,748] | 0,728 [0,722; 0,734] | **0,757** [0,753; 0,760] | 0,507 [0,500; 0,513] |
| coverage_W (↑) | 1,000 | 0,984 [0,983; 0,984] | 0,598 [0,596; 0,601] | 0,759 [0,751; 0,767] | 0,830 [0,829; 0,831] | 1,000 |
| starvation_rate (↓) | 0,000 | 0,005 [0,005; 0,005] | 0,147 [0,145; 0,149] | 0,073 [0,069; 0,077] | 0,015 | 0,000 |
| max_starvation_duration (↓, cycles) | 49,0 | 48,9 | 288,8 | 229,8 | 79,2 | 26,1 |
| stale_rate (↓) | 0,002 | 0,010 | 0,230 | 0,125 | 0,023 | 0,003 |
| silent_excess (sur les 10 scénarios) | +0,009 | −0,025 | +0,039 | −0,007 | −0,026 | 0,000 |
| lowinfo_excess | −0,012 | −0,055 | −0,085 | −0,080 | −0,072 | 0,000 |
| adapt_delay (3 scén.) | 196,7 | 95,9 | 104,6 | 99,4 | 128,1 | 196,7 |
| new_ttfa_median (2 scén.) | 3,16 | 1,56 | 35,2 | 14,2 | 35,6 | 9,25 |
| rare_discovery_rate (1 scén.) | 0,705 | 0,510 | 0,275 | 0,315 | 0,335 | 0,750 |
| Gini de l'attention | 0,059 | 0,307 | 0,684 | 0,506 | 0,581 | 0,020 |
| turnover | 0,999 | 0,655 | 0,301 | 0,502 | 0,404 | 1,000 |

Traduction en langage simple :
- `info_ratio` 0,5 = « autant d'information que l'uniforme » ; **A ≈ R ≈ 0,51**. B monte à 0,65 ; C, D, C2 à 0,73-0,76.
- Mais les politiques qui gagnent le plus d'information (C, D, C2) sont celles qui **laissent le plus de cellules dans l'ombre** (couverture 0,60 / 0,76 / 0,83 ; famine 0,147 / 0,073 / 0,015 ; péremption 0,23 / 0,125 / 0,023). **Il y a une frontière information ↔ couverture** et personne n'est du bon côté des deux (rapport `05` §3.1, que je confirme).
- B est un compromis : +0,14 d'information vs A pour −0,016 de couverture.
- Attention : les moyennes poolées cachent l'hétérogénéité entre scénarios (S9, S5, S1).
- Note de méthode : `adapt_delay`, `new_ttfa_median`, `rare_discovery_rate` sont poolés sur respectivement 3, 2 et 1 scénarios seulement. Les IC de ces trois métriques sont donc beaucoup plus fragiles (ex. rare : n=1 scénario × 20 graines).

### 3.3 Résultats par scénario (rapport `05` §2 ; ✔ 420 cases moyenne±sd recalculées, 0 écart)

J'ai recalculé les 7 tableaux (info_ratio, starvation, max starvation, stale, coverage, Gini, turnover) × 10 scénarios × 6 politiques = 420 cellules « moyenne ± écart-type » à partir des JSON bruts : **0 écart** (tolérance = arrondi).

**info_ratio (↑) par scénario (moyenne ± sd sur 20 graines)**

| Scénario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S1 MASSIVE_COLD_START | 0,490±0,031 | 0,548±0,027 | 0,769±0,022 | 0,673±0,051 | 0,706±0,021 | 0,491±0,033 |
| S2 ABRUPT_REGIME_CHANGE | 0,546±0,054 | 0,672±0,029 | 0,768±0,027 | 0,720±0,034 | 0,741±0,028 | 0,538±0,054 |
| S3 SLOW_DRIFT | 0,592±0,059 | 0,693±0,035 | 0,753±0,037 | 0,696±0,051 | 0,742±0,037 | 0,586±0,057 |
| S4 TEMPORARY_SILENCE | 0,526±0,057 | 0,679±0,033 | 0,778±0,026 | 0,745±0,030 | 0,790±0,019 | 0,542±0,060 |
| S5 PROVIDER_DATA_GAP | 0,472±0,037 | 0,667±0,029 | 0,635±0,071 | 0,696±0,065 | 0,774±0,034 | 0,483±0,040 |
| S6 STALE_BUT_VALID | 0,575±0,052 | 0,686±0,035 | 0,825±0,021 | 0,768±0,046 | 0,785±0,022 | 0,574±0,054 |
| S7 GENUINELY_LOW_INFO | 0,324±0,017 | 0,599±0,010 | 0,814±0,009 | 0,798±0,023 | 0,744±0,008 | 0,295±0,015 |
| S8 RARE_HIGH_INFO | 0,531±0,038 | 0,662±0,026 | 0,816±0,019 | 0,744±0,039 | 0,777±0,019 | 0,527±0,040 |
| S9 LONG_DORMANCY_RETURN | 0,476±0,043 | 0,665±0,035 | 0,515±0,050 | 0,697±0,048 | 0,739±0,031 | 0,486±0,046 |
| S10 DYNAMIC_POPULATION | 0,546±0,048 | 0,617±0,038 | 0,759±0,036 | 0,740±0,032 | 0,769±0,018 | 0,546±0,049 |

Ce que ça dit : C (River tel que livré) est le meilleur en information dans S1, S2, S3, S6, S7, S8 (le rapport `09` l'annonce), mais s'effondre dans S5 (0,635) et S9 (0,515) où les cellules muettes l'aspirent. C2 est le meilleur dans S4, S5, S9 et S10 ; D n'est le meilleur nulle part. Dans S7 (peu d'information), A ≈ R sont très bas (0,32 / 0,30) : répartir l'attention uniformément est ici mauvais.

**starvation_rate (↓)** : A, R = 0,000 partout ; B = 0,000 sauf S5 (0,021 ± 0,002) et S9 (0,028 ± 0,000) ; C 0,061 (S10) à 0,231 (S1) ; D 0,023 (S10) à 0,149 (S7) ; C2 = 0,000 sauf S4 (0,015), S5 (0,060), S9 (0,075).

**max_starvation_duration (cycles)** : la plus longue période sans attention pour une cellule : R 10-35 ; A 28-53 ; B 26-50 dans la plupart des scénarios mais **104 (S5) et 104 (S9)** ; C2 50-58 mais **100 (S4), 138 (S5), 188 (S9)** ; C 180-316 ; D 148-297.

**coverage_W** : A, R = 1,000 partout ; B ≥ 0,942 sauf S9 (0,907) ; C entre 0,477 (S1) et 0,731 (S10) ; D 0,608-0,896 ; C2 0,752-0,885.

**stale_rate** : A, R ≈ 0-0,017 ; B 0-0,041 (S9) ; C 0,067-0,297 ; D 0,026-0,226 ; C2 0-0,087.

**Adaptation (`adapt_delay`, cycles ; censuré au maximum restant)**

| Scénario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S2 | 220±0 | 54±30 | 89±64 | 82±45 | 95±77 | 220±0 |
| S3 | 280±0 | 174±23 | 215±46 | 183±54 | 199±39 | 280±0 |
| S9 | 90±0 | 60±1 | 9±0 | 32±21 | 90±0 | 90±0 |

Fraction de runs censurés (jamais adapté) : S2 : A 1,00 · B 0,00 · C 0,10 · D 0,00 · C2 0,15 · R 1,00 ; S3 : A 1,00 · D 0,05 · autres 0 sauf R 1,00 ; S9 : A 1,00 · B 0 · C 0 · D 0,05 · **C2 1,00** · R 1,00. Tout ceci ✔ recalculé.

**Note de lecture importante (mon analyse, INFERENCE)** : le critère d'adaptation est « part des cellules cibles ≥ 2× leur part dans la population sur 10 cycles ». Une allocation uniforme (R) ne peut **par construction** jamais l'atteindre ; A, dont le rapport de poids extrême est 3 (1,5 : 0,5), ne le peut presque pas non plus. « A ne s'adapte jamais » est donc en partie une conséquence de la définition du critère, pas seulement un constat empirique surprenant (voir 7.2).

**Attention sur cellules muettes (`silent_excess`, + = plus que l'uniforme)**

| Scénario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| S4 | +0,030 | −0,026 | +0,024 | −0,003 | −0,028 | +0,000 |
| S5 | +0,024 | −0,112 | +0,106 | −0,027 | −0,114 | +0,000 |
| S9 | +0,034 | −0,107 | **+0,264** | −0,040 | −0,115 | −0,000 |

✔ (S9, C : part d'attention sur cellules muettes 0,395 ± 0,058 contre 0,130 de référence uniforme, confirmé).

**Autres cas** : S7 `lowinfo_excess` : A −0,049 ; B −0,315 ; C −0,477 ; D −0,476 ; C2 −0,405 ; R 0,000 (✔ calculé) — A réduit très peu l'attention sur les cellules peu informatives, les bandits la réduisent fortement. S8 `rare_discovery_rate` : A 0,705 ; B 0,510 ; C 0,275 ; D 0,315 ; C2 0,335 ; R 0,750 (✔) : le tourniquet et A trouvent le plus d'événements rares car ils regardent tout le monde ; les bandits, qui se concentrent sur les cellules « bonnes en moyenne », en ratent.

### 3.4 Pathologies P1-P8 (rapport `06`)

Vocabulaire : `NOT_OBSERVED / OBSERVED_MILD / OBSERVED` (au-delà des seuils pratiques). Tableau de synthèse du rapport (je l'ai revérifié sur les chiffres cités ; voir détail plus bas) :

| Pathologie | A | B | C | D | C2 |
|---|---|---|---|---|---|
| P1 famine des nouvelles cellules | non | non | **oui** (4,7 % en S1 / 12,6 % en S10 jamais tentées) | léger (0,7 % / 2,1 %) | léger (0 % / 7,8 %) |
| P2 capture par cellules muettes | non (+2,4 à +3,4 pts) | non (−2,6 à −11,2 pts) | **oui** (+2,4 / +10,6 / +26,4 pts) | non | non |
| P3 verrouillage sur les gagnants | n/a | léger (S3 +0,021) | léger (S3 +0,056) | léger (S3 +0,057) | léger (S3 +0,043) |
| P4 pathologie d'oubli | non | non avec M=4 ; **oui si M=1** | n/a | n/a | non |
| P5 explosion du démarrage à froid | non | non | oui (135 cycles) | léger (48) | oui (56) |
| P6 agitation de population | non | non | léger | léger | léger |
| P7 retour de dormance | non récupéré (100 % censuré) | récupéré (~60 cycles) | récupéré vite (9) | récupéré (32) | **échec** (100 % censuré, part 0,000) |
| P8 absence de preuve ≠ négatif | prouvé par test | idem | idem | idem | idem |

Détails chiffrés vérifiés (✔) :
- **P1** : délai médian avant première tentative (cycles) en S1 : A 4,3 · B 3,1 · C 45,8 · D 22,2 · C2 45,8 · R 11,0 ; en S10 : 2,0 · 0,0 · 24,5 · 6,1 · 25,4 · 7,5. Maximum moyen par run en S1 : A 8 · B 8 · C 306 · D 114 · C2 58 · R 18.
- **P5** : cycles pour attendre 90 % de la première cohorte de 90 cellules : A 8 · B 8 · C 135 · D 48 · C2 56 · R 12. Minimum physique ≈ 8,1 cycles (81 cellules / 10 par cycle). `info_ratio` sur les 40 premiers cycles : A 0,514 · B 0,538 · C 0,679 · D 0,627 · C2 0,679 · R 0,513 — c'est-à-dire que ignorer les nouvelles cellules **augmente** le gain d'information à court terme (arbitrage information/démarrage à froid).
- **P3** : excès d'attention sur les cellules qui ont *perdu* de la valeur (50 à 150 cycles après le changement) : S2 : A −0,029 · B −0,090 · C −0,150 · D −0,118 · C2 −0,128 (tous négatifs = ils quittent les cellules dégradées) ; S3 : A −0,005 · B +0,021 · C +0,056 · D +0,057 · C2 +0,043 (léger verrouillage).
- **P4 (diagnostic post hoc, graines 4000-4019)** — B avec γ=0,9995, S=25 fixes, M variable :

| Scénario | M | info_ratio | part silencieuse | référence uniforme | péremption | famine |
|---|---|---|---|---|---|---|
| X1 silence permanent | 1 (sans backoff) | 0,209 | **0,674** | 0,438 | 0,000 | 0,000 |
| X1 | 4 (gelé) | 0,694 | 0,075 | 0,438 | 0,000 | 0,066 |
| X1 | 16 | 0,710 | 0,056 | 0,438 | 0,000 | 0,096 |
| X5 cellules fiables intermittentes | 1 | 0,505 | 0,280 | 0,125 | 0,000 | 0,000 |
| X5 | 4 | 0,557 | 0,046 | 0,125 | 0,070 | 0,022 |
| X5 | 16 | 0,557 | 0,042 | 0,125 | 0,073 | 0,034 |

  Tous ✔ recalculés depuis `followup_B_backoff.json`. Signification : **sans backoff, B est capturée** (67 % de l'attention sur des cellules définitivement muettes, information pire que le tourniquet 0,336) ; avec le backoff, la boucle disparaît. Le backoff est donc « un composant nécessaire, pas une option ». Son coût : le retour de dormance (P7) et le sous-service des cellules intermittentes de valeur (X5).
- **P7 — le mécanisme (rapport)** : avec la garde gelée de C2 (S=50, M=4) une cellule qui ne renvoie rien est revisitée après 100 cycles puis tous les 200 ; les cellules de S9 deviennent muettes à τ=30, leurs revisites tombent à τ≈130 puis τ≈330, donc le retour à τ=230 n'est vu qu'après la fin du test. Et pendant sa fenêtre de backoff, la cellule est aussi exclue de la liste de candidats de River → River ne peut pas non plus s'en apercevoir. Je confirme par le code (`guard_sets`, `excl`).
- **Sensibilité du retour S9 (5 graines, fichiers `sensitivity/B.json` et `C2.json`, ✔)** : B : S=25 → 59,2 cycles ; S=50 → 90 (censuré, 100 % des runs) ; S=100 → 9,0 ; S=200 → 90 ; S=10 → 21,4 ; M=1 → 9,0 ; **M=16 (S=25) → 90 censuré**. C2 : S100/M4 → 11,4 ; S25/M4 → 72,4 ; S50/M4 → 90 ; S25/M16 → 90 ; M=1 → 9,0. Le rapport parle d'une « loterie de phase » du calendrier de backoff : la latence de retour dépend du moment où tombent les revisites, bornée par S·M. Je confirme les chiffres.
- **P8** : tests unitaires + audit compteurs sur les 1 200 runs : River `_n == nombre d'événements EVIDENCE`, VW `learn_calls == nombre d'événements EVIDENCE` ; 110 739 événements « sans preuve » au total (✔ recalculé exactement 110 739) ; 0 violation sur 600 vérifications. Conservation de A : erreur max 7,1e-15 (✔ 7,105e-15). 0 tentative sur cellule inéligible dans les 1 200 runs (✔ 0). **Limite reconnue par le rapport** : P8 prouve qu'aucune politique ne *note* le silence comme un échec ; ça ne prouve pas qu'elles se comportent bien sous silence (C est capturée, C2 rate les retours).

### 3.5 Sensibilité aux paramètres (rapport `07` ; `sensitivity_summary.json` ✔)

Runs descriptifs et post-sélection sur générateurs held-out, **5 graines (3000-3004)** × 10 scénarios ; nombres de configs : A 7, B 19, C 11, C2 11, D 12 ; 0 erreur (journal `sensitivity.log` : 350, 950, 550, 550, 600 runs ✔). Règle de classification (définie par V2, « convention », non pré-enregistrée dans `protocol.json`) : une alternative est « acceptable » si, vs la config gelée, l'info n'est pas pire de plus de 0,06 (2× seuil), la famine pas plus haute de 0,04, la péremption de 0,06, l'excès muet de 0,06. Fraction acceptable ≥ 0,75 ROBUST ; 0,35-0,75 SENSITIVE ; < 0,35 BRITTLE (fragile).

| Politique | Alternatives | Fraction acceptable | Classe | Plage info_ratio | Plage famine | Plage péremption | Plage excès muet (S4/S5/S9) |
|---|---|---|---|---|---|---|---|
| A | 6 | 0,83 | ROBUST | 0,505-0,521 | 0,000-0,000 | 0,002-0,002 | +0,007 à +0,097 |
| B | 16 | 0,69 | SENSITIVE | 0,578-0,685 | 0,000-0,084 | 0,004-0,090 | −0,088 à +0,194 |
| C | 10 | 0,10 | BRITTLE | 0,591-0,779 | 0,134-0,390 | 0,158-0,462 | +0,066 à +0,328 |
| C2 | 10 | 0,40 | SENSITIVE | 0,672-0,796 | 0,000-0,082 | 0,005-0,157 | −0,089 à +0,100 |
| D | 11 | 0,27 | BRITTLE | 0,694-0,824 | 0,053-0,400 | 0,096-0,473 | −0,090 à +0,023 |

✔ Toutes ces valeurs recalculées depuis `sensitivity_summary.json`.

Lecture simple :
- **A « robuste » mais de façon triviale** : ni le plancher (0/5/10/20 %), ni des poids plats ou raides, ni un classifieur alternatif ne le fait sortir du comportement « quasi tourniquet ». Le seul bouton visible est le plancher : l'excès muet monte de +0,007 (0 %) à +0,097 (20 %).
- **B** : γ échange information contre adaptation (info 0,578 à γ=0,98 → 0,685 à γ=0,9995 ; délai d'adaptation 170-197 → 67-105) ; l'intervalle S échange couverture contre information (S=25 : famine 0,005 ; S=100 : famine 0,028-0,056 ; hors grille S=200 : famine 0,084 ; hors grille S=10 : famine 0,000 mais info 0,617) ; **M=1 est dangereux** (excès muet +0,194).
- **C fragile** : aucune des 11 configurations n'évite la famine (0,134-0,390).
- **D fragile** : le taux d'apprentissage et l'exploration font passer le comportement de « presque uniforme » à « glouton et affamant ».
- Inclure ou non la caractéristique « groupe » dans D change peu (par exemple grp0 vs grp1 : 0,741 vs 0,737 d'info à lr0,05/ε0,2).

### 3.6 Statistiques (rapport `08` ; `analysis.json` ✔)

- 150 comparaisons poolées par paires : **106 DISTINGUISHABLE+MEANINGFUL, 33 STATISTICALLY_DISTINGUISHABLE (réel mais trop petit), 1 PRACTICALLY_MEANINGFUL (IC contient 0), 10 INCONCLUSIVE** ✔ (compté exactement). Les 10 inconclusives ✔ : A-R sur couverture, famine, délai d'adaptation, découverte rare ; A-B sur durée max de famine ; B-D et C-D sur délai d'adaptation ; C-C2 sur délai de première tentative ; C-D et D-C2 sur découverte rare. La seule « PRACTICALLY_MEANINGFUL (IC contient 0) » est C vs C2 sur `rare_discovery_rate` (Δ −0,060, IC [−0,160; +0,040]).

Comparaisons phares (Δ = X − Y, poolé, IC 95 % ; toutes ✔ dans `analysis.json` ; le sens du fichier est A-B, j'ai inversé le signe pour B vs A) :

| Comparaison | Métrique | Δ [IC 95 %] | d_z | Cliff | Catégorie |
|---|---|---|---|---|---|
| A vs R | info_ratio | +0,001 [+0,001; +0,002] | +0,09 | +0,05 | STATISTICALLY_DISTINGUISHABLE (sous le seuil 0,03) |
| B vs A | info_ratio | +0,141 [+0,138; +0,144] | +2,17 | +1,00 | DISTINGUISHABLE+MEANINGFUL |
| B vs A | famine | +0,005 | +0,49 | +0,20 | sous seuil 0,02 |
| B vs A | délai d'adaptation | −100,8 [−106,1; −95,4] | | | DISTINGUISHABLE+MEANINGFUL |
| B vs A | excès muet | −0,033 | | | DISTINGUISHABLE+MEANINGFUL |
| B vs C2 | info_ratio | −0,108 [−0,111; −0,105] | −2,59 | −1,00 | C2 meilleure |
| B vs C2 | délai 1re tentative | −34,0 [−35,3; −32,7] | | | B bien plus rapide |
| B vs C2 | délai d'adaptation | −32,2 [−41,6; −23,2] | | | B plus rapide |
| B vs C | famine | −0,142 [−0,144; −0,141] | | | B ≪ C |
| B vs D | info_ratio | −0,079 [−0,085; −0,073] | −1,14 | −0,75 | D meilleure |
| B vs D | délai d'adaptation | −3,4 [−13,4; +6,9] | −0,07 | | INCONCLUSIVE |
| C vs D | info_ratio | +0,016 [+0,010; +0,021] | +0,18 | | sous le seuil |

**Vérification directe de la revendication phare** : B > A en `info_ratio` dans **200 paires scénario×graine sur 200** (✔ compté) ; Δ par scénario B−A : S1 +0,058 · S2 +0,126 · S3 +0,101 · S4 +0,153 · S5 +0,195 · S6 +0,111 · S7 +0,275 · S8 +0,132 · S9 +0,189 · S10 +0,071 (✔). C2 > B en info dans les 10 scénarios (Δ de +0,049 en S3 à +0,158 en S1 ✔).

**Test de dominance (62 cases scénario×métrique)** : pour chaque paire ordonnée (X, Y) on compte les cases où X est pratiquement meilleur / pire / égal ; « X domine Y » seulement s'il n'est pire dans aucune case. Résultat : **pour chacune des 30 paires ordonnées, X est pire dans au moins 4 cases** (minimum 4, pour R>A et A>R — ✔). Exemples ✔ : B>A 25/9/28 ; A>B 9/25/28 ; C2>B 12/31/19 ; B>C2 31/12/19. Donc `ANY_POLICY_DOMINATES_ACROSS_HELDOUT = NO` est correct par comptage.

Robustesse aux graines : coefficient de variation moyen de `info_ratio` (A 0,084 ; B 0,046 ; C 0,046 ; D 0,058 ; C2 0,031 ; R 0,086) ✔ recalculé. Pires runs (✔ recalculés) : famine max A 0,000 ; B 0,028 ; C 0,274 ; D 0,174 ; C2 0,077 ; R 0,000 ; durée max de famine : A 78, B 109, C 388, D 360, C2 188, R 91 ; info minimale : A 0,288, B 0,506, C 0,446, D 0,505, C2 0,657, R 0,261.

### 3.7 Coût de calcul (rapport `05` §4 ; ✔ recalculé)

Secondes de politique par run (3 200 tentatives + burn-in), 4 workers en parallèle : A 0,030 ; B 0,032 ; C 0,064 ; D **3,607** ; C2 0,068 ; R 0,003. VW est ≈ 100× plus lent. Mémoire non re-mesurée en V2 (le rapport cite des valeurs V1 à 160 cellules : 47 Mo numpy seul, ≈ 173-183 Mo avec River, ≈ 71 Mo avec VW ; **non lu** dans les rapports V1). Passage à l'échelle > ~250 cellules non testé.

### 3.8 Scénarios adversariaux post hoc (rapport `09` ; ✔ tables recalculées)

Écrits **après** la Phase B, pour tenter de falsifier le « gagnant apparent » B. Graines 4000-4019, paramètres gelés ; pas dans le verdict.

| # | Attaque |
|---|---|
| X1 | la moitié de la flotte (60/120) muette pour toujours dès τ=40 |
| X2 | 30 cellules basculent entre 0,75 et 0,05 tous les 40 cycles |
| X3 | aucun gradient d'information (toutes P=0,15) |
| X4 | churn extrême : 20 naissances + 20 retraits tous les 10 cycles (cellules de ≈ 40 cycles) |
| X5 | les 30 meilleures cellules ne renvoient rien 1 fois sur 2 |

`info_ratio` (moyenne sur 20 graines) :

| Scénario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| X1 | 0,304 | 0,694 | 0,216 | 0,547 | **0,807** | 0,336 |
| X2 | 0,555 | 0,683 | 0,781 | 0,703 | 0,759 | 0,556 |
| X3 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |
| X4 | 0,574 | 0,622 | 0,681 | 0,693 | 0,679 | 0,575 |
| X5 | 0,486 | 0,557 | 0,529 | 0,526 | **0,617** | 0,483 |

Points clés ✔ : en X1, A (0,304) et C (0,216) font **pire que le tourniquet** (0,336) ; le silence permanent de la moitié de la flotte fait passer la part d'attention sur muets de B à 0,075 (référence uniforme 0,438), de A à 0,492, de C à 0,724, de C2 à 0,037. X3 est **dégénéré** (oracle = n'importe quelle politique → tous 1,000 : limite de la métrique, pas un résultat de politique). X5 : `silent_excess` C +0,230, D +0,171, A +0,027 (✔).

---

## 4. Candidats évalués un par un

Classification du rapport `11` §2 (mes commentaires en italique, marqués **mon analyse**).

### 4.1 B — D-UCB + garde de fraîcheur + backoff : **ADOPT_REFERENCE** (confiance moyenne)

- Sens de « ADOPT_REFERENCE » : *référence externe forte pour une évaluation locale future* — pas une adoption, pas une intégration (rapport `11` en-tête).
- Chiffres : info 0,649 (A 0,508) ; famine 0,005 ; excès muet −0,025 ; +0,141 vs A [0,138 ; 0,144] ; 0 défaillance catastrophique en X1-X5 ; déterministe (18/18).
- Points faibles mesurés : retour de dormance dépendant d'une « phase » (S9 ≈ 60 cycles, jusqu'à censuré selon S et M) ; découverte d'événements rares plus faible que l'uniforme (S8 : 0,51 vs 0,75) ; famine légère en S5/S9 (0,021 / 0,028) ; dégât en X5 (info 0,557, sous-service des cellules intermittentes) ; paramètres γ et S en bord de grille ; sans backoff (M=1) elle est capturée.
- **Conditions de changement de verdict** (rapport) : un rejeu local contredisant le modèle de silence/retour ; une flotte où S·M dépasse la structure réelle des cycles ; des paramètres sélectionnés sur données réelles en bord de grille.
- **Mon analyse (INFERENCE)** : le rapport `09` §3 note que, avec S=25 et un plafond de K/2 = 5 revisites forcées par cycle, la garde ressemble à « un demi-tourniquet » — c'est même vérifiable par arithmétique : 5 revisites × 25 cycles = 125 visites possibles par intervalle pour une flotte de 120 cellules. L'autre moitié du budget est du D-UCB. Donc une partie du bon score de B en couverture/famine est mécaniquement garantie par la garde, et son gain d'information vient de la moitié restante.

### 4.2 C2 — River + garde partagée : **ADAPT_CANDIDATE** (confiance moyenne-basse)

- Meilleure information (0,757), meilleure information au pire run (0,657 min), famine ≤ 0,077 dans tous les runs.
- Défauts : latence de nouvelles cellules ≈ 35 cycles (ε-glouton n'atteint les nouvelles cellules que par exploration aléatoire) ; **retour de dormance en S9 raté à 100 %** (part cible 0,000) ; 7,8 % des nouvelles cellules jamais vues en S10 ; famine 0,167 en X1.
- Conditions : corriger le démarrage à froid (forcer les cellules jamais vues, comme B), détection de retour indépendante de la phase, puis re-validation sur **nouvelles** graines held-out.
- **Mon analyse (INFERENCE)** : C2 bat B en information dans 10 scénarios sur 10, et obtient les meilleurs J en TRAIN/VALIDATION (0,742/0,750 contre 0,692/0,632). Le rapport 11 nomme pourtant B « BEST_EXTERNAL_REFERENCE » et C2 « BEST_ADAPTIVE_CANDIDATE ». La hiérarchie repose sur la décision de pré-enregistrer C2 comme « diagnostic » et non comme « cinquième candidat » : c'est un choix de cadrage, pas un résultat.

### 4.3 A — référence lifecycle pondéré (contrat opérateur) : **ADAPT_CANDIDATE** (garder comme base fixe ; confiance moyenne)

- Points forts : zéro famine dans 1 200 runs held-out et 100 runs adversariaux, péremption ≈ 0 (max 0,017), conservation exacte (7e-15), déterministe, tous les invariants sémantiques respectés.
- Constat : **équivalent au tourniquet** en information (Δ +0,001, sous le seuil 0,03) ; adaptation censurée à 100 % (S2/S3/S9) ; sous le tourniquet en X1 (0,304 vs 0,336) ; insensible à ses propres constantes (7 variantes).
- Cause probable donnée par le rapport (INFERENCE) : faible écart de poids (×3), états qui ne changent qu'après ≥ 20 preuves, plancher de 5 %. **Ma lecture complémentaire (INFERENCE)** : voir 7.2 (l'horizon de 400 cycles empêche mécaniquement la plupart des cellules d'atteindre 20 preuves avant la fin).
- Ce qui changerait le verdict : un modèle d'état plus réactif (< 20 preuves) ou le vrai classifieur privé — **inconnu, non testé**.

### 4.4 D — VW cb_explore_adf, caractéristiques partagées : **PARK** (confiance basse-moyenne)

- Valide, sans fuite, exécuté (pas « NOT_EXECUTED_FOR_VALIDITY »). Info 0,728 ≈ C ; famine 0,073 ; fragile (0,27) ; ≈ 100× plus coûteux.
- Le partage d'information par caractéristiques (groupe) n'apporte **aucun gain mesurable** (variante `grp0` ≥ `grp1` en TRAIN : 0,645 vs 0,636 ; en sensibilité, différences dans le bruit).
- À rouvrir si : caractéristiques qui co-évoluent réellement, `--epsilon_decay` (jamais lancé), budget de calcul tolérant.

### 4.5 C — River tel que livré : **REJECT** comme allocateur (confiance haute pour ce comportement)

- Famine 0,147 (pire run 0,274), 289 cycles de famine max, 4,7-12,6 % de nouvelles cellules jamais vues, capture +26 pts en S9, BRITTLE (0,10). Reproduit la conclusion V1 sur scénarios indépendants.
- Précision du rapport : la bibliothèque River a de bonnes *briques* ; ce sont ses *politiques livrées* qui échouent comme allocateur. Qualité de bibliothèque (maintenance, licence) séparée dans `10`.

### 4.6 R — Tourniquet : repère, pas de verdict.

### 4.7 Éléments de V1 : ce qui survit (`11` §3, à titre de synthèse)

Voir tableau section 8.

---

## 5. Bloc final complet (reproduit tel quel) et explication ligne par ligne

```
TRAIN_SCENARIOS=T1_mixed_abrupt, T2_mixed_drift_gap, T3_churn_lowinfo, T4_dormancy_rare   (seeds 1000-1004)
VALIDATION_SCENARIOS=V1_coldstart_outage, V2_abrupt_then_drift, V3_silence_rare_lowinfo    (seeds 2000-2004)
HELDOUT_SCENARIOS=S1_MASSIVE_COLD_START, S2_ABRUPT_REGIME_CHANGE, S3_SLOW_DRIFT, S4_TEMPORARY_SILENCE,
                  S5_PROVIDER_DATA_GAP, S6_STALE_BUT_VALID, S7_GENUINELY_LOW_INFORMATION,
                  S8_RARE_HIGH_INFORMATION, S9_LONG_DORMANCY_RETURN, S10_DYNAMIC_POPULATION  (seeds 3000-3019, 20 per scenario)

POLICY_A_LIFECYCLE_FLOOR=EXECUTED (operator-supplied contract, fixed, not tuned; evidence-derived classifier is V2-defined)
POLICY_B_DUCB_GUARD=EXECUTED (custom D-UCB idea + guard + backoff; tuned on TRAIN/VALIDATION: gamma 0.9995, S 25, M 4)
POLICY_C_RIVER=EXECUTED (river 0.26.1 EpsilonGreedy+EWMean as shipped, hygiene wrapper; tuned: fading 0.1, eps 0.2); C2 = C + shared guard (diagnostic)
POLICY_D_VW=EXECUTED (vowpalwabbit 9.11.9 cb_explore_adf, shared observable features, no id feature; tuned: epsilon 0.2, lr 0.05, group feature off) — valid formulation existed; not NOT_EXECUTED_FOR_VALIDITY

HELDOUT_ISOLATION=PASS   (17 automated checks, results/isolation_report.json; 18/18 unit tests)

NEW_ARM_STARVATION_A=NOT_OBSERVED (0 % of new cells unseen; mean per-run max first attempt 8 cycles)
NEW_ARM_STARVATION_B=NOT_OBSERVED (0 %; max 8 cycles)
NEW_ARM_STARVATION_C=OBSERVED (4.7 % of new cells never attempted in S1, 12.6 % in S10; mean per-run max first attempt 306 cycles)
NEW_ARM_STARVATION_D=OBSERVED_MILD (0.7 % S1, 2.1 % S10; mean per-run max first attempt 114 cycles)   [C2: 0 % S1, 7.8 % S10]

SILENT_CELL_CAPTURE_A=NOT_OBSERVED (+2.4 to +3.4 pts over uniform baseline: proportional, floor-driven; X1 permanent silence: information 0.304 < round-robin 0.336)
SILENT_CELL_CAPTURE_B=NOT_OBSERVED with the frozen backoff (-2.6 to -11.2 pts vs baseline); OBSERVED if backoff disabled (M=1: 67 % of attention on permanently silent cells in X1)
SILENT_CELL_CAPTURE_C=OBSERVED (+2.4 S4, +10.6 S5, +26.4 pts S9: 39.5 % of attention on silent cells vs 13 % baseline)
SILENT_CELL_CAPTURE_D=NOT_OBSERVED in S4/S5/S9 (-0.3 to -4.0 pts); OBSERVED in post-hoc X5 (+17 pts)   [C2: -2.8 to -11.5 pts]

REGIME_ADAPTATION_A=NONE (adaptation delay censored in 100 % of S2/S3/S9 runs; = round-robin)
REGIME_ADAPTATION_B=YES, moderate (delay S2 54 / S3 174 / S9 60 cycles; 0 % censored)
REGIME_ADAPTATION_C=YES but with starvation/capture (S2 89, S3 215, S9 9 cycles; 10 % censored in S2)
REGIME_ADAPTATION_D=YES, moderate (S2 82 / S3 183 / S9 32; 5 % censored in S3, S9)   [C2: S2 95, S3 199, S9 censored 100 %]

PARAMETER_ROBUSTNESS_A=ROBUST (trivially: floor 0-20 %, flat/steep weights, alt classifier all leave behaviour ~ round-robin)
PARAMETER_ROBUSTNESS_B=SENSITIVE (0.69 acceptable; gamma trades information vs adaptation, S trades coverage vs information, M=1 is unsafe)
PARAMETER_ROBUSTNESS_C=BRITTLE (0.10; no configuration free of starvation)
PARAMETER_ROBUSTNESS_D=BRITTLE (0.27; learning-rate / exploration dominated)   [C2: SENSITIVE 0.40, borderline]

BEST_EXTERNAL_REFERENCE=B (D-UCB + staleness guard + bounded no-evidence backoff)
BEST_ADAPTIVE_CANDIDATE=C2 (River primitives + shared guard: best information and best worst-case information; needs a fix for cold start and return-from-dormancy) — runner-up B

ANY_POLICY_DOMINATES_ACROSS_HELDOUT=NO
ANY_SCIENTIFIC_INVALIDATION=NO

FINAL_VERDICT=ADAPTIVE_POLICY_SUPPORTED_FOR_LOCAL_EVALUATION
```

### Explication ligne par ligne

- **`TRAIN_SCENARIOS`, `VALIDATION_SCENARIOS`, `HELDOUT_SCENARIOS`** : les trois jeux de scénarios et leurs graines (section 2.2). Held-out = 10 scénarios × 20 graines = 200 « situations » ; × 6 politiques = 1 200 runs ✔.
- **`POLICY_A_LIFECYCLE_FLOOR=EXECUTED (...)`** : A a été exécutée avec les constantes de l'opérateur, sans réglage ; la façon de déduire l'état de cycle de vie à partir des preuves (le « classifieur ») a été inventée par la V2, pas fournie par l'opérateur.
- **`POLICY_B_DUCB_GUARD=EXECUTED (...)`** : B est du code sur mesure ; réglages gelés : γ=0,9995 (oubli très lent), S=25 (une cellule non tentée depuis 25 cycles est « forcée »), M=4 (l'intervalle peut être multiplié jusqu'à 4× pour les cellules qui ne répondent pas).
- **`POLICY_C_RIVER=EXECUTED (...)`** : ε-glouton River avec moyenne exponentielle (`fading` 0,1 = poids 10 % de la nouvelle observation) et ε=0,2 (20 % d'exploration au hasard) ; **C2** = C + garde.
- **`POLICY_D_VW=EXECUTED (...)`** : VW avec exploration ε=0,2, taux d'apprentissage 0,05, sans caractéristique de groupe ; « valid formulation existed » = une formulation sans fuite d'information a pu être définie donc D n'est pas écartée d'office.
- **`HELDOUT_ISOLATION=PASS`** : 17 contrôles automatiques (empreintes des fichiers gelés, paramètres = verrou, aucun import held-out dans le code de réglage, graines disjointes, ordre des commits) tous vrais ✔ ; 18 tests unitaires (✔ j'ai lancé : 18 passed).
- **`NEW_ARM_STARVATION_*`** : « une nouvelle cellule peut-elle rester inaperçue ? ». A et B : non (première tentative en ≤ 8 cycles) ; C : oui (4,7 % en S1, 12,6 % en S10 jamais tentées) ; D : léger ; C2 : 0 % en S1 mais 7,8 % en S10 (des cellules qui vivent moins que l'intervalle de garde S=50 sont retirées avant d'être revisitées).
- **`SILENT_CELL_CAPTURE_*`** : « des cellules muettes absorbent-elles trop d'attention ? ». Les « pts » = points de pourcentage au-dessus de la part uniforme. A : +2,4 à +3,4 pts (proportionnel, dû au plancher). B : sous la référence (−2,6 à −11,2) tant que le backoff est actif ; si M=1, 67 % en X1. C : capturée jusqu'à +26,4 pts (S9). D : ok en S4/S5/S9 mais capturée en X5 (+17 pts). Précision (✔) : « +17 pts » correspond à 0,171 mesuré.
- **`REGIME_ADAPTATION_*`** : rapidité à concentrer l'attention sur les cellules qui ont changé. A : aucune (censuré 100 %) ; B : modérée (54/174/60 cycles) ; C : oui mais avec famine/capture ; D : modérée ; C2 : rate S9.
- **`PARAMETER_ROBUSTNESS_*`** : classes du tableau 3.5.
- **`BEST_EXTERNAL_REFERENCE=B`** : la meilleure *référence externe* en tant que compromis sûr ; **`BEST_ADAPTIVE_CANDIDATE=C2`** : la meilleure en information brute, mais avec défauts à corriger.
- **`ANY_POLICY_DOMINATES_ACROSS_HELDOUT=NO`** : aucune politique n'est meilleure ou égale partout (section 3.6).
- **`ANY_SCIENTIFIC_INVALIDATION=NO`** : aucun défaut découvert n'invalide un résultat ; le rapport précise que c'est « une déclaration sur les défauts trouvés, pas une preuve qu'il n'y en a pas ».
- **`FINAL_VERDICT=ADAPTIVE_POLICY_SUPPORTED_FOR_LOCAL_EVALUATION`** : voir section 0. Le rapport note que `NO_POLICY_DOMINATES` est « aussi vrai » mais qu'il a choisi le verdict qui indique quelle décision les preuves soutiennent. **Mon commentaire** : c'est un verdict formulé pour être prudent ; il ne dit pas que B « gagne ».

---

## 6. Contrôles de validité

### 6.1 Ce que la lane a mis en place (et que j'ai vérifié)

| Contrôle | Résultat | Ma vérification |
|---|---|---|
| Isolation held-out (17 contrôles) | PASS | ✔ `isolation_report.json` : 17 clés, toutes `true` ; SHA recalculés identiques |
| Tests unitaires | 18/18 | ✔ j'ai exécuté `pytest` : **18 passed** en 24 s |
| Déterminisme inter-processus | 18 empreintes identiques (3 scénarios × 6 politiques × 3 `PYTHONHASHSEED` : 0, 1, 12345) | ✔ `determinism.json` : 18 clés, `identical: true` |
| Reproduction par moi | S1, graine 3000 : A `4b5e7f46…`, R `e1b86d6f…`, B `ebad78fc…`, C `0ba8a0bc…`, C2 `1fb730ba…`, D `52316946…` | ✔ **6 empreintes identiques** à `determinism.json` ; l'empreinte de B est aussi celle stockée dans `heldout/S1_…json` (seed 3000) |
| Pas de tentative sur cellule inéligible | 0 sur 1 200 runs | ✔ |
| Conservation de l'allocation de A | erreur max 7,1e-15 | ✔ 7,105e-15 |
| Sémantique « absence ≠ négatif » | tests + audit compteurs sur 600 runs River/VW | ✔ (tests exécutés ; compteur d'événements sans preuve 110 739 ✔) |
| Absence de fuite (lookahead) dans le registre | le `Ledger` ne contient aucun champ caché | ✔ lecture de `ledger.py` : pas d'accès à `P`, `silent`, `U` ; les politiques n'importent que `scenario_core.K, FRESH, MAG` |
| Indépendance train/held-out | générateurs séparés, graines disjointes, AST-test d'imports | ✔ `scenarios_dev.py` n'importe pas `scenarios_heldout` ; `make_dev_scenario` refuse `heldout` (test) |

### 6.2 Contrôles négatifs / positifs

- « Contrôle négatif » : X3 (aucun signal) — toutes les politiques obtiennent 1,000 → la métrique devient dégénérée (le rapport le déclare). Aucune politique ne « réussit » ici (nul mérite).
- « Contrôle positif » : le tourniquet R sert de repère uniforme ; A ≈ R montre que A n'apporte rien à l'information, ce qui est cohérent avec la théorie.
- Contrôle d'ablation : backoff M=1 vs M=4 vs M=16 sur X1/X5 (3.4, P4) ; B avec/sans garde.
- Il n'y a **pas** de test « mutation » (introduire volontairement une fuite pour voir si le banc la détecte) : je ne peux pas dire que le banc détecterait une fuite subtile.

### 6.3 Erreurs corrigées en cours de route (dites par le rapport `11` §4 / `01` §9)

1. Règle de départage du réglage codée « rang train » au lieu de « plus proche du centre » → corrigée avant le held-out, 4 réglages refaits.
2. `analysis.py` faisait référence à une métrique sans seuil pré-enregistré (`new_never_attempted`) → plantage après la Phase B ; métrique retirée de l'ensemble de dominance (toujours rapportée) ; analyse relancée ; résultats bruts intacts. **Je n'ai pas pu le vérifier** (l'historique montre un seul commit d'analyse) : ?
3. Exécution des politiques sur graines pilotes (9000-9002) avant le commit de gel (invariants seulement, aucune métrique lue) → divulgué dans `freeze_manifest.json` ✔ (texte lu).
4. Dégénérescence de X3 → limite de métrique.

### 6.4 Écarts au protocole déclarés

- Le dépôt V1 a son banc à `reports/001…/bench/` et non à `bench/` (`00` §1).
- Politique A fournie par l'opérateur (`00` §2.2).
- Règle de classification de la sensibilité définie par V2 hors `protocol.json`.
- Aucune réduction du nombre de graines n'a été nécessaire (Phase A à 54 s).

---

## 7. Critique indépendante

### 7.1 Ce que les chiffres ne prouvent PAS

- **Ils ne prouvent rien sur des données réelles.** Tout est simulé par l'auteur ; le rapport le dit mais la portée réelle est encore plus limitée : les générateurs held-out et dev partagent le même `Builder`, les mêmes distributions (moyennes de groupe U(0,12 ; 0,60), valeurs 0,5 et 1,0, mêmes constantes `K`, `R`, `FRESH`). L'indépendance est **structurelle** (mêmes règles du jeu, autres compositions), pas une vraie sortie de distribution.
- **Les IC ne quantifient que l'incertitude entre graines**, pas celle entre familles de scénarios (rapport `08` §1 le reconnaît). Les IC étroits (par exemple B vs A ±0,003) sont trompeurs quant à la généralisation : dix scénarios choisis par l'auteur.
- **Ils ne prouvent pas que B est « la meilleure »** : C2 est meilleure en information dans tous les scénarios ; C et D le sont dans plusieurs.
- **Ils ne disent rien de la latence réelle**, des retards de retour d'information, des bruits à queues lourdes, ni des flottes de plus de 250 cellules.

### 7.2 A ≈ tourniquet : en partie une conséquence mécanique (mon analyse, INFERENCE)

L'état d'une cellule chez A ne quitte `PROMISING` que si `n_evidence ≥ 20` (`CLS`, `policies.py` l. 32) ; avant `n_evidence < 5`, elle est `EXPLORATION` (poids 1,5). Avec 10 tentatives/cycle et ~120 cellules, une cellule reçoit ≈ 0,083 tentative par cycle ; atteindre 20 preuves demande donc de l'ordre de 240 cycles (et une preuve `EVIDENCE(0.0)` compte comme une preuve : seul le silence n'en compte pas). Le test dure 400 cycles dont 80 de burn-in. Conclusion : **pendant la plus grande partie de l'horizon, A ne peut pas différencier les cellules**, ce qui suffit à expliquer une allocation quasi uniforme, indépendamment de la qualité du contrat. Les variantes testées (plancher, poids, `altcls`) ne touchent pas ce verrou de 20 preuves. Le rapport mentionne le seuil de 20 mais pas cette arithmétique ni le lien avec l'horizon ; le classifieur n'a **pas** été varié sur ce paramètre (`n_proven`, `n_min`). Autrement dit, la conclusion « A ne s'adapte pas » vaut pour *ce classifieur × cet horizon*, pas pour le contrat.

De plus, le critère d'adaptation (≥ 2× la part de population) est inatteignable par une allocation quasi uniforme (section 3.3).

### 7.3 Choix en bord de grille et budgets de réglage inégaux

- Tous les réglages choisis sont au bord : γ=0,9995 maximal pour B (et S=25 minimal) ; ε=0,2 maximal pour C, C2 et D. Le rapport le dit et se contente de le « porter comme caveat » (`04` §3).
- **Effet sur l'équité** (INFERENCE) : B a 45 réglages explorés, dont 2 axes structurels (garde, backoff) inventés par l'auteur ; C 21 ; D 30 ; A 0. L'auteur de l'évaluation est aussi l'auteur de B (code sur mesure, écrit après avoir lu la V1 qui suggérait la garde). Le protocole évite de réutiliser des paramètres V1, mais la **forme** de B est très informée par les défauts déjà connus des scénarios. Pas de « B écrit par un tiers ».
- L'objectif J pénalise fortement famine/péremption, or B et C2 contiennent une garde qui abaisse mécaniquement ces deux termes ; les politiques sans garde (C, D) ne peuvent pas rivaliser sur J. J favorise donc structurellement les designs avec garde, et les métriques de comparaison held-out (famine, péremption, couverture) sont de la même famille que J.

### 7.4 Un cadrage qui décide du « gagnant »

- Pré-enregistrement de C2 comme « diagnostic, pas un cinquième candidat ». Sans ce cadrage, le meilleur en information et en pire cas serait C2, avec un bon J en dev (0,742/0,750 vs 0,692/0,632 pour B).
- Le rapport `09` §4 l'avoue : « "B wins" is false; "B is the safest adaptive candidate" is what survives ». Mais l'étiquette `ADOPT_REFERENCE` reste attachée à B seule.
- Le verdict global est cohérent mais **sa formulation** dépend de ces décisions de cadrage.

### 7.5 Robustesse statistique

- 20 graines × 10 scénarios ; scénarios fixes ; pas de correction pour 150 comparaisons (assumé).
- Les métriques poolées sur 1-3 scénarios (`rare_discovery_rate`, `new_ttfa_median`, `adapt_delay`) sont peu robustes : par exemple B vs A sur `rare_discovery_rate` repose sur un seul scénario (S8) et 20 graines.
- Les tailles d'effet d_z et le delta de Cliff sont calculés sur les différences empilées entre scénarios ; le delta de Cliff (non apparié) sur valeurs concaténées mélange des niveaux de scénarios différents : indicatif seulement.
- La censure : la moyenne du délai d'adaptation avec valeurs censurées (par exemple A à 220/280/90) est une moyenne de bornes, pas de durées ; l'écart poolé « B−A = −100,8 cycles » est donc lié à la manière de coder la censure (l'écart réel de A est ≥ cette valeur, non mesurable).
- Sensibilité : réalisée avec seulement 5 graines qui **se recoupent** avec les graines held-out (3000-3004) — descriptive, mais elle ne doit pas servir à choisir (le rapport le dit).
- Post hoc : les attaques X1-X5 ont été conçues *après* avoir vu les résultats ; elles « peuvent révéler des faiblesses, pas certifier une force » (rapport).

### 7.6 Écarts rapports ↔ résultats bruts ↔ dépôt (cherchés systématiquement)

Résultat global : **aucun écart numérique** entre les rapports et les JSON bruts sur tout ce que j'ai recalculé (plusieurs centaines de valeurs, section 9.1). Les écarts que j'ai trouvés sont d'un autre type :

1. ✘ **Journal périmé** : `bench/v2/logs/tune_BCC2.log` indique `B chosen B|g0.9995|S25|M16` et `C chosen C|eps_ew|f0.3|e0.2`, alors que les paramètres gelés sont M4 et f0.1 (`selected_*.json`, `params_lock.json`). Le journal correspond au premier tirage, avant la correction de la règle de départage. Le rapport `01` §9 documente bien la correction, mais le journal n'a pas été régénéré : un lecteur pressé pourrait croire à une contradiction.
2. ✘ **Explication du choix de C** : `01` §9 attribue le passage de f0.3 à f0.1 à une égalité (« validation J within 0.005 of the leader ⇒ tie ⇒ nearest the grid centre »). En réalité (`selected_C.json`) `f0.1` est le leader strict en validation (0,5142 vs 0,5112) ; la règle « égalité → centre » n'était pas nécessaire. Sans conséquence sur le résultat.
3. ✘ (mineur) **`07` §2 : « M=4 vs M=16 est indistinguable dans ce banc »** — vrai en moyenne globale (B S25 : info 0,654 vs 0,651), mais faux pour S9 : B S25/M16 reste censuré à 90 alors que M4 récupère en ~59 cycles (`sensitivity/B.json` ✔ ; le rapport `06` P7 cite pourtant ces cas). Formulation trop générale.
4. ✘ (cosmétique) La PR s'intitule « (draft) » mais est fermée/mergée ; sans conséquence.
5. ? **Non vérifiable** : que la règle de classification de la sensibilité (`sens_summary.py`) ait été « définie avant sa première exécution » (rien dans le dépôt ne l'horodate avant) ; que l'erreur de `analysis.py` (métrique sans seuil) ait réellement eu lieu (aucune trace dans un journal) ; les dates/versions de River/VW/arXiv du rapport `10` (aucun accès réseau utilisé par moi).
6. Le rapport `06` P6 dit « B... turnover 0,533 … D 0,446, C2 0,309, C 0,270 » : ✔ = valeurs S10 de la table `05`.

### 7.7 Contradictions internes / tensions

- `BEST_EXTERNAL_REFERENCE=B` vs `BEST_ADAPTIVE_CANDIDATE=C2` : deux « meilleurs » ; ce n'est pas contradictoire mais demande de lire les définitions.
- Le verdict `ADAPTIVE_POLICY_SUPPORTED…` est justifié par « B est non dominé, sans échec catastrophique, bat A en info 10/10 et 200/200 » ; mais A est lui-même un repère dont le rapport dit qu'il est quasi identique au tourniquet. **Le contenu informatif de « B bat A » est donc essentiellement « un bandit à oubli bat l'uniforme quand certaines cellules valent plus que d'autres »**, ce qui est attendu par construction dans un simulateur où les valeurs diffèrent et sont apprenables.
- Scénarios de silence (S4, S5, S9) : « B fait moins d'attention aux cellules muettes que l'uniforme » — mais la métrique récompense de ne pas regarder les cellules muettes, alors qu'en pratique regarder une cellule muette est justement la seule façon de savoir qu'elle est revenue (S9) ; le compromis est reconnu par le rapport (P7), mais le tableau final des statuts « NOT_OBSERVED » pour B sur la capture cache ce coût.
- L'oracle d'`info_ratio` connaît les drapeaux de silence de chaque cycle (`ok = elig & ~silent`), même pour X5 où le silence est aléatoire par tentative ; l'oracle est donc inatteignable et les niveaux absolus de `info_ratio` en X5 ne sont pas interprétables en « % de l'optimum ».

### 7.8 Autres fragilités

- Une seule échelle de flotte (30 à 240 cellules) et un seul `K=10` ; l'intervalle de garde est en « cycles » sans lien avec une horloge réelle (rapport `09`).
- L'information est binaire (`0` ou `mag`) ; pas de bruit continu ni de latence.
- Le classifieur de A est de V2 ; toute la conclusion sur A en dépend.
- D est évalué avec un seul jeu de caractéristiques ; conclusion « le partage n'aide pas » limitée à ces caractéristiques.
- Mesure de temps sous charge parallèle (4 workers) : comparatif seulement.
- Le rapport `10` cite des articles arXiv (« titres/dates seulement, non lus ») : à traiter comme non pertinent pour les résultats.

---

## 8. Comparaison entre runs / études (V1 vs V2, dev vs held-out, sensibilité vs run principal)

La lane a une seule branche mais plusieurs « jeux de résultats ». Je compare point par point ce qui répond aux mêmes questions.

### 8.1 V1 (in-sample) vs V2 (held-out) — chiffres tels que cités

Lu : rapports V2 (`11` §3) et l'en-tête de `reports/001…/07_FINAL_ADJUDICATION.md` (lignes 1-70). Les autres rapports V1 (00-06) et son banc : **non lus** par moi.

| Question | V1 (label V1) | V2 (held-out, OBSERVED) | Accord ? | Raison probable de la différence |
|---|---|---|---|---|
| Les bandits « suivent la récompense » affament-ils ? | 20-24 % des cellules intouchées ; 72-82 % périmées (PROVEN in-sample) | C : famine 0,147 ; péremption 0,23 ; D : 0,073 / 0,125 | **Accord qualitatif** | Modèles différents (V1 : 160 cellules, 1 200 tours, récompense Bernoulli ; V2 : sorties typées, groupes, retraits). Les chiffres ne sont **pas** comparables et ne doivent pas être mélangés (`01` §9). |
| Les cellules muettes capturent-elles l'attention ? | 72-89 % du gaspillage dans la fenêtre de trou (PROVEN dans ce scénario) | C en S9 : 39,5 % de l'attention sur muets vs 13 % ; B sans backoff en X1 : 67 % | Accord | Idem. |
| Frontière γ de D-UCB (couverture ↔ adaptation) | PROVEN in-sample | γ échange information/adaptation (0,578→0,685 ; délai 170-197→67-105) ; l'aspect couverture est déplacé sur l'intervalle S | Accord partiel | Dans V2 la couverture est portée par la garde (S), pas par γ. |
| Garde de fraîcheur | supprime la famine, in-sample, code de l'auteur | B : famine 0,005 ; mais sa sûreté dépend du backoff non testé en V1 | Accord renforcé et nuancé | Le backoff (V1 : UNKNOWN) est maintenant OBSERVED nécessaire. |
| Backoff des « tenté sans preuve » | non testé | sans lui B capturée (X1 67 %, info 0,209 < tourniquet) ; avec lui coût = retour de dormance ≤ S·M | Nouveau | — |
| Partage de caractéristiques VW | non testé | aucun gain mesurable ; VW fragile et lent | Nouveau (négatif) | Caractéristiques limitées au registre observable. |
| River « le plus utilisable » | primitives / forme d'API (ses politiques rejetées) | C REJECT ; C2 (primitives + garde) compétitif | Cohérent | — |

### 8.2 Dev (TRAIN/VALIDATION) vs held-out

| Politique | J-VALID (dev) | Position held-out | Commentaire |
|---|---|---|---|
| C2 | 0,750 (meilleur) | meilleur en info (0,757), mais échec S9 | La dev n'avait pas de retour de dormance aussi tardif (T4 : silence 30-150, retour à 150 avec 250 cycles pour récupérer ; S9 : retour à 230, 90 cycles). Le rapport signale explicitement que le J dev « ne prédit pas » le held-out (`04` §3). |
| B | 0,632 | compromis ; écarts TRAIN→VALID +0,059 | — |
| C | 0,514 | REJECT | Dev déjà cohérente avec held-out : 3/21 réglages ≥ tourniquet. |
| D | 0,573 | PARK | Idem. |
| A | 0,453 vs R 0,458 | A ≈ R | Dev prédisait déjà le held-out. |

### 8.3 Sensibilité (5 graines) vs held-out principal (20 graines)

Valeurs de la même configuration gelée : B info 0,654 (5 graines) vs 0,649 (20) ; C 0,756 vs 0,743 ; C2 0,767 vs 0,757 ; D 0,741 vs 0,728 ; A 0,517 vs 0,508 (✔ tables `07` vs `05`). Écart max ≈ 0,013 → cohérent (les 5 graines sont un sous-ensemble des 20, donc pas indépendant).

### 8.4 Adversarial vs held-out

B : information adversariale (0,557-0,694 hors X3) dans la même plage que held-out (0,548-0,693) ; le classement C2 > B en info se répète en X1, X2 (0,759 vs 0,683), X4, X5 ; C et D dépassent B en X2 et X4.

---

## 9. Reproductibilité

### 9.1 Ce que j'ai fait moi-même

| Action | Résultat |
|---|---|
| Recalcul des tableaux du rapport `05` | ✔ 420 cellules, 0 écart |
| Recalcul des moyennes poolées | ✔ |
| Recalcul du réglage (J-TRAIN de B, comptages) | ✔ |
| Recalcul de la sensibilité (`sensitivity_summary.json`), de l'adversarial et du diagnostic de backoff | ✔ |
| Comptage des catégories statistiques (106/33/1/10) et de la dominance | ✔ |
| Exécution de `pytest` (18 tests) | ✔ 18 passed |
| Ré-exécution S1/graine 3000 pour A, R, B, C, C2, D | ✔ 6 empreintes identiques |
| Installation de `vowpalwabbit==9.11.9` (absent de mon environnement) | réalisée pour ce contrôle (dans l'environnement de la session, pas dans le dépôt) |

Je n'ai **pas** relancé les 1 200 runs complets, ni le réglage, ni la sensibilité ni l'adversarial (VW seul demande ≈ 8 min de réglage et ≈ 10 min de sensibilité d'après les journaux).

### 9.2 Comment relancer (commandes du rapport `11` §6)

```bash
python3 -m venv v && . v/bin/activate && pip install -r bench/v2/environment/requirements.lock.txt
cd bench/v2 && PYTHONPATH=src pytest -q tests                # 18 tests
cd src && python tune.py B && python tune.py C && python tune.py C2 && python tune.py D   # réglage dev (écrit configs/selected_*.json)
python heldout.py --seeds 20                                   # Phase B (création exclusive : refuse d'écraser)
python analysis.py && python determinism.py && python verify_isolation.py
# descriptif / post hoc : sensitivity.py <A|B|C|C2|D>, sens_summary.py, adversarial.py, adv_followup.py
```

- **Dépendances** (`requirements.lock.txt`) : numpy 2.4.6, scipy 1.17.1, river 0.26.1, vowpalwabbit 9.11.9, narwhals 2.26.0, pytest 9.1.1 (+ 4 dépendances de pytest). Python 3.11.15 (`python_version.txt`). Machine de l'étude : `Linux vm 6.18.44-fc-v49 x86_64`.
- **Durées observées** : Phase A 54 s ; réglage B 21 s, C 23 s, C2 19 s, D 494 s ; held-out 208 s ; sensibilité A 7 s, B 20 s, C 22 s, C2 17 s, D 569 s (4 cœurs).
- **Attention** : `tune.py C2` exige `selected_C.json` produit par `tune.py C` (et il lit `all_specs`) ; il faut donc l'ordre B, C, C2, D. Refaire `heldout.py`, `sensitivity.py`, `adversarial.py` dans un dossier où les résultats existent déjà **échoue** (création exclusive `'x'`) : il faut travailler dans une copie ou supprimer les résultats.
- **Note technique** : `verify_isolation.py` suppose un dépôt Git avec l'historique exact (commit `034d04a`, chemins `bench/v2/…`) ; hors dépôt, ce contrôle ne se relance pas tel quel.

### 9.3 Ce qui est fourni / ce qui manque

Fourni : code complet, protocole, empreintes, résultats bruts (1 200 runs), tuning brut, sensibilité, adversarial, tests, environnement gelé, journaux.
Manque ou limité : journal de réglage à jour (`tune_BCC2.log` périmé) ; mémoire (RSS) non re-mesurée pour V2 ; aucune exécution sur une autre machine (déterminisme inter-machines UNKNOWN, mais ma ré-exécution dans un environnement de même famille redonne les mêmes empreintes) ; pas d'horodatage externe du gel ; le rapport `10` s'appuie sur des consultations réseau (PyPI, git, arXiv) non reproductibles hors ligne.

---

## 10. Implications pratiques pour AurumShift (pistes « à adjuger plus tard »)

Rappel : **aucune affirmation de compatibilité**. Ce sont des pistes à examiner *plus tard*, contre le vrai dépôt AurumShift, par quelqu'un qui le connaît.

1. **Garder A comme base fixe de comparaison** dans toute évaluation locale (le rapport le propose). Piste : tester localement d'abord *si le classifieur privé réagit en moins de ~20 preuves* — c'est ce qui décide si A peut être autre chose qu'un tourniquet (section 7.2).
2. **Si une politique adaptative est évaluée**, la structure « bandit à oubli + garde de fraîcheur + canal explicite "tenté, sans preuve" avec backoff » est celle qui a le mieux tenu ici. Piste à adjuger : où ce canal existerait dans l'architecture réelle (compatible avec « une source d'autorité par sujet » et « PostgreSQL d'abord » ? — **inconnu**).
3. **L'état minimal** de B est relationnel (par cellule : `N`, `X`, dernière tentative, non-réponses consécutives) — rapport `05` §5 ; à confronter au schéma réel (**inconnu**).
4. **Ne pas utiliser River ou VW comme allocateur tel que livré** (résultats C et D) ; des briques de River dans une composition gardée (C2) restent une piste, avec les deux défauts à corriger.
5. **Le choix de S et M en « cycles »** n'a de sens que lié à la durée réelle d'un cycle et à la latence réelle des preuves (rapport `09`) ; ces valeurs (25, 4) ne se transposent pas.
6. **Contrainte PIT / pas de regard vers le futur** : le banc respecte cette idée en interne (registre observable seulement) mais ne teste aucun scénario de fuite PIT réelle (`pit_unverified` n'est qu'un drapeau qui active le plancher d'exploration de A).
7. **Coût** : les politiques numpy (A, B) coûtent ≈ 0,03 s par run de 3 200 tentatives ; VW ≈ 3,6 s (100× plus). À rapporter au vrai débit, **inconnu**.

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **(Valeur haute) Tester A avec un classifieur plus réactif** : varier `n_min`, `n_proven` (par exemple 5, 10, 20) et l'horizon (800 cycles) pour savoir si « A ≈ tourniquet » est une propriété du contrat ou du couple classifieur × horizon (section 7.2). Peu coûteux (A tourne en 0,03 s/run).
2. **(Haute) Corriger et re-valider C2 sur de nouvelles graines/scénarios held-out** : forcer les cellules jamais vues (comme B) et détecter les retours indépendamment de la phase du backoff. Le rapport le recommande (`11` §2).
3. **(Haute) Étudier la « loterie de phase » du backoff** : par exemple backoff avec sondes aléatoires ou à échelle logarithmique ; mesurer la latence de retour comme distribution, sur plusieurs dates de retour (pas une seule, τ=230).
4. **(Haute) Nouvelle famille held-out réellement différente** (bruit à queues lourdes, corrélation entre cellules, retards de retour, changement + silence simultanés, flottes > 250 cellules) — le rapport `11` §5 le liste ; c'est ce qui réduirait l'incertitude « famille de scénarios ».
5. **(Moyenne) Élargir les grilles au-delà des bords** (γ > 0,9995 pour B ; ε > 0,2 pour C/D) sur TRAIN/VALIDATION seulement, ou reconnaître que le bord est structurel (l'objectif J tire vers l'uniformité).
6. **(Moyenne) Comparaison à budget de réglage égal** et, idéalement, par une personne autre que l'auteur de B.
7. **(Moyenne) Ajouter un objectif à plusieurs critères / frontière de Pareto** plutôt qu'un J unique, pour rendre le « compromis » explicite.
8. **(Moyenne) Rejouer sur des données de taux de réponse réelles** (le rapport le suggère implicitement : « rejeu local ») pour calibrer P, silence, retours.
9. **(Basse) VW `--epsilon_decay`, caractéristiques qui co-évoluent, détecteurs de dérive River comme déclencheurs de redémarrage** — pistes V1 encore ouvertes.
10. **(Basse) Régénérer `tune_BCC2.log`**, harmoniser la formulation de `01` §9 sur le choix de C, et préciser `07` §2 sur M4 vs M16 (écarts de la section 7.6).

---

## 12. Index des fichiers lus

**Rapports (`reports/003_cell_attention_heldout_v2/`, tous lus intégralement)**
- `00_PRIOR_EVIDENCE_AND_SCOPE.md` — récupération de la V1, carte de provenance (V1 / contrat opérateur pour A / définitions V2), périmètre.
- `01_EXPERIMENTAL_DESIGN.md` — modèle de problème, découpage, politiques, métriques, classifieur de A, objectif J, statistiques, écarts.
- `02_SCENARIO_GENERATOR.md` — structure commune, 10 scénarios held-out, scénarios dev, preuves d'isolation.
- `03_POLICY_IMPLEMENTATIONS.md` — A, B, C/C2, D, R ; paramètres gelés.
- `04_TRAIN_VALIDATION_SELECTION.md` — résultats du réglage.
- `05_HELDOUT_RESULTS.md` — résultats held-out poolés et par scénario, coût.
- `06_PATHOLOGY_TESTS.md` — P1-P8.
- `07_PARAMETER_SENSITIVITY.md` — sensibilité (tables complètes).
- `08_STATISTICAL_ANALYSIS.md` — méthode, comparaisons phares, dominance, annexe des 150 comparaisons.
- `09_ADVERSARIAL_REVIEW.md` — X1-X5, verdicts par politique.
- `10_MAINTENANCE_AND_LICENSE_REFRESH.md` — River/VW/licences/littérature (non vérifié par moi : consultations réseau).
- `11_FINAL_ADJUDICATION.md` — bloc final, classifications, réponse à la V1, validité, reproduction.

**Racine du dépôt**
- `claude.md` — doctrine du laboratoire.
- `.gitignore` — lu (3 motifs : `__pycache__/`, `*.pyc`, `.pytest_cache/`).

**`bench/v2/` — documentation, configuration, environnement, journaux**
- `README.md` — carte du dossier, graines, commande de test.
- `configs/protocol.json` — pré-enregistrement.
- `configs/freeze_manifest.json` — empreintes de gel et amendement.
- `configs/selected_B.json`, `selected_C.json`, `selected_C2.json`, `selected_D.json` — paramètres gelés et grilles J (lus par extraction de champs ; `selected_C2.json` et `selected_D.json` : champs clés uniquement).
- `environment/install_commands.txt`, `python_version.txt`, `requirements.lock.txt`, `uname.txt`.
- `logs/heldout_run.log`, `tune_BCC2.log`, `tune_D.log`, `sensitivity.log`.

**`bench/v2/src/` (code lu en entier)**
- `policies.py` (A, R, garde, B, C/C2, D) · `ledger.py` · `scenario_core.py` · `scenarios_heldout.py` · `scenarios_dev.py` · `scenarios_adv.py` · `runner.py` · `metrics.py` · `tune.py` · `heldout.py` · `analysis.py` · `sensitivity.py` · `sens_summary.py` · `adversarial.py` · `adv_followup.py` · `phase_a.py` · `freeze.py` · `verify_isolation.py` · `determinism.py`.
- `tests/test_semantics.py` — 18 tests (lus et exécutés).

**`bench/v2/results/` (résultats)**
- `heldout/S1…S10.json` (1 200 runs) — lus par script (tous les champs de métriques) ; `heldout/params_lock.json`, `run_summary.json` — lus.
- `heldout_analysis/analysis.json` — lu par script (paires, dominance, poolé) ; `pooled_table.md` — début lu ; `pairwise_table.md`, `dominance_table.md`, `per_scenario_tables.md`, `report_tables.json` — **non lus directement** (contenus reconstitués via `analysis.json` et l'annexe du rapport `08`) ; les médianes/quantiles/pires runs du fichier `per_scenario_tables.md` ne sont donc pas vérifiés (les pires runs ont été recalculés par moi à part).
- `tuning/B_raw.json` (lu partiellement, recalcul de J) ; `C_raw.json`, `C2_raw.json`, `D_raw.json` — non lus directement (utilisation de `selected_*.json` qui contient les J complets) ; `tuning/selection_tables.md` — lu.
- `sensitivity/A.json`, `B.json`, `C.json`, `C2.json`, `D.json` — `B.json` et `C2.json` lus par script (S9) ; les autres non lus directement (agrégats via `sensitivity_summary.json`) ; `sensitivity_summary.json` — lu ; `sensitivity_summary.md` — non lu (équivalent au rapport `07`).
- `adversarial/X1…X5.json` — lus par script (`info_ratio`, `silent_excess`) ; `adversarial_tables.md` — début lu ; `followup_B_backoff.json` — lu.
- `determinism/determinism.json` — lu ; `isolation_report.json` — lu ; `phaseA/phaseA_raw.json` — lu par script (nombre de runs, durée, erreurs seulement).

**Contexte externe à la lane**
- GitHub PR #3 — métadonnées lues via l'API.
- `reports/001_adaptive_strategy_fleet/07_FINAL_ADJUDICATION.md` — lignes 1-70 lues (les autres rapports V1 00-06 et le banc V1 : **non lus**).
