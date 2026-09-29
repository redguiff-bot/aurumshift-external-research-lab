# 06 — FINAL ADJUDICATION

Output type per `claude.md`: **ADOPT / ADAPT / PARK / REJECT candidates** for a later adjudication against the real local AurumShift repository. Nothing below claims compatibility with private AurumShift, and nothing designs or changes it. Evidence tags as in `00_SCOPE.md`; every verdict is an INFERENCE built on the tagged evidence in `02`–`05`.

## 1. Headline findings
1. **No candidate is a drop-in.** None combines automatic lease-based dead-worker reassignment, a native dependency graph and zero extra services (INFERENCE from `01`). The graph-capable systems (Temporal, Hatchet, Prefect, Airflow, Conductor, Argo) are the infrastructure-heavy ones; the light ones have no graph. The one native graph designed for coding agents (Beads) is not a runtime.
2. **Recovery is never free of glue.** Every recovering system needed something the operator owns: Absurd — a reconnect loop and an explicit retry strategy; Procrastinate — a periodic stalled-retry task and a process supervisor; DBOS — a stable executor id + pinned app version + supervisor (or the commercial Conductor); Restate — a restarted service endpoint; Beads — a timer running `bd reclaim`. (OBSERVED, `03`)
3. **At-least-once everywhere.** Duplicate side effects were observed in all four runtimes whenever a process was killed mid-step (`03`). Idempotency of agent side effects is the design obligation regardless of choice.
4. **Simplicity ≠ least intervention.** The heaviest artifact (Restate, 225 MB binary, second store) needed the fewest repairs in our runs; the simplest (Procrastinate) needed a DIY recovery task and supervisor to reach parity. (OBSERVED)
5. **Dependency evidence is a gap for every runtime.** Absurd/Procrastinate/DBOS/Restate express dependencies as code or hand-chained tasks; only Beads has a graph, with no structured evidence (INFERENCE from `02`). Whatever runtime is chosen, a dependency/evidence model stays "custom" under the REUSE→ADAPT→WRAP→COMPOSE→CUSTOM doctrine.

## 2. Verdicts
| Rank | Candidate | Verdict | One-line justification | Blocking conditions / what to verify against the real repo |
|---|---|---|---|---|
| 1 | **Absurd** | **ADAPT** | Only candidate where the whole mechanism (lease, reclaim, checkpoints, retries, events) is ~3k readable lines of SQL in the PG that is already authoritative; 0 interventions in kill/retry/cold-restart runs; PG 18.6 SDK tests 93/93 | Bus factor 1 + Alpha + young lease code → treat as *vendorable/forkable* (Apache-2.0), pin a version; wrap with reconnect loop and mandatory retry strategy; no DAG (custom tables); 4 SQL-suite failures on PG 18 need root-causing; claim_timeout vs long agent steps; reclaim needs a free polling worker; bloat under churn untested |
| 2 | **Procrastinate** | **ADAPT (conditional / fallback)** | Most mature simple PG queue (CI PG 14–18, MIT, SQL-queryable, clean graceful shutdown, good retry) | No checkpoints (restart from zero), stalled recovery is opt-in DIY (min cron granularity 1 min → ≈90 s worst, INFERENCE), worker exits on any DB blip, issue #1633 zombie-worker hazard, no DAG; only worthwhile if per-step durability is *not* required |
| 3 | **DBOS Transact** | **PARK** | Best embedded step-replay and survived PG outage without restart, but failover is the commercial Conductor's job | Takeover of a dead executor is not automatic in OSS (PROVEN); code change strands PENDING work (default version = source hash); pickled outputs opaque. Revisit only if a supervisor with stable executor ids is acceptable or Conductor licensing is |
| 4 | **Restate** | **PARK** | Best out-of-box crash tolerance (server kill -9 and service kill recovered, 0 repairs) | Second stateful authority (RocksDB) that cannot live in PG → conflicts with "one authoritative source per concern" / PostgreSQL-first unless a separate authority is acceptable; BSL 1.1 (internal use fine; SaaS-style use restricted); push-style HTTP workers, 1 m/10 m timeouts; 225 MB binary. Revisit if the PG-first constraint is relaxed |
| 5 | **Beads** | **REJECT as runtime / PARK as reference** | Native dependency graph, `ready`, atomic claim, fenced lease, cold-start state — the closest match on the *graph* requirement | Not a worker runtime (no retries, no auto-reclaim, TTL fixed 5 min); Dolt not PG; huge churn (1,558 commits/90 d, 59 corruption/data-loss fixes/90 d, 896 open issues); embedded mode has no SQL/doctor; serialised ≈0.6 s writes. Its dependency semantics may be useful as *reading material* |
| – | River (Go) | **PARK (UNKNOWN fit)** | Simplest automatic rescuer (30 s default, PROVEN in source), 6 tables, PG | Not run; language must fit; workflows are River Pro; MPL-2.0 |
| – | pgqueuer | **PARK** | Heartbeat requeue in source; ~12k LOC | Not run; 1 author; no graph |
| – | LangGraph | **REJECT as orchestrator** | Checkpointer only; no lease/heartbeat (PROVEN by absence) | Could still serve as an in-run agent graph library (not evaluated here) |
| – | Temporal, Hatchet, Inngest, Prefect, Conductor, Airflow/Dagster, Argo, Kestra, Windmill | **REJECT (on simplicity priority)** | Multi-service or cluster stacks; Inngest SSPL; Windmill AGPL | Rejection is on required infrastructure (DOCUMENTED_CLAIM + config reading), **not** on measured failure — none was run |
| – | Celery, Dramatiq, RQ | **REJECT** | Extra broker; visibility-timeout redelivery duplicates (DOCUMENTED_CLAIM) | – |
| – | DIY PG SKIP LOCKED lease table | **Reference pattern** | Absurd is effectively a tested instance of this pattern | Pitfalls (fetched PG docs): SKIP LOCKED gives an "inconsistent view"; fence by lease owner; use DB `now()`; bloat; cycles |

## 3. Recommendation shape (candidate level, not a design)
Under REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST, the evidence points to **COMPOSE**: an existing PG-native runtime (Absurd first; Procrastinate if step durability is unnecessary) + a *small custom* dependency/evidence layer, with idempotency for external side effects and an owned supervisor loop. This is a statement about the external landscape only. Whether it fits AurumShift (existing scheduler, language, PIT/provenance rules, PG 18.6 usage, event-driven intraday needs) can only be decided later against the real repository.

## 4. What would change these verdicts
- Absurd upstream gains a second maintainer, reaches beta, adds a reconnect helper/default retry strategy, or root-cause of the 4 PG 18 SQL failures shows a runtime bug → up or down accordingly.
- DBOS OSS ships in-library takeover of dead executors → upgrade to ADAPT.
- The PG-first constraint is relaxed → Restate becomes the lowest-intervention option.
- The real repository is Go → River jumps to first-class candidate (needs its own kill test).
- Long-run soak shows lease-table bloat or claim latency problems → all PG-queue options degrade together.

## 5. Confidence and honest limits
- Medium confidence in the ranking of 1–4; low confidence in relative timings (single runs, contaminated host twice, tiny scale, different dependency mechanism per system).
- Absurd's favourable result partly reflects that its experiment ran with lease 10 s and enough spare workers; the saturated case took 21.8 s and ≈52 s to finish (OBSERVED).
- Not verified: Docker-based upstream CI, closed-issue histories (API blocked), open-issue count for Restate, power-loss durability, multi-host behaviour, security posture, and all non-deep-dived candidates beyond source/docs reading.
- Claims by sub-agents were tagged at source; the lead re-verified four in code (Absurd lease/SKIP LOCKED, DBOS startup-only recovery, Procrastinate no auto stalled retry, Beads 5-min TTL).

STOP: no changes to private AurumShift were designed or implemented.
