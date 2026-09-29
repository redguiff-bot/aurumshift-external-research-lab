# 01 — Landscape: sources and candidate primitives

## 1.1 Discovery method
Web search (standard mode) over recent papers/working papers (2023–2026 preferred), serious OSS, exchange/vendor research and technical blogs; every candidate was reduced to mechanism, formula, inputs, sampling, horizon, failure modes and lookahead risk (02). Evidence labels follow the repository doctrine: **DOCUMENTED_CLAIM** (from an abstract or search snippet; not re-derived), **OBSERVED** (measured here), **INFERENCE**, **UNKNOWN**. Search coverage was shallow-to-moderate (≈10 queries): this is a landscape, not a systematic review. Exchange research (Binance Research, Deribit Insights) searches returned no citable signal studies; Kaiko/Amberdata results were marketing/paywalled aggregates.

## 1.2 Sources actually used
* `mom`: [TS and CS momentum in crypto (AUT ACFR working paper)](https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf) (DOCUMENTED_CLAIM: TS momentum strong, CS weak, many CS portfolios insignificant after costs); [Momentum Trading in Cryptocurrencies, BATP 44540](https://www.journals.vu.lt/BATP/article/view/44540)
* `mr`: [Short-horizon mean reversion in crypto: matched cross-market measurement, arXiv 2608.21888](https://arxiv.org/pdf/2608.21888) (DOCUMENTED_CLAIM: reversals concentrate after flow-driven moves, taker-buy imbalance)
* `perp`: [Fundamentals of Perpetual Futures, arXiv 2212.06888](https://arxiv.org/pdf/2212.06888v5) (DOCUMENTED_CLAIM: funding pays long->short in proportion to perp-spot gap; perp deviates from no-arbitrage more than FX)
* `carry`: [Cryptocurrency as an Investable Asset Class: Coming of Age, arXiv 2510.14435](https://arxiv.org/pdf/2510.14435) (DOCUMENTED_CLAIM: crypto carry Sharpe 6.45 over 2020-25, 4.06 from 2024, negative in 2025; profit mostly funding)
* `fdesign`: [Designing funding rates for perpetual futures, arXiv 2506.08573](https://arxiv.org/pdf/2506.08573)
* `liq`: [Early-warning signals across seven crypto-perpetual liquidation cascades, arXiv 2607.27070](https://arxiv.org/pdf/2607.27070)
* `xi`: [Fragmentation, Price Formation and Cross-Impact in Bitcoin Markets, arXiv 2108.09750](https://arxiv.org/pdf/2108.09750)
* `vendor`: Vendor liquidity research (Kaiko/Amberdata order-book depth; DOCUMENTED_CLAIM, paywalled/aggregated)
* `lead`: 'Price Transmission from Bitcoin to Altcoins: High-Frequency Evidence' (DOCUMENTED_CLAIM via search snippet: small caps respond with delay)
* `tod`: [Bitcoin Time-of-Day, Day-of-Week and Month-of-Year Effects, UWA](https://research-repository.uwa.edu.au/en/publications/bitcoin-time-of-day-day-of-week-and-month-of-year-effects-in-retu/) (DOCUMENTED_CLAIM: effects are time-varying, no persistent pattern); [Quantpedia: Intraday seasonality in Bitcoin](https://quantpedia.com/strategies/intraday-seasonality-in-bitcoin) (DOCUMENTED_CLAIM: 21-23h UTC)
* `vrp`: [The Bitcoin VIX and its variance risk premium (Sussex)](https://sro.sussex.ac.uk/id/eprint/91094/); [Risk Premia in the Bitcoin Market, arXiv 2410.15195](https://arxiv.org/html/2410.15195v2) (DOCUMENTED_CLAIM: VRP regime-dependent)
* `imom`: [Bitcoin intraday time series momentum, Univ. Birmingham](https://research.birmingham.ac.uk/en/publications/bitcoin-intraday-time-series-momentum/) (DOCUMENTED_CLAIM: first half-hour predicts last half-hour; liquidity-provision driven)
* `qh`: [The Quarter-Hour Effect, arXiv 2607.09426](https://arxiv.org/pdf/2607.09426) (DOCUMENTED_CLAIM: imbalance at quarter-hour openings forecasts 4-12h returns, Binance perps)
* `oss`: OSS: Qlib Alpha158 feature set, freqtrade/FreqAI, vectorbt (DOCUMENTED_CLAIM from web search only; source code NOT inspected in this study)

Additional context from the search results, not used for any number: crypto cascade case studies (Oct-2025 event described as the largest; DOCUMENTED_CLAIM from search summaries), and the observation that many TS-momentum results erode after costs (AUT working paper snippet).

## 1.3 Family coverage
Requested families → executed / discovered-only:
* momentum/trend: P01, P04 (+D01, D16, D18) · mean reversion: P03 (+D03) · vol compression/expansion: P05 (+D14, D15) · carry: P07 (+D09) · basis: P08 (+D09) · funding divergence: P06 (+D10, D11, D13) · OI/price divergence: P09 · liquidation pressure: P10 *proxy* (+D04, D05 not testable) · volume imbalance: P11 (+D02, D24, D28) · liquidity shocks: P12 (+D23) · realized vs implied vol: P15 (+D07) · **term structure: not executed** (D06: no public PIT surface; only single-tenor DVOL) · cross-asset lead/lag: P13 (+D12) · cross-sectional RS: P02 (+D25) · intraday seasonality: P14 (+D22) · breakout persistence: P04, P05 · regime-conditioned signals: evaluated as *conditioning of all 15* in 07, plus D08/D16/D17 discovered · **event-driven macro: not executed** (D20/D21: ≈24 FOMC + ≈32 CPI events cannot pass multiplicity; revised-value risk).

## 1.4 Candidate list (43; 15 executed)
| id | primitive | family | status | forward-safety class |
|---|---|---|---|---|
| P01_TSMOM | Vol-normalised 72h time-series momentum | momentum / trend | EXECUTED | FORWARD_SAFE |
| P02_XS_RS | Cross-sectional 168h relative strength | cross-sectional relative strength | EXECUTED | FORWARD_SAFE |
| P03_REV_4H | Short-horizon reversal (4h z-score) | mean reversion | EXECUTED | FORWARD_SAFE |
| P04_DONCHIAN | Donchian 48h breakout / 24h exit (state machine) | breakout persistence | EXECUTED | FORWARD_SAFE |
| P05_VOL_SQUEEZE_BREAK | Vol compression then directional expansion | volatility compression / expansion | EXECUTED | FORWARD_SAFE |
| P06_FUND_XS | Cross-sectional funding crowding fade | funding divergence / carry (directional) | EXECUTED | FORWARD_SAFE_WITH_RECEIPT_STAMP |
| P07_BASIS_CARRY | Funding-threshold delta-neutral carry (long spot / short perp) | carry / basis | EXECUTED | FORWARD_SAFE_WITH_RECEIPT_STAMP |
| P08_SPOT_PERP_BASIS | Spot-perp basis z-score (time-series) | basis | EXECUTED | FORWARD_SAFE_WITH_RECEIPT_STAMP |
| P09_OI_PRICE | OI-confirmed trend / OI-unwind fade | open-interest / price divergence | EXECUTED | FORWARD_SAFE_WITH_RECEIPT_STAMP |
| P10_LIQ_FLUSH_PROXY | OI-flush contrarian (liquidation-pressure proxy) | liquidation pressure | EXECUTED | FORWARD_SAFE_WITH_RECEIPT_STAMP |
| P11_TAKER_FLOW | Taker-buy imbalance continuation | volume imbalance | EXECUTED | FORWARD_SAFE |
| P12_ILLIQ_SHOCK | Amihud-type liquidity shock fade | liquidity shocks | EXECUTED | FORWARD_SAFE |
| P13_BTC_LEADLAG | BTC->alt 2h catch-up | cross-asset lead/lag | EXECUTED | FORWARD_SAFE |
| P14_HOUR_SEASON | Hour-of-day seasonality (expanding, walk-forward) | intraday seasonality | EXECUTED | FORWARD_SAFE |
| P15_RV_IV_VRP | DVOL minus realised vol (BTC/ETH only) | realized vs implied volatility | EXECUTED | FORWARD_SAFE_WITH_RECEIPT_STAMP |
| D01 | Intraday first-half-hour -> last-half-hour momentum | momentum / trend | discovered | FORWARD_SAFE |
| D02 | Quarter-hour order-imbalance effect | volume imbalance | discovered | FORWARD_SAFE |
| D03 | Flow-conditioned short-horizon reversal | mean reversion | discovered | FORWARD_SAFE |
| D04 | Liquidation-cascade early-warning signals | liquidation pressure | discovered | LOOKAHEAD_RISK |
| D05 | Direct liquidation-print imbalance (forceOrder / OKX liquidation-orders) | liquidation pressure | discovered | FORWARD_SAFE_WITH_RECEIPT_STAMP |
| D06 | Options IV term-structure slope (1w vs 3m) | term structure | discovered | OFFLINE_ONLY |
| D07 | 25-delta risk reversal / skew | realized vs implied volatility | discovered | OFFLINE_ONLY |
| D08 | Dealer gamma exposure (GEX) | regime-conditioned signals | discovered | OFFLINE_ONLY |
| D09 | Dated-futures annualised basis (quarterlies) | basis | discovered | FORWARD_SAFE |
| D10 | Premium-index-implied next funding forecast | funding divergence | discovered | FORWARD_SAFE |
| D11 | Top-trader long/short ratio contrarian | funding divergence | discovered | FORWARD_SAFE_WITH_RECEIPT_STAMP |
| D12 | Coinbase-Binance spot premium | cross-asset lead/lag | discovered | FORWARD_SAFE_WITH_RECEIPT_STAMP |
| D13 | Cross-venue funding spread (HL vs Binance) | funding divergence | discovered | FORWARD_SAFE_WITH_RECEIPT_STAMP |
| D14 | Volatility-managed sizing (inverse realised vol) | volatility compression / expansion | discovered | FORWARD_SAFE |
| D15 | HAR realised-variance forecast / jump & semi-variance | volatility compression / expansion | discovered | FORWARD_SAFE |
| D16 | Efficiency-ratio / ADX gated trend | regime-conditioned signals | discovered | FORWARD_SAFE |
| D17 | HMM / Markov-switching regimes (smoothed) | regime-conditioned signals | discovered | LOOKAHEAD_RISK |
| D18 | Centered MA / HP filter / wavelet / Savitzky-Golay denoising | momentum / trend | discovered | LOOKAHEAD_RISK |
| D19 | Full-sample z-score / quantile transform / PCA | cross-sectional relative strength | discovered | LOOKAHEAD_RISK |
| D20 | Macro surprise (actual-consensus) with revised history | event-driven macro reactions | discovered | LOOKAHEAD_RISK |
| D21 | Scheduled-event vol drift (FOMC/CPI timestamps) | event-driven macro reactions | discovered | FORWARD_SAFE_WITH_RECEIPT_STAMP |
| D22 | Overnight/weekend & day-of-week effects | intraday seasonality | discovered | FORWARD_SAFE |
| D23 | Order-book imbalance / microprice / depth | liquidity shocks | discovered | FORWARD_SAFE_WITH_RECEIPT_STAMP |
| D24 | VPIN / flow toxicity | volume imbalance | discovered | FORWARD_SAFE |
| D25 | Cross-sectional idiosyncratic-vol / low-risk anomaly | cross-sectional relative strength | discovered | FORWARD_SAFE |
| D26 | Stablecoin supply / exchange netflow / on-chain | event-driven macro reactions | discovered | LOOKAHEAD_RISK |
| D27 | Social/search sentiment | event-driven macro reactions | discovered | LOOKAHEAD_RISK |
| D28 | Perp/spot volume dominance ratio | volume imbalance | discovered | FORWARD_SAFE |

