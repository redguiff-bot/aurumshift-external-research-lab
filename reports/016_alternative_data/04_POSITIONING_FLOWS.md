# 04 — Positioning and flows (CFTC, ETF, public exchange positioning)

## Sources

* **CFTC Public Reporting (Socrata) COT** — 3/3 calls HTTP 200; median 856 ms. as-of Tuesday, release rule Fri 15:30 ET documented; dataset overwritten in place, no vintages; holiday delays. **ADAPT** — Weekly, real institutional positioning independent of price at daily lens (R2adj 0.14-0.24), documented release rule; null in test (lev net BTC ret DeltaR2 -0.74 %). Naive Tuesday-dating would leak 3-4 days (see 06). Needs vintage capture.
* **Farside ETF flows** — 0/3 calls HTTP 200; non-200: 403. blocked by Cloudflare challenge; site restates. **PARK** — Most direct ETF flow series but Cloudflare-blocked; only issuer-page capture possible.
* **SPDR GLD holdings (issuer)** — 0/3 calls HTTP 200; non-200: 404 (guessed file URL, provider verdict UNKNOWN). current snapshot overwritten daily; capture forward. **PARK** — Snapshot only; history by own capture; not tested.
* **SEC EDGAR (13F, Form 4, 8-K)** — 3/3 calls HTTP 200; median 527 ms. acceptanceDateTime per filing; amendments are new filings (OBS: acceptanceDateTime present in submissions JSON; amendments-as-new-filings is DOCUMENTED_CLAIM). **PARK** — PIT-native acceptanceDateTime (13F/Form 4/8-K) - strongest PIT source found but low frequency; not tested.
* **Binance Vision (data.binance.vision)** — 3/3 calls HTTP 200; median 664 ms. immutable daily files with checksums; file Last-Modified = publication (OBS). **ADAPT** — Immutable files, checksummed, PIT-native; OI/positioning already in the baseline; long/short account ratio is price-derived (R2adj 0.46) and taker ratio a volume derivative.
* **Deribit public API (index/funding/OI)** — 6/6 calls HTTP 200; median 475 ms. trades/funding prints carry exchange time; server stamps (report 005). **PARK** — See report 005; implied vol is price-derived by construction for information purposes; (one probe hit gateway 502 CONNECT rejection).

## CFTC publication timing (OBS)

Newest BTC row at fetch: as-of 2026-09-22T00:00:00.000. The Socrata dataset exposes `report_date_as_yyyy_mm_dd` (the Tuesday as-of date) and **no release timestamp per row**. Dataset headers (`results/cftc_headers.json`, OBS) show `Last-Modified: Fri, 25 Sep 2026 19:30:07-08 GMT` for the legacy, TFF and disaggregated datasets, i.e. **3 d 19.5 h after the Tuesday as-of date** — consistent with the documented Friday 15:30 ET release, but it is a *dataset-level* stamp that is overwritten at each release; it cannot date historical rows. Tests therefore assume availability = as-of + 6 days (covers Friday release and holiday delays); the naive as-of dating is shown in 06 to quantify the leak.

## Incremental-information results

| Feature | Asset | Pub. lag used | Price-side adj-R² | Best target (min CW p) | n | ΔR²oos | NW t | CW p | BH q | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| `cftc_btc_lev_net_pct_oi` | BTC | 6 d | 0.18 | vol | 1091 | +0.06% | -1.64 | 0.204 | 0.97 | PRICE LINKED PARTIAL NO INCREMENTAL |
| `cftc_btc_am_net_pct_oi` | BTC | 6 d | 0.14 | vol | 1091 | +0.03% | 1.89 | 0.129 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `cftc_btc_oi` | BTC | 6 d | 0.24 | ret | 1091 | +0.48% | -2.30 | 0.054 | 0.93 | PRICE LINKED PARTIAL NO INCREMENTAL |
| `bn_toptrader_ls_pos` | BTC | 0 d | 0.07 | ret | 1055 | +0.24% | -1.81 | 0.154 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `bn_ls_ratio` | BTC | 0 d | 0.46 | abs | 1055 | +0.58% | -2.23 | 0.126 | 0.97 | PRICE DERIVATIVE ONLY REJECT |
| `bn_taker_ls_vol` | BTC | 0 d | 0.10 | abs | 1055 | -0.14% | 0.85 | 0.662 | 0.97 | PRICE DERIVATIVE ONLY REJECT |
| `cftc_gold_mm` | GOLD | 6 d | 0.07 | ret | 768 | -0.19% | -1.09 | 0.433 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `cftc_wti_mm` | CRUDE | 6 d | -0.01 | vol | 763 | -0.61% | 0.31 | 0.694 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |

_ΔR²oos = out-of-sample R² gain of baseline+feature over baseline (expanding window, first 50 % train); negative = feature hurt out of sample. 'Best target' is chosen by min p, i.e. optimistic; the BH q already accounts for all 132 tests._
