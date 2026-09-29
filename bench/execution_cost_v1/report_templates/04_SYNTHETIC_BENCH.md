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

@@truth_decomp@@

## 3. Single market order — model comparison

Models (formulas in `models/models.py`): E1 mid-fill; fixed 5 bps; fixed bps (calibrated); half-spread only (= "zero slippage"); spread-proportional; vol-scaled;
size/depth-linear (L1 + depth within 1 bp); square-root (with and without spread information); book walk on an L2 snapshot (100 bps or 20 bps visible), with/without sqrt fallback.
Calibration: nonlinear least squares of the *scalar* parameters of each model on the mean truth of the four training scenarios × 5 sizes; fitted values:

@@single_params@@

Bias = mean(prediction − truth IS), fees excluded, per (scenario, size), then averaged in absolute value. `us/pred` = wall time per prediction in this Python implementation including context building (INFERENCE: order of magnitude only).

@@single_summary@@

Per held-out scenario (mean |bias| over the five sizes):

@@single_by_scenario@@

By order size for three representative scenarios (signed bias, bps):

@@single_by_size@@

Seed stability (5 independent truth seed sets; identical calibration protocol): the held-out mean |bias| moves by ≤ 0.03 bps for every model except size/depth-linear (0.25 bps), and the ordering never changes — **the variance is in the scenarios, not in the Monte-Carlo noise**.

@@seed_stability@@

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

@@fragmentation@@

## 4. Sliced execution (participation / schedule)

Parent order 0.2 – 5 M USD executed as 1, 5 or 20 equal market children over 600 s (four impact regimes, calibration on `sl_base` only).
Models: independent walks (each child on the same snapshot), propagator (true kernel shape, only λ fitted), propagator with a permanent-only kernel (the common simplification), Almgren–Chriss linear (`ε + ½γX + η·rate`), sqrt total.
Bias vs the ex-drift truth (drift is zero-mean noise; using the raw IS would add ~±1 bp of sampling noise):

@@sliced_summary@@

High-impact regime, 5M USD (detail; truth_ex_drift vs prediction):

@@sliced_detail@@

Schedule ranking (does the model choose the schedule with minimal *expected* cost among 1/5/20 slices?):

@@sliced_rank@@

Fitted parameters (recovered from the base regime only):

@@sliced_params@@

Findings: (i) memory-less independent walks under-charge sliced execution by up to −2.6 bps at 20 slices (they ignore depletion and transient impact); (ii) a propagator layer removes part of it but the residual stays (~−2.2) because depletion recovery is not in the kernel; (iii) the **linear AC form fitted on the base regime mis-orders schedules everywhere (share correct 0 %, mean regret 0.68 bps)** and (iv) the schedule-blind sqrt-total cannot rank at all (regret 3.05 bps). In this truth slicing always lowers *expected* cost (walk savings > impact accrual), so the ranking test is weakly discriminating; the timing-risk trade-off that motivates AC is a variance argument and is not evaluated here (UNKNOWN).

## 5. Competing / repeated orders (E14/E15)

@@competing@@

## 6. Latency, staleness

@@latency@@

(`mean_drift` ≈ 0 in `rw` and `meanrev`, ≈ drift·L in `trend`, ≈ jump in `gap`; `sqrt_lat_sigma` = σ√L.)

## 7. Passive fills & maker/taker

See `08_FILL_MODELS.md` and `10_MAKER_TAKER_LATENCY.md`.

## 8. Reproduce

```
cd bench/execution_cost_v1
python3 synthetic/run_synth.py          # all synthetic experiments -> results/
python3 contract/tests_and_threats.py   # ladder identity, contract tests, E1..E15 matrix
```
