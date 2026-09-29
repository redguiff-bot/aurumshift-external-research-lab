# bench/feature_discovery_v1 — symbolic / sparse / causal-boundary feature discovery (external research)

Study: `reports/015_feature_discovery/`. External only: no AurumShift code, no integration, no trading claim, no costs.

```
src/data.py        public Binance-Vision hourly klines fetcher (raw/*.csv.gz + manifest.json with sha256)
src/features.py    20 causal primitives (rolling z-scored) + target y = 4h forward log-return / (sigma24*sqrt(4))
src/pipeline.py    discovery pipeline: library, MI screen, Gaussian-copula CMI, orthogonalisation, stability selection,
                   gplearn symbolic regression + cross-seed clustering, validation gate + BIC-penalised final selection,
                   frozen held-out evaluation, baselines (raw ridge, LassoCV, tree-importance, permutation-importance, GBM)
src/panels.py      real panel (10 markets), null panel (circularly shifted target), known-truth synthetic panel
src/run_batch.py   python run_batch.py {synth|null|real} [procs]
src/analyze.py     -> results/summary.json (validity checks, consensus over seeds, verdict rule)
configs/protocol.json   pre-registration (committed BEFORE any held-out access)
tests/             causality (truncation), isolation (held-out untouched before LOCK), split, null, BH tests
results/{synth,null,real}/run_<seed>.json, lock_<seed>.json (frozen final list + sha256, written BEFORE held-out evaluation)
```
Run: `pip install numpy scipy pandas scikit-learn gplearn pytest`, `python src/data.py <symbols>` (or use committed raw/), `cd src && python run_batch.py synth|null|real`, `python analyze.py`, `pytest -q tests`.
Seeds: discovery 11-15, null 901-908, synthetic 7001-7006 (smoke/dev seeds 1, 3-6 used only for code debugging, never for reporting).
