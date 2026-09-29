# 06 — Orthogonality, redundancy, persistence, turnover

Signals: per-asset z-scores sampled daily, pooled Spearman. P&L: gross daily P&L of each primitive's primary spec (2023-01→2026-08). Incremental information: regress each primitive's gross daily P&L on all 14 others; report the intercept t-stat and R². (Gross is used so that cost drag does not masquerade as "negative alpha".)

## Clusters (average-linkage on 1−|ρ_signal|, cut at |ρ|≈0.3) and effective breadth
- cluster 1: P03_REV4H, P10_TAKER_IMB, P12_LEADLAG_BTC
- cluster 2: P04_VOLCOMP_BRK
- cluster 3: P11_LIQ_SHOCK
- cluster 4: P01_TSMOM, P02_XS_RS7D, P05_BRK_PERSIST
- cluster 5: P07_PREMIUM
- cluster 6: P15_FUND_DIV
- cluster 7: P08_OI_PRICE
- cluster 8: P09_OI_FLUSH
- cluster 9: P06_FUND_CARRY
- cluster 10: P13_SEASON_HOD
- cluster 11: P14_VRP_DVOL

Effective number of independent bets (participation ratio): signals 10.35, gross P&L 9.93 (of 15).

Top |corr| pairs (signal rank / gross daily P&L):
- P01_TSMOM ~ P05_BRK_PERSIST: sig +0.77, pnl +0.83
- P03_REV4H ~ P10_TAKER_IMB: sig -0.56, pnl -0.62
- P01_TSMOM ~ P02_XS_RS7D: sig +0.54, pnl +0.13
- P03_REV4H ~ P12_LEADLAG_BTC: sig +0.40, pnl +0.23
- P03_REV4H ~ P05_BRK_PERSIST: sig -0.39, pnl -0.20
- P01_TSMOM ~ P07_PREMIUM: sig -0.33, pnl -0.49
- P02_XS_RS7D ~ P07_PREMIUM: sig -0.32, pnl -0.06
- P05_BRK_PERSIST ~ P10_TAKER_IMB: sig +0.31, pnl +0.10

Effective number of independent bets ≈10 (signals) / ≈10 (gross P&L) out of 15 — the set is fairly diverse, with two redundant groups: **{P01 TSMOM, P05 breakout-persistence, P02 relative strength}** (P01–P05 signal ρ +0.77, P&L ρ +0.83: the "breakout persistence" baseline is the same trend information as TSMOM) and **{P03 reversal, P10 taker imbalance, P12 lead-lag}** (P03 vs P10 signal ρ −0.56: taker flow over 4h is largely the mirror image of the 4h return, so "flow continuation" and "return reversal" are opposite sides of one variable).

## Signal rank correlation
|  | P01_TSMOM | P02_XS_RS7D | P03_REV4H | P04_VOLCOMP_BRK | P05_BRK_PERSIST | P06_FUND_CARRY | P07_PREMIUM | P08_OI_PRICE | P09_OI_FLUSH | P10_TAKER_IMB | P11_LIQ_SHOCK | P12_LEADLAG_BTC | P13_SEASON_HOD | P14_VRP_DVOL | P15_FUND_DIV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P01_TSMOM | +1.00 | +0.54 | -0.25 | +0.19 | +0.77 | -0.11 | -0.33 | +0.11 | -0.16 | +0.24 | -0.18 | -0.07 | +0.08 | +0.06 | +0.13 |
| P02_XS_RS7D | +0.54 | +1.00 | -0.12 | +0.05 | +0.31 | -0.27 | -0.32 | +0.21 | -0.04 | +0.09 | -0.09 | -0.04 | +0.14 | +0.16 | +0.22 |
| P03_REV4H | -0.25 | -0.12 | +1.00 | -0.23 | -0.39 | +0.03 | +0.06 | -0.00 | +0.21 | -0.56 | +0.24 | +0.40 | -0.04 | -0.02 | -0.03 |
| P04_VOLCOMP_BRK | +0.19 | +0.05 | -0.23 | +1.00 | +0.26 | -0.01 | -0.06 | +0.02 | -0.05 | +0.19 | -0.25 | -0.12 | +0.01 | +0.05 | -0.00 |
| P05_BRK_PERSIST | +0.77 | +0.31 | -0.39 | +0.26 | +1.00 | -0.04 | -0.24 | +0.09 | -0.18 | +0.31 | -0.21 | -0.14 | +0.05 | +0.02 | +0.08 |
| P06_FUND_CARRY | -0.11 | -0.27 | +0.03 | -0.01 | -0.04 | +1.00 | +0.18 | -0.13 | -0.03 | +0.07 | +0.02 | +0.01 | -0.22 | -0.07 | -0.11 |
| P07_PREMIUM | -0.33 | -0.32 | +0.06 | -0.06 | -0.24 | +0.18 | +1.00 | -0.05 | +0.09 | -0.09 | +0.06 | -0.02 | -0.08 | -0.11 | -0.16 |
| P08_OI_PRICE | +0.11 | +0.21 | -0.00 | +0.02 | +0.09 | -0.13 | -0.05 | +1.00 | +0.12 | -0.00 | -0.01 | +0.01 | +0.06 | -0.00 | +0.05 |
| P09_OI_FLUSH | -0.16 | -0.04 | +0.21 | -0.05 | -0.18 | -0.03 | +0.09 | +0.12 | +1.00 | -0.15 | +0.13 | +0.06 | +0.03 | +0.01 | -0.00 |
| P10_TAKER_IMB | +0.24 | +0.09 | -0.56 | +0.19 | +0.31 | +0.07 | -0.09 | -0.00 | -0.15 | +1.00 | -0.18 | -0.23 | -0.04 | +0.04 | +0.01 |
| P11_LIQ_SHOCK | -0.18 | -0.09 | +0.24 | -0.25 | -0.21 | +0.02 | +0.06 | -0.01 | +0.13 | -0.18 | +1.00 | +0.20 | -0.01 | +0.00 | -0.01 |
| P12_LEADLAG_BTC | -0.07 | -0.04 | +0.40 | -0.12 | -0.14 | +0.01 | -0.02 | +0.01 | +0.06 | -0.23 | +0.20 | +1.00 | +0.01 | +0.01 | -0.02 |
| P13_SEASON_HOD | +0.08 | +0.14 | -0.04 | +0.01 | +0.05 | -0.22 | -0.08 | +0.06 | +0.03 | -0.04 | -0.01 | +0.01 | +1.00 | +0.08 | +0.11 |
| P14_VRP_DVOL | +0.06 | +0.16 | -0.02 | +0.05 | +0.02 | -0.07 | -0.11 | -0.00 | +0.01 | +0.04 | +0.00 | +0.01 | +0.08 | +1.00 | +0.01 |
| P15_FUND_DIV | +0.13 | +0.22 | -0.03 | -0.00 | +0.08 | -0.11 | -0.16 | +0.05 | -0.00 | +0.01 | -0.01 | -0.02 | +0.11 | +0.01 | +1.00 |

## Gross daily P&L correlation
|  | P01_TSMOM | P02_XS_RS7D | P03_REV4H | P04_VOLCOMP_BRK | P05_BRK_PERSIST | P06_FUND_CARRY | P07_PREMIUM | P08_OI_PRICE | P09_OI_FLUSH | P10_TAKER_IMB | P11_LIQ_SHOCK | P12_LEADLAG_BTC | P13_SEASON_HOD | P14_VRP_DVOL | P15_FUND_DIV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P01_TSMOM | +1.00 | +0.13 | -0.19 | +0.45 | +0.83 | -0.06 | -0.49 | +0.12 | -0.12 | +0.16 | -0.11 | -0.12 | +0.18 | +0.12 | +0.09 |
| P02_XS_RS7D | +0.13 | +1.00 | +0.01 | +0.07 | +0.09 | -0.08 | -0.06 | +0.16 | +0.04 | -0.05 | -0.04 | -0.14 | +0.11 | -0.04 | +0.08 |
| P03_REV4H | -0.19 | +0.01 | +1.00 | -0.25 | -0.20 | -0.00 | +0.16 | -0.07 | +0.40 | -0.62 | +0.56 | +0.23 | +0.00 | -0.07 | +0.00 |
| P04_VOLCOMP_BRK | +0.45 | +0.07 | -0.25 | +1.00 | +0.56 | -0.01 | -0.18 | +0.15 | -0.06 | +0.18 | -0.22 | -0.11 | -0.04 | -0.05 | +0.06 |
| P05_BRK_PERSIST | +0.83 | +0.09 | -0.20 | +0.56 | +1.00 | -0.03 | -0.38 | +0.14 | -0.19 | +0.10 | -0.15 | -0.12 | +0.08 | +0.01 | +0.08 |
| P06_FUND_CARRY | -0.06 | -0.08 | -0.00 | -0.01 | -0.03 | +1.00 | +0.06 | -0.11 | -0.05 | +0.11 | -0.02 | -0.04 | -0.05 | -0.05 | -0.07 |
| P07_PREMIUM | -0.49 | -0.06 | +0.16 | -0.18 | -0.38 | +0.06 | +1.00 | +0.00 | +0.16 | -0.15 | +0.07 | +0.10 | -0.03 | -0.15 | -0.06 |
| P08_OI_PRICE | +0.12 | +0.16 | -0.07 | +0.15 | +0.14 | -0.11 | +0.00 | +1.00 | +0.05 | -0.28 | -0.05 | -0.09 | +0.19 | +0.08 | -0.03 |
| P09_OI_FLUSH | -0.12 | +0.04 | +0.40 | -0.06 | -0.19 | -0.05 | +0.16 | +0.05 | +1.00 | -0.28 | +0.26 | +0.08 | +0.08 | -0.00 | +0.02 |
| P10_TAKER_IMB | +0.16 | -0.05 | -0.62 | +0.18 | +0.10 | +0.11 | -0.15 | -0.28 | -0.28 | +1.00 | -0.33 | -0.03 | -0.09 | +0.09 | +0.00 |
| P11_LIQ_SHOCK | -0.11 | -0.04 | +0.56 | -0.22 | -0.15 | -0.02 | +0.07 | -0.05 | +0.26 | -0.33 | +1.00 | +0.19 | +0.10 | +0.05 | +0.00 |
| P12_LEADLAG_BTC | -0.12 | -0.14 | +0.23 | -0.11 | -0.12 | -0.04 | +0.10 | -0.09 | +0.08 | -0.03 | +0.19 | +1.00 | -0.08 | -0.02 | +0.06 |
| P13_SEASON_HOD | +0.18 | +0.11 | +0.00 | -0.04 | +0.08 | -0.05 | -0.03 | +0.19 | +0.08 | -0.09 | +0.10 | -0.08 | +1.00 | +0.12 | +0.03 |
| P14_VRP_DVOL | +0.12 | -0.04 | -0.07 | -0.05 | +0.01 | -0.05 | -0.15 | +0.08 | -0.00 | +0.09 | +0.05 | -0.02 | +0.12 | +1.00 | +0.03 |
| P15_FUND_DIV | +0.09 | +0.08 | +0.00 | +0.06 | +0.08 | -0.07 | -0.06 | -0.03 | +0.02 | +0.00 | +0.00 | +0.06 | +0.03 | +0.03 | +1.00 |

## Incremental (conditional) information on gross P&L
| primitive | alpha_t | R2 |
|---|---|---|
| P01_TSMOM | -1.26 | +0.76 |
| P02_XS_RS7D | +0.74 | +0.08 |
| P03_REV4H | +1.12 | +0.61 |
| P04_VOLCOMP_BRK | +0.55 | +0.38 |
| P05_BRK_PERSIST | +1.05 | +0.76 |
| P06_FUND_CARRY | +0.93 | +0.04 |
| P07_PREMIUM | -0.65 | +0.27 |
| P08_OI_PRICE | +1.05 | +0.25 |
| P09_OI_FLUSH | +0.71 | +0.22 |
| P10_TAKER_IMB | +0.45 | +0.53 |
| P11_LIQ_SHOCK | -1.17 | +0.35 |
| P12_LEADLAG_BTC | -1.40 | +0.11 |
| P13_SEASON_HOD | +1.07 | +0.13 |
| P14_VRP_DVOL | +0.52 | +0.09 |
| P15_FUND_DIV | +0.42 | +0.03 |

No primitive has a significant (|t|>2) intercept once the others are controlled, i.e. none contributes significant incremental *gross* P&L. With no supported candidate, "non-redundant candidates" is 0 by the pre-declared rule; the diversity above is a property of the probe set, not evidence of alpha.

## Persistence (signal autocorrelation) and turnover
Persistent signals (P06, P14, P15, P02, P01) support low turnover; fast signals (P03, P10, P12, P11, P09) are dominated by 1–4h decay and their cost drag is structural.
| primitive | acf_lag1h | acf_lag4h | acf_lag24h | acf_lag72h | turn_day |
|---|---|---|---|---|---|
| P01_TSMOM | +0.97 | +0.89 | +0.38 | +0.01 | +0.60 |
| P02_XS_RS7D | +0.99 | +0.97 | +0.84 | +0.54 | +0.59 |
| P03_REV4H | +0.73 | -0.01 | -0.02 | -0.01 | +4.32 |
| P04_VOLCOMP_BRK | +0.23 | +0.07 | +0.01 | -0.01 | +0.05 |
| P05_BRK_PERSIST | +0.94 | +0.81 | +0.24 | -0.06 | +0.75 |
| P06_FUND_CARRY | +1.00 | +1.00 | +0.91 | +0.67 | +0.33 |
| P07_PREMIUM | +0.93 | +0.66 | +0.49 | +0.35 | +2.65 |
| P08_OI_PRICE | +0.84 | +0.63 | +0.10 | +0.05 | +0.69 |
| P09_OI_FLUSH | +0.57 | +0.11 | +0.00 | -0.00 | +0.24 |
| P10_TAKER_IMB | +0.74 | +0.06 | +0.04 | +0.03 | +4.48 |
| P11_LIQ_SHOCK | +0.05 | +0.01 | -0.01 | +0.00 | +0.83 |
| P12_LEADLAG_BTC | +0.48 | -0.02 | +0.01 | +0.01 | +8.44 |
| P13_SEASON_HOD | +0.73 | +0.03 | +0.98 | +0.94 | +5.05 |
| P14_VRP_DVOL | +1.00 | +0.98 | +0.90 | +0.69 | +0.04 |
| P15_FUND_DIV | +1.00 | +0.97 | +0.63 | +0.42 | +0.78 |

P13's lag-24/72h autocorrelation ≈0.95 is mechanical (same-hour averages repeat daily) while its lag-4h is ≈0: its position rotates every few hours → 5 turns/day at H=4.

Turnover implication: at 6–10 bps per side, a primitive needs gross edge ≳ (turn_day × 365 × ~8 bps) per year of exposure; slow primitives (turn_day ≤ 0.35: P04, P06, P09, P14) are the only ones for which this hurdle is below ~10%/yr, but none of them has gross edge distinguishable from zero.
