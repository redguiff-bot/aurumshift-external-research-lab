# 04 — Expériences de requête PIT

## Scénarios S1–S12 (`results/scenarios.json`) — PROVEN
25/25 vérifications, verdict `LOOKAHEAD_PREVENTED` (axe STRICT). Slots : S8 = [AVAILABLE, NEVER_OBSERVED, AVAILABLE] ; S8b = [AVAILABLE, NOT_YET_KNOWN_AT_T, AVAILABLE].

## Contrôles fuyants (falsification de méthodes naïves)
| Contrôle | Résultat |
|---|---|
| C1 filtre sur `event_time` | LOOKAHEAD_DETECTED |
| C2 `first_observed_at` brut | LOOKAHEAD_DETECTED |
| C3 axe collecteur validé | PREVENTED sur la batterie (S3b/S3c plafonnés LAG_CAP) — non prouvé au-delà de la batterie |
| C4 ordre d'arrivée pur | WRONG_RESULT_NO_LEAK |
| C5 SCD1 | LOOKAHEAD_DETECTED |
| C6 coalesce vers `event_time` | LOOKAHEAD_DETECTED |

## Course de commit (`results/race.json`) — PROVEN
| Régime | Décision | Rejeu | Verdict |
|---|---|---|---|
| NONE | [b] | [a,b] | DETECTED |
| LOCK_W (écrivains seuls) | [] | [a] | DETECTED |
| LOCK_RW (exclusif écrivains + partagé lecteur) | [a] | [a] | PREVENTED |

## Jointures alternatives (`results/joins.json`)
- Feast défaut (`event_timestamp <= entity_timestamp`, commit f0bc0700, `postgres.py`) : DETECTED (10 fuites) — OBSERVED dans le code.
- Feast `filter_by_created_timestamp=True` : WRONG (S4b, ordre d'arrivée, pas de révision).
- DuckDB `ASOF JOIN` sur `event_time` : DETECTED ; sur `ingested_at` : WRONG (S4b) ; égalités non déterministes.
- Polars `join_asof`, pandas `merge_asof` sur `event_time` : DETECTED.
- DuckDB range-join + `QUALIFY row_number`, Polars filtre+`group_by.first` : identiques à la référence.

## Échelle offline (`results/fleet_offline.json`) — OBSERVED
1 102 621 lignes, T = percentile 60 de `ingested_at`, 630 740 faits : `pit.asof` 0,62 s ; Polars 0,18 s (identique) ; DuckDB 0,56 s (identique). Le temps exclut le chargement.
