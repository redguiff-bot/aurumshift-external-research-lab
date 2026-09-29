import os, time, asyncio, datetime
import procrastinate
from procrastinate import RetryStrategy

DB = os.environ.get("DB", "scen")
LOG = os.environ.get("SIDELOG", f"/tmp/lab/work/procrastinate/{DB}.side.log")
app = procrastinate.App(
    connector=procrastinate.PsycopgConnector(kwargs=dict(host="127.0.0.1", port=55403, user="lab", dbname=DB)),
    import_paths=["app"] if False else [],
)

def side(kind, n, attempt):
    with open(LOG, "a") as f:
        f.write(f"{kind},{n},{attempt},{os.getpid()},{time.time():.3f}\n")

@app.task(name="work", pass_context=True)
async def work(ctx, n: int):
    side("work", n, ctx.job.attempts)
    await asyncio.sleep(float(os.environ.get("WORK_SECS", "3")))
    # manual chaining: dependent 'review' deferred only after work body completes
    await review.configure(queueing_lock=None).defer_async(n=n)

@app.task(name="review", pass_context=True)
async def review(ctx, n: int):
    side("review", n, ctx.job.attempts)

@app.task(name="flaky", pass_context=True,
          retry=RetryStrategy(max_attempts=3, wait=0, exponential_wait=0, linear_wait=0) if False else None)
async def flaky_placeholder(ctx, n: int): pass

@app.task(name="flaky2", pass_context=True,
          retry=RetryStrategy(max_attempts=4, exponential_wait=2))  # waits 2,4,8 s
async def flaky2(ctx, n: int):
    side("flaky2", n, ctx.job.attempts)
    if ctx.job.attempts < int(os.environ.get("FAIL_TIMES", "2")):
        raise RuntimeError(f"transient failure attempt {ctx.job.attempts}")

if os.environ.get("RETRY_STALLED") == "1":
    @app.periodic(cron="* * * * *")
    @app.task(queueing_lock="retry_stalled_jobs", name="retry_stalled_jobs")
    async def retry_stalled_jobs(timestamp):
        for job in await app.job_manager.get_stalled_jobs():
            side("retry_stalled", job.id, job.attempts)
            await app.job_manager.retry_job(job)
