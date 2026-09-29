# usage: worker.py <queue> <claim_timeout> <concurrency> [reconnect]
import sys, time, os, traceback
import app
from absurd_sdk import Absurd
q, ct, conc = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); reconnect = len(sys.argv) > 4
def run():
    a = app.make(q)
    print(f"[{time.time():.3f}] worker pid={os.getpid()} queue={q} start", flush=True)
    a.start_worker(claim_timeout=ct, concurrency=conc, poll_interval=0.25)
while True:
    try:
        run(); break
    except Exception as e:
        print(f"[{time.time():.3f}] worker pid={os.getpid()} CRASH {type(e).__name__}: {str(e)[:120]}", flush=True)
        if not reconnect: sys.exit(3)
        time.sleep(1)
