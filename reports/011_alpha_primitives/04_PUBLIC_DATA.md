# 04 — Public data

Scripts: `bench/alpha_primitives_v1/py/fetch_binance_vision.py`, `fetch_other.py`, `fetch_hl.py`, `data_audit.py`. Raw parquet (≈400 MB) is **not committed** (`.gitignore`); re-fetch with the scripts (public, no keys). Derived results are committed in `results/`.

## Sources used
| Source | Endpoint family | Used for | Notes |
|---|---|---|---|
| Binance Vision (bulk) | `data/futures/um/monthly/{klines,premiumIndexKlines,fundingRate}`, `daily/metrics` | 1h perp OHLCV + taker-buy volume, premium index, funding history, 5-min OI / long-short / taker ratios (→ hourly last) | Main `fapi` REST is geo-blocked from this egress (HTTP 451, also in report 005); bulk archive works. Period 2022-10 → 2026-08 (2022-Q4 warm-up only). |
| Deribit | `public/get_volatility_index_data` (DVOL, hourly) | P14 (BTC, ETH) | Full range 2022-10 → 2026-09. |
| Hyperliquid | `POST /info {type: fundingHistory}` | P15 (hourly funding, 10 core assets) | Starts 2023-06 (XRP 2023-06-18, ADA 2023-10-22). Timestamps carry ms jitter → floored to hour. |
| Coinbase Exchange | `products/{X}-USD/candles` (1h) | wrong-venue signal test (9 assets, no BNB), 2024-12 → 2026-08 | ≈10 missing hours per asset in the test window. |
| OKX, Kraken, Gate | REST | **reachability probed on 2026-09-29 only** (OKX candles/funding OK; Gate funding OK; Kraken OHLC OK); **not used in any result** | Left out to keep 10–15 serious primitives; history depth of these venues was not evaluated in this pass. |

No private AurumShift data. No API keys.

## Coverage (core + holdout)
| asset | perp klines from | missing hourly bars | OI/metrics from | 5-min metric rows | HL funding from | CB candles from | CB missing h (test window) |
|---|---|---|---|---|---|---|---|
| BTC | 2022-10-01 | 0 | 2022-10-01 | 419771 | 2023-06-01 | 2024-12-01 | 10 |
| ETH | 2022-10-01 | 0 | 2022-10-01 | 419771 | 2023-06-01 | 2024-12-01 | 10 |
| SOL | 2022-10-01 | 0 | 2022-10-01 | 419753 | 2023-06-01 | 2024-12-01 | 10 |
| XRP | 2022-10-01 | 0 | 2022-10-01 | 419771 | 2023-06-18 | 2024-12-01 | 10 |
| BNB | 2022-10-01 | 0 | 2022-10-01 | 419770 | 2023-06-01 | — | — |
| DOGE | 2022-10-01 | 0 | 2022-10-01 | 419771 | 2023-06-01 | 2024-12-01 | 10 |
| ADA | 2022-10-01 | 0 | 2022-10-01 | 419771 | 2023-10-22 | 2024-12-01 | 10 |
| LINK | 2022-10-01 | 0 | 2022-10-01 | 419771 | 2023-06-01 | 2024-12-01 | 10 |
| AVAX | 2022-10-01 | 0 | 2022-10-01 | 419712 | 2023-06-01 | 2024-12-01 | 10 |
| LTC | 2022-10-01 | 0 | 2022-10-01 | 419727 | 2023-06-01 | 2024-12-01 | 10 |
| DOT | 2022-10-01 | 0 | 2022-10-01 | 419771 | — | — | — |
| ATOM | 2022-10-01 | 0 | 2022-10-01 | 419771 | — | — | — |
| NEAR | 2022-10-01 | 0 | 2022-10-01 | 419482 | — | — | — |
| TRX | 2022-10-01 | 0 | 2022-10-01 | 419763 | — | — | — |
| BCH | 2022-10-01 | 0 | 2022-10-01 | 419734 | — | — | — |
| ETC | 2022-10-01 | 0 | 2022-10-01 | 419634 | — | — | — |

Funding interval reported by Binance Vision for all 16 assets: 8h. Zero-OI rows exist (e.g. BTC 346, ADA 88 of ≈420k 5-min rows; treated as missing). 5-min metric gaps: 0.0010% of rows.

## Cross-venue sanity (Binance perp vs Coinbase spot, hourly, 2025-01 →)
| asset | 1h log-return corr | median |close diff| (bps) |
|---|---|---|
| BTC | 0.9995 | 5.3 |
| ETH | 0.9997 | 5.2 |
| SOL | 0.9979 | 5.4 |
| XRP | 0.9928 | 5.3 |
| DOGE | 0.9967 | 5.3 |
| ADA | 0.9680 | 6.0 |
| LINK | 0.9899 | 5.4 |
| AVAX | 0.9873 | 6.0 |
| LTC | 0.9822 | 5.6 |

Median close gap ≈5–6 bps (perp/spot basis + timestamp alignment); ADA and LTC have the lowest return correlation (0.97–0.98), i.e. price-only signals are not identical across venues, which is the point of the wrong-venue test (09).

## Quirks that matter
- Binance Vision `metrics` `create_time` semantics (start vs end of the 5-min window) are not documented → conservative 1-bar lag.
- Premium-index klines have no volume field (zeros).
- The Hyperliquid funding interval is 1h vs Binance's 8h settlement; P15 compares 24h averages of per-hour rates.
- Assets in the universe were chosen as liquid *in 2026* (survivorship; see 11).
