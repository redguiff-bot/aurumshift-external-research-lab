# 11 — Limitations

1. **Power.** 914 days, 10 highly correlated assets: HOLDOUT net-Sharpe bootstrap bands are ≈±1.5 wide. Absence of support ≠ proof of absence.
2. **Multiplicity.** 15 primitives × several diagnostics × 45 regime tests. Raw p-values are reported; Holm is applied only to the 15 holdout tests. Any single "significant" flag should be assumed spurious until replicated.
3. **Pre-registration is partial.** Parameters were fixed before viewing results except: P07 threshold and P12 trigger (re-selected on DEV after a degenerate first pass, 05 §5.4); the placebo null design (circular shift → block sign randomisation after seeing the circular null was contaminated); IC definition (centered → uncentered after inspecting an inconsistent centered IC); P14/P15 code boundary fixes. The first-pass P07/P12 numbers were seen.
4. **Costs are generic assumptions, not measured fills.** Taker 5 bp + 1–3 bp slippage; no market impact, no queue/maker modelling, no funding-timing slippage, no borrow/margin cost, no capital-efficiency accounting for the carry pair, no exchange counterparty risk. Real fees depend on tier/rebates. UNKNOWN cost was set to 15 bp, not zero.
5. **Execution timing.** 0-latency close-to-close fills (+1..+6 bar latency is falsified, but intrabar execution, partial fills and rate limits are not).
6. **Universe/survivorship.** 10 ex-post liquid Binance perps; new listings and delistings excluded; equal-notional weights overweight high-vol alts; no vol targeting.
7. **Resolution.** 1h bars only; seasonality, quarter-hour and microstructure effects live at finer scales (D02, D23, D24 not tested).
8. **Data.** Binance is the sole full-history source; other venues cover 5 assets with shorter (Gate, Hyperliquid, Kraken) windows. OI timestamp semantics undocumented (conservative +5 min). No historical liquidation prints (P10 is a proxy). DVOL is one tenor; no PIT options surface, so term-structure/skew/GEX are unevaluated.
9. **Regime analysis** uses three simple causal labels; regime-conditional returns are descriptive, not filters, and 3-state splits with ~300 days each carry wide error bars.
10. **Literature layer is DOCUMENTED_CLAIM.** Papers were located via search snippets/abstracts and not independently replicated; OSS projects were not code-inspected; ~10 searches is not a systematic review.
11. **Stat details.** Sharpe on daily aggregated PnL with √365; bootstrap is stationary (7-day blocks); regressions in 06 use plain OLS t-stats without HAC; PCA participation ratio excludes P07; IC uses weekly blocks.
12. **No claim** of production profitability, of compatibility with AurumShift, or that any listed primitive should be integrated.
