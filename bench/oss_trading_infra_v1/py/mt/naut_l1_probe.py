import sys; sys.path.insert(0,'/home/user/aurumshift-external-research-lab/bench/oss_trading_infra_v1/py/mt'); sys.path.insert(0,'py/mt')
from naut_lib import *
def q(bid,ask,t): return QuoteTick(iid, Price.from_str(bid), Price.from_str(ask), inst.make_qty(10.0), inst.make_qty(10.0), t, t)
def run(trades, te=True):
    x=[q("100.00","100.50",1*S)]+trades
    eng = BacktestEngine(BacktestEngineConfig(logging=LoggingConfig(log_level="ERROR", bypass_logging=True)))
    eng.add_venue(venue=Venue("BINANCE"), oms_type=OmsType.NETTING, account_type=AccountType.CASH, base_currency=None, starting_balances=[Money(1_000_000, USDT), Money(10, BTC)], book_type=BookType.L1_MBP, trade_execution=te)
    eng.add_instrument(inst); eng.add_data(x); st=Place(Cfg(instrument_id=iid)); eng.add_strategy(st); eng.run()
    return [(r[0], r[1]/S) for r in st.log_rows if r[0] in ("OrderFilled",)]
print("L1 trade@100.00 x3", run([tr("100.00","4.0",6*S,1),tr("100.00","6.0",8*S,2),tr("100.00","6.0",9*S,3)]))
print("L1 trade through 99.90", run([tr("100.00","4.0",6*S,1),tr("99.90","1.0",8*S,2)]))
print("L1 through, trade_execution off", run([tr("100.00","4.0",6*S,1),tr("99.90","1.0",8*S,2)], False))
