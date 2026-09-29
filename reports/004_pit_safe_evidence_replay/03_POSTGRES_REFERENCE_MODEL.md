# 03 — Modèle de référence PostgreSQL (baseline)

Code : `bench/pit_v1/sql/001_schema.sql`, `002_functions.sql`, `003_race.sql`.

- `pit.obs` : table append-only (triggers `BEFORE UPDATE/DELETE/TRUNCATE` → `deny_mutation()`). Identité unique `(source, provider_event_id, revision, content_hash) NULLS NOT DISTINCT` : la dédup par contenu rend l'ingestion idempotente. CHECK `known_collector_at <= ingested_at`.
- `pit.obs_receipt` : journal de toutes les réceptions (dédoublonnées ou non) → S5 = 1 ligne / 3 réceptions, S10 = 2 lignes / 3 réceptions (PROVEN).
- `pit.ingest` / `ingest_locked` : estampille `ingested_at` par l'horloge DB, calcule l'axe collecteur et `known_basis`.
- Requêtes : `asof(T)` (STRICT), `asof_collector(T)`, `asof_final(T)`, `latest_known`, `slots` (AVAILABLE / NEVER_OBSERVED / NOT_YET_KNOWN_AT_T), `assert_replayable` (fail-closed).
- Vues : `silent_restatements`, `provider_disagreement`.
- Index PIT : `(source, instrument, timeframe, event_time DESC, revision DESC NULLS LAST, axe DESC, obs_id DESC)` ×2 axes.

Ordre de version : `revision DESC NULLS LAST, axe DESC, obs_id DESC`. Filtre de finalité après sélection (sinon une version FINAL périmée réapparaît après correction : testé S7).
Résultat : 25/25 attentes manuelles = SQL = oracle Python (PROVEN, synthétique).
