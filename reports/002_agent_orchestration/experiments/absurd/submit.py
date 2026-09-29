import sys, app, time
from absurd_sdk import Absurd
n = int(sys.argv[1]); ma = int(sys.argv[2]) if len(sys.argv)>2 else 5
rs = None
if len(sys.argv)>3: rs = {"kind":"exponential","base_seconds":float(sys.argv[3]),"factor":2}
a = app.make("main")
for q in ("main","review"): a.create_queue(q)
for i in range(n):
    a.spawn("job", {"n": i}, max_attempts=ma, retry_strategy=rs, idempotency_key=f"job-{i}")
print(f"[{time.time():.3f}] submitted {n}")
