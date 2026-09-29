# 09 — Licence / cost (verbatim facts, no legal conclusion)

Fetched 2026-09-29 (`results/licence_facts.json`, raw pages `raw/lic_*`).

| Source | Cost class | Captured official statement / fact |
|---|---|---|
| FRED web CSV | FREE_UNAUTHENTICATED (observed) | FRED legal page: "You can do a lot of things with FRED data … for your own personal, non-commercial use". Third-party series may carry copyright notices |
| FRED API | FREE_WITH_ACCOUNT (key; DOCUMENTED, key not obtained) | API terms: "Data series available through the FRED® API, may be owned by third parties and subject to copyright restrictions." |
| ALFRED web CSV | FREE_UNAUTHENTICATED (observed); ALFRED-specific terms not separately captured → UNKNOWN | same St. Louis Fed terms family (INFERENCE) |
| BLS | FREE_UNAUTHENTICATED (v1, small quota) / FREE_WITH_ACCOUNT (v2 key) | "You are free to use our public domain material without specific permission, although we do ask that you cite the Bureau of Labor Statistics as the source." Anonymous quota was exhausted after 1 call from the shared egress |
| BEA | FREE_WITH_ACCOUNT | registration form requires agreeing to Terms of Service; not executed |
| EIA | FREE_WITH_ACCOUNT / DEMO_KEY (rate-limited immediately) | "U.S. government publications are in the public domain"; API "you must use the unique API key … free key" |
| NY Fed | FREE_UNAUTHENTICATED; terms page returned no extractable sentence → UNKNOWN | – |
| ECB | FREE_UNAUTHENTICATED | "users … may make free use of the information … When such information is distributed or reproduced, it must appear accurately and the ECB must be cited" |
| Eurostat | FREE_UNAUTHENTICATED; copyright URL 404 → licence UNKNOWN | – |
| Bank of England | FREE_UNAUTHENTICATED | "The Bank typically grants permission for non-commercial re-use of the Resources"; third-party (e.g. LSEG) material separate |
| Bank of Canada | FREE_UNAUTHENTICATED | permits free use/copy/distribute "under the following terms" incl. accuracy due diligence; exceptions listed |
| US Treasury FiscalData | FREE_UNAUTHENTICATED | "The data is offered free, without restriction, and available to copy, adapt, redistribute, or otherwise use for non-commercial or commercial purposes." |
| CFTC | FREE_UNAUTHENTICATED; terms page 404 → UNKNOWN | – |
| World Bank | FREE_UNAUTHENTICATED; the page fetched is the site terms ("informational and non-commercial purposes only, unless otherwise stated"); dataset licence not captured → UNKNOWN | – |
| IMF | FREE_UNAUTHENTICATED; terms page 403 → UNKNOWN | – |
| OECD | FREE_UNAUTHENTICATED; terms page 403 → UNKNOWN | – |
| Philadelphia Fed RTDSM | FREE_UNAUTHENTICATED | page: "may be used by macroeconomic researchers to verify empirical results, to analyze policy, or to forecast"; citation requested |
| TipRanks | via MCP account | terms not captured → UNKNOWN |

No PAID_ONLY source was needed for any result in this study.
