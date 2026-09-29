# 10 — Adjudication (sans score global)

Cinq rôles séparés : STORAGE AUTHORITY · OBSERVATION PROVENANCE · PIT QUERY · OFFLINE REPLAY ENGINE · PROVIDER FINALITY ADAPTER.

| Rôle | Choix |
|---|---|
| STORAGE AUTHORITY | PostgreSQL natif (schéma de référence) |
| OBSERVATION PROVENANCE | `obs_receipt` + `known_basis` (custom, ~2 tables) |
| PIT QUERY | fonction SQL de référence |
| OFFLINE REPLAY ENGINE | DuckDB ou Polars (forme range+first) |
| PROVIDER FINALITY ADAPTER | à écrire par fournisseur ; UNKNOWN par défaut |

| Candidat | Décision | Motif |
|---|---|---|
| PostgreSQL 18 natif | ADOPT | baseline PROVEN |
| PG18 `WITHOUT OVERLAPS` | ADAPT | invariant sur table dérivée seulement |
| Polars | ADOPT (offline) | identique à la référence, 0,18 s |
| DuckDB | ADAPT | correct uniquement en range+QUALIFY, jamais `ASOF JOIN` |
| pandas | REJECT | `merge_asof` fuit ; aucun avantage |
| TimescaleDB | PARK | mêmes résultats mais 3,8× latence ; compression non testée |
| nearform/temporal_tables | REJECT | course de commit DETECTED, pas de révision, table mutable |
| arkhipov/temporal_tables, periods | PARK | non exécutés, même modèle (horloge de transaction) attendu — INFERENCE |
| pg_bitemporal | REJECT | `asserted` fourni par l'appelant, UPDATE (lecture du code) |
| pgMemento | PARK | audit de mutations, non évalué |
| Feast | PARK | algorithme de référence, pas de révision, second service |
| Hopsworks, Tecton | PARK | second service ; Hopsworks dépôt 404 ; non évalués |
| eventsourcing, XTDB, Dolt, TerminusDB, lakeFS, Iceberg, Delta | PARK | second datastore/service sans preuve de nécessité |
