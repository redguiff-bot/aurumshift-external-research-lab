# 00 — Executive summary: AURUMSHIFT_EXTERNAL_EXECUTION_AND_TRANSACTION_COST_INTELLIGENCE_V1

Mode: EXTERNAL_RESEARCH_ONLY · no AurumShift private code · no AurumShift integration. Branch `claude/execution-cost-intelligence-v1`.
Question: which execution / transaction-cost primitives are well-founded and practical enough to be evaluated *later, locally* in AurumShift PAPER? Domain: crypto spot/perps, FX, gold, commodities, intraday, not HFT.

## What was done

* **Landscape** (A–L: spread, slippage, impact, fill, partial fills, adverse selection, maker/taker, scheduling, latency, funding/borrow/roll, fragmentation, implementation shortfall) with sourced notes and a per-model status (`02`).
* **OSS probe**: 21 candidates cloned and source-inspected, 9 smoke-executed, `bidask` (EDGE) re-used on synthetic and real data (`03`).
* **Threat model** E1–E15 with naive-vs-correct numbers and an accounting contract that keeps `UNKNOWN ≠ ZERO` (`01`, `11`).
* **Deterministic synthetic microstructure bench** (14 market scenarios + sliced / competing / latency / fragmentation / spread-estimator / passive-fill / full-fill experiments, seeded, ≈ 1 min to rerun) (`04`).
* **Live public capture** ≈ 50 min + 8 min deep: OKX, Coinbase, Kraken × BTC/ETH/SOL (books, trades, RTT), plus Binance Vision (aggTrades, klines, funding, bookDepth) and OKX funding/borrow/dated-futures curve (`05`).
* Executed and falsified **40 of 51 catalogued models/components** against simpler baselines (`12`, `13`).

## Headline findings

1. **The frictionless / default-bps world is wrong in size-dependent ways.** Live L2 walk cost of a market buy (bps vs mid): BTC 0.3–0.8 @ 100k USD, 1.1–2.5 @ 1M; ETH 1.2–1.6 / 4.0–5.1; SOL 2.7–4.0 / 10–18. A fixed 5 bps over-charges BTC by ≥ 6× and under-charges SOL at 1M by 2–3.5×; half-spread-only under-charges large orders by 5–30 bps (synthetic) (`07`).
2. **The L2 book walk is the only slippage primitive that is (near-)unbiased across scenarios and data**: against the next book snapshot the mean error is ≤ 3.3 % of the cost in the median cell (max 14 % for tiny orders; ≤ 0.05 bps for ≤ 300k USD; up to 0.18 bps at 4 s and 1.6 bps at 30 s for 1–3M USD on the noisiest series, an 8-minute sample); exact wherever depth is visible; it needs a visible-depth flag (25 levels cover only 1.8–20 bps) and a staleness band. It is *not* more accurate (MAE) than a per-instrument calibrated constant in 63 % of the 92 live cells (book flicker; walk wins in 78 % of the 3M-USD cells), but constants need history and **transport poorly across instruments (median error 60–80 %; sqrt-law prior 36–53 %, worst 3–5.5×)** (`07`).
3. **Candle-based spread estimators are not quote substitutes**: Corwin–Schultz/Abdi–Ranaldo/Roll read 1.7–9 bps vs quoted 0.01–1.2 bps live (×3 … ×700 depending on asset; largest on tick-bound BTC); EDGE is the best but only a bound on long samples. Effective spread from 2-second polled snapshots is a staleness meter (6–55× too high on BTC) (`06`).
4. **Passive fills cannot be point-estimated from free data**: public trades vs displayed queue bracket the fill probability in a band 0.07–0.44 wide; the Brownian price-through model is optimistic by 0.17; on synthetic data a calibrated constant matches or beats queue/hybrid models; and maker adverse selection is real (+0.3…+1.4 bps at 30 s; CI excludes 0 in 16 of 18) (`08`, `10`).
5. **Maker vs taker is a decision about fee gap and opportunity cost, not spread**: with BTC half-spreads of ~0.006 bps the break-even fill probability is 0.94–1.0 at zero fee gap and 0.62–0.70 at 2 bps, inside the observable bracket for 7 of 9 series ⇒ `MAKER_TAKER_UNDECIDABLE` from public data (`10`).
6. **Timing (latency) is a variance term, ~zero-mean, until flow or a gap says otherwise**: σ√L holds within ~15 % at ≥ 4 s; drift after strong signed flow is +0.6…+1.8 bps; a 1-minute σ under-states a 100 ms band 2.5×; FX/gold/WTI show session gaps of 1.1–3.3 hourly σ (`10`).
7. **Holding costs are first-order and venue-specific**: BTC perp funding cost a long 9.3 bps per 7 days on average (p05–p95 −0.8…17.3); OKX and Binance funding correlate only 0.43–0.49; one roll step on the OKX BTC-USD curve costs 34–150 bps; borrow has no free defensible number ⇒ `UNKNOWN_COST` (`09`).
8. **Accounting without double counting is achievable and testable**: a price-ladder contract (timing → spread → slippage → impact + holding costs) with fill-basis embedding; ladder identity residual 0.0; the classical "spread + slippage + sqrt-law" stack over-charged ×1.98 in the bench; unknown lines can never enter totals as 0 (`11`).
9. **No drop-in execution model exists**; the supported stack is a set of small primitives whose validity depends on the data regime (below).

## Minimum viable model per data regime (reference recommendation, not integration)

| Regime | Spread | Slippage / impact | Fills | Timing | Holding costs | Status |
|---|---|---|---|---|---|---|
| `OHLCV_ONLY` | `UNKNOWN`, or EDGE as a bound on ≥ 1 000 bars | sqrt-law prior with cross-instrument Y, band ±50–100 %, 3–5× tail flag; participation cap | market: cap only; passive: none (fill = UNKNOWN) | σ√L band + gap flag | funding measured from venue history; borrow UNKNOWN; roll only with curve | **LIMITED** — crypto majors only; nothing empirical for FX/gold/commodities |
| `L1_QUOTES` | measured quoted spread (+age) | orders ≤ displayed size; above → `INSUFFICIENT_DEPTH` + sqrt prior band | market: cap by displayed size; passive: bracket [queue-based, through] | σ_L√L band | as above | **SUPPORTED (limited range)** |
| `L2_BOOK` | measured | depth-capped walk to visible depth, staleness band; multi-child memory optional | depth-capped `filled_fraction`; passive bracket | σ_L√L + gap/withdrawal band | as above | **SUPPORTED** (tested BTC/ETH/SOL ≤ 3M USD, 3 venues, 400 levels) |
| `TRADES_PLUS_BOOK` | + effective spread only with message-rate quotes (untested) | + flow-conditional drift, markout diagnostics | passive bracket stays open without own-order data | + flow-momentum add-on | as above | **SUPPORTED as diagnostics**; impact calibration needs own runs |

## What is *not* supported (and why)

Quote/book models for FX, gold and commodities (no free reliable L1/L2: `MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA`); passive fill probability and queue models; order-level impact (propagator/AC) calibration; borrow costs; anything for stress regimes (`gap`, `withdraw` leave every model 4–15 bps low in the synthetic bench); realised slippage (no own fills). See `14`.

## Confidence and caveats (short)

Live evidence is one 50-minute window on one day and three REST-polled venues; no own orders. The synthetic bench is a constructed truth (circular where a model shares its functional form). Literature formulas marked `[M]` were coded from memory-based notes. Details and counter-scenarios: `12`, `14`.

## Final required block

```
MODELS_DISCOVERED=51 catalogued models/components (table in 13; plus 21 OSS repositories probed)
MODELS_EXECUTED=40 of 51 (own reference implementations and/or OSS smoke runs, on synthetic and/or public data)
OSS_COMPONENTS_TESTED=9 smoke-executed (of 21 cloned and source-inspected; 5 more used as formula references)

SPREAD_REFERENCE=quoted L1 spread distribution with snapshot age (OHLCV-only: EDGE as a bound on >=1000 bars, never a measurement; candle proxies rejected)
SLIPPAGE_REFERENCE=L2 book walk over visible levels with INSUFFICIENT_VISIBLE_DEPTH flag and empirical staleness band (OHLCV-only: sqrt-law prior with +-50-100% band)
IMPACT_REFERENCE=none beyond the walk for a single child order; depletion+propagator memory (ADAPT_CANDIDATE, own-run calibration) for multi-child/repeated orders
FILL_REFERENCE=depth-capped walk for market orders; explicit [P_lower(queue), P_upper] bracket for passive orders (no point estimate supported)

FUNDING_ACCOUNTING_REFERENCE=settled per-venue funding rate x held notional at settlement instants; ESTIMATED only with a band; ZERO_PROVEN only with evidence
BORROW_ACCOUNTING_REFERENCE=venue+tier+date rate if supplied, otherwise UNKNOWN_COST (never zero)
ROLL_ACCOUNTING_REFERENCE=calendar spread + both legs' half-spreads at the roll; NOT_APPLICABLE for perps/spot; UNKNOWN for continuous series without roll record

OHLCV_ONLY_MODEL_SUPPORTED=LIMITED (crypto majors: sqrt-law band + EDGE bound + participation cap; NO for FX/gold/commodities, NO for passive fills)
L1_MODEL_SUPPORTED=YES_LIMITED (spread, orders within displayed size, fill bracket, timing band)
L2_MODEL_SUPPORTED=YES (depth-capped walk; near-unbiased vs next snapshot on 9 live series, N up to 3M USD with 400 levels; realised slippage unmeasured)

DOUBLE_COUNTING_CONTRACT_PROVEN=PROVEN_ALGEBRAICALLY_AND_TESTED_ON_SYNTHETIC_LADDER (ladder identity residual 0.0; basis invariance abs_err 0.0; overcharge refused); NOT_PROVEN_ON_A_REAL_PAPER_ENGINE (UNKNOWN)

ANY_DROP_IN_EXECUTION_MODEL=NO
ANY_SCIENTIFIC_INVALIDATION=YES (of assumptions/models, not of the reference stack: OHLC spread proxies as quote substitutes; fixed 5 bps default; spread-proportional slippage; effective spread from polled snapshots; Brownian price-through fill; AC-linear schedule ranking; fill-model complexity improving maker/taker decisions; single-venue book as market; cross-venue funding proxy; a single calibrated constant transporting across instruments)

SECOND_SERVICE_REQUIRED=NO (all reference primitives are pure functions of data a PAPER runtime already sees; UNKNOWN whether AurumShift has L2 history)
SECOND_DATASTORE_REQUIRED=NO (optional L2/tape history for calibration is small: the 58-minute capture of 9 series is 8 MB gz; a file/existing store suffices)

FINAL_VERDICT=LIMITED_EXECUTION_MODELS_SUPPORTED
```

Rationale for the verdict (one exact value required): the evidence supports a *limited* subset — L1/L2-based cost of market orders on liquid crypto, holding-cost accounting for funding/roll, a latency band, and the no-double-counting ledger — and explicitly does **not** support OHLCV-only spreads, quote/book models for FX/gold/commodities, passive-fill/impact calibration or stress regimes. `EXECUTION_COST_REFERENCE_STACK_SUPPORTED` would over-claim across the stated target domain.

## Where to go next (still external, no integration)

1. A 24 h × several-day L1/L2 capture at message rate (WebSocket) to test effective/realised spread, day/night/weekend regimes and the Δ→0 staleness limit.
2. A small-order testnet or minimum-size live study to replace the book-walk *proxy* with realised slippage and to identify passive fill probabilities.
3. Quote-based data for one FX pair and gold (broker tick history) to close the non-crypto gap.
4. Only then map the contract in `11` onto the local PAPER economic outcome.

STOP.
