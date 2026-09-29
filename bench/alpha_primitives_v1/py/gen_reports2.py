"""Narrative report sections (00,01,02,03,04,10,11) assembled from catalog + results JSON."""
import json, os
import catalog as CT
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); RES = os.path.join(ROOT, "results")
OUT = os.path.join(os.path.dirname(os.path.dirname(ROOT)), "reports", "011_alpha_primitives")
J = lambda f: json.load(open(os.path.join(RES, f)))
s1, s2, s3, s4, s5, s6 = J("s1_main.json"), J("s2_ortho.json"), J("s3_regime.json"), J("s4_cost.json"), J("s5_falsify.json"), J("s6_adjudication.json")
PR = s1["primitives"]; NAMES = list(PR); s5p = s5["prims"]
def f(x, d=2, pct=False):
    if x is None or x != x: return "flat/NA"
    return f"{x*100:.{d}f}%" if pct else f"{x:.{d}f}"
def tab(head, rows): return "| " + " | ".join(head) + " |\n|" + "---|" * len(head) + "\n" + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in rows) + "\n"
def w(fn, s): open(os.path.join(OUT, fn), "w").write(s)
from collections import Counter
EX = [c for c in CT.C if c[11]]; DI = [c for c in CT.C if not c[11]]
cnt_all = Counter(c[10] for c in CT.C); cnt_ex = Counter(c[10] for c in EX)
tiers = {k: s6[k]["tier"].split(" ")[0] for k in NAMES}
netpos = [k for k in NAMES if tiers[k] == "NET_POSITIVE_EXTERNAL_CANDIDATE"]
ginfo = [k for k in NAMES if tiers[k] == "GROSS_INFORMATION_ONLY"]
nonred = [k for k in ginfo if s6[k]["nonredundant"]]
regdep = [k for k in NAMES if s6[k]["regime_dependent"]]
fams = sorted(set(c[2] for c in CT.C))
VERDICT = "NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED"
final = f"""PRIMITIVES_DISCOVERED={len(CT.C)}
PRIMITIVES_EXECUTED={len(EX)}

FORWARD_SAFE_COUNT={cnt_ex['FORWARD_SAFE']}   # executed primitives classed strictly FORWARD_SAFE (a further {cnt_ex['FORWARD_SAFE_WITH_RECEIPT_STAMP']} executed are FORWARD_SAFE_WITH_RECEIPT_STAMP; catalogue-wide: {cnt_all['FORWARD_SAFE']} + {cnt_all['FORWARD_SAFE_WITH_RECEIPT_STAMP']})
LOOKAHEAD_RISK_COUNT={cnt_all['LOOKAHEAD_RISK']}   # discovered candidates classed LOOKAHEAD_RISK (0 among executed; OFFLINE_ONLY discovered: {cnt_all['OFFLINE_ONLY']})

NONREDUNDANT_CANDIDATES={len(nonred)}   # gross-information-only tier AND max|rho|<0.5 AND R2<0.35: {', '.join(nonred)}. NOT net-positive.
REGIME_DEPENDENT_CANDIDATES={len(regdep)}   # statistical flags only (45 tests, ~2 expected by chance): {', '.join(regdep)}

NET_POSITIVE_EXTERNAL_CANDIDATES={len(netpos)}

ANY_DROP_IN_STRATEGY=FALSE
LOCAL_INTEGRATION_AUTHORIZED=FALSE

FINAL_VERDICT={VERDICT}"""
open(os.path.join(RES, "final_block.txt"), "w").write(final + "\n")

# ---------------------------- 00
t = tab(["primitive", "family", "gross Sharpe", "net Sharpe", "DEV net", "HOLDOUT net", "turnover/yr", "tier"],
        [[k, PR[k]["family"], f(PR[k]["full"]["gross_sharpe"]), f(PR[k]["full"]["net_sharpe"]), f(PR[k]["dev"]["net_sharpe"]), f(PR[k]["holdout"]["net_sharpe"]), f"{PR[k]['full']['turn_ann']:.0f}", s6[k]["tier"]] for k in NAMES])
w("00_EXECUTIVE_SUMMARY.md", f"""# 00 — Executive summary — AURUMSHIFT_EXTERNAL_ALPHA_PRIMITIVE_DISCOVERY_V1

**Mode: EXTERNAL_RESEARCH_ONLY · NO_PRIVATE_AURUMSHIFT_CODE · NO_INTEGRATION.** Nothing here is a production-profitability claim, and nothing here says anything about compatibility with the private AurumShift repository.

## Verdict: `{VERDICT}`

We catalogued **{len(CT.C)}** candidate primitives across all {len(fams)} requested family labels ({len(DI)} not executed: mostly missing point-in-time public data, tick/L2 volume, lookahead-tainted, or event counts too small), and executed **{len(EX)}** on 10 Binance USD-M perpetuals at 1h resolution over 2024-03 → 2026-08 (914 days), with DEV/HOLDOUT split, stationary-bootstrap uncertainty, a mechanical causality audit, cross-venue checks (OKX, Coinbase, Gate, Kraken, Hyperliquid, Deribit) and a falsification battery.

**Result: none of the 15 primitives is net-positive after generic taker costs in both DEV and HOLDOUT, none survives 1.5× costs, and no HOLDOUT net-Sharpe test survives multiplicity correction (Holm-15 p = {min(s6[k]['holdout_boot_p_holm15'] for k in NAMES):.2f}).**

{t}
Gross = price PnL + funding, before trading costs; net = after costs (5 bp taker + 1–3 bp slippage per side; UNKNOWN cost = 15 bp). Sharpe on daily PnL, √365.

## What was learned (in order of importance)

1. **Costs, not signals, are the binding constraint.** Break-even cost per side (gross return ÷ turnover) is {f(PR['P14_HOUR_SEASON']['breakeven_bps_per_side'],1)} bp for hourly seasonality, {f(PR['P03_REV_4H']['breakeven_bps_per_side'],1)} bp for 4h reversal, {f(PR['P11_TAKER_FLOW']['breakeven_bps_per_side'],1)} bp for taker-flow, versus 6–8 bp paid. Only P05 (9.0 bp) and P07 (26 bp, but on ~0.3%/yr) clear the bar at 1×, and P05 fails at 1.5×.
2. **Weak positive *gross* information exists in four places, none net-monetisable here:** P07 funding carry (gross Sharpe {f(PR['P07_BASIS_CARRY']['full']['gross_sharpe'])}, delta-neutral, ≈1.4%/yr of capital; the trigger never fired in the HOLDOUT because mean 8h funding fell from 7.6e-5 to 2.4e-5 — the carry compression that arXiv 2510.14435 also reports), P05 vol-squeeze breakout (gross {f(PR['P05_VOL_SQUEEZE_BREAK']['full']['gross_sharpe'])}, replicates on OKX/Coinbase prices but negative in the short Gate window, net ≈ 0, and its IC changes sign between DEV and HOLDOUT), P06 funding-crowding fade (gross {f(PR['P06_FUND_XS']['full']['gross_sharpe'])}, but ≈0 on majors and negative on minors, and the Hyperliquid-funding version has gross Sharpe {f(s5p['P06_FUND_XS']['venues']['hyperliquid_funding_signal']['hl_signal_okx_prices']['gross_sharpe'])}), and P14 hour-of-day seasonality (gross {f(PR['P14_HOUR_SEASON']['full']['gross_sharpe'])}, 4400 turns/yr). With 15 primitives, ≈1.5 raw p ≤ 0.10 gross hits are expected by chance; we have four.
3. **Baselines are hard to beat and the classic families do not survive.** TSMOM and Donchian gross Sharpe ≈0 (TSMOM +1.19 DEV → −1.36 HOLDOUT), XS relative strength ≈0, BTC→alt lead-lag ≈0 at hourly resolution, OI-flush proxy and spot-perp basis negative. The equal-weight long baseline earned {f(s1['baseline_ew_long']['full']['price_ann'],1,True)}/yr price minus {f(-s1['baseline_ew_long']['full']['funding_ann'],1,True)}/yr funding (Sharpe {f(s1['baseline_ew_long']['full']['gross_sharpe'])}) — most directional primitives are correlated to nothing and earn nothing.
4. **Orthogonality is not the problem:** effective independent bets ≈ {s2['effective_independent_bets_pr']:.1f} of {s2['n_primitives_in_pca']}; the only redundant pairs are P01↔P04 (ρ=0.79) and P03↔P11 (ρ=−0.55, opposite signs of one flow-reversal effect). But orthogonal noise is still noise.
5. **Universe sensitivity is large.** On the 5-asset subset used for venue tests the same code gives gross Sharpe 0.91 for P02 (vs 0.16 on 10 assets), 0.57 for P04 (vs 0.17) and 1.30 for P14 (vs 0.85): outcomes move by ±0.7 Sharpe with the asset set, which is itself a measure of how much of any gross "edge" here is selection noise.
6. **Statistical power is limited.** 914 days give a HOLDOUT net-Sharpe 90% bootstrap band of roughly ±1.5 (see 05): a true net Sharpe below ~1 would not be detected. The verdict means *no primitive is supported by this evidence*, not that none can exist — especially with maker execution, lower-fee tiers, other resolutions or other universes, none of which were tested.
7. **Mechanical forward safety is good:** all 15 signal implementations pass a truncation (future-deletion) audit; 0 executed primitives are LOOKAHEAD_RISK; 6 need receipt-stamped live capture (funding, OI, DVOL, cross-market basis) before they could be forward-safe in practice.

## Deviations and honesty notes
* P07's threshold and P12's trigger were mis-specified in the pre-registered first pass and were re-selected on the DEV window only (05 §5.4). Both remain untradeable, so the deviation does not change the verdict.
* Term-structure (options surface), event-driven macro, order-book/tick microstructure and true liquidation-print primitives were **discovered but not executed** (no public point-in-time history, insufficient event count, or tick-volume scope): the corresponding families are covered by a documented contract only (01–03) and, for liquidation pressure, by an OI-flush *proxy* (P10).
* OSS (Qlib/freqtrade/vectorbt) was assessed from web documentation only; source code was not inspected.

## Final block
```
{final}
```
""")

# ---------------------------- 01 LANDSCAPE
rows = [[c[0], c[1], c[2], "EXECUTED" if c[11] else "discovered", c[10]] for c in CT.C]
srcs = {}
for c in CT.C:
    for sk in c[12]: srcs.setdefault(sk, CT.SRC[sk])
w("01_LANDSCAPE.md", f"""# 01 — Landscape: sources and candidate primitives

## 1.1 Discovery method
Web search (standard mode) over recent papers/working papers (2023–2026 preferred), serious OSS, exchange/vendor research and technical blogs; every candidate was reduced to mechanism, formula, inputs, sampling, horizon, failure modes and lookahead risk (02). Evidence labels follow the repository doctrine: **DOCUMENTED_CLAIM** (from an abstract or search snippet; not re-derived), **OBSERVED** (measured here), **INFERENCE**, **UNKNOWN**. Search coverage was shallow-to-moderate (≈10 queries): this is a landscape, not a systematic review. Exchange research (Binance Research, Deribit Insights) searches returned no citable signal studies; Kaiko/Amberdata results were marketing/paywalled aggregates.

## 1.2 Sources actually used
""" + "\n".join(f"* `{k}`: {v}" for k, v in srcs.items()) + f"""

Additional context from the search results, not used for any number: crypto cascade case studies (Oct-2025 event described as the largest; DOCUMENTED_CLAIM from search summaries), and the observation that many TS-momentum results erode after costs (AUT working paper snippet).

## 1.3 Family coverage
Requested families → executed / discovered-only:
* momentum/trend: P01, P04 (+D01, D16, D18) · mean reversion: P03 (+D03) · vol compression/expansion: P05 (+D14, D15) · carry: P07 (+D09) · basis: P08 (+D09) · funding divergence: P06 (+D10, D11, D13) · OI/price divergence: P09 · liquidation pressure: P10 *proxy* (+D04, D05 not testable) · volume imbalance: P11 (+D02, D24, D28) · liquidity shocks: P12 (+D23) · realized vs implied vol: P15 (+D07) · **term structure: not executed** (D06: no public PIT surface; only single-tenor DVOL) · cross-asset lead/lag: P13 (+D12) · cross-sectional RS: P02 (+D25) · intraday seasonality: P14 (+D22) · breakout persistence: P04, P05 · regime-conditioned signals: evaluated as *conditioning of all 15* in 07, plus D08/D16/D17 discovered · **event-driven macro: not executed** (D20/D21: ≈24 FOMC + ≈32 CPI events cannot pass multiplicity; revised-value risk).

## 1.4 Candidate list ({len(CT.C)}; {len(EX)} executed)
{tab(['id', 'primitive', 'family', 'status', 'forward-safety class'], rows)}
""")

# ---------------------------- 02 CONTRACTS
def contract(c):
    return f"""### {c[0]} — {c[1]}{'  [EXECUTED]' if c[11] else '  [discovered, not executed]'}
* **Family:** {c[2]}
* **Mechanism:** {c[3]}
* **Formula:** {c[4]}
* **Required inputs:** {c[5]}
* **Sampling assumptions:** {c[6]}
* **Expected horizon:** {c[7]}
* **Failure modes:** {c[8]}
* **Lookahead risk:** {c[9]}
* **Class:** `{c[10]}`
* **Sources:** {'; '.join(CT.SRC[s] for s in c[12]) if c[12] else 'INFERENCE (no citable source found)'}
"""
w("02_PRIMITIVE_CONTRACTS.md", f"""# 02 — Primitive contracts

Common conventions (all executed primitives): bar index = bar open time; a decision after bar *i* uses only bars ≤ *i*, earns bar *i+1* close-to-close (0-latency fill at the prior close, cost model charges taker fee + slippage; latency +1..+6 bars is falsified in 09). Weights are equal-notional (1/N per asset, clipped to [−1,1]/N); cross-sectional primitives are dollar-neutral with gross 1. Perp positions pay/receive funding at each settlement. Vol estimate σ = 168h trailing std of log returns. Z-scores use trailing 720h windows (min 240). No parameter is tuned except the two DEV-only reselections (05 §5.4). Code: `bench/alpha_primitives_v1/py/primitives.py`.

## Executed primitives
""" + "\n".join(contract(c) for c in EX) + "\n## Discovered, not executed\n" + "\n".join(contract(c) for c in DI))

# ---------------------------- 03 FORWARD SAFETY
audit = s1["causality_audit"]
rows = [[c[0], c[1], c[10], "PASS (max diff " + f"{audit[c[0]]['max_abs_diff']:.0e}" + ")" if c[0] in audit else "not run", c[9]] for c in CT.C]
w("03_FORWARD_SAFETY.md", f"""# 03 — Forward-safety classification

Classes: `FORWARD_SAFE` (computable from data available at decision time with no source-side stamping subtlety) · `FORWARD_SAFE_WITH_RECEIPT_STAMP` (safe only if the feed is captured live with its own receipt timestamp; archives/reconstructions are not evidence of availability) · `OFFLINE_ONLY` (no point-in-time history exists publicly; usable only for offline study) · `LOOKAHEAD_RISK` (uses centered filters, revised/future values or future-normalised features; banned).

Counts — executed: FORWARD_SAFE {cnt_ex['FORWARD_SAFE']}, FORWARD_SAFE_WITH_RECEIPT_STAMP {cnt_ex['FORWARD_SAFE_WITH_RECEIPT_STAMP']}, OFFLINE_ONLY 0, LOOKAHEAD_RISK 0. Catalogue-wide: FORWARD_SAFE {cnt_all['FORWARD_SAFE']}, WITH_RECEIPT_STAMP {cnt_all['FORWARD_SAFE_WITH_RECEIPT_STAMP']}, OFFLINE_ONLY {cnt_all['OFFLINE_ONLY']}, LOOKAHEAD_RISK {cnt_all['LOOKAHEAD_RISK']}.

## Mechanical evidence (OBSERVED)
Truncation audit (05 §5.5): weights recomputed on data cut at 5 timestamps equal the full-data weights before the cut for **all 15** primitives. This detects centered/future-normalised code paths in the signal logic. It cannot detect (a) vendor-side revision, (b) late arrival of data in production, (c) archive-vs-live timestamp semantics — hence the receipt-stamp class.

## Specific stamping assumptions made
* **Klines/taker volume:** usable when the bar has closed (decision after bar *i*, earns bar *i+1*).
* **Funding (Binance):** settled rate stamped `calc_time`; the feature becomes usable after the bar containing the settlement closes (≤1h late, conservative). Funding cash flows are attributed to the bar containing the settlement, paid on the position held *entering* that bar.
* **Open interest (Binance Vision metrics, 5m):** snapshot stamped `create_time` assumed available 5 minutes later (semantics not documented → conservative). Archive files are published after the day; **live use needs REST/WS capture with receipt stamps** (`FORWARD_SAFE_WITH_RECEIPT_STAMP`).
* **Deribit DVOL:** hourly candle used 1h after its start. The venue could recompute the index; receipt stamps needed.
* **Spot–perp basis (P08):** two markets aligned on the same bar; live version needs both feeds stamped.
* **Regime labels (07):** trailing percentiles, lagged one bar.
* **Not used:** revised macro values, centered filters, smoothed HMM states, full-sample normalisation, vendor-restated on-chain series (all listed as LOOKAHEAD_RISK candidates).
* **Survivorship (not lookahead but a bias):** the 10-asset universe was chosen ex post as liquid, long-lived contracts.

## Table
{tab(['id', 'primitive', 'class', 'truncation audit', 'lookahead note'], rows)}
""")

# ---------------------------- 04 PUBLIC DATA
xm = json.load(open(os.path.join(RES, "vision_manifest.json")))
def cnt(kind):
    d = xm.get(kind, {}); n = sum(len(v) for v in d.values()); ok = sum(1 for v in d.values() for x in v.values() if x["status"] in ("ok", "cached")); return n, ok
rows = [[k, *cnt(k)] for k in ["spot_kl", "um_kl", "um_prem", "um_fund", "um_metrics"]]
xvf = s5["venue_info"]; kc = s5["kraken_check"]
w("04_PUBLIC_DATA.md", f"""# 04 — Public data used

No API keys, no private AurumShift data. Raw archives are **not committed** (size); `bench/alpha_primitives_v1/py/fetch_vision.py` and `fetch_xvenue.py` re-download them; `results/vision_manifest.json` holds per-file sha256 of every Binance Vision file used.

## Binance Vision (primary; deterministic archives)
{tab(['dataset', 'files requested', 'files retrieved'], rows)}
Datasets: spot & USD-M 1h klines (2024-01 → 2026-08, incl. taker-buy volumes), USD-M premium-index 1h klines, monthly funding-rate archive (interval 4h/8h per contract), daily 5-minute `metrics` (open interest in coins, ratios). Missing data: 24 premium-index bars (one day); no missing kline bars. `liquidationSnapshot` archive returned 404 for 2024 → **no historical liquidation prints** (P10 is a proxy). Note: spot archive timestamps switched to microseconds from 2025; handled in the loader.

## Cross-venue (falsification only; `results/xvenue_manifest.json`)
| venue | endpoint | coverage obtained | use |
|---|---|---|---|
| OKX | `/market/history-candles` 1H, `*-USDT-SWAP` | 2024-01 → 2026-08, 5 assets | wrong-venue perp prices |
| Coinbase Exchange | `/products/*-USD/candles` 3600 | 2024-01 → 2026-08, 5 assets | wrong-venue spot prices |
| Gate | `/spot/candlesticks` 1h | **only from 2025-09-10** (API depth cap) | wrong-venue spot (short window) |
| Kraken | `/OHLC` interval 60 | **latest 721 bars only** | feed consistency (return corr vs Binance {min(v['ret_corr_vs_binance_perp'] for v in kc.values()):.3f}–{max(v['ret_corr_vs_binance_perp'] for v in kc.values()):.3f}) |
| Hyperliquid | `info` `candleSnapshot` / `fundingHistory` | candles **only from 2026-03-05** (5000-candle cap); funding 2024-01 → 2026-08 (hourly) | funding cross-check (ρ with Binance funding 0.76–0.85), P06 venue test |
| Deribit | `get_volatility_index_data` DVOL, resolution 3600 | 2024-01 → 2026-09-01, BTC & ETH | P15 |

Connectivity from the sandbox worked for all listed hosts; geo-blocked providers noted in report 005 were not needed. Sampling: everything resampled to hourly bars in UTC. Weaknesses: single-provider primary source (Binance), USDT-quoted spot vs USD-quoted Coinbase, Gate/HL/Kraken windows too short for full-sample claims (they are labelled as such wherever used).
""")

# ---------------------------- 10 ADJUDICATION
flags = ["F1_gross_info", "F2_gross_pos_dev_and_holdout", "F3_net_pos_full_dev_holdout", "F4_net_pos_at_1.5x_cost", "F5_perturb_ge70pct_net_pos", "F6_latency1_net_pos", "F7_placebo_p_gross_le_0.10", "F8_majors_and_minors_gross_pos", "F9_venue_transfer_gross_pos", "F10_missing20_stale_net_pos"]
mark = lambda v: "n/a" if v is None else ("✔" if v else "✘")
rows = [[k] + [mark(s6[k][x]) for x in flags] + [f(s6[k]["max_abs_corr"]), "Y" if s6[k]["nonredundant"] else "N", "Y" if s6[k]["regime_dependent"] else "N", s6[k]["tier"]] for k in NAMES]
w("10_ADJUDICATION.md", f"""# 10 — Adjudication

Rules fixed in code (`py/s6_adjudicate.py`) — not adjusted after viewing the flags:
* F1 gross information: gross Sharpe > 0 and one-sided bootstrap p ≤ 0.10 (full sample). F2 gross Sharpe > 0 in both DEV and HOLDOUT. F3 net Sharpe > 0 in FULL, DEV **and** HOLDOUT at base cost. F4 net Sharpe > 0 at 1.5× costs. F5 ≥70% of parameter perturbations net-positive. F6 net > 0 with +1 bar latency. F7 placebo (random-direction null) p ≤ 0.10 on gross Sharpe. F8 gross > 0 on both majors and minors. F9 gross > 0 on every other venue tested. F10 net Sharpe > 0 with 20% random missing data (stale-hold).
* **NET_POSITIVE_EXTERNAL_CANDIDATE** = F3 ∧ F4 ∧ F5 ∧ F6 ∧ F7 ∧ holdout net bootstrap p ≤ 0.10. **GROSS_INFORMATION_ONLY** = F1, or F2 ∧ placebo p ≤ 0.10, but not net-positive. WEAK_GROSS_NOT_SIGNIFICANT = positive full-sample gross Sharpe without significance. REJECTED otherwise.
* NONREDUNDANT = max |ρ| < 0.5 and R² vs others < 0.35. REGIME_DEPENDENT = raw perm. p ≤ 0.05 in a regime family with every compared state sign-consistent DEV→HOLDOUT (45 tests; ≈2 false positives expected).

{tab(['primitive'] + [x.split('_')[0] for x in flags] + ['max |ρ|', 'non-redundant', 'regime-dep.', 'tier'], rows)}

## Decisions
* **NET_POSITIVE_EXTERNAL_CANDIDATES = {len(netpos)}.** F3 fails for all 15: either net Sharpe < 0 in DEV or HOLDOUT, or (P07) the primitive is inactive in the HOLDOUT. The one positive HOLDOUT net Sharpe (P15, +1.02, raw p=0.09, Holm p=1.0) had DEV net −1.14, 2 assets, and zero gross information in the full sample → treated as noise.
* **GROSS_INFORMATION_ONLY = {len(ginfo)}** ({', '.join(ginfo)}): PARK as *information sources / regime variables*, not strategies. P07 is the most economically credible (documented funding-carry mechanism, delta-neutral, survives latency/missing-data tests) but the carry it harvests vanished in the HOLDOUT and pays ≈0.3%/yr net of costs on capital before margin, exchange-risk and basis-blowout effects that are not modelled. P05's gross Sharpe replicates on OKX (0.92) and Coinbase (0.78) prices, but so do P02/P04/P14 — these venues quote near-identical prices (return correlation >0.99), so this is a data-feed consistency check, not independent confirmation — and it is negative in the short Gate window (−0.31); P05 earns ≈0 net and its IC flips sign DEV→HOLDOUT. P06 and P14 fail asset/venue robustness (P06) or cost by two orders of magnitude (P14).
* **Redundancy:** trend pair P01/P04; flow pair P03/P11. Neither pair is worth keeping both members of.
* **External-candidate labels (repo doctrine):** P07 → PARK (monitor carry regime; needs live funding capture); P05 → PARK (re-test on independent later data, lower-cost execution); P06/P14 → PARK as diagnostics; P01, P02, P03, P04, P08, P09, P10, P11, P12, P13, P15 → REJECT for this universe/resolution/cost model (no ADOPT/ADAPT).
* **ANY_DROP_IN_STRATEGY = FALSE. LOCAL_INTEGRATION_AUTHORIZED = FALSE.** Integration adjudication belongs to the later study against the real local repository.

## Suggested next external tests (not executed here)
1. Forward paper-capture of funding, OI and liquidation prints with receipt stamps (removes the archive-vs-live gap for P06/P07/P09/P10 and gives true liquidation data).
2. Lower-frequency (4h/1d) re-run of P05/P06/P02 to reduce cost drag; explicit maker-fill model.
3. Independent 2026-09+ data as a true untouched holdout for P05/P07.
""")

# ---------------------------- 11 LIMITATIONS
w("11_LIMITATIONS.md", f"""# 11 — Limitations

1. **Power.** 914 days, 10 highly correlated assets: HOLDOUT net-Sharpe bootstrap bands are ≈±1.5 wide. Absence of support ≠ proof of absence.
2. **Multiplicity.** 15 primitives × several diagnostics × 45 regime tests. Raw p-values are reported; Holm is applied only to the 15 holdout tests. Any single "significant" flag should be assumed spurious until replicated.
3. **Pre-registration is partial.** Parameters were fixed before viewing results except: P07 threshold and P12 trigger (re-selected on DEV after a degenerate first pass, 05 §5.4); the placebo null design (circular shift → block sign randomisation after seeing the circular null was contaminated); IC definition (centered → uncentered after inspecting an inconsistent centered IC); P14/P15 code boundary fixes. The first-pass P07/P12 numbers were seen.
4. **Costs are generic assumptions, not measured fills.** Taker 5 bp + 1–3 bp slippage; no market impact, no queue/maker modelling, no funding-timing slippage, no borrow/margin cost, no capital-efficiency accounting for the carry pair, no exchange counterparty risk. Real fees depend on tier/rebates. UNKNOWN cost was set to 15 bp, not zero.
5. **Execution timing.** 0-latency close-to-close fills (+1..+6 bar latency is falsified, but intrabar execution, partial fills and rate limits are not).
6. **Universe/survivorship.** 10 ex-post liquid Binance perps; new listings and delistings excluded; equal-notional weights overweight high-vol alts; no vol targeting.
7. **Resolution.** 1h bars only; seasonality, quarter-hour and microstructure effects live at finer scales (D02, D23, D24 not tested).
8. **Data.** Binance is the sole full-history source; other venues cover 5 assets with shorter (Gate, Hyperliquid, Kraken) windows. OI timestamp semantics undocumented (conservative +5 min). No historical liquidation prints (P10 is a proxy). DVOL is one tenor; no PIT options surface, so term-structure/skew/GEX are unevaluated.
9. **Regime analysis** uses three simple causal labels; regime-conditional returns are descriptive, not filters, and 3-state splits with ~300 days each carry wide error bars.
10. **Literature layer is DOCUMENTED_CLAIM.** Papers were located via search snippets/abstracts and not independently replicated; OSS projects were not code-inspected; ~10 searches is not a systematic review.
11. **Stat details.** Sharpe on daily aggregated PnL with √365; bootstrap is stationary (7-day blocks); regressions in 06 use plain OLS t-stats without HAC; PCA participation ratio excludes P07; IC uses weekly blocks.
12. **No claim** of production profitability, of compatibility with AurumShift, or that any listed primitive should be integrated.
""")
print(final)
