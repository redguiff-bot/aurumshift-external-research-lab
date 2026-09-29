"""T13 — ABIDES-JPM (abides-core + abides-markets, unmaintained since 2023-12) — can it run an agent-based LOB simulation, and is a fixed seed reproducible?
Config rmsc04 (default background-agent market), 10:00 -> 10:20 (20 simulated minutes)."""
import sys, json, time, hashlib, warnings; warnings.filterwarnings("ignore")
from abides_core import abides
from abides_core.utils import parse_logs_df
from abides_markets.configs import rmsc04
def run(seed):
    cfg = rmsc04.build_config(seed=seed, end_time="10:20:00", book_logging=False, log_orders=False)
    t = time.perf_counter(); end = abides.run(cfg); dt = time.perf_counter()-t
    ex = end["agents"][0]
    obs = ex.order_books["ABM"]
    # digest of final book + count of agents + last trade
    l2b = obs.get_l2_bid_data(depth=5); l2a = obs.get_l2_ask_data(depth=5); last = obs.last_trade
    n_ev = len(end.get("agents", []))
    dig = hashlib.sha256(repr((l2b, l2a, last)).encode()).hexdigest()[:16]
    return dict(seconds=round(dt, 2), n_agents=n_ev, last_trade=last, best_bid=l2b[0] if l2b else None, best_ask=l2a[0] if l2a else None, digest=dig)
a = run(1); b = run(1); c = run(2)
print(json.dumps(dict(run_seed1=a, rerun_seed1=b, run_seed2=c, reproducible_same_seed=a["digest"] == b["digest"], differs_across_seeds=a["digest"] != c["digest"])))
