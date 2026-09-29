# 03 — News, RSS, social, search/trend, prediction markets

## Sources

* **GDELT DOC 2.0 API** — 1/3 calls HTTP 200; non-200: 429; median 24405 ms. DOC API recomputes; bulk GKG/Events files carry DATEADDED (ingest) => bulk files PIT_NATIVE (DOCUMENTED_CLAIM, not executed). **PARK** — server limit is 1 request per 5 s (429 on 2 of 3 probes spaced 2.5 s; the third returned 200); DOC API is rolling ~3 months so cannot support a 3-year test. Bulk GKG/Events (DATEADDED) is the PIT-friendly route: not executed.
* **Crypto-news RSS (Cointelegraph)** — 3/3 calls HTTP 200; median 454 ms. no history at all; pubDate publisher-set; forward capture with own receipt stamp. **PARK** — No history; usable only via forward capture with receipt stamps; value untested.
* **Federal Reserve press RSS** — 3/3 calls HTTP 200; median 397 ms. no deep history in feed; forward capture. **PARK** — Event calendar/PIT value plausible for event studies; not tested here.
* **Hacker News (Algolia)** — 3/3 calls HTTP 200; median 459 ms. created_at_i is post time; counts retro-change via deletions/flags => use item timestamps not nbHits (nbHits inexact OBS). **ADAPT** — Free, PIT-native item timestamps, independent of price (R2adj 0.08); tested null. Use item-level created_at rather than nbHits. Cheap forward test candidate.
* **StockTwits symbol stream** — 3/3 calls HTTP 200; median 503 ms. recent window only. **PARK** — Recent window only; redistribution forbidden (DOCUMENTED_CLAIM).
* **Reddit .json listing** — 0/3 calls HTTP 200; non-200: 403. blocked from test egress; recent 1000 only. **REJECT** — Blocked from egress (403) and restrictive terms (DOCUMENTED_CLAIM).
* **Bluesky AppView** — 2/3 calls HTTP 200; non-200: None; median 534 ms. createdAt client-declared; use indexedAt from own firehose capture. **PARK** — Reachable via public AppView but 1/3 probe failed with 401/None; social coverage of finance small and client-declared createdAt.
* **Google Trends (unofficial)** — 0/3 calls HTTP 200; non-200: 404. re-sampled every request; no official API. **REJECT** — No official API; every query re-sampled; scraping prohibited (DOCUMENTED_CLAIM); no PIT possible.
* **Wikimedia pageviews REST** — 2/3 calls HTTP 200; non-200: 429; median 394 ms. day-bucket, finalised next day, classification refinements retro; no per-row publication time. **PARK** — Attention proxy is largely a price reaction (Bitcoin views R2adj 0.34, Cryptocurrency 0.20); null incremental. Keep only as a control.
* **alternative.me Fear & Greed** — 3/3 calls HTTP 200; median 337 ms. no publication time, methodology undisclosed; price-derived anyway. **REJECT** — Composite includes volatility/momentum/volume (documented) and is 49 % explained by the price-side matrix: PRICE_DERIVATIVE_ONLY.
* **Polymarket Gamma+CLOB** — 6/6 calls HTTP 200; median 471 ms. trades/price points carry event time; resolution state is mutable. **ADAPT** — PIT-native trade/price time, fully independent by construction; contracts are short-lived so no long history to test; needs forward capture on a fixed basket of macro/crypto markets.
* **Kalshi public market data** — 3/3 calls HTTP 200; median 390 ms. trades timestamped; settlement final. **ADAPT** — Same rationale as Polymarket; macro contracts (CPI/Fed) are the more relevant class; not tested.

## Observations

* **News/RSS have no free deep history through their live endpoints** (RSS ~30 items; GDELT DOC rolling window and 429 from this egress). A news study is possible only with GDELT bulk files or forward capture; neither was executed, so **news was not tested** (missing evidence, not negative evidence).
* **Prediction markets** are the cleanest PIT-native class found (trade time on each print) but individual contracts are short-lived, so a 3-year daily incremental test is not constructible from what is public without a fixed basket of rolling contracts. **Not tested.**
* **Attention data are mostly price reactions:** Wikipedia 'Bitcoin' pageviews are explained 34 % (adj-R²) by same-week price-side variables; Fear & Greed 49 %.

## Incremental-information results

| Feature | Asset | Pub. lag used | Price-side adj-R² | Best target (min CW p) | n | ΔR²oos | NW t | CW p | BH q | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| `fear_greed` | BTC | 1 d | 0.49 | vol | 1091 | +0.12% | 1.93 | 0.180 | 0.97 | PRICE DERIVATIVE ONLY REJECT |
| `hn_btc` | BTC | 2 d | 0.08 | vol | 996 | +0.27% | -1.83 | 0.100 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `wiki_Bitcoin` | BTC | 2 d | 0.34 | vol | 1091 | +0.62% | -2.68 | 0.037 | 0.93 | PRICE LINKED PARTIAL NO INCREMENTAL |
| `wiki_Cryptocurrency` | BTC | 2 d | 0.20 | ret | 1091 | +0.05% | -0.91 | 0.261 | 0.97 | PRICE LINKED PARTIAL NO INCREMENTAL |
| `wiki_gold` | GOLD | 2 d | 0.07 | vol | 777 | +0.55% | -1.53 | 0.144 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |

_ΔR²oos = out-of-sample R² gain of baseline+feature over baseline (expanding window, first 50 % train); negative = feature hurt out of sample. 'Best target' is chosen by min p, i.e. optimistic; the BH q already accounts for all 132 tests._
