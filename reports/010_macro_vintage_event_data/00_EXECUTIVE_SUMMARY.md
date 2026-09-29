# 00 — Executive summary

Mission `AURUMSHIFT_EXTERNAL_MACRO_VINTAGE_AND_EVENT_DATA_V1` — external research only; no private AurumShift code, no integration. Run 2026-09-29 (UTC). All numbers below are OBSERVED from live calls stored in `bench/macro_vintage_v1/`.

## Findings
1. **The blocked item from the prior study is unblocked, partially.** ALFRED answered keylessly through its web CSV endpoint and **proved as-of vintage semantics** (418–1223 vintage dates per series; value at T = last vintage ≤ T; 404 before first vintage). The keyed FRED API was **not** executed (no key), and `fredgraph.csv` (latest FRED) **ignores** `vintage_date`.
2. **Look-ahead from latest-value data is proven** with real cases: payrolls Dec-2008 known 135,489 (−524k, matching the BLS archived release) vs 134,847 today; real GDP 2008:Q4 growth −0.96% at first print vs −2.19% today; industrial production Dec-2008 −2.00% vs −2.82%; unemployment 7.2 vs 7.3. Never-revised controls (NSA CPI, fed funds, WTI) show zero difference.
3. **Independent corroboration.** The Philadelphia Fed Real-Time Data Set (731 monthly vintages) reproduces ALFRED's GDP values exactly (11599.4 / 11525.0 / 13141.9). OECD publishes a native revisions dataflow (`DF_STES_REVISIONS`, 79 monthly editions).
4. **Release-time contract.** ALFRED vintage dates coincide with official calendar dates for 60/60 BLS events (PAYEMS, UNRATE, CPI) and 11/11 BEA GDP events, giving date-level RELEASE_TIME; time-of-day comes from BLS/BEA ICS calendars (08:30 ET). No source gives the actual publication instant except CFTC (`:created_at`, recent rows only; history carries the 2022 migration date).
5. **Everything outside the US is latest-only** (ECB, Eurostat, BoE, BoC, World Bank, IMF); ECB `includeHistory`/`updatedAfter` return the same rows. Only ECB `OBS_STATUS`, Eurostat dataset `updated`, and NY Fed `revisionIndicator` give partial signals.
6. **Official calendars are schedule-only.** No official source tested gives forecast/consensus; the only calendar with actual/estimate/previous was an unofficial aggregator (no event ids, one duplicate).
7. **Limits:** day/month vintage granularity, undocumented web endpoint, one vintage per call, bulk download form errored, BLS/EIA anonymous quotas exhausted by shared egress.

## Final block
```
SOURCES_DISCOVERED=28 (+3 key-gated variants: FRED API, BEA API, BLS v2)
SOURCES_EXECUTED=25 (17 data sources with data path + 8 official calendars fetched; TipRanks unofficial comparator executed separately, not counted)

PIT_NATIVE_EXECUTED=3 (ALFRED web CSV, Philadelphia Fed RTDSM, OECD DF_STES_REVISIONS)
PIT_ADAPTABLE_EXECUTED=6 (BLS API, NY Fed, ECB, Eurostat, CFTC, Treasury yield XML)

FRED_EXECUTED=PARTIAL (web CSV fredgraph executed; official API api.stlouisfed.org not executed - no key)
ALFRED_EXECUTED=YES (web CSV + vintage list page; bulk form POST failed HTTP 500)
FRED_VINTAGE_SEMANTICS_PROVEN=NO (FRED latest ignores vintage_date; keyed API realtime_* not executed)
ALFRED_VINTAGE_SEMANTICS_PROVEN=YES (web CSV, day granularity; keyed API path not tested)

RELEASE_TIMESTAMP_SOURCES=scheduled: BLS ICS, BEA ICS (machine-readable), EIA/FRED/Census HTML; actual-publication stamps: CFTC (recent rows), Treasury yield feed; date-level via ALFRED vintage date. No source gives an intraday actual for macro releases.
REVISION_AWARE_SOURCES=3 vintage-native (ALFRED, Philly Fed RTDSM, OECD STES revisions) + 4 flag-only (BLS P flag, NY Fed revisionIndicator, ECB OBS_STATUS, CFTC :updated_at)

LOOKAHEAD_FROM_LATEST_VALUE_PROVEN=YES

DROP_IN_MACRO_SOURCE=NO
ANY_SCIENTIFIC_INVALIDATION=NO

FINAL_VERDICT=LIMITED_MACRO_PIT_SOURCES_SUPPORTED
```
Reason for LIMITED rather than REFERENCE_STACK: US vintage stack is proven and cross-validated, but it is date/month-granular, relies on an undocumented endpoint (keyed API unexecuted), and no non-US source with vintages was found beyond one OECD flow.
