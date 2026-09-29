# 07 — Expérience d'échelle (indicatif)

Données `gen.py` : 250 instruments × 4 200 barres, seed 42, 2 % doublons, 3 % tardifs, 5 % révisions, 2 % backfill → **1 123 580 réceptions**, 1 102 621 lignes `obs`. Chargement par `pit.ingest`, batches de 5 000, ordre mélangé. Instance jetable, `fsync=off`, machine partagée 32 threads : les débits sont **indicatifs, non représentatifs de la durabilité**.

| | plain | Timescale |
|---|---|---|
| insertion (lignes/s) | 6 561 | 4 700 |
| heap / index obs | 226 Mo / 328 Mo | non mesuré (parent seul) |
| octets/obs total | 502 | — |
| PIT 1 instrument p50/p95 (ms) | 1,7 / 2,45 | 6,5 / 10,9 |
| `latest_known` p50 | 0,14 | 0,23 |
| flotte 250 instruments (ms) | 492 | 781 |
| écarts d'oracle (60 échantillons ×2 axes) | 0 | 0 |
| UPDATE | bloqué | bloqué |

Journal de réceptions : 145 Mo. Limites : 1 seul run par mesure (flotte n=3), pas de concurrence, pas de charge de lecture pendant écriture, oracle échantillonné (60), pas de VACUUM/durabilité.
