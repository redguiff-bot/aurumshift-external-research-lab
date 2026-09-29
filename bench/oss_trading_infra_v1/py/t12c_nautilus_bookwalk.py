"""T12c — nautilus_trader L2 book replay: does a market order larger than top-of-book size walk the book (multiple fills at increasing prices)?
Ask side: 100.50 x1, 101.00 x1, 101.50 x5. Market BUY 3 => expected fills 1@100.50, 1@101.00, 1@101.50 (avg 101.00)."""
import json, warnings; warnings.filterwarnings("ignore")
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig, StrategyConfig, LoggingConfig
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.data import OrderBookDelta, OrderBookDeltas, BookOrder
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide, BookType, BookAction, RecordFlag
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.trading.strategy import Strategy
inst = TestInstrumentProvider.ethusdt_binance()
class S(Strategy):
    def __init__(self): super().__init__(StrategyConfig(strategy_id="S-1")); self.fills = []; self.sent = False; self.events = []; self.n = 0
    def on_start(self): self.subscribe_order_book_deltas(inst.id, book_type=BookType.L2_MBP)
    def on_order_book_deltas(self, d):
        self.n += 1
        if self.n == 2 and not self.sent:
            self.sent = True; self.submit_order(self.order_factory.market(inst.id, OrderSide.BUY, inst.make_qty(3)))
    def on_event(self, e): self.events.append(type(e).__name__ + (":" + str(getattr(e, "reason", "")) if type(e).__name__ == "OrderRejected" else ""))
    def on_order_filled(self, e): self.fills.append((float(e.last_px), float(e.last_qty)))
eng = BacktestEngine(config=BacktestEngineConfig(trader_id=TraderId("BT-001"), logging=LoggingConfig(bypass_logging=True)))
eng.add_venue(venue=Venue("BINANCE"), oms_type=OmsType.NETTING, account_type=AccountType.CASH, base_currency=None, starting_balances=[Money(1_000_000, USDT)], book_type=BookType.L2_MBP)
eng.add_instrument(inst)
levels = [(OrderSide.BUY, 100.0, 1), (OrderSide.BUY, 99.5, 1), (OrderSide.SELL, 100.5, 1), (OrderSide.SELL, 101.0, 1), (OrderSide.SELL, 101.5, 5)]
ds = [OrderBookDelta.clear(inst.id, 0, 1_000, 1_000)]
for i, (sd, px, q) in enumerate(levels):
    last = RecordFlag.F_LAST if i == len(levels)-1 else 0
    ds.append(OrderBookDelta(inst.id, BookAction.ADD, BookOrder(sd, Price(px, 2), Quantity(q, 5), int(px*100)), last, i+1, 1_000, 1_000))
ds.append(OrderBookDelta(inst.id, BookAction.UPDATE, BookOrder(OrderSide.BUY, Price(99.5, 2), Quantity(2, 5), int(99.5*100)), RecordFlag.F_LAST, 99, 2_000, 2_000))
snap = OrderBookDeltas(inst.id, ds[:-1]); upd = OrderBookDeltas(inst.id, ds[-1:])
eng.add_data([snap, upd]); s = S(); eng.add_strategy(s); eng.run()
res = dict(events=s.events, fills=s.fills, n_fills=len(s.fills), total_qty=sum(q for _, q in s.fills), avg_px=(sum(p*q for p, q in s.fills)/sum(q for _, q in s.fills)) if s.fills else None, expected_fills=[[100.5, 1.0], [101.0, 1.0], [101.5, 1.0]], expected_avg=101.0)
print(json.dumps(res))
