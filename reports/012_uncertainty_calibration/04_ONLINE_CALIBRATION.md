# 04 — Online calibration (static vs incremental; instability; lookahead)

**Design.** Base model frozen (trained on rows 0–4000). Calibration block 4000–7000. Stream from 7000 onward (14,000 steps synthetic; ELEC2 from 13,500). The label of step *j* is revealed at *j + h*; a calibrator used at *t* may only use labels with *j + h ≤ t*. h=10 (synthetic), h∈{1, 48} (ELEC2 half-hours). Methods: static Platt / static isotonic; expanding-window Platt; sliding-window Platt (W=1000; 2000 ELEC2, refit every 250); sliding-window isotonic; SGD Platt (lr 0.02); and two **deliberately leaky** variants used only as an audit — `leak_block` fits on the very block it then predicts, `leak_global` on the whole future stream. 8 seeds per synthetic scenario. Scenarios: stationary; abrupt regime transition (two coefficient signs flip at step 12,000); gradual drift (same flip, ramped over 8000 steps); volatility jump (features ×1.5 and signal-to-noise ×0.35 at step 12,000).

**PIT / lookahead audit:** pit_ok (all label indices used satisfy j+h<=t) for every PIT-safe method/run: **True** (216 runs)

## Synthetic scenarios (mean ± 95% CI over 8 seeds; turnover columns are means)

### Stationary
| method | ece | brier | ece_chunk_worst | fcr | turnover | turnover_raw | slope_sd |
|---|---|---|---|---|---|---|---|
| expand_platt | 0.012±0.002 | 0.201±0.001 | 0.047±0.004 | 0.027±0.001 | 0.498 | 0.449 | 0.006 |
| leak_block | 0.012±0.002 | 0.199±0.001 | 0.046±0.003 | 0.026±0.001 | 0.489 | 0.449 | 0.079 |
| leak_global | 0.013±0.001 | 0.201±0.001 | 0.049±0.003 | 0.027±0.001 | 0.498 | 0.449 | 0.0 |
| sgd | 0.012±0.001 | 0.202±0.001 | 0.045±0.004 | 0.031±0.001 | 0.489 | 0.449 | 0.106 |
| static_iso | 0.020±0.003 | 0.202±0.001 | 0.052±0.004 | 0.031±0.005 | 0.494 | 0.449 | nan |
| static_platt | 0.013±0.002 | 0.201±0.001 | 0.049±0.004 | 0.026±0.002 | 0.498 | 0.449 | 0.0 |
| window_iso | 0.020±0.002 | 0.203±0.001 | 0.052±0.002 | 0.035±0.001 | 0.485 | 0.449 | nan |
| window_platt | 0.013±0.002 | 0.201±0.001 | 0.048±0.003 | 0.027±0.001 | 0.496 | 0.449 | 0.039 |
### Abrupt regime transition
| method | ece | brier | ece_chunk_worst | fcr | turnover | turnover_raw | slope_sd |
|---|---|---|---|---|---|---|---|
| expand_platt | 0.067±0.026 | 0.237±0.012 | 0.152±0.062 | 0.028±0.002 | 0.466 | 0.449 | 0.085 |
| leak_block | 0.013±0.002 | 0.221±0.005 | 0.048±0.005 | 0.013±0.003 | 0.391 | 0.449 | 0.203 |
| leak_global | 0.013±0.002 | 0.233±0.010 | 0.119±0.038 | 0.006±0.005 | 0.319 | 0.449 | 0.0 |
| sgd | 0.025±0.006 | 0.227±0.006 | 0.064±0.011 | 0.018±0.004 | 0.395 | 0.449 | 0.223 |
| static_iso | 0.102±0.040 | 0.253±0.023 | 0.187±0.066 | 0.073±0.022 | 0.494 | 0.449 | nan |
| static_platt | 0.100±0.042 | 0.252±0.023 | 0.182±0.067 | 0.065±0.019 | 0.498 | 0.449 | 0.0 |
| window_iso | 0.026±0.003 | 0.229±0.006 | 0.117±0.040 | 0.021±0.003 | 0.343 | 0.449 | nan |
| window_platt | 0.017±0.004 | 0.225±0.005 | 0.104±0.031 | 0.015±0.003 | 0.401 | 0.449 | 0.188 |
### Gradual drift
| method | ece | brier | ece_chunk_worst | fcr | turnover | turnover_raw | slope_sd |
|---|---|---|---|---|---|---|---|
| expand_platt | 0.063±0.024 | 0.239±0.012 | 0.113±0.039 | 0.023±0.004 | 0.446 | 0.449 | 0.079 |
| leak_block | 0.014±0.002 | 0.227±0.006 | 0.047±0.007 | 0.009±0.004 | 0.372 | 0.449 | 0.144 |
| leak_global | 0.013±0.002 | 0.235±0.009 | 0.091±0.022 | 0.005±0.005 | 0.307 | 0.449 | 0.0 |
| sgd | 0.026±0.005 | 0.233±0.007 | 0.066±0.011 | 0.014±0.004 | 0.372 | 0.449 | 0.173 |
| static_iso | 0.111±0.045 | 0.259±0.025 | 0.183±0.063 | 0.077±0.024 | 0.494 | 0.449 | nan |
| static_platt | 0.110±0.046 | 0.257±0.025 | 0.180±0.065 | 0.069±0.020 | 0.498 | 0.449 | 0.0 |
| window_iso | 0.026±0.004 | 0.234±0.007 | 0.063±0.005 | 0.017±0.005 | 0.336 | 0.449 | nan |
| window_platt | 0.016±0.003 | 0.230±0.007 | 0.055±0.006 | 0.011±0.003 | 0.38 | 0.449 | 0.138 |
### Volatility jump
| method | ece | brier | ece_chunk_worst | fcr | turnover | turnover_raw | slope_sd |
|---|---|---|---|---|---|---|---|
| expand_platt | 0.057±0.002 | 0.232±0.001 | 0.138±0.007 | 0.041±0.001 | 0.492 | 0.434 | 0.088 |
| leak_block | 0.014±0.002 | 0.223±0.001 | 0.049±0.004 | 0.010±0.001 | 0.407 | 0.434 | 0.169 |
| leak_global | 0.018±0.003 | 0.230±0.001 | 0.110±0.008 | 0.006±0.000 | 0.449 | 0.434 | 0.0 |
| sgd | 0.024±0.001 | 0.229±0.001 | 0.067±0.005 | 0.018±0.001 | 0.392 | 0.434 | 0.19 |
| static_iso | 0.094±0.004 | 0.244±0.001 | 0.166±0.007 | 0.086±0.010 | 0.489 | 0.434 | nan |
| static_platt | 0.092±0.005 | 0.242±0.001 | 0.164±0.005 | 0.081±0.004 | 0.487 | 0.434 | 0.0 |
| window_iso | 0.025±0.001 | 0.228±0.001 | 0.098±0.010 | 0.021±0.002 | 0.422 | 0.434 | nan |
| window_platt | 0.016±0.001 | 0.226±0.001 | 0.091±0.010 | 0.014±0.001 | 0.425 | 0.434 | 0.158 |

## Real data — ELEC2 (single run; label delay 1 half-hour; h=48 numbers for HGB/LR are in `results/tables/online_ELEC2_*_h48.md`)
### HGB base
| method | ece | brier | ece_chunk_worst | fcr | turnover | turnover_raw | slope_sd |
|---|---|---|---|---|---|---|---|
| expand_platt | 0.016 | 0.149 | 0.090 | 0.064 | 0.241 | 0.208 | 0.075 |
| leak_block | 0.015 | 0.134 | 0.025 | 0.051 | 0.246 | 0.208 | 0.192 |
| leak_global | 0.013 | 0.148 | 0.069 | 0.054 | 0.256 | 0.208 | 0.0 |
| sgd | 0.022 | 0.138 | 0.047 | 0.054 | 0.25 | 0.208 | 0.202 |
| static_iso | 0.069 | 0.163 | 0.196 | 0.083 | 0.182 | 0.208 | nan |
| static_platt | 0.057 | 0.161 | 0.177 | 0.091 | 0.219 | 0.208 | 0.0 |
| window_iso | 0.010 | 0.142 | 0.046 | 0.064 | 0.242 | 0.208 | nan |
| window_platt | 0.017 | 0.141 | 0.044 | 0.055 | 0.26 | 0.208 | 0.13 |
### LR base
| method | ece | brier | ece_chunk_worst | fcr | turnover | turnover_raw | slope_sd |
|---|---|---|---|---|---|---|---|
| expand_platt | 0.025 | 0.158 | 0.142 | 0.055 | 0.156 | 0.141 | 0.262 |
| leak_block | 0.021 | 0.133 | 0.034 | 0.041 | 0.174 | 0.141 | 1.486 |
| leak_global | 0.020 | 0.153 | 0.063 | 0.035 | 0.172 | 0.141 | 0.0 |
| sgd | 0.030 | 0.141 | 0.045 | 0.040 | 0.179 | 0.141 | 0.559 |
| static_iso | 0.139 | 0.196 | 0.279 | 0.190 | 0.107 | 0.141 | nan |
| static_platt | 0.130 | 0.192 | 0.283 | 0.142 | 0.122 | 0.141 | 0.0 |
| window_iso | 0.014 | 0.145 | 0.044 | 0.061 | 0.169 | 0.141 | nan |
| window_platt | 0.024 | 0.146 | 0.057 | 0.043 | 0.181 | 0.141 | 0.782 |

## Pre-declared criterion (worst-chunk ECE gain vs static Platt ≥ 0.02 with the CI lower bound ≥ 0.02; turnover ≤ 1.2× raw turnover)
| scenario | method | worst_chunk_ece_gain_vs_static | ci_lower_ge_0_02 | turnover_ratio_vs_raw |
|---|---|---|---|---|
| abrupt_regime | window_platt | 0.079±0.040 | YES | 0.89 |
| abrupt_regime | window_iso | 0.066±0.033 | YES | 0.76 |
| abrupt_regime | sgd | 0.119±0.064 | YES | 0.88 |
| abrupt_regime | expand_platt | 0.031±0.016 | NO | 1.04 |
| gradual_drift | window_platt | 0.125±0.063 | YES | 0.85 |
| gradual_drift | window_iso | 0.117±0.061 | YES | 0.75 |
| gradual_drift | sgd | 0.114±0.058 | YES | 0.83 |
| gradual_drift | expand_platt | 0.066±0.028 | YES | 0.99 |
| vol_jump | window_platt | 0.073±0.014 | YES | 0.98 |
| vol_jump | window_iso | 0.067±0.013 | YES | 0.97 |
| vol_jump | sgd | 0.097±0.009 | YES | 0.9 |
| vol_jump | expand_platt | 0.026±0.010 | NO | 1.13 |

## Findings
1. **Under stationarity, online adds nothing** (all PIT-safe methods ≈ static, ECE 0.012–0.020). Isotonic variants are again slightly worse (0.020).
2. **Under drift, static calibration fails and PIT-safe online recalibration largely repairs it**: abrupt regime ECE 0.100 (static Platt) → 0.017 (window Platt), 0.025 (SGD); worst-chunk ECE 0.182 → 0.104 (window) / 0.064 (SGD). The recovery is *lagged* (worst chunk is the one containing the transition) — window methods cannot fix the first ≈ h + refit + fill-time steps after a break.
3. **Expanding-window Platt is the weakest online variant** under abrupt change (ECE 0.067, gain vs static not significant under the criterion for abrupt & vol-jump): old regime data dilutes the update. Criterion met by **window Platt, window isotonic, SGD Platt** in all three drift scenarios.
4. **Lookahead inflation is real but here modest for the in-sample block leak and misleading for the global leak:** `leak_block` reaches worst-chunk ECE 0.048 (abrupt) vs 0.104 for PIT-safe window Platt (roughly 2× flatter) and lower decision turnover; `leak_global`, though a lookahead, does *worse* under drift (0.119) because one global map cannot track the change. So a leak does not always make a number look better — it can also hide a method's true behaviour; the audit only bounds it.
5. **Instability.** Decision turnover of online methods is *not* above the raw model's under drift (ratios 0.76–0.98 for window/SGD in the table above; expanding 1.04–1.13), and *is* ≈ static-Platt's under stationarity (0.496 vs 0.498). The parameter path is not free: slope sd 0.04 (window Platt stationary) but 0.106 for SGD lr=0.02 at stationarity, 0.13–0.23 under drift, and on ELEC2-LR the fitted slope sd reaches 0.56–0.78 (unstable, near-collinear logit inputs) — worth capping / smoothing before any use.
6. **Real ELEC2:** static Platt worst-chunk ECE 0.177 (HGB) / 0.283 (LR); window Platt 0.044 / 0.057; expanding 0.090 / 0.142. Online recalibration with a 1-step or 48-step delay gives the same picture (h=48 tables).
7. **FCR** falls with online recalibration under drift (abrupt: 0.065 static → 0.015 window), but never to zero: the first post-break window remains over-confident.

## Verdict for §6
Online recalibration with **PIT-safe delayed labels, sliding window** is supported under drift in these worlds; expanding-window and static are not. The instability/lookahead risk is measurable and controllable (assertion + leak audit) but must be re-audited on any real pipeline.
