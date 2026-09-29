"""Landscape discovery via GitHub search API (unauthenticated, 10 req/min). Records raw metadata only; ranking is NOT by stars."""
import json, subprocess, time, sys, urllib.parse
Q = {
 "market_data_collector": ["cryptofeed", "market data websocket collector exchanges python", "ccxt websocket market data recorder"],
 "historical_downloader": ["historical market data downloader python", "tick data downloader dukascopy", "binance historical data download"],
 "order_book": ["limit order book python", "limit order book simulator", "order book reconstruction l2 l3 rust python"],
 "replay_engine": ["market data replay engine backtest tick", "event-driven backtest engine limit order book", "hft backtest queue position"],
 "event_simulator": ["agent-based market simulator limit order book", "market simulation exchange simulator python"],
 "transaction_cost": ["almgren chriss python", "market impact model python execution cost", "transaction cost analysis python"],
 "feature_computation": ["technical indicators python library", "streaming features online technical indicators", "order flow imbalance features limit order book"],
 "online_statistics": ["online machine learning streaming statistics python", "incremental rolling statistics python"],
 "portfolio_risk": ["portfolio optimization python library", "risk metrics python performance tearsheet", "value at risk library python"],
 "backtest_engine": ["backtesting framework python", "event-driven backtesting python", "vectorized backtesting python"],
 "market_calendar": ["market calendars python exchange trading calendar"],
 "data_quality": ["data validation dataframe python schema", "financial data quality checks ohlcv"],
 "timeseries_storage": ["time series database embedded python", "tick data storage python parquet arctic"],
}
out = {}
for cls, qs in Q.items():
    out[cls] = []
    for q in qs:
        url = "https://api.github.com/search/repositories?q=" + urllib.parse.quote(q + " archived:false") + "&sort=updated&order=desc&per_page=12"
        for attempt in range(3):
            r = subprocess.run(["curl", "-s", url], capture_output=True, text=True).stdout
            try: j = json.loads(r)
            except Exception: j = {}
            if "items" in j: break
            time.sleep(15)
        for it in j.get("items", []):
            out[cls].append(dict(query=q, full_name=it["full_name"], stars=it["stargazers_count"], pushed_at=it["pushed_at"][:10], license=(it.get("license") or {}).get("spdx_id"), language=it["language"], description=(it["description"] or "")[:110]))
        time.sleep(7)
json.dump(out, open(sys.argv[1], "w"), indent=1)
print({k: len(v) for k, v in out.items()})
