# 00 — Résumé exécutif (PIT-safe evidence & replay, V1)

Mode : EXTERNAL_RESEARCH_ONLY · aucun code privé AurumShift · aucune intégration. Données **synthétiques** ; instance PostgreSQL 18.6 jetable (`fsync=off`, machine partagée).
Labels : PROVEN (test reproductible + oracle) · OBSERVED (mesuré/lu dans le code) · DOCUMENTED_CLAIM · INFERENCE · UNKNOWN.

## Conclusion
Un **modèle PostgreSQL natif, append-only, à une table d'observations plus un journal de réceptions**, suffit pour la capture PIT-safe et le rejeu déterministe (PROVEN sur synthétique). Aucun candidat OSS testé n'est un drop-in. Le gain OSS réel est **offline** : DuckDB/Polars reproduisent exactement la sémantique de référence, à condition d'utiliser la forme « filtre d'inégalité + première ligne par groupe », jamais `ASOF JOIN`.

## Réponses
- **Q1 modèle minimal** (PROVEN) : `pit.obs` (identité `source, provider_event_id, revision, content_hash`, `event_time`, `finality_status`, `first_observed_at`, `ingested_at` horloge DB, `known_collector_at`, `known_basis`, `payload`) + `pit.obs_receipt` (toutes les réceptions) + triggers append-only. Voir 03.
- **Q2 correction** (PROVEN) : nouvelle ligne (révision supérieure ou contenu différent) ; jamais d'UPDATE. Restatement silencieux (même révision, contenu différent) détecté par vue.
- **Q3 dernière version connue à T** (PROVEN, 25/25 + 0/60 écart d'oracle à 1,1M ×2 axes) : filtre `axe ≤ T`, puis dernière version par fait (`revision DESC NULLS LAST, axe DESC, obs_id DESC`), puis filtre de finalité *après* la sélection.
- **Q4 live/backfill** (PROVEN sur l'axe STRICT ; CONDITIONNEL sur l'axe collecteur) : le backfill reçoit l'horloge DB ; l'axe collecteur ne crédite `first_observed_at` que si LIVE, non nul, ≤ ingestion et dans `max_lag`.
- **Q5 provenance incomplète** (PROVEN) : garde `PIT_PROVENANCE_INCOMPLETE` fail-closed (S8, S8b avant backfill, S9 périmée).
- **Q6 OSS utile** : PostgreSQL 18 (`btree_gist`/`WITHOUT OVERLAPS` sur table dérivée), DuckDB, Polars (rejeu offline). Feast : algorithme de référence seulement. Voir 06, 10.

## Trouvaille majeure (PROVEN)
Course « ordre de commit ≠ ordre de timestamp » : sans verrou, décision `[b]` vs rejeu `[a,b]` = **LOOKAHEAD_DETECTED**. Un verrou côté écrivains seul ne suffit pas (décision `[]`, rejeu `[a]`). Il faut verrou exclusif écrivains **et** verrou partagé lecteur de décision (`pit.decision_cutoff`) → PREVENTED. Voir 04, 09.

## Bloc final
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

Réserves : synthétique ; finalité fournisseur non vérifiée pour OKX/Coinbase ; compression Timescale non testée (build Apache) ; propriétaire/superuser contourne l'append-only. Voir 11.
