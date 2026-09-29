import os, sys, time, json
from dbos import DBOS, DBOSConfig, Queue

DB = os.environ.get("DBOS_DB", "postgresql://lab@127.0.0.1:55402/dbos_app")
LOG = os.environ.get("SE_LOG", "/tmp/lab/work/dbos/side_effects.log")
FAIL = os.environ.get("FAIL_MODE", "")   # "flaky" => tasks 0-4 fail first 2 attempts, task 5 always fails
SLEEP = float(os.environ.get("WORK_SLEEP", "3"))

def se(kind, task, attempt=0):
    with open(LOG, "a") as f:
        f.write(f"{kind},{task},{attempt},{os.getpid()},{time.time():.3f}\n")

def attempts_so_far(task):
    try:
        return sum(1 for l in open(LOG) if l.startswith(f"work,{task},"))
    except FileNotFoundError:
        return 0

@DBOS.step(retries_allowed=True, max_attempts=4, interval_seconds=1.0, backoff_rate=2.0)
def work(task: int) -> str:
    n = attempts_so_far(task) + 1
    se("work", task, n)
    time.sleep(SLEEP)
    if FAIL == "flaky":
        if task < 5 and n <= 2: raise RuntimeError(f"transient task={task} attempt={n}")
        if task == 5: raise RuntimeError(f"permanent task={task} attempt={n}")
    return f"result-{task}"

@DBOS.step()
def review(task: int, res: str) -> str:
    se("review", task)
    time.sleep(float(os.environ.get("REVIEW_SLEEP", "0")))
    return f"reviewed({res})"

@DBOS.workflow()
def pipeline(task: int) -> str:
    r = work(task)
    return review(task, r)

def main():
    cfg: DBOSConfig = {"name": "labapp", "system_database_url": DB, "application_version": "v1",
                       "executor_id": os.environ.get("EXEC_ID", "w1")}
    DBOS(config=cfg)
    DBOS.launch()
    DBOS.register_queue("q", worker_concurrency=int(os.environ.get("WC", "5")), polling_interval_sec=0.5)
    print(f"[{time.time():.3f}] worker pid={os.getpid()} exec={cfg['executor_id']} launched", flush=True)
    while True: time.sleep(1)

if __name__ == "__main__":
    main()
