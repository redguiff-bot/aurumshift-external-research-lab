"""Matrice de capacités ccxt (REST unifié + WS ccxt.pro) pour les venues C0.
Lecture statique de exchange.has (aucun appel réseau). Usage: python ccxt_has_matrix.py > ccxt_has_matrix.json"""
import json, ccxt, ccxt.pro as pro
VENUES = ["binance", "binanceusdm", "okx", "bybit"]
SURFACES = {
  "bars": ["fetchOHLCV", "watchOHLCV"],
  "bbo": ["fetchTicker", "fetchBidsAsks", "watchTicker", "watchBidsAsks"],
  "depth": ["fetchOrderBook", "watchOrderBook"],
  "trades": ["fetchTrades", "watchTrades"],
  "funding": ["fetchFundingRate", "fetchFundingRates", "fetchFundingRateHistory", "watchFundingRate"],
  "funding_interval": ["fetchFundingInterval", "fetchFundingIntervals"],
  "open_interest": ["fetchOpenInterest", "fetchOpenInterestHistory", "fetchOpenInterests"],
  "mark_index": ["fetchMarkPrice", "fetchMarkPrices", "watchMarkPrice", "fetchMarkOHLCV", "fetchIndexOHLCV", "fetchPremiumIndexOHLCV"],
  "basis_inputs": ["fetchMarkOHLCV", "fetchIndexOHLCV"],
  "liquidations": ["fetchLiquidations", "watchLiquidations", "watchLiquidationsForSymbols"],
  "long_short": ["fetchLongShortRatio", "fetchLongShortRatioHistory"],
  "status_time": ["fetchStatus", "fetchTime"],
}
out = {"ccxt_version": ccxt.__version__, "matrix": {}}
for v in VENUES:
    rest = getattr(ccxt, v)(); ws = getattr(pro, v)()
    row = {}
    for s, methods in SURFACES.items():
        row[s] = {m: (ws.has.get(m) if m.startswith("watch") else rest.has.get(m)) for m in methods}
    out["matrix"][v] = row
    out.setdefault("rateLimit_ms", {})[v] = rest.rateLimit
# résumé: surfaces couvertes (au moins une méthode True ou 'emulated')
summ = {}
for v, row in out["matrix"].items():
    summ[v] = {s: any(x in (True, "emulated") for x in d.values()) for s, d in row.items()}
out["surface_covered"] = summ
print(json.dumps(out, indent=1))
