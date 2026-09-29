# bench/ensemble_v1 — combinaison en ligne d'experts endormis (synthétique)

```
pip install numpy pandas scipy tabulate river
cd py
python unit_tests.py            # invariances et sémantique
python runner.py tune           # ~7 min, 4 cœurs, graines 100-109, écrit tuning_*.csv et tuned_params.json
python runner.py heldout        # ~1-2 min, graines 1000-1029, écrit heldout_raw.csv.gz et blocks_*.npz
python adjudicate.py            # règles pré-enregistrées (03_PROTOCOL) -> adjudication.json, summary_tables.md
python extras.py                # analyses complémentaires (extras.json)
python oss_probe.py             # river EWARegressor (oss_probe.json)
```
- `py/env.py` scénarios et statuts (ACTIVE / INACTIVE / ABSTAIN / DATA_GAP / NO_EVIDENCE) ; `py/learners.py` combineurs ; `py/runner.py` registre, boucle, métriques.
- `results/buggy_mass_fix/` : résultats du premier run (conservation de masse approchée) — conservés pour traçabilité, non utilisés.
- Rapports : `reports/014_strategy_ensemble/`.
