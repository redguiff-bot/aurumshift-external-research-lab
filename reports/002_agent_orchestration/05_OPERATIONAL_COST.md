# 05 — OPERATIONAL COST

Setup times are OBSERVED in this sandbox with a warm package proxy and PG already present, **including agent authoring mistakes where noted**; they are not what a new operator would experience.

## 1. Comparison table
| Dimension | Absurd | DBOS (Py) | Procrastinate | Restate | Beads |
|---|---|---|---|---|---|
| Implementation complexity (core) | 3150-line SQL + 2317-line SDK; readable end-to-end in a day (INFERENCE) | ~32.7k LOC Py; `_sys_db.py` 7.4k lines | ~8.1k lines Py+SQL | ~283k Rust, 984 crates | ~371k Go |
| Services required | PG | PG (or SQLite) | PG | Restate server (+ your endpoint) | none embedded (Dolt inside `bd`); Dolt server for multi-writer |
| Extra glue you must write | reconnect loop; retry strategy; scheduled cleanup; DAG/fan-in | supervisor with stable executor id + pinned version; multi-executor takeover (or Conductor) | periodic stalled-retry task; supervisor for reconnect; chaining; DAG | idempotency for side effects; registration step; long-step pattern | timer running `bd reclaim`; everything runtime-side |
| Durable state model | 5 PG tables/queue, plain SQL | ~11 PG tables, pickled blobs | 4 PG tables, plain SQL | embedded log+RocksDB, SQL via DataFusion | Dolt (MySQL protocol), no SQL in embedded mode |
| Worker lifecycle | pull, lease, checkpoint heartbeat | executor owns PENDING rows; recovery at launch | pull, worker heartbeat 10 s/timeout 30 s | server pushes HTTP/2 to endpoint | agent claims via CLI; lease 5 min |
| Retry / reassignment | strategy (default none); auto reclaim by polling worker | step retries ✔; reassignment ✘ w/o Conductor | RetryStrategy ✔; reassignment DIY | policy ✔ default 70 then pause; reassignment = retry to same endpoint | none; manual reclaim |
| Dependency graph | ✘ (child task + await, events) | code | ✘ (defer-from-task, locks) | code | ✔ native (19 dep types, `ready`/`blocked`) |
| Observability | SQL + optional Habitat/absurdctl | SQL (opaque pickles), Conductor UI paid | SQL, events table | CLI + SQL (18 tables) + UI + Prometheus | CLI (`ready`, `blocked`); no SQL/doctor in embedded |
| Setup time (OBSERVED) | 19 s to schema; ≈10 min to first pipeline | pip 6.3 s; ≈20 min to experiment | pip 9 s; ≈10 min | npm 11 s; ≈2 min to running server (+IPv6 config fix) | first build 3m40s (needed `-tags gms_pure_go`, Go 1.26.7); init 4.9 s |
| Artifact / memory | pip, small | pip, small | pip, small | 225 MB binary; RSS ≈275–307 MB; 220 MB data dir at start | 214 MB binary |
| Operator burden (1–5, INFERENCE) | 2 | 2–3 (4 if failover matters and no Conductor) | 2 | 2 | 2 (as memory), unfit as runtime |
| License | Apache-2.0 | MIT (control plane commercial) | MIT | BSL 1.1 (internal use OK) | MIT |
| Maintenance risk | HIGH (1 author, Alpha) | MED (co. backed, churn 3.0) | MED (1–2 maintainers) | LOW-MED (co. backed, 22 authors) | HIGH (churn, integrity fixes) |

## 2. Operator interventions actually observed
| Scenario | Absurd | DBOS | Procrastinate | Restate | Beads |
|---|---|---|---|---|---|
| A worker SIGKILL | 0 | 1 | ∞ default / 0 after 1 config | 1 | 1 |
| B transient failure | 0 (terminal needs triage) | 0 (terminal needs triage) | 0 | 0 | n/a |
| C store crash | 1 (0 with 12-line wrapper) | 1 (PG only) | 1 (needs supervisor) | 0 repair | 0 |
| D cold restart | 0 (start workers) | 1 (if id/version differ, stranded) | 0 (start workers) | 0 | 0 |

## 3. Ongoing operations (INFERENCE)
- **All Postgres-based options** add tables/functions to the PG the team already runs (PG 18.6 in production per the user): no new backup/HA story, but high-churn `UPDATE`s on task/lease rows imply bloat/vacuum attention — not measured here (UNKNOWN).
- **Restate/Beads** add a second stateful store (backup, upgrade, monitoring). Restate snapshots to S3 are documented, untested.
- **Upgrades:** Absurd = re-apply SQL migrations (project is Alpha; churn UNKNOWN); DBOS = 36 migrations + API removals in 3.0; Procrastinate = schema migration scripts; Beads = frequent breaking changes; Restate = versioned deployments.
- **Supervision** is required by every option that recovers work: systemd/K8s-like restarter for workers (Absurd wrapper, Procrastinate worker exit, Restate service, DBOS executor id) — "no operator" really means "a process supervisor + alerting on stuck/failed rows".
- **Alerts you would need** (INFERENCE): rows stuck in running/doing beyond lease; terminal `failed` count; oldest ready age; duplicate-side-effect audit; PG connectivity.

## 4. What the penalised patterns cost (for contrast, not measured)
Temporal/Hatchet/Inngest/Prefect/Conductor/Airflow/Argo need a multi-service or cluster deployment plus their own database/broker/cache (DOCUMENTED_CLAIM + config reading in landscape). None was run; they are excluded on the stated priority, not on measured failure.
