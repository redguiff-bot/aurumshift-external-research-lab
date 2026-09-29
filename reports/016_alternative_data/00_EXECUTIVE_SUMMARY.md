# 00 — Executive summary

Mission: `AURUMSHIFT_EXTERNAL_ALTERNATIVE_DATA_DISCOVERY_V1` — external research only; no private AurumShift code read; no integration proposed. Run clock: 2026-09-29 (UTC). Evidence labels per `claude.md`.

## What was done
* **39 sources catalogued** (2 paid-only, flagged not executed) in 16 mission categories; **29 executed** (live probes ×3 and/or history pulled, none with a key); the rest not executable without a key/account/payment or blocked from the test egress. Full attribute records (access, cost, history, latency, timestamp/revision semantics, PIT readiness, licence, coverage, rate limits, stability) in 01/06/08 and `bench/alternative_data_v1/results/source_records.*`.
* **44 feature series** built from executed sources (on-chain, mining/mempool, stablecoins, CFTC positioning, Treasury cash, GitHub activity, HN, Wikipedia, ship transits, EIA inventories, weather, Binance public positioning) and tested for incremental information over price/volume/volatility (+funding/OI for BTC) with a pre-registered walk-forward protocol (132 tests, Clark-West + Newey-West + BH-FDR).
* Leakage handled explicitly: conservative publication lags, a naive-lag comparison (06), and a re-fetch revision test.

## Findings
1. **No feature passed the gate: 0 incremental-information candidates.** 5 nominal p<0.05 tests vs ≈7 expected by chance; smallest BH q = 0.66. Most out-of-sample ΔR² are negative.
2. **Power is limited** (07): the test detects partial R² of ~3-4 % at 80 % power at a 1-day horizon, so the null excludes *large* effects only. Weekly series and GitHub (fragmentary data) are weaker still.
3. **9 series are price derivatives and rejected** (USD-denominated on-chain values, market-cap, DeFi TVL, Fear & Greed, long/short account ratio, taker buy/sell ratio). The diagnostic correctly ranks a pure price series at adj-R² 0.86.
4. **35 series are informationally distinct from price but unproven** (adj-R² mostly <0.15): raw hash rate/transactions, mempool, Treasury cash, CFTC positioning, ship transits, EIA inventories, HDD/CDD, HN. Being independent of price is necessary, not sufficient.
5. **PIT posture is weak:** only 9 of 39 sources are PIT_NATIVE for history (ledger/trade/filing/immutable-file timestamps); everything else is LOOKAHEAD_RISK for historical rows and at best PIT_ADAPTABLE via forward capture. Mempool state has **no free history at all**.
6. **Naive dating inflates statistics modestly:** dropping the publication lag raised abs(t) by >1 in 9 of 41 lagged features and nominally-significant tests go 4 → 6 (06). The effect is bounded because most features are unpredictive at either lag; lags used are assumptions, not observed publication times.
7. **Operational hazards found:** ClickHouse GH-events playground changed content between identical queries and has a 14-month hole; PortWatch ArcGIS pagination silently truncates; several endpoints 429/403 from shared egress; Open-Meteo archive is reanalysis (not PIT).

## Adjudication counts (09)
ADOPT 0 · ADAPT 11 · PARK 24 · REJECT 4. ADAPT = forward-capture candidates only.

## Verdict rationale
Zero candidates under a strict, pre-registered gate — but with power too low to conclude the sources are worthless, several categories (news, prediction markets, ETF flows, exchange reserves, mempool) untestable from free history, and almost all history LOOKAHEAD_RISK. The honest reading is **inconclusive**, with a concrete route to resolve it (forward vintage capture, multi-horizon/cross-asset re-test).

## Final block
```
SOURCES_DISCOVERED=39
SOURCES_EXECUTED=29
FREE_SOURCES=37 (free at point of use incl. 3 needing a free key/account and non-commercial-only terms; 29 executed, none with a key)

PIT_NATIVE=9
PIT_ADAPTABLE=23   # LOOKAHEAD_RISK for historical rows, PIT-usable via forward capture / release rule

INCREMENTAL_INFORMATION_CANDIDATES=0
PRICE_DERIVATIVE_ONLY_REJECTS=9

FINAL_VERDICT=STUDY_INCONCLUSIVE
```
