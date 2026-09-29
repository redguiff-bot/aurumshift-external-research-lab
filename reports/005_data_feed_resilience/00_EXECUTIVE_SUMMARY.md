# 00 — Executive summary

Mission: `AURUMSHIFT_EXTERNAL_DATA_FEED_RESILIENCE_AND_FREE_SOURCE_DISCOVERY_V1` — external research only; no private AurumShift code read; no integration proposed.
Run date (test-egress clock): 2026-09-29 (UTC). Evidence labels follow `claude.md`: PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN.

## What was actually done
* 68 candidate sources catalogued; **46 executed end-to-end** (real HTTP/WS calls, parsed, stored in `bench/data_feeds_v1/`), 1 partially, 9 blocked by the test egress, the rest not executed (key / account / own query error / deliberate).
* 18 venue×instrument 1-minute BTC series fetched 3× (t0, +78 s, +362 s); 240-minute window, pairwise + consensus comparison, lag test, re-fetch revision test.
* 14 REST endpoints × 10 sequential calls (latency); 14 WebSocket endpoints × 20 s bounded live samples.
* Derivatives: funding on 9 venues, OI on 8, liquidations on 4 (REST) + 2 (WS), options (Deribit vs OKX, 690 common instruments), dated-futures basis.
* Bulk: Binance Vision daily/monthly files incl. checksum verification and API-vs-bulk equality; Dukascopy tick decode.
* Macro/FX/gold/commodity: 20+ official/quasi-official endpoints; docs/ToS facts gathered separately (`bench/data_feeds_v1/results/docs_facts.json`, 43/47 providers with at least one verbatim quote; the rest `NOT_FOUND`).

## Headline findings (all OBSERVED unless stated)
1. **Keyless crypto coverage is broad and clean.** All 17 crypto bar series that returned data had 0 duplicates, 0 unaligned timestamps and 0 revisions over a 6-minute re-fetch; 16/17 had 0 missing minutes (Bitget: 1), although 4 venues reach that by gap-filling flat zero-volume bars; timestamp label agreement across all venues is exact (best cross-correlation lag = 0 for every venue, `results/lag_test_vs_kraken.json`).
2. **No two venues agree on OHLC.** Exact 4-field OHLC match between any two venues: 0 of 233 common minutes for every pair. Median close difference is 0.3–1.0 bps between the best pairs (Gate/OKX/Binance mirror; Kraken/Coinbase/Bitstamp), 3–4.7 bps across USD-vs-USDT quote currencies, and 13 bps for Bitfinex vs its USD peers (cause UNKNOWN). Volume is not comparable across venues (units differ: base, quote, contracts, USD).
3. **Derivatives gap classes have keyless candidates.** Funding (9 venues), OI snapshot (8), OI history (OKX 8 h @5 min; Gate ~8 h; Binance Vision metrics 5 min daily files), liquidations (OKX REST/WS, Gate, Bitfinex, BitMEX WS), basis (Deribit dated futures; OKX listing), options IV/skew (Deribit 944 + OKX 1272 BTC instruments, 690 common; median IV difference 0.34 vol pts, |median| 0.48, p05 -1.14, p95 2.37; DVOL).
4. **Funding and OI are venue-specific quantities, not one series seen through several windows.** At the 15 shared 8-hour boundaries OKX, Gate, Bitget, KuCoin disagree in sign or magnitude in most rows; OI units differ by an order of magnitude (BTC, USD, contracts×multiplier). Cross-venue use needs explicit normalisation.
5. **PIT posture is weak across the board.** No executed source exposes a provider revision signal *and* a receipt timestamp; Deribit responses carry server `usIn/usOut` microsecond stamps (receipt-side, usable), Binance Vision files carry `Last-Modified`/ETag/CHECKSUM, NY Fed rows carry `revisionIndicator`, ECB SDMX has `OBS_STATUS`/`updatedAfter`. Everything else requires the consumer to stamp receipt time itself (PIT_ADAPTABLE at best).
6. **Hazards found that would silently corrupt a pipeline:** Binance Vision *spot* files change timestamp unit from ms to µs between the 2024-12 and 2025-01 monthly files; Coinbase candle column order differs from every other venue; Kraken returns the forming bar unflagged; gap-filled zero-volume flat bars (Gemini 23/240 flat, Binance.US 174/240, dYdX 202/240) make "0 missing" misleading; OKX REST liquidation endpoint works but is absent from current docs.
7. **Coverage the test egress could not reach:** Binance main API (HTTP 451), Bybit (403), MEXC futures (403), FRED/ALFRED (connection closed by proxy), Stooq, GDELT, IMF, BLS ICS. These are *egress* outcomes, not provider verdicts; the most valuable untested items are FRED/ALFRED (PIT-native macro) and Binance/Bybit derivatives.

## Adjudication counts
ADOPT_REFERENCE 8 · ADAPT_CANDIDATE 22 · PARK 37 · REJECT 1 (no synthetic ranking; see `11_ADJUDICATION.md`).

## Final block
```
SOURCES_DISCOVERED=68
SOURCES_EXECUTED=46 (data path executed, HTTP 200 and parsed); 1 reachable-but-data-path-not-completed (FRED); 9 blocked from the test egress; 12 not executed (key/account/own error/deliberate)
FREE_PUBLIC_SOURCES=43 classified FREE_UNAUTHENTICATED (43 of them executed)
FREE_ACCOUNT_SOURCES=4 classified FREE_WITH_ACCOUNT (0 executed with an account; +3 FREE_TIER executed with a shared demo key; 17 UNKNOWN; 1 PAID_ONLY)

CRYPTO_SPOT_CANDIDATES=11
DERIVATIVES_CANDIDATES=9
FX_CANDIDATES=7
COMMODITY_CANDIDATES=9 (incl. gold proxies; strictly energy/base-metal price feeds: 1, Yahoo unofficial - see 04)
MACRO_CANDIDATES=9

PIT_NATIVE_COUNT=0 observed (+1 DOCUMENTED_CLAIM only: ALFRED, execution blocked)
PIT_ADAPTABLE_COUNT=34 classified (30 executed)

FALLBACK_CAPABLE_COUNT=18 (executed sources holding a PRIMARY/SECONDARY/FALLBACK role in at least one gap class)

ANY_DROP_IN_SOURCE=NO
ANY_SCIENTIFIC_INVALIDATION=NO

FINAL_VERDICT=MULTIPLE_DATA_SOURCE_CANDIDATES_SUPPORTED
```
