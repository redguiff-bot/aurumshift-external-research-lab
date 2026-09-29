# 04 — Backtest engines and transaction-cost models

Raw evidence: `results/t03*, t04*, t12b*, t15*`. Data: 600 seeded synthetic daily bars (gap between close and next open present).

## T03 — fixed order schedule reconciliation
BUY 100 with decision at bar 100, SELL 100 at bar 200, fee 10 bp per side, slippage 5 bp adverse. Analytic PnL: **1793.77** if filled at the decision bar's close; **1802.22** if filled at the next bar's open; **1796.46** if filled at next-bar close (zipline bars use the same prices).

| Engine | Fill convention (default) | PnL | vs analytic |
|---|---|---|---|
| vectorbt (`price=Close`) | whatever `price` you pass; same-bar close by default | 1793.77 | exact (1e-9) |
| vectorbt (`price=Open`, orders shifted +1) | next open | 1802.22 | exact |
| backtrader | next-bar open (broker default) | 1802.22 | exact (fees and 5 bp slippage) |
| zipline-reloaded | next-bar **close** (daily) | 1796.46 | exact (fills 94.034 / 112.205, commission 20.62) |
| backtesting.py `trade_on_close=False` | next open | 1807.82 | **+5.6**: entry exact (93.7334), exit price 112.017 = raw open — the `spread` was not applied to the closing fill |
| backtesting.py `trade_on_close=True` | same-bar close | 1799.36 | +5.6 (same cause on exit) |
| bt | close of the decision bar; **no slippage parameter**; weight-based sizing bought 99, not 100 (fee reserve) | 1786.01 | not comparable (99 sh) vs fee-only analytic 1804.05 |
OBSERVED. Interpretation limited to this configuration; the backtesting.py exit behaviour may depend on how the closing order is produced (`position.close()`), not proven for other paths.

## T04 — engine causality (equity on data[:400] equals equity of the full run restricted to [:400])
SMA 10/30 crossover, fee 10 bp. vectorbt (own signals and `vbt.MA`), backtesting.py, backtrader, bt: **max abs difference 0.0, 0 differing bars**. Leaky controls (signal uses close 5 bars ahead) are detected: vectorbt 5 differing bars (max 2 491), bt 4 (max 609). OBSERVED. Test power note: a one-bar leak (`shift(-1)`) initially differed on only the final bar, so a 5-bar leak was used. Not run: nautilus/zipline (event-driven, no full-frame signals).

## Cost models
* **zipline VolumeShareSlippage (T12b)** — 500-share order, `volume_limit=0.025`, `price_impact=0.1`: fills spread over 8 bars with quantities and prices equal to the hand formula `close·(1+0.1·(filled/volume)²)` to 1.4e-14, once the close is rounded to 3 decimals. The 3-decimal rounding is what the default csvdir/bundle storage does (the 4.5e-4 residual vanishes only with that rounding) — OBSERVED; consequence: **sub-0.001 prices (many crypto pairs) would be quantised** (INFERENCE, not tested).
* **nautilus** — commission from the instrument's maker/taker fees (`MakerTakerFeeModel`: 0.2000 on a 2 000 notional at the sampled fill), `FillModel`, `LatencyModel`, book-walking on L2 (T12c). OBSERVED.
* **hftbacktest** — value/quantity/flat fee models with maker rebate, four queue models, constant/interpolated latency. Fee arithmetic verified in T12a.
* **Almgren–Chriss (wraquant.execution.almgren_chriss, T15)** — λ=0 gives the exact linear schedule; λ>0 trajectories equal the continuous-time sinh formula κ=√(λσ²/η) to 0.0 (ignores γ, no discretisation correction); front-loading grows with λ (first-trade 524 → 4 687 of 10 000 for λ 1e-3 → 1). The library provides **no impact-coefficient calibration**; the function is ten lines and the package needs Python ≥3.13 plus an undeclared `polars` dependency. OBSERVED.
* MACE (Gymnasium cost-model environments) and Quantopian-era slippage classes are the other OSS cost-model sources found; not executed.

## Gap statement
No executed project offers *empirical* cost calibration (spread/impact estimated from fills or quotes). What exists are **parametric models with user-supplied coefficients**. Realistic-cost claims therefore still depend on data the OSS libraries do not create.
