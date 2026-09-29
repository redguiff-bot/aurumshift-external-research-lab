# 00 — Executive summary: free/public alternative-data discovery (mission AURUMSHIFT_EXTERNAL_ALTERNATIVE_DATA_DISCOVERY_V1)

> External research only — no private AurumShift code, no integration claims. Evidence tags: **[OBS]** observed in this study, **[DOC]** stated on a provider page/API response fetched in this study, **[INF]** inference, **[UNK]** unknown/not verified. Study date 2026-09-29 (sandbox clock). Reproduce with `bench/alternative_data_v1/`.


## Verdict
**LIMITED_ALTERNATIVE_DATA_SUPPORTED.** Of 69 sources catalogued in 16 categories (47 actually executed, 62 with a zero-cost route), only **two** cleared the pre-declared incremental-information bar, and they are very different animals:

| candidate | what it is | evidence | PIT status |
|---|---|---|---|
| **EIA weekly US crude-inventory surprise** (vs 5-yr seasonal norm) → WTI/Brent release-day return | physical-economy datum, independent of price (past-price R² = 0.028) | HAC t = -5.32, q<0.001, OOS MSE gain 2.50% (one-sided DM p = 0.058); Brent replicates (t = -6.03); placebo offsets null except Tuesday (API report day-before, p = 0.038); **effect fades after 2021 (p = 0.27)** | LOOKAHEAD_RISK (bulk files have no vintages); PIT_ADAPTABLE only by forward capture on the release clock |
| **Deribit DVOL** (BTC options-implied vol) → next-day log range | information from a *second market* (options), not spot price/volume/realised vol/funding/OI | HAC p < 0.001, OOS MSE gain 2.29% (DM p = 0.005) | PIT_NATIVE (immutable index prints); market-derived, not "alternative" in the non-market sense |

Everything else that was testable (21 crypto/public-liquidity/attention feature blocks × BTC/ETH × 3 targets, plus gas storage, weather, shipping) **failed** to add information beyond the price/volume/volatility/funding/OI baseline once calendar effects were controlled. 12 blocks are classified PRICE_DERIVATIVE_ONLY (react to, or are absorbed by, the baseline); 9 are independent of price but showed no predictive evidence (this is **not** negative evidence — missing evidence is not negative evidence).

## The four findings that matter
1. **Calendar artefacts fake alternative-data alpha.** A first-pass baseline without weekday dummies gave 29/90 in-sample p<0.05 blocks and 8 OOS-significant ones (npm download counts "improved" next-day range by 1.9–3.6 %, DM p ≤ 0.027). Adding 6 weekday dummies and a 60-day vol memory to the baseline removed **all** of them (min BH-q across the family excluding DVOL = 0.26; expected p<0.05 under the null ≈ 4.7, observed 15 in-sample, none OOS-confirmed). 12 pure-noise blocks: 0 with p<0.05.
2. **"Free history" is mostly restated history.** Coin Metrics community: 2067/2219 sampled rows were recomputed in 2026-04 (2,024 of them >30 d after their completion stamp); Binance Vision `metrics` files: 33/40 sampled old files re-uploaded (median 371 d after their day); CFTC Socrata: 231/442 Bitcoin rows carry a single bulk-load stamp (2022-09-13); EIA/Treasury/NY Fed/PortWatch/npm/Wikimedia/DefiLlama/Fear&Greed: no vintages at all → all classified **LOOKAHEAD_RISK** for history per mission rule.
3. **The genuinely PIT-native free sources are not the ones people reach for:** GDELT 15-min files (Last-Modified 4.5–10.1 min before the file stamp, 7/7 samples 2016–2026), GH Archive hourly files (Last-Modified +5.1 min after hour end), Kalshi/Polymarket price history, SEC EDGAR `acceptanceDateTime`, NOAA GFS run files, Deribit index bars. Most are **untested** for information value here (bandwidth/power/time), so they remain open, not rejected.
4. **Several whole categories cannot be tested from free sources today:** ETF flows (iShares returns an HTML shell, Farside is behind a Cloudflare challenge, EDGAR has only periodic filings), Google Trends (no official API), news/RSS/social/mempool (feeds keep hours–days of items; no history → forward capture only), weather forecasts (Open-Meteo daily quota exhausted by the shared egress IP).

## What would change the verdict
* Upgrade to MULTIPLE_… would need ≥1 more PIT-clean, price-independent source with a confirmed OOS gain — the best untested leads are (a) GDELT GKG theme volume/tone, (b) Kalshi/Polymarket macro-event probabilities, (c) mempool/fee state captured forward for ≥12 months, (d) Open-Meteo *historical-forecast* (as-issued forecasts) vs Henry Hub.
* Downgrade would follow if the EIA crude effect is shown to be fully absorbed intraday before any executable timestamp (the post-2021 fade already hints at this).

## Counts (final block)
```
SOURCES_DISCOVERED=69
SOURCES_EXECUTED=47
FREE_SOURCES=62   # zero-cost route (no key: 54; free key required: 8); executed & free: 47

PIT_NATIVE=7   # executed sources; +1 documented but unreachable (FRED/ALFRED)
PIT_ADAPTABLE=6   # executed sources
LOOKAHEAD_RISK=17   # executed sources (historical rows without publication timestamps)
SNAPSHOT_ONLY=17   # executed sources with no history to replay (forward capture only)

INCREMENTAL_INFORMATION_CANDIDATES=2   # EIA weekly crude-inventory surprise (real economy); Deribit DVOL (options-implied vol, market-derived)
PRICE_DERIVATIVE_ONLY_REJECTS=12   # feature blocks (excludes 2 built-in controls); across 7 sources — see 07

FINAL_VERDICT=LIMITED_ALTERNATIVE_DATA_SUPPORTED
```

See `01_SOURCE_LANDSCAPE.md` (all sources), `06_PIT_READINESS.md` (leakage), `07_INCREMENTAL_INFORMATION.md` (tests), `09_ADJUDICATION.md` (ADOPT/ADAPT/PARK/REJECT), `10_LIMITATIONS.md`.
