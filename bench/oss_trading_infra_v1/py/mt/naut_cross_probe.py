import sys; sys.path.insert(0,'/home/user/aurumshift-external-research-lab/bench/oss_trading_infra_v1/py/mt'); sys.path.insert(0,'py/mt')
from naut_lib import *
# crossing test: ask update to 99.90 at 9s -> must fill our 100.00 bid
def feed2():
    x=feed(); x.insert(-1, d(BookAction.ADD, SELL, "99.90", "2.0", 9*S+1, True, 5)); return x
import naut_lib
eng = BacktestEngine(BacktestEngineConfig(logging=LoggingConfig(log_level="INFO")))
eng.add_venue(venue=Venue("BINANCE"), oms_type=OmsType.NETTING, account_type=AccountType.CASH, base_currency=None, starting_balances=[Money(1_000_000, USDT), Money(10, BTC)], book_type=BookType.L2_MBP, trade_execution=True)
eng.add_instrument(inst); eng.add_data(feed2()); st=Place(Cfg(instrument_id=iid)); eng.add_strategy(st); eng.run()
print([r[0] for r in st.log_rows])
