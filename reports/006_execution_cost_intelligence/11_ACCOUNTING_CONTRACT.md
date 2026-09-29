# 11 — Reference cost-accounting contract (no dual counting)

Reference artifact only: `bench/execution_cost_v1/contract/cost_contract.py` (≈ 90 lines, stdlib only) and the tests in `contract/tests_and_threats.py`.
It defines a decomposition that *can later be mapped* to a PAPER economic outcome; it is not an integration proposal and knows nothing about AurumShift.

## 1. The price ladder (each displacement has exactly one owner)

For a BUY (mirror for SELL):

```
decision_mid ──timing──► exec_mid ──spread──► touch ──slippage(walk)──► avg_fill ──fee──► net price
                            ▲
                            └── impact: displacement of exec_mid produced by OWN earlier fills (multi-child / repeated orders)
holding costs (time based, off the ladder):  funding · borrow · roll
```

| Line | Definition (bps of notional, + = cost) | Owner of the price rung |
|---|---|---|
| `fee` | exchange/broker commission on the fill (maker or taker rate × notional) | explicit cash flow |
| `timing` | `exec_mid − decision_mid` (latency, staleness, adverse drift) — zero mean in RW, non-zero mean under trend/adverse flow | exogenous price move |
| `spread` | `touch − exec_mid` = half the quoted spread at the execution instant | quote |
| `slippage` | `avg_fill − touch`: walking the book beyond the touch for *this* order's size (temporary, own-order, same instant) | book depth |
| `impact` | later fills' `exec_mid` displaced by earlier own fills (transient + permanent propagator/depletion) | own past flow |
| `funding` | settled perp funding at settlement instants × held notional | venue rate |
| `borrow` | short-borrow interest × time × notional | venue/tier rate |
| `roll` | calendar spread + both legs' half-spreads at a roll | curve |

Identity (PROVEN on the synthetic bench, residual 0.0 over every scenario × size × slicing run): `IS = timing + spread + slippage + impact`.

## 2. States per line

| State | Meaning | Charged in totals? | Requirements |
|---|---|---|---|
| `measured` | observed from a real fill / statement / settled record | yes | source |
| `estimated` | model output | yes (with optional `lo/hi` band) | model id + data regime in `source` |
| `embedded_by_basis` | the PAPER fill price already contains this rung | **no** (0 added) | automatic from fill basis |
| `zero_cost_proven` | evidence shows the cost is zero | yes (0) | `source` mandatory |
| `unknown` | no evidence, no defensible estimate | **never** (listed, `complete=False`) | – |
| `not_applicable` | structurally absent (spot has no funding…) | no | – |

## 3. Fill-basis → embedded rungs (the anti-double-counting table)

| PAPER fill basis | Already embeds | Lines that must still be charged |
|---|---|---|
| `MID` | nothing | spread, slippage, (timing), fees |
| `TOUCH` (bid/ask) | spread | slippage, fees |
| `BOOK_VWAP` | spread + slippage | fees (+timing if snapshot is stale) |
| `LAST_TRADE` | nothing provable (a print may be at bid or ask) | treat like MID |
| `BAR_CLOSE` | nothing provable, staleness unknown | treat like MID; spread/slippage `estimated` from OHLCV regime models or `unknown` |
| `REAL_FILL` (venue fill record) | spread, slippage, timing, impact | fees, holding costs |

`Ledger.put()` raises `DOUBLE_COUNT` when an `estimated/measured` charge is added for an embedded rung; `Ledger.seal()` marks unspecified embedded rungs `EMBEDDED_BY_BASIS` and unspecified other rungs `UNKNOWN` (never 0).

## 4. Evidence that the contract prevents dual counting

```json
{
 "ladder_identity_max_abs_residual_bps": 0.0,
 "basis_no_double_count": {
  "MID": {
   "embedded_in_fill": 0.0,
   "contract_extra": 1.6134885861328108,
   "total": 1.6134885861328108,
   "truth": 1.6134885861328108,
   "abs_err": 0.0
  },
  "TOUCH": {
   "embedded_in_fill": 0.5,
   "contract_extra": 1.1134885861328108,
   "total": 1.6134885861328108,
   "truth": 1.6134885861328108,
   "abs_err": 0.0
  },
  "BOOK_VWAP": {
   "embedded_in_fill": 1.6134885861328108,
   "contract_extra": 0.0,
   "total": 1.6134885861328108,
   "truth": 1.6134885861328108,
   "abs_err": 0.0
  },
  "overcharge_refused": true,
  "naive_stack_bps": 3.192102223663528,
  "truth_bps": 1.6134885861328108,
  "overcharge_ratio": 1.9783853763194685
 },
 "unknown_not_zero": {
  "unknown_listed": true,
  "net_withheld": true,
  "complete_when_all_resolved": true,
  "zero_proof_needs_source": true
 }
}
```

* **Basis invariance** (PROVEN, synthetic): for `MID`, `TOUCH`, `BOOK_VWAP` fills the sum "basis-embedded + contract charge" equals the ground-truth cost to the last digit (`abs_err = 0.0`), i.e. the same trade booked on three bases yields the same total.
* **Overcharge is impossible by construction**: `put(spread)` on `BOOK_VWAP` raises.
* **Naive stacking is not harmless** (OBSERVED, synthetic): full spread (1 bp) + a 1 bp "slippage" + a sqrt-law term that itself includes the half-spread charges **3.19 bps** for a trade whose true cost is **1.61 bps** (×1.98) — the exact failure the contract removes.
* Limits: the identity is algebraic, so the "proof" says the *contract is internally consistent*; it does not say a given estimator (sqrt, walk…) is unbiased. That is tested separately (`07`, `12`). Mapping to a real PAPER engine's price definitions is **UNKNOWN** here by design.

## 5. Suggested mapping to a PAPER economic outcome (reference only)

```
gross_pnl_bps          # from the PAPER mark at its own reference price
net_known_bps   = gross − Σ(measured + estimated lines)
net_upper_bound = gross − Σ(lower bounds of estimated lines)      # valid when unknown lines are costs ≥ 0
net_bps         = withheld if any applicable line is UNKNOWN       # never “unknown = 0”
```

Line-by-line: what is measured / estimated / embedded / unknown / not applicable, per data regime.

| Line | OHLCV_ONLY | L1_QUOTES | L2_BOOK | TRADES_PLUS_BOOK |
|---|---|---|---|---|
| fee | measured (schedule × tier) | same | same | same |
| timing | `estimated` band σ√L (zero-mean) + tail flag; `unknown` if trend/gap risk is material | same, σ from quotes | same | + flow-momentum drift (OBSERVED 0.6–1.2 bps after top-quartile flow, `06/10`) |
| spread | `estimated` from EDGE (OSS `bidask`) with tick-floor guard, else `unknown` | `measured` (quoted/half-spread) | `measured` | `measured` + effective spread from signed trades |
| slippage | `unknown` (or sqrt-law upper bound, band) | `estimated` size/depth only within the visible window, else band | `estimated`: book walk; `INSUFFICIENT_VISIBLE_DEPTH` flag beyond visible levels | book walk + staleness band from snapshot-to-snapshot error |
| impact | `estimated` sqrt/propagator only with a fitted Y and only for multi-child; else `unknown` | same | propagator/depletion layer over the walk | + Kyle-λ style check |
| funding | `measured` from venue history (independent of market-data regime) | same | same | same |
| borrow | `unknown` unless supplied | same | same | same |
| roll | `estimated` from curve if quotes exist; else `unknown` | `measured` at roll | `measured` | `measured` |

## 6. Usage sketch (reference)

```python
from cost_contract import Ledger, Line, State
L = Ledger(basis="BOOK_VWAP")                       # paper filled by walking a book -> spread+slippage embedded
L.put(Line("fee", State.MEASURED, 5.0, source="taker schedule"))
L.put(Line("funding", State.ESTIMATED, 1.3, lo=-0.1, hi=2.6, source="binance_vision 7d dist"))
L.seal()                                            # borrow/roll/timing/impact -> UNKNOWN (never 0)
L.total()   # {'known_bps': 6.3, ..., 'unknown': ['timing','impact','borrow','roll'], 'complete': False}
```
