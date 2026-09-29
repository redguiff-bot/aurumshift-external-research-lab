# 04 — FAILURE MODES

Legend: ✔ handled automatically (observed) · ◐ handled with config/glue · ✘ not handled · ? unknown. Evidence tags as in `00_SCOPE.md`. "Obs" refers to `03_REPRODUCTION.md`.

## 1. Matrix (top 5)
| Failure | Absurd | DBOS (no Conductor) | Procrastinate | Restate | Beads |
|---|---|---|---|---|---|
| Worker SIGKILL, another live worker exists | ✔ after lease (≈10 s configured), *if a polling worker has a free slot* (Obs A: 7–22 s) | ✘ live worker never takes over; needs the same `executor_id`+`application_version` to restart (Obs A) | ✘ by default (jobs `doing` forever); ◐ with DIY periodic `retry_stalled_jobs` (24.7 s best, ≈90 s worst INFERENCE) | ◐ server retries with backoff; needs the service endpoint back (Obs A) | ✘ manual `bd reclaim`; TTL 5 min fixed |
| Step already finished before crash | ✔ checkpoint reused (0 dup `work`) | ✔ replayed from `operation_outputs` | ✘ no checkpoints: job restarts from zero | ✔ journal replay (but result lost if server down at that instant → 2× `work`) | n/a |
| Interrupted step's side effect | at-least-once (5 dup) | at-least-once (5 dup) | at-least-once (4 dup) | at-least-once (2× each) | n/a |
| PG (or store) crash and restart | ✘ SDK workers die in <1 s; ◐ 12-line reconnect loop | ✔ app self-heals | ✘ worker stops itself even on 3 s blip → supervisor required | ✔ (server kill -9, same data dir) | ✔ embedded: no corruption observed (limited checks) |
| Whole system stopped, resumed later | ✔ | ◐ only same executor id + same code version | ✔ | ✔ | ✔ |
| Transient step failure | ✔ retry strategy (default: **none → immediate, 5 attempts <1 s**) | ✔ `max_attempts` | ✔ RetryStrategy (5 s poll granularity by default) | ✔ policy (default 70 attempts then pause) | ✘ no retry concept |
| Terminal failure | task `failed`, needs triage | workflow ERROR, triage; `max_recovery_attempts` 100 then dead-letter | job `failed`, triage | paused (default) or killed, triage | n/a |
| Long step > lease/timeout | ✘ re-executed while alive if no heartbeat (12 dup reviews) | no lease → not applicable; workflow timeout optional | heartbeat is worker-level (10 s/30 s), not per-job | inactivity timeout 1 m / abort 10 m default (not tested >1 m) | lease 5 min, must `bd heartbeat` |
| Zombie/late worker after takeover | run-state fenced (AB002); **side effects not fenced** | n/a (no takeover) | ✘ issue #1633: presumed-stalled worker can still finish/retry after takeover (OBSERVED via issues page) | journal-based, state fenced by server (INFERENCE) | ✔ late heartbeat refused, non-owner close refused (Obs A) |
| Code deploy while work in flight | ✔ (state is data) | ✘ default `application_version` = md5 of source → old PENDING stranded | ✔ (task names) | ✔ deployment registration versioned (not tested) | n/a |
| Dependency cycle / wrong graph | no graph | code | no graph | code | `blocks` graph; cycle handling not tested (UNKNOWN) |

## 2. Cross-cutting failure modes (INFERENCE unless tagged)
1. **At-least-once is universal (OBSERVED in all 4 runtimes).** Any side effect outside the store — git push, PR comment, file write, API call, LLM-billed call — needs its own idempotency key or fenced write. No candidate offers exactly-once for user code. For coding/research agents this is the dominant correctness risk, not queue mechanics.
2. **Lease vs. step length.** Absurd's lease and Beads' 5-min TTL assume heartbeats; long agent steps must heartbeat or checkpoint frequently, or be split. A too-short lease = duplicate live execution (OBSERVED, Absurd).
3. **Recovery depends on liveness of something.** Absurd needs a polling worker with a free slot (saturation delayed reclaim to 21.8 s and a stall-prone design when all slots are held by awaiting parents — OBSERVED). Procrastinate needs your periodic task. DBOS needs the same executor id back. Beads needs a timer. Restate needs the service endpoint back. "Low operator intervention" is really "a supervisor + a recovery loop you must own".
4. **Await-in-worker deadlock shape (Absurd).** Parent awaiting a child in another queue holds a worker slot (PROVEN); with N slots all held by parents, children starve (INFERENCE, consistent with the 21.8 s/52 s observation; not tested to deadlock).
5. **Silent defaults.** Absurd default retry = immediate; Procrastinate default = stuck forever; DBOS default executor id `"local"` + source-hash version; Restate default bind `[::]` fails without IPv6; Beads default CGO build failed here. Each is small but each is where "low intervention" quietly breaks.
6. **Young / concentrated maintenance.** Absurd: 1 author, Alpha, lease-code fixes in March 2026. Procrastinate/DBOS: bus factor ≈1–2. Beads: extreme churn, 59 corruption/data-loss fixes in 90 days, 896 open issues. Restate: healthiest team but heaviest artifact.
7. **Two sources of truth.** Restate (RocksDB) or Beads (Dolt) beside PostgreSQL contradicts "one authoritative source per concern" (`claude.md`) unless it *is* the sole authority for that concern (INFERENCE; final call belongs to the real repo).
8. **Observability gaps.** DBOS pickled outputs are opaque in psql; Beads embedded mode has no SQL/doctor; Absurd/Procrastinate are plain-SQL friendly (OBSERVED).
9. **Test-suite blind spot.** Neither Absurd, Procrastinate, nor (as read) DBOS ships a SIGKILL/PG-crash end-to-end test; Restate has chaos tests at cluster level only. Our experiments are the only kill-level evidence here — and they are single runs.
10. **Environment coupling.** Absurd's own suite needs Docker+PG16 and had 4 failures on PG 18 (harness/planner-related per INFERENCE). Not evidence of runtime breakage, but PG 18 has not been verified upstream for Absurd (UNKNOWN); Procrastinate has PG 14–18 CI (OBSERVED).
