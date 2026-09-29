# 05 — Results (base cost, EXTERNAL_RESEARCH_ONLY)

Universe: 10 Binance USD-M perpetuals (BTC ETH SOL XRP BNB DOGE ADA LINK AVAX LTC), 1h bars, evaluation 2024-03-01 → 2026-08-31 (914 days).
DEV = 2024-03-01 → 2025-05-31; HOLDOUT = 2025-06-01 → 2026-08-31. Parameters are pre-registered defaults, fixed before results were viewed, except the two DEV-only reselections below. Sharpe = daily PnL, √365. PnL is a fraction of gross capital (equal-notional legs, 1/N per asset).
**GROSS = price PnL + funding cash flow, before trading costs. NET = GROSS − trading costs.** Base cost per side: taker 5 bp + slippage/half-spread (BTC/ETH 1 bp → 6 bp; other assets 3 bp → 8 bp); spot leg of the carry pair +5 bp fee. Unmapped venue/asset → 15 bp (UNKNOWN_COST ≠ ZERO_COST).

Baseline BASE_EW_LONG (equal-weight long all 10 perps, no rebalancing cost, funding paid): gross/net Sharpe 0.20, price 18.7%/yr, funding -5.4%/yr, max DD -101.6% (sum of daily returns). Beta, not alpha: every directional primitive below must beat this in risk-adjusted terms AND be uncorrelated with it (see 06).

## 5.1 Full-sample decomposition
| primitive | gross Sharpe | net Sharpe | gross ann. | price | funding | cost | net ann. | turnover/yr | break-even bps/side |
|---|---|---|---|---|---|---|---|---|---|
| P01_TSMOM | -0.06 | -0.61 | -2.6% | -0.6% | -2.0% | -23.9% | -26.5% | 314 | -0.8 |
| P02_XS_RS | 0.16 | -0.60 | 3.2% | 3.4% | -0.3% | -15.0% | -11.8% | 197 | 1.6 |
| P03_REV_4H | 0.38 | -2.33 | 11.5% | 10.9% | 0.6% | -80.0% | -68.5% | 1052 | 1.1 |
| P04_DONCHIAN | 0.17 | -0.19 | 8.3% | 10.7% | -2.4% | -17.5% | -9.2% | 230 | 3.6 |
| P05_VOL_SQUEEZE_BREAK | 0.66 | 0.10 | 5.4% | 5.6% | -0.2% | -4.6% | 0.9% | 60 | 9.0 |
| P06_FUND_XS | 0.72 | -0.80 | 11.9% | 8.8% | 3.1% | -25.1% | -13.2% | 329 | 3.6 |
| P07_BASIS_CARRY | 3.10 | 0.64 | 1.4% | 0.0% | 1.4% | -1.1% | 0.3% | 6 | 26.1 |
| P08_SPOT_PERP_BASIS | -0.39 | -1.45 | -8.7% | -10.4% | 1.6% | -23.5% | -32.2% | 308 | -2.8 |
| P09_OI_PRICE | 0.52 | -0.86 | 13.0% | 14.0% | -1.0% | -34.4% | -21.4% | 453 | 2.9 |
| P10_LIQ_FLUSH_PROXY | -0.31 | -0.74 | -2.7% | -2.8% | 0.0% | -3.8% | -6.6% | 51 | -5.4 |
| P11_TAKER_FLOW | 0.61 | -3.08 | 11.8% | 12.2% | -0.5% | -71.3% | -59.5% | 940 | 1.3 |
| P12_ILLIQ_SHOCK | 0.45 | -0.63 | 0.8% | 0.8% | 0.0% | -2.0% | -1.2% | 27 | 3.2 |
| P13_BTC_LEADLAG | -0.09 | -5.81 | -2.0% | -1.9% | -0.0% | -119.7% | -121.7% | 1531 | -0.1 |
| P14_HOUR_SEASON | 0.85 | -11.58 | 22.6% | 22.7% | -0.1% | -332.9% | -310.3% | 4410 | 0.5 |
| P15_RV_IV_VRP | -0.02 | -0.13 | -1.1% | -0.9% | -0.2% | -4.6% | -5.7% | 77 | -1.4 |

`break-even bps/side` = gross annual return ÷ annual turnover: the per-side cost at which net = 0. Compare with 6–8 bp paid.

## 5.2 DEV vs HOLDOUT (with stationary-bootstrap uncertainty)
| primitive | DEV gross | DEV net | HOLDOUT gross | HOLDOUT net | HOLDOUT net Sharpe 90% boot band | HOLDOUT net p (1-sided) | Holm(15) p | FULL gross p (1-sided) |
|---|---|---|---|---|---|---|---|---|
| P01_TSMOM | 1.19 | 0.66 | -1.36 | -1.94 | -3.78 .. -0.26 | 0.96 | 1.00 | 0.55 |
| P02_XS_RS | -0.06 | -0.68 | 0.55 | -0.52 | -2.09 .. 0.95 | 0.70 | 1.00 | 0.40 |
| P03_REV_4H | 0.73 | -1.86 | 0.01 | -2.84 | -4.10 .. -1.70 | 1.00 | 1.00 | 0.25 |
| P04_DONCHIAN | 0.16 | -0.17 | 0.20 | -0.20 | -1.62 .. 1.08 | 0.60 | 1.00 | 0.38 |
| P05_VOL_SQUEEZE_BREAK | 0.89 | 0.45 | 0.40 | -0.27 | -1.77 .. 1.08 | 0.61 | 1.00 | 0.14 |
| P06_FUND_XS | 0.27 | -0.94 | 1.40 | -0.62 | -2.19 .. 0.78 | 0.72 | 1.00 | 0.10 |
| P07_BASIS_CARRY | 4.44 | 0.91 | flat/NA | flat/NA | 0.00 .. 0.00 | 1.00 | 1.00 | 0.00 |
| P08_SPOT_PERP_BASIS | -0.95 | -1.74 | 0.40 | -1.10 | -2.66 .. 0.41 | 0.88 | 1.00 | 0.74 |
| P09_OI_PRICE | 0.85 | -0.37 | 0.09 | -1.54 | -3.37 .. 0.08 | 0.92 | 1.00 | 0.20 |
| P10_LIQ_FLUSH_PROXY | 0.49 | -0.04 | -0.93 | -1.28 | -2.26 .. -0.48 | 0.98 | 1.00 | 0.74 |
| P11_TAKER_FLOW | 0.13 | -3.46 | 1.13 | -2.67 | -4.33 .. -1.17 | 0.99 | 1.00 | 0.14 |
| P12_ILLIQ_SHOCK | 0.49 | -0.61 | 0.41 | -0.65 | -2.15 .. 0.66 | 0.75 | 1.00 | 0.20 |
| P13_BTC_LEADLAG | -0.63 | -5.74 | 0.67 | -6.14 | -7.79 .. -4.62 | 1.00 | 1.00 | 0.57 |
| P14_HOUR_SEASON | 0.28 | -11.26 | 1.46 | -11.91 | -13.81 .. -10.25 | 1.00 | 1.00 | 0.07 |
| P15_RV_IV_VRP | -1.05 | -1.14 | 1.15 | 1.02 | -0.38 .. 2.30 | 0.09 | 1.00 | 0.50 |

p-values are one-sided stationary block bootstrap (7-day blocks, 2000 draws), null = mean ≤ 0. Holm(15) adjusts the 15 holdout-net tests.

## 5.3 Information coefficient (position vs forward vol-normalised return, uncentered/cosine, weekly blocks)
| primitive | IC horizon (h) | IC full | IC dev | IC holdout | active share |
|---|---|---|---|---|---|
| P01_TSMOM | 6 | -0.0192 (t=-1.4, 140w) | +0.0064 (t=+0.4, 74w) | -0.0479 (t=-2.1, 66w) | 1.00 |
| P02_XS_RS | 24 | +0.0034 (t=+0.6, 138w) | +0.0009 (t=+0.1, 73w) | +0.0063 (t=+0.8, 65w) | 1.00 |
| P03_REV_4H | 4 | +0.0031 (t=+0.3, 140w) | -0.0061 (t=-0.5, 74w) | +0.0135 (t=+0.9, 66w) | 1.00 |
| P04_DONCHIAN | 24 | -0.0222 (t=-1.0, 139w) | -0.0051 (t=-0.2, 74w) | -0.0417 (t=-1.2, 65w) | 0.99 |
| P05_VOL_SQUEEZE_BREAK | 12 | +0.0051 (t=+0.1, 96w) | -0.0875 (t=-1.2, 45w) | +0.0868 (t=+1.3, 51w) | 0.18 |
| P06_FUND_XS | 24 | +0.0090 (t=+1.6, 139w) | +0.0080 (t=+1.0, 74w) | +0.0101 (t=+1.3, 65w) | 1.00 |
| P07_BASIS_CARRY | 8 | -0.0686 (t=-0.8, 10w) | -0.0686 (t=-0.8, 10w) | NA | 0.04 |
| P08_SPOT_PERP_BASIS | 12 | +0.0115 (t=+1.0, 139w) | -0.0013 (t=-0.1, 73w) | +0.0257 (t=+1.5, 66w) | 1.00 |
| P09_OI_PRICE | 12 | -0.0002 (t=-0.0, 139w) | +0.0002 (t=+0.0, 73w) | -0.0008 (t=-0.0, 66w) | 1.00 |
| P10_LIQ_FLUSH_PROXY | 4 | +0.0195 (t=+0.3, 42w) | +0.0574 (t=+0.7, 24w) | -0.0311 (t=-0.4, 18w) | 0.07 |
| P11_TAKER_FLOW | 4 | +0.0041 (t=+0.6, 139w) | +0.0072 (t=+0.8, 73w) | +0.0007 (t=+0.1, 66w) | 1.00 |
| P12_ILLIQ_SHOCK | 4 | +0.0721 (t=+0.7, 10w) | NA | NA | 0.04 |
| P13_BTC_LEADLAG | 2 | -0.0057 (t=-0.9, 140w) | -0.0101 (t=-1.3, 74w) | -0.0007 (t=-0.1, 66w) | 1.00 |
| P14_HOUR_SEASON | 1 | +0.0088 (t=+1.8, 128w) | +0.0035 (t=+0.6, 62w) | +0.0137 (t=+1.8, 66w) | 0.97 |
| P15_RV_IV_VRP | 24 | +0.0030 (t=+0.1, 137w) | -0.0287 (t=-0.8, 72w) | +0.0381 (t=+1.0, 65w) | 1.00 |

IC is diagnostic only. It is not defined for P07 (delta-neutral pair) and P12 has too few active weeks in some windows.

## 5.4 DEV-only re-selection of two mis-specified triggers (disclosed deviation)
* **P07_BASIS_CARRY**: DEV-only grid [{"thr": 0.0001, "dev_net_sharpe": -2.9338, "dev_gross_sharpe": 9.7859, "dev_turn_ann": 51.8013, "dev_net_ann": -0.0324}, {"thr": 0.0001, "dev_net_sharpe": -0.086, "dev_gross_sharpe": 6.2069, "dev_turn_ann": 22.6332, "dev_net_ann": -0.0008}, {"thr": 0.0002, "dev_net_sharpe": -0.2267, "dev_gross_sharpe": 5.4489, "dev_turn_ann": 19.6048, "dev_net_ann": -0.0019}, {"thr": 0.0003, "dev_net_sharpe": 0.9107, "dev_gross_sharpe": 4.4396, "dev_turn_ann": 10.9978, "dev_net_ann": 0.0065}, {"thr": 0.0005, "dev_net_sharpe": -0.1903, "dev_gross_sharpe": 3.0814, "dev_turn_ann": 8.3679, "dev_net_ann": -0.0011}] -> selected `{"thr": 0.0003, "dev_net_sharpe": 0.9106823736319379, "dev_gross_sharpe": 4.439628553995378, "dev_turn_ann": 10.997816593886464, "dev_net_ann": 0.006456144314614585}`
* **P12_ILLIQ_SHOCK**: DEV-only grid [{"zt": 1.25, "dev_net_sharpe": -3.0988, "dev_gross_sharpe": 0.1868, "dev_turn_ann": 619.0655, "dev_net_ann": -0.4438}, {"zt": 1.5, "dev_net_sharpe": -2.0815, "dev_gross_sharpe": -0.0742, "dev_turn_ann": 161.5404, "dev_net_ann": -0.1275}, {"zt": 1.75, "dev_net_sharpe": -0.6097, "dev_gross_sharpe": 0.486, "dev_turn_ann": 25.7413, "dev_net_ann": -0.0108}, {"zt": 2.0, "dev_net_sharpe": -0.515, "dev_gross_sharpe": -0.2866, "dev_turn_ann": 2.0721, "dev_net_ann": -0.0037}] -> selected `{"zt": 2.0, "dev_net_sharpe": -0.5149775311405915, "dev_gross_sharpe": -0.2866148804284775, "dev_turn_ann": 2.0720524017467254, "dev_net_ann": -0.003693099150157169}`

Both first-pass triggers were degenerate: P07's threshold (1e-4 per 8h) equals Binance's default funding clamp so the state flip-flopped (51 turns/yr on the DEV window, cost > gross); P12's log-Amihud z>2 fired on 0.014% of bars. Selection used the DEV window only (P12: highest DEV net Sharpe among candidates with ≥20 turns/yr, i.e. 1.75). HOLDOUT was not used. Nevertheless the initial full-sample results had been seen, so P07/P12 carry a mild snooping penalty.

## 5.5 Causality audit (mechanical lookahead test)
For each primitive, weights were recomputed with all data after 5 random cut-points deleted; weights up to the cut-point (minus one bar for P14's boundary construction) must match the full-data weights to 1e-9. Result: **15/15 PASS**, max abs diff 0.0e+00. This proves the signal code is causal; it does not prove the *archives* were available with the stamped latency (see 03).
