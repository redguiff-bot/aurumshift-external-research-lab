# 07 — Regime-conditional behaviour

Regimes are computed only from trailing information and lagged one bar: **vol** = BTC 168h realised-vol percentile vs trailing 90 days (low/mid/high terciles); **trend** = sign of BTC 30-day return (bull/bear); **funding_heat** = cross-asset mean funding percentile vs trailing 90 days (cold/neutral/hot). Share of evaluation hours: **vol**: low=0.40, high=0.35, mid=0.25; **trend**: bull=0.55, bear=0.46; **funding_heat**: cold=0.37, hot=0.32, neutral=0.31.

Test of regime dependence: range across states of mean hourly gross PnL vs a null of the same labels circularly shifted (300 draws; preserves label persistence). **45 primitive×regime tests are run, so ≈2 raw p≤0.05 hits are expected by chance.** Gross returns shown; net is in the JSON.

| primitive | regime family | GROSS annualised return per state (t on daily sums) | perm. p (state range) | sign-consistent DEV→HOLDOUT (states) |
|---|---|---|---|---|
| P01_TSMOM | vol | high: -59.0% (t=-1.0); low: 29.5% (t=0.9); mid: 25.3% (t=0.5) | 0.41 | 1/3 |
| P01_TSMOM | trend | bear: -71.7% (t=-1.6); bull: 55.1% (t=1.6) | 0.04 | 1/2 |
| P01_TSMOM | funding_heat | cold: -50.2% (t=-1.0); hot: 89.9% (t=2.1); neutral: -42.5% (t=-1.0) | 0.11 | 2/3 |
| P02_XS_RS | vol | high: 2.3% (t=0.1); low: -27.4% (t=-1.7); mid: 53.0% (t=2.1) | 0.04 | 2/3 |
| P02_XS_RS | trend | bear: -32.1% (t=-2.0); bull: 32.7% (t=1.8) | 0.02 | 2/2 |
| P02_XS_RS | funding_heat | cold: -48.6% (t=-2.7); hot: 66.9% (t=2.6); neutral: -1.7% (t=-0.1) | 0.00 | 2/3 |
| P03_REV_4H | vol | high: 69.7% (t=1.9); low: -9.3% (t=-0.3); mid: -36.9% (t=-1.0) | 0.01 | 3/3 |
| P03_REV_4H | trend | bear: 16.3% (t=0.6); bull: 7.4% (t=0.3) | 0.82 | 0/2 |
| P03_REV_4H | funding_heat | cold: 35.1% (t=1.0); hot: 17.2% (t=0.6); neutral: -22.5% (t=-0.6) | 0.39 | 2/3 |
| P04_DONCHIAN | vol | high: -51.3% (t=-0.8); low: 45.2% (t=1.1); mid: 33.2% (t=0.5) | 0.39 | 2/3 |
| P04_DONCHIAN | trend | bear: -8.4% (t=-0.2); bull: 22.3% (t=0.6) | 0.62 | 1/2 |
| P04_DONCHIAN | funding_heat | cold: -7.9% (t=-0.1); hot: 32.0% (t=0.6); neutral: 3.0% (t=0.1) | 0.80 | 1/3 |
| P05_VOL_SQUEEZE_BREAK | vol | high: -2.3% (t=-0.2); low: 10.0% (t=1.3); mid: 9.0% (t=1.0) | 0.54 | 1/3 |
| P05_VOL_SQUEEZE_BREAK | trend | bear: 4.4% (t=0.5); bull: 6.3% (t=0.8) | 0.82 | 1/2 |
| P05_VOL_SQUEEZE_BREAK | funding_heat | cold: 8.8% (t=1.1); hot: 4.2% (t=0.4); neutral: 2.7% (t=0.3) | 0.92 | 1/3 |
| P06_FUND_XS | vol | high: 3.0% (t=0.1); low: 9.8% (t=0.7); mid: 27.5% (t=1.4) | 0.56 | 1/3 |
| P06_FUND_XS | trend | bear: 13.2% (t=0.9); bull: 10.7% (t=0.7) | 0.87 | 2/2 |
| P06_FUND_XS | funding_heat | cold: 11.3% (t=0.6); hot: 7.3% (t=0.4); neutral: 17.3% (t=0.9) | 0.92 | 3/3 |
| P07_BASIS_CARRY | vol | high: 2.7% (t=3.8); low: 0.2% (t=1.5); mid: 1.7% (t=3.2) | 0.21 | 0/3 |
| P07_BASIS_CARRY | trend | bear: 0.0% (t=flat/NA); bull: 2.6% (t=4.9) | 0.08 | 1/2 |
| P07_BASIS_CARRY | funding_heat | cold: 0.0% (t=flat/NA); hot: 4.5% (t=5.0); neutral: 0.0% (t=flat/NA) | 0.00 | 2/3 |
| P08_SPOT_PERP_BASIS | vol | high: 13.0% (t=0.4); low: -6.9% (t=-0.4); mid: -42.0% (t=-1.3) | 0.26 | 2/3 |
| P08_SPOT_PERP_BASIS | trend | bear: 19.7% (t=1.0); bull: -32.5% (t=-1.6) | 0.12 | 2/2 |
| P08_SPOT_PERP_BASIS | funding_heat | cold: 22.3% (t=0.9); hot: -70.3% (t=-2.6); neutral: 18.4% (t=0.8) | 0.02 | 3/3 |
| P09_OI_PRICE | vol | high: 40.0% (t=1.2); low: 0.3% (t=0.0); mid: -4.5% (t=-0.1) | 0.53 | 1/3 |
| P09_OI_PRICE | trend | bear: 5.4% (t=0.2); bull: 19.4% (t=1.0) | 0.71 | 0/2 |
| P09_OI_PRICE | funding_heat | cold: 16.8% (t=0.5); hot: 47.7% (t=1.9); neutral: -27.7% (t=-1.3) | 0.12 | 2/3 |
| P10_LIQ_FLUSH_PROXY | vol | high: -2.8% (t=-0.2); low: -2.7% (t=-0.5); mid: -2.8% (t=-0.3) | 1.00 | 1/3 |
| P10_LIQ_FLUSH_PROXY | trend | bear: 2.3% (t=0.3); bull: -7.0% (t=-0.8) | 0.26 | 0/2 |
| P10_LIQ_FLUSH_PROXY | funding_heat | cold: 5.5% (t=0.6); hot: 1.5% (t=0.2); neutral: -17.0% (t=-1.2) | 0.12 | 2/3 |
| P11_TAKER_FLOW | vol | high: -15.4% (t=-0.6); low: 24.0% (t=1.4); mid: 30.4% (t=1.5) | 0.20 | 2/3 |
| P11_TAKER_FLOW | trend | bear: -6.2% (t=-0.3); bull: 26.9% (t=1.7) | 0.23 | 1/2 |
| P11_TAKER_FLOW | funding_heat | cold: -11.7% (t=-0.5); hot: 15.5% (t=0.8); neutral: 36.0% (t=1.7) | 0.17 | 2/3 |
| P12_ILLIQ_SHOCK | vol | high: 2.8% (t=1.0); low: 0.1% (t=0.1); mid: -0.7% (t=-0.5) | 0.50 | 1/3 |
| P12_ILLIQ_SHOCK | trend | bear: 3.4% (t=1.5); bull: -1.3% (t=-1.3) | 0.04 | 2/2 |
| P12_ILLIQ_SHOCK | funding_heat | cold: 1.4% (t=0.5); hot: -0.4% (t=-0.3); neutral: 1.4% (t=0.8) | 0.80 | 2/3 |
| P13_BTC_LEADLAG | vol | high: -11.1% (t=-0.4); low: 11.4% (t=0.7); mid: -10.4% (t=-0.4) | 0.75 | 2/3 |
| P13_BTC_LEADLAG | trend | bear: -18.5% (t=-1.0); bull: 11.9% (t=0.6) | 0.18 | 1/2 |
| P13_BTC_LEADLAG | funding_heat | cold: -9.1% (t=-0.4); hot: 12.5% (t=0.5); neutral: -8.6% (t=-0.4) | 0.79 | 1/3 |
| P14_HOUR_SEASON | vol | high: 8.5% (t=0.3); low: 24.9% (t=1.1); mid: 38.6% (t=1.2) | 0.62 | 2/3 |
| P14_HOUR_SEASON | trend | bear: -0.3% (t=-0.0); bull: 41.7% (t=2.0) | 0.15 | 1/2 |
| P14_HOUR_SEASON | funding_heat | cold: 13.1% (t=0.4); hot: 31.0% (t=1.2); neutral: 25.1% (t=0.9) | 0.90 | 0/3 |
| P15_RV_IV_VRP | vol | high: -40.9% (t=-0.7); low: 61.5% (t=1.6); mid: -44.6% (t=-1.0) | 0.19 | 2/3 |
| P15_RV_IV_VRP | trend | bear: -11.0% (t=-0.3); bull: 7.2% (t=0.2) | 0.65 | 0/2 |
| P15_RV_IV_VRP | funding_heat | cold: 28.6% (t=0.6); hot: -32.2% (t=-0.7); neutral: -4.0% (t=-0.1) | 0.62 | 1/3 |


Reading rules used in 10: a primitive is called REGIME_DEPENDENT only if raw perm. p ≤ 0.05 in at least one family AND every compared state keeps its sign from DEV to HOLDOUT. Conditional gross returns in a single state are never treated as a tradable filter without an independent holdout: the filter would be selected on the same data.
