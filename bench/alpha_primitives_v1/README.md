# bench/alpha_primitives_v1

Code and derived results for `reports/011_alpha_primitives/`. EXTERNAL_RESEARCH_ONLY: public data, no private AurumShift code, no integration.

Run order (from `py/`, `pip install numpy pandas scipy requests`):

1. `fetch_vision.py` — Binance Vision archives (1h spot/perp klines, premium index, funding, daily 5m metrics) into `cache/` (git-ignored, ~few hundred MB uncompressed); writes `results/vision_manifest.json` (sha256 per file).
2. `fetch_xvenue.py` — OKX / Coinbase / Gate / Kraken / Hyperliquid / Deribit DVOL for falsification (`cache/xv/`).
3. Build panel once: `python -c "import alpha_lib as L, pickle; pickle.dump(L.build_panel(), open('../cache/panel.pkl','wb'))"`
4. `s0_tune.py` (DEV-only re-selection for P07/P12; result already baked into `primitives.py` defaults) → `s1_main.py` → `s2_ortho.py` → `s3_regime.py` → `s4_cost.py` → `s5_falsify.py` (~2 min) → `s6_adjudicate.py` → `gen_reports.py` → `gen_reports2.py` (writes the reports and `results/final_block.txt`).

Files: `alpha_lib.py` (loaders, backtest, metrics), `primitives.py` (the 15 executed primitives, pre-registered defaults), `catalog.py` (43-candidate catalogue with contracts and forward-safety class), `common.py` (shared loaders/regimes), `results/*.json` (all derived numbers; every table in the reports is generated from them).

Conventions: bar index = bar open (UTC); decision after bar i uses bars ≤ i and earns bar i+1. GROSS = price + funding before trading costs; NET = after costs (5 bp taker + 1–3 bp slippage/side; unknown = 15 bp). DEV 2024-03-01→2025-05-31, HOLDOUT 2025-06-01→2026-08-31.
