# Analyse approfondie — Lane 009 : Adjudication de réplication des deux études de capacité 008 (PR #9 ouverte)

> Auteur de l'analyse : analyste de recherche (session Claude Code), pour Jean-François.
> Date de l'analyse : 2026-09-29. Dépôt : `aurumshift-external-research-lab` (recherche externe, aucun code privé AurumShift).
> Convention de lecture : ✔ = chiffre du rapport revérifié par moi contre les fichiers bruts ; ✘ = écart constaté ; ? = non vérifiable / non relancé.
> Étiquettes de preuve du dépôt (`claude.md`) : PROVEN, OBSERVED, DOCUMENTED_CLAIM, INFERENCE, UNKNOWN. Je les réutilise et je précise ce qui vient du rapport (« le rapport affirme ») et ce que j'ai moi-même recalculé (« j'ai vérifié »).
> Rappel de méthode : je n'ai modifié ni checkout aucune branche. J'ai lu les branches avec `git show` / `git archive` vers un dossier temporaire (scratchpad), puis recalculé les chiffres avec Python dans ce dossier temporaire. Le seul fichier écrit dans le dépôt est celui-ci.

---

## Petit lexique (pour toi, qui ne connais ni GitHub ni le trading quantitatif)

Je définis ici les mots dont tu auras besoin ; ils sont aussi rappelés à leur première occurrence dans le texte.

| Mot | Sens simple |
|---|---|
| **Branche** (GitHub) | Une « version parallèle » du dossier de travail. `main` est la version de référence ; chaque étude vit sur sa propre branche. |
| **PR (pull request)** | Une demande de fusion : « voici mes modifications, voulez-vous les intégrer à `main` ? ». `PR #9` = la demande n°9. « Ouverte » = pas encore fusionnée ni fermée. « Draft » = brouillon, marquée « pas prête ». |
| **Commit / SHA** | Un commit est un enregistrement daté d'un ensemble de modifications. Son SHA est son empreinte (une suite de caractères, ex. `ccbcdd3`) qui l'identifie de façon unique. |
| **Slot** | Une « place » de position ouverte. Si le système ne peut avoir que 4 positions ouvertes en même temps, il a 4 slots. C'est l'objet de la lane : *à qui donne-t-on les places rares ?* |
| **FIFO** | « Premier arrivé, premier servi » : on donne la place au plus ancien candidat, sans regarder sa qualité. |
| **Score** | Une note prédictive attachée à chaque opportunité de trade (plus elle est haute, plus le gain espéré est grand). |
| **bps (points de base)** | 1 bps = 0,01 %. Une unité de rendement très petite, standard en finance. |
| **Edge** | Le gain espéré d'une opportunité avant coûts. **Net** = edge moins coûts. |
| **Synthétique** | Fabriqué par simulation, pas issu de vrais marchés. Toutes les études de cette lane le sont. |
| **Tuning / validation / held-out** | Trois jeux de données successifs : (1) *tuning* pour régler les paramètres, (2) *validation* pour choisir entre réglages, (3) *held-out* (« mis de côté ») qu'on ne regarde qu'**une fois**, à la fin, pour un verdict honnête. |
| **Pré-enregistrement** | On écrit à l'avance, dans un fichier daté et empreinté, la règle de décision, pour ne pas la ré-ajuster après avoir vu les résultats. |
| **IC 95 % / bootstrap** | Intervalle de confiance : fourchette dans laquelle le vrai effet se trouve « probablement ». Le *bootstrap* le calcule en rééchantillonnant les données des milliers de fois. Si l'IC exclut 0, l'effet est « distinguable de zéro ». |
| **dz** | Unité de l'étude A : gain par slot-heure divisé par une densité de valeur typique du scénario (pour rendre les scénarios comparables). Sans dimension. |
| **Réplication** | Deux études indépendantes retrouvent-elles la même conclusion ? Ici : REPLICATED / PARTIALLY_REPLICATED / CONTRADICTED / NOT_COMPARABLE / NOT_TESTED_IN_ONE_STUDY. |
| **Étude A / Étude B** | A = branche `risk-capacity-turnover-v1` (PR #6 fusionnée en version partielle, puis PR #10). B = branche `festive-archimedes-c3fso6` (PR #8). Ce sont deux implémentations indépendantes de la même mission « 008 ». |

---

## 0. Fiche d'identité

| Champ | Valeur (source) |
|---|---|
| Lane | 009 — Adjudication de réplication des deux études de capacité 008 |
| Branche analysée | `origin/claude/aurumshift-replication-adjudication-jzeujc` |
| PR | **#9** « research(009): capacity Study A/B replication adjudication — CAPACITY_REPLICATION_INCONCLUSIVE », état **open, draft** (liste PR via API GitHub ; créée 2026-09-29T15:56:30Z) |
| Commit unique | `ccbcdd3eda28b59eac55697a6819a297f60ba7f1`, daté 2026-09-29 15:56:19 +0000, message « research(009): capacity Study A/B replication adjudication (read-only, external, synthetic) », parent = `1a449df` (merge de la PR #6 dans `main`) |
| Fichiers | 13 fichiers, +649 lignes, 0 suppression (`git diff --shortstat origin/main...` ✔) : 11 rapports Markdown `00`–`10` (≈ 64,5 Ko, 510 lignes) + `evidence/adjudication_probe.py` (83 lignes) + `evidence/adjudication_probe_output.txt` (56 lignes) |
| Taille du corpus 009 | ≈ 75 Ko (somme des octets de `wc -c`) |
| Objets adjugés | Étude A : `main` `1a449df` (PR #6, version partielle « run 1 ») ; suppl. : branche `claude/risk-capacity-turnover-v1` au commit `cb13041`. Étude B : PR #8 `0ff4f71` (75 fichiers, +49 515 lignes ✔) |
| Verdict final (009) | `FINAL_VERDICT=CAPACITY_REPLICATION_INCONCLUSIVE` (`00_EXECUTIVE_SUMMARY.md`) |
| Force du verdict | **Conditionnelle et explicitement provisoire.** Le rapport dit lui-même que sur la définition stricte de la mission, l'étude A « ne peut rien répliquer au niveau held-out » ; le niveau supplémentaire (validation de A, non fusionnée) pointe vers `CAPACITY_FINDINGS_PARTIALLY_REPLICATED`. Le verdict décrit donc l'**état des preuves à l'instant de l'analyse**, pas l'état du monde synthétique. |
| Autorisations | `CAP_CHANGE_AUTHORIZED=FALSE`, `LOCAL_INTEGRATION_AUTHORIZED=FALSE` |
| Disposition PR #8 | `REQUIRES_CORRECTION_BEFORE_MERGE` |
| **Fait nouveau (postérieur à 009)** | La PR **#10** (branche `claude/risk-capacity-turnover-v1`, tête `ea3fc74`, créée 2026-09-29T16:02:20Z, draft) apporte le held-out de l'étude A (52 200 runs), 14 rapports `reports/008_risk_capacity_turnover/00–13` et un verdict pré-enregistré `CAPACITY_ALLOCATION_REFERENCE_SUPPORTED` (méthode `COMPOSED`). 009 n'a pas pu le lire ; voir **section 13**, que j'ai ajoutée à la demande. |

Ce que j'ai lu : les 11 rapports + les 2 fichiers `evidence/` **intégralement** (branche 009) ; côté sources de vérification, en lecture seule : les deux corpus (A : `main` et branche complète ; B : PR #8) pour recalculer les chiffres, plus `claude.md`.

---

## 1. Mission et question posée

### 1.1 La question, reformulée simplement

Deux sessions d'IA ont, chacune de leur côté, construit un « simulateur » de la situation suivante : *un moteur de recherche/paper-trading a plus d'opportunités de trade qu'il n'a de places (slots) disponibles ; comment choisir celles qui méritent une place ?* Elles ont testé une vingtaine de règles (premier arrivé, tirage au sort, classement par gain net espéré, seuils, apprentissage par bandit, pénalités de corrélation…), et obtenu deux verdicts qui ne portent pas le même nom :

- Étude B (PR #8) : `MULTIPLE_CAPACITY_METHODS_SUPPORTED`.
- Étude A (branche, PR #6 puis #10) : au moment de 009, sans verdict ; depuis, `CAPACITY_ALLOCATION_REFERENCE_SUPPORTED`.

La lane 009 est **un arbitrage** : « Si deux études indépendantes répondent à la même question, leurs réponses concordent-elles ? Là où elles divergent, est-ce un bug, une différence d'hypothèses, ou une vraie contradiction ? Et peut-on en tirer quelque chose pour AurumShift ? » Elle ne produit aucune nouvelle simulation de fond ; elle lit, compare, recalcule quelques contrastes et fait 6 tests d'hypothèses (« sondes ») sur le simulateur de A.

Les dix sous-questions (R1 à R10) sont, en langage simple :

| Q | Question |
|---|---|
| R1 | Le FIFO fait-il moins bien quand les places sont rares ? |
| R2 | Refuser les candidats à gain net estimé ≤ 0 (« écran net ») explique-t-il une part importante du gain ? |
| R3 | Classer par score bat-il le FIFO ? |
| R4 | Classer par gain net par heure de place occupée bat-il le classement par score brut ? |
| R5 | Une méthode plus complexe que le classement simple rapporte-t-elle quelque chose ? |
| R6 | Une pénalité de corrélation améliore-t-elle l'économie nette ? |
| R7 | Les bandits (apprentissage par essai/erreur) justifient-ils leur complexité ? |
| R8 | La qualité du score domine-t-elle la qualité de l'allocateur ? |
| R9 | Classer crée-t-il des effets de famine (certains instruments jamais servis) ou de concentration ? |
| R10 | L'intérêt d'un allocateur diminue-t-il quand les places deviennent abondantes ? |

### 1.2 Contraintes applicables (claude.md)

- Doctrine **REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST** : ici il ne s'agit pas de choisir une bibliothèque, mais l'esprit s'applique — 009 ne propose rien de sur mesure, et ses « hypothèses locales » (rapport 09) sont des idées à *falsifier* plus tard.
- Étiquettes **PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN** : 009 les emploie dans ses en-têtes de section, mais de façon moins systématique que les rapports A/B (les labels du rapport 05 sont des labels de *réplication*, pas des labels de preuve).
- Contraintes AurumShift rappelées par `claude.md` : recherche seule/paper seul, aucun capital réel, « missing evidence is not negative evidence », coûts de marché réalistes, PIT/no-lookahead, faible charge opérateur. **Limite dure** : ne jamais prétendre connaître l'implémentation privée d'AurumShift. 009 respecte cette limite (voir section 10 : je ne l'ai pas trouvé en défaut).
- Contraintes propres à la mission : « lecture seule, ne rien modifier, ne pas fusionner, ne pas commenter la PR #8 » ; les deux corpus intacts (009 l'affirme ; je n'ai rien qui la contredise : aucune trace de modification des chemins de A ou B dans son commit, 13 fichiers tous sous `reports/009…`).

---

## 2. Méthode

### 2.1 Données / sources

Il n'y a **aucune donnée de marché**. 009 travaille sur des fichiers déjà produits :

| Objet | Ce qui est lu |
|---|---|
| Étude A « telle que fusionnée » (niveau *strict*) | `main` `1a449df` : `bench/capacity_v1/py/*.py` (1 712 lignes), `results/{tuning_raw.csv.gz, tuned_params*.json, tuning_table*.csv, validation.json, tune.log}` ; **aucun rapport, aucun held-out, aucun pré-enregistrement** |
| Étude A branche (niveau *supplémentaire*) | commit `cb13041` : code corrigé, `validation_raw.csv.gz`, pré-enregistrement v2, `validation_verdict_dryrun.json` ; held-out « en cours » (le journal ne contenait que des avertissements) |
| Étude B | PR #8 : `src/` (simulateur), `tests/` (77 tests), `configs/{prereg,frozen_params}.json`, `results/{tuning,validation,heldout,diagnostics,analysis}`, rapports `reports/008…/00–14` |

### 2.2 Ce que 009 fait, pas à pas (protocole)

1. **Identité des corpus** (01) : SHA, dates, périmètre, sessions.
2. **Diff d'hypothèses** (02) : 26 dimensions comparées *dans le code* (pas dans les README) avec l'étiquette IDENTICAL / SEMANTICALLY_EQUIVALENT / DIFFERENT / UNKNOWN.
3. **Cartographie des politiques** (03) : 15 lignes, par *sémantique de décision* (pas par nom), grade EQUIVALENT / CLOSE / ANALOGUE / NO_COUNTERPART.
4. **Comparaison de protocole** (04) : séparations tuning/validation/held-out, pré-enregistrement, seeds, tests de fuite.
5. **Matrice de réplication** (05) : 10 questions × 2 colonnes (strict / supplémentaire).
6. **Comparaison numérique** (06) : on **ne poole pas** ; on compare (a) le signe, (b) l'ordre des méthodes, (c) chaque effet comme **part du gain du classement simple sur FIFO** (une grandeur sans unité).
7. **Désaccords** (07) et **contrôle des bugs** (08) : chaque désaccord est testé pour cause « bug » vs « hypothèse » ; deux désaccords le sont par expérience directe sur le simulateur de A (script `adjudication_probe.py`, 20 graines, famille S3, cap 4).
8. **Hypothèses locales** (09) et **disposition de la PR #8** (10).

### 2.3 Splits, pré-enregistrement, gel, graines (côté corpus adjugés)

| | A (fusionné, run 1) | A (branche, run 2) | B (PR #8) |
|---|---|---|---|
| Tuning | graines 1000+, 3 graines × 3 variantes × 12 familles, caps 4 et 6 ; **deux tours** (grilles élargies après avoir vu le tour 1) | idem sur code corrigé | graines 1000–1005 |
| Validation | code et graines 2000+ définis, **aucun résultat de politique** | exécutée (12 familles × 3 variantes × 4 graines × 4 caps) | graines 2000–2007, top-3 du tuning rejoué, meilleur gelé |
| Held-out | défini (graines 9000+), **non exécuté** | non exécuté à l'analyse | graines 3000–3019 (H1) ; H2/H3 3000–3009 ; exécuté **une fois** |
| Pré-enregistrement | **aucun** (le garde-fou de `runner.heldout()` pointe un fichier absent) | v1 puis v2 (v2 écrit après re-tuning et validation) | `prereg.json` avant tout fichier held-out, avec empreinte du code |
| Seuils | — | δ_material 0,10 ; δ_equiv 0,02, « fixés après avoir vu la validation » | δ = 0,25 bps (≈ 10 % du M1 typique du FIFO, INFERENCE), sensibilité 0,1/0,5 |

### 2.4 Critères de décision propres à 009

009 ne fixe pas de seuil numérique unique ; il utilise les étiquettes de réplication (rapport 05) définies ainsi, **sans définition chiffrée écrite** (point faible, voir section 7) :

- REPLICATED : même signe, même ordre de grandeur relatif, les IC des deux études vont dans le même sens.
- PARTIALLY_REPLICATED : signe concordant mais magnitude ou label divergent, ou preuve seulement partielle.
- NOT_TESTED_IN_ONE_STUDY : l'une des deux études n'a pas de résultat sur la question.
- Règle de conduite : « deux niveaux de preuve, jamais mélangés » ; « pas de méta-analyse » ; chaque désaccord doit avoir une **cause taxonomique** parmi : hypothèses de monde, sémantique de score, hypothèses de coûts, ingestion des candidats, définition de capacité, modèle de durée, implémentation d'algorithme, protocole de tuning, protocole statistique, bug.
- Seuils cités dans 009 (repris des deux études, pas propres à 009) : δ_equiv A = 0,02 dz ; δ B = 0,25 bps ; « FIFO_FAIL » A = meilleur dz ≥ 0,10 avec IC bas > 0 ; B = écart > δ avec IC bas > 0.

Une phrase de synthèse de la méthode : *009 est une lecture critique assortie de recalculs sur données brutes ; sa qualité dépend donc surtout de la fidélité de ses lectures de code (que je vérifie en partie, section 6) et de la validité de sa comparaison « par part de gain » (section 7).*

---

## 3. Résultats détaillés, rapport par rapport

Convention : « le rapport affirme » = repris du texte ; « j'ai vérifié » = recalculé par moi sur les fichiers bruts (détails en section 6, registre V1–V24).

### 3.1 Rapport 00 — Synthèse (`00_EXECUTIVE_SUMMARY.md`)

**Constat qui structure tout** (le rapport affirme ; j'ai vérifié les points marqués) :

1. *L'étude A telle que fusionnée dans `main` (PR #6, `1a449df`) n'est pas une étude terminée.* C'est un instantané « travail en cours » : simulateur, 27 politiques, résultats de tuning, contrôles de simulateur, tests de fuite. **Ni résultats de validation par politique, ni pré-enregistrement, ni held-out, ni rapport.** Le message de commit dit lui-même « WIP, held-out not yet run ». ✔ (vérifié : `main` ne contient que `validation.json` = contrôles du simulateur ; pas de `validation_raw`).
2. C'est de plus le « run 1 », que ses auteurs ont déclaré remplacé (commit `7c991af`) à cause d'un biais de démarrage de l'estimateur de covariance (dit *warm-up bias*) et d'un « normaliseur » défectueux : **un seul scénario (S12) fournit 48 % de l'objectif de tuning poolé**. ✔ (j'ai recalculé 0,48).
3. Donc la prémisse de la mission (« deux réplications indépendantes d'un même protocole ») n'est vraie que pour B. A ne peut être comparée qu'en **hypothèses, politiques et protocole**, et en **résultats** seulement faiblement.

**Deux niveaux de preuve, jamais mélangés :**

| Niveau | Source | Statut |
|---|---|---|
| Strict | A exactement comme fusionnée (`1a449df`, run 1, tuning seul) | la définition de la mission |
| Supplémentaire | A run 2, branche non fusionnée (`cb13041`) : code corrigé, validation, dry-run ; held-out illisible | divulgué, non autoritaire, susceptible de changer |

**Réponses R1–R10** (strict / supplémentaire) — reproduites entièrement en section 4 et 8.

**Ce qui se réplique (niveau supplémentaire)** — chiffres du rapport :
- Le classement par valeur nette bat l'ordre d'arrivée : B **+0,365 bps par slot-heure disponible** (≈ 20 % du 1,78 du FIFO) ; A **+0,154 dz**. ✔ (V1, V7)
- Un **écran net seul** capte une part importante mais variable du gain : B **45 %**, A **65 %** dans ses propres mondes, **33 %** quand on donne au simulateur de A les niveaux d'edge/coûts de B. ✔ pour 45 % (0,164/0,365 = 44,9 %) et 65 % (0,100/0,154) ; le 33 % vient d'une sonde sur laquelle je reviens (V13 : `NETPOS` +0,454 / `RANK_NET` +1,393 = 32,6 % ✔).
- Bandits et pénalités de corrélation n'améliorent pas la valeur nette ; les bandits coûtent bien plus de calcul.
- Le meilleur « complexe » ajoute un incrément **petit mais détectable** : B **+0,062** (14 % du gain simple), A **+0,025** (16 %). ✔ (V3, V16)
- Le classement crée un peu de « famine douce » et de concentration ; la famine dure est ≈ 0 (sauf `LIN_TS` de A). ✔ (V17)

**Quatre désaccords matériels**, tous attribués à des hypothèses de monde/coûts, aucun à un bug, deux par expérience directe :
1. **Préemption** (`OLDEST_SLOT` : fermer la plus vieille position pour libérer une place) : B **+0,185**, A **−0,085**. La sonde montre que le moteur de A, alimenté avec l'edge/les coûts de B, redonne un gain (**+0,435**) et bascule à **−1,057** avec des coûts ×3. ✔ (V12 : sortie de sonde rejouée identique).
2. **FIFO vs aléatoire/round-robin** : A les trouve un peu *meilleurs* que FIFO, B tiède ou un peu pires. Sans la décroissance d'edge selon l'âge d'attente, l'effet disparaît (**+0,057 → −0,019**). ✔ (V12)
3. **Spam (S10)** : le spam de A a des scores gonflés et une vraie valeur négative ; celui de B est à cadence élevée mais honnête.
4. **Valeur résiduelle à K = 10** : A garde **0,099 dz** (environ la moitié de K = 3), B ≈ 0.

**Verdicts** : 2 bugs confirmés dans A tel que fusionné (auto-déclarés, non corrigés dans `main`) ; 0 dans B ; capacité non autorisée ; PR #8 `REQUIRES_CORRECTION_BEFORE_MERGE` ; **verdict final `CAPACITY_REPLICATION_INCONCLUSIVE`** avec re-adjudication à prévoir « quand le held-out de A arrivera et que son run 2 sera fusionné ».

### 3.2 Rapport 01 — Identité des corpus (`01_CORPUS_IDENTITY.md`)

Tableaux d'identité (déjà résumés en 2.1 et 2.3). Détails supplémentaires :

- **A fusionné** : 12 familles de scénarios S1–S12 × 3 variantes jitterisées ; 27 politiques + 2 oracles + une borne LP hors-ligne (LP = programmation linéaire ; « borne » = maximum théorique en connaissant l'avenir) ; simulateur horaire, T = 1000, N = 12 instruments en 4 grappes, file d'attente à TTL = 3 (TTL = durée de vie d'un candidat en attente), `cap` slots identiques. Tuning : 108 jobs, **72 configurations**, **15 552 lignes** — ✔ (V19 : 15 552 lignes, 72 politiques, 18 bases).
- **A branche** : 7 commits après la fusion (`3bbc451` validation+pré-enregistrement v1 ; `7c991af` **remplace le run 1** ; `c4d0b86` re-tuning + validation + pré-enregistrement v2 ; `cb13041` « held-out en cours »). Le défaut d'estimateur (`cov = eye(N)*40` a priori) est **toujours dans le code de `main`**. Session d'origine `session_013y25LsVGmzcNzKXFo1FEfW`, « peut-être encore vivante » (009 le signale à juste titre : elle l'était, puisqu'elle a poussé le held-out ensuite).
- **B** : simulateur horaire, W = 600 (+48 de marge), N = 10/12/15 selon le split, TTL = 4 depuis la *dernière* émission, une position par instrument ; 12 politiques implémentables + un oracle ; 4 modes d'ingestion (RAW, DEDUP_LATEST, COOLDOWN, SCORE_UPDATE). Tests : **77 tests, 77 passés en 16 s** (rapport) → j'ai relancé : **77 passed in 17,61 s** ✔ (V20). PR #8 : 75 fichiers, +49 515 ✔ (V21).

### 3.3 Rapport 02 — Diff d'hypothèses (`02_ASSUMPTION_DIFF.md`)

26 lignes ; répartition des étiquettes (comptées par moi sur le tableau du rapport) : IDENTICAL 1 (pas de temps 1 h) ; SEMANTICALLY_EQUIVALENT « pur » 3 (lignes 15, 25, 26 : accrual linéaire, RNG, décalage entre splits) ; étiquettes mixtes 6 (lignes 4, 9, 10, 11, 12, 22 : équivalent sur un aspect, différent sur un autre) ; DIFFERENT « pur » 16. Les lignes **décisives** (le rapport le dit et je suis d'accord) :

| # | Dimension | A | B | Pourquoi ça compte |
|---|---|---|---|---|
| 5 | Charge en candidats | `load` × 4 « équivalents-slot » d'**opportunités distinctes**, chacune avec son edge/durée | `load` × 4 / durée moyenne d'**émissions** brutes, dont beaucoup répètent le même instrument | on ne mesure pas la même « rareté » |
| 6 | Une position par instrument | **non imposé** | imposé | A peut occuper plusieurs slots avec le même instrument |
| 8 | Edge latent | par opportunité, **décroît en exp(−âge/8)** pendant l'attente | AR(1) par instrument-heure, l'état à l'*admission* compte | explique FIFO vs aléatoire (D2) |
| 13 | **Rapport edge/coût** | edge ≈ 10, coût ≈ 8,5 : quasi seuil de rentabilité | edge ≈ 20, coût ≈ 6,5 : confortablement positif | **explique la préemption (D1)** |
| 14 | Durée de détention | par opportunité, estimation bruitée au niveau candidat ; durée moyenne ≈ 15 h | pas d'estimation par candidat, EWMA par instrument ; ≈ 8,7 h | explique R4 et K = 10 |
| 17 | Métrique | latent (bruit exclu) normalisé (dz) | réalisée (bruit inclus), bps bruts | **aucun effet n'est poolable** |
| 20 | Spam | instrument 0, edge vrai −2, **score biaisé de +12** (nuisible) | deux instruments à 20× le débit, edge médian, scores honnêtes (inoffensif) | S10 ne teste pas la même menace |
| 21 | Préemption | `EVICT_SWAP` et `OLDEST_SLOT`, frais forcé +3 bps | `OLDEST_SLOT` seul, sans frais additionnel | signe de D1 |

Conclusion du rapport (juste, à mon avis) : *aucune taille d'effet n'est poolable* ; seuls le signe, l'ordre et les parts de gain sont comparables ; les lignes 9, 15, 25 sont celles où les deux études sont « le même modèle », donc leur accord n'est **pas** une preuve indépendante de robustesse.

### 3.4 Rapport 03 — Cartographie des politiques (`03_POLICY_MAPPING.md`)

15 lignes. Les correspondances exactes :

| Famille | A | B | Grade |
|---|---|---|---|
| FIFO | `FIFO` | `FIFO` (ingestion RAW) | CLOSE |
| FIFO + écran net | `FIFO_NETPOS` | `FIFO_SCREEN` | EQUIVALENT |
| Classement net | `RANK_NET` | `SCORE_RANK` (**malgré son nom, classe le net**) | EQUIVALENT |
| Net par slot-heure | `SLOTHOUR_DENSITY`, `SLOTHOUR_HAZARD` | `SLOTHOUR` | CLOSE (informations de durée différentes) |
| Incertitude | `UNCERTAINTY_LCB` (calibration bayésienne), `COMPOSED` | `UNCERTAINTY_LCB` (rétrécissement vers l'historique de l'instrument) | ANALOGUE |
| Prix d'ombre | `SHADOW_PRICE`, `ONLINE_KNAPSACK_PSI`, `FLUID_QUANTILE`, `TRUNK_RESERVATION` | `SLOTHOUR_SHADOW` | ANALOGUE |
| Corrélation | 4 politiques (`CORR_PENALTY`, `MARGINAL_RISK`, `CLUSTER_CAP`, `CORR_HARD_REJECT`) | `CORR_AWARE` | ANALOGUE |
| Bandit | `LINUCB`, `LIN_TS`, `SLEEPING_HEDGE` | `LINTS` | ANALOGUE |
| Préemption | `OLDEST_SLOT`, `EVICT_SWAP` | `OLDEST_SLOT` | CLOSE |
| Round-robin / quota / aléatoire | idem | idem | EQUIVALENT |
| Classement score brut | `RANK_SCORE_RAW` | — | NO_COUNTERPART |
| Secrétaire (1/e) | `SECRETARY_1_OVER_E` | — | NO_COUNTERPART |

`POLICY_SEMANTICS_COMPARABLE=PARTIAL`. Quatre « pièges de nommage » : (1) B `SCORE_RANK` = A `RANK_NET`, **pas** `RANK_SCORE_RAW` ; (2) B fait tourner FIFO en ingestion RAW et les classeurs en SCORE_UPDATE — 009 a testé que cela ne biaise pas (FIFO ne bouge que de 1,81 à 1,85 selon le mode, écart à `SLOTHOUR` ≈ 0,44–0,48) ✔ (V14 : FIFO 1,814/1,810/1,853/1,845 ; SLOTHOUR 2,259/2,290/2,195/2,280) ; (3) les ensembles « complexes » diffèrent ; (4) « complexe > simple » est mesuré contre `RANK_NET` (A) mais `SLOTHOUR` (B).

### 3.5 Rapport 04 — Comparaison de protocole (`04_PROTOCOL_COMPARISON.md`)

Tableau en 3 colonnes (déjà repris en 2.3), plus les **faiblesses de protocole** listées honnêtement par 009 :

- **A fusionné** : (1) pas une étude ; (2) l'objectif de tuning est corrompu par le normaliseur S12 (48 %) ; (3) les grilles étendues du tour 2 n'ont jamais été validées sur `main` ; (4) toute « amélioration vs FIFO » est *in-sample* pour la méthode tunée (FIFO n'est pas tuné) : direction fiable, taille non.
- **A run 2** : (5) seuils fixés après validation ; pré-enregistrement en v2 après un v1 raté ; (6) peu de graines de validation (4 par variante) : IC serrés parce que les blocs sont peu coûteux, pas parce que les mondes sont divers ; (7) la règle `FIFO_FAIL` prend le meilleur de quatre méthodes par famille : biais haussier reconnu.
- **B** : (8) code d'analyse écrit après H1 (déclaré) ; (9) δ = 0,25 bps permissif : six méthodes dans l'ensemble « T » dont un bandit ; (10) mondes held-out issus du même générateur ; (11) réglé à K = 4 seulement.
- **Les deux** : (12) même famille de générateur, scores calibrés par construction, coûts constants, accrual linéaire → un accord entre deux générateurs bricolés « dans le même esprit » est une preuve plus faible que des données indépendantes.

Points de contrôle notés par 009 et que j'ai regardés : tests de fuite de A (`validation.json` : 27 politiques × 5 cas = **135 runs, 0 échec**, canaris détectés 5/5) ✔ (V22) ; test métamorphique de B (préfixe invariant) avec oracle correctement signalé — non relancé à part la suite de tests (77/77 ✔).

### 3.6 Rapport 05 — Matrice de réplication (`05_REPLICATION_MATRIX.md`)

La table complète (10 questions × strict/supplémentaire) est reproduite au § 8.2 avec mes vérifications. **Décompte du rapport** : strict = 0 REPLICATED, 5 PARTIALLY_REPLICATED, 0 CONTRADICTED, 0 NOT_COMPARABLE, 5 NOT_TESTED_IN_ONE_STUDY ; supplémentaire = 6 REPLICATED (R1, R2, R3, R6, R7, R9), 3 PARTIALLY (R4, R5, R10), 1 NOT_TESTED (R8), 0 CONTRADICTED. ✔ (recompté sur le bloc final : strict = R1, R6, R7, R9, R10 partial = 5 ; R2, R3, R4, R5, R8 not tested = 5 ; supplémentaire = 6 + 3 + 1 = 10 ✔).

Phrase clé : *« Aucune question de tête n'est CONTRADICTED. Les désaccords sont dans les résultats secondaires (préemption, aléatoire vs FIFO, spam, résiduel K = 10) et dans les labels que chaque étude colle sur R5. »*

### 3.7 Rapport 06 — Comparaison numérique (`06_NUMERIC_COMPARISON.md`)

**Table maîtresse** (chiffres du rapport ; ✔ = retrouvés à l'identique par ma relance de la sonde et/ou par recalcul indépendant) :

| Contraste | B : bps / slot-heure dispo [IC 95 %], victoires | A run 2 (validation) : dz [IC 95 %] | Signe identique ? | Part du gain simple (B / A) | Vérif. |
|---|---|---|---|---|---|
| Écran net − FIFO | +0,164 [0,128 ; 0,200], 11/13 | +0,100 [0,091 ; 0,109] | oui | 45 % / 65 % | ✔ V1, V7 |
| Classement net − FIFO | +0,365 [0,318 ; 0,411], 12/13 | +0,154 [0,140 ; 0,168] | oui | 100 % | ✔ |
| Classement net − écran net | +0,201 [0,157 ; 0,245], 12/13 | +0,054 [0,045 ; 0,064] | oui | 55 % / 35 % | ✔ |
| Score brut − FIFO | non testé | +0,134 [0,120 ; 0,148] | — | — | ✔ |
| Net − score brut | non testé | +0,020 [0,018 ; 0,023] | — | — | ✔ |
| Slot-heure − classement net | +0,070 [0,033 ; 0,110], 11/13 | +0,001 [0,000 ; 0,003] | ≥ 0 des deux côtés | 19 % / 1 % | ✔ |
| Meilleur complexe − simple | +0,062 [0,022 ; 0,098], 10/13 | +0,025 [0,017 ; 0,034] | oui | **14 % / 16 %** | ✔ |
| `UNCERTAINTY_LCB` − simple | +0,062 (vs `SLOTHOUR`) | +0,010 [0,005 ; 0,017] (vs `RANK_NET`) | oui | 14 % / 6 % | ✔ |
| Prix d'ombre − simple | +0,009 [−0,026 ; 0,043] | `SHADOW_PRICE` +0,020, `KNAPSACK` +0,017 | faible, même signe | 2 % / 13 % | A : `SHADOW_PRICE` +0,020 [0,014 ; 0,025] ✔ ; `KNAPSACK` ? |
| Pénalité de corrélation − simple | −0,022 [−0,052 ; 0,010] | `CORR_PENALTY` 0,000 ; `MARGINAL_RISK` +0,004 | ≈ 0 | ≈ 0 | ✔ |
| Bandit − simple | −0,020 [−0,058 ; 0,019] | `LIN_TS` −0,013 [−0,021 ; −0,004] ; `LINUCB` −0,029 | ≤ 0 | −5 % / −8 % à −19 % | ✔ |
| Aléatoire − FIFO | −0,042 (rapport B [−0,087 ; 0,001] ; re-bootstrap 009 [−0,072 ; −0,012]) | +0,024 [0,016 ; 0,032] | **non** | −12 % / +16 % | ✔ (V8) |
| Round-robin − FIFO | −0,006 [−0,050 ; 0,035] | +0,030 [0,023 ; 0,037] | **non** (minime) | −2 % / +19 % | ✔ |
| Quota égal − FIFO | −0,041 [−0,082 ; 0,002] | +0,031 [0,024 ; 0,038] | **non** (minime) | −11 % / +20 % | ✔ |
| Préemption − FIFO | +0,185 [0,149 ; 0,221], 10/13 | −0,085 [−0,101 ; −0,071] | **non** | n/a | ✔ |

Deux nuances de vérification à retenir : (i) le rapport donne pour B « `OLDEST_SLOT` − FIFO +0,185 [0,149 ; 0,221] » = IC de la sonde 009 ; **le fichier de B lui-même (`H1_paired_macro.csv`) donne [0,140 ; 0,229]** : deux bootstraps différents, même point ; (ii) pour `EQUAL_QUOTA − FIFO`, l'IC de B [−0,082 ; 0,002] inclut 0 mais le re-bootstrap de 009 [−0,076 ; −0,007] l'exclut : 009 signale cette différence pour l'aléatoire mais pas pour le quota. Conclusion : « tiède ou un peu pire » est le bon résumé de B, mais « statistiquement indistinguable » (formule de B) est **fragile** selon le bootstrap.

**Dépendance à la capacité K** (synthétique, sensibilité seulement) :

| K | B : classement − FIFO (`SLOTHOUR`, macro, 10 graines) | A run 2 : `RANK_NET` − FIFO (dz) | A `FIFO_NETPOS` − FIFO | A : part de slots occupés par FIFO | B : FIFO « tous slots pleins » |
|---|---|---|---|---|---|
| 3 | +0,679 [0,607 ; 0,756] | +0,192 | +0,117 | 0,90 | 0,84 |
| 4 | +0,476 [0,413 ; 0,539] | +0,176 | +0,109 | 0,88 | 0,78 |
| 6 | +0,156 [0,102 ; 0,211] | +0,148 | +0,097 | 0,85 | 0,65 |
| 10 | **−0,041** [−0,059 ; −0,024] | **+0,099** [0,089 ; 0,110] | +0,076 | 0,77 | 0,12 (occupation 0,61) |

✔ toutes ces valeurs (V9, V10, V11) ; K = 10 / K = 3 : B ≈ −6 %, A ≈ +52 %. Explication du rapport : les familles « rares » de A (S3 à charge 4×, S5, S6, S7 à 3×) restent sur-souscrites à K = 10, alors que la charge absolue fixe de B laisse la plupart des slots libres.

**Dépendance au scénario** (rapport) : scénarios d'échec du FIFO côté B (δ = 0,25) S12, S3, S4, S5, S5b, S7, S8, S9 ; équivalents S1, S2, S6, S10, S11. Côté A run 2 : échec S10, S11, S12, S2, S3, S4, S5, S7, S8, S9 ; équivalent S1 ; S6 ni l'un ni l'autre. Recouvrement : 7 des 10 échecs de A sont aussi des échecs de B (S12, S3, S4, S5, S7, S8, S9). Différences : S2, S10, S11 (A échoue, B équivalent).

**Part de l'écran net selon le monde** : 72 % (S3 par défaut de A) ; 33 % (A avec edge/coûts de B) ; 45 % (B). Elle baisse quand le rapport edge/coût monte, ce qui prédit — dit le rapport — la moindre valeur de l'écran dans B. (INFERENCE, cohérente avec les trois points.)

**Étude A telle que fusionnée (strict)** : méthode tunée − FIFO, split de tuning, unités `dens0_sd`, K ∈ {4,6} poolés : `COMPOSED` +0,243 ; `UNCERTAINTY_LCB` +0,239 ; `SHADOW_PRICE` +0,232 ; `MARGINAL_RISK` +0,225 ; `SLOTHOUR_DENSITY` +0,220 ; `CORR_PENALTY` +0,216 ; `LIN_TS` +0,174 ; `LINUCB` +0,176 ; `ONLINE_KNAPSACK_PSI` +0,172 ; `OLDEST_SLOT` −0,116. ✔ **Tous vérifiés** sur `tuning_raw.csv.gz` (V5) ; par famille, `SLOTHOUR_DENSITY` − FIFO : S12 = +1,268 contre 0,011–0,285 ailleurs ✔ ; en retirant S12, la moyenne passe de 0,22 à 0,125 (« ≈ 0,12 » du rapport ✔).

**Pourquoi les labels de R5 diffèrent** (rapport ; arithmétique que j'ai recalculée) : FIFO ≈ 0,089 et `RANK_NET` ≈ 0,242 en A run 2 (gain 0,154) ✔. δ_equiv de A = 0,02 = 13 % de ce gain ; δ de B = 0,25 bps = 57 % du gain de `SLOTHOUR` (0,435) et 14 % du 1,78 du FIFO. Un incrément complexe de 14–16 % du gain simple est donc « matériel » sous la marge de A et « dans l'égalité » sous celle de B, **sans désaccord sur l'effet sous-jacent**. ✔ arithmétique : 0,02/0,154 = 13,0 % ; 0,25/0,435 = 57,5 %.

### 3.8 Rapport 07 — Désaccords (`07_DISAGREEMENTS.md`)

**D1 Préemption.** Cause : niveaux de coût et d'edge (hypothèses de monde et de coût). Non testé comme bug. **Testé sur le simulateur de A** :

| Réglage du simulateur de A | FIFO | `OLDEST_SLOT`(4 h) − FIFO | (12 h) − FIFO |
|---|---|---|---|
| A par défaut (edge ≈ 10, coût ≈ 8,5, frais d'éviction +3 bps) | −0,06 | **−1,404** | −0,254 |
| Edge de type B (moyenne 22), coût 3–7, durée de base 7 h, sans frais d'éviction, sans décroissance d'attente | 2,22 | **+0,435** | +0,231 |
| idem, coût ×3 | 0,85 | **−1,057** | +0,004 |

✔ **Rejoué par moi à l'identique, bit à bit** (V12). Corroboré par le diagnostic D3 de B (moyennes de S3 et S6, croyance de coût « connue », coûts ×1/×2/×3) : `OLDEST_SLOT` 3,00 → 1,51 → 0,02 contre FIFO 2,47 → 1,74 → 1,00 ✔ (V15 : ce sont bien les **moyennes de S3 et S6** — 009 ne le dit pas ; par scénario le retournement arrive plus tôt en S3 : `OLDEST_SLOT` − FIFO = +0,27 / −0,56 / −1,39 à coût ×1/×2/×3).

**D2 FIFO vs aléatoire/RR/quota.** Cause : décroissance d'edge avec l'attente dans A. Test : `RANDOM − FIFO` = **+0,057 ± 0,026** par défaut (tau = 8) ; **−0,019 ± 0,027** sans décroissance ; −0,020 avec économie de type B. ✔ (V12).

**D3 Spam (S10).** Cause : sémantique de score/menace. Lu dans le code, non exécuté. A : le spam attire les classeurs et perd de l'argent ; le meilleur gain de A sur FIFO est +0,391 dz, +0,282 sur `FIFO_NETPOS`. B : menace inoffensive ; sa batterie de « score gaming » est réservée à la validation et « non atténuée par aucune politique » (limitation 15 de B ✔ confirmé dans `14_LIMITATIONS.md`).

**D4 Résiduel K = 10.** Cause : définition de charge et de durée. Utilisation de FIFO : 77 % (A) contre 61 % (B) ✔ (V10).

**D5 Slot-heure vs net (R4).** Cause : modèle de durée + design des scénarios. A donne une estimation de durée *au niveau candidat* (`dur_hat`), B seulement une EWMA par instrument. Le gain de B se concentre en S6 (+0,358) et S3 (+0,189) ; les variantes S6 de A ont des ratios de densité rapide/lent 0,8–3,0 (validation 1,25/2,0/0,8 ; held-out 1,8/0,9/3,0), « beaucoup plus doux ». Hors S6, le gain macro de B est **+0,046** ✔ (V16, j'ai recalculé 0,046). **Ceci est remis en cause par le held-out de A (section 13.3).**

**D6 Labels de verdict.** Cause : marges d'équivalence pratique (arithmétique ci-dessus).

**D7 Différences secondaires.** Meilleurs différents (`UNCERTAINTY_LCB` chez B, `COMPOSED`/prix d'ombre chez A) — écarts petits, donc attendus ; paramètres tunés divergents (B : θ = 0,25, ω = 0,6, κ = 0, α = 0,1 ; A run 1 : k = 0,5, κ = 25, η = 0,1, min_hold 12) ; oracle non comparable (B 5,7 vs 2,3 ; A 0,25 vs 0,18 dz).

**Tableau d'attribution** (rapport) : D1 cause coût+monde, pas de bug, niveau de preuve « expérience sur le moteur de A + D3 de B » ; D2 monde (décroissance), expérience ; D3 sémantique de score, source ; D4 charge+durée, source+utilisation ; D5 modèle de durée+design, source+tableau B ; D6 protocole statistique, arithmétique.

### 3.9 Rapport 08 — Contrôle des bugs et conclusion capacité (`08_BUG_CHECK.md`)

**Partie 1** — pour chaque désaccord, un candidat-bug est examiné : comptabilité d'éviction (A `close(...,"evict")` inscrit `edge·k/d + marché − coût − 3` ; B tronque à `gross(i, t_in, hh) − coût` ; cohérents), tri FIFO (`(-âge, cid)` vs `(t_first, inst)`), etc. Verdict : **aucun bug**.

**Partie 2 — défauts trouvés :**

| # | Défaut | Statut selon 009 | Ma vérification |
|---|---|---|---|
| 1 | Biais de démarrage de l'estimateur de covariance (`cov = eye(N)*40`) dans A/`main` | CONFIRMÉ (auto-déclaré) | code présent dans `main` : ✔ (non modifié dans `main` ; corrigé sur la branche) |
| 2 | Normaliseur qui explose (S12 = 48 % de l'objectif) | CONFIRMÉ indépendamment | ✔ recalculé : S12 = 0,48 |
| 3 | Garde-fou held-out pointant vers un fichier de pré-enregistrement absent de `main` | Mineur | ✔ (fichier absent de `main`, présent sur la branche) |
| 4 | Contrôle Erlang-B biaisé (`sim_block < erlang_b` de 0,002 à 0,020 sur 9 lignes) | Mineur, OBSERVED | ✔ (V22 : 9/9 lignes, min 0,0023, max 0,0197) |
| 6 | Avertissements NaN inexpliqués `policies.py:190` (branche A) | NON CONFIRMÉ | **mis à jour par le held-out**, section 13.6 |
| 7 | B : aucun défaut de code | 77/77 tests ✔, hash des paramètres gelés ✔ | ✔ (V20, V23) |
| 8 | B : sur-généralisation dans le texte (« l'inversion renverse le gain ») | Documentation | ✔ partiellement ; voir V18 (nuance ✘ sur le 47 %) |
| 9 | B : `MULTIPLE_CAPACITY_METHODS_SUPPORTED` vient de |T|=6 sous δ permissif | Cadrage | ✔ (B le dit lui-même dans son § Interprétation) |
| 10 | Nom trompeur `SCORE_RANK` | Cadrage | ✔ (`val = sc − cost_est` dans le code de B) |

**Partie 3 — conclusion capacité** (mission §8) : *ni l'une ni l'autre* des études ne peut autoriser de changer `max_open_positions`, de déployer un allocateur, de changer le comportement PAPER ; et les résultats à K = 3/4/6/10 ne sont que de la sensibilité (charge fixée en absolu, paramètres réglés à K = 4 (B) ou 4/6 (A), désaccord entre les deux études à K = 10 = preuve de dépendance au générateur).

### 3.10 Rapport 09 — Hypothèses locales (`09_LOCAL_HYPOTHESES.md`)

Cinq hypothèses « à falsifier localement » ; aucune n'autorise un test.

| Hyp. | Contenu | Statut selon 009 | Effet attendu si ça se transfère |
|---|---|---|---|
| **H1′** | Le classement par valeur nette bat l'ordre d'arrivée quand la demande dépasse la capacité | Répliquée | 20 % de la valeur du FIFO (B) ; 2,7× la valeur normalisée du FIFO (A) ✔ (0,242/0,089 = 2,72) |
| **H2** | Un écran « score − coût > 0 » capte une part matérielle | Répliquée | 45 % (B), 65 % (A) ; 33 %–72 % dans les mondes de A |
| **H5** | Bandits et pénalités de corrélation inutiles faute de preuve locale | Répliquée | bandits −0,020 (B) / −0,013 à −0,029 (A), calcul ×24 ; corrélation ≈ 0 |
| **H3′** | Net (éventuellement / durée) suffit comme référence simple | Partielle | +0,07 (B, tiré par S6) vs ≈ 0 (A) |
| **H4** | Le rétrécissement d'incertitude aide quand les scores répétés sont bruités | Partielle | B +0,062 ; A +0,010 (rétrécissement), +0,025 (composite) |
| **H6** (nouvelle) | La préemption n'est bénéfique que si l'edge net par trade est grand par rapport au coût | Conditionnelle | le signe bascule pour un facteur ≈ 3 |

Chaque hypothèse est formulée avec un critère de falsification (« falsifiée si… ») et les données locales nécessaires (journal des candidats avec score à l'instant de décision, estimation de coût, résultat ; histogramme des durées réalisées ; historique de scores répétés). Sont explicitement **non proposés** : toute valeur de capacité, tout déploiement, tout test de plafond ; prix d'ombre, knapsack, LinTS/LinUCB, experts endormis, solveurs ILP ; les garde-fous de famine comme allocateurs (coût ≈ 0,12–0,13 dz chez A, 0,4–0,5 bps chez B).

**Pré-requis locaux communs** : calibration des scores et sa dérive ; l'ordre d'arrivée porte-t-il de l'information ? ; coût réel par admission et par fermeture forcée ; distribution des durées et lien avec l'edge ; harnais de rejeu apparié sans anticipation.

### 3.11 Rapport 10 — Disposition de la PR #8 (`10_PR8_DISPOSITION.md`)

Décision : `REQUIRES_CORRECTION_BEFORE_MERGE`. Pourquoi pas les trois autres :

| Option | Verdict de 009 | Raison |
|---|---|---|
| `SUPERSEDED_BY_PR6` | Non | la PR #6 est un instantané WIP d'un run retiré : ne peut pas supplanter une étude complète pré-enregistrée |
| `KEEP_DRAFT_AS_RESEARCH_ARCHIVE` | Non | l'archiver jetterait la seule preuve held-out complète du dépôt |
| `MERGE_AS_INDEPENDENT_REPLICATION` | Pas encore | fusionner mettrait deux implémentations homonymes sous `bench/capacity_v1/` sans indiquer laquelle est retirée, et publierait deux affirmations non pleinement soutenues |

Quatre corrections (texte/provenance seulement, aucune sur résultats/code) : (1) corriger l'affirmation « l'inversion renverse le gain » ; (2) qualifier le label `MULTIPLE_…` ; (3) ajouter une section de provenance dans `bench/capacity_v1/README.md` ; (4) réparer l'état de la PR (la passer en draft ou enregistrer la décision) et revérifier les conflits quand la branche de A arrivera, car les deux écrivent sous `bench/capacity_v1/results/`. *(Le point (4) est devenu concret, section 13.7.)*

### 3.12 Fichiers `evidence/`

- `adjudication_probe.py` (83 lignes) : quatre blocs — [1] contrastes A run 2 (validation) avec bootstrap par blocs (famille, variante, graine) ; [2] contrôle du normaliseur sur `main` ; [3] contrastes B (H1) et test de confusion d'ingestion (H2) ; [4] sondes sur le simulateur de A avec hypothèses modifiées (20 graines × cap 4 × famille S3).
- `adjudication_probe_output.txt` (56 lignes) : sortie correspondante.

**Résultat de ma relance** (extraction des corpus dans un dossier temporaire, `numpy 2.4.6`, `pandas 3.0.6`, 18 s) : `diff` de la sortie relancée contre la sortie livrée = **vide** — sortie reproduite à l'identique, bit à bit (V12). 

---

## 4. Candidats / méthodes évalués un par un

009 n'attribue pas ADOPT/ADAPT/PARK/REJECT (il n'est pas une étude de bibliothèques). Il classe des **familles de méthodes** par leur statut de réplication et propose des **hypothèses locales à falsifier**. Je traduis dans le vocabulaire de `claude.md` pour t'aider à lire, en marquant clairement que la traduction est **la mienne** (INFERENCE) et qu'elle ne vaut **jamais** adoption : « à tester localement » ne signifie pas « compatible avec AurumShift » (UNKNOWN).

### 4.1 Les méthodes d'allocation (dans 009)

| Famille (noms A / B) | Statut 009 | Traduction (mienne) | Justification chiffrée (009, ✔ = vérifié) | Ce qui ferait changer le verdict |
|---|---|---|---|---|
| **FIFO** | Référence faible, échoue quand la demande dépasse la capacité | référence de comparaison, pas candidat | B : ranking > FIFO de +0,365 (12/13) ; A : +0,154 dz ✔ | Si l'ordre d'arrivée porte de l'information locale (B, limitation 2) |
| **Écran net** (`FIFO_NETPOS` / `FIFO_SCREEN`) | H2 répliquée | **ADAPT-candidat de contrôle** (à tester en premier, coût nul) | B +0,164 = 45 % ; A +0,100 = 65 % ✔ | Coût local impossible à estimer → l'écran perd son sens (UNKNOWN_COST ≠ 0) |
| **Classement net** (`SCORE_RANK` / `RANK_NET`) | H1′ répliquée, « référence » | **référence à tester** | B +0,365 [0,318 ; 0,411] ; A +0,154 [0,140 ; 0,168] ✔ | Scores mal calibrés : l'avantage fond de ≈ 45–70 % (B D2) et s'inverse à pente négative (A) |
| **Net / durée espérée** (`SLOTHOUR*`) | H3′ partielle | **conditionnel** | B +0,070 (dominé par S6 +0,358 et S3 +0,189) ; A +0,001 ✔ | Forte hétérogénéité locale des durées → utile ; sinon ≈ classement net |
| **Rétrécissement / pooling** (`UNCERTAINTY_LCB`) | H4 partielle | **secondaire** | B +0,062 (10/13) ; A +0,010 ✔ | Si les émissions se répètent par instrument et sont bruitées (S8 +0,26, S12 +0,14 en B) |
| **Composite** (`COMPOSED`, A seul) | non testé en B | **PARK pour 009** (effet +0,025 dz, 16 % du gain simple) | ✔ +0,025 [0,017 ; 0,034] | Dépend de la marge d'équivalence choisie (13 % vs 57 % du gain) |
| **Prix d'ombre / knapsack / fluide / trunk** | « aucun bénéfice répliqué » | **PARK** | B : +0,009 [−0,026 ; 0,043] ; A : +0,020 (`SHADOW_PRICE`) ✔ | Si le held-out de A confirme un gain > marge (c'est le cas, section 13) |
| **Corrélation** (`CORR_*`, `MARGINAL_RISK`, `CLUSTER_CAP`) | H5 répliquée (« pas de gain de valeur ») | **PARK côté rendement ; question ouverte côté risque** | B −0,022 [−0,052 ; 0,010], drawdown −7 %/−8 % ; A `CORR_PENALTY` 0,000, `MARGINAL_RISK` +0,004 ✔ | Un drawdown local attribuable à des admissions simultanées corrélées |
| **Bandits** (`LINUCB`, `LIN_TS`, `SLEEPING_HEDGE` / `LINTS`) | H5 répliquée | **REJECT-pour-l'instant** | B −0,020 [−0,058 ; 0,019], ≈ 24× le calcul ; A −0,013 à −0,029 ✔ | Score inversé ou non calibré (voir 13.5) |
| **Préemption** (`OLDEST_SLOT`, `EVICT_SWAP`) | H6 conditionnelle | **diagnostic seulement** | B +0,185 ; A −0,085 ✔ ; bascule avec coût ×3 ✔ | Mesure locale du rapport edge/coût et du coût d'une fermeture forcée |
| **Round-robin / quota / aléatoire** | monitoring seulement | **pas des allocateurs** ; indicateurs de famine | coûtent ≈ 0,12–0,13 dz (A) / 0,4–0,5 bps (B) vs le classement | — |
| **Secrétaire 1/e** (A seul) | non proposé | **REJECT** | dans le held-out de A : +0,014 dz vs FIFO, famine 0,9 instruments (section 13) | — |
| **Oracles** | non implémentables | jamais dans un verdict | A : bornes non comparables ; B : oracle glouton avec bruit réalisé | — |

### 4.2 Les hypothèses locales (rapport 09)

| Hyp. | Ce qui la rend intéressante | Falsifiée localement si… | Nécessite | Ma remarque |
|---|---|---|---|---|
| H1′ | seule hypothèse à effet net répliqué dans les deux études | sur une période où candidats ≥ slots libres, le top-k estimé-net n'a pas un net réalisé supérieur au top-k par ordre d'arrivée (IC apparié incluant 0) | journal des candidats horodaté + estimation du coût + issue | la falsification suppose qu'on sache mesurer un « contre-factuel sûr » (UNKNOWN) |
| H2 | coût quasi nul | les rejetés n'ont pas un net réalisé plus faible que les admis, ou l'estimation de coût est trop mauvaise pour définir un signe | estimation locale de coût défendable | l'écran est aussi ce qu'une politique FIFO sensée ferait déjà (A : 61 % du gain, section 13) |
| H5 | évite la complexité | un drawdown concentré attribuable à des admissions simultanées corrélées qu'une pénalité de groupe supprime sans baisser le net | définitions locales de groupes + co-mouvements réalisés | **à reformuler** après le held-out de A (13.5) |
| H3′ | référence simple | dispersion des durées faible devant celle des valeurs (alors la normalisation est du bruit) | distribution des durées réalisées par instrument | l'explication de l'écart A/B (D5) est fragilisée (13.3) |
| H4 | gain de qualité si scores répétés bruités | les émissions répétées ne sont pas plus bruitées que la dispersion inter-candidats | historique de scores répétés | — |
| H6 | signe dépendant du rapport edge/coût | rapport mesuré sous le point de bascule ou coût de fermeture forcée ≠ coût d'entrée | mesures de coûts et d'edge | prudence : une règle de sortie n'est pas un allocateur et peut changer le comportement réalisé |

### 4.3 Les options de disposition de la PR #8

Tableau en 3.11. **Conditions de changement de verdict** (les miennes, INFERENCE) : `REQUIRES_CORRECTION_BEFORE_MERGE` deviendrait `MERGE_AS_INDEPENDENT_REPLICATION` une fois les quatre corrections faites ; il deviendrait un choix d'arbitrage **humain** entre A et B si la même arborescence `reports/008_risk_capacity_turnover/` reçoit deux jeux de fichiers (section 13.7).

---

## 5. Bloc final (reproduit tel quel) et explication ligne par ligne

```
STUDY_A_SHA=1a449df5239753e39d657fdf14813a8f1995a985 (main, merge of PR #6; content commits 1d676ff, 588dc4b, da2f7c4)  [supplementary: branch tip cb130415d0e4211a5379fb29be5cac3a2749859e]
STUDY_B_SHA=0ff4f71efe7fd2a3e3014407553f0c3665617d2f (PR #8 head; prereg ad2adda, heldout c64cbb4)

ASSUMPTIONS_IDENTICAL=FALSE
POLICY_SEMANTICS_COMPARABLE=PARTIAL (8 of 10 families map with caveats; see 03)

R1_FIFO_SCARCITY=PARTIALLY_REPLICATED   (supplementary: REPLICATED)
R2_NET_SCREEN=NOT_TESTED_IN_ONE_STUDY   (supplementary: REPLICATED)
R3_SCORE_RANKING=NOT_TESTED_IN_ONE_STUDY   (supplementary: REPLICATED)
R4_SLOT_HOUR=NOT_TESTED_IN_ONE_STUDY   (supplementary: PARTIALLY_REPLICATED)
R5_COMPLEXITY=NOT_TESTED_IN_ONE_STUDY   (supplementary: PARTIALLY_REPLICATED)
R6_CORRELATION=PARTIALLY_REPLICATED   (supplementary: REPLICATED)
R7_BANDITS=PARTIALLY_REPLICATED   (supplementary: REPLICATED)
R8_SCORE_QUALITY=NOT_TESTED_IN_ONE_STUDY   (supplementary: NOT_TESTED_IN_ONE_STUDY)
R9_STARVATION=PARTIALLY_REPLICATED   (supplementary: REPLICATED)
R10_CAPACITY_SCARCITY=PARTIALLY_REPLICATED   (supplementary: PARTIALLY_REPLICATED)

MATERIAL_CONTRADICTIONS=4 (preemption sign; FIFO-vs-random sign; spam response; K=10 residual value), all attributed to assumptions
IMPLEMENTATION_BUGS_FOUND=2 confirmed in Study A as merged (run-1 estimator warm-up bias; run-1 normaliser blow-up); 0 in Study B

REPLICATED_LOCAL_HYPOTHESES=H1' (net-value ranking beats arrival order when demand exceeds capacity), H2 (net-edge screen), H5 (bandit/correlation machinery unnecessary without local evidence)
  partially: H3' (hold-normalised ranking as reference), H4 (uncertainty pooling); conditional: H6 (preemption sign depends on cost/edge)

CAP_CHANGE_AUTHORIZED=FALSE
LOCAL_INTEGRATION_AUTHORIZED=FALSE

PR8_DISPOSITION=REQUIRES_CORRECTION_BEFORE_MERGE

FINAL_VERDICT=CAPACITY_REPLICATION_INCONCLUSIVE
```

(Le rapport reproduit ce bloc à la fin de `00_EXECUTIVE_SUMMARY.md`. Je l'ai recopié caractère pour caractère ; les valeurs correspondent à celles du corps du texte de 009, sauf ce que je signale en section 7.)

### Explication clé par clé

| Clé | Ce que ça veut dire | Remarque |
|---|---|---|
| `STUDY_A_SHA` | Empreinte du code de l'étude A adjugée. Le niveau *strict* est `main` après la PR #6 (`1a449df`, résultat de trois commits de contenu `1d676ff`, `588dc4b`, `da2f7c4`) ; le niveau *supplémentaire* est la pointe de la branche `cb130415…` | Depuis 009, la branche a avancé jusqu'à `ea3fc74` (PR #10). Le SHA de 009 est donc **périmé** pour A (section 13). |
| `STUDY_B_SHA` | Tête de la PR #8 `0ff4f71…` ; pré-enregistrement au commit `ad2adda`, held-out au commit `c64cbb4` | Toujours la tête de la PR #8 à l'heure de mon analyse ✔. |
| `ASSUMPTIONS_IDENTICAL=FALSE` | Les deux simulateurs ne modélisent pas le même monde (26 dimensions, 16 « différentes » purement, cf. 3.3) | Point de départ de « rien n'est poolable ». |
| `POLICY_SEMANTICS_COMPARABLE=PARTIAL` | 8 familles sur 10 demandées ont un pendant, dont 3 seulement « équivalentes » | Explique la prudence sur R4–R7. |
| `R1_FIFO_SCARCITY` … `R10_CAPACITY_SCARCITY` | Statut de réplication de chaque question. La valeur *sans* parenthèse est le niveau strict (A tel que fusionné), la parenthèse le niveau supplémentaire | Les « NOT_TESTED_IN_ONE_STUDY » au niveau strict viennent de ce que l'étude A fusionnée ne contient pas les politiques concernées (`RANK_NET`, `FIFO_NETPOS`, `RANK_SCORE_RAW`…) dans sa sortie de tuning. |
| `MATERIAL_CONTRADICTIONS=4` | Quatre désaccords de signe/réponse jugés « matériels » (préemption, aléatoire vs FIFO, spam, résiduel à K = 10), tous imputés à des hypothèses | Voir 3.8. |
| `IMPLEMENTATION_BUGS_FOUND=2 … 0` | Deux défauts d'implémentation dans A/`main` (estimateur, normaliseur), auto-déclarés ; zéro dans B | Ces deux défauts sont corrigés dans le run 2 (branche/PR #10), pas dans `main`. |
| `REPLICATED_LOCAL_HYPOTHESES=H1′, H2, H5` (+ partielles H3′, H4 ; conditionnelle H6) | Les hypothèses à tester un jour sur des données AurumShift, classées par degré de réplication | La clé ne dit pas « à faire », seulement « à juger plus tard ». |
| `CAP_CHANGE_AUTHORIZED=FALSE` | Rien ici n'autorise à changer le nombre max de positions ouvertes | Cohérent avec `claude.md`. |
| `LOCAL_INTEGRATION_AUTHORIZED=FALSE` | Rien n'autorise à intégrer quoi que ce soit dans AurumShift | Idem. |
| `PR8_DISPOSITION=REQUIRES_CORRECTION_BEFORE_MERGE` | La PR #8 est saine mais doit recevoir 4 corrections de texte/provenance avant fusion | À revisiter (13.7). |
| `FINAL_VERDICT=CAPACITY_REPLICATION_INCONCLUSIVE` | Sur la définition stricte, A ne peut rien répliquer au niveau held-out ; les preuves disponibles sont insuffisantes pour trancher | Le corps du texte ajoute que le niveau supplémentaire pointe vers `CAPACITY_FINDINGS_PARTIALLY_REPLICATED`, mais ce second verdict n'est **pas** dans le bloc. |

---

## 6. Contrôles de validité

### 6.1 Ce que 009 a fait pour se contrôler lui-même

- **Deux niveaux de preuve** : évite de faire dire au niveau supplémentaire (non fusionné, validation) ce qu'il ne peut pas dire.
- **Rien n'est poolé** : évite l'erreur classique (mélanger des unités).
- **Sondes causales** (2 sur 4 désaccords) : au lieu de proposer une explication, il la teste en modifiant le simulateur de A.
- **Bootstrap de vérification** (B) : re-dérive tous les contrastes de B depuis les CSV bruts et signale une différence d'IC (aléatoire − FIFO).
- **Tests de fuite / anticipation** : 009 *lit* ceux de A (135 runs, 0 échec, canaris détectés 5/5) et de B (métamorphique) ; il **relance** la suite de tests de B (77/77) mais **pas** la suite de fuite de A (déclaré dans 08 « Not verified »).
- **Déterminisme** : 009 relance rien de tel à part la reproduction ; il rapporte « 300 ré-exécutions de cellules held-out, 0 divergence » de B sans le vérifier (déclaré).
- **Contrôle négatif / positif** : la sonde D2 (sans décroissance d'attente → effet disparaît) est un contrôle négatif de l'explication ; le fait que le moteur de A retrouve le signe de B avec des paramètres de type B est un contrôle positif de l'explication de D1.
- **Erreurs corrigées en cours de route / écarts au protocole** : 009 ne consigne aucune correction de sa propre part ; il note l'écart de bootstrap (aléatoire − FIFO) et l'existence d'un avertissement NaN non expliqué. Il se déclare « lecture seule » et affirme n'avoir touché ni A, ni B, ni commenté la PR #8 : conforme à ce que je vois (le commit ne touche que `reports/009…`).

### 6.2 Mon registre de vérifications indépendantes (V1–V25)

Méthode : extraction des corpus (`git archive`) dans le scratchpad, installation de `numpy/pandas/scipy` (absents), recalculs avec le même type de bootstrap que la sonde (4000 rééchantillonnages, `default_rng(1)`).

| # | Chiffre / affirmation de 009 | Verdict | Détail |
|---|---|---|---|
| V1 | A run 2 validation : `RANK_NET`−FIFO +0,154 [0,140 ; 0,168] ; `FIFO_NETPOS` +0,100 ; `RANK_SCORE_RAW` +0,134 ; net−brut +0,020 ; net−écran +0,054 ; `SLOTHOUR_DENSITY`−net +0,001 ; `CORR_PENALTY` 0,000 ; `MARGINAL_RISK` +0,004 ; `CLUSTER_CAP` +0,001 ; `LIN_TS` −0,013 ; `LINUCB` −0,029 ; `RANDOM` +0,024 ; RR +0,030 ; quota +0,031 ; `OLDEST_SLOT` −0,085 | ✔ | recalculés sur `validation_raw.csv.gz` (16 704 lignes, 12 familles, 29 politiques) : identiques aux 3 décimales, IC identiques |
| V2 | FIFO ≈ 0,089 dz, `RANK_NET` ≈ 0,242 | ✔ | moyennes 0,089 / 0,242 |
| V3 | `COMPOSED`−`RANK_NET` +0,025 [0,017 ; 0,034] ; `UNCERTAINTY_LCB` +0,010 [0,005 ; 0,017] | ✔ | |
| V4 | δ_equiv 0,02 = 13 % du gain ; δ_B 0,25 = 57 % de 0,435 | ✔ | 0,02/0,154 = 13,0 % ; 0,25/0,435 = 57,5 % |
| V5 | Strict : `COMPOSED` +0,243, `UNCERTAINTY_LCB` +0,239, `SHADOW_PRICE` +0,232, `MARGINAL_RISK` +0,225, `SLOTHOUR_DENSITY` +0,220, `CORR_PENALTY` +0,216, `LIN_TS` +0,174, `LINUCB` +0,176, `KNAPSACK` +0,172, `OLDEST_SLOT` −0,116 | ✔ | recalculés sur `tuning_raw.csv.gz` (15 552 lignes ; 72 politiques ; 18 bases ; caps 4 et 6) |
| V6 | S12 = 48 % du poolé ; `SLOTHOUR_DENSITY`−FIFO en S12 = +1,268 ; sans S12 ≈ 0,12 | ✔ | 0,48 ; 1,268 ; 0,125 |
| V7 | B held-out H1 : `FIFO_SCREEN` +0,164 [0,128 ; 0,200] 11/13 ; `SCORE_RANK` +0,365 12/13 ; `SLOTHOUR` +0,435 13/13 ; `SLOTHOUR`−`SCORE_RANK` +0,070 11/13 ; `LCB`−`SLOTHOUR` +0,062 ; `CORR_AWARE` −0,022 ; `LINTS` −0,020 ; `SHADOW` +0,009 ; `OLDEST_SLOT` +0,185 | ✔ | sur `H1_primary.csv` (13 scénarios × 20 graines) ; le fichier `H1_paired_macro.csv` de B donne les mêmes points (IC légèrement différents : ex. `OLDEST_SLOT` [0,140 ; 0,229] vs [0,149 ; 0,221]) |
| V8 | B : `RANDOM`−FIFO −0,042, IC B [−0,087 ; 0,001], re-bootstrap 009 [−0,072 ; −0,012] | ✔ | les deux IC existent bien (`H1_paired_macro.csv` et sonde) ; idem `EQUAL_QUOTA` : B [−0,082 ; 0,002], 009 [−0,076 ; −0,007] (non signalé par 009) |
| V9 | B, effet par K : +0,679 / +0,476 / +0,156 / −0,041 (`SLOTHOUR`−FIFO, 10 graines) | ✔ | `H3_capacity_sweep.csv` ; FIFO macro 1,834/1,814/1,720/1,312 |
| V10 | B : FIFO « tous slots pleins » 0,84/0,78/0,65/0,12 ; occupation 0,61 à K = 10 | ✔ | `full_frac` 0,839/0,784/0,646/0,123 ; occupation = 3 657,7 / (10 × 600) = 0,61 |
| V11 | A : `RANK_NET`−FIFO par cap 0,192/0,176/0,148/0,099 ; `NETPOS` 0,117/0,109/0,097/0,076 ; occupation FIFO 0,90/0,88/0,85/0,77 | ✔ | |
| V12 | Sortie complète de la sonde (4 blocs) | ✔ | relancée : `diff` **vide** vs la sortie livrée (durée 18 s) |
| V13 | Part de l'écran 33 % (edge/coût de type B) | ✔ | 0,454 / 1,393 = 32,6 % ; 72 % (S3 par défaut) = 0,549/0,759 = 72,3 % |
| V14 | Confusion d'ingestion B : FIFO 1,81–1,85 ; écart à `SLOTHOUR` 0,44–0,48 | ✔ | FIFO 1,810–1,853 ; écarts 0,449/0,470/0,440/0,480 selon RAW/DEDUP/COOLDOWN/SCORE_UPDATE — j'ai recalculé les écarts : (2,259−1,814)=0,445 ; (2,280−1,845)=0,435 ; (2,195−1,853)=0,342 ; (2,290−1,810)=0,480 → **✘ mineur** : l'écart en mode COOLDOWN est 0,34, pas 0,44–0,48 (le COOLDOWN pénalise les classeurs, ce que B écrit lui-même) |
| V15 | D3 de B : `OLDEST_SLOT` 3,00 → 1,51 → 0,02, FIFO 2,47 → 1,74 → 1,00 | ✔ (avec précision) | ce sont des **moyennes de S3 et S6** (croyance « connue ») ; 009 ne l'indique pas |
| V16 | Hors S6, gain macro de `SLOTHOUR`−`SCORE_RANK` = +0,046 ; `LCB`−`SLOTHOUR` gagne 10/13 | ✔ | 0,046 ; 10/13 |
| V17 | B : famine douce 0,016 (FIFO) → 0,03–0,06 ; déni max 215 → 273–330 h ; part max d'admission 0,144 → 0,155–0,168 ; famine dure ≤ 0,005. A K = 4 : min admit 0,336 → 0,229 ; part max 0,153 → 0,180 ; HHI 0,531 → 0,567 ; famine dure 0 → 0,014 (`LIN_TS` 0,13) ; `MARGINAL_RISK` sd 87 → 77, drawdown 323 → 265 | ✔ | B : 0,0162 → 0,0315–0,0586 ; 214,8 → 272,7–330,5 ; 0,144 → 0,152–0,168 ; max 0,0048. A : 0,336 → 0,229 ; 0,153 → 0,180 ; 0,531 → 0,567 ; 0 → 0,014 ; 0,132 ; 87,2 → 77,0 ; 322,8 → 264,9 |
| V18 | B D2 : « `SCORE_RANK` (2,24 vs 1,89) reste au-dessus de FIFO avec un gain coupé ≈ 47 % » | ✔ / **✘** | 2,240 vs 1,894 ✔ ; mais le gain de `SCORE_RANK` passe de 1,108 à 0,346 = **−69 %** (pas −47 %) ; −47 % vaut pour `SLOTHOUR` (−47,3 %) et `UNCERTAINTY_LCB` (−47,6 %). B écrit lui-même « 45–70 % » : 009 a repris le bas de la fourchette |
| V19 | Tuning A : 108 jobs, 72 politiques, 15 552 lignes | ✔ | 15 552 = 108 × 2 caps × 72 |
| V20 | B : 77 tests passent | ✔ | `77 passed in 17.61s` (dans une copie scratch) |
| V21 | PR #8 : 75 fichiers, +49 515 | ✔ | `git diff --shortstat origin/main...` : 75 files, 49 515 insertions |
| V22 | A `main` : Erlang-B 9 lignes toutes `sim_block < erlang_b`, erreur 0,002–0,020 ; fuite : 27 politiques × 5 cas = 135 runs, 0 échec, canaris 5/5 | ✔ | 0,0023–0,0197 ; 135 runs ; `failures: []` |
| V23 | B : hash des paramètres gelés = hash pré-enregistré ; `determinism_check.json` existe | ✔ | `ebcd46c4…` identique ; `hash_mismatches: 0`, `sampled: 300` (fichier lu ; les 300 ré-exécutions **non relancées** = ?) |
| V24 | (mon ajout) A branche : pré-enregistrement v2 lié à des empreintes | ✔ | `tuned_params.json` sha `d95c9910…` ; `policies.py` `0fcb4129…` ; `env.py` `e98f3d97…` ; `heldout_verdict.py` `e844d35b…` — toutes égales à celles inscrites dans `PREREGISTRATION.json` ; `policies.py` et `env.py` **identiques** entre `cb13041` et la pointe `ea3fc74` (le code n'a pas changé après les résultats de 009) |
| V25 | `main` ne contient que les sorties du tour 1 du run 1 (non octet-identique à `superseded_run1/`) | ✔ | `tuned_params.json` de `main` = `tuned_params_round1.json` (empreinte `e7ddf828…`) ; ≠ `tuned_params.json` du dossier `superseded_run1` (round 2) |

**Bilan des vérifications :** 22 des 25 lignes sont ✔ sans réserve ; 2 comportent une imprécision mineure (V14 : mode COOLDOWN ; V18 : 47 % vs 69 % pour `SCORE_RANK`) ; V23 (relance des 300 cellules) reste **?** pour la partie « relance » ; aucun chiffre clé de 009 n'est faux au sens de l'écart matériel.

---

## 7. Critique indépendante

### 7.1 Ce que 009 fait bien
- Il **refuse de trancher au-delà de ses preuves** (deux niveaux ; un verdict « inconclusif » assumé).
- Il **teste** deux de ses explications plutôt que de les affirmer ; la sonde est reproductible à l'octet.
- Il **sépare** les faits de comparaison (signe, ordre, parts) des faits de magnitude.
- Il ne fait **aucune** affirmation de compatibilité AurumShift ; `CAP_CHANGE_AUTHORIZED=FALSE` est cohérent avec `claude.md`.

### 7.2 Points faibles

1. **Les labels de réplication ne sont pas définis numériquement.** « PARTIALLY_REPLICATED » couvre : « même signe, taille très différente » (R4), « effet répliqué, label différent » (R5), « direction identique, magnitudes différentes » (R10), et « tuning seul » (strict). Quatre situations distinctes sous une seule étiquette ; le décompte « 6 REPLICATED / 3 PARTIALLY » dépend de jugements non écrits.
2. **La sonde D1 modifie huit paramètres d'un coup** (`mu_mean` 10→22, `fee_lo/hi`, `slip_lo/hi`, `dur_base` 12→7, `tau`→∞, `evict_extra` 3→0 — voir `adjudication_probe.py`, dictionnaire `BL`). Seul l'ajout « coût ×3 » est un levier unique. La conclusion « cause : niveaux de coût et d'edge » est donc **plausible mais pas isolée** : la suppression des 3 bps de frais d'éviction, le raccourcissement de la durée de base ou l'absence de décroissance pourraient à eux seuls peser. Aucune ablation paramètre par paramètre. Et A tue `OLDEST_SLOT` avec ≈ 155 fermetures forcées par run (données A, section 13) : ces 3 bps × 155 sont un candidat sérieux.
3. **Sondes à faible effectif** : 20 graines, une seule famille (S3), un seul cap (4). D2 rapporte ±0,026 ; D1 ne rapporte pas d'IC du tout (moyennes seulement). Pour un signe qui bascule de −1,4 à +0,4, c'est amplement suffisant ; pour la conclusion « −0,019 n.s. » de D2, c'est à la limite de la puissance.
4. **Asymétrie de la validation croisée** : 009 transplante le monde de B dans le moteur de A, jamais l'inverse (le moteur de B n'est pas rejoué avec des hypothèses de type A : par exemple avec un edge qui décroît pendant l'attente). Le diagnostic est donc unilatéral.
5. **Comparer une validation à un held-out** : le niveau supplémentaire met la *validation* de A (sur laquelle les seuils ont été fixés) face au *held-out* de B. C'est le point le plus délicat de la méthode. Le held-out de A (section 13) montre que l'inquiétude était **modérée** : le décalage validation → held-out pour les contrastes cités est ≤ 0,015 dz et ne change aucun signe (13.2).
6. **Dénominateurs mélangés dans les « parts »** : R2 utilise `SCORE_RANK` comme base (45 %), R5 utilise `SLOTHOUR` (14 %), R4 utilise `SCORE_RANK` (19 %). C'est écrit, mais la colonne « part du gain simple » du rapport 06 laisse penser à une base unique.
7. **Les blocs du bootstrap de A ne sont pas indépendants** : variantes d'une même famille partagent la structure ; A le dit (limitation 4). 009 le reprend sans le quantifier. Les IC de A sont donc probablement **trop étroits** (A : IC ±0,01 sur 450 blocs) par rapport à l'incertitude « design ».
8. **Résumé « famine modeste »** : côté B, la famine douce est multipliée par 2 à 3,6 (0,016 → 0,032–0,059) et le déni maximal passe de 215 h à 273–330 h (+27 % à +54 %). C'est un jugement de valeur (« modeste »). B lui-même parle de « 2–7× » (00, point 6).
9. **Verdict final unique alors que le texte en suggère deux.** Le corps du texte de 00 dit « suppl. → PARTIALLY_REPLICATED », mais `FINAL_VERDICT` est `INCONCLUSIVE`. C'est cohérent avec la règle « strict d'abord » mais **le bloc final est plus pessimiste que la lecture d'ensemble** : un lecteur pressé lira « on ne sait rien » alors que la direction est claire.
10. **Choix en bord de grille (hérités)** : B a `SHADOW θ = 0` (bord bas) et `UNCERTAINTY_LCB ω = 0,6` (bord haut) ; A a des optima au bord (limitation 5 de A). 009 n'en fait pas un point de sa critique, alors qu'il en dépend pour R5 (le « meilleur complexe » est justement choisi au bord).
11. **Erreurs/imprécisions locales** (voir V14, V15, V18) : COOLDOWN, moyenne S3/S6 non signalée, 47 % vs 69 %. Aucune ne change de conclusion.
12. **Un paragraphe de 08 est trop absolu** : « 0 bug dans B » — vrai au sens où 77 tests passent, où le hash est cohérent, et où la lecture du code n'a rien montré ; mais 009 n'a pas relancé le tuning/held-out de B. La formule correcte est « aucun défaut *détecté* », que 009 emploie d'ailleurs ailleurs (« I found no code defect »).

### 7.3 Hypothèses fragiles sur lesquelles repose l'ensemble
- Deux **générateurs de mondes bricolés** aux hypothèses proches en ce qui concerne le score (calibré par construction, pente 1), le coût (constant par admission) et l'accrual linéaire. Leur accord est en partie un accord **entre deux constructions du même auteur-modèle**, ce que 009 dit (point 12 de 04) mais dont il ne tire pas toutes les conséquences (le mot « replicated » est trompeur : une réplication indépendante suppose des données ou des hypothèses indépendantes).
- La comparabilité « par parts de gain » suppose que le dénominateur (gain du classement simple) est du même type dans les deux mondes ; or A mesure l'edge *latent* et B le net *réalisé*.

### 7.4 Ce que les chiffres ne prouvent pas
- Rien sur AurumShift, sur un plafond, sur un allocateur, sur le comportement PAPER.
- Pas que « le classement net est meilleur en pratique » : seulement qu'il l'est dans deux simulateurs où le score est bon par construction. Si le score réel est mal calibré, l'avantage fond de 45–70 % (B) ou s'inverse (A).
- Pas que les 4 désaccords sont *dus* aux hypothèses désignées : D1 et D2 sont testés (D2 proprement, D1 avec les réserves ci-dessus) ; D3, D4, D5 ne sont que « lus dans le code ».
- Pas que « les bandits sont inutiles » : seulement qu'ils n'aident pas quand le score est calibré.

### 7.5 Écarts entre rapports et résultats bruts / contradictions internes
- **Aucun écart matériel** entre les chiffres clés de 009 et les fichiers bruts (V1–V25).
- Écarts mineurs : V14 (COOLDOWN), V18 (69 % vs 47 %), V15 (moyenne S3/S6), V8 (quota non signalé).
- **Contradictions internes légères** : (i) 00 range R6 en « REPLICATED (no) », 05 le compte parmi les 6 REPLICATED : l'étiquette « répliqué » signifie ici « l'absence de gain se réplique » — sémantique ambiguë ; (ii) 09 déclare H5 « répliquée » tout en reconnaissant « modest drawdown/PnL-dispersion reductions in both » ; c'est cohérent si H5 est purement une hypothèse de rendement, mais la formulation de la clé (« machinery unnecessary ») dépasse ce que le rapport 06 montre pour le risque ; (iii) 01 indique la PR #8 « mergeable_state clean », 10 la juge non fusionnable en l'état : deux niveaux de « fusionnable » (technique vs éditorial), sans le dire.
