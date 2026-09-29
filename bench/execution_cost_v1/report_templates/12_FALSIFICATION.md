# 12 — Falsification log

Rule from the brief: *a complex model that cannot be calibrated must not beat a simpler one by assumption.* Each row is an explicit attempt to break a claim, with the test, the outcome, and whether it holds. Outcome labels: **FALSIFIED** (the claim fails the test), **SURVIVED** (test passed; not proof), **PARTIAL**, **INCONCLUSIVE** (data cannot decide). Evidence type: SYN = synthetic truth (constructed), LIVE = public snapshots/tape (no own fills), VIS = Binance Vision history. SYN evidence about model-vs-truth *sharing a functional form* is not counted as support (CIRCULAR).

| # | Claim under test | Test | Outcome | Numbers | Evidence |
|---|---|---|---|---|---|
| F1 | "Mid-price fill is fine" (E1) | cost of an order vs frictionless | **PARTIAL** — fine only for tiny orders on tick-bound majors | true walk cost 0.01–0.65 bps for BTC/ETH ≤ 10k USD, 0.3–2.5 bps at 0.1–1M, 10–18 bps SOL at 1M; synthetic mean |bias| 5.0 | LIVE+SYN (`07`) |
| F2 | "A fixed 5 bps default is conservative" | vs live walk and synthetic | **FALSIFIED** | overstates BTC ≤ 100k by ≥ 6× (to ~500×); understates SOL at 1M by 2–3.5×; synthetic 4.73 vs 4.00 for a calibrated constant | LIVE+SYN |
| F3 | "Spread-proportional captures slippage" | live (k fitted on half-sample), synthetic | **FALSIFIED** | no size term; Coinbase BTC 100k: MAE 3.5 vs 0.32 bps for a constant; synthetic `shallow` 1e7: −28.8 for spread-only | LIVE+SYN |
| F4 | "Vol-scaled cost is a better default than fixed" | synthetic (no coupling / coupling); live coupling | **PARTIAL / INCONCLUSIVE** | truth insensitive to σ in the uncoupled world (×1.03 vs model ×2.1); with coupling (`coupled_hivol`) sqrt 1.03 vs half-spread-only 2.86; live spread–vol Spearman 0.26–0.78 positive in 9/9 but walk-vol weak (−0.06…0.56) | SYN+LIVE |
| F5 | "Sqrt-law with one calibrated Y transports" | leave-one-series-out on 9 venue-asset series; synthetic concave/shallow | **PARTIAL** — best transporter, still ±50 % | median rel. error 36–53 % (constant 60–80 %); worst 3–5.5×; synthetic `shallow` 1e7: −20.8 bps | LIVE+SYN (`07` §3.3) |
| F6 | "Size/depth-linear from L1 + 1-bp depth is a cheap L2 substitute" | wall / shallow scenarios | **FALSIFIED** | held-out mean |bias| 7.05, `wall` 35.6 bps | SYN |
| F7 | "Book walk on a stale snapshot beats a calibrated per-instrument constant" | next-snapshot walk, half-sample calibration | **PARTIAL** — no systematic bias, rarely more accurate | walk MAE < constant MAE in 37 % of 92 cells (28 % at ≤ 100k, 78 % at 3M); mean |bias| 0.025 vs 0.52 bps | LIVE (`07` §3.2) |
| F8 | "Staleness up to 30 s materially degrades the walk" | Δ = 4 s vs 30 s | **FALSIFIED (in this window)** | MAE only 7–20 % higher at 30 s; error is book flicker (< 4 s), Δ→0 untestable | LIVE |
| F9 | "Corwin–Schultz / Abdi–Ranaldo / Roll ≈ quoted spread" | OHLC of live trades and Binance klines vs quotes | **FALSIFIED** | live CS 1.9–5.1, AR 1.7–4.5, Roll 4.4–9.2 bps vs quoted 0.01–1.2; Binance BTC CS 0.8–1.5 vs 1-tick 0.001 | LIVE+VIS+SYN |
| F10 | "EDGE (OSS `bidask`) fixes it" | synthetic grid, 4 months of klines, ≈ 50 live bars | **PARTIAL** | good at ≥ 1 bp spread (5.0 vs 5.0), overstates ≤ 1 tick at high σ (0.2→2.5), 0.04–0.18 bps on Binance BTC/ETH vs 1-tick truth, unstable on 51 bars (0.09–2.7) | SYN+VIS+LIVE |
| F11 | "Effective spread from polled snapshots ≈ quoted" | trades vs 2 s snapshots | **FALSIFIED** | mean effective 0.4–1.9 bps vs quoted 0.01–1.15 (6–55× on BTC); staleness explains it | LIVE |
| F12 | "Almgren–Chriss linear cost ranks schedules" | 1 / 5 / 20 slices, 4 impact regimes | **FALSIFIED** | AC share correct 0 %, regret 0.68 bps; propagator/walk 100 % but the test is weakly discriminating (slicing always cheaper in expectation) | SYN |
| F13 | "Propagator memory fully explains sliced cost" | true-kernel vs permanent-only kernel vs independent | **PARTIAL** | residual −2.2 bps at 20 slices (depletion omitted); wrong (permanent-only) kernel is no worse (0.21 vs 0.21) | SYN |
| F14 | "Brownian price-through gives passive fill probability" | vs observed price-through and bounds | **FALSIFIED** | optimistic by 0.17 (all 18 cases); synthetic MAE equal to a constant (0.21) | LIVE+SYN |
| F15 | "Queue-volume model beats a constant fill probability" | 432 synthetic cells | **FALSIFIED** | MAE 0.40 vs 0.21 | SYN |
| F16 | "A better fill model gives a better maker/taker decision" | decision accuracy / regret | **FALSIFIED** | blind: all 62 % / 4.3 bps; drift-aware: constant p 95 % / 0.03 bps vs price-through 70 % / 2.8, queue 71 % / 2.1, hybrid 65 % / 3.8 | SYN |
| F17 | "Passive fill probability is identifiable from public data" | tape vs displayed queue | **FALSIFIED** | bracket [P_lower, P_upper] 0.07–0.44 wide (mean 0.27) | LIVE |
| F18 | "Maker adverse selection is negligible at non-HFT scale" | post-fill markout vs unconditional | **FALSIFIED** | +0.29…+1.40 bps at 30 s, CI excludes 0 in 16/18 | LIVE |
| F19 | "Latency is symmetric noise" | mean and conditional drift; gap | **PARTIAL** | mean ≈ 0 and sd ≈ σ√L ±15 % at ≥ 4 s; but +0.6…+1.8 bps after strong flow; σ at 1-min under-states 100-ms band 2.5×; gaps 1.1–3.3 σ_hour in FX/gold/WTI | LIVE+VIS |
| F20 | "Another venue's funding is a good proxy" | OKX vs Binance settled rates | **FALSIFIED** | corr 0.43 (BTC) / 0.49 (ETH), mean |diff| 0.27–0.28 bps/8h | VIS+LIVE |
| F21 | "Borrow is small enough to ignore" | arithmetic + public base rate | **UNTESTABLE** (no realised data) → `UNKNOWN` | 5–50 % APR ⇒ 9.6–96 bps/7 days (INFERENCE) | – |
| F22 | "Square-root law (exponent 0.5) holds in aggregate crypto flow" | Binance flow–return deciles | **INCONCLUSIVE** | slopes 0.56–1.0; OOS RMSE sqrt < linear < zero by ≤ 8 % / ≤ 21 %; walk-cost exponent in N 0.39–0.87 (median 0.55) | VIS+LIVE |
| F23 | "A single-venue book represents the market" | synthetic routing; live venue dispersion | **FALSIFIED** | ×1.4/2.2/3.3 for 2/4/8 venues; live walk 100k differs ×1.7–1.9 across venues | SYN+LIVE |
| F24 | "Naive stacking of spread + slippage + impact is harmless" | contract test | **FALSIFIED** | ×1.98 overcharge; contract refuses | SYN |
| F25 | "The models are exact on known books" | walk on truth-consistent scenarios | **CIRCULAR** — not evidence | mean |bias| 0.01–0.05 | SYN |
| F26 | "A drop-in execution model exists" | all of the above | **FALSIFIED** | no single model spans data regimes, size range and asset classes | – |

## Observations on what could *not* be falsified
* The ladder identity and the fill-basis embedding table (algebraic).
* "UNKNOWN must not be mapped to zero": no test can support the opposite.
* Anything for FX / gold / commodities on the quote/book side (no data): `MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA`.

## Scientific invalidations
The following pre-registered-in-spirit hypotheses were invalidated by this study: F2, F3, F6, F9, F11, F12, F14, F15, F16, F17, F18, F20, F23, F24, F26 (see table). None of them invalidates the reference stack proposed in `00`/`13`; each *is* the reason a simpler component is preferred.
