# 11 — Limitations

- Données synthétiques ; aucun test sur données AurumShift ni sur flux fournisseur réel.
- `fsync=off`, `synchronous_commit=off`, machine partagée : débits indicatifs seulement ; aucune mesure de durabilité.
- Append-only par triggers : contournable par le propriétaire ou un superuser (`ALTER TABLE … DISABLE TRIGGER`). Il faudrait rôles et REVOKE ; non testé.
- Axe collecteur : validé sur la batterie seulement ; dérive d'horloge et stabilité de rejeu dans `max_lag` non testées à l'échelle. L'axe STRICT est la seule garantie PROVEN.
- Verrou advisory global : sérialise les écrivains ; débit sous concurrence non mesuré ; le lecteur de décision doit appeler `decision_cutoff` (discipline applicative).
- Timescale : compression et tailles non mesurées (build Apache) ; unicité contrainte par `event_time`.
- Candidats non exécutés : pg_bitemporal (code lu), pgMemento, periods, arkhipov, Hopsworks, Tecton, event-sourcing, XTDB, Dolt, TerminusDB, lakeFS, Iceberg, Delta.
- Finalité fournisseur : OKX et Coinbase non établies ; Binance documentée seulement.
- Oracle : 60 échantillons par axe à 1,1M ; flotte n=3 ; un seul run.
- Feast : algorithme lu au commit f0bc0700, comportement réimplémenté, non exécuté.
