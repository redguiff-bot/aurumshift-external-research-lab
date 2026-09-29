"""T12b — zipline-reloaded VolumeShareSlippage: liquidity-limited partial fills + quadratic impact, vs hand computation.
Order 500 shares at decision bar 100; volume_limit=0.025, price_impact=0.1.
NOTE: expected close is rounded to 3 decimals because the bcolz/csvdir daily bundle stores prices as integers*1e-3 (OBSERVED: 4.5e-4 residual disappears)."""
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
from zipline.finance.slippage import VolumeShareSlippage
from zipline.finance.commission import PerDollar
fills = []
def initialize(ctx):
    ctx.i = -1; ctx.s = symbol("XXX")
    set_slippage(VolumeShareSlippage(volume_limit=0.025, price_impact=0.1)); set_commission(PerDollar(cost=FEE))
def handle_data(ctx, data):
    ctx.i += 1
    if ctx.i == BUY_BAR: order(ctx.s, 500)
def analyze(ctx, perf):
    for dt, txs in perf["transactions"].items():
        for t in txs: fills.append(dict(dt=str(dt.date()), bar=int(df.index.get_loc(pd.Timestamp(dt.date()))), px=float(t["price"]), amount=int(t["amount"]), commission=None))
    fills.append(dict(commissions=float(perf["orders"].explode().dropna().map(lambda o: o["commission"]).sum()) if perf["orders"].explode().dropna().size else 0.0))
    fills.append(dict(ending_value=float(perf["portfolio_value"].iloc[-1])))
run_algorithm(start=df.index[0], end=df.index[-1], initialize=initialize, handle_data=handle_data,
              analyze=analyze, capital_base=1e9, bundle="bt", data_frequency="daily")
tx = [f for f in fills if "px" in f]
rem = 500; exp = []; b = BUY_BAR + 1
while rem > 0:
    vol = float(df.Volume.iloc[b]); share = min(rem/vol, 0.025); amt = min(rem, int(round(share*vol))) if False else int(share*vol)
    px = round(float(df.Close.iloc[b]), 3); imp = (amt/vol)**2*0.1*px; exp.append(dict(bar=b, amount=amt, px=px+imp, close=px, volume=vol)); rem -= amt; b += 1
    if amt == 0: break
res_exp = exp
res = dict(engine="zipline-reloaded", fills=[f for f in fills if 'px' in f], expected_hand=res_exp[:12], n_expected_fills=len(res_exp))

print(json.dumps(res))
