"""Lookahead probe. (A) can a strategy read bar t+1 through the engine's normal per-bar API?
(B) if an oracle 'future' array is handed in (as a precomputed indicator), does the engine notice? (It never should;
we only record whether the API structurally exposes the future.)"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, json
from common import *
df = synth(); fut = (df.close.shift(-1) > df.close).fillna(False)   # perfect foresight
res = {}
# backtesting.py
from backtesting import Backtest, Strategy
d = df.rename(columns=str.capitalize).tz_localize(None)
class A(Strategy):
    def init(self): self.f = self.I(lambda: fut.values.astype(float))
    def next(self):
        if self.f[-1] and not self.position: self.buy()
        elif not self.f[-1] and self.position: self.position.close()
st = Backtest(d, A, cash=1e6, commission=0).run()
class P(Strategy):
    def init(self): pass
    def next(self):
        try: self.data.Close[len(self.data)]; self.leak = "leak"
        except Exception as e: self.leak = type(e).__name__
        Backtest_flag.append(self.leak)
Backtest_flag = []
Backtest(d, P, cash=1e6).run()
res["backtesting.py"] = {"B_foresight_return_pct": round(st["Return [%]"], 1), "A_direct_future_index": sorted(set(map(str, Backtest_flag)))[:2]}
# backtrader
import backtrader as bt
flag = []
class BP(bt.Strategy):
    def next(self):
        try: self.data.close[1]; flag.append("leak" if len(self.data) < self.data.buflen() else "last_bar")
        except Exception as e: flag.append(type(e).__name__)
cer = bt.Cerebro(); cer.addstrategy(BP); cer.adddata(bt.feeds.PandasData(dataname=df.tz_localize(None))); cer.run()
res["backtrader"] = {"A_direct_future_index": sorted(set(flag))}
# vectorbt / bt : whole-array API by construction
import vectorbt as vbt
pf = vbt.Portfolio.from_signals(df.close, entries=fut & ~fut.shift(1).fillna(False), exits=~fut & fut.shift(1).fillna(False), price=df.close, init_cash=1e6, fees=0, size_type="amount", size=1000)
res["vectorbt"] = {"B_foresight_final_value": round(float(pf.final_value()), 0), "A": "whole-array API: future is addressable by construction (no per-bar boundary)"}
print(json.dumps(res, indent=1)); json.dump(res, open("../../results/leak_probe.json", "w"), indent=1)
