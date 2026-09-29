# 01 — Exigences et modèle de menace

## Contrats (testés)
1. as-of : un fait est visible à T seulement si `axe ≤ T` ; une révision arrivée après T ne remplace pas la version antérieure.
2. backfill : `BACKFILL_LOOKAHEAD_PREVENTED=TRUE` requis.
3. finalité : PRELIMINARY / FINAL / CORRECTED / UNKNOWN, filtrée après sélection de la dernière version.
4. déterminisme : deux exécutions à T identique → même ensemble d'`obs_id`, y compris après arrivées tardives.
5. append-only ; fail-closed sur provenance incomplète.

## Deux axes de connaissance
- STRICT = `ingested_at` (horloge DB, `strict_clock`) : inattaquable par l'appelant.
- COLLECTEUR = `known_collector_at` : crédit à `first_observed_at` seulement si provenance LIVE, non nulle, ≤ ingestion, dans `max_lag`=60 s. `known_basis` ∈ COLLECTOR_CLOCK, DB_CLOCK_BACKFILL, DB_CLOCK_UNVERIFIED_PROVENANCE, DB_CLOCK_NO_FIRST_OBSERVED, DB_CLOCK_SKEW_CAP, DB_CLOCK_LAG_CAP.

## Menaces (S1–S12 et contrôles fuyants C1–C6)
Filtrer sur `event_time` (C1) · sur `first_observed_at` brut (C2) · axe collecteur sans validation (C3) · ordre d'arrivée pur (C4) · SCD1 écrasant (C5) · `coalesce` vers `event_time` (C6) · doublons de réception · révisions désordonnées · restatement silencieux · deux fournisseurs en désaccord · trous (jamais observé / pas encore connu) · course de commit · dérive d'horloge collecteur · propriétaire malveillant (hors périmètre, cf. 11).
