# 08 — Cost sensitivity

Cost model: per-side bps of traded notional = taker fee 5 bp + slippage (BTC/ETH 1, others 3) → 6/8 bp; carry spot leg +5 bp; UNKNOWN venue/asset = 15 bp; funding is paid/received explicitly per settlement. "Maker-only" is *not* assumed: fill probability/adverse selection is unknown, and UNKNOWN_COST ≠ ZERO_COST (the 0–2 bp columns are shown as upper bounds, not scenarios).

## 8.1 Net Sharpe vs cost multiplier (full sample)
| primitive | net Sharpe @0× (=gross) | 0.5× | 1× (base) | 1.5× | 2× | 3× | all-UNKNOWN 15 bp | funding excluded (wrong for perps; shows funding weight) | gross/cost ratio |
|---|---|---|---|---|---|---|---|---|---|
| P01_TSMOM | -0.06 | -0.34 | -0.61 | -0.89 | -1.16 | -1.70 | -0.61 | -0.57 | -0.11 |
| P02_XS_RS | 0.16 | -0.22 | -0.60 | -0.99 | -1.37 | -2.13 | -0.60 | -0.59 | 0.21 |
| P03_REV_4H | 0.38 | -0.96 | -2.33 | -3.71 | -5.12 | -7.97 | -2.33 | -2.35 | 0.14 |
| P04_DONCHIAN | 0.17 | -0.01 | -0.19 | -0.37 | -0.54 | -0.90 | -0.19 | -0.14 | 0.48 |
| P05_VOL_SQUEEZE_BREAK | 0.66 | 0.38 | 0.10 | -0.17 | -0.45 | -1.00 | 0.10 | 0.12 | 1.19 |
| P06_FUND_XS | 0.72 | -0.04 | -0.80 | -1.56 | -2.31 | -3.82 | -0.80 | -0.98 | 0.47 |
| P07_BASIS_CARRY | 3.10 | 1.97 | 0.64 | -0.39 | -1.06 | -1.80 | 0.64 | -2.78 | 1.29 |
| P08_SPOT_PERP_BASIS | -0.39 | -0.92 | -1.45 | -1.98 | -2.51 | -3.57 | -1.45 | -1.53 | -0.37 |
| P09_OI_PRICE | 0.52 | -0.17 | -0.86 | -1.54 | -2.23 | -3.60 | -0.86 | -0.82 | 0.38 |
| P10_LIQ_FLUSH_PROXY | -0.31 | -0.52 | -0.74 | -0.95 | -1.16 | -1.57 | -0.74 | -0.74 | -0.72 |
| P11_TAKER_FLOW | 0.61 | -1.24 | -3.08 | -4.91 | -6.72 | -10.30 | -3.08 | -3.06 | 0.17 |
| P12_ILLIQ_SHOCK | 0.45 | -0.09 | -0.63 | -1.17 | -1.71 | -2.75 | -0.63 | -0.63 | 0.42 |
| P13_BTC_LEADLAG | -0.09 | -2.96 | -5.81 | -8.65 | -11.45 | -16.86 | -5.81 | -5.81 | -0.02 |
| P14_HOUR_SEASON | 0.85 | -5.41 | -11.58 | -17.60 | -23.42 | -34.21 | -11.58 | -11.58 | 0.07 |
| P15_RV_IV_VRP | -0.02 | -0.08 | -0.13 | -0.18 | -0.23 | -0.34 | -0.13 | -0.12 | -0.23 |

## 8.2 Net annual return vs uniform per-side cost
| primitive | 0 bp/side | 2 bp/side | 5 bp/side | 8 bp/side | 12 bp/side | 20 bp/side | 30 bp/side |
|---|---|---|---|---|---|---|---|
| P01_TSMOM | -2.6% | -8.9% | -18.3% | -27.8% | -40.3% | -65.4% | -96.8% |
| P02_XS_RS | 3.2% | -0.8% | -6.7% | -12.6% | -20.5% | -36.2% | -55.9% |
| P03_REV_4H | 11.5% | -9.5% | -41.1% | -72.6% | -114.7% | -198.8% | -304.0% |
| P04_DONCHIAN | 8.3% | 3.7% | -3.2% | -10.1% | -19.3% | -37.7% | -60.7% |
| P05_VOL_SQUEEZE_BREAK | 5.4% | 4.2% | 2.4% | 0.6% | -1.8% | -6.6% | -12.6% |
| P06_FUND_XS | 11.9% | 5.3% | -4.6% | -14.4% | -27.6% | -53.9% | -86.8% |
| P07_BASIS_CARRY | 1.2% | 0.9% | 0.6% | 0.3% | -0.2% | -1.0% | -2.1% |
| P08_SPOT_PERP_BASIS | -8.7% | -14.9% | -24.2% | -33.4% | -45.7% | -70.4% | -101.2% |
| P09_OI_PRICE | 13.0% | 4.0% | -9.6% | -23.2% | -41.3% | -77.5% | -122.7% |
| P10_LIQ_FLUSH_PROXY | -2.7% | -3.8% | -5.3% | -6.8% | -8.9% | -12.9% | -18.0% |
| P11_TAKER_FLOW | 11.8% | -7.0% | -35.2% | -63.4% | -101.0% | -176.2% | -270.2% |
| P12_ILLIQ_SHOCK | 0.8% | 0.3% | -0.5% | -1.3% | -2.4% | -4.5% | -7.2% |
| P13_BTC_LEADLAG | -2.0% | -32.6% | -78.5% | -124.5% | -185.7% | -308.2% | -461.4% |
| P14_HOUR_SEASON | 22.6% | -65.6% | -197.9% | -330.2% | -506.6% | -859.4% | -1300.5% |
| P15_RV_IV_VRP | -1.1% | -2.6% | -4.9% | -7.2% | -10.3% | -16.5% | -24.2% |

## 8.3 HOLDOUT net Sharpe at 1× and 2×
| primitive | HOLDOUT net Sharpe 1× | HOLDOUT net Sharpe 2× |
|---|---|---|
| P01_TSMOM | -1.94 | -2.50 |
| P02_XS_RS | -0.52 | -1.58 |
| P03_REV_4H | -2.84 | -5.77 |
| P04_DONCHIAN | -0.20 | -0.60 |
| P05_VOL_SQUEEZE_BREAK | -0.27 | -0.95 |
| P06_FUND_XS | -0.62 | -2.63 |
| P07_BASIS_CARRY | flat/NA | flat/NA |
| P08_SPOT_PERP_BASIS | -1.10 | -2.60 |
| P09_OI_PRICE | -1.54 | -3.17 |
| P10_LIQ_FLUSH_PROXY | -1.28 | -1.63 |
| P11_TAKER_FLOW | -2.67 | -6.41 |
| P12_ILLIQ_SHOCK | -0.65 | -1.74 |
| P13_BTC_LEADLAG | -6.14 | -12.87 |
| P14_HOUR_SEASON | -11.91 | -25.11 |
| P15_RV_IV_VRP | 1.02 | 0.90 |

Take-aways are in 10. Key structural fact: the gross/cost ratio exceeds 1 for exactly two primitives (P05 and P07, see last column); primitives with positive gross Sharpe but high turnover (P03, P11, P14, P09) have break-even costs of 0.5–3 bp/side, far below one taker fee. P05 loses its net edge at 1.5× cost; P07's net edge is ~0.3%/yr of capital.
