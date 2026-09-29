import catalog as C, primitives as pr, os
R = "../../../reports/011_alpha_primitives/"; os.makedirs(R, exist_ok=True)
o = ["# 02 — Primitive contracts (PRE-DECLARED)\n",
"Status: written and committed **before** the full 10-asset results were produced. A 3-asset (BTC/ETH/SOL) smoke run of the pipeline was seen beforehand (disclosed in 11_LIMITATIONS); no signal definition, sign, horizon, mode or threshold was changed after it.\n",
"Every primitive fixes, ex ante: sign (direction), primary mode (TS = per-asset sized, CS = dollar-neutral cross-sectional), primary horizon H, and all parameters. Secondary horizon/mode are reported but **adjudication uses the primary spec only** (15 tests ⇒ Benjamini–Hochberg over 15).\n",
"## Common conventions\n",
"- Rows are 1h bars labelled by open time; row t is known at t+1h (decision instant). Fill at next open (delay 0); +1/+2 bar delay tested in falsification.",
"- Portfolio: 1/H of the book re-formed every hour and held H hours (overlapping tranches), TS weight = clip(s/std₇₂₀(s),±1)/N (gross ≤ 1), CS weight = demeaned clipped z, gross 1, dollar-neutral, ≥60% of universe valid.",
"- Universe (core): BTC ETH SOL XRP BNB DOGE ADA LINK AVAX LTC (Binance USD-M perps). Holdout universe for the different-asset test: DOT ATOM NEAR TRX BCH ETC.",
"- Splits: DEV 2023-01→2024-12, TEST 2025-01→2026-08 (2022-10→2022-12 warm-up only). No parameter is fitted on either split; both are out-of-sample with respect to fitting, but the *design* was made with knowledge of published literature (see 11).",
"- Costs per side (bps, generic, NOT venue-verified): BTC/ETH 6, other core 8, holdout 10 (≈5 taker fee + 1/3/5 half-spread/slippage). Stress ×2/×3/×5; ×0.5 shown only as an optimistic bound. **Unknown costs (market impact, fee tiers, borrow, latency slippage) are not zero** — they are what the multipliers stand in for. Funding paid/received is charged from real funding data and included in *net*.",
"- gross = price P&L only. net = gross − trading cost − funding.\n",
"## Adjudication rules (pre-declared)\n",
"- C1 forward-safety: truncation test PASS (bench/…/lookahead_test.py).",
"- C2 net Sharpe > 0 in both DEV and TEST at 1× cost.",
"- C3 FULL-sample net Newey–West t ≥ 2.0 **and** BH-q < 0.10 across the 15 primary tests.",
"- C5 net Sharpe > 0 at 2× cost. C6 ≥70% of applicable falsification checks passed (delay+1, parameter perturbation min>0, missing-25%, stale-25%, holdout assets gross>0, Coinbase-signal venue gross>0).",
"- Tier: SUPPORTED_ROBUST = C1∧C2∧C3∧C5∧C6; SUPPORTED_FRAGILE = C1∧C2∧C3 only; GROSS_ONLY = gross t ≥ 2 but not net; else NOT_SUPPORTED.",
"- Non-redundant = supported primitive whose |signal-rank corr| and |gross daily-P&L corr| < 0.5 versus every higher-ranked supported primitive.",
"- Regime-dependent = net t ≤ −1.5 in one and ≥ +1.5 in the opposite bucket (vol low/high or trend up/down), or t ≥ 2.5 in a bucket while FULL net t < 2.",
"- FINAL_VERDICT: MULTIPLE (≥3 SUPPORTED_ROBUST non-redundant), LIMITED (1–2 SUPPORTED_ROBUST or SUPPORTED_FRAGILE non-redundant), NO_ROBUST (none), INCONCLUSIVE (data/pipeline failure or placebo test shows pipeline cannot separate signal from noise).\n",
"## Executed primitives\n"]
for n, v in C.X.items():
    fn, fam, mode, H, sH, note, needs = pr.REG[n]; m = v
    o += [f"### {n} — {fam}\n", f"- **Mechanism**: {m[0]}", f"- **Formula**: {m[1]}", f"- **Required inputs**: {m[2]}", f"- **Sampling**: {m[3]}", f"- **Horizon**: {m[4]}", f"- **Pre-declared**: sign `{note}`; primary mode **{mode}**, primary H **{H}h** (secondary {sH}h)", f"- **Failure modes**: {m[5]}", f"- **Lookahead risks / controls**: {m[6]}", f"- **Forward-safety class**: `{m[7]}`", f"- **Literature basis**: {m[8]}\n"]
o += ["## Discovered but not executed\n", "| id | primitive | family | class | why not executed |", "|---|---|---|---|---|"] + [f"| {d[0]} | {d[1]} | {d[2]} | `{d[3]}` | {d[4]} |" for d in C.D]
open(R + "02_PRIMITIVE_CONTRACTS.md", "w").write("\n".join(o) + "\n")
