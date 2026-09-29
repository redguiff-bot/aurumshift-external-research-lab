# Analyse approfondie — Lane 002 : Orchestration d'agents, simplification (PR #1 ouverte)

> Auteur : analyste de recherche (Claude), pour Jean-François.
> Date de l'analyse : 2026-09-29. Tout ce qui suit est fait à partir de la lecture de la branche `origin/claude/funny-hopper-3paobd`, sans checkout ni modification.
> Convention de lecture : quand je cite un chiffre, le chemin du fichier source est entre parenthèses. « Le rapport affirme » = ce que dit le texte des rapports ; « Vérifié » = j'ai recalculé le chiffre à partir des fichiers bruts du dépôt ; « non vérifiable » = la pièce brute n'est pas dans le dépôt.
> Marqueurs de vérification : ✔ vérifié / ✘ écart / ? non vérifiable.

---

## 0. Fiche d'identité

| Élément | Valeur | Source |
|---|---|---|
| Lane | 002 — Orchestration d'agents, simplification (mission `EXTERNAL_RESEARCH_AGENT_ORCHESTRATION_SIMPLIFICATION_V1`) | `reports/002_agent_orchestration/00_SCOPE.md` |
| Branche | `claude/funny-hopper-3paobd` (tête `56f36cd`, un « Merge branch 'main' » du 2026-09-29) | `git log` |
| Pull request | n°1 « Research 002: agent orchestration simplification », **ouverte, non brouillon, non fusionnée**, créée 2026-09-29 06:56:32 UTC, mise à jour 13:34:10 UTC ; 8 commits, 107 fichiers modifiés, +1643 / −1 lignes (GitHub) | API GitHub PR #1 |
| Commits propres à la lane (7) | `443b9cc` scripts d'expérience (06:56:24), `93a6b5a` et `ca4cca3` mises à jour scripts/logs, `a50d929` logs DBOS, `7e16d43` logs Absurd, `a9b3b29` logs Beads (07:10:03), `c9535e6` « Add agent orchestration research reports 00-06 » (07:17:45). Tous le 2026-09-29, auteur « Claude » | `git log -- reports/002_agent_orchestration` |
| Fichiers dans `reports/002_agent_orchestration/` | **106 fichiers, 111 168 octets (≈ 109 Ko)** : 7 rapports `.md` (55 436 octets), 22 scripts `.sh`, 8 `.py`, 1 `.mjs`, 2 `.toml`, 51 `.txt`, 14 `.out`, 1 fichier `manual_restart_ts` | `git ls-tree -r -l` |
| Fichier hors dossier de la lane modifié par la PR | `.gitignore` (le 107e fichier de la PR) | `git diff --name-only` |
| Verdict final | **Pas de candidat « clé en main ».** Absurd = **ADAPT** (rang 1), Procrastinate = **ADAPT conditionnel / repli** (rang 2), DBOS Transact = **PARK**, Restate = **PARK**, Beads = **REJECT comme moteur d'exécution / PARK comme référence**. Recommandation de forme : **COMPOSE** (un moteur PostgreSQL existant + une petite couche « dépendances/preuves » maison) | `06_FINAL_ADJUDICATION.md` §2–3 |
| Force du verdict | **Moyenne** pour le classement des rangs 1 à 4 (le rapport le dit : « Medium confidence »), **faible** pour les comparaisons de temps (essais uniques, machine partagée deux fois « contaminée », échelle minuscule, mécanisme de dépendance différent selon le système). Je la juge cohérente avec les preuves, avec des réserves listées en §7 | `06` §5 |

Ce que la lane **n'est pas** : ce n'est pas un benchmark de performance, ni une revue de sécurité, ni une conception pour AurumShift (le dépôt ne contient aucun code privé AurumShift).

Glossaire minimal pour la suite (première occurrence, en langage simple) :
- **Orchestrateur / moteur d'exécution durable** : un logiciel qui distribue des tâches à des « ouvriers » (workers) et retient leur état, pour qu'une tâche interrompue puisse reprendre.
- **Lease (bail)** : un « droit de tenir la tâche pendant N secondes ». Si l'ouvrier ne renouvelle pas son bail, un autre peut reprendre la tâche.
- **Heartbeat (battement de cœur)** : signal périodique qu'envoie un ouvrier pour dire « je suis vivant » et prolonger son bail.
- **Checkpoint** : sauvegarde du résultat d'une étape, pour ne pas la refaire après une panne.
- **SIGKILL / `kill -9`** : tuer brutalement un programme, sans lui laisser le temps de se nettoyer (simule un plantage).
- **At-least-once (« au moins une fois »)** : garantie que la tâche sera exécutée une fois ou plus — donc des doublons sont possibles ; opposé à exactly-once (« exactement une fois »), que personne ne garantit ici.
- **Idempotent** : une opération qu'on peut répéter sans changer le résultat (ex. « écris le fichier X avec ce contenu » plutôt que « ajoute une ligne »).
- **Postgres / PostgreSQL** : la base de données relationnelle (celle qu'AurumShift utiliserait, en version 18.6 d'après le rapport).
- **`FOR UPDATE SKIP LOCKED`** : commande SQL qui permet à plusieurs ouvriers de piocher chacun une ligne libre sans se marcher dessus.
- **DAG / graphe de dépendances** : « la tâche C ne démarre qu'après A et B ».
- **BSL 1.1, SSPL, AGPL** : licences logicielles restrictives ou « à source disponible » (voir §4).
- **Bus factor** : nombre de personnes qui, si elles disparaissent, condamnent le projet (ici 1 ou 2 = fragile).
- **ADOPT / ADAPT / PARK / REJECT** : adopter tel quel / adapter / mettre de côté avec conditions de réouverture / rejeter.
- **PR (pull request)** : une « demande de fusion » sur GitHub : un paquet de modifications proposé, relisible, pas encore intégré à la branche principale.

---

## 1. Mission et question posée

### 1.1 La question, reformulée simplement
« Quel logiciel open source existant permet de faire tourner pendant longtemps des agents (programmation, recherche) en s'assurant que : une tâche a un propriétaire temporaire (bail), qu'elle est réessayée si elle échoue, qu'un travailleur peut relire le travail d'un autre (worker/reviewer), que l'état survit aux pannes, qu'on peut reprendre le lendemain dans une autre session, et qu'un humain n'a presque jamais à intervenir — **avec la simplicité d'exploitation comme premier critère** ? » (`00_SCOPE.md`, section « Question »)

Sont explicitement pénalisés : les piles lourdes en infrastructure, les semaines de réglage, les architectures distribuées opaques, les courtiers de messages et bases de données inutiles.

### 1.2 Contraintes de la doctrine (`claude.md`)
- Priorité **REUSE → ADAPT → WRAP → COMPOSE → CUSTOM en dernier** : réutiliser tel quel > adapter > envelopper > composer plusieurs briques > écrire soi-même en dernier recours.
- Pour chaque candidat significatif : sources primaires (dépôts, docs officielles), **ne pas croire les README aveuglément**, lire le code, cloner et exécuter si possible, inspecter architecture / algorithmes / maintenance / issues / dépendances / persistance / complexité d'exploitation / modes de panne / licence / reproductibilité.
- Étiquettes de preuve : **PROVEN** (prouvé, code lu avec fichier:ligne ou test exécuté dont le résultat est dans `experiments/`), **OBSERVED** (vu dans une exécution, une sortie, `git log`, une page web), **DOCUMENTED_CLAIM** (dit par la doc, non vérifié), **INFERENCE** (raisonnement à partir de ce qui précède), **UNKNOWN** (impossible à établir).
- Interdits : classer sur les étoiles GitHub, fabriquer des résultats de benchmark. Rejeter ou mettre en PARK ce qui exige un réglage excessif.
- Contraintes AurumShift à garder en tête (mais **sans jamais affirmer la compatibilité**) : recherche/paper-only, pas de capital réel, PostgreSQL d'abord, PIT/provenance/pas de lookahead, événementiel/intraday non-HFT, **une seule source d'autorité par sujet**, « l'absence de preuve n'est pas une preuve négative », faible relais opérateur, reproductibilité, la complexité d'infra doit se justifier.
- Frontière : la recherche produit des candidats ADOPT/ADAPT/PARK/REJECT ; l'adjudication finale se fait plus tard contre le vrai dépôt local AurumShift.

### 1.3 Sortie attendue
Un classement de candidats (pas une architecture). Le rapport 06 le dit : « Output type per `claude.md` : ADOPT / ADAPT / PARK / REJECT candidates ».

---

## 2. Méthode

### 2.1 Chaîne de travail déclarée (`00_SCOPE.md`, « Method »)
1. **12 dépôts clonés** (blobless, historique complet) : absurd, beads, dbos-transact-py, hatchet, inngest, langgraph, pgqueuer, prefect, procrastinate, restate, river, temporal. Licence, dernier commit, commits/auteurs sur 90 jours, étiquettes calculés depuis `git log` (OBSERVED). *(Non vérifiable ici : les clones ne sont pas dans le dépôt.)*
2. **23 candidats/architectures criblés** (`01_LANDSCAPE.md`).
3. **Top 5 inspecté en profondeur** (source, tests, issues) : Absurd, DBOS, Procrastinate, Restate, Beads (`02_TOP5.md`).
4. **Expériences de panne/reprise** sur ces 5 (la demande initiale : 3) (`03_REPRODUCTION.md`).
5. Modes de panne, coûts d'exploitation, adjudication : `04`, `05`, `06`.

Le choix du top 5 est **un jugement** (le rapport le dit) : « simplicité d'abord, puis couverture des exigences ». River (Go) et pgqueuer, candidats simples et solides, **n'ont pas été approfondis** et **aucune expérience** n'a été faite dessus.

### 2.2 Environnement d'expérience et ses limites (à lire avant de croire un chiffre)
(`00_SCOPE.md`, « Environment and its limits »)
- Bac à sable cloud : 4 vCPU / 15 Go, **pas de démon Docker**, pas d'IPv6, sortie HTTPS via proxy ; `api.github.com` bloqué pour les dépôts hors périmètre → les compteurs d'issues ouvertes viennent de pages HTML via WebFetch, sinon UNKNOWN.
- **PostgreSQL 18.6** (version de production déclarée de l'utilisateur) obtenue en extrayant le `.deb` pgdg `postgresql-18` dans un préfixe privé ; toutes les expériences PG tournent dessus ; le PG16 système ne sert que de client.
- **Six agents travaillaient en parallèle sur la même machine. Contamination croisée** : un `pkill -9 -u lab postgres` d'un agent a tué le cluster PG d'un autre agent **au moins deux fois** (Absurd avant le scénario C ; Procrastinate dans un essai du scénario B). Les essais concernés ont été relancés ou marqués ; les logs gardent les essais avortés.
- Échelle minuscule : **20 tâches, environ 3 s de travail chacune, 4–5 en parallèle**. Cela mesure la **sémantique** (est-ce que ça récupère ? combien de doublons ? que fait l'opérateur ?) et non le débit ni la stabilité longue durée.
- Versions testées ≠ HEAD des clones : Procrastinate PyPI 3.10.0 (clone tag 3.9.0) ; serveur Restate npm 1.7.12 (HEAD 1.8.0-dev) ; Beads compilé depuis HEAD `e7138e93` avec `-tags gms_pure_go` (build CGO par défaut échoué : en-têtes ICU manquants) ; DBOS 3.1.0 ; absurd-sdk 0.5.0.
- Seules ont été simulées : SIGKILL et arrêt immédiat de PG. **Pas** de coupure de courant, disque plein, partition réseau, dérive d'horloge, multi-machines.
- Le « lead » a relu les rapports des sous-agents et **vérifié dans le code quatre affirmations** (Absurd lease/SKIP LOCKED, DBOS reprise seulement au démarrage, Procrastinate sans relance automatique des jobs bloqués, Beads TTL 5 min codé en dur). Les autres affirmations sont les constats étiquetés des sous-agents, **non re-dérivés**.

### 2.3 Protocole expérimental commun (`03_REPRODUCTION.md`, « Common workload »)
- 20 tâches. Une tâche = une étape `work` (ajoute une ligne `tâche, tentative, pid, horodatage` à un fichier « effets de bord », puis dort ~3 s) suivie d'une étape dépendante `review`.
- Les **doublons d'effets de bord** sont comptés depuis ce fichier. Une **« intervention »** = toute action humaine autre que démarrer normalement workers/PG.
- Le mécanisme de dépendance **diffère selon le système** (donc les charges ne sont pas strictement identiques) : Absurd = tâche enfant dans une seconde file + attente ; DBOS = deuxième étape dans le même workflow ; Procrastinate = `defer` de `review` écrit à la main après `work` ; Restate = deuxième `ctx.run` dans le même handler ; Beads = 20 tickets « worker » avec un ticket « reviewer » bloqué par chacun.

Quatre scénarios :
- **A** : tuer un worker en plein travail (SIGKILL).
- **B** : échec transitoire, réessais/backoff, échec terminal.
- **C** : plantage de PostgreSQL (`kill -9` du postmaster ou `pg_ctl -m immediate`) puis redémarrage (pour Restate : c'est le serveur Restate qu'on tue ; pour Beads : on tue les processus `bd`).
- **D** : continuation inter-sessions (tout arrêter, attendre, redémarrer).

### 2.4 Splits, pré-enregistrement, gel de paramètres, graines
Cette lane n'est pas une étude de données : **il n'y a ni jeu tuning/validation/held-out, ni pré-enregistrement formel, ni graine aléatoire déclarée**. Le seul élément aléatoire est l'instant du kill dans les scripts Beads (`random.uniform(0.02,0.6)` dans `kill9.sh`, `random.uniform(0.05,0.5)` dans `kill9_claim.sh`) et l'ordonnancement naturel des processus. Aucune graine n'est fixée. Chaque scénario est un **essai unique** (« single-run, non-benchmark », `00_SCOPE.md`). Je n'ai trouvé aucune répétition d'un même scénario dans les fichiers, sauf : Absurd A avec plusieurs configurations (kill à +1,5 s, +4,5 s, variantes « await »), Absurd B (3 configurations), Procrastinate C (3 modes selon le rapport), Beads race (N = 2, 4, 8). Les critères de décision sont qualitatifs (rang par jugement « simplicité d'abord ») et non des seuils numériques pré-déclarés.

### 2.5 Critères de décision (ce qui remplace des « seuils »)
Il n'y a pas de seuil chiffré de type « ADOPT si X > Y ». Les règles effectivement utilisées, telles qu'elles apparaissent :
- Rejet précoce sur **poids d'infrastructure** (services requis) : Temporal, Hatchet, Inngest (aussi SSPL), Prefect, Conductor, Airflow/Dagster, Argo, Kestra, Windmill (AGPL), Celery/Dramatiq/RQ (courtier supplémentaire + doublons par redélivrance).
- Échelle « Ops » de 1 (une bibliothèque + votre base) à 5 (plateforme de cluster), **INFERENCE** à partir des services requis (`01`).
- Note « operator burden » 1–5 (`05`, INFERENCE) : Absurd 2, DBOS 2–3 (4 si le basculement compte et pas de Conductor), Procrastinate 2, Restate 2, Beads 2 (comme mémoire) mais « inadapté comme moteur ».
- Nombre d'**interventions opérateur observées** par scénario (`05` §2).
- Risque de maintenance : HIGH / MED / LOW-MED d'après le nombre d'auteurs et de commits sur 90 jours.
- Doctrine : PostgreSQL d'abord, « une source d'autorité par sujet ».

---

## 3. Résultats détaillés

### 3.1 Rapport 01 — Le paysage (23 candidats)
Le tableau complet est dans `01_LANDSCAPE.md`. Version condensée avec les colonnes utiles :

| # | Candidat | Type | Services requis | Reprise (bail/relance) | Graphe | Licence | Activité 90 j (commits / auteurs) | Ops | Verdict de criblage |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Absurd** | exécution durable dans PG (fonctions SQL + SDK) | PG seul | bail `claim_timeout`, checkpoints par étape, stratégies de retry | non natif | Apache-2.0 | 6 / 1 (dernier 2026-08-04) | 1–2 | Approfondi |
| 2 | **DBOS Transact (Py)** | bibliothèque de workflows durables | PG (ou SQLite) | `executor_id`, reprise au démarrage, retries d'étapes ; pas de bail | en code | MIT (Conductor/Cloud commercial) | 81 / 7 | 1–2 | Approfondi |
| 3 | **Procrastinate** | file de tâches Python sur PG | PG | SKIP LOCKED, heartbeat, détection « stalled » (relance opt-in) | non | MIT | 97 / 6 | 1–2 | Approfondi |
| 4 | **Restate** | serveur d'exécution durable | 1 binaire Rust (journal + RocksDB embarqués) + vos services HTTP | invocations poussées, rejeu du journal | en code | BSL 1.1 (SDK MIT) | 293 / 22 | 2 | Approfondi |
| 5 | **Beads (bd)** | graphe de tâches git/Dolt pour agents | aucun en mode embarqué | claim CAS + bail 5 min, `bd reclaim` manuel ; pas de retry | **oui** (~19 types) | MIT | 1558 / 116 | 1 (mais agité) | Approfondi |
| 6 | Temporal | moteur de workflows | serveur multi-services + base | heartbeat/timeouts | via code | MIT | 538 / 63 | 4 | Puissant mais lourd |
| 7 | River | bibliothèque de jobs Go | PG | SKIP LOCKED ; « rescuer » élu chef (30 s) | non (OSS) | MPL-2.0 | 85 / 9 | 1 | Simple et robuste, Go seulement |
| 8 | Hatchet | file + DAG | moteur + PG (+ RabbitMQ par défaut) | timeouts/retries | oui | MIT | 470 / 20 | 3 | Plus gros que le besoin |
| 9 | Inngest | fonctions à étapes événementielles | serveur + Redis + base | baux (4 s / 2 min) | en code | **SSPL** + licence future Apache | 286 / 22 | 3–4 | Licence + modèle HTTP inadaptés |
| 10 | LangGraph | bibliothèque de graphes d'agents | aucun (checkpointer PG/SQLite) | **aucune** détection de crash | dans un run | MIT | 113 / 17 | 1 | Pas un orchestrateur |
| 11 | pgqueuer | file Python sur PG | PG | SKIP LOCKED + requeue par heartbeat | non | MIT | 124 / **1** | 1 | Simple ; bus factor 1 |
| 12 | Prefect | orchestrateur de flows | serveur API + base + workers | heartbeats | oui | Apache-2.0 | 398 / 54 | 3 | Lourd |
| 13 | Celery | file de tâches | Redis ou RabbitMQ | acks_late, redélivrance | canvas | BSD (mémoire) | UNKNOWN | 2–3 | Courtier en plus, doublons |
| 14 | Dramatiq | idem | RabbitMQ/Redis | middleware retry | pipelines | LGPL | UNKNOWN | 2 | Courtier |
| 15 | RQ / Huey | idem | Redis (Huey aussi SQLite) | timeouts | minimal | BSD / MIT | UNKNOWN | 2 / 1 | Huey-SQLite ok sur 1 machine |
| 16 | Airflow / Dagster | orchestrateurs de données | base + planificateur + web | heartbeats | oui | Apache-2.0 (mémoire) | UNKNOWN | 4–5 | Mauvaise forme, lourd |
| 17 | Conductor OSS / Orkes | moteur JSON | serveur + base + ES | timeouts | oui | Apache-2.0 | actif | 4 | Pile JVM lourde |
| 18 | Argo Workflows | CRD Kubernetes | Kubernetes | retry de pods | oui | Apache-2.0 (mémoire) | UNKNOWN | 5 | Seulement si déjà k8s |
| 19 | Windmill | plateforme scripts/flows | serveur + workers + PG | file dans PG | flows | AGPLv3 + EE propriétaire | actif | 3 | Plateforme ; AGPL |
| 20 | Kestra | orchestrateur YAML | JVM + base | – | oui | Apache-2.0 (mémoire) | UNKNOWN | 3–4 | Non examiné |
| 21 | Table de baux PG maison | patron | PG | selon conception | vos tables | n/a | n/a | 1 + vos bugs | Viable (~100–300 lignes) |
| 22 | File SQLite | patron | aucun | `BEGIN IMMEDIATE` | vos tables | n/a | n/a | 1 | Une seule machine |
| 23 | Tableaux git/markdown/flock | patron | git/fichiers | mkdir/flock | ad hoc | n/a | n/a | 1 | Fragile en concurrence |

Tailles brutes de code non-test (approximatives, `wc` grossier, peuvent inclure du code généré) : Temporal ~360k lignes Go, Hatchet ~237k Go, Prefect ~203k Py, Inngest ~179k Go, River ~45k Go, LangGraph ~44k Py, pgqueuer ~12k Py ; approfondis : Absurd 3150 lignes SQL + 2317 lignes SDK Py, DBOS ~32,7k Py, Procrastinate ~8,1k Py+SQL, Restate ~283k Rust (984 crates dans `Cargo.lock`), Beads ~371k Go (`01_LANDSCAPE.md`).

Constats de niveau paysage du rapport :
- **F1 (INFERENCE)** : aucun candidat ne combine *réaffectation automatique par bail* + *graphe de dépendances natif* + *zéro service supplémentaire*. Les systèmes à graphe sont lourds ; les légers n'ont pas de graphe.
- **F2** : tout ce qui récupère du travail est « au moins une fois » ; personne ne donne « exactement une fois » pour les effets de bord du code utilisateur.
- **F3** : trois licences demandent attention : Inngest (SSPL), Restate serveur (BSL 1.1, usage interne autorisé), Windmill (AGPL). La reprise automatique multi-exécuteurs de DBOS relève d'un plan de contrôle commercial.

Ce que ça signifie en simple : le « paysage » sert à écarter vite les usines à gaz ; l'écart reposait sur les services requis (documentés) — **pas** sur des essais. Le rapport le reconnaît pour 19 des 23 candidats (jamais exécutés).

### 3.2 Rapport 02 — Inspection de code du top 5 (résumé chiffré par candidat)

**Absurd** (`earendil-works/absurd`, Apache-2.0)
- Fichier SQL unique `sql/absurd.sql` de 3150 lignes (~40 fonctions plpgsql) + SDK Python 2317 lignes (1 dépendance : psycopg) + SDK TypeScript ; tableau de bord Habitat et CLI absurdctl optionnels (non exercés). PROVEN.
- 5 tables par file : `t_` tâches, `r_` runs (une ligne par tentative), `c_` checkpoints, `e_` événements, `w_` attentes. Lisible en SQL. PROVEN.
- `claim_task` = `FOR UPDATE SKIP LOCKED` + bail (`claim_timeout` ; 30 s par défaut en SQL, 10 s dans les expériences). Écrire un checkpoint ou un `heartbeat` prolonge le bail ; `await_task_result` fait un heartbeat automatique. PROVEN.
- **Pas de « reaper »** : les baux expirés sont balayés *dans* `claim_task`, par n'importe quel worker qui interroge, au plus `qty` runs par appel (`absurd.sql:965`). Il faut un worker vivant avec un emplacement libre. PROVEN.
- Fencing (clôture) : un worker « périmé » qui tente de compléter/checkpointer un run réattribué reçoit l'erreur AB002 (avalée par le SDK). Cela clôture l'état du run, **pas** les effets de bord utilisateur. PROVEN.
- Retry : none / fixe / exponentiel, plafond 1 jour. **Par défaut : pas de stratégie → réessai immédiat** ; `max_attempts` par défaut du SDK Python = 5. PROVEN.
- Pas de graphe natif : tâche enfant dans une *autre* file + `ctx.await_task_result` (occupe un slot ; l'attente dans la même file est refusée), événements, sleep. Fan-out/fan-in = issue ouverte #110.
- Tests : ~161 SQL, ~93 SDK Python, ~100 TypeScript ; tous exigent Docker + postgres:16. **Aucun test ne tue un processus ni PG** ; la reprise est testée par voyage dans le temps (`fake_now`). PROVEN.
- **PG 18.6** : tests SDK Python **93/93** passent après correction de la fixture (Docker absent). Suite SQL **107 réussites / 4 échecs** : deux tests `uuidv7`, un test de détachement de partition (le `uuidv7()` natif de PG 18 ignore `fake_now` — INFERENCE : problème de harnais) et une assertion de plan d'index de bail (INFERENCE : choix du planificateur sur petite table). Les tests pg_cron e2e et la construction d'absurdctl n'ont pas été exécutés. OBSERVED.
- Maintenance : 309 commits ; dernier 2026-08-04 (version 0.5.0) ; **90 j : 6 commits, 1 auteur** (Ronacher 282/309 au total) ; `pyproject` marque « Alpha » ; 22 issues ouvertes ; correctifs de la voie de bail groupés en mars 2026 (`89833e6`, `39587e9`, `300a5c2`, `b87b423`) → code jeune.
- Installation : PG + venv + schéma en 19 s ; premier pipeline fonctionnel ≈ 10 min.

**DBOS Transact (Python)** (`dbos-inc/dbos-transact-py`, MIT)
- Bibliothèque, pas serveur ; seul service requis : PG (SQLite par défaut en dev). 6 dépendances directes, ~32,7k lignes (`_sys_db.py` 7,4k lignes). PROVEN.
- État : `workflow_status` (~40 colonnes), `workflow_input/output`, `operation_outputs`, `notifications`, `workflow_events`, `streams`, `workflow_schedules`, `application_versions`, `queues` ; 36 migrations. Les sorties d'étapes sont **picklées** par défaut → base64 opaque dans psql.
- **Aucun bail, aucun heartbeat, aucune détection de worker mort.** La propriété = chaîne `executor_id` sur les lignes PENDING. PROVEN.
- Reprise automatique **uniquement au lancement du processus**, pour les lignes où `executor_id` et `application_version` sont les siens (`_dbos.py:697-711`, `_recovery.py:36-70`, `_sys_db.py:2675`). Reprendre le travail d'un *autre* exécuteur n'est atteignable que depuis le gestionnaire websocket du Conductor (`conductor.py:178`) ou la fonction privée `_recover_pending_workflows`. Ignoré si `conductor_key` défini. PROVEN.
- Défauts piégeux : `executor_id="local"` ; `application_version` = md5 du source des workflows → **un changement de code isole le travail PENDING de l'ancienne version** ; `max_recovery_attempts=100` puis « dead-letter ».
- Étapes : retries `max_attempts=3, interval=1.0, backoff=2.0` par défaut ; file avec concurrence, limitation de débit, priorité, déduplication, partitions, délai ; annulation/reprise/fork/workflows enfants/send-recv/événements.
- Tests : 54 fichiers / ~1222 fonctions de test + suite « chaos » de 4 tests (5000 workflows). Les tests de reprise lus (`tests/test_dbos.py:342,394,471`) manipulent la base dans le même processus plutôt que de SIGKILL des processus séparés (INFERENCE, audit incomplet).
- Maintenance : 81 commits / 7 auteurs sur 90 j (un auteur = 63) ; 3 issues ouvertes (WebFetch), aucune sur la reprise ; la 3.0 a retiré des API → agitation.
- Installation : pip 6,3 s ; ≈ 20 min pour une expérience fonctionnelle, y compris 2 corrections d'API (`register_queue` doit suivre `launch()` en 3.x).

**Procrastinate** (`procrastinate-org/procrastinate`, MIT)
- Bibliothèque Python sur PG seul ; 4 tables (`jobs`, `events`, `periodic_defers`, `workers`) + 18 fonctions plpgsql ; ~8,1k lignes.
- Claim : `FOR UPDATE OF jobs SKIP LOCKED`, `ORDER BY priority DESC, id` ; `lock` sérialise ; `queueing_lock` déduplique.
- Heartbeat 10 s, `stalled_worker_timeout` 30 s (`worker.py:48-49`). Un worker n'élimine les lignes de workers morts qu'**à son propre démarrage** (`worker.py:445`), laissant le job en `doing` avec `worker_id` NULL. `get_stalled_jobs()` (`manager.py:223`) **liste seulement**. **Rien ne relance automatiquement les jobs bloqués** ; la doc (`retry_stalled_jobs.md`) dit qu'ils restent « forever » sauf tâche périodique écrite par vous.
- `RetryStrategy(max_attempts, wait, linear_wait, exponential_wait, retry_exceptions)`. NOTIFY seulement à l'insertion et à l'abandon → les réessais attendent l'intervalle de sondage (5 s par défaut).
- Pas de graphe : `lock`, `queueing_lock`, priorité, `scheduled_at`, defer-depuis-une-tâche. Un job programmé dans le futur en tête bloque sa file de lock (issue #1599).
- Sémantique « au moins une fois » ; issue #1633 : un worker présumé bloqué peut encore terminer/relancer après la reprise (OBSERVED, WebFetch).
- Tests : 644 fonctions / 36 fichiers ; aucun test bout-en-bout SIGKILL/crash PG trouvé (INFERENCE par grep). CI sur PG 14–18 (`ci.yml:24-32`).
- Maintenance : 97 commits / 90 j, 2 auteurs humains (Jablon 55 ; 1769 au total) + bots ; 3533 commits ; tag 3.10.0 ; 12 issues ouvertes.

**Restate** (`restatedev/restate`, BSL 1.1 ; SDK TS MIT)
- Un binaire Rust de 225 Mo avec cinq rôles (http-ingress, admin, worker, log-server, metadata-server) ; journal Bifrost + RocksDB embarqués ; 24 partitions par défaut, réplication 1 ; invoque votre service **HTTP/2** et rejoue le journal. ~283k lignes Rust ; 984 paquets. **PostgreSQL ne peut pas servir de magasin** (métadonnées : raft/répliqué/objet/DynamoDB).
- Licence BSL 1.1 (`LICENSE:1-66`) : licence de conversion Apache-2.0 au plus tôt à 4 ans par version ; l'usage additionnel autorisé permet tout sauf un « Public Restate Platform Service » (offre gérée où des tiers enregistrent leurs endpoints). Usage interne en production autorisé.
- Durabilité : WAL + fsync par défaut (`crates/log-server/src/rocksdb_logstore/writer.rs:495-506`) ; désactiver le WAL est marqué « [DANGEROUS] » (`types/src/config/log_server.rs:169-174`). Coupure de courant **non testée** ; instantanés S3/GCS/Azure présents en code, désactivés, non testés.
- Retry par défaut : 500 ms initial ×2, max 1 min, 70 tentatives puis **PAUSE** (pas d'échec) ; idempotence 1 jour ; timeout d'inactivité 1 min, d'abandon 10 min.
- Pas de graphe intégré. Observabilité : CLI, SQL (DataFusion, 18 tables), UI `/ui/`, Prometheus.
- Tests : ~1206 attributs de test / 247 fichiers ; `cluster_chaos_test` (3 nœuds, 60 s de chaos) ; Jepsen nocturne (DOCUMENTED_CLAIM). **Aucun test SIGKILL mono-nœud avec SDK trouvé dans le dépôt.**
- Maintenance : 293 commits / 22 auteurs sur 90 j ; les 6 premiers auteurs 86/73/56/22/13/12 → noyau ≈ 3–4 ; 91 tags ; issues ouvertes UNKNOWN.
- Empreinte : RSS ≈ 275 Mo au démarrage, ≈ 307 Mo après 60 invocations, 55–84 threads ; répertoire de données ≈ 220 Mo au premier démarrage ; npm install 11 s ; ≈ 2 min pour un serveur en marche. Liaison par défaut `[::]` en échec (RT0004, pas d'IPv6) → il faut `bind-ip=127.0.0.1`.

**Beads (`bd`)** (`steveyegge/beads`, MIT)
- CLI de graphe de tâches avec bail, conçu comme mémoire d'agents ; **pas un moteur d'exécution** : ni répartiteur, ni superviseur, ni compteur/backoff de retry, ni registre de workers, ni rôle de relecteur.
- Stockage : Dolt « seul backend supporté » ; mode embarqué par défaut (`.beads/embeddeddolt/`, verrou de fichier = un seul écrivain) ; le mode serveur exige `dolt sql-server` épinglé sur Dolt 2.2.0 (DOCUMENTED_CLAIM, non testé). `bd sql` et `bd doctor` **non supportés en mode embarqué** → pas de vue SQL. **Pas PostgreSQL.**
- Claim par compare-and-swap atomique sur une cellule `row_lock` aléatoire (`issueops/claim.go`) ; le re-claim par le même acteur est un no-op idempotent.
- Bail : `bd heartbeat`, `bd reclaim` ; TTL codé en dur **5 min** (`issueops/lease.go:19-30`), modifiable seulement par clé de contexte Go (pas d'option CLI/config). **Rien ne réclame automatiquement** : seuls appelants de `ReclaimExpiredLeases` = `bd reclaim` et sa variante proxy ; la doc dit de l'appeler depuis un minuteur de superviseur.
- Identité : chaîne `BEADS_ACTOR` non authentifiée. ~19 types de dépendances (`types.go:1277-1307`) ; seuls `blocks`, `parent-child`, `conditional-blocks`, `waits-for` affectent `ready` (`types.go:1363`). « Preuve » = motif de clôture/commentaires/métadonnées ; **pas de barrière de preuve structurée** (INFERENCE).
- Volume : ~371k lignes Go de production vs ~533k de tests ; 1781 fichiers de test / 9874 fonctions.
- Agitation : 10 959 commits ; **1558 sur 90 j par 117 auteurs** ; 131 tags (v1.3.0 le 2026-09-15) ; CHANGELOG avec de nombreux « Breaking: » en 1.x ; 26 sujets de commits contiennent « corruption », 26 « lost/data loss » ; **59 correctifs de corruption/perte de données sur 90 j** ; **896 issues ouvertes** (WebFetch) ; #6929 : la migration en mode serveur avale une erreur → « table not found: leases ».
- Build : CGO par défaut **échoué** (ICU) ; `-tags gms_pure_go` fonctionne, Go 1.26.7 ; 3 min 40 au premier build, 60 s ensuite ; binaire 214 Mo ; `bd init` 4,9 s ; `bd create` ≈ 0,55 s.

Rapports de second rang (non approfondis) : **River** — `SKIP LOCKED` (`river_job.sql:186,217`) + « rescuer » élu chef, 30 s par défaut (`internal/maintenance/job_rescuer.go:31`), 6 tables ; workflows = River Pro (payant, DOCUMENTED_CLAIM). **pgqueuer** — requeue par heartbeat (`qb.py:433`, `core/heartbeat.py`), colonne `attempts`, ~12k lignes, 1 auteur sur 90 j ; `qb.py:353` : SKIP LOCKED qui glisse au-delà d'un plafond de concurrence (issue #761). **Temporal** — référence de justesse (heartbeats `service/history/timer_queue_active_task_executor.go`) mais multi-services + base + règles de déterminisme.

### 3.3 Rapport 03 — Expériences : ce que dit le rapport, ce que j'ai vérifié dans les fichiers bruts

#### 3.3.1 Scénario A — tuer un worker en plein travail
Résultats du rapport (`03_REPRODUCTION.md`) :

| Système | Config | Observé | Délai de réaffectation | Doublons | Interventions |
|---|---|---|---|---|---|
| Absurd | bail 10 s, 5 tâches en vol | un worker vivant réclame via le balayage de `claim_task` | 9,5–10,1 s ; **21,8 s** (≈ 52 s pour finir) quand tous les workers étaient saturés par des parents en attente ; 7,1 s avec un worker libre | 5 doublons `work` si tué en cours d'étape ; **0** si `work` déjà checkpointé (20 checkpoints réutilisés) | 0 |
| DBOS | 2 workers vivants w1, w2 ; on tue w1 | **le survivant ne reprend pas** ; les 5 workflows de w1 restent PENDING pendant les 50 s (A1) / 20 s (A2) d'observation | jamais (jusqu'au redémarrage de w1 avec même id+version) ; après redémarrage : fini en ≈ 6,5 s | A1 : 5 doublons `work` ; A2 (tué pendant `review`) : `work` rejoué depuis `operation_outputs`, seul `review` dupliqué | 1 |
| Procrastinate | défaut | 4 jobs tenus par le worker tué restent `doing` ≥ 140 s ; un nouveau worker élimine la ligne du mort mais les jobs restent `doing` ; `get_stalled_jobs()` liste les 4 | **jamais** sans opérateur | 0 doublon mais 4 jobs jamais finis | ∞ |
| Procrastinate | + tâche périodique `retry_stalled_jobs` écrite à la main (cron chaque minute, heartbeat 10 s, timeout 30 s) | 4 jobs relancés 24,7 s après le kill ; 20 work + 20 review réussis | 24,7 s (rapide car le worker est mort avant son premier heartbeat) ; pire cas ≈ 90 s = 30 s de péremption + ≤ 60 s de tick cron — **INFERENCE** | 4 doublons `work` | 0 après configuration unique |
| Restate | 1 nœud, on tue le service 1,5 s après soumission | le serveur affiche « backing-off, Connection refused » avec intervalles croissants ; après redémarrage du service, 20/20 finis | lié au backoff + redémarrage manuel | `work` exécuté 40 fois pour 20 tâches (2× chacune) ; `review` exactement 20 | 1 |
| Beads | le demandeur meurt ; bail 5 min | après expiration (07:06:21), sans opérateur jusqu'à 07:08:41 : `bd ready` omet le ticket et un autre agent échoue à `--claim` (« already claimed by agent2 ») ; `bd reclaim --older-than 0s` rétablit 10 claims périmés ; le heartbeat tardif de l'ancien propriétaire est **refusé** | manuel (TTL fixe 5 min) | n/a | 1 |

**Vérification sur les fichiers bruts Absurd (mes recalculs, différences d'horodatage epoch)** :

| Essai (dossier `logs/`) | kill (epoch) | 1er run réattribué / échec de bail | Début tentative 2 | Fin (tous terminaux) | Doublons `work` | Doublons `review` |
|---|---|---|---|---|---|---|
| `A_k1.5` (kill à +1,5 s) | …049,78 | …059,890 (=+10,11 s) | …059,898 (+10,12 s) ; 1er effet de bord tentative >1 à **+10,14 s** | 15 sondages ; +14,7 s | **5** (tâches 0–4) | 0 |
| `A_k4.5` (kill à +4,5 s) | …070,403 | …079,657 (+9,25 s) | …079,911 ; 1er effet de bord à **+9,52 s** | 14 sondages | **5** (tâches 15–19) | 0 |
| `A_await` (workers saturés) | …099,52 | …121,316 = **+21,80 s** | …152,53 (+53,0 s) | 52 sondages ; +53,4 s | **0** | 0 |
| `A_await_free` (worker libre) | …286,251 | …293,370 = **+7,12 s** | …293,626 (+7,38 s) | 11 sondages ; +10,5 s | **0** | 0 |
| `A_await_spare` | …170,393 | …192,248 (+21,86 s) | …207,869 (+37,5 s) ; 1er effet de bord >1 à +47,60 s | 91 sondages ; +94,4 s | 0 | **12** (32 exécutions pour 20 tâches) ; état final : 17 review terminées, **3 échouées** |

Les états finaux sont : `main tasks: completed=20`, `review tasks: completed=20` (sauf `A_await_spare`, 17 terminées + 3 échouées) (`experiments/absurd/logs/*/final_state.txt`). Les comptes de runs : 15 runs de tentative 1 terminés + 5 échoués (`$ClaimTimeout`, le bail périmé) + 5 runs de tentative 2 terminés (`run_counts.txt`) — l'échec des 5 runs de la tentative 1 avec la raison `$ClaimTimeout` est la preuve directe que **c'est le mécanisme de bail** qui a réaffecté.

Verdicts de vérification pour le scénario A Absurd :
- « kill +1,5 s → 10,1 s » ✔ (10,14 s). « kill +4,5 s → 9,5 s » ✔ (9,52 s).
- « 21,8 s » ✔ (21,80 s). « ≈ 52 s pour finir » ✔ (52 sondages = 53,4 s).
- « 7,1 s avec un worker libre » ✔ (7,12 s).
- « 5 doublons `work` quand tué en cours d'étape » ✔ ; « 0 quand `work` déjà checkpointé » ✔ (0 doublon dans `A_await` et `A_await_free`, avec `no attempt>1 side effects`, c.-à-d. la tentative 2 n'a *refait aucun* effet de bord : reprise depuis les checkpoints). « 20 checkpoints réutilisés » : ? (la valeur 20 n'apparaît pas explicitement ; c'est cohérent avec « 0 effet de bord en tentative 2 »).
- Nuance que je note : dans `A_await` l'échec de bail apparaît à +21,8 s alors que le bail est de 10 s. Le rapport l'attribue à la saturation (aucun slot libre pour balayer). Cohérent avec le code lu (balayage dans `claim_task`) mais **c'est une inférence** : les fichiers ne contiennent pas le moment d'expiration du bail lui-même.
- **Point que le rapport présente de façon ambiguë** : la ligne « Absurd lease hazard (our misconfiguration, real hazard) : … 12 duplicate reviews with no crash » (rapport 03, « Extra observations ») correspond, dans les fichiers, à `A_await_spare`, un essai **avec** kill de M1 (`A_await_spare.out` : « SIGKILL M1 »). Ce n'est donc pas « sans crash » au sens du run ; le crash était là, mais les 12 doublons de `review` surviennent tardivement (+47,6 s) et n'ont pas la crash comme cause directe apparente. La configuration exacte de l'essai (variables `RCT`, `RCONC` de `scnA.sh`) n'est pas enregistrée. Le rapport ne mentionne pas non plus les **3 tâches `review` échouées** de cet essai. Voir §7.

**Vérification DBOS scénario A** (fichiers `experiments/dbos/`) :
- A1 : 45 instantanés de la phase 1 sur 48,2 s (…125,82 → …174,00) montrent en continu `w1:PENDING=5` : ✔ « 5 workflows restent PENDING pendant 50 s ». Les 5 bloqués sont t15–t19 (`A1_stuck.txt`). A2 : 20 instantanés sur 20,8 s, bloqués t0–t4 (`A2_stuck.txt`) ✔ « 20 s ».
- Après redémarrage de w1, `SUCCESS=20` apparaît **4,6 s** après le premier instantané de phase 2 (A1) et 4,4 s (A2). Le rapport dit « ≈ 6,5 s » : compatible mais l'instant précis du redémarrage n'est pas enregistré (le script l'affiche à l'écran mais aucun fichier ne le garde) → ✔ approximatif / ? précis.
- **Anomalie non expliquée par le rapport** : pendant la phase 2 (après redémarrage de `w1`), les cinq lignes PENDING apparaissent sous `exec=w2:PENDING=5` (à partir de …176,39 en A1 et …253,90 en A2) et non `w1`. Or seul `w1` a été redémarré et `w2` était vivant. Cela suggère que les workflows ont changé d'exécuteur au moment de la reprise (peut-être que w2 a fini par les récupérer, ou qu'une reprise a réécrit `executor_id`). Le rapport ne le mentionne pas et conclut « le survivant ne reprend pas ». Voir §7.
- `A1_ops.txt` / `A2_ops.txt` : 40 lignes (20 tâches × `work` et `review`) ✔ cohérent avec « `work` rejoué depuis `operation_outputs` » ; mais les fichiers d'effets de bord (`A*_side_effects.log`) copiés par le script ne sont **pas** dans le dépôt → « A1 : 5 doublons `work` ; A2 : seul `review` dupliqué » : ? non vérifiable.

**Procrastinate scénario A** : aucun script `scenA.sh` ni log correspondant dans le dépôt (le dossier contient `scenC.sh`, `app.py` avec la tâche périodique optionnelle `retry_stalled_jobs`, et deux petits fichiers de « gaps »). « ≥ 140 s », « 24,7 s », « 4 doublons » : ? non vérifiable. Le code de la tâche périodique est bien présent dans `app.py` (activée par `RETRY_STALLED=1`), ce qui confirme la configuration décrite.

**Restate scénario A** : seul `scenarioA_notes.txt` (une ligne : « first attempt: svc SIGKILLed ~1.5s after submit of 20; note my pgrep -f also killed the shell ») → « 40 exécutions de `work` » : ? non vérifiable. À noter : la note admet que le `pgrep -f` a tué aussi le shell de l'opérateur, ce qui rend le protocole bruité.

**Beads scénario A** : `race.8.*.out` (voir §3.3.4). La séquence du bail (07:06:21 → 07:08:41) : ? non enregistrée en fichier ; je constate seulement que 07:06:21 UTC est bien dans la fenêtre temporelle des autres expériences (epoch 1790665581).

#### 3.3.2 Scénario B — échec transitoire, réessais, échec terminal

| Système | Config | Observé (rapport) |
|---|---|---|
| Absurd | exponentiel base 2 s ×2 | écarts non contestés 2,03 s puis 4,05 s puis succès ; sous contention 3,06 s, 4,11 s ; `work` exécuté une fois par tâche (checkpoint réutilisé). `FAIL_FIRST=99, max_attempts=3` : les 20 échouent à la tentative 3, `review` jamais créé. **Sans stratégie de retry : 5 tentatives brûlées en < 1 s** |
| DBOS | `max_attempts=4`, défauts intervalle 1 s ×2 | tâche 0 réussit à la tentative 3 ; la tâche 5 (toujours en échec) fait 4 tentatives (écarts ≈ 2/3/5 s dont 1 s de sleep), finit ERROR `DBOSMaxStepRetriesExceeded` ; 19 SUCCESS + 1 ERROR |
| Procrastinate | `RetryStrategy(max_attempts=4, exponential_wait=2)` | polling par défaut → écarts 5,0/5,0/10,0/20,0 s (le retry n'émet pas de NOTIFY, pris au sondage 5 s). Avec `--fetch-job-polling-interval=0.5` → 2,03/4,04/8,05/16,09 s. Le job toujours en échec s'exécute **5 fois** (max_attempts=4 ⇒ 5 exécutions), finit `failed` |
| Restate | `ctx.run` retry 1 s ×2 | 3 échecs puis succès aux écarts 1011/2008/4009 ms ; `maxRetryAttempts=4` → écarts 506/1006/2007 ms puis HTTP 500 (terminal) ; simple `throw` avec politique par défaut → écarts 546…20 639 ms, reste en backoff (annulé après ≈ 7 tentatives ; défaut = pause après 70) |
| Beads | – | pas de mécanisme de retry (PROVEN par absence) |

**Vérification** :
- Absurd `B_transient_2tasks/task0_timeline.txt` : tentative 2 écart **2,03 s**, tentative 3 écart **4,05 s**, succès ✔. `B_transient/task0_timeline.txt` (20 tâches, contention) : écarts **3,06 s** et **4,11 s** ✔. `B_transient/analysis.txt` : `{'work': 20, 'fail': 40, 'review': 20}` → `work` exécuté une seule fois par tâche ✔ ; 40 échecs = 2 par tâche ✔.
- Absurd `B_terminal` : `final_state.txt` = `main tasks: failed=20`, `review tasks:` vide ✔ ; `task_summary.txt` `failed|3|3|20` (état, tentatives, max, nombre) ✔ ; `analysis.txt` `{'work': 20, 'fail': 60}` ✔ (20×3 échecs). 
- « Sans stratégie, 5 tentatives en < 1 s » : ? aucun fichier de log correspondant (les trois dossiers B utilisent une stratégie exponentielle de 2 s). Cette affirmation repose sur la lecture du code (« default = no strategy → immediate retry », PROVEN par lecture) plus, peut-être, sur un essai non archivé.
- Procrastinate `logs/B_scenb2_gaps.txt` : n=99 tentatives à +0 ; +5,02 s (écart 5,02) ; +10,03 s (écart 5,01) ; +20,04 s (écart 10,01) ; +40,06 s (écart 20,02) ✔ « 5,0/5,0/10,0/20,0 » ; 5 exécutions (tentatives 0 à 4) ✔. `B_scenb3_gaps.txt` : écarts **2,03/4,04/8,05/16,09** ✔ **exactement** ceux du rapport.
- DBOS B et Restate B : scripts `scenB.sh` (DBOS) et `svc.mjs` (Restate : `transient`, `terminal`, `defaultpolicy`) présents ; **sorties absentes** → ? non vérifiable pour les chiffres (1011/2008/4009 ms, etc.).
- Petit écart de cohérence interne (mineur) : dans `procrastinate/app.py`, le commentaire du code dit `exponential_wait=2  # waits 2,4,8 s` pour `max_attempts=4`, alors que le log observe 4 attentes (2, 4, 8, 16 s) et 5 exécutions. Le rapport rapporte bien les 5 exécutions ; le commentaire du script est simplement faux.

#### 3.3.3 Scénario C — plantage de PostgreSQL (ou du magasin) puis redémarrage

| Système | Observé (rapport) | Interventions |
|---|---|---|
| Absurd | **les workers du SDK tels que livrés meurent en ≈ 0,8 s** (OperationalError) ; pas de progrès pendant 90 s tant que les workers ne sont pas relancés à la main ; ensuite fini en 10 s, aucune tâche perdue, 5 `review` en double. Avec une boucle de reconnexion de 12 lignes (écrite par l'équipe) : terminé 18,9 s après le retour de PG, 0 intervention. Le SDK n'a pas de reconnexion | 1 tel que livré / 0 avec l'enveloppe |
| DBOS | l'application reste vivante, journalise ≈ 12 erreurs « connexion refusée » pendant 12 s de panne ; au retour de PG, 20 finis, sans redémarrage, sans doublon (40 lignes d'effets de bord). *Réserve :* rien n'était en vol pendant la panne | 1 (redémarrer PG seul) |
| Procrastinate | 3 essais (arrêt immédiat, `kill -9` du postmaster + enfants, blip de 3 s) : **le worker ne se reconnecte pas** ; la tâche d'écoute échoue → le worker s'arrête lui-même (`_monitor_side_tasks`) même sur un blip de 3 s ; les jobs en cours finissent puis le processus sort ; 12 jobs `work` restent `todo` jusqu'au redémarrage d'un worker. Aucun job perdu/dupliqué | 1 sans superviseur (systemd) |
| Restate (le serveur est tué, pas PG) | `kill -9` du serveur à +1,5 s, redémarrage sur le même répertoire de données : redémarre sans réparation, leaders réélus, 20 finis ; `work` exécuté 2× chacun (le service a fini le travail pendant que le serveur était éteint, résultat non journalisable) ; `review` une fois | 0 réparation |
| Beads (embarqué) | 60 `bd create` tués à des instants aléatoires 20–600 ms (51 vivants au moment du kill) : base ouverte, 21 tickets distincts valides, le `create` suivant fonctionne, export JSONL concordant. 30 processus `claim` tués → 0 ligne incohérente. Contrôle limité à list/show/export → « aucune corruption observée », **pas** une preuve de robustesse aux crashs | 0 |

**Vérification** :
- Absurd C : `C_noreconnect/final_state.txt` = `main tasks: pending=10 running=10`, `review tasks: pending=5 running=5` ✔ : figé, pas de progression sans redémarrage manuel des workers (`manual_restart_ts` = 1790665502,257 : ✔ existe). `C_noreconnect/analysis.txt` : `work exec 10 unique 10 dups 0`, `review exec 5 unique 5 dups 0`. `C_reconnect/final_state.txt` = tout `completed=20` ✔ ; `C_reconnect/analysis.txt` : `work exec 20 unique 20 dups 0`, `review exec 25 unique 20 dups 5` ✔ « 5 `review` en double ». `run_counts.txt` de `C_reconnect` : `1|completed|10`, `1|failed|10`, `2|completed|10` (10 runs de tentative 1 échoués puis repris). **Nuance** : le rapport attribue « 5 dup reviews » aussi au cas « tel que livré » ; dans les fichiers, ce chiffre (5) figure dans `C_reconnect`, et le cas `C_noreconnect` est archivé **avant** la relance manuelle (état figé), donc « fini en 10 s » après relance manuelle et « 5 dup reviews » pour le cas livré : ? non vérifiable (pas de log post-relance archivé). Les durées « ≈ 0,8 s » (mort des workers), « 18,9 s » : ? non vérifiables (`events.log` et `w_*.log` non archivés).
- DBOS C : `C_timeline.txt` montre `SUCCESS=20` à partir de …390,74 ✔ (20/20 finis, redémarrage inclus, sans intervention sur l'app) ; « ≈ 12 erreurs » et « 40 lignes d'effets de bord » : ? (logs non archivés). Ma remarque : le premier instantané (…368,74) est pris **après** le retour de PG (`snap` ne s'exécute qu'après `pgstart`), donc la chronologie ne montre pas l'état pendant la panne ; le script attend 12 s avant de redémarrer PG. Le script `scenC.sh` fait aussi `pkill -9 -u lab postgres`, ce qui est le **même type de commande** qui avait contaminé les autres agents (mais ici appliqué à sa propre instance sur le port 55402).
- Procrastinate C : script `scenC.sh` présent (modes `immediate` et `kill9`) ; les logs `logs/C_*` (`worker_alive`, ligne des erreurs) : ? non archivés → « le worker s'arrête même sur un blip de 3 s » : ? non vérifiable (un « blip » de 3 s est un 3e mode non couvert par `scenC.sh` avec `DOWN` réglable : `DOWN=${DOWN:-15}` — plausible avec `DOWN=3`).
- Restate D/C : `scenarioD.out` (voir §3.3.4).
- Beads : scripts `kill9.sh` (60 itérations, `kill -9` après `random.uniform(0.02,0.6)`) et `kill9_claim.sh` (3 rondes × workers 6 à 15 = 30 claims tués) ✔ concordent avec « 60 » et « 30 » ; les sorties (51 vivants, 21 valides, 0 incohérent) : ? non archivées.

#### 3.3.4 Scénario D — continuation inter-sessions

| Système | Observé (rapport) |
|---|---|
| Absurd | arrêt de tous les workers, 25 s d'inactivité, nouveaux workers → reprise, 20/20 en 18 s ; 5 `review` en double (tués en vol) ; seule action = démarrer les workers |
| DBOS | tous processus morts → rien ne progresse. Un nouvel exécuteur `w3` vide les 15 workflows ENQUEUED mais **pas** les 5 PENDING de w1 ; un worker en version d'application v2 ne récupère rien ; un processus avec l'identité **d'origine** (id + version) récupère les 5 en ≈ 4,5 s (seul `review` interrompu dupliqué). 1 intervention |
| Procrastinate | 20 jobs déférés sans worker ; un worker démarre, SIGTERM après 5 s, draine ses 4 jobs en cours et sort en 1,4 s ; un nouveau worker 15 s plus tard finit les 20 work + 20 review, 0 doublon. Arrêt propre net |
| Restate | 20 invocations soumises service éteint ; serveur en SIGTERM, attente 60 s, redémarrage : 20 toujours en attente ; service lancé plus tard → 20 terminées (un `pkill -f` accidentel a tué les deux processus brutalement, récupéré aussi) |
| Beads | chaque appel `bd` est un nouveau processus ; claims, dépendances et clôtures survivent. `bd prime` non exercé |

**Vérification** :
- Restate D (`scenarioD.out`) : `submitted 20 with service DOWN` ✔ ; `graceful stop took 0s` ; `5.0M restate-data` (avant) ; `pending after restart: 20` ✔ ; `START 20 END 20 REVIEW 20` ✔ (20 exécutions de `work` et 20 de `review`, **aucun doublon** dans ce scénario D) ; RSS **306 780 Ko** (✔ « ≈ 307 Mo »), **55** threads (✔ « 55–84 »), `221M restate-data` (✔ « ≈ 220 Mo ») ; `Showing 0/0 invocations` (plus rien en attente à la fin). Le script `scenarioD.sh` montre `sleep 60` entre l'arrêt et le redémarrage ✔ « attente 60 s ». « L'arrêt gracieux a pris 0 s » n'est pas commenté par le rapport.
- DBOS D : script `scenD.sh` ✔ présent (étapes D2 : nouvel exécuteur `w3` même version v1 ; D3 : `w1` avec `APP_VER=v2` ; D1 : `w1` v1 original) ; les sorties ne sont pas archivées → les chiffres (15 ENQUEUED drainés, 5 PENDING non repris, 4,5 s) : ? (le chiffre 4,5 s est toutefois cohérent avec les 4,4–4,6 s mesurés en scénario A).
- Absurd D : `scnD.sh` ✔ présent ; sorties (18 s, 5 doublons) : ? non archivées.
- Procrastinate D : pas de script `scenD.sh` : ?.

#### 3.3.5 Observations complémentaires et Beads parallèle
- DBOS SQLite : un processus a survécu à un `kill -9` + redémarrage, 20/20 récupérés ; deux processus démarrant simultanément sur un fichier neuf → course de migration (« table workflow_status already exists »). ? non archivé.
- Beads, écrivains parallèles : 8 processus × 5 créations = 40/40 réussies, 26,3 s (≈ 0,66 s/écriture, ≈ 1,5 écriture/s) ? non archivé. 
- Beads, course au claim : `race.8.*.out` (8 fichiers) : ✔ **exactement un gagnant** (`race.8.6.out` : « Updated issue lab-12w — worker-10 », `exit=0`) et **sept perdants** avec « issue already claimed by agent6 », `exit=1`. C'est cohérent avec « exactement un vainqueur ». Les essais N=2 et N=4 : ? non archivés. Remarque : les agents sont numérotés 1 à 8 et c'est `agent6` qui a gagné, cohérent avec le nom du fichier `race.8.6.out`.

### 3.4 Rapport 04 — Modes de panne

Matrice du rapport (légende : ✔ traité automatiquement, ◐ traité avec config/colle, ✘ non traité, ? inconnu) :

| Panne | Absurd | DBOS (sans Conductor) | Procrastinate | Restate | Beads |
|---|---|---|---|---|---|
| Worker SIGKILL, un autre worker vivant | ✔ après le bail (≈ 10 s configuré) *si un worker qui interroge a un slot libre* (7–22 s) | ✘ le survivant ne reprend pas ; il faut redémarrer avec le même `executor_id` + `application_version` | ✘ par défaut ; ◐ avec tâche périodique maison (24,7 s meilleur cas, ≈ 90 s pire cas INFERENCE) | ◐ le serveur réessaie avec backoff ; il faut que le service revienne | ✘ `bd reclaim` manuel ; TTL 5 min |
| Étape terminée avant le crash | ✔ checkpoint réutilisé | ✔ rejouée depuis `operation_outputs` | ✘ pas de checkpoint : repart de zéro | ✔ rejeu du journal (mais résultat perdu si le serveur est arrêté à cet instant → 2× `work`) | n/a |
| Effet de bord de l'étape interrompue | au moins une fois (5 doublons) | au moins une fois (5) | au moins une fois (4) | au moins une fois (2×) | n/a |
| Crash PG / magasin | ✘ workers du SDK meurent < 1 s ; ◐ boucle de reconnexion de 12 lignes | ✔ l'application se rétablit | ✘ le worker s'arrête même sur 3 s ; superviseur requis | ✔ (kill -9 serveur, même répertoire) | ✔ embarqué : aucune corruption observée (contrôles limités) |
| Système arrêté puis repris | ✔ | ◐ seulement même executor id + même version de code | ✔ | ✔ | ✔ |
| Échec transitoire | ✔ (défaut : **aucune stratégie → immédiat, 5 tentatives < 1 s**) | ✔ | ✔ (granularité 5 s) | ✔ (défaut 70 tentatives puis pause) | ✘ |
| Échec terminal | tâche `failed`, tri manuel | workflow ERROR ; `max_recovery_attempts` 100 puis dead-letter | job `failed` | en pause (défaut) ou tué | n/a |
| Étape plus longue que le bail | ✘ réexécutée alors qu'elle vit (12 `review` en double) | pas de bail | heartbeat au niveau du worker (10 s/30 s), pas par job | timeouts 1 min / 10 min par défaut (non testé > 1 min) | bail 5 min, `bd heartbeat` requis |
| Worker zombie après reprise | état du run clôturé (AB002) ; **effets de bord non clôturés** | n/a | ✘ issue #1633 | clôturé par le serveur (INFERENCE) | ✔ heartbeat tardif refusé, clôture par non-propriétaire refusée |
| Déploiement de code pendant du travail en vol | ✔ (l'état est de la donnée) | ✘ version = md5 du source → l'ancien PENDING est isolé | ✔ | ✔ (non testé) | n/a |
| Cycle de dépendances | pas de graphe | code | pas de graphe | code | non testé (UNKNOWN) |

Dix modes de panne transverses (INFERENCE sauf mention) retenus par le rapport :
1. **« Au moins une fois » est universel** (OBSERVED sur les 4 moteurs). Tout effet de bord hors du magasin (git push, commentaire de PR, écriture de fichier, appel d'API facturé) a besoin de sa propre clé d'idempotence ou d'une écriture clôturée. « Pour des agents de code/recherche, c'est le risque de justesse dominant, pas la mécanique des files. »
2. **Bail vs durée d'étape** : un bail trop court = exécution en double d'un travailleur vivant (OBSERVED avec Absurd).
3. **La reprise dépend de la vivacité de quelque chose** (worker à slot libre pour Absurd, votre tâche périodique pour Procrastinate, le même executor id pour DBOS, un minuteur pour Beads, le retour du service pour Restate). « Faible intervention » signifie en réalité « un superviseur + une boucle de reprise à vous ».
4. **Forme d'interblocage par attente dans un worker (Absurd)** : un parent qui attend un enfant occupe un slot ; si les N slots sont tenus par des parents, les enfants sont affamés (INFERENCE, cohérent avec le 21,8 s / 52 s ; **pas testé jusqu'à l'interblocage**).
5. **Défauts silencieux** : Absurd retry immédiat par défaut ; Procrastinate bloqué à jamais par défaut ; DBOS `local` + version = hash de source ; Restate bind `[::]` ; Beads build CGO.
6. **Maintenance jeune ou concentrée** : Absurd 1 auteur/Alpha ; Procrastinate et DBOS bus factor ≈ 1–2 ; Beads agitation extrême ; Restate équipe la plus saine mais artefact le plus lourd.
7. **Deux sources de vérité** : Restate (RocksDB) ou Beads (Dolt) à côté de PG contredit « une seule autorité par sujet » sauf s'ils sont la seule autorité du sujet.
8. **Lacunes d'observabilité** : sorties picklées DBOS opaques ; Beads embarqué sans SQL/doctor ; Absurd/Procrastinate lisibles en SQL.
9. **Angle mort des suites de test** : ni Absurd, ni Procrastinate, ni (tel que lu) DBOS n'ont de test SIGKILL/crash-PG de bout en bout ; Restate a du chaos au niveau cluster seulement. **Les expériences de cette lane sont la seule preuve au niveau kill ici, et ce sont des essais uniques.**
10. **Couplage à l'environnement** : la suite d'Absurd exige Docker + PG16 et a eu 4 échecs sous PG 18 ; PG 18 non vérifié en amont pour Absurd (UNKNOWN) ; Procrastinate a une CI PG 14–18.

### 3.5 Rapport 05 — Coût d'exploitation

Tableau comparatif du rapport :

| Dimension | Absurd | DBOS (Py) | Procrastinate | Restate | Beads |
|---|---|---|---|---|---|
| Complexité du cœur | 3150 SQL + 2317 SDK ; lisible en une journée (INFERENCE) | ~32,7k Py | ~8,1k Py+SQL | ~283k Rust, 984 crates | ~371k Go |
| Services requis | PG | PG (ou SQLite) | PG | serveur Restate (+ votre endpoint) | aucun en embarqué ; serveur Dolt pour multi-écrivain |
| Colle à écrire | boucle de reconnexion ; stratégie de retry ; nettoyage planifié ; DAG/fan-in | superviseur à executor id stable + version épinglée ; reprise multi-exécuteurs (ou Conductor) | tâche périodique de relance ; superviseur ; chaînage ; DAG | idempotence des effets de bord ; enregistrement ; patron pour longues étapes | minuteur `bd reclaim` ; tout le côté runtime |
| Modèle d'état | 5 tables PG/file, SQL clair | ~11 tables PG, blobs picklés | 4 tables PG, SQL clair | journal+RocksDB embarqués, SQL via DataFusion | Dolt, pas de SQL en embarqué |
| Cycle de vie worker | pull, bail, heartbeat de checkpoint | l'exécuteur possède les PENDING ; reprise au lancement | pull, heartbeat 10 s / timeout 30 s | le serveur pousse en HTTP/2 | l'agent réclame par CLI ; bail 5 min |
| Graphe de dépendances | ✘ | code | ✘ | code | ✔ natif (19 types) |
| Temps d'installation (OBSERVED) | 19 s schéma ; ≈ 10 min premier pipeline | pip 6,3 s ; ≈ 20 min | pip 9 s ; ≈ 10 min | npm 11 s ; ≈ 2 min (+ correctif IPv6) | 1er build 3 min 40 ; init 4,9 s |
| Artefact/mémoire | pip, petit | pip, petit | pip, petit | binaire 225 Mo ; RSS 275–307 Mo ; 220 Mo de données | binaire 214 Mo |
| Charge opérateur (1–5, INFERENCE) | 2 | 2–3 (4 si basculement sans Conductor) | 2 | 2 | 2 (mémoire), inadapté runtime |
| Licence | Apache-2.0 | MIT (plan de contrôle commercial) | MIT | BSL 1.1 (usage interne OK) | MIT |
| Risque de maintenance | HIGH | MED | MED | LOW-MED | HIGH |

Interventions opérateur réellement observées (rapport `05` §2) :

| Scénario | Absurd | DBOS | Procrastinate | Restate | Beads |
|---|---|---|---|---|---|
| A : SIGKILL worker | 0 | 1 | ∞ par défaut / 0 après 1 config | 1 | 1 |
| B : échec transitoire | 0 (terminal = tri) | 0 (terminal = tri) | 0 | 0 | n/a |
| C : crash du magasin | 1 (0 avec 12 lignes) | 1 (PG seul) | 1 (superviseur) | 0 réparation | 0 |
| D : reprise à froid | 0 | 1 (si id/version diffèrent) | 0 | 0 | 0 |

Opérations continues (INFERENCE) : les options PG ajoutent des tables/fonctions au PG déjà exploité, sans nouvelle histoire de sauvegarde/HA, mais les `UPDATE` à forte rotation sur tâches/baux impliquent du **bloat/vacuum non mesuré (UNKNOWN)** ; Restate/Beads ajoutent un second magasin d'état ; **tout système qui récupère du travail exige un superviseur de processus** (systemd/K8s) et des alertes (lignes bloquées au-delà du bail, compte de `failed`, âge du plus ancien prêt, audit de doublons d'effets, connectivité PG).

Vérifié dans les bruts : l'empreinte Restate (§3.3.4). Les temps d'installation, tailles de binaires, décomptes de LOC : ? non vérifiables (pas de clone).

### 3.6 Rapport 06 — Adjudication (le verdict)

Cinq constats de tête :
1. **Aucun candidat n'est clé en main.**
2. **La reprise n'est jamais gratuite** : chacun a exigé une « colle » de l'opérateur.
3. **« Au moins une fois » partout** : l'idempotence des effets de bord est une obligation de conception quel que soit le choix.
4. **Simplicité ≠ moindre intervention** : l'artefact le plus lourd (Restate) a demandé le moins de réparations ; le plus simple (Procrastinate) a demandé une tâche de reprise maison et un superviseur pour arriver à parité.
5. **La « preuve de dépendance » est une lacune chez tous** : le modèle dépendances/preuves reste du « custom » dans la doctrine REUSE→…→CUSTOM.

(Verdicts par candidat : voir §4.)

---

## 4. Candidats / méthodes évalués un par un

Le rapport ne donne pas de note chiffrée mais un verdict et des conditions. Voici pour chaque candidat : verdict, justification chiffrée, ce qui a été vérifié, et **ce qui changerait le verdict** (`06` §4 et §2).

### 4.1 Absurd — **ADAPT** (rang 1)
- Justification (rapport) : seul candidat où le mécanisme complet (bail, reprise, checkpoints, retries, événements) tient en ~3k lignes SQL lisibles dans le PG déjà autoritatif ; 0 intervention dans les essais kill/retry/reprise à froid ; tests SDK PG 18.6 : 93/93.
- Confirmé par mes vérifications : reprise par bail en 7,1–10,1 s avec worker libre (`logs/A_*`), pas de doublon `work` quand l'étape est checkpointée, retries exponentiels aux écarts attendus (2,03/4,05 s), échec terminal à 3 tentatives, reprise à froid (`D` non archivé mais scénario cohérent).
- Bloquants/conditions : 1 seul auteur + Alpha + code de bail jeune → à traiter comme **forkable/vendorisable** (Apache-2.0), épingler une version ; envelopper avec boucle de reconnexion + stratégie de retry obligatoire ; **pas de DAG** (tables maison) ; 4 échecs SQL sous PG 18 à analyser ; `claim_timeout` vs longues étapes d'agent ; la reprise exige un worker libre qui interroge ; bloat sous rotation non testé.
- Ce qui ferait monter/descendre : Absurd gagne un 2e mainteneur, passe en beta, ajoute un helper de reconnexion/une stratégie de retry par défaut, ou l'analyse des 4 échecs PG 18 révèle un bug runtime (→ selon le cas plus haut ou plus bas).
- Mon commentaire : le « 0 intervention » du verdict s'entend pour A, B et D ; en C il faut 1 intervention sans la boucle maison ; et l'essai `A_await_spare` (12 doublons `review`, 3 `review` échouées) montre que la configuration de bail peut, à elle seule, casser la garantie. Le verdict ADAPT (et non ADOPT) l'intègre.

### 4.2 Procrastinate — **ADAPT conditionnel / repli** (rang 2)
- Justification : file PG simple la plus mûre (CI PG 14–18, MIT, lisible en SQL, arrêt propre net — vérifié par le rapport en D : SIGTERM, drainage de 4 jobs, sortie en 1,4 s ; bon retry). Retries vérifiés exactement dans `logs/B_scenb2_gaps.txt` et `B_scenb3_gaps.txt`.
- Bloquants : pas de checkpoints (repart de zéro), reprise des jobs bloqués = tâche à écrire soi-même (granularité cron 1 min → ≈ 90 s pire cas, INFERENCE), le worker sort à la moindre coupure DB, issue #1633 (zombie), pas de DAG. Vaut la peine seulement si la durabilité par étape n'est **pas** requise.

### 4.3 DBOS Transact — **PARK** (rang 3)
- Justification : meilleure reprise de rejeu d'étapes embarquée, a survécu à une panne PG sans redémarrage ; mais la reprise d'un exécuteur mort est le travail du Conductor commercial.
- Confirmé dans les bruts : `A1_timeline_phase1.txt` (5 workflows PENDING pendant 48 s sans reprise par w2) ; réserve : l'anomalie `w2` en phase 2 (§3.3.1, §7).
- Conditions de réouverture : la reprise automatique d'un exécuteur mort devient disponible en OSS → ADAPT ; ou un superviseur avec executor ids stables est acceptable, ou la licence Conductor est acceptable. Code modifié = travail PENDING isolé (version = hash du source) ; sorties picklées opaques.

### 4.4 Restate — **PARK** (rang 4)
- Justification : meilleure tolérance aux pannes « d'origine » (kill -9 du serveur et du service : récupérés, 0 réparation) — partiellement vérifié (`scenarioD.out` : 20/20).
- Bloquants : **second magasin d'état** (RocksDB) qui ne peut pas résider dans PG → conflit avec « une seule autorité »/PG-first sauf autorité séparée acceptée ; BSL 1.1 (usage interne OK, usage de type SaaS restreint) ; workers « poussés » en HTTP, timeouts 1 min/10 min ; binaire 225 Mo.
- Conditions : si la contrainte PG-first est relâchée, Restate devient l'option à moindre intervention.

### 4.5 Beads — **REJECT comme moteur / PARK comme référence** (rang 5)
- Justification : graphe de dépendances natif, `ready`, claim atomique, bail clôturé, état de démarrage à froid — le plus proche pour l'exigence *graphe*. Vérifié : course de claim à N=8, un seul gagnant (`race.8.*.out`).
- Bloquants : pas un runtime (ni retries, ni reprise automatique, TTL fixe 5 min) ; Dolt ≠ PG ; agitation énorme (1558 commits / 90 j, 59 correctifs de corruption/perte de données / 90 j, 896 issues ouvertes) ; pas de SQL/doctor en mode embarqué ; écritures sérialisées ≈ 0,6 s. Sa sémantique de dépendances peut servir de lecture.

### 4.6 Candidats non approfondis (aucune expérience)
| Candidat | Verdict | Justification | Réserve |
|---|---|---|---|
| River (Go) | **PARK (fit UNKNOWN)** | rescuer automatique 30 s (PROVEN en source), 6 tables, PG | non exécuté ; le langage doit convenir ; workflows = River Pro ; MPL-2.0. « Si le vrai dépôt est en Go, River devient candidat de premier rang (test kill à faire) » |
| pgqueuer | **PARK** | requeue par heartbeat en source ; ~12k lignes | non exécuté ; 1 auteur ; pas de graphe |
| LangGraph | **REJECT comme orchestrateur** | checkpointer seul, aucun bail/heartbeat (PROVEN par absence) | pourrait rester utile comme bibliothèque de graphe intra-run (non évalué) |
| Temporal, Hatchet, Inngest, Prefect, Conductor, Airflow/Dagster, Argo, Kestra, Windmill | **REJECT (priorité simplicité)** | piles multi-services/cluster ; Inngest SSPL ; Windmill AGPL | rejet sur l'infrastructure requise (DOCUMENTED_CLAIM + lecture de config), **pas** sur une panne mesurée |
| Celery, Dramatiq, RQ | **REJECT** | courtier supplémentaire ; redélivrance par visibility-timeout → doublons (DOCUMENTED_CLAIM) | — |
| Table de baux PG maison (SKIP LOCKED) | **Patron de référence** | Absurd en est « une instance testée » | écueils : vue « incohérente » de SKIP LOCKED, clôture par propriétaire du bail, utiliser `now()` de la base, bloat, cycles |

### 4.7 Ce qui changerait les verdicts (`06` §4, reproduit)
- Absurd : 2e mainteneur, beta, helper de reconnexion, stratégie par défaut, ou cause racine des 4 échecs PG 18.
- DBOS : reprise en bibliothèque d'un exécuteur mort en OSS → ADAPT.
- Contrainte PG-first relâchée → Restate devient l'option à moindre intervention.
- Vrai dépôt en Go → River de premier rang (test kill à faire).
- Test de longue durée (soak) montrant du bloat de la table de baux ou une latence de claim → toutes les options basées sur des files PG se dégradent ensemble.

---

## 5. « Bloc final » — le verdict tel quel, et explication ligne par ligne

Cette lane n'a **pas de bloc de paramètres gelés** (pas de config de stratégie). Le « bloc final » est le tableau d'adjudication `06_FINAL_ADJUDICATION.md` §2. Je le reproduis tel quel :

```
| Rank | Candidate | Verdict | One-line justification | Blocking conditions / what to verify against the real repo |
| 1 | Absurd | ADAPT | Only candidate where the whole mechanism (lease, reclaim, checkpoints, retries, events) is ~3k readable lines of SQL in the PG that is already authoritative; 0 interventions in kill/retry/cold-restart runs; PG 18.6 SDK tests 93/93 | Bus factor 1 + Alpha + young lease code → treat as vendorable/forkable (Apache-2.0), pin a version; wrap with reconnect loop and mandatory retry strategy; no DAG (custom tables); 4 SQL-suite failures on PG 18 need root-causing; claim_timeout vs long agent steps; reclaim needs a free polling worker; bloat under churn untested |
| 2 | Procrastinate | ADAPT (conditional / fallback) | Most mature simple PG queue (CI PG 14–18, MIT, SQL-queryable, clean graceful shutdown, good retry) | No checkpoints (restart from zero), stalled recovery is opt-in DIY (min cron granularity 1 min → ≈90 s worst, INFERENCE), worker exits on any DB blip, issue #1633 zombie-worker hazard, no DAG; only worthwhile if per-step durability is not required |
| 3 | DBOS Transact | PARK | Best embedded step-replay and survived PG outage without restart, but failover is the commercial Conductor's job | Takeover of a dead executor is not automatic in OSS (PROVEN); code change strands PENDING work (default version = source hash); pickled outputs opaque. Revisit only if a supervisor with stable executor ids is acceptable or Conductor licensing is |
| 4 | Restate | PARK | Best out-of-box crash tolerance (server kill -9 and service kill recovered, 0 repairs) | Second stateful authority (RocksDB) that cannot live in PG → conflicts with "one authoritative source per concern" / PostgreSQL-first unless a separate authority is acceptable; BSL 1.1 (internal use fine; SaaS-style use restricted); push-style HTTP workers, 1 m/10 m timeouts; 225 MB binary. Revisit if the PG-first constraint is relaxed |
| 5 | Beads | REJECT as runtime / PARK as reference | Native dependency graph, ready, atomic claim, fenced lease, cold-start state — the closest match on the graph requirement | Not a worker runtime (no retries, no auto-reclaim, TTL fixed 5 min); Dolt not PG; huge churn (1,558 commits/90 d, 59 corruption/data-loss fixes/90 d, 896 open issues); embedded mode has no SQL/doctor; serialised ≈0.6 s writes. Its dependency semantics may be useful as reading material |
| – | River (Go) | PARK (UNKNOWN fit) | Simplest automatic rescuer (30 s default, PROVEN in source), 6 tables, PG | Not run; language must fit; workflows are River Pro; MPL-2.0 |
| – | pgqueuer | PARK | Heartbeat requeue in source; ~12k LOC | Not run; 1 author; no graph |
| – | LangGraph | REJECT as orchestrator | Checkpointer only; no lease/heartbeat (PROVEN by absence) | Could still serve as an in-run agent graph library (not evaluated here) |
| – | Temporal, Hatchet, Inngest, Prefect, Conductor, Airflow/Dagster, Argo, Kestra, Windmill | REJECT (on simplicity priority) | Multi-service or cluster stacks; Inngest SSPL; Windmill AGPL | Rejection is on required infrastructure (DOCUMENTED_CLAIM + config reading), not on measured failure — none was run |
| – | Celery, Dramatiq, RQ | REJECT | Extra broker; visibility-timeout redelivery duplicates (DOCUMENTED_CLAIM) | – |
| – | DIY PG SKIP LOCKED lease table | Reference pattern | Absurd is effectively a tested instance of this pattern | Pitfalls (fetched PG docs): SKIP LOCKED gives an "inconsistent view"; fence by lease owner; use DB now(); bloat; cycles |
```

Recommandation de forme (`06` §3, verbatim en substance) : « Under REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST, the evidence points to COMPOSE: an existing PG-native runtime (Absurd first; Procrastinate if step durability is unnecessary) + a small custom dependency/evidence layer, with idempotency for external side effects and an owned supervisor loop. This is a statement about the external landscape only. »

### 5.1 Explication de chaque « clé » du tableau
- **Rank** : ordre d'intérêt (jugement, pas un score). Les lignes sans rang (« – ») sont des candidats non approfondis.
- **Candidate** : le logiciel.
- **Verdict** : ADAPT = on l'utiliserait en l'enveloppant/modifiant ; PARK = on le range avec des conditions de réouverture ; REJECT = écarté ; « Reference pattern » = pas un produit, une idée à imiter.
- **One-line justification** : la raison principale du verdict, en une phrase.
- **Blocking conditions / what to verify against the real repo** : ce qui bloque, ou ce qu'il faudra vérifier plus tard contre le vrai dépôt AurumShift (à ne pas confondre avec une garantie de compatibilité : le rapport dit explicitement qu'il n'en affirme aucune).
- Détail de quelques termes du tableau : *bus factor 1* = un seul mainteneur ; *Alpha* = le projet se déclare non stable ; *vendorable/forkable* = on peut copier/forker le code (Apache-2.0 l'autorise) pour ne pas dépendre du mainteneur ; *reconnect loop* = boucle qui relance le worker si la base coupe ; *mandatory retry strategy* = définir explicitement la stratégie de réessai (sinon Absurd réessaie immédiatement) ; *claim_timeout* = durée du bail ; *free polling worker* = un worker qui interroge encore et a un emplacement libre, seul à pouvoir balayer les baux expirés ; *bloat* = gonflement des tables PG par les mises à jour fréquentes ; *conductor* = plan de contrôle commercial de DBOS ; *executor id* = identité de l'ouvrier DBOS ; *pickled outputs* = sorties sérialisées en format Python binaire ; *BSL 1.1* = licence « Business Source » : usage interne permis, service géré public restreint, devient Apache 4 ans plus tard ; *SSPL* = licence très restrictive pour les services cloud ; *AGPL* = licence copyleft réseau (impose de publier vos modifications si vous offrez le service) ; *MPL-2.0* = copyleft au niveau du fichier ; *River Pro* = version payante de River ; *visibility-timeout* = mécanisme de redélivrance de Redis/SQS : si pas d'accusé de réception à temps, le message est renvoyé (source de doublons).

### 5.2 Statut de confiance déclaré (`06` §5)
- Confiance **moyenne** sur le classement 1–4 ; **faible** sur les temps relatifs.
- Le résultat favorable d'Absurd « reflète en partie que son expérience tournait avec bail 10 s et assez de workers libres ; le cas saturé a pris 21,8 s et ≈ 52 s pour finir ». Je l'ai vérifié (§3.3.1).
- Non vérifié : CI Docker amont, historiques d'issues fermées, issues ouvertes de Restate, durabilité en cas de coupure de courant, comportement multi-machines, posture de sécurité, candidats non approfondis au-delà de la lecture.

---

## 6. Contrôles de validité

### 6.1 Tests de fuite / lookahead
Non applicable au sens financier : cette lane ne manipule ni séries temporelles ni modèle. Le rapport ne parle pas de PIT (point-in-time). Le seul « lookahead » concevable serait l'utilisation d'un résultat de test pour choisir la configuration d'un autre : non observé ; les configurations (bail 10 s, backoff base 2 s) sont fixées dans les scripts avant les essais (`scnA.sh`, `scnB.sh`).

### 6.2 Déterminisme et répétition
- Essais uniques, non répétés (`00_SCOPE.md` : « Treat all timings as single-run, non-benchmark »). Aucune graine. Pas d'intervalle de confiance ni d'écart-type — normal vu N=1.
- Les scénarios Absurd A ont **cinq variantes** (`A_k1.5`, `A_k4.5`, `A_await`, `A_await_free`, `A_await_spare`) : elles donnent 10,1 s, 9,5 s, 21,8 s, 7,1 s et (pour le dernier) 21,9 s de délai au premier échec de bail. Cela donne une idée de dispersion (7 à 22 s) mais expliquée par la saturation, non par le hasard.

### 6.3 Contrôles négatifs / positifs
- **Contrôles positifs** (un mécanisme qui doit fonctionner) : reprise par bail d'Absurd ; retries avec backoff ; reprise à froid ; course de claim Beads (un gagnant). Tous observés.
- **Contrôles négatifs** (un mécanisme qui *ne doit pas* fonctionner) : DBOS sans reprise par le survivant ; Procrastinate sans relance automatique ; Beads sans réclamation automatique ; Absurd sans reconnexion. Chaque « absence » a été à la fois lue dans le code (PROVEN) et observée, ce qui est une bonne pratique.
- **Pas de test de la vraie charge d'agent** : une étape de ~3 s ne ressemble pas à une étape d'agent de plusieurs minutes (limite reconnue : Restate > 1 min non testé).

### 6.4 Erreurs corrigées en cours de route / écarts déclarés
- Contamination croisée : deux `pkill -9 postgres` inter-agents (Absurd avant C ; Procrastinate dans un essai B). Essais relancés ou marqués ; les logs gardent les essais avortés (`00_SCOPE.md`). Je ne peux pas retrouver dans les fichiers **quels** essais sont concernés, sauf que `procrastinate` mentionne une exécution interrompue.
- `pgrep -f` de l'opérateur qui a tué aussi son propre shell (`restate/scenarioA_notes.txt`).
- DBOS : 2 corrections d'API (`register_queue` après `launch()` en 3.x) pendant le montage.
- Absurd : fixture de test corrigée pour PG 18.6/sans Docker (`02_TOP5.md`).
- Beads : build CGO échoué → `-tags gms_pure_go`.
- Restate : liaison IPv6 échouée → `bind-ip = "127.0.0.1"` (fichier `restate.toml` confirme les ports 55411–55413 en `127.0.0.1` ✔).
- Le lead a re-vérifié 4 affirmations dans le code (Absurd bail/SKIP LOCKED, DBOS reprise au démarrage, Procrastinate pas de relance auto, Beads TTL 5 min).

### 6.5 Provenance et limites de mes propres vérifications
- J'ai relu les 7 rapports, tous les scripts et tous les fichiers de résultats du dossier. **Je n'ai pas cloné les 12 dépôts** ni relu le code amont : toutes les lignes `fichier:ligne` du rapport (ex. `absurd.sql:965`, `_dbos.py:697-711`, `worker.py:445`, `lease.go:19-30`) sont ? non vérifiables ici. Je ne peux donc distinguer que « ce que le rapport affirme » de « ce que les fichiers de résultats archivés confirment ».
- Table de vérification de chiffres (≥ 10) : voir le tableau ci-dessous.

| # | Chiffre / affirmation du rapport | Fichier de vérification | Résultat |
|---|---|---|---|
| 1 | Absurd, kill +1,5 s → tentative 2 en 10,1 s ; 5 doublons `work` | `experiments/absurd/logs/A_k1.5/{analysis,attempt_gt1_runs}.txt` | ✔ 10,14 s, 5 doublons (tâches 0–4) |
| 2 | Absurd, kill +4,5 s → 9,5 s | `logs/A_k4.5/analysis.txt` | ✔ 9,52 s, 5 doublons (tâches 15–19) |
| 3 | Absurd saturé : 21,8 s ; ≈ 52 s pour finir | `logs/A_await/*` | ✔ 21,80 s ; 52 sondages (53,4 s) |
| 4 | Absurd worker libre : 7,1 s | `logs/A_await_free/*` | ✔ 7,12 s |
| 5 | Absurd : 0 doublon `work` si checkpointé | `logs/A_await/analysis.txt`, `A_await_free/analysis.txt` | ✔ 0 (« no attempt>1 side effects ») |
| 6 | Absurd : 12 `review` en double (bail trop court) | `logs/A_await_spare/analysis.txt` | ✔ 12 (32 exécutions/20 tâches) mais ✘ formulation « sans crash » (kill présent) et 3 `review` échouées non mentionnées |
| 7 | Absurd B : écarts 2,03 s / 4,05 s ; 3,06 s / 4,11 s | `logs/B_transient_2tasks/task0_timeline.txt`, `B_transient/task0_timeline.txt` | ✔ |
| 8 | Absurd B terminal : 20 échecs à la tentative 3, `review` jamais créé | `logs/B_terminal/{final_state,task_summary,analysis}.txt` | ✔ |
| 9 | Absurd C : sans reconnexion, figé ; avec reconnexion, 20/20 et 5 `review` en double | `logs/C_noreconnect/final_state.txt`, `logs/C_reconnect/{final_state,analysis}.txt` | ✔ (figé : pending=10 running=10 ; reco : completed=20, dups 5) ; « 0,8 s », « 18,9 s » : ? |
| 10 | DBOS A : 5 workflows PENDING bloqués sans reprise, ≈ 50 s (A1) / 20 s (A2) | `experiments/dbos/A1_timeline_phase1.txt`, `A2_timeline_phase1.txt`, `*_stuck.txt` | ✔ (48,2 s / 20,8 s) |
| 11 | DBOS : reprise après redémarrage ≈ 6,5 s | `A*_timeline_phase2.txt` | ✔ approx. (4,4–4,6 s depuis le 1er instantané de phase 2 ; instant exact du redémarrage non enregistré) ; anomalie `w2` (§7) |
| 12 | DBOS C : 20/20 finis après panne PG, sans redémarrage de l'app | `experiments/dbos/C_timeline.txt` | ✔ (SUCCESS=20) ; 12 erreurs, 40 lignes : ? |
| 13 | Procrastinate B : 5,0/5,0/10,0/20,0 s et 2,03/4,04/8,05/16,09 s ; 5 exécutions | `procrastinate/logs/B_scenb2_gaps.txt`, `B_scenb3_gaps.txt` | ✔ exact |
| 14 | Procrastinate A : ≥ 140 s bloqué ; 24,7 s avec tâche périodique | — | ? aucun log |
| 15 | Restate D : 20 en attente après redémarrage ; 20/20 terminés ; RSS ≈ 307 Mo ; 55 threads ; 221 Mo | `restate/scenarioD.out` | ✔ (306 780 Ko, 55, 221M) |
| 16 | Restate A : `work` 40 exécutions pour 20 tâches | `restate/scenarioA_notes.txt` (1 ligne) | ? |
| 17 | Beads : course au claim, 1 gagnant (N=8) | `beads/race.8.{1..8}.out` | ✔ (un `exit=0`, sept `exit=1`) ; N=2,4 : ? |
| 18 | Beads : 60 kills, 21 valides ; 30 claims tués, 0 incohérent ; 8×5 écritures en 26,3 s | `beads/kill9*.sh` (scripts seulement) | ? (les scripts concordent avec 60 et 30 ; sorties non archivées) |
| 19 | Taille : « 106 fichiers » | `git ls-tree` | ✔ 106 (+ `.gitignore` = 107 de la PR) |
| 20 | PR : « 23 candidats criblés, 12 clonés, 5 approfondis » | corps de la PR #1, `00_SCOPE.md`, `01_LANDSCAPE.md` | ✔ cohérent entre les trois ; 12 clones non vérifiables |

Bilan : 14 chiffres ou groupes de chiffres ✔, 1 partiellement ✘ (formulation du cas 12 doublons), plusieurs ? à cause d'archives brutes manquantes.

---

## 7. Critique indépendante

### 7.1 Points forts (à ne pas oublier)
- Honnêteté méthodologique rare : chaque rapport commence par ses limites ; les deux contaminations croisées sont divulguées ; les étiquettes PROVEN/OBSERVED/INFERENCE sont utilisées de bout en bout ; les verdicts sont conditionnels et donnent leurs conditions de changement.
- Les « absences » (pas de reprise automatique dans DBOS, Procrastinate, Beads) sont lues dans le code *et* observées.
- Le rapport insiste, à juste titre, sur le fait que l'effet de bord « au moins une fois » est le vrai risque de justesse.

### 7.2 Points faibles et choix fragiles

**Échelle et statistique**
1. **N = 1 par scénario**, 20 tâches de 3 s, 4–5 en parallèle. Aucun intervalle de confiance. Les comparaisons de temps entre systèmes (« 24,7 s » contre « 21,8 s » etc.) ne sont pas interprétables comme des différences réelles ; le rapport le dit, mais les tableaux de `05` les placent côte à côte.
2. **Charges non identiques** : un système attend un enfant dans une autre file (Absurd), un autre chaîne deux étapes (DBOS, Restate), un troisième dépose la seconde étape à la main (Procrastinate). Les doublons et délais ne sont pas strictement comparables.
3. **Machine partagée par six agents** : les latences sont contaminées par d'autres charges ; deux cross-kills prouvent le manque d'isolation.

**Choix en bord de grille / hypothèses fragiles**
4. **Bail de 10 s** (défaut SQL = 30 s) : choisi pour accélérer les essais. Or la reprise « en 7–10 s » est la conséquence directe de ce réglage ; avec un bail de 30 s (défaut) ou de plusieurs minutes (étapes d'agent longues), les délais seraient à multiplier. Et un bail trop court crée l'effet inverse (doublons vivants). Le résultat « 0 intervention » pour Absurd est donc **conditionné à un réglage que l'on ne sait pas adapté à des étapes d'agent réelles**.
5. **Le cas « saturé » (21,8 s)** n'est pas une pathologie extrême : avec des parents en attente occupant tous les slots, le rapport n'a **pas** testé l'interblocage complet (mode 4 du rapport 04, « pas testé jusqu'à l'interblocage »).
6. **Étapes de 3 s vs agents de plusieurs minutes** : les seuils de Restate (1 min inactivité, 10 min abandon) et de Beads (5 min) ne sont pas testés contre des étapes longues.
7. **Interventions comptées par convention** : « intervention » = action humaine hors démarrage normal. Mais démarrer une boucle de reconnexion écrite par l'équipe compte « 0 » pour Absurd alors que c'est du code à écrire et maintenir ; à l'inverse, l'exploitation d'un superviseur (systemd) n'est pas comptée. La note « 0 » de la colonne « C » d'Absurd est donc **avec l'enveloppe maison**.
8. **Les verdicts ADAPT vs PARK reposent sur une préférence (PG-first, une autorité)** issue de `claude.md`, non sur une mesure. Restate est le meilleur en tolérance aux pannes observée et il est PARK *par contrainte de doctrine*. C'est explicité, mais le lecteur pressé pourrait croire à une défaite technique.
9. **Le rang 1 d'Absurd repose sur un mainteneur unique, projet Alpha, code de bail vieux de quelques mois** : le verdict ADAPT « forkable » transfère la charge de maintenance vers AurumShift ; le rapport le note, mais l'évalue « HIGH » et classe pourtant Absurd premier.

**Ce que les chiffres ne prouvent pas**
- Ils ne prouvent rien sur : débit, latence sous charge, bloat/vacuum sous rotation, multi-machines, coupure de courant, dérive d'horloge (le bail dépend de l'horloge de la base), sécurité, coûts LLM, comportement à 1000 tâches, comportement après des jours de fonctionnement.
- Ils ne prouvent pas que Procrastinate/DBOS/Restate/Beads seraient « pires » qu'Absurd en production ; ils montrent leurs *défauts de configuration par défaut* et leurs *glues requises* sur un petit banc.
- Le classement 19 candidats non exécutés est purement documentaire.
- « Absurd = 0 intervention » ne signifie pas « pas de surveillance » : le rapport lui-même dit qu'il faut un superviseur + des alertes.

### 7.3 Écarts rapport ↔ résultats bruts, et contradictions internes
1. **Formulation trompeuse « 12 duplicate reviews with no crash »** (`03`, Extra observations) : le seul essai qui produit 12 doublons de `review` (`A_await_spare`) inclut un `SIGKILL M1` et se termine avec **3 tâches `review` échouées**, ce que le rapport ne signale pas. Les 12 doublons interviennent à +47,6 s, donc longtemps après le kill, ce qui appuie l'idée d'un effet de bail sur `review`, mais la configuration exacte (`RCT`, `RCONC`) n'est pas archivée. À rapporter comme : « 12 doublons de `review` et 3 `review` échouées dans l'essai `A_await_spare`, cause exacte non établie par les fichiers ».
2. **Anomalie d'`executor_id` DBOS** en phase 2 des scénarios A1/A2 : après redémarrage de `w1`, les 5 workflows en attente s'affichent sous `w2` (`exec=w2:PENDING=5`) avant de finir. Cela ne prouve pas que `w2` a repris (peut-être une mise à jour de propriétaire par la reprise de `w1`), mais cela contredit en apparence le message net « seul le même executor id reprend ». Le rapport ne l'explique pas. À élucider avant de figer le verdict DBOS (dans le pire cas, DBOS a un chemin de reprise inter-exécuteurs plus généreux que décrit ; dans le meilleur, c'est un artefact de `snap`).
3. **Pièces brutes manquantes** : `events.log`, `sideeffects.log`, `w_*.log` (Absurd), `*_side_effects.log` (DBOS), `C_*` et les journaux de scénarios A et D (Procrastinate), tous les `*.log` de Restate et de Beads, `notes/beads.md` (cité dans `beads/README.txt` : « /tmp/lab/notes/beads.md », hors dépôt). Le rapport 03 cite pourtant `restate/{...*.log}` et `beads/{*.log}` dans sa section « Reproduce » : ils n'existent pas dans l'arbre. Environ la moitié des chiffres de `03` (24,7 s, 18,9 s, 0,8 s, ≥140 s, 40 exécutions Restate, 21 tickets Beads, 26,3 s) ne sont donc pas contrôlables.
4. **« 5 attempts burned in <1 s » (Absurd sans stratégie)** : aucun fichier d'essai correspondant (tous les B utilisent une stratégie exponentielle). C'est PROVEN par lecture de code (défaut), pas OBSERVED.
5. **Confusion possible sur « 5 review en double »** : le rapport attribue ce chiffre au cas « tel que livré » ; il apparaît dans les fichiers uniquement pour `C_reconnect` (`review exec 25 unique 20 dups 5`), tandis que `C_noreconnect` est archivé avant la relance manuelle.
6. **Commentaire de code faux** dans `procrastinate/app.py` (`# waits 2,4,8 s` pour 4 tentatives) vs 4 attentes observées (2/4/8/16 s) et 5 exécutions : sans conséquence, mais illustre que `max_attempts=4` donne 5 exécutions (le rapport le signale correctement).
7. **Rang vs risque** : Absurd est classé n°1 tout en étant noté « HIGH » en risque de maintenance ; Restate est noté « LOW-MED » en risque mais PARK. Ce n'est pas une contradiction (la contrainte PG-first et la simplicité priment) mais c'est une tension à expliciter aux décideurs.
8. **Décomptes de la PR** : la PR annonce 107 fichiers et +1643/−1 ; le dossier contient 106 fichiers (le 107e est `.gitignore`). ✔ pas de contradiction, juste une précision.
9. **Chronologie** : les epoch des logs (`1790665049` à `1790665581`, soit 06:57:29 à 07:06:21 UTC le 2026-09-29) tombent à peu près en même temps que les commits « WIP » (06:56 à 07:10), alors que la PR est datée 06:56:32. Si l'horloge du bac à sable n'est pas décalée, la PR aurait été ouverte avant la fin des essais ; c'est probablement un artefact d'horloge/commit et sans conséquence pour les conclusions. Je ne peux pas le trancher (UNKNOWN).
10. **Scripts codés en dur** : `/tmp/lab/...`, `/home/user/aurumshift-external-research-lab/...` (Procrastinate), ports 55401–55413, `pgstart.sh` non commité (reconnu). Non relançables en l'état.

### 7.4 Biais possibles
- **Biais d'ancrage par la doctrine** : `claude.md` (PG-first, une autorité) fait passer Restate et Beads derrière des solutions PG même si leurs propriétés de reprise sont meilleures ou complémentaires.
- **Biais de disponibilité** : les 5 candidats approfondis sont ceux qui semblaient simples au criblage ; River et pgqueuer, jugés simples, n'ont pas été testés — il se peut que River (rescuer automatique) batte Absurd en robustesse si le langage convient.
- **Biais de l'auteur du banc** : la reconnexion et la stratégie de retry d'Absurd ont été écrites par les testeurs (12 lignes) ; d'autres systèmes n'ont pas reçu le même « coup de pouce » (ex. un wrapper de reconnexion pour Procrastinate). Le rapport le note en partie (« 0 après config unique »).
- **Biais de confirmation** : le verdict « ADAPT » pour deux moteurs PG suit l'hypothèse de départ (« PG-first »).

---

## 8. Comparaison de plusieurs runs/branches

Cette lane n'a **qu'une seule branche, un seul run principal** (la PR #1). Il n'y a pas de deuxième exécution indépendante à comparer. Ce que je peux comparer :
- **Rapport vs fichiers bruts** : voir §6.5 (tableau de vérification) et §7.3.
- **Entre systèmes au sein de la lane** : voir §3.3 et §3.5.
- **Avec la synthèse globale** (`SYNTHESE_LANES.md`, lignes 33 et 80–82, lu seulement pour cette ligne) : elle résume la lane 002 comme « Absurd = ADAPT, Procrastinate = ADAPT (repli), DBOS/Restate = PARK, Beads = REJECT », PR n°1 ouverte non brouillon. ✔ cohérent avec `06`. Le reste de la synthèse n'a pas été lu en détail (non lu).
- **Dispersion interne** : les 5 essais Absurd A donnent des délais de premier échec de bail de 7,1 à 21,9 s ; la cause dominante est la saturation des slots, pas le bruit.

---

## 9. Reproductibilité

### 9.1 Ce qui est fourni
- Les 7 rapports, 22 scripts shell, 8 scripts Python, 1 module Node (`svc.mjs`), configs Restate (`restate.toml`, `default-config.toml`), logs partiels (voir §7.3, point 3).
- Ports privés : Absurd 55401, DBOS 55402, Procrastinate 55403 ; Restate 55411 (ingress), 55412 (admin), 55413 (bind), 55414 (service) ; scripts sous `/tmp/lab/...`.

### 9.2 Dépendances (d'après rapports et scripts)
- PostgreSQL 18.6 extrait du paquet pgdg dans un préfixe privé (`/tmp/lab/pg18root/usr/lib/postgresql/18/bin`), authentification `trust`, un cluster par système (`/tmp/lab/pg/{absurd,dbos,procrastinate}`), lancés par `/tmp/lab/bin/pgstart.sh` (**non commité**).
- Python : `absurd-sdk 0.5.0` (psycopg), `dbos 3.1.0` (psycopg 3.3.6, SQLAlchemy 2.1.1), `procrastinate 3.10.0` ; Node : `@restatedev/restate-sdk`, serveur `restate-server` 1.7.12 ; Go 1.26.7 pour Beads (`go build -tags gms_pure_go -o bd ./cmd/bd`, `bd` 1.3.0).
- Les schémas : Absurd `absurd.sql` (à appliquer), Procrastinate `procrastinate schema --apply` (via `mkdb.sh`), DBOS migrations automatiques.

### 9.3 Commandes (telles que déduites des scripts, non exécutées par moi)
- Absurd : `scnA.sh <secondes avant kill> <dossier>` (variables `EXTRA`, `RCT`, `RCONC`, `M2CONC`, `REVIEW_SECS`), `scnB.sh <FAIL_FIRST> <max_attempts> <dossier>`, `scnC.sh <0|1> <dossier>`, `scnD.sh <dossier>`, `submit.py <n> [max_attempts] [base_secondes]`, `worker.py <file> <claim_timeout> <concurrence> [reconnect]`.
- DBOS : `scenA.sh` (`TAG`, `KILL_AFTER`, `PH1`), `scenB.sh`, `scenC.sh`, `scenD.sh`, `enqueue.py`, `lib.sh`.
- Procrastinate : `mkdb.sh <db>`, `run_worker.sh <db> <nom> [concurrence]`, `defer.py`, `defer_b.py`, `scenC.sh <db> <immediate|kill9>` (env `DOWN`, `RETRY_STALLED=1`).
- Restate : `start_server.sh`, `start_svc.sh`, `scenarioD.sh` (nécessite `RESTATE_ADMIN_URL`).
- Beads : `race.sh <id> <N>`, `kill9.sh`, `kill9_claim.sh`.
- Durée totale des essais : de l'ordre de la dizaine de minutes de mur d'après les epoch des logs (06:57–07:06 UTC) ; les scénarios individuels durent de 20 s à ~2 min. Le montage complet (PG, venvs, clones, builds Go de 3 min 40 s) est plus long. Ce dernier point est mon estimation, non documentée.

### 9.4 Ce qui manque pour relancer proprement
- `pgstart.sh` et la création des clusters PG (reconnu par le rapport).
- Les chemins absolus (`/tmp/lab`, `/home/user/aurumshift-external-research-lab/...`).
- Les scripts de scénarios A/B/D pour Procrastinate et A/B/C pour Restate (seuls `scenarioD.sh` et `svc.mjs` sont livrés).
- Les scripts Beads pour l'expiration de bail et `bd reclaim`.
- Les journaux d'effets de bord et `events.log` qui permettraient de recompter les doublons.
- Le fichier `notes/beads.md` cité par `beads/README.txt`.
- Aucun `requirements.txt`, ni `package.json`, ni conteneur qui figerait les versions (les versions sont dans le texte du rapport).

---

## 10. Implications pratiques pour AurumShift (pistes « à adjuger plus tard »)

Rappel de frontière (`claude.md`) : rien de ce qui suit n'affirme une compatibilité avec AurumShift ; tout est à confronter au dépôt réel.

1. **À adjuger : est-ce que l'orchestration d'agents doit vivre dans le PostgreSQL existant ?** Les deux moteurs PG (Absurd, Procrastinate) correspondent à la contrainte « PG-first » et « une autorité par sujet » ; à confronter à la façon dont AurumShift gère déjà planificateur, files et provenance.
2. **À adjuger : la forme COMPOSE** (un moteur d'exécution + une petite couche « dépendances/preuves » propre) : la couche de preuves relèverait de « CUSTOM » et devrait respecter les règles PIT/provenance/« l'absence de preuve n'est pas une preuve négative » propres à AurumShift, que cette lane ne connaît pas.
3. **À adjuger : politique d'idempotence des effets de bord des agents** (clés d'idempotence sur git push, commentaires de PR, écritures de fichiers, appels facturés) — indépendante du moteur choisi.
4. **À adjuger : superviseur de processus + alertes** (lignes bloquées au-delà du bail, `failed` terminal, âge du plus ancien prêt, audit de doublons, connectivité PG) — obligatoire pour tous les moteurs.
5. **À adjuger : langage du vrai dépôt.** Si Go, River devient un candidat à tester ; si Python, Absurd/Procrastinate/DBOS ; si TypeScript, SDK TS d'Absurd et Restate.
6. **À adjuger : tolérance à un second magasin d'état.** Si la contrainte PG-first n'est pas stricte, Restate est l'option à moindre intervention observée ; si elle l'est, le rejeter reste cohérent.
7. **À adjuger : durée des étapes d'agent réelles** vs bail (`claim_timeout`), timeouts de Restate (1 min/10 min), TTL Beads (5 min). Si les étapes durent des minutes, le découpage en sous-étapes ou le heartbeat fréquent devient une exigence de conception.
8. **À adjuger : licence et gouvernance.** Absurd = un auteur et Alpha → prévoir de le forker/épingler ; DBOS Conductor commercial ; Restate BSL 1.1 ; à valider avec les usages d'AurumShift.
9. **Pistes de lecture** : la sémantique de dépendances de Beads (`blocks`, `parent-child`, `conditional-blocks`, `waits-for`, portes, `ready`) comme inspiration pour le modèle de dépendances/preuves, sans dépendre du produit.

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **[Valeur haute] Rejouer les scénarios A–D avec un bail réaliste et des étapes longues** (1 à 10 min, avec heartbeats) pour Absurd (et, si possible, River et Procrastinate). Ce sont ces paramètres qui décideront du réglage du bail et du risque de doublons vivants.
2. **[Haute] Élucider l'anomalie DBOS `w2`** (§7.3, point 2) : refaire A1/A2 en journalisant `executor_id` par workflow avant/après redémarrage ; décider si DBOS mérite une réouverture.
3. **[Haute] Analyser les 4 échecs de la suite SQL d'Absurd sous PG 18** (bug du harnais vs bug runtime), et rejouer plusieurs fois le scénario A pour obtenir une dispersion (N ≥ 10).
4. **[Haute] Test de saturation d'Absurd** : N parents en attente sur N slots, pour établir si l'interblocage se produit réellement (mode de panne 4).
5. **[Moyenne-haute] Tester River** (si le langage convient) et pgqueuer avec le même banc de kill que pour les cinq autres.
6. **[Moyenne] Mesures de bloat/vacuum et de latence de claim** sous rotation prolongée (soak) sur PG 18.6, pour les deux moteurs PG.
7. **[Moyenne] Archiver les journaux bruts manquants** (`events.log`, `sideeffects.log`, journaux de Procrastinate/Restate/Beads) et les scripts manquants, et remplacer les chemins absolus par des variables d'environnement, avec un `pgstart.sh` versionné.
8. **[Moyenne] Prototype de la couche « dépendances/preuves »** (tables PG maison au-dessus d'Absurd) et de la politique d'idempotence des effets, à évaluer contre le vrai dépôt.
9. **[Basse-moyenne] Tester Beads en mode serveur** (multi-écrivains, dolt push/pull) si son modèle de graphe doit être réutilisé au-delà de la lecture.
10. **[Basse] Restate : étapes > 1 min, promesses durables, coupure de courant, instantanés**.
11. **[Basse] Sécurité et clôture des effets de bord** (fencing des effets externes, pas seulement de l'état du run).

---

## 12. Index des fichiers lus

Base : branche `origin/claude/funny-hopper-3paobd`, dossier `reports/002_agent_orchestration/`. Autres fichiers : `claude.md` (doctrine, lu en entier), `SYNTHESE_LANES.md` (seulement les lignes 33 et 80–82 consultées ; le reste : non lu), API GitHub PR #1 (métadonnées).

**Rapports**
- `00_SCOPE.md` — mission, question, tags de preuve, méthode, environnement et limites.
- `01_LANDSCAPE.md` — 23 candidats, tableau, tailles de code, constats F1–F3.
- `02_TOP5.md` — inspection de source Absurd/DBOS/Procrastinate/Restate/Beads + runner-ups.
- `03_REPRODUCTION.md` — scénarios A–D, observations complémentaires, non testé, reproduction.
- `04_FAILURE_MODES.md` — matrice de pannes, dix modes transverses.
- `05_OPERATIONAL_COST.md` — comparaison de coût, interventions, opérations continues.
- `06_FINAL_ADJUDICATION.md` — constats, verdicts, forme de recommandation, conditions de changement, confiance.

**Absurd (`experiments/absurd/`)**
- `app.py` — tâches `job` (étape `work` + spawn/await `review`) et `review`, journal d'effets de bord ; `FAIL_FIRST`, `WORK_SECS`.
- `worker.py` — lance un worker (file, claim_timeout, concurrence) ; boucle de reconnexion optionnelle (le fameux « wrapper »).
- `submit.py` — soumet N tâches avec `max_attempts` et stratégie exponentielle optionnelle.
- `reset.sh`, `state.sh` — remise à zéro des files, comptage d'états.
- `scnA.sh`, `scnB.sh`, `scnC.sh`, `scnD.sh` — scénarios kill worker / retry / crash PG / reprise à froid.
- `logs/A_await/`, `A_await_free/`, `A_await_spare/`, `A_k1.5/`, `A_k4.5/` — (`*.out`, `analysis.txt`, `attempt_gt1_runs.txt`, `final_state.txt`, `run_counts.txt`) résultats du scénario A.
- `logs/B_terminal/`, `B_transient/`, `B_transient_2tasks/` — (`analysis.txt`, `final_state.txt`, `task0_timeline.txt`, `task_summary.txt`) résultats du scénario B.
- `logs/C_noreconnect/`, `C_reconnect/` — (`analysis.txt`, `final_state.txt`, `run_counts.txt`, `manual_restart_ts`) résultats du scénario C.

**DBOS (`experiments/dbos/`)**
- `app.py`, `enqueue.py`, `lib.sh`, `reset.sh`, `scenA.sh`, `scenB.sh`, `scenC.sh`, `scenD.sh` — application et scénarios.
- `A1_ops.txt`, `A2_ops.txt` — opérations enregistrées (`operation_outputs`) par workflow.
- `A1_stuck.txt`, `A2_stuck.txt` — workflows restés PENDING sous w1.
- `A1_timeline_phase1.txt`, `A1_timeline_phase2.txt`, `A2_timeline_phase1.txt`, `A2_timeline_phase2.txt`, `C_timeline.txt` — chronologies d'états.

**Procrastinate (`experiments/procrastinate/`)**
- `app.py`, `defer.py`, `defer_b.py`, `mkdb.sh`, `q.sh`, `run_worker.sh`, `scenC.sh` — application et scénario C.
- `logs/B_scenb2_gaps.txt`, `logs/B_scenb3_gaps.txt` — écarts entre tentatives (polling 5 s / 0,5 s).

**Restate (`experiments/restate/`)**
- `restate.toml`, `default-config.toml` (seulement l'en-tête lu ; le reste du fichier : non lu), `start_server.sh`, `start_svc.sh`, `svc.mjs`, `scenarioD.sh`, `scenarioD.out`, `scenarioA_notes.txt`.

**Beads (`experiments/beads/`)**
- `README.txt`, `race.sh`, `race.8.1.out` … `race.8.8.out`, `kill9.sh`, `kill9_claim.sh`.

**Non lu / absent** : les 12 dépôts amont clonés (non fournis) ; toutes les lignes `fichier:ligne` du code amont citées par les rapports ; `/tmp/lab/notes/beads.md` ; `pgstart.sh` ; journaux non archivés listés en §7.3.
