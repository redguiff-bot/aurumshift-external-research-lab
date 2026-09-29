# 03 — Replay, order books, event simulators

Raw evidence: `results/t01*, t02*, t12a*, t12c*, t13*, t16*`.

## T01 — L2 book correctness (200 000 seeded set/delete level events, final full-depth SHA-256 vs naive dict reference)
| Candidate | Matches reference | Events/s (incl. Python call overhead) |
|---|---|---|
| sortedcontainers (baseline) | yes | 1.73 M |
| hftbacktest 2.4.4 (`HashMapMarketDepthBacktest`) | yes | 1.96 M (single `elapse` over the array) |
| nautilus_trader 1.231.0 `OrderBook` (L2_MBP) | yes | 0.74 M (per-delta Python object construction included) |
OBSERVED. Throughputs are not like-for-like (hftbacktest ingests a prebuilt numpy array; nautilus receives Python delta objects). A first hftbacktest run mismatched because of the tester's read loop; corrected and re-run (logged here for honesty).

## T16 — nanobook 0.18.1 matching vs a FIFO price-time reference (20 000 GTC limit orders)
15 149 trades, identical (price, qty) sequence to the reference, best bid/ask equal, event-log replay yields identical trades; 1.19 M orders/s. OBSERVED. Project is young (18 releases) and bundles portfolio/broker code (`IbkrBroker`) in the same wheel → runtime-authority surface for a component that only needs a book.

## T02 — nautilus_trader BacktestEngine (100 000 quotes, market order every 50th)
* Two independent processes → identical fill digest `0cfe9174d9e0352c` (2 000 fills, same commission 425.478672). OBSERVED determinism. 19 k quotes/s including strategy callbacks.
* Default fill semantics: the order fills **on the same quote it was submitted against, at the touch** (2000/2000 same ts, 2000/2000 fill price = ask/bid). With `LatencyModel(250 ms)` and quotes 1 s apart: mean fill delay 1000 ms, fills at a later quote's price (4/399 equal the submit touch). So latency is opt-in and must be configured. OBSERVED.
* T12c: with L2_MBP book deltas, a market BUY of 3 walked the book exactly (1@100.50, 1@101.00, 1@101.50; avg 101.00). Gotcha: single `OrderBookDelta` objects passed to `add_data` produced "no market" rejections; the same data wrapped in `OrderBookDeltas` worked. OBSERVED.

## T12a — hftbacktest queue position (known answer)
Bid queue ahead = 10; resting BUY 1 @ best bid; sell trades of 4 then 7 then 1. All four queue models (risk-adverse, power-prob 2, power-prob 3, log-prob) left the order NEW after the 4-lot trade and FILLED after the cumulative 11 exceeded the queue; maker rebate fee −0.01 = −1 bp × 100 × 1 as configured. OBSERVED. The scenario is deterministic and **does not discriminate between the probabilistic models** (they coincide here). Data requirement: the caller must convert feeds into hftbacktest's event array; upstream tests are thin in Python (1 test file; Rust tests inline, not counted).

## T13 — ABIDES-JPM (agent-based LOB simulator)
Runs only in a Python 3.9 environment with pinned numpy 1.22 / pandas 1.2.4 / pomegranate 0.14.5 (not installable in the 3.12 stack). `rmsc04`, 20 simulated minutes, 1 117 agents: ≈3.5–4 s; same seed ⇒ identical book digest, different seed ⇒ different. OBSERVED. Repository dormant since 2023-12-13 (18 commits total). Useful as a scenario generator reference only.

## Summary
Deterministic, correct replay/book components exist and were verified on known answers: hftbacktest (book + queue), nautilus (book + fills + latency), nanobook (matching). None supplies PIT/revision semantics — they replay *given* event streams; provenance stays the caller's responsibility.
