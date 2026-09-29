# bench/alternative_data_v1 — free/public alternative-data discovery

External research only (no private AurumShift code, no integration). Report: `reports/016_alternative_data/`.

## Layout
| path | purpose |
|---|---|
| `py/probe_all.py` | live probe of ~97 endpoints (status, 3-sample latency, size, history bounds, freshness, stamp/rate-limit headers) → `results/probe_results.json`. **`parsed_ok` is unreliable for 3 placeholder extractors (AISHub, GIE AGSI, Etherscan V1 → auth errors); `py/catalog.py` overrides them.** |
| `py/pit_probes.py` | PIT/revision probes: GDELT file stamps, GH Archive, Binance Vision restatement scan, CFTC `:created_at`, Coin Metrics completion/status-time, Kalshi/Polymarket depth, RSS retention, Wayback attempt → `results/pit_probes.json` |
| `py/licenses.py` | fetches provider terms pages, keyword evidence → `results/license_evidence.json` |
| `py/collect.py`, `py/collect_rest.py` | pull daily research panels into `data/` (re-runnable; `collect_rest` = rate-limited Wikimedia/npm/Deribit with back-off) |
| `py/fetch_eia.py` | EIA bulk zips → `data/raw/` (gitignored, ~60 MB) |
| `py/panel.py` | decision-time panel builder (baseline features, availability lags) |
| `py/analysis_crypto.py` | incremental-information tests on BTC/ETH (`ALT_NO_CALENDAR=1` reproduces the first-pass baseline) → `results/incremental_results*.csv` |
| `py/summarize.py` | applies the pre-declared classification → `results/candidate_summary.csv`, `results/summary.json` |
| `py/real_economy.py`, `py/real_economy_robust.py` | EIA crude/gas, CPC weather, PortWatch tests + placebo/sub-period robustness (`ALT_NO_WINSOR=1` = raw returns) |
| `py/catalog.py`, `py/gen_reports.py` | source catalogue → renders the 11 report files |

## Reproduce
```
pip install requests pandas numpy scipy statsmodels
cd bench/alternative_data_v1/py
python collect.py && python collect_rest.py && python fetch_eia.py
python probe_all.py && python pit_probes.py && python licenses.py
python analysis_crypto.py && ALT_NO_CALENDAR=1 python analysis_crypto.py && python summarize.py
ALT_NO_WINSOR=1 python real_economy.py && python real_economy.py && python real_economy_robust.py
python gen_reports.py
```
Network results depend on the sandbox egress IP (shared quotas, geo-blocks) and on the run date; committed `results/` are the run of 2026-09-29. `data/um_metrics_5m_*.csv.gz` (40 MB) and `data/raw/` are gitignored; daily aggregates `data/um_metrics_daily_*.csv` are committed.
