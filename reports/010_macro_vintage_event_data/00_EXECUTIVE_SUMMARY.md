# 00 — Executive summary (macro PIT / vintage / event data)

Status labels: PROVEN (executed here, raw archived) · OBSERVED · DOCUMENTED_CLAIM · INFERENCE · UNKNOWN.

## Headline
1. **ALFRED is reachable keyless and returns true vintages — PROVEN.** `alfredgraph.csv?id=S&vintage_date=T` returned
   the series *as it existed on T*. 7 series tested (GDPC1, GDP, PAYEMS, INDPRO, CPIAUCSL, UNRATE, DGS10 control); vintage
   counts 414–5118 per series. E.g. PAYEMS Apr-2020: 131072 (2020-05-08) → 131045 (05-11) → 130403 (06-05) → 130303 (07-02) → … → 130426 today.
2. **FRED web CSV (`fredgraph.csv`) is latest-value only — PROVEN.** `vintage_date=` and `realtime_start/end=` were
   silently ignored (3 byte-identical responses, same sha256). Using it for history creates lookahead.
3. **The official FRED API (`api.stlouisfed.org`) was NOT executed with a key** (no key in env; keyless → HTTP 400).
   Its `realtime_start/realtime_end` semantics are DOCUMENTED_CLAIM only. ALFRED's own endpoint is what proved vintage semantics.
4. **Lookahead from latest-value data is PROVEN and material**: over 95 first releases (2018-01 → 2025-12) every PAYEMS,
   INDPRO and CPIAUCSL first print differs from today's value; INDPRO's MoM-% change differs from first print by a median
   0.25 pp (max 1.94 pp) and flips sign in 16/95 releases; PAYEMS flips sign in 3/95 (e.g. Aug-2025 first print +22k,
   latest −70k), CPI 6/95.
5. **Other vintage-native sources found & executed**: OECD `DSD_STES_REVISIONS` (dimension `EDITION` = monthly vintage,
   89 editions 2019-05…2026-09 for USA 2019 quarterly data) and World Bank *WDI Database Archives* (source 57, `Version` YYYYMM; USA GDP 2015 differs across versions).
6. **Release time-of-day**: only the *schedule* side has it — BEA `release_dates.json` gives UTC timestamps (12:30/13:30Z = 08:30 ET);
   19/19 past BEA GDP dates equal ALFRED's GDP release dates. ALFRED vintages are **date-granular** (a vintage dated the release day already
   contains the release-day value): intraday RELEASE_TIME stays UNKNOWN in the value feed. No source gave actual+revision+timestamp in one keyless feed.
7. **Not a drop-in**: the value feed (ALFRED) and the timestamp feed (BEA/BLS calendars) are separate; BLS calendar 403 and BLS API quota-throttled;
   EIA/BEA APIs need registration; FRED terms restrict commercial use ("other uses (e.g., commercial) are subject to additional restrictions" — verbatim, no legal conclusion).

## Verdict: LIMITED_MACRO_PIT_SOURCES_SUPPORTED
Daily-granularity US vintage reconstruction is supported by executed evidence; non-US and intraday timing are not.
See `10_ADJUDICATION.md`, `11_LIMITATIONS.md`.

## FINAL BLOCK
See end of `10_ADJUDICATION.md` (and the PR body).
