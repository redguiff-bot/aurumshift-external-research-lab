# 10 — Maker vs taker, and latency

## Part A — Is the maker/taker choice practically modelable without HFT queue simulation?

### A.1 Structure (PROVEN arithmetic, relative to arrival mid, BUY)

* taker: `half_spread + walk + fee_t`
* maker (post at the touch, wait H, then chase with a market order): `P·(−half_spread + fee_m) + (1−P)·(drift_nofill + half_spread + walk + fee_t)`
* ⇒ `maker − taker = −P·(2·half_spread + Δfee) + (1−P)·drift_nofill`, with `Δfee = fee_t − fee_m`.
* break-even fill probability **P\* = X / (X + 2·half_spread + Δfee)** where `X = E[drift | no fill]` is the cost of being left behind.

Three inputs are needed and only one of them is cheaply observable: the spread (L1), the fee gap Δfee (a schedule: UNKNOWN for OKX/Bybit/Coinbase official tables here, `02` M; **parameterised** below), and the pair (P, X) — the fill probability and the opportunity cost, which depend on queue position and on alpha/drift over the waiting horizon.

### A.2 Synthetic: the decision is about drift, not about the fill model

432 cells (queue 0/0.5/1, aggressor volume, drift 0/0.1/0.4 bps/s, flow informativeness, σ, fee pair (2,5) or (8,10), spread 1 or 5 bps), 800 trials each, H = 60 s:

@@maker_shares@@

By drift (bps/s; positive = price runs away from a passive buyer, i.e. the strategy has alpha in the direction of the trade):

@@maker_grid@@

By fee pair and queue position:

@@maker_grid_fee@@

@@maker_grid_q@@

Decision quality of fill models (accuracy = agrees with the truth on "maker or taker?"; regret = extra cost of the model's choice vs the best choice; "alpha_aware" means the model is *told* the true drift, "blind" means it assumes zero drift):

@@decision@@

* **All fill models are equally wrong when the drift is unknown** (accuracy 62 %, regret 4.3 bps — identical to always-maker). The variable that decides is `drift_nofill` (the opportunity cost), i.e. the strategy's own alpha horizon, not the queue.
* When drift is *given*, the **calibrated constant `p`** reaches 95 % accuracy (regret 0.03 bps) and beats the price-through (70 %, 2.8 bps), displayed-queue (71 %, 2.1 bps) and hybrid (65 %, 3.8 bps) models: in this world **complexity in the fill model buys nothing**.
* Averaged over the whole grid maker is **more** expensive than taker in both fee sets (by 1.7 bps at fees (2,5) and 2.4 bps at (8,10); tables above) because the grid contains many high-drift cells; maker still wins in 62 % of the cells. The average hides the structure: it is the cell-level drift/queue combination that decides.
* Limits: synthetic; the constant p is fitted in-sample on the same grid (an optimistic baseline); real cancellations are not modelled in the truth beyond a single cancel rate.

### A.3 Live: what public data can and cannot say

For 9 series × 30 s, hypothetical bid at the touch (`08` §3). Post-fill adverse markout (mid 30 s after the fill vs the fill price, positive = adverse for a buyer) versus the unconditional markout, with a 20-snapshot block-bootstrap 95 % CI of the difference:

@@live_fill@@

* **Adverse selection is present and measurable**: conditional − unconditional = +0.29 … +1.40 bps in all 18 series×horizons, with the 95 % CI excluding 0 in 16 of 18 (the two exceptions are OKX SOL). For BTC on OKX it is +0.55 bps — ~90× the half-spread. OBSERVED for this one window (n ≈ 410–490 overlapping windows per series).
* **Opportunity cost X is large** relative to the spread: when the bid is not touched within 30 s the mid has risen by 3.3–6.9 bps on average (front-of-queue definition). Break-even fill probabilities:

@@live_breakeven@@

Reading: with a zero fee gap, a passive BTC/ETH order at the touch needs P > 0.94–1.0 to beat the taker (the half-spread is ~0.006 bps, there is nothing to save); with a 2 bps fee gap P\* ≈ 0.62–0.70 lies **inside** the observable bracket [P_lower, P_upper] (P_lower 0.36–0.76, P_upper 0.79–0.90) for 7 of 9 series — the public data cannot tell whether maker wins there (Coinbase BTC/ETH have P_lower above P\*: maker wins even at the back of the queue); with a 5 bps gap P\* ≈ 0.39–0.53 and maker wins even at the back of the queue in 7 of 9 series (ambiguous for OKX SOL and Kraken SOL).

### A.4 Verdict

* Maker/taker **can be modelled as a decision rule** `maker iff P·(2·hs + Δfee) > (1−P)·X`, but its inputs `P` and `X` are **not identifiable from free data**: `P` only within a bracket 0.07–0.44 wide (mean 0.27), `X` only conditionally on an alpha horizon. Where the bracket straddles `P*` (typical for fee gaps ≈ 1–3 bps, i.e. today's spot tiers if the secondary fee data are right, UNKNOWN), the choice is **unjustifiable from public data** and must be flagged `MAKER_TAKER_UNDECIDABLE`.
* A defensible reference PAPER policy is therefore to keep the choice as an *input* (order-type flag) and cost both legs: taker fully (`spread + walk + fee`), maker as bracket (`fill_prob ∈ [P_lower, P_upper]`, unfilled remainder charged at chase cost with `X` from the live conditional distribution above, and adverse markout as a diagnostic).
* Cancellation risk (orders cancelled on drift, on venue events) is not observable here.

## Part B — Latency at AurumShift scale (no HFT assumptions)

### B.1 Timeline model

`t_decision → (system delay) → t_submit → (network + venue) → t_arrive/t_fill`, and the market observation `t_obs ≤ t_decision` has an age. Price risk = drift of the executable price from `t_obs` (what the model saw) to `t_fill`:
`total_age = (t_decision − t_obs) + (t_submit − t_decision) + (t_fill − t_submit)`. The contract's `timing` line owns this rung (`11`). Measured pieces:

* REST round trips (public endpoints from this sandbox, p50): OKX 275–278 ms, Coinbase 76–166 ms, Kraken 161–164 ms (`05`). These are *this environment's* numbers, not AurumShift's (UNKNOWN).
* Mid drift over horizon (live, snapshots ≥ 4 s so that the sampling gap does not blur the horizon):

@@live_drift@@

* Binance aggTrades last-trade price drift, all horizons (4 / 2 days):

@@vision_drift@@

### B.2 Findings (OBSERVED)

1. **Unconditional mean drift is ≈ 0** (|mean| ≤ 0.42 bps even at 30–60 s) and **the standard deviation follows σ√L within ~10–15 % at ≥ 4 s** live (e.g. OKX BTC: 1.75 bps at 4 s vs 1.55 predicted; 4.43 vs 4.23 at 30 s). A zero-mean symmetric band `σ√L` is thus adequate for the *mean* cost.
2. **σ must be estimated at the latency horizon**: on Binance tape `sd/√h` falls from 3.25 (0.1 s) to 1.96 (1 s), 1.56 (10 s), 1.29 (60 s) for BTC — microstructure noise inflates short-horizon variance; extrapolating a 1-minute σ to a 100-ms latency would *under*-state the band by ~2.5×.
3. **Drift is conditionally biased**: after the top quartile of 1-second signed flow, the next 1–30 s return continues in the flow direction by +0.6 … +1.8 bps (BTC 0.88 at 1 s, ETH 0.66). A random-walk perturbation misses this adverse-flow term, which is the mechanism behind the maker adverse selection in A.3 and the taker slippage-under-latency in `04` (trend/gap rows).
4. **Scale vs spread**: for BTC on OKX the 4-s drift sd (1.75 bps) is ~300× the half-spread and ≥ 4× the book-walk cost of a 100k USD order (0.37 bps): at these venues **timing variance, not spread, dominates the cost distribution** (the mean is still ~0).
5. Tail: synthetic gap scenario (+15 bps) shifts every model by ≈ 13 bps; FX/gold/WTI hourly series show **session gaps** with mean |gap| of 11.5 bps (EURUSD), 54 bps (XAU futures), 250 bps (WTI continuous, roll-contaminated) versus 1-hour σ of 6.5 / 31 / 75 bps (`results/fx_gold_ohlc.json`): weekend/rollover gaps are ≈ 1.1–3.3 σ_hour and cannot be handled by a latency perturbation.

### B.3 Is a simple bounded perturbation enough?

* **Yes** for the *expected* cost of taker orders in RW-like regimes at 0.1–30 s latency: `timing ~ N(0, (σ_L√L)²)` with σ_L calibrated at horizon L (synthetic `rw`, `meanrev`; live BTC/ETH), reported as a band, mean 0.
* **No** for (i) flow-conditional drift (needs `E[drift | signed-flow z-score]` from a tape: available from free aggTrades-like data), (ii) gaps/session boundaries (needs an explicit gap flag/band; FX/gold/commodities have weekend gaps that dominate), (iii) stale-snapshot risk when the book was thin (`withdraw`).
* A stronger model than "bounded perturbation" is warranted only for (i), and the minimal version is an additive conditional mean `β·flow_z·σ√L` fitted on a tape; no HFT-style latency-arbitrage or queue-jumping model is needed at this scale (INFERENCE).
