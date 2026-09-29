import json, sys
from probe_lib import call
now=None
T=[
# spot
("okx_spot_candles","https://www.okx.com/api/v5/market/candles",{"instId":"BTC-USDT","bar":"1m","limit":"100"}),
("kraken_ohlc","https://api.kraken.com/0/public/OHLC",{"pair":"XBTUSD","interval":"1"}),
("coinbase_candles","https://api.exchange.coinbase.com/products/BTC-USD/candles",{"granularity":"60"}),
("bitstamp_ohlc","https://www.bitstamp.net/api/v2/ohlc/btcusd/",{"step":"60","limit":"100"}),
("bitfinex_candles","https://api-pub.bitfinex.com/v2/candles/trade:1m:tBTCUSD/hist",{"limit":"100"}),
("kucoin_klines","https://api.kucoin.com/api/v1/market/candles",{"symbol":"BTC-USDT","type":"1min"}),
("gemini_candles","https://api.gemini.com/v2/candles/btcusd/1m",None),
("gateio_spot","https://api.gateio.ws/api/v4/spot/candlesticks",{"currency_pair":"BTC_USDT","interval":"1m","limit":"100"}),
("bitget_spot","https://api.bitget.com/api/v2/spot/market/candles",{"symbol":"BTCUSDT","granularity":"1min","limit":"100"}),
("mexc_spot","https://api.mexc.com/api/v3/klines",{"symbol":"BTCUSDT","interval":"1m","limit":"100"}),
("htx_spot","https://api.huobi.pro/market/history/kline",{"symbol":"btcusdt","period":"1min","size":"100"}),
("cryptocompare","https://min-api.cryptocompare.com/data/v2/histominute",{"fsym":"BTC","tsym":"USD","limit":"100"}),
("coingecko_ohlc","https://api.coingecko.com/api/v3/coins/bitcoin/ohlc",{"vs_currency":"usd","days":"1"}),
("coinpaprika","https://api.coinpaprika.com/v1/tickers/btc-bitcoin",None),
("binance_vision_list","https://data.binance.vision/?prefix=data/spot/daily/klines/BTCUSDT/1m/",None),
("binance_us","https://api.binance.us/api/v3/klines",{"symbol":"BTCUSDT","interval":"1m","limit":"100"}),
("binance_data_api","https://data-api.binance.vision/api/v3/klines",{"symbol":"BTCUSDT","interval":"1m","limit":"100"}),
("bybit_kline","https://api.bybit.com/v5/market/kline",{"category":"spot","symbol":"BTCUSDT","interval":"1","limit":"100"}),
("bybit_nl","https://api.bybit.nl/v5/market/kline",{"category":"spot","symbol":"BTCUSDT","interval":"1","limit":"100"}),
# derivs
("okx_funding","https://www.okx.com/api/v5/public/funding-rate-history",{"instId":"BTC-USDT-SWAP","limit":"100"}),
("okx_oi","https://www.okx.com/api/v5/public/open-interest",{"instType":"SWAP","instId":"BTC-USDT-SWAP"}),
("okx_oi_hist","https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-history",{"instId":"BTC-USDT-SWAP","period":"5m"}),
("okx_liq","https://www.okx.com/api/v5/public/liquidation-orders",{"instType":"SWAP","uly":"BTC-USDT","state":"filled"}),
("okx_mark_candles","https://www.okx.com/api/v5/market/mark-price-candles",{"instId":"BTC-USDT-SWAP","bar":"1m"}),
("okx_opt_summary","https://www.okx.com/api/v5/public/opt-summary",{"uly":"BTC-USD"}),
("deribit_funding","https://www.deribit.com/api/v2/public/get_funding_rate_history",{"instrument_name":"BTC-PERPETUAL","start_timestamp":"1780000000000","end_timestamp":"1790000000000"}),
("deribit_chart","https://www.deribit.com/api/v2/public/get_tradingview_chart_data",{"instrument_name":"BTC-PERPETUAL","resolution":"1","start_timestamp":"1790000000000","end_timestamp":"1790100000000"}),
("deribit_book_summary_opt","https://www.deribit.com/api/v2/public/get_book_summary_by_currency",{"currency":"BTC","kind":"option"}),
("deribit_dvol","https://www.deribit.com/api/v2/public/get_volatility_index_data",{"currency":"BTC","start_timestamp":"1790000000000","end_timestamp":"1790100000000","resolution":"3600"}),
("deribit_trades","https://www.deribit.com/api/v2/public/get_last_trades_by_currency",{"currency":"BTC","kind":"option","count":"100"}),
("deribit_ticker_perp","https://www.deribit.com/api/v2/public/ticker",{"instrument_name":"BTC-PERPETUAL"}),
("kraken_fut_tickers","https://futures.kraken.com/derivatives/api/v3/tickers",None),
("kraken_fut_hist_funding","https://futures.kraken.com/derivatives/api/v4/historicalfundingrates",{"symbol":"PF_XBTUSD"}),
("bitmex_funding","https://www.bitmex.com/api/v1/funding",{"symbol":"XBTUSD","count":"100","reverse":"true"}),
("bitmex_liq","https://www.bitmex.com/api/v1/liquidation",{"count":"50","reverse":"true"}),
("bitmex_bucketed","https://www.bitmex.com/api/v1/trade/bucketed",{"binSize":"1m","symbol":"XBTUSD","count":"100","reverse":"true"}),
("bitmex_instr","https://www.bitmex.com/api/v1/instrument",{"symbol":"XBTUSD"}),
("bitfinex_deriv_status","https://api-pub.bitfinex.com/v2/status/deriv",{"keys":"tBTCF0:USTF0"}),
("bitfinex_liq","https://api-pub.bitfinex.com/v2/liquidations/hist",{"limit":"50"}),
("gate_fut_funding","https://api.gateio.ws/api/v4/futures/usdt/funding_rate",{"contract":"BTC_USDT","limit":"100"}),
("gate_fut_liq","https://api.gateio.ws/api/v4/futures/usdt/liq_orders",{"contract":"BTC_USDT","limit":"100"}),
("gate_fut_stats","https://api.gateio.ws/api/v4/futures/usdt/contract_stats",{"contract":"BTC_USDT","interval":"5m","limit":"100"}),
("bitget_funding","https://api.bitget.com/api/v2/mix/market/history-fund-rate",{"symbol":"BTCUSDT","productType":"usdt-futures"}),
("bitget_oi","https://api.bitget.com/api/v2/mix/market/open-interest",{"symbol":"BTCUSDT","productType":"usdt-futures"}),
("mexc_fut_funding","https://contract.mexc.com/api/v1/contract/funding_rate/history",{"symbol":"BTC_USDT","page_num":"1","page_size":"100"}),
("kucoin_fut_funding","https://api-futures.kucoin.com/api/v1/contract/funding-rates",{"symbol":"XBTUSDTM","from":"1789000000000","to":"1790000000000"}),
("hyperliquid_meta","https://api.hyperliquid.xyz/info",None),
("dydx_candles","https://indexer.dydx.trade/v4/candles/perpetualMarkets/BTC-USD",{"resolution":"1MIN","limit":"100"}),
("dydx_funding","https://indexer.dydx.trade/v4/historicalFunding/BTC-USD",{"limit":"100"}),
("bybit_fund","https://api.bybit.com/v5/market/funding/history",{"category":"linear","symbol":"BTCUSDT","limit":"100"}),
("binance_fapi_funding","https://fapi.binance.com/fapi/v1/fundingRate",{"symbol":"BTCUSDT","limit":"100"}),
("binance_vision_um","https://data.binance.vision/?prefix=data/futures/um/daily/metrics/BTCUSDT/",None),
("coinalyze_demo","https://api.coinalyze.net/v1/exchanges",None),
("cryptocompare_fut","https://min-api.cryptocompare.com/data/v2/histohour",{"fsym":"BTC","tsym":"USDT","limit":"10"}),
]
res=[]
for n,u,p in T:
    o=call(n,u,p)
    j=o.get("json"); s=(json.dumps(j)[:140] if j is not None else (o.get("text") or o.get("err") or "")[:140].replace("\n"," "))
    print(f"{n:28s} {o.get('status')} {o.get('ms')}ms {o.get('bytes')}B | {s}")
    res.append({k:v for k,v in o.items() if k not in("json","text")})
json.dump(res,open("../results/sweep1.json","w"),indent=1)
