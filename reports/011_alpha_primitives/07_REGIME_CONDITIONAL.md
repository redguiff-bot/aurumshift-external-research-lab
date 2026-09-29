# 07 — Regime-conditional behaviour

Regimes are past-only (03): volatility = BTC 168h realised-vol percentile vs trailing 365d (LOW <⅓, HIGH >⅔); trend = sign of BTC 30d return. Labels at row t are applied to bar t+1's P&L. Primary specs.

## Net t-stats by regime
| primitive | LOWVOL | MIDVOL | HIGHVOL | UPTREND | DOWNTREND |
|---|---|---|---|---|---|
| P01_TSMOM | +1.32 | -0.18 | -1.48 | +0.37 | -1.20 |
| P02_XS_RS7D | -0.72 | +0.86 | -0.63 | +0.75 | -1.62 |
| P03_REV4H | -6.30 | -5.01 | -2.73 | -5.99 | -4.82 |
| P04_VOLCOMP_BRK | +0.79 | +0.21 | -1.08 | -0.27 | +0.25 |
| P05_BRK_PERSIST | +0.70 | +0.67 | -1.39 | -0.07 | -0.27 |
| P06_FUND_CARRY | +0.58 | -0.41 | +0.62 | -0.69 | +1.86 |
| P07_PREMIUM | -2.52 | -3.27 | -2.05 | -4.41 | -1.47 |
| P08_OI_PRICE | -0.89 | -1.02 | +0.24 | -0.38 | -0.81 |
| P09_OI_FLUSH | -2.37 | -1.62 | +0.43 | -0.64 | -1.42 |
| P10_TAKER_IMB | -5.04 | -2.80 | -6.42 | -6.83 | -5.02 |
| P11_LIQ_SHOCK | -4.56 | -2.93 | -2.30 | -4.69 | -2.97 |
| P12_LEADLAG_BTC | -21.14 | -18.18 | -15.74 | -21.97 | -23.29 |
| P13_SEASON_HOD | -5.92 | -3.85 | -3.27 | -3.54 | -6.56 |
| P14_VRP_DVOL | +0.99 | +0.37 | -0.77 | +1.05 | -0.96 |
| P15_FUND_DIV | -1.50 | -0.12 | -1.94 | -1.25 | -1.90 |

## Net Sharpe by regime
| primitive | LOWVOL | MIDVOL | HIGHVOL | UPTREND | DOWNTREND |
|---|---|---|---|---|---|
| P01_TSMOM | +1.15 | -0.18 | -1.21 | +0.25 | -0.85 |
| P02_XS_RS7D | -0.63 | +0.78 | -0.53 | +0.51 | -1.19 |
| P03_REV4H | -5.49 | -4.51 | -1.98 | -3.77 | -3.39 |
| P04_VOLCOMP_BRK | +0.73 | +0.22 | -0.73 | -0.18 | +0.18 |
| P05_BRK_PERSIST | +0.63 | +0.67 | -1.14 | -0.05 | -0.19 |
| P06_FUND_CARRY | +0.59 | -0.40 | +0.53 | -0.49 | +1.52 |
| P07_PREMIUM | -2.27 | -2.90 | -1.62 | -2.74 | -1.11 |
| P08_OI_PRICE | -0.79 | -0.84 | +0.17 | -0.23 | -0.56 |
| P09_OI_FLUSH | -1.93 | -1.14 | +0.29 | -0.41 | -0.67 |
| P10_TAKER_IMB | -4.63 | -2.61 | -4.89 | -4.19 | -3.78 |
| P11_LIQ_SHOCK | -4.29 | -2.83 | -1.54 | -2.97 | -2.14 |
| P12_LEADLAG_BTC | -20.02 | -14.97 | -14.21 | -15.14 | -17.90 |
| P13_SEASON_HOD | -5.10 | -3.60 | -2.93 | -2.38 | -5.24 |
| P14_VRP_DVOL | +1.02 | +0.36 | -0.63 | +0.75 | -0.78 |
| P15_FUND_DIV | -1.42 | -0.12 | -1.71 | -0.89 | -1.53 |

## Gross Sharpe by regime
| primitive | LOWVOL | MIDVOL | HIGHVOL | UPTREND | DOWNTREND |
|---|---|---|---|---|---|
| P01_TSMOM | +1.71 | +0.36 | -0.81 | +0.80 | -0.47 |
| P02_XS_RS7D | +0.32 | +1.52 | +0.14 | +1.20 | -0.31 |
| P03_REV4H | -0.61 | -0.66 | +1.04 | +0.27 | -0.11 |
| P04_VOLCOMP_BRK | +1.46 | +0.77 | -0.31 | +0.41 | +0.70 |
| P05_BRK_PERSIST | +1.34 | +1.29 | -0.64 | +0.61 | +0.31 |
| P06_FUND_CARRY | +0.92 | -0.23 | +0.68 | -0.35 | +1.86 |
| P07_PREMIUM | +0.59 | -0.88 | -0.27 | -1.17 | +1.23 |
| P08_OI_PRICE | +0.56 | +0.36 | +1.06 | +0.91 | +0.44 |
| P09_OI_FLUSH | -0.65 | -0.36 | +1.06 | +0.56 | -0.01 |
| P10_TAKER_IMB | +0.45 | +1.17 | -1.73 | -0.41 | +0.08 |
| P11_LIQ_SHOCK | -1.02 | -0.67 | +0.06 | -0.45 | -0.39 |
| P12_LEADLAG_BTC | -2.45 | +0.34 | -0.84 | -1.39 | -0.11 |
| P13_SEASON_HOD | +0.49 | +0.85 | +0.53 | +1.92 | -1.10 |
| P14_VRP_DVOL | +1.26 | +0.56 | -0.61 | +0.88 | -0.66 |
| P15_FUND_DIV | +0.16 | +1.29 | -0.57 | +0.34 | +0.01 |

## Low- vs high-vol gross difference (NW-based Welch t on hourly gross P&L)
| primitive | LOWVOL_gross_S | HIGHVOL_gross_S | gross_low_minus_high_t |
|---|---|---|---|
| P01_TSMOM | +1.71 | -0.81 | +1.93 |
| P02_XS_RS7D | +0.32 | +0.14 | +0.09 |
| P03_REV4H | -0.61 | +1.04 | -1.55 |
| P04_VOLCOMP_BRK | +1.46 | -0.31 | +1.45 |
| P05_BRK_PERSIST | +1.34 | -0.64 | +1.52 |
| P06_FUND_CARRY | +0.92 | +0.68 | +0.00 |
| P07_PREMIUM | +0.59 | -0.27 | +0.64 |
| P08_OI_PRICE | +0.56 | +1.06 | -0.80 |
| P09_OI_FLUSH | -0.65 | +1.06 | -1.75 |
| P10_TAKER_IMB | +0.45 | -1.73 | +2.10 |
| P11_LIQ_SHOCK | -1.02 | +0.06 | -0.76 |
| P12_LEADLAG_BTC | -2.45 | -0.84 | -0.88 |
| P13_SEASON_HOD | +0.49 | +0.53 | -0.22 |
| P14_VRP_DVOL | +1.26 | -0.61 | +1.34 |
| P15_FUND_DIV | +0.16 | -0.57 | +0.61 |

## Reading
- **Pre-declared rule (net-based) → 0 regime-dependent candidates.** No primitive has net t ≥ +1.5 in one vol/trend bucket and ≤ −1.5 in the opposite, and none reaches net t ≥ 2.5 in any bucket.
- **Descriptive lean (not counted)**: the trend/breakout cluster and P14 earn positive gross in LOWVOL and negative in HIGHVOL (P01 +1.71/−0.81, P04 +1.46/−0.31, P05 +1.34/−0.64, P14 +1.26/−0.61); P10 similar (+0.45/−1.73). The differences have t ≈ 1.3–2.1 each, i.e. borderline individually and not significant after accounting for the 15 comparisons; they are also collinear (P01/P05/P04 are one bet). The opposite lean (better in HIGHVOL) appears for P03 reversal, P09 OI-flush and P08 (HIGHVOL gross +1.04/+1.06/+1.06), consistent with the stated mechanisms (forced-flow fades and OI confirmation need volatility) but equally weak.
- Costs remain decisive: in every regime the high-turnover primitives stay deeply net negative, so no regime *gate* rescues them.
- This is the only place the design allowed conditional information to matter; the conclusion is "plausible regime lean in the trend cluster, unproven and cost-dominated". A vol-gated trend overlay is a candidate for a future, better-powered study, not a finding here.
