# 01 — Source landscape

Source cards. `docs:` text is a short quote captured from official pages (`results/docs_facts.json`; NOT_FOUND where the page was unreachable/JS-only). Nothing is inferred: empty means UNKNOWN. Cards for sources that were **not executed** carry only what the probe response itself showed.

| Group | Discovered | Executed (HTTP 200 + parsed) |
|---|---|---|
| Crypto exchanges & bulk | 26 | 22 |
| FX / gold | 22 | 14 |
| Commodities / macro | 14 | 8 |
| Calendar / news | 6 | 2 |
| **Total** | **68** | **46** |

### Crypto exchanges & bulk

#### OKX v5 public  `okx`
* **Asset/gap classes:** SPOT, FUND, OI, LIQ, OPT, BASIS, BAR_MTF · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET www.okx.com/api/v5/market/candles, /public/funding-rate-history, /public/open-interest, /rubik/stat/contracts/open-interest-history, /public/opt-summary, /public/liquidation-orders (REST observed 200; current docs list only a WS liquidation channel); WS wss://ws.okx.com/ws/v5/public
* **Auth:** none for public
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** GET /api/v5/market/candles Rate Limit: 40 requests per 2 seconds; history-candles 20/2s; funding-rate 10/2s; open-interest 20/2s; opt-summary 20/2s (rule: IP)
* **Historical depth (OBSERVED):** candles: pagination via `after`; 1m history-candles deeper (depth not measured); OI history: 100 rows = 8.25h @5m (observed); funding: 30+ rows/8h  ·  docs: market/candles: 'This endpoint can retrieve the latest 1,440 data entries'; 'The maximum is 300' per request (history-candles 'from recent years'); funding-rate-history '…
* **Streaming:** WS OK (port 443 path); :8443 reset by test egress
* **Update frequency:** 1m bars; funding 8h; OI 5m
* **Timestamp semantics:** candle ts = bar-open epoch ms (aligned with peers, lag test); candle field[8] confirm=1 marks closed bar  ·  docs: Opening time of the candlestick, Unix timestamp format in milliseconds
* **Provider IDs:** instId strings (BTC-USDT, BTC-USDT-SWAP, BTC-USD-261030)
* **Revision behaviour:** none observed across 6-min re-fetch (0 revised bars/240)  ·  docs: candle field confirm: '0 represents that it is uncompleted, 1 represents that it is completed' (WS candle doc); no correction policy found
* **Finality semantics:** `confirm` flag on candle (OBSERVED)
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** Best single derivatives coverage among keyless venues; REST liquidation endpoint undocumented => contract risk

#### Kraken spot REST/WS  `kraken`
* **Asset/gap classes:** SPOT, BAR_MTF · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.kraken.com/0/public/OHLC; WS wss://ws.kraken.com/v2
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** Every REST API user has a 'call counter'... Tier Max API Counter: Starter 15, Intermediate 20, Pro 20; decay -0.33/-0.5/-1 per sec
* **Historical depth (OBSERVED):** OHLC returns ~720 rows per call (`since` cursor); older depth not measured  ·  docs: Returns up to 720 of the most recent entries (older data cannot be retrieved, regardless of the value of since).
* **Streaming:** WS OK (17 trades/20s sample)
* **Update frequency:** 1m bars
* **Timestamp semantics:** OHLC ts = bar-open epoch s; response includes forming bar (3 rows >= end in sample)  ·  docs: Return OHLC entries since the given timestamp (intended for incremental updates); interval in minutes: 1,5,15,30,60,240,1440,10080,21600; last entry is current not-yet-co…
* **Provider IDs:** pair names (XXBTZUSD / XBTUSD alias)
* **Revision behaviour:** 0 revised of 240  ·  docs: The last entry in the OHLC array is for the current, not-yet-committed timeframe, and will always be present, regardless of the value of since.
* **Finality semantics:** none (forming bar included, unflagged)
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** USD-quoted; tight to peers (0.43 bps median dev from group consensus)

#### Kraken Futures public  `kraken_fut`
* **Asset/gap classes:** FUND, OI, BASIS · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET futures.kraken.com/derivatives/api/v3/tickers, /api/v4/historicalfundingrates?symbol=PF_XBTUSD
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** Public endpoints do not have a cost and therefore do not count against any rate limiting budget.
* **Historical depth (OBSERVED):** funding history 1MB response (from 2025-09-24 in sample)  ·  docs: more_candles: 'True if there are more candles in time range' (paginated); Kraken does not provide a bulk historical data dump or websocket replay service.
* **Streaming:** not tested
* **Update frequency:** hourly funding
* **Timestamp semantics:** ISO-8601 Z timestamps  ·  docs: NOT_FOUND
* **Provider IDs:** symbols PF_XBTUSD, FI_XBTUSD_YYMMDD
* **Revision behaviour:** not tested  ·  docs: NOT_FOUND
* **Finality semantics:** none observed
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** fixed-maturity FI_ contracts showed openInterest 0 and no last trade => thin basis venue

#### Coinbase Exchange public  `coinbase`
* **Asset/gap classes:** SPOT, GOLD · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.exchange.coinbase.com/products/BTC-USD/candles (max 300/req); WS wss://ws-feed.exchange.coinbase.com
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** Public Endpoints: Requests per second per IP: 10; Requests per second per IP in bursts: Up to 15
* **Historical depth (OBSERVED):** 300 candles/request, windowed by start/end  ·  docs: The maximum number of data points for a single request is 300 candles. If your selection ... results in more than 300 data points, your request is rejected.
* **Streaming:** WS OK (106 matches/20s)
* **Update frequency:** 1m bars; matches real-time
* **Timestamp semantics:** candle row [time,low,high,open,close,volume] (column order differs from peers); time = bucket start epoch s  ·  docs: time bucket start time; Candle schema is of the form [timestamp, price_low, price_high, price_open, price_close]
* **Provider IDs:** product ids BTC-USD, PAXG-USD; WS match has trade_id/sequence
* **Revision behaviour:** 0 revised of 240  ·  docs: Historical rate data may be incomplete. No data is published for intervals where there are no ticks.
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** USD spot; PAXG-USD as gold proxy

#### Bitstamp  `bitstamp`
* **Asset/gap classes:** SPOT · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET www.bitstamp.net/api/v2/ohlc/btcusd/ ; WS wss://ws.bitstamp.net
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** As standard, all clients can make 400 requests per second. There is a default limit threshold of 10,000 requests per 10 minutes in place.
* **Historical depth (OBSERVED):** 1000 rows/req observed (ignored my start/end in one call: returned 1000 rows)  ·  docs: OHLC endpoint has 'limit' and 'step' params (max 1000 per request per doc summary; not re-verified verbatim)
* **Streaming:** WS OK (11 trades/20s; median recv-event 45.6 ms)
* **Update frequency:** 1m bars
* **Timestamp semantics:** ts = bar-open epoch s; WS microtimestamp  ·  docs: NOT_FOUND
* **Provider IDs:** pair slugs
* **Revision behaviour:** 0 revised of 240  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** Companies seeking to utilize Bitstamp's exchange data for their own commercial purposes are directed to contact partners@bitstamp.net to receive and sign a commercial use…
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** docs: commercial exploitation of data => contact vendor

#### Bitfinex public v2  `bitfinex`
* **Asset/gap classes:** SPOT, LIQ, OI · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api-pub.bitfinex.com/v2/candles/trade:1m:tBTCUSD/hist, /v2/liquidations/hist, /v2/status/deriv
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** The current rate limit is between 10 and 90 requests per minute, depending on the specific REST API endpoint; candles: Rate Limit: 30 reqs/min
* **Historical depth (OBSERVED):** liquidations/hist: 500 rows spanning 78h across all symbols (observed)  ·  docs: limit: Number of records in response (max. 10000). The endpoint provides the last 100 candles by default
* **Streaming:** WS OK (13 trades/20s)
* **Update frequency:** 1m bars
* **Timestamp semantics:** MTS = bar-open ms; array-positional schema [MTS,O,C,H,L,V]  ·  docs: If start is given, only records with MTS >= start (milliseconds) will be given as response.
* **Provider IDs:** tBTCUSD; liquidation rows carry position id
* **Revision behaviour:** 0 revised  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** any use of our API needs to be in compliance with our API Terms of Service
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** SPOT price level sits ~13 bps above USD peers (unexplained; cause UNKNOWN) => do not use for level-sensitive work until explained; liquidation history is the useful part

#### KuCoin public  `kucoin`
* **Asset/gap classes:** SPOT, FUND · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.kucoin.com/api/v1/market/candles; api-futures.kucoin.com/api/v1/contract/funding-rates
* **Auth:** none for REST; WS needs a token from a bullet endpoint (not tested)
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** Public Rate Limit Pool ... endpoints that can be accessed without authentication. Rate limits for these endpoints are managed based on the IP address.
* **Historical depth (OBSERVED):** 1500 rows/req (documented number not verified)  ·  docs: For each query, the system would return at most 1500 pieces of data. To obtain more data, please page the data by time. (UTA v2: Spot: no limit on historical range; Futur…
* **Streaming:** not tested (token flow)
* **Update frequency:** 1m bars; funding 8h
* **Timestamp semantics:** ts = bar-open epoch s; array [time,O,C,H,L,vol,turnover]  ·  docs: Start time of the candle interval, in seconds (UTA v2 Get Klines); classic startAt/endAt: 'Start time (second)'
* **Provider IDs:** BTC-USDT, XBTUSDTM
* **Revision behaviour:** 0 revised  ·  docs: No data is published for intervals where there are no ticks.
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** funding values differ from OKX/Gate (venue-specific)

#### Gemini public  `gemini`
* **Asset/gap classes:** SPOT · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.gemini.com/v2/candles/btcusd/1m
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** For public API entry points, we limit requests to 120 requests per minute, and recommend that you do not exceed 1 request per second.
* **Historical depth (OBSERVED):** fixed ~1440 rows/call, no start/end params (observed)  ·  docs: NOT_FOUND
* **Streaming:** WS OK but 2102 msgs/20s of book updates (heavy)
* **Update frequency:** 1m bars
* **Timestamp semantics:** ms epoch bar-open  ·  docs: Response is an array of arrays: timestamp (milliseconds), open, high, low, close, volume; time frames 1m,5m,15m,30m,1h,6h,1day (open/close semantics not stated)
* **Provider IDs:** btcusd
* **Revision behaviour:** 0 revised  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** 23/240 flat and 16/240 zero-volume bars (gap-filled); ret. corr vs consensus 0.79 => low information per bar

#### Gate.io v4  `gate`
* **Asset/gap classes:** SPOT, FUND, LIQ, OI · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.gateio.ws/api/v4/spot/candlesticks; /futures/usdt/funding_rate; /liq_orders; /contract_stats; /contracts/BTC_USDT
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** contract_stats 99 rows @5m (~8h); liq_orders 13 rows/19 min (observed)  ·  docs: Maximum of 1000 points can be returned in a query. Be sure not to exceed the limit when specifying from, to and interval (official Gate SDK doc of GET /spot/candlesticks)
* **Streaming:** not tested
* **Update frequency:** 1m bars; funding 8h
* **Timestamp semantics:** candle row has closed-flag string; funding `t` in epoch s with 1 s jitter on first row  ·  docs: Start time of candlesticks, formatted in Unix timestamp in seconds. Default to `to - 100 * interval` if not specified
* **Provider IDs:** contract BTC_USDT
* **Revision behaviour:** 0 revised  ·  docs: NOT_FOUND
* **Finality semantics:** closed flag on candle (OBSERVED)
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** Best ret. corr to consensus (0.988) among USDT spot; OI in contracts (quanto 0.0001 BTC): unit trap

#### Bitget v2  `bitget`
* **Asset/gap classes:** SPOT, FUND, OI · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.bitget.com/api/v2/spot/market/candles, /mix/market/history-fund-rate, /mix/market/open-interest
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** funding pageSize 30 rows; deeper not measured  ·  docs: NOT_FOUND
* **Streaming:** not tested
* **Update frequency:** 1m bars
* **Timestamp semantics:** ms epoch bar-open  ·  docs: NOT_FOUND
* **Provider IDs:** BTCUSDT (+productType)
* **Revision behaviour:** 0 revised  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** 1 minute (2026-09-29T09:02Z) missing while OKX/MEXC/Kraken have trades, persisted across 2 fetches; funding rate frequently pinned at 0.0001 (cap/floor?) in sample

#### MEXC spot  `mexc`
* **Asset/gap classes:** SPOT · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.mexc.com/api/v3/klines; futures host contract.mexc.com returned 403 from test egress
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** 1000 rows/req  ·  docs: NOT_FOUND
* **Streaming:** not tested
* **Update frequency:** 1m bars
* **Timestamp semantics:** ms epoch bar-open  ·  docs: NOT_FOUND
* **Provider IDs:** BTCUSDT
* **Revision behaviour:** 0 revised  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** no docs facts extracted (NOT_FOUND); futures API unreachable here

#### HTX spot  `htx`
* **Asset/gap classes:** SPOT · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.huobi.pro/market/history/kline
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** New Version Rate limit ... applied on UID basis... [market] It is suggested to use WebSocket interface ... WebSocket notification has lower latency and not have rate limi…
* **Historical depth (OBSERVED):** size<=300 (used)  ·  docs: size: The number of data returns [1-2000] (GET /market/history/kline); 'The market data is updated once per second.'
* **Streaming:** not tested
* **Update frequency:** 1m bars
* **Timestamp semantics:** id = bar-open epoch s; newest-first  ·  docs: id: The UNIX timestamp in seconds as response id; 'The start time for candlesticks is based on Singapore time (GMT+8)'; ts Unit: Millisecond
* **Provider IDs:** btcusdt
* **Revision behaviour:** 0 revised  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** -4.5 bps vs USDT-group consensus, 8/240 flat bars; larger deviation than peers

#### Deribit public v2  `deribit`
* **Asset/gap classes:** FUND, OI, BASIS, OPT, GOLD, BAR_MTF · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET www.deribit.com/api/v2/public/get_book_summary_by_currency (option|future), get_tradingview_chart_data, get_funding_rate_history, get_volatility_index_data (DVOL), ticker; WS wss://www.deribit.com/ws/api/v2
* **Auth:** none for public
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** Public, non-authorized API requests are rate-limited on a per-IP basis. They do not draw from the sub-account-level credit pool.
* **Historical depth (OBSERVED):** funding 168 hourly rows/7d complete; DVOL 72 hourly rows/3d  ·  docs: NOT_FOUND
* **Streaming:** WS OK (76 msgs/20s; median recv-event 68.6 ms, p95 292 ms)
* **Update frequency:** 1m bars; funding hourly; book summary snapshot; DVOL hourly
* **Timestamp semantics:** event ts ms epoch; response carries usIn/usOut microsecond server stamps (receipt-side timestamp observable!)  ·  docs: The earliest timestamp to return result from (milliseconds since the UNIX epoch); DVOL candles: 'timestamp in ms, open, high, low, close'; book summary creation_timestamp…
* **Provider IDs:** instrument_name (BTC-25DEC26-85000-C); trades carry trade_id
* **Revision behaviour:** 0 revised of 240 (perp bars)  ·  docs: NOT_FOUND
* **Finality semantics:** none flagged
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** Only keyless source with full BTC options surface (944 instruments) + DVOL; OI reported in USD contracts for BTC

#### BitMEX public  `bitmex`
* **Asset/gap classes:** FUND, LIQ · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET www.bitmex.com/api/v1/funding, /liquidation, /trade/bucketed; WS wss://ws.bitmex.com/realtime
* **Auth:** none for public
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** funding 30 rows/8h; XBTUSD instrument state Settled (probe returned 0 bars)  ·  docs: count: Number of results to fetch. Must be a positive integer. (binSize options 1m,5m,1h,1d; max value not stated in swagger)
* **Streaming:** WS OK (1 liq msg/20s)
* **Update frequency:** funding 8h
* **Timestamp semantics:** ISO-8601  ·  docs: Timestamps returned by our bucketed endpoints are the **end** of the period, indicating when the bucket was written to disk.
* **Provider IDs:** symbol
* **Revision behaviour:** not tested  ·  docs: Also note the `open` price is equal to the `close` price of the previous timeframe bucket. partial: If true, will send in-progress (incomplete) bins
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** XBTUSD is settled; liquidation REST returned [] at sample time; low current relevance

#### Hyperliquid info API  `hyperliquid`
* **Asset/gap classes:** SPOT, FUND, OI, LIQ, GOLD, BAR_MTF · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** POST api.hyperliquid.xyz/info {type: candleSnapshot|fundingHistory|metaAndAssetCtxs|allMids(dex=xyz)}; WS wss://api.hyperliquid.xyz/ws
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** The following rate limits apply per IP address: REST requests share an aggregated weight limit of 1200 per minute.
* **Historical depth (OBSERVED):** funding 168 hourly rows/7d; candle snapshot 241 bars/4h  ·  docs: Candle snapshot: Only the most recent 5000 candles are available; 'To query larger ranges, use the last returned timestamp as the next startTime for pagination.'
* **Streaming:** WS OK (61 trades + 5 L2 msgs/20s; median recv-event 300 ms, p95 626 ms)
* **Update frequency:** 1m bars; funding hourly; asset ctx snapshot
* **Timestamp semantics:** candle `t` open ms / `T` close ms; funding `time` has ms jitter (…059 ms) - not on the hour boundary  ·  docs: req: {"coin": <coin>, "interval": "15m", "startTime": <epoch millis>, "endTime": <epoch millis>} (open/close semantics of returned candle not stated on page)
* **Provider IDs:** coin symbol; trades carry tid/hash
* **Revision behaviour:** 0 revised of 240  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** OI snapshot in BTC (34.3k) in same call as funding/premium; `xyz` dex lists commodity/equity perps incl. GOLD (mid 4153.05)

#### dYdX v4 indexer  `dydx`
* **Asset/gap classes:** FUND · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET indexer.dydx.trade/v4/candles/perpetualMarkets/BTC-USD, /historicalFunding/BTC-USD, /perpetualMarkets
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** funding 200 hourly rows  ·  docs: get_perpetual_market_candles: limit (u32) 'The maximum number of candles to retrieve.'; fromISO/toISO 'The start timestamp in ISO format.' (no max stated)
* **Streaming:** WS connected, subscribed, 0 trades in 20s
* **Update frequency:** 1m bars sparse
* **Timestamp semantics:** startedAt ISO-8601  ·  docs: fromISO: The start timestamp in ISO format. (candle startedAt semantics not stated)
* **Provider IDs:** ticker BTC-USD; effectiveAtHeight (block height!)
* **Revision behaviour:** 0 revised  ·  docs: NOT_FOUND
* **Finality semantics:** block height offers chain finality reference (DOCUMENTED shape, not exploited)
* **Licence / ToS (DOCUMENTED_CLAIM):** Terms-of-Use & Privacy Policy page: 'By using, recording, referencing, or downloading ... any information contained on this page or in any dYdX Trading Inc. database or d…
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** 150/240 zero-volume bars and ret. corr 0.43 vs consensus in sample: thin market

#### Binance data-api.binance.vision (spot mirror)  `binance_api`
* **Asset/gap classes:** SPOT, BAR_MTF · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET data-api.binance.vision/api/v3/klines; WS wss://data-stream.binance.vision/ws/btcusdt@trade
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** Every request will contain X-MBX-USED-WEIGHT-(intervalNum)(intervalLetter) ...; Repeatedly violating rate limits ... will result in an automated IP ban (HTTP status 418).…
* **Historical depth (OBSERVED):** 1000 rows/req  ·  docs: GET /api/v3/klines: limit 'Default: 500; Maximum: 1000.' 'If startTime and endTime are not sent, the most recent klines are returned.'
* **Streaming:** WS OK (627 trades/20s; median recv-event 66 ms)
* **Update frequency:** 1m bars; trades tick
* **Timestamp semantics:** ms epoch bar-open; WS trade event T  ·  docs: Klines are uniquely identified by their open time. Timestamp parameters (e.g. startTime, endTime, timestamp) can be passed in milliseconds or microseconds.
* **Provider IDs:** symbol; trade id `t`
* **Revision behaviour:** 0 revised of 240  ·  docs: Archived files may be updated at a later date as a result of recently discovered issues. Below is an exhaustive list of updates performed to the archive
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** api.binance.com/fapi returned HTTP 451 from this egress; the market-data-only mirror works. ToS/licence text NOT_FOUND

#### Binance Vision bulk (data.binance.vision)  `binance_vision`
* **Asset/gap classes:** SPOT, FUND, OI, BASIS, BAR_MTF · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET data.binance.vision/data/{spot|futures/um}/{daily|monthly}/{klines|trades|metrics|fundingRate|premiumIndexKlines}/... + .CHECKSUM; S3 listing via s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** spot BTCUSDT 1m from 2017-08 (observed 21,360 rows in 2017-08 file); futures um metrics (OI, LSR) 5-min daily files (289 rows)  ·  docs: All symbols are supported, with new daily data becoming available the next day and new monthly data at the first monday of the month.
* **Streaming:** n/a
* **Update frequency:** daily files, published ~1 day after day end
* **Timestamp semantics:** *** SPOT files switched from ms to MICROSECOND epoch between the 2024-12 and 2025-01 monthly files (13 vs 16 digits) *** ; futures klines stay ms  ·  docs: Note: The timestamp for SPOT Data from January 1st 2025 onwards will be in microseconds. Klines columns: Open time ... Close time
* **Provider IDs:** file names by symbol/date; ETag + CHECKSUM (sha256 verified OK)
* **Revision behaviour:** daily bulk == API klines for 2026-09-26: 1440/1440 bars identical (OBSERVED); older-file revision not tested  ·  docs: Archived files may be updated at a later date as a result of recently discovered issues. / 2022-08-08 ... Fixed inconsistent data
* **Finality semantics:** immutable dated files; Last-Modified/ETag observable
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** Only source with bulk OI/LSR (metrics) + funding + premium index for Binance perps; liquidationSnapshot & bookTicker folders 404 for BTCUSDT

#### Binance.US  `binance_us`
* **Asset/gap classes:** SPOT · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.binance.us/api/v3/klines
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** 1000 rows/req  ·  docs: NOT_FOUND
* **Streaming:** not tested
* **Update frequency:** 1m bars
* **Timestamp semantics:** ms  ·  docs: NOT_FOUND
* **Provider IDs:** BTCUSDT
* **Revision behaviour:** 0 revised  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** 112/240 zero-volume bars; corr 0.59: too thin

#### Binance main REST/WS (api/fapi.binance.com)  `binance_main`
* **Asset/gap classes:** SPOT, FUND, OI, LIQ · **cost:** UNKNOWN · **executed:** BLK
* **Endpoint:** api.binance.com, fapi.binance.com, stream.binance.com
* **Auth:** HTTP 451 (restricted location) from test egress
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** WS reset
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** NOT TESTED: blocked at test egress; capability from Vision/mirror only

#### Bybit v5  `bybit`
* **Asset/gap classes:** SPOT, FUND, OI, LIQ · **cost:** UNKNOWN · **executed:** BLK
* **Endpoint:** api.bybit.com, api.bybit.nl, stream.bybit.com
* **Auth:** HTTP 403 CloudFront country block from test egress
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** NOT TESTED (geo-block)

#### CoinGecko public API  `coingecko`
* **Asset/gap classes:** SPOT · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.coingecko.com/api/v3/coins/bitcoin/ohlc
* **Auth:** none for the call executed (docs: demo plan/key limits)
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** Demo plan: 100 calls/min, 10k call credits/mo (pricing page)
* **Historical depth (OBSERVED):** days=1 returns 30-minute candles (observed)  ·  docs: Historical data on the Basic plan is restricted to the past 2 years. (OHLC docs); pricing table shows '1 year' daily historical for Demo; OHLC days: '1','7','14','30','90…
* **Streaming:** n/a
* **Update frequency:** 30-min candle
* **Timestamp semantics:** ms epoch  ·  docs: The timestamp in the response indicates the close time of each OHLC candle. / The last completed UTC day (00:00) is available 35 minutes after midnight (00:35 UTC).
* **Provider IDs:** coin id
* **Revision behaviour:** not tested  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** you shall duly attribute ownership of the CoinGecko API to CoinGecko by displaying prominently the message 'Powered by CoinGecko' / you are not permitted to sell, rent, l…
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** aggregated pricing, coarse bars; attribution required by terms; MCP connector failed to connect in this session

#### CryptoCompare / CoinDesk data API  `cryptocompare`
* **Asset/gap classes:** SPOT · **cost:** UNKNOWN · **executed:** N
* **Endpoint:** GET min-api.cryptocompare.com/data/v2/histominute
* **Auth:** HTTP 401 'API key required'
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** key required; free tier existence NOT verified here

#### Coinalyze API  `coinalyze`
* **Asset/gap classes:** FUND, OI, LIQ · **cost:** UNKNOWN · **executed:** N
* **Endpoint:** GET api.coinalyze.net/v1/*
* **Auth:** HTTP 401 'Invalid/Missing API key'
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** aggregated OI/funding/liquidations vendor - highest-relevance UNTESTED candidate; free-key terms UNKNOWN

#### alternative.me Fear&Greed  `alt_fng`
* **Asset/gap classes:** NEWS · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.alternative.me/fng/?limit=N
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** Limits: Please respect our server capacities and avoid unnecessary requests, our endpoints will only update every 5 minutes anyway. (crypto API docs; no numeric FNG limit…
* **Historical depth (OBSERVED):** 3159 daily rows (limit=0)  ·  docs: limit: Limit the number of returned results. The default value is '1', use '0' for all available data.
* **Streaming:** n/a
* **Update frequency:** daily
* **Timestamp semantics:** epoch s + time_until_update  ·  docs: Timestamp format: Unix time (default); time_until_update returned only for latest value; date_format option
* **Provider IDs:** -
* **Revision behaviour:** not tested  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** Commercial use is allowed as long as the attribution is given right next to the display of the data. / You must properly acknowledge the source of the data and prominentl…
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** sentiment index, commercial use allowed with attribution per docs

#### mempool.space / blockchain.info charts  `onchain`
* **Asset/gap classes:** NEWS · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET mempool.space/api/v1/prices ; api.blockchain.info/charts/hash-rate
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** 5-day chart window  ·  docs: NOT_FOUND
* **Streaming:** n/a
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** epoch s  ·  docs: NOT_FOUND
* **Provider IDs:** -
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** auxiliary, off-scope for market data gaps

### FX / gold

#### ECB Data Portal (SDMX) + eurofxref  `ecb`
* **Asset/gap classes:** FX · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=csvdata|jsondata; www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** from 1999-01-04 (observed); daily reference rate 14:15 CET  ·  docs: startPeriod & endPeriod (Defining a date range) - 'It is possible to define a date range for which Observations are to be returned'; no max stated
* **Streaming:** n/a
* **Update frequency:** daily
* **Timestamp semantics:** observation date (TIME_PERIOD); OBS_STATUS column; `updatedAfter` param accepted (200)  ·  docs: Periods: YYYY for annual; YYYY-MM for monthly; YYYY-MM-DD for daily. EUR ref rates: 'based on the daily concertation procedure ... around 14:10 CET' (euro FX ref rates pa…
* **Provider IDs:** series key EXR/D.USD.EUR.SP00.A
* **Revision behaviour:** revisions exposed via OBS_STATUS/updatedAfter (mechanism accepted; no revision seen)  ·  docs: Developers who update their local databases with data stored in the ECB Data Portal should make use of the updatedAfter parameter
* **Finality semantics:** OBS_STATUS
* **Licence / ToS (DOCUMENTED_CLAIM):** When such information is distributed or reproduced, it must appear accurately and the ECB must be cited as the source.
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** reference (fixing) rate, not tradable price

#### Frankfurter  `frankfurter`
* **Asset/gap classes:** FX · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.frankfurter.dev/v1/latest | /v1/{date}..{date}
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** Requests are rate-limited to prevent abuse, but there are no monthly or daily caps.
* **Historical depth (OBSERVED):** from 1999 (observed 2019-12-31 boundary example)  ·  docs: For large date ranges, request NDJSON to stream results line by line. (no explicit max range)
* **Streaming:** n/a
* **Update frequency:** daily
* **Timestamp semantics:** date  ·  docs: Frankfurter tracks daily exchange rates from 104 central banks and off[icial providers] (daily date-stamped rates; time-of-day not stated)
* **Provider IDs:** -
* **Revision behaviour:** none exposed  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** The rates themselves fall under each provider's terms.
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** values identical to ECB for the 8 overlapping days (derived, not independent)

#### Bank of England IADB  `boe`
* **Asset/gap classes:** FX, MACRO · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&SeriesCodes=XUDLUSS
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** daily (from 2026-09-01 in probe)  ·  docs: The new/revised data filter was enabled on 3 June 2007 and therefore won't allow a request prior to this date.
* **Streaming:** n/a
* **Update frequency:** daily
* **Timestamp semantics:** date string  ·  docs: Daily rates will be updated at 9:30am, no more than two working days after the date to which they relate.
* **Provider IDs:** series code XUDLUSS
* **Revision behaviour:** not tested  ·  docs: This option flags new and revised data observations between the selected date ranges that have been published; (a) since the previous publication or (b) from a given date…
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** GBP/USD spot 4pm; XUDLERS is EUR-per-GBP (not EURUSD)

#### Bank of Canada Valet  `boc`
* **Asset/gap classes:** FX, MACRO · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=N
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** recent=N  ·  docs: NOT_FOUND
* **Streaming:** n/a
* **Update frequency:** daily
* **Timestamp semantics:** date  ·  docs: NOT_FOUND
* **Provider IDs:** series FXUSDCAD
* **Revision behaviour:** not tested  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** the Bank permits you to freely use, copy, distribute and transmit its website content under the following terms: 1.1. Attribution You must attribute the Bank of Canada as…
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** free-use terms quoted in docs

#### open.er-api.com  `openerapi`
* **Asset/gap classes:** FX · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET open.er-api.com/v6/latest/USD
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** Rate Limiting: our open access free exchange rate API has to be rate limited. If you only request once every 24 hours you won't need to read any more of this section. Rat…
* **Historical depth (OBSERVED):** latest only  ·  docs: Open access returns latest rates only; no historical endpoint documented in open access docs (Free plan differs)
* **Streaming:** n/a
* **Update frequency:** daily
* **Timestamp semantics:** time_last_update_utc / time_next_update_utc  ·  docs: response fields time_last_update_unix / time_last_update_utc / time_next_update_unix (example "time_last_update_utc": "Fri, 02 Apr 2020 00:06:37 +0000")
* **Provider IDs:** -
* **Revision behaviour:** overwritten daily  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** This open access API is subject to our Terms and requires attribution. / this license does not permit re-distribution of our data.
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** terms: attribution; no redistribution

#### fawazahmed0/currency-api (jsDelivr)  `fawaz`
* **Asset/gap classes:** FX · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** versioned by npm date tag (not tested)  ·  docs: NOT_FOUND
* **Streaming:** n/a
* **Update frequency:** daily
* **Timestamp semantics:** date  ·  docs: NOT_FOUND
* **Provider IDs:** -
* **Revision behaviour:** versioned CDN snapshots (DOCUMENTED shape, untested)  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** licence NOT_FOUND

#### Yahoo Finance chart endpoint (unofficial)  `yahoo`
* **Asset/gap classes:** FX, GOLD, COMM, MACRO, BAR_MTF · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1m|1h|1d&range=5d|1mo
* **Auth:** none (unofficial)
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** 1m: 534 bars in 1d range (GC=F); 5d hourly ~106 bars  ·  docs: NOT_FOUND
* **Streaming:** n/a
* **Update frequency:** 1m
* **Timestamp semantics:** epoch s; null closes possible (EURUSD=X 2026-09-28 daily close null)  ·  docs: NOT_FOUND
* **Provider IDs:** Yahoo symbols (GC=F, CL=F, EURUSD=X)
* **Revision behaviour:** not tested  ·  docs: NOT_FOUND
* **Finality semantics:** meta.regularMarketTime
* **Licence / ToS (DOCUMENTED_CLAIM):** (Yahoo developer API terms, not Finance-chart specific) prohibits: 'Sell, lease, share, transfer, or sublicense the Yahoo APIs or access or access codes thereto or derive…
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** HTTP 429 seen on root probe and NG=F; XAUUSD=X returned no data; ToS restrictive on redistribution (docs: developer terms)

#### Dukascopy historical feed (bi5)  `dukascopy`
* **Asset/gap classes:** FX, GOLD, COMM, BAR_MTF · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET datafeed.dukascopy.com/datafeed/XAUUSD/2024/00/02/10h_ticks.bi5 (LZMA; 20-byte big-endian ticks)
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** tick file decoded: 4,969 ticks for one hour; candle endpoints returned HTTP 429  ·  docs: You can download forex data for major currency pairs and other assets. The data is in .csv format and you can download it in different timeframes, from tick-by-tick to mo…
* **Streaming:** n/a
* **Update frequency:** tick
* **Timestamp semantics:** ms offset from hour start (month index 0-based in URL)  ·  docs: Timestamp uint32: Milliseconds since start of day (UTC)  (Dukascopy wiki data-export, .bi5 tick format)
* **Provider IDs:** instrument code
* **Revision behaviour:** historical files static (not tested for change)  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** you agree to use the WEBSITE solely for your own non-commercial use and benefit, and not for resale or other transfer ...; you may download material ... for your own pers…
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** non-commercial only (docs quote); decoder needed; 20 s download latency once

#### gold-api.com  `goldapi`
* **Asset/gap classes:** GOLD · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.gold-api.com/price/XAU
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** No Rate Limiting for real time prices; Free: 10 API requests/hour to the price history API OR the OHLC Endpoint
* **Historical depth (OBSERVED):** spot only (history 10 req/h on free)  ·  docs: Premium: Unlimited API requests, including the price history API; Minute and Hour Aggregations on the price history API
* **Streaming:** n/a
* **Update frequency:** ~1 min (updatedAt)
* **Timestamp semantics:** updatedAt ISO  ·  docs: NOT_FOUND
* **Provider IDs:** symbol
* **Revision behaviour:** overwritten  ·  docs: gold-api.com makes no guarantees regarding the accuracy, completeness, or reliability of any Data provided through the Service.
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** Terms: The Service is provided 'as is'; 'If you send multiple requests per second or otherwise abuse the Service, your IP address may be temporarily or permanently banned…
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** snapshot only

#### Swissquote public quotes  `swissquote`
* **Asset/gap classes:** GOLD, FX · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** snapshot  ·  docs: NOT_FOUND
* **Streaming:** n/a
* **Update frequency:** sub-second ts
* **Timestamp semantics:** ts ms  ·  docs: NOT_FOUND
* **Provider IDs:** XAU/USD
* **Revision behaviour:** overwritten  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** undocumented endpoint; bid 4152.875 / ask 4153.565 at snapshot

#### Tokenised-gold pairs (PAXG/XAUT on OKX, Kraken, Coinbase, Deribit, Hyperliquid xyz)  `tokgold`
* **Asset/gap classes:** GOLD · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** OKX XAUT-USDT, Kraken PAXGUSD/XAUTUSD, Coinbase PAXG-USD, Deribit PAXG_USDC-PERPETUAL, Hyperliquid allMids dex=xyz
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** 1H bars fetched on all four venues  ·  docs: NOT_FOUND
* **Streaming:** WS on the venues
* **Update frequency:** 24/7
* **Timestamp semantics:** as venue  ·  docs: NOT_FOUND
* **Provider IDs:** venue symbols
* **Revision behaviour:** as venue  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** 24/7 gold proxies; snapshot spread vs XAU spot proxy: OKX XAUT +0.07%, Kraken XAUT +0.05%, PAXG +0.19..+0.21%, Deribit PAXG perp +0.4%: token != spot XAU

#### LBMA precious metals prices (prices.lbma.org.uk JSON)  `lbma`
* **Asset/gap classes:** GOLD · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET prices.lbma.org.uk/json/gold_am.json
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** 14,844 rows from 1968-01-02 (observed)  ·  docs: NOT_FOUND
* **Streaming:** n/a
* **Update frequency:** 2x daily benchmark
* **Timestamp semantics:** date string; v=[USD,GBP,EUR]  ·  docs: The LBMA Gold Price is set twice daily in auctions ... commencing at 10:30 and 15:00 London time. The LBMA Silver Price is set daily ... commencing at 12:00 noon London t…
* **Provider IDs:** -
* **Revision behaviour:** not tested  ·  docs: NOT_FOUND
* **Finality semantics:** benchmark auction result
* **Licence / ToS (DOCUMENTED_CLAIM):** A licence from IBA is required in order to obtain, use or redistribute real-time or historical LBMA Platinum and Palladium Price data
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** docs: IBA licence required to redistribute (quoted for platinum/palladium; gold terms not verified)

#### Trading Economics API  `tradingeconomics`
* **Asset/gap classes:** MACRO, CAL, FX, COMM · **cost:** PAID_ONLY · **executed:** N
* **Endpoint:** GET api.tradingeconomics.com/calendar?c=guest:guest
* **Auth:** guest key discontinued (HTTP 410, observed)
* **Free tier / public access:** PAID_ONLY
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** paid subscription required

#### exchangerate.host  `exchangerate_host`
* **Asset/gap classes:** FX · **cost:** UNKNOWN · **executed:** N
* **Endpoint:** GET api.exchangerate.host/latest
* **Auth:** missing_access_key error (200 body)
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** free-plan capability UNKNOWN

#### Alpha Vantage (demo key)  `alphavantage`
* **Asset/gap classes:** FX · **cost:** FREE_TIER · **executed:** Y
* **Endpoint:** GET www.alphavantage.co/query?function=FX_DAILY&from_symbol=EUR&to_symbol=USD&apikey=demo
* **Auth:** demo key worked for EURUSD; own key required otherwise
* **Free tier / public access:** FREE_TIER
* **Rate limit (DOCUMENTED_CLAIM):** We are pleased to provide free stock API service covering the majority of our datasets for 25 API requests per day and unlimited API requests for verified open-source or …
* **Historical depth (OBSERVED):** daily series (depth not measured)  ·  docs: TIME_SERIES_DAILY: 'covering 25+ years of historical data'; intraday: 'Any month in the last 25+ years since 2000-01'; outputsize compact = latest 100 data points
* **Streaming:** n/a
* **Update frequency:** daily
* **Timestamp semantics:** date  ·  docs: Intraday regular hours '9:30am to 4:00pm US Eastern Time'; FX endpoints return '(timestamp, open, high, low, close)'; bar timestamp semantic not stated
* **Provider IDs:** -
* **Revision behaviour:** not tested  ·  docs: By default, adjusted=true and the output time series is adjusted by historical split and dividend events.
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** docs: 25 requests/day free; EURUSD close 1.13700 on 2026-09-28 vs ECB fix 1.1378 (different time basis)

#### Twelve Data (demo key)  `twelvedata`
* **Asset/gap classes:** FX · **cost:** FREE_TIER · **executed:** Y
* **Endpoint:** GET api.twelvedata.com/time_series?symbol=EUR/USD&interval=1h|1day&apikey=demo
* **Auth:** demo key worked
* **Free tier / public access:** FREE_TIER
* **Rate limit (DOCUMENTED_CLAIM):** 8 API credits per minute (800 a day) on Basic (free) plan; 'API credits quota will be reset each minute'
* **Historical depth (OBSERVED):** 5 rows requested  ·  docs: outputsize: Number of data points to retrieve. Supports values in the range from 1 to 5000.
* **Streaming:** n/a
* **Update frequency:** 1h/1d
* **Timestamp semantics:** datetime string (timezone not stated in payload sample)  ·  docs: timezone param: 'UTC for datetime at universal UTC standard'; or exchange local / IANA name (default per docs; open/close semantics not verified)
* **Provider IDs:** -
* **Revision behaviour:** not tested  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** Personal & non-commercial: Access the data for personal, internal, and non-commercial purposes.
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** free plan: personal/internal/non-commercial (docs quote)

#### Polygon.io  `polygon`
* **Asset/gap classes:** FX · **cost:** UNKNOWN · **executed:** N
* **Endpoint:** GET api.polygon.io/v2/aggs/ticker/C:EURUSD/...
* **Auth:** HTTP 401 without key
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** 5 API Calls / Minute (Stocks Basic free plan)
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: 2 Years Historical Data; End of Day Data (Basic plan); aggs limit: Max 50,000; default 5,000
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: The Unix millisecond timestamp for the start of the aggregate window (field t)
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: Results are adjusted for splits by default; set adjusted: false to disable
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** free plan 'for personal use only' (pricing page summary; Terms index page lists separate Individuals/Businesses ToS, not read)
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** free plan documented for stocks (5 calls/min); FX capability on free plan UNKNOWN

#### Finnhub  `finnhub`
* **Asset/gap classes:** CAL, FX · **cost:** UNKNOWN · **executed:** N
* **Endpoint:** GET finnhub.io/api/v1/calendar/economic
* **Auth:** HTTP 401 'Please use an API key'
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** You hereby agree to not redistribute or share access to data or derived results from the data obtained from Finnhub with anyone or any 3rd party without written approval …
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** docs: no redistribution of data or derived results; economic-calendar free-tier capability UNKNOWN

#### Financial Modeling Prep  `fmp`
* **Asset/gap classes:** CAL · **cost:** FREE_WITH_ACCOUNT · **executed:** N
* **Endpoint:** GET financialmodelingprep.com/api/v3/economic_calendar
* **Auth:** HTTP 401 'Invalid API KEY ... create a Free API Key'
* **Free tier / public access:** FREE_WITH_ACCOUNT
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** legacy /api/v3 endpoint; free-tier calendar capability UNKNOWN

#### OANDA fxTrade Practice API  `oanda`
* **Asset/gap classes:** FX · **cost:** UNKNOWN · **executed:** N
* **Endpoint:** GET api-fxpractice.oanda.com/v3/instruments/EUR_USD/candles
* **Auth:** HTTP 401 without token
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** 120 requests per second. Excess requests will receive HTTP 429 error.
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** practice account needed; not tested

#### Stooq CSV  `stooq`
* **Asset/gap classes:** FX, GOLD, COMM · **cost:** UNKNOWN · **executed:** BLK
* **Endpoint:** GET stooq.com/q/d/l/?s=xauusd&i=d
* **Auth:** connection reset from test egress
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** NOT TESTED

#### metals.live / goldprice.org  `metals_live`
* **Asset/gap classes:** GOLD · **cost:** UNKNOWN · **executed:** BLK
* **Endpoint:** api.metals.live (SSL error), data-asg.goldprice.org (403)
* **Auth:** UNKNOWN
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** NOT TESTED

### Commodities / macro

#### FRED API + fredgraph.csv  `fred`
* **Asset/gap classes:** MACRO, COMM · **cost:** FREE_WITH_ACCOUNT · **executed:** PART
* **Endpoint:** GET api.stlouisfed.org/fred/series/observations (key); fred.stlouisfed.org/graph/fredgraph.csv (keyless)
* **Auth:** free API key required (HTTP 400 'api_key not set' observed); keyless CSV unreachable from test egress (proxy closes connection)
* **Free tier / public access:** FREE_WITH_ACCOUNT
* **Rate limit (DOCUMENTED_CLAIM):** The Federal Reserve Bank of St. Louis may impose or adjust the limit on the amount of bandwidth you may use or the number of transactions you may send or receive through …
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: limit: maximum value 100,000 observations per request; observation_start default 1776-07-04, observation_end default 9999-12-31
* **Streaming:** n/a
* **Update frequency:** daily-monthly
* **Timestamp semantics:** observation date; realtime_start/realtime_end params (DOCUMENTED, not executed)  ·  docs: NOT_FOUND
* **Provider IDs:** series id
* **Revision behaviour:** ALFRED vintages (DOCUMENTED)  ·  docs: output_type options: 'Observations by Vintage Date, New and Revised Observations Only' (3) and 'Observations, Initial Release Only' (4); default real-time period is today
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** Data series available through the FRED® API, may be owned by third parties and subject to copyright restrictions... Before using data series owned by third parties for an…
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** DATA PATH NOT EXECUTED. Highest-priority follow-up: run with a free key from an unrestricted network. Third-party series carry copyright restrictions (docs quote)

#### ALFRED (archival FRED)  `alfred`
* **Asset/gap classes:** MACRO · **cost:** FREE_WITH_ACCOUNT · **executed:** BLK
* **Endpoint:** GET alfred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1&vintage_date=... ; API realtime_start/end
* **Auth:** free API key for API; host unreachable from test egress
* **Free tier / public access:** FREE_WITH_ACCOUNT
* **Rate limit (DOCUMENTED_CLAIM):** Same FRED API terms: FRB St. Louis 'may impose or adjust the limit on the amount of bandwidth you may use or the number of transactions'
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: ALFRED® allows you to retrieve each economic data release (vintage) that was available on a specific date in history. / Economic data time travel since 2006
* **Streaming:** n/a
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** vintage_date / realtime_start/realtime_end (URL parameters accepted by design; DOCUMENTED_CLAIM, NOT verified)  ·  docs: The real-time period marks when facts were true or when information was known until it changed.
* **Provider IDs:** series id
* **Revision behaviour:** full vintage history (DOCUMENTED_CLAIM)  ·  docs: ALFRED® users can change the real-time period to retrieve information that was known as of a past period of history.
* **Finality semantics:** as-of vintage dates
* **Licence / ToS (DOCUMENTED_CLAIM):** Same FRED API terms: third-party series 'subject to copyright restrictions'; must display 'This product uses the FRED® API but is not endorsed or certified by the Federal…
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** PIT_NATIVE is a documented claim only - execution blocked

#### EIA Open Data API v2  `eia`
* **Asset/gap classes:** COMM, MACRO · **cost:** FREE_WITH_ACCOUNT · **executed:** N
* **Endpoint:** GET api.eia.gov/v2/petroleum/pri/spt/data/
* **Auth:** API_KEY_MISSING (HTTP 403) - free registration (message)
* **Free tier / public access:** FREE_WITH_ACCOUNT
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: The API can only return 5000 rows in JSON format. Please consider constraining your request with facet, start, or end, or using offset to paginate results.
* **Streaming:** n/a
* **Update frequency:** daily/weekly
* **Timestamp semantics:** period  ·  docs: NOT_FOUND
* **Provider IDs:** route/series
* **Revision behaviour:** not tested  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** U.S. government publications are in the public domain and are not subject to copyright protection.
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** not executed: needs key. Public-domain per docs

#### BLS Public Data API  `bls`
* **Asset/gap classes:** MACRO · **cost:** FREE_TIER · **executed:** Y
* **Endpoint:** POST/GET api.bls.gov/publicAPI/v1|v2/timeseries/data/{id}
* **Auth:** v1 keyless (25 queries/day documented); v2 needs registration key (500/day documented)
* **Free tier / public access:** FREE_TIER
* **Rate limit (DOCUMENTED_CLAIM):** Daily query limit: 500 (v2.0 registered) vs 25 (v1.0); Series per query limit: 50 vs 25
* **Historical depth (OBSERVED):** v1: ~10 years (DOCUMENTED, not measured)  ·  docs: Years per query limit: 20 (v2.0) vs 10 (v1.0)
* **Streaming:** n/a
* **Update frequency:** monthly
* **Timestamp semantics:** year+period; footnote codes  ·  docs: NOT_FOUND
* **Provider IDs:** series id CUUR0000SA0
* **Revision behaviour:** latest-only values; revisions not tracked in API  ·  docs: NOT_FOUND
* **Finality semantics:** footnotes (P=preliminary)
* **Licence / ToS (DOCUMENTED_CLAIM):** Data accessed through BLS.gov do not, and should not, include controls over its end use. / cite the date that data were accessed or retrieved
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** OBSERVED: first probe returned REQUEST_NOT_PROCESSED daily-threshold message, later probe REQUEST_SUCCEEDED => shared-IP/day quota unpredictable

#### US Treasury daily par yield curve (CSV)  `treasury_yc`
* **Asset/gap classes:** MACRO · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve&_format=csv
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** per-year files back to 1990 (35 rows returned for 1990 probe, 24 for 2026 YTD - both fewer than expected trading days: UNEXPLAINED)  ·  docs: Treasury provides historical data back to 2000. (page text)
* **Streaming:** n/a
* **Update frequency:** daily
* **Timestamp semantics:** MM/DD/YYYY  ·  docs: The par yields are derived from input market prices, which are indicative quotations obtained by the Federal Reserve Bank of New York at approximately 3:30 PM each busine…
* **Provider IDs:** column per tenor
* **Revision behaviour:** not tested  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** row counts anomalous; verify pagination before relying on it

#### US Treasury FiscalData API  `treasury_fd`
* **Asset/gap classes:** MACRO · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/...
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** 2001-01-31 earliest in probe  ·  docs: page[size]= and page[number]= ... The page size will set the number of rows that are returned on a request; neither pagination parameter is required (max not stated)
* **Streaming:** n/a
* **Update frequency:** monthly
* **Timestamp semantics:** record_date  ·  docs: NOT_FOUND
* **Provider IDs:** -
* **Revision behaviour:** not tested  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** The data is offered free, without restriction, and available to copy, adapt, redistribute, or otherwise use for non-commercial or commercial purposes.
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** public domain 'without restriction' (docs quote); low frequency

#### NY Fed Markets API (SOFR etc.)  `nyfed`
* **Asset/gap classes:** MACRO · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET markets.newyorkfed.org/api/rates/secured/sofr/last/N.json | search.json?startDate=&endDate=
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** from 2018-04-03 (observed)  ·  docs: NOT_FOUND
* **Streaming:** n/a
* **Update frequency:** daily
* **Timestamp semantics:** effectiveDate  ·  docs: NOT_FOUND
* **Provider IDs:** -
* **Revision behaviour:** `revisionIndicator` field per row (OBSERVED, empty in sample)  ·  docs: NOT_FOUND
* **Finality semantics:** revisionIndicator
* **Licence / ToS (DOCUMENTED_CLAIM):** In general, the New York Fed intends for Website visitors to have permission to use and share Content.
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** closest to native revision signalling among keyless macro sources

#### CFTC Commitments of Traders (Socrata)  `cftc`
* **Asset/gap classes:** COMM, GOLD, MACRO · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET publicreporting.cftc.gov/resource/6dca-aqww.json?$where=...&$order=...
* **Auth:** none (app token optional)
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** Socrata: we do not throttle API requests that are using an application token, unless those requests are determined to be abusive; requests without token come from a share…
* **Historical depth (OBSERVED):** from 1986-01-15 (observed)  ·  docs: Each historical report is viewable with the data for the respective reporting week, along with all historical data compressed within an annual file.
* **Streaming:** n/a
* **Update frequency:** weekly
* **Timestamp semantics:** report_date_as_yyyy_mm_dd (as-of Tuesday); publication lag NOT in payload  ·  docs: The COT Report is generally published each Friday at 3:30 pm Eastern Time (US), using the data from the immediately preceding Tuesday of that week.
* **Provider IDs:** cftc_contract_market_code (088691 = GOLD COMEX)
* **Revision behaviour:** not tested  ·  docs: The CFTC receives the data from the reporting firms on Wednesday morning and then corrects and verifies the data for release by Friday afternoon.
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** positioning, not price. Publication (release) timestamp absent => PIT needs external schedule

#### World Bank API + Commodity Pink Sheet  `worldbank`
* **Asset/gap classes:** MACRO, COMM · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET api.worldbank.org/v2/country/US/indicator/...; Pink Sheet monthly xlsx (765 KB downloaded)
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** annual indicators; monthly commodity xlsx (history depth not measured)  ·  docs: The default setting is 50 results per page (max not stated); Many data series date back over 50 years
* **Streaming:** n/a
* **Update frequency:** annual/monthly
* **Timestamp semantics:** `lastupdated` per response (2026-07-13)  ·  docs: date formats: yearly 2000, monthly 2012M01, quarterly 2013Q1, YTD:2013; ranges with colon '2000:2001'
* **Provider IDs:** indicator id
* **Revision behaviour:** overwrites  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** When you download or use the Datasets, you are agreeing to comply with the terms of a CC BY 4.0 license, and also agreeing to the following mandatory and binding addition
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** CC BY 4.0 per docs quote

#### Eurostat dissemination API  `eurostat`
* **Asset/gap classes:** MACRO · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?...
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** monthly  ·  docs: A request for full dataset could result in a response of up to several megabytes, and can be returned after several minutes. ... asynchronous requests may be useful.
* **Streaming:** n/a
* **Update frequency:** monthly
* **Timestamp semantics:** JSON-stat with `updated` dataset timestamp (2026-02-06 for the cube read)  ·  docs: NOT_FOUND
* **Provider IDs:** dataset code
* **Revision behaviour:** dataset-level `updated` stamp (OBSERVED); no vintages  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** Reuse of statistical data, metadata, publications, and other dissemination tools published on this website for commercial or non-commercial purposes is authorised provide…
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** dataset-level update stamp is a usable observation-time proxy

#### Swiss National Bank data portal  `snb`
* **Asset/gap classes:** MACRO, FX · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET data.snb.ch/api/cube/devkum/data/json/en
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** 891 KB cube  ·  docs: NOT_FOUND
* **Streaming:** n/a
* **Update frequency:** monthly
* **Timestamp semantics:** -  ·  docs: NOT_FOUND
* **Provider IDs:** -
* **Revision behaviour:** not tested  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** not evaluated beyond reachability

#### BEA API  `bea`
* **Asset/gap classes:** MACRO · **cost:** UNKNOWN · **executed:** N
* **Endpoint:** GET apps.bea.gov/api/data
* **Auth:** empty body without key
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** key required; free status not verified

#### IMF DataMapper API  `imf`
* **Asset/gap classes:** MACRO · **cost:** UNKNOWN · **executed:** BLK
* **Endpoint:** GET www.imf.org/external/datamapper/api/v1/...
* **Auth:** HTTP 403 from test egress
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** NOT TESTED

#### OECD SDMX  `oecd`
* **Asset/gap classes:** MACRO · **cost:** UNKNOWN · **executed:** N
* **Endpoint:** GET sdmx.oecd.org/public/rest/data/...
* **Auth:** my query key was malformed ('expecting 7 got 6'); not retried
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** NOT TESTED PROPERLY (own error)

### Calendar / news

#### Faireconomy/ForexFactory weekly calendar JSON  `faireconomy`
* **Asset/gap classes:** CAL · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET nfs.faireconomy.media/ff_calendar_thisweek.json (.xml also)
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** current week only: nextweek/lastweek 404 (observed)  ·  docs: NOT_FOUND
* **Streaming:** n/a
* **Update frequency:** weekly file
* **Timestamp semantics:** ISO-8601 with offset; 141 events; impact High/Medium/Low/Holiday  ·  docs: NOT_FOUND
* **Provider IDs:** none (title+country+date)
* **Revision behaviour:** no `actual` field at all in payload (0/141); two fetches 2 s apart identical  ·  docs: NOT_FOUND
* **Finality semantics:** none
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** schedule + forecast + previous only, no release values; unofficial; licence NOT_FOUND

#### federalreserve.gov FOMC calendar page  `fomc`
* **Asset/gap classes:** CAL · **cost:** FREE_UNAUTHENTICATED · **executed:** Y
* **Endpoint:** GET www.federalreserve.gov/monetarypolicy/fomccalendars.htm (HTML; 165 KB)
* **Auth:** none
* **Free tier / public access:** FREE_UNAUTHENTICATED
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** HTML scrape  ·  docs: NOT_FOUND
* **Streaming:** n/a
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** scrape only; not parsed

#### BLS release schedule ICS  `blsics`
* **Asset/gap classes:** CAL · **cost:** UNKNOWN · **executed:** BLK
* **Endpoint:** GET www.bls.gov/schedule/news_release/bls.ics
* **Auth:** HTTP 403 (HTML) from test egress
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** NOT TESTED

#### GDELT DOC API  `gdelt`
* **Asset/gap classes:** NEWS · **cost:** UNKNOWN · **executed:** BLK
* **Endpoint:** GET api.gdeltproject.org/api/v2/doc/doc
* **Auth:** connection reset from test egress
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: within 15 minutes of GDELT monitoring a news report ... GDELT Event and Global Knowledge Graph now update every 15 minutes.
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** all datasets released by the GDELT Project are available for unlimited and unrestricted use for any academic, commercial, or governmental use ... You may redistribute, re…
* **Commercial use / redistribution:** see licence quote; NOT verified beyond quote
* **Note:** NOT TESTED; docs: unrestricted use

#### TipRanks connector (economic calendar etc.)  `tipranks`
* **Asset/gap classes:** CAL, NEWS · **cost:** UNKNOWN · **executed:** N
* **Endpoint:** MCP connector in this session (get_economic_calendar, get_latest_news)
* **Auth:** account connector; terms UNKNOWN
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** deliberately NOT executed: would consume the account holder's quota and terms are unverified

#### CryptoPanic  `cryptopanic`
* **Asset/gap classes:** NEWS · **cost:** UNKNOWN · **executed:** BLK
* **Endpoint:** GET cryptopanic.com/api/v1/posts/?public=true
* **Auth:** HTTP 403 (Cloudflare page)
* **Free tier / public access:** UNKNOWN
* **Rate limit (DOCUMENTED_CLAIM):** NOT_FOUND
* **Historical depth (OBSERVED):** UNKNOWN  ·  docs: NOT_FOUND
* **Streaming:** UNKNOWN
* **Update frequency:** UNKNOWN
* **Timestamp semantics:** UNKNOWN  ·  docs: NOT_FOUND
* **Provider IDs:** UNKNOWN
* **Revision behaviour:** UNKNOWN  ·  docs: NOT_FOUND
* **Finality semantics:** UNKNOWN
* **Licence / ToS (DOCUMENTED_CLAIM):** NOT_FOUND
* **Commercial use / redistribution:** UNKNOWN (no official text retrieved)
* **Note:** NOT TESTED
