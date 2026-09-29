# 05 — Features, online statistics, portfolio/risk

Raw evidence: `results/t05*, t06*, t07*`.

## T05 — indicator causality (prefix invariance across every indicator a library exposes)
Value at row t computed on data[:400] must equal the value on 600 rows.
* **ta 0.11.0**: 91 columns from `add_all_ta_features`, 86 causal, **5 not**: `trend_kst`, `trend_kst_sig`, `trend_kst_diff`, `trend_visual_ichimoku_a`, `trend_visual_ichimoku_b`. Differences are confined to the warm-up rows (rows 0–25 for Ichimoku, 14–43 for KST): the leading NaN region is back-filled with the first valid (future) value. Hand Wilder RSI(14) differs from `RSIIndicator` by ≤5.3e-3 (RSI seeding convention). OBSERVED.
* **pandas-ta 0.4.71b0** (AllStudy, 271 columns): 262 causal, **9 not**: `DPO_20` (centered), `ICS_26` (Ichimoku chikou), and seven `TOS_STDEVALL_*` (full-sample regression bands). `AllStudy` ran ~10 s for 600 rows. OBSERVED. The `.ta.strategy` API named in older docs does not exist in this version.
* **vectorbt 1.1.1** indicators MA, MSTD, BBANDS, RSI, STOCH, MACD, ATR, OBV: 0 leaky outputs. OBSERVED.
* **tsfresh 0.21.2** rolled windows (min=max_timeshift=19, minimal parameters): 10/10 causal features, 0.66 s. OBSERVED.
Lesson: an indicator library must be *allow-listed by prefix-invariance test*, not trusted wholesale.

## T06 — river 0.26.1 online statistics (200 000 points at offset 1e9, σ=0.01)
* Mean rel. err 5e-15; variance rel. err 6.9e-6 (naive Σx² formula: 2.6e6 — catastrophic); covariance 2.7e-6. Rolling(100) variance rel. err 3.2e-4 vs exact window variance — **identical to pandas' rolling variance**, so both share the same add/remove precision loss at large offsets (OBSERVED; matters for price-level, not return-level, inputs).
* Pickle snapshot/restore mid-stream gives identical continuation (248-byte state); 2 fresh runs identical.
* 0.56 M updates/s for mean+var+cov in pure Python.
* Drift detectors on a 1.5σ mean shift at t=2000: ADWIN detects at +15 samples with 0 false alarms, PageHinkley +19 (1 false alarm), KSWIN +161 (3 false alarms). Single synthetic scenario — no generality claimed.
* `EWMean` uses `fading_factor`; max diff vs pandas `ewm(adjust=False)` 0.038 at level 1e9 (initialisation transient, ~4e-11 relative). Semantics must be pinned by the caller.

## T07 — portfolio and metrics (6 assets, 1 500 obs, closed-form min-variance on the same sample covariance)
| Library | max weight error (unconstrained min-var) | notes |
|---|---|---|
| PyPortfolioOpt 1.6.0 | 3.4e-10 | **HRPOpt crashes** with current SciPy (`_LINKAGE_METHODS` missing) — compatibility rot, OBSERVED |
| riskfolio-lib 7.3.0 | 3.0e-6 | CVaR min-risk OK; cvxpy dependency |
| skfolio 1.4.9 | 7.6e-5 | HRP OK; solver tolerance |
All deterministic across two runs. Metrics: empyrical-reloaded equals hand-computed Sharpe, Sortino, max drawdown, CAGR, historical VaR/CVaR (≤1e-15); quantstats equals hand for Sharpe/Sortino/drawdown/CAGR but its VaR/CVaR (0.01756/0.02221) are **parametric**, not historical (0.01793/0.02241). OBSERVED.
