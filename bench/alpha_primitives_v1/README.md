# bench/alpha_primitives_v1

Code and derived results for `reports/011_alpha_primitives/`. External research only; no private AurumShift code; public data, no keys.

Pipeline (run from `py/`, needs `pip install numpy pandas scipy pyarrow requests`):
1. `fetch_binance_vision.py [SYM…]`, `fetch_other.py` (Deribit DVOL, Coinbase), `fetch_hl.py` (Hyperliquid funding) → `data/*.parquet` (≈400 MB, git-ignored).
2. `data_audit.py` → `results/data_audit.json`.
3. `run_main.py` → `results/main_results.json`, `pnl_primary.parquet` (hourly, git-ignored), `signals_daily.parquet`.
4. `lookahead_test.py` → `results/lookahead_test.json` (truncation test + leaky negative control).
5. `falsify.py` → `results/falsification.json` (stress battery, placebo, planted-signal controls).
6. `exploratory_followup.py` → `results/exploratory_followup.json` (non-primary, not adjudicated).
7. `analysis.py` → `results/tables/*.md`, `results/adjudication.json`; `gen_contracts.py` / `gen_reports.py` → `reports/011_alpha_primitives/`.

`primitives.py` = the 15 executed primitives; `catalog.py` = contracts + discovered-not-executed list; `lib.py` = panel loader, overlapping-tranche simulator, NW statistics.
`results/final_block.txt` holds the final block. Results depend on the wall-clock snapshot (2026-09-29) and provider histories.
