# 06 — Conformal methods: what is actually valid? (§7)

Setup: `py/conformal.py`, α=0.10 for regression intervals on the latent forward return, α=0.20 for 3-class LAC sets; 12 held-out seeds; frozen W=300, half-life 150, ACI γ=0.01 (chosen on tuning seeds; γ=0.02 lowered the coverage gap slightly but raised the infinite-interval rate from 4 % to 9 % for ACI-on-split-scores). All online methods use only matured scores (H=10); ACI's error feedback is delayed by the same H. Tables `results/tables/conf_*.md`, public: `public_*`. Coverage is *marginal, averaged over the 3000 post-onset steps*, unless a "worst window" (300 steps) or conditional split is named.

## Theory (DOCUMENTED_CLAIM; papers not re-derived here) vs what this lab observed
| method | textbook guarantee (assumption) | holds here? |
|---|---|---|
| split conformal | finite-sample marginal coverage ≥1−α under **exchangeability** of calibration and test scores | iid control: 0.902 ± 0.006 (OBSERVED). Non-exchangeable but stationary world (AR features, clustered vol): 0.904 ± 0.015 pre-onset — **marginally fine, but no guarantee is implied** (INFERENCE; ergodic averaging, not exchangeability). **Under shift: fails** (below). |
| conditional coverage of any of these | not provided by split conformal; impossible in general distribution-free | broken even in the iid control: split gives 0.981 (low-vol rows) vs 0.823 (high-vol rows) at nominal 0.90 (OBSERVED). Heteroscedasticity, not shift, causes this. |
| weighted conformal (Tibshirani et al.) | valid under **covariate** shift with a *known* likelihood ratio; not for label/concept shift | California covariate shift with an *estimated* ratio (domain classifier on unlabeled test X): 0.651 vs split 0.589 vs nominal 0.90 — the correction helps but is far from valid because the ratio is estimated on extreme, poorly-supported regions. |
| rolling-window / recency-weighted conformal | none (heuristic); Barber et al. give a coverage-gap bound depending on how far the weights are from exchangeability | roughly right on average (0.89) but undercovers transiently (worst 300-step window 0.82–0.83; 0.73 for a volatility jump). |
| ACI (Gibbs & Candès) | long-run average miscoverage → α for **arbitrary** shift, deterministically, assuming the true coverage indicator is fed back **immediately** | 0.897–0.899 average (OBSERVED) even with the delay H=10, but with delayed feedback the published bound does **not** apply as stated (Angelopoulos et al. and others discuss delay/regret — not verified here): treat as empirical. It is a *long-run marginal* statement only: no local, no conditional statement. Worst 300-step window 0.87. |
| ACI on split scores | same | Can output **infinite intervals**: 9.3 % of post-onset steps (0.3 % on rolling scores) — coverage is bought with trivial intervals. |
| Gaussian interval | none (parametric) | fails already in the stationary world: coverage 0.751 ± 0.028 vs 0.90 (heavy tails from volatility mixture + rare cluster). |
| EnbPI, conformal PID, SAOCP, AgACI | time-series/online guarantees of various kinds | **not executed** (`01_METHODS.md`) — no claim. |

## Regression intervals under shift (post-onset, mean over the 7 shift scenarios, α=0.10)
| method | marginal coverage | worst 300-step window | median width | infinite-interval rate |
|---|---|---|---|---|
| Gaussian | 0.578 | 0.499 | 2.84 | 0 |
| split conformal | **0.766** | 0.696 | 4.37 | 0 |
| rolling | 0.890 | 0.817 | 6.35 | 0 |
| recency-weighted | 0.894 | 0.828 | 6.39 | 0 |
| ACI (split scores) | 0.897 | 0.865 | (mean 41, capped) | 0.093 |
| ACI (rolling scores) | **0.899** | 0.869 | 6.47 | 0.003 |
| normalised split | 0.907 | 0.877 | 6.63 | 0 |
| normalised + ACI | 0.900 | 0.881 | 6.61 | 0 |
Volatility jump: split 0.538, Gaussian 0.368, rolling 0.879 (worst window 0.733), ACI-rolling 0.900 (worst 0.864). Regime transition: split 0.729. The price of validity is width: +45–50 % over split conformal after shifts. Locally normalised scores narrow the vol-conditional gap only partly (in the non-shifted world: low-vol 0.931 / high-vol 0.871 for normalised+ACI vs 0.981 / 0.824 for plain split).

## Classification sets (LAC, α=0.20; LR base; post-onset shift-only means)
split coverage 0.668 (target 0.80), rolling 0.793, weighted 0.793, ACI-split 0.796, ACI-rolling 0.800. Set size ≈2.05 for the online variants. Fraction of singleton decisions (usable "confident" calls): 0.24–0.25 shifted (shift-only, ACI/rolling); ≈0.38–0.42 in the stationary world; singleton accuracy 0.63 (shifted). The guarantee controls coverage, not decision quality — with a weak signal it buys validity by abstaining on most rows (`05_ABSTENTION.md`).

## Real data
* ELEC2 (α=0.2, 16 blocks of 2000): split coverage drifts between 0.59 and 0.87 across blocks (mean 0.72 LR / 0.73 GBM); rolling 0.68–0.89; ACI-rolling 0.785–0.812 in every block (mean 0.800). Confirms the synthetic finding on genuinely drifting data.
* iid tasks (credit-g, breast-cancer, 20 re-splits): split coverage 0.80–0.81 with std 0.03–0.06 (valid on average; high variance at n_cal≈114–200).
* California: iid split 0.901 ± 0.005; covariate-shift split 0.589 (Gaussian 0.546).

## Adjudication on §7
Valid (in the sense the literature states) only where assumptions hold: split conformal for **iid/exchangeable** data. Under **time series + drift** the defensible statements are (a) ACI-type methods give *empirically* near-nominal **long-run marginal** coverage, (b) nothing here gives valid conditional or per-regime coverage, (c) recency methods are heuristics that undercover during transitions, (d) with delayed labels every online guarantee is weaker than the papers' immediate-feedback theorems. CONFORMAL_SUPPORTED is therefore **PARTIAL** (marginal coverage monitor only).
