# 03 — Forward safety

Classes: `FORWARD_SAFE` (only immutable closed-bar public prints ≤ decision time), `FORWARD_SAFE_WITH_RECEIPT_STAMP` (exchange-derived fields — funding, OI snapshots, premium index, DVOL, HL funding — whose real-time availability delay is *not* in the archive; a live version must store its own receipt timestamp), `OFFLINE_ONLY`, `LOOKAHEAD_RISK`.

## Rules enforced
1. Hourly rows are labelled by bar open; row t is treated as known at t+1h. Fills at next open (delay 0); +1/+2 bars tested.
2. Trailing windows only: every rolling statistic ends at t; normalisation by trailing (720h) std — never full-sample. No centered/smoothed filter, no HMM smoothing, no change-point segmentation.
3. Funding uses **settled** values only, stamped at settlement floored to the hour (available at the following decision); predicted funding is excluded. Funding *charged* in P&L is the value settled at the end of the holding bar (accounting only, never a feature).
4. Bulk 5-min OI snapshots get an extra 1-bar receipt lag; DVOL is lagged 1 bar (candle-stamping convention unverified).
5. Macro: no macro primitive executed; if executed later, first-release stamps and ex-ante consensus only (no revised series).
6. Regime labels (BTC 168h RV percentile vs trailing 365d; 30d trend sign) are past-only and applied to the *next* bar's P&L.

## Empirical test (bench/…/py/lookahead_test.py)
For 6 random cut points T, each signal is recomputed on data truncated at T and compared with the full-data value on rows T-300…T (P13 at both horizons). Any difference ⇒ LOOKAHEAD_RISK.
Result: **15/15 PASS (max abs diff 0.0)**. Negative control (signal = next-bar return): FAIL, as required, so the test is not blind. Additionally, a planted-future signal is detected by the simulator with gross Sharpe 26.7 (H=4) while the same signal shifted by 3H gives -0.39, validating return/decision alignment.

## Classification of the executed primitives
| primitive | class | truncation test | specific controls |
|---|---|---|---|
| P01_TSMOM | `FORWARD_SAFE` | PASS | Only closed-bar closes ≤ t; σ trailing. No centered filter. |
| P02_XS_RS7D | `FORWARD_SAFE` | PASS | Universe fixed ex ante (no survivorship filter by future liquidity) — 10 majors alive throughout, so survivorship bias exists (assets chosen with hindsight of being liquid in 2026). |
| P03_REV4H | `FORWARD_SAFE` | PASS | Bar t closed before decision; no partial bar. |
| P04_VOLCOMP_BRK | `FORWARD_SAFE` | PASS | Donchian and compression windows shifted by one bar (exclude current bar); no in-progress-bar squeeze. |
| P05_BRK_PERSIST | `FORWARD_SAFE` | PASS | Window includes bar t (closed) only. |
| P06_FUND_CARRY | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | PASS | Uses settled funding only (never predicted); stamp = calc time floored to hour → visible next decision. Real-time receipt latency not in archive. |
| P07_PREMIUM | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | PASS | Exchange-derived index; archive gives no receipt time; bar closed. |
| P08_OI_PRICE | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | PASS | Extra 1-bar receipt lag applied to compensate unknown publication delay of bulk metrics. |
| P09_OI_FLUSH | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | PASS | OI lagged 1 bar; thresholds fixed ex ante. |
| P10_TAKER_IMB | `FORWARD_SAFE` | PASS | Kline volumes are final at close. |
| P11_LIQ_SHOCK | `FORWARD_SAFE` | PASS | z uses trailing window incl. current closed bar. |
| P12_LEADLAG_BTC | `FORWARD_SAFE` | PASS | β uses returns ≤ t only. |
| P13_SEASON_HOD | `FORWARD_SAFE` | PASS | Trailing 60-day same-hour means only; verified by truncation test. |
| P14_VRP_DVOL | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | PASS | DVOL lagged one bar (candle stamping convention unverified); trailing RV only — forward RV variant excluded (LOOKAHEAD_RISK). |
| P15_FUND_DIV | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | PASS | Both stamps floored to the hour and visible at the next decision; HL time jitter (ms) handled by flooring. |

## Discovered but not executed
| id | primitive | class | note |
|---|---|---|---|
| D16 | Dated-futures term-structure slope (Deribit) | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | not executed: no public point-in-time curve history for expired instruments in bulk |
| D17 | Perp vs dated-future basis | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | not executed: same PIT-curve gap as D16 |
| D18 | Macro event reaction (FOMC/CPI first-print surprise) | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | not executed: needs first-release stamps + ex-ante consensus vintages; using revised prints would be LOOKAHEAD_RISK; 3.7y sample has ~40 FOMC/CPI events (power) |
| D19 | Realized Amihud illiquidity | `FORWARD_SAFE` | not executed: overlaps P11; source S18 not verifiable |
| D20 | Top-trader long/short ratio contrarian | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | not executed: metrics available; deprioritised as redundant with funding/OI family |
| D21 | True liquidation-stream intensity (forceOrder/HL/OKX) | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | not executed: public streams are sampled/partial; no complete history (report 005) |
| D22 | HMM regime gating with smoothed states | `LOOKAHEAD_RISK` | not executed: smoothed/full-sample fit uses the future; filtered-probability variant is FSR |
| D23 | Offline change-point segmentation (ruptures-style) | `OFFLINE_ONLY` | not executed: offline by construction |
| D24 | Centered MA / HP / smoothed Kalman trend | `LOOKAHEAD_RISK` | not executed: centered filter uses future bars |
| D25 | Full-sample z-normalised features | `LOOKAHEAD_RISK` | not executed: future-normalised scale |
| D26 | Quarter-hour order-imbalance effect (Kim & Hansen 2026) | `FORWARD_SAFE` | not executed: needs trade-level tape; too heavy for this pass |
| D27 | CTREND ML trend factor (Fieberg et al. JFQA 2025) | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | not executed: ML, needs walk-forward and >3000-coin universe |
| D28 | First-half-hour → last-half-hour intraday momentum (Shen et al.) | `FORWARD_SAFE` | not executed: session definition ex ante; overlaps P01/P13 at 1h resolution |
| D29 | FX fixing seasonality (Krohn-Mueller-Whelan) | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | not executed: needs FX/gold intraday history and DST-exact stamps |
| D30 | FX/crypto carry (rate differential) | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | not executed: needs point-in-time rates |
| D31 | BTC vs equity/macro lead-lag | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | not executed: needs synchronised equity ticks |
| D32 | VRP with realised forward variance (DVOL − RV_fwd) | `LOOKAHEAD_RISK` | not executed: uses future RV; ex-post analysis only |
| D33 | Predicted (next-period) funding from premium index | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | not executed: predicted-vs-settled definitions differ by venue |
| D34 | Bollinger/Keltner squeeze evaluated on the in-progress bar | `LOOKAHEAD_RISK` | not executed: intrabar lookahead (repainting) |

Counts over all 34: FORWARD_SAFE 12, FORWARD_SAFE_WITH_RECEIPT_STAMP 16, OFFLINE_ONLY 1, LOOKAHEAD_RISK 5.

Residual (non-testable) risks: archive timestamps vs real-time publication; survivorship of the 10-asset universe (see 11); exchange-side retroactive corrections to bulk files (UNKNOWN).
