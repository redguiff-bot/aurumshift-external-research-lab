# raw_orchestrator — mesures et vérifications faites directement par l'orchestrateur

Horloge sandbox : 2026-10-05 (UTC).

## O1. Connecteur TipRanks (MCP) — `get_economic_calendar` (MEASURED_BY_THIS_MISSION, L2, 1 appel)

Appel : `daysBack=3, daysForward=7, countries="US,Euro Zone,Germany,UK,Japan", impact="High,Medium", limit=60`
(appel fait le 2026-10-05 vers ~11:30 UTC). 50 événements renvoyés (`totalMatched=50`).

Constats :
- Champs : `actual, country, estimate, event, impact, prev, time, unit`. **Aucun identifiant d'événement**, aucune
  date de publication de l'actual, aucune révision. (Confirme LAB_PRIOR 010.)
- `time` sans fuseau ; NFP 2026-10-02 = `12:30:00` et ISM Services = `14:00:00` ⇒ cohérent avec **UTC** pendant l'heure
  d'été US (08:30 / 10:00 ET). INFERENCE (aucun marqueur de fuseau).
- Actuals présents pour les événements passés : ex. US Non Farm Payrolls actual 29.0 K, estimate 90.0, prev 162.0
  (2026-10-02) ; Unemployment 4.2 vs 4.1 ; UK Inflation 3.3.
- Défauts de qualité : `unit` paddé d'espaces (`"          "` pour ISM, `"M         "` pour API Crude) ; positions CFTC
  attribuées au pays de la devise (« Japan » pour JPY) ; filtre « Euro Zone » n'a renvoyé aucun événement de la zone
  euro (aucun ECB/PMI zone euro) ⇒ libellé de pays UNKNOWN ou couverture partielle.
- Avantage : actual + estimate + prev dans un seul appel, sans clé côté laboratoire (connecteur déjà attaché à la
  session de l'opérateur). Risque : conditions d'usage systématique/redistribution UNKNOWN ; données « may be delayed »
  (texte d'instruction du serveur MCP) ⇒ **jamais horodatage PIT** ; usage = oracle de cohérence de valeurs (actual,
  consensus) a posteriori, ou capture forward avec `receipt_time` propre.
- Classification : WATCH (oracle de cohérence actual/consensus), pas source.

## O2. confseq — installation (MEASURED_BY_THIS_MISSION)

- `uv pip install confseq` (0.0.11, sdist) **échoue sur Python 3.11** : erreur de compilation pybind11
  (`invalid use of incomplete type ‘PyFrameObject’`) ; même échec depuis le dépôt git master.
- Sur Python 3.10, le build passe mais l'import échoue avec NumPy 2 (`np.float_` supprimé) ; fonctionne avec
  `numpy<2` (1.26.4). La lane A a produit un patch de 6 lignes pour Py3.11 + NumPy 2 (`bench/laneA/confseq_py311_numpy2.patch`).
- Conséquence : dépendance fragile ⇒ vendoriser la partie « betting » (Python pur) plutôt que dépendre du paquet.

## O3. Bench Q1 — inférence quorum (voir BENCHMARKS.md §Q1 et `bench/quorum_inference/`)

## O4. Vérifications croisées des affirmations critiques des lanes

- OKX checksum déprécié (lane E) : citation du changelog OKX recopiée dans `raw_laneE.md` l.22 + mesure 598/598
  messages à checksum=0. Non re-mesuré par l'orchestrateur.
- hftbacktest plafond 100 ticks (lane CD) : chemin source `hftbacktest/src/backtest/proc/partialfillexchange.rs`
  et commentaire `// todo: set the proper upper bound.` cités ; reproduction numérique exacte (part expirée = part
  d'ordres traversant > 100 ticks). Cohérent ; non re-mesuré.
- Prix Tardis (lane CD) : grille relevée sur la page officielle des prix (VENDOR_CLAIM, prix publiés).
- Rien n'a été relu ligne à ligne dans les 1 500 lignes de notes de lanes : ce sont des notes de travail.
