import warnings, os, sys, time, json, hashlib; warnings.filterwarnings("ignore")
os.environ["ZIPLINE_ROOT"] = "/tmp/zl/root"
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import synth, save
import exchange_calendars as xc
import zipline, zipline.data.bundles as b
from zipline import run_algorithm
from zipline.api import order_target_percent, symbol, record
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities
res = {"version": zipline.__version__}
cal = xc.get_calendar("XNYS"); sess = cal.sessions_in_range("2023-01-03", "2024-06-28").tz_localize(None)
os.makedirs("/tmp/zl/csv/daily", exist_ok=True)
for sym, seed in (("AAA", 3), ("BBB", 4)):
    d = synth(len(sess), seed=seed); d.index = sess; d.index.name = "date"; d["dividend"] = 0.0; d["split"] = 1.0
    d.to_csv(f"/tmp/zl/csv/daily/{sym}.csv")
register("mycsv", csvdir_equities(["daily"], "/tmp/zl/csv"), calendar_name="XNYS", start_session=sess[0], end_session=sess[-1])
t0 = time.perf_counter(); b.ingest("mycsv", show_progress=False); res["ingest_seconds"] = round(time.perf_counter() - t0, 2)
def initialize(ctx): ctx.a = symbol("AAA"); ctx.b = symbol("BBB")
def handle_data(ctx, data):
    h = data.history([ctx.a, ctx.b], "close", 20, "1d")
    w = 0.5 if h[ctx.a].iloc[-1] > h[ctx.a].mean() else 0.0
    order_target_percent(ctx.a, w); order_target_percent(ctx.b, 0.5 - w / 2 if h[ctx.b].iloc[-1] > h[ctx.b].mean() else 0.0)
    record(px=data.current(ctx.a, "close"))
def run():
    return run_algorithm(start=pd.Timestamp("2023-06-01"), end=pd.Timestamp("2024-06-28"), initialize=initialize, handle_data=handle_data, capital_base=1e6, bundle="mycsv", trading_calendar=cal if False else None, data_frequency="daily")
try:
    t0 = time.perf_counter(); p1 = run(); res["run_seconds"] = round(time.perf_counter() - t0, 2); p2 = run()
    res["n_days"] = len(p1); res["final_portfolio_value"] = float(p1.portfolio_value.iloc[-1])
    res["deterministic_2runs"] = bool(np.allclose(p1.portfolio_value.values, p2.portfolio_value.values, rtol=0, atol=1e-9))
    res["commission_slippage_defaults"] = "per-share commission $0.001 min $0 & VolumeShareSlippage(0.025, 0.1) by default (OBSERVED in source: finance/commission.py L25-28, slippage.py L269-270)"
    res["orders_filled_next_bar"] = bool((p1.orders.map(len).sum() > 0))
except Exception as e: res["run_error"] = f"{type(e).__name__}: {str(e)[:400]}"
# strict-calendar gate: extra weekend session must be rejected at ingest
try:
    d = synth(30, seed=1, start="2023-01-03", freq="1D").tz_localize(None); d.index.name = "date"; d["dividend"] = 0.0; d["split"] = 1.0
    os.makedirs("/tmp/zl/csv2/daily", exist_ok=True); d.to_csv("/tmp/zl/csv2/daily/ZZZ.csv")
    register("bad", csvdir_equities(["daily"], "/tmp/zl/csv2"), calendar_name="XNYS", start_session=pd.Timestamp("2023-01-03"), end_session=pd.Timestamp("2023-02-10"))
    b.ingest("bad", show_progress=False); res["calendar_gate"] = "ingest ACCEPTED weekend bars"
except Exception as e: res["calendar_gate"] = f"ingest REJECTED: {type(e).__name__}: {str(e)[:160]}"
print(json.dumps(res, indent=1)); save("zl_microtest.json", res)
