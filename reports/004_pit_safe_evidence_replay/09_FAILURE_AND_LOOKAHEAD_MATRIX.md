# 09 — Matrice des échecs et lookahead

| Approche | Backfill | Révision tardive | Course de commit | Verdict |
|---|---|---|---|---|
| Référence PG STRICT, sans verrou | OK | OK | **DETECTED** | LOOKAHEAD_DETECTED |
| Référence PG STRICT + verrou W seul | OK | OK | **DETECTED** | LOOKAHEAD_DETECTED |
| Référence PG STRICT + verrou W/R | OK | OK | OK | LOOKAHEAD_PREVENTED |
| Axe collecteur validé | conditionnel | OK | non couvert | PREVENTED sur batterie seulement |
| `event_time` seul (C1) | fuit | fuit | — | DETECTED |
| `first_observed_at` brut (C2) | fuit | — | — | DETECTED |
| SCD1 (C5) | fuit | fuit | — | DETECTED |
| coalesce `event_time` (C6) | fuit | — | — | DETECTED |
| ordre d'arrivée pur (C4) | — | faux (sans fuite) | — | WRONG |
| Feast défaut | fuit | pas de révision | — | DETECTED |
| Feast `filter_by_created_timestamp` | — | WRONG | — | WRONG |
| DuckDB/Polars/pandas as-of sur event_time | fuit | — | — | DETECTED |
| DuckDB range+QUALIFY / Polars first | OK | OK | dépend de la source | = référence |
| nearform/temporal_tables | OK | pas de révision | **DETECTED** | LOOKAHEAD_DETECTED |
| pg_bitemporal | fuite possible (asserted appelant) | UPDATE | non testé | non exécuté |
| WITHOUT OVERLAPS sur SCD2 mutable | fuit | — | — | DETECTED |
