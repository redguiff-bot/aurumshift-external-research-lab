# 09 — Adjudication

> External research only — no private AurumShift code, no integration claims. Evidence tags: **[OBS]** observed in this study, **[DOC]** stated on a provider page/API response fetched in this study, **[INF]** inference, **[UNK]** unknown/not verified. Study date 2026-09-29 (sandbox clock). Reproduce with `bench/alternative_data_v1/`.


Per repository doctrine (REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST) the outputs are ADOPT / ADAPT / PARK / REJECT **candidates**; final integration adjudication happens later against the real local AurumShift repository. Nothing here claims compatibility with the private implementation.

## FINAL_VERDICT: **LIMITED_ALTERNATIVE_DATA_SUPPORTED**
Rationale: exactly two candidates cleared a pre-declared, FDR-controlled, OOS-confirmed, price-independence bar; one is a non-market real-economy signal that is contemporaneous and fading (event-clock only), the other is options-market-derived. No PIT-clean, price-independent *crypto-native* alternative feed produced OOS information. Large families were untestable (missing history/access), so `NO_USEFUL_ALTERNATIVE_DATA_FOUND` would overstate the negative and `MULTIPLE_…` would overstate the positive. `STUDY_INCONCLUSIVE` is not chosen because the tested families gave calibrated, decisive answers (noise controls 0/12; price-derived controls flagged; positive control passed).

| source / family | call | reason |
|---|---|---|
| EIA weekly crude/gas inventories (bulk + release files) | ADAPT | Only non-market candidate (t≈-5, OOS +2.5 %, Brent replicates, price-independent). Event-clock: ingest on the release schedule with own receipt stamps; test at intraday resolution; expect executability limits (post-2021 fade). Public-domain licence. |
| Deribit DVOL / options book summary | ADAPT | Passes OOS on range (+2.3 %). Market-derived (options), so it competes with whatever vol inputs a system already has — overlap can only be judged against the real repo. Capture own vintages; immutable index prints. |
| Coin Metrics community (flows, activity, MVRV…) | PARK | No increment; exchange flows are price-reactive (R² 0.41). Keep as *forward-capture* candidate because completion/status-time fields make first-seen logging verifiable; history is recomputed (2067/2219 rows). CC licence variant to confirm. |
| mempool.space / Blockstream / ETH RPC (raw chain state) | PARK | Only source of true mempool/fee-market state, but snapshot-only: value unknown until ≥6–12 months of self-captured history exist. Cheap to capture. |
| GDELT 2.0 raw files | PARK | PIT-native and free for commercial use; batch-time not publication-time; a full GKG build is ≈0.17 TB/year (96 files/day × ~5 MB) → needs a scoped, theme-filtered or sampled ingest before it can be tested. |
| Kalshi / Polymarket macro-event probabilities | PARK | PIT-native price history; independent of crypto price for macro/election contracts. Needs an event-labelled study (FOMC etc.) with more history than the ~1 year reachable; BTC-threshold contracts are price derivatives (REJECT those). |
| GH Archive | PARK | PIT-native; no crypto-repo series built. npm/PyPI proxies showed no increment. |
| CFTC COT (TFF/legacy/disaggregated) | PARK | Rule-based PIT (native stamps only after 2022-09); positioning absorbed by baseline for BTC vol/return. Still valid as macro context for commodities/FX (untested here). |
| Treasury TGA, NY Fed RRP | PARK | Independent of price but no increment for BTC/ETH; not tested on rates/gold/FX where the liquidity channel is more direct. |
| Fear & Greed (alternative.me) | REJECT | Composite of price-vol/momentum/social; reactivity 0.43; no increment; no vintages. |
| DefiLlama stablecoin supply / DEX volume | REJECT | USD-denominated, restated history, subsumed by baseline; no increment. |
| Blockchain.com charts, npm/PyPI/crates counts, Wikipedia page-views | REJECT | No increment after calendar controls; LOOKAHEAD_RISK; restrictive/unclear terms (Blockchain.com). |
| Binance long/short & taker ratios, OKX/Bitfinex stats | PARK | Same-venue microstructure; Binance ratios no OOS gain; OKX/Bitfinex keep only weeks–months (capture-only). |
| RSS feeds (crypto news, Fed/SEC/ECB press) | PARK | Zero history; forward capture is trivial and gives an event clock, value untested. |
| Public social (Reddit RSS, StockTwits, Mastodon, HN, 4chan) | REJECT | ToS-restricted or tiny/noisy; hours of retention; no PIT history. HN/Arctic Shift optional for research only. |
| ETF flows (iShares, Farside, Yahoo) | PARK | No accessible free source; not negative evidence. Revisit with a sanctioned data route. |
| Weather: CPC degree days, NWS, NCEI, NASA POWER | REJECT (realised) / PARK (forecast) | Realised anomalies are priced (no increment); Open-Meteo historical-forecast and NOAA GFS are the PIT route but were quota-blocked/untested. |
| Shipping: IMF PortWatch | PARK | Genuine physical-flow data, 2-day freshness, but AIS-revised and no effect on WTI at weekly horizon (p=0.16, n=381). |
| Google Trends, Bluesky, Reddit JSON, Glassnode, LunarCrush, FRED/ALFRED (unreachable) | PARK | Blocked/keyed from this environment: missing evidence. |

## Suggested sequencing (research-side only)
1. Stand up a small **forward-capture** harness (append-only, receipt-stamped): mempool snapshots, RSS, Kalshi/Polymarket macro markets, Coin Metrics rows with completion/status stamps, OKX/Bitfinex stats, NWS forecasts.
2. Re-run the EIA crude study with **release-timestamped intraday** prices to learn whether any executable window exists.
3. Build a theme-filtered GDELT GKG daily series (crypto/central-bank/energy themes) and test with the same harness (`py/analysis_crypto.py` is source-agnostic: add a block).
4. Re-test liquidity series (TGA/RRP) on rates/gold/FX, where the transmission channel is more direct than for crypto.
