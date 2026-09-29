# 08 — Turnover and slot-hour economics: attempts to falsify each idea

## 1. Expected net ÷ expected hold (SLOTHOUR) vs raw EV ranking (SCORE_RANK)
- Heldout macro: SLOTHOUR − SCORE_RANK = +0.070 [+0.031,+0.109]; significant only in S5b and S6 (S6: +0.36 [+0.16,+0.56]); indistinguishable elsewhere; **no scenario where SCORE_RANK is significantly better** (heldout).
- **Falsification attempt succeeded partially** (validation, score-quality ladder D2): with a near-perfect score (τ=0, oracle-score UPPER BOUND ONLY) SCORE_RANK 3.15 > SLOTHOUR 2.98: dividing by an *estimated* per-instrument hold adds noise when hold varies within an instrument more than between instruments (INFERENCE). Slot-hour ranking pays off when duration heterogeneity is *between* instruments and the hold estimate is learnable (S6).
- Also in S6, EV ranking (SCORE_RANK) captured long slots (mean hold 12.0 h vs 7.8 h) and had a lower point estimate than FIFO (3.08 vs 3.19; significance not tested) — long-slot capture is real.

## 2. Slot shadow price / opportunity-cost threshold (SLOTHOUR_SHADOW: admit iff rate ≥ θ·EWMA(rate of admitted))
- Frozen θ=0.25 (lowest grid value; θ=0 is SLOTHOUR). Validation-split sensitivity (13 scenarios): θ=0.25 → 2.34, 0.5 → 2.05, 0.75 → 1.07, 1.0 → 0.40, 1.25 → 0.19: **collapse** as the threshold idles slots.
- Heldout vs SLOTHOUR: +0.009 [−0.026,+0.044] macro (tie); significantly **better only in S4** (late high-quality arrival: +0.26, idle slot-hours 901 vs 577) and significantly **worse in S1/S2** (low load: refusing admissible trades costs). Interpretation (INFERENCE): a shadow price is worth something only when saturation is bursty and quality is time-clustered; otherwise it is a costly way to hold slots empty. Falsified as a general method; retained as a *situational* candidate.
- Best-in-rule note: the pre-registered BEST_SLOT_HOUR argmax is SLOTHOUR_SHADOW@0.25 by +0.009 — a statistical tie; SLOTHOUR is the practical reference.

## 3. Minimum holding constraint / turnover neutrality (OLDEST_SLOT, min_hold ∈ {2,4,8})
Validation macro M1: min_hold 2 → 2.09, 4 → 2.27, 8 → 2.19: too-short holds waste cost; too long stops recycling. Heldout: +0.185 vs FIFO but only +0.021 [−0.022,+0.066] vs FIFO_SCREEN macro; significantly better than FIFO_SCREEN in S4 and S6, significantly worse in S5/S5b. **Cost sensitivity destroys it**: at 3× costs OLDEST_SLOT earns -1.16 on S3 (all other policies positive). A preemption rule needs a defensible partial-accrual model (A3) — UNKNOWN locally.

## 4. Hazard-adjusted value and turnover penalty
Not executed as separate methods: hazard adjustment would require a duration/exit-hazard model (no such information exists in the abstraction beyond per-instrument mean hold); a turnover penalty is algebraically a cost increase and is covered by (a) the net-value screen with true cost and (b) the cost-belief sensitivity below. Status: UNKNOWN — not falsified, not supported.

## 5. Cost uncertainty (D3, validation split, frozen params; UNKNOWN_COST ≠ ZERO_COST)
S3_chronic, M1 by true-cost multiplier and *policy cost belief*:
| bel | cm | FIFO | FIFO_SCREEN | SCORE_RANK | SLOTHOUR | UNCERT_LCB | OLDEST_SLOT |
|---|---|---|---|---|---|---|---|
| known | 0.500 | 2.312 | 2.679 | 3.379 | 3.541 | 3.539 | 2.992 |
| known | 1.000 | 1.894 | 2.364 | 3.002 | 3.141 | 3.153 | 2.161 |
| known | 2.000 | 1.059 | 1.804 | 2.154 | 2.210 | 2.332 | 0.499 |
| known | 3.000 | 0.224 | 1.222 | 1.439 | 1.534 | 1.599 | -1.163 |
| unknown_conservative | 0.500 | 2.312 | 2.807 | 3.299 | 3.552 | 3.512 | 2.992 |
| unknown_conservative | 1.000 | 1.894 | 2.394 | 2.860 | 3.102 | 3.064 | 2.161 |
| unknown_conservative | 2.000 | 1.059 | 1.568 | 1.980 | 2.201 | 2.168 | 0.499 |
| unknown_conservative | 3.000 | 0.224 | 0.743 | 1.101 | 1.300 | 1.272 | -1.163 |
| zero | 0.500 | 2.312 | 2.624 | 3.406 | 3.559 | 3.564 | 2.992 |
| zero | 1.000 | 1.894 | 2.210 | 2.962 | 3.095 | 3.088 | 2.161 |
| zero | 2.000 | 1.059 | 1.381 | 2.074 | 2.168 | 2.136 | 0.499 |
| zero | 3.000 | 0.224 | 0.552 | 1.186 | 1.240 | 1.183 | -1.163 |
S6 (short-vs-long):
| bel | cm | FIFO | FIFO_SCREEN | SCORE_RANK | SLOTHOUR | UNCERT_LCB | OLDEST_SLOT |
|---|---|---|---|---|---|---|---|
| known | 0.500 | 3.354 | 3.377 | 3.155 | 3.550 | 3.697 | 4.500 |
| known | 1.000 | 3.040 | 3.142 | 2.863 | 3.349 | 3.482 | 3.840 |
| known | 2.000 | 2.412 | 2.505 | 2.615 | 2.596 | 2.647 | 2.522 |
| known | 3.000 | 1.785 | 2.010 | 2.277 | 2.038 | 2.102 | 1.203 |
| unknown_conservative | 0.500 | 3.354 | 3.309 | 3.259 | 3.456 | 3.479 | 4.500 |
| unknown_conservative | 1.000 | 3.040 | 3.041 | 3.045 | 3.170 | 3.202 | 3.840 |
| unknown_conservative | 2.000 | 2.412 | 2.505 | 2.615 | 2.596 | 2.647 | 2.522 |
| unknown_conservative | 3.000 | 1.785 | 1.969 | 2.186 | 2.022 | 2.092 | 1.203 |
| zero | 0.500 | 3.354 | 3.214 | 3.212 | 3.688 | 3.473 | 4.500 |
| zero | 1.000 | 3.040 | 2.925 | 2.986 | 3.341 | 3.121 | 3.840 |
| zero | 2.000 | 2.412 | 2.348 | 2.535 | 2.646 | 2.416 | 2.522 |
| zero | 3.000 | 1.785 | 1.770 | 2.083 | 1.952 | 1.711 | 1.203 |
Findings: ranking methods degrade gracefully when costs double or triple (they stay positive; FIFO falls to 0.22). **Assuming zero cost when the true cost is 3× lowers FIFO_SCREEN from 1.22 to 0.55** (screening collapses) whereas rank-only methods lose less (SLOTHOUR 1.53 → 1.24) because *ranking* is far less cost-sensitive than *thresholding*. A conservative unknown-cost prior lands between the two. Rank-based conclusions therefore survive cost misspecification better than screen-based ones.

## 6. Score-quality ladder (D2, S3 chronic, validation split; oracle score = UPPER BOUND ONLY)
| lvl | FIFO | FIFO_SCREEN | SCORE_RANK | SLOTHOUR | SLOTHOUR_SHDW | UNCERT_LCB | CORR_AWARE | LINTS | OLDEST_SLOT |
|---|---|---|---|---|---|---|---|---|---|
| calibrated_noisy | 1.894 | 2.364 | 3.002 | 3.141 | 3.072 | 3.153 | 3.191 | 3.086 | 2.161 |
| inverted | 1.894 | 2.008 | 2.240 | 2.551 | 2.409 | 2.554 | 2.501 | 2.504 | 2.161 |
| missing50 | 1.894 | 2.081 | 2.747 | 3.134 | 2.984 | 3.131 | 2.953 | 2.906 | 2.161 |
| noisy_x2 | 1.894 | 2.290 | 2.691 | 2.639 | 2.604 | 2.886 | 2.724 | 2.747 | 2.161 |
| perfect_UB_only | 1.894 | 2.397 | 3.150 | 2.980 | 3.385 | 3.140 | 3.249 | 3.208 | 2.161 |
| poor_calibration | 1.894 | 2.135 | 2.486 | 2.558 | 2.252 | 2.634 | 2.395 | 2.418 | 2.161 |
| stale60 | 1.894 | 2.353 | 3.006 | 3.135 | 3.220 | 3.071 | 3.114 | 3.078 | 2.161 |
