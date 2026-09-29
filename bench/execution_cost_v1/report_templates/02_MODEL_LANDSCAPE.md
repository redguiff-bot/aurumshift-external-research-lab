# 02 — Model landscape (A–L) and what this study actually tested

The mission forbids a bibliography-only report. This page is a map: for each family, *what the model claims*, *what data it needs*, *fit for non-HFT (AurumShift scale)*, and *what this study did with it*.
The long sourced notes (formulas, URLs, provenance tiers `[V]` verified-in-session vs `[M]` from memory) are appended verbatim below; **every `[M]` formula must be re-derived before being coded into anything**, and the ones actually coded here (Roll, Corwin–Schultz, Abdi–Ranaldo, Almgren–Chriss cost form, square-root, propagator kernel) were coded from the formulas quoted in the notes and checked only against synthetic data with known truth (they can therefore be wrong in constants; see `12`).

Labels: PROVEN · OBSERVED · DOCUMENTED_CLAIM · INFERENCE · UNKNOWN.

| # | Family | Representative models | Data required | Non-HFT fit | Status in this study |
|---|---|---|---|---|---|
| A | Spread estimation | quoted / effective / realized spread; Roll (1984); Corwin–Schultz (2012); Abdi–Ranaldo (2017); EDGE (Ardia et al. 2024, OSS `bidask`); trade-flip estimator | L1 + trades (effective/realized); OHLC (proxies) | Effective/quoted: excellent. OHLC proxies: only as bound | **Executed**: synthetic grid (`06`), live quotes vs proxies (`05`,`06`), Binance klines (`06`) |
| B | Slippage | fixed bps; spread-proportional; vol-scaled; size/depth; square-root; L2 walk | L1, OHLCV, or L2 | Good | **Executed** (synthetic, live snapshot-to-snapshot) (`07`) |
| C | Market impact | Almgren–Chriss (2000) linear; square-root law (Bouchaud, Tóth…); propagator (Bouchaud et al. 2004); Obizhaeva–Wang (2013); Gatheral no-dynamic-arbitrage constraints | metaorder-tagged fills or full tape + L2 | Square-root/propagator meaningful for multi-child parent orders; linear AC weak | AC-linear, sqrt, propagator **executed** (synthetic); flow–return regression on Binance aggTrades **executed**; Obizhaeva–Wang/Gatheral: theory only (PARK/constraint) |
| D | Fill probability | constant p; price-through (Brownian first-passage); displayed-queue vs trade volume; hybrid; Cont–Stoikov–Talreja; queue-reactive (Huang–Lehalle–Rosenbaum) | trades; L1 size; **L3/queue events** for CST/QR | Simple ones fine; CST/QR need event data | Simple four **executed** (synthetic + live bounds); CST/QR **MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA** |
| E | Partial fills | depth-capped fills; probabilistic; participation caps | L2 | Good | **Executed** (depth-capped, `filled_fraction`) |
| F | Adverse selection | post-fill markout; realized spread; Kyle λ; VPIN | tape + mids | Markout/λ fine; VPIN contested (Andersen–Bondarenko) | markout, realized spread, λ **executed**; VPIN not executed |
| G | Maker/taker | Cartea–Jaimungal, Avellaneda–Stoikov style HJB; empirical fill/markout trade-off (Albers et al. 2025) | own quote–fill experiments | Only as a coarse decision rule | **Executed** decision grid (synthetic) + fill bounds (live) (`10`) |
| H | Scheduling | TWAP / VWAP / POV | volume profile | fine | TWAP (equal children) **executed**; VWAP/POV UNKNOWN (need intraday profile study) |
| I | Latency-to-price-risk | σ√L drift; winner's-curse on fills | timestamps, σ | simple bounded model adequate in RW regimes | **Executed** (synthetic sweeps, live drift, aggTrades drift) |
| J | Funding/borrow/roll | venue formulas; settlement discrete events; calendar spreads | rate histories, curves | essential | **Executed** on public data (`09`); FX/gold: UNKNOWN |
| K | Fragmentation | cross-impact, venue leadership | synchronous multi-venue books | matters via which book you walk | synthetic **executed**; live cross-venue snapshot dispersion **executed** |
| L | Implementation shortfall | Perold 1988; delay/spread/impact/opportunity/explicit decomposition | decision & arrival prices, fills | the accounting frame | ladder implemented & tested (`11`) |

Models discovered (named distinct models/estimators in this landscape and OSS probe): counted in the final block of `00`.

## Corrections to the appended notes (found while executing)

1. Latency arithmetic in note I: σ_annual = 60 %, L = 200 ms ⇒ σ√L = 0.6·√(0.2/31.536e6) ≈ 4.8e-5 = **0.48 bps**, not 0.15 bp (INFERENCE, arithmetic). Live BTC mid-drift over 1–4 s is measured directly in `10`.
2. Fee schedules for OKX/Bybit/Coinbase came from secondary aggregators and are UNKNOWN until the official tables are read; Binance futures 0.075 %/0.075 % is flagged unverified by the note itself. This study therefore treats fees as a **parameter** (5/2 bps and 10/8 bps taker/maker cells), never as a finding.
3. The "2026-prefixed arXiv IDs" cited in the notes come from the search tool and were not independently validated.
4. The square-root exponent for *current* crypto venues is UNKNOWN in the literature accessible here (one 2014 Mt.Gox-era paper; one non-peer-reviewed counter-example). This study's own Binance aggTrades flow–return exponent (0.67 for BTC 1-min bars, 0.85 ETH; `07`) is an **aggregate-flow regression**, not a metaorder study, and is confounded by reverse causality — it does not settle the question.

---

# Appendix — sourced landscape notes (verbatim)

@@landscape_notes@@
