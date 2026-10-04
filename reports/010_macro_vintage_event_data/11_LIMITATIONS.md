# 11 — Limitations

1. **FRED API never executed with a key.** All FRED-family vintage proof comes from ALFRED's graph-CSV endpoint (a website download route; its stability/ToS for programmatic use is UNKNOWN).
2. **Date granularity.** ALFRED vintage = day; intraday release time unknown. Vintage D includes release-day values.
3. **BLS**: API shared-IP daily threshold; single early success not archived; schedule pages 403. BLS data therefore not tested for revisions (ALFRED covers BLS-origin series PAYEMS/UNRATE/CPI).
4. **BEA/EIA official value APIs** not tested with registered keys (EIA only DEMO_KEY, latest data).
5. **IMF WEO vintages not reached** (guessed file URLs failed; may exist elsewhere). **BoE** blocked for python-requests (curl ok). **OECD** result covers USA quarterly 2019 only.
6. **Small samples**: 7 ALFRED series; 3–4 chosen revision examples per series (chosen for known revision activity → not a random sample; the 95-release table is systematic). Weekly oil (`WCESTUS1`) not tested.
7. **Rebasing**: INDPRO/GDPC1 level comparisons mix revision with re-referencing; scale-free metrics used for statistics.
8. **Bisection** for first-appearance assumes monotone appearance.
9. **ALFRED bulk POST download failed (HTTP 500)** — likely my form encoding; a fully-automated bulk fetch is unproven.
10. **Licence**: excerpts by regex; several terms pages 403/404 → UNKNOWN. No legal conclusion.
11. **Custom User-Agent stall** on FRED/ALFRED/IMF (OBSERVED) — access can depend on client identity; may change.
12. Environment: single egress IP, one day (2026-09-29); results may differ elsewhere/later. TipRanks sample is non-official and only 3 rows retained.
13. Raw cache: 23 MB in `raw/` (OECD dataflow list 8.9 MB, BoC list 3.6 MB, ALFRED snapshots).
