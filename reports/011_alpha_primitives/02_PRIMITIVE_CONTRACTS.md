# 02 — Primitive contracts (PRE-DECLARED)

Status: written and committed **before** the full 10-asset results were produced. A 3-asset (BTC/ETH/SOL) smoke run of the pipeline was seen beforehand (disclosed in 11_LIMITATIONS); no signal definition, sign, horizon, mode or threshold was changed after it.

Every primitive fixes, ex ante: sign (direction), primary mode (TS = per-asset sized, CS = dollar-neutral cross-sectional), primary horizon H, and all parameters. Secondary horizon/mode are reported but **adjudication uses the primary spec only** (15 tests ⇒ Benjamini–Hochberg over 15).

## Common conventions

- Rows are 1h bars labelled by open time; row t is known at t+1h (decision instant). Fill at next open (delay 0); +1/+2 bar delay tested in falsification.
- Portfolio: 1/H of the book re-formed every hour and held H hours (overlapping tranches), TS weight = clip(s/std₇₂₀(s),±1)/N (gross ≤ 1), CS weight = demeaned clipped z, gross 1, dollar-neutral, ≥60% of universe valid.
- Universe (core): BTC ETH SOL XRP BNB DOGE ADA LINK AVAX LTC (Binance USD-M perps). Holdout universe for the different-asset test: DOT ATOM NEAR TRX BCH ETC.
- Splits: DEV 2023-01→2024-12, TEST 2025-01→2026-08 (2022-10→2022-12 warm-up only). No parameter is fitted on either split; both are out-of-sample with respect to fitting, but the *design* was made with knowledge of published literature (see 11).
- Costs per side (bps, generic, NOT venue-verified): BTC/ETH 6, other core 8, holdout 10 (≈5 taker fee + 1/3/5 half-spread/slippage). Stress ×2/×3/×5; ×0.5 shown only as an optimistic bound. **Unknown costs (market impact, fee tiers, borrow, latency slippage) are not zero** — they are what the multipliers stand in for. Funding paid/received is charged from real funding data and included in *net*.
- gross = price P&L only. net = gross − trading cost − funding.

## Adjudication rules (pre-declared)

- C1 forward-safety: truncation test PASS (bench/…/lookahead_test.py).
- C2 net Sharpe > 0 in both DEV and TEST at 1× cost.
- C3 FULL-sample net Newey–West t ≥ 2.0 **and** BH-q < 0.10 across the 15 primary tests.
- C5 net Sharpe > 0 at 2× cost. C6 ≥70% of applicable falsification checks passed (delay+1, parameter perturbation min>0, missing-25%, stale-25%, holdout assets gross>0, Coinbase-signal venue gross>0).
- Tier: SUPPORTED_ROBUST = C1∧C2∧C3∧C5∧C6; SUPPORTED_FRAGILE = C1∧C2∧C3 only; GROSS_ONLY = gross t ≥ 2 but not net; else NOT_SUPPORTED.
- Non-redundant = supported primitive whose |signal-rank corr| and |gross daily-P&L corr| < 0.5 versus every higher-ranked supported primitive.
- Regime-dependent = net t ≤ −1.5 in one and ≥ +1.5 in the opposite bucket (vol low/high or trend up/down), or t ≥ 2.5 in a bucket while FULL net t < 2.
- FINAL_VERDICT: MULTIPLE (≥3 SUPPORTED_ROBUST non-redundant), LIMITED (1–2 SUPPORTED_ROBUST or SUPPORTED_FRAGILE non-redundant), NO_ROBUST (none), INCONCLUSIVE (data/pipeline failure or placebo test shows pipeline cannot separate signal from noise).

## Executed primitives

### P01_TSMOM — momentum/trend

- **Mechanism**: Under-reaction / herding: past vol-scaled return persists (time-series momentum).
- **Formula**: s = ½·[r24/(σ·√24) + r72/(σ·√72)], r_n = ln(C_t/C_{t-n}), σ = 720h rolling std of 1h log returns. w = clip(s/std_720(s),±1)/N.
- **Required inputs**: Perp 1h close
- **Sampling**: 1h bars; decision at bar close
- **Horizon**: 24h primary, 4h secondary
- **Pre-declared**: sign `+ continuation`; primary mode **TS**, primary H **24h** (secondary 4h)
- **Failure modes**: Trend reversals (V-shapes), chop regimes, momentum crashes after sharp drawdowns.
- **Lookahead risks / controls**: Only closed-bar closes ≤ t; σ trailing. No centered filter.
- **Forward-safety class**: `FORWARD_SAFE`
- **Literature basis**: S1,S2c (landscape B); DOCUMENTED_CLAIM only

### P02_XS_RS7D — cross-sectional relative strength

- **Mechanism**: Cross-sectional relative strength: winners over 7d keep outperforming within a liquid basket.
- **Formula**: s = ln(C_t/C_{t-168})/(σ√168); dollar-neutral: CS-demeaned clipped z, gross 1.
- **Required inputs**: Perp 1h close, 10 assets
- **Sampling**: 1h, 24h hold
- **Horizon**: 24h primary, 4h secondary
- **Pre-declared**: sign `+ winners keep winning`; primary mode **CS**, primary H **24h** (secondary 4h)
- **Failure modes**: Basket dominated by one factor (BTC beta); sector rotations; only 10 assets (thin cross-section).
- **Lookahead risks / controls**: Universe fixed ex ante (no survivorship filter by future liquidity) — 10 majors alive throughout, so survivorship bias exists (assets chosen with hindsight of being liquid in 2026).
- **Forward-safety class**: `FORWARD_SAFE`
- **Literature basis**: S1,S3 (landscape B)

### P03_REV4H — mean reversion

- **Mechanism**: Liquidity-provision / overreaction: 1–4h moves partly reverse.
- **Formula**: s = −ln(C_t/C_{t-4})/(σ√4). TS mode.
- **Required inputs**: Perp 1h close
- **Sampling**: 1h, 4h hold
- **Horizon**: 4h primary, 24h secondary
- **Pre-declared**: sign `- fade 4h move`; primary mode **TS**, primary H **4h** (secondary 24h)
- **Failure modes**: Trending regimes; turnover ≫ edge (cost-dominated); larger coins show momentum not reversal.
- **Lookahead risks / controls**: Bar t closed before decision; no partial bar.
- **Forward-safety class**: `FORWARD_SAFE`
- **Literature basis**: S3,S4 (landscape B)

### P04_VOLCOMP_BRK — vol compression -> expansion + breakout

- **Mechanism**: Vol compression → expansion: breakout after low realised range resolves directionally.
- **Formula**: comp_t = [mean_24(PK)/mean_720(PK)]_{t-1} < 0.7 (Parkinson variance); s = 1[C_t>max H_{t-48..t-1}] − 1[C_t<min L_{t-48..t-1}] if comp else 0.
- **Required inputs**: Perp 1h OHLC
- **Sampling**: 1h
- **Horizon**: 24h primary, 4h secondary
- **Pre-declared**: sign `+ breakout direction after compression`; primary mode **TS**, primary H **24h** (secondary 4h)
- **Failure modes**: False breakouts, sparse signal (few trades → low power), gap-like moves.
- **Lookahead risks / controls**: Donchian and compression windows shifted by one bar (exclude current bar); no in-progress-bar squeeze.
- **Forward-safety class**: `FORWARD_SAFE`
- **Literature basis**: generic (no verified academic source; landscape A gap)

### P05_BRK_PERSIST — breakout persistence (baseline)

- **Mechanism**: Breakout persistence baseline: position within 48h Donchian range, continuous.
- **Formula**: s = (C_t − minL_48)/(maxH_48 − minL_48) − ½.
- **Required inputs**: Perp 1h OHLC
- **Sampling**: 1h
- **Horizon**: 24h primary, 4h secondary
- **Pre-declared**: sign `+ position in 48h Donchian range`; primary mode **TS**, primary H **24h** (secondary 4h)
- **Failure modes**: Range-bound markets; overlaps P01 by construction (baseline for redundancy).
- **Lookahead risks / controls**: Window includes bar t (closed) only.
- **Forward-safety class**: `FORWARD_SAFE`
- **Literature basis**: generic

### P06_FUND_CARRY — carry / funding

- **Mechanism**: Carry: perp longs pay funding when leverage demand is high; short crowded / long uncrowded earns carry and fades crowding.
- **Formula**: s = −mean_72h(f_ph), f_ph = last settled funding / interval_h (per-hour), ffilled from settlement stamp. CS mode, dollar-neutral.
- **Required inputs**: Binance USD-M funding history
- **Sampling**: 8h (some assets 4h) settlement, ffilled hourly
- **Horizon**: 24h primary, 4h secondary
- **Pre-declared**: sign `- short high-funding, long low-funding (receive carry)`; primary mode **CS**, primary H **24h** (secondary 4h)
- **Failure modes**: Funding regime shifts; funding can stay extreme; delta-one carry needs spot leg (not modelled — this is a directional CS perp book).
- **Lookahead risks / controls**: Uses settled funding only (never predicted); stamp = calc time floored to hour → visible next decision. Real-time receipt latency not in archive.
- **Forward-safety class**: `FORWARD_SAFE_WITH_RECEIPT_STAMP`
- **Literature basis**: S1,S5 (landscape A/B)

### P07_PREMIUM — basis (perp premium index)

- **Mechanism**: Basis: perp premium over index reflects leveraged demand; large positive deviations mean-revert.
- **Formula**: s = −(mean_4(prem) − mean_720(prem)), prem = Binance premium-index kline close.
- **Required inputs**: Binance premium index klines
- **Sampling**: 1h
- **Horizon**: 4h primary, 24h secondary
- **Pre-declared**: sign `- fade premium deviation`; primary mode **TS**, primary H **4h** (secondary 24h)
- **Failure modes**: Premium is small vs. costs; structural drift; correlated with P03.
- **Lookahead risks / controls**: Exchange-derived index; archive gives no receipt time; bar closed.
- **Forward-safety class**: `FORWARD_SAFE_WITH_RECEIPT_STAMP`
- **Literature basis**: S5 (landscape A)

### P08_OI_PRICE — open-interest / price divergence

- **Mechanism**: OI–price divergence: OI rising with the move = new leveraged positions confirm trend; OI falling = short-covering.
- **Formula**: s = sign(r24)·ΔlnOI_24/(σ_OI·√24) with OI = coin-denominated open interest, lagged +1h.
- **Required inputs**: Binance metrics (5-min OI snapshots) → hourly last, lagged 1 bar
- **Sampling**: 5-min → 1h
- **Horizon**: 24h primary, 4h secondary
- **Pre-declared**: sign `+ OI rising with move confirms it`; primary mode **TS**, primary H **24h** (secondary 4h)
- **Failure modes**: OI notional vs contracts confusion; venue OI is one venue only; snapshot stamp semantics unverified.
- **Lookahead risks / controls**: Extra 1-bar receipt lag applied to compensate unknown publication delay of bulk metrics.
- **Forward-safety class**: `FORWARD_SAFE_WITH_RECEIPT_STAMP`
- **Literature basis**: S4,S7,S9 (landscape A); no verified predictive source (gap)

### P09_OI_FLUSH — liquidation pressure (OI-flush proxy)

- **Mechanism**: Liquidation-pressure proxy: sharp OI collapse alongside a large move indicates forced closing that overshoots; fade it.
- **Formula**: big_t = |r6|/(σ√6)>1.5; s = −sign(r6)·max(0, −z_ΔOI6 − 1) if big else 0.
- **Required inputs**: Binance OI metrics + closes
- **Sampling**: 1h
- **Horizon**: 4h primary, 24h secondary
- **Pre-declared**: sign `- fade price move accompanied by OI collapse`; primary mode **TS**, primary H **4h** (secondary 24h)
- **Failure modes**: Proxy only (true liquidation tape not available historically); rare events → low power; cascades can continue.
- **Lookahead risks / controls**: OI lagged 1 bar; thresholds fixed ex ante.
- **Forward-safety class**: `FORWARD_SAFE_WITH_RECEIPT_STAMP`
- **Literature basis**: S9,S10 (landscape A)

### P10_TAKER_IMB — volume imbalance (taker flow)

- **Mechanism**: Order-flow persistence: net aggressive buying predicts near-term continuation (price impact of signed flow).
- **Formula**: s = Σ_4h(2·TBQ − QV)/Σ_4h QV (taker-buy quote volume from kline).
- **Required inputs**: Perp 1h kline taker-buy volume
- **Sampling**: 1h
- **Horizon**: 4h primary, 24h secondary
- **Pre-declared**: sign `+ flow persistence`; primary mode **TS**, primary H **4h** (secondary 24h)
- **Failure modes**: Flow already in price by bar close; high turnover.
- **Lookahead risks / controls**: Kline volumes are final at close.
- **Forward-safety class**: `FORWARD_SAFE`
- **Literature basis**: S12,S13,S14 (landscape A)

### P11_LIQ_SHOCK — liquidity shock (volume z>1.5)

- **Mechanism**: Liquidity shock: on abnormal volume (z>1.5) the concurrent 1h move contains liquidity-driven overshoot.
- **Formula**: s = −r1/σ if z(ln QV; 168h) > 1.5 else 0.
- **Required inputs**: Perp 1h close, quote volume
- **Sampling**: 1h
- **Horizon**: 4h primary, 24h secondary
- **Pre-declared**: sign `- fade 1h move on volume shock`; primary mode **TS**, primary H **4h** (secondary 24h)
- **Failure modes**: Volume shocks are often informed (news) → continuation, not reversal; sparse.
- **Lookahead risks / controls**: z uses trailing window incl. current closed bar.
- **Forward-safety class**: `FORWARD_SAFE`
- **Literature basis**: S16,S17 (landscape A)

### P12_LEADLAG_BTC — cross-asset lead/lag

- **Mechanism**: Cross-asset lead/lag: alts under-react to BTC moves over 1–4h.
- **Formula**: s_a = (β_a·r^{BTC}_2h − r^a_2h)/(σ√2), β = 720h rolling OLS beta; BTC excluded from the book. CS mode on 9 alts.
- **Required inputs**: Perp 1h closes
- **Sampling**: 1h
- **Horizon**: 4h primary, 24h secondary
- **Pre-declared**: sign `+ alt catches up to beta*BTC 2h move`; primary mode **CS**, primary H **4h** (secondary 24h)
- **Failure modes**: Alt beta instability, execution latency ≥ effect duration (often minutes), cost-dominated at 1h.
- **Lookahead risks / controls**: β uses returns ≤ t only.
- **Forward-safety class**: `FORWARD_SAFE`
- **Literature basis**: S10,S11 (landscape B)

### P13_SEASON_HOD — intraday seasonality

- **Mechanism**: Intraday seasonality (hour-of-day): trailing same-hour mean returns.
- **Formula**: s = Σ_{j=1..H} (1/60)Σ_{i=1..60} r_{t+j−24i}, all indices ≤ t.
- **Required inputs**: Perp 1h close
- **Sampling**: 1h, UTC hours
- **Horizon**: 4h primary, 24h secondary
- **Pre-declared**: sign `+ trailing same-hour mean return`; primary mode **TS**, primary H **4h** (secondary 24h)
- **Failure modes**: Effect instability (documented contradiction S14 vs S16); data-snooping if hour chosen ex post (not done here).
- **Lookahead risks / controls**: Trailing 60-day same-hour means only; verified by truncation test.
- **Forward-safety class**: `FORWARD_SAFE`
- **Literature basis**: S14,S15,S16 (landscape B)

### P14_VRP_DVOL — realized vs implied vol

- **Mechanism**: Realized vs implied vol: implied above realised (vs own trailing mean) = compensated risk-bearing.
- **Formula**: s = [DVOL_{t-1} − RV_168h(t)] − mean_2160(same); RV=std of 1h log returns·√8760·100. BTC & ETH only.
- **Required inputs**: Deribit DVOL hourly + closes
- **Sampling**: 1h
- **Horizon**: 24h primary, 4h secondary
- **Pre-declared**: sign `+ VRP above own mean -> positive return (BTC/ETH only)`; primary mode **TS**, primary H **24h** (secondary 4h)
- **Failure modes**: Only 2 assets → low power; DVOL is 30d-forward implied while horizon is 24h.
- **Lookahead risks / controls**: DVOL lagged one bar (candle stamping convention unverified); trailing RV only — forward RV variant excluded (LOOKAHEAD_RISK).
- **Forward-safety class**: `FORWARD_SAFE_WITH_RECEIPT_STAMP`
- **Literature basis**: S19,S20 (landscape A/B)

### P15_FUND_DIV — funding divergence (Binance vs Hyperliquid)

- **Mechanism**: Funding divergence: Binance funding above Hyperliquid funding signals venue-specific crowding.
- **Formula**: s = −[mean_24(f^{BN}_ph) − mean_24(f^{HL}_ph)]. CS mode.
- **Required inputs**: Binance + Hyperliquid funding histories
- **Sampling**: 1h (HL) / 8h (BN) → 1h
- **Horizon**: 24h primary, 4h secondary
- **Pre-declared**: sign `- Binance funding above HL -> crowded`; primary mode **CS**, primary H **24h** (secondary 4h)
- **Failure modes**: HL funding has different clamps/definitions; 2023-06+ only; venue-specific.
- **Lookahead risks / controls**: Both stamps floored to the hour and visible at the next decision; HL time jitter (ms) handled by flooring.
- **Forward-safety class**: `FORWARD_SAFE_WITH_RECEIPT_STAMP`
- **Literature basis**: S1,S5; cross-venue funding comparison in report 005

## Discovered but not executed

| id | primitive | family | class | why not executed |
|---|---|---|---|---|
| D16 | Dated-futures term-structure slope (Deribit) | term structure | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | no public point-in-time curve history for expired instruments in bulk |
| D17 | Perp vs dated-future basis | basis | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | same PIT-curve gap as D16 |
| D18 | Macro event reaction (FOMC/CPI first-print surprise) | event-driven macro | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | needs first-release stamps + ex-ante consensus vintages; using revised prints would be LOOKAHEAD_RISK; 3.7y sample has ~40 FOMC/CPI events (power) |
| D19 | Realized Amihud illiquidity | liquidity shocks | `FORWARD_SAFE` | overlaps P11; source S18 not verifiable |
| D20 | Top-trader long/short ratio contrarian | positioning | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | metrics available; deprioritised as redundant with funding/OI family |
| D21 | True liquidation-stream intensity (forceOrder/HL/OKX) | liquidation pressure | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | public streams are sampled/partial; no complete history (report 005) |
| D22 | HMM regime gating with smoothed states | regime-conditioned | `LOOKAHEAD_RISK` | smoothed/full-sample fit uses the future; filtered-probability variant is FSR |
| D23 | Offline change-point segmentation (ruptures-style) | regime-conditioned | `OFFLINE_ONLY` | offline by construction |
| D24 | Centered MA / HP / smoothed Kalman trend | momentum/trend | `LOOKAHEAD_RISK` | centered filter uses future bars |
| D25 | Full-sample z-normalised features | generic | `LOOKAHEAD_RISK` | future-normalised scale |
| D26 | Quarter-hour order-imbalance effect (Kim & Hansen 2026) | volume imbalance | `FORWARD_SAFE` | needs trade-level tape; too heavy for this pass |
| D27 | CTREND ML trend factor (Fieberg et al. JFQA 2025) | momentum/trend | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | ML, needs walk-forward and >3000-coin universe |
| D28 | First-half-hour → last-half-hour intraday momentum (Shen et al.) | intraday seasonality | `FORWARD_SAFE` | session definition ex ante; overlaps P01/P13 at 1h resolution |
| D29 | FX fixing seasonality (Krohn-Mueller-Whelan) | intraday seasonality | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | needs FX/gold intraday history and DST-exact stamps |
| D30 | FX/crypto carry (rate differential) | carry | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | needs point-in-time rates |
| D31 | BTC vs equity/macro lead-lag | cross-asset lead/lag | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | needs synchronised equity ticks |
| D32 | VRP with realised forward variance (DVOL − RV_fwd) | realized vs implied vol | `LOOKAHEAD_RISK` | uses future RV; ex-post analysis only |
| D33 | Predicted (next-period) funding from premium index | carry | `FORWARD_SAFE_WITH_RECEIPT_STAMP` | predicted-vs-settled definitions differ by venue |
| D34 | Bollinger/Keltner squeeze evaluated on the in-progress bar | vol compression | `LOOKAHEAD_RISK` | intrabar lookahead (repainting) |
