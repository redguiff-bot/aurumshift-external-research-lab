# 06 — Execution tests

All numbers are from the test egress (cloud container via policy proxy), so latencies include the proxy path and are **not** representative of a colocated consumer. Raw first-pass captures: `bench/data_feeds_v1/raw/*.json`; run logs: `results/sweep1.json`, `results/sweep2.json`, `results/latency_ratelimit.json`.

## Discovery sweep (single call each)
119 endpoint probes. HTTP 200: 90. Non-200 or failed: 29.

| probe | status | ms | bytes | error |
|---|---|---|---|---|
| `okx_spot_candles` | 200 | 700.0 | 11173 |  |
| `kraken_ohlc` | 200 | 511.1 | 57258 |  |
| `coinbase_candles` | 200 | 510.3 | 20485 |  |
| `bitstamp_ohlc` | 200 | 794.9 | 13341 |  |
| `bitfinex_candles` | 200 | 649.7 | 5160 |  |
| `kucoin_klines` | 200 | 811.8 | 8559 |  |
| `gemini_candles` | 200 | 650.4 | 88548 |  |
| `gateio_spot` | 200 | 1249.4 | 9184 |  |
| `bitget_spot` | 200 | 679.2 | 10618 |  |
| `mexc_spot` | 200 | 826.3 | 9717 |  |
| `htx_spot` | 200 | 804.4 | 13347 |  |
| `cryptocompare` | 401 | 528.3 | 273 |  |
| `coingecko_ohlc` | 200 | 478.4 | 2305 |  |
| `coinpaprika` | 200 | 576.9 | 814 |  |
| `binance_vision_list` | 200 | 693.7 | 2712 |  |
| `binance_us` | 200 | 1083.7 | 15771 |  |
| `binance_data_api` | 200 | 1459.7 | 16953 |  |
| `bybit_kline` | 403 | 491.7 | 96 |  |
| `bybit_nl` | 403 | 613.2 | 96 |  |
| `okx_funding` | 200 | 678.7 | 19498 |  |
| `okx_oi` | 200 | 747.3 | 189 |  |
| `okx_oi_hist` | 200 | 675.9 | 8946 |  |
| `okx_liq` | 200 | 723.4 | 12727 |  |
| `okx_mark_candles` | 200 | 678.1 | 6156 |  |
| `okx_opt_summary` | 200 | 822.7 | 748923 |  |
| `deribit_funding` | 200 | 1113.8 | 107825 |  |
| `deribit_chart` | 200 | 700.7 | 110775 |  |
| `deribit_book_summary_opt` | 200 | 665.0 | 421024 |  |
| `deribit_dvol` | 200 | 542.7 | 1285 |  |
| `deribit_trades` | 200 | 576.1 | 32788 |  |
| `deribit_ticker_perp` | 200 | 548.3 | 694 |  |
| `kraken_fut_tickers` | 200 | 696.8 | 151529 |  |
| `kraken_fut_hist_funding` | 200 | 1069.1 | 1022545 |  |
| `bitmex_funding` | 200 | 981.1 | 16572 |  |
| `bitmex_liq` | 200 | 763.8 | 2 |  |
| `bitmex_bucketed` | 200 | 861.4 | 21946 |  |
| `bitmex_instr` | 200 | 786.3 | 2050 |  |
| `bitfinex_deriv_status` | 200 | 450.3 | 196 |  |
| `bitfinex_liq` | 200 | 961.2 | 4856 |  |
| `gate_fut_funding` | 200 | 1183.6 | 2873 |  |
| `gate_fut_liq` | 200 | 1141.3 | 1833 |  |
| `gate_fut_stats` | 200 | 1521.0 | 61497 |  |
| `bitget_funding` | 200 | 667.7 | 1579 |  |
| `bitget_oi` | 200 | 644.6 | 161 |  |
| `mexc_fut_funding` | 403 | 687.6 | 432 |  |
| `kucoin_fut_funding` | 200 | 473.2 | 2374 |  |
| `hyperliquid_meta` | 405 | 638.2 | 0 |  |
| `dydx_candles` | 200 | 1236.4 | 29610 |  |
| `dydx_funding` | 200 | 1049.5 | 13228 |  |
| `bybit_fund` | 403 | 483.7 | 96 |  |
| `binance_fapi_funding` | 451 | 473.5 | 224 |  |
| `binance_vision_um` | 200 | 643.9 | 2712 |  |
| `coinalyze_demo` | 401 | 640.5 | 37 |  |
| `cryptocompare_fut` | 401 | 319.2 | 273 |  |
| `hyperliquid_info` | 200 | 657.6 | 72257 |  |
| `hyperliquid_candle` | 200 | 619.8 | 13642 |  |
| `hyperliquid_funding` | 200 | 680.7 | 16876 |  |
| `frankfurter_latest` | 200 | 745.0 | 109 |  |
| `frankfurter_hist` | 200 | 762.6 | 1286 |  |
| `open_er_api` | 200 | 477.3 | 2965 |  |
| `fawaz_currency` | 200 | 481.8 | 7512 |  |
| `ecb_eurofxref` | 200 | 861.4 | 1547 |  |
| `ecb_sdmx_fx` | 200 | 1381.0 | 3644 |  |
| `ecb_sdmx_fx_hist` | 200 | 2081.6 | 3634 |  |
| `exchangerate_host` | 200 | 680.3 | 193 |  |
| `yahoo_chart_xau` | 200 | 544.3 | 8333 |  |
| `yahoo_chart_eurusd` | 200 | 535.6 | 11277 |  |
| `stooq_xau` | None | 11563.3 | None | ConnectionError(ProtocolError('Connection aborted.', ConnectionResetEr |
| `stooq_pl` | None | 11866.4 | None | ConnectionError(ProtocolError('Connection aborted.', ConnectionResetEr |
| `dukascopy_bi5` | 200 | 19728.7 | 21048 |  |
| `gold_api_xau` | 200 | 652.4 | 182 |  |
| `gold_api_xag` | 200 | 633.8 | 182 |  |
| `goldprice_org` | 403 | 641.6 | 10 |  |
| `metals_live` | None | 529.3 | None | SSLError(MaxRetryError("HTTPSConnectionPool(host='api.metals.live', po |
| `swissquote_xau` | 200 | 569.8 | 1129 |  |
| `lbma_gold_am` | 200 | 1070.8 | 924963 |  |
| `kraken_paxg` | 200 | 533.8 | 57718 |  |
| `kraken_xauusd_fx` | 200 | 632.7 | 53396 |  |
| `okx_xaut` | 200 | 729.5 | 10253 |  |
| `coinbase_paxg` | 200 | 540.9 | 18430 |  |
| `deribit_paxg_perp` | 200 | 621.4 | 10987 |  |
| `okx_swap_xaut` | 200 | 588.3 | 97 |  |
| `hl_xyz_gold` | 200 | 660.9 | 2588 |  |
| `fred_csv_dgs10` | None | 20543.6 | None | ReadTimeout(ReadTimeoutError("HTTPSConnectionPool(host='fred.stlouisfe |
| `fred_csv_wti` | None | 20488.2 | None | ReadTimeout(ReadTimeoutError("HTTPSConnectionPool(host='fred.stlouisfe |
| `fred_csv_gold` | None | 20509.1 | None | ReadTimeout(ReadTimeoutError("HTTPSConnectionPool(host='fred.stlouisfe |
| `fred_api_nokey` | 400 | 1009.6 | 162 |  |
| `alfred_csv_vintage` | None | 20469.9 | None | ReadTimeout(ReadTimeoutError("HTTPSConnectionPool(host='alfred.stlouis |
| `eia_nokey` | 403 | 973.9 | 163 |  |
| `bls_api_v1` | 200 | 621.7 | 224 |  |
| `treasury_fiscal` | 200 | 852.9 | 2398 |  |
| `treasury_yield_csv` | 200 | 677.4 | 15176 |  |
| `nyfed_sofr` | 200 | 888.7 | 1208 |  |
| `worldbank` | 200 | 541.8 | 1146 |  |
| `worldbank_pink` | 200 | 757.9 | 765246 |  |
| `imf_datamapper` | 403 | 727.6 | 429 |  |
| `eurostat` | 200 | 764.3 | 3219 |  |
| `oecd_sdmx` | 403 | 614.0 | 49 |  |
| `cftc_cot` | 200 | 941.9 | 13961 |  |
| `bea_nokey` | 200 | 845.8 | 0 |  |
| `bankofcanada` | 200 | 724.4 | 1003 |  |
| `boe_iadb` | 200 | 1033.1 | 412 |  |
| `snb` | 200 | 1921.2 | 891356 |  |
| `ff_calendar` | 200 | 493.0 | 19110 |  |
| `ff_calendar_xml` | 200 | 482.7 | 48669 |  |
| `fed_fomc_cal` | 200 | 554.7 | 165460 |  |
| `bls_schedule_ics` | 403 | 731.7 | 1325 |  |
| `gdelt_doc` | None | 11471.7 | None | ConnectionError(ProtocolError('Connection aborted.', ConnectionResetEr |
| `cryptopanic_nokey` | 403 | 279.9 | 4551 |  |
| `fear_greed` | 200 | 500.6 | 393 |  |
| `blockchain_info` | 200 | 934.0 | 422 |  |
| `mempool_space` | 200 | 506.6 | 108 |  |
| `tradingeconomics_guest` | 410 | 658.6 | 214 |  |
| `fmp_nokey` | 401 | 592.9 | 184 |  |
| `finnhub_nokey` | 401 | 605.9 | 34 |  |
| `alphavantage_demo` | 200 | 552.4 | 17313 |  |
| `twelvedata_demo` | 200 | 480.9 | 3228 |  |
| `polygon_nokey` | 401 | 551.5 | 101 |  |
| `oanda_nokey` | 401 | 519.9 | 65 |  |

## Repeated latency (10 sequential calls, 1 s spacing, small payloads)
| endpoint | ok | median ms | p90 ms | max ms |
|---|---|---|---|---|
| okx_candles | 10/10 | 666.1 | 690.7 | 716.3 |
| kraken_ohlc | 10/10 | 590.8 | 620.0 | 702.4 |
| coinbase_candles | 10/10 | 509.6 | 533.6 | 556.2 |
| bitstamp_ohlc | 10/10 | 644.8 | 801.5 | 1351.5 |
| deribit_ticker | 10/10 | 613.8 | 636.7 | 670.9 |
| hyperliquid_info_meta | 10/10 | 724.8 | 971.2 | 979.1 |
| kucoin_candles | 10/10 | 707.5 | 831.5 | 1912.8 |
| gate_candles | 10/10 | 1297.3 | 1390.2 | 1448.4 |
| bitget_candles | 10/10 | 710.3 | 815.5 | 856.7 |
| dydx_candles | 10/10 | 562.7 | 768.3 | 1213.4 |
| binance_dataapi | 10/10 | 1180.3 | 1353.5 | 2124.2 |
| frankfurter_latest | 10/10 | 508.8 | 571.5 | 616.6 |
| ecb_sdmx | 10/10 | 905.4 | 976.6 | 1191.4 |
| nyfed_sofr | 10/10 | 677.8 | 819.0 | 905.5 |

## "Bursts" — honest description
Three bursts were requested well below documented limits (OKX 20 calls; Coinbase 8; Deribit 20). Because each call takes ~0.5–0.7 s through the egress, achieved rates were ≈1.5 req/s, i.e. **the egress, not the provider, set the throttle; no 429 was provoked on any exchange**:

| burst | calls | actual seconds | statuses |
|---|---|---|---|
| okx_candles_20_in_4s(doc:40/2s) | 20 | 13.59 | 200 |
| coinbase_candles_8_in_2s(doc:10/s) | 8 | 4.02 | 200 |
| deribit_ticker_20_in_4s(doc numeric: see docs_facts) | 20 | 11.26 | 200 |

Rate-limit *enforcement* was only observed passively: Dukascopy candle endpoints HTTP 429 after a few requests; Yahoo HTTP 429 on the root probe and NG=F; BLS daily-threshold message (first probe) that later cleared; geo-blocks Binance 451, Bybit/MEXC-futures/IMF/goldprice 403. Documented limits (quotes in `01`): OKX candles 40/2 s; Coinbase 10/s per IP; Hyperliquid 1200 weight/min per IP; Gemini 120/min; gold-api history 10/h free; Alpha Vantage 25/day; Twelve Data 8/min; BLS v1 25/day. Rate-limit response headers were essentially absent (only `Date`/`Server` captured on OKX, Coinbase, Deribit) — consumers cannot self-throttle from headers on these venues.

## Not measured
HTTP 429/Retry-After recovery behaviour; sustained-hour stability; WS reconnect/gap-recovery/sequence-gap semantics; multi-hour late-arrival/revision drift; clock-skew-corrected latency.
