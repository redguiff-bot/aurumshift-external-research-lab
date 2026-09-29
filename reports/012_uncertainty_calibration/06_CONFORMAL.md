# 06 — Conformal prediction: what is actually valid?

## Theory status (DOCUMENTED_CLAIM — recalled, not re-verified this session)
* **Split conformal** guarantees marginal coverage ≥ 1−α **only under exchangeability** of calibration and test points. Time-series autocorrelation, drift and delayed labels violate it.
* **Non-exchangeable / weighted CP** (Barber et al. 2023): coverage gap bounded in terms of weights and a distribution-distance term; fixed recency weights come with **no distribution-free coverage guarantee** unless the drift is small in that sense. Our λ=0.998 weights are ad hoc.
* **ACI** (Gibbs & Candès 2021): with immediate label feedback, the *long-run average* miscoverage converges to α at rate O(1/(γT)) **without distributional assumptions** — a statement about the time-average of the error sequence, **not** conditional coverage, not per-regime coverage, not coverage of the acted (singleton) subset.
* **Delayed labels** (our case): the textbook ACI theorem assumes error at *t* is observed before predicting *t+1*. With delay h the update uses stale errors; I did **not** prove a guarantee for this variant (UNKNOWN; empirical only).
* Rolling-window CP has no distribution-free guarantee under drift.

## Experimental design
LAC score (1 − calibrated P(true class)) on Platt-calibrated HGB probabilities (Platt fit on rows 4000–5500, conformal calibration scores from rows 5500–7000, so calibrator and scores use disjoint rows). Sets: {up}, {down}, {both} (=abstain), ∅. Score of step *j* usable from *j+h*. Methods: `split` (frozen), `rolling` (W=1000), `weighted` (λ=0.998), `aci` (γ=0.005, h=10 delayed feedback), `aci_h0` (textbook, unrealistic). Scenarios: **iid_control** (φ=0 — exchangeable), AR(1) stationary, abrupt regime transition, gradual drift, volatility jump; and **ELEC2** (real; h=1 half-hour). 8 seeds; coverage judged marginally **and** in 500-step rolling windows (`min_roll_cov`, `frac_win_below` = share of windows below 1−α−0.05). `singleton_acc` = accuracy on rows where the set is a single label (i.e. where a decision would be taken).

## Classification, α=0.2 (target coverage 0.80)
| kind | method | coverage | min_roll_cov | frac_win_below | singleton | both_abstain | singleton_acc |
|---|---|---|---|---|---|---|---|
| iid_control | aci | 0.800±0.000 | 0.765 | 0.0 | 0.746 | 0.254 | 0.732 |
| iid_control | aci_h0 | 0.800±0.000 | 0.768 | 0.0 | 0.746 | 0.254 | 0.732 |
| iid_control | rolling | 0.800±0.001 | 0.752 | 0.002 | 0.747 | 0.253 | 0.732 |
| iid_control | split | 0.796±0.011 | 0.746 | 0.021 | 0.757 | 0.243 | 0.731 |
| iid_control | weighted | 0.802±0.000 | 0.76 | 0.0 | 0.744 | 0.256 | 0.733 |
| ar_stationary | aci | 0.800±0.000 | 0.764 | 0.0 | 0.742 | 0.258 | 0.73 |
| ar_stationary | aci_h0 | 0.800±0.000 | 0.766 | 0.0 | 0.742 | 0.258 | 0.731 |
| ar_stationary | rolling | 0.800±0.001 | 0.752 | 0.0 | 0.743 | 0.257 | 0.73 |
| ar_stationary | split | 0.801±0.005 | 0.754 | 0.002 | 0.74 | 0.26 | 0.731 |
| ar_stationary | weighted | 0.801±0.001 | 0.76 | 0.0 | 0.741 | 0.259 | 0.731 |
| gradual_drift | aci | 0.800±0.000 | 0.764 | 0.0 | 0.582 | 0.418 | 0.653 |
| gradual_drift | aci_h0 | 0.800±0.000 | 0.765 | 0.0 | 0.582 | 0.418 | 0.654 |
| gradual_drift | rolling | 0.797±0.001 | 0.746 | 0.006 | 0.589 | 0.411 | 0.652 |
| gradual_drift | split | 0.726±0.014 | 0.645 | 0.69 | 0.74 | 0.26 | 0.629 |
| gradual_drift | weighted | 0.798±0.001 | 0.754 | 0.0 | 0.587 | 0.413 | 0.653 |
| abrupt_regime | aci | 0.800±0.000 | 0.756 | 0.0 | 0.597 | 0.403 | 0.663 |
| abrupt_regime | aci_h0 | 0.800±0.000 | 0.756 | 0.001 | 0.598 | 0.402 | 0.663 |
| abrupt_regime | rolling | 0.796±0.001 | 0.711 | 0.033 | 0.606 | 0.394 | 0.662 |
| abrupt_regime | split | 0.733±0.013 | 0.638 | 0.6 | 0.74 | 0.26 | 0.638 |
| abrupt_regime | weighted | 0.798±0.001 | 0.728 | 0.022 | 0.602 | 0.398 | 0.663 |
| vol_jump | aci | 0.800±0.000 | 0.755 | 0.001 | 0.614 | 0.386 | 0.674 |
| vol_jump | aci_h0 | 0.800±0.000 | 0.751 | 0.003 | 0.614 | 0.386 | 0.674 |
| vol_jump | rolling | 0.795±0.001 | 0.703 | 0.05 | 0.625 | 0.375 | 0.672 |
| vol_jump | split | 0.723±0.005 | 0.63 | 0.653 | 0.779 | 0.221 | 0.645 |
| vol_jump | weighted | 0.797±0.000 | 0.718 | 0.035 | 0.622 | 0.378 | 0.673 |
| ELEC2 | aci | 0.800 | 0.755 | 0.0 | 0.886 | 0.082 | 0.811 |
| ELEC2 | aci_h0 | 0.800 | 0.756 | 0.0 | 0.887 | 0.08 | 0.811 |
| ELEC2 | rolling | 0.796 | 0.692 | 0.106 | 0.908 | 0.068 | 0.802 |
| ELEC2 | split | 0.764 | 0.589 | 0.386 | 0.975 | 0.0 | 0.783 |
| ELEC2 | weighted | 0.800 | 0.732 | 0.011 | 0.902 | 0.074 | 0.805 |

## Classification, α=0.1 (target coverage 0.90)
| kind | method | coverage | min_roll_cov | frac_win_below | singleton | both_abstain | singleton_acc |
|---|---|---|---|---|---|---|---|
| ar_stationary | aci | 0.900±0.000 | 0.872 | 0.0 | 0.484 | 0.516 | 0.793 |
| ar_stationary | aci_h0 | 0.900±0.000 | 0.875 | 0.0 | 0.485 | 0.515 | 0.794 |
| ar_stationary | rolling | 0.900±0.001 | 0.861 | 0.0 | 0.486 | 0.514 | 0.794 |
| ar_stationary | split | 0.900±0.005 | 0.859 | 0.0 | 0.486 | 0.514 | 0.795 |
| ar_stationary | weighted | 0.901±0.000 | 0.869 | 0.0 | 0.482 | 0.518 | 0.795 |
| abrupt_regime | aci | 0.900±0.000 | 0.871 | 0.0 | 0.358 | 0.642 | 0.717 |
| abrupt_regime | aci_h0 | 0.900±0.000 | 0.871 | 0.0 | 0.358 | 0.642 | 0.717 |
| abrupt_regime | rolling | 0.897±0.001 | 0.836 | 0.018 | 0.365 | 0.635 | 0.716 |
| abrupt_regime | split | 0.845±0.011 | 0.764 | 0.554 | 0.486 | 0.514 | 0.679 |
| abrupt_regime | weighted | 0.899±0.001 | 0.846 | 0.009 | 0.361 | 0.639 | 0.716 |
| ELEC2 | aci | 0.900 | 0.876 | 0.0 | 0.71 | 0.29 | 0.859 |
| ELEC2 | aci_h0 | 0.900 | 0.875 | 0.0 | 0.713 | 0.287 | 0.86 |
| ELEC2 | rolling | 0.898 | 0.823 | 0.024 | 0.714 | 0.286 | 0.857 |
| ELEC2 | split | 0.849 | 0.671 | 0.445 | 0.832 | 0.168 | 0.818 |
| ELEC2 | weighted | 0.902 | 0.865 | 0.0 | 0.709 | 0.291 | 0.861 |

## Pre-declared criterion (|coverage − (1−α)| ≤ 0.03 and ≤ 10% of windows below 1−α−0.05)
| kind | alpha | aci | aci_h0 | rolling | split | weighted |
|---|---|---|---|---|---|---|
| ELEC2 | 0.1 | YES | YES | YES | NO | YES |
| ELEC2 | 0.2 | YES | YES | NO | NO | YES |
| abrupt_regime | 0.1 | YES | YES | YES | NO | YES |
| abrupt_regime | 0.2 | YES | YES | YES | NO | YES |
| ar_stationary | 0.1 | YES | YES | YES | YES | YES |
| ar_stationary | 0.2 | YES | YES | YES | YES | YES |
| gradual_drift | 0.2 | YES | YES | YES | NO | YES |
| iid_control | 0.2 | YES | YES | YES | YES | YES |
| vol_jump | 0.2 | YES | YES | YES | NO | YES |

## Regression intervals (α=0.2; synthetic, 3× / ramped volatility)
| kind | method | coverage | min_roll_cov | frac_win_below | width |
|---|---|---|---|---|---|
| reg_stationary | aci | 0.800±0.000 | 0.766 | 0.0 | 1.387 |
| reg_stationary | rolling | 0.800±0.001 | 0.756 | 0.0 | 1.385 |
| reg_stationary | split | 0.798±0.011 | 0.751 | 0.022 | 1.379 |
| reg_vol_jump | aci | 0.800±0.000 | 0.732 | 0.013 | 3.01 |
| reg_vol_jump | rolling | 0.793±0.001 | 0.581 | 0.049 | 2.95 |
| reg_vol_jump | split | 0.512±0.009 | 0.301 | 0.669 | 1.379 |
| reg_vol_ramp | aci | 0.800±0.000 | 0.765 | 0.0 | 3.171 |
| reg_vol_ramp | rolling | 0.792±0.001 | 0.743 | 0.006 | 3.12 |
| reg_vol_ramp | split | 0.452±0.010 | 0.307 | 0.973 | 1.379 |

## Public data: California housing, split-CP intervals (α=0.2), 10 repetitions
| mode | coverage | target | width |
|---|---|---|---|
| covariate_shift(train/cal MedInc<=P60, test MedInc>P60) | 0.498±0.006 | 0.8 | 0.817 |
| random_split(exchangeable) | 0.799±0.004 | 0.8 | 0.95 |

## Findings (OBSERVED)
1. **Control:** on the exchangeable stream all five methods land at 0.796–0.802 coverage — the implementation is sound where theory applies.
2. **Split conformal is invalid under drift, and the failure is large:** abrupt/gradual/vol-jump coverage 0.723–0.733 (target 0.80), 60–69% of windows below target−0.05 (α=0.2); regression vol-jump coverage **0.512** and 0.452 under a volatility ramp; California-housing covariate shift **0.498 vs 0.80**. Textbook coverage must **not** be claimed for split CP on non-stationary data — this is what the experiments show.
3. **Rolling, weighted and ACI restore marginal coverage** (0.795–0.800) under drift. Worst-window coverage stays below target: 0.70–0.76 for rolling/ACI (0.71 rolling, 0.756 ACI abrupt), ELEC2 α=0.2 rolling 0.69 (10.6% of windows below → fails the criterion by a hair), ACI 0.755, weighted 0.732. ACI is the most stable; its time-average is ≈ exactly 0.800 in every scenario, consistent with the ACI theorem, but **local under-coverage after a break remains** (the guarantee is asymptotic average).
4. **Delay barely matters here:** `aci` (h=10) vs `aci_h0` differ by ≤0.001 coverage. Not a proof (γ small, h small vs T).
5. **Marginal coverage ≠ decision reliability.** At α=0.2 the singleton (act) rows have accuracy **0.65–0.73** on synthetic streams (abrupt 0.663; iid-control 0.732; ELEC2 0.78–0.81) — well below the 0.80 "coverage" target; the guarantee covers all rows including the both-label sets that are counted as trivially correct. Do not read "80% coverage" as "80% of BUY/SELL calls are right".
6. **Abstention cost:** at α=0.1, 51–64% of rows return {both} (abstain) in the synthetic worlds; at α=0.2 26–42%. The choice of α *is* the abstention rate. Set-based abstention (both ⇒ HOLD) yields singleton accuracy only slightly above the confidence-threshold policy in 05 at similar coverage (untested formally).
7. **Regression:** `rolling` recovers marginal coverage after a vol jump (0.793) but with min-window 0.58; ACI 0.800 with min-window 0.732; intervals widen 1.38 → ≈3.0 as they should.

## What is supported
| Setting | Supported conformal method | Basis |
|---|---|---|
| exchangeable | split CP | theory + control run |
| stationary time series (AR φ=0.7, this generator) | split CP empirically OK (coverage 0.801) — **theory does not cover it; empirical only** | OBSERVED |
| abrupt / gradual drift, vol jump, ELEC2 | ACI (delayed) and weighted CP hold marginal coverage; rolling holds on synthetic, borderline on ELEC2 α=0.2 | OBSERVED; ACI additionally has the DOCUMENTED_CLAIM long-run guarantee (h=0) |
| covariate shift (housing), split CP | **not valid** (0.498) | OBSERVED |
| decision-level (singleton) reliability | **no method supported**; needs singleton-conditional monitoring | OBSERVED |
