# 03 — OSS components and reference implementations

Method: 21 candidates were shallow-cloned (clones outside this repo) and their **source** inspected (not READMEs); 9 were smoke-executed in isolated virtualenvs; two
(`bidask`, zipline slippage formulas) were then reused or cross-checked in this study's own experiments. GitHub API was unreachable in the sandbox, so release counts,
contributor counts and star counts are **UNKNOWN**; "last commit" comes from the cloned `git log` (OBSERVED) and tags are approximate (`git ls-remote`). Stars were not used.
Full per-candidate records (license, activity, dependencies, asset-class assumptions, required data, online/offline suitability, fit for non-HFT, failure modes, source paths,
smoke result, claim labels) are in `bench/execution_cost_v1/oss_probe/oss_findings.{json,md}` and reproduced in the appendix below.

## 1. Overview

@@oss_table@@

Counts: discovered = 21, source-inspected = 21, smoke-executed = 9 (of which `tick` only partially: simulation ran, `fit` failed on numpy 2.x).
Not executed for stated reasons: `mbt_gym` (install failure), `bmoscon/orderbook` (wrong PyPI package / needs Python ≥ 3.13), ABIDES ×2 (old numpy/pandas pins), LEAN and `freqtrade` (heavy installs; source read only), plus the archived/rejected ones.

## 2. What the study itself executed with OSS

* **`bidask` (EDGE estimator, MIT, Ardia–Guidotti–Kroencke 2024)** run on (a) synthetic OHLC with known spread, (b) Binance Vision 1-minute klines. Result vs the textbook estimators reimplemented here:

  Synthetic (mean over the seed grid, bps; `eff_truth` = realised mean effective spread of the synthetic tape):

@@spread_edge@@

  Real Binance BTCUSDT/ETHUSDT spot 1-min klines (daily EDGE, averaged over days; exchange tick is 0.0012 / 0.037 bps and the trade-flip spread median is exactly 1 tick, see `06`):

@@spread_edge_real@@

  EDGE is the most accurate OHLC estimator in the synthetic grid at moderate/large spreads and is far less inflated by volatility than Corwin–Schultz / high-low proxies (compare `06` table), but it still over-reads spreads that are ≤ 1 tick when volatility is large (0.2 bps true → 0.75–2.5 bps) and reads 0.06–0.18 bps on BTC/ETH where the true quoted spread is ~1 tick (≈ 0.001–0.04 bps). **Verdict: usable as an OHLCV-only spread sanity bound, not as a quote substitute.**
* **zipline-reloaded** `VolumeShareSlippage` / `FixedBasisPointsSlippage`: formula outputs reproduced by the probe (50.002 and 50.025 on the mock order) — PROVEN formulas, but bar-close reference, no spread, no book: equivalent to the *fixed-bps* and *vol-scaled* family that this study finds indistinguishable and size-blind for large orders (`07`).
* **Almgren–Chriss notebook**: trajectory reproduces TWAP as risk aversion → 0 (PROVEN in the probe). Its *linear-cost* form was re-implemented here (`m_sliced_ac`) and mis-ranked schedules in every synthetic cell (`04`).
* **hftbacktest / nautilus_trader / ABIDES / PyLOB**: heavyweight event-driven simulators for HFT; their fill models are Bernoulli or queue-position rules that need L2/L3 event feeds not available from free non-HFT data ⇒ PARK (see adjudication).

## 3. Adjudication summary (details in `13_ADJUDICATION.md`)

* ADOPT_REFERENCE (as oracle/specification, not as runtime dependency): `zipline-reloaded` slippage formulas, QuantConnect LEAN slippage/fill/fee models, `bidask` (EDGE), `ccxt` (fee/funding-rate schema), `freqtrade` funding-fee logic (concept only: GPL-3.0).
* ADAPT_CANDIDATE: Almgren–Chriss notebook (needs a tested module, calibrated η, γ).
* PARK: `hftbacktest`, `nautilus_trader`, `vectorbt`, `mbt_gym`, ABIDES (both), `hummingbot`, `PyLOB`, `vnpy`.
* REJECT: original `zipline`, `backtesting.py` (AGPL), `backtrader` (GPL, unmaintained), `tick`, `bmoscon/orderbook`, `pyfolio/quantstats` for spread estimation (no such estimators found).

## Appendix — per-candidate records (verbatim from the probe)

@@oss_full@@
