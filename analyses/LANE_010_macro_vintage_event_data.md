# Lane 010 — Macro : vintages et données d'événements — analyse approfondie

Auteur de l'analyse : analyste de recherche (Claude), pour Jean-François.
Date de l'analyse : 2026-09-29. Lecture faite sans checkout : `git show origin/claude/macro-vintage-event-data-v1:<chemin>` + extraction de l'arbre `bench/macro_vintage_v1` dans un dossier temporaire pour recalculer des chiffres (aucune branche modifiée, rien poussé).

Convention de lecture des marqueurs de vérification :
- ✔ = chiffre du rapport revérifié contre un fichier brut ou recalculé par moi
- ✘ = écart ou affirmation contredite par un fichier brut
- ? = non vérifiable avec ce qui est dans le dépôt

Labels du dépôt (claude.md) : PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN. Je les réutilise quand je qualifie une affirmation.

---

## 0. Fiche d'identité

| Élément | Valeur | Source |
|---|---|---|
| Lane | 010 — Macro : vintages et données d'événements | `SYNTHESE_LANES.md` ligne 40 |
| Mission | `AURUMSHIFT_EXTERNAL_MACRO_VINTAGE_AND_EVENT_DATA_V1` | `reports/010.../00_EXECUTIVE_SUMMARY.md` |
| Branche | `origin/claude/macro-vintage-event-data-v1` (une seule branche, pas de run « b ») | `git branch -r` |
| PR | #17 « Macro vintage & event data study (ALFRED/FRED/official sources) », **ouverte, brouillon (draft)**, non fusionnée, `mergeable_state: clean`, 2 commits, 197 fichiers, +72 364 lignes | lecture GitHub de la PR 17 |
| Base | `main` au commit `1a449df` (fusion de la PR #6, 2026-09-29 15:59 +0200) | `git merge-base` |
| Commits de la lane | `8d6ba69` « bench(macro_vintage_v1): probes and ALFRED/other-source test scripts with raw outputs » (2026-09-29 18:34:04 UTC) ; `2816204` « reports/010_macro_vintage_event_data: macro vintage & event data study » (18:37:49 UTC). Auteur affiché : « Claude ». PR créée 18:37:59 UTC | `git log` |
| Fenêtre d'exécution des appels réseau | environ 18:22 à 18:35 UTC le 2026-09-29 (horodatages `receipt_time_utc` des `*.meta.json` et `run_utc` des JSON de résultats) | fichiers `results/*.json` |
| Nombre de fichiers de la lane | 197 (12 rapports + 185 fichiers sous `bench/macro_vintage_v1`) | `git ls-tree` |
| Taille | 6 535 308 octets au total : 35 541 octets de rapports, 6 499 767 octets de bench (dont environ 2,5 Mo de pages web brutes de licences/calendriers et les fichiers Philly Fed/OCDE) | `git ls-tree -l` |
| Verdict final | `FINAL_VERDICT=LIMITED_MACRO_PIT_SOURCES_SUPPORTED` | `00_EXECUTIVE_SUMMARY.md` |
| Force du verdict | **Modérée, et honnêtement bornée** : le cœur (ALFRED sert bien les valeurs « telles que connues à la date T », et le « lookahead » venant des valeurs les plus récentes est réel) est solide sur les séries testées (je l'ai revérifié). Mais c'est un échantillon petit (8 séries américaines, 2 à 4 dates chacune), un endpoint web non documenté, aucune clé API exécutée, et plusieurs affirmations secondaires sont soit non prouvées dans le dépôt, soit contredites par les fichiers bruts (voir sections 6 et 7). |
| Autres drapeaux du bloc final | `DROP_IN_MACRO_SOURCE=NO`, `ANY_SCIENTIFIC_INVALIDATION=NO`, `LOOKAHEAD_FROM_LATEST_VALUE_PROVEN=YES`, `ALFRED_VINTAGE_SEMANTICS_PROVEN=YES`, `FRED_VINTAGE_SEMANTICS_PROVEN=NO` | idem |

Glossaire rapide (les termes reviennent partout, je les définis une fois ici, puis à leur première occurrence dans le texte) :

- **Vintage** (« millésime » de données) : une photographie d'une série économique telle qu'elle était publiée à un jour donné. Les chiffres macro sont révisés après coup (le chômage de décembre 2008 a été publié à 7,2 %, puis corrigé à 7,3 %). Chaque version successive est un « vintage ».
- **Lookahead** (« regard vers le futur ») : utiliser dans un backtest (simulation sur le passé) une information qui n'existait pas encore à la date simulée. Ici : utiliser la valeur révisée d'aujourd'hui alors qu'à l'époque on ne connaissait que la première estimation.
- **PIT** (point-in-time, « à la date exacte ») : discipline qui consiste à ne montrer à un algorithme que ce qui était connu à l'instant T.
- **ALFRED** : la base d'archives de la Réserve fédérale de Saint-Louis. FRED donne la dernière version des séries ; ALFRED (Archival FRED) donne les anciennes versions.
- **API** : « interface de programmation », une adresse web qu'un programme interroge pour obtenir des données. Une **clé d'API** est un mot de passe gratuit ou payant qui identifie l'appelant.
- **ICS** : format de fichier calendrier (comme un export Google Agenda).
- **Consensus / prévision** : la moyenne des estimations d'économistes avant une publication (par exemple « on attend +150 000 emplois »).

---

## 1. Mission et question posée

### 1.1 Reformulation simple

Dans une étude précédente (lane 005), les sources macro avec historique de révisions (FRED/ALFRED) n'avaient pas pu être jointes : « injoignables » (`SYNTHESE_LANES.md` ligne 138 de la lane 010 décrit la mission comme « débloquer le point resté ouvert après 005 »). Cette lane 010 pose donc la question :

> Existe-t-il des sources de données macroéconomiques gratuites/officielles qui permettent de savoir, pour une date T passée, quelle valeur était connue à T (pas la valeur révisée d'aujourd'hui), et à quel moment exact chaque chiffre a été rendu public ? Et existe-t-il des calendriers d'événements (publications macro) avec valeurs réelles / prévues ?

Sous-questions traitées par les rapports :
1. Quelles sont les sources (28 recensées) et lesquelles répondent sans clé (01).
2. FRED/ALFRED : la récupération « as-of » (à une date passée) fonctionne-t-elle vraiment ? (02)
3. Sources officielles américaines : BLS, BEA, EIA, NY Fed, Trésor, CFTC, Philly Fed, Fed G.17 (03).
4. Zone euro, Royaume-Uni, Canada, international (04).
5. Contrat d'horodatage : quatre horloges distinctes (observation, publication, révision, réception) (05).
6. Preuve chiffrée de l'existence du lookahead et chemins de révision (06).
7. Classement « préparation PIT » (07), calendriers et valeurs d'événements (08), licences/coûts (09), adjudication (10), limites (11).

### 1.2 Contraintes (claude.md, résumé fidèle)

- Recherche externe seulement ; aucun code privé AurumShift ; ne jamais prétendre connaître l'implémentation privée.
- Doctrine : REUSE → ADAPT → WRAP → COMPOSE → CUSTOM en dernier (réutiliser d'abord, adapter, envelopper, composer, écrire sur mesure en dernier recours).
- Sources primaires d'abord ; ne pas croire les README aveuglément ; exécuter les candidats quand c'est possible ; ne pas fabriquer de benchmark.
- Labels : PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN.
- Contraintes AurumShift pertinentes citées dans claude.md : research-only/paper-only, PostgreSQL d'abord, **PIT / provenance / no-lookahead critiques**, une source autoritaire par sujet, « l'absence de preuve n'est pas une preuve négative », faible relais opérateur.
- Ce que je constate sur le respect de ces contraintes : les rapports emploient les labels correctement dans l'ensemble (surtout « OBSERVED », « INFERENCE », « UNKNOWN »). Trois endroits emploient PROVEN ou un fait comme acquis sans fichier à l'appui (section 6/7).

---

## 2. Méthode

### 2.1 Nature de l'étude

Ce n'est **pas** un backtest ni une simulation de marché. Il n'y a donc ni univers de titres, ni simulateur, ni découpage tuning/validation/held-out, ni graines aléatoires, ni gel de paramètres, ni pré-enregistrement de seuils. C'est une **étude d'accessibilité et de sémantique de données** : on appelle des services web réels, on enregistre les réponses brutes (`bench/macro_vintage_v1/raw/`) avec métadonnées (statut HTTP, en-têtes, horodatage de réception `receipt_time_utc`, empreinte `sha256`), on résume dans `results/*.json`, et les rapports commentent.

Conséquences pour la grille de lecture demandée :
- **Splits tuning/validation/held-out** : sans objet (aucun paramètre ajusté). Je le note pour ne pas laisser croire à un oubli.
- **Pré-enregistrement / gel** : aucun document de seuils écrit avant l'exécution n'est présent dans les fichiers lus. Les « critères de décision » sont les définitions de classes du rapport 07 et l'adjudication du rapport 10, définies après coup (INFERENCE : je n'ai vu aucun fichier antérieur aux résultats qui les fixe ; les commits sont tous deux datés de 18:34–18:37 après les appels de 18:22–18:35).
- **Déterminisme** : les résultats dépendent du monde extérieur à l'instant du test (données « latest » du 2026-09-29, quotas partagés). Le README du bench le dit implicitement (« reruns may return quota errors »).

### 2.2 Protocole d'appel

`bench/macro_vintage_v1/py/common.py` (27 lignes, bibliothèque standard uniquement) : une fonction `get()` qui envoie la requête avec un User-Agent de recherche (`aurumshift-external-research-lab/macro-vintage-v1 (research; contact ...)`), mesure la latence, calcule le sha256 et écrit `raw/<nom>` + `raw/<nom>.meta.json`. L'horodatage `receipt_time_utc` représente notre propre « RECEIPT_TIME » (quand nous avons reçu la donnée), une des quatre horloges de la section 5 du rapport.

Scripts (dans l'ordre du README) :
| Script | Lignes | Rôle |
|---|---|---|
| `probe_sources.py` | 53 | 43 URL sondées (statut, taille, début du corps) → `results/probe_sources.json` |
| `alfred_test.py` | 75 | boucle sur 10 séries : liste des vintages ALFRED, test lookahead à 2–4 dates T par série → `results/alfred_lookahead.json` |
| `alfred_paths.py` | 64 | cas limites (avant premier vintage), équivalence « as-of », 6 chemins de révision, 5 pièges (traps), alignement calendrier BLS ↔ vintages ALFRED → `results/alfred_paths.json` |
| `other_sources.py` | 87 | tests BLS v1, archive BLS 2009-01-09, ECB, Eurostat, NY Fed, BoE, BoC, Trésor, CFTC, Banque mondiale, FMI, OCDE, Philly, EIA, BEA → `results/other_sources.json` |
| `calendars.py` | 25 | contenu des calendriers officiels (mots-clés forecast/previous/actual, présence d'heures) → `results/calendars.json` |
| `extra_checks.py` | 22 | 11 événements PIB BEA ↔ vintages ALFRED ; OCDE `DF_STES_REVISIONS` → `results/extra_checks.json` |
| `licence_facts.py` | 30 | extraction de phrases de licence sur 18 pages → `results/licence_facts.json` |
| `common.py` | 27 | utilitaires |

### 2.3 Mécanisme central : comment on interroge ALFRED

Point d'accès utilisé (`alfred_test.py`, constante `B`) : `https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=<SERIE>&vintage_date=YYYY-MM-DD[&cosd=..&coed=..]`. Le rapport 02 précise que c'est l'endpoint web derrière l'interface graphique, **non documenté comme contrat** (et le rapport dit bien « INFERENCE »).

Deux calculs par test de lookahead (fonction `main()` de `alfred_test.py`) :
1. **Valeur connue à T** = dernière observation retournée par ALFRED avec `vintage_date=T` (fenêtre de 2 ans avant T via `cosd`).
2. **Valeur « latest »** = même observation lue sur `fredgraph.csv` (dernière version FRED) le jour du test.
3. Différence absolue, différence de croissance (pourcentage vs observation précédente **dans le même vintage** pour « known », dans la dernière version pour « latest »), nombre d'observations de la fenêtre qui diffèrent de plus de 1e-9 (`n_obs_revised_vs_latest`).

### 2.4 Critères de décision (seuils exacts)

Il n'y a **pas de seuil numérique** pré-défini. Les décisions reposent sur des critères qualitatifs. Les voici tels que écrits :

Classes de préparation PIT (rapport 07) :
- **PIT_NATIVE** : le fournisseur sert une récupération as-of/vintage/édition (exécutée).
- **PIT_ADAPTABLE** : pas d'historique, mais drapeau de statut / horodatage de mise à jour / horodatage de ligne qui permet une capture correcte **vers l'avant** avec notre propre horodatage de réception.
- **PIT_WEAK** : dernière valeur seulement, aucun signal de révision (l'usage historique = lookahead).
- **PIT_UNSUITABLE** : inutilisable.

Coûts (rapport 09) : FREE_UNAUTHENTICATED / FREE_WITH_ACCOUNT / PAID_ONLY / UNKNOWN.

Verdicts d'adjudication (rapport 10) : ADOPT_REFERENCE / ADAPT_CANDIDATE / PARK / REJECT. Le rapport 00 explique le choix LIMITED plutôt que REFERENCE_STACK par une raison rédigée, pas par un seuil : « la pile américaine est prouvée et recoupée, mais granularité jour/mois, endpoint non documenté (API à clé non exécutée), rien de vintage hors US sauf un flux OCDE ».

### 2.5 Ce que la méthode ne fait pas

- Pas de test statistique. Le rapport 11 l'assume : « revision magnitudes are examples, not statistics ».
- Pas de tirage aléatoire des dates T : les dates sont choisies à la main (voir section 7).
- Pas d'exécution avec clés (FRED, BEA, BLS v2, EIA) car aucune clé n'existait dans l'environnement.

---

## 3. Résultats détaillés

### 3.1 Rapport 01 — Paysage des sources (28 sources)

Le rapport dresse un tableau de 28 lignes (source, officielle ou non, accès observé, exécutée ou non). Je reproduis l'essentiel, complété par mes vérifications dans `results/probe_sources.json`.

| # | Source | Résultat observé | Vérifié |
|---|---|---|---|
| 1 | FRED API `api.stlouisfed.org` | HTTP 400 « Variable api_key is not set » | ✔ (`raw/fred_api_nokey`) |
| 2 | FRED web CSV `fredgraph.csv` | 200 sans clé ; ignore `vintage_date` | ✔ |
| 3 | ALFRED web CSV + page `downloaddata` | 200 sans clé | ✔ |
| 4 | BLS API v1/v2 | v1 : 200 une fois (32 lignes) ; ensuite « daily threshold reached » | ✔ (`raw/bls_v1_recall`) |
| 5 | BLS calendrier (HTML + `bls.ics`) | 313 événements | ✔ recompté |
| 6 | BEA API | « Invalid API UserId » | ✔ |
| 7 | BEA calendrier (HTML + ICS) | 119 événements | ✔ recompté |
| 8 | EIA API v2 | 403 sans clé ; DEMO_KEY : 200 une fois | ✔ (statut 200, « incomplete return », total 270228 lignes) |
| 10 | NY Fed | 250 lignes SOFR | ✔ |
| 11 | ECB SDMX | 200 ; `updatedAfter`/`includeHistory` | **nuancé (voir 3.9 et section 7)** |
| 13 | Eurostat | 200 ; `updated` = 2026-02-06T23:00:00+0100 | ✔ |
| 15 | Banque d'Angleterre IADB | première URL renvoie une page HTML (302/erreur), seconde forme URL renvoie du CSV | ✔ (`raw/boe_iadb` 18 668 octets HTML puis `boe_iadb_v2` CSV) |
| 16 | Banque du Canada Valet | 200 | ✔ |
| 17–18 | Trésor FiscalData / XML | 200 | ✔ |
| 19 | CFTC Socrata | 200 | ✔ |
| 20 | Banque mondiale | 200, `lastupdated` WDI 2026-07-13 | ✔ |
| 21 | FMI DataMapper | 200 | ✔ |
| 22 | FMI SDMX | liste des dataflows seulement | ✔ |
| 23 | OCDE SDMX | 200 | ✔ (`oecd_sdmx_cli`) |
| 24 | Philly Fed RTDSM | xlsx | ✔ (voir 3.5) |
| 25–27 | Calendriers FRED, Fed G.17, Census | HTML | ✔ (fichiers présents) |
| 28 | TipRanks (MCP) | comparateur non officiel | ? (résultat court dans `results/tipranks_calendar_comparator.json`) |

Comptage annoncé : 28 sources ; 17 sources de données exécutées + 8 calendriers = 25 exécutées. **Point d'arithmétique** (INFERENCE de ma part) : la liste entre parenthèses est « 2,3,4,8,10,11,13,15,16,17,18,19,20,21,23,24 + OECD revisions flow », soit 16 numéros + le flux de révisions OCDE. Mais ce flux est un sous-ensemble de la ligne 23 (OCDE). Sauf à compter aussi le FMI SDMX « partiel » (ligne 22), le décompte propre est 16 + 8 = 24 et non 25. De même, « +3 variantes à clé (FRED API, BEA API, BLS v2) » : la FRED API et la BEA API sont déjà les lignes 1 et 6 du tableau de 28. Les compteurs `SOURCES_DISCOVERED=28 (+3)` et `SOURCES_EXECUTED=25` semblent donc gonflés d'une unité ou de plusieurs, sans conséquence sur le verdict. À corriger si on cite ces nombres.

Les 43 sondes de `probe_sources.py` (JSON `results/probe_sources.json`) : statuts 200 pour presque tout, 400 (FRED API sans clé), 403 (EIA sans clé), 404 (ECB `updatedAfter` sur ICP), et -1 (le fichier plat BLS `ce.data.0.AllCESSeries` échoue à la lecture : `IncompleteRead(350914448 bytes read)`, soit environ 351 Mo tentés).

### 3.2 Rapport 02 — FRED / ALFRED

Ce qui n'a PAS été exécuté (et que le rapport dit clairement) : l'API FRED officielle avec `realtime_start/realtime_end`. Sa sémantique n'est donc que DOCUMENTED_CLAIM ici.

Ce qui a été prouvé par exécution (fichiers `results/alfred_paths.json` et `alfred_lookahead.json`), avec mes vérifications :

1. **Équivalence « as-of »** : pour T donné, `vintage_date=T` renvoie le même contenu que le dernier vintage ≤ T, et diffère du vintage suivant. 4 cas sur 4 (`asof_equivalence`) :

| Série | T | Dernier vintage ≤ T | Vintage suivant | égal au dernier ≤ T | diffère du suivant |
|---|---|---|---|---|---|
| GDPC1 (PIB réel) | 2009-02-15 | 2009-01-30 | 2009-02-27 | oui | oui |
| PAYEMS (emplois non agricoles) | 2014-10-10 | 2014-10-03 | 2014-11-07 | oui | oui |
| CPIAUCSL (inflation CPI désaisonnalisée) | 2022-07-15 | 2022-07-13 | 2022-08-10 | oui | oui |
| INDPRO (production industrielle) | 2019-06-10 | 2019-05-15 | 2019-06-14 | oui | oui |
✔ vérifié.

2. **Avant le premier vintage → 404** : GDPC1 à 1985-01-01 et 1991-12-01 (premier vintage 1991-12-04), PAYEMS à 1950-01-01 (premier vintage 1955-05-06) : statut 404, corps vide. ✔ Point important : pas de repli silencieux vers la dernière version.

3. **Pièges silencieux (« traps »)** — ✔ tous confirmés dans `results/alfred_paths.json → traps` :
   - `fredgraph.csv` avec `vintage_date=2009-01-30` renvoie 16485.350 pour 2008-10-01 (valeur actuelle), pas 11599.4 : le paramètre est ignoré sans erreur.
   - `alfredgraph.csv` avec `realtime_start/realtime_end` : ignorés, renvoie la dernière version, colonne étiquetée `GDPC1_20260929`.
   - Plusieurs vintages séparés par virgule : seul le **premier** est honoré (colonne `GDPC1_20090130`, valeur 11599.4).
   - Paramètre `vintage_date` répété : seul le **dernier** est honoré (colonne `GDPC1_20090227`, valeur 11525.0).
   - `vintage_date` futur (2026-12-31) : renvoie la dernière version, colonne `GDPC1_20260929`.
   Signification : un programme naïf qui « ajoute vintage_date » sur FRED ou envoie une date future obtient du lookahead **sans aucune erreur**. C'est le piège que le pipeline d'AurumShift devrait blinder (piste, pas affirmation, section 10).

4. **Colonne nommée d'après le vintage** : `GDPC1_20090130`. Aucun horodatage, aucun identifiant de publication, aucun indicateur « préliminaire/final », aucune raison de révision. ✔ (colonnes observées dans les traps).

5. **Profondeur de vintage variable** : nombre de vintages et premier/dernier vintage (`alfred_lookahead.json`) :

| Série | Nb vintages | Premier | Dernier |
|---|---|---|---|
| GDPC1 | 418 | 1991-12-04 | 2026-08-26 |
| PAYEMS | 859 | 1955-05-06 | 2026-09-04 |
| CPIAUCSL | 669 | 1972-07-21 | 2026-09-11 |
| CPIAUCNS (CPI non désaisonnalisé) | 931 | 1949-03-24 | 2026-09-11 |
| INDPRO | 1223 | 1927-01-26 | 2026-09-18 |
| UNRATE (chômage) | 799 | 1960-03-15 | 2026-09-04 |
| DCOILWTICO (pétrole WTI) | 799 | 2011-04-06 | 2026-09-23 |
| PCEPI (prix de la consommation PCE) | 315 | 2000-08-01 | 2026-08-26 |
| DFF (taux des fonds fédéraux) | 5133 | 2005-06-28 | 2026-09-28 |
| WCESTUS1 (stocks hebdo de brut EIA) | 0 (indisponible) | | |
✔ (le chiffre 418 pour GDPC1 recompté aussi dans le HTML brut `raw/alfred_downloaddata_page`).

6. **Formulaire de téléchargement en masse** : POST → HTTP 500, cause inconnue (`UNKNOWN`, non exploré). L'obtention d'« observations par période temps-réel » en bloc n'est donc pas démontrée. ? (l'échec n'est pas capturé dans un fichier brut dédié, seulement affirmé).

Verdict du rapport : ALFRED via web CSV = PIT_NATIVE au grain du jour ; pas un remplacement immédiat (un appel par vintage, endpoint non documenté, pas d'heure).

### 3.3 Rapport 03 — Sources officielles américaines

Tableau du rapport reproduit et vérifié ligne par ligne :

| Source | Observation | Horodatage de publication | Info de révision | Vintage | Verdict de vérif. |
|---|---|---|---|---|---|
| BLS API v1 | `year`+`period` (M08) | aucun | note de bas de page `P` = préliminaire ; drapeau `latest:"true"` | non | ✔ champs `footnotes, latest, period, periodName, value, year` ; codes de notes `["", "P"]` ; 32 lignes ; 20/20 mois communs égaux à ALFRED |
| Calendrier BLS | – | heure prévue ET dans l'ICS (`DTSTART;TZID=US-Eastern:…T083000`) | – | – | ✔ 313 événements ; 2025-01-03 → 2026-12-30 |
| API BEA | – | – | – | – | ✔ non exécutée (« Invalid API UserId ») |
| Calendrier BEA | – | UTC (ex. `20250130T133000Z`) | Advance/Second/Third dans le titre | – | ✔ 119 événements ; **mais voir ✘ ci-dessous sur les identifiants** |
| EIA API v2 | `period` | aucun | aucun | non | ✔ un appel DEMO_KEY, puis limite atteinte |
| NY Fed | `effectiveDate` | aucun | `revisionIndicator` (vide sur les 250 lignes SOFR) | non | ✔ valeurs `[""]`, 250 lignes |
| Trésor FiscalData | `record_date` | aucun | aucun | non | ✔ |
| Trésor XML | `NEW_DATE` | Atom `<updated>` = 2026-09-29T02:38:00Z | aucun | non | ✔ le chiffre, mais l'interprétation est fragile (voir section 7) |
| CFTC COT | `report_date_as_yyyy_mm_dd` | `:created_at` 2026-09-25T19:30:08Z (vendredi 15:30 ET) sur lignes récentes | `:updated_at` | non | ✔ pour les lignes récentes |
| Philly Fed RTDSM | trimestre | aucun (le vintage est un mois) | vintages mensuels complets | **oui** | ✔ recalculé (3.5) |
| Fed G.17 | – | page de dates seulement | – | – | ✔ fichier présent |

**Recoupement archive BLS ↔ ALFRED (payrolls déc. 2008)** — le rapport affirme : le communiqué BLS archivé du 2009-01-09 dit « Total nonfarm payroll employment declined sharply (-524,000) in December » et ALFRED donne 135 489 − 136 013 = −524. **J'ai vérifié dans le fichier brut** `raw/bls_empsit_2009_01_09` (251 756 octets) :
- La phrase exacte « Total nonfarm payroll employment declined sharply (-524,000) in December » est présente une fois. ✔
- Le tableau de données du communiqué donne : `Nonfarm employment ... 137,331 | p136,033 | 136,597 | p136,013 | p135,489 | p-524`. Donc octobre = 136 597, novembre = 136 013, décembre = 135 489 (préliminaires, préfixe `p`). Ces trois valeurs sont **identiques** au vintage ALFRED du 2009-01-09 (`other_sources.json → bls_archive_vs_alfred_initial`: 2008-10-01 = 136 597 ; 2008-11-01 = 136 013 ; 2008-12-01 = 135 489). ✔ C'est même plus fort que ce que le rapport écrit : la concordance porte sur trois mois, pas seulement la variation.
- Le chômage passe de 6,8 à 7,2 % dans ce communiqué : ✔ cohérent avec UNRATE « connu » 7,2 (3.6).
- Nota : l'extrait automatique stocké dans `results/other_sources.json` (`bls_text`) est tronqué (« ...the unemployment rate rose from 6. ») car l'expression régulière coupe au premier point décimal ; c'est cosmétique, le fichier brut est complet.

### 3.4 Rapport 04 — Zone euro, Royaume-Uni, Canada, international

| Source | Ce qui est observé | Mon contrôle |
|---|---|---|
| ECB SDMX (ICP HICP, EXR) | `OBS_STATUS` A/E ; `OBS_COM` avec avis de changement de méthode HICP (à partir du 2026-02-04, jeu de données remplacé) | ✔ valeurs `["A","E"]` sur 24 lignes ; le texte « As of 4 February 2026 onwards, the euro area HICP inflation will undergo major methodological changes... » est dans `raw/ecb_sdmx_csv` |
| ECB `updatedAfter`/`includeHistory` | « HTTP 200 mais lignes identiques à la requête simple » | **✘ partiellement contredit — voir 3.9** |
| Eurostat `prc_hicp_manr` | `updated` = 2026-02-06T23:00:00+0100 ; pas de drapeau par observation (`status` null) | ✔ (4 valeurs renvoyées seulement) |
| BoE IADB | date + valeur | ✔ |
| BoC Valet | `d` + `v` | ✔ (clés `terms, seriesDetail, observations`) |
| Banque mondiale | `lastupdated` par source (WDI 2026-07-13) ; source 57 « WDI Database Archives » (lastupdated 2025-10-29) ; source 93 « FPN Datahub Archive » (2026-07-21) | ✔ ; le rapport ne mentionne pas la source 93 (omission mineure) |
| FMI DataMapper | dernière WEO seulement ; pages d'archives WEO : 403 | ✔ (`imf_weo_pages` = « Access Denied ») |
| FMI SDMX `api.imf.org` | liste des flux seulement | ✔ |
| OCDE SDMX | flux standards = dernière valeur ; **`DF_STES_REVISIONS`** : dimensions `REF_AREA.FREQ.MEASURE.UNIT_MEASURE.ACTIVITY.EDITION`, 79 éditions mensuelles `202003`…`202609` ; clé `USA.M.PRVM.IX.BTE..` → 3148 lignes ; production 2020-03 : 99,57 (éd. 202005), 100,21 (202006), 100,23, 100,34, 100,47, 100,39… | ✔ recalculé sur `raw/oecd_stes_revisions_USA_PRVM.csv` (voir 3.5) |

Remarque OCDE : les requêtes « trop larges » ont renvoyé HTTP 413. La découverte du flux `DF_STES_REVISIONS` n'est **pas reproductible depuis les scripts** : `other_sources.py` cherche des flux de révision dans la liste complète (`oecd_dataflow_list`, 8,9 Mo, non conservée), mais sa sortie enregistrée dit `n_dataflows: 0, revision_related: []` (expression régulière qui n'a rien reconnu). Le flux a donc été trouvé et téléchargé par une manipulation hors script (ni URL ni empreinte ni `meta.json` pour `oecd_stes_revisions_USA_PRVM.csv`). Voir sections 6/9.

### 3.5 Vérifications indépendantes : Philly Fed et OCDE

**Philadelphia Fed Real-Time Data Set (RTDSM)** — j'ai installé `openpyxl` dans mon environnement et relu `raw/philly_routputMvQd.xlsx` (696 437 octets) :
- 731 colonnes de vintages (`ROUTPUT65M11` … `ROUTPUT26M9`), 319 lignes de trimestres (`1947:Q1` … `2026:Q2`). ✔ « 731 monthly vintages, 1965M11–2026M9 ».
- Ligne 2008:Q4 : `ROUTPUT09M1` = `#N/A` ; `ROUTPUT09M2` = 11599.4 ; `ROUTPUT09M3` = 11525.0 ; `ROUTPUT09M4`, `M5`, `M6`, `M7` = 11522.1 ; `ROUTPUT09M8` = 13141.9 ; `ROUTPUT10M8` = 12993.7 ; `ROUTPUT11M8` = 12883.5 ; `ROUTPUT13M8` = 14574.6 ; `ROUTPUT23M9` = 15366.6 ; `ROUTPUT26M9` = 16485.4.
- Comparaison avec ALFRED GDPC1 2008-10-01 : 2009-01-30 = 11599.4 ✔ ; 2009-02-27 = 11525.0 ✔ ; 2009-03-26 = 11522.1 ✔ (correspond à `09M4`, donc le vintage de mars du Philly est le « troisième estimé », ce que le rapport laissait en suspens en écrivant que `09M3` précède le troisième estimé) ; 2009-07-31 = 13141.9 ✔ ; 2010-07-30 = 12993.7 ✔ ; 2011-07-29 = 12883.5 ✔ ; 2013-07-31 = 14574.6 ✔ ; 2021-07-29 = 15366.607 vs Philly 15366.6 (arrondi à 1 décimale) ✔ ; latest 16485.35 vs 16485.4 ✔.
- Nuance : « accord exact » vaut à 1 décimale. Philly arrondit ses vintages récents à 1 décimale alors qu'ALFRED garde 3 décimales pour les vintages récents (`14576.985`, `15328.027`, etc.).
- Un second fichier `raw/philly_ROUTPUTQvQd.xlsx` (243 160 octets, 244 colonnes de vintages trimestriels `ROUTPUT65Q4` … `ROUTPUT26Q3`) est présent mais n'est utilisé par aucun rapport (non mentionné).
- Le fichier `philly_realtime_dataset` (page HTML) est identique (même sha) à `lic_philly_rtds`, et la regex du script n'y a trouvé aucun lien de données (`data_links: []`) : les xlsx ont donc été téléchargés hors script.

**OCDE `DF_STES_REVISIONS`** — recalcul sur `raw/oecd_stes_revisions_USA_PRVM.csv` :
- 3148 lignes ✔ ; 79 éditions distinctes ✔ ; première `202003`, dernière `202609` ✔ ; structure `OECD.SDD.STES:DSD_STES_REVISIONS@DF_STES_REVISIONS(4.0)` ; mesure unique `PRVM` (volume de production), unité `IX` (indice), activité `BTE` (industrie hors construction).
- Observation 2020-03 par édition : 202005 = 99.57 ; 202006 = 100.21 ; 202007 = 100.23 ; 202008 = 100.34 ; 202009 = 100.47 ; 202010 = 100.39 puis 100.39 constant ; 77 éditions contiennent 2020-03. ✔ identique au rapport.
- Portée : **une seule mesure d'un seul pays**. « PIT_NATIVE (monthly edition, one measure family) » est donc une description exacte, mais le rapport 00 l'inclut dans « PIT_NATIVE_EXECUTED=3 » sans nuance sur cette étroitesse (la nuance est dans le 04 et le 07).

### 3.6 Rapport 06 — Tests de révision et preuve de lookahead

**Tableau A complet (26 lignes)** — c'est le résultat central. J'ai reproduit les chiffres depuis `results/alfred_lookahead.json` ; tous coïncident avec le rapport (✔ pour les 26 lignes). Colonnes : série, date T, vintage utilisé, observation, valeur connue à T, dernière valeur, écart, croissance connue à T, croissance dernière version, et j'ajoute la taille de la fenêtre et le nombre d'observations révisées (`n_obs_in_2y_window` / `n_obs_revised_vs_latest`, qui viennent du JSON, pas du rapport).

| Série | T | Vintage | Obs. | Connu à T | Dernier | Écart | Croiss. T % | Croiss. dern. % | fenêtre / révisées |
|---|---|---|---|---|---|---|---|---|---|
| GDPC1 | 2009-02-15 | 2009-01-30 | 2008-10-01 | 11599.4 | 16485.35 | +4885.95 | -0.965 | -2.189 | 8 / 8 |
| GDPC1 | 2011-08-15 | 2011-07-29 | 2011-04-01 | 13270.1 | 17035.114 | +3765.014 | 0.319 | 0.677 | 10 / 10 |
| GDPC1 | 2013-08-15 | 2013-07-31 | 2013-04-01 | 15648.7 | 17709.671 | +2060.971 | 0.416 | 0.268 | 10 / 10 |
| GDPC1 | 2018-08-15 | 2018-07-27 | 2018-04-01 | 18507.2 | 20150.476 | +1643.276 | 1.000 | 0.531 | 10 / 10 |
| PAYEMS | 2009-01-12 | 2009-01-09 | 2008-12-01 | 135489 | 134847 | -642 | -0.385 | -0.512 | 24 / 24 |
| PAYEMS | 2009-03-12 | 2009-03-06 | 2009-02-01 | 133768 | 133318 | -450 | -0.484 | -0.568 | 26 / 26 |
| PAYEMS | 2014-10-10 | 2014-10-03 | 2014-09-01 | 139435 | 139563 | +128 | 0.178 | 0.211 | 33 / 33 |
| PAYEMS | 2020-05-11 | 2020-05-11 | 2020-04-01 | 131045 | 130426 | -619 | -13.548 | -13.565 | 28 / 28 |
| CPIAUCSL | 2009-01-20 | 2009-01-16 | 2008-12-01 | 211.49 | 211.398 | -0.092 | -0.737 | -0.823 | 24 / 24 |
| CPIAUCSL | 2015-03-01 | 2015-02-26 | 2015-01-01 | 234.677 | 234.747 | +0.07 | -0.680 | -0.637 | 25 / 25 |
| CPIAUCSL | 2022-07-15 | 2022-07-13 | 2022-06-01 | 295.328 | 294.957 | -0.371 | 1.322 | 1.256 | 30 / 30 |
| CPIAUCSL | 2024-03-15 | 2024-03-12 | 2024-02-01 | 311.054 | 310.967 | -0.087 | 0.442 | 0.410 | 26 / 26 |
| CPIAUCNS (contrôle) | 2009-01-20 | 2009-01-16 | 2008-12-01 | 210.228 | 210.228 | 0 | -1.034 | -1.034 | 24 / 0 |
| CPIAUCNS (contrôle) | 2022-07-15 | 2022-07-13 | 2022-06-01 | 296.311 | 296.311 | 0 | 1.374 | 1.374 | 30 / 0 |
| INDPRO | 2009-01-20 | 2009-01-16 | 2008-12-01 | 103.5966 | 90.8357 | -12.7609 | -2.001 | -2.820 | 24 / 24 |
| INDPRO | 2012-05-01 | 2012-04-17 | 2012-03-01 | 96.5685 | 96.74 | +0.1715 | -0.005 | -0.518 | 27 / 27 |
| INDPRO | 2019-06-10 | 2019-05-15 | 2019-04-01 | 109.1818 | 102.274 | -6.9078 | -0.511 | -0.585 | 28 / 28 |
| INDPRO | 2022-08-01 | 2022-07-15 | 2022-06-01 | 104.3648 | 101.018 | -3.3468 | -0.199 | -0.311 | 30 / 30 |
| UNRATE | 2009-01-12 | 2009-01-09 | 2008-12-01 | 7.2 | 7.3 | +0.1 | 5.882 | 7.353 | 24 / 11 |
| UNRATE | 2010-03-01 | 2010-02-05 | 2010-01-01 | 9.7 | 9.8 | +0.1 | -3.000 | -1.010 | 25 / 16 |
| UNRATE | 2020-05-11 | 2020-05-08 | 2020-04-01 | 14.7 | 14.8 | +0.1 | 234.091 | 236.364 | 28 / 8 |
| DCOILWTICO (contrôle) | 2015-01-15 | 2015-01-14 | 2015-01-12 | 46.06 | 46.06 | 0 | -4.736 | -4.736 | 511 / 0 |
| DCOILWTICO (contrôle) | 2022-07-15 | 2022-07-13 | 2022-07-11 | 106.09 | 106.09 | 0 | -0.646 | -0.646 | 633 / 0 |
| PCEPI | 2012-05-01 | 2012-04-30 | 2012-03-01 | 115.62 | 94.284 | -21.336 | 0.208 | 0.191 | 27 / 27 |
| PCEPI | 2022-07-15 | 2022-06-30 | 2022-05-01 | 122.052 | 115.525 | -6.527 | 0.588 | 0.621 | 29 / 29 |
| DFF (contrôle) | 2015-01-15 | 2015-01-15 | 2015-01-14 | 0.12 | 0.12 | 0 | 0 | 0 | 744 / 0 |
| DFF (contrôle) | 2022-07-15 | 2022-07-15 | 2022-07-14 | 1.58 | 1.58 | 0 | 0 | 0 | 926 / 0 |

Ce que ça signifie en langage simple :
- **Les niveaux « latest » ne sont pas comparables aux niveaux historiques pour GDPC1, INDPRO, PCEPI** : ces séries sont ré-étalonnées (changement d'année de base pour les dollars chaînés du PIB, ré-indexation à 100 pour les indices). D'où l'écart de +4 886 sur le PIB de 2008:Q4 qui n'est pas une « révision » au sens économique. Le rapport le dit (« growth columns remove that effect »). Les vraies comparaisons sont les colonnes de croissance.
- **PIB 2008:Q4** : à la première publication (2009-01-30) la croissance trimestrielle réelle était -0,965 % ; aujourd'hui elle est -2,189 %. Recalcul : 11599.4 / 11712.4 − 1 = −0,965 % ; 16485.35 / 16854.295 − 1 = −2,189 % ✔. Rapport : « sens identique, ampleur 2,3× » : 2,189/0,965 = 2,27 ✔. Nota : ce sont des taux **trimestriels non annualisés** ; en taux annualisé ce serait environ −3,8 % à l'époque et environ −8,5 % aujourd'hui (calcul à partir des taux ci-dessus, INFERENCE arithmétique, non présenté par le rapport).
- **Emplois déc. 2008** : connu 135 489 (variation −524 000 vs novembre à 136 013, soit −0,385 %) ; valeur actuelle 134 847 (−0,512 % contre la valeur actuelle de novembre). ✔ recalculé : 135489/136013 − 1 = −0,385 %.
- **Production industrielle déc. 2008** : −2,001 % connu contre −2,820 % actuel ✔.
- **Chômage déc. 2008** : 7,2 connu (et confirmé par le communiqué BLS archivé) contre 7,3 aujourd'hui ✔. Avril 2020 : 14,7 puis 14,8.
- **Contrôles jamais révisés** (CPI non désaisonnalisé, taux des fonds fédéraux, pétrole WTI) : écart nul et 0 observation modifiée sur toutes les fenêtres (donc la machinerie ne fabrique pas de fausses révisions) ✔.
- **Colonne « 8–33 observations différentes »** : le rapport écrit « 8–33 » pour les séries révisées. ✔ (min 8 : UNRATE 2020 ; max 33 : PAYEMS 2014). **Mise en garde** : pour GDPC1/INDPRO/PCEPI (ré-étalonnage) et CPIAUCSL, toute la fenêtre est « révisée » (24/24, etc.) simplement parce que la base d'indice a changé ou que les facteurs saisonniers sont revisés chaque année ; ce nombre surestime donc l'impact « économique ». Pour UNRATE (11/24, 16/25, 8/28) c'est plus informatif.
- Le tableau contient aussi une petite inexactitude de présentation : les colonnes « growth % » du chômage (5,882 ; 234,091) sont le **changement en pourcentage d'un taux**, peu parlant (passer de 6,8 à 7,2 n'est pas « +5,9 % de chômage »). Sans conséquence sur les conclusions (écart de 0,1 point).

**Tableau B — chemins de révision d'une observation** (dans `alfred_paths.json → paths`, tous ✔ identiques au rapport) :

| Observation | Premier vintage | Chemin (vintage : valeur) | Dernière valeur |
|---|---|---|---|
| GDPC1 2008-10-01 | 2009-01-30 | 2009-01-30 : 11599.4 → 2009-02-27 : 11525.0 → 2009-03-26 : 11522.1 → 2009-07-31 : 13141.9 → 2010-07-30 : 12993.7 → 2011-07-29 : 12883.5 → 2013-07-31 : 14574.6 → 2014-07-30 : 14577.0 → 2017-10-27 : 14576.985 → 2018-07-27 : 15328.027 → 2021-07-29 : 15366.607 → 2023-09-28 : 16485.35 | 16485.35 |
| PAYEMS 2008-12-01 | 2009-01-09 | 135489 → 135178 (2009-02-06) → 135074 (2009-03-06) → 134328 (2010-02-05) → 134383 → 134379 → 134425 → 134774 → 134773 → 134844 → 134846 → 134842 (2018-02-02) | 134847 |
| INDPRO 2008-12-01 | 2009-01-16 | 103.5966 → 103.2183 → 103.1895 → 102.3671 → 102.5212 → 102.4338 → 102.365 (2009-06-16) → 91.0342 (2010-06-25) → 89.3334 → 89.3744 → 89.5631 → 89.5075 (2014-04-16) | 90.8357 |
| CPIAUCSL 2022-06-01 | 2022-07-13 | 295.328 → 294.728 (2023-02-10) → 294.996 → 295.072 → 294.957 (2026-02-13) | 294.957 |
| UNRATE 2020-04-01 | 2020-05-08 | 14.7 → 14.8 (2021-01-08) → 14.7 (2022-01-07) → 14.9 (2024-01-05) → 14.8 (2024-01-10) | 14.8 |
| PAYEMS 2020-04-01 | 2020-05-08 | 131072 (05-08) → 131045 (**2020-05-11**) → 130403 → 130303 → 130161 → 130513 → 130430 → 130421 → 130424 → 130426 | 130426 |

Notes de lecture :
- Le script limite chaque chemin à 12 valeurs distinctes (`if len(path) >= 12: break`). Donc PAYEMS 2008-12 s'arrête en 2018 (134 842 alors que la dernière valeur est 134 847) et INDPRO 2008-12 s'arrête en 2014 (89,5075 vs 90,8357 actuel). Le rapport ne dit pas que ces deux chemins sont tronqués ; ils ne contredisent pas le texte (« ≥ 10 ans »), mais on ne voit pas la fin.
- Le saut du PIB au vintage du **2009-07-31** (11522.1 → 13141.9, +14 %) est une révision d'ensemble/changement de base, pas une révision de conjoncture. Le rapport l'indique.
- **Curiosité 2020-05-11** : PAYEMS avril 2020 a deux vintages, 2020-05-08 (131 072) et 2020-05-11 (131 045), soit 3 jours après la publication BLS. Le rapport note « cause UNKNOWN ». Conséquence directe : la ligne PAYEMS du tableau A pour T = 2020-05-11 utilise le vintage 2020-05-11, donc **pas la première publication** (131 072) mais une correction ; la croissance connue (−13,548 %) est donc celle d'après correction. Détail non signalé dans le tableau A.
- Autre fait non signalé : PCEPI, T = 2012-05-01, vintage utilisé 2012-04-30 pour l'observation de mars 2012 ; T = 2022-07-15, vintage 2022-06-30 pour mai 2022 (le mois de juin 2022 n'était pas encore publié). Cela montre que ALFRED reflète bien le délai de publication (l'observation « la plus récente connue » n'est pas le mois précédent) : cohérent avec un vrai PIT.

**D. Conclusion du rapport** : `LOOKAHEAD_FROM_LATEST_VALUE_PROVEN = YES`. Je confirme : sur les séries révisées testées, utiliser la dernière valeur à la place de celle connue à T change la valeur du dernier point et une large part de l'historique récent, ce que ne fait pas une série jamais révisée. La formulation « proven » est justifiée pour l'existence du phénomène ; elle ne dit rien sur son **ampleur typique** (voir critique).

### 3.7 Rapport 05 — Contrat d'horodatage : quatre horloges

Le rapport distingue OBSERVATION_TIME (période décrite), RELEASE_TIME (publication), REVISION_TIME (modification), RECEIPT_TIME (notre réception). Règle appliquée : « la date d'observation n'est jamais transformée en date de publication » ; sinon `RELEASE_TIME_UNKNOWN`. Je juge la règle saine.

**Alignement vintages ALFRED ↔ calendriers officiels** :
- BLS : sur 2025-01-01 → 2026-09-28, Employment Situation : PAYEMS 20/20 et UNRATE 20/20 dates de vintage = date calendrier ; CPI : CPIAUCSL 20/20. ✔ (`alfred_paths.json → calendar_alignment`: `bls_past_events: 20`, `vintage_date_equals_calendar_date: 20`, `alfred_vintages_not_on_a_bls_date: []`, `alfred_vintages_since_2025: 20`). J'ai vérifié l'ICS brut : 23 événements « Employment Situation » au total dont 3 futurs (2026-10-02, 2026-11-06, 2026-12-04) → 20 passés ✔ ; 23 « Consumer Price Index » dont 3 futurs → 20 ✔. L'ICS contient bien les décalages dus à l'arrêt de l'administration fédérale (emploi : 2025-11-20 et 2025-12-16 ; CPI : 2025-10-24 et 2025-12-18), et ALFRED les reproduit. Heures : 174 événements à 10:00 et 139 à 08:30 ; les trois séries testées sont à 08:30 ✔ (le rapport 08 indique « 08:30/10:00 ET » ✔).
- BEA : 11/11 événements PIB (Advance/Second/Third et Q3-2025 décalé : Initial 2025-12-23, Updated 2026-01-22) ont un vintage ALFRED le même jour (`extra_checks.json`: `n: 11, same_day: 11`). ✔ Heures ICS en UTC : 13:30Z ou 12:30Z (= 08:30 ET selon l'heure d'été), répartition dans l'ICS : 12:30 (62), 13:30 (31), 14:00 (19), 15:00 (6), 17:30 (1).
- Construction proposée : date = date du vintage ALFRED ; heure = heure officielle du calendrier ce jour-là. Le rapport la qualifie « PIT_ADAPTABLE, INFERENCE au-delà des séries testées, casse pour les corrections non programmées (PAYEMS 2020-05-11) ». Bien.

**CFTC (piège de lookahead)** : le rapport affirme que `:created_at` de la ligne du 2026-09-22 est 2026-09-25T19:30:08Z (vendredi 15:30 ET) ✔ (fichier `raw/cftc_socrata_sys` : `":created_at":"2026-09-25T19:30:08.958Z"`, 3 lignes, mêmes horodatages), mais que pour la date de rapport 2015-01-06 elle est 2022-09-13T14:25:38Z, « la date de migration du jeu de données ». **✘/? Cette deuxième affirmation n'est appuyée par aucun fichier du dépôt** : « 2022-09-13 » et « 2015-01-06 » n'apparaissent ni dans `raw/`, ni dans `results/` (recherche exhaustive) — seulement dans le texte du rapport 05. L'interprétation « migration » est une INFERENCE. Elle est plausible et importante (si elle est vraie, les horodatages de lignes historiques sont des dates de chargement en masse, pas de publication), mais je ne peux pas la vérifier ici.

### 3.8 Rapport 07 — Préparation PIT

Tableau reproduit :

| Source | Classe | Base | Grain |
|---|---|---|---|
| ALFRED (web CSV) | PIT_NATIVE | as-of par `vintage_date`, 404 avant le premier vintage | jour |
| Philly Fed RTDSM | PIT_NATIVE | 731 colonnes mensuelles | mois |
| OCDE `DF_STES_REVISIONS` | PIT_NATIVE | 79 éditions mensuelles, indice de production USA seul testé | mois |
| API BLS | PIT_ADAPTABLE | drapeaux `P`, `latest` | – |
| NY Fed | PIT_ADAPTABLE | `revisionIndicator` (aucune révision vue sur 250 lignes) | – |
| ECB SDMX | PIT_ADAPTABLE | `OBS_STATUS` ; paramètre d'historique « ignoré » | – |
| Eurostat | PIT_ADAPTABLE | `updated` du jeu de données | jeu |
| CFTC | PIT_ADAPTABLE | `:created_at/:updated_at`, valides pour lignes récentes | seconde |
| Trésor XML | PIT_ADAPTABLE | Atom `<updated>` | flux |
| `fredgraph.csv` | PIT_UNSUITABLE pour l'historique | ignore `vintage_date` | – |
| API FRED | UNKNOWN | non exécutée | – |
| BoE, BoC, EIA API, FiscalData, Banque mondiale, FMI DataMapper | PIT_WEAK | dernière valeur, aucun signal | – |
| TipRanks | PIT_UNSUITABLE (non officiel) | pas d'id, pas de vintage, doublon | – |

Compteurs : PIT_NATIVE = 3 ; PIT_ADAPTABLE = 6 ✔ (cohérents avec le bloc final).

Lacunes résiduelles déclarées : aucune heure intraday dans les sources de vintage ; chemin bulk/API ALFRED non testé ; hors US pas de source de vintage sauf le flux OCDE (mesures limitées) ; historiques de révision ECB/Eurostat « non trouvés ».

**Réserve sur le classement du Trésor XML** : les 20 balises `<updated>` du flux (1 pour le flux, 19 pour les entrées) portent toutes la même valeur `2026-09-29T02:38:00Z`, alors que les entrées couvrent les dates du 2026-09-01 au 2026-09-28 (`NEW_DATE`). C'est un horodatage de **génération du flux**, pas un horodatage de publication par observation. Le rapport 07 le classe « Grain : flux » (correct) mais le bloc final 00 range « Treasury yield feed » parmi les « actual-publication stamps ». Voir section 7.

### 3.9 ECB : le test de `updatedAfter` / `includeHistory` — ce que disent réellement les fichiers bruts

Le rapport 01/04/07 : « `updatedAfter` et `includeHistory=true` → HTTP 200 mais lignes identiques à la requête simple (donc inutilisables comme historique de révision ; OBSERVED pour EXR lastN=2) ». Ce que contiennent les fichiers :

| Fichier | Requête | Statut | Octets | Empreinte (12 premiers car.) | Remarque |
|---|---|---|---|---|---|
| `ecb_sdmx_updatedAfter` | ICP `M.U2.N.000000.4.ANR?updatedAfter=2026-08-01…` | **404** | 462 | 315089770551 | corps : « No Series was returned for the query… updatedAfter="2026-08-01T02:00:00.000+02:00" … includeHistory="false" » |
| `ecb_hist` | EXR `D.USD.EUR.SP00.A?includeHistory=true&lastNObservations=2` | 200 | 742 | 6087ad5c9281 | 2 lignes, colonnes standard |
| `ecb_upd_z` / `ecb_upd_plus` / `ecb_upd_and_hist` | idem avec `updatedAfter=2026-08-01…` | 200 | 765 | beec5ff9b2e7 (identiques entre eux) | **colonne supplémentaire `ACTION` = `Replace`** |

Constats :
1. Les trois réponses `updatedAfter` sont **différentes** de la requête `includeHistory` seule (765 vs 742 octets, colonne `ACTION` ajoutée). Le paramètre `updatedAfter` est donc reconnu par le serveur (il change le format), pas « ignoré ».
2. La requête ICP avec `updatedAfter=2026-08-01` renvoie **404 « No Series was returned »**. C'est le comportement d'un filtre honoré : la série ICP (HICP historique, remplacée depuis le 2026-02-04 d'après l'avis de méthode) n'a pas été mise à jour depuis le 2026-08-01, donc aucun résultat. Le rapport 01 note ce 404 dans la ligne de sondes mais ne le discute pas.
3. Le test « EXR lastN=2 » est **non discriminant** : le taux de change quotidien EXR change tous les jours, donc les deux dernières observations ont forcément été « mises à jour » après le 2026-08-01, et il n'y avait aucune révision à exposer. Ne pas voir de différence n'établit pas que l'historique de révision est absent.
Conclusion : l'affirmation « inutilisable comme historique de révision » est **trop forte** (✘ partiel). Ce qui est réellement établi : `updatedAfter` semble fonctionner comme filtre de mise à jour (avec drapeau `ACTION`), et `includeHistory` n'a pas été testé sur une série effectivement révisée. La conséquence pratique (« ECB = PIT_ADAPTABLE, capture avant avec horodatage propre ») reste prudente, mais la mention « ECB revision histories were not found » est plutôt « non testée correctement ».

### 3.10 Rapport 08 — Calendriers et valeurs d'événements

Deux classes :

**Calendriers « horaire seulement »** (`results/calendars.json`, mes contrôles) :
| Calendrier | Machine-lisible | Heure | Id d'événement | Valeurs |
|---|---|---|---|---|
| BLS | ICS, 313 événements | 08:30 / 10:00 ET | UID par événement (313 `SEQUENCE:1`) | aucune |
| BEA | ICS, 119 événements | UTC | **rapport : « none used » ; fichier : 119 UID présents** | aucune ; étape (Advance/Second/Third) dans le titre |
| EIA WPSR | HTML | heures dans le texte (17 motifs) | – | aucune ; le mot « forecast » vient de la navigation (Forecasts/projections), ✔ |
| FRED release calendar | HTML | 11 heures | – | aucune |
| Census | HTML | 178 heures | – | aucune |
| ECB, Eurostat, Fed G.17 | HTML | 0 heure détectée | – | aucune ; ECB « forecast » = menu ✔ ; **Eurostat « previous » = vrai dans `calendars.json`, non discuté** |

**✘ BEA et identifiants** : `raw/bea_ics_real` contient 119 lignes `UID:` (par ex. `UID:0fa03438-49ca-472e-a96c-02e3c21ad4b7`) et un `DTSTAMP` et un `SEQUENCE` par événement. Le rapport 03 écrit « none (no UID used) » et le 08 « none used » : le rapport dit qu'il n'a pas *utilisé* l'UID ; le fichier prouve qu'il **existe**. Or un identifiant stable d'événement est précisément ce qu'on cherchait (le rapport reproche au comparateur TipRanks de ne pas en avoir). Autre information non exploitée : `SEQUENCE` BEA > 0 pour 27 événements (10 à 1, 9 à 2, 6 à 3, 1 à 4, 1 à 5) = événements reprogrammés ; `DTSTAMP` majoritairement 2025-09-23 (49 événements) et 2025-09-29 (40), donc l'ICS BEA est une image récente qui a été reconstruite après coup.

**Flux de valeurs** : ALFRED/RTDSM/OCDE fournissent des valeurs par vintage → on peut dériver « actual » et « previous tel que connu à T » et la révision (différence). Prévision/consensus : **aucune source officielle testée**. Seul comparateur : le MCP TipRanks (non officiel), champs `actual`, `estimate`, `prev`, `time`, `impact`, `unit` ; pas d'id d'événement, pas d'attribution, pas de révision ; un événement en double (« API Crude Oil Stock Change » à 2026-09-15T20:30:00 et T21:00:00, valeurs identiques). Exemples donnés : Retail Sales MoM 2026-09-16T12:30:00 actual 1.2, estimate 0.8, prev -0.6 ; NY Empire State 2026-09-15T12:30:00 actual 7.6, estimate 14.75, prev 20.6 (`results/tipranks_calendar_comparator.json`) ✔ ; l'échantillon complet (8 événements) n'est pas conservé, seulement 2 en exemple. L'heure sans fuseau (12:30) est interprétée comme 08:30 ET « par inférence » : cohérent avec l'heure BLS/BEA de 08:30 ET (12:30Z pendant l'heure d'été).

### 3.11 Rapport 09 — Licences et coûts

Extraits capturés (`results/licence_facts.json`), tous ✔ retrouvés dans le JSON :
| Source | Classe de coût | Fait capturé |
|---|---|---|
| FRED web CSV | gratuit sans authentification | « You can do a lot of things with FRED data … for your own personal, non-commercial use » |
| FRED API | gratuit avec compte (clé, documenté, non obtenue) | « Data series available through the FRED® API, may be owned by third parties and subject to copyright restrictions. » |
| ALFRED | gratuit sans authentification observé ; conditions ALFRED non capturées → UNKNOWN | famille de conditions du Saint-Louis Fed (INFERENCE) |
| BLS | gratuit (v1 petit quota) / avec compte (v2) | « You are free to use our public domain material without specific permission, although we do ask that you cite the Bureau of Labor Statistics as the source. » |
| BEA | avec compte | inscription avec acceptation des conditions ; non exécuté |
| EIA | avec compte / DEMO_KEY | « U.S. government publications are in the public domain » ; clé gratuite requise |
| NY Fed | sans authentification ; conditions → UNKNOWN (aucune phrase extraite) | – |
| ECB | sans authentification | « users … may make free use of the information … must appear accurately and the ECB must be cited » |
| Eurostat | conditions → UNKNOWN (URL copyright 404) | – |
| BoE | sans authentification | « The Bank typically grants permission for non-commercial re-use of the Resources » |
| BoC | sans authentification | libre usage « under the following terms » avec exceptions |
| Trésor FiscalData | sans authentification | « The data is offered free, without restriction, and available to copy, adapt, redistribute, or otherwise use for non-commercial or commercial purposes. » |
| CFTC | conditions → UNKNOWN (404) | – |
| Banque mondiale | conditions du site : « informational and non-commercial purposes only, unless otherwise stated » ; licence du jeu de données non capturée → UNKNOWN | – |
| FMI | 403 → UNKNOWN | – |
| OCDE | 403 → UNKNOWN | – |
| Philly Fed | gratuit | « may be used by macroeconomic researchers to verify empirical results, to analyze policy, or to forecast » ; citation demandée |
| TipRanks | via compte MCP ; conditions UNKNOWN | – |

Le rapport ajoute « No PAID_ONLY source was needed for any result » (✔ cohérent) et s'interdit toute conclusion juridique (sain). **Point sensible non tranché** : l'usage de FRED/ALFRED est décrit « pour usage personnel non commercial » et « les séries tierces peuvent avoir un droit d'auteur » : le rapport le cite mais n'en tire pas de conséquence (bonne discipline) — c'est un point à adjuger (section 10).

### 3.12 Rapport 11 — Limites déclarées (11 points) : voir section 7 pour l'évaluation.

---

## 4. Candidats / méthodes évalués un par un

Verdicts du rapport 10 (« pas de classement synthétique »), avec mon appréciation de la justification chiffrée et des conditions de changement.

| Composant | Décision du rapport | Justification chiffrée (vérifiée ?) | Mon avis | Ce qui ferait changer le verdict |
|---|---|---|---|---|
| ALFRED, récupération as-of (web CSV) | **ADOPT_REFERENCE** (US, grain jour) avec enveloppe ADAPT | 4/4 équivalences as-of ; 404 avant premier vintage ; 20+20+20 dates BLS et 11 dates BEA alignées ; valeurs initiales = archive BLS (3 mois) et = Philly Fed (✔) | Défendable pour les 8 séries testées ; « ADOPT_REFERENCE » est un peu généreux vu que l'endpoint n'est pas documenté et que la clé n'a jamais été utilisée. Je le lirais « référence de contrôle de sémantique » plutôt que « source de production » | Test API FRED à clé (`realtime_*`), test bulk, échec de l'endpoint web, découverte d'un vintage manquant/erroné sur une série non testée |
| API FRED `realtime_*` | PARK | non exécutée, aucune clé | cohérent : ne rien affirmer | obtention d'une clé gratuite et rejeu de `alfred_test.py` |
| `fredgraph.csv` | **REJECT** pour l'historique | ignore `vintage_date` (✔ 16485.350 renvoyé au lieu de 11599.4) | solide | aucun |
| Philly Fed RTDSM | ADOPT_REFERENCE (contrôle croisé indépendant) | 731 vintages, valeurs identiques à ALFRED sur PIB (✔ recalculé à 1 décimale) | solide comme contrôle ; limité (série `ROUTPUT` testée, mensuel, la liste des autres variables du jeu n'a pas été extraite) | idem : élargir aux autres variables du jeu |
| OCDE STES revisions | ADAPT_CANDIDATE | 79 éditions, 3148 lignes, une seule mesure USA | prudent ; vraie valeur potentielle car non-US, mais couverture inconnue | test sur d'autres pays/mesures ; documentation du flux |
| ICS BLS + BEA | ADOPT_REFERENCE pour RELEASE_TIME programmé | 100 % d'accord de date sur séries testées (✔) | valable **pour les séries testées sur 2025–2026 seulement** ; l'alignement est partiellement circulaire (voir 7) | un calendrier d'archive pour 2008–2024 ; comparaison à un calendrier figé avant les événements |
| API BLS | PARK | quota anonyme épuisé après 1 appel | cohérent ; le rapport ne teste jamais v2 | clé v2 |
| CFTC Socrata | ADAPT_CANDIDATE (capture avant seulement) | `:created_at` valable après la migration 2022-09 | la borne « 2022-09 » n'est pas dans les fichiers (✘/?) ; sinon raisonnable | preuve brute de la date de migration |
| NY Fed, ECB, Eurostat, Trésor | ADAPT_CANDIDATE (capture avant avec horodatage de réception) | drapeaux/horodatages sans historique | prudent pour NY Fed/Eurostat ; pour ECB voir 3.9 (test mal conçu, potentiel sous-estimé) ; Trésor : stamp de flux | test ECB `includeHistory`/`updatedAfter` sur une série effectivement révisée |
| BoE, BoC, EIA, FiscalData, Banque mondiale, FMI DataMapper | PARK pour usage PIT | dernière valeur, aucun signal | cohérent | découverte d'un mécanisme d'archive (par ex. source 57 Banque mondiale « WDI Database Archives ») |
| TipRanks calendrier | PARK / non PIT | non officiel, pas d'id, 1 doublon | cohérent | fourniture d'ids et d'horodatage de publication |

Note de doctrine (REUSE→ADAPT→WRAP→COMPOSE→CUSTOM) : la lane ne propose aucun développement sur mesure ; les recommandations sont des enveloppes autour de services existants (WRAP/ADAPT) et une composition date-de-vintage + heure-de-calendrier (COMPOSE). C'est conforme.

---

## 5. Bloc final complet et explication ligne par ligne

Bloc reproduit tel quel (`reports/010_macro_vintage_event_data/00_EXECUTIVE_SUMMARY.md`) :

```
SOURCES_DISCOVERED=28 (+3 key-gated variants: FRED API, BEA API, BLS v2)
SOURCES_EXECUTED=25 (17 data sources with data path + 8 official calendars fetched; TipRanks unofficial comparator executed separately, not counted)

PIT_NATIVE_EXECUTED=3 (ALFRED web CSV, Philadelphia Fed RTDSM, OECD DF_STES_REVISIONS)
PIT_ADAPTABLE_EXECUTED=6 (BLS API, NY Fed, ECB, Eurostat, CFTC, Treasury yield XML)

FRED_EXECUTED=PARTIAL (web CSV fredgraph executed; official API api.stlouisfed.org not executed - no key)
ALFRED_EXECUTED=YES (web CSV + vintage list page; bulk form POST failed HTTP 500)
FRED_VINTAGE_SEMANTICS_PROVEN=NO (FRED latest ignores vintage_date; keyed API realtime_* not executed)
ALFRED_VINTAGE_SEMANTICS_PROVEN=YES (web CSV, day granularity; keyed API path not tested)

RELEASE_TIMESTAMP_SOURCES=scheduled: BLS ICS, BEA ICS (machine-readable), EIA/FRED/Census HTML; actual-publication stamps: CFTC (recent rows), Treasury yield feed; date-level via ALFRED vintage date. No source gives an intraday actual for macro releases.
REVISION_AWARE_SOURCES=3 vintage-native (ALFRED, Philly Fed RTDSM, OECD STES revisions) + 4 flag-only (BLS P flag, NY Fed revisionIndicator, ECB OBS_STATUS, CFTC :updated_at)

LOOKAHEAD_FROM_LATEST_VALUE_PROVEN=YES

DROP_IN_MACRO_SOURCE=NO
ANY_SCIENTIFIC_INVALIDATION=NO

FINAL_VERDICT=LIMITED_MACRO_PIT_SOURCES_SUPPORTED
```

Explication clé par clé :

| Clé | Signification en langage simple | Ce que j'en pense |
|---|---|---|
| `SOURCES_DISCOVERED=28 (+3 …)` | 28 services recensés ; 3 variantes qui demandent une clé (FRED API, BEA API, BLS v2) | les deux premières sont déjà lignes 1 et 6 du tableau : le « +3 » double compte probablement (3.1) |
| `SOURCES_EXECUTED=25` | 25 services réellement appelés (17 sources de données + 8 calendriers), TipRanks à part | arithmétique à corriger (OCDE compté deux fois : 24 propres) |
| `PIT_NATIVE_EXECUTED=3` | 3 sources qui servent « la valeur telle que connue à T » | ✔ vérifié pour ALFRED et Philly ; OCDE limité à une mesure USA |
| `PIT_ADAPTABLE_EXECUTED=6` | 6 sources sans historique mais avec un indice (drapeau, date de mise à jour) permettant de bien enregistrer les données à partir de maintenant | ✔ cohérent avec 07 ; ECB potentiellement sous-classé (3.9) |
| `FRED_EXECUTED=PARTIAL` | seule la partie web CSV de FRED a tourné, pas l'API officielle (pas de clé) | ✔ |
| `ALFRED_EXECUTED=YES` | ALFRED a répondu ; le téléchargement en masse (formulaire) a échoué en HTTP 500 | ✔ (l'échec du POST n'est pas capturé dans un fichier brut : ?) |
| `FRED_VINTAGE_SEMANTICS_PROVEN=NO` | on n'a pas prouvé que FRED gère les vintages (la version web les ignore, l'API n'a pas été testée) | ✔ honnête |
| `ALFRED_VINTAGE_SEMANTICS_PROVEN=YES` | on a prouvé le comportement « as-of » d'ALFRED au grain du jour, par le canal web | ✔ pour les séries testées |
| `RELEASE_TIMESTAMP_SOURCES=…` | d'où vient l'heure de publication : heures prévues (ICS BLS/BEA, pages HTML), horodatages réels seulement pour CFTC (lignes récentes) et flux du Trésor ; date via le vintage ALFRED ; aucune heure réelle intraday pour les publications macro | la mention « Treasury yield feed » comme horodatage réel est fragile (identique pour 20 balises) |
| `REVISION_AWARE_SOURCES=3 + 4` | 3 sources natives + 4 avec drapeaux seulement | ✔ cohérent (ECB OBS_STATUS A/E, BLS P, NY Fed vide, CFTC `:updated_at`) |
| `LOOKAHEAD_FROM_LATEST_VALUE_PROVEN=YES` | utiliser la dernière valeur au lieu de celle connue à T crée réellement un regard vers le futur | ✔ |
| `DROP_IN_MACRO_SOURCE=NO` | aucune source « prête à brancher » qui couvre tout | ✔ raisonnable |
| `ANY_SCIENTIFIC_INVALIDATION=NO` | aucune prémisse antérieure n'est invalidée | ✔ ; l'affirmation antérieure « ALFRED PIT-native = DOCUMENTED_CLAIM » passe à PROVEN pour le canal web |
| `FINAL_VERDICT=LIMITED_MACRO_PIT_SOURCES_SUPPORTED` | des sources PIT macro limitées sont prises en charge (US, jour/mois) | ✔ verdict cohérent avec les preuves ; l'étiquette dit bien « limited » |

---

## 6. Contrôles de validité

### 6.1 Ce que la lane fait bien

- **Contrôles négatifs** : séries jamais révisées (CPIAUCNS, DFF, DCOILWTICO) donnent 0 écart et 0 observation modifiée (✔ 6 tests, `n_obs_revised_vs_latest: 0`). La machinerie ne fabrique donc pas de faux lookahead.
- **Contrôles positifs** : séries connues pour être révisées montrent des révisions ; le chômage 7,2→7,3 correspond au communiqué BLS d'époque.
- **Vérité terrain externe** : (i) BLS archive 2009-01-09 : trois mois de payrolls identiques à ALFRED ; (ii) Philly Fed : 8 vintages identiques à ALFRED sur le PIB 2008:Q4 (à 1 décimale). Ce sont deux sources indépendantes de l'endpoint ALFRED : c'est le point le plus fort de la lane.
- **Cas limites** : 404 avant premier vintage ; 5 pièges silencieux documentés ; futur → repli silencieux sur la dernière version.
- **Traçabilité** : chaque appel du bench a un `.meta.json` (statut, en-têtes, `receipt_time_utc`, sha256). Les dates de réception (18:22–18:35 UTC) sont cohérentes avec les `run_utc` des JSON.
- **Règle d'horloges** : jamais de mapping observation → publication.
- **Transparence** : le rapport 11 liste 11 limites, dont le contexte d'exécution (IP partagée, absence de clés), la petitesse de l'échantillon, les licences UNKNOWN.

### 6.2 Tests de fuite / lookahead

L'ensemble de la lane est, en un sens, un test de lookahead. Aucun modèle n'est entraîné, donc pas de « fuite » de type entraînement/validation. Le risque de fuite qui existe est celui des **outils de test eux-mêmes** : la comparaison utilise `fredgraph.csv` du jour comme « latest » ; ça suppose que ce fichier reflète bien la dernière version d'ALFRED. Vérification par le contrôle : la dernière colonne ALFRED (`GDPC1_20260929` sur une date future) est identique à `fredgraph.csv` (16485.350 pour 2008-10-01 dans les deux cas). ✔

### 6.3 Déterminisme

Non déterministe par nature (services vivants). Les vintages historiques, eux, devraient être stables (une fois publié, un vintage ne change pas), sauf si ALFRED corrige ses archives. Les « latest » varient avec le temps. Les JSON ne sont donc reproductibles que pour la partie historique. Pas de graine aléatoire (rien d'aléatoire).

### 6.4 Erreurs corrigées en cours de route / écarts au protocole

Observés dans les fichiers (le dépôt ne garde pas de journal explicite d'erreurs) :
- Sonde initiale `bea_schedule_ics` (`https://www.bea.gov/news/schedule/ical`) : la réponse est du HTML (61 290 octets), pas de l'ICS. Corrigé dans `calendars.py` en récupérant `https://www.bea.gov/news/schedule/ics/online-calendar-subscription.ics` sous `bea_ics_real`. Le rapport 01 ne mentionne pas cet aller-retour.
- Sonde initiale BoE : première forme d'URL renvoie une page HTML ; seconde forme (`/boeapps/iadb/fromshowcolumns.asp`) donne le CSV. Mentionné dans 01.
- `bls_ces_flat` (fichier plat BLS d'environ 351 Mo) : échec `IncompleteRead`, non conservé (rapport 11, point 11 ✔).
- Sorties du script `other_sources.py` incomplètes : `oecd → n_dataflows: 0`, `philly → data_links: []`. Les deux valeurs montrent que les regex ne matchent pas ; les fichiers utiles ont donc été obtenus autrement (non scripté).
- Fichiers dupliqués dans `raw/` (empreintes identiques) : `ust_yield_xml` = `ust_yield_xml_full` ; `boe_iadb_v2` = `boe_iadb_v2b` ; `imf_datamapper_gdp_usa` = `imf_datamapper_weo` ; `wb_sources` = `worldbank_archive_sources` ; `philly_realtime_dataset` = `lic_philly_rtds`. Sans conséquence.

### 6.5 Écarts aux exigences de traçabilité

- Deux fichiers de données centraux (`philly_routputMvQd.xlsx`, `oecd_stes_revisions_USA_PRVM.csv`) n'ont ni `meta.json`, ni URL, ni empreinte, ni script de téléchargement dans le dépôt. Provenance non traçable (viole l'esprit « provenance » du dépôt).
- Une affirmation (CFTC 2015-01-06 → 2022-09-13) sans fichier brut.

---

## 7. Critique indépendante

### 7.1 Écarts entre rapports et résultats bruts (détectés)

| # | Affirmation du rapport | Ce que montrent les fichiers | Gravité |
|---|---|---|---|
| E1 | ECB : `updatedAfter`/`includeHistory` « ignorés, lignes identiques » (01, 04, 07) | La réponse `updatedAfter` diffère (colonne `ACTION=Replace`, 765 vs 742 octets) ; la requête ICP avec `updatedAfter` renvoie 404 « No Series was returned » (filtre honoré) ; le test EXR est non discriminant | Moyenne : sous-estime un possible historique de révision ECB ; la conclusion « non trouvé » devrait être « non testé de façon concluante » |
| E2 | BEA ICS : « pas d'identifiant d'événement / no UID used » (03, 08) | 119 `UID` présents (un par événement), plus `SEQUENCE` (27 événements reprogrammés) et `DTSTAMP` | Moyenne : l'information existe ; le rapport la présente comme absente pour BEA et pour le tableau comparatif |
| E3 | CFTC : historique 2015-01-06 avec `:created_at` = 2022-09-13T14:25:38Z, « date de migration » (05) | Aucun fichier du dépôt ne contient ces valeurs | Moyenne : point important pour la sécurité PIT, invérifiable ici |
| E4 | Trésor XML = « actual-publication stamp » (00) | 20 balises `<updated>` toutes égales à 2026-09-29T02:38:00Z pour des entrées du 2026-09-01 au 2026-09-28 : stamp de génération du flux | Moyenne : classé correctement « grain flux » en 07 mais mal rangé en 00 |
| E5 | OCDE : flux découvert via la liste des dataflows (implicite) | `results/other_sources.json` : `n_dataflows: 0` | Faible : le résultat central OCDE est réel (fichier CSV), mais sa découverte n'est pas rejouable |
| E6 | Comptage 25 exécutées / 28 (+3) | OCDE compté deux fois ; FRED API et BEA API déjà dans les 28 | Faible |
| E7 | Tableau A ligne PAYEMS T=2020-05-11 présentée comme « valeur connue à T » | vintage utilisé = 2020-05-11 (correction), pas la première publication 2020-05-08 (131 072) | Faible : signalé ailleurs (06 B et 05) mais pas dans le tableau |
| E8 | Chemins PAYEMS 2008-12 et INDPRO 2008-12 | tronqués à 12 valeurs (plafond dans `alfred_paths.py`) ; non signalé | Faible |
| E9 | Eurostat calendrier : aucune valeur | `calendars.json` : `previous: true` pour Eurostat, non discuté (ECB et EIA « forecast » sont expliqués, pas Eurostat « previous ») | Faible |
| E10 | Banque mondiale : archives | source 93 « FPN Datahub Archive » non mentionnée | Très faible |

### 7.2 Points faibles méthodologiques

1. **Échantillon petit et non aléatoire** : 8 séries américaines révisées, 2 à 4 dates T choisies à la main par série, dont plusieurs autour de la crise 2008–2009 et de 2020 (périodes de révisions atypiquement grandes). Les « exemples de lookahead » (payrolls déc. 2008, PIB T4-2008, production industrielle, chômage) sont des cas **dramatiques mais vrais**. Ils prouvent l'existence du phénomène, pas son ampleur moyenne. Le rapport 11 (point 7) le dit : « examples, not statistics ».
2. **Sélection des exemples** : les cas vedettes du rapport 00 sont tous du même mois (décembre 2008 pour trois séries sur quatre). Un lecteur pressé pourrait surestimer la généralité. À l'inverse, PAYEMS 2014-09 a une révision de sens opposé (+128), CPI 2015-01 aussi (+0,07) : le tableau montre que le signe varie, ce qui est une bonne information. Le rapport ne calcule pas de statistique de révision moyenne/absolue.
3. **Dépendance à un endpoint web non documenté** (`alfredgraph.csv`) : le contrat n'est pas garanti ; le rapport le dit deux fois. Le fait que `realtime_start/realtime_end` soit ignoré sur cet endpoint alors qu'il est documenté sur l'API montre que ce n'est pas le même produit.
4. **Alignement calendrier ↔ vintage partiellement circulaire** : l'ICS BLS/BEA est une photographie récente (BEA : `DTSTAMP` en 2025-09 à 2026-01, `SEQUENCE` jusqu'à 5) qui contient les dates réelles des événements passés (y compris les décalages de l'arrêt fédéral). 60/60 et 11/11 montrent donc que « les dates actuelles de l'ICS coïncident avec les dates de vintage », pas que le calendrier *prévisionnel* de l'époque prévoyait bien ces dates. Pour une heure de publication *ex ante* (connue à l'avance), il faudrait un calendrier archivé à l'époque. Par ailleurs l'alignement porte sur 2025–2026 seulement ; pour 2008 (le cas vedette) aucun calendrier officiel n'a été testé (le rapport 11 point 3 le dit).
5. **Granularité** : vintages ALFRED au jour ; l'heure n'est reconstruite que par le calendrier. Pour une stratégie intra-journalière (le dépôt cite « event-driven / intraday »), une publication à 08:30 ET et un vintage daté du même jour impliquent que la valeur n'est connue qu'à partir de 08:30, mais le fichier ne prouve pas *à quelle minute* ALFRED l'a reçue.
6. **Quotas / IP partagée** : BLS et EIA n'ont qu'un appel chacun ; les conclusions « PARK » sont donc fondées sur un seul échantillon.
7. **Comparaison « latest » à un instant** : les « latest » sont datés du 2026-09-29 ; les valeurs pourront changer (cas : GDPC1 2008-10-01 a changé pour la dernière fois en 2023-09-28).
8. **Choix en bord de grille** : sans objet (pas de grille de paramètres). Le seul « bord » est le plafond de 12 valeurs par chemin de révision (E8) et la fenêtre de 2 ans de `cosd` dans `alfred_test.py`.
9. **Hypothèses fragiles** : (i) que `vintage_date` de l'endpoint web = date de publication réelle (vérifié 60/60 sur 3 séries, jamais sur 2008–2024) ; (ii) que les corrections non planifiées (PAYEMS 2020-05-11) sont rares (une seule instance testée, cause inconnue) ; (iii) que le Philly Fed et ALFRED sont « indépendants » : le rapport dit « independent providers » et écrit ailleurs qu'ils utilisent des sources différentes ; cependant ils dérivent tous deux des publications BEA, donc l'accord confirme la fidélité de la reproduction, pas la vérité économique.

### 7.3 Ce que les chiffres ne prouvent PAS

- Que ALFRED est complet et exact pour toutes les séries (seules 8 ont été testées).
- Que le chemin API à clé de FRED se comporte comme le chemin web.
- Que l'absence de vintage hors US est structurelle (ECB : test mal conçu ; Banque mondiale source 57 : requêtes d'archive non abouties, cause non explorée ; FMI archives : 403).
- Que le flux du Trésor est horodaté à la publication.
- Qu'une heure de publication intraday est disponible pour les indicateurs macro (le rapport le dit : non).
- Qu'il y a une différence significative de performance de stratégie entre données PIT et données « latest » : la lane n'a fait aucun backtest.
- La licence de redistribution ou d'usage commercial pour aucune source (le rapport s'interdit toute conclusion juridique ; 8 licences sur 18 en UNKNOWN ou partielles).

### 7.4 Contradictions internes

- Bloc final : « actual-publication stamps: CFTC (recent rows), Treasury yield feed » vs rapport 07 : Trésor « Grain : flux » (stamp de génération), et rapport 05 : « only CFTC recent rows and Treasury yield feed » — cohérent en apparence, mais le fichier montre un stamp unique pour 19 dates différentes.
- Rapport 03 : « BEA … Event id : none » vs fichier ICS BEA avec UID (E2).
- Rapport 04/07 : ECB « history param ignored » vs `ACTION=Replace` et 404 filtré (E1).
- `SOURCES_EXECUTED` (E6).
- Rapport 05 dit que la construction date+heure « casse pour les corrections non programmées (PAYEMS 2020-05-11) » et le rapport 06 dit « cause UNKNOWN (not explained by any calendar fetched) » : cohérent.

### 7.5 Biais possibles

- Biais de disponibilité : on teste des séries très visibles (PIB, emplois, CPI), les mieux archivées.
- Biais de période d'observation : les révisions de 2008–2009 et 2020 sont exceptionnelles.
- Biais d'environnement : horloge du test (2026-09-29), IP partagée ; certains sites bloquent les clients anonymes (403 BLS sans User-Agent, IMF/OCDE) — l'affirmation « BLS 403 without UA » n'est pas conservée en fichier (?).

---

## 8. Comparaison de plusieurs runs/branches

Sans objet : une seule branche (`claude/macro-vintage-event-data-v1`) et un seul run. `SYNTHESE_LANES.md` (ligne 150) signale une possible « session en double » (une autre session sur `claude/tender-lovelace-h86kec`) dont je n'ai vu aucun résultat poussé ; non lu, non comparé. Les seuls recoupements internes possibles sont ceux de la section 3.5 (ALFRED vs Philly vs BLS archive) : accord parfait sur 3 mois de payrolls et 8 valeurs de PIB.

---

## 9. Reproductibilité

Commande du README :
`cd bench/macro_vintage_v1/py && python3 probe_sources.py && python3 alfred_test.py && python3 alfred_paths.py && python3 other_sources.py && python3 calendars.py && python3 extra_checks.py && python3 licence_facts.py`

- Dépendances : Python 3 bibliothèque standard ; `openpyxl` seulement pour lire le xlsx du Philly Fed (j'ai dû l'installer pour vérifier ; le module manquait dans mon environnement).
- Réseau requis, sans clé. Durée d'après le README : `alfred_test.py` ≈ 5 min, `alfred_paths.py` ≈ 10 min ; les autres sont courts (la fenêtre observée de tous les appels est d'environ 13 minutes, 18:22–18:35 UTC).
- Fourni : scripts, réponses brutes, `meta.json` (sauf exceptions), résultats agrégés, 12 rapports.
- **Manque / non reproductible depuis le dépôt** : (1) téléchargement des deux fichiers Philly Fed (xlsx mensuel et trimestriel) ; (2) téléchargement du CSV OCDE de révisions (URL de la requête `USA.M.PRVM.IX.BTE..` non consignée) ; (3) requête CFTC historique de 2015 ; (4) l'échec HTTP 500 du formulaire ALFRED ; (5) requêtes d'archive Banque mondiale « indicator not found » ; (6) OCDE liste de flux (8,9 Mo, non conservée) et liste BoC (3,6 Mo, la sonde `boc_schedule` a un `meta` mais le corps n'est pas dans le dépôt) ; (7) l'appel TipRanks (MCP, huit événements, seuls deux exemples conservés).
- Une re-exécution donnera des valeurs « latest » différentes, des vintages historiques identiques (sauf correction d'archive), et sans doute des erreurs de quota BLS/EIA (IP partagée).
- Rejouabilité partielle du script `extra_checks.py` : il lit `oecd_stes_revisions_USA_PRVM.csv` sans le télécharger ; il échouera si ce fichier est absent.

---

## 10. Implications pratiques pour AurumShift (pistes à adjuger plus tard, aucune affirmation de compatibilité)

Je n'ai aucune connaissance du code privé d'AurumShift ; tout ce qui suit est à **adjuger** par vous avec la connaissance interne.

1. Une règle « jamais de dernière valeur pour le passé » : la lane montre que `fredgraph.csv` (dernière version) + un paramètre `vintage_date` ignoré = lookahead silencieux. Piste : à adjuger si un contrôle de garde (par exemple exiger la colonne nommée `<SERIE>_<AAAAMMJJ>` égale à la date demandée) aurait un sens dans un pipeline macro.
2. Piège des dates futures : un `vintage_date` futur renvoie la dernière version, sans erreur. Piste : à adjuger si un rejet explicite des dates postérieures à l'instant de la requête est pertinent.
3. Séparer les quatre horloges (observation, publication, révision, réception) dans le modèle de données PIT ; le rapport 05 en donne la grille. À adjuger : correspondance avec ce qui existe déjà en interne.
4. Pour le temps de publication : composition « date de vintage ALFRED + heure officielle du calendrier BLS/BEA » (COMPOSE) plutôt que du sur-mesure ; à adjuger avec les réserves de 7.2 (circularité, 2025–2026 seulement, corrections non programmées).
5. Capture vers l'avant (forward capture) avec horodatage de réception propre pour les sources sans historique (NY Fed, ECB, Eurostat, Trésor, CFTC) ; l'ECB mérite un nouveau test correct avant de décider (3.9).
6. Licences : FRED/ALFRED parlent d'usage personnel non commercial et de séries tierces possiblement sous droit d'auteur ; BLS/EIA/Trésor sont en domaine public/libre. À adjuger : quelle source retenir pour un usage recherche vs production ; une clé API FRED (gratuite) est mentionnée comme documentée, non obtenue.
7. Le calendrier avec prévisions/consensus n'existe pas en source officielle testée ; le seul candidat testé (TipRanks) est non officiel, sans id ni vintage. À adjuger si un consensus est réellement nécessaire.
8. Ne pas déduire de cette lane un gain de performance ; aucun backtest n'a été fait.

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **Tester l'API FRED officielle** avec une clé gratuite (`realtime_start/realtime_end`, `output_type`) et rejouer `alfred_test.py` : lève le point « clé jamais exécutée », qui conditionne le passage de LIMITED à REFERENCE_STACK. Valeur : très haute.
2. **Mesure statistique des révisions** : au lieu de 4 dates choisies à la main, échantillonner toutes les dates de publication 1990–2025 pour les mêmes séries et rapporter la révision absolue moyenne/médiane et les percentiles de l'écart « première publication vs dernière valeur » par série. Valeur : haute (donne l'ampleur du lookahead, ce que la lane n'a pas fait).
3. **Alignement vintage ↔ dates de publication sur l'historique** (2008–2024), avec un calendrier archivé (BLS/BEA archives) plutôt que l'ICS actuel. Valeur : haute (lève la circularité).
4. **Retester l'ECB** (`updatedAfter`, `includeHistory`) sur une série connue pour être révisée, et documenter la colonne `ACTION`. Valeur : moyenne-haute (potentielle source de vintages non-US).
5. **Élargir l'OCDE `DF_STES_REVISIONS`** (autres pays, autres mesures) et conserver l'URL, la date de requête et l'empreinte. Valeur : moyenne-haute.
6. **Corriger la provenance** des fichiers Philly/OCDE/CFTC (scripts de téléchargement + `meta.json`) et corriger E2, E4, E6. Valeur : moyenne (hygiène de preuve).
7. **CFTC** : capturer la preuve brute de la date de migration 2022-09 (ou infirmer). Valeur : moyenne.
8. **Résoudre l'énigme PAYEMS 2020-05-11** (vintage 3 jours après la publication) et rechercher d'autres vintages hors calendrier sur 2000–2025. Valeur : moyenne.
9. **Tester le chemin bulk ALFRED** (HTTP 500 sur le formulaire) et une clé BEA/BLS v2/EIA. Valeur : moyenne.
10. **Banque mondiale source 57** (archives WDI) : comprendre pourquoi les requêtes d'archive échouent ; FMI archives WEO (403 avec User-Agent de recherche). Valeur : basse-moyenne.
11. **Licences UNKNOWN** (ALFRED, NY Fed, Eurostat, CFTC, FMI, OCDE) : capturer les textes par un autre canal. Valeur : moyenne pour une décision réelle d'usage.

---

## 12. Index des fichiers lus

Rapports (`reports/010_macro_vintage_event_data/`, tous lus intégralement) :
- `00_EXECUTIVE_SUMMARY.md` : 7 constats, bloc final, raison du verdict LIMITED.
- `01_SOURCE_LANDSCAPE.md` : tableau des 28 sources, comptages.
- `02_FRED_ALFRED.md` : ce qui a été / n'a pas été exécuté ; sémantique et pièges ALFRED.
- `03_US_OFFICIAL_MACRO.md` : tableau BLS/BEA/EIA/NY Fed/Trésor/CFTC/Philly/G.17 ; recoupements archive BLS et Philly.
- `04_EU_UK_CANADA.md` : ECB, Eurostat, BoE, BoC, Banque mondiale, FMI, OCDE.
- `05_RELEASE_TIMESTAMPS.md` : quatre horloges ; alignements ; piège CFTC.
- `06_REVISION_VINTAGE_TESTS.md` : tableau de 26 lignes, chemins de révision, conclusion lookahead.
- `07_PIT_READINESS.md` : classes PIT et classement par source.
- `08_CALENDAR_EVENT_VALUES.md` : calendriers sans valeurs ; comparateur TipRanks.
- `09_LICENSE_COST.md` : faits de licence sans conclusion juridique.
- `10_ADJUDICATION.md` : décisions par composant.
- `11_LIMITATIONS.md` : 11 limites déclarées.

Bench (`bench/macro_vintage_v1/`) :
- `README.md` : commande de reproduction, contenu.
- `py/common.py` : utilitaire d'appel + métadonnées. `py/probe_sources.py` : 43 sondes. `py/alfred_test.py` : boucle lookahead. `py/alfred_paths.py` : cas limites, chemins, pièges, alignement BLS. `py/other_sources.py` : BLS, ECB, Eurostat, NY Fed, BoE, BoC, Trésor, CFTC, WB, FMI, OCDE, EIA, BEA. `py/calendars.py` : contenu des calendriers. `py/extra_checks.py` : PIB BEA↔ALFRED, OCDE. `py/licence_facts.py` : extraction de phrases de licence. (Tous lus en entier.)
- `results/alfred_lookahead.json`, `alfred_paths.json`, `extra_checks.json`, `other_sources.json`, `calendars.json`, `probe_sources.json`, `licence_facts.json`, `tipranks_calendar_comparator.json` : lus/recalculés (le JSON de licences en extraits ; `probe_sources.json` en synthèse).
- `raw/` (échantillonnage, non lus intégralement) : `bls_empsit_2009_01_09` (lu : phrase -524 000, tableau 136 597/136 013/135 489, chômage 7,2), `alfred_downloaddata_page` (comptage vintages), `bls_schedule_ics` et `bea_ics_real` (recomptés : 313/119 événements, UID, DTSTAMP, SEQUENCE, heures), `philly_routputMvQd.xlsx` (recalculé) et `philly_ROUTPUTQvQd.xlsx` (structure), `oecd_stes_revisions_USA_PRVM.csv` (recalculé), `ecb_*` (8 fichiers lus), `eurostat_sdmx_updatedAfter` (en-tête), `cftc_socrata_sys`, `cftc_cot_legacy`, `ust_yield_xml_full` (balises `<updated>`), `bea_nokey_head`, `bea_api_nokey`, `bls_v1_recall`, `bls_ces_flat.meta.json`, `fred_api_nokey`, `fred_graph_csv`, `eia_demo` (début), `imf_weo_pages`. Les autres fichiers `raw/*` (pages de licences complètes, calendriers HTML, réponses BoC/FMI/Banque mondiale, `imf_api_dataflow` 444 Ko, `census_econ_indicators_cal`, etc.) : **non lus en entier** (seulement via les résumés JSON).
- Autres : `claude.md` (règles), `SYNTHESE_LANES.md` (lignes sur la lane 010), PR #17 (métadonnées GitHub). Autres lanes : non lues.
