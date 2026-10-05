# raw_laneBJKL — PIT/bitemporel (B), stockage/compute/événements (J), observabilité/qualité/tracking (K), mémoire/outillage agent (L)

Mission AURUMSHIFT_EXTERNAL_ACCELERATION_RADAR_V1 · date sandbox 2026-10-05 · laboratoire externe : aucun code, aucune base ni aucun credential AurumShift touché.
Étiquettes : VERIFIED_FACT · MEASURED_BY_THIS_MISSION (MBTM) · UPSTREAM_BENCHMARK · VENDOR_CLAIM · INFERENCE · UNKNOWN.
Base : LAB_PRIOR 004 (PIT Postgres natif ; 00, 04, 06, 10), LAB_PRIOR 017 (infra OSS ; 00, 02, 05, 07, 08), LAB_PRIOR 002 (orchestration ; 06).
Règle appliquée : aucune infra « par mode ». Un candidat ne monte que s'il y a un goulot mesuré ou un bénéfice scientifique proche du chemin critique (premier OutcomeV1 forward ; expérience quorum A/B/C sur un DecisionInput gelé). L'autorité PIT reste Postgres.

## 0. Environnement et écarts de procédure
- Venvs : `scratchpad/venvs/laneBJKL` (polars 1.44.2, duckdb 1.5.6, pandas 3.0.6, pyarrow 25.0.1, pandera 0.33.1, psycopg 3.3.6, adbc-driver-postgresql 1.12.0), `laneBJKL_mlflow` (mlflow 3.16.1), `laneBJKL_mlflow-skinny`, `laneBJKL_otel` (opentelemetry-sdk 1.45.0), `laneBJKL_pandera` (mesure d'empreinte seulement).
- **Écart 1 :** le scratchpad est `root:700` et son parent était remis en 700 pendant la session. L'utilisateur `postgres` ne pouvait donc pas y accéder. L'instance PG16 jetable a tourné dans `/tmp/laneBJKL_pg` (port 55433, `fsync=off`, `pg_stat_statements` préchargé). Elle a été arrêtée puis supprimée à la fin (MBTM).
- **Écart 2 :** pour compiler pgvector, `apt-get update && apt-get install postgresql-server-dev-16` a été lancé. Effet de bord dans le sandbox : le paquet `postgresql-16` est passé de 16.14 à 16.15, et `vector.so` a été installé dans `/usr/lib/postgresql/16/lib`. Ce changement ne touche que le sandbox, mais il peut concerner d'autres lanes qui utilisent PG16.
- Pas d'accès à l'API GitHub (`gh api` refusé pour la session). Les licences ont été lues dans `raw.githubusercontent.com/<repo>/<branche>/LICENSE`, les tags via `git ls-remote`, et les versions et dates via l'API JSON de PyPI.
- Reproduction : `bench/laneBJKL/run.sh`. Toutes les données sont synthétiques et seedées (seed 18). Machine de 4 vCPU et 15 Go partagée avec d'autres lanes, donc les temps sont indicatifs (mesure unique).

## 1. LANE B — PIT / bitemporel / identité de features

### B-1 Ce qui est réellement dans PG18, et ce qui ne l'est toujours pas en PG19
- VERIFIED_FACT (https://www.postgresql.org/docs/18/release-18.html) : PG18 ajoute les « temporal constraints » : `WITHOUT OVERLAPS` pour PRIMARY KEY/UNIQUE et `PERIOD` pour FOREIGN KEY, sur la dernière colonne (range). Il ajoute aussi `uuidv7()`, des colonnes générées virtuelles par défaut et l'AIO.
- VERIFIED_FACT (absence) : `FOR PORTION OF` (UPDATE/DELETE temporels) **n'apparaît ni** dans les notes PG18, **ni** dans la doc `sql-update` devel, **ni** dans les notes PG19. Vérifié le 2026-10-05 ; PG19 en est à la Beta 4 du 2026-09-24 (https://www.postgresql.org/docs/19/release-19.html).
- VERIFIED_FACT (https://www.postgresql.org/docs/19/ddl-temporal-tables.html) : « PostgreSQL does not currently support system time ». PG19 ajoute seulement une section de documentation sur les tables temporelles (application time).
- VERIFIED_FACT (https://www.postgresql.org/support/versioning/) : les versions courantes sont 18.6 et 16.15.
- Conséquence (INFERENCE, cohérente avec LAB_PRIOR 004/06) : le natif PG ne fournit toujours pas de temps de connaissance (system time). Le motif de 004 (append-only + `ingested_at` horloge DB + verrous advisory) reste nécessaire. `WITHOUT OVERLAPS` sert d'invariant sur une table dérivée → **WATCH**.

### B-2 ASOF : l'interdiction de LAB_PRIOR 004 tient-elle encore, et pourquoi ? (L3, MBTM)
Script : `bench/laneBJKL/pit_asof_bench.py`. Sémantique de référence (004 Q3), pour une décision (symbol, T) :
1. lignes connues = `ingested_at ≤ T` **et** `event_time ≤ T` ;
2. fait = `event_time` max ;
3. version = `revision` max parmi les lignes connues.

Les données sont construites pour exercer les cas difficiles :
- 50 symboles, 1 à 3 révisions par fait ;
- 2 % des faits révisés ont leur rev0 qui arrive **après** la rev1 (cas S4b) ;
- 0,1 % des lignes ont une horloge biaisée (`ingested_at < event_time`) ;
- `ingested_at` est arrondi à 10 ms, ce qui crée des ex aequo.

La référence (DuckDB range join + QUALIFY, forme 004) est calculée sur les 2 000 premières décisions. Le contrôle de lookahead porte sur les 200 000.

| 5 000 095 lignes, 200 000 décisions (versions polars 1.44.2, duckdb 1.5.6) | écarts vs réf. /2 000 | décisions avec lookahead /200 000 | temps |
|---|---|---|---|
| Référence range+QUALIFY (2 000 décisions seulement) | — | — | 21,25 s |
| Polars `join_asof` naïf sur `event_time` | 579 | **57 423** | 0,32 s |
| Polars `join_asof` naïf sur `ingested_at` | 328 | 72 | 0,68 s |
| DuckDB `ASOF JOIN` naïf sur `ingested_at` | 328 | 72 | 1,11 s |
| **Polars timeline-ASOF** (nouveau motif) | **0** | **0** | **3,83 s** |
| **DuckDB timeline-ASOF** (même motif, SQL) | **0** | **0** | 5,33 s |
Instantané de flotte à un T (gel d'un DecisionInput, forme 004) : Polars 0,40 s et DuckDB 0,67 s, résultats identiques. Les deux timelines sont identiques sur les 200 000 décisions (`polars_vs_duckdb_timeline_full_equal=true`). À 1 M lignes : réf. 5,96 s pour 2 000 décisions, timeline Polars 0,71 s et DuckDB 1,11 s pour 200 000 décisions, mêmes conclusions (0 écart, 0 lookahead) (`res_pit_asof_1000000.json`).

**Pourquoi l'ASOF naïf reste interdit (MBTM, confirme 004) :**
- (a) Sur `event_time`, l'ASOF ignore le temps de connaissance : 28 % des décisions voient une ligne ingérée après T.
- (b) Sur `ingested_at`, il prend la *dernière arrivée*. C'est une révision inférieure arrivée en retard, ou une révision tardive d'un fait plus ancien. Les lignes à horloge biaisée fuient en plus (72 cas).
- (c) DuckDB n'admet qu'**une seule** inégalité dans un ASOF (VERIFIED_FACT, https://duckdb.org/docs/current/sql/query_syntax/from). Les deux axes ne peuvent donc pas être exprimés directement.
- (d) Les ex aequo ne sont pas déterministes : à 1 M lignes, Polars donne 421 écarts et DuckDB 420 sur les mêmes données.

**Apport nouveau (MBTM) :** l'ASOF devient **exact** une fois appliqué à une *timeline de connaissance* dérivée :
- (1) `available_at = greatest(ingested_at, event_time)`. Les deux conditions `≤ T` se réduisent alors à une seule.
- (2) Par symbole, trié par `available_at`, on prend le cummax lexicographique de `(event_time, revision)` (encodé `event_time*4+revision`), puis une ligne par instant.
- (3) On fait un `join_asof backward` sur `available_at`.

Coût : une passe de tri, puis O(log n) par décision. Cela remplace un range join en O(N×M) : à 5 M lignes, environ 10,6 ms par décision pour la référence contre environ 0,02 ms pour la timeline. Le facteur d'environ 550 vient d'une extrapolation linéaire (INFERENCE).

Limites : l'encodage suppose `revision < 4`. La finalité (filtre après sélection, 004) n'est pas couverte. La règle `ingested_at ≥ event_time` reste à surveiller : `greatest()` *masque* les horloges biaisées au lieu de les signaler (voir K-1). Classification : **BENCH_NOW** (L3 sur de vrais fichiers C0, en rejeu offline seulement ; l'autorité reste la fonction SQL Postgres).

### B-3 Fiches courtes (L0)
- **XTDB v2** — VERIFIED_FACT : licence MPL-2.0 (fichier LICENSE). Bitemporel « automatique » au sens SQL:2011 (https://docs.xtdb.com/). Tag observé : `v2.2.0-rc1`. Client PyPI `xtdb` 0.6.2 de 2023 (VERIFIED_FACT, PyPI). C'est un serveur JVM avec sa propre persistance, donc un **second datastore** qui deviendrait une seconde autorité PIT. **PARK** sans dossier de migration. UNKNOWN : comportement face à la course de commit (non exécuté).
- **Dolt / DoltgreSQL** — Apache-2.0, tag v1.4.0 (VERIFIED_FACT). La version y est un *commit*, pas le temps de connaissance fournisseur (INFERENCE). Churn et corruptions observés via Beads/Dolt dans LAB_PRIOR 002. **PARK**.
- **Iceberg / Delta (PyIceberg 0.12.0, deltalake 1.6.6)** — le time travel repose sur le temps de *commit* du snapshot (INFERENCE). Utile pour archiver des fichiers C0, mais Parquet + sha256 (LAB_PRIOR 017 : écritures pyarrow reproductibles octet à octet) suffit pour un canari file-only. **PARK**.
- **lakeFS** — serveur + store, sans goulot mesuré. **PARK**.
- **Feast 0.66.0** — algorithme de référence. Le PIT y repose sur `event_timestamp` seul, sans révision (004). **PARK**.
- **Hopsworks 5.0.9** (plateforme) → **PARK**. **Featureform 1.15.8** (dernière release 2025-04-11, VERIFIED_FACT PyPI) → **REJECT**. **Chronon 0.0.115** (Apache-2.0, Scala/Spark) → **PARK**, référence pour les backfills PIT seulement.
- **temporal_tables (nearform)**, **pg_bitemporal** → **REJECT** (004). **periods / arkhipov** → **PARK** (004).
- **Détection de fuite** : `deepchecks` 0.19.1 (dernière release 2024-12-15, VERIFIED_FACT PyPI) cible des fuites ML IID. Il n'a pas de test de troncature temporelle → **PARK**. Le contrôle le plus utile reste le **test de troncature/préfixe** maison : le résultat à T doit rester inchangé quand on ajoute des lignes avec `available_at > T`. Il s'ajoute au contrôle « ligne retenue `ingested_at ≤ T` et `event_time ≤ T` » utilisé ici, qui a détecté 57 423 fuites → **BENCH_NOW** (motif, quelques lignes).

## 2. LANE J — stockage / compute / événements

### J-1 Versions (VERIFIED_FACT, PyPI)
DuckDB 1.5.6 (2026-09-28) est **identique** à LAB_PRIOR 017. Polars est en 1.44.2. Les résultats ASOF/Parquet de 017 ne sont donc pas refaits, au-delà de B-2.

### J-2 Transfert PG ↔ Arrow (L2, MBTM, `pg_transfer_bench.py`)
Cas mesuré : 1 M lignes C0, Parquet → PG16, puis relecture.

| Opération | Temps | Égalité (sha256 canonique) |
|---|---|---|
| ADBC `adbc_ingest` (Parquet → table) | 1,74 s | — |
| psycopg COPY BINARY (boucle Python `write_row`) | 2,02 s | — |
| ADBC `fetch_arrow_table` | 0,93 s | égal |
| psycopg `fetchall` (tuples Python) | 3,16 s | — |
| DuckDB `ATTACH … (TYPE postgres, READ_ONLY)` → Arrow | 0,86 s | égal |

Piège observé (MBTM) : en DuckDB 1.5, `.arrow()` renvoie un `RecordBatchReader` *paresseux*. Une première mesure de 0,06 s était fausse : la lecture n'avait pas encore eu lieu.

Lecture : en rejeu ou export de DecisionInput, l'Arrow natif gagne environ ×3,4 en lecture. En écriture, le gain est marginal face à COPY. Aucun goulot AurumShift n'est mesuré → ADBC et le scanner DuckDB passent en **WATCH**.

### J-3 Fiches L0
- **TimescaleDB 2.30.2** — VERIFIED_FACT : le fichier LICENSE indique un mélange Apache-2.0 / Timescale License. La compression et les CAgg relèvent de la TSL (017). Latence PIT environ 3,8 fois plus élevée (004). **PARK**.
- **pg_duckdb** (MIT, tag v1.1.1) — introduit un moteur tiers *dans le processus* de l'autorité PG (preload) sans goulot mesuré → **PARK**.
- **pg_mooncake** (MIT, tag v0.1.3) — jeune → **PARK**.
- **pg_parquet** (licence PostgreSQL, tag v0.5.1) — `COPY TO/FROM` Parquet côté serveur. Pertinent pour geler un DecisionInput, mais pas compilé ici (pgrx) ; l'alternative côté client (ADBC/pyarrow) est mesurée → **WATCH**.
- **DataFusion 54.0.0** — fait doublon avec DuckDB/Polars → **PARK**.
- **NATS JetStream** (Apache-2.0) → **PARK** : second service/log, alors que le runtime événementiel est déjà une autorité AurumShift.
- **Redpanda** → **REJECT** : BSL + RCL (VERIFIED_FACT, `licenses/README.md`), plus un service.
- **LISTEN/NOTIFY + réplication logique** — natifs. NOTIFY n'est pas durable (INFERENCE, doc) → **WATCH**.
- **pgmq** (licence PostgreSQL, v1.13.0) — recouvre LAB_PRIOR 002 (Absurd/Procrastinate) → **PARK**.

## 3. LANE K — observabilité / qualité / tracking d'expériences

### K-1 DQ « observation C0 » (L2, MBTM, `dq_c0_bench.py`, 999 971 lignes)
Colonnes : venue, symbol, event_time, ingested_at, bid, ask, depth (3 venues × 22 symboles). Huit familles de fautes injectées à compte connu :
- 37 bid ≥ ask ;
- 23 lignes ingérées avant l'event ;
- 41 lignes avec un retard > 5 s ;
- 11 profondeurs négatives ;
- 9 trous > 60 s ;
- 7 inversions ;
- 5 doublons ;
- 6 bid nuls.

| | lignes de code | temps 1 M | comptes |
|---|---|---|---|
| Polars écrit à la main | **13** | 0,50 s | crossed 37, ing<ev 30, stale 41, depth<0 11, null 6, non-monotone 12, gaps 9, clés dupliquées 10 |
| Pandera 0.33.1 backend polars (`DataFrameModel` + 5 `dataframe_check`) | 26 | 0,60 s | **identiques à la main sur les 8 règles** |
| Pandera backend pandas (`DataFrameSchema`) | 12 | 1,31 s (+ conversion) | failure_cases en *cellules* : 295 pour bid_lt_ask ; en lignes uniques, 43 |

Les écarts avec les fautes injectées sont tous expliqués (MBTM) :
- 30 = 23 injectées + 7 effets des inversions ;
- 12 = 7 inversions + 5 doublons ajoutés en fin de flux ;
- 10 = 5 paires de doublons.

**Piège observé :** un `bid` nul **passe** le check custom `bid < ask` en Polars (comparaison nulle ⇒ non comptée : 37), mais **échoue** en pandas (NaN ⇒ False : 43). Il est rattrapé dans les deux cas par `not_nullable`, mais la sémantique des nulls diffère selon le backend.

Empreinte `pandera[polars]` : 12 distributions, 188 Mo, polars compris (MBTM). Pour mémoire, GX coûte 267 Mo / 35 distributions (017).

Aucun framework ne connaît les gaps ni la monotonie par flux : ce sont des checks custom dans tous les cas (cf. 017). Lecture : Pandera-polars n'enlève **pas** de code (×2 lignes). Il apporte un contrat déclaratif, une table de failure cases et des types, pour un surcoût d'environ 20 %. → **BENCH_NOW** comme contrat à la frontière C0 file-only, sans autorité (L3 sur de vrais fichiers C0). **GX → PARK**. **Soda Core → REJECT** : ELv2, VERIFIED_FACT (LICENSE).

### K-2 Ledger d'expérience forward : MLflow comme miroir vs table append-only (L2, MBTM)
Le test MLflow 3.16.1 (`mlflow_shadow_ledger.py`) logue trois bras : A quorum=2, B quorum=1 shadow, C single-family shadow. Chaque bras porte `decision_input_sha256`, des métriques et un artefact avec son sha256 en tag.

Empreinte et performance :
- Empreinte : `mlflow` complet = 89 distributions / 630 Mo. `mlflow-skinny` = 43 distributions / 87 Mo, mais **sans sqlalchemy/alembic** : il ne peut pas servir seul de backend DB.
- Le backend Postgres crée **59 tables** dans `public` (runs, metrics, params, tags, `secrets`, `webhooks`, `endpoints`, `mcp_servers`, `trace_*`…).
- Premier connect + migration : 2,35 s (PG) et 9,65 s (sqlite). Trois runs se loguent en 0,4 s (PG).

Ce qui ferait de MLflow un **second magasin de vérité modifiable** (MBTM) :
- un tag est réécrivable (`artifact_sha256` → `TAMPERED` accepté) ;
- une métrique peut être re-loggée : la « dernière » valeur (999) remplace l'originale dans `latest_metrics`, avec l'historique des deux valeurs ;
- un run supprimé passe en `lifecycle_stage=deleted` ;
- seuls les params sont immuables (`MlflowException`) ;
- les artefacts sont dans un répertoire séparé, sans vérification de hash.

L'alternative `ledger_pg_minimal.sql` (51 lignes SQL non vides) est **une table** `xp.run_ledger` avec :
- identité sur `seq` ;
- `decision_input_sha256`, `artifact_uri` + `artifact_sha256` (Parquet), `code_ref` ;
- `recorded_at = clock_timestamp()` ;
- une chaîne `prev_hash/row_hash` sous verrou advisory ;
- des triggers qui refusent UPDATE, DELETE et TRUNCATE.

Résultats MBTM : UPDATE et DELETE sont refusés. 0 rupture de chaîne avant falsification. Après qu'un superuser a désactivé le trigger et modifié une ligne : **1 rupture détectée**. La falsification est détectée mais pas empêchée.

**Réponse à la question clé :** le ledger forward le plus léger sans seconde autorité est **la table append-only dans le Postgres d'autorité + des fichiers Parquet adressés par sha256** → **BENCH_NOW**. MLflow ne peut être, au mieux, qu'un **miroir read-only alimenté depuis cette table** (UI de comparaison), dans un schéma ou une base dédiée → **PARK** tant qu'aucun besoin d'UI n'est exprimé.

Limites du ledger :
- `recorded_at::text` dépend de `TimeZone` : il faut canoniser en UTC avant le hash ;
- un attaquant qui recalcule toute la chaîne n'est pas détecté sans ancrage externe du dernier hash.

### K-3 OpenTelemetry Python SDK 1.45.0 (L1, MBTM, `otel_smoke.py`)
- Empreinte : 4 distributions / 3 Mo ; import 0,29 s.
- Un span parent→enfant (`decision_v1.evaluate` → `pit.snapshot`) est exporté vers la console, avec un compteur `decision.count` et un histogramme `pit.snapshot.lag_ms` lus par `InMemoryMetricReader`.
- Coût : 16 µs par span sans processeur, 43 µs par span avec BatchSpanProcessor en mémoire.

Le vrai coût serait le backend (collecteur, TSDB), qui créerait un second magasin de métriques. → **WATCH**, comme ADAPTER de transport seulement si l'autorité d'observabilité AurumShift le demande.

### K-4 Autres (L0/L1)
- **pg_stat_statements** : smoke MBTM. Le top 3 est capturé (build HNSW 10,2 s, COPY 3,3 s…). C'est l'outil à utiliser *avant* toute infra pour prouver un goulot → **WATCH**, sans doute déjà présent.
- **pgwatch, Prometheus/Grafana** → **PARK** (services).
- **Evidently 0.7.23** → **WATCH** : oracle de drift offline sur Parquet ; le drift n'est pas une fuite.
- **whylogs 1.6.4** (dernière release 2024-12-03) → **PARK**.
- **NannyML 0.13.1** (2025-07) → **PARK**.
- **Aim 3.29.1** (2025-05, store propre) → **PARK**.
- **DVC 3.67.1** → **PARK** (second ledger via git, recouvre Parquet+sha256).
- **OpenLineage 1.53.0 / Marquez** → **PARK** (service + base ; la lignée économique est une autorité AurumShift).
- **dbt + Elementary** → **PARK**.

## 4. LANE L — mémoire / connaissance / outillage agent (Postgres-first, jamais autorité)

### L-1 pgvector 0.8.7 (L2, MBTM, `pgvector_smoke.py`)
- Clone du tag `v0.8.7` (commit f37c13f, 2026-10-01). `make -j4` pour PG16 en **11,1 s**, une fois les en-têtes `postgresql-server-dev-16` installés (environ 30 s d'apt ; sans eux, le build est impossible).
- `CREATE EXTENSION vector` passe sur 16.15.
- 50 000 vecteurs gaussiens de dimension 128 : COPY 3,3 s ; HNSW (m=16, ef_construction=64) 10,2 s ; 68,8 Mo table + index.
- recall@10 vs scan exact : 0,46 à `ef_search=40` (1,2 ms/requête), 0,82 à `ef_search=200` (3,5 ms/requête). Le plan utilise bien HNSW.

Le gaussien aléatoire est le pire cas pour un ANN : ce n'est pas un indicateur de qualité de retrieval (INFERENCE). Aucun gap du chemin critique → **PARK**. Si une mémoire agent devient nécessaire, ce sera pgvector dans un schéma séparé, explicitement non autoritaire.

### L-2 Fiches L0
- **pgvectorscale** (licence PostgreSQL, VERIFIED_FACT ; tag 0.9.1 ; build pgrx non tenté) → **PARK**.
- **VectorChord** → **REJECT** : double licence AGPLv3 / ELv2, VERIFIED_FACT (LICENSE).
- **ParadeDB pg_search** → **PARK** : Community en AGPL-3.0 (VERIFIED_FACT, README) ; Enterprise commerciale, UNKNOWN_PRICE ; le FTS natif suffit (INFERENCE).
- **Apache AGE** (Apache-2.0) → **PARK**.
- **Mem0 2.2.1** : pgvector est supporté (VERIFIED_FACT, https://docs.mem0.ai/components/vectordbs/dbs/pgvector). La mémoire est extraite et réécrite par LLM (INFERENCE, non vérifié ici), donc non déterministe et jamais une autorité → **PARK**.
- **Letta 0.34.4** (serveur) → **PARK**.
- **Graphiti 0.30.2** → **REJECT** : backends Neo4j, FalkorDB, Kuzu ou Neptune, **pas de Postgres** ; ingestion par LLM (VERIFIED_FACT, README).
- **LightRAG 1.5.7 / Cognee 1.6.2** → **PARK**.
- **Serena** : SolidLSP sous MIT, application sous GPL-3.0-or-later (VERIFIED_FACT, LICENSE), tag v1.7.0. Avec **tree-sitter, la repo map d'aider et zoekt** : outillage opérateur hors chemin critique → **WATCH**.

## 5. Commandes clés exécutées (extraits)
```
uv venv -p 3.11 venvs/laneBJKL && uv pip install polars duckdb pandas pyarrow pandera psycopg[binary] opentelemetry-sdk adbc-driver-postgresql
python pit_asof_bench.py {1000000,5000000} 200000 2000 0.001   -> res_pit_asof_*.json
python dq_c0_bench.py 1000000                                    -> res_dq_c0_1M.json (MAXRSS 737 Mo, 3 variantes)
apt-get update && apt-get install postgresql-server-dev-16       -> apt_exit=0 (PG16 16.14→16.15)
git clone --depth 1 -b v0.8.7 https://github.com/pgvector/pgvector && make -j4  -> build 11,1 s
initdb/pg_ctl (port 55433, /tmp/laneBJKL_pg) ; pgvector_smoke.py ; ledger_pg_minimal.sql ; mlflow_shadow_ledger.py (sqlite, PG) ; pg_transfer_bench.py ; pg_ctl stop ; rm -rf
```

## 6. UNKNOWN restants
- Comportement réel des fichiers C0_V2 : distributions de `ingested_at - event_time`, révisions effectives par venue et horloges biaisées. La timeline-ASOF et Pandera n'ont été testés que sur données synthétiques.
- Existence d'un goulot de rejeu ou d'export dans AurumShift : non mesurée, d'où ADBC, pg_parquet et pg_duckdb en WATCH ou PARK.
- XTDB v2 : comportement sous course de commit ; maturité de la v2.2.
- pg_parquet et pgvectorscale : non compilés (pgrx).
- Effets juridiques de l'AGPL (ParadeDB, VectorChord), de l'ELv2 (Soda) et de la TSL (Timescale) pour AurumShift : non évalués.
- Mem0 : le mécanisme de réécriture par LLM n'a pas été vérifié en code.
