# 02 — Primitive contracts

Common conventions (all executed primitives): bar index = bar open time; a decision after bar *i* uses only bars ≤ *i*, earns bar *i+1* close-to-close (0-latency fill at the prior close, cost model charges taker fee + slippage; latency +1..+6 bars is falsified in 09). Weights are equal-notional (1/N per asset, clipped to [−1,1]/N); cross-sectional primitives are dollar-neutral with gross 1. Perp positions pay/receive funding at each settlement. Vol estimate σ = 168h trailing std of log returns. Z-scores use trailing 720h windows (min 240). No parameter is tuned except the two DEV-only reselections (05 §5.4). Code: `bench/alpha_primitives_v1/py/primitives.py`.

## Executed primitives
### P01_TSMOM — Vol-normalised 72h time-series momentum  [EXECUTED]
* **Family:** momentum / trend
* **Mechanism:** Slow information diffusion, herding, trend-following flows
* **Formula:** z=sum(log r,72h)/(sigma_168h*sqrt72); w=clip(z,-1,1)/N; rebalance 6h
* **Required inputs:** perp close
* **Sampling assumptions:** 1h bars, close-to-close, trade next bar
* **Expected horizon:** 6-24h
* **Failure modes:** Whipsaw in range regimes; equal-notional weighting overweights alts; cost drag
* **Lookahead risk:** None: trailing windows only (truncation audit PASS)
* **Class:** `FORWARD_SAFE`
* **Sources:** [TS and CS momentum in crypto (AUT ACFR working paper)](https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf) (DOCUMENTED_CLAIM: TS momentum strong, CS weak, many CS portfolios insignificant after costs); [Momentum Trading in Cryptocurrencies, BATP 44540](https://www.journals.vu.lt/BATP/article/view/44540)

### P02_XS_RS — Cross-sectional 168h relative strength  [EXECUTED]
* **Family:** cross-sectional relative strength
* **Mechanism:** Winner-loser drift within a liquid universe
* **Formula:** rank(sum log r,168h) demeaned, gross=1 dollar-neutral; rebalance 24h
* **Required inputs:** perp close x10 assets
* **Sampling assumptions:** 1h bars
* **Expected horizon:** 1-7d
* **Failure modes:** Weak CS momentum in literature; survivorship of ex-post liquid universe; small universe (10)
* **Lookahead risk:** None (audit PASS); universe selection is ex-post (survivorship bias, not lookahead in signal)
* **Class:** `FORWARD_SAFE`
* **Sources:** [TS and CS momentum in crypto (AUT ACFR working paper)](https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf) (DOCUMENTED_CLAIM: TS momentum strong, CS weak, many CS portfolios insignificant after costs); [Momentum Trading in Cryptocurrencies, BATP 44540](https://www.journals.vu.lt/BATP/article/view/44540)

### P03_REV_4H — Short-horizon reversal (4h z-score)  [EXECUTED]
* **Family:** mean reversion
* **Mechanism:** Liquidity-provision premium after flow-driven overshoot
* **Formula:** w=-clip(z4/2,-1,1)/N, z4=sum log r 4h/(sigma*sqrt4); rebalance 4h
* **Required inputs:** perp close
* **Sampling assumptions:** 1h bars
* **Expected horizon:** 1-4h
* **Failure modes:** Trends/cascades; turnover ~1000x/yr makes it cost-fragile
* **Lookahead risk:** None (audit PASS)
* **Class:** `FORWARD_SAFE`
* **Sources:** [Short-horizon mean reversion in crypto: matched cross-market measurement, arXiv 2608.21888](https://arxiv.org/pdf/2608.21888) (DOCUMENTED_CLAIM: reversals concentrate after flow-driven moves, taker-buy imbalance)

### P04_DONCHIAN — Donchian 48h breakout / 24h exit (state machine)  [EXECUTED]
* **Family:** breakout persistence
* **Mechanism:** Range expansion continues (stop clustering, herding)
* **Formula:** enter long/short on close beyond prior 48h high/low; exit at prior 24h opposite extreme
* **Required inputs:** perp close/high/low
* **Sampling assumptions:** 1h bars; prior-bar extremes shifted 1
* **Expected horizon:** 1-5d
* **Failure modes:** False breakouts in chop; redundant with TSMOM (rho~0.8)
* **Lookahead risk:** Extremes use shift(1): no current-bar leak (audit PASS)
* **Class:** `FORWARD_SAFE`
* **Sources:** [TS and CS momentum in crypto (AUT ACFR working paper)](https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf) (DOCUMENTED_CLAIM: TS momentum strong, CS weak, many CS portfolios insignificant after costs); [Momentum Trading in Cryptocurrencies, BATP 44540](https://www.journals.vu.lt/BATP/article/view/44540)

### P05_VOL_SQUEEZE_BREAK — Vol compression then directional expansion  [EXECUTED]
* **Family:** volatility compression / expansion
* **Mechanism:** Vol clusters; low-vol squeeze precedes range expansion; first-move direction persists
* **Formula:** squeeze=sigma_24h/sigma_168h; trailing 90d percentile; if min pct over 12h<0.2 and |z6|>1: w=sign(R6); hold 12h
* **Required inputs:** perp close
* **Sampling assumptions:** 1h bars; rolling rank on past 2160h only
* **Expected horizon:** 6-24h
* **Failure modes:** Direction miss on fake expansion; sparse (18% active); fails closed under 20% missing data
* **Lookahead risk:** Rolling percentile uses past window only (audit PASS)
* **Class:** `FORWARD_SAFE`
* **Sources:** [TS and CS momentum in crypto (AUT ACFR working paper)](https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf) (DOCUMENTED_CLAIM: TS momentum strong, CS weak, many CS portfolios insignificant after costs); [Momentum Trading in Cryptocurrencies, BATP 44540](https://www.journals.vu.lt/BATP/article/view/44540)

### P06_FUND_XS — Cross-sectional funding crowding fade  [EXECUTED]
* **Family:** funding divergence / carry (directional)
* **Mechanism:** Extreme positive funding = crowded longs paying to hold; fade crowd, also collect funding
* **Formula:** rank(-mean of last 3 settled funding, per-8h normalised) dollar-neutral; rebalance 24h; funding cash paid/received per settlement
* **Required inputs:** Binance USD-M fundingRate archive (calc_time), perp close
* **Sampling assumptions:** Settlement stamp; feature usable after the bar containing settlement closes
* **Expected horizon:** 1-3d
* **Failure modes:** Funding regime change (mean per-8h funding fell 7.6e-5 -> 2.4e-5 in holdout); venue-specific; funding interval changes (4h/8h) normalised
* **Lookahead risk:** Settlement rate is known only at calc_time: feature lags one bar; archive != live stamped capture
* **Class:** `FORWARD_SAFE_WITH_RECEIPT_STAMP`
* **Sources:** [Fundamentals of Perpetual Futures, arXiv 2212.06888](https://arxiv.org/pdf/2212.06888v5) (DOCUMENTED_CLAIM: funding pays long->short in proportion to perp-spot gap; perp deviates from no-arbitrage more than FX); [Cryptocurrency as an Investable Asset Class: Coming of Age, arXiv 2510.14435](https://arxiv.org/pdf/2510.14435) (DOCUMENTED_CLAIM: crypto carry Sharpe 6.45 over 2020-25, 4.06 from 2024, negative in 2025; profit mostly funding); [Designing funding rates for perpetual futures, arXiv 2506.08573](https://arxiv.org/pdf/2506.08573)

### P07_BASIS_CARRY — Funding-threshold delta-neutral carry (long spot / short perp)  [EXECUTED]
* **Family:** carry / basis
* **Mechanism:** Perp premium funds short-perp/long-spot arbitrageurs; funding is the carry
* **Formula:** on if mean of last 3 settlements >= thr (dev-selected 3e-4 per 8h); pnl = r_spot - r_perp + funding; costs on both legs
* **Required inputs:** spot+perp close, funding archive
* **Sampling assumptions:** 1h bars; funding stamps
* **Expected horizon:** 8h-weeks
* **Failure modes:** Carry compression (holdout: never triggered at thr); capital efficiency (margin) unmodelled; exchange/ADL/basis-blowout risk unmodelled
* **Lookahead risk:** Threshold selected on DEV only; holdout untouched (audit PASS)
* **Class:** `FORWARD_SAFE_WITH_RECEIPT_STAMP`
* **Sources:** [Fundamentals of Perpetual Futures, arXiv 2212.06888](https://arxiv.org/pdf/2212.06888v5) (DOCUMENTED_CLAIM: funding pays long->short in proportion to perp-spot gap; perp deviates from no-arbitrage more than FX); [Cryptocurrency as an Investable Asset Class: Coming of Age, arXiv 2510.14435](https://arxiv.org/pdf/2510.14435) (DOCUMENTED_CLAIM: crypto carry Sharpe 6.45 over 2020-25, 4.06 from 2024, negative in 2025; profit mostly funding)

### P08_SPOT_PERP_BASIS — Spot-perp basis z-score (time-series)  [EXECUTED]
* **Family:** basis
* **Mechanism:** Rich perp vs spot = leveraged long demand -> mean reversion
* **Formula:** b=perp_close/spot_close-1; z=zscore(b,720h); w=-clip(z/2,-1,1)/N; rebalance 12h
* **Required inputs:** perp close, spot close (two markets)
* **Sampling assumptions:** Both bar closes must share a timestamp; USDT vs USD basis contamination
* **Expected horizon:** 12-48h
* **Failure modes:** Stablecoin depeg noise; structural drift of basis; two-feed timestamp skew
* **Lookahead risk:** Two feeds: requires receipt stamps to guarantee both bars were available at decision (audit PASS on aligned archive)
* **Class:** `FORWARD_SAFE_WITH_RECEIPT_STAMP`
* **Sources:** [Fundamentals of Perpetual Futures, arXiv 2212.06888](https://arxiv.org/pdf/2212.06888v5) (DOCUMENTED_CLAIM: funding pays long->short in proportion to perp-spot gap; perp deviates from no-arbitrage more than FX)

### P09_OI_PRICE — OI-confirmed trend / OI-unwind fade  [EXECUTED]
* **Family:** open-interest / price divergence
* **Mechanism:** Rising OI + trend = new positioning follows; falling OI + move = short covering/long liquidation, fades
* **Formula:** w=clip(z24,-1,1)*sign(zscore(dlog OI_24h,720h))/N; rebalance 12h
* **Required inputs:** Binance 5m OI (sum_open_interest, coins) + perp close
* **Sampling assumptions:** OI snapshot treated as available create_time+5min; hourly last obs
* **Expected horizon:** 12h-2d
* **Failure modes:** OI timestamp semantics ambiguous; archive is daily-published, live needs stamped REST/WS capture
* **Lookahead risk:** Conservative +5min availability shift; audit PASS
* **Class:** `FORWARD_SAFE_WITH_RECEIPT_STAMP`
* **Sources:** [Early-warning signals across seven crypto-perpetual liquidation cascades, arXiv 2607.27070](https://arxiv.org/pdf/2607.27070)

### P10_LIQ_FLUSH_PROXY — OI-flush contrarian (liquidation-pressure proxy)  [EXECUTED]
* **Family:** liquidation pressure
* **Mechanism:** Forced liquidations overshoot; price rebounds after flush
* **Formula:** event: |z4|>2.5 and dlog OI_4h < -1.5*sd; w=-sign(R4), hold 4h
* **Required inputs:** Binance 5m OI + perp close (no historical liquidation prints in Binance Vision: liquidationSnapshot returned 404 for 2024)
* **Sampling assumptions:** 1h bars
* **Expected horizon:** 2-6h
* **Failure modes:** Proxy only (not actual liquidation prints); few events; cascade continuation
* **Lookahead risk:** Audit PASS; direct liquidation feed is forward-collect only
* **Class:** `FORWARD_SAFE_WITH_RECEIPT_STAMP`
* **Sources:** [Early-warning signals across seven crypto-perpetual liquidation cascades, arXiv 2607.27070](https://arxiv.org/pdf/2607.27070)

### P11_TAKER_FLOW — Taker-buy imbalance continuation  [EXECUTED]
* **Family:** volume imbalance
* **Mechanism:** Aggressive flow carries information (informed/momentum flow)
* **Formula:** imb=2*taker_buy_quote/quote_vol-1; z of 6h mean (720h); w=clip(z/2,-1,1)/N; rebalance 4h
* **Required inputs:** perp kline taker_buy_quote_volume
* **Sampling assumptions:** 1h bars
* **Expected horizon:** 2-6h
* **Failure modes:** Literature (arXiv 2608.21888) says REVERSAL after imbalance -> sign is pre-registered as continuation; high turnover
* **Lookahead risk:** Bar-close fields only (audit PASS)
* **Class:** `FORWARD_SAFE`
* **Sources:** [Short-horizon mean reversion in crypto: matched cross-market measurement, arXiv 2608.21888](https://arxiv.org/pdf/2608.21888) (DOCUMENTED_CLAIM: reversals concentrate after flow-driven moves, taker-buy imbalance); [Fragmentation, Price Formation and Cross-Impact in Bitcoin Markets, arXiv 2108.09750](https://arxiv.org/pdf/2108.09750)

### P12_ILLIQ_SHOCK — Amihud-type liquidity shock fade  [EXECUTED]
* **Family:** liquidity shocks
* **Mechanism:** Move on thin volume = temporary impact, reverts
* **Formula:** ill=log(|r|+1e-5)-log(quote_vol); z(720h)>1.75 -> w=-sign(r), hold 4h
* **Required inputs:** perp close, quote volume
* **Sampling assumptions:** 1h bars
* **Expected horizon:** 2-6h
* **Failure modes:** Trigger initially mis-specified (z>2 fires 0.014% of bars); threshold reselected on DEV; sparse (4% active)
* **Lookahead risk:** Audit PASS
* **Class:** `FORWARD_SAFE`
* **Sources:** Vendor liquidity research (Kaiko/Amberdata order-book depth; DOCUMENTED_CLAIM, paywalled/aggregated)

### P13_BTC_LEADLAG — BTC->alt 2h catch-up  [EXECUTED]
* **Family:** cross-asset lead/lag
* **Mechanism:** Alts under-react to BTC moves at short lag
* **Formula:** s_alt=clip((z2_BTC - z2_alt)/2,-1,1), BTC not traded; rebalance 2h
* **Required inputs:** perp close x10
* **Sampling assumptions:** 1h bars
* **Expected horizon:** 1-3h
* **Failure modes:** Lag has largely disappeared at hourly resolution; 1500x/yr turnover
* **Lookahead risk:** Audit PASS
* **Class:** `FORWARD_SAFE`
* **Sources:** 'Price Transmission from Bitcoin to Altcoins: High-Frequency Evidence' (DOCUMENTED_CLAIM via search snippet: small caps respond with delay)

### P14_HOUR_SEASON — Hour-of-day seasonality (expanding, walk-forward)  [EXECUTED]
* **Family:** intraday seasonality
* **Mechanism:** Recurring liquidity/session flows (US/Asia open)
* **Formula:** per asset & hour-of-day: expanding mean/(sd/sqrt n) of past same-hour returns (min 90 obs); w=clip(t/2,-1,1)/N; rebalance hourly
* **Required inputs:** perp close
* **Sampling assumptions:** 1h bars
* **Expected horizon:** 1h
* **Failure modes:** Literature: effects time-varying (UWA); turnover ~4400x/yr
* **Lookahead risk:** Expanding estimate excludes current obs; boundary check passes
* **Class:** `FORWARD_SAFE`
* **Sources:** [Bitcoin Time-of-Day, Day-of-Week and Month-of-Year Effects, UWA](https://research-repository.uwa.edu.au/en/publications/bitcoin-time-of-day-day-of-week-and-month-of-year-effects-in-retu/) (DOCUMENTED_CLAIM: effects are time-varying, no persistent pattern); [Quantpedia: Intraday seasonality in Bitcoin](https://quantpedia.com/strategies/intraday-seasonality-in-bitcoin) (DOCUMENTED_CLAIM: 21-23h UTC)

### P15_RV_IV_VRP — DVOL minus realised vol (BTC/ETH only)  [EXECUTED]
* **Family:** realized vs implied volatility
* **Mechanism:** IV-RV spread proxies risk premium / fear; pre-registered sign: long when IV rich
* **Formula:** vrp=DVOL-100*sigma_168h*sqrt(8760); z(720h); w=clip(z,-1,1)/2 on BTC,ETH; rebalance 24h
* **Required inputs:** Deribit DVOL hourly + perp close
* **Sampling assumptions:** DVOL candle usable 1h after start
* **Expected horizon:** 1-3d
* **Failure modes:** Only 2 assets; single-tenor index; sign ambiguous
* **Lookahead risk:** DVOL index may be recomputed by venue; stamp needed
* **Class:** `FORWARD_SAFE_WITH_RECEIPT_STAMP`
* **Sources:** [The Bitcoin VIX and its variance risk premium (Sussex)](https://sro.sussex.ac.uk/id/eprint/91094/); [Risk Premia in the Bitcoin Market, arXiv 2410.15195](https://arxiv.org/html/2410.15195v2) (DOCUMENTED_CLAIM: VRP regime-dependent)

## Discovered, not executed
### D01 — Intraday first-half-hour -> last-half-hour momentum  [discovered, not executed]
* **Family:** momentum / trend
* **Mechanism:** Liquidity provision at session boundaries
* **Formula:** r_first30 predicts r_last30 (session-defined)
* **Required inputs:** 30m bars, session definition
* **Sampling assumptions:** 24/7 market has no natural session
* **Expected horizon:** 30m
* **Failure modes:** Session definition arbitrary in crypto; 30m bars not fetched
* **Lookahead risk:** None if session fixed a priori
* **Class:** `FORWARD_SAFE`
* **Sources:** [Bitcoin intraday time series momentum, Univ. Birmingham](https://research.birmingham.ac.uk/en/publications/bitcoin-intraday-time-series-momentum/) (DOCUMENTED_CLAIM: first half-hour predicts last half-hour; liquidity-provision driven)

### D02 — Quarter-hour order-imbalance effect  [discovered, not executed]
* **Family:** volume imbalance
* **Mechanism:** Periodic algo activity at :00/:15/:30/:45
* **Formula:** imbalance at quarter-hour open -> 4-12h return
* **Required inputs:** Binance aggTrades tick data
* **Sampling assumptions:** tick
* **Expected horizon:** 4-12h
* **Failure modes:** Tick volume (TB-scale) beyond this study; claim from 2026 preprint not independently checked
* **Lookahead risk:** Trade timestamps only
* **Class:** `FORWARD_SAFE`
* **Sources:** [The Quarter-Hour Effect, arXiv 2607.09426](https://arxiv.org/pdf/2607.09426) (DOCUMENTED_CLAIM: imbalance at quarter-hour openings forecasts 4-12h returns, Binance perps)

### D03 — Flow-conditioned short-horizon reversal  [discovered, not executed]
* **Family:** mean reversion
* **Mechanism:** Reversal concentrated after taker-imbalance moves
* **Formula:** reversal x |imbalance| interaction
* **Required inputs:** 1h/5m klines with taker fields
* **Sampling assumptions:** 1h
* **Expected horizon:** 1-6h
* **Failure modes:** Largely spanned by P03/P11 (rho -0.55) at hourly res
* **Lookahead risk:** None
* **Class:** `FORWARD_SAFE`
* **Sources:** [Short-horizon mean reversion in crypto: matched cross-market measurement, arXiv 2608.21888](https://arxiv.org/pdf/2608.21888) (DOCUMENTED_CLAIM: reversals concentrate after flow-driven moves, taker-buy imbalance)

### D04 — Liquidation-cascade early-warning signals  [discovered, not executed]
* **Family:** liquidation pressure
* **Mechanism:** Critical-slowing-down style precursors before cascades
* **Formula:** rolling variance/autocorr of returns + leverage/order flow
* **Required inputs:** 1m price, 5m leverage
* **Sampling assumptions:** 1m/5m
* **Expected horizon:** minutes-hours
* **Failure modes:** Only ~7 major events: no statistical power; retro-fitted
* **Lookahead risk:** Event windows selected ex post -> LOOKAHEAD_RISK if used for calibration
* **Class:** `LOOKAHEAD_RISK`
* **Sources:** [Early-warning signals across seven crypto-perpetual liquidation cascades, arXiv 2607.27070](https://arxiv.org/pdf/2607.27070)

### D05 — Direct liquidation-print imbalance (forceOrder / OKX liquidation-orders)  [discovered, not executed]
* **Family:** liquidation pressure
* **Mechanism:** Forced flow pressure
* **Formula:** signed liquidation notional / OI
* **Required inputs:** Binance forceOrder WS, OKX liquidation-orders REST (recent only)
* **Sampling assumptions:** event
* **Expected horizon:** minutes-hours
* **Failure modes:** No historical archive found (Binance Vision 404); forward collection required
* **Lookahead risk:** Receipt-stamped live capture is safe; retro reconstructions are not
* **Class:** `FORWARD_SAFE_WITH_RECEIPT_STAMP`
* **Sources:** [Early-warning signals across seven crypto-perpetual liquidation cascades, arXiv 2607.27070](https://arxiv.org/pdf/2607.27070)

### D06 — Options IV term-structure slope (1w vs 3m)  [discovered, not executed]
* **Family:** term structure
* **Mechanism:** Backwardation signals stress
* **Formula:** IV_1w - IV_3m
* **Required inputs:** Deribit option chains, PIT surface
* **Sampling assumptions:** tick/15m
* **Expected horizon:** 1-7d
* **Failure modes:** No public point-in-time historical surface; DVOL is single tenor
* **Lookahead risk:** Reconstructing from EOD/reprocessed data is OFFLINE_ONLY
* **Class:** `OFFLINE_ONLY`
* **Sources:** [The Bitcoin VIX and its variance risk premium (Sussex)](https://sro.sussex.ac.uk/id/eprint/91094/); [Risk Premia in the Bitcoin Market, arXiv 2410.15195](https://arxiv.org/html/2410.15195v2) (DOCUMENTED_CLAIM: VRP regime-dependent)

### D07 — 25-delta risk reversal / skew  [discovered, not executed]
* **Family:** realized vs implied volatility
* **Mechanism:** Skew prices crash demand
* **Formula:** IV(25dP)-IV(25dC)
* **Required inputs:** Deribit chains
* **Sampling assumptions:** 15m
* **Expected horizon:** 1-7d
* **Failure modes:** Same PIT limitation as D06
* **Lookahead risk:** OFFLINE_ONLY
* **Class:** `OFFLINE_ONLY`
* **Sources:** [The Bitcoin VIX and its variance risk premium (Sussex)](https://sro.sussex.ac.uk/id/eprint/91094/); [Risk Premia in the Bitcoin Market, arXiv 2410.15195](https://arxiv.org/html/2410.15195v2) (DOCUMENTED_CLAIM: VRP regime-dependent)

### D08 — Dealer gamma exposure (GEX)  [discovered, not executed]
* **Family:** regime-conditioned signals
* **Mechanism:** Dealer hedging dampens/amplifies vol
* **Formula:** sum gamma*OI by strike
* **Required inputs:** Deribit OI by strike history
* **Sampling assumptions:** daily/15m
* **Expected horizon:** 1-3d
* **Failure modes:** No PIT public archive; model assumptions on dealer side
* **Lookahead risk:** OFFLINE_ONLY
* **Class:** `OFFLINE_ONLY`
* **Sources:** [The Bitcoin VIX and its variance risk premium (Sussex)](https://sro.sussex.ac.uk/id/eprint/91094/); [Risk Premia in the Bitcoin Market, arXiv 2410.15195](https://arxiv.org/html/2410.15195v2) (DOCUMENTED_CLAIM: VRP regime-dependent)

### D09 — Dated-futures annualised basis (quarterlies)  [discovered, not executed]
* **Family:** basis
* **Mechanism:** Cost-of-carry / leverage demand
* **Formula:** (F-S)/S*365/T
* **Required inputs:** Binance delivery klines, Deribit futures
* **Sampling assumptions:** 1h
* **Expected horizon:** weeks
* **Failure modes:** Data present but not built; P07 covers perp analogue; carry Sharpe reported to fall/turn negative in 2025 (arXiv 2510.14435)
* **Lookahead risk:** None
* **Class:** `FORWARD_SAFE`
* **Sources:** [Cryptocurrency as an Investable Asset Class: Coming of Age, arXiv 2510.14435](https://arxiv.org/pdf/2510.14435) (DOCUMENTED_CLAIM: crypto carry Sharpe 6.45 over 2020-25, 4.06 from 2024, negative in 2025; profit mostly funding)

### D10 — Premium-index-implied next funding forecast  [discovered, not executed]
* **Family:** funding divergence
* **Mechanism:** Next funding is predictable from live premium
* **Formula:** TWAP premium over window -> predicted funding
* **Required inputs:** Binance premiumIndexKlines (in hand), fundingInfo
* **Sampling assumptions:** 1h/1m
* **Expected horizon:** 8h
* **Failure modes:** Nearly identical information to P06/P08
* **Lookahead risk:** None
* **Class:** `FORWARD_SAFE`
* **Sources:** [Designing funding rates for perpetual futures, arXiv 2506.08573](https://arxiv.org/pdf/2506.08573)

### D11 — Top-trader long/short ratio contrarian  [discovered, not executed]
* **Family:** funding divergence
* **Mechanism:** Retail crowding vs top-trader positioning
* **Formula:** count_toptrader_long_short_ratio
* **Required inputs:** Binance metrics (in hand)
* **Sampling assumptions:** 5m
* **Expected horizon:** 1-3d
* **Failure modes:** Definition changes; account-level, not notional
* **Lookahead risk:** Vision 5m stamp semantics
* **Class:** `FORWARD_SAFE_WITH_RECEIPT_STAMP`
* **Sources:** [Early-warning signals across seven crypto-perpetual liquidation cascades, arXiv 2607.27070](https://arxiv.org/pdf/2607.27070)

### D12 — Coinbase-Binance spot premium  [discovered, not executed]
* **Family:** cross-asset lead/lag
* **Mechanism:** US vs global flow
* **Formula:** cb_close/binance_close-1
* **Required inputs:** Coinbase, Binance spot
* **Sampling assumptions:** 1h
* **Expected horizon:** hours
* **Failure modes:** USD vs USDT basis contaminates
* **Lookahead risk:** None
* **Class:** `FORWARD_SAFE_WITH_RECEIPT_STAMP`
* **Sources:** [Fragmentation, Price Formation and Cross-Impact in Bitcoin Markets, arXiv 2108.09750](https://arxiv.org/pdf/2108.09750)

### D13 — Cross-venue funding spread (HL vs Binance)  [discovered, not executed]
* **Family:** funding divergence
* **Mechanism:** Funding arbitrage pressure
* **Formula:** f_HL - f_Binance
* **Required inputs:** Hyperliquid fundingHistory, Binance
* **Sampling assumptions:** 1h/8h
* **Expected horizon:** 1-3d
* **Failure modes:** HL hourly vs Binance 8h; used only as cross-check in 09
* **Lookahead risk:** Stamps
* **Class:** `FORWARD_SAFE_WITH_RECEIPT_STAMP`
* **Sources:** [Fragmentation, Price Formation and Cross-Impact in Bitcoin Markets, arXiv 2108.09750](https://arxiv.org/pdf/2108.09750)

### D14 — Volatility-managed sizing (inverse realised vol)  [discovered, not executed]
* **Family:** volatility compression / expansion
* **Mechanism:** Vol clusters; risk targeting
* **Formula:** w=target/sigma_hat
* **Required inputs:** perp close
* **Sampling assumptions:** 1h
* **Expected horizon:** n/a
* **Failure modes:** Sizing overlay, not a return primitive
* **Lookahead risk:** Trailing only
* **Class:** `FORWARD_SAFE`
* **Sources:** [The Bitcoin VIX and its variance risk premium (Sussex)](https://sro.sussex.ac.uk/id/eprint/91094/); [Risk Premia in the Bitcoin Market, arXiv 2410.15195](https://arxiv.org/html/2410.15195v2) (DOCUMENTED_CLAIM: VRP regime-dependent)

### D15 — HAR realised-variance forecast / jump & semi-variance  [discovered, not executed]
* **Family:** volatility compression / expansion
* **Mechanism:** Long memory of RV
* **Formula:** HAR-RV regression
* **Required inputs:** 5m returns
* **Sampling assumptions:** 5m
* **Expected horizon:** 1-5d
* **Failure modes:** Requires 5m bars, walk-forward refit
* **Lookahead risk:** Refit must be expanding; in-sample fit is LOOKAHEAD_RISK
* **Class:** `FORWARD_SAFE`
* **Sources:** [The Bitcoin VIX and its variance risk premium (Sussex)](https://sro.sussex.ac.uk/id/eprint/91094/); [Risk Premia in the Bitcoin Market, arXiv 2410.15195](https://arxiv.org/html/2410.15195v2) (DOCUMENTED_CLAIM: VRP regime-dependent)

### D16 — Efficiency-ratio / ADX gated trend  [discovered, not executed]
* **Family:** regime-conditioned signals
* **Mechanism:** Trend works only in directional regimes
* **Formula:** KER_72h gate on TSMOM
* **Required inputs:** perp close
* **Sampling assumptions:** 1h
* **Expected horizon:** 1-5d
* **Failure modes:** Variant of P01 (would be redundant); regime conditioning evaluated across all primitives in 07
* **Lookahead risk:** None
* **Class:** `FORWARD_SAFE`
* **Sources:** [TS and CS momentum in crypto (AUT ACFR working paper)](https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf) (DOCUMENTED_CLAIM: TS momentum strong, CS weak, many CS portfolios insignificant after costs); [Momentum Trading in Cryptocurrencies, BATP 44540](https://www.journals.vu.lt/BATP/article/view/44540)

### D17 — HMM / Markov-switching regimes (smoothed)  [discovered, not executed]
* **Family:** regime-conditioned signals
* **Mechanism:** Latent vol/trend regimes
* **Formula:** Kim smoother posteriors
* **Required inputs:** returns
* **Sampling assumptions:** 1h/1d
* **Expected horizon:** days
* **Failure modes:** Smoothed posteriors use future data
* **Lookahead risk:** Smoothed = LOOKAHEAD_RISK; filtered = FORWARD_SAFE
* **Class:** `LOOKAHEAD_RISK`
* **Sources:** [The Bitcoin VIX and its variance risk premium (Sussex)](https://sro.sussex.ac.uk/id/eprint/91094/); [Risk Premia in the Bitcoin Market, arXiv 2410.15195](https://arxiv.org/html/2410.15195v2) (DOCUMENTED_CLAIM: VRP regime-dependent)

### D18 — Centered MA / HP filter / wavelet / Savitzky-Golay denoising  [discovered, not executed]
* **Family:** momentum / trend
* **Mechanism:** Denoised trend
* **Formula:** two-sided filter
* **Required inputs:** close
* **Sampling assumptions:** any
* **Expected horizon:** any
* **Failure modes:** Two-sided filters use future bars: end-point behaviour differs from history
* **Lookahead risk:** Centered filter = LOOKAHEAD_RISK (banned by mission)
* **Class:** `LOOKAHEAD_RISK`
* **Sources:** OSS: Qlib Alpha158 feature set, freqtrade/FreqAI, vectorbt (DOCUMENTED_CLAIM from web search only; source code NOT inspected in this study)

### D19 — Full-sample z-score / quantile transform / PCA  [discovered, not executed]
* **Family:** cross-sectional relative strength
* **Mechanism:** Feature standardisation
* **Formula:** (x-mu_all)/sd_all
* **Required inputs:** any
* **Sampling assumptions:** any
* **Expected horizon:** any
* **Failure modes:** Uses future distribution
* **Lookahead risk:** Future-normalised = LOOKAHEAD_RISK (banned)
* **Class:** `LOOKAHEAD_RISK`
* **Sources:** OSS: Qlib Alpha158 feature set, freqtrade/FreqAI, vectorbt (DOCUMENTED_CLAIM from web search only; source code NOT inspected in this study)

### D20 — Macro surprise (actual-consensus) with revised history  [discovered, not executed]
* **Family:** event-driven macro reactions
* **Mechanism:** Surprise moves rates/risk appetite
* **Formula:** z(actual - consensus)
* **Required inputs:** FRED/ALFRED, calendars
* **Sampling assumptions:** event
* **Expected horizon:** minutes-hours
* **Failure modes:** Revised actuals / restated consensus
* **Lookahead risk:** Revised values = LOOKAHEAD_RISK; first-release vintage with receipt stamp = FORWARD_SAFE_WITH_RECEIPT_STAMP
* **Class:** `LOOKAHEAD_RISK`
* **Sources:** INFERENCE (no citable source found)

### D21 — Scheduled-event vol drift (FOMC/CPI timestamps)  [discovered, not executed]
* **Family:** event-driven macro reactions
* **Mechanism:** Pre-event vol compression, post-event expansion
* **Formula:** event-time bars
* **Required inputs:** Public release calendars
* **Sampling assumptions:** event
* **Expected horizon:** 1-24h
* **Failure modes:** ~24 FOMC + ~32 CPI events in sample: no power after multiplicity correction
* **Lookahead risk:** Schedule is known ahead: safe if calendar captured before event
* **Class:** `FORWARD_SAFE_WITH_RECEIPT_STAMP`
* **Sources:** INFERENCE (no citable source found)

### D22 — Overnight/weekend & day-of-week effects  [discovered, not executed]
* **Family:** intraday seasonality
* **Mechanism:** Traditional-market closure liquidity
* **Formula:** DOW/weekend dummy expanding mean
* **Required inputs:** perp close
* **Sampling assumptions:** 1h
* **Expected horizon:** 1d
* **Failure modes:** Time-varying (UWA); partly covered by P14
* **Lookahead risk:** Expanding only
* **Class:** `FORWARD_SAFE`
* **Sources:** [Bitcoin Time-of-Day, Day-of-Week and Month-of-Year Effects, UWA](https://research-repository.uwa.edu.au/en/publications/bitcoin-time-of-day-day-of-week-and-month-of-year-effects-in-retu/) (DOCUMENTED_CLAIM: effects are time-varying, no persistent pattern); [Quantpedia: Intraday seasonality in Bitcoin](https://quantpedia.com/strategies/intraday-seasonality-in-bitcoin) (DOCUMENTED_CLAIM: 21-23h UTC)

### D23 — Order-book imbalance / microprice / depth  [discovered, not executed]
* **Family:** liquidity shocks
* **Mechanism:** Queue imbalance predicts next tick
* **Formula:** (bid_depth-ask_depth)/(sum)
* **Required inputs:** L2 book stream
* **Sampling assumptions:** tick
* **Expected horizon:** seconds-minutes
* **Failure modes:** HFT-scale, no free historical archive; outside intraday mandate
* **Lookahead risk:** Live-only capture
* **Class:** `FORWARD_SAFE_WITH_RECEIPT_STAMP`
* **Sources:** Vendor liquidity research (Kaiko/Amberdata order-book depth; DOCUMENTED_CLAIM, paywalled/aggregated)

### D24 — VPIN / flow toxicity  [discovered, not executed]
* **Family:** volume imbalance
* **Mechanism:** Toxic flow precedes vol
* **Formula:** volume-bucket order imbalance
* **Required inputs:** trades
* **Sampling assumptions:** volume time
* **Expected horizon:** hours
* **Failure modes:** Trade data + bucketing choices; spanned partly by P11
* **Lookahead risk:** Trailing
* **Class:** `FORWARD_SAFE`
* **Sources:** [Fragmentation, Price Formation and Cross-Impact in Bitcoin Markets, arXiv 2108.09750](https://arxiv.org/pdf/2108.09750)

### D25 — Cross-sectional idiosyncratic-vol / low-risk anomaly  [discovered, not executed]
* **Family:** cross-sectional relative strength
* **Mechanism:** Lottery preference
* **Formula:** rank(-idio vol)
* **Required inputs:** daily bars
* **Sampling assumptions:** 1d
* **Expected horizon:** weeks
* **Failure modes:** Daily horizon; not intraday
* **Lookahead risk:** Trailing
* **Class:** `FORWARD_SAFE`
* **Sources:** [TS and CS momentum in crypto (AUT ACFR working paper)](https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf) (DOCUMENTED_CLAIM: TS momentum strong, CS weak, many CS portfolios insignificant after costs); [Momentum Trading in Cryptocurrencies, BATP 44540](https://www.journals.vu.lt/BATP/article/view/44540)

### D26 — Stablecoin supply / exchange netflow / on-chain  [discovered, not executed]
* **Family:** event-driven macro reactions
* **Mechanism:** Liquidity injection
* **Formula:** netflow z
* **Required inputs:** vendor on-chain
* **Sampling assumptions:** daily
* **Expected horizon:** days
* **Failure modes:** Vendor-restated history, PIT unknown; excluded
* **Lookahead risk:** Restated = LOOKAHEAD_RISK
* **Class:** `LOOKAHEAD_RISK`
* **Sources:** INFERENCE (no citable source found)

### D27 — Social/search sentiment  [discovered, not executed]
* **Family:** event-driven macro reactions
* **Mechanism:** Attention
* **Formula:** index
* **Required inputs:** vendor
* **Sampling assumptions:** daily
* **Expected horizon:** days
* **Failure modes:** Revised/opaque, non-market data
* **Lookahead risk:** Revision risk
* **Class:** `LOOKAHEAD_RISK`
* **Sources:** INFERENCE (no citable source found)

### D28 — Perp/spot volume dominance ratio  [discovered, not executed]
* **Family:** volume imbalance
* **Mechanism:** Derivatives-driven regimes
* **Formula:** perp_vol/spot_vol z
* **Required inputs:** perp+spot klines (in hand)
* **Sampling assumptions:** 1h
* **Expected horizon:** hours-days
* **Failure modes:** Not executed (budget)
* **Lookahead risk:** None
* **Class:** `FORWARD_SAFE`
* **Sources:** [Fundamentals of Perpetual Futures, arXiv 2212.06888](https://arxiv.org/pdf/2212.06888v5) (DOCUMENTED_CLAIM: funding pays long->short in proportion to perp-spot gap; perp deviates from no-arbitrage more than FX)
