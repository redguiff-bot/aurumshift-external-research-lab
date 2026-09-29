# 10 — Adjudication

Rules were fixed in `02_PRIMITIVE_CONTRACTS.md` before the run: C1 forward-safe; C2 net Sharpe >0 in DEV and TEST; C3 FULL net NW t ≥ 2 and BH-q < 0.10 over 15; C5 net >0 at ×2 cost; C6 ≥70% of falsification checks passed. `SUPPORTED_ROBUST` = C1∧C2∧C3∧C5∧C6, `SUPPORTED_FRAGILE` = C1∧C2∧C3.

## Criteria table (C6 = falsification pass rate; boolean columns 1.00=true)
| primitive | C1_forward_safe | C2_net_pos_both_halves | C3_net_t2_BH | C5_survives_cost_x2 | C6_falsification_pass_rate | tier | regime_dependent | net_t | gross_t |
|---|---|---|---|---|---|---|---|---|---|
| P01_TSMOM | 1.00 | 0.00 | 0.00 | 0.00 | 0.17 | NOT_SUPPORTED | 0.00 | -0.57 | 0.41 |
| P02_XS_RS7D | 1.00 | 0.00 | 0.00 | 0.00 | 0.33 | NOT_SUPPORTED | 0.00 | -0.26 | 1.26 |
| P03_REV4H | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | NOT_SUPPORTED | 0.00 | -7.84 | 0.20 |
| P04_VOLCOMP_BRK | 1.00 | 0.00 | 0.00 | 0.00 | 0.50 | NOT_SUPPORTED | 0.00 | -0.00 | 1.08 |
| P05_BRK_PERSIST | 1.00 | 0.00 | 0.00 | 0.00 | 0.17 | NOT_SUPPORTED | 0.00 | -0.23 | 0.98 |
| P06_FUND_CARRY | 1.00 | 0.00 | 0.00 | 0.00 | 0.60 | NOT_SUPPORTED | 0.00 | 0.44 | 0.83 |
| P07_PREMIUM | 1.00 | 0.00 | 0.00 | 0.00 | 0.20 | NOT_SUPPORTED | 0.00 | -4.41 | -0.50 |
| P08_OI_PRICE | 1.00 | 0.00 | 0.00 | 0.00 | 0.20 | NOT_SUPPORTED | 0.00 | -0.84 | 1.60 |
| P09_OI_FLUSH | 1.00 | 0.00 | 0.00 | 0.00 | 0.20 | NOT_SUPPORTED | 0.00 | -1.40 | 0.73 |
| P10_TAKER_IMB | 1.00 | 0.00 | 0.00 | 0.00 | 0.20 | NOT_SUPPORTED | 0.00 | -8.50 | -0.44 |
| P11_LIQ_SHOCK | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | NOT_SUPPORTED | 0.00 | -5.54 | -0.93 |
| P12_LEADLAG_BTC | 1.00 | 0.00 | 0.00 | 0.00 | 0.17 | NOT_SUPPORTED | 0.00 | -31.11 | -1.77 |
| P13_SEASON_HOD | 1.00 | 0.00 | 0.00 | 0.00 | 0.17 | NOT_SUPPORTED | 0.00 | -6.99 | 1.18 |
| P14_VRP_DVOL | 1.00 | 0.00 | 0.00 | 0.00 | 0.50 | NOT_SUPPORTED | 0.00 | 0.17 | 0.40 |
| P15_FUND_DIV | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | NOT_SUPPORTED | 0.00 | -2.10 | 0.40 |

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
