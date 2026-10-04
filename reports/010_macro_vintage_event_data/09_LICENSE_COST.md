# 09 — Licence / cost (captured statements only; no legal conclusion)

Snippets archived in `bench/macro_vintage_v1/results/licence_snippets.json`, raw pages `raw/licence/`.
| Source | Cost class | Captured statement / fact |
|---|---|---|
| ALFRED keyless CSV | FREE_UNAUTHENTICATED (observed) | FRED legal FAQ: "FRED provides data and data services to the public for non-commercial, educational, and personal uses subject to a few prohibitions. Furthermore, other uses (e.g., commercial) are subject to additional restrictions." Some series carry third-party copyright. Terms also prohibit "an unreasonable amount of bandwidth". |
| FRED API | FREE_WITH_ACCOUNT | "All web service requests require an API key"; "All users of an application shall use their own API key." |
| BLS API | FREE_TIER (unregistered v1/v2 quotas; daily threshold observed) | terms page 403 to automated fetch → UNKNOWN |
| BEA | FREE_WITH_ACCOUNT | UserID sign-up form requires agreeing to terms of service |
| EIA | FREE_WITH_ACCOUNT (DEMO_KEY worked) | "EIA data is provided free of charge…"; "U.S. government publications are in the public domain" (with protected third-party materials exception) |
| NY Fed | FREE_UNAUTHENTICATED (observed) | terms page path returned "Page Not Found" → UNKNOWN |
| ECB | FREE_UNAUTHENTICATED (observed) | "Copyright © for the entire content of this website: European Central Bank" — reuse conditions on the page not captured → UNKNOWN |
| Eurostat | FREE_UNAUTHENTICATED (observed) | copyright URL 404 → UNKNOWN |
| BoE | FREE_UNAUTHENTICATED (curl) | legal page 403 → UNKNOWN |
| Bank of Canada | FREE_UNAUTHENTICATED | Terms of Use page reachable; conditions not extracted → UNKNOWN |
| Treasury FiscalData | FREE_UNAUTHENTICATED | "offered free, without restriction, and available to copy, adapt, redistribute, or otherwise use for non-commercial or commercial purposes" |
| CFTC | FREE_UNAUTHENTICATED | policy URL 404 → UNKNOWN |
| World Bank | FREE_UNAUTHENTICATED | "provided for informational and non-commercial purposes only, unless otherwise stated" (Terms of Use for datasets page) |
| IMF | FREE_UNAUTHENTICATED (datamapper) | terms page 403 → UNKNOWN |
| OECD | FREE_UNAUTHENTICATED | terms page 403 → UNKNOWN |
Note: statements are excerpts of pages read by regex; consult the full official text.
