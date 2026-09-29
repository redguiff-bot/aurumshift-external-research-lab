# 09 — Falsification

Every stress is applied to the pre-declared primary spec of each primitive, FULL sample unless noted (script `py/falsify.py`; table `results/falsification_table.json`). Values are **net Sharpe** unless the column says gross.

| test | how |
|---|---|
| higher costs | ×2, ×3, ×5 (and ×0.5 optimistic) |
| wrong venue | signal computed from **Coinbase spot** bars, P&L on Binance perps, TEST window, 9 assets (price-only primitives only; `venue_base_gross` = same assets/window with Binance-derived signal) |
| different asset | holdout universe DOT ATOM NEAR TRX BCH ETC (BTC used only as leader for P12); N/A for P14, P15 |
| regime reversal / high vol / low vol | see 07 (bucketed net/gross Sharpe; no primitive flips significantly) |
| missing data | 10% / 25% of bars per asset randomly missing (3 seeds); features from last-observation-carried-forward feed, no position on missing rows (extra turnover) |
| stale data | random 3-bar frozen runs, 10% / 25% coverage; engine trades on stale features unaware |
| parameter perturbation | all look-backs ×0.5, 0.75, 1.5, 2 (min/max reported) |
| latency | +1 and +2 bar execution delay |
| null / control | 150 placebo signals; planted-future signal (must be detected); 3H-misaligned control (must be ≈0) |

## Battery table (net Sharpe; hold_* and venue_* columns are gross where labelled)
| primitive | base_net | delay1 | delay2 | cost_x2 | cost_x3 | cost_x5 | miss10 | miss25 | stale10 | stale25 | k_min | k_max | hold_gross | hold_net | venue_base_gross | venue_cb_gross |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P01_TSMOM | -0.27 | -0.22 | -0.18 | -0.70 | -1.13 | -1.99 | -0.32 | -0.39 | -0.26 | -0.25 | -0.37 | +0.12 | +0.07 | -0.57 | -0.42 | -0.41 |
| P02_XS_RS7D | -0.13 | -0.17 | -0.21 | -0.92 | -1.72 | -3.30 | -0.41 | -0.81 | -0.15 | -0.21 | -0.36 | +0.07 | +0.48 | -0.29 | +0.35 | +0.27 |
| P03_REV4H | -3.58 | -3.74 | -3.95 | -7.31 | -11.05 | -18.56 | -3.71 | -3.93 | -3.70 | -3.88 | -3.96 | -2.39 | -0.22 | -4.96 | -0.92 | -0.91 |
| P04_VOLCOMP_BRK | -0.00 | -0.16 | -0.10 | -0.52 | -1.04 | -2.08 | +0.01 | -0.03 | -0.00 | +0.01 | -0.31 | +0.12 | +0.30 | -0.47 | +0.77 | +0.94 |
| P05_BRK_PERSIST | -0.11 | -0.07 | -0.05 | -0.65 | -1.19 | -2.26 | -0.16 | -0.26 | -0.11 | -0.11 | -0.54 | +0.02 | +0.42 | -0.34 | -0.04 | -0.11 |
| P06_FUND_CARRY | +0.24 | +0.24 | +0.24 | -0.29 | -0.82 | -1.89 | -0.18 | -0.87 | +0.23 | +0.25 | -0.18 | +0.55 | +0.16 | -0.08 | nan | nan |
| P07_PREMIUM | -2.10 | -2.10 | -1.93 | -4.08 | -6.05 | -9.99 | -2.47 | -2.98 | -2.07 | -1.97 | -2.67 | -1.14 | +0.19 | -2.37 | nan | nan |
| P08_OI_PRICE | -0.37 | -0.47 | -0.57 | -1.40 | -2.43 | -4.50 | -0.42 | -0.55 | -0.36 | -0.39 | -0.78 | -0.13 | +0.32 | -1.09 | nan | nan |
| P09_OI_FLUSH | -0.53 | -0.37 | -0.15 | -1.35 | -2.16 | -3.76 | -0.47 | -0.50 | -0.51 | -0.43 | -0.83 | +0.45 | +0.01 | -1.13 | nan | nan |
| P10_TAKER_IMB | -4.02 | -3.95 | -3.91 | -7.86 | -11.68 | -19.25 | -4.29 | -4.83 | -4.09 | -4.06 | -5.55 | -2.10 | +0.36 | -4.53 | nan | nan |
| P11_LIQ_SHOCK | -2.53 | -2.71 | -3.17 | -4.64 | -6.74 | -10.82 | -2.50 | -2.52 | -2.48 | -2.48 | -2.75 | -2.09 | -0.56 | -2.91 | -0.89 | -0.54 |
| P12_LEADLAG_BTC | -16.02 | -16.61 | -16.58 | -31.33 | -46.81 | -78.02 | -16.78 | -17.22 | -17.16 | -18.03 | -16.02 | -13.27 | -0.93 | -16.35 | +0.47 | +0.41 |
| P13_SEASON_HOD | -3.62 | -4.46 | -5.23 | -7.81 | -11.99 | -20.28 | -4.00 | -4.58 | -3.89 | -4.34 | -4.54 | -3.40 | +0.39 | -5.07 | -0.81 | -0.99 |
| P14_VRP_DVOL | +0.09 | +0.11 | +0.13 | -0.02 | -0.14 | -0.36 | -0.02 | -0.10 | +0.01 | +0.03 | -0.05 | +0.75 | nan | nan | nan | nan |
| P15_FUND_DIV | -1.13 | -1.16 | -1.20 | -2.46 | -3.78 | -6.44 | -1.40 | -1.75 | -1.08 | -1.10 | -1.27 | -0.98 | nan | nan | nan | nan |

## Controls
- Placebo (150 random EWMA-24h signals, TS, H=24, same costs): gross t sd 0.94 (≈1 ⇒ t-stats are well calibrated), p95 1.58, p99 2.05; net-t p95 -1.62.
- Planted future signal: gross Sharpe 26.7 (H=4), 16.7 (H=24); with one extra bar of delay 21.7/15.9; 3H-misaligned ≈ -0.39/-0.60. The simulator is neither blind nor leaky.

## What broke
- **Costs**: every primary spec is net-negative at ×3; only P06 (+0.24) and P14 (+0.09) are positive at ×1 and both are negative or ≈0 at ×2.
- **Split stability**: P06 flips (DEV +0.87 → TEST −0.76 net); P01/P05/P08/P13 lose their DEV gross Sharpe in TEST.
- **Missing data**: P06 carry drops from +0.24 to −0.87 (25% missing) — missing rows cut positions and add turnover to a low-turnover carry book; P02 −0.13→−0.81. Stale data barely moves any primitive (frozen 3-bar runs shift signals by tiny amounts relative to their slow decay) — a warning that the slow primitives are also *insensitive* rather than robust.
- **Parameters** (all look-backs ×0.5…×2): net Sharpe is negative under every perturbation for 8/15 (P03, P07, P08, P10, P11, P12, P13, P15 — cost-dominated everywhere); for the other 7 (P01, P02, P04, P05, P06, P09, P14) the range straddles zero; none is positive under all perturbations.
- **Different assets**: gross Sharpe on the holdout universe is positive for P02 (+0.48), P04 (+0.30), P05 (+0.42), P08 (+0.32), P10 (+0.36), P13 (+0.39), P07 (+0.19), P06 (+0.16), P09 (+0.01) but net is negative everywhere; none of these gross values is significant.
- **Wrong venue**: signals from Coinbase spot give gross Sharpe similar to Binance-derived on the same window for P02 (+0.27 vs +0.35), P04 (+0.94 vs +0.77), P12 (+0.41 vs +0.47) — the price-only signals themselves transfer across venue; P01/P05/P13 are ≈0 or negative in both.

## Exploratory follow-up of the six strongest non-primary specs (not adjudicated)
Gross Sharpe under stress (net Sharpe for the cost keys):
```
{
 "P13_SEASON_HOD|CS|H4": {
  "full": 2.8,
  "dev": 3.87,
  "test": 1.19,
  "delay1": 1.27,
  "delay2": -0.02,
  "cost_x0.25": -1.0,
  "cost_x0.5": -4.82,
  "holdout_assets": 0.61,
  "coinbase_signal_TEST": 1.87,
  "binance_signal_same_assets_TEST": 1.7
 },
 "P05_BRK_PERSIST|CS|H4": {
  "full": 2.27,
  "dev": 3.85,
  "test": -0.05,
  "delay1": 2.12,
  "delay2": 1.95,
  "cost_x0.25": 0.89,
  "cost_x0.5": -0.44,
  "holdout_assets": 0.86,
  "coinbase_signal_TEST": 0.01,
  "binance_signal_same_assets_TEST": 0.17
 },
 "P01_TSMOM|CS|H4": {
  "full": 1.64,
  "dev": 2.94,
  "test": -0.28,
  "delay1": 1.51,
  "delay2": 1.39,
  "cost_x0.25": 0.77,
  "cost_x0.5": -0.08,
  "holdout_assets": 0.74,
  "coinbase_signal_TEST": -0.2,
  "binance_signal_same_assets_TEST": -0.22
 },
 "P08_OI_PRICE|TS|H4": {
  "full": 1.38,
  "dev": 1.66,
  "test": 1.02,
  "delay1": 1.35,
  "delay2": 1.39,
  "cost_x0.25": 0.64,
  "cost_x0.5": -0.06,
  "holdout_assets": 0.53
 },
 "P05_BRK_PERSIST|CS|H24": {
  "full": 1.26,
  "dev": 2.39,
  "test": -0.43,
  "delay1": 1.14,
  "delay2": 1.02,
  "cost_x0.25": 0.74,
  "cost_x0.5": 0.25,
  "holdout_assets": -0.08,
  "coinbase_signal_TEST": -0.22,
  "binance_signal_same_assets_TEST": -0.07
 },
 "P02_XS_RS7D|CS|H4": {
  "full": 1.16,
  "dev": 1.51,
  "test": 0.64,
  "delay1": 1.05,
  "delay2": 0.95,
  "cost_x0.25": 0.71,
  "cost_x0.5": 0.24,
  "holdout_assets": 0.7,
  "coinbase_signal_TEST": 0.6,
  "binance_signal_same_assets_TEST": 0.68
 }
}
```
- P13|CS|H4 (cross-sectional hour-of-day seasonality): gross 2.8 (DEV 3.9, TEST 1.2), survives one delay bar (1.3) but not two (≈0), transfers to Coinbase-derived signal (TEST 1.9 vs 1.7 Binance), but only +0.6 on the holdout universe and turns net-positive only below ≈0.18× the assumed cost with 8.4 turns/day. A real but tiny, latency-sensitive statistical regularity that is not monetisable at these costs.
- P05|CS|H4, P01|CS|H4, P05|CS|H24 (cross-sectional trend/breakout): DEV 2.4–3.9 → TEST −0.4…0.0. Period-specific.
- P08|TS|H4 (OI confirmation): stable across halves (1.66/1.02), across delay, positive in holdout (0.53) — the most consistent gross lead — but break-even 0.48× (turnover 2.4/day).
