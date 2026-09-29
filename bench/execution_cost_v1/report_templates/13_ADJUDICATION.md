# 13 — Adjudication

One verdict per serious model/component: `ADOPT_REFERENCE` · `ADAPT_CANDIDATE` · `PARK` · `REJECT`. **No overall score is assigned.** "Executed" = executed in this study on synthetic and/or public data (own reference implementation or OSS smoke run); "No" = discovered, documented, not run (reason in the last column or in `14`).
Verdicts are about *external reference value for a later local PAPER evaluation*, not about integration.

| # | Model / component | Family | Executed | Verdict | Why (evidence pointers) |
|---|---|---|---|---|---|
| 1 | Quoted spread (L1), distribution + snapshot age | A spread | Yes | ADOPT_REFERENCE | tick-bound majors: 1 tick; SOL 0.8 bps; only defensible cost of crossing (`06`) |
| 2 | Effective spread (aggressor + prevailing mid) | A spread | Yes (polled) | ADAPT_CANDIDATE | breaks with 2 s snapshots (6–55× on BTC); needs message-rate L1 (untested here) |
| 3 | Realized spread / post-trade markout | A/F | Yes | ADOPT_REFERENCE (diagnostic) | +0.3…+1.4 bps adverse at 30 s, CI ≠ 0 in 16/18 (`10`); not a taker cost |
| 4 | Roll (1984) | A spread | Yes | REJECT | 4.4–9.2 bps live vs ≤ 1.2 quoted |
| 5 | Corwin–Schultz (2012) | A spread | Yes | REJECT | volatility-driven; 0.2 bps → 1.2–12.4 synthetic; 0.8–1.5 bps Binance BTC vs 0.001 |
| 6 | Abdi–Ranaldo (2017) | A spread | Yes | REJECT | 0 at high σ, 1.7–4.5 live |
| 7 | High–low range proxy | A spread | Yes | REJECT | is a volatility measure |
| 8 | EDGE (`bidask`, Ardia–Guidotti–Kroencke 2024) | A spread, OSS | Yes | ADAPT_CANDIDATE | best OHLC estimator on synthetic grid; usable only as bound on ≥ 1 000-bar samples; stability poor on ≈ 50 bars |
| 9 | Trade-flip (consecutive opposite aggressor prints) | A spread | Yes | ADAPT_CANDIDATE | median = 1 tick on Binance BTC/ETH; needs aggressor flag + µs timestamps |
| 10 | Fixed 5 bps default | B slippage | Yes | REJECT | F2 |
| 11 | Per-instrument × size-bucket empirical cost table (calibrated constant) | B slippage | Yes | ADAPT_CANDIDATE | strongest MAE baseline when history exists (`07` §3.2) but transports poorly (60–80 % median error) — must be built per instrument from L2 history |
| 12 | Half-spread only ("zero slippage") | B slippage | Yes | REJECT | F1/E3 |
| 13 | Spread-proportional | B slippage | Yes | REJECT | F3 |
| 14 | Vol-scaled | B slippage | Yes | REJECT | F4 (no size term; coupling evidence weak for walk) |
| 15 | Size/depth-linear from L1 + 1 bp depth | B slippage | Yes | REJECT | F6 |
| 16 | Square-root law with cross-instrument Y | B/C | Yes | ADAPT_CANDIDATE | best transporter (36–53 %), OHLCV-only prior with ±50–100 % band and 3–5× tail flag |
| 17 | L2 book walk with visible-depth flag and staleness band | B slippage | Yes | ADOPT_REFERENCE | no systematic bias vs next snapshot (median ≤ 3.3 % of cost), exact in synthetic where depth visible, defined to 3M USD with 400 levels |
| 18 | zipline `VolumeShareSlippage` / `FixedBasisPointsSlippage` | B slippage, OSS | Yes (smoke) | ADOPT_REFERENCE (formula oracle for bar-level baselines only) | formulas verified by the probe; bar-close reference, no spread/book (`03`) |
| 19 | QuantConnect LEAN slippage/fill/fee models | B/E, OSS | No (source read) | ADOPT_REFERENCE (fee-model coverage as specification) | Apache-2.0; heavy install |
| 20 | Almgren–Chriss linear cost / schedule | C impact | Yes | PARK | mis-ranks schedules (F12); the OSS notebook is a valid trajectory reference (ADAPT for trajectory math only) |
| 21 | Propagator (Bouchaud et al.) + depletion recovery | C impact | Yes (synthetic) | ADAPT_CANDIDATE | needed only for multi-child/repeated orders; calibration from own runs, not from free data |
| 22 | Obizhaeva–Wang block-book model | C impact | No | PARK | equivalent to depth-linear + resilience; parameters UNKNOWN |
| 23 | Gatheral no-dynamic-arbitrage constraint (`δ+γ ≥ 1`) | C impact | No | ADOPT_REFERENCE (as constraint on any fitted kernel) | theory; [M] formula must be re-checked |
| 24 | Huberman–Stanzl permanent-impact linearity | C impact | No | PARK | theory constraint |
| 25 | Kissell I-Star | C impact | No | PARK | form UNKNOWN |
| 26 | Aggregate flow–return regression (Kyle λ / sqrt deciles) | C/F | Yes (Vision) | PARK | endogenous, not metaorder; use as diagnostic only |
| 27 | "Always fill at touch" (passive) | D fill | Yes | REJECT | F14–F17 |
| 28 | Constant fill probability | D fill | Yes | PARK | statistically equal to better models on synthetic; not identifiable live |
| 29 | Brownian price-through fill | D fill | Yes | PARK | optimistic by 0.17; usable only as an upper bound |
| 30 | Displayed-queue vs trade-volume fill | D fill | Yes | PARK | F15 |
| 31 | Hybrid through/queue fill | D fill | Yes | PARK | F16 |
| 32 | Fill bracket [P_lower(queue), P_through/P_upper] from tape | D fill | Yes | ADOPT_REFERENCE | honest about non-identifiability (`08`) |
| 33 | Depth-capped market-order fills (`filled_fraction`) | E partial | Yes | ADOPT_REFERENCE | exact wherever depth visible |
| 34 | Cont–Stoikov–Talreja queue model | D fill | No | PARK | needs L3/event intensities: `MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA` |
| 35 | Queue-reactive model (Huang–Lehalle–Rosenbaum) | D fill | No | PARK | same |
| 36 | hftbacktest queue/latency fill models | D fill, OSS | Yes (smoke) | PARK | HFT tick/L2-event feeds required (`03`) |
| 37 | nautilus_trader `FillModel` (Bernoulli) | D fill, OSS | Yes (smoke) | PARK | probability toggle, no evidence base |
| 38 | VPIN | F toxicity | No | PARK | contested (Andersen–Bondarenko) |
| 39 | Maker/taker break-even rule `P* = X/(X+2hs+Δfee)` with bracketed P | G maker/taker | Yes | ADAPT_CANDIDATE | `10`; result `MAKER_TAKER_UNDECIDABLE` when bracket straddles P* |
| 40 | HJB maker models (Avellaneda–Stoikov, Cartea–Jaimungal, Guéant–Lehalle–Fernandez-Tapia) | G | No | PARK | need own quote-fill experiments |
| 41 | TWAP (equal children) | H schedule | Yes | ADOPT_REFERENCE (as the test schedule) | used in all sliced experiments |
| 42 | VWAP / POV schedules | H schedule | No | PARK | intraday volume-profile study not done |
| 43 | Zero-mean σ_L√L latency band | I latency | Yes | ADOPT_REFERENCE | ±15 % at ≥ 4 s live; σ must be estimated at the latency horizon |
| 44 | Flow-conditional drift add-on | I latency | Yes (measured) | ADAPT_CANDIDATE | +0.6…+1.8 bps after strong flow (Vision) |
| 45 | Perp funding: settled per-venue rate × held notional at settlement instants | J funding | Yes | ADOPT_REFERENCE | `09`; venue-specific (corr 0.43–0.49 across venues) |
| 46 | Short borrow: venue+tier+date rate else `UNKNOWN_COST` | J borrow | Yes (contract) | ADOPT_REFERENCE | never 0; only base rate observable |
| 47 | Futures roll: calendar spread + 2 leg half-spreads | J roll | Yes (OKX curve) | ADOPT_REFERENCE (crypto dated futures) | 34–150 bps per step |
| 48 | FX swap points / gold financing / COMEX roll | J | No | PARK | no free reliable source used; structure documented only |
| 49 | Cross-venue routing / fragmentation-aware book choice | K | Yes (synthetic + live dispersion) | ADAPT_CANDIDATE | ×1.4–3.3 error if the wrong book is used |
| 50 | Implementation-shortfall ladder + fill-basis embedding contract | L / accounting | Yes | ADOPT_REFERENCE | `11` |
| 51 | Perold decomposition into delay/spread/impact/opportunity/explicit | L | Yes (in ladder) | ADOPT_REFERENCE | `11` |

OSS repositories (21 discovered and source-inspected; 9 smoke-executed): verdicts per repository in `03_OSS_COMPONENTS.md` (ADOPT_REFERENCE ×5, ADAPT_CANDIDATE ×1, PARK ×9, REJECT ×6 — as stated by the probe; note the zipline/LEAN/freqtrade/ccxt/bidask verdicts are "reference/oracle", never runtime dependencies).

Counts (computed from the table above by `build_reports.py`): models/components catalogued = @@n_models@@; executed in this study = @@n_exec@@; verdicts — ADOPT_REFERENCE @@n_adopt@@, ADAPT_CANDIDATE @@n_adapt@@, PARK @@n_park@@, REJECT @@n_reject@@.
