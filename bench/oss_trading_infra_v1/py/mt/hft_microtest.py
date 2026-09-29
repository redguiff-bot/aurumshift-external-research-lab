"""hftbacktest 2.4.4 microtest: (1) queue-model fill semantics on a hand-built L2 feed with known ground truth,
(2) order/exchange latency (order arriving after the trade must not fill), (3) determinism, (4) throughput on 2M synthetic events."""
import json, time, hashlib, numpy as np
from numba import njit
from hftbacktest import (BacktestAsset, HashMapMarketDepthBacktest, DEPTH_EVENT, TRADE_EVENT, BUY_EVENT, SELL_EVENT,
                         EXCH_EVENT, LOCAL_EVENT, GTC, LIMIT, event_dtype)
S = 1_000_000_000
def ev(flags, t, px, qty): return (flags | EXCH_EVENT | LOCAL_EVENT, t, t, px, qty, 0, 0, 0.0)
BID, ASK = DEPTH_EVENT | BUY_EVENT, DEPTH_EVENT | SELL_EVENT
def feed(t_trade_offset=0):
    rows = [ev(BID, 1*S, 100.0, 10.0), ev(ASK, 1*S, 100.5, 10.0),
            ev(TRADE_EVENT | SELL_EVENT, 6*S + t_trade_offset, 100.0, 4.0),   # aggressive sell 4 @ bid
            ev(BID, 7*S, 100.0, 4.0),                                          # visible qty at bid falls 10->4
            ev(TRADE_EVENT | SELL_EVENT, 8*S, 100.0, 6.0),
            ev(TRADE_EVENT | SELL_EVENT, 9*S, 100.0, 6.0),
            ev(ASK, 9*S+1, 100.5, 10.0)]
    return np.array(rows, dtype=event_dtype)
@njit
def strat(hbt, place_ns):
    hbt.elapse(place_ns)
    hbt.submit_buy_order(0, 1, 100.0, 1.0, GTC, LIMIT, False)
    fill_t = -1
    while hbt.elapse(100_000_000) == 0:
        if fill_t < 0 and hbt.position(0) > 0:
            fill_t = hbt.current_timestamp
    return fill_t
def run(data, qm, order_lat_ns=0, feed_lat=0, place_ns=5*S, fee=None):
    a = BacktestAsset().data([data]).linear_asset(1.0).constant_order_latency(order_lat_ns, order_lat_ns).tick_size(0.5).lot_size(1.0)
    a = {"risk_adverse": a.risk_adverse_queue_model, "prob_power2": lambda: a.power_prob_queue_model(2.0),
         "prob_log": a.log_prob_queue_model, "prob_power3": a.power_prob_queue_model3 if False else (lambda: a.power_prob_queue_model(3.0))}[qm]()
    a = a.no_partial_fill_exchange()
    if fee: a = a.trading_value_fee_model(*fee)
    hbt = HashMapMarketDepthBacktest([a])
    ft = strat(hbt, place_ns)
    pos = hbt.position(0); sv = hbt.state_values(0)
    r = {"fill_t_s": None if ft < 0 else round(ft / S, 3), "position": pos, "fee": sv.fee, "balance": round(sv.balance, 6)}
    hbt.close(); return r
res = {"version": __import__("hftbacktest").__version__ if hasattr(__import__("hftbacktest"), "__version__") else "2.4.4"}
d = feed()
res["ground_truth"] = ("bid 100.0 has 10 ahead when we join (t=5s). trades at 100.0: 4@6s, 6@8s, 6@9s; depth falls to 4 at 7s. "
   "Sell-side volume at our price through 9s = 16 >= 10 ahead: FIFO says filled by 9s (after 8s: 4+6=10 ahead consumed -> 8s or 9s edge). "
   "risk_adverse: ahead only reduces by depth change (10->4 at 7s => 4 ahead) then trades 6@8s clear it => fill expected 8s.")
res["queue_models"] = {qm: run(d, qm) for qm in ("risk_adverse", "prob_power2", "prob_log", "prob_power3")}
res["order_latency"] = {
  "lat_0": run(d, "risk_adverse", 0),
  "lat_1.5s_(entry_at_6.5s_after_4@6s_trade)": run(d, "risk_adverse", int(1.5*S)),
  "lat_4s_(entry_at_9s)": run(d, "risk_adverse", 4*S)}
res["fee_model_value_maker_-0.01%_taker_0.05%"] = run(d, "risk_adverse", 0, fee=(-0.0001, 0.0005))
h0 = [json.dumps(run(d, "prob_power2"), sort_keys=True) for _ in range(3)]
res["determinism_3_runs_identical"] = len(set(h0)) == 1
# throughput: 2M events random-walk L2 + trades
rng = np.random.default_rng(1)
n = 1_000_000; t = np.sort(rng.integers(1*S, 3600*S, 2*n)); rows = []
mid = 100.0; arr = np.zeros(2*n, dtype=event_dtype)
px = np.round(100 + np.cumsum(rng.choice([-0.5, 0, 0.5], 2*n, p=[.2, .6, .2])), 1)
kind = rng.integers(0, 3, 2*n)
arr["ev"] = np.where(kind == 0, BID, np.where(kind == 1, ASK, TRADE_EVENT | SELL_EVENT)) | EXCH_EVENT | LOCAL_EVENT
arr["exch_ts"] = t; arr["local_ts"] = t; arr["qty"] = rng.integers(1, 20, 2*n).astype(float)
arr["px"] = np.where(kind == 0, px - 0.5, np.where(kind == 1, px + 0.5, px))
@njit
def spin(hbt):
    while hbt.elapse(1_000_000_000) == 0: pass
a = BacktestAsset().data([arr]).linear_asset(1.0).constant_order_latency(1_000_000, 1_000_000).risk_adverse_queue_model().no_partial_fill_exchange().tick_size(0.5).lot_size(1.0)
hbt = HashMapMarketDepthBacktest([a]); spin(hbt)  # warm (includes numba compile)
hbt.close()
t0 = time.perf_counter(); hbt = HashMapMarketDepthBacktest([a]); spin(hbt); dt = time.perf_counter() - t0; hbt.close()
res["throughput_2M_events"] = {"seconds_warm": round(dt, 3), "events_per_s": int(2*n/dt)}
print(json.dumps(res, indent=1))
from common import save; save("hft_microtest.json", res)
