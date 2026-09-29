# 04 — Public data used

No API keys, no private AurumShift data. Raw archives are **not committed** (size); `bench/alpha_primitives_v1/py/fetch_vision.py` and `fetch_xvenue.py` re-download them; `results/vision_manifest.json` holds per-file sha256 of every Binance Vision file used.

## Binance Vision (primary; deterministic archives)
| dataset | files requested | files retrieved |
|---|---|---|
| spot_kl | 320 | 320 |
| um_kl | 320 | 320 |
| um_prem | 320 | 320 |
| um_fund | 320 | 320 |
| um_metrics | 9740 | 9740 |

Datasets: spot & USD-M 1h klines (2024-01 → 2026-08, incl. taker-buy volumes), USD-M premium-index 1h klines, monthly funding-rate archive (interval 4h/8h per contract), daily 5-minute `metrics` (open interest in coins, ratios). Missing data: 24 premium-index bars (one day); no missing kline bars. `liquidationSnapshot` archive returned 404 for 2024 → **no historical liquidation prints** (P10 is a proxy). Note: spot archive timestamps switched to microseconds from 2025; handled in the loader.

## Cross-venue (falsification only; `results/xvenue_manifest.json`)
| venue | endpoint | coverage obtained | use |
|---|---|---|---|
| OKX | `/market/history-candles` 1H, `*-USDT-SWAP` | 2024-01 → 2026-08, 5 assets | wrong-venue perp prices |
| Coinbase Exchange | `/products/*-USD/candles` 3600 | 2024-01 → 2026-08, 5 assets | wrong-venue spot prices |
| Gate | `/spot/candlesticks` 1h | **only from 2025-09-10** (API depth cap) | wrong-venue spot (short window) |
| Kraken | `/OHLC` interval 60 | **latest 721 bars only** | feed consistency (return corr vs Binance 0.995–0.999) |
| Hyperliquid | `info` `candleSnapshot` / `fundingHistory` | candles **only from 2026-03-05** (5000-candle cap); funding 2024-01 → 2026-08 (hourly) | funding cross-check (ρ with Binance funding 0.76–0.85), P06 venue test |
| Deribit | `get_volatility_index_data` DVOL, resolution 3600 | 2024-01 → 2026-09-01, BTC & ETH | P15 |

Connectivity from the sandbox worked for all listed hosts; geo-blocked providers noted in report 005 were not needed. Sampling: everything resampled to hourly bars in UTC. Weaknesses: single-provider primary source (Binance), USDT-quoted spot vs USD-quoted Coinbase, Gate/HL/Kraken windows too short for full-sample claims (they are labelled as such wherever used).
