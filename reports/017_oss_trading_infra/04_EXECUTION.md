# 04 — Execution realism: transaction-cost, queue, latency and fill models

Scope: which OSS components let a research replay charge realistic costs and respect latency/queue position, and what was *verified* rather than read. Scripts: `py/mt/tcm_microtest.py`, `hft_microtest.py`, `naut_microtest.py`, `port_microtest.py`, `zl_microtest.py`.

## Cost models
| Component | Model | Verified how | Result |
|---|---|---|---|
| **cvxportfolio 1.5.1** (GPL-3.0; one author) `TransactionCost(a, b, exponent)` | linear spread term `a·|z|` plus impact term `b·σ·|z|^exponent / volume^(exponent−1)` (DOCUMENTED_CLAIM for the closed form; behaviour below is OBSERVED) | 1-step `MarketSimulator` run from cash into `Uniform()` on 4 assets, constant volumes, capital 1 M and 4 M vs a zero-cost run | spread only (a = 0.001): cost **1 000.0** at 1 M = exactly 10 bps of traded notional; **4 000.0** at 4 M (ratio 4.000). Impact only (b = 1, exponent 1.5): 2 042.45 vs 16 339.58 → ratio **8.000000000000227** = 4^1.5. Simulation deterministic (2 runs equal). PROVEN on the functional form. |
| **hftbacktest** `trading_value_fee_model(maker, taker)` | fee = rate × traded value | one maker fill of 1 lot @ 100.0 with maker −0.01 % | fee −0.01 (rebate) booked |
| **nautilus_trader** `FeeModel`, `FillModel`, `LatencyModel` (constructor arguments of `add_venue`) | fee, probabilistic fill/slippage, latency | signature inspected; `FillModel(prob_fill_on_limit=…)` and `LatencyModel(base_latency_nanos)` instantiated and run | no change to the passive-fill outcome in my probe (9 configs); latency changed the event hash; the *cost* models were not exercised (UNKNOWN) |
| **zipline-reloaded** | default per-share commission `DEFAULT_PER_SHARE_COST = 0.001`, min $0 per trade; `VolumeShareSlippage(volume_limit, price_impact=0.1)` | constants read in `finance/commission.py` L25–28 and `finance/slippage.py` L269–270 | OBSERVED in source; equity-share oriented, not tuned for crypto/FX/gold |
| **backtesting.py** | `commission` (fraction or callable) | run with 0 only | not exercised beyond zero |
| **tcapy** (Apache-2.0) | TCA on real trade/order data | not run — needs Redis, Celery, Memcached, MongoDB/Arctic/KDB/InfluxDB and MySQL/Postgres (README); last commit 2022-05 | REJECT |

## Queue position, latency and fills (hand ground truth in `03`)
* **hftbacktest**: passive fill time follows the chosen queue model; order-entry latency shifts when an order becomes eligible; separate feed latency exists (`feed_latency`, `order_latency` accessors). PROVEN for the risk-adverse queue on one scenario; the three probabilistic queue models coincided in that scenario, so their *differences* are UNTESTED.
* **Nautilus**: fills when the simulated book crosses; no print-driven queue-aware passive fill reproduced (UNKNOWN whether supported).
* **Bar engines** (`backtesting.py`, `backtrader`, `vectorbt`): fill at next open/close by construction; no queue or latency notion. The next-open convention reproduced the oracle exactly.

## What no tested component provides
* **Calibrated impact/spread parameters** for the AurumShift venues or instruments: every model is a functional form the user must fit (INFERENCE — no OSS package tested ships calibrated crypto/FX/gold parameters).
* **Own-order market impact inside an L2 replay**: not tested in hftbacktest or Nautilus (UNKNOWN).
* **Fee schedules per venue** as data: only the fee *mechanism* exists.

## Composition the evidence supports (not an integration proposal)
`cost model (cvxportfolio form, or the same formula implemented locally)` ⟂ `replay core (hftbacktest / Nautilus)` are independent; nothing tested forces them into one platform. Because cvxportfolio is GPL-3.0 with a single author, the *formula* is the reusable reference and the package is an ADAPT candidate only after licence and maintenance are cleared.
