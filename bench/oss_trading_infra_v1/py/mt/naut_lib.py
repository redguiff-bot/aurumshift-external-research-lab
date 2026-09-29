"""NautilusTrader microtest: L2 book delta replay + resting limit order, ground truth as in hft_microtest.
bid 100.0 x10 / ask 100.5 x10 ; strategy buys 1 @ 100.0 at t=5s ; sell trades 4@6s, 6@8s, 6@9s ; depth 10->4 at 7s.
Also: determinism (hash of order/fill events across 2 runs), throughput on 1M synthetic quote ticks, import time."""
import time, json, hashlib, sys
t_imp = time.perf_counter()
import pandas as pd, numpy as np
from decimal import Decimal
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig, StrategyConfig
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.identifiers import Venue, InstrumentId
from nautilus_trader.model.enums import OmsType, AccountType, BookType, BookAction, OrderSide, AggressorSide, TimeInForce
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.model.currencies import USDT, BTC
from nautilus_trader.model.data import OrderBookDelta, TradeTick, QuoteTick, BookOrder
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.core.rust.model import RecordFlag
IMPORT_S = round(time.perf_counter() - t_imp, 2)
S = 1_000_000_000
inst = TestInstrumentProvider.btcusdt_binance()
iid = inst.id
def d(action, side, px, sz, t, last=True, oid=0):
    return OrderBookDelta(iid, action, BookOrder(side, Price.from_str(px), inst.make_qty(float(sz)), oid), RecordFlag.F_LAST if last else 0, 0, t, t)
def tr(px, sz, t, n): return TradeTick(iid, Price.from_str(px), inst.make_qty(float(sz)), AggressorSide.SELLER, TradeId(str(n)), t, t)
BUY, SELL = OrderSide.BUY, OrderSide.SELL
def feed(through=False):
    x = [OrderBookDelta.clear(iid, 0, 1*S, 1*S),
         d(BookAction.ADD, BUY, "100.00", "10.0", 1*S, False, 1), d(BookAction.ADD, SELL, "100.50", "10.0", 1*S, True, 2),
         tr("100.00", "4.0", 6*S, 1),
         *( [tr("99.90", "1.0", 9*S//1 + 2, 9)] if through else [] ),
         d(BookAction.UPDATE, BUY, "100.00", "4.0", 7*S, True, 1),
         tr("100.00", "6.0", 8*S, 2), tr("100.00", "6.0", 9*S, 3),
         d(BookAction.UPDATE, SELL, "100.50", "10.0", 9*S+1, True, 2)]
    return x
class Cfg(StrategyConfig, frozen=True):
    instrument_id: InstrumentId
class Place(Strategy):
    def __init__(self, c):
        super().__init__(c); self.placed = False; self.log_rows = []
    def on_start(self):
        self.subscribe_order_book_deltas(self.config.instrument_id, book_type=BookType.L2_MBP)
        self.subscribe_trade_ticks(self.config.instrument_id)
    def on_order_book_deltas(self, deltas):
        if not self.placed and self.clock.timestamp_ns() >= 5*S:
            o = self.order_factory.limit(self.config.instrument_id, BUY, inst.make_qty(1.0), Price.from_str("100.00"), time_in_force=TimeInForce.GTC)
            self.submit_order(o); self.placed = True
    def on_trade_tick(self, t):
        if not self.placed and self.clock.timestamp_ns() >= 5*S:
            o = self.order_factory.limit(self.config.instrument_id, BUY, inst.make_qty(1.0), Price.from_str("100.00"), time_in_force=TimeInForce.GTC)
            self.submit_order(o); self.placed = True
    def on_event(self, e):
        self.log_rows.append((type(e).__name__, getattr(e, "ts_event", 0), str(getattr(e, "last_px", "")), str(getattr(e, "last_qty", ""))))
def run(prob_touch=None, through=False, latency_ns=None, trade_execution=True):
    eng = BacktestEngine(BacktestEngineConfig(logging=LoggingConfig(log_level="ERROR", bypass_logging=True)))
    kw = dict(venue=Venue("BINANCE"), oms_type=OmsType.NETTING, account_type=AccountType.CASH, base_currency=None,
              starting_balances=[Money(1_000_000, USDT), Money(10, BTC)], book_type=BookType.L2_MBP, trade_execution=trade_execution)
    if prob_touch is not None:
        from nautilus_trader.backtest.models import FillModel
        kw["fill_model"] = FillModel(prob_fill_on_limit=prob_touch, prob_slippage=0.0, random_seed=42)
    if latency_ns is not None:
        from nautilus_trader.backtest.models import LatencyModel
        kw["latency_model"] = LatencyModel(base_latency_nanos=latency_ns)
    eng.add_venue(**kw)
    eng.add_instrument(inst); eng.add_data(feed(through))
    st = Place(Cfg(instrument_id=iid)); eng.add_strategy(st)
    eng.run()
    fills = [r for r in st.log_rows if r[0] == "OrderFilled"]
    out = {"events": [r[0] for r in st.log_rows], "fills": [(r[1]/S, r[2], r[3]) for r in fills]}
    out["hash"] = hashlib.sha256(json.dumps(st.log_rows, default=str).encode()).hexdigest()[:12]
    eng.dispose(); return out
