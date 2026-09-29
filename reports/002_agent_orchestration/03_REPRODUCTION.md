# 03 — REPRODUCTION (crash / retry / recovery experiments)

All results below are **OBSERVED** in this sandbox unless tagged otherwise; raw scripts and logs are under `experiments/<name>/`. Read `00_SCOPE.md` limits first: 20 tasks, ~3 s of work, single runs, parallel agents sharing one host (two cross-kill incidents, flagged below).

Five systems were exercised (task asked for 3): **Absurd, DBOS, Procrastinate** (PG 18.6), plus **Restate** (own server) and **Beads** (embedded Dolt).

## Common workload
20 tasks. Task = step `work` (appends `task,attempt,pid,ts` to a side-effect log file, sleeps ~3 s) followed by a dependent `review` step/task. Duplicate side effects are counted from that log. "Intervention" = a human/operator action other than starting workers/PG normally.

Dependency mechanism per system (differs, so not identical workloads): Absurd = child task in a second queue + await; DBOS = second step in the same workflow; Procrastinate = hand-built `defer` of `review` after `work` returns; Restate = second `ctx.run` in the handler; Beads = 20 worker issues each with a blocked reviewer issue.

## Scenario A — SIGKILL a worker mid-task
| System | Config | Observed | Time to reassignment | Duplicates | Interventions |
|---|---|---|---|---|---|
| Absurd | lease 10 s, 5 tasks in flight | live worker reclaimed via `claim_task` sweep; kill at +1.5 s → attempt 2 began 10.1 s later; kill at +4.5 s → 9.5 s | 9.5–10.1 s; **21.8 s** (≈52 s to finish) when all workers were saturated by awaiting parents; 7.1 s with a free worker | 5 dup `work` when killed mid-step; **0** when `work` already checkpointed (20 checkpoints reused) | 0 |
| DBOS | 2 live workers w1,w2; kill w1 | **surviving worker did not take over**; w1's 5 workflows stayed PENDING for the full 50 s (A1) / 20 s (A2) watch | never (until same executor id restarts): after restarting w1 with same id+version, done within ≈6.5 s | A1: 5 dup `work`; A2 (kill during `review`): `work` replayed from `operation_outputs`, only `review` dup | 1 (restart the dead executor id) |
| Procrastinate | default (nothing configured) | 4 jobs held by the killed worker stayed `doing` ≥140 s with a surviving worker; a fresh worker pruned the dead worker row but jobs stayed `doing`; `get_stalled_jobs()` listed all 4 | **never** without operator | 0 dups, but 4 jobs never finish | ∞ (needs operator) |
| Procrastinate | + hand-written periodic `retry_stalled_jobs` (cron `* * * * *`, heartbeat 10 s, timeout 30 s) | 4 jobs retried 24.7 s after kill; all 20 work + 20 review succeeded | 24.7 s (fast only because the worker died before its first heartbeat). Worst case ≈90 s = 30 s staleness + ≤60 s cron tick — **INFERENCE** | 4 dup `work` | 0 after one-time config |
| Restate | single node, kill service endpoint 1.5 s after submit | server showed "backing-off, Connection refused" with growing intervals; after restarting the service all 20 completed | tied to backoff + manual restart of the service | `work` 40 executions for 20 tasks (2× each); `review` exactly 20 | 1 (restart the service process) |
| Beads | claimant dies; 5-min lease | after lease expiry (07:06:21) with no operator until 07:08:41: `bd ready` omitted the item and another agent's `--claim` failed "already claimed by agent2"; `bd reclaim --older-than 0s` reverted 10 stale claims; a rescuer claimed one and the old owner's late heartbeat was **refused** | manual only (TTL fixed 5 min) | n/a (no work executed by bd) | 1 (`bd reclaim`) |

## Scenario B — transient failure, retry/backoff, terminal failure
| System | Config | Observed |
|---|---|---|
| Absurd | exponential base 2 s ×2 | uncontended gaps 2.03 s, 4.05 s then success; under contention 3.06 s, 4.11 s; `work` ran once per task (checkpoint reused). `FAIL_FIRST=99, max_attempts=3`: all 20 failed at attempts=3, review never spawned. **No retry strategy set → 5 attempts burned in <1 s** (default is immediate retry). |
| DBOS | `max_attempts=4`, defaults interval 1 s ×2 | task 0 succeeded attempt 3; always-failing task 5 ran 4 attempts (gaps ≈2/3/5 s incl. 1 s sleep), ended workflow ERROR `DBOSMaxStepRetriesExceeded`; 19 SUCCESS + 1 ERROR. Terminal failure needs human triage. |
| Procrastinate | `RetryStrategy(max_attempts=4, exponential_wait=2)` | default polling → gaps 5.0/5.0/10.0/20.0 s (retry sends no NOTIFY; picked up on 5 s poll). With `--fetch-job-polling-interval=0.5` → 2.03/4.04/8.05/16.09 s. Always-failing job ran **5** times (max_attempts=4 ⇒ 5 runs), ended `failed`. One run was interrupted by another agent's `pkill -9 postgres` (kept in logs, not the scenario under test). |
| Restate | `ctx.run` retry 1 s ×2 | 3 failures then success at gaps 1011/2008/4009 ms; `maxRetryAttempts=4` → gaps 506/1006/2007 ms then caller HTTP 500 (terminal); plain handler throw under default policy → gaps 546…20639 ms, stays backing-off (we cancelled after ≈7 attempts; default = pause after 70). |
| Beads | – | not applicable (no retry mechanism: PROVEN by absence). |

## Scenario C — PostgreSQL crash mid-run (`kill -9` postmaster / `pg_ctl -m immediate`), then restart
| System | Observed | Interventions |
|---|---|---|
| Absurd | **SDK workers as shipped died in ≈0.8 s** (OperationalError); no progress for 90 s until workers restarted by hand; then finished in 10 s, no lost tasks, 5 dup reviews. With a 12-line reconnect loop around `start_worker` (written by us): completed 18.9 s after PG returned, 0 interventions. SDK has no reconnect (INFERENCE from code + run). | 1 as shipped / 0 with wrapper |
| DBOS | app stayed alive, logged ≈12 connection-refused errors over a 12 s outage; after PG returned all 20 finished, no app restart, no duplicates (40 side-effect lines). *Caveat:* nothing in flight was at risk during the outage. | 1 (restart PG only) |
| Procrastinate | 3 runs (immediate stop, kill -9 postmaster+children, 3 s blip): **worker did not reconnect**; listener side task failed → worker stopped itself (`_monitor_side_tasks`) even on a 3 s blip; in-flight jobs drained then process exited; remaining 12 `work` jobs stayed `todo` until a worker was restarted. No jobs lost/duplicated. | 1 without a supervisor (systemd) |
| Restate (own server killed, not PG) | `kill -9` server 1.5 s after submit, restart on same data dir: came up without repair, leaders re-elected, all 20 completed; `work` ran 2× each (service finished work while server down, result could not be journaled); `review` once. | 0 repair (process restarts only) |
| Beads (embedded) | 60 `bd create` killed at random 20–600 ms (51 alive when killed): DB opened, 21 distinct valid issues, next create worked, JSONL export matched. 30 killed claim processes → 0 inconsistent status/assignee/lease rows. Integrity check limited to list/show/export (`doctor`, `sql`, `fsck` unavailable in embedded mode) → "no corruption observed", **not** proof of crash-safety. | 0 |

## Scenario D — cross-session continuation
| System | Observed |
|---|---|
| Absurd | stop all workers, idle 25 s, start new workers → resumed, 20/20 in 18 s; 5 dup reviews (killed in flight); only action = start workers. |
| DBOS | with all processes dead nothing progresses. New executor id w3 drained the 15 ENQUEUED workflows but **not** w1's 5 PENDING; a worker on app version v2 recovered nothing; a process with the *original* executor id + version recovered the 5 in ≈4.5 s (only interrupted `review` duplicated). 1 intervention. |
| Procrastinate | 20 jobs deferred with no worker; worker started, SIGTERM after 5 s drained its 4 running jobs and exited in 1.4 s; a new worker 15 s later finished all 20 work + 20 review, 0 duplicates. Graceful stop is clean. |
| Restate | 20 invocations submitted with service down; server SIGTERM, 60 s wait, restart: 20 still pending; service started later → all 20 completed. (An accidental `pkill -f` that killed both processes uncleanly was also recovered.) |
| Beads | every `bd` call is a fresh process; claims, deps and closes survived across all of them. `bd prime` not exercised. |

## Extra observations
- **DBOS SQLite:** single process survived kill -9 + restart, 20/20 recovered; two processes starting simultaneously on a fresh file hit a migration race ("table workflow_status already exists"). Single-host (INFERENCE).
- **Absurd lease hazard (our misconfiguration, real hazard):** a step longer than the lease with no heartbeat was re-executed *while still alive* → 12 duplicate reviews with no crash.
- **Beads parallel writers:** 8 processes × 5 creates = 40/40 success, no lock errors, 26.3 s (≈0.66 s/write, ≈1.5 writes/s). Claim race: 2/4/8 parallel claimants → exactly one winner each (one round per N; embedded file lock serialises, so nothing is learned about server-mode races).

## Not tested (UNKNOWN)
Power loss/fsync (Restate claim is code-reading only); network partition; multi-host; clock skew; Restate cluster/snapshots/virtual objects/awakeables; Beads server mode and multi-clone dolt push/pull merges, gates/molecules/wisps; long-running (>1 min) steps on Restate; Absurd Habitat/absurdctl/pg_cron; Temporal/River/Hatchet/pgqueuer (no experiments); throughput and soak behaviour of everything; TS/Go SDKs of DBOS.

## Reproduce
Scripts: `experiments/absurd/{scnA..scnD.sh,app.py,worker.py,submit.py}`, `experiments/dbos/{scenA..scenD.sh,app.py,enqueue.py,lib.sh}`, `experiments/procrastinate/{app.py,defer*.py,scenC.sh,logs/}`, `experiments/restate/{scenarioD.sh,restate.toml,*.log}`, `experiments/beads/{race.sh,kill9*.sh,*.log,README.txt}`. They assume a private PG 18 cluster with trust auth on ports 55401–55403 (`pgstart.sh` style; not committed) and are **not** hardened for re-execution elsewhere — paths and ports are sandbox-specific.
