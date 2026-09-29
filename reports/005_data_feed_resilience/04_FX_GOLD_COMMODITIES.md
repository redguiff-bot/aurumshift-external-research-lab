# 04 — FX, gold/metals, commodities

Code: `py/sweep2.py`, `py/fxgold.py`, `py/macro.py`. Results: `results/fxgold_bulk.json`, `results/macro_tests.json`.

## Gold snapshot cross-check (2026-09-29T13:02:35Z; single snapshot, not a series)
| Source | price | vs gold-api XAU (4152.40) | nature |
|---|---|---|---|
| gold-api.com XAU | 4152.40 | — | spot snapshot (`updatedAt` 2026-09-29T13:02:10Z) |
| Swissquote XAU/USD standard | 4152.875 / 4153.565 (bid/ask) | +0.01% / +0.03% | quote, spread ≈ 0.69 USD |
| Hyperliquid `xyz` dex GOLD | 4153.05 | +0.02% | perp mid |
| OKX XAUT-USDT | 4155.2 | +0.07% | tokenised gold, USDT-quoted |
| Kraken XAUTUSD | 4154.3 | +0.05% | tokenised gold |
| Kraken PAXGUSD | 4160.29 | +0.19% | tokenised gold |
| Coinbase PAXG-USD | 4161.26 | +0.21% | tokenised gold |
| Deribit PAXG_USDC-PERPETUAL | 4168.87 | +0.40% | perp on tokenised gold |
| Yahoo GC=F | 4186.6 | +0.82% | COMEX futures (contango/roll, different instrument) |
| Yahoo XAUUSD=X | no data | — | probe returned no result |

Reading (OBSERVED): spot-like sources agree within ~3 bps of each other; tokenised gold trades 5–20 bps above; the futures contract carries ~80 bps. Different instruments, so no source is treated as reference. Gold 24/7 proxies were also fetched as 1H bars on Kraken (PAXG, XAUT), OKX (XAUT), Coinbase (PAXG), Deribit (PAXG perp) — schemas match their BTC counterparts. **LBMA** gold AM/PM benchmark JSON: 14,844 daily rows from 1968-01-02 to 2026-09-28 (OBSERVED); redistribution terms restrictive per IBA (docs quote is for platinum/palladium; gold terms unverified).
**Dukascopy** XAUUSD tick file for 2024-01-02 10h decoded: 4,969 ticks (first ask/bid 2077.255/2076.965), i.e. usable keyless historical ticks; candle endpoints returned HTTP 429 after a few requests (OBSERVED rate-limit enforcement). Licence: non-commercial (docs quote).

## FX (EURUSD and majors)
* **ECB SDMX** (`EXR/D.USD.EUR.SP00.A`): 8 latest daily fixes retrieved; back to 1999-01-04; `updatedAfter` accepted; CSV carries OBS_STATUS.
* **Frankfurter**: 10 daily values 2026-09-15…09-28 — the 8 overlapping dates equal ECB to 4 decimals (derived from ECB, not independent).
* **Alpha Vantage demo key** EURUSD 2026-09-28: O 1.13840 H 1.13910 L 1.13520 C 1.13700; **Twelve Data demo** 2026-09-28: C 1.13716; **ECB fix** 1.1378 (14:15 CET) — differences of 0.6–0.8 pips reflect different cut-off times, not error.
* **Yahoo EURUSD=X** daily closes track ECB within ~10 pips on shared dates but the 2026-09-28 close is `null` (OBSERVED) — null closes must be handled.
* **BoE IADB** GBP/USD XUDLUSS daily CSV; **BoC Valet** FXUSDCAD JSON; **open.er-api** latest only (updates once a day, `time_next_update_utc`); **fawazahmed0** CDN snapshot.
* Intraday FX keyless: only Yahoo (unofficial, 429 seen) and Dukascopy ticks (non-commercial). No keyless official intraday FX source found.

## Commodities / energy
* Keyless price feeds: **Yahoo chart** — CL=F, BZ=F, HG=F, SI=F, DX-Y.NYB each returned 106 hourly bars/5 d (NG=F got HTTP 429, retry not attempted); GC=F 534 one-minute bars/day with 0 null closes.
* **CFTC COT** (Socrata): weekly positioning incl. GOLD–COMEX (OI 412,800 on 2026-09-22) and PAX GOLD PERP STYLE (Coinbase Derivatives, OI 1,310); history from 1986-01-15.
* **World Bank Commodity Pink Sheet** monthly XLSX downloaded (765 KB); **EIA** needs a free key (HTTP 403 API_KEY_MISSING) — NOT executed; **FRED** WTI/gold series not reachable from the test egress.
* No keyless official *intraday* energy or base-metal feed was found. Exchange-native crypto perps on commodities exist (Hyperliquid `xyz` dex lists ALUMINIUM plus equities, e.g. mid 3080.0) — venue/instrument risk, not evaluated as a commodity price source.
