import os, time, sys
from absurd_sdk import Absurd
DSN = "postgres://lab@127.0.0.1:55401/postgres"
LOGDIR = os.environ.get("ABS_LOGDIR", "/tmp/lab/work/absurd/run")
SIDE = os.path.join(LOGDIR, "sideeffects.log")
WORK_SECS = float(os.environ.get("WORK_SECS", "3"))
FAIL_FIRST = int(os.environ.get("FAIL_FIRST", "0"))   # scenario B: raise on first N attempts
def se(kind, task, attempt):
    with open(SIDE, "a") as f:
        f.write(f"{kind},{task},{attempt},{os.getpid()},{time.time():.3f}\n")
def make(queue_main="main", **kw):
    a = Absurd(DSN, queue_name=queue_main, **kw)
    @a.register_task("job", queue="main")
    def job(params, ctx):
        n = params["n"]; att = ctx._task["attempt"]
        def work():
            se("work", n, att); time.sleep(WORK_SECS); return {"n": n, "done": True}
        w = ctx.step("work", work)
        if FAIL_FIRST and att <= FAIL_FIRST:
            se("fail", n, att); raise RuntimeError(f"transient failure attempt {att}")
        rid = ctx.step("spawn_review", lambda: str(a.spawn("review", {"n": n}, queue="review", idempotency_key=f"review-{n}")["task_id"]))
        snap = ctx.await_task_result(rid, queue_name="review", timeout=120)
        return {"n": n, "review": snap.result if hasattr(snap, "result") else str(snap)}
    @a.register_task("review", queue="review")
    def review(params, ctx):
        att = ctx._task["attempt"]
        def r():
            se("review", params["n"], att); time.sleep(float(os.environ.get("REVIEW_SECS","0.2"))); return "ok"
        return {"review": ctx.step("review", r)}
    return a
