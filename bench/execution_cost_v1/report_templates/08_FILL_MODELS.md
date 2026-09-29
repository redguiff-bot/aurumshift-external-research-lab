# 08 — Fill and partial-fill models

Scope: market-order depth caps (partial fills), probabilistic/participation fills, passive fills at the touch (price-through, queue, hybrid), and the minimum useful model per data regime.
Evidence: synthetic worlds (known truth) and live public bounds (OKX/Coinbase/Kraken, BTC/ETH/SOL, ≈ 50 min). No own orders exist, so **no live fill probability was measured, only bounds**.

## 1. How often does "full fill" distort? (synthetic)

**Market orders.** Full-fill is exact as long as the order is a small fraction of *total* book depth, and wrong in a very lopsided way once it is not (thin-book grid: `A` = depth scale, 5 depths × 4 sizes = 20 cells):

@@fullfill@@

@@fullfill_share@@. Two separate distortions are visible in that table: (i) **partial fills** appear only when `N/depth ≳ 2` (rare, but then 56 % of a 10M USD order is unexecutable in the thinnest book) and (ii) **cost at touch** — even when the fill is 100 %, "fill at the touch" charges 0.5 bps vs a true walk of 0.6 → 360 bps in the same table. The second distortion is the common one; it is a slippage error (`07`), not a fill-fraction error.

**Passive orders.** "Always fills at the touch" is wrong almost everywhere in the synthetic limit-order world:

@@passive_fullfill@@

**Live** (bounds, §3): a bid at the touch had a fill probability of at least 0.36–0.84 (back of queue, 30–60 s) and at most 0.79–0.94 (front of queue); even the front-of-queue upper bound is below 1, so "always fills" overstates the fill probability by at least 6–21 points at best and by 16–64 points at the back of the queue.

## 2. Passive fill models compared (synthetic, 432 cells × fill fraction)

Cells vary queue position (0/0.5/1 of displayed queue), aggressor volume (0.5k/2k/20k USD/s), drift (0/0.1/0.4 bps/s), flow-informativeness, volatility, fees, spread. Error = prediction − truth fill fraction over H = 60 s:

@@fill_models@@

* `always_fill` is biased +0.30. `const_p` (calibrated on the whole grid: p = 0.70) has zero bias and MAE 0.21, **as good as the price-through model** (MAE 0.21, bias +0.18) and better than the displayed-queue model (0.40, biased −0.12) and the hybrid (0.26, +0.25).
* The synthetic truth has a non-trivial dependence on drift/queue/volume that none of the four captures well; the *calibrated constant* is a hard baseline. A queue model that needs a displayed queue size and a trade rate **does not beat a constant** in this world (falsification of "more inputs ⇒ better fill model").

## 3. Live evidence: bounds only

For each snapshot a hypothetical BUY limit at the best bid was tracked over the public trade tape for H = 30 / 60 s:

* `P_upper` — any trade at ≤ bid price (assumes we are first in the queue);
* `P_through` — a trade strictly below the bid (independent of queue position);
* `P_lower` — cumulative volume traded at ≤ bid ≥ the displayed queue (we are last; ignores cancellations, which only help us).

@@live_fill@@

Brownian first-passage ("price-through") model against the observed `P_through` (tick and σ from the same capture):

@@live_fill_model@@

@@live_fill_model_summary@@

* **The bracket [P_lower, P_upper] is 0.07–0.44 wide** (mean 0.27): without queue-position information a passive fill probability cannot be pinned down from public data. This is a structural limit (cancellations are invisible in aggregated L2), not a small-sample issue.
* The Brownian price-through model is **optimistic by 0.17 on average, in every one of 18 cases** (it treats the touch as continuous and ignores that a strict trade-through requires a print below the bid, not just a tick of mid movement). Falsified as a stand-alone fill model for large-tick assets; usable only as an upper bound.
* Queue models of the Cont–Stoikov–Talreja / queue-reactive type need per-level event intensities and queue sizes at message rate (L3 or full L2 diffs): `MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA` in this study (REST snapshots every ≥ 2 s).

## 4. Minimum useful model per data regime (reference)

| Data regime | Market/marketable orders | Passive orders |
|---|---|---|
| `OHLCV_ONLY` | participation cap vs bar volume (fill fraction = min(1, cap·V_bar/N)); cap value is **UNKNOWN** (not calibrated here) | **no fill model supported**; if required, "fill iff bar low < limit − ε" is the price-through rule (upper-bound-like, live P_through 0.67–0.92) and must be reported as an *optimistic* bound with `fill_prob = UNKNOWN` |
| `L1_QUOTES` | fill at touch only for `N ≤ displayed size`; beyond that `INSUFFICIENT_DEPTH` flag (not a silent switch to another model, `04` §3.7) | bracket `[P_lower(queue = displayed size), P_through]`; carry both, decide with the pessimistic end |
| `L2_BOOK` | exact depth-capped walk of the visible levels; unfilled remainder reported; visible-depth limit flagged (`07`) | same bracket; `P_lower` uses the real queue at the level, still ignoring cancels |
| `TRADES_PLUS_BOOK` | + staleness band from snapshot-to-snapshot differences (`07`) | + post-fill markout from the tape (adverse selection of fills, 0.3–1.4 bps at 30 s, `10`); bracket still open without own-order data |

Verdict: `FILL_REFERENCE = depth-capped book walk (market) + explicit [lower, upper] fill bracket (passive)`; probabilistic passive-fill *point* models are not supported by free data.
