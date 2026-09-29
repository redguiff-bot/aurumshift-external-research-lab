# 08 — Failure modes (all OBSERVED unless tagged)

| # | failure mode | evidence | consequence / mitigation tested |
|---|---|---|---|
| F1 | **Static calibrator + shift ⇒ confident and wrong** | ECE drift +0.04…+0.19; CWM 0.07 → 0.17 (GBM, temperature); ELEC2 static ECE up to 0.37 | online recalibration with matured labels cuts CWM to 0.01–0.03 |
| F2 | **Static recalibration can hurt** (ELEC2 LR: Brier 0.456 raw → 0.478) | `public_elec_overall.md` | never treat a calibration split as evergreen; monitor |
| F3 | **Concept/volatility shift invisible to input detectors** | vol_jump / regime_transition: 5.9 % flag rate = false-alarm level, error 0.49 / 0.64 | only realised-loss monitor (needs labels, delay 150–500 steps) |
| F4 | **Mean imputation hides missingness** | Mahalanobis detection 0 % under 40 % missing; DATA_GAP F1 = 0 without flags | keep explicit missing/staleness flags as first-class inputs |
| F5 | **Stale values look in-distribution** | KS/Mahalanobis slow (300–1500 steps); repeat-value monitor 100 steps | exact-repeat / age monitors |
| F6 | **OOD rows stay confident** | OOD-flagged rows: mean conf 0.73, error 0.48; OOD recall only 0.39 | explicit OOD gate; still misses shifts inside the training support |
| F7 | **Ensemble disagreement is weak** | AURC no better than max-prob; MODEL_UNCERTAINTY F1 0.07; LR bootstrap MI ranking near random | variance from resampling the same learner ≠ epistemic uncertainty; not adopted |
| F8 | **Platt on saturated confidences** | GBM ECE 0.119 vs 0.027 temperature | use temperature (acts on logits) or beta/isotonic |
| F9 | **Top-label calibrators leave the rest of the distribution mis-shaped** | GBM log loss 1.05 (beta/isotonic) vs 0.96 (temperature) | temperature preferred when the full vector matters |
| F10 | **Expanding-window recalibration dilutes the new regime** | shift-only GBM ECE 0.080 vs 0.025 (window) | forget old data |
| F11 | **Look-ahead flatters flexible calibrators** | isotonic Brier −0.008 to −0.016 with a one-block peek; ECE hardly moves | check Brier/log loss, enforce label maturity in the store; test with corrupted-future-labels harness |
| F12 | **Split conformal under drift** | coverage 0.766 (target 0.90), 0.538 for a vol jump; ELEC2 0.59–0.87 | ACI/rolling for marginal coverage only |
| F13 | **ACI trivial intervals** | infinite-interval rate 9.3 % (split scores) | prefer rolling scores or cap intervals; report width |
| F14 | **Conditional coverage broken even when iid** | 0.98 vs 0.82 by volatility state (iid control) | normalised scores narrow the gap only partly; do not quote marginal coverage per regime |
| F15 | **Recency conformal transients** | worst 300-step window 0.73–0.83 after shifts | treat post-shift window as uncovered |
| F16 | **Abstention on a weak signal collapses opportunity count** | conformal singleton 38–42 % in-dist, 24 % shifted | do not use α=0.2 sets as a trade gate on a weak signal |
| F17 | **Abstention can destroy value in a still-profitable regime** | vol_jump: utility 414 → 403 with online confidence | abstention is risk control, not alpha |
| F18 | **Autocorrelation inflates detector false alarms** | KS/Mahalanobis FAR 5–8 % with validation-max thresholds | persistence rule; no iid p-values |
| F19 (INFERENCE) | **Window-length sensitivity** | ELEC2 selected W=2000 / HL=1000 at the grid edge | grid was too narrow for slow drift; use a wider grid / adaptive window |
| F20 (UNKNOWN) | Parameter instability of the online calibrator, R sensitivity, interaction with real forward-return label overlap | not measured | future work |
