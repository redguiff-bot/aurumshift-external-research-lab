"""Assemble reports/011_alpha_primitives/*.md from results/tables + hand-written narrative. Numbers in prose were checked against results/*.json at write time; tables are included verbatim."""
import json, os, catalog as C
R = "../../../reports/011_alpha_primitives/"; T = "../results/tables/"; S = "../../../../.claude/scratch/"
SC = "/tmp/claude-0/-home-user-aurumshift-external-research-lab/758a237d-5754-5b30-9051-0d7166f6f084/scratchpad/"
t = lambda f: open(T + f + ".md").read()
adj = json.load(open("../results/adjudication.json")); fin = adj["final"]; cnt = C.counts()
aud = json.load(open("../results/data_audit.json")); LA = json.load(open("../results/lookahead_test.json")); F = json.load(open("../results/falsification.json"))
ex = json.load(open("../results/exploratory_followup.json"))
def w(n, s): open(R + n, "w").write(s)
FINAL = f"""```
PRIMITIVES_DISCOVERED={cnt['discovered']}
PRIMITIVES_EXECUTED={cnt['executed']}

FORWARD_SAFE_COUNT={cnt['fs']}            # strict class FORWARD_SAFE (+{cnt['fsr']} FORWARD_SAFE_WITH_RECEIPT_STAMP, {cnt['off']} OFFLINE_ONLY)
LOOKAHEAD_RISK_COUNT={cnt['la']}          # all among the discovered-not-executed variants; 0 of 15 executed

NONREDUNDANT_CANDIDATES={len(fin['NONREDUNDANT'])}
REGIME_DEPENDENT_CANDIDATES={len(fin['REGIME_DEPENDENT'])}

NET_POSITIVE_EXTERNAL_CANDIDATES={len(fin['SUPPORTED'])}

ANY_DROP_IN_STRATEGY=FALSE
LOCAL_INTEGRATION_AUTHORIZED=FALSE

FINAL_VERDICT=NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED
```"""
open("../results/final_block.txt", "w").write(FINAL.strip("`\n") + "\n")
# ---------------- 00
w("00_EXECUTIVE_SUMMARY.md", f"""# 00 — Executive summary: external alpha-primitive discovery V1

Mission `AURUMSHIFT_EXTERNAL_ALPHA_PRIMITIVE_DISCOVERY_V1`. EXTERNAL_RESEARCH_ONLY — no private AurumShift code, no integration, no production-profitability claim. Snapshot date 2026-09-29. Code and raw derived results: `bench/alpha_primitives_v1/`.

## What was done
- Discovered **{cnt['discovered']}** candidate primitives across the 18 requested families (landscape in 01, contracts in 02), read from papers/working papers/OSS/exchange & vendor research (source verification status is recorded per source; several are only DOCUMENTED_CLAIM).
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
{FINAL}

Counting notes: FORWARD_SAFE_COUNT is the strict class count over all {cnt['discovered']} discovered primitives (12); with receipt-stamp-dependent ones the forward-safe-in-principle total is {cnt['fs']+cnt['fsr']}. LOOKAHEAD_RISK counts discovered variants that are lookahead-prone as commonly implemented (smoothed HMM, centered filters, full-sample normalisation, forward-RV VRP, in-progress-bar squeeze); none was executed as such. NET_POSITIVE_EXTERNAL_CANDIDATES counts primitives meeting C1∧C2∧C3 (10); two primitives have small positive full-sample net point estimates (P06 +0.24, P14 +0.09 Sharpe) that fail C2 and C3.

## Reports
01 landscape · 02 contracts (pre-declared) · 03 forward safety · 04 public data · 05 results · 06 orthogonality · 07 regime-conditional · 08 cost sensitivity · 09 falsification · 10 adjudication (ADOPT/ADAPT/PARK/REJECT) · 11 limitations.
""")
# ---------------- 01
A = open(SC + "landscape_A.md").read(); B = open(SC + "landscape_B.md").read()
w("01_LANDSCAPE.md", f"""# 01 — Landscape: where candidate primitives were discovered

Sources searched (2026-09-29): arXiv/SSRN/RePEc and journal pages, BIS/NY Fed/Bank of Canada working papers, exchange/vendor research (Deribit Insights, Amberdata, K33, Bytetree), serious OSS (CCXT, hmmlearn, ruptures, alphalens-reloaded, Freqtrade, Hummingbot), and the lab's prior corpus (report 005 on public feeds). Two research passes were run by sub-agents; each source carries a status: VERIFIED (page opened, title/authors/year confirmed), PARTIAL (only via search snippet), NON_VÉRIFIÉ. **The lead analyst did not independently re-open every page**; all empirical claims are `DOCUMENTED_CLAIM` (reported by the source, not reproduced here). Formulas labelled generic are standard definitions, not extractions from the PDFs.

## Family → what was found → what was executed
| Family (requested) | Evidence quality found | Executed as | Not executed (see 02 tail) |
|---|---|---|---|
| momentum / trend | crypto trend factor (Fieberg et al., JFQA 2025), intraday TS momentum (Shen et al. 2022) — DOCUMENTED_CLAIM of net survival on wide coin universes | P01 | D24, D27, D28 |
| mean reversion | De Nicola 2021 (1–4h negative autocorr, BTC); Zaremba et al. 2021 (reversal only in illiquid coins) | P03, P11 | — |
| vol compression/expansion | no verified academic crypto source (gap); blogs only | P04 | D34 |
| carry | BIS WP 1087 (Crypto Carry), He–Manela–Ross–von Wachter perpetual-futures paper | P06 | D30, D33 |
| basis | BIS WP 1087; premium-index mechanism | P07 | D16, D17 |
| funding divergence | cross-venue funding differences documented in lab report 005; no verified predictive paper | P15 | — |
| OI / price divergence | no verified academic source on predictive power (gap); vendor/blog narrative | P08 | D20 |
| liquidation pressure | cascade-dynamics papers (2026 arXiv, very recent, not peer-reviewed); no complete public liquidation history | P09 (OI-flush *proxy*) | D21 |
| volume imbalance | Cont–Kukanov–Stoikov OFI (equities), Kim & Hansen quarter-hour effect 2026 | P10 (taker-flow, 1h) | D26 |
| liquidity shocks | Deng & Zhou 2023/2025 (Amihud-type); "Realized Illiquidity" not verifiable | P11 | D19 |
| realized vs implied vol | Almeida et al. 2024/25 (BTC VRP); Alexander & Imeraj (not verifiable) | P14 | D32 |
| term structure | BIS carry paper; Deribit reports not verifiable | — | D16, D17 |
| cross-asset lead/lag | Kurihara–Matsumoto 2026 (PARTIAL), Pascual et al. 2025 (price discovery) | P12 | D31 |
| cross-sectional relative strength | Fieberg et al., Liu–Tsyvinski–Wu (PARTIAL) | P02 | — |
| intraday seasonality | Padyšák–Vojtko 2022 vs Baur et al. 2017 (contradictory); Hansen–Kim–Kimbrough 2021; Krohn–Mueller–Whelan (FX fixings) | P13 | D29 |
| breakout persistence | no verified academic source (gap) | P05 (baseline), P04 | — |
| regime-conditioned | HMM (Koki et al.), Daniel–Moskowitz momentum crashes; smoothed-state lookahead risk | regime analysis layer (07) + P04 gate | D22, D23 |
| event-driven macro | NY Fed / Croushore–Stark vintages (lookahead), no verified 2023–26 CPI/FOMC crypto/gold effect | — | D18 |

Honest gaps: no verified academic source for OI/price predictive power, breakout persistence in crypto, or intraday reversal on majors post-2023; FX-carry sources are pre-2016; several 2026 arXiv items are unreviewed and one PDF was unreadable. Where evidence was thin, the primitive was still executed as a *falsifiable mechanism*, not as an evidence-backed claim.

## Appendix A — sub-agent notes: crypto derivatives / microstructure families
{A}

## Appendix B — sub-agent notes: classic factors, seasonality, regimes, macro
{B}
""")
# ---------------- 03
rows = "\n".join(f"| {n} | `{v[7]}` | {LA.get(n, {}).get('verdict','')} | {v[6]} |" for n, v in C.X.items())
drows = "\n".join(f"| {d[0]} | {d[1]} | `{d[3]}` | not executed: {d[4]} |" for d in C.D)
w("03_FORWARD_SAFETY.md", f"""# 03 — Forward safety

Classes: `FORWARD_SAFE` (only immutable closed-bar public prints ≤ decision time), `FORWARD_SAFE_WITH_RECEIPT_STAMP` (exchange-derived fields — funding, OI snapshots, premium index, DVOL, HL funding — whose real-time availability delay is *not* in the archive; a live version must store its own receipt timestamp), `OFFLINE_ONLY`, `LOOKAHEAD_RISK`.

## Rules enforced
1. Hourly rows are labelled by bar open; row t is treated as known at t+1h. Fills at next open (delay 0); +1/+2 bars tested.
2. Trailing windows only: every rolling statistic ends at t; normalisation by trailing (720h) std — never full-sample. No centered/smoothed filter, no HMM smoothing, no change-point segmentation.
3. Funding uses **settled** values only, stamped at settlement floored to the hour (available at the following decision); predicted funding is excluded. Funding *charged* in P&L is the value settled at the end of the holding bar (accounting only, never a feature).
4. Bulk 5-min OI snapshots get an extra 1-bar receipt lag; DVOL is lagged 1 bar (candle-stamping convention unverified).
5. Macro: no macro primitive executed; if executed later, first-release stamps and ex-ante consensus only (no revised series).
6. Regime labels (BTC 168h RV percentile vs trailing 365d; 30d trend sign) are past-only and applied to the *next* bar's P&L.

## Empirical test (bench/…/py/lookahead_test.py)
For 6 random cut points T, each signal is recomputed on data truncated at T and compared with the full-data value on rows T-300…T (P13 at both horizons). Any difference ⇒ LOOKAHEAD_RISK.
Result: **15/15 PASS (max abs diff 0.0)**. Negative control (signal = next-bar return): FAIL, as required, so the test is not blind. Additionally, a planted-future signal is detected by the simulator with gross Sharpe {F['_controls']['planted_future_H4_delay0']['gross_sharpe']:.1f} (H=4) while the same signal shifted by 3H gives {F['_controls']['misaligned_3H_H4_delay0']['gross_sharpe']:+.2f}, validating return/decision alignment.

## Classification of the executed primitives
| primitive | class | truncation test | specific controls |
|---|---|---|---|
{rows}

## Discovered but not executed
| id | primitive | class | note |
|---|---|---|---|
{drows}

Counts over all {cnt['discovered']}: FORWARD_SAFE {cnt['fs']}, FORWARD_SAFE_WITH_RECEIPT_STAMP {cnt['fsr']}, OFFLINE_ONLY {cnt['off']}, LOOKAHEAD_RISK {cnt['la']}.

Residual (non-testable) risks: archive timestamps vs real-time publication; survivorship of the 10-asset universe (see 11); exchange-side retroactive corrections to bulk files (UNKNOWN).
""")
# ---------------- 04
pa = aud["per_asset"]; xs = aud["cross_venue_bn_perp_vs_cb_spot"]
arows = "\n".join(f"| {a} | {v['kl_first'][:10]} | {v['kl_missing_bars']} | {v['metrics_first'][:10]} | {v['metrics_rows']} | {v.get('hl_first','—')[:10]} | {v.get('cb_first','—')[:10]} | {v.get('cb_missing_hours_2025_01_to_2026_08','—')} |" for a, v in pa.items())
xrows = "\n".join(f"| {a} | {v['ret_corr']:.4f} | {v['median_abs_close_diff_bps']:.1f} |" for a, v in xs.items())
w("04_PUBLIC_DATA.md", f"""# 04 — Public data

Scripts: `bench/alpha_primitives_v1/py/fetch_binance_vision.py`, `fetch_other.py`, `fetch_hl.py`, `data_audit.py`. Raw parquet (≈400 MB) is **not committed** (`.gitignore`); re-fetch with the scripts (public, no keys). Derived results are committed in `results/`.

## Sources used
| Source | Endpoint family | Used for | Notes |
|---|---|---|---|
| Binance Vision (bulk) | `data/futures/um/monthly/{{klines,premiumIndexKlines,fundingRate}}`, `daily/metrics` | 1h perp OHLCV + taker-buy volume, premium index, funding history, 5-min OI / long-short / taker ratios (→ hourly last) | Main `fapi` REST is geo-blocked from this egress (HTTP 451, also in report 005); bulk archive works. Period 2022-10 → 2026-08 (2022-Q4 warm-up only). |
| Deribit | `public/get_volatility_index_data` (DVOL, hourly) | P14 (BTC, ETH) | Full range 2022-10 → 2026-09. |
| Hyperliquid | `POST /info {{type: fundingHistory}}` | P15 (hourly funding, 10 core assets) | Starts 2023-06 (XRP 2023-06-18, ADA 2023-10-22). Timestamps carry ms jitter → floored to hour. |
| Coinbase Exchange | `products/{{X}}-USD/candles` (1h) | wrong-venue signal test (9 assets, no BNB), 2024-12 → 2026-08 | ≈10 missing hours per asset in the test window. |
| OKX, Kraken, Gate | REST | **reachability probed on 2026-09-29 only** (OKX candles/funding OK; Gate funding OK; Kraken OHLC OK); **not used in any result** | Left out to keep 10–15 serious primitives; history depth of these venues was not evaluated in this pass. |

No private AurumShift data. No API keys.

## Coverage (core + holdout)
| asset | perp klines from | missing hourly bars | OI/metrics from | 5-min metric rows | HL funding from | CB candles from | CB missing h (test window) |
|---|---|---|---|---|---|---|---|
{arows}

Funding interval reported by Binance Vision for all 16 assets: 8h. Zero-OI rows exist (e.g. BTC {pa['BTC']['oi_zero_rows']}, ADA {pa['ADA']['oi_zero_rows']} of ≈420k 5-min rows; treated as missing). 5-min metric gaps: {100*pa['BTC']['metrics_5min_gap_share']:.4f}% of rows.

## Cross-venue sanity (Binance perp vs Coinbase spot, hourly, 2025-01 →)
| asset | 1h log-return corr | median |close diff| (bps) |
|---|---|---|
{xrows}

Median close gap ≈5–6 bps (perp/spot basis + timestamp alignment); ADA and LTC have the lowest return correlation (0.97–0.98), i.e. price-only signals are not identical across venues, which is the point of the wrong-venue test (09).

## Quirks that matter
- Binance Vision `metrics` `create_time` semantics (start vs end of the 5-min window) are not documented → conservative 1-bar lag.
- Premium-index klines have no volume field (zeros).
- The Hyperliquid funding interval is 1h vs Binance's 8h settlement; P15 compares 24h averages of per-hour rates.
- Assets in the universe were chosen as liquid *in 2026* (survivorship; see 11).
""")
# ---------------- 05
w("05_RESULTS.md", f"""# 05 — Results

Definitions: **gross** = price P&L of the portfolio (before any cost or funding). **net** = gross − trading cost (generic per-side bps, see 08) − funding paid/received (real settled funding). Sharpe annualised on hourly P&L; t = Newey–West (lags = max(2H,24)). FULL = 2023-01→2026-08 (3.66y), DEV = 2023–24, TEST = 2025-01→2026-08. Only **primary specs** (pre-declared sign, mode, H) enter adjudication. BH_q = Benjamini–Hochberg q over the 15 primary one-sided net tests.

## Primary specs — Sharpe gross vs net
{t('05_primary')}
## Primary specs — economics (annualised %, gross exposure ≤ 1)
`turn_day` = gross notional traded per day / gross exposure. `cs_ic` = mean cross-sectional Spearman IC of the signal vs forward H-return (sampled every H rows) and its t-stat.
{t('05_econ')}
## Reading the table
- **Nothing net-significant**: best net Sharpe +0.24 (P06, t 0.44) and +0.09 (P14). Net t-stats between −4.4 and −31 for P03, P07, P10, P11, P12, P13 (and −2.1 for P15) mean these are cost-dominated with confidence, not just unproven.
- **Gross edge is weak and unstable across halves**: primary gross Sharpe is positive in DEV for 9/15 and in TEST for 7/15, positive in both for only P02 and P04 (≈0.3–0.8, not significant). Trend/breakout/OI-confirmation (P01, P05, P06, P08, P13) fall from +0.7…+1.8 (DEV) to −0.03…−0.8 (TEST). Several primitives (P07, P10, P12, P14, P15) show the *opposite* of their pre-declared sign in DEV and positive gross in TEST — consistent with noise.
- **Statistical IC ≠ tradable edge**: rank ICs are highly significant for P03 (+0.032, t 8.0), P12 (+0.027, t 6.6), P13 (+0.020, t 5.0), P06 (+0.037, t 4.0), P07 (t 3.0), yet their magnitude-weighted gross P&L is ≈0 or negative. Rank IC weights all 10 assets equally, while P&L is dominated by large moves that do not follow the small-move pattern. The effects are 1–4h in size and are consumed by 6–10 bps per side at 4–8 turns/day.
- **Carry (P06)**: only primitive whose net stays ≥0 (funding received +5.6%/yr offsets part of the cost) but the gross edge is not significant (t 0.83) and TEST net Sharpe is −0.76.
- Full-sample pipeline calibration: placebo signals (150 random, EWMA-24h-smoothed, same pipeline, H=24 TS): gross-t sd {F['_placebo']['gross_t_sd']:.2f}, p95 {F['_placebo']['gross_t_p95']:.2f}, p99 {F['_placebo']['gross_t_p99']:.2f}; net-t p95 {F['_placebo']['net_t_p95']:.2f} (random signals lose money net, as expected). No primary gross t (max 1.60, P08) exceeds the placebo p95 by a meaningful margin.

## Non-primary specs (exploratory only, 45 extra tests, uncorrected)
The other mode/horizon of every primitive was also run. Top gross t-stats (breakeven_x = cost multiple at which net = 0, funding netted):
{t('05_allspecs_top')}
These are the only places with strong gross statistics, all cross-sectional or 4h; all have break-even multiples ≤0.65× the assumed costs and most decay in TEST (P05|CS|H4 3.85→−0.05, P01|CS|H4 2.94→−0.28). Follow-up in 09.

## Secondary horizon/mode for every primitive
{t('05_alt')}
""")
# ---------------- 06
w("06_ORTHOGONALITY.md", f"""# 06 — Orthogonality, redundancy, persistence, turnover

Signals: per-asset z-scores sampled daily, pooled Spearman. P&L: gross daily P&L of each primitive's primary spec (2023-01→2026-08). Incremental information: regress each primitive's gross daily P&L on all 14 others; report the intercept t-stat and R². (Gross is used so that cost drag does not masquerade as "negative alpha".)

## Clusters (average-linkage on 1−|ρ_signal|, cut at |ρ|≈0.3) and effective breadth
{t('06_clusters')}
Effective number of independent bets ≈10 (signals) / ≈10 (gross P&L) out of 15 — the set is fairly diverse, with two redundant groups: **{{P01 TSMOM, P05 breakout-persistence, P02 relative strength}}** (P01–P05 signal ρ +0.77, P&L ρ +0.83: the "breakout persistence" baseline is the same trend information as TSMOM) and **{{P03 reversal, P10 taker imbalance, P12 lead-lag}}** (P03 vs P10 signal ρ −0.56: taker flow over 4h is largely the mirror image of the 4h return, so "flow continuation" and "return reversal" are opposite sides of one variable).

## Signal rank correlation
{t('06_sigcorr')}
## Gross daily P&L correlation
{t('06_pnlcorr')}
## Incremental (conditional) information on gross P&L
{t('06_incremental')}
No primitive has a significant (|t|>2) intercept once the others are controlled, i.e. none contributes significant incremental *gross* P&L. With no supported candidate, "non-redundant candidates" is 0 by the pre-declared rule; the diversity above is a property of the probe set, not evidence of alpha.

## Persistence (signal autocorrelation) and turnover
Persistent signals (P06, P14, P15, P02, P01) support low turnover; fast signals (P03, P10, P12, P11, P09) are dominated by 1–4h decay and their cost drag is structural.
{t('06_persistence')}
P13's lag-24/72h autocorrelation ≈0.95 is mechanical (same-hour averages repeat daily) while its lag-4h is ≈0: its position rotates every few hours → 5 turns/day at H=4.

Turnover implication: at 6–10 bps per side, a primitive needs gross edge ≳ (turn_day × 365 × ~8 bps) per year of exposure; slow primitives (turn_day ≤ 0.35: P04, P06, P09, P14) are the only ones for which this hurdle is below ~10%/yr, but none of them has gross edge distinguishable from zero.
""")
# ---------------- 07
w("07_REGIME_CONDITIONAL.md", f"""# 07 — Regime-conditional behaviour

Regimes are past-only (03): volatility = BTC 168h realised-vol percentile vs trailing 365d (LOW <⅓, HIGH >⅔); trend = sign of BTC 30d return. Labels at row t are applied to bar t+1's P&L. Primary specs.

## Net t-stats by regime
{t('07_regime_net_t')}
## Net Sharpe by regime
{t('07_regime_net_S')}
## Gross Sharpe by regime
{t('07_regime_gross_S')}
## Low- vs high-vol gross difference (NW-based Welch t on hourly gross P&L)
{t('07_regime_lowhigh')}
## Reading
- **Pre-declared rule (net-based) → 0 regime-dependent candidates.** No primitive has net t ≥ +1.5 in one vol/trend bucket and ≤ −1.5 in the opposite, and none reaches net t ≥ 2.5 in any bucket.
- **Descriptive lean (not counted)**: the trend/breakout cluster and P14 earn positive gross in LOWVOL and negative in HIGHVOL (P01 +1.71/−0.81, P04 +1.46/−0.31, P05 +1.34/−0.64, P14 +1.26/−0.61); P10 similar (+0.45/−1.73). The differences have t ≈ 1.3–2.1 each, i.e. borderline individually and not significant after accounting for the 15 comparisons; they are also collinear (P01/P05/P04 are one bet). The opposite lean (better in HIGHVOL) appears for P03 reversal, P09 OI-flush and P08 (HIGHVOL gross +1.04/+1.06/+1.06), consistent with the stated mechanisms (forced-flow fades and OI confirmation need volatility) but equally weak.
- Costs remain decisive: in every regime the high-turnover primitives stay deeply net negative, so no regime *gate* rescues them.
- This is the only place the design allowed conditional information to matter; the conclusion is "plausible regime lean in the trend cluster, unproven and cost-dominated". A vol-gated trend overlay is a candidate for a future, better-powered study, not a finding here.
""")
# ---------------- 08
w("08_COST_SENSITIVITY.md", f"""# 08 — Cost sensitivity

## Cost model (generic, deliberately not venue-specific)
Per side, in bps of traded notional: BTC/ETH **6**, other core assets **8**, holdout assets **10** — ≈5 bps taker fee plus 1/3/5 bps half-spread/slippage. Applied to |Δw| of the overlapping-tranche book (so turnover and cost are exact for the simulated policy). Funding is charged from actual settled Binance funding, per position sign. **Not modelled** (UNKNOWN, treated as *not zero*, hence the multipliers): market impact, VIP/maker fee tiers or rebates, queue/latency slippage, borrow, margin financing, exchange outages, tax. UNKNOWN_COST ≠ ZERO_COST: ×0.5 is shown only as an optimistic bound, never used for adjudication.

## Net Sharpe vs cost multiplier (primary specs) and break-even
`breakeven_x` = multiple of the assumed cost at which (gross − funding) = cost. Values <1 mean the primitive loses money at the assumed cost; values >1 leave a margin.
{t('08_cost')}
## Reading
- Break-even multiples: only P14 (1.78), P06 (1.45), P04 (1.00) and P02 (0.84)/P05 (0.79) are near or above 1; the rest are ≤0.64. Those near 1 have insignificant gross edge, so a break-even near 1 is *zero edge with zero cost*, not margin of safety.
- At ×2 costs every primary spec is net-negative (best: P14 −0.02, P06 −0.29); at ×3 all remain negative. Costs, not signal decay, are the binding constraint for hourly-horizon primitives.
- Gross and net are reported separately everywhere; **no primitive is claimed profitable** and nothing here is a production-profitability statement.
- Cost/turnover of overlapping tranches at H=4 vs H=24: raising H reduces turnover ≈ proportionally but also weakens the (already tiny) 4h effects — see the secondary-horizon table in 05.
""")
# ---------------- 09
fal = t('09_falsification')
fx = json.dumps({k: {a: (round(b.get('gross_S', b.get('net_S', 0)), 2)) for a, b in v.items()} for k, v in ex.items()}, indent=1)
w("09_FALSIFICATION.md", f"""# 09 — Falsification

Every stress is applied to the pre-declared primary spec of each primitive, FULL sample unless noted (script `py/falsify.py`; table `results/falsification_table.json`). Values are **net Sharpe** unless the column says gross.

| test | how |
|---|---|
| higher costs | ×2, ×3, ×5 (and ×0.5 optimistic) |
| wrong venue | signal computed from **Coinbase spot** bars, P&L on Binance perps, TEST window, 9 assets (price-only primitives only; `venue_base_gross` = same assets/window with Binance-derived signal) |
| different asset | holdout universe DOT ATOM NEAR TRX BCH ETC (BTC used only as leader for P12); N/A for P14, P15 |
| regime reversal / high vol / low vol | see 07 (bucketed net/gross Sharpe; no primitive flips significantly) |
| missing data | 10% / 25% of bars per asset randomly missing (3 seeds); features from last-observation-carried-forward feed, no position on missing rows (extra turnover) |
| stale data | random 3-bar frozen runs, 10% / 25% coverage; engine trades on stale features unaware |
| parameter perturbation | all look-backs ×0.5, 0.75, 1.5, 2 (min/max reported) |
| latency | +1 and +2 bar execution delay |
| null / control | 150 placebo signals; planted-future signal (must be detected); 3H-misaligned control (must be ≈0) |

## Battery table (net Sharpe; hold_* and venue_* columns are gross where labelled)
{fal}
## Controls
- Placebo (150 random EWMA-24h signals, TS, H=24, same costs): gross t sd {F['_placebo']['gross_t_sd']:.2f} (≈1 ⇒ t-stats are well calibrated), p95 {F['_placebo']['gross_t_p95']:.2f}, p99 {F['_placebo']['gross_t_p99']:.2f}; net-t p95 {F['_placebo']['net_t_p95']:.2f}.
- Planted future signal: gross Sharpe {F['_controls']['planted_future_H4_delay0']['gross_sharpe']:.1f} (H=4), {F['_controls']['planted_future_H24_delay0']['gross_sharpe']:.1f} (H=24); with one extra bar of delay {F['_controls']['planted_future_H4_delay1']['gross_sharpe']:.1f}/{F['_controls']['planted_future_H24_delay1']['gross_sharpe']:.1f}; 3H-misaligned ≈ {F['_controls']['misaligned_3H_H4_delay0']['gross_sharpe']:+.2f}/{F['_controls']['misaligned_3H_H24_delay0']['gross_sharpe']:+.2f}. The simulator is neither blind nor leaky.

## What broke
- **Costs**: every primary spec is net-negative at ×3; only P06 (+0.24) and P14 (+0.09) are positive at ×1 and both are negative or ≈0 at ×2.
- **Split stability**: P06 flips (DEV +0.87 → TEST −0.76 net); P01/P05/P08/P13 lose their DEV gross Sharpe in TEST.
- **Missing data**: P06 carry drops from +0.24 to −0.87 (25% missing) — missing rows cut positions and add turnover to a low-turnover carry book; P02 −0.13→−0.81. Stale data barely moves any primitive (frozen 3-bar runs shift signals by tiny amounts relative to their slow decay) — a warning that the slow primitives are also *insensitive* rather than robust.
- **Parameters** (all look-backs ×0.5…×2): net Sharpe is negative under every perturbation for 8/15 (P03, P07, P08, P10, P11, P12, P13, P15 — cost-dominated everywhere); for the other 7 (P01, P02, P04, P05, P06, P09, P14) the range straddles zero; none is positive under all perturbations.
- **Different assets**: gross Sharpe on the holdout universe is positive for P02 (+0.48), P04 (+0.30), P05 (+0.42), P08 (+0.32), P10 (+0.36), P13 (+0.39), P07 (+0.19), P06 (+0.16), P09 (+0.01) but net is negative everywhere; none of these gross values is significant.
- **Wrong venue**: signals from Coinbase spot give gross Sharpe similar to Binance-derived on the same window for P02 (+0.27 vs +0.35), P04 (+0.94 vs +0.77), P12 (+0.41 vs +0.47) — the price-only signals themselves transfer across venue; P01/P05/P13 are ≈0 or negative in both.

## Exploratory follow-up of the six strongest non-primary specs (not adjudicated)
Gross Sharpe under stress (net Sharpe for the cost keys):
```
{fx}
```
- P13|CS|H4 (cross-sectional hour-of-day seasonality): gross 2.8 (DEV 3.9, TEST 1.2), survives one delay bar (1.3) but not two (≈0), transfers to Coinbase-derived signal (TEST 1.9 vs 1.7 Binance), but only +0.6 on the holdout universe and turns net-positive only below ≈0.18× the assumed cost with 8.4 turns/day. A real but tiny, latency-sensitive statistical regularity that is not monetisable at these costs.
- P05|CS|H4, P01|CS|H4, P05|CS|H24 (cross-sectional trend/breakout): DEV 2.4–3.9 → TEST −0.4…0.0. Period-specific.
- P08|TS|H4 (OI confirmation): stable across halves (1.66/1.02), across delay, positive in holdout (0.53) — the most consistent gross lead — but break-even 0.48× (turnover 2.4/day).
""")
# ---------------- 10
adjt = t('10_adjudication')
w("10_ADJUDICATION.md", f"""# 10 — Adjudication

Rules were fixed in `02_PRIMITIVE_CONTRACTS.md` before the run: C1 forward-safe; C2 net Sharpe >0 in DEV and TEST; C3 FULL net NW t ≥ 2 and BH-q < 0.10 over 15; C5 net >0 at ×2 cost; C6 ≥70% of falsification checks passed. `SUPPORTED_ROBUST` = C1∧C2∧C3∧C5∧C6, `SUPPORTED_FRAGILE` = C1∧C2∧C3.

## Criteria table (C6 = falsification pass rate; boolean columns 1.00=true)
{adjt}
Outcome: **0 SUPPORTED_ROBUST, 0 SUPPORTED_FRAGILE, 0 GROSS_ONLY (primary gross t ≥ 2: none)**. C1 holds for all 15; C2 fails everywhere (no primitive is net-positive in both halves); C3 fails everywhere.

## Disposition per the lab doctrine (ADOPT / ADAPT / PARK / REJECT — external research only, no local-compatibility claim)
| primitive | disposition | reason |
|---|---|---|
| P03 REV4H | REJECT (as a 1h standalone) | significant rank IC but ≈0 gross P&L; 4.3 turns/day ⇒ −116%/yr net |
| P10 TAKER_IMB | REJECT | mirror of P03; gross ≈0/negative; 4.5 turns/day |
| P12 LEADLAG_BTC | REJECT at 1h | effect exists in rank terms (IC t 6.6) but 8.4 turns/day and ≈−15% gross; would need sub-minute execution (not testable with public 1h data) |
| P07 PREMIUM | REJECT | wrong-signed/zero gross, high turnover |
| P11 LIQ_SHOCK | REJECT | negative gross; volume shocks are informed, not liquidity-driven, on these assets |
| P13 SEASON_HOD | PARK | strongest gross statistics of all (CS H4) but cost-dominated and latency-fragile; only interesting as a normaliser/gate (Hansen–Kim–Kimbrough) rather than a directional signal |
| P15 FUND_DIV | PARK | positive gross but not significant, net −1.1 |
| P09 OI_FLUSH | PARK | mechanism-plausible, low turnover, 0.28 gross Sharpe, insignificant; needs real liquidation tape (not public in history) |
| P01/P02/P05 (trend cluster) | PARK as baseline | largely redundant with each other; P01/P05 positive gross in 2023–24, ≤0 in 2025–26; P02 stays weakly positive (+0.84/+0.33, insignificant); useful only as a benchmark/regime gate |
| P08 OI_PRICE | PARK | most consistent gross lead (both halves, holdout, delay-robust at H=4), but break-even 0.48–0.64× costs |
| P04 VOLCOMP_BRK | PARK | net ≈0 (turnover 0.05/day), gross 0.55, insignificant; sparse |
| P06 FUND_CARRY | PARK | only primitive with net ≥0 at ×1 but flips sign across halves and fails missing-data test; its economic content is carry, which needs a hedged (spot/dated) implementation not tested here |
| P14 VRP_DVOL | PARK | +0.09 net, only 2 assets, no power |
**ADOPT: none. ADAPT: none.**

## Non-redundant / regime-dependent counts
With no supported primitive: NONREDUNDANT_CANDIDATES = 0, REGIME_DEPENDENT_CANDIDATES = 0, NET_POSITIVE_EXTERNAL_CANDIDATES = 0 (rule-based). Descriptive-only structure: two redundancy groups (trend cluster; reversal/flow/lead-lag cluster), effective breadth ≈10/15 (06); a borderline low-vol lean in the trend cluster (07).

## Final verdict
`FINAL_VERDICT = NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED`

Why not INCONCLUSIVE: the pipeline was validated (15/15 truncation tests; leaky control fails; planted signal detected at Sharpe 17–27; placebo t calibrated ≈N(0,1)); the cost-dominance findings are high-confidence (|net t| up to 31); the pre-declared rule was applied mechanically. The verdict is bounded by power (11): it excludes net Sharpe ≳1 at these costs and this cadence, not smaller edges.

What would change it (for a *future external* study, not this one): (i) maker/queue-aware execution model and real fee tiers; (ii) minute-level or order-book/OFI data for P03/P10/P12; (iii) hedged carry (spot/dated futures) for P06/P15; (iv) point-in-time liquidation and term-structure archives; (v) a longer sample or wider universe for the OI-confirmation (P08) and vol-gated trend leads; (vi) macro event primitives with first-release stamps.

## Final block
{FINAL}
""")
# ---------------- 11
w("11_LIMITATIONS.md", f"""# 11 — Limitations

1. **Power.** 3.66 years of hourly data; Sharpe s.e. ≈ 0.5 (placebo sd 0.48). A true net Sharpe below ≈1 is not detectable. Overlapping-tranche portfolios and 10 assets add serial/cross-sectional dependence; NW lags are max(2H,24). t-stats are approximately calibrated (placebo gross-t sd 0.94) but tails were only sampled 150 times.
2. **Not fully blind.** A 3-asset (BTC/ETH/SOL) smoke run was executed and read *before* the full run, to debug the pipeline (it showed e.g. P02 TS, P08 TS H4 gross t>2). No signal definition, sign, horizon, mode, threshold or cost was changed afterwards; only data-handling fixes (`min_periods`, OI zeros → missing, reindexing of columns) and added controls/analysis. The literature-informed *design* of 15 primitives is itself a researcher degree of freedom. Contracts were committed first (git history) — the commit contains those smoke outputs, which the full run overwrote.
3. **Survivorship.** The 10 core assets are majors alive and liquid on Binance USD-M throughout 2023–2026 (chosen with 2026 hindsight), which favours momentum-type primitives and flatters small-cap dynamics; the holdout assets are also survivors. No delisted assets.
4. **Costs are generic.** 6–10 bps per side is an assumption, not a venue quote; no impact model; fees tiers/rebates unknown. Multipliers stand in for that unknown. A maker-only strategy could have very different economics — untested.
5. **Funding accounting.** Uses settled funding at each settlement, position-sign-aware, for a *directional perp book* — no spot leg. Binance Vision reported an 8h interval for all assets in the period; if some assets ran 4h, per-hour normalisation of features (P06/P15) is off for them (UNKNOWN).
6. **Timestamps.** Archive stamps are exchange-side; receipt delays are unknown. OI/metrics/DVOL get a conservative 1-bar lag; funding/premium/HL do not beyond flooring. Live use requires recorded receipt stamps (class FORWARD_SAFE_WITH_RECEIPT_STAMP).
7. **Proxies.** P09 is an OI-flush *proxy*, not real liquidations; P07 uses the exchange premium index; P14 has only two assets (BTC/ETH) and a 30d-forward implied vol vs a 24h holding period.
8. **Not executed**: term structure, macro events, real liquidation tape, order-book/OFI, tick flow, FX/gold, equity linkage, ML factors (see 02 tail). "Multi-asset" here means crypto perps only.
9. **Multiple testing.** Adjudication uses 15 primary tests (BH). The 45 non-primary specs and regime tables are exploratory and uncorrected; nothing in them is claimed.
10. **Literature status.** Source verification was done by sub-agents via page fetches; some pages were unreadable (403/PDF) and are marked. Several 2026 arXiv items are unreviewed. Claims are DOCUMENTED_CLAIM, not reproduced.
11. **Data provenance.** OKX/Kraken/Gate were only reachability-probed; Binance main API is geo-blocked from this egress. Cross-venue price checks use Coinbase only (corr 0.97–0.9997).
12. **Reproducibility.** Raw data not committed (400 MB); scripts fetch public endpoints, but Deribit/Hyperliquid/Coinbase histories can be revised or truncated by providers. Results depend on the wall-clock snapshot (2026-09-29). Hourly P&L (`pnl_primary.parquet`) is not committed; a daily version is.
13. **No integration claim.** Nothing here asserts compatibility with, or benefit to, the private AurumShift system; local integration is not authorised (`LOCAL_INTEGRATION_AUTHORIZED=FALSE`).
""")
print("reports written")
