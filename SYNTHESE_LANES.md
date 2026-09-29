# Synthèse des lanes Claude Cloud — AurumShift External Research Lab

Rédigée le 2026-09-29 (UTC), tutoiement, pour quelqu'un qui découvre GitHub.
Sources : les PR GitHub (titres et descriptions), les branches `origin/claude/*` (rapports `00_EXECUTIVE_SUMMARY.md` relus), l'état des sessions Claude Cloud.

> Limite : je n'ai pas le texte exact des missions d'origine (les prompts). Le champ « Mission » ci-dessous est reconstruit à partir des titres de session, des PR et des rapports « scope ». Quand une lane est pilotée par un identifiant de mission cité dans un rapport, je le donne.

---

## 0. Lexique GitHub minimal

| Mot | Ce que ça veut dire pour toi |
|---|---|
| **Dépôt (repo)** | Le dossier partagé : `redguiff-bot/aurumshift-external-research-lab`. |
| **Branche** | Une copie de travail parallèle. Chaque session Claude a écrit sur sa branche `claude/…`. `main` est la version « officielle ». |
| **PR (pull request)** | Une demande « intègre ma branche dans `main` ». On la lit, on la valide ou on la ferme. |
| **Draft (brouillon)** | Une PR marquée « pas prête ». Elle ne peut pas être fusionnée tant que tu n'as pas cliqué **Ready for review**. |
| **Merge** | Intégrer la PR dans `main`. **Merged** = déjà intégrée. **Closed** sans merge = abandonnée. |
| **Fichier `.md`** | Un texte (Markdown). Sur GitHub, ouvre la PR, onglet **Files changed**, et clique sur les fichiers pour les lire. |

**Comment lire une PR :** ouvre le lien → lis la description → onglet **Files changed** → ouvre `reports/NNN_…/00_EXECUTIVE_SUMMARY.md`.
**Comment valider :** bouton **Ready for review** (si draft) puis **Merge pull request**. Ne fusionne pas deux PR d'une même lane sans décider laquelle garder (voir §3).

---

## 1. Vue d'ensemble

### 1.1 Tableau des lanes de recherche (dépôt)

| N° | Lane | Verdict final | Où c'est | État GitHub |
|---|---|---|---|---|
| 001 | Flotte de stratégies adaptatives (paysage) | pas de « drop-in » ; top 5 (River, VW, MABWiser, Optuna, SMPyBandits) | PR [#2](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/2) | **Mergée** dans `main` |
| 002 | Orchestration d'agents, simplification | Absurd = ADAPT, Procrastinate = ADAPT (repli), DBOS/Restate = PARK, Beads = REJECT | PR [#1](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/1) | **Ouverte** (non-draft) |
| 003 | Cell-attention V2 (held-out) | `ADAPTIVE_POLICY_SUPPORTED_FOR_LOCAL_EVALUATION` | PR [#3](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/3) | **Mergée** |
| 004 | Evidence PIT-safe et rejeu | `POSTGRES_NATIVE_PIT_PATTERN_SUPPORTED` | PR [#4](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/4) | **Mergée** |
| 005 | Résilience des flux de données | `MULTIPLE_DATA_SOURCE_CANDIDATES_SUPPORTED` | PR [#5](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/5) | **Mergée** |
| 006 | Coûts d'exécution et transaction | `LIMITED_EXECUTION_MODELS_SUPPORTED` | PR [#7](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/7) | Ouverte (draft) |
| 008 | Capacité de risque et turnover | **Deux études indépendantes avec des verdicts différents** (voir §2.8) | PR [#8](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/8), [#10](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/10) (+ [#6](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/6) mergée, WIP) | 2 PR ouvertes en concurrence |
| 009 | Adjudication de la réplication 008 | `CAPACITY_REPLICATION_INCONCLUSIVE` | PR [#9](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/9) | Ouverte (draft) |
| 010 | Macro : vintages et événements | `LIMITED_MACRO_PIT_SOURCES_SUPPORTED` | PR [#17](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/17) | Ouverte (draft) |
| 011 | Primitives d'alpha | `NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED` (deux runs, même verdict) | PR [#12](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/12), [#22](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/22) | 2 PR ouvertes |
| 012 | Calibration d'incertitude et abstention | `LIMITED_UNCERTAINTY_METHODS_SUPPORTED` (deux runs, même verdict) | PR [#19](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/19), [#24](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/24) | 2 PR ouvertes |
| 013 | Apprentissage en ligne, non-stationnarité | `LIMITED_ONLINE_METHODS_SUPPORTED` (run 1) ; run 2 incomplet | PR [#14](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/14) | 1 PR ; branche `-b` sans PR |
| 014 | Ensemble de stratégies, experts endormis | **Divergent** : `STUDY_INCONCLUSIVE` vs `NO_ROBUST_ENSEMBLE_METHOD` | PR [#15](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/15), [#21](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/21) | 2 PR ouvertes |
| 015 | Découverte de features | **Divergent** : `LIMITED_STABLE_FEATURES_SUPPORTED` vs `NO_STABLE_NEW_FEATURES` | PR [#13](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/13), [#20](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/20) | 2 PR ouvertes |
| 016 | Données alternatives | **Divergent** : `STUDY_INCONCLUSIVE` vs `LIMITED_ALTERNATIVE_DATA_SUPPORTED` | PR [#11](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/11), [#23](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/23) | 2 PR ouvertes |
| 017 | Infra OSS de recherche en trading | `MULTIPLE_OSS_COMPONENTS_SUPPORTED` (deux runs, même verdict) | PR [#16](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/16), [#18](https://github.com/redguiff-bot/aurumshift-external-research-lab/pull/18) | 2 PR ouvertes |
| — | Détection de changement de régime | **Aucun livrable poussé** | branche `claude/regime-changepoint-v1` absente du dépôt | Rien sur GitHub |

Le numéro de rapport est celui du dossier `reports/NNN_…`. Il n'y a pas de rapport 007 dans le dépôt (aucune lane 007 trouvée).

### 1.2 Trois messages à retenir

1. **Ce qui est déjà dans `main` :** 001, 003, 004, 005 et un état intermédiaire (WIP, tuning seul) de 008. Tout le reste est en PR non fusionnée.
2. **Six lanes ont été lancées deux fois** (011, 012, 014, 015, 016, 017), plus 008 et 013. Chaque exécution a écrit dans les mêmes dossiers `reports/NNN_…/`. **Ne fusionne jamais les deux PR d'une même lane** : elles se marchent dessus (conflits) et produisent des rapports contradictoires.
3. **Sur quatre lanes, les deux runs indépendants ne sont pas d'accord** (014, 015, 016, et 008). C'est une information utile, pas un bug : elle mesure la fragilité du verdict.

---

## 2. Détail lane par lane

Légende des étiquettes de preuve (règle du `claude.md`) : PROVEN (test reproductible), OBSERVED (vu directement), DOCUMENTED_CLAIM (dit par la doc), INFERENCE, UNKNOWN.
Vocabulaire des décisions : **ADOPT** (reprendre tel quel), **ADAPT** (reprendre en l'adaptant), **PARK** (mettre de côté), **REJECT**.
Règle commune à toutes les lanes : recherche externe uniquement, aucun code privé AurumShift, aucune intégration. Aucun verdict ne dit qu'une chose est compatible avec AurumShift.

---

### 001 — Flotte de stratégies adaptatives (paysage) — MERGÉE
- **Mission :** `EXTERNAL_RESEARCH_ADAPTIVE_STRATEGY_FLEET_LANDSCAPE_V1`. Cartographier les outils de sélection adaptative (bandits, apprentissage en ligne) capables d'allouer l'attention à une flotte de stratégies.
- **Livré :** rapports 00 à 07 et `bench/`. 23 candidats/techniques, réduits à un top 5 : River, Vowpal Wabbit, MABWiser, Optuna, SMPyBandits. Sources lues, installées et exécutées. Benchmark synthétique (20 graines par politique, balayage de sensibilité, déterminisme vérifié sous `PYTHONHASHSEED`).
- **Résultats clés :**
  - Aucun projet n'est un ordonnanceur d'attention prêt à l'emploi : aucun ADOPT « système complet ».
  - Les politiques gloutonnes (récompense seule) affament 20 à 24 % des cellules et en laissent 72 à 82 % périmées.
  - Les règles qui oublient perdent 72 à 89 % de l'attention pendant les trous.
  - MABWiser échoue au démarrage à froid. SMPyBandits ne s'importe pas avec le SciPy actuel.
  - Une garde de péremption (staleness guard) supprime la famine à regret égal. Code de référence à moi, paramètres in-sample : ça montre une direction, pas un résultat transposable.
- **Réserves :** une seule famille de scénario synthétique ; nombre d'issues ouvertes lu via WebFetch résumé (API GitHub bloquée) ; Optuna, détecteurs de dérive River, partage de features VW, tests C++ de VW non exécutés.
- **GitHub :** PR #2 mergée. Rien à faire.

### 002 — Orchestration d'agents, simplification — OUVERTE
- **Mission :** `EXTERNAL_RESEARCH_AGENT_ORCHESTRATION_SIMPLIFICATION_V1`. Trouver une façon simple (PostgreSQL d'abord) de faire tourner et récupérer des agents après panne.
- **Livré :** `reports/002_agent_orchestration/` (00_SCOPE à 06_FINAL_ADJUDICATION) + scripts d'expérience et logs. 23 candidats criblés, 12 clonés, 5 approfondis : Absurd, DBOS, Procrastinate, Restate, Beads. Tests de crash/reprise sur PostgreSQL 18.6.
- **Verdicts :** Absurd **ADAPT** (rang 1) ; Procrastinate **ADAPT conditionnel / repli** ; DBOS **PARK** ; Restate **PARK** ; Beads **REJECT comme runtime / PARK comme référence** ; River (Go) et pgqueuer **PARK** ; LangGraph **REJECT comme orchestrateur** ; Temporal, Hatchet, Prefect, Airflow, etc. **REJECT** sur critère de simplicité (pas sur des échecs mesurés) ; Celery/Dramatiq/RQ **REJECT**.
- **Constats :** aucun candidat n'est un drop-in ; la récupération après panne demande toujours du « glue » côté opérateur ; at-least-once partout (des effets en double observés dans les 4 runtimes testés), donc l'idempotence des actions d'agent est obligatoire ; le modèle de dépendances/preuves reste du sur-mesure ; recommandation de forme : **COMPOSE** (runtime PG-natif + petite couche custom de dépendances).
- **Réserves :** confiance moyenne sur le classement, faible sur les temps (essais uniques, petite échelle, hôte contaminé deux fois, deux « kills croisés » entre agents parallèles signalés).
- **GitHub :** PR #1 ouverte, **non draft**. À relire puis merger si tu es d'accord.

### 003 — Cell-attention held-out V2 — MERGÉE
- **Mission :** valider en « held-out » (jeu de test jamais vu) les conclusions de la V1 sur l'ordonnancement de l'attention par cellule.
- **Livré :** rapports 00 à 11, `bench/v2/`. 1 200 runs held-out (10 scénarios × 20 graines × 6 politiques), tuning, sensibilité, revue adverse post-hoc. La politique A est un contrat de référence fourni par l'opérateur, pas dérivé de la V1.
- **Résultats :** aucune politique ne domine (contrôle de dominance sur 62 cellules). A équivaut au round-robin sur l'information. B (D-UCB + garde de péremption + backoff sans preuve) bat A sur l'information dans 10/10 scénarios et 200/200 graines, sans coût de couverture notable. River tel quel (C) affame et se fait capturer par les cellules silencieuses ; River + garde (C2) a la meilleure information mais démarre lentement et échoue au retour de dormance ; VW à features partagées (D) est fragile. Isolation held-out PASS (17 contrôles), 18/18 tests, déterminisme 18/18.
- **Verdict :** `ADAPTIVE_POLICY_SUPPORTED_FOR_LOCAL_EVALUATION` (force modérée, modèle synthétique). ADOPT_REFERENCE veut dire seulement « bonne référence externe pour une évaluation locale future ».
- **Réserves :** B, C, D choisis en bord de grille ; A dépend d'un classificateur de cycle de vie défini en V2 ; scénarios adverses post-hoc ; incertitude sur la famille de scénarios non couverte.
- **GitHub :** PR #3 mergée (base = branche V1). Rien à faire.

### 004 — Evidence PIT-safe et rejeu — MERGÉE
- **Mission :** trouver un schéma « point-in-time » (PIT, on ne voit que ce qu'on savait à l'instant T) pour les preuves et leur rejeu.
- **Livré :** `reports/004_pit_safe_evidence_replay/` (00 à 11), `bench/pit_v1/`. PostgreSQL 18.6 jetable, données synthétiques.
- **Résultats :** modèle de référence PG : 25/25 scénarios, 0/60 écart avec l'oracle sur 1 123 580 lignes. Course de commit : `LOOKAHEAD_DETECTED` sans verrou ou avec verrou écrivains seul ; `PREVENTED` avec verrou exclusif écrivains + partagé lecteur. Aucun candidat drop-in : nearform/temporal_tables (course détectée), pg_bitemporal (le temps « asserted » est fourni par l'appelant), Feast (pas de révision). DuckDB/Polars identiques à la référence en range+first ; `ASOF JOIN` interdit.
- **Verdict :** `POSTGRES_NATIVE_PIT_PATTERN_SUPPORTED`.
- **Réserves :** `fsync=off` ; finalité des données OKX/Coinbase non établie ; compression Timescale non testée ; append-only contournable par le propriétaire.
- **GitHub :** PR #4 mergée. Rien à faire.

### 005 — Résilience des flux de données — MERGÉE
- **Mission :** trouver des sources de données de marché gratuites/peu chères, comparer, et évaluer la résilience (repli).
- **Livré :** `reports/005_data_feed_resilience/` (00 à 12), `bench/data_feeds_v1/` (code, captures brutes, citations de conditions d'utilisation).
- **Chiffres :** 68 sources découvertes, 46 exécutées ; 43 gratuites publiques, 4 avec compte (aucune exécutée avec compte) ; candidats : spot crypto 11, dérivés 9, FX 7, matières 9, macro 9 ; PIT_NATIVE observé 0 (+1 documenté, ALFRED, injoignable) ; PIT_ADAPTABLE 34 ; capables de repli 18 ; `ANY_DROP_IN_SOURCE=NO` ; `ANY_SCIENTIFIC_INVALIDATION=NO`.
- **Pièges trouvés :** timestamps Binance Vision spot qui passent de ms à µs en 2025-01 ; barres en formation non signalées ; barres de volume nul remplies après trou ; unités de funding/OI propres à chaque place.
- **Verdict :** `MULTIPLE_DATA_SOURCE_CANDIDATES_SUPPORTED`.
- **Réserves :** Binance principal/fapi (451), Bybit (403), MEXC futures, FRED/ALFRED injoignables depuis le réseau de test : non évalués (pas rejetés) ; un seul point de vue et une seule fenêtre de temps ; licences = citations, pas un avis juridique.
- **GitHub :** PR #5 mergée. Rien à faire.

### 006 — Coûts d'exécution et de transaction — OUVERTE (draft)
- **Mission :** intelligence sur l'exécution et les coûts de transaction (modèles de coûts, carnet d'ordres, latence, comptabilité).
- **Livré :** `reports/006_execution_cost_intelligence/` (00 à 14) et `bench/execution_cost_v1/`. Banc de microstructure synthétique (14 scénarios + expériences : tranchage, concurrence, latence, fragmentation, spread, fills passifs). Capture publique en direct (OKX, Coinbase, Kraken × BTC/ETH/SOL, ~50 min + 8 min de profondeur) + Binance Vision + funding/emprunt/roll OKX. Sonde OSS : 21 candidats inspectés, 9 exécutés en fumée. Contrat comptable (échelle de prix, fill-basis, UNKNOWN ≠ ZERO) avec tests. 51 modèles/composants catalogués, 40 exécutés et falsifiés face à des baselines plus simples.
- **Verdict :** `LIMITED_EXECUTION_MODELS_SUPPORTED`. Soutenus : marche dans le carnet L2, comptabilité du coût de portage, bande de latence, registre sans double comptage. Non soutenus : spreads déduits de l'OHLCV seul, modèles de cotation FX/or/matières, calibration de fill passif et d'impact.
- **Réserves :** aucun fill propre ; une seule journée de capture ; la « vérité » synthétique est construite. Rapports générés depuis `report_templates/` par `build_reports.py`.
- **GitHub :** PR #7 (draft). À lire, puis Ready for review et merge si OK.

### 008 — Capacité de risque et turnover (allocation de slots) — DEUX ÉTUDES EN CONCURRENCE
- **Mission :** comment allouer un nombre limité de positions ouvertes (slots) ; effet du turnover et de la diversification ; sans recommander de valeur de plafond de production.
- **Historique :** la session A a d'abord poussé un état de travail (simulateur, tests, tuning), mergé par erreur dans `main` via PR #6. La session B, voyant la branche occupée, a travaillé sur une autre branche (`claude/festive-archimedes-c3fso6`) et ouvert PR #8. La session A a ensuite refait le travail complet depuis `main` (PR #10).
- **Étude B (PR #8, non-draft) :** `reports/008_risk_capacity_turnover/00–14`, `bench/capacity_v1/` (simulateur déterministe, 12 politiques + oracle non implémentable, 77 tests). Pré-enregistrement avant tout fichier held-out ; held-out exécuté une fois avec paramètres gelés et hachés ; test métamorphique d'absence d'anticipation (12 politiques passent, l'oracle est détecté). Résultats (K=4, 13 scénarios × 20 graines) : FIFO, round-robin, aléatoire et quota égal sont statistiquement indistinguables et ~20 à 28 % sous le classement par score ; l'essentiel du gain vient de deux règles simples (filtre d'edge net +0,16 ; classement edge net par slot-heure attendu +0,44 bps par slot-heure vs FIFO) ; les méthodes complexes ne battent la meilleure simple que de +0,06 (marge pré-enregistrée : 0,25). Verdict **`MULTIPLE_CAPACITY_METHODS_SUPPORTED`**.
- **Étude A (PR #10, draft) :** `reports/008_risk_capacity_turnover/00–13`, `bench/capacity_v1/` (29 politiques, pré-enregistrement v2 commité avant le held-out, script de verdict, tests de fuite, sonde OSS). Résultat : **`CAPACITY_ALLOCATION_REFERENCE_SUPPORTED`** (référence `COMPOSED`), mais la marge sur le simple classement par EV net est mince (+0,023 vs barre 0,02) ; avec une marge d'équivalence de 0,03 on aurait `MULTIPLE_CAPACITY_METHODS_SUPPORTED`. FIFO nettement pire dans 13/15 familles held-out. Le run 1 a été écarté avant tout held-out (biais de démarrage de covariance, shrinkage trop fort, normaliseur qui explose) et archivé dans `results/superseded_run1/`.
- **Réserves communes :** synthétique ; scores calibrés par construction ; l'edge s'accumule linéairement avec le temps de détention ; mondes held-out de la même famille de générateur.
- **Conflit important :** A et B écrivent tous deux dans `reports/008_risk_capacity_turnover/` et `bench/capacity_v1/` (chemins différents en partie : B utilise `src/ tests/ configs/`, A utilise `py/`), donc un merge des deux produira des conflits et deux « vérités ». Voir lane 009.
- **GitHub :** choisis une PR, ferme l'autre sans merger. L'adjudication 009 recommande de corriger #8 avant merge (documentation/provenance).

### 009 — Adjudication de réplication des deux études de capacité — OUVERTE (draft)
- **Mission :** adjudication en lecture seule des deux études indépendantes 008 (A et B), sans les modifier.
- **Livré :** `reports/009_capacity_replication_adjudication/00–10` + `evidence/` (script de sonde et sortie).
- **Résultats :** l'étude A telle que mergée (PR #6) n'est qu'un instantané tuning-only d'un run que ses propres auteurs ont retiré ; le normaliseur qui explose est confirmé dans les données mergées (le scénario S12 fournit 48 % de l'objectif poolé de tuning). Deux niveaux de preuve jamais mélangés : « strict » (A mergée) et « supplémentaire » (run 2 de A, split de validation). Au niveau supplémentaire : R1, R2, R3, R6, R7, R9 répliquent ; R4, R5, R10 partiellement ; R8 non testé côté A ; aucune question centrale n'est contredite. Quatre désaccords secondaires (signe de la préemption, FIFO vs aléatoire, spam, résidu à K=10) sont attribués aux hypothèses de monde/coût, dont deux reproduits en exécutant le simulateur A sous hypothèses modifiées. Disposition de la PR #8 : `REQUIRES_CORRECTION_BEFORE_MERGE` (documentation et provenance, résultats sains, 77/77 tests).
- **Verdict :** `CAPACITY_REPLICATION_INCONCLUSIVE` ; `CAP_CHANGE_AUTHORIZED=FALSE` ; `LOCAL_INTEGRATION_AUTHORIZED=FALSE`.
- **À faire (dans la PR) :** relancer `evidence/adjudication_probe.py` sur des copies fraîches des deux corpus ; ré-adjuger quand le held-out de A sera disponible (il l'est maintenant via PR #10, donc ré-adjudication à demander).
- **GitHub :** PR #9 (draft). À lire avant de décider entre #8 et #10.

### 010 — Macro : vintages et données d'événements — OUVERTE (draft)
- **Mission :** `AURUMSHIFT_EXTERNAL_MACRO_VINTAGE_AND_EVENT_DATA_V1`. Débloquer le point resté ouvert après 005 (FRED/ALFRED injoignables) : sources macro avec vintages (valeur telle que connue à la date T) et horodatages de publication.
- **Livré :** `reports/010_macro_vintage_event_data/00–11`, `bench/macro_vintage_v1/`.
- **Résultats (OBSERVED, appels réels) :**
  - ALFRED répond sans clé via son CSV web et **prouve la sémantique as-of** (418 à 1 223 dates de vintage par série ; valeur à T = dernier vintage ≤ T ; 404 avant le premier vintage). L'API FRED à clé n'a pas été exécutée (pas de clé) ; `fredgraph.csv` ignore `vintage_date`.
  - **Le lookahead des valeurs « dernière révision » est prouvé** : payrolls déc. 2008 connu 135 489 (−524 k) contre 134 847 aujourd'hui ; croissance du PIB réel T4-2008 : −0,96 % au premier print contre −2,19 % ; production industrielle −2,00 % contre −2,82 % ; chômage 7,2 contre 7,3. Les séries jamais révisées (CPI NSA, fed funds, WTI) donnent zéro écart.
  - Corroboration indépendante : le Real-Time Data Set de la Fed de Philadelphie (731 vintages mensuels) reproduit exactement les valeurs de PIB d'ALFRED ; l'OCDE publie un flux natif de révisions (`DF_STES_REVISIONS`, 79 éditions).
  - Les dates de vintage ALFRED coïncident avec les calendriers officiels (60/60 événements BLS, 11/11 BEA), soit une date de publication ; l'heure vient des calendriers ICS BLS/BEA (08:30 ET). Seul le CFTC donne l'instant réel (`:created_at`, lignes récentes).
  - Hors US : tout est « dernière valeur seulement » (BCE, Eurostat, BoE, BoC, Banque mondiale, FMI).
  - Les calendriers officiels donnent le calendrier seul, pas de consensus ; le seul calendrier avec actual/estimate/previous est un agrégateur non officiel.
- **Bloc final :** 28 sources découvertes (+3 variantes à clé), 25 exécutées ; PIT_NATIVE exécuté 3 (ALFRED web CSV, RTDSM Philly Fed, OCDE) ; PIT_ADAPTABLE 6 ; `DROP_IN_MACRO_SOURCE=NO`.
- **Verdict :** `LIMITED_MACRO_PIT_SOURCES_SUPPORTED` (pas « reference stack » car : granularité jour/mois, endpoint web non documenté, API à clé non exécutée, presque rien hors US).
- **Réserves :** quotas anonymes BLS/EIA épuisés par la sortie réseau partagée ; formulaire de téléchargement en masse ALFRED en erreur HTTP 500.
- **Doublon de session :** deux sessions « Macroeconomic vintage » (dont une sur `claude/tender-lovelace-h86kec`) ; une seule branche `claude/macro-vintage-event-data-v1` existe sur le dépôt, la seconde n'y a rien poussé que je puisse voir.
- **GitHub :** PR #17 (draft). Aucun conflit avec d'autres PR.

### 011 — Primitives d'alpha — DEUX RUNS, MÊME VERDICT
- **Mission :** découvrir et falsifier des « primitives d'alpha » (signaux élémentaires) de façon externe, avec règle de support nette de coûts pré-déclarée.
- **Run 1 (PR #12, branche `alpha-primitives-v1`) :** 34 primitives découvertes (18 familles), 15 exécutées avec contrats commités avant le run complet. Univers : 10 majeures Binance USD-M en horaire, 2023-01 à 2026-08 (DEV 2023–24 / TEST 2025–26), plus univers de holdout à 6 actifs et Coinbase spot (test de mauvaise place). Autres sources : Deribit DVOL, funding Hyperliquid. Sécurité vers l'avant : 15/15 passent un test de troncature, un contrôle volontairement fuyant échoue ; un signal planté est détecté ; 150 signaux placebo donnent des t-stats calibrés proches de N(0,1). Meilleur Sharpe brut primaire +0,71 (t 1,60), meilleur net +0,24 (t 0,44). Six primitives nettes négatives avec confiance (turnover + coûts). Certaines spécifications non primaires à gros t brut (saisonnalité par heure en coupe transversale) ont un coût de rentabilité ≤ 0,65× des coûts supposés : pistes dominées par les coûts. Verdict `NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED`, `ANY_DROP_IN_STRATEGY=FALSE`, `LOCAL_INTEGRATION_AUTHORIZED=FALSE`.
- **Run 2 (PR #22, branche `amazing-pasteur-o4csin`) :** 43 primitives découvertes, 15 exécutées ; 9 strictement FORWARD_SAFE exécutées (+6 avec estampille de réception) ; 0 lookahead parmi les exécutées ; 4 candidats non redondants (P05, P06, P07, P14 — information brute seulement, **pas** nets positifs) ; 4 « régime-dépendants » (P02, P03, P08, P12 — drapeaux statistiques sur 45 tests, ~2 attendus par hasard) ; `NET_POSITIVE_EXTERNAL_CANDIDATES=0`. Même verdict.
- **Réserves (run 1) :** faible puissance (un vrai Sharpe net < ≈ 1 est indétectable) ; coûts génériques ; biais de survie dans l'univers ; un run de fumée sur 3 actifs lu avant le run complet (aucune définition, signe, horizon ou mode modifié ensuite) ; vérification de sources du paysage faite par sous-agents.
- **Accord :** les deux runs concluent qu'aucune primitive n'est nette positive. Les comptes diffèrent (34 vs 43 découvertes ; 12 vs 9 FORWARD_SAFE) mais pas la conclusion.
- **GitHub :** les deux PR touchent `reports/011_alpha_primitives/` et `bench/alpha_primitives_v1/`. Garde-en une (la #12 est plus détaillée dans sa description ; la #22 est le run indépendant de confirmation) et ferme l'autre, ou merge l'une et archive l'autre.

### 012 — Calibration d'incertitude et abstention — DEUX RUNS, MÊME VERDICT
- **Mission :** que valent la calibration, l'abstention et le conformal quand la distribution change ?
- **Run 1 (PR #19, branche `uncertainty-calibration-v1`, rapports 00–10, `bench/uncertainty_v1/`) :** 31 méthodes découvertes, 26 exécutées. Données : mondes synthétiques contrôlés (20 graines shift/taxonomie, 8 en ligne/conformal) + données publiques (ELEC2 dérivante réelle, cancer du sein, logements Californie).
  - Stationnaire : un GBM sur-confiant a ECE 0,118 et taux de fausse confiance 0,119 ; Platt/température/beta ramènent l'ECE à 0,022 (oracle 0,017) ; isotonique n'apporte rien à n=3000.
  - **Ne survit pas au shift :** la calibration tient sur 2 shifts sur 6 (features, features manquantes) ; échoue sur saut de volatilité (ECE 0,141), transition de régime (0,172), features périmées (0,076), changement de place (0,068). Sur ELEC2 réel, un calibrateur ajusté sur la fenêtre de calibration a **dégradé** l'ECE de LR (0,103 → 0,15–0,17).
  - Un modèle peut rester confiant en ayant tort (AUROC de la confiance 0,39/0,43 sous shift de features et saut de vol) ; le taux de fausse confiance monte de 2 à 4,5× ; les transitions de régime sont invisibles aux détecteurs sans étiquette (AUROC 0,50).
  - Abstention : τ=0,6 (dérivé d'un gain ±1, coût 0,2, sans tuning) écarte 69 % des lignes, baisse le risque sélectif de 0,318 à 0,256, évite 45 % des mauvaises décisions et garde 75 % des bonnes ; sans effet sous concept shift (0,486 → 0,482).
  - Recalibration en ligne : utile sous dérive **si et seulement si PIT-safe** (Platt à fenêtre glissante : ECE régime abrupt 0,100 → 0,017 ; pire tranche 0,182 → 0,104 ; expanding-window faible ; pente instable, sd jusqu'à 0,78 sur ELEC2-LR).
  - Conformal : le split CP est invalide sous dérive (couverture 0,72–0,73 vs 0,80 ; covariate shift logements 0,498 ; régression vol-jump 0,512) ; ACI (y compris avec retour retardé) et CP pondéré par récence tiennent la couverture marginale partout ; mais la couverture marginale n'est pas la fiabilité de décision (précision des singletons 0,65–0,73 pour « 80 % » de couverture).
  - Séparation des causes : DATA_GAP 0,97 et OOD 0,98 de rappel ; NO_SIGNAL 0,36 ; MODEL_UNCERTAINTY 0,15.
  - Références : simple = Platt sur bloc de calibration isolé + seuil de confiance dérivé du coût + drapeaux manquant/périmé ; en ligne = Platt glissant (labels retardés, PIT-assertion) + ACI à retour retardé + moniteur de calibration.
  - Deux erreurs corrigées en cours de route (fuite dans la définition du label ELEC2 ; calibrateur ajusté par erreur sur les lignes d'entraînement dans le code en ligne), consignées dans le rapport 08.
  - Verdict : `LIMITED_UNCERTAINTY_METHODS_SUPPORTED`.
- **Run 2 (PR #24, branche `uncertainty-calibration-v1-b`) :** étude indépendante, verdict identique `LIMITED_UNCERTAINTY_METHODS_SUPPORTED`. 11 fichiers de rapport. (Je n'ai pas relu ses tableaux en détail : à faire avant de choisir laquelle merger.)
- **GitHub :** #19 et #24 écrivent dans les mêmes dossiers. Garde-en une. La session correspondante (`01UzaERE…`) était en `REQUIRES_ACTION` à un moment donné mais est maintenant passée en `IDLE / review_ready`.

### 013 — Apprentissage en ligne pour marchés non stationnaires — 1 RUN COMPLET, 1 INCOMPLET
- **Mission :** comparer des méthodes d'apprentissage en ligne légères sous non-stationnarité, sans données de marché.
- **Run 1 (PR #14, branche `online-learning-v1`, rapports 00–10, `bench/online_learning_v1/`) :** 15 algorithmes candidats (River 0.26.1 + petits wrappers numpy RLS/Kalman/Platt/reset/banque) + 3 baselines (gelé, batch expansif, refit glissant borné). 10 scénarios de dérive × 2 pistes × 15 graines held-out (3 750 runs), hyperparamètres gelés sur des graines de tuning séparées, run de sensibilité à faible SNR, suite rejeu/checkpoint/fuite avec contrôle négatif. Règles de décision pré-enregistrées dans `02_PROTOCOL.md` avant le held-out.
  - Seuls le **RLS avec oubli** (régression, 0,85× le refit glissant) et le **SGD logistique + banque de dérive** (classification, 0,88×) méritent leur place ; aucune méthode ne passe sur les deux pistes. Arbres/ARF/ADWIN-bagging 2,6 à 5,2× pires qu'un refit glissant borné. 25/25 entrées rejouables bit à bit, restaurables depuis checkpoint pickle, sans fuite (une seule plateforme).
  - Verdict : `LIMITED_ONLINE_METHODS_SUPPORTED`.
  - Réserves : synthétique ; plusieurs valeurs tunées en bord de grille ; les chiffres absolus ne se transposent pas aux marchés réels.
- **Run 2 (branche `online-learning-v1-b`, sans PR) :** seulement le banc (harnais, scripts) et les résultats de tuning (`tune.json`, graines de tuning uniquement). **Pas de held-out, pas de rapports, pas de PR.** Lane incomplète pour ce run.
- **GitHub :** PR #14 uniquement. Le run 2 n'a rien à merger.

### 014 — Ensemble de stratégies, experts endormis — DEUX RUNS, VERDICTS DIFFÉRENTS
- **Mission :** combiner en ligne des familles de stratégies hétérogènes dont seules certaines sont valides selon l'état du marché (experts endormis/spécialistes).
- **Run 1 (PR #15, branche `strategy-ensemble-experts-v1`, rapports 00–10, `bench/ensemble_v1/`) :** 13 familles découvertes ; contrôle de sources OSS (river/mabwiser/contextualbandits) ; simulateur numpy seul (12 scénarios cœur + 1 stress), 20 lignes de méthode, tests unitaires, pré-enregistrement commité avant tuning, tuning (graines 0–5), 22 880 runs held-out, sensibilité, extras bruit d'étiquette et famine.
  - Traiter la preuve manquante comme pire récompense coûte 2,0 à 3,3× de regret (plus que tout choix d'algorithme) ; gel + prior neutre = décisif. WTA/EWMA sont les meilleures baselines (11,7/11,8 ×1e-3) ; Equal 63, Static 25, bandits 18–59. Les méthodes à mise à jour endormie sont plus robustes aux trous, à l'abstention informative et aux spécialistes malchanceux au départ, mais ne franchissent pas la marge pré-enregistrée de 10 % sans étiquette de régime ; Hedge « dés-oublieur » lent après changement de leader. Mélange contextuel : ~95 % de précision d'étiquette requise pour battre la baseline de 10 %. Pondération par diversité et planchers/plafonds : aucun bénéfice sous cet objectif neutre au risque.
  - Verdict : **`STUDY_INCONCLUSIVE`**. Deux définitions de portes (G4a, G4b) étaient mal spécifiées ; c'est déclaré dans le rapport 08 et l'analyse amendée post-hoc est étiquetée comme telle ; les deux voies donnent le même verdict.
- **Run 2 (PR #21, branche `strategy-ensemble-experts-v1-b`, rapports 00–10 en français) :** 30 graines held-out, 11 scénarios, 17 méthodes exécutées + 6 ablations + sonde OSS de `river.ensemble.EWARegressor`. Verdict : **`NO_ROBUST_ENSEMBLE_METHOD`** (règles pré-enregistrées, appliquées sans modification).
  - Sémantique des absences PROVEN : ne jamais mettre à jour un expert endormi ni un expert dont le feedback manque ; traiter « inactif » comme négatif fait passer EWMA de 0,55 à 1,16 et le Hedge endormi de 0,73 à 1,35 (nrm, 1 = poids égaux).
  - Meilleures moyennes : EG (0,487) et Fixed-share endormi (0,494), devant EWMA (0,548), Hedge endormi simple (0,725), poids statiques (0,923) ; mais l'avantage d'EG sur EWMA (−0,061) est à peine au-dessus de la marge δ = 0,05 et EG est significativement pire qu'EWMA dans au moins un scénario.
  - Famine : seuls Fixed-share et MPP passent le test « nouvel expert » ; le spécialiste de régime rare est laissé à 0,16–0,32 de part (oracle 0,92) sauf par le mélange contextuel (0,63), qui échoue ailleurs. Diversité : le rabais de redondance réduit la masse du cluster corrélé mais coûte +0,19 en moyenne. Bandits : 3,4 à 3,8× pires que les poids égaux. `river.ensemble.EWARegressor` n'a pas de notion d'expert endormi : 1,5 à 4× pire que les poids égaux.
  - Bloc final : `STARVATION_CONTROLLED=FALSE`, `COMPLEXITY_JUSTIFIED=FALSE`, `MISSING_EVIDENCE_HANDLED=TRUE`.
- **Lecture croisée :** les deux runs s'accordent sur le fond (aucune méthode ne passe les portes strictes ; gel des absences décisif ; complexité non justifiée) mais l'étiquette diffère (`INCONCLUSIVE` vs `NO_ROBUST`). Attention : un chiffre de performance n'est pas comparable d'un run à l'autre (métriques différentes : regret ×1e-3 vs nrm).
- **GitHub :** #15 et #21 se recouvrent (`reports/014_strategy_ensemble/`, `bench/ensemble_v1/`). Garde-en une ; l'autre sert de contre-vérification.

### 015 — Découverte de features — DEUX RUNS, VERDICTS DIFFÉRENTS
- **Mission :** découverte automatique de features de marché compactes et interprétables (symbolique, parcimonie, interactions, frontières causales) sans surajustement silencieux.
- **Run 1 (PR #13, branche `feature-discovery-v1`) :** 9 marchés crypto spot 1h réels (4 pour la découverte, 5 jamais vus), splits temporels stricts + embargo, protocole pré-enregistré commité avant les runs, formules gelées (digest), held-out lu **une seule fois** (verrou). Méthodes : MI/CMI, stability selection, lasso, interactions exhaustives, GP (gplearn), orthogonalisation, Cochran-Q / ICP-lite. Baselines : ridge brut, lasso, importance d'arbre, permutation. Arène synthétique à vérité connue (40+40 réplications) : FWER sous H0 = 0/40.
  - Bloc final : `FEATURES_DISCOVERED=2`, `FEATURES_HELDOUT_STABLE=1`, `SYMBOLIC_EXPRESSIONS_STABLE=0`, `NONREDUNDANT_FEATURES=0`, `CAUSAL_IDENTIFIED_COUNT=0`, `COMPLEXITY_JUSTIFIED=NO`. Verdict : `LIMITED_STABLE_FEATURES_SUPPORTED`.
  - Réserve du rapport : la seule formule stable (`ret_72h·sgn(mag_168)` sur y_vol, IC held-out +0,104) est redondante avec les baselines (corrélation partielle −0,035) : lecture pratique, rien à ajouter aux primitives brutes. Déviations du protocole (toutes avant le held-out) : `02_PROTOCOL.md §12`. Références citées de mémoire.
- **Run 2 (PR #20, branche `feature-discovery-v1-b`) :** 80 candidats distincts avant validation sur 5 graines ; 0 stable en held-out ; 0 expression symbolique stable ; 0 non redondante ; 0 causale ; `COMPLEXITY_JUSTIFIED=NO`. Verdict : **`NO_STABLE_NEW_FEATURES`** (force MODÉRÉE-FAIBLE : une classe d'actifs, ~2,3 ans, une définition de cible). Le rapport signale explicitement l'existence du run 1, non lu ni réutilisé (indépendance).
  - **Attention :** cette branche contient aussi des fichiers `.whl` (paquets Python : numpy, scipy, scikit-learn, gplearn, etc.) à sa racine. Ce n'est pas du contenu de recherche ; à retirer avant tout merge.
- **Lecture croisée :** un seul candidat « stable » côté run 1, redondant ; zéro côté run 2. Conclusion pratique commune : n'ajoute rien aux primitives brutes.
- **GitHub :** #13 et #20 se recouvrent. Garde-en une. Si tu prends #20, fais retirer les `.whl` avant merge.

### 016 — Données alternatives — DEUX RUNS, VERDICTS DIFFÉRENTS
- **Mission :** découvrir et tester des sources de données alternatives gratuites/publiques : apportent-elles de l'information incrémentale au-delà de prix/volume/volatilité ?
- **Run 1 (PR #11, branche `alternative-data-v1`) :** 39 sources catalogues sur 16 catégories, 29 exécutées (sondes en direct et/ou historique, sans clé). 44 séries de features testées pour l'information incrémentale (+funding/OI pour BTC) : protocole walk-forward pré-enregistré, Clark-West + Newey-West + BH-FDR, 132 tests, simulation puissance/MDE. Fuite : délais de publication prudents, comparaison au décalage naïf, test de re-collecte pour révisions ; classification PIT par source. Bloc final : `SOURCES_DISCOVERED=39`, `SOURCES_EXECUTED=29`, `FREE_SOURCES=37`, `PIT_NATIVE=9`, `PIT_ADAPTABLE=23`, `INCREMENTAL_INFORMATION_CANDIDATES=0`, `PRICE_DERIVATIVE_ONLY_REJECTS=9`. Verdict : `STUDY_INCONCLUSIVE` (0 candidat, mais faible puissance : partial R² minimal détectable ≈ 3–4 % à 1 jour ; plusieurs catégories non testables avec l'historique gratuit ; presque tout l'historique est LOOKAHEAD_RISK).
- **Run 2 (PR #23, branche `alternative-data-v1-b`) :** 69 sources découvertes, 47 exécutées ; 62 gratuites (54 sans clé, 8 avec clé gratuite) ; PIT_NATIVE 7 (+1 documenté injoignable : FRED/ALFRED) ; PIT_ADAPTABLE 6 ; LOOKAHEAD_RISK 17 ; SNAPSHOT_ONLY 17. **2 candidats d'information incrémentale** : la surprise des stocks hebdomadaires de pétrole brut EIA (économie réelle) et le DVOL de Deribit (volatilité implicite d'options, dérivé du marché) ; 12 rejets « dérivé de prix seulement » (7 sources). Verdict : `LIMITED_ALTERNATIVE_DATA_SUPPORTED`.
- **Lecture croisée :** les deux runs s'accordent que la plupart des sources ne sont pas utilisables sans risque de lookahead et que le prix explique l'essentiel. Le run 2 a couvert plus de sources et trouve 2 pistes (dont DVOL, qui est lui-même un produit du marché). La différence de verdict tient à l'univers testé et à la puissance, pas à un désaccord sur un fait.
- **GitHub :** #11 et #23 se recouvrent. Garde la #23 si tu veux le périmètre le plus large ; la #11 est plus prudente.

### 017 — Infrastructure OSS pour la recherche en trading — DEUX RUNS, MÊME VERDICT
- **Mission :** trouver des composants OSS réutilisables pour la plomberie de recherche (carnets d'ordres, rejeu, moteurs de backtest, causalité, indicateurs, statistiques en ligne, portefeuille/risque, calendriers, qualité de données, stockage, collecteurs, modèles de coûts), sans code AurumShift.
- **Run 1 (PR #16, branche `oss-trading-research-infra-v1`) :** 54 projets découverts, 32 exécutés (31 avec microtest terminé, 1 partiel : databento-dbn), 16 microtests. Adjudication : ADOPT_REFERENCE 9, ADAPT_CANDIDATE 5, PARK 32, REJECT 8. Lacunes qu'aucun candidat OSS ne couvre : magasin PIT append-only avec heure de réception côté serveur, estimation de coûts calibrée sur données, indicateurs causaux par construction. Découvertes notables : `ta` et `pandas-ta` fuient silencieusement le futur (5/91 et 9/271 colonnes) ; les moteurs de backtest ne collent au PnL manuel que si la convention de fill est comprise ; ArcticDB est un second datastore sous BSL. Verdict : `MULTIPLE_OSS_COMPONENTS_SUPPORTED`.
- **Run 2 (PR #18, branche `amazing-wozniak-bwjdfp`) :** 67 projets criblés, 41 avec microtest comportemental exécuté, 3 install/import seuls, 23 criblés sur métadonnées ; ADOPT_REFERENCE 14, ADAPT 10, PARK 36, REJECT 7 ; « drop-in » étroits au niveau bibliothèque : exchange_calendars, river, hdrhistogram/ddsketch, TA-Lib, pyarrow, DuckDB/polars en calcul seul (pas de service, licence permissive). Même verdict.
- **Réserves :** recherche GitHub bloquée dans le bac à sable (découverte non exhaustive) ; données synthétiques ; compatibilité AurumShift UNKNOWN par conception.
- **GitHub :** #16 et #18 se recouvrent (`reports/017_oss_trading_infra/`, `bench/oss_trading_infra_v1/`). La #18 est plus large (67 vs 54, 41 vs 32 exécutés). Garde-en une.

### — Détection de changement de régime — SANS LIVRABLE
- **Mission :** algorithmes de détection de changement de régime (changepoint).
- **État :** session `Regime changepoint detection algorithms`, branche prévue `claude/regime-changepoint-v1`, dernier résumé de tâche : « repo setup, data fetched, building regime-change detector ». La session est **déconnectée** depuis 14:21 UTC. **Aucune branche, aucune PR, aucun rapport** sur GitHub.
- **Ce que ça veut dire :** le travail n'a pas abouti. À relancer si tu veux cette lane.

---

## 3. Doublons et conflits : ce que tu dois trancher

| Lane | PR concurrentes | Recouvrement | Ce que je te recommande |
|---|---|---|---|
| 008 | #8 (non draft) vs #10 (draft) | Même dossier de rapport, deux implémentations, verdicts différents | Lire #9 (adjudication), corriger #8 comme demandé (provenance), puis n'en merger qu'une |
| 011 | #12 vs #22 | Mêmes dossiers, même verdict | Une seule |
| 012 | #19 vs #24 | Mêmes dossiers, même verdict | Une seule |
| 014 | #15 vs #21 | Mêmes dossiers, verdicts proches mais étiquettes différentes | Une seule, en citant l'autre comme contre-vérification |
| 015 | #13 vs #20 | Mêmes dossiers, verdicts différents | Une seule ; retirer les `.whl` si #20 |
| 016 | #11 vs #23 | Mêmes dossiers, verdicts différents | Une seule |
| 017 | #16 vs #18 | Mêmes dossiers, même verdict | Une seule |
| 013 | #14 seule | Branche `-b` sans PR, tuning seul | Rien à merger côté `-b` |

**Astuce :** tu peux garder la deuxième étude sans merger. Ferme la PR (bouton **Close pull request**), la branche reste consultable.

---

## 4. Autres sessions Claude Cloud du jour (hors dépôt de recherche)

Je n'ai accès qu'aux titres, dates et statuts de ces sessions : **pas à leurs résultats**. Aucune ne pousse dans ce dépôt.

| Session | Statut | Dernière activité (UTC) |
|---|---|---|
| Aurumshift PIT Cell canonical promotion v1 | Inactive, **en attente d'une entrée de ta part** : « lock_timeout test + position status + T0 snapshot » | 19:56 |
| AurumShift pré-reboot autostart and recovery audit | Archivée | 14:33 |
| AURUMSHIFT_CELL_RUNTIME_PRODUCER_CODE_CLOSURE_V1 | Archivée | 14:33 |
| AurumShift Cell identity authority contract closure | Archivée | 12:35 |
| Ram saturée | Archivée | 12:42 |
| aurumshift logical backup and restore proof | Archivée | 11:06 |
| AurumShift git local remote rationalization map | Archivée | 11:06 |
| Aurumshift paper decision to outcome causal closure v1 | Archivée | 11:36 |
| AurumShift cell attention external V2 local shadow evaluation | Archivée | 09:46 |
| AurumShift backup Barman stale chain forensic | Archivée | 08:58 |
| fedora-velvet-mist | Archivée | 08:26 |
| Token Optimizer Claude Code pilot | Archivée | 06:01 |
| AURUMSHIFT_4388 palette et hiérarchie visuelle | Archivée | 05:49 |
| AURUMSHIFT Dev Fabric runtime convergence | Archivée | 09-28 18:15 |
| Aurumshift cell identity hardening blockers | Archivée | 09-28 15:42 |
| AurumShift raw market observation contract design | Archivée | 09-28 16:17 |
| Dev Fabric WIP convergence adjudication | Archivée | 09-28 11:31 |
| AurumShift crypto 24h market neutral walkforward | Archivée | 09-28 09:12 |
| Permission allow rule settings.local.json | Archivée | 09-28 09:12 |
| Sprint en file local | Archivée | 09-28 09:13 |
| AurumShift global business acceleration and integration prep v2 | Archivée | 09-28 09:13 |
| AurumShift business roadmap mega acceleration v1 | Archivée | 09-28 06:44 |
| AurumShift PAPER economic truth overnight closure | Archivée | 09-27 17:24 |
| Grove agentshell binding closure v1 | Archivée | 09-26 23:41 |

La session « PIT Cell canonical promotion » est la seule active et bloquée : elle travaille sur ton code local (canal `bridge`), pas sur ce dépôt.

---

## 5. Ce qui reste à faire, par ordre de priorité

1. **Décider** pour 008 (#8 ou #10), en lisant #9.
2. **Choisir une PR** parmi les paires 011, 012, 014, 015, 016, 017 (voir §3).
3. **Fusionner** les PR sans concurrent que tu valides : #1 (002), #7 (006), #9 (009), #14 (013), #17 (010).
4. **Répondre** à la session « PIT Cell canonical promotion » (bloquée sur une entrée de ta part).
5. **Décider** si tu relances « Regime changepoint » (rien n'a été livré) et si tu complètes le run 2 de « Online learning » (tuning seul).
6. **Faire relire l'adjudication 009** une fois choisie la version de 008, pour qu'elle reflète le held-out de l'étude A.

---

## 6. Limites de cette synthèse

- Missions reconstruites, pas citées (voir en tête).
- Pour la lane 012 run 2 et les lanes 017 run 1 vs run 2, j'ai lu les résumés exécutifs et les descriptions de PR, pas chaque rapport en détail.
- Rien n'a été relancé ni vérifié par moi : les chiffres viennent des rapports et des PR, pas de mes propres exécutions.
- Les verdicts sont des étiquettes de recherche externe, jamais une preuve de compatibilité avec AurumShift.
