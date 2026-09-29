"""T01 — L2 order-book correctness vs a naive reference, on a seeded random delta stream.
Candidates: nautilus_trader OrderBook (Rust), hftbacktest depth (Rust/numba), sortedcontainers reference.
Metric: top-of-book + full-depth checksum equality after every N events; throughput; run-to-run determinism."""
import sys, json, time, hashlib, random
which = sys.argv[1]
SEED, N, TICK = 7, 200_000, 0.5
rng = random.Random(SEED)
mid0 = 20000.0
# stream: (side, price, qty) ; qty==0 -> delete level. Keeps book uncrossed by construction (bids<mid<asks).
stream = []
for i in range(N):
    side = rng.choice("BA"); off = rng.randint(1, 60)
    px = mid0 - off*TICK if side == "B" else mid0 + off*TICK
    q = 0.0 if rng.random() < 0.35 else round(rng.uniform(0.001, 5), 3)
    stream.append((side, px, q))

def ref_final():
    B, A = {}, {}
    for s, p, q in stream:
        d = B if s == "B" else A
        if q == 0: d.pop(p, None)
        else: d[p] = q
    return B, A
def digest(B, A):
    h = hashlib.sha256()
    for p in sorted(B, reverse=True): h.update(f"B{p:.1f}:{B[p]:.3f};".encode())
    for p in sorted(A): h.update(f"A{p:.1f}:{A[p]:.3f};".encode())
    return h.hexdigest()[:16]
RB, RA = ref_final(); ref_digest = digest(RB, RA)
res = dict(candidate=which, n_events=N, ref_digest=ref_digest, ref_levels=[len(RB), len(RA)])

if which == "sortedcontainers":
    from sortedcontainers import SortedDict
    t = time.perf_counter(); B = SortedDict(); A = SortedDict()
    for s, p, q in stream:
        d = B if s == "B" else A
        if q == 0: d.pop(p, None)
        else: d[p] = q
    dt = time.perf_counter() - t
    res.update(digest=digest(dict(B), dict(A)), seconds=dt)

elif which == "nautilus":
    from nautilus_trader.model.book import OrderBook
    from nautilus_trader.model.data import OrderBookDelta, BookOrder
    from nautilus_trader.model.enums import BookType, BookAction, OrderSide
    from nautilus_trader.model.identifiers import InstrumentId
    from nautilus_trader.model.objects import Price, Quantity
    iid = InstrumentId.from_str("BTCUSDT.TEST")
    book = OrderBook(iid, BookType.L2_MBP)
    t = time.perf_counter(); seq = 0
    live = {"B": {}, "A": {}}
    for s, p, q in stream:
        seq += 1
        side = OrderSide.BUY if s == "B" else OrderSide.SELL
        if q == 0:
            if p not in live[s]: continue
            act = BookAction.DELETE; del live[s][p]
        else:
            act = BookAction.UPDATE if p in live[s] else BookAction.ADD; live[s][p] = q
        o = BookOrder(side, Price(p, 1), Quantity(q if q else live[s].get(p, 1.0) or 1.0, 3), int(p*10))
        book.apply_delta(OrderBookDelta(iid, act, o, 0, seq, seq, seq))
    dt = time.perf_counter() - t
    B = {float(l.price): float(l.size()) for l in book.bids()}
    A = {float(l.price): float(l.size()) for l in book.asks()}
    res.update(digest=digest(B, A), seconds=dt, integrity=str(book.check_integrity()) if callable(book.check_integrity) else None,
               best_bid=float(book.best_bid_price()), best_ask=float(book.best_ask_price()))

elif which == "hftbacktest":
    import numpy as np
    from hftbacktest import (BacktestAsset, HashMapMarketDepthBacktest, event_dtype,
                             DEPTH_EVENT, EXCH_EVENT, LOCAL_EVENT, BUY_EVENT, SELL_EVENT)
    ev = np.zeros(N, dtype=event_dtype)
    for i, (s, p, q) in enumerate(stream):
        ev[i] = (DEPTH_EVENT | EXCH_EVENT | LOCAL_EVENT | (BUY_EVENT if s == "B" else SELL_EVENT),
                 i+1, i+1, p, q, 0, 0, 0.0)
    asset = (BacktestAsset().data([ev]).linear_asset(1.0).constant_order_latency(1, 1)
             .risk_adverse_queue_model().no_partial_fill_exchange().trading_value_fee_model(0.0, 0.0)
             .tick_size(TICK).lot_size(0.001))
    hbt = HashMapMarketDepthBacktest([asset])
    t = time.perf_counter()
    rc = hbt.elapse(N + 10)
    dt = time.perf_counter() - t
    res["elapse_rc"] = rc
    d = hbt.depth(0)
    B = {}; A = {}
    lo = int(round((mid0-70*TICK)/TICK)); hi = int(round((mid0+70*TICK)/TICK))
    for tk in range(lo, hi+1):
        px = round(tk*TICK, 1)
        bq = d.bid_qty_at_tick(tk); aq = d.ask_qty_at_tick(tk)
        if bq > 0: B[px] = round(bq, 3)
        if aq > 0: A[px] = round(aq, 3)
    res.update(digest=digest(B, A), seconds=dt, best_bid=d.best_bid, best_ask=d.best_ask)
    hbt.close()

res["match_reference"] = res.get("digest") == ref_digest
res["events_per_s"] = round(N / res["seconds"]) if res.get("seconds") else None
print(json.dumps(res))
