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
