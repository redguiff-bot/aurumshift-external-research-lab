# 05 — Empirical public-data experiment

Only free, public, unauthenticated data. No AurumShift data. All raw captures for the live part are committed under `bench/execution_cost_v1/data/live` and `data/deep`; Binance Vision zips are re-downloadable (`analysis/fetch_vision.sh`).

## 1. Sources and roles (as fixed by the study brief)

| Source | Role | What was pulled |
|---|---|---|
| OKX (spot BTC/ETH/SOL-USDT + BTC/ETH-USDT-SWAP) | primary live microstructure | REST L2 (25 levels; 400 in the deep run), recent trades with taker side, funding (current + history), mark price |
| Coinbase Exchange (BTC/ETH/SOL-USD) | independent spot cross-check | REST L2 (25/400 levels of the aggregated book), trades (side = maker side), ticker |
| Kraken (XBT/ETH/SOL-USD) | second independent spot cross-check | REST depth (25/400), trades with taker side |
| Binance Vision (data.binance.vision) | historical calibration/reference **only** (not live execution evidence) | spot aggTrades BTC 2026-09-20…23, ETH 09-21/22; 1-minute klines BTC Jun–Aug, ETH Aug; USD-M funding history May–Aug (BTC/ETH); USD-M bookDepth 2026-09-20 |
| Yahoo chart endpoint (unofficial) | FX/gold/WTI OHLC **only for volatility/gap scaling** | 1-hour OHLC, 6 months: GC=F, EURUSD, USDJPY, CL=F, BTC-USD control |

Binance's live API (HTTP 451) and Bybit's (403) were not reachable from the sandbox; they were not used. HFT-grade feeds (WebSocket L3) were not captured: REST polling every ≈ 2.0–2.6 s, 3 threads (one per venue), round-trip time recorded per request.

Live run: 2026-09-29 ≈ 13:01–13:51 UTC (≈ 50 min, ≈ 1 264–1 498 book snapshots per series; ≈ 2 800–20 800 trades per series) plus an 8-minute 400-level "deep" run right after. Everything is one time window on one day.

@@live_overview@@

(`beta` = median exponent of the cumulative-depth curve `C(x) ∝ x^β` fitted on the visible levels; `sigma` in bps/√s from snapshot mids; `vis_depth_bps` = median distance covered by the visible ask levels.)

## 2. What the data look like (OBSERVED)

* **Book depth (ask side, USD available within x bps of the touch)** — the top 25 levels only reach 1.8–3.6 bps on BTC/ETH (≈ 20 bps on SOL):

@@live_depth@@

* The visible cumulative-depth curve is **concave** in distance (β ≈ 0.3–0.7 near the touch), not the convex β ≈ 1.5 that generates a square-root cost in the synthetic base book. Beyond the visible window the shape is UNKNOWN from these snapshots; the Binance USD-M `bookDepth` file (bands ±0.2 … ±5 %, far book) has a log-log slope of 0.81 between 20 and 500 bps for BTCUSDT on 2026-09-20 (`results/empirical_vision.json`), i.e. sub-linear in the far book too.
* **Vol ↔ liquidity coupling** (Spearman between trailing 30-snapshot realised vol and quoted spread / walk cost), positive in all 9 series for the spread (0.26–0.78) and mostly positive for the walk cost — the world where cost scales with vol is not a modelling artefact:

@@live_coupling@@

## 3. Deep run (400 visible levels)

@@deep_overview@@

Book-walk cost (bps vs mid) at larger notionals once more depth is visible, and the fraction of snapshots whose visible depth covers the notional:

@@deep_walk@@

@@deep_cov@@

## 4. Which models are calibratable from free data?

| Model / quantity | Fields required | Result in this study |
|---|---|---|
| Quoted spread distribution | L1 | **Calibrated** (`06`). Snapshot-based, 2 s cadence |
| Effective / realised spread | quote at trade time + aggressor | **Not from polled snapshots**: dominated by staleness noise (`06` §2). A message-rate feed was not tested → `MODEL_NOT_CALIBRATABLE_FROM_FREE_DATA` for REST polling; UNKNOWN for WebSocket |
| Trade-flip spread | aggressor flag + fine timestamps | **Calibrated** on Binance Vision (median = 1 tick) |
| OHLC proxies (Roll, CS, AR, EDGE) | OHLC | Falsified as quote substitutes; EDGE usable as bound on long samples (`06`) |
| Book-walk slippage | L2 snapshot | **Measurable** within the visible window; near-unbiased vs the next snapshot (median |bias| ≤ 3.3 % of cost), MAE 0.13–0.8 bps for ≤ 100k USD (`07`); **realised** slippage unmeasurable without own fills |
| Fixed / spread-prop / sqrt constants | costs + σ + V_day | Fit trivially in-sample; **transport poorly** across venue-assets (`07` §3, LOO) |
| Propagator / Almgren–Chriss impact | metaorder-tagged fills | `MODEL_NOT_CALIBRATABLE_FROM_FREE_DATA`. Only aggregate 1/5-min flow-return regressions on Binance tape (`07` §4) |
| Fill probability (point) | own order lifecycle / L3 | **Bounds only**: bracket 0.07–0.44 wide (`08`) |
| Queue-reactive / Cont–Stoikov–Talreja | L3 events, queue intensities | `MODEL_NOT_CALIBRATABLE_FROM_FREE_DATA` |
| Adverse selection (markout) | tape + mids | **Measured** (0.3–1.4 bps at 30 s, CI excludes 0 in 16/18) (`10`) |
| Kyle λ (aggregate) | signed volume + returns | Measured on Binance (2.3–6.6 bps per 1M USD/min, R² 0.2–0.34) (`07`) |
| Latency drift | mids/tape | **Measured**, follows σ√L ±15 % at ≥ 4 s (`10`) |
| Perp funding | funding history | **Calibrated** (4 months, 2 venues) (`09`) |
| Short borrow | rate history + tier | `UNKNOWN` (only a venue base rate; unit unverified) |
| Futures roll | curve | **Measured** (OKX BTC-USD dated curve snapshot) |
| FX / gold / commodities quotes, books, fills | quotes, books | `MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA` — see §6 |

## 5. Cross-venue view (fragmentation in the data)

OKX quotes USDT, Coinbase/Kraken USD; for OKX pairs the mean mid difference (1.7–2.7 bps, the USDT/USD basis) was removed. Mid difference sd is 0.9–1.5 bps for BTC/ETH/SOL versus a quoted spread of 0.01–1 bps, so **the best venue changes from snapshot to snapshot at the bps level**; `frac_crossed` is high because the mid dispersion exceeds the spread — with 1.5–3 s of snapshot skew this is **not** an arbitrage signal and is not evidence of tradable edge (fees dominate):

@@live_cross@@

Per-venue walk costs differ by ×1.7–1.9 across venues for the same asset and size (100k USD: BTC 0.34–0.61 bps, ETH 0.78–1.45, SOL 3.1–5.2, `07`), so **which book a PAPER models** is a first-order choice.

## 6. FX, gold, commodities: policy and what was done

Free reliable L1/L2 are **not available** for these classes in this study, so quote/book-dependent models are `MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA` and were **not** validated (no order-book-walk, no spread/fill/queue calibration from OHLCV). Only public 1-hour OHLC was used to scale volatility, look at session gaps and bound latency effects:

@@fxgold@@

Observations: (i) σ per √s is 0.11 (EURUSD), 0.16 (USDJPY), 0.52 (gold futures), 1.25 (WTI) bps vs 0.69 for BTC-USD in the same window, so the synthetic base σ = 0.9 is BTC-like, not FX-like; the 2-second latency band is ≈ 0.15–0.7 bps for FX/gold vs ~1 bp for BTC. (ii) These markets are **not 24/7**: 104–112 bars/week present vs 158 for BTC (one hour bars, 168 possible), with 26–27 session gaps > 3 h in 6 months whose mean |gap| is 1.1–3.3 hourly σ — the `gap` scenario is the relevant stress for them, and Corwin–Schultz/AR "spreads" of 0–28 bps on these bars are almost entirely volatility and cannot be checked without quotes. (iii) The WTI series is a continuous-contract series; roll effects contaminate its gap statistics (INFERENCE).

## 7. Reproduce

```
python3 analysis/empirical_live.py data/live live && python3 analysis/empirical_live.py data/deep deep
python3 analysis/transport_loo.py live && python3 analysis/transport_loo.py deep
python3 analysis/empirical_vision.py && python3 analysis/funding_borrow_roll.py && python3 analysis/fx_gold_ohlc.py
```
