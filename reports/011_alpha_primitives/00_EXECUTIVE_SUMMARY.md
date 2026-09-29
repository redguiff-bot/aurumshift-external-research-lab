# 00 — Executive summary — AURUMSHIFT_EXTERNAL_ALPHA_PRIMITIVE_DISCOVERY_V1

**Mode: EXTERNAL_RESEARCH_ONLY · NO_PRIVATE_AURUMSHIFT_CODE · NO_INTEGRATION.** Nothing here is a production-profitability claim, and nothing here says anything about compatibility with the private AurumShift repository.

## Verdict: `NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED`

We catalogued **43** candidate primitives across all 19 requested family labels (28 not executed: mostly missing point-in-time public data, tick/L2 volume, lookahead-tainted, or event counts too small), and executed **15** on 10 Binance USD-M perpetuals at 1h resolution over 2024-03 → 2026-08 (914 days), with DEV/HOLDOUT split, stationary-bootstrap uncertainty, a mechanical causality audit, cross-venue checks (OKX, Coinbase, Gate, Kraken, Hyperliquid, Deribit) and a falsification battery.

**Result: none of the 15 primitives is net-positive after generic taker costs in both DEV and HOLDOUT, none survives 1.5× costs, and no HOLDOUT net-Sharpe test survives multiplicity correction (Holm-15 p = 1.00).**

| primitive | family | gross Sharpe | net Sharpe | DEV net | HOLDOUT net | turnover/yr | tier |
|---|---|---|---|---|---|---|---|
| P01_TSMOM | momentum/trend | -0.06 | -0.61 | 0.66 | -1.94 | 314 | REJECTED |
| P02_XS_RS | cross-sectional relative strength | 0.16 | -0.60 | -0.68 | -0.52 | 197 | WEAK_GROSS_NOT_SIGNIFICANT |
| P03_REV_4H | mean reversion | 0.38 | -2.33 | -1.86 | -2.84 | 1052 | WEAK_GROSS_NOT_SIGNIFICANT |
| P04_DONCHIAN | breakout persistence | 0.17 | -0.19 | -0.17 | -0.20 | 230 | WEAK_GROSS_NOT_SIGNIFICANT |
| P05_VOL_SQUEEZE_BREAK | volatility compression/expansion | 0.66 | 0.10 | 0.45 | -0.27 | 60 | GROSS_INFORMATION_ONLY (not net-monetisable at generic taker costs) |
| P06_FUND_XS | funding divergence / carry (crowding fade) | 0.72 | -0.80 | -0.94 | -0.62 | 329 | GROSS_INFORMATION_ONLY (not net-monetisable at generic taker costs) |
| P07_BASIS_CARRY | carry / basis (delta-neutral) | 3.10 | 0.64 | 0.91 | flat/NA | 6 | GROSS_INFORMATION_ONLY (not net-monetisable at generic taker costs) |
| P08_SPOT_PERP_BASIS | basis (spot-perp z-score) | -0.39 | -1.45 | -1.74 | -1.10 | 308 | REJECTED |
| P09_OI_PRICE | open-interest / price divergence | 0.52 | -0.86 | -0.37 | -1.54 | 453 | WEAK_GROSS_NOT_SIGNIFICANT |
| P10_LIQ_FLUSH_PROXY | liquidation pressure (OI-flush proxy) | -0.31 | -0.74 | -0.04 | -1.28 | 51 | REJECTED |
| P11_TAKER_FLOW | volume imbalance | 0.61 | -3.08 | -3.46 | -2.67 | 940 | WEAK_GROSS_NOT_SIGNIFICANT |
| P12_ILLIQ_SHOCK | liquidity shock | 0.45 | -0.63 | -0.61 | -0.65 | 27 | WEAK_GROSS_NOT_SIGNIFICANT |
| P13_BTC_LEADLAG | cross-asset lead/lag | -0.09 | -5.81 | -5.74 | -6.14 | 1531 | REJECTED |
| P14_HOUR_SEASON | intraday seasonality | 0.85 | -11.58 | -11.26 | -11.91 | 4410 | GROSS_INFORMATION_ONLY (not net-monetisable at generic taker costs) |
| P15_RV_IV_VRP | realized vs implied vol (BTC/ETH only) | -0.02 | -0.13 | -1.14 | 1.02 | 77 | REJECTED |

Gross = price PnL + funding, before trading costs; net = after costs (5 bp taker + 1–3 bp slippage per side; UNKNOWN cost = 15 bp). Sharpe on daily PnL, √365.

## What was learned (in order of importance)

1. **Costs, not signals, are the binding constraint.** Break-even cost per side (gross return ÷ turnover) is 0.5 bp for hourly seasonality, 1.1 bp for 4h reversal, 1.3 bp for taker-flow, versus 6–8 bp paid. Only P05 (9.0 bp) and P07 (26 bp, but on ~0.3%/yr) clear the bar at 1×, and P05 fails at 1.5×.
2. **Weak positive *gross* information exists in four places, none net-monetisable here:** P07 funding carry (gross Sharpe 3.10, delta-neutral, ≈1.4%/yr of capital; the trigger never fired in the HOLDOUT because mean 8h funding fell from 7.6e-5 to 2.4e-5 — the carry compression that arXiv 2510.14435 also reports), P05 vol-squeeze breakout (gross 0.66, replicates on OKX/Coinbase prices but negative in the short Gate window, net ≈ 0, and its IC changes sign between DEV and HOLDOUT), P06 funding-crowding fade (gross 0.72, but ≈0 on majors and negative on minors, and the Hyperliquid-funding version has gross Sharpe -1.54), and P14 hour-of-day seasonality (gross 0.85, 4400 turns/yr). With 15 primitives, ≈1.5 raw p ≤ 0.10 gross hits are expected by chance; we have four.
3. **Baselines are hard to beat and the classic families do not survive.** TSMOM and Donchian gross Sharpe ≈0 (TSMOM +1.19 DEV → −1.36 HOLDOUT), XS relative strength ≈0, BTC→alt lead-lag ≈0 at hourly resolution, OI-flush proxy and spot-perp basis negative. The equal-weight long baseline earned 18.7%/yr price minus 5.4%/yr funding (Sharpe 0.20) — most directional primitives are correlated to nothing and earn nothing.
4. **Orthogonality is not the problem:** effective independent bets ≈ 10.4 of 14; the only redundant pairs are P01↔P04 (ρ=0.79) and P03↔P11 (ρ=−0.55, opposite signs of one flow-reversal effect). But orthogonal noise is still noise.
5. **Universe sensitivity is large.** On the 5-asset subset used for venue tests the same code gives gross Sharpe 0.91 for P02 (vs 0.16 on 10 assets), 0.57 for P04 (vs 0.17) and 1.30 for P14 (vs 0.85): outcomes move by ±0.7 Sharpe with the asset set, which is itself a measure of how much of any gross "edge" here is selection noise.
6. **Statistical power is limited.** 914 days give a HOLDOUT net-Sharpe 90% bootstrap band of roughly ±1.5 (see 05): a true net Sharpe below ~1 would not be detected. The verdict means *no primitive is supported by this evidence*, not that none can exist — especially with maker execution, lower-fee tiers, other resolutions or other universes, none of which were tested.
7. **Mechanical forward safety is good:** all 15 signal implementations pass a truncation (future-deletion) audit; 0 executed primitives are LOOKAHEAD_RISK; 6 need receipt-stamped live capture (funding, OI, DVOL, cross-market basis) before they could be forward-safe in practice.

## Deviations and honesty notes
* P07's threshold and P12's trigger were mis-specified in the pre-registered first pass and were re-selected on the DEV window only (05 §5.4). Both remain untradeable, so the deviation does not change the verdict.
* Term-structure (options surface), event-driven macro, order-book/tick microstructure and true liquidation-print primitives were **discovered but not executed** (no public point-in-time history, insufficient event count, or tick-volume scope): the corresponding families are covered by a documented contract only (01–03) and, for liquidation pressure, by an OI-flush *proxy* (P10).
* OSS (Qlib/freqtrade/vectorbt) was assessed from web documentation only; source code was not inspected.

## Final block
```
PRIMITIVES_DISCOVERED=43
PRIMITIVES_EXECUTED=15

FORWARD_SAFE_COUNT=9   # executed primitives classed strictly FORWARD_SAFE (a further 6 executed are FORWARD_SAFE_WITH_RECEIPT_STAMP; catalogue-wide: 21 + 12)
LOOKAHEAD_RISK_COUNT=7   # discovered candidates classed LOOKAHEAD_RISK (0 among executed; OFFLINE_ONLY discovered: 3)

NONREDUNDANT_CANDIDATES=4   # gross-information-only tier AND max|rho|<0.5 AND R2<0.35: P05_VOL_SQUEEZE_BREAK, P06_FUND_XS, P07_BASIS_CARRY, P14_HOUR_SEASON. NOT net-positive.
REGIME_DEPENDENT_CANDIDATES=4   # statistical flags only (45 tests, ~2 expected by chance): P02_XS_RS, P03_REV_4H, P08_SPOT_PERP_BASIS, P12_ILLIQ_SHOCK

NET_POSITIVE_EXTERNAL_CANDIDATES=0

ANY_DROP_IN_STRATEGY=FALSE
LOCAL_INTEGRATION_AUTHORIZED=FALSE

FINAL_VERDICT=NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED
```
