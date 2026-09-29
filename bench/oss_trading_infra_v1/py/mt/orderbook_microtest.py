"""dyn4mik3/OrderBook (GitHub HEAD; PyPI 0.1.2 wheel is import-broken) — price-time priority ground truth."""
import json, time, sys
sys.path.insert(0, "/tmp/ob_src")
from orderbook import OrderBook
ob = OrderBook()
def q(side, px, qty, tid, ts): return {'type': 'limit', 'side': side, 'quantity': qty, 'price': px, 'trade_id': tid, 'timestamp': ts}
ob.process_order(q('bid', 100.0, 10, 'A', 1), False, False)
ob.process_order(q('bid', 100.0, 5, 'B', 2), False, False)
tr, rest = ob.process_order(q('ask', 100.0, 12, 'C', 3), False, False)
res = {"expected_FIFO": "C(12) sells against A first (10) then B (2): trades [A 10, B 2], B keeps 3",
       "trades": [(t['party1'][0], t['party2'][0], t['quantity'], t['price']) for t in tr], "remaining_incoming": rest, "best_bid": ob.get_best_bid()}
try: ob.get_volume_at_price('bid', 100.0)
except Exception as e: res["get_volume_at_price"] = f"{type(e).__name__}: {e}"
t0 = time.perf_counter(); n = 50_000
for i in range(n): ob.process_order(q('bid' if i % 2 else 'ask', 100 + (i % 7) * 0.01, 1 + i % 5, f't{i}', i), False, False)
res["orders_per_s"] = int(n / (time.perf_counter() - t0))
res["features_absent"] = "no L2/L3 feed ingestion, no queue-position for a passive order, no latency, no replay clock (matching engine only)"
print(json.dumps(res, default=str, indent=1))
import os; json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "results", "orderbook_microtest.json"), "w"), indent=1, default=str)
