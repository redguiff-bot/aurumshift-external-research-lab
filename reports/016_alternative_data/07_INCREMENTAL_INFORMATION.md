# 07 — Does the data add information beyond price, volume, volatility, funding, OI?

> External research only — no private AurumShift code, no integration claims. Evidence tags: **[OBS]** observed in this study, **[DOC]** stated on a provider page/API response fetched in this study, **[INF]** inference, **[UNK]** unknown/not verified. Study date 2026-09-29 (sandbox clock). Reproduce with `bench/alternative_data_v1/`.


## Design (classification rules written in the docstring of `py/analysis_crypto.py` before the first run; the baseline was revised once afterwards — see the calendar section)
* **Asset/target panel.** BTCUSDT and ETHUSDT daily (Binance spot 1-d klines via `data-api.binance.vision`), 2021-01-01 → 2026-09-28 (~2000 BTC days; ETH ~1700 — Binance ETH `metrics` start 2021-12). Decision instant = 00:00 UTC of day *d*; targets on day *d*: log return, log high/low range (volatility), |return|.
* **Baseline (information already in price/volume/vol/funding/OI):** lagged 1/5/20-day returns; log range 1/5/20/60-day means; log quote-volume and trade-count z-scores; taker-buy share; funding (level, deviation from 7-day mean); Δ log OI (1d, 5d), OI z-score; **6 weekday dummies** (target-day calendar effect). Funding/OI come from Binance Vision (5-min `metrics` rows, 8-h funding files).
* **Candidate blocks** (2 features each: trailing 30-day z-score of level and 1-day change; % change for stablecoin supply; level & change for F&G), lagged per `06`. Sources: Coin Metrics community (flows, active addresses, tx count, hash rate), Blockchain.com (tx count, mempool size, fees, unique addresses), DefiLlama (stablecoin supply, DEX volume), Fear & Greed, CFTC TFF, Treasury TGA, NY Fed RRP, Wikipedia page-views, npm downloads, Binance long/short & taker ratios. **Controls:** 2 seeded Gaussian-noise blocks (false-positive calibration), a price-derived block (60-d drawdown + 30-d momentum), Coin Metrics MVRV (price/realised-price), and Deribit DVOL (designed as the positive control for the volatility target; because it passes the same rules it is *also counted as a candidate* — a post-hoc relabel, disclosed).
* **Tests per (asset, block, target):** (1) HAC(5) Wald p for the block in baseline+block OLS; (2) univariate HAC p; (3) expanding-window OOS (min train 400 d, refit every 10 d): MSE gain vs baseline and one-sided Diebold–Mariano with HAC(5); (4) sign stability (cosine of standardised block coefficients across chronological halves); (5) **price-reactivity R²** of the block measured on observation dates against same-day return/|return|/range + 5 lags of each (`react_ctmp`), past-only version (`react_past`), and R² of the lagged block on the full baseline (`red_base`); (6) Benjamini–Hochberg FDR over all 93 primary tests (controls except DVOL excluded).
* **Classification (pre-declared).** *INCREMENTAL_CANDIDATE*: p_incr<0.05 **and** BH-q<0.10 **and** OOS gain>0 with DM one-sided p<0.10 **and** sign-stable **and** price-reactivity<0.40. *PRICE_DERIVATIVE_ONLY*: reactivity ≥0.40, or all univariately-significant tests are absorbed by the baseline (p_incr ≥ 0.10). *INDEPENDENT_NO_EVIDENCE*: neither — informationally distinct but unproven (not negative evidence).

## Calibration controls
| cand | klass | min_p_incr | max_oos_gain_pct | react_ctmp_max | n_p05 | n_tests |
|---|---|---|---|---|---|---|
| deribit_dvol_CONTROL_implied_vol | INCREMENTAL_CANDIDATE | 0.000 | 2.292 | 0.190 | 3 | 3 |
| CONTROL_noise_A | INDEPENDENT_NO_EVIDENCE | 0.071 | 0.154 | 0.008 | 0 | 6 |
| CONTROL_noise_B | INDEPENDENT_NO_EVIDENCE | 0.196 | -0.176 | -0.000 | 0 | 6 |
| CONTROL_price_derived_drawdown_mom | PRICE_DERIVATIVE_ONLY | 0.057 | 0.068 | 0.332 | 0 | 6 |
| cm_mvrv_CONTROL_price_derived | PRICE_DERIVATIVE_ONLY | 0.177 | -0.303 | 0.875 | 0 | 3 |

Noise blocks: 0/12 with p<0.05 and 0/12 with DM p<0.10 (calibrated). Price-derived and MVRV blocks are correctly flagged PRICE_DERIVATIVE_ONLY (MVRV reactivity 0.88). DVOL passes (positive control for power: OOS +2.29 % on log-range, DM p = 0.005).

## Results by block
| cand | klass | n_tests | n_p05 | min_p_incr | min_q_fam | best_target | best_oos_gain_pct | best_dm_p | react_ctmp_max | red_base_max |
|---|---|---|---|---|---|---|---|---|---|---|
| deribit_dvol_CONTROL_implied_vol | INCREMENTAL_CANDIDATE | 3 | 3 | 0.000 | 0.000 | BTC:lrange | 2.292 | 0.005 | 0.190 | 0.422 |
| treasury_tga_liquidity | INDEPENDENT_NO_EVIDENCE | 6 | 1 | 0.012 | 0.213 | BTC:absret | -0.642 | 0.799 | 0.017 | 0.127 |
| binance_um_positioning_ratios | INDEPENDENT_NO_EVIDENCE | 6 | 1 | 0.019 | 0.213 | BTC:absret | -0.009 | 0.506 | 0.324 | 0.442 |
| nyfed_reverse_repo | INDEPENDENT_NO_EVIDENCE | 6 | 2 | 0.024 | 0.213 | BTC:lrange | 0.060 | 0.451 | 0.044 | 0.158 |
| wikipedia_pageviews_Bitcoin | INDEPENDENT_NO_EVIDENCE | 3 | 1 | 0.031 | 0.213 | BTC:lrange | -0.219 | 0.670 | 0.126 | 0.254 |
| cm_tx_count | INDEPENDENT_NO_EVIDENCE | 6 | 1 | 0.031 | 0.213 | ETH:ret | -0.055 | 0.552 | 0.129 | 0.236 |
| cm_hashrate | INDEPENDENT_NO_EVIDENCE | 3 | 1 | 0.033 | 0.213 | BTC:ret | -0.542 | 0.882 | 0.008 | 0.028 |
| npm_downloads_npm_web3 | INDEPENDENT_NO_EVIDENCE | 3 | 0 | 0.067 | 0.307 | ETH:lrange | -0.218 | 0.749 | 0.198 | 0.663 |
| CONTROL_noise_A | INDEPENDENT_NO_EVIDENCE | 6 | 0 | 0.071 |  | ETH:lrange | 0.154 | 0.226 | 0.008 | -0.002 |
| bc_tx_fees_btc | INDEPENDENT_NO_EVIDENCE | 3 | 0 | 0.098 | 0.381 | BTC:ret | -0.792 | 0.917 | 0.127 | 0.255 |
| CONTROL_noise_B | INDEPENDENT_NO_EVIDENCE | 6 | 0 | 0.196 |  | BTC:ret | -0.565 | 0.905 | -0.000 | -0.000 |
| bc_mempool_size | INDEPENDENT_NO_EVIDENCE | 3 | 0 | 0.230 | 0.509 | BTC:ret | -0.463 | 0.901 | 0.019 | 0.034 |
| npm_downloads_npm_ethers | PRICE_DERIVATIVE_ONLY | 3 | 1 | 0.006 | 0.189 | ETH:ret | -0.777 | 0.864 | 0.212 | 0.688 |
| llama_dex_volume | PRICE_DERIVATIVE_ONLY | 6 | 1 | 0.013 | 0.213 | BTC:lrange | 0.204 | 0.339 | 0.500 | 0.611 |
| cm_exchange_flows | PRICE_DERIVATIVE_ONLY | 6 | 1 | 0.024 | 0.213 | BTC:lrange | 0.292 | 0.241 | 0.414 | 0.636 |
| alternative_me_fear_greed | PRICE_DERIVATIVE_ONLY | 6 | 1 | 0.026 | 0.213 | BTC:absret | -0.200 | 0.640 | 0.426 | 0.522 |
| npm_downloads_npm_solana_web3.js | PRICE_DERIVATIVE_ONLY | 3 | 1 | 0.034 | 0.213 | ETH:ret | -0.479 | 0.771 | 0.214 | 0.726 |
| cm_active_addresses | PRICE_DERIVATIVE_ONLY | 6 | 0 | 0.051 | 0.298 | ETH:absret | -0.248 | 0.702 | 0.211 | 0.420 |
| CONTROL_price_derived_drawdown_mom | PRICE_DERIVATIVE_ONLY | 6 | 0 | 0.057 |  | ETH:ret | -0.122 | 0.628 | 0.332 | 0.726 |
| llama_stablecoin_supply | PRICE_DERIVATIVE_ONLY | 6 | 0 | 0.096 | 0.381 | ETH:lrange | 0.200 | 0.078 | 0.187 | 0.546 |
| npm_downloads_npm_bitcoinjs-lib | PRICE_DERIVATIVE_ONLY | 3 | 0 | 0.124 | 0.428 | BTC:ret | -1.577 | 0.913 | 0.291 | 0.761 |
| bc_unique_addresses | PRICE_DERIVATIVE_ONLY | 3 | 0 | 0.166 | 0.473 | BTC:lrange | -0.194 | 0.789 | 0.215 | 0.489 |
| bc_tx_count | PRICE_DERIVATIVE_ONLY | 3 | 0 | 0.175 | 0.473 | BTC:absret | -0.130 | 0.741 | 0.013 | 0.059 |
| cm_mvrv_CONTROL_price_derived | PRICE_DERIVATIVE_ONLY | 3 | 0 | 0.177 |  | BTC:absret | -0.303 | 0.807 | 0.875 | 0.726 |
| cftc_tff_btc_cme | PRICE_DERIVATIVE_ONLY | 3 | 0 | 0.260 | 0.538 | BTC:lrange | -0.628 | 0.971 | 0.042 | 0.133 |
| wikipedia_pageviews_Ethereum | PRICE_DERIVATIVE_ONLY | 3 | 0 | 0.551 | 0.751 | ETH:lrange | -0.260 | 0.875 | 0.153 | 0.339 |

Top-20 individual tests by p_incr:
| cand | asset | target | n | p_incr | p_univ | q_bh | oos_gain_pct | dm_p_onesided | sign_cos | react_ctmp | red_base |
|---|---|---|---|---|---|---|---|---|---|---|---|
| deribit_dvol_CONTROL_implied_vol | BTC | lrange | 1896 | 0.000 | 0.000 |  | 2.292 | 0.005 | 0.947 | 0.190 | 0.422 |
| deribit_dvol_CONTROL_implied_vol | BTC | absret | 1896 | 0.000 | 0.000 |  | 0.423 | 0.353 | 0.669 | 0.190 | 0.422 |
| npm_downloads_npm_ethers | ETH | ret | 1635 | 0.006 | 0.355 | 0.257 | -0.777 | 0.864 | 0.475 | 0.212 | 0.688 |
| treasury_tga_liquidity | BTC | absret | 1534 | 0.012 | 0.002 | 0.257 | -0.642 | 0.799 | 0.980 | 0.017 | 0.118 |
| llama_dex_volume | BTC | lrange | 2008 | 0.013 | 0.001 | 0.257 | 0.204 | 0.339 | -0.531 | 0.490 | 0.518 |
| binance_um_positioning_ratios | BTC | absret | 1671 | 0.019 | 0.105 | 0.257 | -0.009 | 0.506 | 0.892 | 0.313 | 0.442 |
| nyfed_reverse_repo | BTC | lrange | 2008 | 0.024 | 0.000 | 0.257 | 0.060 | 0.451 | 0.956 | 0.044 | 0.158 |
| cm_exchange_flows | BTC | lrange | 2008 | 0.024 | 0.049 | 0.257 | 0.292 | 0.241 | 0.874 | 0.397 | 0.611 |
| deribit_dvol_CONTROL_implied_vol | BTC | ret | 1896 | 0.024 | 0.011 |  | -0.162 | 0.615 | 0.398 | 0.190 | 0.422 |
| alternative_me_fear_greed | BTC | absret | 2008 | 0.026 | 0.086 | 0.257 | -0.200 | 0.640 | 0.298 | 0.426 | 0.522 |
| wikipedia_pageviews_Bitcoin | BTC | lrange | 2008 | 0.031 | 0.031 | 0.257 | -0.219 | 0.670 | 0.782 | 0.126 | 0.254 |
| cm_tx_count | ETH | ret | 1676 | 0.031 | 0.090 | 0.257 | -0.055 | 0.552 | 0.710 | 0.129 | 0.236 |
| nyfed_reverse_repo | BTC | absret | 2008 | 0.031 | 0.000 | 0.257 | -0.855 | 0.889 | 0.893 | 0.044 | 0.158 |
| cm_hashrate | BTC | ret | 2008 | 0.033 | 0.026 | 0.257 | -0.542 | 0.882 | 0.818 | 0.008 | 0.028 |
| npm_downloads_npm_solana_web3.js | ETH | ret | 1635 | 0.034 | 0.258 | 0.257 | -0.479 | 0.771 | 0.801 | 0.214 | 0.726 |
| cm_active_addresses | ETH | absret | 1676 | 0.051 | 0.397 | 0.347 | -0.248 | 0.702 | 0.999 | 0.029 | 0.043 |
| llama_dex_volume | BTC | absret | 2008 | 0.056 | 0.054 | 0.347 | -0.285 | 0.711 | 0.027 | 0.490 | 0.518 |
| CONTROL_price_derived_drawdown_mom | ETH | ret | 1676 | 0.057 | 0.196 |  | -0.122 | 0.628 | 0.980 | 0.294 | 0.726 |
| alternative_me_fear_greed | BTC | lrange | 2008 | 0.065 | 0.311 | 0.347 | -0.393 | 0.841 | 0.800 | 0.426 | 0.522 |
| cm_tx_count | BTC | absret | 2008 | 0.065 | 0.002 | 0.347 | -0.055 | 0.605 | 0.952 | 0.009 | 0.058 |

In-sample: 15/93 tests have p<0.05 (≈4.7 expected under the null; 3 of them are DVOL); best BH-q for any non-DVOL test = 0.26. **No non-control crypto block passes the OOS test** — the best non-DVOL OOS MSE gain is 0.29 % (Coin Metrics exchange flows → log-range; DM p = 0.24).

## The calendar artefact (why the baseline has weekday dummies)
First-pass baseline *without* weekday dummies and the 60-day vol term (`ALT_NO_CALENDAR=1`, saved `results/incremental_results_no_calendar.csv`): 29/90 tests at p<0.05, 11 at p<0.001, 8 with OOS DM p<0.10 — e.g. npm downloads "improved" next-day range by 1.9–3.6 % (DM p ≤ 0.027) because both npm traffic and crypto volatility have a weekday cycle. Strong tests (p<0.001, OOS>0, DM p<0.10) in that first pass:
| cand | asset | target | p_incr | oos_gain_pct | dm_p_onesided |
|---|---|---|---|---|---|
| npm_downloads_npm_bitcoinjs-lib | BTC | lrange | 0.000 | 3.577 | 0.000 |
| npm_downloads_npm_solana_web3.js | ETH | lrange | 0.000 | 2.427 | 0.008 |
| cm_exchange_flows | ETH | lrange | 0.000 | 1.067 | 0.008 |
| bc_unique_addresses | BTC | lrange | 0.000 | 1.355 | 0.012 |
| npm_downloads_npm_web3 | ETH | lrange | 0.000 | 1.934 | 0.024 |
| npm_downloads_npm_ethers | ETH | lrange | 0.000 | 1.911 | 0.027 |

All disappear with calendar controls. Lesson: any candidate reporting an OOS gain on volatility must first beat weekday dummies.

## Sensitivity: optimistic availability (one day less lag for lag ≥ 2 sources)
72 extra tests; p<0.05 in 6; passing p<0.05 **and** OOS>0 **and** DM p<0.10: **0**. Hits (all fail OOS):
| cand | asset | target | lag_days | p_incr | oos_gain_pct | dm_p_onesided |
|---|---|---|---|---|---|---|
| cm_tx_count | BTC | absret | 1 | 0.031 | -0.302 | 0.781 |
| llama_dex_volume | BTC | lrange | 1 | 0.002 | 0.348 | 0.198 |
| treasury_tga_liquidity | BTC | absret | 2 | 0.010 | -1.252 | 0.931 |
| wikipedia_pageviews_Bitcoin | BTC | lrange | 1 | 0.044 | -0.358 | 0.795 |
| cm_exchange_flows | ETH | ret | 1 | 0.038 | -0.024 | 0.521 |
| npm_downloads_npm_ethers | ETH | ret | 1 | 0.012 | 0.022 | 0.483 |

## Real-economy tests
See `05_REAL_ECONOMY.md` (EIA crude candidate; gas storage & weather inconclusive; PortWatch none).

## Conclusions
* Candidates: **EIA weekly crude-inventory surprise, Deribit DVOL**.
* PRICE_DERIVATIVE_ONLY (12 blocks): npm_downloads_npm_ethers, llama_dex_volume, cm_exchange_flows, alternative_me_fear_greed, npm_downloads_npm_solana_web3.js, cm_active_addresses, llama_stablecoin_supply, npm_downloads_npm_bitcoinjs-lib, bc_unique_addresses, bc_tx_count, cftc_tff_btc_cme, wikipedia_pageviews_Ethereum.
* INDEPENDENT but unproven (9 blocks): treasury_tga_liquidity, binance_um_positioning_ratios, nyfed_reverse_repo, wikipedia_pageviews_Bitcoin, cm_tx_count, cm_hashrate, npm_downloads_npm_web3, bc_tx_fees_btc, bc_mempool_size.
* Not tested for lack of history/access: RSS/news/social, mempool state, prediction markets, GDELT, GH Archive, ETF flows, weather forecasts.
