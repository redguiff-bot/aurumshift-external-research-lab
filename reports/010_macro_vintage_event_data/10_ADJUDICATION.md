# 10 — Adjudication

## Questions from the mission
| Question | Answer | Status |
|---|---|---|
| Can historical vintages be retrieved keyless? | Yes, ALFRED, day granularity, 7 series | PROVEN |
| Does FRED CSV "today" leak the future? | Yes, 8/8 cases; 95-release statistics | PROVEN |
| Are `realtime_start/end` semantics proven? | No — API key absent | DOCUMENTED_CLAIM |
| Is release time-of-day available with values? | No source | PROVEN absence in tested feeds |
| Any official calendar with UTC timestamps? | BEA only | PROVEN |
| Non-US vintage sources? | OECD editions, World Bank archives (coarse, month) | PROVEN |
| Drop-in single source? | No | INFERENCE from above |

## Recommended reference stack (external research view, not integration)
1. Values as-of: ALFRED vintages (US) — check commercial terms first (FRED legal text above); FRED API with key for bulk/`output_type`.
2. Timing: BEA `release_dates.json` (executed); BLS/Fed/Census calendars need a fetch path that avoids the 403 (UNKNOWN).
3. Non-US: OECD `STES_REVISIONS` editions (month), World Bank archives (annual).
4. Forward capture (own receipt log) for ECB (`updatedAfter`), Eurostat (`updated`), NY Fed, EIA, CFTC.
5. Rule: before any release, use vintage D−1; the release-day vintage already holds the release.

## Prior-study reconciliation
Study 005 recorded FRED/ALFRED hosts as blocked by the egress proxy (5 attempts). In this run they were reachable (default UA). This supersedes 005's "not executed" on ALFRED; it does not contradict its conclusion that release-timestamped macro values are the weakest class (still true for time-of-day).

## Scientific invalidation check
No earlier claim in 005 is invalidated; one limitation supersession (above). Level-based revision numbers for INDPRO/GDPC1 are contaminated by rebasing — I report scale-free % changes instead (06). ANY_SCIENTIFIC_INVALIDATION = NO.

## FINAL BLOCK
```
SOURCES_DISCOVERED=16            (15 official priority sources + 1 non-official contrast)
SOURCES_EXECUTED=14              (13 official returned data [ALFRED, FRED CSV, EIA, NY Fed, ECB, Eurostat, BoE, BoC, Treasury, CFTC, World Bank, IMF, OECD]
                                  + BEA schedule; BLS one unarchived success; FRED API refused; TipRanks contrast excluded)
PIT_NATIVE_EXECUTED=3            (ALFRED, OECD STES_REVISIONS, World Bank WDI Archives)
PIT_ADAPTABLE_EXECUTED=8         (NY Fed, ECB, Eurostat, EIA, CFTC, Treasury, BoC, BoE)
FRED_EXECUTED=PARTIAL            (web CSV yes; official API keyless -> HTTP 400)
ALFRED_EXECUTED=YES
FRED_VINTAGE_SEMANTICS_PROVEN=NO (API realtime_* unexecuted; CSV proven latest-only)
ALFRED_VINTAGE_SEMANTICS_PROVEN=YES
RELEASE_TIMESTAMP_SOURCES=5      (time-of-day: BEA schedule, Eurostat dataset stamp [latest only], CFTC dataset stamp [latest only]; date/month only: ALFRED, World Bank/OECD editions)
REVISION_AWARE_SOURCES=3         (+2 flag-only: NY Fed revisionIndicator, ECB OBS_STATUS)
LOOKAHEAD_FROM_LATEST_VALUE_PROVEN=YES
DROP_IN_MACRO_SOURCE=NO
ANY_SCIENTIFIC_INVALIDATION=NO
FINAL_VERDICT=LIMITED_MACRO_PIT_SOURCES_SUPPORTED
```
