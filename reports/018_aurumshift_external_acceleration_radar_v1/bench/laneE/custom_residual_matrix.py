"""Lane E — matrice « code custom supprimé » : 12 surfaces C0 × 3 venues, à partir de exchange.has (ccxt) +
résultats mesurés OKX (okx_rest_l2.json / okx_ws_l2.json). Statut par cellule :
  UNIFIED   : méthode unifiée True, mesurée OK sur OKX (ou non mesurable ici → UNIFIED_UNMEASURED pour binance/bybit)
  EMULATED  : 'emulated' dans has
  PARTIAL   : méthode présente mais champ PIT/semantique perdu (mesuré) → wrapper custom requis
  MISSING   : non supporté (None/False) → appel natif custom
Usage : python custom_residual_matrix.py  (lit ccxt_has_matrix.json) → custom_residual_matrix.csv + résumé stdout"""
import json, csv
H = json.load(open("ccxt_has_matrix.json"))["matrix"]
VEN = {"binance(spot+usdm)": ("binance", "binanceusdm"), "okx": ("okx", "okx"), "bybit": ("bybit", "bybit")}
# surface -> (venue_kind, méthode, perte PIT mesurée/lue sur le code)
SURF = [
 ("bars_1m",            "spot", "fetchOHLCV",              "barre en formation renvoyée ; flag natif confirm (OKX) / x (Binance kline WS) non exposé"),
 ("bbo",                "spot", "watchBidsAsks",           None),
 ("depth_snapshot",     "spot", "fetchOrderBook",          {"okx": "REST : nonce=None alors que OKX renvoie seqId (mesuré) ; nb d'ordres (4e champ) perdu", "bybit": "REST : nonce non renseigné (u/seq Bybit ignorés, lecture code)"}),
 ("depth_stream",       "spot", "watchOrderBook",          None),
 ("trades",             "spot", "watchTrades",             None),
 ("funding_current",    "swap", "fetchFundingRate",        {"okx": "timestamp=None (ts natif OKX seulement dans info) — Binance(time)/Bybit(ts) le remplissent (lecture code)"}),
 ("funding_history",    "swap", "fetchFundingRateHistory", None),
 ("oi_current",         "swap", "fetchOpenInterest",       "openInterestAmount en contrats ; contractSize hétérogène (OKX 0.01 BTC / 1000 DOGE mesuré) ; champ baseVolume déprécié → normalisation d'unités custom"),
 ("oi_history",         "swap", "fetchOpenInterestHistory", None),
 ("mark_index_basis",   "swap", "fetchMarkPrice",          {"okx": "indexPrice=None dans fetchMarkPrice → fetchIndexOHLCV ou appel natif", "bybit": "fetchMarkPrice absent → fetchTicker (markPrice/indexPrice) ou fetchMark/IndexOHLCV"}),
 ("liquidations",       "swap", "watchLiquidations",       None),
 ("receipt_timestamp",  "any",  None,                       "aucune méthode : ccxt n'ajoute jamais d'horodatage de réception"),
]
rows, tally = [], {}
for s, kind, m, loss in SURF:
    row = {"surface": s, "method": m or "-"}
    for vn, (spot_id, swap_id) in VEN.items():
        if m is None:
            st = "MISSING"
        else:
            v = H[swap_id if kind == "swap" else spot_id]
            flat = {k: x for d in v.values() for k, x in d.items()}
            h = flat.get(m)
            if h is True: st = "UNIFIED"
            elif h == "emulated": st = "EMULATED"
            else: st = "MISSING"
            # fallback REST pour liquidations / mark
            if s == "liquidations" and st == "MISSING": st = "MISSING"
            l = loss.get(vn.split("(")[0]) if isinstance(loss, dict) else loss
            if l and st in ("UNIFIED", "EMULATED"): st = "PARTIAL"
        if vn != "okx" and st in ("UNIFIED", "EMULATED"): st += "_UNMEASURED"
        row[vn] = st
        tally[st.split("_")[0]] = tally.get(st.split("_")[0], 0) + 1
    row["pit_loss_or_note"] = (json.dumps(loss, ensure_ascii=False) if isinstance(loss, dict) else loss) or ""
    rows.append(row)
with open("custom_residual_matrix.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
for r in rows: print(r)
print("TALLY (36 cellules) :", tally)
