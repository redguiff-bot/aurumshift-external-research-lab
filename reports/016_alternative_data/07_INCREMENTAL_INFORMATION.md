# 07 — Incremental information beyond price, volume, volatility, funding, OI

## Protocol (fixed before results; no tuning)

```
decision time = end of trading day d. target_{d} = next trading day's (a) return, (b) |return|, (c) log(volume_{d+1}/mean volume d-6..d).
 baseline X_d = r_d..r_{d-6}, |r_d|,|r_{d-1}|,|r_{d-2}|, log(v_d/mean28 v), log rv7  [+ funding_d, dlog OI_d for BTC].
 feature = z-score (trailing window, current obs excluded) of the change over 1 week; usable from as-of date + conservative publication lag; forward-filled (limit 10 d).
 tests: in-sample OLS coef of feature added to baseline (Newey-West 5 lags); expanding-window OOS (first 50% train, refit every 5 d) DeltaR2_oos vs baseline with Clark-West p (one-sided);
        BH-FDR q=0.10 across ALL feature x target tests. CANDIDATE needs: BH pass AND in-sample NW p<0.05 AND DeltaR2_oos>0 AND same in-sample sign in both halves AND price-side R2adj<0.40 AND not price-by-construction.
 independence diagnostic: adj-R2 of the native (as-of-date) feature on a contemporaneous price-side matrix (1d ret, 7d ret, prior 7d ret, |7d ret|, log rv7, vol ratio, [funding7, dOI7]).
 naive_lag0 variant: same test with availability lag 0 to measure look-ahead inflation for scheduled/aggregated releases.
```

Window 2023-10 → 2026-09 (BTC ≈1,090 daily obs; futures ≈ 830 trading days; weekly series ≈ 170 obs; GitHub ≈ 260-490). Baseline includes funding and ΔOI **for BTC only** (Binance Vision daily files); gold/crude/natgas have price, volume, volatility only.

## Headline

* **44 feature series tested** (0 not testable), 132 (feature × target) tests.
* **Candidates passing the full gate: 0.** Nominal p<0.05 (Clark-West) in 5 tests versus ≈ 6.6 expected by chance; smallest BH q = 0.66.
* Class counts: INDEPENDENT_NO_INCREMENTAL_EVIDENCE: 29, PRICE_DERIVATIVE_ONLY_REJECT: 9, PRICE_LINKED_PARTIAL_NO_INCREMENTAL: 6.
* **Most features have NEGATIVE out-of-sample ΔR²** — adding them made predictions worse. This is the normal signature of no signal plus estimation noise.

## Power (BTC, same n and gate; synthetic feature with known partial R²)

| Target | n | 0.25 % | 0.5 % | 1 % | 2 % | 4 % |
|---|---|---|---|---|---|---|
| ret | 1091 | 0 % | 0 % | 2 % | 34 % | 90 % |
| abs | 1091 | 0 % | 0 % | 5 % | 22 % | 78 % |
| vol | 1091 | 0 % | 0 % | 8 % | 44 % | 96 % |

Detection probability of the pre-registered gate. **Minimum detectable effect (80 % power) ≈ 3-4 % partial R² at a 1-day horizon.** A true incremental effect of 0.5-2 % (already large for a daily crypto feature) would be missed most of the time. The null therefore rules out *large* incremental effects only — it does **not** show that these sources are useless. Weekly series (CFTC, EIA; ~170 obs) have far less power than this table.

## Price-derivative rejects

Rejected if price-by-construction (USD-denominated or composite containing price/volume) **or** price-side adj-R² ≥ 0.40:

| Feature | Reason | Price-side adj-R² |
|---|---|---|
| `bc_transaction-fees-usd` | by construction: USD-denominated => contains BTC price | 0.05 |
| `bc_estimated-transaction-volume-usd` | by construction: USD-denominated => contains BTC price | 0.13 |
| `bc_cost-per-transaction` | by construction: USD-denominated => contains BTC price | 0.04 |
| `bc_market-cap` | by construction: USD-denominated => contains BTC price | 0.86 |
| `bc_miners-revenue` | by construction: USD-denominated => contains BTC price | 0.11 |
| `defi_tvl_usd` | by construction: TVL in USD includes token prices | 0.64 |
| `fear_greed` | by construction: composite incl. volatility/momentum/volume | 0.49 |
| `bn_ls_ratio` | explained by price-side matrix | 0.46 |
| `bn_taker_ls_vol` | by construction: taker buy/sell volume ratio is a volume derivative | 0.10 |

Sanity check: `bc_market-cap` (pure price × supply) has price-side adj-R² 0.86, the DeFi TVL series 0.64, Fear & Greed 0.49 — the diagnostic recovers known derivatives.

## Full table (all tested features)

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
| `cftc_btc_lev_net_pct_oi` | BTC | 6 d | 0.18 | vol | 1091 | +0.06% | -1.64 | 0.204 | 0.97 | PRICE LINKED PARTIAL NO INCREMENTAL |
| `cftc_btc_am_net_pct_oi` | BTC | 6 d | 0.14 | vol | 1091 | +0.03% | 1.89 | 0.129 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `cftc_btc_oi` | BTC | 6 d | 0.24 | ret | 1091 | +0.48% | -2.30 | 0.054 | 0.93 | PRICE LINKED PARTIAL NO INCREMENTAL |
| `tga_btc` | BTC | 2 d | 0.05 | abs | 1091 | +0.10% | -2.33 | 0.106 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `gh_push` | BTC | 2 d | 0.11 | vol | 489 | +1.00% | -2.35 | 0.032 | 0.93 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `gh_merged_pr` | BTC | 2 d | 0.05 | abs | 259 | +4.38% | 2.32 | 0.005 | 0.66 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `gh_actors` | BTC | 2 d | 0.05 | vol | 489 | -0.30% | -0.47 | 0.690 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `gh_btc_stars` | BTC | 2 d | 0.18 | vol | 488 | +0.89% | -2.46 | 0.051 | 0.93 | PRICE LINKED PARTIAL NO INCREMENTAL |
| `fear_greed` | BTC | 1 d | 0.49 | vol | 1091 | +0.12% | 1.93 | 0.180 | 0.97 | PRICE DERIVATIVE ONLY REJECT |
| `hn_btc` | BTC | 2 d | 0.08 | vol | 996 | +0.27% | -1.83 | 0.100 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `wiki_Bitcoin` | BTC | 2 d | 0.34 | vol | 1091 | +0.62% | -2.68 | 0.037 | 0.93 | PRICE LINKED PARTIAL NO INCREMENTAL |
| `wiki_Cryptocurrency` | BTC | 2 d | 0.20 | ret | 1091 | +0.05% | -0.91 | 0.261 | 0.97 | PRICE LINKED PARTIAL NO INCREMENTAL |
| `bn_toptrader_ls_pos` | BTC | 0 d | 0.07 | ret | 1055 | +0.24% | -1.81 | 0.154 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `bn_ls_ratio` | BTC | 0 d | 0.46 | abs | 1055 | +0.58% | -2.23 | 0.126 | 0.97 | PRICE DERIVATIVE ONLY REJECT |
| `bn_taker_ls_vol` | BTC | 0 d | 0.10 | abs | 1055 | -0.14% | 0.85 | 0.662 | 0.97 | PRICE DERIVATIVE ONLY REJECT |
| `tga_gold` | GOLD | 2 d | 0.03 | abs | 803 | +0.19% | 1.75 | 0.156 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `cftc_gold_mm` | GOLD | 6 d | 0.07 | ret | 768 | -0.19% | -1.09 | 0.433 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `wiki_gold` | GOLD | 2 d | 0.07 | vol | 777 | +0.55% | -1.53 | 0.144 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `cftc_wti_mm` | CRUDE | 6 d | -0.01 | vol | 763 | -0.61% | 0.31 | 0.694 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `eia_crude` | CRUDE | 7 d | -0.01 | ret | 769 | +0.49% | 1.81 | 0.089 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `pw_Strait_of` | CRUDE | 10 d | 0.07 | ret | 778 | +0.16% | 1.85 | 0.216 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `pw_Suez_Canal` | CRUDE | 10 d | 0.06 | ret | 778 | +0.30% | -1.88 | 0.129 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `pw_Bab_el-Mandeb` | CRUDE | 10 d | 0.03 | abs | 778 | -0.03% | 0.82 | 0.558 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `eia_gas` | NATGAS | 7 d | 0.03 | vol | 760 | -0.10% | 0.56 | 0.580 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `hdd_us5` | NATGAS | 7 d | 0.02 | ret | 549 | -0.72% | -0.05 | 0.775 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `cdd_us5` | NATGAS | 7 d | 0.03 | vol | 544 | -0.11% | -0.79 | 0.463 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |

_ΔR²oos = out-of-sample R² gain of baseline+feature over baseline (expanding window, first 50 % train); negative = feature hurt out of sample. 'Best target' is chosen by min p, i.e. optimistic; the BH q already accounts for all 132 tests._

## Independent but unproven

Features with price-side adj-R² < 0.15 carry information that is *not* a repackaging of price-side variables (e.g. `bc_hash-rate` 0.00, `bc_n-transactions` 0.02, `tga_btc` 0.05, `eia_crude` −0.02, `pw_*` < 0.08). Independence is a necessary, not sufficient, condition: none of them showed incremental predictive value here.
