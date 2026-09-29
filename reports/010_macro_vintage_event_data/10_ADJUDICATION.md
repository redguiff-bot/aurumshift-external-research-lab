# 10 — Adjudication (no synthetic ranking)

| Component | Decision | Why |
|---|---|---|
| ALFRED as-of retrieval (web CSV) | **ADOPT_REFERENCE (US, day granularity)** with ADAPT wrapper | Proven as-of semantics, 20+11 release dates aligned, initial values match BLS archive and Philly Fed. Needs one-call-per-vintage loop, guards for silent failures (future date, ignored params), and a decision on the undocumented endpoint vs keyed API |
| FRED API with `realtime_*` | PARK (needs key, untested) | Do not claim semantics; obtain key and re-run `alfred_test.py` equivalents |
| `fredgraph.csv` | REJECT for history | ignores `vintage_date` → silent look-ahead |
| Philadelphia Fed RTDSM | ADOPT_REFERENCE as independent cross-check | monthly vintages, exact agreement with ALFRED on GDP |
| OECD STES revisions | ADAPT_CANDIDATE | vintage-aware, monthly editions, non-US coverage; only one measure family tested |
| BLS ICS + BEA ICS | ADOPT_REFERENCE for scheduled RELEASE_TIME | machine-readable, 100% date agreement with ALFRED on tested series |
| BLS API | PARK | latest-only; anonymous quota exhausted immediately from shared egress; key needed |
| CFTC Socrata | ADAPT_CANDIDATE (forward capture only) | `:created_at` valid only after 2022-09 migration |
| NY Fed, ECB, Eurostat, Treasury | ADAPT_CANDIDATE (forward capture with own receipt stamp) | flags/stamps but no history |
| BoE, BoC, EIA, FiscalData, World Bank, IMF DataMapper | PARK for PIT use | latest-only |
| TipRanks calendar | PARK / not a PIT source | unofficial, no ids/vintages |

Scientific-invalidation check: none of the earlier premises is invalidated. The earlier claim "ALFRED PIT-native = DOCUMENTED_CLAIM" is now upgraded to PROVEN for the web-CSV path. Not invalidated but refined: FRED (latest) is *not* PIT-usable.
