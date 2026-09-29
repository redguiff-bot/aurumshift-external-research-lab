# 11 — Limitations

1. No FRED/BEA/BLS-v2/EIA keys: official FRED API, BEA API and BLS v2 were **not** executed. ALFRED evidence comes from the web CSV endpoint, which is not a documented contract and may change.
2. Single egress IP shared with other users: BLS anonymous quota and EIA DEMO_KEY were exhausted after one call each; results from those two are single-sample.
3. Vintage granularity: ALFRED = date; Philly Fed and OECD = month. No source tested gives the intraday release instant; scheduled time-of-day comes from separate calendars (only 2025-01 → 2026-12 in the BLS ICS, 2025 → early 2026 in BEA ICS fetched). Earlier history has no official machine-readable calendar in this study.
4. ALFRED vintage dates can differ from official release dates (PAYEMS vintage 2020-05-11, cause UNKNOWN). Alignment was verified on 3 BLS and 1 BEA series over 2025-2026 only.
5. ALFRED vintage depth varies by series; vintages before the first date are unavailable (404). Weekly EIA petroleum stocks are not on FRED.
6. Bulk ALFRED download (form POST) returned HTTP 500 for my requests; full "real-time period" files not tested.
7. Only 6 revision paths and 8 series × 2–4 dates were sampled; revision magnitudes are examples, not statistics. Level differences for chained-dollar/index series conflate revisions with re-basing (growth columns provided).
8. Non-US: ECB/Eurostat/BoE/BoC/IMF/World Bank revision histories were not found (World Bank archive source 57 could not be queried by my attempts; IMF WEO archive pages 403). The OECD revisions flow was tested for one US measure only.
9. Licence: several terms pages were 403/404 or yielded no sentence (marked UNKNOWN). No legal conclusions.
10. TipRanks was used as a labelled unofficial comparator through an MCP tool; its `time` timezone is inferred.
11. Raw OECD dataflow list (8.9 MB), BoC series list (3.6 MB) and the BLS flat file (attempt failed, IncompleteRead) were not kept in the repo.
