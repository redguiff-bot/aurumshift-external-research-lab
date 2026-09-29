# 02 — Protocol (pre-registered in `configs/protocol.json`, committed before any real held-out access)

- **Data (OBSERVED):** hourly klines, Binance Vision public API, 20 000 bars/market, window 2024-05-20 → 2026-09-01 (manifest with sha256 in `raw/manifest.json`), 10 markets: discovery {BTC, ETH, BNB, SOL, XRP, ADA}, unseen {DOGE, LINK, LTC, AVAX} (evaluated only in the held-out time segment; never used in any fit).
- **Primitives (20):** returns 1/4/12/24/72h, vol 24/72h, ranges, log-volume/quote-volume/trade-count vs 72h mean, taker-buy share (1h, 24h), close location, distance to 24h high/low, MA24/MA72 ratios, Amihud-like illiquidity. Each causally rolling-z-scored (W=500) ⇒ dimensionless.
- **Target:** `y = log(c[t+4]/c[t]) / (σ24_t·√4)`, clipped ±6. Not a feature.
- **Splits (time, identical rows for all markets):** discovery-train 0–50 %, validation 50–70 %, held-out 70–100 %; 24-bar embargo/purge between segments (> 4-bar label overlap).
- **What each segment may do:** train → all fitting, screening, orientation (sign) and standardisation freezing; validation → gate (same sign, ≥70 % market agreement, p<0.10 block-bootstrap) and final selection (greedy BIC-penalised incremental validation R² over raw ridge, `k_new = 1+nodes/4`, ≤8 features); held-out → evaluated **once**, on a frozen list whose sha256 is written to `results/real/lock_<seed>.json` *before* the held-out is touched (asserted by `tests/test_isolation.py::test_heldout_untouched_before_lock`, and by `access_order` stored in every result).
- **Held-out "stable" =** pooled IC>0 with the same sign as validation, |IC|≥0.005, BH q≤0.10 over the frozen list (time-block bootstrap, block 48, shared across markets to preserve cross-market dependence), ≥70 % of 10 markets same sign, unseen-market pooled IC>0.
- **"New" =** composite/symbolic AND partial IC vs raw primitives ≥0.003 (p<0.10). **Non-redundant =** |corr| <0.8 on validation to earlier kept features.
- **Multiple seeds:** 5 discovery seeds (11–15: subsampling + GP seeds); consensus over seeds (feature must be selected in ≥3/5 seeds and stable in the majority of its appearances). 8 null seeds; 6 synthetic seeds.
- **Multiple markets:** 6 discovery + 4 unseen; synthetic arena 10 markets.
- **Penalties:** BIC parameter/complexity penalty at final selection; node-count complexity term; n_eff = n/4 (overlap).
- **Verdict rules:** in the protocol JSON; validity (synthetic recall ≥0.6 & ≤1 FD/run; null mean stable ≤0.5) is a precondition.

## Deviations disclosed (honest record)
1. After a smoke run on synthetic seed 1 (not reported), I changed (a) the BIC/CMI effective-n divisor to a per-panel attribute (real: 4, synthetic: 1) and (b) synthetic size to T=19 000, β=0.06 so the arena is not trivially under-powered relative to the real panel. The synthetic β was therefore tuned on a smoke seed; the reported 12/12 recovery is a *power demonstration at a chosen effect size*, not a general guarantee. INFERENCE for smaller effects.
2. The invariance Q-test is very sensitive with n_eff in the thousands; the synthetic gated term (strength varies ±30 % by market) is flagged non-invariant in 6/6 runs although its sign is consistent. That is the pre-registered rule working as written, but it is stricter than "same direction everywhere".
3. Decile profiles / provenance fields were added to the result schema after the synthetic batch started; they do not alter any selection logic (synthetic results predate them and lack those fields).
