"""Same SMA20/50 long/flat strategy on 5000 synthetic 1-min bars, fills at NEXT bar open, no fees.
Reference = 20-line numpy loop (used only as an oracle, not a candidate)."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, json, sys
from common import *
df = synth(); S = sig(df)
def oracle():
    pos = S.shift(1).fillna(False).values  # signal known at close t-1 -> position held during bar t, entered at open t
    o, c = df.open.values, df.close.values
    eq, cash_units, entry = 1.0, 0, None; trades = []; prev = False
    pnl = 0.0; equity = 1.0
    for i in range(len(df)):
        if pos[i] and not prev: entry = o[i]
        if (not pos[i]) and prev: trades.append(o[i]/entry-1); equity *= o[i]/entry; entry = None
        prev = pos[i]
    if prev: trades.append(c[-1]/entry-1); equity *= c[-1]/entry   # close at end
    return {"n_trades": len(trades), "final_equity": round(equity,6), "pnl_1000_units": None}
res = {"oracle": oracle()}
def run_bt_py():
    from backtesting import Backtest, Strategy
    d = df.rename(columns=str.capitalize).tz_localize(None)
    class St(Strategy):
        def init(self): self.s = self.I(lambda: S.values.astype(float), name="sig")
        def next(self):
            if self.s[-1] and not self.position: self.buy()
            elif not self.s[-1] and self.position: self.position.close()
    st = Backtest(d, St, cash=1_000_000, commission=0, trade_on_close=False, finalize_trades=True).run()
    return {"n_trades": int(st["# Trades"]), "final_equity": round(st["Equity Final [$]"]/1e6, 6)}
def run_backtrader():
    import backtrader as bt
    class St(bt.Strategy):
        def __init__(s): s.sm = bt.ind.SMA(period=20); s.sl = bt.ind.SMA(period=50)
        def next(s):
            if s.sm[0] > s.sl[0] and not s.position: s.buy()
            elif s.sm[0] <= s.sl[0] and s.position: s.close()
    cer = bt.Cerebro(); cer.broker.setcash(1e6); cer.broker.setcommission(0); cer.addstrategy(St)
    d = bt.feeds.PandasData(dataname=df.tz_localize(None)); cer.adddata(d)
    cer.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cer.addsizer(bt.sizers.FixedSize, stake=1000)
    cer.run(); ta = cer.runstrats[0][0].analyzers.ta.get_analysis()
    tot = ta.get("total", {})
    return {"n_trades": int(tot.get("closed", 0)) + int(tot.get("open", 0)), "final_value": cer.broker.getvalue(), "note": "fixed stake 1000 units; SMA warm-up differs (min period)"}
def run_vbt():
    import vectorbt as vbt
    e = S.shift(1).fillna(False)
    pf = vbt.Portfolio.from_signals(df.close, entries=S & ~S.shift(1).fillna(False), exits=~S & S.shift(1).fillna(False), price=df.open.shift(-1), init_cash=1e6, fees=0, size_type="amount", size=1000, freq="1min")
    # entries signalled at close t executed at open t+1
    return {"n_trades": int(pf.trades.count()), "final_value": float(pf.final_value())}
def run_bt_lib():
    import bt
    w = S.shift(1).fillna(False).astype(float).to_frame("X")   # weight decided at t-1, applied on close-to-close return
    st = bt.Strategy("s", [bt.algos.RunDaily(), bt.algos.SelectAll(), bt.algos.WeighTarget(w), bt.algos.Rebalance()])
    r = bt.run(bt.Backtest(st, df[["close"]].rename(columns={"close":"X"}), integer_positions=False, progress_bar=False))
    return {"total_return": float(r.stats.loc["total_return"].iloc[0]), "note": "runs; close-to-close rebalance, no next-open fill; result not comparable to oracle"}
def run_qstrader():
    import qstrader; return {"version": getattr(qstrader, "__version__", "?"), "note": "import ok; needs own DataHandler/SimulationEngine + daily calendar; not run"}
for name, fn in [("backtesting.py", run_bt_py), ("backtrader", run_backtrader), ("vectorbt", run_vbt), ("bt", run_bt_lib), ("qstrader", run_qstrader)]:
    try:
        a, ta = timed(fn); b, tb = timed(fn)
        res[name] = {**a, "runtime_s": ta, "deterministic_2runs": a == b}
    except Exception as ex:
        res[name] = {"error": f"{type(ex).__name__}: {str(ex)[:200]}"}
print(json.dumps(res, indent=1, default=str))
json.dump(res, open("../../results/bt_engines.json", "w"), indent=1, default=str)
