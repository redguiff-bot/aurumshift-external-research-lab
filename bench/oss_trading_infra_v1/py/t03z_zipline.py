"""T03z — zipline-reloaded: same fixed schedule on XNYS sessions via a csvdir bundle. Observes fill bar/price semantics."""
import os, sys, json, tempfile, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, __file__.rsplit("/",1)[0])
root = tempfile.mkdtemp(); os.environ["ZIPLINE_ROOT"] = root
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo
import exchange_calendars as xcals
from common import *
cal = xcals.get_calendar("XNYS"); sess = cal.sessions_in_range("2023-01-03", "2025-12-31")[:600]
df = make_bars().iloc[:600]; df.index = sess.tz_localize(None)
d = os.path.join(root, "csv", "daily"); os.makedirs(d)
out = df.rename(columns=str.lower); out["dividend"] = 0.0; out["split"] = 1.0; out.index.name = "date"
out.to_csv(os.path.join(d, "XXX.csv"))
from zipline.data.bundles import register, ingest
from zipline.data.bundles.csvdir import csvdir_equities
register("bt", csvdir_equities(["daily"], os.path.join(root, "csv")), calendar_name="XNYS")
ingest("bt", show_progress=False)
from zipline import run_algorithm
from zipline.api import order, symbol, set_slippage, set_commission, record
from zipline.finance.slippage import FixedBasisPointsSlippage
from zipline.finance.commission import PerDollar
fills = []
def initialize(ctx):
    ctx.i = -1; ctx.s = symbol("XXX")
    set_slippage(FixedBasisPointsSlippage(basis_points=5, volume_limit=1.0)); set_commission(PerDollar(cost=FEE))
def handle_data(ctx, data):
    ctx.i += 1
    if ctx.i == BUY_BAR: order(ctx.s, QTY)
    if ctx.i == SELL_BAR: order(ctx.s, -QTY)
def analyze(ctx, perf):
    for dt, txs in perf["transactions"].items():
        for t in txs: fills.append(dict(dt=str(dt.date()), bar=int(df.index.get_loc(pd.Timestamp(dt.date()))), px=float(t["price"]), amount=int(t["amount"]), commission=None))
    fills.append(dict(commissions=float(perf["orders"].explode().dropna().map(lambda o: o["commission"]).sum()) if perf["orders"].explode().dropna().size else 0.0))
    fills.append(dict(ending_value=float(perf["portfolio_value"].iloc[-1])))
run_algorithm(start=df.index[0], end=df.index[-1], initialize=initialize, handle_data=handle_data,
              analyze=analyze, capital_base=1e9, bundle="bt", data_frequency="daily")
tx = [f for f in fills if "px" in f]
res = dict(engine="zipline-reloaded", fills=fills, pnl=fills[-1]["ending_value"]-1e9)
for f in tx: f["match"] = {c: float(df[c].iloc[f["bar"]]) for c in ("Open","Close")}
print(json.dumps(res))
