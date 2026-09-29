# 02 — On-chain, mempool, exchange flows, developer activity

## Sources

* **Blockchain.com Charts API** — 6/6 calls HTTP 200; median 590 ms. aggregates re-served with Last-Modified=fetch time; capture forward daily + keep vintages. Adjudication: **PARK** — Free and convenient but aggregates are re-served without vintages; no incremental evidence (14 blockchain.info series tested, none significant). Prefer deriving own aggregates from blocks (blockstream) if on-chain is pursued.
* **mempool.space REST (blocks/fees/mining)** — 9/9 calls HTTP 200; median 473 ms. live mempool has no history: forward capture is the ONLY way; mining series aggregated ex-post. Adjudication: **ADAPT** — Only source of LIVE mempool/fee-market state (no history exists) => forward capture with own receipt timestamps is the only way to ever test mempool signals; mining aggregates null in tests.
* **Blockstream Esplora** — 6/6 calls HTTP 200; median 641 ms. block/tx timestamps on-ledger; derive own aggregates; reorg buffer of ~6 blocks. Adjudication: **ADAPT** — PIT-native ledger data; own aggregation removes the vintage problem of chart APIs. Value unproven (chart-derived proxies null).
* **Blockchair stats** — 3/3 calls HTTP 200; median 839 ms. snapshot only; history paid. Adjudication: **PARK** — Snapshot-only on free tier; nothing beyond blockstream/mempool.space.
* **DefiLlama stablecoins & TVL** — 6/6 calls HTTP 200; median 476 ms. history recomputed when adapters change (DOC/INFERENCE); forward snapshots needed. Adjudication: **ADAPT** — Stablecoin supply change is only partly independent of price (R2adj 0.28); its raw next-day-return signal (DeltaR2 +0.39 %, BH q 0.97) is not significant; needs forward vintage capture because history is recomputed.
* **ClickHouse public playground github_events (GH Archive)** — 3/3 calls HTTP 200; median 526 ms. created_at = event time; BUT coverage holes (2024-06-06..2025-09) => completeness not guaranteed (OBS). Adjudication: **REJECT** — Table content changed between two identical queries 14 min apart and has holes (2024-06..2025-08) and no rows after 2026-07-02: no stability contract. Use GH Archive files instead.
* **GH Archive hourly dumps** — 3/3 calls HTTP 200; median 587 ms. immutable hourly files, Last-Modified = publication time (OBS header). Adjudication: **ADAPT** — Immutable PIT-native hourly files (Last-Modified = publication). Heavy (~100 MB/hour) - process forward incrementally. Developer-activity tests (via playground copy) null; independent of price.
* **GitHub REST API** — 0/3 calls HTTP 200; non-200: 403. not executed (session policy); author dates client-set, history rewritable. Adjudication: **PARK** — Blocked by this session's scope policy, not a provider verdict; commit dates client-set.
* **npm downloads / pypistats** — 6/6 calls HTTP 200; median 544 ms. restated for bots/mirrors; pypistats 180 d only. Adjudication: **PARK** — npm long history is free; pypistats 180 d; mirror/bot restatement; not tested.
* **Exchange wallet/reserve flows (Glassnode/CryptoQuant/Arkham)** — not executed (no keyless endpoint). not executed. Adjudication: **PARK** — Not free at useful resolution; not executed.

## Observations that matter

* **Mempool has no free history.** `mempool.space` exposes live mempool/fee-histogram state only; blockchain.info `mempool-size` exists as a chart but is an ex-post aggregate with `Last-Modified` = fetch time (OBS). Any real mempool study needs forward capture from now on (INFERENCE from endpoint inventory).
* **Exchange flows/reserves:** no keyless free source with history and un-proprietary labels was found; vendor address labels are proprietary (DOC). Not executed. The only public exchange-side positioning data that *was* executed is Binance Vision futures metrics (OI, long/short ratios) — see 04.
* **GitHub REST was blocked by this session's repository-scope policy** (HTTP 403 with an explicit scope message) — a session limitation, not a provider verdict. GitHub activity was instead read from the ClickHouse public playground copy of GH Archive.
* **ClickHouse playground instability (OBS):** identical queries 14 minutes apart returned different global min/max `created_at` (2011-02-12..2026-09-29 vs 2023-01-13..2026-07-02); the per-repo daily series used for testing had a hole 2024-06-06..2025-08 and ends 2026-07-02 (`bench/.../results/gh_playground_stability.json`). Adjudicated REJECT as a feed; GH Archive hourly files (immutable, header-stamped) are the recommended path. GitHub tests therefore use only ~260-490 usable days.

* **`gh_merged_pr` vs |return|** is the smallest raw p-value in the study (CW p=0.005, ΔR²oos +4.4 %) but rests on n=259 days with only ~130 OOS days from fragmentary data; BH q=0.66. It is the single result worth re-testing on GH Archive files, and is not a finding.

## Incremental-information results (BTC, next-day targets)

| Feature | Asset | Pub. lag used | Price-side adj-R² | Best target (min CW p) | n | ΔR²oos | NW t | CW p | BH q | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| `bc_n-transactions` | BTC | 2 d | 0.02 | abs | 1091 | -0.47% | -1.61 | 0.479 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `bc_n-unique-addresses` | BTC | 2 d | 0.07 | abs | 1091 | -0.18% | 1.03 | 0.487 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `bc_hash-rate` | BTC | 2 d | 0.00 | ret | 1091 | -0.02% | 1.15 | 0.373 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `bc_avg-block-size` | BTC | 2 d | -0.00 | vol | 1091 | +0.21% | -1.28 | 0.082 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `bc_mempool-size` | BTC | 2 d | 0.01 | abs | 1091 | +0.35% | 2.07 | 0.050 | 0.93 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `bc_mempool-count` | BTC | 2 d | 0.04 | abs | 1091 | +0.51% | 1.90 | 0.012 | 0.81 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `bc_median-confirmation-time` | BTC | 2 d | 0.00 | abs | 1091 | -0.07% | 0.89 | 0.466 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `bc_transaction-fees` | BTC | 2 d | 0.02 | ret | 1091 | +0.03% | -0.79 | 0.334 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `bc_utxo-count` | BTC | 2 d | 0.02 | abs | 1091 | -0.12% | -0.94 | 0.356 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `bc_transaction-fees-usd` | BTC | 2 d | 0.05 | ret | 1091 | +0.02% | -0.78 | 0.355 | 0.97 | PRICE DERIVATIVE ONLY REJECT |
| `bc_estimated-transaction-volume-usd` | BTC | 2 d | 0.13 | abs | 1091 | -0.06% | 0.99 | 0.428 | 0.97 | PRICE DERIVATIVE ONLY REJECT |
| `bc_cost-per-transaction` | BTC | 2 d | 0.04 | ret | 1091 | -1.06% | 1.71 | 0.730 | 0.97 | PRICE DERIVATIVE ONLY REJECT |
| `bc_market-cap` | BTC | 2 d | 0.86 | ret | 1091 | -0.08% | -0.51 | 0.655 | 0.97 | PRICE DERIVATIVE ONLY REJECT |
| `bc_miners-revenue` | BTC | 2 d | 0.11 | abs | 1091 | -0.86% | -2.14 | 0.475 | 0.97 | PRICE DERIVATIVE ONLY REJECT |
| `ms_avg_fees_sat_per_block` | BTC | 2 d | 0.03 | abs | 1025 | -0.06% | 0.63 | 0.574 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `ms_avg_block_weight` | BTC | 2 d | 0.01 | ret | 1025 | -0.04% | 0.89 | 0.430 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `stable_mcap` | BTC | 2 d | 0.28 | ret | 1091 | +0.39% | 1.75 | 0.105 | 0.97 | PRICE LINKED PARTIAL NO INCREMENTAL |
| `defi_tvl_usd` | BTC | 2 d | 0.64 | ret | 1091 | +0.02% | -0.84 | 0.337 | 0.97 | PRICE DERIVATIVE ONLY REJECT |
| `gh_push` | BTC | 2 d | 0.11 | vol | 489 | +1.00% | -2.35 | 0.032 | 0.93 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `gh_merged_pr` | BTC | 2 d | 0.05 | abs | 259 | +4.38% | 2.32 | 0.005 | 0.66 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `gh_actors` | BTC | 2 d | 0.05 | vol | 489 | -0.30% | -0.47 | 0.690 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `gh_btc_stars` | BTC | 2 d | 0.18 | vol | 488 | +0.89% | -2.46 | 0.051 | 0.93 | PRICE LINKED PARTIAL NO INCREMENTAL |

_ΔR²oos = out-of-sample R² gain of baseline+feature over baseline (expanding window, first 50 % train); negative = feature hurt out of sample. 'Best target' is chosen by min p, i.e. optimistic; the BH q already accounts for all 132 tests._
