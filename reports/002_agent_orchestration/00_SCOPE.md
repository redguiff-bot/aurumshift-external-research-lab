# 00 — SCOPE

Mission: `EXTERNAL_RESEARCH_AGENT_ORCHESTRATION_SIMPLIFICATION_V1`
Date of research: 2026-09-29. Research-only. This lab never saw the private AurumShift code; nothing here claims compatibility with it (see `claude.md`, "Important boundary").

## Question
Which open-source orchestration/runtime systems can run **long-running coding/research agents** with: task leases, retries, worker/reviewer workflows, durable state, crash recovery, dependency evidence, cross-session continuation and low operator intervention — with **operational simplicity as the first criterion**.

Penalised explicitly: infrastructure-heavy stacks, weeks of tuning, opaque distributed architectures, unnecessary brokers/databases/services.

## Evidence tags (used everywhere)
| Tag | Meaning here |
|---|---|
| PROVEN | Verified by reading source (file:line given) or by a test that was executed and whose result is in `experiments/` |
| OBSERVED | Seen in a run, an output, `git log`, a web page fetched during this session |
| DOCUMENTED_CLAIM | Stated in README/docs; not verified by us |
| INFERENCE | Our reasoning from the above |
| UNKNOWN | Could not be established |

## Method
1. 12 repos cloned (blobless, full history) into a scratch dir: absurd, beads, dbos-transact-py, hatchet, inngest, langgraph, pgqueuer, prefect, procrastinate, restate, river, temporal. License, last commit, 90-day commits/authors, tags computed from `git log` (OBSERVED).
2. 23 candidates/architectures screened (`01_LANDSCAPE.md`).
3. Top 5 inspected in depth by reading source, tests, issues (`02_TOP5.md`).
4. Top 3 (+ 2 more where feasible) exercised in a crash/retry/recovery experiment (`03_REPRODUCTION.md`).
5. Failure modes, operational cost, adjudication: `04`–`06`.

The top-5 selection is a **judgement** made from the landscape screen (simplicity first, then coverage of the requirements). River (Go) and pgqueuer were strong simple candidates that were **not** deep-dived; see `06`.

## Environment and its limits (read before trusting any number)
- Cloud sandbox, 4 vCPU / 15 GB, no Docker daemon, no IPv6. Outbound HTTPS via proxy; `api.github.com` was **blocked** for out-of-scope repos, so open-issue counts come from WebFetch of GitHub HTML pages where it worked, else UNKNOWN.
- **PostgreSQL 18.6** (user's stated production version) was obtained by extracting the pgdg `postgresql-18` .deb into a private prefix (OBSERVED: `select version()` = 18.6). All PG experiments ran on it. The system PG16 was only a client.
- Six agents worked in parallel on the same host. **Cross-contamination happened**: one agent's `pkill -9 -u lab postgres` killed another agent's PG cluster at least twice (Absurd before scenario C; Procrastinate in one scenario-B run). Affected runs were rerun or flagged; logs keep the aborted runs. Treat all timings as single-run, non-benchmark.
- Scale is tiny: 20 tasks, ~3 s of work each, 4–5 in flight. This measures **semantics** (does it recover, how many duplicates, what does the operator do), not throughput or long-run stability.
- Tested versions differ from clone HEAD in places: Procrastinate PyPI 3.10.0 (clone tag 3.9.0); Restate server npm 1.7.12 (HEAD 1.8.0-dev); Beads built from HEAD e7138e93 with `-tags gms_pure_go` (default CGO build failed on missing ICU headers); DBOS 3.1.0; absurd-sdk 0.5.0.
- Only SIGKILL / immediate PG stop were simulated. No power loss, disk-full, network partition, clock skew, multi-host.
- The lead reviewed sub-agent reports and spot-checked four key claims in source (Absurd lease/SKIP LOCKED, DBOS startup-only recovery, Procrastinate no auto stalled retry, Beads 5-min hardcoded lease TTL): all matched. Other claims are the sub-agents' tagged findings, not independently re-derived.

## Out of scope
Designing or implementing anything in private AurumShift. Throughput benchmarks. Security review. Cost of LLM calls.
