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
