# 02 — Data: collectors, downloaders, calendars, data quality, time-series storage

All numbers are from `bench/oss_trading_infra_v1/results/*.json` produced by the scripts in `py/mt/`. Egress notes: the sandbox reaches Kraken, Coinbase, OKX, Bitstamp, Deribit-via-Tardis and data.binance.vision; Binance API returns 451 and Bybit 403 (egress outcomes, not provider verdicts). A CA path had to be given to ccxt (`validateServerSsl`, TLS verification stays on) because the sandbox re-terminates TLS.

## Collectors and historical downloaders
| Candidate | What was run | Result (label) |
|---|---|---|
| **ccxt** 4.5.84 (MIT) | `fetch_ohlcv(limit=100, 1m)` on 6 venues; `fetch_trades` on Kraken | OBSERVED: kraken/coinbase/okx/bitstamp OK (0.7–2.4 s per call in the saved run, 60 000 ms step, 104 exchanges in the registry); binance 451, bybit 403. **Every** venue's last bar was still forming. Trade objects have `timestamp/datetime/id/price/amount…` but **no local receipt time**. |
| **cryptofeed** 2.4.1 (AGPL) | 20 s live WS trades per exchange, no keys | OBSERVED: Kraken 38 trades, Bitstamp 24; each callback receives a local `receipt` timestamp next to the exchange `timestamp` (first Kraken trade: local receipt stamp **34 ms earlier** than the exchange timestamp — local/exchange clock skew or exchange-side stamping, cause UNKNOWN, but it means receipt-vs-event ordering cannot be assumed; first Bitstamp trade: receipt 4.8 s **after** the exchange timestamp). Coinbase: `401 Unauthorized` on `/api/v3/brokerage/products` (symbol discovery now needs credentials). Needs `asyncio.set_event_loop(new_event_loop())` after `FeedHandler()` on py3.11 + uvloop 0.22 or `run()` raises "no current event loop". |
| **binance-public-data** (no LICENSE file) | `download-kline.py -t spot -s BTCUSDT -i 1m -y 2025 -m 3 -c 1` | OBSERVED: 44 640 rows, 0 duplicates, all steps 60 000 000 (µs) — timestamps are 16-digit **microseconds** in 2025 spot files; `.CHECKSUM` downloaded and sha256 verified **by us** (matched); the script only downloads the checksum file (grep of `utility.py`: no hashing code). |
| **tardis-python** 5.0.1 (MPL-2.0) | `download_datasets(deribit, trades, BTC-PERPETUAL, 2025-03-01)` no key | OBSERVED: keyless first-day-of-month sample, 131 910 rows, columns `exchange,symbol,timestamp,local_timestamp,id,side,price,amount` — a receipt-side `local_timestamp` is present. Other days are commercial (DOCUMENTED_CLAIM). |
| **yfinance** 1.7.0 (Apache-2.0) | `download('AAPL', 5d)` | OBSERVED: 5 rows in 0.7 s; a direct curl to the Yahoo chart endpoint answered 429. Unofficial endpoint → stability/ToS risk (INFERENCE). |
| databento-python, openbb, pandas-datareader, findatapy, freqtrade, hummingbot, LEAN, vnpy | not executed | key required / platform-sized / runtime-authority / low maintenance (see `08`). |

Reading: the OSS layer for **collection** is thin glue over exchange endpoints. `ccxt` is a wrapper-worthy REST client (needs receipt stamping, forming-bar drop, unit normalisation — all still custom, but small); `cryptofeed` is the only tested OSS WS collector that natively hands the consumer a receipt timestamp, at the cost of AGPL and a low-activity single-maintainer repo (39 commits/12 m). `binance-public-data` and `tardis-python` are references for official bulk layouts; neither removes the need for the consumer's own checksum/unit/PIT layer.

## Market calendars (`cal_microtest.py`)
* `exchange_calendars` 4.13.2 vs `pandas_market_calendars` 5.4.0, NYSE 2020-01-02…2026-12-30: **1 758 sessions each, 0 differences**; 14 early closes 2020–2026 identical lists; 2025-01-09 (national day of mourning) and 2026-07-03 are not sessions; 2024-07-03/11-29/12-24 close 17:00/18:00/18:00 UTC in both; NYSE close 21:00 UTC on 2024-03-08 (EST) and 20:00 UTC on 2024-03-11 (EDT) — PROVEN against known dates.
* Other calendars in `exchange_calendars`: `CMES` (255 sessions 2024), XLON (250, 08:00–16:30 UTC), XTKS (244, lunch break), XHKG (242, break), `IEPA` (255 sessions, 01:00–23:00 UTC example); a `24/7` alias exists; 71 canonical calendars vs 211 names in `pandas_market_calendars`.
* `pandas_market_calendars` **requires `exchange-calendars>=3.3`** (its metadata) — it is a layer on top, so it adds no independent second opinion (its own definitions may still differ for calendars it defines itself; not tested).
* Load 0.18 s; 6 months of NYSE minutes 0.09 s. Default bounds 2006-09-29…2027-09-29 → sessions outside the window raise `DateOutOfBounds` (a useful guard).
* `zipline-reloaded` uses the same calendars and **rejects** bars on non-session days at ingest (weekend rows raised `AssertionError … Extra sessions`), i.e. calendar-as-data-gate works out of the box (`zl_microtest.json`).
* Not tested: whether calendar *history* changes between releases (a PIT concern for calendars); pinning the package version is the only control observed.

## Data-quality frameworks (`dq_microtest.py`)
A 3 000-bar 1-minute frame with injected faults (5 high<low, 3 negative close, 3 NaN close, 20 zero-volume flat bars, 2 +30 % spikes, 10 missing minutes, 4 duplicate rows, 1 swapped pair). A plain-pandas reference counts: high<low 5, non-positive 3, duplicates 4, non-monotonic 2, NaN 3, zero-volume 20, missing minutes 10.
| Framework | Native detection | Cost |
|---|---|---|
| **pandera** 0.33.1 | lazy validation → failure-case table (105 rows): uniqueness 8 (= both members of 4 dup pairs), `>0` 3, not-nullable 3, monotonic 1, cross-column high/low checks 42+48 (the composite check also flags rows touched by the injected negative/spike values); missing-minute gaps need a custom check | 0.085 s, 11 MB own, 10 dists |
| **great_expectations** 1.23.2 | unique ts 8, `close>0` 3, not-null 3, `high>=low` 5, volume≥0 pass; `ExpectColumnValuesToBeIncreasing` returned failure without a count; no built-in gap expectation | 0.11 s, 267 MB / 35 dists |
| **frictionless** 5.19.1 | `duplicate-row` 4, `deviated-value` 5 (3σ) on a CSV resource; refuses absolute paths ("not safe") | 0.2 s, 35 MB |
| **pointblank** 0.27.0 | 3 steps on a polars frame reported 2/1/1 failures | young port (92 % one author) |
Reading: no framework understands **time-series continuity** (gaps, forming-bar flat/zero-volume filler, unit changes) natively; that stays custom or a custom check. Pandera is the lightest way to express the row/column invariants; Great Expectations adds 250 MB and concepts for the same seven invariants (INFERENCE on "not justified": the mission's doctrine weights operational cost).

## Time-series storage (PostgreSQL-first)
Sandbox: PostgreSQL 16.15, TimescaleDB 2.30.2 (Timescale apt repo), pg_partman 5.0.1 (Ubuntu package). 3 M tick rows, 20 symbols, one table three ways (`sql/tss_microtest.sql`, raw output `results/tss_microtest.txt`).
| | plain table | native declarative partitions (no extension) | TimescaleDB hypertable |
|---|---|---|---|
| size, uncompressed | 275.4 MB | 276.5 MB | 397.7 MB |
| 1-min OHLC, 1 symbol, 1 day (EXPLAIN ANALYZE) | 10.09 ms | 10.18 ms | **5.62 ms** |
| 1-min bars equal to native partitioning? | — | — | **yes** (md5 of aggregated bars equal) |
| after `compress_chunk` (18 chunks) | — | — | **29.4 MB** (13.5×) |
| continuous aggregate 1-min bars | — | — | 500 001 rows materialised |
* `SHOW timescaledb.license` = `timescale`: compression and continuous aggregates are Timescale-License features, the Apache-2 build does not include them (DOCUMENTED_CLAIM; we ran only the TSL build). Requires `shared_preload_libraries` + server restart + the vendor apt repo (596 MB installed by apt). Availability on managed PostgreSQL is UNKNOWN.
* `pg_partman` `create_parent(... p_premake := 4)` created 10 child tables; it automates what the DO-block above did by hand. Optional convenience, not a capability gap.
* **DuckDB** 1.5.6 as a *compute-only* layer: read-only `ATTACH` of the live PG16 worked (3 M rows scanned, 500 001 minute-groups computed in 1.95 s including the extension download — needs outbound access to the DuckDB extension host at first use); ASOF join equal to pandas and polars (below); Parquet query in place 4.6 ms.
* **ArcticDB** 6.26.0: `read(as_of=version)` and `read(as_of=timestamp)` return the pre-restatement values (native PIT), but it is its own LMDB/S3 store under BSL 1.1 → a second datastore.
* **ClickHouse** (clickhouse-local 26.10): ASOF correct for `>=` and `>` but requires ≥1 equality column, and an unmatched left row is returned as `0` (see `results/clickhouse_local_asof.txt`) — missing evidence becomes a valid-looking number unless `join_use_nulls=1` (DOCUMENTED_CLAIM, not re-tested).
* QuestDB, InfluxDB, VictoriaMetrics: not executed; each is a separate server and datastore.

### ASOF / PIT-join equality (`store_microtest.py`, 50 k trades × 200 k quotes incl. 100 exact-timestamp ties)
| Engine | inclusive (`>=`) | strict (`>`) | time |
|---|---|---|---|
| pandas `merge_asof` | reference | reference | 21 ms |
| polars `join_asof` | equal | equal | 5 ms |
| DuckDB `ASOF LEFT JOIN` | equal | equal | 61 ms (incl. registration) |
Invariant "joined quote ts ≤ (or <) trade ts": 0 violations in DuckDB. Parquet (`pyarrow`, zstd, no dictionary): two writes → identical sha256; 200 k quotes = 1.85 MB.

## What this section supports
* Calendars: `exchange_calendars` — PROVEN on the dates above; pure library.
* PIT joins and interchange: DuckDB/polars/pandas agree; pyarrow bytes are reproducible.
* Storage: an in-PG path exists (native partitioning, or TimescaleDB with the licence caveat); no candidate that needs its own datastore is required to close a *tested* gap.
* Not closed by OSS: collector receipt-stamping/PIT provenance, time-series gap detection, forming-bar handling — all remain small custom layers around ADAPT candidates.
