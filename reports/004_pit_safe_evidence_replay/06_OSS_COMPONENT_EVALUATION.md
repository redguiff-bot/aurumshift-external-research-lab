# 06 — Évaluation des composants OSS

## PG18 `WITHOUT OVERLAPS` (`results/without_overlaps.txt`) — OBSERVED
Utile comme **invariant sur une table dérivée** (intervalles par `LEAD` sur l'axe append-only). Le motif SCD2 mutable exige un UPDATE de réécriture ; un backfill déclarant un `known` rétroactif sur un instrument neuf passe et fuit ; un ex aequo sur `ingested_at` produit un intervalle vide non signalé.

## nearform/temporal_tables (`results/cand_temporal_tables.json`) — OBSERVED (exécuté)
- T1 backfill invisible (horloge DB) : oui. T2 `sys_period` forgé : accepté mais écrasé par le trigger.
- T3 correction visible correctement dans l'historique (100 → 101).
- T4 pas de notion de révision : la dernière arrivée gagne (rev1 périmée = valeur courante).
- T5 une seule ligne par clé (deux fournisseurs → conflit sans changer le schéma).
- T6 table courante mutable (UPDATE/DELETE possibles par conception).
- T7 course : `now()` = début de transaction ⇒ décision [R2], rejeu [R1,R2] = **LOOKAHEAD_DETECTED**.
- As-of exige `UNION` courante + historique.

## pg_bitemporal — OBSERVED (code lu, non exécuté)
`ll_bitemporal_insert` prend `p_asserted` fourni par l'appelant ; `ll_bitemporal_correction` réécrit `asserted` de l'ancienne ligne (UPDATE). Fuite possible par construction ; non append-only. Extrait : `results/pg_bitemporal_correction_excerpt.sql`.

## Feast — OBSERVED (code)
Pas de révision, PIT par défaut sur `event_timestamp` seul (fuit). Référence d'algorithme, pas drop-in. Le service en plus est un second service.

## DuckDB / Polars — OBSERVED
Moteurs de rejeu offline corrects **si** la forme est range+first ; `ASOF JOIN`/`join_asof` interdits.

## Timescale — OBSERVED partiel
Unicité doit inclure `event_time`. Mêmes résultats d'oracle (0/60), 2 chunks. Coût : insertion 4 700 vs 6 561 lignes/s, latence PIT ~3,8× (6,5 vs 1,7 ms p50). **Compression non testée** : build Apache (`functionality not supported under the current "apache" license`). Tailles table non mesurées (la mesure ne couvrait que le parent, 8 kio = artefact).

## Non exécutés (documentation) : pgMemento, periods, arkhipov/temporal_tables, Hopsworks, eventsourcing, XTDB, Dolt, TerminusDB, lakeFS, Iceberg, Delta — UNKNOWN sur le comportement PIT.
