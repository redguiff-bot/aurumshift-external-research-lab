# 08 — Cost sensitivity

## Cost model (generic, deliberately not venue-specific)
Per side, in bps of traded notional: BTC/ETH **6**, other core assets **8**, holdout assets **10** — ≈5 bps taker fee plus 1/3/5 bps half-spread/slippage. Applied to |Δw| of the overlapping-tranche book (so turnover and cost are exact for the simulated policy). Funding is charged from actual settled Binance funding, per position sign. **Not modelled** (UNKNOWN, treated as *not zero*, hence the multipliers): market impact, VIP/maker fee tiers or rebates, queue/latency slippage, borrow, margin financing, exchange outages, tax. UNKNOWN_COST ≠ ZERO_COST: ×0.5 is shown only as an optimistic bound, never used for adjudication.

## Net Sharpe vs cost multiplier (primary specs) and break-even
`breakeven_x` = multiple of the assumed cost at which (gross − funding) = cost. Values <1 mean the primitive loses money at the assumed cost; values >1 leave a margin.
| primitive | gross_S | net Sharpe x0.5 | net Sharpe x1 | net Sharpe x2 | net Sharpe x3 | net Sharpe x5 | breakeven_x | fund_ann_pct |
|---|---|---|---|---|---|---|---|---|
| P01_TSMOM | +0.20 | -0.06 | -0.27 | -0.70 | -1.13 | -1.99 | +0.37 | +1.50 |
| P02_XS_RS7D | +0.63 | +0.27 | -0.13 | -0.92 | -1.72 | -3.30 | +0.84 | -0.62 |
| P03_REV4H | +0.09 | -1.73 | -3.58 | -7.31 | -11.05 | -18.56 | +0.03 | -0.68 |
| P04_VOLCOMP_BRK | +0.55 | +0.26 | -0.00 | -0.52 | -1.04 | -2.08 | +1.00 | +0.09 |
| P05_BRK_PERSIST | +0.47 | +0.16 | -0.11 | -0.65 | -1.19 | -2.26 | +0.79 | +1.79 |
| P06_FUND_CARRY | +0.45 | +0.50 | +0.24 | -0.29 | -0.82 | -1.89 | +1.45 | -5.58 |
| P07_PREMIUM | -0.24 | -1.11 | -2.10 | -4.08 | -6.05 | -9.99 | -0.06 | -4.14 |
| P08_OI_PRICE | +0.71 | +0.14 | -0.37 | -1.40 | -2.43 | -4.50 | +0.64 | +0.96 |
| P09_OI_FLUSH | +0.28 | -0.13 | -0.53 | -1.35 | -2.16 | -3.76 | +0.35 | -0.03 |
| P10_TAKER_IMB | -0.20 | -2.09 | -4.02 | -7.86 | -11.68 | -19.25 | -0.04 | -1.40 |
| P11_LIQ_SHOCK | -0.42 | -1.47 | -2.53 | -4.64 | -6.74 | -10.82 | -0.19 | -0.10 |
| P12_LEADLAG_BTC | -0.92 | -8.44 | -16.02 | -31.33 | -46.81 | -78.02 | -0.06 | -0.07 |
| P13_SEASON_HOD | +0.61 | -1.52 | -3.62 | -7.81 | -11.99 | -20.28 | +0.14 | +1.23 |
| P14_VRP_DVOL | +0.21 | +0.14 | +0.09 | -0.02 | -0.14 | -0.36 | +1.78 | +0.10 |
| P15_FUND_DIV | +0.22 | -0.46 | -1.13 | -2.46 | -3.78 | -6.44 | +0.15 | +0.25 |

## Reading
- Break-even multiples: only P14 (1.78), P06 (1.45), P04 (1.00) and P02 (0.84)/P05 (0.79) are near or above 1; the rest are ≤0.64. Those near 1 have insignificant gross edge, so a break-even near 1 is *zero edge with zero cost*, not margin of safety.
- At ×2 costs every primary spec is net-negative (best: P14 −0.02, P06 −0.29); at ×3 all remain negative. Costs, not signal decay, are the binding constraint for hourly-horizon primitives.
- Gross and net are reported separately everywhere; **no primitive is claimed profitable** and nothing here is a production-profitability statement.
- Cost/turnover of overlapping tranches at H=4 vs H=24: raising H reduces turnover ≈ proportionally but also weakens the (already tiny) 4h effects — see the secondary-horizon table in 05.
