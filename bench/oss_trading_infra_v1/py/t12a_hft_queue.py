"""T12a — hftbacktest queue-position / fill-realism known-answer test.
Book: bid 100.0 x10 (queue ahead = 10), ask 100.5 x10. We rest BUY 1 @100.0. Then seller-initiated trades at 100.0: 4, then 7 (cumulative 11 > 10).
Expected (conservative FIFO): no fill after 4; fill after cumulative trades exceed the queue ahead (10) -> after the 7."""
import json, sys, warnings; warnings.filterwarnings("ignore")
import numpy as np
from hftbacktest import (BacktestAsset, HashMapMarketDepthBacktest, event_dtype, DEPTH_EVENT, EXCH_EVENT, LOCAL_EVENT, BUY_EVENT, SELL_EVENT, TRADE_EVENT, GTC, LIMIT, DEPTH_SNAPSHOT_EVENT, NEW, FILLED, CANCELED, EXPIRED, NONE)
def run(model):
    ev = []
    def add(t, e, px, q): ev.append((e | EXCH_EVENT | LOCAL_EVENT, t, t, px, q, 0, 0, 0.0))
    add(1_000, DEPTH_SNAPSHOT_EVENT | BUY_EVENT, 100.0, 10.0); add(1_000, DEPTH_SNAPSHOT_EVENT | SELL_EVENT, 100.5, 10.0)
    add(10_000, TRADE_EVENT | SELL_EVENT, 100.0, 4.0); add(20_000, TRADE_EVENT | SELL_EVENT, 100.0, 7.0); add(30_000, TRADE_EVENT | SELL_EVENT, 100.0, 1.0)
    arr = np.array(ev, dtype=event_dtype)
    a = BacktestAsset().data([arr]).linear_asset(1.0).constant_order_latency(0, 0).no_partial_fill_exchange().trading_value_fee_model(-0.0001, 0.0004).tick_size(0.5).lot_size(0.1)
    a = {"risk_adverse": a.risk_adverse_queue_model, "prob_power2": lambda: a.power_prob_queue_model(2.0), "prob_power3": lambda: a.power_prob_queue_model(3.0), "log_prob": lambda: a.log_prob_queue_model()}[model]()
    hbt = HashMapMarketDepthBacktest([a]); hbt.elapse(2_000)
    hbt.submit_buy_order(0, 1, 100.0, 1.0, GTC, LIMIT, False)
    trace = []
    for t in (5_000, 12_000, 22_000, 40_000):
        hbt.elapse(t - hbt.current_timestamp)
        o = hbt.orders(0).get(1); trace.append(dict(t=t, status=int(o.status), exec_qty=float(o.exec_qty), position=float(hbt.position(0)), fee=float(hbt.state_values(0).fee)))
    hbt.close(); return trace
res = {m: run(m) for m in ("risk_adverse", "prob_power2", "prob_power3", "log_prob")}
import hftbacktest as h; res["status_codes"] = {n: int(getattr(h, n)) for n in ("NONE", "NEW", "EXPIRED", "FILLED", "CANCELED") if hasattr(h, n)}
print(json.dumps(res))
