"""T04 — engine-level causality (prefix invariance): equity on data[:T] must equal equity on full data restricted to [:T].
SMA(10/30) crossover, fee 10bp. A deliberately leaky control (signal uses close 5 bars ahead) must be detected."""
import sys, json, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, __file__.rsplit("/",1)[0])
import numpy as np, pandas as pd
from common import *
eng = sys.argv[1]; T = 400; full = make_bars(n=600, seed=5); part = full.iloc[:T]

def signals(df, leak=False):
    f = df.Close.rolling(10).mean(); s = df.Close.rolling(30).mean(); long = (f > s)
    if leak: long = (df.Close.shift(-5) > df.Close)
    return long.fillna(False)

def run(df, leak=False):
    if eng == "vectorbt":
        import vectorbt as vbt
        lg = signals(df, leak); entries = lg & ~lg.shift(1, fill_value=False); exits = ~lg & lg.shift(1, fill_value=False)
        pf = vbt.Portfolio.from_signals(df.Close, entries=entries, exits=exits, fees=FEE, init_cash=100_000, size=1.0, size_type="percent")
        return pf.value()
    if eng == "vectorbt_native_MA":
        import vectorbt as vbt
        fast = vbt.MA.run(df.Close, 10); slow = vbt.MA.run(df.Close, 30)
        entries = fast.ma_crossed_above(slow); exits = fast.ma_crossed_below(slow)
        pf = vbt.Portfolio.from_signals(df.Close, entries=entries, exits=exits, fees=FEE, init_cash=100_000)
        return pf.value()
    if eng == "backtesting":
        from backtesting import Backtest, Strategy
        from backtesting.lib import crossover
        def SMA(x, n): return pd.Series(x).rolling(n).mean()
        class X(Strategy):
            def init(self): self.f = self.I(SMA, self.data.Close, 10); self.s = self.I(SMA, self.data.Close, 30)
            def next(self):
                if crossover(self.f, self.s): self.buy()
                elif crossover(self.s, self.f): self.position.close()
        st = Backtest(df, X, cash=100_000, commission=FEE, finalize_trades=False).run()
        return st["_equity_curve"]["Equity"]
    if eng == "backtrader":
        import backtrader as bt
        class X(bt.Strategy):
            def __init__(self):
                self.c = bt.indicators.CrossOver(bt.indicators.SMA(period=10), bt.indicators.SMA(period=30)); self.eq = []
            def next(self):
                if self.c > 0: self.buy(size=int(self.broker.getcash()/self.data.close[0]*0.99))
                elif self.c < 0 and self.position: self.close()
                self.eq.append(self.broker.getvalue())
        cb = bt.Cerebro(); cb.broker.setcash(100_000); cb.broker.setcommission(commission=FEE)
        cb.adddata(bt.feeds.PandasData(dataname=df.rename(columns=str.lower))); cb.addstrategy(X); st = cb.run()[0]
        return pd.Series(st.eq, index=df.index[-len(st.eq):])
    if eng == "bt":
        import bt as btl
        px = df[["Close"]].rename(columns={"Close": "X"}); lg = signals(df, leak).astype(float).to_frame("X")
        s_ = btl.Strategy("s", [btl.algos.SelectAll(), btl.algos.WeighTarget(lg), btl.algos.Rebalance()])
        bk = btl.Backtest(s_, px, initial_capital=100_000, commissions=lambda q, p: abs(q)*p*FEE); btl.run(bk)
        return bk.strategy.values
def cmp(leak):
    a = run(full, leak).iloc[:T]; b = run(part, leak)
    a, b = a.align(b, join="inner"); d = (a - b).abs()
    return dict(n=len(d), max_abs_diff=float(d.max()), n_diff=int((d > 1e-6).sum()))
res = dict(engine=eng, causal_strategy=cmp(False))
if eng in ("vectorbt", "bt"): res["leaky_control"] = cmp(True)
print(json.dumps(res))
