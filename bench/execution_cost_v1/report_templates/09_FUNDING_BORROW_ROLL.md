# 09 — Funding, borrow, roll: accounting contracts and what free data can support

Required states (mission §10): `KNOWN_COST`, `ZERO_COST_PROVEN`, `UNKNOWN_COST`, `NOT_APPLICABLE`. **UNKNOWN is never mapped to zero.**
In the ledger (`contract/cost_contract.py`) `KNOWN_COST` is split into `MEASURED` (settled/observed) and `ESTIMATED` (forward-looking, model id required).

Data pulled for this section: Binance Vision monthly funding history (USD-M BTCUSDT/ETHUSDT, 2026-05…08), OKX public funding history (last ~3 months), OKX public
dated inverse futures curve and index, OKX public margin-borrow base rates. Script: `analysis/funding_borrow_roll.py`, output `results/funding_borrow_roll.json`.

## 1. Perpetual funding

Formula (DOCUMENTED_CLAIM, exchange help pages; see `02_MODEL_LANDSCAPE.md` J): `F = P + clamp(I − P, ±0.05 %)` with interest `I` ≈ 0.03 %/day, `P` a premium index, settlement every 8 h by default
(Binance: 00/08/16 UTC; interval can shrink to 1 h after cap/floor events). OKX and Bybit have the same structure with venue specifics.

Contract:

| State | Condition | Value |
|---|---|---|
| `MEASURED` | position open at a settlement instant; rate = venue's *settled* rate for that instrument/timestamp | `notional × rate` (long pays if rate>0) |
| `ESTIMATED` | forward period not yet settled; source must name the estimator (last settled, EWMA, premium-index projection) and carry a `lo/hi` band | band from the historical distribution below |
| `ZERO_PROVEN` | the position was flat at every settlement instant of the holding period (evidence: timestamps) **or** the venue lists a 0 % rate for that instrument in the settlement record | 0 |
| `UNKNOWN` | funding history unavailable for that venue/instrument, or holding period crosses an unrecorded interval change | not charged; net outcome withheld/interval |
| `NOT_APPLICABLE` | spot instrument, or dated future (no funding) | – |

Rules that fall out of the data:

* Funding is a *discrete* event at settlement instants (OBSERVED: Binance Vision history has strictly 8 h spacing, 0 gaps over 4 months for both symbols; `interval_hours` column is always 8). An intraday round trip that avoids 00/08/16 UTC pays **zero** funding (INFERENCE from the formula — must then be `ZERO_PROVEN`, not "ignored").
* Use the **settled venue-specific** rate. OKX-announced vs OKX-realised rates were identical in all 277 settlements checked per symbol (max abs diff 0.0 bps), but **OKX and Binance rates correlate only 0.43 (BTC) / 0.49 (ETH)** over 191 overlapping settlements and differ by 0.27 / 0.28 bps per period on average (mean |diff|, table below): borrowing the funding series of another venue is a measurable error, not a rounding one.
* The rate is signed and skewed: positive in 87 % (BTC) / 81 % (ETH) of periods so a long is a net payer in this sample (OBSERVED, 4 months, one regime).

@@funding_meta@@

Cost of holding a **long** perp (bps of notional, positive = long pays), all overlapping windows in May–Aug 2026:

@@funding_hold@@

Cross-venue check (OKX settled vs Binance settled, same timestamps):

@@funding_xvenue@@

Verdict: `FUNDING_ACCOUNTING_REFERENCE = settled-rate × held notional at settlement instants, per venue/instrument, states as above`. Free data suffices for *history*; the *forward* term is only a distribution (7-day 5–95 % band ≈ −0.8 … +17.3 bps for BTC (mean 9.3)).

## 2. Short borrow

* Spot short/margin borrow interest is venue-, tier- and asset-specific; hourly/daily accrual (DOCUMENTED_CLAIM in exchange docs; details UNKNOWN, `02` J.5). Shorting via perps replaces borrow with funding (§1).
* Free public data gives **only the venue's base margin rate** (OKX `interest-rate-loan-quota`): shown below; unit (per hour vs per day) is a DOCUMENTED_CLAIM I could not verify offline (UNKNOWN). Realised tier discounts, availability caps, and the historical series are **not** observable → the correct state for a PAPER short-borrow line is `UNKNOWN` unless a specific venue+tier+date rate is supplied.
* Illustration only (INFERENCE, arithmetic): at an assumed 5 %–50 % APR a 7-day short costs 9.6–96 bps of notional — the same order as the whole spread+slippage budget for a liquid pair. This is why `UNKNOWN → 0` is a first-order error, not a rounding one.

@@borrow@@

Contract: `borrow` ∈ {`MEASURED` (from a statement), `ESTIMATED` (venue base rate × time, band = tier range), `UNKNOWN`, `NOT_APPLICABLE` (long-only spot, perp/futures short)}. `ZERO_PROVEN` only if the venue documents a 0 % borrow for that asset/tier on those dates.

## 3. Futures roll

Roll cost for a long moving from expiry `a` to `b` (identity, PROVEN): `calendar_spread + half_spread_a + half_spread_b` (in bps of price), plus fees on two legs. Observed on the OKX BTC-USD dated inverse curve (public, live at the time of the query):

@@roll_curve@@

@@roll_pairs@@

Observations: annualised basis is ≈ 4–5 % on every tenor (OBSERVED, one snapshot); one-step rolls cost 34–49 bps (28-day steps) and 133–150 bps (91-day steps) all-in, of which the two legs' half-spreads are 1.6–20 bps (the far, illiquid contracts dominate). A "roll ignored" PAPER would silently drop this term.
Contract: `roll` = `NOT_APPLICABLE` for perps/spot and for holds that end before expiry; `MEASURED` at an actual roll; `ESTIMATED` from the curve snapshot otherwise (band = leg spreads); `UNKNOWN` when the instrument is a continuous/back-adjusted series whose roll dates or adjustment method are not recorded (the roll cost is then hidden inside the series).
Not tested: CME/COMEX gold, WTI, FX forwards/swaps — no free reliable quote/curve source was used (see mission policy and `14`). FX rollover/swap points and gold financing: `UNKNOWN` numerically; only the *structure* is documented (`02` J.6–J.8).

## 4. Summary

| Component | Reference accounting | Evidence level |
|---|---|---|
| Funding | discrete, settled, venue-specific, per held notional | OBSERVED on 4 months × 2 venues × 2 symbols |
| Borrow | venue+tier+date rate or `UNKNOWN` | free data insufficient ⇒ UNKNOWN is the supported state |
| Roll | calendar spread + 2 half-spreads at the roll | OBSERVED on one OKX curve snapshot; other asset classes UNKNOWN |
