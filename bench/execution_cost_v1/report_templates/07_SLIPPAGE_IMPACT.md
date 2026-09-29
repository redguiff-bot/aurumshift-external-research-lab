# 07 — Slippage and market impact

## 1. Slippage models compared: assumptions, inputs

| Model | Cost predicted (bps vs arrival mid, fees excluded) | Implicit assumptions | Inputs |
|---|---|---|---|
| Frictionless mid fill (E1) | 0 | executable at mid | – |
| Fixed bps `c` | `c` (default 5, or calibrated) | cost independent of size, spread, volatility, depth, time | – |
| Half-spread only ("zero slippage") | `s/2` | book infinitely deep at the touch | L1 |
| Spread-proportional | `k·s/2` | cost ∝ spread; size-blind | L1 |
| Volatility-scaled | `s/2 + a·σ` | cost ∝ σ (i.e. timing is charged as a positive mean) | L1, σ |
| Size/depth-linear | `s/2 + b·N/D_1bp` | linear walk out of the depth within 1 bp | L1 size + depth within 1 bp |
| Square-root | `s/2 + Y·σ_day·√(N/V_day)` | concave impact; Y transports across instruments | σ_day, V_day (OHLCV), optionally s |
| L2 book walk | `s/2 + VWAP_distance(N)` on the snapshot | static book over the latency window; own order only | L2 snapshot (visible depth ≥ N) |

Assumptions to state explicitly before using any of them: (a) what the reference is (arrival mid), (b) whether spread is inside the model (it is for all but fixed-bps/vol-scaled in a way that double counts if a spread line is added — see §5), (c) whether timing drift is charged with a non-zero mean (vol-scaled does; the walk does not), (d) size regime (validity ≤ visible depth).

## 2. Sensitivity to order size, volatility, depth, latency

**Size** (synthetic, `04` §3; bias by size shown there): frictionless and half-spread models are exact only for tiny orders; all models without a size term are off by 1–30 bps at 1e7 USD; the walk is exact while depth is visible.

**Volatility and depth** (synthetic, 1M USD, ratio of cost relative to the `base` scenario; truth vs model). The truth here has *no* volatility–liquidity coupling, so volatility does not move the mean cost (×1.03) while σ-carrying models (`vol_scaled`, `sqrt`) predict ×2.1: that gap is a property of the synthetic world, **not** a finding about markets — in the live data volatility and spread do move together (`05` §2, Spearman 0.26–0.78), and in the `coupled_hivol / coupled_lovol` scenarios (spread and depth co-move with σ) the σ-carrying sqrt model improves (mean |bias| 1.03 / 0.47 vs 2.86 / 0.68 for half-spread-only):

@@sensitivity@@

**Latency**: does not change the mean cost of the walk or of any static model in a random walk (mean drift ≈ 0), it changes the *variance* by σ²L — see `10` B. Under trend/adverse flow it shifts the mean by `drift·L` and every static model is biased by exactly that amount.

## 3. Empirical: book-walk cost from public snapshots (not realised slippage)

Mean cost (bps vs mid) of a hypothetical BUY market order of notional N walking the visible ask levels. Top-25-level run (visible depth 1.8–20 bps) and coverage (share of snapshots whose visible depth ≥ N):

@@live_walk@@

@@live_walk_cov@@

Deep run (400 levels, 8 minutes, 192–240 snapshots per series) — coverage is ≥ 98 % for all N up to 3M USD:

@@deep_walk@@

@@deep_cov@@

Observations (OBSERVED, one window):

* At 100k USD the walk costs 0.29–0.77 bps (BTC), 1.15–1.63 (ETH), 2.7–4.0 (SOL); at 1M USD 1.1–2.5 (BTC), 4.0–5.1 (ETH), 10–18 (SOL). Local exponent of walk cost in N between 100k and 1M: 0.39–0.87 (median 0.55); i.e. close to, but not identical to, a square-root scaling.
* A 5 bps default overstates BTC at ≤ 100k USD by ≥ 6× (up to ~500× at 1k USD) and understates SOL at 1M USD by 2–3.5×; the frictionless fill is defensible only for BTC/ETH at ≤ 10k USD (true walk cost 0.01–0.65 bps).
* **Visible-depth limit**: with the usual top-25 REST view the walk is defined for BTC only up to ≈ 0.1–0.3M USD (coverage 0.98 at 100k, 0.78 at 300k on OKX, ~0 at 1M) — a PAPER using 25 levels must return `INSUFFICIENT_VISIBLE_DEPTH` above that, not extrapolate.
* **Venue dispersion** (same asset, same size): 100k USD BTC 0.29–0.77 bps, ETH 1.15–1.63, SOL 2.7–4.0.

### 3.1 Snapshot staleness

Error of predicting the walk at `t + Δ` with the snapshot at `t` (bias, mean absolute error, p95 of |error|, and mean cost), Δ = 4 s and 30 s:

@@live_stale@@

* **Near-unbiased**: top-25 run — |mean error| ≤ 0.05 bps everywhere (median ≤ 0.012 bps; ≤ 3 % of the cost at N ≥ 100k, ≤ 10 % at 1k–10k); deep run — ≤ 0.11 bps up to 300k USD, and for 1–3M USD median 0.012–0.062 bps but up to 0.53 bps (1M) and 1.62 bps (3M, OKX SOL at 30 s) on the noisiest series; relative to cost the median is ≤ 3.3 % and the maximum 14 % (small orders). Not exact, but no systematic sign.
* **Error floor, not decay**: MAE at Δ = 30 s is only 7–20 % above Δ = 4 s (e.g. OKX BTC 100k: 0.41 vs 0.39; Coinbase SOL 100k: 1.30 vs 1.08): the dominant error is book flicker faster than 4 s, not slow drift of liquidity; the Δ→0 limit is unmeasurable with 2 s polling (UNKNOWN).
* The error is of the same order as the cost itself for small orders (MAE 0.13 vs mean cost 0.09 bps for OKX BTC 10k), so per-trade walk costs are noisy; averages are reliable.

### 3.2 Does the walk beat calibrated constants? (falsification attempt)

Predict the walk at t+4 s with (a) the snapshot walk (no calibration), (b) a constant calibrated per series×N on the first half of the capture, (c) half-spread only, (d) spread-proportional / sqrt with parameters calibrated on the first half; test on the second half. Top-25 run (N ≤ 1M):

@@live_baselines_mae@@

Deep run (N up to 3M; 8-minute capture, so calibration and test halves are 4 minutes each):

@@deep_baselines_mae@@

@@walk_vs_const@@

Reading: the per-instrument-per-size constants are a *strong* baseline for MAE because the capture is stationary and small orders are dominated by book flicker — **the walk wins mostly where the book regime changes within the window (Coinbase/OKX/Kraken ETH and SOL at ≥ 1M USD; 78 % of the 3M-USD cells)**, and has no systematic bias (mean |bias| 0.025 vs 0.52 bps for the half-sample constants). The constants win in MAE for BTC and for small sizes but they need a per-venue, per-instrument, per-size history that a PAPER does not have on day one; §3.3 tests what happens when that history comes from *other* instruments.

### 3.3 Calibration transport: leave-one-series-out

Fit the constant / `Y` / spread multiple on the other 8 venue-asset series and predict the ninth (mean walk cost at N; only series with ≥ 95 % coverage):

Top-25 run:

@@transport_live@@

Deep run (N up to 1M USD):

@@transport_deep@@

* A single calibrated **constant transports with median relative error 60–80 %** and worst-case factors 6–9×; **sqrt-with-cross-series-Y is the best transporter (median error 36–53 %, worst 3–5.5×)** but is still ±50 %. Half-spread-only under-charges by 75–98 % (worst 11–414×). *No cross-instrument constant is trustworthy to better than about a factor of two*; conversely the sqrt form (size and σ/V scaling) removes about half of the constant model's transport error.
* Therefore, for `OHLCV_ONLY` the supportable statement is a **band from a sqrt-law prior with a cross-instrument Y**, flagged `ESTIMATED` with ±50–100 % error and a 3–5× tail — not a measurement.

## 4. Market impact

### 4.1 Which impact concepts survive at non-HFT intraday scale

| Concept | Definition | Survives at 1e4–1e7 USD, minutes-scale? | Charged as |
|---|---|---|---|
| **Spread crossing** | half-spread at execution | yes (0.006 bps BTC … 0.4–0.6 bps SOL) | `spread` |
| **Temporary impact of this order** (book walk, same instant) | VWAP beyond touch | yes — the dominant size cost (0.3–2.5 bps BTC at 0.1–1M USD) | `slippage` (walk) — **not** additionally an "impact" line |
| **Transient impact of earlier own child orders** | displacement of mid still decaying when the next child hits (propagator/depletion) | only for multi-child parents or repeated orders within τ ≈ tens of seconds to minutes (synthetic E15: 5 children of 500k USD cost 2.5–5.1 bps/order vs 2.3 for one, depending on spacing 600 s … 1 s; `04` §5) | `impact` |
| **Permanent impact** | information/inventory effect that persists | negligible for one small order (aggregate market flow gives λ = 2.3–6.6 bps per 1M USD **net market flow per minute**, R² 0.2–0.34, Binance tape, `§4.2`; own-order share is a tiny fraction); matters only as a marking effect for *later* fills | `impact` on later children only; never on this fill |
| **Adverse price movement** (timing) | exogenous drift + informed flow during the latency window | yes, zero-mean in RW; conditional mean +0.6…+1.8 bps after strong flow | `timing` |

### 4.2 Aggregate flow–return regression on Binance aggTrades (context, not metaorder impact)

1-minute and 5-minute bars, signed USD flow `Q` vs bar return; fit on all days but the last, out-of-sample RMSE on the last day (bps):

@@vision_impact@@

* Flow explains 22–34 % of bar return variance (R²), slope 2.3–6.6 bps per 1M USD net flow; the log-log slope of signed impact vs |Q| deciles is 0.56–1.0 (BTC 0.67/0.56, ETH 0.85/1.0): **inconclusive between square-root and linear**, and OOS RMSE ranks sqrt < linear < zero but by ≤ 8 % (vs linear) and ≤ 21 % (vs zero). This is aggregate flow, endogenous (returns also cause flow) and *not* a metaorder study — it does not measure the impact of a single trader's order and must not be used to calibrate one. Metaorder-level evidence for current crypto venues is UNKNOWN in the accessible literature (`02`).

### 4.3 What the sliced-execution synthetic bench says about impact modelling

(`04` §4) memory-less walks under-charge multi-child parents by up to 2.6 bps at 20 slices; a propagator layer removes about half; a linear AC form mis-orders schedules; a schedule-blind sqrt cannot rank. Depletion recovery (τ ≈ 20 s) is a first-order term that the propagator-only model omits.

## 5. Accounting decomposition (no double counting)

Every model above is **IS-calibrated** (it predicts the price move from arrival mid to average fill) and therefore already contains some rungs of the ladder in `11`. Adding a second model's rungs on top double counts:

| Model | Rungs implicitly inside | Safe pairing |
|---|---|---|
| Fixed bps | spread + slippage + mean timing | use alone; all other lines `EMBEDDED_BY_BASIS`-like (declare basis `FIXED_IS`) |
| Spread-proportional | spread + (some) slippage | alone, or with an explicit fee line |
| Vol-scaled | spread + timing (non-zero mean) | alone |
| Square-root (IS-calibrated) | spread + slippage + mean timing (+ average own impact) | alone; **do not add a spread line** (this is the most common double count) |
| Almgren–Chriss (ε, γ, η) | ε = spread/fixed cost, γ permanent, η temporary | alone; do not pair ε with a spread line |
| L2 walk | half-spread + slippage | `BOOK_VWAP` basis; add only `timing` band, fees, `impact` (multi-child) |
| Propagator | transient/permanent impact of *earlier* fills only | pair with walk (temporary part) — never with an IS-calibrated model |

The contract (`11`) turns this table into code: choosing a model fixes a fill basis and the ledger refuses charges for embedded rungs; the naive stack "full spread + 1 bp slippage + sqrt" over-charges a 1M USD trade in the synthetic base book by ×1.98.

## 6. Verdicts

* **`SLIPPAGE_REFERENCE`**: L2 book walk over the visible levels with an explicit `INSUFFICIENT_VISIBLE_DEPTH` flag and a staleness band taken from the empirical snapshot-to-snapshot error (≈ 0.1–0.8 bps for ≤ 100k USD; wider above). Supported for the regime and range tested (BTC/ETH/SOL, three venues, N ≤ 3M USD, 400 levels).
* **`IMPACT_REFERENCE`**: for a single child order, no separate impact line beyond the walk; for multi-child/repeated orders, walk per child + depletion/recovery + transient impact memory (propagator family) — **ADAPT_CANDIDATE**, needs calibration from the user's own PAPER runs (not calibratable from free data). Square-root law as an OHLCV-only prior with a ±50–100 % band.
* Not supported: any fixed/proportional model as a default, and any impact model calibrated on aggregate tape flow as if it were order-level.
