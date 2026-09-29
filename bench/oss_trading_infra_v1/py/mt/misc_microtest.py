import json, time, os, sys, warnings; warnings.filterwarnings("ignore")
res = {}
# tardis-dev: free first-day-of-month sample, no API key
try:
    import tardis_dev
    t0 = time.perf_counter()
    tardis_dev.download_datasets(exchange="deribit", data_types=["trades"], from_date="2025-03-01", to_date="2025-03-02", symbols=["BTC-PERPETUAL"], download_dir="/tmp/misc/tardis")
    fs = [os.path.join(dp, f) for dp, _, fn in os.walk("/tmp/misc/tardis") for f in fn]
    res["tardis_dev_free_first_day"] = {"files": [(os.path.basename(f), os.path.getsize(f)) for f in fs], "seconds": round(time.perf_counter() - t0, 1)}
    if fs:
        import gzip, pandas as pd
        df = pd.read_csv(fs[0]); res["tardis_dev_free_first_day"].update({"rows": len(df), "columns": list(df.columns), "has_local_timestamp": "local_timestamp" in df.columns})
except Exception as e: res["tardis_dev_free_first_day"] = {"error": f"{type(e).__name__}: {str(e)[:250]}"}
# yfinance
try:
    import yfinance as yf
    t0 = time.perf_counter(); d = yf.download("AAPL", period="5d", interval="1d", progress=False, auto_adjust=False)
    res["yfinance"] = {"rows": int(len(d)), "seconds": round(time.perf_counter() - t0, 1), "empty": bool(d.empty)}
except Exception as e: res["yfinance"] = {"error": f"{type(e).__name__}: {str(e)[:250]}"}
# pointblank
try:
    import pointblank as pb, polars as pl, numpy as np
    df = pl.DataFrame({"ts": list(range(10)), "px": [1.0, 2.0, -1.0, 4.0, None, 6.0, 7.0, 8.0, 9.0, 10.0], "hi": [2.0]*10, "lo": [1.0]*9 + [3.0]})
    v = pb.Validate(df).col_vals_gt("px", 0).col_vals_not_null("px").col_vals_ge("hi", pb.col("lo")).interrogate()
    res["pointblank"] = {"version": pb.__version__, "n_failed_per_step": [s for s in v.n_failed().values()] if hasattr(v, "n_failed") else "?", "all_passed": bool(v.all_passed())}
except Exception as e: res["pointblank"] = {"error": f"{type(e).__name__}: {str(e)[:250]}"}
print(json.dumps(res, indent=1, default=str))
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "results", "misc_microtest.json"), "w"), indent=1, default=str)
