# 02 — Data: collectors, downloaders, calendars, quality, storage

Raw evidence: `bench/oss_trading_infra_v1/results/t08*, t09*, t10*, t11*, t14*`.

## Collectors / downloaders (T11, live network from the sandbox egress, 2026-09-29)
* **ccxt 4.5.84 REST** — OBSERVED: `fetch_ohlcv('1m', limit=60)` succeeded on 6 of 8 venues (Kraken, Coinbase, OKX, Bitstamp, Gate, KuCoin): identical 6-column rows, 0 duplicates, strictly monotonic, step 60 000 ms. Binance (HTTP 451) and Bybit (HTTP 403) were blocked by the egress (same as report 005; not a library verdict).
  * **Forming bar is returned and not flagged** on all 6 venues (last bar opened 10–58 s earlier) — the caller must drop it. OBSERVED.
  * No receipt/ingest timestamp in REST rows or in ccxt.pro trades (keys: amount,cost,datetime,fee,fees,id,info,order,price,side,symbol,takerOrMaker,timestamp,type). OBSERVED. A PIT consumer must stamp receipt itself.
  * Sandbox-specific: ccxt ignores `REQUESTS_CA_BUNDLE`; `verify=self.verify and self.validateServerSsl` collapses a CA path to `True`, so the CA path had to be set through `validateServerSsl` (REST) and `ssl_context` (ccxt.pro). TLS verification stayed on. OBSERVED, egress-specific.
  * ccxt.pro websocket trades: Kraken 27 trades/12 s, Coinbase 171/12 s; OKX websocket timed out (cause UNKNOWN). Latencies in T11 include the implicit `load_markets` call.
* **cryptofeed 2.5.0** — OBSERVED: Kraken BTC-USD, 15 s: 25 trades and 3 991 L2 updates; each callback receives `(data, receipt_timestamp)` — trade `timestamp` 4.1 ms before `receipt` in the sample. This is the only executed collector that hands over a local receipt time natively. Licence hazard: latest 3.0.1 is AGPL-3.0+ and needs Python ≥3.13; the executed 2.5.0 declares XFree86-1.1 (DOCUMENTED_CLAIM from metadata). Single dominant maintainer (74 % of 12 m commits).
* **yfinance 1.7.0** — OBSERVED: BTC-USD 1m (1 081 rows) and SPY 1d worked. Unofficial Yahoo endpoint; ToS/stability risk (INFERENCE; report 005 covered Yahoo).
* **binance-public-data / dukascopy-node** — not executed here; bulk-file behaviour (checksums, ms→µs unit switch on spot files) is already OBSERVED in report 005. Repo dormant since 2025-01 (binance-public-data). ADOPT_REFERENCE only as file-layout spec.
* **databento-dbn** — PARTIAL: `MBOMsg` carries `ts_event`, `ts_recv`, `ts_in_delta`, `ts_out`, `sequence`, `flags` (OBSERVED from the record type). The offline encode/decode roundtrip was not completed (Metadata constructor signature mismatch) → roundtrip UNKNOWN. The paid API/client was not exercised.

## Market calendars (T08)
Known-answer set: NYSE 2024–2025 full holidays (21), early closes (6), DST open times (4 dates). Both libraries: 21/21 holidays, 0 extra closures, 6/6 early closes, identical UTC opens across the March/November DST transitions. OBSERVED. Caveat: the expected list was compiled by the tester from published NYSE schedules (not re-fetched in this run) — INFERENCE for the expected side; the two libraries are independent implementations and agree.
* exchange_calendars: 71 exchange calendars incl. 24/7; default window 2006-09-29 → 2027-09-29 (rolling ±1 y bound; must be widened for longer horizons).
* pandas_market_calendars: 211 calendars incl. 24/7, several CME/CBOT, FX; schedule available to 2035 in the test.

## Data-quality frameworks (T09)
200 000 one-minute bars; clean frame + 12 single-defect variants taken from report-005 hazards (duplicate ts, non-monotonic, high<low, close>high, negative volume, null, ms→µs unit switch, missing minutes, flat zero-volume run, ×10 spike, future timestamp, stale repeated bar). Derived columns (dt, |return|, run lengths) were computed once outside every framework.

| Framework | clean passes | defects detected | clean-run time | native vs custom |
|---|---|---|---|---|
| pandera 0.33.1 | yes | 12/12 | 0.11 s | monotonic and cross-column need lambdas |
| great_expectations 1.23.2 | yes | 12/12 | 0.23 s | monotonic (`BeIncreasing`) and pairwise A≥B are native |
| pointblank 0.27.0 | yes | 12/12 | 1.33 s | cross-column native; monotonic not native |
| frictionless 5.19.1 | yes | 5/12 (nulls, unique, ranges only) | 4.76 s | no cross-column / sequence checks |

Limit: several defects trip more than one rule, so "detected" is not attributed to a specific rule. A first frictionless run reported clean=fail because of its unsafe-path rule (fixed with `basepath`) — an operator-experience cost.

## Time-series storage (T10, 1 M rows × 5 float/int columns)
* **ArcticDB 6.26.0 (LMDB)** — OBSERVED: write 0.114 s, read 0.014 s, 41.8 MB on disk, frame equal except index `freq` attribute. Versioning works: `update` created version 1; `as_of=0` and `as_of=<timestamp before update>` return the original, `as_of=<after>` the correction; snapshots survive symbol delete; out-of-order append is rejected. **But** `prune_previous_versions` removes history, any writer can `delete`, `write()` has no timestamp/known-at argument (version time is stamped by the writing process — INFERENCE), LMDB backend is single-writer (DOCUMENTED_CLAIM). It is a *second datastore* and licence is BSL 1.1.
* **DuckDB + Parquet** — OBSERVED: write 0.134 s, read 0.223 s, 34.7 MB; no native versioning; PIT must be modelled with a `known_at` column (report 004). `ASOF JOIN` remains a PIT hazard unless the input is pre-filtered.
No executed OSS store supplies *enforced append-only + server-side receipt time + revision identity* — that remains a database-design concern (report 004), not a library one.
