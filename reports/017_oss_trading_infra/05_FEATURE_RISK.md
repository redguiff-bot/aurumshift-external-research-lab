# 05 — Feature computation, online statistics, portfolio and risk

Scripts: `py/mt/stats_microtest.py`, `feat_microtest.py`, `port_microtest.py`. Data: synthetic seeded GBM-like 1-minute series (200 000 bars for statistics, 20 000 for indicators), so the oracle is exact numpy/pandas, not a market claim.

## Online statistics (river 0.26.1, tdigest 0.5.2.2, ddsketch 3.0.1, hdrhistogram 0.10.7)
| Test (n = 199 999 log-returns unless stated) | Result |
|---|---|
| river `Mean` / `Var` vs numpy | abs error 8.9e-21 / relative 8.4e-15; 0.72 µs per update (both stats) |
| river `Rolling(Mean, 100)` vs pandas rolling | max abs error 5.6e-19 |
| river `EWMean(fading_factor=0.05)` vs pandas `ewm(alpha=0.05, adjust=False)` | max abs error 1.1e-19 |
| river P² streaming p99 | est 9.217e-4 vs exact 9.227e-4 → relative error 9.8e-4 |
| tdigest p99 (50 k values) | 9.247e-4 vs exact 9.245e-4, but 1.29 s for 50 k updates (pure Python) |
| ddsketch (α = 1 %) p99 of |ret| | relative error **0.99 %** ≤ claimed 1 %; merge of two halves gives the same error |
| hdrhistogram (3 significant digits) p99 | relative error 5.6e-6 |
| river determinism | identical output on repeated runs |
Reading: `river` gives numerically exact O(1) online moments/rolling/EW windows — the direct fit for streaming feature state. The sketches deliver bounded-error quantiles and are mergeable (useful for distributed/partitioned stats). `tdigest` is slow and frozen (last release 2019).

## Feature/indicator libraries (batch vs streaming parity, causality)
| Comparison | Result |
|---|---|
| `ta` EMA vs pandas `ewm(adjust=False)` | max abs 0.0 after 100 bars |
| `talipp` (streaming) EMA vs `ta` | max abs **2.4e-3** over the whole series — talipp seeds the EMA with an SMA, `ta`/pandas start from the first value; vs pandas after 100 bars 7.2e-7 |
| `talipp` RSI14 vs `ta` | 2.8e-6 after 200 bars |
| `talipp` ATR14 vs `ta` | 0.0 after 200 bars |
| `ta` RSI prefix consistency (value at t unchanged when future appended) | 0.0 |
| `TA-Lib` 0.8.1 RSI prefix consistency | 0.0; RSI14 on 20 k bars ≈ 0.17–0.19 ms; wheel installs in ~1 s |
| `pandas-ta` 0.4.71b0 (py3.12 only) without TA-Lib installed | RSI/ATR means equal TA-Lib to 1e-16, prefix consistency 0.0; with TA-Lib installed it **delegates** to TA-Lib (identical values, so that run is not independent) |
Reading: the indicator layer is a solved commodity and causal in the tested cases; the only trap is **warm-up/seed conventions** (`talipp` vs pandas), which must be stated in any batch↔streaming parity contract. `pandas-ta`'s upstream repository is unreachable and its only PyPI builds are pre-releases for Python ≥ 3.12 → provenance risk (REJECT).

## Portfolio and risk libraries (5 assets × 1 000 days, long-only minimum variance; oracle = SLSQP on the sample covariance)
| Library | max abs weight difference vs oracle | Deterministic | Note |
|---|---|---|---|
| PyPortfolioOpt 1.6.0 | **2.6e-9** | yes | isolated-venv import failed: undeclared dependency `packaging` |
| Riskfolio-Lib 7.3.0 | 5.1e-7 | yes | 85 dists / 963 MB alone |
| skfolio 1.4.9 | 3.0e-5 (solver tolerance) | yes | 52 releases in 12 m; sklearn API |
| empyrical-reloaded 0.5.12 | Sharpe Δ 1.0e-15, max-DD Δ 0 vs numpy | — | isolated import failed: undeclared dependency `pytz` |
| quantstats 0.0.86 | Sharpe Δ 0, max-DD Δ 0 vs numpy | — | 349 MB env, report/plot oriented |
| cvxportfolio 1.5.1 | policy + simulator ran, deterministic (2 runs); costs verified in `04` | yes | GPL-3.0, one author |
Three optimisers agree with an independent solver to ≤ 3e-5, so they are mutually usable as cross-check oracles. Nothing tested covers *risk limits as governance* (limit breaches, kill logic) — those are policy code, not library features (INFERENCE).

## What this section supports
* Online stats: `river` (moments/rolling/EW), `hdrhistogram`/`ddsketch` (quantiles) — ADOPT_REFERENCE, drop-in at library level.
* Indicators: `TA-Lib` as parity oracle (ADOPT_REFERENCE); `talipp` as streaming implementation (ADAPT: parity contract needed).
* Portfolio/risk: PyPortfolioOpt/Riskfolio as cross-check oracles; skfolio and cvxportfolio as ADAPT candidates with the flags above.
