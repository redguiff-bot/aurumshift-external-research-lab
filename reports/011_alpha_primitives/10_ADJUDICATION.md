# 10 — Adjudication

Rules fixed in code (`py/s6_adjudicate.py`) — not adjusted after viewing the flags:
* F1 gross information: gross Sharpe > 0 and one-sided bootstrap p ≤ 0.10 (full sample). F2 gross Sharpe > 0 in both DEV and HOLDOUT. F3 net Sharpe > 0 in FULL, DEV **and** HOLDOUT at base cost. F4 net Sharpe > 0 at 1.5× costs. F5 ≥70% of parameter perturbations net-positive. F6 net > 0 with +1 bar latency. F7 placebo (random-direction null) p ≤ 0.10 on gross Sharpe. F8 gross > 0 on both majors and minors. F9 gross > 0 on every other venue tested. F10 net Sharpe > 0 with 20% random missing data (stale-hold).
* **NET_POSITIVE_EXTERNAL_CANDIDATE** = F3 ∧ F4 ∧ F5 ∧ F6 ∧ F7 ∧ holdout net bootstrap p ≤ 0.10. **GROSS_INFORMATION_ONLY** = F1, or F2 ∧ placebo p ≤ 0.10, but not net-positive. WEAK_GROSS_NOT_SIGNIFICANT = positive full-sample gross Sharpe without significance. REJECTED otherwise.
* NONREDUNDANT = max |ρ| < 0.5 and R² vs others < 0.35. REGIME_DEPENDENT = raw perm. p ≤ 0.05 in a regime family with every compared state sign-consistent DEV→HOLDOUT (45 tests; ≈2 false positives expected).

| primitive | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 | F10 | max |ρ| | non-redundant | regime-dep. | tier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P01_TSMOM | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | 0.79 | N | N | REJECTED |
| P02_XS_RS | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✔ | ✘ | ✘ | 0.32 | Y | Y | WEAK_GROSS_NOT_SIGNIFICANT |
| P03_REV_4H | ✘ | ✔ | ✘ | ✘ | ✘ | ✘ | ✘ | ✔ | ✘ | ✘ | 0.55 | N | Y | WEAK_GROSS_NOT_SIGNIFICANT |
| P04_DONCHIAN | ✘ | ✔ | ✘ | ✘ | ✘ | ✘ | ✘ | ✔ | ✔ | ✘ | 0.79 | N | N | WEAK_GROSS_NOT_SIGNIFICANT |
| P05_VOL_SQUEEZE_BREAK | ✘ | ✔ | ✘ | ✘ | ✘ | ✔ | ✔ | ✔ | ✘ | ✘ | 0.27 | Y | N | GROSS_INFORMATION_ONLY (not net-monetisable at generic taker costs) |
| P06_FUND_XS | ✔ | ✔ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | 0.20 | Y | N | GROSS_INFORMATION_ONLY (not net-monetisable at generic taker costs) |
| P07_BASIS_CARRY | ✔ | ✘ | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ | n/a | ✔ | flat/NA | Y | N | GROSS_INFORMATION_ONLY (not net-monetisable at generic taker costs) |
| P08_SPOT_PERP_BASIS | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | 0.41 | Y | Y | REJECTED |
| P09_OI_PRICE | ✘ | ✔ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✔ | ✘ | 0.20 | Y | N | WEAK_GROSS_NOT_SIGNIFICANT |
| P10_LIQ_FLUSH_PROXY | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | 0.34 | Y | N | REJECTED |
| P11_TAKER_FLOW | ✘ | ✔ | ✘ | ✘ | ✘ | ✘ | ✘ | ✔ | ✔ | ✘ | 0.55 | N | N | WEAK_GROSS_NOT_SIGNIFICANT |
| P12_ILLIQ_SHOCK | ✘ | ✔ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✔ | ✘ | 0.10 | Y | Y | WEAK_GROSS_NOT_SIGNIFICANT |
| P13_BTC_LEADLAG | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | 0.16 | Y | N | REJECTED |
| P14_HOUR_SEASON | ✔ | ✔ | ✘ | ✘ | ✘ | ✘ | ✔ | ✔ | ✘ | ✘ | 0.19 | Y | N | GROSS_INFORMATION_ONLY (not net-monetisable at generic taker costs) |
| P15_RV_IV_VRP | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | n/a | n/a | ✘ | 0.12 | Y | N | REJECTED |


## Decisions
* **NET_POSITIVE_EXTERNAL_CANDIDATES = 0.** F3 fails for all 15: either net Sharpe < 0 in DEV or HOLDOUT, or (P07) the primitive is inactive in the HOLDOUT. The one positive HOLDOUT net Sharpe (P15, +1.02, raw p=0.09, Holm p=1.0) had DEV net −1.14, 2 assets, and zero gross information in the full sample → treated as noise.
* **GROSS_INFORMATION_ONLY = 4** (P05_VOL_SQUEEZE_BREAK, P06_FUND_XS, P07_BASIS_CARRY, P14_HOUR_SEASON): PARK as *information sources / regime variables*, not strategies. P07 is the most economically credible (documented funding-carry mechanism, delta-neutral, survives latency/missing-data tests) but the carry it harvests vanished in the HOLDOUT and pays ≈0.3%/yr net of costs on capital before margin, exchange-risk and basis-blowout effects that are not modelled. P05's gross Sharpe replicates on OKX (0.92) and Coinbase (0.78) prices, but so do P02/P04/P14 — these venues quote near-identical prices (return correlation >0.99), so this is a data-feed consistency check, not independent confirmation — and it is negative in the short Gate window (−0.31); P05 earns ≈0 net and its IC flips sign DEV→HOLDOUT. P06 and P14 fail asset/venue robustness (P06) or cost by two orders of magnitude (P14).
* **Redundancy:** trend pair P01/P04; flow pair P03/P11. Neither pair is worth keeping both members of.
* **External-candidate labels (repo doctrine):** P07 → PARK (monitor carry regime; needs live funding capture); P05 → PARK (re-test on independent later data, lower-cost execution); P06/P14 → PARK as diagnostics; P01, P02, P03, P04, P08, P09, P10, P11, P12, P13, P15 → REJECT for this universe/resolution/cost model (no ADOPT/ADAPT).
* **ANY_DROP_IN_STRATEGY = FALSE. LOCAL_INTEGRATION_AUTHORIZED = FALSE.** Integration adjudication belongs to the later study against the real local repository.

## Suggested next external tests (not executed here)
1. Forward paper-capture of funding, OI and liquidation prints with receipt stamps (removes the archive-vs-live gap for P06/P07/P09/P10 and gives true liquidation data).
2. Lower-frequency (4h/1d) re-run of P05/P06/P02 to reduce cost drag; explicit maker-fill model.
3. Independent 2026-09+ data as a true untouched holdout for P05/P07.
