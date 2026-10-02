# 04 — Online (incremental) calibration (Q3; §6 of the brief)

Setup: `py/online.py`. Recalibrators refit every R=50 steps using only labels matured by t−H (H=10). Variants: `static` (fit once on the calibration split), `window` (last W=600 matured rows, incl. validation history), `expanding` (all matured rows), `decay` (exponential weights, half-life 400), plus the leaky controls `leak_h0` (H=1) and `leak_peek` (may see the next block). W and half-life were chosen on the tuning seeds among {300,600,1200} / {150,400,1000} (differences between neighbours were small; W=600 gave the best ECE/Brier trade-off; `tune_*_online.csv`). 12 held-out seeds. Tables: `results/tables/online_*.md`; figure `results/figures/rolling_ece.png`.

## Does online recalibration survive shift? (OBSERVED)
Post-onset ECE, temperature scaling, GBM base:
| scenario | static | expanding | decay | **window** |
|---|---|---|---|---|
| feature_shift | 0.154 | 0.112 | 0.033 | 0.026 |
| regime_transition | 0.178 | 0.139 | 0.061 | 0.055 |
| stale_features | 0.136 | 0.101 | 0.025 | 0.018 |
| venue_change | 0.094 | 0.069 | 0.019 | 0.014 |
| vol_jump | 0.082 | 0.056 | 0.020 | 0.024 |
| missing_features | 0.069 | 0.055 | 0.025 | 0.020 |
| rare_cluster | 0.033 | 0.027 | 0.020 | 0.018 |
| none | 0.025 | 0.025 | 0.022 | 0.020 |
Shift-only means (7 scenarios), GBM: ECE 0.107 → 0.025 (window) / 0.029 (decay) / 0.080 (expanding); CWM 0.127 → 0.025 / 0.028 / 0.085; Brier 0.670 → 0.641. LR: ECE 0.117 → 0.035, CWM 0.185 → 0.053. The same holds for beta and isotonic maps, but temperature is best throughout (GBM shift-only ECE: beta 0.060, isotonic 0.064 vs temperature 0.025). **Expanding-window calibration is only a mild improvement** — old data dilutes the new regime — so "incremental" must mean *forgetting*.

Rolling ECE (500-step windows; figure): onset produces a transient spike (feature shift ≈0.09, vol jump ≈0.06, regime ≈0.07–0.09) that decays within roughly 500–1000 steps for window/decay; static ECE stays at 0.09–0.23 for the rest of the run. The regime transition (gradual rotation) never returns to the in-distribution level (ECE ≈0.055 vs 0.02–0.04) within the run: recalibration can track a *level* change in confidence but the model is simply wrong, so calibrated confidence becomes low and Brier stays high (0.665 vs 0.576 in-distribution).

**Real data (ELEC2, 33k held-out rows, OBSERVED):** GBM/temperature ECE 0.164 (static) → 0.021 (window) / 0.021 (decay); Brier 0.471 → 0.386. LR/temperature ECE 0.189 → 0.043, Brier 0.478 → 0.372. Per-block static GBM ECE climbs to 0.20–0.37 in blocks 4–11 and returns to 0.01–0.04 at the end, whereas the online GBM variants stay ≤ 0.14 throughout (online LR ≤ 0.19; `elec2.png`). Caveat: the validation-selected W=2000 and half-life 1000 sit at the *edge* of the candidate grid — a longer window might do better.

## Stationary cost / instability (OBSERVED)
* In the `none` world online recalibration costs nothing: ECE 0.020 vs 0.025, Brier 0.577 vs 0.576 (GBM temperature); LR ECE 0.018 vs 0.020.
* **Decision turnover** (action series with the validation-chosen abstention τ): static vs window in the stationary world 0.487 vs 0.487 (GBM); over the 7 shifts 0.487 → 0.467 (GBM), 0.357 → 0.341 (LR). Recalibration never changes the argmax (temperature/top-label maps are argmax-preserving), it only moves the accept/abstain boundary. Largest *added* turnover vs static is +0.023 (beta, feature shift); it *reduces* turnover by up to −0.10 when it starts abstaining under regime transition. No evidence of destabilising flip-flopping at R=50, W=600.
* Not measured: calibrator-parameter jitter (e.g. trajectory of the fitted temperature) and sensitivity to R. UNKNOWN.

## Look-ahead (OBSERVED)
With H=1 or with a peek of one block the *low-capacity* calibrators are barely flattered (GBM temperature shift-only ECE 0.0249 honest vs 0.0246 `leak_h0` vs 0.0255 `leak_peek`), but the *flexible* isotonic map is: Brier 0.694 honest vs 0.686 peek (GBM, shift-only), LR 0.634 vs 0.622; ELEC2 LR isotonic Brier 0.355 honest vs 0.339 peek (temperature 0.372 vs 0.368). So the inflation from label leakage grows with calibrator capacity, and ECE alone would understate it — Brier/log loss should be checked. In real trading the leak is worse than modelled here because forward-return labels overlap in time (label horizon H is real and must be enforced by the point-in-time store); the harness asserts it, but only for a fixed H.

## Verdict for §6
ONLINE_CALIBRATION_SUPPORTED on this evidence: sliding-window/decayed temperature scaling with matured labels is stable, cheap, and recovers most calibration after shifts; it cannot create information (regime_transition Brier remains 0.665) and it needs a *label feed with a known maturity delay*, which the private system may or may not provide (UNKNOWN).
