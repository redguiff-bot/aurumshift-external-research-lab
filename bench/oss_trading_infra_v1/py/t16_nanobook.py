"""T16 — nanobook (Rust LOB, python bindings, 0.18.1): price-time-priority matching vs a naive FIFO reference on a seeded random limit-order stream (GTC), plus event-log replay determinism."""
import json, random, time, collections, warnings; warnings.filterwarnings("ignore")
import nanobook
rng = random.Random(5); N = 20000; ops = []
for i in range(N): ops.append((rng.choice(["buy", "sell"]), 10000 + rng.randint(-15, 15), rng.randint(1, 20)))
# reference
bids = collections.defaultdict(collections.deque); asks = collections.defaultdict(collections.deque); rtrades = []
for oid, (s, p, q) in enumerate(ops):
    book, opp = (bids, asks) if s == "buy" else (asks, bids)
    while q > 0 and opp:
        bp = (min(opp) if s == "buy" else max(opp))
        if (s == "buy" and bp > p) or (s == "sell" and bp < p): break
        dq = opp[bp]
        while q > 0 and dq:
            r = dq[0]; f = min(q, r[1]); rtrades.append((bp, f)); q -= f; r[1] -= f
            if r[1] == 0: dq.popleft()
        if not dq: del opp[bp]
    if q > 0: book[p].append([oid, q])
ref_bb = max(bids) if bids else None; ref_ba = min(asks) if asks else None
ex = nanobook.Exchange(); t = time.perf_counter()
for s, p, q in ops: ex.submit_limit(s, p, q, "gtc")
dt = time.perf_counter() - t
tr = ex.trades(); nt = [(x.price, x.quantity) for x in tr]
bb, ba = ex.best_bid_ask()
res = dict(n_orders=N, orders_per_s=round(N/dt), n_trades_nanobook=len(nt), n_trades_ref=len(rtrades), trades_equal=nt == rtrades, best_bid=str(bb), best_ask=str(ba), ref_best_bid=ref_bb, ref_best_ask=ref_ba)
try:
    ev = ex.events(); ex2 = nanobook.Exchange.replay(ev); res["replay_trades_equal"] = [(x.price, x.quantity) for x in ex2.trades()] == nt
except Exception as e: res["replay_error"] = repr(e)[:200]
print(json.dumps(res, default=str))
