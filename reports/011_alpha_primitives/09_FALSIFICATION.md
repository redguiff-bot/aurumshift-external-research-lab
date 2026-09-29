# 09 — Falsification battery

Goal: try to break every primitive. Anything that only works at one venue, one cost level, one parameter setting, one asset group or one regime is not a primitive. Cross-venue panels use 5 assets (BTC ETH SOL XRP DOGE): OKX perp (from 2024-04-10), Coinbase spot USD (same window; spot cost = perp + 5 bp), Gate spot (only from 2025-12-19, API depth limit), Hyperliquid candles (only ~6 months; used for data checks only), Kraken (721 hourly bars; return correlation vs Binance perp 0.995–0.999, so price feeds agree and venue divergence is not a price-data artefact). Because these venues quote near-identical prices, cross-venue agreement is a consistency check, not independent evidence; note also that the 5-asset subset yields different gross Sharpes than the 10-asset universe (universe sensitivity, see 00). Price-only primitives run natively on the other venue (no funding on either side for like-for-like); feature primitives (funding/OI/flow/illiquidity) are computed from Binance data and *executed* on OKX prices.

## 9.1 Higher costs
See 08 (0.5×–3×, uniform bp, all-UNKNOWN). No primitive is net-positive at 1.5× in both DEV and HOLDOUT.

## 9.2 Wrong venue / different data provider
| primitive | venue test | result on other venue | same-asset/window reference |
|---|---|---|---|
| P01_TSMOM | okx_perp | gross 0.20 / net -0.30 | gross 0.19 / net -0.30 |
| P01_TSMOM | coinbase_spot | gross 0.22 / net -0.62 | gross 0.19 / net -0.65 |
| P01_TSMOM | gate_spot | gross -0.45 / net -1.31 | gross -0.47 / net -1.33 |
| P02_XS_RS | okx_perp | gross 0.93 / net 0.32 | gross 0.91 / net 0.29 |
| P02_XS_RS | coinbase_spot | gross 0.95 / net -0.07 | gross 0.91 / net -0.13 |
| P02_XS_RS | gate_spot | gross -0.30 / net -1.98 | gross -0.30 / net -1.98 |
| P03_REV_4H | okx_perp | gross 0.13 / net -2.48 | gross 0.15 / net -2.45 |
| P03_REV_4H | coinbase_spot | gross 0.21 / net -4.26 | gross 0.15 / net -4.30 |
| P03_REV_4H | gate_spot | gross -0.49 / net -5.35 | gross -0.49 / net -5.34 |
| P04_DONCHIAN | okx_perp | gross 0.63 / net 0.30 | gross 0.57 / net 0.24 |
| P04_DONCHIAN | coinbase_spot | gross 0.58 / net 0.02 | gross 0.57 / net 0.01 |
| P04_DONCHIAN | gate_spot | gross 0.58 / net -0.03 | gross 0.58 / net -0.00 |
| P05_VOL_SQUEEZE_BREAK | okx_perp | gross 0.92 / net 0.44 | gross 0.93 / net 0.45 |
| P05_VOL_SQUEEZE_BREAK | coinbase_spot | gross 0.78 / net 0.00 | gross 0.93 / net 0.11 |
| P05_VOL_SQUEEZE_BREAK | gate_spot | gross -0.31 / net -1.46 | gross -0.78 / net -1.95 |
| P06_FUND_XS | binance_signal_okx_prices | OKX exec: gross 0.05 / net -1.08 | Binance exec: gross 0.07 / net -1.06 |
| P06_FUND_XS | hyperliquid_funding_signal | HL funding signal, OKX prices: gross -1.54 / net -2.35 | Binance funding signal, OKX prices: gross 0.05 / net -1.08; corr HL~Binance funding BTC 0.79, ETH 0.76, SOL 0.85, XRP 0.78, DOGE 0.84 |
| P08_SPOT_PERP_BASIS | binance_signal_okx_prices | OKX exec: gross -0.35 / net -1.23 | Binance exec: gross -0.30 / net -1.18 |
| P09_OI_PRICE | binance_signal_okx_prices | OKX exec: gross 1.68 / net 0.57 | Binance exec: gross 1.68 / net 0.56 |
| P10_LIQ_FLUSH_PROXY | binance_signal_okx_prices | OKX exec: gross -0.66 / net -1.08 | Binance exec: gross -0.66 / net -1.07 |
| P11_TAKER_FLOW | binance_signal_okx_prices | OKX exec: gross 0.66 / net -2.54 | Binance exec: gross 0.61 / net -2.59 |
| P12_ILLIQ_SHOCK | binance_signal_okx_prices | OKX exec: gross 1.11 / net 0.19 | Binance exec: gross 1.11 / net 0.19 |
| P13_BTC_LEADLAG | okx_perp | gross 0.25 / net -4.88 | gross 0.26 / net -4.89 |
| P13_BTC_LEADLAG | coinbase_spot | gross 0.28 / net -8.23 | gross 0.26 / net -8.27 |
| P13_BTC_LEADLAG | gate_spot | gross -1.52 / net -12.46 | gross -1.57 / net -12.43 |
| P14_HOUR_SEASON | okx_perp | gross 1.31 / net -11.92 | gross 1.30 / net -11.93 |
| P14_HOUR_SEASON | coinbase_spot | gross 1.35 / net -21.32 | gross 1.30 / net -21.08 |
| P14_HOUR_SEASON | gate_spot | gross -0.09 / net -25.46 | gross 1.06 / net -23.17 |


## 9.3 Different asset groups
| primitive | majors (BTC ETH BNB SOL XRP) gross/net | minors (DOGE ADA LINK AVAX LTC) gross/net | leave-one-asset-out net Sharpe range |
|---|---|---|---|
| P01_TSMOM | 0.11 / -0.46 | -0.19 / -0.69 | -0.75 .. -0.50 |
| P02_XS_RS | 0.45 / -0.16 | 0.31 / -0.32 | -1.08 .. -0.17 |
| P03_REV_4H | 0.32 / -2.57 | 0.40 / -1.98 | -2.41 .. -2.19 |
| P04_DONCHIAN | 0.31 / -0.06 | 0.05 / -0.27 | -0.30 .. -0.05 |
| P05_VOL_SQUEEZE_BREAK | 0.67 / 0.12 | 0.51 / 0.07 | -0.07 .. 0.25 |
| P06_FUND_XS | 0.03 / -1.02 | -0.10 / -1.29 | -1.00 .. -0.41 |
| P07_BASIS_CARRY | 2.95 / 0.38 | 3.12 / 0.78 | 0.56 .. 0.75 |
| P08_SPOT_PERP_BASIS | -0.03 / -1.06 | -0.57 / -1.45 | -1.61 .. -1.31 |
| P09_OI_PRICE | 1.45 / 0.19 | -0.33 / -1.40 | -1.11 .. -0.48 |
| P10_LIQ_FLUSH_PROXY | -0.02 / -0.52 | -0.46 / -0.79 | -0.86 .. -0.55 |
| P11_TAKER_FLOW | 0.61 / -3.07 | 0.50 / -2.47 | -3.14 .. -2.86 |
| P12_ILLIQ_SHOCK | 1.14 / 0.31 | -0.40 / -1.23 | -0.88 .. -0.08 |
| P13_BTC_LEADLAG | 0.07 / -5.98 | -0.18 / -5.04 | -6.04 .. -5.40 |
| P14_HOUR_SEASON | 1.34 / -12.53 | 0.39 / -9.48 | -12.08 .. -10.86 |
| P15_RV_IV_VRP | -0.02 / -0.13 | NA | -0.24 .. -0.04 |


## 9.4 Regime reversal, high volatility, low volatility
Per-regime gross/net tables are in 07 (vol terciles, bull/bear, funding heat). Sub-period stability:
| primitive | share of quarters gross>0 | share net>0 | worst quarter net | share of 90d windows net>0 |
|---|---|---|---|---|
| P01_TSMOM | 0.45 | 0.36 | -33.3% | 0.26 |
| P02_XS_RS | 0.55 | 0.55 | -22.8% | 0.35 |
| P03_REV_4H | 0.73 | 0.09 | -34.1% | 0.04 |
| P04_DONCHIAN | 0.64 | 0.45 | -22.8% | 0.44 |
| P05_VOL_SQUEEZE_BREAK | 0.55 | 0.55 | -6.3% | 0.53 |
| P06_FUND_XS | 0.55 | 0.36 | -13.9% | 0.40 |
| P07_BASIS_CARRY | 0.27 | 0.09 | -1.0% | 0.04 |
| P08_SPOT_PERP_BASIS | 0.36 | 0.27 | -34.1% | 0.25 |
| P09_OI_PRICE | 0.64 | 0.27 | -20.0% | 0.26 |
| P10_LIQ_FLUSH_PROXY | 0.36 | 0.18 | -6.2% | 0.29 |
| P11_TAKER_FLOW | 0.82 | 0.00 | -33.9% | 0.00 |
| P12_ILLIQ_SHOCK | 0.73 | 0.45 | -1.9% | 0.41 |
| P13_BTC_LEADLAG | 0.55 | 0.00 | -40.1% | 0.00 |
| P14_HOUR_SEASON | 0.64 | 0.00 | -94.0% | 0.00 |
| P15_RV_IV_VRP | 0.36 | 0.36 | -31.6% | 0.47 |


## 9.5 Missing data (fail-closed / stale-hold), 3 seeds averaged; net Sharpe
`flat/NA` under stale-hold means the primitive never trades (fails closed because a strict rolling window can no longer be filled).
| primitive | 5% random obs missing (flat / stale-hold) | 20% missing | 10% asset-day outages |
|---|---|---|---|
| P01_TSMOM | -0.47 / -0.47 | flat/NA / flat/NA | -0.37 / -0.37 |
| P02_XS_RS | flat/NA / flat/NA | flat/NA / flat/NA | 0.25 / 0.25 |
| P03_REV_4H | -2.40 / -2.40 | -2.02 / -2.02 | -2.40 / -2.40 |
| P04_DONCHIAN | -0.40 / -0.40 | flat/NA / flat/NA | -0.29 / -0.29 |
| P05_VOL_SQUEEZE_BREAK | 0.37 / 0.37 | flat/NA / flat/NA | 0.04 / 0.04 |
| P06_FUND_XS | -0.72 / -0.72 | -0.48 / -0.48 | -0.57 / -0.57 |
| P07_BASIS_CARRY | 0.70 / 0.70 | 0.79 / 0.79 | 0.67 / 0.67 |
| P08_SPOT_PERP_BASIS | -1.41 / -1.41 | -1.45 / -1.45 | -1.43 / -1.43 |
| P09_OI_PRICE | -0.92 / -0.92 | -0.38 / -0.38 | -0.82 / -0.82 |
| P10_LIQ_FLUSH_PROXY | -0.71 / -0.71 | -0.72 / -0.72 | -0.57 / -0.57 |
| P11_TAKER_FLOW | -2.64 / -2.64 | -0.00 / -0.00 | -2.86 / -2.86 |
| P12_ILLIQ_SHOCK | -0.65 / -0.65 | -0.71 / -0.71 | -1.07 / -1.07 |
| P13_BTC_LEADLAG | -4.70 / -4.70 | -2.04 / -2.04 | -4.89 / -4.89 |
| P14_HOUR_SEASON | -12.07 / -12.07 | -14.29 / -14.29 | -12.02 / -12.02 |
| P15_RV_IV_VRP | flat/NA / flat/NA | flat/NA / flat/NA | 0.34 / 0.34 |


## 9.6 Stale data / latency (fills delayed by 1–6 bars; net Sharpe)
| primitive | base net | lag+1h | +2h | +3h | +6h |
|---|---|---|---|---|---|
| P01_TSMOM | -0.61 | -0.62 | -0.67 | -0.72 | -0.50 |
| P02_XS_RS | -0.60 | -0.71 | -0.75 | -0.77 | -0.50 |
| P03_REV_4H | -2.33 | -3.18 | -3.48 | -3.08 | -2.46 |
| P04_DONCHIAN | -0.19 | -0.22 | -0.18 | -0.15 | -0.12 |
| P05_VOL_SQUEEZE_BREAK | 0.10 | 0.52 | 0.61 | 0.92 | 0.14 |
| P06_FUND_XS | -0.80 | -0.65 | -0.60 | -0.65 | -0.71 |
| P07_BASIS_CARRY | 0.64 | 0.62 | 0.67 | 0.70 | 0.60 |
| P08_SPOT_PERP_BASIS | -1.45 | -1.38 | -1.18 | -1.27 | -1.36 |
| P09_OI_PRICE | -0.86 | -0.91 | -0.85 | -1.21 | -1.63 |
| P10_LIQ_FLUSH_PROXY | -0.74 | -0.73 | -0.50 | -0.64 | 0.22 |
| P11_TAKER_FLOW | -3.08 | -3.01 | -3.22 | -3.50 | -3.53 |
| P12_ILLIQ_SHOCK | -0.63 | -0.77 | -1.12 | -0.63 | -1.26 |
| P13_BTC_LEADLAG | -5.81 | -6.24 | -5.70 | -5.09 | -5.53 |
| P14_HOUR_SEASON | -11.58 | -12.82 | -13.60 | -13.00 | -13.86 |
| P15_RV_IV_VRP | -0.13 | -0.25 | -0.27 | -0.24 | -0.22 |


## 9.7 Parameter perturbation (scalable parameters ×0.5, ×0.75, ×1.5, ×2)
| primitive | share net>0 | share gross>0 | median net Sharpe | min | max |
|---|---|---|---|---|---|
| P01_TSMOM | 0.00 | 0.75 | -0.30 | -0.63 | -0.12 |
| P02_XS_RS | 0.25 | 0.50 | -0.74 | -1.74 | 0.14 |
| P03_REV_4H | 0.00 | 0.25 | -2.43 | -2.73 | -1.99 |
| P04_DONCHIAN | 0.12 | 1.00 | -0.22 | -0.42 | 0.01 |
| P05_VOL_SQUEEZE_BREAK | 0.58 | 1.00 | 0.16 | -0.72 | 1.04 |
| P06_FUND_XS | 0.25 | 1.00 | -0.90 | -1.49 | 0.19 |
| P07_BASIS_CARRY | 0.75 | 1.00 | 0.34 | -0.80 | 1.02 |
| P08_SPOT_PERP_BASIS | 0.00 | 0.00 | -1.40 | -2.10 | -0.82 |
| P09_OI_PRICE | 0.00 | 1.00 | -0.34 | -0.42 | -0.28 |
| P10_LIQ_FLUSH_PROXY | 0.25 | 0.42 | -0.51 | -1.50 | 0.75 |
| P11_TAKER_FLOW | 0.00 | 0.75 | -3.59 | -4.56 | -2.20 |
| P12_ILLIQ_SHOCK | 0.00 | 0.83 | -1.00 | -5.82 | -0.24 |
| P13_BTC_LEADLAG | 0.00 | 0.25 | -5.20 | -5.81 | -3.84 |
| P14_HOUR_SEASON | 0.00 | 1.00 | -11.60 | -11.87 | -10.89 |
| P15_RV_IV_VRP | 0.25 | 0.50 | -0.10 | -0.37 | 0.02 |


## 9.8 Placebo (directional information test)
Directional primitives: independent ±1 per asset per 24h block multiplied into the weights (keeps turnover/exposure structure, destroys direction; 200 draws). P07: circular time shift (random timing of the carry state). A circular shift was first tried for all primitives and *rejected*: wrap-around lets late, better-informed expanding estimates hit early returns, inflating the null (P14's null Sharpe was 2.1 vs 0.85 observed).
| primitive | null | observed gross Sharpe | null gross Sharpe (mean ± sd) | p (null ≥ observed) |
|---|---|---|---|---|
| P01_TSMOM | block_sign_randomisation | -0.06 | 0.03 ± 0.62 | 0.59 |
| P02_XS_RS | block_sign_randomisation | 0.16 | -0.04 ± 0.67 | 0.34 |
| P03_REV_4H | block_sign_randomisation | 0.38 | -0.02 ± 0.64 | 0.27 |
| P04_DONCHIAN | block_sign_randomisation | 0.17 | -0.03 ± 0.66 | 0.39 |
| P05_VOL_SQUEEZE_BREAK | block_sign_randomisation | 0.66 | -0.09 ± 0.57 | 0.08 |
| P06_FUND_XS | block_sign_randomisation | 0.72 | 0.09 ± 0.68 | 0.19 |
| P07_BASIS_CARRY | circular_shift | 3.10 | 2.24 ± 0.64 | 0.03 |
| P08_SPOT_PERP_BASIS | block_sign_randomisation | -0.39 | -0.04 ± 0.66 | 0.72 |
| P09_OI_PRICE | block_sign_randomisation | 0.52 | -0.02 ± 0.65 | 0.20 |
| P10_LIQ_FLUSH_PROXY | block_sign_randomisation | -0.31 | -0.07 ± 0.62 | 0.64 |
| P11_TAKER_FLOW | block_sign_randomisation | 0.61 | 0.05 ± 0.60 | 0.17 |
| P12_ILLIQ_SHOCK | block_sign_randomisation | 0.45 | -0.06 ± 0.64 | 0.20 |
| P13_BTC_LEADLAG | block_sign_randomisation | -0.09 | -0.01 ± 0.60 | 0.55 |
| P14_HOUR_SEASON | block_sign_randomisation | 0.85 | -0.05 ± 0.63 | 0.07 |
| P15_RV_IV_VRP | block_sign_randomisation | -0.02 | 0.00 ± 0.67 | 0.54 |

