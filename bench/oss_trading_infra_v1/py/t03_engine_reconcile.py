"""T03 — fixed order schedule (BUY 100 @ decision bar 100, SELL @ bar 200) with fee 10bp + slippage 5bp, per engine.
Compare fill price / bar and PnL with the analytic result under 'same-bar close' and 'next-bar open' conventions."""
import sys, json, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, __file__.rsplit("/",1)[0])
import numpy as np, pandas as pd
from common import *
eng = sys.argv[1]; df = make_bars(); an = analytic(df); res = dict(engine=eng, analytic=an)

def ident(px):  # which bar/col does px match?
    for col in ("Open", "Close", "High", "Low"):
        for adj in (0, +SLIP, -SLIP):
            m = np.where(np.isclose(df[col].values*(1+adj), px, rtol=1e-9))[0]
            if len(m): return dict(bar=int(m[0]), col=col, slip_adj=adj)
    return None

if eng == "vectorbt":
    import vectorbt as vbt
    size = pd.Series(0.0, index=df.index); size.iloc[BUY_BAR] = QTY; size.iloc[SELL_BAR] = -QTY
    pf = vbt.Portfolio.from_orders(df["Close"], size=size, price=df["Close"], fees=FEE, slippage=SLIP, init_cash=1e9, size_type="amount")
    rec = pf.orders.records_readable
    res["fills"] = [dict(bar=int(df.index.get_loc(r["Index"])) if "Index" in r else None, px=float(r["Price"]), side=r["Side"], fees=float(r["Fees"])) for _, r in rec.iterrows()]
    res["pnl"] = float(pf.total_profit())
elif eng == "vectorbt_next_open":
    import vectorbt as vbt
    size = pd.Series(0.0, index=df.index); size.iloc[BUY_BAR+1] = QTY; size.iloc[SELL_BAR+1] = -QTY
    pf = vbt.Portfolio.from_orders(df["Close"], size=size, price=df["Open"], fees=FEE, slippage=SLIP, init_cash=1e9, size_type="amount")
    rec = pf.orders.records_readable
    res["fills"] = [dict(px=float(r["Price"]), side=r["Side"], fees=float(r["Fees"])) for _, r in rec.iterrows()]
    res["pnl"] = float(pf.total_profit())
elif eng in ("backtesting_next_open", "backtesting_trade_on_close"):
    from backtesting import Backtest, Strategy
    class Sched(Strategy):
        def init(self): self.i = 0
        def next(self):
            i = len(self.data) - 1
            if i == BUY_BAR: self.buy(size=QTY)
            if i == SELL_BAR: self.position.close()
    # backtesting.py has no slippage arg: slippage emulated with 'spread' (added in full to each fill price)
    bt = Backtest(df, Sched, cash=1e9, commission=FEE, spread=SLIP, trade_on_close=(eng.endswith("close")), finalize_trades=True)
    st = bt.run(); tr = st["_trades"]
    res["fills"] = [dict(entry_bar=int(r.EntryBar), exit_bar=int(r.ExitBar), entry_px=float(r.EntryPrice), exit_px=float(r.ExitPrice)) for r in tr.itertuples()]
    res["pnl"] = float(tr["PnL"].sum())
elif eng == "bt":
    import bt as btl
    price = df[["Close"]].rename(columns={"Close": "X"}); cap = 1e6
    w = pd.DataFrame(np.nan, index=df.index, columns=["X"])
    w.iloc[BUY_BAR] = QTY*price["X"].iloc[BUY_BAR]/cap*(1+1e-9); w.iloc[SELL_BAR] = 0.0
    s_ = btl.Strategy("s", [btl.algos.RunOnDate(df.index[BUY_BAR], df.index[SELL_BAR]), btl.algos.SelectAll(),
                            btl.algos.WeighTarget(w), btl.algos.Rebalance()])
    bk = btl.Backtest(s_, price, initial_capital=cap, commissions=lambda q, p: abs(q)*p*FEE, integer_positions=True)
    r = btl.run(bk); tx = bk.strategy.get_transactions()
    res["fills"] = [dict(date=str(i[0]), px=float(v["price"]), qty=float(v["quantity"])) for i, v in tx.iterrows()]
    eq = bk.strategy.values; res["pnl"] = float(eq.iloc[-1] - cap)
    res["note"] = "bt: no slippage parameter; fills at the price-frame value of the decision bar (Close here). Compare with SLIP=0 analytic."
    pb, ps = df.Close.iloc[BUY_BAR], df.Close.iloc[SELL_BAR]
    res["analytic_no_slip"] = dict(pnl=(ps-pb)*QTY - FEE*QTY*(pb+ps))
elif eng == "backtrader":
    import backtrader as bt
    class Sched(bt.Strategy):
        def __init__(self): self.log = []
        def next(self):
            i = len(self) - 1
            if i == BUY_BAR: self.buy(size=QTY)
            if i == SELL_BAR: self.sell(size=QTY)
        def notify_order(self, o):
            if o.status == o.Completed: self.log.append(dict(bar=len(self)-1, px=o.executed.price, comm=o.executed.comm, side="buy" if o.isbuy() else "sell"))
    cb = bt.Cerebro(); cb.broker.setcash(1e9); cb.broker.setcommission(commission=FEE)
    cb.broker.set_slippage_perc(SLIP)
    cb.adddata(bt.feeds.PandasData(dataname=df.rename(columns=str.lower)))
    cb.addstrategy(Sched); st = cb.run()[0]; res["fills"] = st.log; res["pnl"] = cb.broker.getvalue() - 1e9
print(json.dumps(res, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o)))
