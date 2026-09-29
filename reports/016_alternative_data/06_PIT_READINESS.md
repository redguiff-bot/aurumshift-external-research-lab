# 06 — PIT readiness and leakage

## Classification rule (mission §4)

* **PIT_NATIVE** — every historical row carries an event/publication time that cannot be revised after the fact (ledger, trade, filing, immutable file).
* **LOOKAHEAD_RISK** — historical rows have **no historical publication timestamp** (aggregate re-served with fetch-time `Last-Modified`, as-of dates only, reanalysis, recomputed history). Per the mission this is the default for such rows, **including scheduled official releases** whose publication time is only known from a calendar rule.
* **PIT_ADAPTABLE (forward)** — LOOKAHEAD_RISK for history, but becomes point-in-time if the consumer captures vintages with its own receipt timestamp from now on (or a documented release rule gives a conservative lag). Historical backtests on these are *estimates*.

Counts over 39 sources: **PIT_NATIVE 9**, **LOOKAHEAD_RISK for historical rows 30**, of which **PIT_ADAPTABLE going forward 23**, NOT_READY 7.

| Source | Historical class | Forward readiness | Note |
|---|---|---|---|
| `bc_charts` | LOOKAHEAD_RISK | PIT_ADAPTABLE | aggregates re-served with Last-Modified=fetch time; capture forward daily + keep vintages |
| `mempool_space` | LOOKAHEAD_RISK | PIT_ADAPTABLE | live mempool has no history: forward capture is the ONLY way; mining series aggregated ex-post |
| `blockstream` | PIT_NATIVE | PIT_NATIVE | block/tx timestamps on-ledger; derive own aggregates; reorg buffer of ~6 blocks |
| `blockchair` | LOOKAHEAD_RISK | PIT_ADAPTABLE | snapshot only; history paid |
| `defillama_stable` | LOOKAHEAD_RISK | PIT_ADAPTABLE | history recomputed when adapters change (DOC/INFERENCE); forward snapshots needed |
| `gdelt_doc` | LOOKAHEAD_RISK | PIT_ADAPTABLE | DOC API recomputes; bulk GKG/Events files carry DATEADDED (ingest) => bulk files PIT_NATIVE (DOCUMENTED_CLAIM, not executed) |
| `rss_crypto` | LOOKAHEAD_RISK | PIT_ADAPTABLE | no history at all; pubDate publisher-set; forward capture with own receipt stamp |
| `rss_fed` | LOOKAHEAD_RISK | PIT_ADAPTABLE | no deep history in feed; forward capture |
| `hn_algolia` | PIT_NATIVE | PIT_NATIVE | created_at_i is post time; counts retro-change via deletions/flags => use item timestamps not nbHits (nbHits inexact OBS) |
| `stocktwits` | LOOKAHEAD_RISK | PIT_ADAPTABLE | recent window only |
| `reddit_json` | LOOKAHEAD_RISK | NOT_READY | blocked from test egress; recent 1000 only |
| `bluesky` | LOOKAHEAD_RISK | PIT_ADAPTABLE | createdAt client-declared; use indexedAt from own firehose capture |
| `gtrends` | LOOKAHEAD_RISK | NOT_READY | re-sampled every request; no official API |
| `wikipedia_pv` | LOOKAHEAD_RISK | PIT_ADAPTABLE | day-bucket, finalised next day, classification refinements retro; no per-row publication time |
| `fear_greed` | LOOKAHEAD_RISK | PIT_ADAPTABLE | no publication time, methodology undisclosed; price-derived anyway |
| `polymarket` | PIT_NATIVE | PIT_NATIVE | trades/price points carry event time; resolution state is mutable |
| `kalshi` | PIT_NATIVE | PIT_NATIVE | trades timestamped; settlement final |
| `cftc_cot` | LOOKAHEAD_RISK | PIT_ADAPTABLE | as-of Tuesday, release rule Fri 15:30 ET documented; dataset overwritten in place, no vintages; holiday delays |
| `etf_farside` | LOOKAHEAD_RISK | NOT_READY | blocked by Cloudflare challenge; site restates |
| `etf_ssga_gld` | LOOKAHEAD_RISK | PIT_ADAPTABLE | current snapshot overwritten daily; capture forward |
| `sec_edgar` | PIT_NATIVE | PIT_NATIVE | acceptanceDateTime per filing; amendments are new filings (OBS: acceptanceDateTime present in submissions JSON; amendments-as-new-filings is DOCUMENTED_CLAIM) |
| `fiscal_dts` | LOOKAHEAD_RISK | PIT_ADAPTABLE | record_date only; release rule T+1 documented |
| `nyfed` | LOOKAHEAD_RISK | PIT_ADAPTABLE | revisionIndicator present but no vintage store (see report 005) |
| `gh_playground` | PIT_NATIVE | PIT_NATIVE | created_at = event time; BUT coverage holes (2024-06-06..2025-09) => completeness not guaranteed (OBS) |
| `gharchive` | PIT_NATIVE | PIT_NATIVE | immutable hourly files, Last-Modified = publication time (OBS header) |
| `github_rest` | LOOKAHEAD_RISK | NOT_READY | not executed (session policy); author dates client-set, history rewritable |
| `npm_pypi` | LOOKAHEAD_RISK | PIT_ADAPTABLE | restated for bots/mirrors; pypistats 180 d only |
| `portwatch` | LOOKAHEAD_RISK | PIT_ADAPTABLE | AIS nowcast revised (DOC); publish weekly; vintage capture needed |
| `eia_files` | LOOKAHEAD_RISK | PIT_ADAPTABLE | release calendar documented; final values only |
| `eia_api` | LOOKAHEAD_RISK | PIT_ADAPTABLE | same as files; key needed (not executed) |
| `gie_agsi` | LOOKAHEAD_RISK | PIT_ADAPTABLE | updatedAt field documented (DOC) but key needed (not executed) |
| `openmeteo` | LOOKAHEAD_RISK | PIT_ADAPTABLE | archive=ERA5 reanalysis NOT PIT; historical-forecast API (stored runs) is PIT-like (DOC) but was rate-limited (OBS 429) |
| `nws` | LOOKAHEAD_RISK | PIT_ADAPTABLE | forecast text replaced; forward capture |
| `noaa_ndbc` | LOOKAHEAD_RISK | PIT_ADAPTABLE | rolling 45 d |
| `deribit_dvol` | PIT_NATIVE | PIT_NATIVE | trades/funding prints carry exchange time; server stamps (report 005) |
| `binance_vision` | PIT_NATIVE | PIT_NATIVE | immutable daily files with checksums; file Last-Modified = publication (OBS) |
| `exchange_reserves` | LOOKAHEAD_RISK | NOT_READY | not executed |
| `baltic_shipping` | LOOKAHEAD_RISK | NOT_READY | not executed |
| `ais_open` | LOOKAHEAD_RISK | NOT_READY | not executed |

## Re-fetch revision test (OBS)

Same historical window fetched twice, ~170 s apart; all rows except the last two days compared.

| Series | Rows compared | Rows changed | Last-Modified t0 | Last-Modified t1 |
|---|---|---|---|---|
| blockchain_info_ntx | 51 | 0 | Tue, 29 Sep 2026 17:58:35 GMT | Tue, 29 Sep 2026 18:01:29 GMT |
| defillama_stable | 3225 | 0 | Tue, 29 Sep 2026 16:22:25 GMT | Tue, 29 Sep 2026 16:22:25 GMT |
| cftc_btc_lev_short | 198 | 0 | None | None |
| fear_greed | 88 | 0 | None | None |
| treasury_tga | 118 | 0 | None | None |
| hn_algolia_count | 1 | 0 | None | None |

A 3-minute window cannot detect slow restatements (DefiLlama adapter recomputation, PortWatch nowcast revisions, ERA5T→ERA5); 0 changes here is *not* evidence of immutability. The `Last-Modified` header of the chart API equals the fetch time, so it carries no publication information (OBS).

## Observed newest-row latency (snapshot at 2026-09-29T17:57:28+00:00)

```
{
 "blockchain_info_ntx": {
  "newest_x": "2026-09-28T00:00:00+00:00",
  "age_h": 42.0,
  "last_modified": "Tue, 29 Sep 2026 17:57:29 GMT"
 },
 "mempool_space_tip": {
  "tip_block_time": "2026-09-29T17:52:32+00:00",
  "age_min": 6.0
 },
 "cftc_btc": {
  "newest_report_date": "2026-09-22T00:00:00.000",
  "dataset_last_modified": null
 },
 "treasury_dts": {
  "newest_record_date": "2026-09-25"
 },
 "binance_vision_metrics_2026-09-28": {
  "status": 200,
  "last_modified": "Tue, 29 Sep 2026 07:18:11 GMT"
 },
 "binance_vision_metrics_2026-09-27": {
  "status": 200,
  "last_modified": "Mon, 28 Sep 2026 06:38:19 GMT"
 },
 "binance_vision_metrics_2026-09-26": {
  "status": 200,
  "last_modified": "Sun, 27 Sep 2026 06:44:17 GMT"
 },
 "gh_playground_last6d": "",
 "gh_playground_after_0702": "1970-01-01 00:00:00\t0\n",
 "hn_newest_bitcoin_story": {
  "created": "2026-09-29T10:49:22Z"
 },
 "defillama_stable": {
  "newest": "2026-09-29T00:00:00+00:00",
  "last_modified": "Tue, 29 Sep 2026 16:22:25 GMT"
 },
 "eia_wpsr_xls": {
  "last_modified": null,
  "newest_week_ending": "2026-09-18 00:00:00"
 },
 "wikipedia_newest": "2026092800",
 "fear_greed_newest": "2026-09-29T00:00:00+00:00",
 "portwatch_newest": [
  {
   "date": "2026-09-27"
  }
 ],
 "portwatch_last_modified": null
}
```

## Leakage demonstration: conservative lag vs naive lag 0

Same test re-run with the feature treated as available at its as-of/period date (lag 0) — what a careless backtest would do. Column = largest increase in |NW t| across the three targets, and the largest ΔR²oos increase.

| Feature | Conservative lag | Change in abs(NW t), lag0 minus conservative | Change in ΔR²oos | Target |
|---|---|---|---|---|
| `ms_avg_fees_sat_per_block` | 2 d | +1.72 | +0.90% | vol |
| `defi_tvl_usd` | 2 d | +1.45 | +0.72% | vol |
| `ms_avg_block_weight` | 2 d | +1.43 | -0.12% | abs |
| `cftc_btc_oi` | 6 d | +1.42 | -0.25% | vol |
| `tga_gold` | 2 d | +1.19 | +0.29% | vol |
| `eia_gas` | 7 d | +1.06 | +0.48% | abs |
| `bc_utxo-count` | 2 d | +1.05 | +0.06% | ret |
| `cftc_wti_mm` | 6 d | +1.03 | +0.76% | ret |
| `cftc_gold_mm` | 6 d | +1.02 | +0.96% | abs |
| `pw_Suez_Canal` | 10 d | +0.99 | +0.32% | abs |
| `pw_Strait_of` | 10 d | +0.94 | +1.42% | ret |
| `bc_market-cap` | 2 d | +0.91 | +0.76% | ret |
| `bc_transaction-fees` | 2 d | +0.90 | +0.37% | abs |
| `gh_push` | 2 d | +0.86 | +0.68% | abs |
| `bc_n-unique-addresses` | 2 d | +0.86 | +0.37% | ret |
| `gh_merged_pr` | 2 d | +0.85 | -0.08% | ret |
| `stable_mcap` | 2 d | +0.80 | +0.47% | vol |
| `gh_btc_stars` | 2 d | +0.78 | +2.24% | vol |
| `eia_crude` | 7 d | +0.77 | +0.45% | abs |
| `bc_transaction-fees-usd` | 2 d | +0.66 | +0.35% | abs |
| `cftc_btc_lev_net_pct_oi` | 6 d | +0.57 | +0.75% | vol |
| `fear_greed` | 1 d | +0.54 | +0.27% | abs |
| `bc_median-confirmation-time` | 2 d | +0.54 | +0.04% | ret |
| `hdd_us5` | 7 d | +0.51 | +0.42% | vol |
| `bc_mempool-size` | 2 d | +0.50 | +0.03% | vol |
| `bc_mempool-count` | 2 d | +0.49 | +0.15% | ret |
| `bc_cost-per-transaction` | 2 d | +0.46 | +0.50% | abs |
| `pw_Bab_el-Mandeb` | 10 d | +0.41 | +0.04% | vol |
| `wiki_gold` | 2 d | +0.39 | +0.07% | abs |
| `gh_actors` | 2 d | +0.37 | +0.17% | vol |
| `cdd_us5` | 7 d | +0.23 | +0.01% | abs |
| `bc_hash-rate` | 2 d | +0.19 | +0.35% | ret |
| `hn_btc` | 2 d | +0.19 | +0.26% | ret |
| `wiki_Bitcoin` | 2 d | +0.17 | +0.11% | ret |
| `cftc_btc_am_net_pct_oi` | 6 d | +0.16 | +0.73% | vol |
| `wiki_Cryptocurrency` | 2 d | +0.14 | +0.21% | abs |
| `bc_miners-revenue` | 2 d | +0.04 | +0.70% | ret |
| `bc_estimated-transaction-volume-usd` | 2 d | +0.03 | +0.32% | vol |
| `tga_btc` | 2 d | -0.14 | +0.15% | ret |
| `bc_n-transactions` | 2 d | -0.29 | +0.66% | ret |
| `bc_avg-block-size` | 2 d | -0.62 | +0.49% | abs |

9 of 41 lagged features show abs(t) rising by more than 1.0 when the lag is dropped (max +1.72). Tests nominally significant on BOTH Clark-West and Newey-West (p<0.05, unadjusted): **4 with the conservative lag vs 6 with lag 0** among the same 41 lagged features and their 3 targets. The inflation is modest and mixed in sign because most features are unpredictive at either lag; a lag that is too short cannot create signal from nothing, it only adds contemporaneous noise. The risk is largest for series that co-move with price on the target day: `gh_btc_stars` vs next-day volume goes from t=-2.46 (lag 2) to t=-3.24 (lag 0). **The lags themselves are assumptions** (see 10): they bound, but do not measure, real publication times.
