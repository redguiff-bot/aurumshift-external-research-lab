# 04 — Deterministic synthetic microstructure bench

**No claim that any result here transfers to production.** The synthetic world is a *controlled truth* used to (a) verify accounting
identities, (b) falsify models against simpler baselines under known mechanisms, (c) measure sensitivity and data-regime degradation.
Where the truth generator shares a functional form with a model (book-walk, propagator) the model wins by construction; those
rows are marked CIRCULAR and are **not** evidence. Evidence lives in the scenarios where the truth differs from the model's assumptions
(gap, liquidity withdrawal, wall, concave book, fragmentation, misspecified kernels) and in `05` (real data).

Code: `bench/execution_cost_v1/synthetic/synth.py` (truth), `models/models.py` (models), `synthetic/run_synth.py` (experiments).
Everything is seeded (numpy `default_rng`), rerun = identical numbers. Runtime of the full synthetic suite is about a minute on one core.

## 1. Truth world (documented assumptions)

| Element | Definition |
|---|---|
| Mid | arithmetic random walk in bps, `σ√dt` (base σ = 0.9 bps/√s ≈ 50 % annual vol), optional drift (trend), OU pull (mean reversion), one signed jump at a random time inside the latency window (gap) |
| Book | cumulative notional depth to distance `x` bps from the touch `C(x)=A·x^β` on a 0.25 bps grid, 600 bps deep, lognormal per-level noise (sd 0.35), persistence between observed and executed book (ρ=0.7) |
| Spread | constant (base 1 bp); liquidity-withdrawal scenario multiplies it ×3 |
| Own impact | propagator kernel `G(τ)=λ[φ+(1−φ)(1+τ/τ0)^−γ]` per 1M USD (base λ=0.4 bps, φ=0.4, τ0=30 s, γ=0.5) on later child fills + depletion of consumed levels recovering at ρ=0.05/s |
| Latency | decision→arrival uniform in ±50 % of the scenario mean |
| Limit orders | tick-snapped quotes (0.5 bps), queue ahead consumed by sell aggressor flow, price-through fills, cancels, flow-imbalance AR(1) that predicts drift (`info`), flow-price coupling (`λ_flow`), horizon H = 60 s then chase with a market order |
| Fees | taker 5 bps / maker 2 bps (or 10 / 8 in the fee-sensitivity cells); *fees are a separate measured line* and excluded from the cost-model comparison |
| Fragmentation | depth split equally over `n_venues`; the *observed* snapshot is one venue's book, the *truth* routes across all |

Cost convention (ladder, BUY): `IS = timing + half_spread + walk + impact` relative to **arrival mid**, where
timing = exec-mid − decision-mid, half_spread = touch − exec-mid, walk = VWAP − touch, impact = displacement of exec-mid caused by own earlier fills.
Ladder identity: max |IS − Σ components| over every scenario × size × slicing run = **0.0** (PROVEN, `results/truth_decomposition.csv`).

## 2. Scenarios

Required by the mission: small order/deep market (`deep`, `base` × 1e3–1e5), large order/shallow (`shallow`, N up to 1e7), high vol (`hivol`),
low vol (`lovol`), liquidity withdrawal (`withdraw`: depth ×0.15, spread ×3 *after* the snapshot), trend continuation (`trend`: drift 0.5 bps/s adverse, latency 3 s),
mean-reverting (`meanrev`: OU κ=0.15/s, latency 5 s), gap move (`gap`: +15 bps jump inside a 1 s latency window). Extra: `wall` (book almost empty until 10 bps then a large wall),
`fragmented` (4 venues), `concave_book` (β=0.5; matches the live top-of-book concavity), `coupled_hivol` / `coupled_lovol` (σ×3 or ÷3 *with* depth ÷3 / ×3 and spread widening/narrowing — the volatility–liquidity coupling seen live), plus sweeps of order size (1e3 … 1e7 USD ≈ 5e-7 … 5e-3 of daily volume),
participation/slicing (1/5/20 children over 600 s), latency (0.05 … 20 s), queue position (0 / 0.5 / 1 of displayed queue ahead), fragmentation (1/2/4/8 venues).
Training scenarios for calibration: `base, deep, hivol, lovol`. Held-out: everything else.

Truth decomposition (mean over 300 trials per cell, `IS_se` = standard error of IS):

| scenario_N | IS | drift | half_spread | walk | impact | filled | IS_se | identity_maxabs |
|---|---|---|---|---|---|---|---|---|
| base / 1e+04 | 0.65 | 0.03 | 0.50 | 0.12 | 0.00 | 1.00 | 0.04 | 0.00 |
| base / 1e+06 | 1.59 | -0.03 | 0.50 | 1.12 | 0.00 | 1.00 | 0.04 | 0.00 |
| base / 1e+07 | 5.60 | -0.03 | 0.50 | 5.14 | 0.00 | 1.00 | 0.04 | 0.00 |
| shallow / 1e+04 | 2.24 | -0.06 | 2.00 | 0.30 | 0.00 | 1.00 | 0.04 | 0.00 |
| shallow / 1e+06 | 8.26 | 0.02 | 2.00 | 6.24 | 0.00 | 1.00 | 0.04 | 0.00 |
| shallow / 1e+07 | 30.80 | -0.01 | 2.00 | 28.81 | 0.00 | 1.00 | 0.05 | 0.00 |
| withdraw / 1e+04 | 1.68 | -0.02 | 1.50 | 0.19 | 0.00 | 1.00 | 0.04 | 0.00 |
| withdraw / 1e+06 | 5.43 | -0.02 | 1.50 | 3.95 | 0.00 | 1.00 | 0.04 | 0.00 |
| withdraw / 1e+07 | 19.58 | -0.07 | 1.50 | 18.16 | 0.00 | 1.00 | 0.04 | 0.00 |
| trend / 1e+04 | 2.11 | 1.49 | 0.50 | 0.12 | 0.00 | 1.00 | 0.09 | 0.00 |
| trend / 1e+06 | 3.15 | 1.54 | 0.50 | 1.11 | 0.00 | 1.00 | 0.10 | 0.00 |
| trend / 1e+07 | 7.16 | 1.53 | 0.50 | 5.13 | 0.00 | 1.00 | 0.09 | 0.00 |
| gap / 1e+04 | 13.86 | 13.23 | 0.50 | 0.12 | 0.00 | 1.00 | 0.28 | 0.00 |
| gap / 1e+06 | 14.45 | 12.83 | 0.50 | 1.12 | 0.00 | 1.00 | 0.31 | 0.00 |
| gap / 1e+07 | 19.08 | 13.43 | 0.50 | 5.15 | 0.00 | 1.00 | 0.26 | 0.00 |

## 3. Single market order — model comparison

Models (formulas in `models/models.py`): E1 mid-fill; fixed 5 bps; fixed bps (calibrated); half-spread only (= "zero slippage"); spread-proportional; vol-scaled;
size/depth-linear (L1 + depth within 1 bp); square-root (with and without spread information); book walk on an L2 snapshot (100 bps or 20 bps visible), with/without sqrt fallback.
Calibration: nonlinear least squares of the *scalar* parameters of each model on the mean truth of the four training scenarios × 5 sizes; fitted values:

| model | c | k | a | b | Y | hs_fallback |
|---|---|---|---|---|---|---|
| fixed_bps | 1.6470 | n/a | n/a | n/a | n/a | n/a |
| fixed_5bps_default | 5.0000 | n/a | n/a | n/a | n/a | n/a |
| spread_prop | n/a | 3.2940 | n/a | n/a | n/a | n/a |
| vol_scaled | n/a | n/a | 0.6499 | n/a | n/a | n/a |
| size_depth | n/a | n/a | n/a | 0.2059 | n/a | n/a |
| sqrt | n/a | n/a | n/a | n/a | 0.1168 | 0.5000 |
| sqrt_ohlcv | n/a | n/a | n/a | n/a | 0.1168 | 0.5000 |
| walk_fallback | n/a | n/a | n/a | n/a | 0.1168 | 0.5000 |

Bias = mean(prediction − truth IS), fees excluded, per (scenario, size), then averaged in absolute value. `us/pred` = wall time per prediction in this Python implementation including context building (INFERENCE: order of magnitude only).

| model | data regime | mean |bias| train | mean |bias| TEST | TEST excl. gap+withdraw | gap+withdraw only | RMSE train | RMSE TEST | us/pred |
|---|---|---|---|---|---|---|---|---|
| E1_mid_fill | OHLCV | 1.65 | 5.00 | 3.59 | 10.62 | 2.00 | 5.36 | 0.81 |
| fixed_5bps_default | OHLCV | 3.55 | 4.73 | 4.04 | 7.49 | 3.74 | 5.06 | 0.81 |
| fixed_bps_calibrated | OHLCV | 1.26 | 4.00 | 2.75 | 8.97 | 1.68 | 4.52 | 0.85 |
| half_spread_only(E3) | L1 | 1.15 | 4.27 | 2.81 | 10.12 | 1.67 | 4.79 | 2.52 |
| spread_prop | L1 | 1.26 | 4.01 | 2.77 | 8.97 | 1.68 | 4.48 | 2.66 |
| vol_scaled | L1 | 1.19 | 4.00 | 2.62 | 9.53 | 1.59 | 4.51 | 2.60 |
| size_depth(L1+D1bp) | L1 | 0.25 | 7.05 | 6.59 | 8.92 | 0.98 | 7.83 | 2.58 |
| sqrt_law(OHLCV-only) | OHLCV | 0.67 | 3.65 | 2.19 | 9.48 | 1.27 | 4.18 | 1.91 |
| sqrt_law(L1 spread) | L1 | 0.67 | 3.42 | 1.90 | 9.48 | 1.27 | 4.02 | 3.85 |
| book_walk_L2_top20(20bps) | L2_top20 | 0.04 | 2.48 | 0.91 | 8.76 | 0.84 | 3.24 | 10.23 |
| book_walk_L2_top20+sqrt_fallback | L2_top20 | 0.04 | 2.57 | 1.02 | 8.76 | 0.84 | 3.33 | 11.18 |
| book_walk_L2(100bps) | L2 | 0.04 | 2.13 | 0.47 | 8.76 | 0.84 | 2.92 | 14.68 |

Per held-out scenario (mean |bias| over the five sizes):

| model | concave_book | coupled_hivol | coupled_lovol | fragmented | gap | meanrev | shallow | trend | wall | withdraw |
|---|---|---|---|---|---|---|---|---|---|---|
| E1_mid_fill | 2.28 | 4.36 | 0.93 | 1.85 | 15.11 | 1.87 | 9.35 | 3.34 | 4.76 | 6.13 |
| fixed_5bps_default | 4.28 | 3.53 | 4.07 | 3.40 | 10.11 | 3.35 | 7.27 | 2.53 | 3.88 | 4.88 |
| fixed_bps_calibrated | 2.27 | 2.72 | 1.15 | 1.39 | 13.46 | 1.34 | 7.71 | 1.69 | 3.75 | 4.49 |
| half_spread_only(E3) | 1.78 | 2.86 | 0.68 | 1.35 | 14.61 | 1.37 | 7.35 | 2.84 | 4.26 | 5.63 |
| spread_prop | 2.27 | 3.50 | 0.66 | 1.39 | 13.46 | 1.34 | 7.59 | 1.69 | 3.75 | 4.49 |
| vol_scaled | 1.94 | 2.74 | 0.57 | 1.26 | 14.02 | 1.22 | 7.11 | 2.25 | 3.87 | 5.04 |
| size_depth(L1+D1bp) | 1.55 | 1.38 | 0.28 | 3.47 | 13.40 | 0.29 | 8.47 | 1.66 | 35.60 | 4.44 |
| sqrt_law(OHLCV-only) | 1.40 | 1.95 | 0.41 | 0.71 | 13.97 | 0.74 | 6.53 | 2.20 | 3.62 | 4.99 |
| sqrt_law(L1 spread) | 1.40 | 1.03 | 0.47 | 0.71 | 13.97 | 0.74 | 5.03 | 2.20 | 3.62 | 4.99 |
| book_walk_L2_top20(20bps) | 0.36 | 0.12 | 0.01 | 1.80 | 13.25 | 0.05 | 3.39 | 1.48 | 0.02 | 4.27 |
| book_walk_L2_top20+sqrt_fallback | 1.24 | 0.12 | 0.01 | 1.00 | 13.25 | 0.05 | 4.20 | 1.48 | 0.02 | 4.27 |
| book_walk_L2(100bps) | 0.03 | 0.12 | 0.01 | 1.99 | 13.25 | 0.05 | 0.04 | 1.48 | 0.02 | 4.27 |

By order size for three representative scenarios (signed bias, bps):

| scenario | model | 1000.0 | 10000.0 | 100000.0 | 1000000.0 | 10000000.0 |
|---|---|---|---|---|---|---|
| base | half_spread_only(E3) | -0.11 | -0.15 | -0.26 | -1.09 | -5.10 |
| base | sqrt_law(L1 spread) | -0.09 | -0.08 | -0.05 | -0.40 | -2.92 |
| base | book_walk_L2_top20(20bps) | 0.01 | -0.03 | -0.01 | 0.03 | 0.04 |
| base | book_walk_L2(100bps) | 0.01 | -0.03 | -0.01 | 0.03 | 0.04 |
| shallow | half_spread_only(E3) | -0.08 | -0.24 | -1.38 | -6.26 | -28.80 |
| shallow | sqrt_law(L1 spread) | -0.00 | 0.01 | -0.59 | -3.74 | -20.82 |
| shallow | book_walk_L2_top20(20bps) | 0.04 | 0.06 | -0.03 | -0.03 | -16.81 |
| shallow | book_walk_L2(100bps) | 0.04 | 0.06 | -0.03 | -0.03 | 0.04 |
| concave_book | half_spread_only(E3) | -0.09 | -0.13 | -0.14 | -0.13 | -8.41 |
| concave_book | sqrt_law(L1 spread) | -0.07 | -0.06 | 0.08 | 0.56 | -6.23 |
| concave_book | book_walk_L2_top20(20bps) | 0.03 | -0.00 | -0.02 | 0.03 | -1.74 |
| concave_book | book_walk_L2(100bps) | 0.03 | -0.00 | -0.02 | 0.03 | -0.05 |

Seed stability (5 independent truth seed sets; identical calibration protocol): the held-out mean |bias| moves by ≤ 0.03 bps for every model except size/depth-linear (0.25 bps), and the ordering never changes — **the variance is in the scenarios, not in the Monte-Carlo noise**.

| model | TEST_mean | TEST_min | TEST_max | train_mean | fitted_param_sd |
|---|---|---|---|---|---|
| E1_mid_fill | 4.99 | 4.97 | 5.00 | 1.64 | n/a |
| fixed_5bps_default | 4.74 | 4.72 | 4.75 | 3.55 | n/a |
| fixed_bps_calibrated | 4.00 | 3.98 | 4.01 | 1.26 | n/a |
| half_spread_only(E3) | 4.26 | 4.25 | 4.28 | 1.14 | n/a |
| spread_prop | 4.02 | 4.01 | 4.04 | 1.26 | 0.02 |
| vol_scaled | 4.01 | 4.00 | 4.02 | 1.19 | 0.01 |
| size_depth(L1+D1bp) | 7.04 | 6.89 | 7.14 | 0.24 | 0.00 |
| sqrt_law(OHLCV-only) | 3.65 | 3.63 | 3.67 | 0.67 | n/a |
| sqrt_law(L1 spread) | 3.42 | 3.40 | 3.44 | 0.67 | 0.00 |
| book_walk_L2_top20(20bps) | 2.48 | 2.46 | 2.49 | 0.04 | n/a |
| book_walk_L2_top20+sqrt_fallback | 2.57 | 2.55 | 2.59 | 0.04 | n/a |
| book_walk_L2(100bps) | 2.13 | 2.11 | 2.14 | 0.04 | n/a |

### Findings (OBSERVED in this synthetic world unless labelled otherwise)

1. **Frictionless mid-fill and the uncalibrated 5 bps default lose to every calibrated alternative in-sample, and out-of-sample to every alternative except the size/depth-linear model (7.05)** in mean |bias|; a fixed 5 bps is *worse* than a calibrated constant (4.73 vs 4.00 held-out mean |bias|) and over-charges small orders by ~4.3 bps.
2. **Spread-only ("zero slippage") is the dominant error for large orders**: at 1e7 USD in `shallow` it under-charges by 28.8 bps; in the deep `base` book by 5.1 bps.
3. **Spread-proportional, vol-scaled and fixed-bps models are statistically indistinguishable** on held-out scenarios (held-out mean |bias| 4.01 / 4.01 / 4.00): none of them contains size, so none can price the size axis (which is the axis on which cost varies by 1–2 orders of magnitude).
4. **Square-root with calibrated Y helps but does not transport**: best non-book model held-out (3.42 with the L1 spread; 3.65 OHLCV-only), yet in `shallow` it still under-charges 1e7 USD by 20.8 bps and in `concave_book` mis-signs at 1e6 (+0.5 vs −0.02 for the walk). Its single Y was fitted on convex books; the exponent of the impact term is an assumption, not a finding.
5. **Size/depth-linear (L1 + depth within 1 bp) is the worst held-out model (7.05)**: exact for the calibration books, catastrophic for a wall book (35.6 bps): extrapolating depth from a 1 bp window is unsafe. *A more complex-looking model that cannot be calibrated beyond its window loses to the simple baselines — falsified.*
6. **Book walk is by far the best when the relevant depth is visible** (held-out mean |bias| 2.13 with 100 bps visible; 0.47 excluding gap+withdraw; its remaining error is `fragmented` 2.0 — a single venue's book — and the unforecastable `trend` 1.5, `gap`, `withdraw`), and CIRCULAR only where the truth book is exactly the walked snapshot (train columns). Its real content: it is unbiased for `wall`, `shallow`, `concave_book`, `meanrev`, and it is the only model that sees a wall.
7. **Truncating the visible book (20 bps) reintroduces the failure**: `shallow` 1e7 USD bias −16.8 bps; falling back to the (train-calibrated) sqrt law does *not* help (4.20 vs 3.39 mean |bias| in `shallow`) because the fallback inherits sqrt's calibration mismatch. The correct degradation is to *flag* `INSUFFICIENT_VISIBLE_DEPTH` and return a bound, not to silently switch model.
8. **Nothing predicts the tails**: `gap` (+15 bps jump) leaves all models ≈ 13 bps low and `withdraw` ≈ 4.3–5.6 bps low, including the book walk (its snapshot is pre-event). The mean-bias table therefore separates "modelable" (excl. gap+withdraw) from "tail". Tail risk needs a band/flag, not a point estimate (INFERENCE).
9. **Fragmentation**: a single-venue snapshot over-estimates the cost of a smart-routed 1M USD order by 1.4× / 2.2× / 3.3× for 2 / 4 / 8 equal venues (table below) — and would *under*-estimate it if the trader can reach only one venue. Which book to walk is a modelling decision, not a detail.

| n_venues | truth_routed_all | single_venue_walk_estimate |
|---|---|---|
| 1.00 | 2.26 | 2.26 |
| 2.00 | 2.26 | 3.28 |
| 4.00 | 2.26 | 4.91 |
| 8.00 | 2.26 | 7.50 |

## 4. Sliced execution (participation / schedule)

Parent order 0.2 – 5 M USD executed as 1, 5 or 20 equal market children over 600 s (four impact regimes, calibration on `sl_base` only).
Models: independent walks (each child on the same snapshot), propagator (true kernel shape, only λ fitted), propagator with a permanent-only kernel (the common simplification), Almgren–Chriss linear (`ε + ½γX + η·rate`), sqrt total.
Bias vs the ex-drift truth (drift is zero-mean noise; using the raw IS would add ~±1 bp of sampling noise):

| model | test | train |
|---|---|---|
| almgren_chriss_linear | 1.13 | 0.36 |
| independent_walks(no memory) | 0.32 | 0.19 |
| propagator(permanent-only kernel) | 0.21 | 0.10 |
| propagator(true shape, lambda fitted) | 0.21 | 0.02 |
| sqrt_total(no schedule info) | 1.33 | 0.95 |

High-impact regime, 5M USD (detail; truth_ex_drift vs prediction):

| slices | model | truth_ex_drift | pred | bias |
|---|---|---|---|---|
| 1 | independent_walks(no memory) | 6.74 | 6.75 | 0.01 |
| 1 | propagator(true shape, lambda fitted) | 6.74 | 6.75 | 0.01 |
| 1 | propagator(permanent-only kernel) | 6.74 | 6.75 | 0.01 |
| 1 | almgren_chriss_linear | 6.74 | 6.93 | 0.19 |
| 1 | sqrt_total(no schedule info) | 6.74 | 3.80 | -2.94 |
| 5 | independent_walks(no memory) | 4.62 | 2.60 | -2.03 |
| 5 | propagator(true shape, lambda fitted) | 4.62 | 3.17 | -1.46 |
| 5 | propagator(permanent-only kernel) | 4.62 | 3.53 | -1.10 |
| 5 | almgren_chriss_linear | 4.62 | 2.67 | -1.95 |
| 5 | sqrt_total(no schedule info) | 4.62 | 3.80 | -0.82 |
| 20 | independent_walks(no memory) | 3.91 | 1.34 | -2.57 |
| 20 | propagator(true shape, lambda fitted) | 3.91 | 2.05 | -1.86 |
| 20 | propagator(permanent-only kernel) | 3.91 | 2.44 | -1.47 |
| 20 | almgren_chriss_linear | 3.91 | 2.67 | -1.23 |
| 20 | sqrt_total(no schedule info) | 3.91 | 3.80 | -0.11 |

Schedule ranking (does the model choose the schedule with minimal *expected* cost among 1/5/20 slices?):

| model | mean_regret_bps | share_correct_best |
|---|---|---|
| almgren_chriss_linear | 0.68 | 0.00 |
| independent_walks(no memory) | 0.00 | 1.00 |
| propagator(permanent-only kernel) | 0.00 | 1.00 |
| propagator(true shape, lambda fitted) | 0.00 | 1.00 |
| sqrt_total(no schedule info) | 3.05 | 0.00 |

Fitted parameters (recovered from the base regime only):

```
{
 "prop_true_shape": {
  "lam": 0.46554339318380267,
  "phi": 0.4,
  "tau0": 30.0,
  "gamma": 0.5
 },
 "prop_wrong_shape": {
  "lam": 0.46554339318380267,
  "phi": 1.0,
  "tau0": 30.0,
  "gamma": 0.5
 },
 "ac": {
  "g": 0.8669279126052383,
  "eta": 0.8523900772251115
 },
 "sqrt": {
  "Y": 0.15272200435651284,
  "hs_fallback": 0.5
 },
 "none": {}
}
```

Findings: (i) memory-less independent walks under-charge sliced execution by up to −2.6 bps at 20 slices (they ignore depletion and transient impact); (ii) a propagator layer removes part of it but the residual stays (~−2.2) because depletion recovery is not in the kernel; (iii) the **linear AC form fitted on the base regime mis-orders schedules everywhere (share correct 0 %, mean regret 0.68 bps)** and (iv) the schedule-blind sqrt-total cannot rank at all (regret 3.05 bps). In this truth slicing always lowers *expected* cost (walk savings > impact accrual), so the ranking test is weakly discriminating; the timing-risk trade-off that motivates AC is a variance argument and is not evaluated here (UNKNOWN).

## 5. Competing / repeated orders (E14/E15)

| kind | k | gap_s | N | naive_independent | truth_avg_cost_per_order | underestimate_x |
|---|---|---|---|---|---|---|
| E14_simultaneous | 1 | n/a | 100000.00 | 1.12 | 1.12 | 1.00 |
| E14_simultaneous | 1 | n/a | 500000.00 | 2.28 | 2.28 | 1.00 |
| E14_simultaneous | 2 | n/a | 100000.00 | 1.12 | 1.48 | 1.32 |
| E14_simultaneous | 2 | n/a | 500000.00 | 2.28 | 3.31 | 1.45 |
| E14_simultaneous | 5 | n/a | 100000.00 | 1.12 | 2.28 | 2.03 |
| E14_simultaneous | 5 | n/a | 500000.00 | 2.28 | 5.65 | 2.48 |
| E14_simultaneous | 10 | n/a | 100000.00 | 1.12 | 3.31 | 2.95 |
| E14_simultaneous | 10 | n/a | 500000.00 | 2.28 | 8.65 | 3.80 |
| E15_sequential_recovery | 5 | 1.00 | 500000.00 | 2.28 | 5.10 | 2.24 |
| E15_sequential_recovery | 5 | 10.00 | 500000.00 | 2.28 | 3.67 | 1.61 |
| E15_sequential_recovery | 5 | 60.00 | 500000.00 | 2.28 | 2.59 | 1.14 |
| E15_sequential_recovery | 5 | 600.00 | 500000.00 | 2.28 | 2.47 | 1.09 |

## 6. Latency, staleness

| regime | lat | mean_drift | sd_drift | sqrt_lat_sigma | ratio_sd_to_half_spread |
|---|---|---|---|---|---|
| rw | 0.05 | -0.00 | 0.20 | 0.20 | 0.40 |
| trend | 0.05 | 0.02 | 0.20 | 0.20 | 0.40 |
| meanrev | 0.05 | -0.00 | 0.20 | 0.20 | 0.40 |
| gap | 0.05 | 13.05 | 5.04 | 0.20 | 10.08 |
| rw | 0.25 | -0.01 | 0.45 | 0.45 | 0.90 |
| trend | 0.25 | 0.12 | 0.45 | 0.45 | 0.90 |
| meanrev | 0.25 | -0.01 | 0.45 | 0.45 | 0.90 |
| gap | 0.25 | 13.04 | 5.04 | 0.45 | 10.08 |
| rw | 1.00 | -0.02 | 0.90 | 0.90 | 1.80 |
| trend | 1.00 | 0.48 | 0.91 | 0.90 | 1.82 |
| meanrev | 1.00 | -0.02 | 0.90 | 0.90 | 1.80 |
| gap | 1.00 | 13.03 | 5.08 | 0.90 | 10.15 |
| rw | 5.00 | -0.04 | 2.01 | 2.01 | 4.03 |
| trend | 5.00 | 2.46 | 2.13 | 2.01 | 4.26 |
| meanrev | 5.00 | -0.04 | 2.01 | 2.01 | 4.03 |
| gap | 5.00 | 13.01 | 5.33 | 2.01 | 10.66 |
| rw | 20.00 | -0.08 | 4.03 | 4.02 | 8.06 |
| trend | 20.00 | 9.93 | 4.90 | 4.02 | 9.80 |
| meanrev | 20.00 | -0.08 | 4.03 | 4.02 | 8.06 |
| gap | 20.00 | 12.97 | 6.28 | 4.02 | 12.56 |

(`mean_drift` ≈ 0 in `rw` and `meanrev`, ≈ drift·L in `trend`, ≈ jump in `gap`; `sqrt_lat_sigma` = σ√L.)

## 7. Passive fills & maker/taker

See `08_FILL_MODELS.md` and `10_MAKER_TAKER_LATENCY.md`.

## 8. Reproduce

```
cd bench/execution_cost_v1
python3 synthetic/run_synth.py          # all synthetic experiments -> results/
python3 contract/tests_and_threats.py   # ladder identity, contract tests, E1..E15 matrix
```
