# macro_vintage_v1 — external point-in-time macro data tests

External research only; no AurumShift code. All numbers below come from HTTP calls made on 2026-09-29
from the research container. Raw responses: `raw/` (receipt log: `raw/_receipts.jsonl`, one JSON line per call,
`receipt_time_utc` = local clock at response end). Derived results: `results/`.

Run order (Python 3.11 + requests; results are cached in `raw/`, delete a file to re-fetch):
1. `py/probe_sources.py`      keyless reachability/semantics of all priority sources
2. `py/alfred_vintage.py`     ALFRED vintage retrieval + revision paths (7 series)
3. `py/lookahead.py`, `py/lookahead_scalefree.py`   latest-value vs first-print lookahead statistics
4. `py/asof_vs_today.py`      FRED "today" vs ALFRED as-of-T
5. `py/probe_semantics.py`    World Bank archives, OECD editions, ECB/Eurostat/NYFed/CFTC flags
6. `py/licence_capture.py`    official terms pages (snippets only; no legal conclusion)

Environment notes: FRED/ALFRED/IMF stalled or 403'd a custom User-Agent; the default requests UA works
(`common.py`). Bank of England returns Akamai 403 to python-requests but 200 to curl (`raw/boe_curl.csv`).
BLS unregistered API returned "daily threshold reached" (shared egress IP) for all later calls; its one earlier
success was seen only in tool output and is NOT archived. `results/notes/receipts_custom_UA_run.jsonl` is the
failed first run (kept as evidence). `raw/tipranks_calendar_sample.json` is a NON-OFFICIAL aggregator sample.

Trimmed for size (re-fetch via probe scripts; sha256 in receipts): oecd_dataflows.xml (8.5 MB), boc_lists.json (3.5 MB), oecd_rev_struct.xml (1.9 MB).
