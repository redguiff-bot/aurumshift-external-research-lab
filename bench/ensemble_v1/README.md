# bench/ensemble_v1 — sleeping-experts ensemble study (report 014)

Synthetic, numpy-only. See `PREREGISTRATION.md` (frozen before tuning/held-out) and `reports/014_strategy_ensemble/`.

```
py/scenarios.py   generator: 12 CORE + 1 stress scenarios, 5-state semantics (NOT_EXIST/INACTIVE/ABSTAIN/GAP/OBS)
py/learners.py    20 rows: Equal, Static, WTA, EWMA, HedgePlain, SleepHedge, SleepEG, FixedShare, Disc*, bounded, BMA, Ctx*, Div*, bandits
py/registry.py    methods + tuning grids
py/runner.py      simulation loop + metrics ('correct' vs 'naive_zero' semantics)
py/test_semantics.py  simplex / freeze-on-missing / no-look-ahead tests
py/tune.py tune2.py   tuning seeds 0-5 (round 1 + one grid-extension round)
py/heldout.py     seeds 1000-1039 + stress 2000-2019 + naive_zero reruns (22,880 runs)
py/analyze.py analyze_amended.py sensitivity.py label_noise.py starvation_extra.py
results/          tuned_params.json, heldout_runs.jsonl.gz, gates*.json, tables.md, sensitivity.csv, label_noise.csv, ...
```
Run order: `test_semantics.py → tune.py → tune2.py → heldout.py → analyze.py → analyze_amended.py → sensitivity.py → label_noise.py → starvation_extra.py`.
