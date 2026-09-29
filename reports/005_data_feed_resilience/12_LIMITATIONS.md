# 12 — Limitations

1. **Single vantage point, single time window.** Everything ran from one cloud egress on 2026-09-29 (≈12:50–13:15 UTC), 240-minute bar window, re-fetches only 78 s and 362 s later. No multi-day stability, no overnight/weekend behaviour, no outage or maintenance-window sampling.
2. **Egress-blocked providers are unassessed, not rejected:** Binance main REST/WS/fapi (HTTP 451), Bybit (403), MEXC futures (403), FRED/ALFRED (connection closed by proxy ×5), Stooq, GDELT, IMF, BLS ICS, goldprice.org, metals.live, CryptoPanic. Cost/licence for these is UNKNOWN.
3. **Not executed:** keyed sources without a key (FRED, EIA, BEA, Coinalyze, CryptoCompare/CoinDesk, Polygon, Finnhub, FMP, OANDA); TipRanks connector (deliberately, to spare an account quota); CoinGecko MCP connector failed to connect; OECD query was my own malformed request.
4. **Rate-limit behaviour not stress-tested.** I stayed under documented limits; the egress cap (~1.5 req/s) prevented meaningful bursts. No provider 429 recovery/Retry-After semantics were measured on exchanges.
5. **Revision/late-arrival tests are short (≤6 min) and limited to closed 1-minute bars.** Funding/OI/options/macro revisions over days were not observed.
6. **Latency is proxy-inclusive** and WS latency uses the container clock against provider timestamps with no skew correction.
7. **Docs facts** (`docs_facts.json`) come from an automated official-page pass; several pages were 403/JS-only and are `NOT_FOUND`; some quotes are condensed or spliced from adjacent sentences; licence conclusions are not legal advice. Rate limits in `01` are DOCUMENTED_CLAIM, not measured, except where stated.
8. **Raw artifacts:** files >400 KB were truncated on capture and the truncated copies were deleted (Deribit/OKX option summaries, Kraken Futures funding, LBMA, SNB, Pink Sheet); derived statistics were computed from full live responses in the same scripts (`dv.py`, `fxgold.py`, `macro.py`), so the numbers stand but those raw bodies are not archived.
9. **Small samples for skew/basis:** options compared as marks (not executable quotes); skew (25Δ RR) not computed; basis test on Deribit only.
10. **Instrument mapping caveats:** perp bars compare different contract specs and quote currencies; volumes are not unit-normalised; USDT/USD basis unmodelled.
11. **US Treasury CSV** returned fewer rows than trading days (24 for 2026 YTD) — unexplained, not investigated.
12. **Simulation-era prices:** the observed prices (e.g. BTC ≈ 84 k, gold ≈ 4.15 k) are what the providers returned; no attempt was made to validate them against anything outside the providers.
13. No AurumShift code, schema or data was read; "gap classes" are the mission's stated list, so relevance to actual needs is INFERENCE.
