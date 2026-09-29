# 03 — Order books, replay engines, event simulators, backtest engines

Scripts: `py/mt/hft_microtest.py`, `naut_microtest.py` (+ `naut_cross_probe.py`, `naut_l1_probe.py`), `abides_microtest.py`, `orderbook_microtest.py`, `bt_engines.py`, `leak_probe.py`, `zl_microtest.py`.

## Ground truth used for L2 replay
Hand-built L2 feed (identical in hftbacktest and Nautilus): bid 100.0 × 10, ask 100.5 × 10 at t = 1 s; our 1-lot passive bid at 100.0 joins at t = 5 s (10 ahead in the queue); sell prints at 100.0: 4 @ 6 s, 6 @ 8 s, 6 @ 9 s; visible bid size at 100.0 falls 10 → 4 at 7 s. Derivation for a *risk-averse* queue (queue ahead reduced only by visible-size drops, then prints): 4 ahead after 7 s → the 6-lot print at 8 s clears it → fill at **8.0 s**. FIFO with prints only would also make the fill happen by 8–9 s.

## hftbacktest 2.4.4 (MIT)
| Test | Result (label) |
|---|---|
| risk-adverse queue model | fill at **8.0 s**, position 1.0, balance −100.0 (PROVEN vs derivation) |
| power-prob ×2 / ×3, log-prob queue models | all 8.0 s in this single scenario (OBSERVED; scenario does not discriminate between them) |
| order latency (entry = response latency) | 0 → fill 8.0 s; 4 s → **no fill** (order reaches the exchange at 9 s; position 0); 1.5 s → position 1.0 at the end but no fill visible to the strategy inside the feed window (INFERENCE: response-side latency delays local visibility) |
| fee model (`trading_value_fee_model(-0.0001, 0.0005)`) | fee −0.01 on a 100.0 maker fill |
| determinism | 3 repeated runs identical (JSON hash) |
| throughput | 2 M synthetic L2+trade events, 1 s clock stride: 0.17 s warm → **~11 M events/s** (numba JIT on first call) |
* Data model: numpy structured array `event_dtype` (`ev, exch_ts, local_ts, px, qty, order_id, ival, fval` — 64 bytes/event) with **separate exchange and local timestamps** and separate feed/order latency models → receipt-time semantics are first-class. No database, no service.
* Constraints seen: `constant_latency` is deprecated (use `constant_order_latency`); upstream slowed (last commit 2025-12-23, 24 commits/12 m, top author 62 %); repo tree exposes one test file by path (Rust inline tests not counted); converters for Tardis-format data exist in `hftbacktest/examples` (`2_download_tardis.py`, `3_convert.py` in the repo tree).

## nautilus_trader 1.221.0 installed (LGPL-3.0-or-later; PyPI also lists 1.231.0 and 2.0.0rc5)
| Test | Result |
|---|---|
| L2_MBP delta replay, resting limit bid, same feed | order accepted; **no fill** from the sell prints at 100.0 (`trade_execution=True`), none from a print through the limit at 99.90, none with `FillModel(prob_fill_on_limit=1.0)`, none with a 1.5 s `LatencyModel` — 6 L2 variants |
| book crossing (ask added at 99.90) | `OrderFilled` + `PositionOpened` — fills happen when the simulated book crosses (OBSERVED) |
| L1_MBP quotes+trades | `trade_execution=True`: no fill with 3 prints at 100.00 or one at 99.90; `trade_execution=False`: filled at 6.0 s because the trade tick updates the L1 book (not queue-aware) — 3 L1 variants |
| Verdict on this probe | a print-driven, queue-aware passive fill was **not reproduced in 9 configurations**; whether a supported setting exists is UNKNOWN (my setup may be incomplete) |
| determinism | event stream hash identical in repeated runs |
| throughput | 1 M quote ticks, passive strategy: 2.78–2.87 s → **349–360 k events/s** |
| footprint | 574 MB venv (299 MB the package), 15 distributions, import 0.06–0.6 s |
* It is a full trading platform (live adapters, message bus, cache, Parquet catalog). Used as a replay engine it must be constrained to backtest mode; the live-order code path stays installed (runtime-authority surface, INFERENCE from architecture).

## ABIDES (agent-based market simulation)
* `abides-jpmc-public` (BSD-3): fails on Python 3.11 because the pinned `pomegranate==0.14.5` only ships cp37–cp39 wheels. On a Python 3.9 venv with numpy 1.22, pandas 1.2.4, scipy 1.10 the `rmsc04` config (1 117 agents, `end_time=09:45:00`) ran in **1.6 s**, seed 1 twice → identical hash; seed 2 → different hash (deterministic and seed-sensitive, OBSERVED). No commits since 2023-12. Useful only as a scenario generator with an isolated legacy runtime.
* `abides-sim/abides` (first-generation): abandoned since 2020 → REJECT.

## Order-book libraries
* `dyn4mik3/OrderBook`: PyPI 0.1.2 is import-broken (circular import); GitHub HEAD matches FIFO ground truth (A 10, B 2 against a 12-lot sell) but `get_volume_at_price` raises `AttributeError`; ~121–150 k orders/s. Matching only — no feed ingestion, no queue-position for a passive order, no latency, no clock.
* The L2 book *is* inside hftbacktest (`HashMapMarketDepth`, ROI-vector depth) and Nautilus (Rust `OrderBook`, L1/L2/L3); no standalone maintained pure order-book library was found that adds anything over those two.

## Backtest engines (`bt_engines.py`): same SMA20/50 long/flat rule on 5 000 synthetic 1-min bars, fills at the next bar's open, zero fees
Oracle = 20-line numpy loop (57 trades; final equity 0.97741).
| Engine | Trades | Result vs oracle | Runtime | Deterministic |
|---|---|---|---|---|
| backtesting.py 0.6.6 | 57 | 0.977346 (Δ 6e-5) | 0.65 s | yes |
| backtrader 1.9.78.123 | 57 | final value 997 776.116329 | 0.74 s | yes |
| vectorbt 1.1.1 | 57 | final value 997 776.116329 (Δ ≈ 7e-9 vs backtrader) | 22.2 s first call (numba JIT) | yes |
| bt 1.2.3 | — | close-to-close rebalance; no next-open fill; not comparable | 0.85 s | yes |
| zipline-reloaded 3.1.1 | (daily NYSE test) | ingest rejects non-session bars; 271-day run deterministic | 1.1 s | yes |
| qstrader 0.3.0 | not run | installed/imported only | — | — |
Three independent implementations agree with the oracle on trade count and P&L to ≤ 6e-5 — the engine arithmetic is not the risk.

### Look-ahead probe (`leak_probe.py`)
| Engine | (A) can the strategy read bar t+1 through the per-bar API? | (B) does it accept a precomputed peeking array? |
|---|---|---|
| backtesting.py | no — index past the end raises `IndexError` | **yes** — perfect-foresight indicator returned **+115.8 %** with no warning |
| backtrader | **yes on preloaded data** — `data.close[1]` returned a value on every bar except the last, `IndexError` only at the end | (not tested; same class of risk) |
| vectorbt | whole-array API: the future is addressable by construction | **yes** — foresight entries/exits gave final 1 075 087 from 1 000 000 at zero fees |
| zipline-reloaded | not probed | not probed |
Conclusion (OBSERVED): none of the tested engines can *detect* a look-ahead that enters as data; a per-bar API only prevents accidental positive indexing. PIT/no-lookahead must be guaranteed by the feed/data layer (as-of joins, receipt timestamps) — consistent with the AurumShift constraint list, and independent of which engine is used.

## What this section supports
* Replay/simulation at tick/L2 level: `hftbacktest` (ADAPT), `nautilus_trader` (ADAPT, constrained to backtest mode, passive-fill semantics unresolved).
* Bar-level engines: `backtesting.py` is a compact cross-check oracle (AGPL); `vectorbt`, `backtrader`, `bt`, `zipline-reloaded` are PARK (licence/whole-array/frozen/daily-oriented respectively).
* No candidate provides PIT enforcement; nothing here replaces a PIT-aware data layer.
