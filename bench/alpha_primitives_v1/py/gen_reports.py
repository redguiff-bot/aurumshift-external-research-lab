"""Generates the data-heavy report sections from results/*.json (no numbers typed by hand in tables)."""
import json, os, datetime as dt
import catalog as CT
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); RES = os.path.join(ROOT, "results")
OUT = os.path.join(os.path.dirname(os.path.dirname(ROOT)), "reports", "011_alpha_primitives"); os.makedirs(OUT, exist_ok=True)
J = lambda f: json.load(open(os.path.join(RES, f)))
s0, s1, s2, s3, s4, s5, s6 = J("s0_tune.json"), J("s1_main.json"), J("s2_ortho.json"), J("s3_regime.json"), J("s4_cost.json"), J("s5_falsify.json"), J("s6_adjudication.json")
s5p = s5["prims"]; NAMES = list(s1["primitives"]); PR = s1["primitives"]
def f(x, d=2, pct=False):
    if x is None or x != x: return "flat/NA"
    return f"{x*100:.{d}f}%" if pct else f"{x:.{d}f}"
def tab(head, rows): return "| " + " | ".join(head) + " |\n|" + "---|" * len(head) + "\n" + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in rows) + "\n"
def w(fn, s): open(os.path.join(OUT, fn), "w").write(s)
short = lambda k: k.split("_", 1)[0]

# ---------------- 05 RESULTS
r = []
for k in NAMES:
    a = PR[k]; F, D, H = a["full"], a["dev"], a["holdout"]
    r.append([k, f(F["gross_sharpe"]), f(F["net_sharpe"]), f(F["gross_ann"], 1, True), f(F["price_ann"], 1, True), f(F["funding_ann"], 1, True), f(-F["cost_ann"], 1, True), f(F["net_ann"], 1, True), f"{F['turn_ann']:.0f}", f(a["breakeven_bps_per_side"], 1)])
t1 = tab(["primitive", "gross Sharpe", "net Sharpe", "gross ann.", "price", "funding", "cost", "net ann.", "turnover/yr", "break-even bps/side"], r)
r = []
for k in NAMES:
    a = PR[k]; F, D, H = a["full"], a["dev"], a["holdout"]
    r.append([k, f(D["gross_sharpe"]), f(D["net_sharpe"]), f(H["gross_sharpe"]), f(H["net_sharpe"]), f(H["boot"]["lo5"]) + " .. " + f(H["boot"]["hi95"]) if H.get("boot") else "NA", f(H["boot"]["p_one_sided"]) if H.get("boot") else "NA", f(s6[k]["holdout_boot_p_holm15"]), f(a["boot_gross_full"]["p_one_sided"])])
t2 = tab(["primitive", "DEV gross", "DEV net", "HOLDOUT gross", "HOLDOUT net", "HOLDOUT net Sharpe 90% boot band", "HOLDOUT net p (1-sided)", "Holm(15) p", "FULL gross p (1-sided)"], r)
r = []
for k in NAMES:
    a = PR[k]
    def ic(x): return "NA" if x["ic"] is None else f"{x['ic']:+.4f} (t={x['t']:+.1f}, {x['weeks']}w)"
    r.append([k, a["ic_H"], ic(a["ic_full"]), ic(a["ic_dev"]), ic(a["ic_holdout"]), f(a["active_share"], 2)])
t3 = tab(["primitive", "IC horizon (h)", "IC full", "IC dev", "IC holdout", "active share"], r)
B = s1["baseline_ew_long"]
base = f"Baseline BASE_EW_LONG (equal-weight long all 10 perps, no rebalancing cost, funding paid): gross/net Sharpe {f(B['full']['gross_sharpe'])}, price {f(B['full']['price_ann'],1,True)}/yr, funding {f(B['full']['funding_ann'],1,True)}/yr, max DD {f(B['full']['maxdd_net'],1,True)} (sum of daily returns). Beta, not alpha: every directional primitive below must beat this in risk-adjusted terms AND be uncorrelated with it (see 06)."
tune = "\n".join(f"* **{k}**: DEV-only grid {json.dumps([{kk: (round(vv,4) if isinstance(vv,float) else vv) for kk, vv in row.items()} for row in v['grid']])} -> selected `{json.dumps(v['selected'])}`" for k, v in s0.items())
w("05_RESULTS.md", f"""# 05 — Results (base cost, EXTERNAL_RESEARCH_ONLY)

Universe: 10 Binance USD-M perpetuals (BTC ETH SOL XRP BNB DOGE ADA LINK AVAX LTC), 1h bars, evaluation 2024-03-01 → 2026-08-31 (914 days).
DEV = 2024-03-01 → 2025-05-31; HOLDOUT = 2025-06-01 → 2026-08-31. Parameters are pre-registered defaults, fixed before results were viewed, except the two DEV-only reselections below. Sharpe = daily PnL, √365. PnL is a fraction of gross capital (equal-notional legs, 1/N per asset).
**GROSS = price PnL + funding cash flow, before trading costs. NET = GROSS − trading costs.** Base cost per side: taker 5 bp + slippage/half-spread (BTC/ETH 1 bp → 6 bp; other assets 3 bp → 8 bp); spot leg of the carry pair +5 bp fee. Unmapped venue/asset → 15 bp (UNKNOWN_COST ≠ ZERO_COST).

{base}

## 5.1 Full-sample decomposition
{t1}
`break-even bps/side` = gross annual return ÷ annual turnover: the per-side cost at which net = 0. Compare with 6–8 bp paid.

## 5.2 DEV vs HOLDOUT (with stationary-bootstrap uncertainty)
{t2}
p-values are one-sided stationary block bootstrap (7-day blocks, 2000 draws), null = mean ≤ 0. Holm(15) adjusts the 15 holdout-net tests.

## 5.3 Information coefficient (position vs forward vol-normalised return, uncentered/cosine, weekly blocks)
{t3}
IC is diagnostic only. It is not defined for P07 (delta-neutral pair) and P12 has too few active weeks in some windows.

## 5.4 DEV-only re-selection of two mis-specified triggers (disclosed deviation)
{tune}

Both first-pass triggers were degenerate: P07's threshold (1e-4 per 8h) equals Binance's default funding clamp so the state flip-flopped (51 turns/yr on the DEV window, cost > gross); P12's log-Amihud z>2 fired on 0.014% of bars. Selection used the DEV window only (P12: highest DEV net Sharpe among candidates with ≥20 turns/yr, i.e. 1.75). HOLDOUT was not used. Nevertheless the initial full-sample results had been seen, so P07/P12 carry a mild snooping penalty.

## 5.5 Causality audit (mechanical lookahead test)
For each primitive, weights were recomputed with all data after 5 random cut-points deleted; weights up to the cut-point (minus one bar for P14's boundary construction) must match the full-data weights to 1e-9. Result: **{sum(1 for v in s1['causality_audit'].values() if v['pass'])}/15 PASS**, max abs diff {max(v['max_abs_diff'] for v in s1['causality_audit'].values()):.1e}. This proves the signal code is causal; it does not prove the *archives* were available with the stamped latency (see 03).
""")

# ---------------- 06 ORTHOGONALITY
C = s2["corr_gross"]; ks = [k for k in NAMES if k in C]
mat = tab([""] + [short(k) for k in ks], [[short(a)] + [f"{C[b][a]:.2f}" if C[b][a] is not None else "NA" for b in ks] for a in ks])
red = tab(["primitive", "max |corr| (partner)", "R² vs all others", "cluster (|dist|<0.5)", "market beta", "alpha ann. (gross)", "alpha t", "corr to EW market"], [[k, f"{s2['redundancy'][k]['max_abs_corr']:.2f} ({short(s2['redundancy'][k]['partner'])})" if k in s2['redundancy'] else "excluded (delta-neutral / degenerate)", f(s2['redundancy'][k]['R2_vs_others']) if k in s2['redundancy'] else "NA", s2['clusters_absdist_lt_0.5'].get(k, "NA"), f(s2['market_beta'][k]['beta']), f(s2['market_beta'][k]['alpha_ann'], 1, True), f(s2['market_beta'][k]['alpha_t']), f(s2['market_beta'][k]['corr_mkt'])] for k in NAMES])
per = tab(["primitive", "weight autocorr 1h", "6h", "24h", "72h", "mean holding (h)", "turnover/yr", "cost drag/yr", "share of 90d windows gross>0"], [[k] + [f(s2['persistence'][k].get(x)) for x in ("wac_lag1", "wac_lag6", "wac_lag24", "wac_lag72")] + [f(s2['persistence'][k]['mean_hold_hours'], 1), f"{s2['persistence'][k]['turnover_per_year']:.0f}", f(s2['persistence'][k]['cost_drag_ann_at_base'], 1, True), f(s2['persistence'][k]['frac_90d_windows_gross_pos'])] for k in NAMES])
PC = s2["corr_position"]; pk = list(PC)
pmat = tab([""] + [short(k) for k in pk], [[short(a)] + [f"{PC[b][a]:.2f}" for b in pk] for a in pk])
w("06_ORTHOGONALITY.md", f"""# 06 — Orthogonality, redundancy, persistence, turnover

All measures on the evaluation window, daily GROSS PnL (net PnL correlations are dominated by common cost structure and are in `results/s2_ortho.json`).

## 6.1 Daily gross-PnL correlation
{mat}
* PCA participation ratio (effective independent bets) over {s2['n_primitives_in_pca']} primitives: **{s2['effective_independent_bets_pr']:.1f}** (P07 excluded: near-constant carry stream). A high ratio mostly says most streams are noise-dominated and mutually uncorrelated, not that each carries alpha.
* Redundant pairs (|ρ| ≥ 0.5): P01↔P04 (0.79, trend family), P03↔P11 (−0.55, reversal vs continuation of flow: the same information with opposite sign). Every other pair has |ρ| < 0.5.
* Cluster count at |1−|ρ||<0.5: see table below.

## 6.2 Redundancy, market beta and alpha
{red}
`alpha` is the intercept of daily gross PnL on the equal-weight perp market return (OLS t, no HAC).

## 6.3 Position correlation (perp-equivalent exposure; P07 excluded)
{pmat}

## 6.4 Persistence and turnover implications
{per}
Turnover implication: at the generic 6–8 bp per side, any primitive with turnover above roughly 100–150×/yr needs a gross edge above 6–12%/yr *per unit of gross exposure* just to break even; only P05, P07 and the slow group (P02, P04) are in a plausible cost range, and none clears it (see 08).
""")

# ---------------- 07 REGIME
rows = []
for k in NAMES:
    for n, x in s3["prims"][k].items():
        st = x["states"]; parts = []
        for s, v in sorted(st.items()):
            g = v["gross_full"]; parts.append(f"{s}: {f(g['ann_ret'],1,True)} (t={f(g['t'],1)})")
        rows.append([k, n, "; ".join(parts), f(x["perm_p_range"]), f"{x['sign_consistent_dev_holdout']}/{x['n_states_cmp']}"])
t7 = tab(["primitive", "regime family", "GROSS annualised return per state (t on daily sums)", "perm. p (state range)", "sign-consistent DEV→HOLDOUT (states)"], rows)
shr = "; ".join(f"**{n}**: " + ", ".join(f"{a}={b:.2f}" for a, b in v.items()) for n, v in s3["regime_share"].items())
w("07_REGIME_CONDITIONAL.md", f"""# 07 — Regime-conditional behaviour

Regimes are computed only from trailing information and lagged one bar: **vol** = BTC 168h realised-vol percentile vs trailing 90 days (low/mid/high terciles); **trend** = sign of BTC 30-day return (bull/bear); **funding_heat** = cross-asset mean funding percentile vs trailing 90 days (cold/neutral/hot). Share of evaluation hours: {shr}.

Test of regime dependence: range across states of mean hourly gross PnL vs a null of the same labels circularly shifted (300 draws; preserves label persistence). **45 primitive×regime tests are run, so ≈2 raw p≤0.05 hits are expected by chance.** Gross returns shown; net is in the JSON.

{t7}

Reading rules used in 10: a primitive is called REGIME_DEPENDENT only if raw perm. p ≤ 0.05 in at least one family AND every compared state keeps its sign from DEV to HOLDOUT. Conditional gross returns in a single state are never treated as a tradable filter without an independent holdout: the filter would be selected on the same data.
""")

# ---------------- 08 COST
rows = []
for k in NAMES:
    c = s4[k]; m = c["mult"]
    rows.append([k] + [f(m[x]["full"]["net_sharpe"]) for x in ("0", "0.5", "1", "1.5", "2", "3")] + [f(c["all_unknown_15bps"]["net_sharpe"]), f(c["no_funding_net_sharpe"]), f(c["gross_to_cost_ratio"])])
t8 = tab(["primitive", "net Sharpe @0× (=gross)", "0.5×", "1× (base)", "1.5×", "2×", "3×", "all-UNKNOWN 15 bp", "funding excluded (wrong for perps; shows funding weight)", "gross/cost ratio"], rows)
rows = []
for k in NAMES:
    u = s4[k]["uniform_bps"]; rows.append([k] + [f(u[b]["net_ann"], 1, True) for b in ("0", "2", "5", "8", "12", "20", "30")])
t8b = tab(["primitive"] + [f"{b} bp/side" for b in (0, 2, 5, 8, 12, 20, 30)], rows)
rows = [[k, f(s4[k]["mult"]["1"]["holdout"]["net_sharpe"]), f(s4[k]["mult"]["2"]["holdout"]["net_sharpe"])] for k in NAMES]
t8c = tab(["primitive", "HOLDOUT net Sharpe 1×", "HOLDOUT net Sharpe 2×"], rows)
w("08_COST_SENSITIVITY.md", f"""# 08 — Cost sensitivity

Cost model: per-side bps of traded notional = taker fee 5 bp + slippage (BTC/ETH 1, others 3) → 6/8 bp; carry spot leg +5 bp; UNKNOWN venue/asset = 15 bp; funding is paid/received explicitly per settlement. "Maker-only" is *not* assumed: fill probability/adverse selection is unknown, and UNKNOWN_COST ≠ ZERO_COST (the 0–2 bp columns are shown as upper bounds, not scenarios).

## 8.1 Net Sharpe vs cost multiplier (full sample)
{t8}
## 8.2 Net annual return vs uniform per-side cost
{t8b}
## 8.3 HOLDOUT net Sharpe at 1× and 2×
{t8c}
Take-aways are in 10. Key structural fact: the gross/cost ratio exceeds 1 for exactly two primitives (P05 and P07, see last column); primitives with positive gross Sharpe but high turnover (P03, P11, P14, P09) have break-even costs of 0.5–3 bp/side, far below one taker fee. P05 loses its net edge at 1.5× cost; P07's net edge is ~0.3%/yr of capital.
""")

# ---------------- 09 FALSIFICATION
def pert(k): p = s5p[k]["perturbation"]; return [f(p["frac_net_pos"], 2), f(p["frac_gross_pos"], 2), f(p["median_net_sharpe"]), f(p["min_net_sharpe"]), f(p["max_net_sharpe"])]
t9a = tab(["primitive", "share net>0", "share gross>0", "median net Sharpe", "min", "max"], [[k] + pert(k) for k in NAMES])
t9b = tab(["primitive", "base net", "lag+1h", "+2h", "+3h", "+6h"], [[k, f(PR[k]["full"]["net_sharpe"])] + [f(s5p[k]["latency"][l]["net_sharpe"]) for l in ("1", "2", "3", "6")] for k in NAMES])
rows = []
for k in NAMES:
    m = s5p[k]["missing"]; rows.append([k] + [f"{f(m[x]['flat']['net_sharpe'])} / {f(m[x]['stale']['net_sharpe'])}" for x in ("obs_0.05", "obs_0.2", "asset_day_0.1")])
t9c = tab(["primitive", "5% random obs missing (flat / stale-hold)", "20% missing", "10% asset-day outages"], rows)
rows = []
for k in NAMES:
    a = s5p[k]["assets"]; lo = a["leave_one_out_net_sharpe"]
    rows.append([k, f(a["majors"]["gross_sharpe"]) + " / " + f(a["majors"]["net_sharpe"]) if a["majors"] else "NA", f(a["minors"]["gross_sharpe"]) + " / " + f(a["minors"]["net_sharpe"]) if a["minors"] else "NA", f"{f(lo['min'])} .. {f(lo['max'])}" if lo else "NA"])
t9d = tab(["primitive", "majors (BTC ETH BNB SOL XRP) gross/net", "minors (DOGE ADA LINK AVAX LTC) gross/net", "leave-one-asset-out net Sharpe range"], rows)
rows = []
for k in NAMES:
    p = s5p[k]["placebo"]; rows.append([k, p["null"], f(p["obs_gross"]), f(p["placebo_gross_mean"]) + " ± " + f(p["placebo_gross_sd"]), f(p["p_gross"])])
t9e = tab(["primitive", "null", "observed gross Sharpe", "null gross Sharpe (mean ± sd)", "p (null ≥ observed)"], rows)
rows = [[k, f(s5p[k]["quarters"]["frac_gross_pos"]), f(s5p[k]["quarters"]["frac_net_pos"]), f(s5p[k]["quarters"]["worst_q_net"], 1, True), f(s5p[k]["rolling90_net_pos_frac"])] for k in NAMES]
t9f = tab(["primitive", "share of quarters gross>0", "share net>0", "worst quarter net", "share of 90d windows net>0"], rows)
rows = []
for k in NAMES:
    v = s5p[k].get("venues") or {}
    for vn, x in v.items():
        if "venue" in x: rows.append([k, vn, f"gross {f(x['venue']['gross_sharpe'])} / net {f(x['venue']['net_sharpe'])}", f"gross {f(x['binance_same_assets_same_window']['gross_sharpe'])} / net {f(x['binance_same_assets_same_window']['net_sharpe'])}"])
        elif "okx_exec" in x: rows.append([k, vn, f"OKX exec: gross {f(x['okx_exec']['gross_sharpe'])} / net {f(x['okx_exec']['net_sharpe'])}", f"Binance exec: gross {f(x['binance_exec']['gross_sharpe'])} / net {f(x['binance_exec']['net_sharpe'])}"])
        elif "hl_signal_okx_prices" in x: rows.append([k, vn, f"HL funding signal, OKX prices: gross {f(x['hl_signal_okx_prices']['gross_sharpe'])} / net {f(x['hl_signal_okx_prices']['net_sharpe'])}", f"Binance funding signal, OKX prices: gross {f(x['binance_signal_okx_prices']['gross_sharpe'])} / net {f(x['binance_signal_okx_prices']['net_sharpe'])}; corr HL~Binance funding " + ", ".join(f"{a} {v_:.2f}" for a, v_ in x['corr_hl_vs_binance_funding'].items())])
t9g = tab(["primitive", "venue test", "result on other venue", "same-asset/window reference"], rows)
vi = s5["venue_info"]; kc = s5["kraken_check"]
w("09_FALSIFICATION.md", f"""# 09 — Falsification battery

Goal: try to break every primitive. Anything that only works at one venue, one cost level, one parameter setting, one asset group or one regime is not a primitive. Cross-venue panels use 5 assets (BTC ETH SOL XRP DOGE): OKX perp (from {vi['okx_perp']['eval_start'][:10]}), Coinbase spot USD (same window; spot cost = perp + 5 bp), Gate spot (only from {vi['gate_spot']['eval_start'][:10]}, API depth limit), Hyperliquid candles (only ~6 months; used for data checks only), Kraken (721 hourly bars; return correlation vs Binance perp {min(v['ret_corr_vs_binance_perp'] for v in kc.values()):.3f}–{max(v['ret_corr_vs_binance_perp'] for v in kc.values()):.3f}, so price feeds agree and venue divergence is not a price-data artefact). Because these venues quote near-identical prices, cross-venue agreement is a consistency check, not independent evidence; note also that the 5-asset subset yields different gross Sharpes than the 10-asset universe (universe sensitivity, see 00). Price-only primitives run natively on the other venue (no funding on either side for like-for-like); feature primitives (funding/OI/flow/illiquidity) are computed from Binance data and *executed* on OKX prices.

## 9.1 Higher costs
See 08 (0.5×–3×, uniform bp, all-UNKNOWN). No primitive is net-positive at 1.5× in both DEV and HOLDOUT.

## 9.2 Wrong venue / different data provider
{t9g}

## 9.3 Different asset groups
{t9d}

## 9.4 Regime reversal, high volatility, low volatility
Per-regime gross/net tables are in 07 (vol terciles, bull/bear, funding heat). Sub-period stability:
{t9f}

## 9.5 Missing data (fail-closed / stale-hold), 3 seeds averaged; net Sharpe
`flat/NA` under stale-hold means the primitive never trades (fails closed because a strict rolling window can no longer be filled).
{t9c}

## 9.6 Stale data / latency (fills delayed by 1–6 bars; net Sharpe)
{t9b}

## 9.7 Parameter perturbation (scalable parameters ×0.5, ×0.75, ×1.5, ×2)
{t9a}

## 9.8 Placebo (directional information test)
Directional primitives: independent ±1 per asset per 24h block multiplied into the weights (keeps turnover/exposure structure, destroys direction; 200 draws). P07: circular time shift (random timing of the carry state). A circular shift was first tried for all primitives and *rejected*: wrap-around lets late, better-informed expanding estimates hit early returns, inflating the null (P14's null Sharpe was 2.1 vs 0.85 observed).
{t9e}
""")
print("written", OUT)
