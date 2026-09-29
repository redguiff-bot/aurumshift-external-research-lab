# 10 — Limitations

1. **Low power** (see 07): minimum detectable partial R² ≈ 3-4 % at n≈1,000; weekly features far weaker. The null result is weak evidence.
2. **One design only:** next-day linear OLS, one fixed transform (weekly change, trailing z-score), conservative lags chosen a priori. Regime effects, non-linearities, multi-day horizons, intraday timing and event studies were not examined.
3. **Baseline asymmetry:** funding/OI in the baseline for BTC only. Commodity baselines are price/volume/vol only (their derivatives data do not exist in this study); Yahoo continuous futures are unofficial and unadjusted (roll jumps winsorised).
4. **Historical rows are LOOKAHEAD_RISK** for almost every tested series: lags are assumptions (aggregates +2 d, CFTC +6 d, EIA/weather +7 d, PortWatch +10 d), not observed publication times. A lag that is too short leaks; too long loses power.
5. **Not tested (missing evidence, not negative):** news/GDELT bulk, RSS, prediction markets, ETF flows (blocked/no history), exchange reserves, options/vol surfaces beyond report 005, EDGAR filings, GDELT tone, Google Trends, mempool state, GH Archive files directly.
6. **Egress effects:** GitHub REST blocked by session scope policy (403); Reddit 403; Farside Cloudflare 403; SEC needed declared UA; Wikipedia/GDELT/Open-Meteo hist-forecast rate-limited (429) from a shared IP; FRED closed by proxy earlier (report 005). These are egress outcomes, not provider verdicts.
7. **Data instability:** the ClickHouse playground changed between identical queries (see 02); GitHub-based tests use fragmentary coverage (~260-490 days). Fetched data are single-time snapshots at 2026-09-29 (test-egress clock); re-running later can give different numbers (history recomputation, table rebuilds).
8. **Multiple testing:** 132 tests, BH q=0.10; the 'best target' columns in report tables are selected by min p and must not be read as effect estimates.
9. **Licence review** is documentary and not legal advice.
10. **Stability sample** = 3 calls per endpoint within ~10 s; it says nothing about outages, deprecations or throttling under load.
11. No CoinGecko/TipRanks connectors were used (unavailable in the session); no paid or keyed data were used.
