# 06 — Spread models: quoted vs effective vs realized vs OHLC vs trade-based

Question: which spread measures are usable for a non-HFT cost layer, and where does each break? Candle-based estimators are **not** assumed equivalent to quotes; they are falsified against quotes wherever quotes exist (crypto), and against a synthetic truth elsewhere.

Evidence: (1) live public L2 + trades, ≈ 50 min, OKX/Coinbase/Kraken × BTC/ETH/SOL (1 264–1 498 snapshots per series, `05`); (2) Binance Vision aggTrades (BTC 4 days, ETH 2 days) and 1-minute klines (BTC 3 months, ETH 1 month); (3) synthetic OHLC with known spread (`synthetic/run_synth.py::exp_spread_estimators`); (4) OSS `bidask` (EDGE).

## 1. Quoted spread (L1) — the reference

@@live_overview@@

* All three venues quote BTC/ETH at (nearly) **one tick** most of the time (`one_tick_frac` 0.44–1.0) and the tick itself is 0.001–0.04 bps for BTC/ETH: the half-spread of BTC is **≈ 0.006 bps** on OKX/Kraken, i.e. **≈ 50–750× smaller than the 4–30 s one-sigma mid drift** (`10`; ratio depends on venue). For tick-bound majors the spread is a rounding error next to timing and depth; for SOL (≈ 1 tick = 0.83 bps) it is a real cost.
* Coinbase quotes are wider/more variable than OKX (BTC mean 0.069 bps, p95 0.47 bps; ETH 0.29, p95 0.95): OBSERVED intermittent widening. Mean ≠ typical: use the distribution, not only the mean.
* Sampling: REST polling every 2.0–2.6 s with 76–278 ms round trips means the "quote" is an unsynchronised snapshot. For a cost layer this is fine (spread is persistent); it is not fine for effective/realized spread (below).

## 2. Effective and realized spread from polled snapshots — where it breaks

@@live_spreadmeas@@

* Mean **effective** spread (2·|px − mid|) is **0.4–1.9 bps** vs quoted 0.01–1.15: on tick-bound BTC it is 6–55× too high; the **median** recovers the quote for OKX/Coinbase BTC (0.012 / 0.001 bps) but not for Kraken.
* Cause (INFERENCE, consistent with the numbers): the "mid" is a snapshot 1–1.5 s stale on average; with σ ≈ 0.8 bps/√s the expected staleness error is `σ√age·√(2/π) ≈ 0.7 bps`, which matches the OKX BTC mean (0.66). **Effective spread measured against polled snapshots is a staleness meter when the true spread ≪ σ√age.** It needs a message-rate L1 stream (not available from the REST snapshots used here) to be meaningful.
* **Realized** spread (2·side·(px − mid_{t+h})) is negative at h = 5 s in 8 of 9 series (−0.3 … −1.3 bps): consistent with adverse selection / flow momentum (OBSERVED; the Binance tape shows +0.6–1.8 bps continuation after top-quartile signed flow, `10`), but the same staleness noise contaminates it. Its sign, not its magnitude, is the usable information. A taker cost layer should not use realized spread as cost (it measures the maker's P&L).
* Trade side: the venue flag agreed with the quote rule in 75–85 % (OKX, Kraken) and only 25–33 % for Coinbase (flag = maker side; used inverted). The residual disagreement is dominated by the same staleness.

## 3. Trade-based estimator (no quotes needed): consecutive opposite-aggressor prints

Binance Vision aggTrades carry the aggressor flag. Taking consecutive prints < 5 ms apart with opposite aggressor, the price difference is a direct read of the prevailing spread:

@@vision_overview@@

The **median equals one tick exactly** (0.0012 bps BTC, 0.0365 bps ETH); the mean is 0.05–0.14 bps because of episodes of wider spreads (and 9–16 % zero differences). OBSERVED. This is the cleanest *quote-free* spread read available from free data — but it requires an aggressor flag and sub-ms timestamps; it does not exist for FX/gold/commodities (`14`).

## 4. OHLC proxies vs quotes — falsified as equivalents

Live 1-minute trade-built bars (≈ 51–75 bars per series) against the quoted spread of the same capture:

@@live_ohlc@@

Binance klines, 1-minute, daily estimates averaged over 30/31 days (tick 0.0012 bps BTC, 0.037 bps ETH; trade-flip median = 1 tick):

@@vision_ohlc@@

Synthetic OHLC with known spread (mean over 250 one-minute bars × seeds; `tick` = quote grid 1 bp):

@@spread_synth@@

OSS EDGE (`bidask`) on the same synthetic grid and on real data:

@@spread_edge@@

@@spread_edge_real@@

EDGE on the ≈ 50 live trade bars (noisy; shown for completeness):

@@edge_live@@

### Where each estimator breaks (all OBSERVED here)

| Estimator | Needs | Breaks when | Evidence |
|---|---|---|---|
| Quoted spread (L1) | L1 stream | staleness of the snapshot; intermittent widening (use distribution) | live table §1 |
| Effective spread | quote at trade time + aggressor | true spread ≪ σ√staleness (polled snapshots) | §2: 6–55× too high on BTC |
| Realized spread | + horizon | always mixes cost with adverse selection; negative for takers' counterparties | §2 |
| Roll (1984) | serial covariance of trade prices | flow autocorrelation, large ticks/vol: reads 4.4–9.2 bps live (quoted ≤ 1.2), 0.7–1.3 bps on Binance BTC | §4 |
| Corwin–Schultz (2012) | H/L bars | dominated by volatility: synthetic 0.2 bps spread → 1.2/3.8/12.4 bps at σ = 0.3/0.9/2.7; 31–46 % of bar-pairs floor at 0 live; real BTC 0.8–1.5 bps vs tick-bound truth ~0.001 | synthetic, live, Vision |
| Abdi–Ranaldo (2017) | C/H/L | better than CS at low σ, collapses to 0 at high σ (synthetic 0.2 bps, σ = 2.7 → 0.00); live 1.7–4.5 bps | synthetic, live |
| H/L range × ½ | H/L | is a volatility measure, not a spread | 3.1–7.0 bps live |
| EDGE (Ardia et al. 2024, OSS `bidask`) | OHLC, long sample | true spread ≲ 1 tick with high σ (0.2 → 0.75–2.5 bps synthetic); < 100 bars (live: 0.09–2.7 bps, unstable) | synthetic, live, Vision 0.06–0.18 |
| Trade-flip | aggressor flag + µs timestamps | no flag / coarse timestamps | Vision |

## 5. Verdict (reference only)

* `SPREAD_REFERENCE = quoted L1 spread (distribution, with staleness age)` when quotes exist; effective spread only from a message-rate L1+trades feed; OHLCV-only ⇒ `EDGE` as an **upper-bound sanity band on samples ≥ 1 000 bars** (never as a measurement) and otherwise `UNKNOWN`.
* Candle-based Roll / Corwin–Schultz / Abdi–Ranaldo / range proxies: **not supported** as spread substitutes for liquid crypto (2–100× overstated vs quotes) — and there is no free quote data to test them for FX/gold/commodities (`MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA`). On FX/gold/WTI hourly bars they return 1.9–28 bps (`results/fx_gold_ohlc.json`), which cannot be judged without quotes; note that ~all of it is volatility.
