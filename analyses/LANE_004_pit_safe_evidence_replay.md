# Analyse approfondie — Lane 004 : Evidence PIT-safe et rejeu (PR #4 mergée)

Auteur de l'analyse : Claude (analyste de recherche), le 2026-09-29.
Lecteur visé : Jean-François, qui ne connaît ni GitHub ni le trading quantitatif. Chaque terme technique est expliqué à sa première occurrence.

Conventions de lecture de ce document :
- « Le rapport affirme » = ce qui est écrit dans les rapports du dépôt.
- « J'ai vérifié » = j'ai relu le chiffre dans un fichier de résultats bruts ou dans le code. Marques : ✔ vérifié, ✘ écart, ? non vérifiable.
- Les labels du dépôt (voir section 1) : PROVEN, OBSERVED, DOCUMENTED_CLAIM, INFERENCE, UNKNOWN. Quand j'ajoute un jugement à moi, je l'écris « (mon analyse) ».
- Tous les chemins sont relatifs à la racine du dépôt, lus sur la branche `origin/main` (sans checkout, avec `git show`).
- Aucun fichier de la lane n'a été modifié. Le seul fichier écrit est celui-ci.

---

## 0. Fiche d'identité

| Élément | Valeur | Source |
|---|---|---|
| Lane | 004 — Evidence PIT-safe et rejeu (« PIT » = Point-In-Time, voir section 1) | `reports/004_pit_safe_evidence_replay/` |
| Branche de travail | `origin/claude/pit-safe-evidence-replay-v1` | `git branch -r` |
| Branche lue pour cette analyse | `origin/main` (contient la lane après fusion) | demandé |
| Pull request (PR) | n° 4, « Merge pull request #4 from redguiff-bot/claude/pit-safe-evidence-replay-v1 », fusionnée par `RedGuiff` le 2026-09-29 à 14:50:08 +0200 (commit `9100649`) | `git log` |
| Commit de contenu | `cfb332e` « research(pit): étude externe PIT-safe evidence & replay V1 — verdict POSTGRES_NATIVE_PIT_PATTERN_SUPPORTED », auteur `redguiff-bot`, 2026-09-29 11:53:14 +0200 | `git log` |
| Commit parent du contenu | `2807f7f` « Add files via upload » (RedGuiff, 2026-09-29 08:35:20 +0200) | `git log` |
| Volume du commit | 42 fichiers, 3 575 lignes ajoutées | `git show --stat cfb332e` |
| Fichiers de la lane sur `main` | 39 (12 rapports + 27 fichiers dans `bench/pit_v1/`) | `git ls-tree` |
| Écart 42 vs 39 | Le commit contenait aussi 3 fichiers `__pycache__/*.cpython-314.pyc` (caches Python compilés) qui ne sont plus dans l'arbre de `main`. Sans conséquence. | `git show --name-only cfb332e` |
| Taille | Rapports : 18 985 octets. `bench/pit_v1/` : 137 481 octets. Total 156 466 octets (~153 Kio). Le plus gros fichier est une copie de code de Feast (`results/feast_src/postgres.py`, 53 061 octets). | `git ls-tree -l` |
| Type de données | 100 % synthétiques (inventées par un générateur), aucune donnée de marché réelle | `00_EXECUTIVE_SUMMARY.md` |
| Verdict final | `FINAL_VERDICT=POSTGRES_NATIVE_PIT_PATTERN_SUPPORTED` | `00_EXECUTIVE_SUMMARY.md` |
| Force du verdict | Forte sur la **logique** (le modèle SQL donne la bonne réponse sur 25 scénarios écrits à la main et sur 60 échantillons à 1,1 million de lignes). Faible à modérée sur tout ce qui est **opérationnel** (durabilité, concurrence, sécurité, données réelles). Voir section 7. (mon analyse) |
| Autres lanes qui touchent PIT | `reports/005_data_feed_resilience/08_PIT_READINESS.md` existe ; **non lu** (hors périmètre demandé). |
| Absence notable | Pas de README, pas de protocole, pas de préenregistrement dans cette lane. Les 12 rapports sont très courts (18 985 octets en tout). Le fichier `SYNTHESE_LANES.md` existe dans le répertoire de travail mais **pas** sur `origin/main` ; non lu. |

Explication des termes de la fiche :
- **Branche** : une « ligne de travail » parallèle dans Git (l'outil de versionnage). La branche `main` est la version officielle ; les autres sont des brouillons.
- **PR (pull request)** : une demande de fusion d'une branche de travail dans `main`. « Mergée » = acceptée et fusionnée.
- **Commit** : un instantané enregistré du dépôt, avec auteur, date et message.

---

## 1. Mission et question posée

### 1.1 La question, en langage simple

Imagine que tu as un robot de trading qui prend une décision à 10 h 05. Pour être honnête scientifiquement, quand tu « rejoues » cette décision plus tard (pour l'auditer ou la tester), le rejeu doit voir **exactement** ce que le robot savait à 10 h 05, ni plus ni moins. Si le rejeu voit, par erreur, une donnée qui n'est arrivée qu'à 20 h, on dit qu'il y a un **lookahead** (« regard vers le futur ») : le test est truqué en faveur du robot sans que personne ne s'en aperçoive.

Cette lane cherche donc :
1. Quel est le **modèle minimal** de stockage qui garantit un rejeu « PIT-safe » ?
2. Comment gérer proprement les **corrections** de données (le fournisseur republie une valeur corrigée) ?
3. Comment retrouver « la dernière version connue à l'instant T » ?
4. Comment traiter les **données rattrapées après coup** (« backfill ») sans polluer le passé ?
5. Que faire quand la **provenance** (d'où et quand une donnée est arrivée) est incomplète ?
6. Existe-t-il un composant **open source** réutilisable, ou faut-il un motif maison sur PostgreSQL ?

(Ce sont les questions Q1 à Q6 du résumé exécutif, `00_EXECUTIVE_SUMMARY.md`.)

### 1.2 Glossaire (première occurrence)

- **PIT / Point-In-Time (« à l'instant donné »)** : ne montrer que ce qui était connu à un instant T.
- **Lookahead** : fuite d'information du futur dans un calcul du passé.
- **Rejeu (replay)** : refaire tourner une décision passée sur les données telles qu'elles étaient.
- **Evidence (« preuve »)** : les observations stockées (barres de prix, etc.) sur lesquelles une décision s'appuie.
- **Observation** : une valeur reçue d'un fournisseur (par exemple la clôture d'une bougie de 5 minutes).
- **Bougie / barre / kline / candle** : résumé du prix sur une période (ouverture, plus haut, plus bas, clôture). `5m` = 5 minutes.
- **`event_time`** (« temps de l'événement », ou *valid time*) : quand le fait s'est produit dans le monde (la bougie de 10:00).
- **`ingested_at`** (« temps d'ingestion », ou *transaction time*) : quand **notre base de données** a enregistré la donnée, mesuré par **l'horloge de la base**. C'est l'axe « STRICT ».
- **`first_observed_at`** : quand le **collecteur** (le programme qui récupère les données) dit avoir vu la donnée la première fois. Peut être faux ou absent.
- **Bitemporel** : un stockage qui garde deux temps à la fois, celui de l'événement et celui de la connaissance.
- **Backfill** : rattrapage de données passées insérées longtemps après coup (par exemple à 20 h pour une bougie de 10 h).
- **Révision** : nouvelle version d'un fait déjà publié (le fournisseur corrige la clôture).
- **Restatement silencieux** : le fournisseur change le contenu **sans** incrémenter le numéro de révision.
- **Finalité** : statut de la donnée (PRELIMINARY = provisoire, FINAL = définitive, CORRECTED = corrigée, UNKNOWN = inconnue).
- **Append-only** : on ne fait qu'ajouter des lignes ; jamais de modification ni de suppression.
- **Fail-closed** : en cas de doute, le système refuse (lève une erreur) plutôt que de deviner.
- **Oracle** : un programme indépendant et simple, écrit à part, qui calcule la « bonne réponse » pour la comparer à celle du système testé.
- **Contrôle négatif / fuyant** : une méthode volontairement fausse dont on vérifie qu'elle est bien détectée comme fausse (ça prouve que la batterie de tests sait détecter des fuites).
- **SCD1 / SCD2** : deux façons classiques de gérer l'historique. SCD1 = écraser la valeur en place (on perd le passé). SCD2 = fermer l'ancienne ligne et en ouvrir une nouvelle (on garde le passé, mais en modifiant des lignes).
- **PostgreSQL (« Postgres »)** : la base de données relationnelle open source visée ; **PG18** = version 18.
- **Trigger** : petit programme que la base déclenche automatiquement à chaque écriture ; ici il refuse toute modification.
- **Verrou advisory (« conseil »)** : un verrou logique que les programmes s'échangent pour se mettre d'accord (ici pour ordonner les écritures).
- **OSS** : logiciel open source.
- **Feature store** : un entrepôt de « variables » (features) pour l'apprentissage automatique (Feast en est un).

### 1.3 Contraintes de la doctrine du dépôt (`claude.md`, lu)

- Le dépôt est un laboratoire de recherche externe ; il ne contient **aucun code AurumShift** et ne doit pas prétendre connaître l'implémentation privée d'AurumShift.
- Priorité : **REUSE → ADAPT → WRAP → COMPOSE → CUSTOM en dernier** : d'abord réutiliser tel quel, sinon adapter, sinon envelopper, sinon composer, et n'écrire du code maison qu'en dernier recours.
- Pour chaque candidat : sources primaires, ne pas croire les README aveuglément, cloner et exécuter quand c'est faisable, inspecter licence, maintenance, dépendances, modèle de persistance, complexité d'exploitation, modes de défaillance, reproductibilité.
- Labels obligatoires : PROVEN (prouvé par test reproductible), OBSERVED (mesuré ou lu dans le code), DOCUMENTED_CLAIM (affirmé par une doc), INFERENCE (déduit), UNKNOWN (inconnu).
- Contraintes AurumShift citées : recherche seule / papier seulement (« paper-only »), pas de capital réel, PostgreSQL d'abord, PIT / provenance / pas de lookahead critiques, événementiel et intrajournalier (pas de haute fréquence), une source faisant autorité par sujet, « l'absence de preuve n'est pas une preuve d'absence », coûts de marché réalistes, faible charge opérateur, reproductibilité, la complexité d'infrastructure doit se justifier.
- Frontière : ne **jamais** affirmer qu'un candidat est compatible avec AurumShift à partir de ce dépôt. Verdicts possibles : ADOPT / ADAPT / PARK / REJECT ; l'adjudication finale se fait plus tard contre le vrai dépôt local.

### 1.4 Contrats testés (`01_REQUIREMENTS_AND_THREAT_MODEL.md`)

1. **As-of** : un fait n'est visible à T que si son axe de connaissance est ≤ T ; une révision arrivée après T ne remplace pas la version antérieure.
2. **Backfill** : `BACKFILL_LOOKAHEAD_PREVENTED=TRUE` requis.
3. **Finalité** : filtrée **après** avoir sélectionné la dernière version.
4. **Déterminisme** : deux exécutions à T identique donnent le même ensemble d'`obs_id`, y compris après arrivées tardives.
5. **Append-only** et **fail-closed** sur provenance incomplète.

Deux axes de connaissance :
- **STRICT** = `ingested_at`, horloge de la base (`strict_clock`), présenté comme inattaquable par l'appelant.
- **COLLECTEUR** = `known_collector_at` : on crédite l'horloge du collecteur (`first_observed_at`) seulement si la provenance est LIVE (flux temps réel), non nulle, ≤ l'ingestion et dans un délai `max_lag` de 60 s ; sinon on retombe sur l'horloge de la base, avec une étiquette `known_basis` (COLLECTOR_CLOCK, DB_CLOCK_BACKFILL, DB_CLOCK_UNVERIFIED_PROVENANCE, DB_CLOCK_NO_FIRST_OBSERVED, DB_CLOCK_SKEW_CAP, DB_CLOCK_LAG_CAP).

Menaces listées : S1 à S12 (scénarios) et contrôles fuyants C1 à C6 (voir 3.2), plus : doublons de réception, révisions désordonnées, restatement silencieux, deux fournisseurs en désaccord, trous (jamais observé / pas encore connu), course de commit, dérive d'horloge du collecteur, propriétaire malveillant (hors périmètre).

---

## 2. Méthode

### 2.1 Nature de l'étude

Étude **exploratoire de faisabilité** sur données synthétiques, exécutée sur une instance PostgreSQL 18.6 jetable. Ce n'est pas une étude statistique : il n'y a pas d'hypothèse à tester avec des seuils de significativité, mais des **tests de correction** (le SQL rend-il l'ensemble attendu ?) et des **mesures de performance** indicatives.

### 2.2 Environnement (`bench/pit_v1/env/environment.txt`, lu)

- Linux 7.2.6 (Fedora 44), x86_64 ; 32 threads, 125 Go de RAM, **machine partagée** à charge non contrôlée.
- PostgreSQL 18.6 (RPM Fedora extrait en espace utilisateur), `btree_gist` 1.8 ; TimescaleDB 2.27.1 (RPM Fedora, licence RPM Apache-2.0).
- Python 3.14.7, DuckDB 1.5.5, Polars 1.43.2, pandas 2.3.3, psycopg 3.3.3.
- Réglages PG : `shared_buffers=2GB`, `fsync=off`, `synchronous_commit=off`, `full_page_writes=off`. Ces trois derniers coupent les garanties de durabilité pour aller vite : les débits mesurés ne sont **pas** représentatifs d'une base réelle (le rapport le dit).

### 2.3 Données et univers

- **Scénarios manuels S1 à S10** (`bench/pit_v1/py/scenarios.py`) : des cas construits à la main avec des heures fixes (base `D0 = 2026-03-02 00:00 UTC`, source fournisseur « A », timeframe `5m`). Attentes écrites à la main **avant** de comparer au SQL et à l'oracle.
- **Données d'échelle** (`bench/pit_v1/py/gen.py`) : générateur déterministe, `seed=42`, 250 instruments (`I0000`…`I0249`) × 4 200 barres de 300 s (`tf_s=300`) = 1 050 000 faits de base. Paramètres par défaut : 2 % de doublons, 3 % de livraisons tardives (LIVE avec 60 à 900 s de retard), 5 % de révisions (revision=1, statut CORRECTED, décalage 600 à 40 000 s), 2 % de backfill (retard 3 600 à 72 000 s ; la moitié des backfills n'ont pas de `first_observed_at`). Le cas normal : retard 0,2 à 5 s, `first_observed_at` = ingestion − U(0 ; 1 s). Prix : clôture ≈ 100 + gaussienne(0 ; 1).
  - Résultat mesuré : 1 123 580 réceptions soumises, 1 102 621 lignes `obs` (donc 20 959 doublons dédoublonnés = 1,996 % de 1 050 000, ✔ cohérent avec 2 %) et 52 621 lignes de plus que la base (5,01 %, ✔ cohérent avec 5 % de révisions).
- **Ordre d'ingestion** : les lignes sont mélangées (`random.Random(1).shuffle`) pour que l'ordre d'arrivée ne soit pas l'ordre des événements. Les batches sont de 5 000 lignes par transaction.
- **Point important** (mon analyse) : dans `scale.py`, `UPDATE pit.config SET strict_clock=false` est exécuté, et les `ingested_at` sont **fournis** par le générateur. Le test à l'échelle ne teste donc pas l'horloge DB réelle ; il teste la logique de requête sur des horodatages synthétiques cohérents. C'est normal pour reproduire un historique, mais cela signifie que la propriété « `ingested_at` = horloge DB non falsifiable » n'est jamais exercée dans les scénarios ni à l'échelle (elle l'est seulement dans `race.py`, avec `strict_clock=true`).

### 2.4 Simulateur / protocole

Il n'y a pas de simulateur de trading. Le protocole se compose de :
1. Un schéma SQL (`sql/001_schema.sql`, `002_functions.sql`, `003_race.sql`).
2. Une batterie de scénarios avec attentes manuelles + oracle Python indépendant (`common.py: oracle_asof`) : Python pur, sans SQL de sélection, qui applique la même règle (dernier `rank = (revision, axe, obs_id)` par fait, avec `revision` NULL classée la plus basse).
3. Des contrôles fuyants C1 à C6 (méthodes naïves) exécutés sur la même batterie.
4. Une expérience de course de commit (`race.py`).
5. Une comparaison de moteurs de jointure (`joins.py`) : réimplémentation de l'algorithme de Feast, DuckDB, Polars, pandas.
6. Un essai du candidat `nearform/temporal_tables` (`cand_temporal_tables.py`), exécuté.
7. Un essai de `WITHOUT OVERLAPS` (`sql/010_without_overlaps.sql`).
8. Une expérience d'échelle à 1,1 M de lignes (`scale.py plain|ts`) et un rejeu hors base (`fleet_offline.py`).

### 2.5 Splits tuning / validation / held-out, préenregistrement, gel des paramètres

- **Splits** : **aucun**. Ce n'est pas une étude d'optimisation de paramètres, il n'y a donc pas de jeu de tuning, de validation ou de held-out. (Le « held-out » = jeu mis de côté et jamais regardé avant le verdict final ; il n'a pas de sens ici.)
- **Préenregistrement** (déclarer critères et paramètres avant de regarder les résultats) : **aucun document**. Les « attentes manuelles » des scénarios sont dans le code (`checks` dans `scenarios.py`), mais rien ne prouve dans le dépôt qu'elles ont été figées avant les résultats. Le dépôt ne contient pas d'historique intermédiaire de cette lane (un seul commit de contenu). (mon analyse)
- **Paramètres figés dans le code** : `max_lag = 60 s` (`pit.config`), `seed=42` (générateur), `Random(1)` (mélange), `Random(7)` (choix des instruments et des T de latence), taille de batch 5 000, chunk Timescale de 14 jours, percentile 60 de `ingested_at` pour le rejeu hors base.
- **Graines** : listées ci-dessus. Les mesures de latence utilisent 60 tirages (flotte : 3).

### 2.6 Critères de décision (seuils exacts)

Il n'y a pas de seuil chiffré de décision du type « accepter si > X ». Les critères sont **mécaniques** :
- Verdict par moteur/contrôle : `LOOKAHEAD_DETECTED` si au moins un résultat utilise une ligne dont `ingested_at > T` ; `WRONG_RESULT_NO_LEAK` si le résultat diffère de la référence sans fuite ; `LOOKAHEAD_PREVENTED` (et « égal à la référence ») sinon. Source : `scenarios.py` (`ctl_sql`) et `joins.py`.
- Batterie de référence : passe si les 25 vérifications sont vraies (SQL = attendu manuel = oracle) et si les comptages, les slots et la garde fail-closed sont conformes.
- Oracle à l'échelle : 0 écart sur 60 échantillons (30 tirages × 2 axes).
- Course : verdict `LOOKAHEAD_PREVENTED` si la décision et le rejeu voient le même ensemble.
- Tolérance de l'axe collecteur : `max_lag = 60 s` ; `first_observed_at` ne doit pas être postérieur à l'ingestion.
- Étiquettes d'adjudication : ADOPT / ADAPT / PARK / REJECT, **sans score global** (`10_ADJUDICATION.md`).

Aucun seuil de performance n'est fixé à l'avance : les mesures sont « indicatives ».

---

## 3. Résultats détaillés

### 3.1 Le modèle de référence PostgreSQL (`03_POSTGRES_REFERENCE_MODEL.md`, `sql/001..003`)

Ce que le rapport affirme et que j'ai confirmé en lisant le SQL (✔ pour la description du code) :

- **`pit.obs`** : table principale, une ligne par **contenu distinct** d'un fait (une version). Colonnes : identité (`source`, `instrument`, `timeframe`, `event_time`), identité du message (`provider_event_id`, `revision` nullable, `content_hash` = md5 de `instrument|timeframe|event_time|finality|payload`), version et provenance (`dataset_version`, `finality_status`, `finality_basis`, `provenance` ∈ LIVE/BACKFILL/UNKNOWN), axes (`first_observed_at`, `ingested_at`, `known_collector_at`, `known_basis`) et `payload jsonb`. Contrainte : `known_collector_at <= ingested_at`.
- **Dédup** par index unique `(source, provider_event_id, revision, content_hash) NULLS NOT DISTINCT` : une même livraison répétée n'ajoute pas de ligne.
- **`pit.obs_receipt`** : journal de **toutes** les réceptions (avec `is_first`), lié à `obs` ; garde la lignée des doublons sans polluer les requêtes PIT.
- **Append-only mécanique** : triggers `BEFORE UPDATE/DELETE/TRUNCATE` qui lèvent `restrict_violation` (message « pit: table obs is append-only »).
- **`pit.ingest`** : estampille `ingested_at` par `clock_timestamp()` si `strict_clock=true`, sinon prend la valeur fournie (mode test). Calcule l'axe collecteur et `known_basis`, insère avec `ON CONFLICT DO NOTHING`, journalise la réception.
- **`pit.asof(T)`** : `DISTINCT ON (source, instrument, timeframe, event_time)` avec `WHERE ingested_at <= T` et `ORDER BY … revision DESC NULLS LAST, ingested_at DESC, obs_id DESC`. C'est « la dernière version connue à T de chaque fait ».
- **`pit.asof_collector(T)`** : même chose sur l'axe collecteur.
- **`pit.asof_final(T)`** : `asof` puis filtre `finality_status IN ('FINAL','CORRECTED')`. La finalité est filtrée **après** la sélection, sinon une ancienne version FINAL réapparaît quand une correction préliminaire l'a remplacée (testé S7b).
- **`pit.latest_known(T, source, instrument, timeframe)`** : le fait le plus récent (par `event_time`) connu à T, version correcte, `LIMIT 1`.
- **`pit.slots(...)`** : diagnostic par créneau ; statuts AVAILABLE, PRELIMINARY_ONLY, NOT_YET_KNOWN_AT_T, NEVER_OBSERVED (le code déclare aussi STALE dans un commentaire mais ne le produit pas). Marqué « AUDIT SEULEMENT : ne jamais exposer à la décision » car il révèle l'existence future.
- **`pit.assert_replayable(...)`** : garde fail-closed qui lève `PIT_PROVENANCE_INCOMPLETE` si des créneaux ne sont pas AVAILABLE, si des lignes de provenance non vérifiée existent dans la fenêtre, ou si la donnée est périmée (`p_max_stale`).
- **Vues** : `pit.silent_restatements` (même message et même révision, contenus différents) et `pit.provider_disagreement` (≥ 2 sources avec des payloads différents).
- **Verrouillage** (`003_race.sql`) : `pit.ingest_locked` prend un verrou advisory **exclusif** de transaction avant d'estampiller ; `pit.decision_cutoff()` prend le **même** verrou en mode **partagé** puis renvoie `clock_timestamp()`.
- **Index PIT** : deux index de 96,9 Mo chacun (un par axe) en plus de la clé primaire (24,8 Mo) et de l'index d'identité (109,5 Mo) (✔ `results/scale_plain.json`).

Résultat de la batterie : **25/25** (✔ voir 3.2). Le rapport écrit « 25/25 attentes manuelles = SQL = oracle Python (PROVEN, synthétique) » : c'est exact au sens du fichier `scenarios.json` (pour chaque check `pass=true` avec `sql == expected == oracle`).

### 3.2 Scénarios et contrôles fuyants (`04_PIT_QUERY_EXPERIMENTS.md`, `results/scenarios.json`)

#### 3.2.1 Les 25 vérifications (toutes `pass=true`, ✔ relues une par une)

| # | Scénario | Ce que ça teste | Attendu = obtenu |
|---|---|---|---|
| 1 | S1 avant réception (T=10:00:01) | rien de visible avant l'arrivée | ensemble vide |
| 2 | S1 après réception (10:00:04) | visible après | {S1.a} |
| 3 | S2 avant arrivée tardive (10:06) | livraison tardive (2 min 30) invisible avant | vide |
| 4 | S2 après (10:08) | visible après | {S2.a} |
| 5 | S3 backfill, décision 10:05 | fait de 10:00 inséré à 20:00, invisible à 10:05 | vide |
| 6 | S3 après backfill (20:00:01) | visible ensuite | {S3.a} |
| 7 | S3b backfill à `first_observed_at` mensonger | l'horloge collecteur prétend 10:00:01 | vide |
| 8 | S3c backfill mal étiqueté LIVE | étiqueté LIVE à tort | vide |
| 9 | S4/S11 décision entre publication et correction (11:10) | on voit la révision 1, pas la 2 | {S4.r1} |
| 10 | S4 après correction (11:30) | on voit la révision 2 | {S4.r2} |
| 11 | S4b rev2 arrivée avant rev1 : rev2 gagne (11:30) | révision désordonnée | {S4b.r2} |
| 12 | S4b avant rev1 retardée (11:22) | idem | {S4b.r2} |
| 13 | S5 doublons : 1 seule version | même message ×3 | {S5.a1} |
| 14 | S5b redélivrance d'un message supersédé ignorée | un ancien message re-livré ne ressuscite pas | {S5b.B} |
| 15 | S6 A seul avant B | deux fournisseurs, B arrive plus tard | {S6.A} |
| 16 | S6 A et B après | les deux visibles | {S6.A, S6.B} |
| 17 | S7 préliminaire visible (ALL) | statut provisoire visible en mode tout | {S7.p} |
| 18 | S7 FINAL_ONLY avant final | rien de définitif | vide |
| 19 | S7 FINAL_ONLY après final | le final | {S7.f} |
| 20 | S7b restatement préliminaire : dernier gagne (ALL) | un FINAL puis un PRELIMINARY | {S7b.p} |
| 21 | S7b FINAL_ONLY, sélection puis filtre : rien | le point clef de l'ordre sélection/filtre | vide |
| 22 | S9 dernier connu | donnée périmée mais présente | {S9.a} |
| 23 | S10 avant ré-import | version 1 | {S10.v1} |
| 24 | S10 après ré-import identique | pas de changement | {S10.v1} |
| 25 | S10 après restatement | contenu changé sans nouvelle révision | {S10.v3} |

Comptages complémentaires (`counts`, tous vrais ✔) : S5 = 1 ligne `obs` pour 3 réceptions ; S5b = 2 lignes ; S10 = 2 lignes `obs` pour 3 réceptions ; `S10_silent_restatements`=1 ; `S6_disagreement_view`=1 ; `S5_first_known_unchanged`=true (la première connaissance n'est pas repoussée par un doublon).

Slots ✔ : S8 = [AVAILABLE, NEVER_OBSERVED, AVAILABLE] ; S8b = [AVAILABLE, NOT_YET_KNOWN_AT_T, AVAILABLE].

Garde fail-closed ✔ : S8 manquant → `FAIL_CLOSED` (1 créneau non disponible) ; S8b avant l'arrivée du backfill → `FAIL_CLOSED` ; S8b après le backfill → `PASS` ; S9 périmée à 30 min avec seuil 10 min → `FAIL_CLOSED` (`stale=t`) ; S9 fraîche à 5 min → `PASS`.

Alias de dédup (`dedup_aliases`) : `S5.a2`, `S5.a3` → `S5.a1` ; `S5b.A2` → `S5b.A` ; `S10.v2` → `S10.v1` (les doublons reçoivent le même `obs_id`).

Réserve importante (mon analyse) : les libellés « S11 » et « S12 » cités dans le rapport n'existent pas comme scénarios séparés. « S11 » est fondu dans le check 9 (« S4/S11 ») ; la course de commit (probablement S12) est traitée séparément dans `race.py`. Le rapport parle de « S1–S12 » alors que la batterie contient les scénarios S1, S2, S3, S3b, S3c, S4, S4b, S5, S5b, S6, S7, S7b, S8, S8b, S9, S10. Écart de présentation mineur, pas d'écart de fond. (✘ mineur, voir 7.6)

#### 3.2.2 Contrôles fuyants C1 à C6 (✔ `scenarios.json` → `controls`)

Ce sont des « mauvaises méthodes » exécutées sur la même batterie. Une bonne batterie doit les prendre en défaut.

| Contrôle | Méthode naïve | Verdict obtenu (fichier brut) | Fuites | Faux sans fuite | Verdict du rapport |
|---|---|---|---|---|---|
| C1 | filtrer sur `event_time` seul | LOOKAHEAD_DETECTED | 10 | 0 | idem ✔ |
| C2 | `first_observed_at` brut | LOOKAHEAD_DETECTED | 2 | 0 | idem ✔ |
| C3 | axe collecteur validé | LOOKAHEAD_PREVENTED | 0 | 0 | « PREVENTED sur la batterie » ✔ |
| C4 | ordre d'arrivée pur, sans tri par révision | WRONG_RESULT_NO_LEAK | 0 | 1 | idem ✔ |
| C5 | SCD1 (écrasement, état courant) | LOOKAHEAD_DETECTED | 10 | 0 | idem ✔ |
| C6 | `coalesce(first_observed_at, event_time)` | LOOKAHEAD_DETECTED | 2 | 0 | idem ✔ |

Lecture simple :
- C1, C5 fuient beaucoup (10 cas sur les 23 checks « asof » de la batterie (25 moins les 2 checks `asof_final`)).
- C2 et C6 fuient sur les cas de backfill où l'horloge du collecteur est fausse ou absente.
- C4 ne fuit pas mais donne un résultat faux quand une révision ancienne arrive après une plus récente (elle deviendrait la « dernière connue »).
- **C3** (l'axe collecteur validé) passe : la batterie ne montre aucun problème. Le rapport précise que c'est « non prouvé au-delà de la batterie ».
- La référence STRICT (`pit.asof`) : `reference_leaks=[]`, `reference_verdict=LOOKAHEAD_PREVENTED`, `all_reference_checks_pass=true` ✔.

Erreur de détail dans le rapport (✘ mineur) : `04_PIT_QUERY_EXPERIMENTS.md` écrit « S3b/S3c plafonnés LAG_CAP ». Dans le code : S3b est un backfill (`provenance=BACKFILL`), donc `known_basis = DB_CLOCK_BACKFILL`, pas LAG_CAP ; seul S3c (étiqueté LIVE à tort, 20:00 − 10:00:01 ≫ 60 s) est plafonné par LAG_CAP. Le comportement est correct, la description est imprécise.

Lacune de couverture (mon analyse) : aucun scénario ne place `first_observed_at` **dans le futur** de l'ingestion. La branche `DB_CLOCK_SKEW_CAP` du code n'est donc jamais exercée par la batterie ni par le générateur d'échelle (le générateur produit `first_observed_at` ≤ ingestion). Le rapport `05` cite pourtant SKEW_CAP comme « validé sur la batterie » (« un LIVE mensonger est plafonné (SKEW_CAP, LAG_CAP) — validé sur la batterie seulement »). Pour SKEW_CAP, c'est **non vérifié** dans les fichiers lus (?). Pour LAG_CAP, ✔ via S3c.

### 3.3 Course de commit (`results/race.json`, `sql/003_race.sql`, `py/race.py`)

Le problème, expliqué simplement : le système estampille une ligne avec l'heure `t1` **avant** que la transaction soit validée (« commit »). Une autre écriture plus tardive `t2 > t1` peut être validée **avant**. Si une décision est prise entre les deux, elle voit `b` (t2) mais pas `a` (t1, pas encore validée) ; un rejeu ultérieur à la même heure T verra `a` **et** `b`, parce que `a` porte une estampille antérieure à T. La décision et son rejeu divergent : c'est un lookahead de fait (le rejeu « sait » plus que la décision).

Trois régimes testés (✔ valeurs relues) :

| Régime | Ce que la décision a vu | Ce que le rejeu voit | Stable ? | Verdict |
|---|---|---|---|---|
| NONE (sans verrou) | [b] | [a, b] | non | LOOKAHEAD_DETECTED |
| LOCK_W (verrou exclusif côté écrivains seulement) | [] | [a] | non | LOOKAHEAD_DETECTED |
| LOCK_RW (exclusif écrivains **+** partagé lecteur `decision_cutoff`) | [a] | [a] | oui | LOOKAHEAD_PREVENTED |

Lecture : verrouiller seulement les écrivains ne suffit pas, parce que le lecteur peut choisir son T pendant que A est en vol. Il faut que le lecteur attende la fin des écritures en cours (verrou partagé) avant de figer T. Le rapport qualifie cette « trouvaille majeure » de PROVEN.

Réserves (mon analyse, voir aussi 7) :
- **Un seul run par régime** ; le déroulement dépend de `time.sleep(0.3)`, `sleep(0.5)` et de délais d'attente (`join(timeout=…)`). Ce n'est pas un test de concurrence répété (pas de N runs, pas d'écarts).
- Les 3 valeurs `T` sont des horloges réelles du 2026-09-29 (jour d'exécution).
- C'est un test à **2 écrivains et 1 lecteur** avec une seule paire d'instruments. Ça démontre l'existence du problème et l'efficacité du remède **dans ce scénario**, pas une garantie générale.
- Le coût du remède n'est pas mesuré : un verrou global sérialise tous les écrivains et un décideur bloque l'ingestion pendant sa transaction.

### 3.4 Jointures alternatives et moteurs (`results/joins.json`, `py/joins.py`)

Test sur **23 paires (instrument, T)** dérivées de la batterie (25 checks, dont deux paires répétées avec `asof_final`). Référence : `pit.latest_known`. Verdicts (✔ relus) :

| Moteur / méthode | Fuites | Faux sans fuite | Verdict |
|---|---|---|---|
| Feast, défaut (`event_timestamp <= entity_timestamp`) | 10 | 1 | LOOKAHEAD_DETECTED |
| Feast, `filter_by_created_timestamp=True` | 0 | 1 | WRONG_RESULT_NO_LEAK |
| DuckDB `ASOF JOIN` sur `event_time` | 5 | 5 | LOOKAHEAD_DETECTED |
| DuckDB `ASOF JOIN` sur `ingested_at` | 0 | 1 | WRONG_RESULT_NO_LEAK |
| DuckDB jointure par plage + `QUALIFY row_number` | 0 | 0 | égal à la référence |
| Polars `join_asof` sur `event_time` | 10 | 1 | LOOKAHEAD_DETECTED |
| Polars filtre + `group_by().first()` | 0 | 0 | égal à la référence |
| pandas `merge_asof` sur `event_time` | 10 | 1 | LOOKAHEAD_DETECTED |

Le rapport dit « 10 fuites » pour Feast défaut ✔, « DETECTED » pour DuckDB ASOF/Polars/pandas ✔, « WRONG (S4b) » pour `filter_by_created_timestamp` et pour DuckDB ASOF sur `ingested_at` : ✔ pour le nombre (1 faux sans fuite) ; le nom du scénario S4b n'apparaît pas dans mon extrait agrégé (?).

Deux points de méthode (mon analyse) :
1. Le « Feast » testé n'est **pas** Feast exécuté : c'est une **réimplémentation** en Python (`joins.py`, fonction `feast()`) de la logique lue dans le SQL de Feast. Le code de Feast (commit `f0bc0700be7029166e6605e407de6d229cd1e93e`, `results/feast_src/postgres.py`, 1 392 lignes) confirme : le gabarit de requête contient `subquery.event_timestamp <= entity_dataframe.entity_timestamp` (ligne ~1006) ; le filtre sur `created_timestamp <= entity_timestamp` n'est actif que si `filter_by_created_timestamp` est vrai **et** qu'une colonne `created_timestamp` existe (lignes ~1012-1013) ; le tri est `ORDER BY event_timestamp DESC[, created_timestamp DESC]` (ligne ~1052). La description du rapport est donc fidèle au code (✔ pour la lecture du code). Mais le chiffre « 10 fuites » vient de la réimplémentation, pas d'une exécution de Feast. Le rapport `04` le range sous « OBSERVED dans le code », et `11` dit « comportement réimplémenté, non exécuté » : cohérent, à condition de ne pas lire « 10 fuites » comme un résultat d'exécution de Feast.
2. Le mot « fuite » est défini par la **colonne `ingested_at` du laboratoire**. Feast est un entrepôt de variables pour le machine learning qui ne prétend pas gérer les révisions ni l'horloge d'ingestion. Le verdict « Feast fuit » signifie donc « Feast, utilisé avec ce jeu de colonnes et sans notre colonne de connaissance, ne protège pas » et non « Feast est défectueux » (mon analyse).

### 3.5 Rejeu hors base à l'échelle (`results/fleet_offline.json`, `py/fleet_offline.py`)

- 1 102 621 lignes chargées dans une DataFrame Polars ; `T` = percentile 60 de `ingested_at` (`2026-03-10 19:30:02.809993+01:00`) ; 630 740 faits distincts renvoyés (✔ `ref_size`).
- Durées : `pit.asof` dans PostgreSQL 0,62 s ; Polars 0,18 s ; DuckDB 0,56 s. `polars_equal=true`, `duckdb_equal=true` (✔).
- Rapport `04` : mêmes chiffres ✔. Il précise « Le temps exclut le chargement ».

Lecture : les deux moteurs hors base retrouvent **exactement** le même ensemble d'`obs_id` que la fonction SQL, à condition d'utiliser la forme « filtre `ingested_at <= T`, tri, première ligne par groupe ».

Réserve de comparabilité (mon analyse) : les 0,62 s de PostgreSQL incluent la transmission de 630 740 identifiants au client Python (`fetchall`), alors que 0,18 s (Polars) et 0,56 s (DuckDB) sont des calculs en mémoire sur des données déjà chargées. Le rapport signale seulement que « le chargement est exclu ». La comparaison de vitesse 3,4× (0,62/0,18) n'est donc pas à égalité de périmètre ; l'égalité **des résultats** est, elle, solide.

### 3.6 Échelle : plain contre Timescale (`07_SCALE_EXPERIMENT.md`, `results/scale_plain.json`, `results/scale_ts.json`)

Tableau du rapport (tous les chiffres vérifiés dans les JSON bruts, ✔) :

| Mesure | plain (PostgreSQL) | Timescale | Vérification |
|---|---|---|---|
| Réceptions soumises | 1 123 580 | 1 123 580 | ✔ |
| Lignes `obs` | 1 102 621 | 1 102 621 | ✔ |
| Durée d'insertion | 171,2 s | 239,1 s | ✔ |
| Insertion (lignes/s, chemin fonction) | 6 561 | 4 700 | ✔ (1 123 580/171,2 = 6 563 ; le JSON dit 6 561, différence d'arrondi sur la durée) |
| Heap `obs` | 225 910 784 o (≈226 Mo décimaux) | 8 192 o (artefact, parent seul) | ✔ |
| Index `obs` | 328 155 136 o (≈328 Mo) | 40 960 o (artefact) | ✔ |
| Octets par `obs` (heap + index) | 502 | 0 (artefact) | ✔ (554 065 920/1 102 621 = 502,5) |
| Journal `obs_receipt` (total) | 144 998 400 o (≈145 Mo) | idem | ✔ |
| PIT 1 instrument p50 / p95 / max | 1,70 / 2,45 / 2,64 ms | 6,50 / 10,88 / 11,24 ms | ✔ |
| `latest_known` p50 / p95 / max | 0,14 / 0,34 / 0,63 ms | 0,23 / 0,66 / 0,98 ms | ✔ |
| `asof_collector` 1 instrument p50 | 1,65 ms | 6,29 ms | ✔ (non cité dans le rapport 07) |
| Flotte 250 instruments p50 (n=3) | 491,83 ms (p95 508,64) | 781,31 ms (p95 818,37) | ✔ |
| Écarts d'oracle | 0 / 60 | 0 / 60 | ✔ |
| UPDATE | bloqué (« pit: table obs is append-only (UPDATE refused) ») | bloqué (sur le chunk `_hyper_1_1_chunk`) | ✔ |
| Chunks Timescale | — | 2 | ✔ |
| Compression Timescale | — | erreur « functionality not supported under the current "apache" license » | ✔ |

Détail des index plain (✔) : clé primaire 24 788 992 o ; `obs_identity` 109 527 040 o ; `obs_pit_ing` 96 919 552 o ; `obs_pit_col` 96 919 552 o. Somme = 328 155 136 o. Les deux index PIT pèsent 193 839 104 o, soit 59 % de la taille des index et 35 % de heap + index (mon calcul).

Ratios calculés (mon analyse) : latence PIT Timescale/plain = 6,5/1,7 = 3,82 (le rapport dit 3,8× ✔) ; débit d'insertion plain/Timescale = 1,40 ; flotte Timescale/plain = 1,59.

Ce que ça signifie en langage simple :
- Sur ce matériel et sans contrainte de durabilité, retrouver « l'état connu à T » d'un instrument sur ~4 400 lignes prend ≈ 2 ms, et pour les 250 instruments ≈ 0,5 s.
- Stocker ~1,1 M observations coûte ≈ 0,55 Go (heap + index) plus 0,145 Go de journal, soit environ 0,7 Go pour 1,1 M lignes ; les index PIT en sont une bonne part.
- Timescale (extension de PostgreSQL pour séries temporelles) ne donne aucun gain ici et est ~3,8× plus lent pour la requête PIT ; sa compression, l'intérêt principal, n'a pas pu être testée avec le build Apache.

Défaut de mesure signalé par le rapport lui-même : pour Timescale, `pg_table_size('pit.obs')` ne mesure que la table parente (8 Kio) et non les chunks : c'est pourquoi `bytes_per_obs_total` vaut 0. Le rapport le dit (« artefact ») ✔.

Limites (déjà listées dans `07` et `11`) : un seul run par mesure, flotte n=3, pas de concurrence, pas de charge de lecture pendant l'écriture, oracle échantillonné (60), pas de VACUUM ni de durabilité.

Point d'attention que le rapport ne souligne pas (mon analyse) : dans ce jeu généré, les livraisons LIVE ont `first_observed_at` = ingestion − U(0 ; 1 s), donc toujours dans les 60 s de `max_lag`, y compris les livraisons tardives. L'axe collecteur et l'axe STRICT sont donc quasiment confondus pour les lignes LIVE (écart < 1 s), et les cas SKEW_CAP / LAG_CAP n'apparaissent pas à l'échelle. Le « 0 écart d'oracle sur l'axe collecteur » à 1,1 M est donc peu exigeant.

### 3.7 Candidats OSS exécutés ou lus (`06_OSS_COMPONENT_EVALUATION.md`)

#### 3.7.1 PG18 `WITHOUT OVERLAPS` (`results/without_overlaps.txt`, `sql/010_without_overlaps.sql`) — exécuté

`WITHOUT OVERLAPS` est une contrainte de PostgreSQL 18 qui interdit que deux intervalles de temps se chevauchent pour la même clé. Sorties brutes lues (✔) :
- (A) Table SCD2 **mutable** : la correction impose un `UPDATE` de la ligne ouverte (réécriture de l'historique). Un backfill qui chevauche est bien refusé (`OVERLAP_REJECTED (23P01)`). Mais un backfill sur un instrument **neuf** avec un `known` rétroactif est **accepté** et la requête de contrôle à T=10:05 le voit : `LEAK_QUERY_T=10:05 sees Y | rows 1` → fuite.
- (B) Table **dérivée** de l'axe append-only (intervalles calculés par `LEAD`) : clé primaire OK (`DERIVED_PK_OK | 3`), et la requête de contrôle ne voit pas Y (`DERIVED_LEAK_QUERY_T=10:05 sees Y | 0`).
- Cas d'égalité : deux versions avec le même `ingested_at` produisent **un intervalle vide** non signalé (`TIE_EMPTY_RANGES | 1`). L'invariant ne détecte donc pas l'ambiguïté d'ordre.

Verdict du rapport : ADAPT, comme invariant sur une table dérivée seulement. ✔ cohérent avec les sorties.

#### 3.7.2 `nearform/temporal_tables` (`results/cand_temporal_tables.json`, `py/cand_temporal_tables.py`) — exécuté

Extension écrite en plpgsql qui versionne automatiquement les lignes modifiées dans une table d'historique. Résultats bruts (✔) :
- T1 backfill invisible à 10:05 (horloge DB) : `true`.
- T2 `sys_period` forgé par l'appelant : accepté mais écrasé par le trigger (`ACCEPTED_BUT_TRIGGER_OVERWRITES=False`, c'est-à-dire que la requête à 10:05 ne voit pas la ligne forgée).
- T3 correction : avant = 100, après = 101 (correct).
- T4 révision désordonnée : la valeur courante est **100** (la révision périmée gagne, car le modèle n'a pas de numéro de révision).
- T5 deux fournisseurs pour la même clé : `REJECTED_UNIQUE` (un seul fournisseur par fait sans modifier le schéma).
- T6 : la table courante est modifiable et supprimable par conception (`T6_delete_moves_to_history=2`).
- T7 course : la décision voit [R2], le rejeu voit [R1, R2] → `LOOKAHEAD_DETECTED`. Cause : `now()`/début de transaction sert d'estampille alors que la visibilité ne vient qu'au commit.
- Note du rapport : l'as-of exige une `UNION` entre table courante et historique.

Le rapport parle d'un commit `1824073a` dans le script (`cand_temporal_tables.py`, docstring) ; le hash complet n'est pas donné et je n'ai pas pu le vérifier (?).

#### 3.7.3 `pg_bitemporal` — code lu, non exécuté

Le fichier `results/pg_bitemporal_correction_excerpt.sql` (lu) montre que `ll_bitemporal_correction` exécute un `UPDATE … SET asserted = timeperiod_range(lower(asserted), %L, '[)')` sur l'ancienne ligne, avec `p_now` fourni par l'appelant. Deux propriétés visibles dans l'extrait : (1) l'horloge d'assertion est un paramètre de l'appelant ; (2) l'historique est **réécrit** par UPDATE. Le rapport en déduit « fuite possible par construction ; non append-only ». Je confirme la lecture de l'extrait (✔), mais c'est une inférence non testée (le rapport le classe OBSERVED « code lu, non exécuté »). L'extrait ne couvre que la fonction de correction, pas la fonction d'insertion `ll_bitemporal_insert` que le rapport cite aussi (?).

#### 3.7.4 Feast — code lu, algorithme réimplémenté
Voir 3.4.

#### 3.7.5 DuckDB, Polars, pandas — exécutés
Voir 3.4 et 3.5. Les moteurs sont corrects si la forme « range + first » est utilisée ; `ASOF JOIN` / `join_asof` / `merge_asof` sur `event_time` fuient.

#### 3.7.6 TimescaleDB — exécuté partiellement
Voir 3.6. Contraintes trouvées dans `scale.py` : la clé unique doit inclure la colonne de partitionnement `event_time` ; la clé étrangère de `obs_receipt` vers `obs` est supprimée (impossible vers une hypertable sans `event_time`). Ce sont des modifications du schéma de référence (le SQL Timescale est produit par remplacements de chaînes dans `ts_sql()`).

#### 3.7.7 Non exécutés (documentation seule)
pgMemento, periods, arkhipov/temporal_tables, Hopsworks (dépôt 404), Tecton (non listé dans les métadonnées), eventsourcing, XTDB, Dolt, TerminusDB, lakeFS, Iceberg, Delta : classés UNKNOWN pour le comportement PIT.

Métadonnées de dépôts (`results/candidates_meta.tsv`, ✔) : `scalegenius/pg_bitemporal` BSD-3, dernier push 2022-04-20 ; `arkhipov/temporal_tables` BSD-2, 2026-01-12 ; `nearform/temporal_tables` NOASSERTION (pas de licence détectée par GitHub), 2025-11-24 ; `pgMemento` LGPL-3.0, 2026-04-27 ; `xocolatl/periods` PostgreSQL, 2025-10-08 ; `timescale/timescaledb` NOASSERTION ; `feast-dev/feast` Apache-2.0 ; `duckdb` MIT ; `polars` MIT ; `pandas` BSD-3 ; `pyeventsourcing/eventsourcing` BSD-3 ; `xtdb` MPL-2.0 ; `dolt` Apache-2.0 ; `terminusdb` Apache-2.0 ; `lakeFS` NOASSERTION ; `iceberg` et `delta` Apache-2.0. Plusieurs autres noms essayés sont en 404 : `hopsworks/hopsworks`, `pythoneer/eventsourcing`, `tembo-io/pg_bitemporal`, `hettie-d/pg_bitemporal_temporal_tables`, `cybertec-postgresql/pg_timetravel`, `fenrirunbound/pgtemporal`. Le fichier contient aussi `darold/pgtt` et `mlflow/mlflow`, non discutés dans les rapports.

Remarque (mon analyse) : le rapport `02` classe `pgMemento` et `periods` comme « D » (documentation seule) ; ce sont des extensions de plpgsql qui auraient pu être exécutées sur le même PostgreSQL. Le rapport ne dit pas pourquoi elles ne l'ont pas été.

### 3.8 Finalité fournisseur (`08_PROVIDER_FINALITY.md`)

| Fournisseur | Constat du rapport | Label |
|---|---|---|
| Binance (flux kline) | champ `x` = « Is this kline closed? » ; poussé toutes les 1 000 ms (1 s) / 2 000 ms (autres) | DOCUMENTED_CLAIM (page web-socket-streams récupérée le 2026-09-29) |
| OKX (chandeliers) | champ `confirm` : texte de la doc non obtenu (page tronquée) | UNKNOWN |
| Coinbase Exchange (chandeliers) | granularités {60, 300, 900, 3600, 21600, 86400} ; aucune déclaration de finalité/révision trouvée | DOCUMENTED_CLAIM (absence) → UNKNOWN pour la finalité |

Ces constats viennent de pages web récupérées à la volée ; **aucune capture de page n'est enregistrée dans le dépôt** : je ne peux donc pas les vérifier (?). Règle du rapport : toute finalité non prouvée est stockée UNKNOWN et exclue de `asof_final` (fail-closed). Une clôture `x=true` n'exclut pas une correction ultérieure du fournisseur (INFERENCE), détectable seulement par `silent_restatements` ou `provider_disagreement`.

### 3.9 Matrice des échecs (`09_FAILURE_AND_LOOKAHEAD_MATRIX.md`)

Le rapport résume par approche : Backfill / Révision tardive / Course de commit / Verdict. Points de recoupement avec les résultats bruts :
- Référence PG STRICT sans verrou : DETECTED (course) ✔ `race.json` NONE.
- Référence + verrou écrivains seuls : DETECTED ✔ `race.json` LOCK_W.
- Référence + verrou écrivains/lecteur : PREVENTED ✔ `race.json` LOCK_RW.
- C1, C2, C5, C6 : DETECTED ✔ ; C4 : WRONG ✔ ; C3 : « PREVENTED sur batterie seulement » ✔.
- Feast défaut : DETECTED ✔ ; `filter_by_created_timestamp` : WRONG ✔.
- DuckDB/Polars/pandas as-of sur event_time : DETECTED ✔ ; range+QUALIFY / Polars first : = référence ✔ (« dépend de la source » pour la course : non testé, c'est une inférence).
- nearform : DETECTED (course) ✔ ; pg_bitemporal : « non exécuté » ✔.
- `WITHOUT OVERLAPS` sur SCD2 mutable : DETECTED ✔ (un cas de fuite, sur instrument neuf).

Écart de forme (mon analyse) : la matrice mélange des verdicts **mesurés** (exécutés) et des verdicts **inférés** à partir de la lecture de code (pg_bitemporal, Feast). La colonne « Course de commit » est « — » pour beaucoup de lignes parce que la course n'a été exécutée que sur trois régimes de la référence et sur nearform.

---

## 4. Candidats et méthodes évalués un par un

Le rapport `10` sépare cinq rôles (STORAGE AUTHORITY, OBSERVATION PROVENANCE, PIT QUERY, OFFLINE REPLAY ENGINE, PROVIDER FINALITY ADAPTER) et renonce à un score global (cohérent avec la doctrine). Choix par rôle :

| Rôle | Choix |
|---|---|
| STORAGE AUTHORITY | PostgreSQL natif (schéma de référence) |
| OBSERVATION PROVENANCE | `obs_receipt` + `known_basis` (maison, ~2 tables) |
| PIT QUERY | fonction SQL de référence |
| OFFLINE REPLAY ENGINE | DuckDB ou Polars (forme range + first) |
| PROVIDER FINALITY ADAPTER | à écrire par fournisseur ; UNKNOWN par défaut |

Décisions par candidat, avec ma justification chiffrée et les conditions qui pourraient changer le verdict (les conditions sont de moi, marquées « mon analyse »; le rapport ne les donne pas) :

| Candidat | Décision (rapport) | Justification chiffrée (source) | Condition de changement (mon analyse) |
|---|---|---|---|
| PostgreSQL 18 natif | ADOPT | 25/25 ; 0/60 d'oracle à 1,1 M ; 1,7 ms p50 ; 0,49 s flotte | Devient REJECT si des tests sur données réelles ou sous durabilité complète révèlent un écart ; à revalider avec `fsync=on`, rôles et REVOKE |
| PG18 `WITHOUT OVERLAPS` | ADAPT | invariant OK sur table dérivée (`DERIVED_PK_OK`, 0 fuite) ; sur SCD2 mutable, 1 fuite ; cas d'égalité non signalé | Utile seulement si on veut un garde-fou de cohérence des intervalles ; ne remplace pas la sélection PIT |
| Polars | ADOPT (hors base) | identique à la référence (`polars_equal=true`) ; 0,18 s | Perd son statut si la forme « filtre + `first` » n'est pas imposée par revue de code ; test sur autres versions de Polars |
| DuckDB | ADAPT | identique en range+QUALIFY (`duckdb_equal=true`, 0,56 s) ; `ASOF JOIN` : 5 fuites et 5 faux (23 paires) | Idem : interdiction d'`ASOF JOIN` à codifier |
| pandas | REJECT | `merge_asof` : 10 fuites, 1 faux ; « aucun avantage » | Non pertinent sauf besoin d'écosystème ; le rapport ne teste pas pandas avec la forme sûre (filtre + tri + `groupby().first()`) — mon analyse |
| TimescaleDB | PARK | mêmes résultats d'oracle (0/60) mais latence PIT ×3,8 (6,5 vs 1,7 ms) et insertion 4 700 vs 6 561 lignes/s ; compression non testée | Reconsidérer si la volumétrie dépasse largement 1,1 M, avec un build sous licence permettant la compression, et si on mesure la taille des chunks |
| nearform/temporal_tables | REJECT | course DETECTED (T7), pas de révision (T4 : 100 périmé gagne), table mutable (T6), un fournisseur par clé (T5) | Peu probable de changer (défauts structurels) |
| arkhipov/temporal_tables, periods | PARK | non exécutés ; même modèle d'horloge de transaction attendu — INFERENCE | Exécuter les mêmes tests T1–T7 |
| pg_bitemporal | REJECT | `asserted` fourni par l'appelant ; UPDATE de l'ancienne ligne (extrait lu) | Exécuter pour confirmer (le rapport n'a pas exécuté) |
| pgMemento | PARK | audit de mutations, non évalué | Exécuter ; pertinent seulement si on veut journaliser des UPDATE, pas comme moteur PIT |
| Feast | PARK | algorithme de référence lu (commit `f0bc0700…`) ; pas de révision ; second service | Si un besoin de feature store apparaît, à évaluer avec les colonnes `created_timestamp` |
| Hopsworks, Tecton | PARK | second service ; Hopsworks dépôt 404 ; non évalués | — |
| eventsourcing, XTDB, Dolt, TerminusDB, lakeFS, Iceberg, Delta | PARK | second datastore ou service sans preuve de nécessité | Changerait si le volume ou la gouvernance exigeait un magasin dédié |

Observation (mon analyse) : la doctrine dit « REUSE → ADAPT → WRAP → COMPOSE → CUSTOM last ». Le rapport conclut à un motif **CUSTOM** en SQL (« ANY_CANDIDATE_DROP_IN=FALSE »). C'est cohérent avec le chemin autorisé (CUSTOM en dernier), avec la justification que les candidats exécutés échouent sur des points précis (course, révision, mutabilité). En revanche, pour `pgMemento`, `periods`, `arkhipov`, `pg_bitemporal`, l'étape « REUSE/ADAPT » n'est pas menée jusqu'à l'exécution, ce qui laisse la justification du CUSTOM appuyée sur deux candidats exécutés (nearform, Timescale) et deux lus (pg_bitemporal, Feast).

---

## 5. Bloc final

### 5.1 Bloc final (reproduit tel quel depuis `00_EXECUTIVE_SUMMARY.md`)

```
POSTGRES_REFERENCE_PIT_CORRECT=TRUE
BACKFILL_LOOKAHEAD_PREVENTED=TRUE
REVISION_LOOKAHEAD_PREVENTED=TRUE
DUPLICATE_HANDLING_PROVEN=TRUE
FINALITY_MODEL_PROVEN=TRUE
BEST_POSTGRES_PATTERN=append-only observations + receipts journal, axe ingested_at (horloge DB), verrou advisory exclusif écrivains + partagé lecteur, dernière version par (revision, axe, obs_id), finalité filtrée après sélection
BEST_REUSABLE_OSS_COMPONENTS=PostgreSQL 18 (btree_gist WITHOUT OVERLAPS sur table dérivée) ; DuckDB et Polars (rejeu offline, forme range+QUALIFY/first)
SECOND_DATASTORE_REQUIRED=FALSE
SECOND_SERVICE_REQUIRED=FALSE
PIT_QUERY_COMPLEXITY=LOW (une fonction SQL d'une table, ~1 fenêtre ; 1,7 ms p50 par instrument, 0,49 s flotte de 250 instruments sur 1,1M lignes)
SCALE_EXPERIMENT_ROWS=1123580
ANY_CANDIDATE_DROP_IN=FALSE
ANY_SCIENTIFIC_INVALIDATION=FALSE
FINAL_VERDICT=POSTGRES_NATIVE_PIT_PATTERN_SUPPORTED
```

Réserves que le rapport ajoute juste après le bloc : « synthétique ; finalité fournisseur non vérifiée pour OKX/Coinbase ; compression Timescale non testée (build Apache) ; propriétaire/superuser contourne l'append-only. Voir 11. »

### 5.2 Explication ligne par ligne

| Clé | Signification en langage simple | Ce que j'ai vérifié |
|---|---|---|
| `POSTGRES_REFERENCE_PIT_CORRECT=TRUE` | Le modèle SQL de référence renvoie toujours l'ensemble attendu à T (sur la batterie et sur les échantillons) | ✔ 25/25 et 0/60 ; mais valide seulement contre l'oracle écrit par le même auteur (voir 7) |
| `BACKFILL_LOOKAHEAD_PREVENTED=TRUE` | Une donnée rattrapée après coup est invisible aux dates de décision antérieures | ✔ S3, S3b, S3c, S8b ; **sur l'axe STRICT**. Sur l'axe collecteur, seulement sur la batterie |
| `REVISION_LOOKAHEAD_PREVENTED=TRUE` | Une correction arrivée après T ne remplace pas la version connue à T | ✔ S4, S4b, S10 |
| `DUPLICATE_HANDLING_PROVEN=TRUE` | Les doublons ne créent pas de nouvelle version et sont tracés | ✔ S5 (1 ligne, 3 réceptions), S10 (2 lignes, 3 réceptions) ; réserve sur le retour à un contenu ancien (7.4) |
| `FINALITY_MODEL_PROVEN=TRUE` | Le modèle interne PRELIMINARY/FINAL/CORRECTED/UNKNOWN est correct | ✔ S7, S7b **côté modèle**. Le mapping vers les vrais fournisseurs n'est PAS prouvé (OKX UNKNOWN, Coinbase UNKNOWN) |
| `BEST_POSTGRES_PATTERN=…` | Le motif recommandé : table d'observations en ajout seul + journal des réceptions, axe = horloge de la base, verrous écrivains/lecteur pour la course, version choisie par (révision, axe, `obs_id`), finalité filtrée après sélection | Composants tous présents dans le SQL lu |
| `BEST_REUSABLE_OSS_COMPONENTS=…` | Ce qui est réutilisable : PostgreSQL 18 (avec `WITHOUT OVERLAPS` sur une table dérivée), DuckDB et Polars pour le rejeu hors base | ✔ pour DuckDB/Polars (égalité) ; `WITHOUT OVERLAPS` ✔ exécuté |
| `SECOND_DATASTORE_REQUIRED=FALSE` | Pas besoin d'une deuxième base de données | Conclusion tirée de l'absence de besoin constaté à 1,1 M de lignes ; c'est une absence de preuve de nécessité, pas une preuve d'inutilité pour des volumes plus élevés (INFERENCE) |
| `SECOND_SERVICE_REQUIRED=FALSE` | Pas besoin d'un deuxième service (type Feast) | idem |
| `PIT_QUERY_COMPLEXITY=LOW (…)` | La requête PIT est simple (une fonction SQL sur une table) ; performances 1,7 ms p50 et 0,49 s | ✔ chiffres ; la fonction utilise `DISTINCT ON`, pas une « fenêtre » au sens SQL (le « ~1 fenêtre » est approximatif) |
| `SCALE_EXPERIMENT_ROWS=1123580` | Nombre de réceptions à l'échelle | ✔ (`rows_submitted`) ; les lignes stockées sont 1 102 621 |
| `ANY_CANDIDATE_DROP_IN=FALSE` | Aucun candidat OSS ne peut être branché tel quel | Conclusion soutenue par 2 candidats exécutés, 2 lus ; 9+ non exécutés |
| `ANY_SCIENTIFIC_INVALIDATION=FALSE` | Aucun résultat n'invalide scientifiquement l'étude | Aucune contradiction interne majeure trouvée (voir 7) ; les faiblesses sont des limites de portée |
| `FINAL_VERDICT=POSTGRES_NATIVE_PIT_PATTERN_SUPPORTED` | Le motif PostgreSQL natif est soutenu par les preuves de cette étude synthétique | Verdict cohérent avec les résultats à condition de garder les réserves de la section 7 |

---

## 6. Contrôles de validité

### 6.1 Tests de fuite / lookahead
- Le test principal est **mécanique** : tout résultat contenant une ligne dont `ingested_at > T` est une fuite (`leak_of` dans `scenarios.py`, boucle des checks dans `joins.py`). La fonction de référence `pit.asof` ne fuit sur aucun des checks (`reference_leaks=[]`).
- Le test est bien construit pour la question posée : il ne dépend pas du SQL testé ; il compare l'`ingested_at` de la ligne renvoyée avec T.
- Angle mort (mon analyse) : la notion de fuite est **relative à l'axe `ingested_at`**. Si `ingested_at` lui-même était faux (par exemple parce que `strict_clock` a été mis à `false`, ou parce que le lot a été importé avec des horodatages fournis), le test ne le verrait pas.

### 6.2 Déterminisme
- Le rapport annonce comme contrat « deux exécutions à T identique → même ensemble d'`obs_id` » (`01`). Aucun script ne relance deux fois la même requête après une arrivée tardive pour comparer ; ce qui est testé est l'égalité avec l'oracle, et la stabilité décision/rejeu dans la course. La propriété est **soutenue** (le SQL est déterministe par tri total `revision, axe, obs_id`) mais **non testée en tant que telle** (?).
- Limite structurelle (mon analyse) : le dernier critère de tri est `obs_id`, un identifiant auto-incrémenté **propre à la base**. Deux bases reconstruites à partir des mêmes sources mais dans un ordre d'ingestion différent peuvent attribuer des `obs_id` différents ; le rejeu est donc déterministe **dans une même base**, pas forcément entre deux reconstructions.
- Reproductibilité des données : le générateur est déterministe (`seed=42`), l'ordre d'ingestion mélangé l'est aussi (`Random(1)`), mais l'attribution des `obs_id` dépend de l'ordre d'exécution du Python.

### 6.3 Contrôles négatifs / positifs
- Contrôles négatifs (méthodes fausses détectées) : C1, C2, C4, C5, C6 + Feast, DuckDB ASOF, Polars/pandas as-of, nearform, `WITHOUT OVERLAPS` sur SCD2. La batterie sait donc détecter des fuites.
- Contrôles positifs (méthodes correctes reconnues) : `pit.asof` (référence), DuckDB range+QUALIFY, Polars filtre+`first`. Le contrôle C3 est un cas particulier : il passe la batterie, ce qui ne suffit pas à le valider.
- Contrôle d'oracle : oracle Python indépendant du SQL de sélection, à la fois dans la batterie (25 cas) et à l'échelle (60 échantillons).

### 6.4 Erreurs corrigées en cours de route, écarts au protocole déclarés
- Le rapport ne documente **aucune** erreur corrigée en cours de route ni aucun écart au protocole (il n'y a pas de protocole écrit). Les seuls écarts déclarés sont des limitations (`11_LIMITATIONS.md`) : synthétique, `fsync=off`, append-only contournable, axe collecteur non validé au-delà de la batterie, verrou global non mesuré, Timescale (compression), candidats non exécutés, finalité fournisseur, oracle échantillonné, Feast réimplémenté.
- Un artefact de mesure est déclaré et expliqué : la taille Timescale de 8 Kio.
- Présence de `__pycache__` dans le commit d'origine, retiré de `main` : indice de nettoyage, sans effet.

### 6.5 Autres contrôles observés
- Test de mutation : `UPDATE` refusé sur la table plain (`pit: table obs is append-only (UPDATE refused)`) et sur un chunk d'hypertable ✔ (dans `scale_*.json`). Le `DELETE` sur chunk compressé n'a pas été testé (la compression a échoué).
- Test `nearform` T2 : un `sys_period` forgé est écrasé (donc l'horloge de transaction n'est pas falsifiable par l'appelant dans ce candidat).

---

## 7. Critique indépendante

### 7.1 Ce qui est solide
- La **logique de sélection PIT** est petite, lisible et vérifiée de deux façons indépendantes (attentes manuelles + oracle) sur 25 cas variés, plus 60 échantillons à 1,1 M de lignes sur deux axes (0 écart).
- La **falsification** est bien faite : les méthodes naïves (C1 à C6) et les moteurs courants sont pris en défaut par le même critère mécanique.
- La **découverte de la course de commit** est un vrai apport : elle montre qu'un modèle « correct » sur la logique peut être faux à la concurrence, et que le verrou côté écrivains seul ne suffit pas (`race.json`).
- La **candeur** de `11_LIMITATIONS.md` : les principales limites sont écrites.

### 7.2 Points faibles et choix fragiles
1. **Tout est synthétique**. Rien ne dit que les vrais flux (Binance, OKX, Coinbase) se comportent comme les cas S1 à S10. Les fréquences (2 % doublons, 3 % tardifs, 5 % révisions, 2 % backfill) sont des choix arbitraires.
2. **Le modèle est jugé par des attentes et un oracle écrits par la même équipe qui a écrit le SQL.** Un défaut de **compréhension** (la mauvaise règle métier) serait reproduit par les trois. Les 25 attentes prouvent que le SQL implémente la règle voulue, pas que la règle est la bonne.
3. **L'axe STRICT est présenté comme « inattaquable par l'appelant »**, mais : (a) `ingest` accepte un paramètre `p_ingested_at` qui est ignoré seulement si `strict_clock=true` ; (b) `strict_clock` est une valeur dans la table `pit.config`, que rien ne protège par trigger (les triggers d'append-only ne couvrent que `obs` et `obs_receipt`) ; (c) aucun test ne vérifie explicitement qu'avec `strict_clock=true` la valeur fournie est ignorée. La propriété est vraie **par lecture du code** (OBSERVED), pas testée (mon analyse). Le rapport `11` mentionne le contournement du propriétaire ou du superuser, mais pas cette porte-là.
4. **Les scénarios et l'échelle tournent avec `strict_clock=false`**. Le mode de production (horloge DB) n'est exercé que dans `race.py`. Les résultats « PROVEN » sur l'axe STRICT sont donc des résultats de **logique de requête sur des horodatages fournis**.
5. **Retour à un contenu ancien** (mon analyse, INFERENCE tirée du code et de S5b) : la dédup est faite sur `(source, provider_event_id, revision, content_hash)`. Pour un fournisseur **sans numéro de révision** (`revision = NULL`), si la valeur passe de A à B puis revient à A, la troisième livraison est traitée comme un doublon de la première, donc **absorbée** : la version « courante » restera B. C'est exactement le comportement voulu pour une redélivrance (S5b) mais faux pour un vrai retour à A. Le modèle ne peut pas distinguer les deux cas sans numéro de révision. Non testé, non mentionné dans `11`.
6. **Axe collecteur** : (a) la branche SKEW_CAP n'est jamais exercée ; (b) à l'échelle, `first_observed_at` est toujours à moins d'1 s de l'ingestion, donc l'axe ne se distingue presque pas de STRICT ; (c) le rapport le qualifie lui-même de « CONDITIONNEL ». Conclusion : seul l'axe STRICT est réellement établi.
7. **Verrou global** : `pg_advisory_xact_lock(hashtext('pit.stamp_order'))` sérialise **tous** les écrivains. Débit sous concurrence non mesuré ; l'insertion à 6 561 lignes/s a été obtenue sans concurrence et `synchronous_commit=off`. Le lecteur de décision doit appeler `decision_cutoff()` : c'est une **discipline applicative** (le rapport `11` le dit). Un oubli rend le système à nouveau vulnérable, sans erreur visible.
8. **Course : un seul run** avec des `sleep`. Pas de répétition, pas de test avec plusieurs instruments ni avec des transactions longues (par exemple les batches de 5 000 lignes du chargement).
9. **Alternative native non explorée** (mon analyse, INFERENCE) : le rapport ne discute pas l'usage de mécanismes de visibilité de PostgreSQL (identifiants de transaction, instantanés) comme axe de connaissance à la place d'une horloge murale. Je n'affirme pas que cela résoudrait la course, seulement que l'espace des solutions n'a pas été exploré.
10. **Comparaison Feast** : réimplémentation et pas exécution ; « fuite » définie selon une colonne que Feast ne connaît pas (voir 3.4).
11. **Comparaison de vitesse Polars/DuckDB/PG** à périmètre non identique (voir 3.5).
12. **Timescale** : le PARK repose sur ×3,8 en latence à 1,1 M de lignes avec 2 chunks seulement ; à cette taille, les avantages de Timescale (compression, chunk exclusion sur de très gros volumes) n'ont pas de raison d'apparaître ; le test n'est pas à même de départager l'outil sur ses points forts. Le rapport le reconnaît en partie (compression non testée).
13. **Volume** : 1,1 M de lignes ≈ 250 instruments × ~14,6 jours de barres 5 minutes. C'est petit par rapport à des historiques de plusieurs années sur plus d'instruments. Extrapoler la latence et la taille (502 octets par ligne, 0,145 Go de journal) est une INFERENCE.
14. **Recouvrement des tests de mutation** : le rapport dit que l'append-only tient (UPDATE bloqué), mais TRUNCATE, DELETE et `ALTER TABLE … DISABLE TRIGGER` ne sont pas testés dans les scripts fournis ; le rapport `11` reconnaît le contournement.
15. **Pas de préenregistrement** : impossible de prouver que les critères précèdent les résultats. Les verdicts sont surtout binaires et mécaniques, ce qui limite le risque, mais la sélection des scénarios (S1 à S10) reste au choix de l'auteur.

### 7.3 Ce que les chiffres ne prouvent PAS
- Ils ne prouvent pas que ce motif est **compatible** avec AurumShift (interdit par `claude.md`).
- Ils ne prouvent pas la correction sur des flux réels (formats, horloges, retards réels).
- Ils ne prouvent pas la tenue sous **concurrence** ni sous **durabilité complète**.
- Ils ne prouvent pas que l'append-only résiste à un acteur privilégié.
- Ils ne prouvent pas la **finalité** réelle chez OKX et Coinbase, ni même qu'une clôture Binance est définitive.
- Ils ne prouvent pas l'absence de meilleur candidat parmi ceux non exécutés.
- « 0 écart / 60 échantillons » ne borne pas le taux d'erreur vrai : avec 0 échec sur 60, la borne haute à 95 % est de l'ordre de 5 % (règle des trois : 3/60 = 5 %) (mon calcul). Les 25 cas manuels couvrent des scénarios ciblés, pas une proportion de l'espace.

### 7.4 Écarts entre rapports et résultats bruts (bilan)

| Élément | Rapport | Brut | Statut |
|---|---|---|---|
| 25/25 vérifications | oui | `scenarios.json` : 25 checks, 25 pass | ✔ |
| 1 123 580 réceptions / 1 102 621 lignes | oui | `scale_plain.json` | ✔ |
| Insertion 6 561 vs 4 700 l/s | oui | idem | ✔ |
| Heap 226 Mo / index 328 Mo | oui | 225 910 784 o / 328 155 136 o (unités décimales) | ✔ |
| 502 o/obs | oui | 502 | ✔ |
| PIT p50 1,7 / 2,45 ms ; Timescale 6,5 / 10,9 | oui | 1,70 / 2,45 ; 6,50 / 10,88 | ✔ |
| Flotte 492 vs 781 ms | oui | 491,83 vs 781,31 | ✔ |
| `latest_known` p50 0,14 / 0,23 | oui | idem | ✔ |
| Oracle 0/60 ×2 | oui | 0 sur 60 échantillons (30 tirages × 2 axes) | ✔ |
| Course NONE/LOCK_W/LOCK_RW | oui | `race.json` | ✔ |
| Feast défaut 10 fuites | oui | `joins.json` : 10 | ✔ |
| Rejeu hors base 0,62/0,18/0,56 s ; 630 740 faits | oui | `fleet_offline.json` | ✔ |
| nearform T1–T7 | oui | `cand_temporal_tables.json` | ✔ |
| `WITHOUT OVERLAPS` : fuite SCD2, invariant dérivé, intervalle vide | oui | `without_overlaps.txt` | ✔ |
| Slots S8/S8b, garde fail-closed | oui | `scenarios.json` | ✔ |
| Métadonnées candidats (dates, licences) | oui | `candidates_meta.tsv` | ✔ |
| « S1–S12 » | oui | Il n'y a pas de S11/S12 séparés | ✘ mineur (présentation) |
| « S3b/S3c plafonnés LAG_CAP » | oui | S3b = BACKFILL cap ; S3c = LAG_CAP | ✘ mineur |
| SKEW_CAP « validé sur la batterie » | oui | aucun scénario n'exerce SKEW_CAP | ✘ ou ? (non vérifié dans les fichiers lus) |
| DuckDB : « égalités non déterministes » | oui | aucun test de ce point dans les scripts lus | ? |
| Finalité Binance/OKX/Coinbase | oui | aucune capture de page dans le dépôt | ? |
| « ~1 fenêtre » (complexité) | oui | la requête utilise `DISTINCT ON`, pas de fenêtre | imprécision de vocabulaire |
| Hash de commit `nearform` `1824073a` | dans le script | non vérifié | ? |

Bilan : **aucune contradiction numérique** entre rapports et résultats bruts sur les 24 chiffres clés vérifiés. Les écarts sont de présentation ou de couverture.

### 7.5 Contradictions internes
- Aucune contradiction forte. Une tension : le résumé parle de « PROVEN » pour Q4 sur l'axe STRICT, avec `BACKFILL_LOOKAHEAD_PREVENTED=TRUE` sans qualificatif dans le bloc final, alors que l'axe collecteur est « CONDITIONNEL » dans le corps. Le bloc final devrait porter la mention « axe STRICT » (mon analyse).
- `ANY_SCIENTIFIC_INVALIDATION=FALSE` cohabite avec plusieurs choses non testées (durabilité, concurrence), ce qui est acceptable (« pas d'invalidation » n'est pas « validation complète »).

### 7.6 Détails mineurs
- Le rapport `01` parle de « S1–S12 » (voir 3.2.1). Le rapport `05` parle de « validé sur la batterie seulement » pour la dérive d'horloge, ce qui est cohérent avec la limite.
- Le rapport `06` liste `arkhipov` et `periods` sous D ; le rapport `10` les range en PARK avec l'INFERENCE « même modèle d'horloge de transaction attendu ». Cette inférence est plausible, non testée.

---

## 8. Comparaison de plusieurs runs ou branches

Il n'y a **qu'une seule branche** (`claude/pit-safe-evidence-replay-v1`) et **un seul run** par mesure. Il n'y a pas de branche « -b » pour cette lane (contrairement à d'autres lanes du dépôt comme `alternative-data-v1-b`). Les comparaisons internes possibles :

### 8.1 Plain contre Timescale (mêmes questions, chiffres côte à côte)

| Question | Plain | Timescale | Accord ? |
|---|---|---|---|
| Correction (écarts d'oracle) | 0/60 | 0/60 | Accord |
| Append-only (UPDATE bloqué) | oui | oui (sur chunk) | Accord |
| Débit d'insertion | 6 561 l/s | 4 700 l/s | Diverge (-28 %) |
| Latence PIT p50 | 1,70 ms | 6,50 ms | Diverge (×3,8) |
| Latence `latest_known` p50 | 0,14 ms | 0,23 ms | Diverge (×1,6) |
| Flotte 250 instr | 491,83 ms | 781,31 ms | Diverge (×1,6) |
| Taille | 502 o/obs mesurés | non mesurable | Non comparable |
| Compression | sans objet | échec de licence | Non testé |

Pourquoi ça diverge (INFERENCE, non testée) : la partition en chunks ajoute un coût de planification et de fusion pour une requête qui n'est pas filtrée par `event_time`, et la clé unique élargie à `event_time` alourdit l'insertion. Le rapport ne donne pas d'explication ; c'est mon hypothèse.

### 8.2 Batterie contre échelle
Les deux montrent 0 écart avec l'oracle ; la batterie teste des cas ciblés (pièges), l'échelle teste la volumétrie avec des cas aléatoires génériques. Elles se complètent mais ne se recoupent pas : les cas de piège (S3b/c, S4b, S7b, S10) ne sont pas dans le générateur d'échelle.

### 8.3 Rapport contre résultats bruts
Voir 7.4 : accord sur tous les chiffres vérifiés.

### 8.4 Autres lanes
Une lane 005 (`data_feed_resilience`, avec un fichier `08_PIT_READINESS.md`) traite un sujet voisin ; **non lue** ici. Aucune comparaison n'est faite.

---

## 9. Reproductibilité

### 9.1 Ce qui est fourni
- Tout le SQL (`sql/001_schema.sql`, `002_functions.sql`, `003_race.sql`, `010_without_overlaps.sql`).
- Tous les scripts Python (`common.py`, `gen.py`, `scenarios.py`, `joins.py`, `race.py`, `scale.py`, `fleet_offline.py`, `cand_temporal_tables.py`).
- Les résultats bruts (JSON, logs, TSV) et l'environnement (`env/environment.txt`).
- Une copie du code de Feast avec son commit (`results/feast_src/postgres.py` et `.commit`).

### 9.2 Comment relancer (reconstitué à partir des scripts ; aucun mode d'emploi n'est écrit dans le dépôt)
1. Disposer d'un PostgreSQL 18.6 jetable écoutant sur un socket Unix. Les scripts lisent les variables d'environnement `PGHOST` (défaut `~/.cache/tmp/ext`), `PGPORT` (défaut `54329`), `PGUSER` (défaut `pit`), `PITDB` (défaut `pitlab`). Les bases utilisées : `pitlab` (plain), `pitts` (Timescale), `pitx` (jointures), `pitc` (candidat nearform).
2. Avoir Python 3.14 avec `psycopg`, `duckdb`, `polars`, `pandas`.
3. Batterie : `python bench/pit_v1/py/scenarios.py` (crée le schéma, lance S1-S10 et C1-C6). Jointures : `joins.py` (exécute d'abord la batterie). Course : `race.py`. Échelle : `scale.py plain` puis `scale.py ts`, `fleet_offline.py`. Candidat : `cand_temporal_tables.py` (nécessite l'extension `nearform/temporal_tables` installée dans la base `pitc`). `WITHOUT OVERLAPS` : `psql -f sql/010_without_overlaps.sql` (extension `btree_gist`).
4. Durées observées : insertion de 1,12 M de réceptions 171,2 s (plain) et 239,1 s (Timescale), sur matériel puissant avec `fsync=off`. La durée totale des autres scripts n'est pas documentée (?).

### 9.3 Ce qui manque
- Aucun README ni script de lancement global ; l'initialisation du serveur PostgreSQL (`initdb`, options `fsync=off`…) n'est pas fournie.
- L'installation de TimescaleDB et de `nearform/temporal_tables` n'est pas scriptée.
- Pas de fichier de dépendances (`requirements.txt`) ; les versions sont seulement dans `environment.txt`.
- Les `obs_id` et les horloges (`race.json`, `fleet_offline.json`) dépendent de l'exécution ; les valeurs numériques absolues (débits, latences) ne se reproduiront pas à l'identique (machine partagée).
- Les pages web citées pour la finalité fournisseur ne sont pas archivées.
- Je n'ai **pas** relancé les scripts : je n'ai pas vérifié qu'ils s'exécutent. Mes vérifications portent sur la cohérence entre rapports, code et résultats fournis.

---

## 10. Implications pratiques pour AurumShift (pistes « à adjuger plus tard »)

Rappel : rien ici n'affirme une compatibilité avec le dépôt privé AurumShift, dont je ne sais rien. Ce sont des pistes à adjuger plus tard contre le vrai dépôt local.

1. **Piste : le motif « observations en ajout seul + journal de réceptions »** pourrait, si le dépôt privé utilise déjà PostgreSQL, être comparé à ce que fait le code existant pour stocker les données de marché et leur provenance. À adjuger : le code existant a-t-il déjà un axe de connaissance dans la base ?
2. **Piste : discipline d'horloge.** La règle « c'est l'horloge de la base qui estampille, pas le collecteur » est facile à vérifier dans un code existant (qui écrit `ingested_at` ?). À adjuger.
3. **Piste : rejeu hors base avec DuckDB ou Polars** en forme « filtre + première ligne par groupe », et **interdiction de `ASOF JOIN` / `merge_asof` sur l'horloge de l'événement** pour toute étude qui doit être PIT. À adjuger : quels outils de rejeu sont déjà utilisés ?
4. **Piste : la course de commit.** Vérifier si une décision peut être prise pendant qu'une écriture est en vol. À adjuger : le code existant prend-il un T sans barrière ?
5. **Piste : fail-closed sur données incomplètes** (créneaux manquants, provenance non vérifiée, donnée périmée) avec une garde du type `assert_replayable`. À adjuger.
6. **Piste : finalité fournisseur.** Ne pas réutiliser le modèle sans un adaptateur par fournisseur ; par défaut UNKNOWN. À adjuger : quels fournisseurs AurumShift utilise-t-il ?
7. **Piste : composants à écarter d'office** d'après cette étude, à condition que le contexte soit le même : mise à jour en place (SCD1), `ASOF JOIN` sur l'horloge de l'événement, tables d'historique fondées sur `now()` de transaction.
8. **Piste : ne rien ajouter** (pas de second datastore ni de second service) tant qu'un besoin mesuré ne le justifie : c'est la conclusion du rapport, cohérente avec « complexité d'infrastructure doit se justifier ». À adjuger contre les volumes réels.

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **(Très haute valeur) Tester le mode de production** : `strict_clock=true`, `fsync=on`, `synchronous_commit=on`, plusieurs écrivains concurrents, avec le verrou global. Mesurer débit et latence de décision. Vérifier explicitement que la valeur `p_ingested_at` est ignorée et que `pit.config` est protégée.
2. **(Très haute valeur) Répéter la course** N fois (par exemple N ≥ 100) avec plusieurs instruments, transactions longues (batches de 5 000) et plusieurs lecteurs ; chercher un cas où LOCK_RW échoue. Explorer une alternative fondée sur les mécanismes natifs de visibilité de PostgreSQL.
3. **(Haute valeur) Tester le retour à un contenu ancien** pour les fournisseurs sans révision (A → B → A) et définir la règle (par exemple exiger un numéro de séquence côté adaptateur).
4. **(Haute valeur) Exercer l'axe collecteur** : cas `first_observed_at` futur (SKEW_CAP), dérive d'horloge progressive, jeu d'échelle où une fraction significative des lignes LIVE dépasse `max_lag`.
5. **(Haute valeur) Valider avec des flux réels** enregistrés (Binance au minimum) : comparer les clôtures `x=true` avec des re-téléchargements différés pour mesurer les restatements réels. Archiver les pages de documentation citées (OKX `confirm`, Coinbase).
6. **(Moyenne) Exécuter les candidats restants** (`pgMemento`, `periods`, `arkhipov`, `pg_bitemporal`) avec les tests T1–T7, pour transformer les INFERENCE en OBSERVED ou PROVEN.
7. **(Moyenne) Sécurité de l'append-only** : rôles, `REVOKE`, propriétaire séparé, test de `DISABLE TRIGGER`, `TRUNCATE`, `DELETE`.
8. **(Moyenne) Timescale** : tester avec un build permettant la compression ; mesurer les tailles des chunks ; tester à un volume supérieur (par exemple 50 à 100 M de lignes).
9. **(Moyenne) Durcir l'oracle** : un second oracle écrit par une autre personne ou dans un autre langage, sans reprendre la règle de tri de l'auteur ; plus de 60 échantillons ; test de propriétés (propriété-based testing) sur des jeux aléatoires avec injection systématique des cas pièges.
10. **(Basse) Reproductibilité** : ajouter un README, un script de lancement, un fichier de dépendances, un mode d'emploi pour `initdb`.
11. **(Basse) Corriger la présentation** : S11/S12, S3b vs S3c (BACKFILL/LAG_CAP), « ~1 fenêtre », mention « axe STRICT » dans `BACKFILL_LOOKAHEAD_PREVENTED`.

---

## 12. Index des fichiers lus

Rapports (`reports/004_pit_safe_evidence_replay/`) — tous lus intégralement :
- `00_EXECUTIVE_SUMMARY.md` — conclusion, réponses Q1-Q6, trouvaille majeure (course), bloc final, réserves.
- `01_REQUIREMENTS_AND_THREAT_MODEL.md` — 5 contrats testés, deux axes de connaissance, menaces S1-S12 et C1-C6.
- `02_CANDIDATE_LANDSCAPE.md` — tableau des familles de candidats, licences, dates, statut E/D.
- `03_POSTGRES_REFERENCE_MODEL.md` — description du schéma de référence, requêtes et vues.
- `04_PIT_QUERY_EXPERIMENTS.md` — scénarios S1-S12, contrôles C1-C6, course, jointures alternatives, échelle hors base.
- `05_BACKFILL_AND_REVISION_TESTS.md` — backfill, révisions, doublons, restatements, test de mutation.
- `06_OSS_COMPONENT_EVALUATION.md` — WITHOUT OVERLAPS, nearform, pg_bitemporal, Feast, DuckDB/Polars, Timescale, non exécutés.
- `07_SCALE_EXPERIMENT.md` — tableau plain vs Timescale à 1,1 M de lignes.
- `08_PROVIDER_FINALITY.md` — finalité Binance/OKX/Coinbase.
- `09_FAILURE_AND_LOOKAHEAD_MATRIX.md` — matrice d'approches × types d'échec.
- `10_ADJUDICATION.md` — cinq rôles et décisions ADOPT/ADAPT/PARK/REJECT.
- `11_LIMITATIONS.md` — liste des limitations.

SQL (`bench/pit_v1/sql/`) — lus intégralement :
- `001_schema.sql` — types, tables `obs`, `obs_receipt`, `config`, index, triggers d'ajout seul.
- `002_functions.sql` — `ingest`, `asof`, `asof_collector`, `asof_final`, `latest_known`, `slots`, `assert_replayable`, vues.
- `003_race.sql` — `ingest_locked` et `decision_cutoff` (verrou advisory exclusif/partagé).
- `010_without_overlaps.sql` — expérience `WITHOUT OVERLAPS` sur SCD2 mutable et table dérivée.

Scripts Python (`bench/pit_v1/py/`) — lus intégralement :
- `common.py` — connexion, dates de base, oracle indépendant, sauvegarde.
- `gen.py` — générateur déterministe de 1,1 M d'observations.
- `scenarios.py` — batterie S1-S10, 25 checks, comptages, slots, garde, contrôles C1-C6.
- `joins.py` — comparaison Feast/DuckDB/Polars/pandas.
- `race.py` — course de commit, 3 régimes.
- `scale.py` — expérience d'échelle plain/Timescale, latences, oracle.
- `fleet_offline.py` — rejeu hors base Polars/DuckDB.
- `cand_temporal_tables.py` — tests T1-T7 du candidat nearform.

Résultats (`bench/pit_v1/results/`) — lus (les JSON complets ont été affichés ou agrégés) :
- `scenarios.json` — 25 checks, comptages, slots, garde, contrôles, alias de dédup.
- `joins.json` — 8 méthodes × 23 paires (agrégats lus ; exemples de fuite non détaillés).
- `race.json` — 3 régimes.
- `scale_plain.json` / `scale_plain.log` — mesures plain (le log reproduit le JSON).
- `scale_ts.json` / `scale_ts.log` — mesures Timescale.
- `fleet_offline.json` — rejeu hors base.
- `cand_temporal_tables.json` — T1-T7.
- `candidates_meta.tsv` — métadonnées GitHub des candidats (dates, licences, étoiles).
- `without_overlaps.txt` — sortie brute de `psql`.
- `pg_bitemporal_correction_excerpt.sql` — extrait de la fonction de correction (lu en début de fichier ; suite non lue).
- `feast_src/postgres.py` — 1 392 lignes de code Feast (lues par sondage : lignes 70-160 et repérages par recherche de motifs ; le reste **non lu**).
- `feast_src/postgres.py.commit` — hash `f0bc0700be7029166e6605e407de6d229cd1e93e`.

Autres :
- `bench/pit_v1/env/environment.txt` — environnement d'exécution.
- `claude.md` (racine) — doctrine du dépôt (lu).
- Historique Git de la PR n° 4 et du commit `cfb332e` (dates, auteur, volume).

Non lus : `reports/005_data_feed_resilience/08_PIT_READINESS.md` et les autres lanes ; `SYNTHESE_LANES.md` (présent en local, absent de `origin/main`) ; les pages web fournisseurs citées dans `08_PROVIDER_FINALITY.md` (non archivées) ; la suite de l'extrait `pg_bitemporal` et la plus grande partie de `feast_src/postgres.py`.
