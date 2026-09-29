# 00 — Executive summary: external alpha-primitive discovery V1

Mission `AURUMSHIFT_EXTERNAL_ALPHA_PRIMITIVE_DISCOVERY_V1`. EXTERNAL_RESEARCH_ONLY — no private AurumShift code, no integration, no production-profitability claim. Snapshot date 2026-09-29. Code and raw derived results: `bench/alpha_primitives_v1/`.

## What was done
- Discovered **34** candidate primitives across the 18 requested families (landscape in 01, contracts in 02), read from papers/working papers/OSS/exchange & vendor research (source verification status is recorded per source; several are only DOCUMENTED_CLAIM).
- **Executed 15** with contracts (mechanism, formula, inputs, sampling, horizon, failure modes, lookahead risks, sign, mode, horizon) **written and committed before the full run**. Universe: 10 Binance USD-M majors, hourly, 2023-01 → 2026-08 (DEV 2023–24 / TEST 2025–26), plus a 6-asset holdout universe and Coinbase spot bars for a wrong-venue test. Data: Binance Vision bulk, Deribit DVOL, Hyperliquid funding, Coinbase candles (04).
- Forward-safety: all 15 pass an empirical truncation test (a deliberately leaky control fails it, as it must); none uses centered filters, revised macro values or future-normalised features (03).
- Orthogonality, regime conditioning, cost sensitivity (×0.5…×5, funding charged from real data) and a 9-way falsification battery, plus a 150-run placebo and a planted-signal control to calibrate the pipeline (05–09).

## Result (one paragraph)
**No executed primitive shows a statistically supported net-of-cost edge.** On the pre-declared primary specs the best full-sample gross Sharpe is +0.71 (P08 OI/price, NW t=1.60) and the best net Sharpe is +0.24 (P06 funding carry, t=0.44) — inside the placebo noise band (150 random smoothed signals: gross-t sd 0.94, p95 1.58, p99 2.05). Six of fifteen primitives (P03, P07, P10, P11, P12, P13) are net-negative with high statistical confidence (net t from −4.4 to −31): five of them trade 2.7–8.4 gross-exposure turns/day at 6–10 bps per side, which outweighs any gross edge (P11 additionally has negative gross). The two slow, low-turnover primitives with non-negative net point estimates (P06 carry, P14 VRP) are statistically indistinguishable from zero and P06 flips sign between DEV and TEST. P01, P05, P08 (and P06, P13) earn positive gross in 2023–24 and decay to ≈0 or negative in 2025–26; only P02 and P04 keep a positive (insignificant) gross Sharpe in both halves. Zero primitives meet the pre-declared support rule (C1∧C2∧C3), so zero are non-redundant or regime-dependent candidates by rule.

Several *non-primary* specs show large gross t-stats (e.g. cross-sectional hour-of-day seasonality P13|CS|H4, gross Sharpe 2.8, t=5.3) but with break-even costs of only 0.18× the assumed costs, i.e. they are cost-dominated leads, not candidates (exploratory; multiple-testing caveat; 09).

## What this does and does not say
- It says: at hourly resolution, with generic taker-type costs, on 10 liquid perps over 3.7 years, none of these 15 public-data primitives clears a pre-declared, multiple-testing-controlled net bar, and the pipeline is demonstrably able to detect a planted signal and to reject random ones.
- It does **not** say no edge exists: statistical power is limited (Sharpe s.e. ≈ 0.5 over 3.7y ⇒ a true net Sharpe below ≈1 is undetectable), costs are generic, only public data at ≥1h resolution was used, and maker/queue execution, order-book features, tick-level flow, macro-event and term-structure primitives were not executed (11).
- No drop-in strategy: primitives are standalone probes, not tuned or combined.

## Final block
```
PRIMITIVES_DISCOVERED=34
PRIMITIVES_EXECUTED=15

FORWARD_SAFE_COUNT=12            # strict class FORWARD_SAFE (+16 FORWARD_SAFE_WITH_RECEIPT_STAMP, 1 OFFLINE_ONLY)
LOOKAHEAD_RISK_COUNT=5          # all among the discovered-not-executed variants; 0 of 15 executed

NONREDUNDANT_CANDIDATES=0
REGIME_DEPENDENT_CANDIDATES=0

NET_POSITIVE_EXTERNAL_CANDIDATES=0

ANY_DROP_IN_STRATEGY=FALSE
LOCAL_INTEGRATION_AUTHORIZED=FALSE

FINAL_VERDICT=NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED
```

Counting notes: FORWARD_SAFE_COUNT is the strict class count over all 34 discovered primitives (12); with receipt-stamp-dependent ones the forward-safe-in-principle total is 28. LOOKAHEAD_RISK counts discovered variants that are lookahead-prone as commonly implemented (smoothed HMM, centered filters, full-sample normalisation, forward-RV VRP, in-progress-bar squeeze); none was executed as such. NET_POSITIVE_EXTERNAL_CANDIDATES counts primitives meeting C1∧C2∧C3 (10); two primitives have small positive full-sample net point estimates (P06 +0.24, P14 +0.09 Sharpe) that fail C2 and C3.

## Reports
01 landscape · 02 contracts (pre-declared) · 03 forward safety · 04 public data · 05 results · 06 orthogonality · 07 regime-conditional · 08 cost sensitivity · 09 falsification · 10 adjudication (ADOPT/ADAPT/PARK/REJECT) · 11 limitations.
