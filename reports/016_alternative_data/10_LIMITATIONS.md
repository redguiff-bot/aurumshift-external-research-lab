# 10 — Limitations

> External research only — no private AurumShift code, no integration claims. Evidence tags: **[OBS]** observed in this study, **[DOC]** stated on a provider page/API response fetched in this study, **[INF]** inference, **[UNK]** unknown/not verified. Study date 2026-09-29 (sandbox clock). Reproduce with `bench/alternative_data_v1/`.


1. **Forking paths, disclosed.** (a) The first run lacked weekday dummies and 60-day vol memory; adding them after seeing 29/90 spurious hits is a data-driven baseline change (both runs are saved). (b) Real-economy returns were winsorised at 0.5/99.5 % *after* the raw-return EIA run gave OOS gain 0.89 % (DM p = 0.22) vs 2.50 % (p = 0.058) winsorised; both are saved (`results/real_economy_results_raw_returns.csv` vs `real_economy_results.csv`; in-sample t = −4.61 raw vs −5.32 winsorised) — treat the EIA OOS significance as borderline. (c) The economic-sign screen that dropped gas-storage/weather was applied post hoc. (d) Availability lags and the 0.40 reactivity threshold were fixed a priori but are judgemental.
2. **Daily resolution.** Everything is tested at daily bars; event-driven sources (EIA, CFTC, prediction markets, RSS) need intraday timestamps to judge executability.
3. **Sample.** ~2000 days per crypto asset (one bull-bear cycle); weekly series have 300–1000 points; HAC(5) may under-cover long-memory volatility (the 15 vs 4.7 expected p<0.05 count hints at mild over-rejection) — hence the OOS+FDR requirements.
4. **Baseline scope.** Funding/OI are Binance-USDT-M only; OI in contracts, not USD; no options/term-structure inputs in the baseline (DVOL therefore counts as "new").
5. **Only 2 assets, 3 targets;** no cross-sectional, no intraday, no transaction-cost or tradability test — *information* value only.
6. **Untested ≠ rejected.** GDELT, GH Archive, Kalshi/Polymarket, RSS/news/social, mempool state, ETF flows, weather forecasts, Google Trends are missing evidence, not negative evidence.
7. **Environment.** Shared-egress quotas (Open-Meteo, Wikimedia, GDELT DOC, Wayback, Kalshi) and geo-blocks (Binance fapi, Bybit) hide sources; probe statuses are single-day observations, not stability SLAs. `parsed_ok=True` in `probe_results.json` is unreliable for three placeholder extractors (AISHub, GIE AGSI, Etherscan V1 return auth errors) — the catalogue overrides them as not executed.
8. **Licence evidence** is keyword-grep of fetched pages; JS-rendered/403 pages are UNVERIFIED; nothing here is legal advice.
9. **Restatement measured only where stamps allowed** (Coin Metrics, Binance Vision, CFTC). DefiLlama/Blockchain.com/F&G/EIA restatement magnitude is UNKNOWN (Wayback blocked).
10. **Clock.** The sandbox clock (2026-09-29) and price levels are taken as given; no attempt was made to validate them against a second time source.
11. **No AurumShift code seen;** compatibility, overlap with existing inputs and operational fit are outside scope.
