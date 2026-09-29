# 05 — Results

Definitions: **gross** = price P&L of the portfolio (before any cost or funding). **net** = gross − trading cost (generic per-side bps, see 08) − funding paid/received (real settled funding). Sharpe annualised on hourly P&L; t = Newey–West (lags = max(2H,24)). FULL = 2023-01→2026-08 (3.66y), DEV = 2023–24, TEST = 2025-01→2026-08. Only **primary specs** (pre-declared sign, mode, H) enter adjudication. BH_q = Benjamini–Hochberg q over the 15 primary one-sided net tests.

## Primary specs — Sharpe gross vs net
| primitive | mode | H | gross_S_DEV | gross_S_TEST | gross_S_FULL | gross_t | net_S_DEV | net_S_TEST | net_S_FULL | net_t | BH_q |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P01_TSMOM | TS | 24 | +0.72 | -0.38 | +0.20 | +0.41 | +0.24 | -0.83 | -0.27 | -0.57 | +1.00 |
| P02_XS_RS7D | CS | 24 | +0.84 | +0.33 | +0.63 | +1.26 | +0.20 | -0.65 | -0.13 | -0.26 | +1.00 |
| P03_REV4H | TS | 4 | +1.01 | -0.93 | +0.09 | +0.20 | -2.80 | -4.47 | -3.58 | -7.84 | +1.00 |
| P04_VOLCOMP_BRK | TS | 24 | +0.40 | +0.68 | +0.55 | +1.08 | -0.26 | +0.19 | -0.00 | -0.00 | +1.00 |
| P05_BRK_PERSIST | TS | 24 | +0.95 | -0.03 | +0.47 | +0.98 | +0.32 | -0.58 | -0.11 | -0.23 | +1.00 |
| P06_FUND_CARRY | CS | 24 | +0.86 | -0.20 | +0.45 | +0.83 | +0.87 | -0.76 | +0.24 | +0.44 | +1.00 |
| P07_PREMIUM | TS | 4 | -0.62 | +0.39 | -0.24 | -0.50 | -1.91 | -2.51 | -2.10 | -4.41 | +1.00 |
| P08_OI_PRICE | TS | 24 | +1.37 | -0.17 | +0.71 | +1.60 | +0.34 | -1.32 | -0.37 | -0.84 | +1.00 |
| P09_OI_FLUSH | TS | 4 | +0.89 | -0.40 | +0.28 | +0.73 | +0.01 | -1.13 | -0.53 | -1.40 | +1.00 |
| P10_TAKER_IMB | TS | 4 | -0.85 | +0.60 | -0.20 | -0.44 | -4.50 | -3.42 | -4.02 | -8.50 | +1.00 |
| P11_LIQ_SHOCK | TS | 4 | -0.13 | -0.81 | -0.42 | -0.93 | -2.13 | -3.10 | -2.53 | -5.54 | +1.00 |
| P12_LEADLAG_BTC | CS | 4 | -1.86 | +0.56 | -0.92 | -1.77 | -15.34 | -17.57 | -16.02 | -31.11 | +1.00 |
| P13_SEASON_HOD | TS | 4 | +1.80 | -0.80 | +0.61 | +1.18 | -2.68 | -4.73 | -3.62 | -6.99 | +1.00 |
| P14_VRP_DVOL | TS | 24 | -0.55 | +1.08 | +0.21 | +0.40 | -0.69 | +0.97 | +0.09 | +0.17 | +1.00 |
| P15_FUND_DIV | CS | 24 | -0.51 | +1.26 | +0.22 | +0.40 | -1.51 | -0.59 | -1.13 | -2.10 | +1.00 |

## Primary specs — economics (annualised %, gross exposure ≤ 1)
`turn_day` = gross notional traded per day / gross exposure. `cs_ic` = mean cross-sectional Spearman IC of the signal vs forward H-return (sampled every H rows) and its t-stat.
| primitive | gross_ann_pct | net_ann_pct | cost_ann_pct | fund_ann_pct | turn_day | cs_ic | cs_ic_t |
|---|---|---|---|---|---|---|---|
| P01_TSMOM | +7.59 | -10.46 | +16.54 | +1.50 | +0.60 | -0.01 | -0.83 |
| P02_XS_RS7D | +13.05 | -2.66 | +16.33 | -0.62 | +0.59 | -0.01 | -1.31 |
| P03_REV4H | +3.02 | -116.24 | +119.94 | -0.68 | +4.32 | +0.03 | +8.03 |
| P04_VOLCOMP_BRK | +1.45 | -0.01 | +1.36 | +0.09 | +0.05 | +0.02 | +0.84 |
| P05_BRK_PERSIST | +18.17 | -4.33 | +20.72 | +1.79 | +0.75 | -0.01 | -0.87 |
| P06_FUND_CARRY | +7.80 | +4.14 | +9.24 | -5.58 | +0.33 | +0.04 | +4.02 |
| P07_PREMIUM | -8.86 | -78.29 | +73.57 | -4.14 | +2.65 | +0.01 | +3.02 |
| P08_OI_PRICE | +13.16 | -6.95 | +19.15 | +0.96 | +0.69 | -0.02 | -2.35 |
| P09_OI_FLUSH | +2.28 | -4.38 | +6.69 | -0.03 | +0.24 | +0.03 | +2.66 |
| P10_TAKER_IMB | -6.52 | -128.72 | +123.60 | -1.40 | +4.48 | -0.01 | -1.43 |
| P11_LIQ_SHOCK | -4.51 | -27.48 | +23.08 | -0.10 | +0.83 | +0.00 | +0.57 |
| P12_LEADLAG_BTC | -14.75 | -254.06 | +239.38 | -0.07 | +8.44 | +0.03 | +6.65 |
| P13_SEASON_HOD | +20.38 | -121.11 | +140.26 | +1.23 | +5.05 | +0.02 | +5.04 |
| P14_VRP_DVOL | +1.62 | +0.66 | +0.85 | +0.10 | +0.04 | +0.02 | +0.88 |
| P15_FUND_DIV | +3.52 | -18.39 | +21.66 | +0.25 | +0.78 | +0.02 | +2.13 |

## Reading the table
- **Nothing net-significant**: best net Sharpe +0.24 (P06, t 0.44) and +0.09 (P14). Net t-stats between −4.4 and −31 for P03, P07, P10, P11, P12, P13 (and −2.1 for P15) mean these are cost-dominated with confidence, not just unproven.
- **Gross edge is weak and unstable across halves**: primary gross Sharpe is positive in DEV for 9/15 and in TEST for 7/15, positive in both for only P02 and P04 (≈0.3–0.8, not significant). Trend/breakout/OI-confirmation (P01, P05, P06, P08, P13) fall from +0.7…+1.8 (DEV) to −0.03…−0.8 (TEST). Several primitives (P07, P10, P12, P14, P15) show the *opposite* of their pre-declared sign in DEV and positive gross in TEST — consistent with noise.
- **Statistical IC ≠ tradable edge**: rank ICs are highly significant for P03 (+0.032, t 8.0), P12 (+0.027, t 6.6), P13 (+0.020, t 5.0), P06 (+0.037, t 4.0), P07 (t 3.0), yet their magnitude-weighted gross P&L is ≈0 or negative. Rank IC weights all 10 assets equally, while P&L is dominated by large moves that do not follow the small-move pattern. The effects are 1–4h in size and are consumed by 6–10 bps per side at 4–8 turns/day.
- **Carry (P06)**: only primitive whose net stays ≥0 (funding received +5.6%/yr offsets part of the cost) but the gross edge is not significant (t 0.83) and TEST net Sharpe is −0.76.
- Full-sample pipeline calibration: placebo signals (150 random, EWMA-24h-smoothed, same pipeline, H=24 TS): gross-t sd 0.94, p95 1.58, p99 2.05; net-t p95 -1.62 (random signals lose money net, as expected). No primary gross t (max 1.60, P08) exceeds the placebo p95 by a meaningful margin.

## Non-primary specs (exploratory only, 45 extra tests, uncorrected)
The other mode/horizon of every primitive was also run. Top gross t-stats (breakeven_x = cost multiple at which net = 0, funding netted):
| spec | gross_t | gross_S_DEV | gross_S_TEST | gross_ann_pct | cost_ann_pct | fund_ann_pct | breakeven_x | net_S | turn_day |
|---|---|---|---|---|---|---|---|---|---|
| P13_SEASON_HOD|CS|H4 | +5.30 | +3.87 | +1.19 | +42.82 | +232.99 | -0.13 | +0.18 | -12.44 | +8.39 |
| P05_BRK_PERSIST|CS|H4 | +4.44 | +3.85 | -0.05 | +45.63 | +107.15 | +0.89 | +0.42 | -3.09 | +3.85 |
| P01_TSMOM|CS|H4 | +3.18 | +2.94 | -0.28 | +38.46 | +79.16 | +0.65 | +0.48 | -1.76 | +2.84 |
| P08_OI_PRICE|TS|H4 | +2.82 | +1.66 | +1.02 | +32.28 | +65.18 | +1.10 | +0.48 | -1.45 | +2.36 |
| P05_BRK_PERSIST|CS|H24 | +2.36 | +2.39 | -0.43 | +21.06 | +33.40 | +0.24 | +0.62 | -0.75 | +1.20 |
| P02_XS_RS7D|CS|H4 | +2.26 | +1.51 | +0.64 | +25.16 | +40.70 | -0.36 | +0.63 | -0.70 | +1.46 |
| P04_VOLCOMP_BRK|TS|H4 | +2.00 | +0.60 | +1.61 | +5.11 | +7.68 | +0.12 | +0.65 | -0.59 | +0.27 |
| P10_TAKER_IMB|CS|H4 | +1.78 | +1.49 | +0.05 | +13.83 | +224.16 | +0.54 | +0.06 | -13.98 | +8.05 |
| P01_TSMOM|CS|H24 | +1.73 | +1.57 | -0.17 | +18.10 | +31.07 | -0.05 | +0.58 | -0.63 | +1.12 |
| P07_PREMIUM|CS|H4 | +1.64 | +0.50 | +1.29 | +13.83 | +166.51 | -4.51 | +0.11 | -8.62 | +5.98 |
| P08_OI_PRICE|TS|H24 | +1.60 | +1.37 | -0.17 | +13.16 | +19.15 | +0.96 | +0.64 | -0.37 | +0.69 |
| P08_OI_PRICE|CS|H4 | +1.57 | +0.74 | +0.97 | +15.17 | +133.78 | +0.33 | +0.11 | -6.41 | +4.83 |

These are the only places with strong gross statistics, all cross-sectional or 4h; all have break-even multiples ≤0.65× the assumed costs and most decay in TEST (P05|CS|H4 3.85→−0.05, P01|CS|H4 2.94→−0.28). Follow-up in 09.

## Secondary horizon/mode for every primitive
| spec (non-primary) | gross_S | gross_t | net_S | net_t | turn_day |
|---|---|---|---|---|---|
| P01_TSMOM|TS|H4 | -0.01 | -0.03 | -0.98 | -1.93 | +1.39 |
| P01_TSMOM|CS|H4 | +1.64 | +3.18 | -1.76 | -3.35 | +2.84 |
| P01_TSMOM|CS|H24 | +0.88 | +1.73 | -0.63 | -1.22 | +1.12 |
| P02_XS_RS7D|TS|H4 | +0.68 | +1.39 | +0.21 | +0.43 | +0.70 |
| P02_XS_RS7D|CS|H4 | +1.16 | +2.26 | -0.70 | -1.36 | +1.46 |
| P02_XS_RS7D|TS|H24 | +0.50 | +1.06 | +0.27 | +0.57 | +0.30 |
| P03_REV4H|CS|H4 | -0.97 | -1.90 | -13.34 | -26.64 | +8.47 |
| P03_REV4H|TS|H24 | +0.10 | +0.21 | -1.13 | -2.43 | +0.72 |
| P03_REV4H|CS|H24 | -1.57 | -3.23 | -5.62 | -11.57 | +1.40 |
| P04_VOLCOMP_BRK|TS|H4 | +1.11 | +2.00 | -0.59 | -1.09 | +0.27 |
| P04_VOLCOMP_BRK|CS|H4 | +0.38 | +0.73 | -7.07 | -13.20 | +1.31 |
| P04_VOLCOMP_BRK|CS|H24 | +0.13 | +0.24 | -2.83 | -5.10 | +0.23 |
| P05_BRK_PERSIST|TS|H4 | +0.65 | +1.29 | -0.56 | -1.11 | +1.82 |
| P05_BRK_PERSIST|CS|H4 | +2.27 | +4.44 | -3.09 | -5.92 | +3.85 |
| P05_BRK_PERSIST|CS|H24 | +1.26 | +2.36 | -0.75 | -1.40 | +1.20 |
| P06_FUND_CARRY|TS|H4 | -0.44 | -0.87 | -0.38 | -0.75 | +0.17 |
| P06_FUND_CARRY|CS|H4 | +0.51 | +0.95 | +0.12 | +0.22 | +0.46 |
| P06_FUND_CARRY|TS|H24 | -0.43 | -0.86 | -0.35 | -0.71 | +0.14 |
| P07_PREMIUM|CS|H4 | +0.80 | +1.64 | -8.62 | -17.58 | +5.98 |
| P07_PREMIUM|TS|H24 | -0.26 | -0.57 | -0.62 | -1.37 | +0.55 |
| P07_PREMIUM|CS|H24 | +0.76 | +1.46 | -1.62 | -3.12 | +1.19 |
| P08_OI_PRICE|TS|H4 | +1.38 | +2.82 | -1.45 | -2.97 | +2.36 |
| P08_OI_PRICE|CS|H4 | +0.82 | +1.57 | -6.41 | -12.22 | +4.83 |
| P08_OI_PRICE|CS|H24 | +0.05 | +0.11 | -2.55 | -5.17 | +1.33 |
| P09_OI_FLUSH|CS|H4 | +0.40 | +0.82 | -4.75 | -9.55 | +1.24 |
| P09_OI_FLUSH|TS|H24 | +0.65 | +1.50 | +0.31 | +0.72 | +0.05 |
| P09_OI_FLUSH|CS|H24 | -1.10 | -2.35 | -3.28 | -6.82 | +0.22 |
| P10_TAKER_IMB|CS|H4 | +0.92 | +1.78 | -13.98 | -26.73 | +8.05 |
| P10_TAKER_IMB|TS|H24 | -0.47 | -1.05 | -1.26 | -2.82 | +0.75 |
| P10_TAKER_IMB|CS|H24 | +0.23 | +0.42 | -4.17 | -7.66 | +1.35 |
| P11_LIQ_SHOCK|CS|H4 | -0.61 | -1.27 | -8.63 | -17.02 | +2.95 |
| P11_LIQ_SHOCK|TS|H24 | +0.00 | +0.01 | -0.89 | -2.18 | +0.14 |
| P11_LIQ_SHOCK|CS|H24 | -0.05 | -0.10 | -3.47 | -7.30 | +0.50 |
| P12_LEADLAG_BTC|TS|H4 | +0.24 | +0.50 | -5.00 | -10.57 | +3.85 |
| P12_LEADLAG_BTC|TS|H24 | +0.31 | +0.64 | -1.79 | -3.67 | +0.63 |
| P12_LEADLAG_BTC|CS|H24 | -1.54 | -3.10 | -7.07 | -14.21 | +1.39 |
| P13_SEASON_HOD|CS|H4 | +2.80 | +5.30 | -12.44 | -23.49 | +8.39 |
| P13_SEASON_HOD|TS|H24 | +0.45 | +0.93 | +0.33 | +0.68 | +0.11 |
| P13_SEASON_HOD|CS|H24 | -0.05 | -0.09 | -0.39 | -0.73 | +0.25 |
| P14_VRP_DVOL|TS|H4 | +0.02 | +0.04 | -0.20 | -0.38 | +0.07 |
| P15_FUND_DIV|TS|H4 | +0.56 | +1.11 | +0.02 | +0.05 | +0.51 |
| P15_FUND_DIV|CS|H4 | +0.64 | +1.18 | -1.45 | -2.69 | +1.31 |
| P15_FUND_DIV|TS|H24 | +0.52 | +1.06 | +0.14 | +0.29 | +0.33 |

