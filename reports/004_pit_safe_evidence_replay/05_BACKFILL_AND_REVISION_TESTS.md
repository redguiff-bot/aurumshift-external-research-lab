# 05 — Backfill et révisions

- Backfill : un fait d'`event_time` ancien inséré après T est invisible à T sur l'axe STRICT (PROVEN, S3/S8b). Sur l'axe collecteur, `first_observed_at` déclaré par un backfill n'est pas crédité (`DB_CLOCK_BACKFILL`), un LIVE mensonger est plafonné (`SKEW_CAP`, `LAG_CAP`) — validé sur la batterie seulement (limite : dérive d'horloge générale non testée).
- Révisions : une révision arrivée après T ne remplace pas la version antérieure ; révision désordonnée (r1 arrive après r2) : la plus haute révision gagne sur l'axe STRICT tant qu'elle est connue ; r1 seule à T reste r1 (S4, S4b).
- Doublons : dédup par contenu, réceptions journalisées (PROVEN).
- Restatement silencieux (même révision, contenu différent) : deux lignes, signalé par `silent_restatements` (PROVEN) ; le choix entre elles retombe sur `axe DESC, obs_id DESC`, déterministe.
- Test de mutation : UPDATE refusé sur table plain (`pit: table obs is append-only`) et sur chunk hypertable.
