# 03 — Forward-safety classification

Classes: `FORWARD_SAFE` (computable from data available at decision time with no source-side stamping subtlety) · `FORWARD_SAFE_WITH_RECEIPT_STAMP` (safe only if the feed is captured live with its own receipt timestamp; archives/reconstructions are not evidence of availability) · `OFFLINE_ONLY` (no point-in-time history exists publicly; usable only for offline study) · `LOOKAHEAD_RISK` (uses centered filters, revised/future values or future-normalised features; banned).

Counts — executed: FORWARD_SAFE 9, FORWARD_SAFE_WITH_RECEIPT_STAMP 6, OFFLINE_ONLY 0, LOOKAHEAD_RISK 0. Catalogue-wide: FORWARD_SAFE 21, WITH_RECEIPT_STAMP 12, OFFLINE_ONLY 3, LOOKAHEAD_RISK 7.

## Mechanical evidence (OBSERVED)
Truncation audit (05 §5.5): weights recomputed on data cut at 5 timestamps equal the full-data weights before the cut for **all 15** primitives. This detects centered/future-normalised code paths in the signal logic. It cannot detect (a) vendor-side revision, (b) late arrival of data in production, (c) archive-vs-live timestamp semantics — hence the receipt-stamp class.

## Specific stamping assumptions made
* **Klines/taker volume:** usable when the bar has closed (decision after bar *i*, earns bar *i+1*).
* **Funding (Binance):** settled rate stamped `calc_time`; the feature becomes usable after the bar containing the settlement closes (≤1h late, conservative). Funding cash flows are attributed to the bar containing the settlement, paid on the position held *entering* that bar.
* **Open interest (Binance Vision metrics, 5m):** snapshot stamped `create_time` assumed available 5 minutes later (semantics not documented → conservative). Archive files are published after the day; **live use needs REST/WS capture with receipt stamps** (`FORWARD_SAFE_WITH_RECEIPT_STAMP`).
* **Deribit DVOL:** hourly candle used 1h after its start. The venue could recompute the index; receipt stamps needed.
* **Spot–perp basis (P08):** two markets aligned on the same bar; live version needs both feeds stamped.
* **Regime labels (07):** trailing percentiles, lagged one bar.
* **Not used:** revised macro values, centered filters, smoothed HMM states, full-sample normalisation, vendor-restated on-chain series (all listed as LOOKAHEAD_RISK candidates).
* **Survivorship (not lookahead but a bias):** the 10-asset universe was chosen ex post as liquid, long-lived contracts.

## Table
| id | primitive | class | truncation audit | lookahead note |
|---|---|---|---|---|
| P01_TSMOM | Vol-normalised 72h time-series momentum | FORWARD_SAFE | PASS (max diff 0e+00) | None: trailing windows only (truncation audit PASS) |
| P02_XS_RS | Cross-sectional 168h relative strength | FORWARD_SAFE | PASS (max diff 0e+00) | None (audit PASS); universe selection is ex-post (survivorship bias, not lookahead in signal) |
| P03_REV_4H | Short-horizon reversal (4h z-score) | FORWARD_SAFE | PASS (max diff 0e+00) | None (audit PASS) |
| P04_DONCHIAN | Donchian 48h breakout / 24h exit (state machine) | FORWARD_SAFE | PASS (max diff 0e+00) | Extremes use shift(1): no current-bar leak (audit PASS) |
| P05_VOL_SQUEEZE_BREAK | Vol compression then directional expansion | FORWARD_SAFE | PASS (max diff 0e+00) | Rolling percentile uses past window only (audit PASS) |
| P06_FUND_XS | Cross-sectional funding crowding fade | FORWARD_SAFE_WITH_RECEIPT_STAMP | PASS (max diff 0e+00) | Settlement rate is known only at calc_time: feature lags one bar; archive != live stamped capture |
| P07_BASIS_CARRY | Funding-threshold delta-neutral carry (long spot / short perp) | FORWARD_SAFE_WITH_RECEIPT_STAMP | PASS (max diff 0e+00) | Threshold selected on DEV only; holdout untouched (audit PASS) |
| P08_SPOT_PERP_BASIS | Spot-perp basis z-score (time-series) | FORWARD_SAFE_WITH_RECEIPT_STAMP | PASS (max diff 0e+00) | Two feeds: requires receipt stamps to guarantee both bars were available at decision (audit PASS on aligned archive) |
| P09_OI_PRICE | OI-confirmed trend / OI-unwind fade | FORWARD_SAFE_WITH_RECEIPT_STAMP | PASS (max diff 0e+00) | Conservative +5min availability shift; audit PASS |
| P10_LIQ_FLUSH_PROXY | OI-flush contrarian (liquidation-pressure proxy) | FORWARD_SAFE_WITH_RECEIPT_STAMP | PASS (max diff 0e+00) | Audit PASS; direct liquidation feed is forward-collect only |
| P11_TAKER_FLOW | Taker-buy imbalance continuation | FORWARD_SAFE | PASS (max diff 0e+00) | Bar-close fields only (audit PASS) |
| P12_ILLIQ_SHOCK | Amihud-type liquidity shock fade | FORWARD_SAFE | PASS (max diff 0e+00) | Audit PASS |
| P13_BTC_LEADLAG | BTC->alt 2h catch-up | FORWARD_SAFE | PASS (max diff 0e+00) | Audit PASS |
| P14_HOUR_SEASON | Hour-of-day seasonality (expanding, walk-forward) | FORWARD_SAFE | PASS (max diff 0e+00) | Expanding estimate excludes current obs; boundary check passes |
| P15_RV_IV_VRP | DVOL minus realised vol (BTC/ETH only) | FORWARD_SAFE_WITH_RECEIPT_STAMP | PASS (max diff 0e+00) | DVOL index may be recomputed by venue; stamp needed |
| D01 | Intraday first-half-hour -> last-half-hour momentum | FORWARD_SAFE | not run | None if session fixed a priori |
| D02 | Quarter-hour order-imbalance effect | FORWARD_SAFE | not run | Trade timestamps only |
| D03 | Flow-conditioned short-horizon reversal | FORWARD_SAFE | not run | None |
| D04 | Liquidation-cascade early-warning signals | LOOKAHEAD_RISK | not run | Event windows selected ex post -> LOOKAHEAD_RISK if used for calibration |
| D05 | Direct liquidation-print imbalance (forceOrder / OKX liquidation-orders) | FORWARD_SAFE_WITH_RECEIPT_STAMP | not run | Receipt-stamped live capture is safe; retro reconstructions are not |
| D06 | Options IV term-structure slope (1w vs 3m) | OFFLINE_ONLY | not run | Reconstructing from EOD/reprocessed data is OFFLINE_ONLY |
| D07 | 25-delta risk reversal / skew | OFFLINE_ONLY | not run | OFFLINE_ONLY |
| D08 | Dealer gamma exposure (GEX) | OFFLINE_ONLY | not run | OFFLINE_ONLY |
| D09 | Dated-futures annualised basis (quarterlies) | FORWARD_SAFE | not run | None |
| D10 | Premium-index-implied next funding forecast | FORWARD_SAFE | not run | None |
| D11 | Top-trader long/short ratio contrarian | FORWARD_SAFE_WITH_RECEIPT_STAMP | not run | Vision 5m stamp semantics |
| D12 | Coinbase-Binance spot premium | FORWARD_SAFE_WITH_RECEIPT_STAMP | not run | None |
| D13 | Cross-venue funding spread (HL vs Binance) | FORWARD_SAFE_WITH_RECEIPT_STAMP | not run | Stamps |
| D14 | Volatility-managed sizing (inverse realised vol) | FORWARD_SAFE | not run | Trailing only |
| D15 | HAR realised-variance forecast / jump & semi-variance | FORWARD_SAFE | not run | Refit must be expanding; in-sample fit is LOOKAHEAD_RISK |
| D16 | Efficiency-ratio / ADX gated trend | FORWARD_SAFE | not run | None |
| D17 | HMM / Markov-switching regimes (smoothed) | LOOKAHEAD_RISK | not run | Smoothed = LOOKAHEAD_RISK; filtered = FORWARD_SAFE |
| D18 | Centered MA / HP filter / wavelet / Savitzky-Golay denoising | LOOKAHEAD_RISK | not run | Centered filter = LOOKAHEAD_RISK (banned by mission) |
| D19 | Full-sample z-score / quantile transform / PCA | LOOKAHEAD_RISK | not run | Future-normalised = LOOKAHEAD_RISK (banned) |
| D20 | Macro surprise (actual-consensus) with revised history | LOOKAHEAD_RISK | not run | Revised values = LOOKAHEAD_RISK; first-release vintage with receipt stamp = FORWARD_SAFE_WITH_RECEIPT_STAMP |
| D21 | Scheduled-event vol drift (FOMC/CPI timestamps) | FORWARD_SAFE_WITH_RECEIPT_STAMP | not run | Schedule is known ahead: safe if calendar captured before event |
| D22 | Overnight/weekend & day-of-week effects | FORWARD_SAFE | not run | Expanding only |
| D23 | Order-book imbalance / microprice / depth | FORWARD_SAFE_WITH_RECEIPT_STAMP | not run | Live-only capture |
| D24 | VPIN / flow toxicity | FORWARD_SAFE | not run | Trailing |
| D25 | Cross-sectional idiosyncratic-vol / low-risk anomaly | FORWARD_SAFE | not run | Trailing |
| D26 | Stablecoin supply / exchange netflow / on-chain | LOOKAHEAD_RISK | not run | Restated = LOOKAHEAD_RISK |
| D27 | Social/search sentiment | LOOKAHEAD_RISK | not run | Revision risk |
| D28 | Perp/spot volume dominance ratio | FORWARD_SAFE | not run | None |

