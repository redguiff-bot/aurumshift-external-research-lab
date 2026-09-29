# 05 — Real economy: shipping, energy inventories, weather, government datasets

## Sources

* **IMF PortWatch (ArcGIS FeatureServer)** — 3/3 calls HTTP 200; median 630 ms. AIS nowcast revised (DOC); publish weekly; vintage capture needed. **PARK** — Genuinely new real-economy data (independent of price, R2adj <0.08) but nowcast is revised and null for crude in this test; keep for vintage-captured study.
* **Baltic Dry Index / freight indices** — not executed (no keyless endpoint). not executed. **PARK** — Paid; not executed.
* **AIS open feeds (AISHub, GFW)** — not executed (no keyless endpoint). not executed. **PARK** — Needs account/receiver sharing; not executed.
* **EIA weekly petroleum/gas files (xls)** — 3/3 calls HTTP 200; median 10257 ms. release calendar documented; final values only. **ADAPT** — Scheduled, official, independent of price (R2adj ~0); null for WTI here (single 3-year sample, 173 weeks). Weekly frequency limits power.
* **EIA API v2** — 0/3 calls HTTP 200; non-200: 403. same as files; key needed (not executed). **PARK** — Same data as files; key required, not executed.
* **GIE AGSI+ EU gas storage** — HTTP 200 x3 but body is a key-required error (no data); not executed. updatedAt field documented (DOC) but key needed (not executed). **PARK** — Requires key; not executed; EU gas storage relevant to gas only.
* **Open-Meteo archive / historical-forecast** — 0/6 calls HTTP 200; non-200: 429. archive=ERA5 reanalysis NOT PIT; historical-forecast API (stored runs) is PIT-like (DOC) but was rate-limited (OBS 429). **PARK** — Archive is ERA5 reanalysis (NOT PIT); PIT-like historical-forecast API rate-limited (429) from this egress. HDD/CDD null for natgas here.
* **NWS api.weather.gov** — 3/3 calls HTTP 200; median 505 ms (landing page only; no forecast data probed). forecast text replaced; forward capture. **PARK** — Forecast text replaced; needs forward capture; not tested.
* **NOAA NDBC buoys realtime** — 3/3 calls HTTP 200; median 682 ms. rolling 45 d. **PARK** — Rolling 45 d; niche.
* **Treasury FiscalData DTS (TGA)** — 3/3 calls HTTP 200; median 803 ms. record_date only; release rule T+1 documented. **ADAPT** — TGA liquidity series independent of price (R2adj 0.05); null for BTC/gold in this test; PIT via T+1 rule; low cost to keep capturing.
* **NY Fed markets (RRP/SOFR)** — 3/3 calls HTTP 200; median 662 ms. revisionIndicator present but no vintage store (see report 005). **PARK** — Covered in report 005; not re-tested here.

## Observations

* Commodity targets are Yahoo *unofficial* continuous front-month futures (unadjusted, roll jumps winsorised at 0.5/99.5 %) — baseline for these assets has **no funding/OI** (they do not exist); price/volume/volatility only. This is a weaker baseline than BTC's.
* **Weather:** the executed archive is ERA5 reanalysis — hindsight-assimilated, *not* point-in-time; results are an upper bound and the feature is LOOKAHEAD_RISK. The PIT-like `historical-forecast` API returned HTTP 429 ('Daily API request limit exceeded') from the shared egress (OBS).
* **PortWatch** ArcGIS pagination: `resultRecordCount=2000` is silently capped by the server's `exceededTransferLimit`; a first naive loop stopped at 250 rows (bug found and fixed, 1215 rows retrieved).
* EIA `xls` files were slow (median ~10 s per call, OBS) but complete; `api.eia.gov` needs a key (HTTP 403 without).

## Incremental-information results

| Feature | Asset | Pub. lag used | Price-side adj-R² | Best target (min CW p) | n | ΔR²oos | NW t | CW p | BH q | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| `tga_btc` | BTC | 2 d | 0.05 | abs | 1091 | +0.10% | -2.33 | 0.106 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `tga_gold` | GOLD | 2 d | 0.03 | abs | 803 | +0.19% | 1.75 | 0.156 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `eia_crude` | CRUDE | 7 d | -0.01 | ret | 769 | +0.49% | 1.81 | 0.089 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `pw_Strait_of` | CRUDE | 10 d | 0.07 | ret | 778 | +0.16% | 1.85 | 0.216 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `pw_Suez_Canal` | CRUDE | 10 d | 0.06 | ret | 778 | +0.30% | -1.88 | 0.129 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `pw_Bab_el-Mandeb` | CRUDE | 10 d | 0.03 | abs | 778 | -0.03% | 0.82 | 0.558 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `eia_gas` | NATGAS | 7 d | 0.03 | vol | 760 | -0.10% | 0.56 | 0.580 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `hdd_us5` | NATGAS | 7 d | 0.02 | ret | 549 | -0.72% | -0.05 | 0.775 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |
| `cdd_us5` | NATGAS | 7 d | 0.03 | vol | 544 | -0.11% | -0.79 | 0.463 | 0.97 | INDEPENDENT NO INCREMENTAL EVIDENCE |

_ΔR²oos = out-of-sample R² gain of baseline+feature over baseline (expanding window, first 50 % train); negative = feature hurt out of sample. 'Best target' is chosen by min p, i.e. optimistic; the BH q already accounts for all 132 tests._
