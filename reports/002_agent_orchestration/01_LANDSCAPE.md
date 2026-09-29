# 01 — LANDSCAPE (23 candidates/architectures)

Activity numbers are OBSERVED from local `git log` (90 days ending 2026-09-29) for cloned repos; others UNKNOWN unless a page was fetched. "Ops" = operational burden 1 (a library + your DB) … 5 (cluster platform); it is our INFERENCE from required services unless marked.

| # | Candidate | Type | Services required for a real deployment | Durable store | Lease / retry | Dependency graph | License | Activity (90d commits / authors) | Ops | Screen verdict | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Absurd** | PG-native durable execution (SQL functions + SDKs) | Postgres only; you run workers | PG (5 tables/queue) | lease `claim_timeout`, per-step checkpoints, retry strategies | none native (child task + events) | Apache-2.0 | 6 / 1 (last 2026-08-04) | 1–2 | **Deep-dive** | PROVEN/OBSERVED |
| 2 | **DBOS Transact (Py)** | library durable workflows | Postgres (or SQLite); no server | PG/SQLite | executor_id ownership, startup recovery, step retries; no lease | child workflows in code | MIT (Conductor/Cloud commercial) | 81 / 7 | 1–2 | **Deep-dive** | PROVEN/OBSERVED |
| 3 | **Procrastinate** | Python PG task queue | Postgres; workers | PG (4 tables) | SKIP LOCKED, heartbeat, stalled detection (opt-in retry), RetryStrategy | none (locks, defer-from-task) | MIT | 97 / 6 | 1–2 | **Deep-dive** | PROVEN/OBSERVED |
| 4 | **Restate** | durable-execution server | 1 Rust binary (embedded log+RocksDB) + your HTTP service endpoints | embedded | server-pushed invocations, journal replay, retry policy | code-level | BSL 1.1 (SDK MIT) | 293 / 22 | 2 | **Deep-dive** | PROVEN/OBSERVED |
| 5 | **Beads (bd)** | git/Dolt task graph for agents | none in embedded mode (Dolt embedded) | Dolt | claim CAS + 5-min lease, manual `bd reclaim`; no retry | **yes** (~19 dep types) | MIT | 1558 / 116 | 1 (but churn) | **Deep-dive** | PROVEN/OBSERVED |
| 6 | Temporal | workflow engine | server (several services) + Cassandra/MySQL/PG/SQLite (+ES optional) | event history in DB | heartbeat/timeouts, retry policies | via code (child workflows) | MIT | 538 / 63 | 4 | Powerful; heavy; determinism constraint | PROVEN(files)/INFERENCE |
| 7 | River | Go job library | Postgres | PG (6 tables) | SKIP LOCKED; leader-elected rescuer (30 s default) | none in OSS (Pro workflows) | MPL-2.0 | 85 / 9 | 1 | Simplest robust queue, Go-only, no DAG | PROVEN(files) |
| 8 | Hatchet | task queue + DAG platform | engine + Postgres (+RabbitMQ default MQ; PG mq option) | PG | timeouts/retries/reassign | yes | MIT | 470 / 20 | 3 | Feature-rich; bigger than need | PROVEN(config)/DOCUMENTED_CLAIM |
| 9 | Inngest | event-driven step functions | server + Redis + DB | Redis + DB | leases (4 s partition, 2 m connect) | in code | **SSPL** + Apache-2.0 future license (3 y) ; SDK Apache-2.0 | 286 / 22 | 3–4 | License + HTTP-callback model unfit | PROVEN(license, consts) |
| 10 | LangGraph | agent graph library | none (PG/SQLite checkpointer) | PG/SQLite checkpoints (4 tables) | **none** for crash detection | in-run graph only | MIT | 113 / 17 | 1, but not an orchestrator | Not an orchestrator | PROVEN by absence |
| 11 | pgqueuer | Python PG queue | Postgres | PG | SKIP LOCKED + heartbeat requeue | none | MIT | 124 / **1** | 1 | Simple; bus factor 1 | PROVEN |
| 12 | Prefect | flow orchestrator | API server + DB + workers | DB | worker/run heartbeats, automations | yes | Apache-2.0 | 398 / 54 | 3 | Heavy for this use | OBSERVED/DOCUMENTED_CLAIM |
| 13 | Celery | task queue | Redis or RabbitMQ (+result backend) | broker (not durable history) | acks_late; Redis visibility-timeout redelivery | canvas | BSD (recall) | UNKNOWN | 2–3 | Extra broker; duplicate risk | DOCUMENTED_CLAIM (fetched docs) |
| 14 | Dramatiq | task queue | RabbitMQ/Redis | broker | retry middleware | pipelines | LGPL (fetched) | UNKNOWN | 2 | Broker again | DOCUMENTED_CLAIM |
| 15 | RQ / Huey | task queue | Redis (Huey: also SQLite/file) | Redis/SQLite | timeouts/registries | minimal | BSD / MIT (recall) | UNKNOWN | 2 / 1 | Huey-SQLite fine on one host | UNKNOWN (recall) |
| 16 | Airflow / Dagster | data orchestrators | metadata DB + scheduler + web (+workers) | PG | task heartbeats/retries | yes (core) | Apache-2.0 (recall) | UNKNOWN | 4–5 | Wrong shape, heavy | UNKNOWN (recall) |
| 17 | Conductor OSS / Orkes | JSON workflow engine | server + DB (Redis/PG/…) + ES/OpenSearch | DB | task timeouts/retries | yes | Apache-2.0 | active | 4 | Heavy JVM stack | DOCUMENTED_CLAIM (fetched) |
| 18 | Argo Workflows | k8s workflow CRDs | Kubernetes | etcd/CRD | pod retry strategies | yes | Apache-2.0 (recall) | UNKNOWN | 5 | Only if already on k8s | UNKNOWN (recall) |
| 19 | Windmill | scripts/flows platform | server + workers + Postgres | PG | job queue in PG, retries | flows | AGPLv3 + proprietary EE | active | 3 | Platform; AGPL | DOCUMENTED_CLAIM (fetched) |
| 20 | Kestra | YAML orchestrator | JVM + DB | DB | – | yes | Apache-2.0 (EE paid) (recall) | UNKNOWN | 3–4 | Not examined | UNKNOWN |
| 21 | DIY PG lease table | pattern | Postgres | PG | as designed | own tables | n/a | n/a | 1 + you own bugs | Viable (~100–300 lines); see pitfalls | INFERENCE + fetched PG docs |
| 22 | SQLite-file queue | pattern | none | file | `BEGIN IMMEDIATE` claim | own | n/a | n/a | 1 | Single host only | INFERENCE |
| 23 | git/markdown/flock boards | pattern | none/git | files | mkdir/flock | ad hoc | n/a | n/a | 1 | Fragile under concurrency | INFERENCE |

## Rough non-test size of cloned candidates (OBSERVED, crude `wc`, may include generated code)
Temporal ~360k Go · Hatchet ~237k Go · Prefect ~203k Py · Inngest ~179k Go · River ~45k Go · LangGraph ~44k Py · pgqueuer ~12k Py. Deep-dived: Absurd 3150-line SQL + 2317-line Py SDK · DBOS ~32.7k Py · Procrastinate ~8.1k Py+SQL · Restate ~283k Rust (984 crates in Cargo.lock) · Beads ~371k Go.

## Screening logic (why 5 went deep)
- Rejected early on infrastructure weight (INFERENCE from documented required services): Temporal, Hatchet, Inngest (also SSPL), Prefect, Conductor, Airflow/Dagster, Argo, Kestra, Windmill (AGPL), Celery/Dramatiq/RQ (extra broker + redelivery duplicates).
- Not an orchestrator: LangGraph (no lease/heartbeat table; nothing detects a dead run — PROVEN by absence in checkpoint-postgres).
- Simple Postgres queues, no durable steps/DAG: River, pgqueuer, Procrastinate. Only Procrastinate was deep-dived (Python, largest maintainer base of the three in Python, CI on PG 14–18).
- Deep-dived because they cover the durable-state / recovery / continuation requirements with ≤1 extra service: Absurd, DBOS, Procrastinate, Restate; plus Beads because it is the only candidate with a native dependency graph designed for coding agents.

## Landscape-level findings
- **F1 (INFERENCE from table):** no candidate found combines *lease-based automatic dead-worker reassignment* + *native dependency graph* + *zero additional services*. Graph-capable systems (Temporal, Hatchet, Prefect, Airflow, Conductor, Argo) are the heavy ones; the light ones have no graph.
- **F2:** everything that recovers work is at-least-once; none gives exactly-once for user side effects (see `04`).
- **F3:** three licenses need care: Inngest (SSPL), Restate server (BSL 1.1, internal use allowed), Windmill (AGPL). DBOS's automatic multi-executor recovery is a commercial control plane.
