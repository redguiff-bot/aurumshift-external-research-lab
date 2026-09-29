import time, sys, json, hashlib
from abides_core import abides
from abides_core.utils import parse_logs_df
from abides_markets.configs import rmsc04
def run(seed):
    cfg = rmsc04.build_config(seed=seed, end_time="09:45:00", book_logging=False, log_orders=False, stdout_log_level="ERROR") if 'stdout_log_level' in rmsc04.build_config.__code__.co_varnames else rmsc04.build_config(seed=seed, end_time="09:45:00")
    t0 = time.perf_counter(); end = abides.run(cfg); dt = time.perf_counter() - t0
    ex = end["agents"][0]
    ob = ex.order_books["ABM"]
    trades = getattr(ob, "last_trade", None)
    return {"seconds": round(dt, 1), "last_trade": trades, "n_agents": len(end["agents"]), "hash": hashlib.sha256(str((trades, ob.get_l1_bid_data(), ob.get_l1_ask_data())).encode()).hexdigest()[:12]}
out = {}
try:
    a = run(1); b = run(1); c = run(2)
    out = {"run_seed1": a, "run_seed1_again": b, "run_seed2": c, "deterministic": a["hash"] == b["hash"], "seed_sensitive": a["hash"] != c["hash"]}
except Exception as e:
    import traceback; out = {"error": f"{type(e).__name__}: {str(e)[:400]}", "tb": traceback.format_exc()[-600:]}
print(json.dumps(out, default=str, indent=1))
