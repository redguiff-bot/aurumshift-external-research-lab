# 01 — Realistic PAPER execution threat model (E1–E15)

Scope: external research only. "Naive PAPER accounting" below means a hypothetical simulator that books fills at a reference
price with no execution frictions. Nothing here describes or inspects AurumShift code.

Labels: PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN (see `claude.md` doctrine).

## 1. Method

For each adversarial case we compute the **naive** value a frictionless PAPER would book and the **correct** value from one of:

* the deterministic synthetic microstructure world (`bench/execution_cost_v1/synthetic/synth.py`) — a controlled *truth*, not reality;
* public data (Binance Vision funding history; OKX public dated-futures curve) for the holding-cost cases E8/E10.

All numbers below are produced by `bench/execution_cost_v1/contract/tests_and_threats.py` and stored in
`results/threat_matrix_and_contract_tests.json`. Units: bps of notional (unless stated). Sign: positive = cost to the trader.
Parameters of the synthetic world are documented in `04_SYNTHETIC_BENCH.md`; they are illustrative, not calibrated to a venue
(OBSERVED live top-of-book depth is much more concave than the synthetic base book, see `05`/`07`).

## 2. Threat matrix (naive vs correct)

| id | name | naive | correct | error | unit |
|---|---|---|---|---|---|
| E1 | mid-price fill fantasy | 0.00 | 0.81 | -0.81 | bps |
| E2 | zero spread | 0.00 | 0.50 | -0.50 | bps |
| E3 | zero slippage (spread only) | 0.50 | 1.68 | -1.18 | bps |
| E4 | infinite liquidity (fill at touch) | 0.50 | 360.56 | -360.06 | bps |
| E5 | fill at stale quote (trend, lat 3s) | 0.00 | 1.63 | -1.63 | bps |
| E5b | stale quote across gap | 0.00 | 13.58 | -13.58 | bps |
| E6 | full fill though depth insufficient | 1.00 | 0.88 | 0.12 | filled_fraction |
| E7 | no adverse selection (passive always fills at touch) | 1.50 | 4.24 | -2.74 | bps |
| E8 | funding omitted (perp long held 7d, BTC, May-Aug 2026 rolling windows) | 0.00 | 9.35 | -9.35 | bps |
| E9 | borrow unknown treated as zero | 0.00 | n/a | n/a | bps |
| E10 | roll ignored (OKX BTC-USD 261127->261225, long) | 0.00 | 33.81 | -33.81 | bps |
| E11 | latency ignored (random walk, lat 5s) | 0.00 | 2.01 | -2.01 | bps (1 sd of drift; mean~0) |
| E12 | quote disappears before execution (depth x0.15, spread x3) | 1.68 | 5.51 | -3.83 | bps |
| E13 | market order crosses many levels (10M USD) | 0.50 | 5.72 | -5.22 | bps |
| E14 | 5 correlated simultaneous orders (500k each) priced independently | 2.28 | 5.65 | -3.37 | bps/order |
| E15 | 5 repeated orders 1s apart (depletion, rho=0.05/s) | 2.28 | 5.10 | -2.82 | bps/order |

Reading guide (OBSERVED from the run, INFERENCE where stated):

* E1–E3, E13: even at a 0.5 bps half-spread the frictionless accountant under-charges by 0.8 bps (100k USD) up to 5 bps (10M USD). The error is *size dependent*, so a constant correction cannot fix it.
* E4/E6: with a thin book, "infinite liquidity" mis-prices a 50M USD order by ~360 bps and books 100 % fills when only ~88 % is executable in the synthetic thin-book case (`filled_fraction`).
* E5/E5b/E11: latency drift is **zero-mean** in a random walk (mean ≈ 0, sd = σ√L) but has a **non-zero mean** under trend/gap/adverse flow — a symmetric noise band is enough for the former, not for the latter (see `10_MAKER_TAKER_LATENCY.md`).
* E7: assuming a passive order always fills at the touch mis-states cost by ~2.7 bps in the shown cell; the error grows with drift (see `08`/`10`).
* E8/E10: funding and roll are not small: 7-day BTC perp funding was on average **9.4 bps** (p05–p95 shown in `09`) of notional; a one-roll calendar step on the OKX BTC-USD curve cost **~34 bps** all-in (OKX BTC-USD 261127→261225). Omitting them is a first-order error for any holding period ≥ days.
* E9: borrow has **no defensible numeric value** from free data → must be `UNKNOWN_COST`, not 0 (see contract below).
* E14/E15: 5 simultaneous same-side orders of 500k USD each are charged 2.28 bps/order independently vs 5.65 bps/order when they walk one book (×2.5); five sequential children 1 s apart cost 5.10 vs 2.28 bps/order (×2.2); the penalty decays with the recovery time (`07`).

## 3. Expected correct behaviour (requirements on any PAPER cost layer)

| Case | Required behaviour | Cost-line state |
|---|---|---|
| E1 mid fill | price at an *executable* reference (touch or book VWAP) or add spread+slippage lines | spread, slippage ∈ {ESTIMATED, MEASURED, EMBEDDED_BY_BASIS}; never silently absent |
| E2 zero spread | no quote ⇒ spread is UNKNOWN (not 0) | `UNKNOWN` |
| E3 zero slippage | size-dependent walk/impact line whenever size is not negligible vs depth | ESTIMATED (L2 walk) or UNKNOWN (OHLCV-only, then bounded estimate) |
| E4/E6 infinite/insufficient liquidity | cap by visible depth, report `filled_fraction`, unfilled quantity is *not* free (opportunity cost line or reject) | fill fraction propagated |
| E5 stale quote | fill against price at *arrival* time (decision time + latency); staleness age is an input | timing line ESTIMATED |
| E7 no adverse selection | passive fill probability < 1 with a chase/cancel leg; post-fill markout tracked | fill model + timing |
| E8 funding omitted | accrue at exchange settlement instants for the actual held quantity | funding `MEASURED` (settled) / `ESTIMATED` (forward) |
| E9 borrow unknown | never 0; net outcome withheld or returned as an interval | `UNKNOWN` |
| E10 roll ignored | roll = calendar spread + both legs' half-spreads at roll | roll `MEASURED`/`ESTIMATED` |
| E11 latency ignored | bounded zero-mean perturbation for RW-like regimes; explicit tail flag otherwise | timing band |
| E12 quote disappears | staleness stress band on slippage (depth ×0.15, spread ×3 in the bench ⇒ +3.8 bps at 1M USD) | slippage + band |
| E13 multi-level cross | integrate the walk over levels | slippage ESTIMATED |
| E14 correlated simultaneous | net the aggregate flow against **one** book; never price each order against a fresh book | impact/slippage on aggregate |
| E15 repeated orders | book depletion + recovery memory across orders | impact ESTIMATED with memory |

## 4. UNKNOWN_COST ≠ ZERO_COST

The reference contract (`contract/cost_contract.py`, `11_ACCOUNTING_CONTRACT.md`) makes the distinction structural:

* `UNKNOWN` lines never contribute to totals; `Ledger.total()` lists them in `unknown`, `complete=False`;
* `Ledger.net_outcome_bps` deliberately returns `net_bps_if_unknown_were_zero = None` and only exposes an *upper bound* (gross − known lower bound) and a *known-only* figure;
* `ZERO_PROVEN` must carry a `source` (assertion enforced) — a zero must be evidenced, an absence of evidence stays `UNKNOWN`;
* attempting to add an `ESTIMATED/MEASURED` charge for a rung that the fill basis already embeds raises `DOUBLE_COUNT`.

Contract test results (PROVEN by execution on the synthetic ladder; see limits in `14`):

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

## 5. What this threat model does *not* show

* It does not show the magnitude of any real venue's errors: the synthetic truth is constructed. The live/empirical counterparts of E1–E4 and E12 are in `05_PUBLIC_DATA_EXPERIMENT.md`.
* E9 has no numeric "correct" value on purpose. OKX publishes a base margin borrow rate (`results/funding_borrow_roll.json`, unit unverified) but the tier, availability and realised interest are not observable from free public data ⇒ UNKNOWN (INFERENCE).
