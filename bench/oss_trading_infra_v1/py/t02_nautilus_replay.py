"""T02 — nautilus_trader BacktestEngine: determinism (2 runs, 1 fresh process each), fill semantics, fee model.
Synthetic quote-tick random walk (seeded). Strategy: on every 50th quote alternate market BUY/SELL 1 unit."""
import sys, json, time, hashlib, random
from decimal import Decimal
import pandas as pd
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import MakerTakerFeeModel, FillModel
from nautilus_trader.config import BacktestEngineConfig, StrategyConfig, LoggingConfig
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.trading.strategy import Strategy

class S(Strategy):
    def __init__(self, inst, every=50):
        super().__init__(StrategyConfig(strategy_id="S-1")); self.inst = inst; self.n = 0; self.side = OrderSide.BUY
        self.fills = []; self.submit_ts = {}
    def on_start(self): self.subscribe_quote_ticks(self.inst.id)
    def on_quote_tick(self, q):
        self.n += 1
        if self.n % 50 == 0:
            o = self.order_factory.market(self.inst.id, self.side, self.inst.make_qty(1))
            self.submit_ts[str(o.client_order_id)] = (q.ts_event, float(q.bid_price), float(q.ask_price))
            self.submit_order(o); self.side = OrderSide.SELL if self.side == OrderSide.BUY else OrderSide.BUY
    def on_order_filled(self, e):
        self.fills.append((str(e.client_order_id), e.ts_event, float(e.last_px), float(e.last_qty), float(e.commission.as_double()), str(e.order_side)))

def run(N, seed, fee_model, latency=None):
    rng = random.Random(seed)
    eng = BacktestEngine(config=BacktestEngineConfig(trader_id=TraderId("BT-001"), logging=LoggingConfig(bypass_logging=True)))
    venue = Venue("BINANCE")
    eng.add_venue(venue=venue, oms_type=OmsType.NETTING, account_type=AccountType.CASH, base_currency=None,
                  starting_balances=[Money(1_000_000, USDT)], fee_model=fee_model, **({'latency_model': latency} if latency else {}), fill_model=FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0, random_seed=1))
    inst = TestInstrumentProvider.ethusdt_binance(); eng.add_instrument(inst)
    px = 2000.0; ticks = []; t0 = pd.Timestamp("2025-01-02", tz="UTC").value
    for i in range(N):
        px *= 1 + rng.gauss(0, 0.0002); spr = 0.02
        ticks.append(QuoteTick(inst.id, Price(round(px - spr/2, 2), 2), Price(round(px + spr/2, 2), 2),
                               Quantity(10, 5), Quantity(10, 5), t0 + i*1_000_000_000, t0 + i*1_000_000_000))
    eng.add_data(ticks)
    s = S(inst); eng.add_strategy(s)
    t = time.perf_counter(); eng.run(); dt = time.perf_counter() - t
    out = dict(fills=s.fills, submit=s.submit_ts, seconds=dt)
    eng.dispose()
    return out

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000
    lat_ms = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    lat = None
    if lat_ms:
        from nautilus_trader.backtest.models import LatencyModel
        lat = LatencyModel(base_latency_nanos=lat_ms*1_000_000)
    r = run(N, 11, MakerTakerFeeModel(), lat)
    h = hashlib.sha256(json.dumps(r["fills"]).encode()).hexdigest()[:16]
    # fill semantics: is fill ts == submit quote ts? fill price == ask/bid at submit quote?
    same_ts = 0; px_ok = 0
    for f in r["fills"]:
        ts, bid, ask = r["submit"][f[0]]
        same_ts += (f[1] == ts); px_ok += (f[2] == (ask if f[5] in ("1","BUY","OrderSide.BUY") else bid))
    commission = sum(f[4] for f in r["fills"])
    print(json.dumps(dict(n_quotes=N, n_fills=len(r["fills"]), fills_digest=h, seconds=r["seconds"], quotes_per_s=round(N/r["seconds"]),
        fills_at_submit_ts=same_ts, fill_px_equals_touch_at_submit=px_ok, total_commission=commission,
        first_fills=r["fills"][:3], latency_ms=lat_ms, mean_fill_delay_ms=sum((f[1]-r['submit'][f[0]][0]) for f in r['fills'])/max(1,len(r['fills']))/1e6)))
