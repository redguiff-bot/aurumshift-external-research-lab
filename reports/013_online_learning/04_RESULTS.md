# 04 — Results (held-out seeds 1–15, configs frozen on tuning seeds 100–102)

All numbers OBSERVED from `bench/online_learning_v1/results/main.json` via `py/analyze.py` (tables regenerated verbatim below). Synthetic streams only (see 10).
"Regret" = excess KL (track C) / excess MSE (track R) against the known generating process; lower is better. `rolling` = best simple reference (chosen on tuning seeds).

## 4.1 Headline

* **Frozen** and **expanding batch retrain** are 5.4× / 3.1× (C) and 7.9× / 5.2× (R) worse than a bounded rolling refit in geometric-mean regret over the 8 drift scenarios. Ignoring drift, or retraining rarely on all history, is clearly not sufficient.
* **A bounded rolling refit is a strong baseline**: 8 of 12 (C) and 9 of 11 (R) other methods are *worse* than it on the drift aggregate, including every tree/forest/bagging method (2.6–5.2× worse).
* Two incremental methods clear the pre-registered bar (a)+(b)+(c)+(d): **`bank_sgd_log` on track C** (ratio 0.88, CI [0.87,0.90]) and **`rls` on track R** (ratio 0.85, CI [0.84,0.85]). Different methods on different tracks: no method passes on both (`bank_rls` on R: ratio 1.23; `rls` alone is not a classifier).
* Near-misses that fail (b) (no blow-up): `blr` R (ratio 0.78 but 1.58× rolling on `false_drift`), `sgd_log` C (0.90 but 2.39× rolling on `false_drift`), `reset_sgd_log` C (0.93; fails (a) only because gain < 10 %).
* Gains are modest (12–15 %) against a tuned rolling refit and mostly come from *bounded forgetting*, not from drift detection: the drift-triggered resets (`reset_*`) are no better than the plain recursive learner they wrap.
* Tuning vs held-out ranking agreement: Spearman 0.97 (C), 0.72 (R) — both ≥ 0.5, so the study is not flagged inconclusive by the pre-registered rule.

## 4.2 Pre-registered criteria per method (from `results/summary.json`)

| track | method | (a) gain ratio [CI] | (b) worst scenario ratio | (c) max state growth | (d) replay | earns place |
|---|---|---|---|---|---|---|
| C | adwin_bag | 2.61 [2.53,2.70] ✗ | 7.13 (gradual) ✗ | 3.89 ✗ | ✓ | no |
| C | arf | 3.32 [3.26,3.38] ✗ | 10.78 (false_drift) ✗ | 5.10 ✗ | ✓ | no |
| C | bank_sgd_log | 0.88 [0.87,0.90] ✓ | 1.14 (gradual) ✓ | 1.03 ✓ | ✓ | **YES** |
| C | batch | 3.07 [3.02,3.11] ✗ | 9.87 (gradual) ✗ | 4.33 ✗ | ✓ | no |
| C | frozen | 5.40 [5.26,5.54] ✗ | 23.95 (gradual) ✗ | 1.00 ✓ | ✓ | no |
| C | hat | 2.99 [2.90,3.08] ✗ | 8.91 (false_drift) ✗ | 4.72 ✗ | ✓ | no |
| C | ht | 3.04 [2.97,3.12] ✗ | 8.31 (false_drift) ✗ | 3.96 ✗ | ✓ | no |
| C | pa_platt | 1.20 [1.18,1.21] ✗ | 1.53 (gradual) ✗ | 1.00 ✓ | ✓ | no |
| C | pa_raw | 1.21 [1.19,1.23] ✗ | 3.42 (stationary) ✗ | 1.00 ✓ | ✓ | no |
| C | reset_sgd_log | 0.93 [0.92,0.94] ✗ | 1.20 (false_drift) ✓ | 1.04 ✓ | ✓ | no |
| C | sgd_log | 0.90 [0.89,0.91] ✗ | 2.39 (false_drift) ✗ | 1.00 ✓ | ✓ | no |
| C | sgd_log_platt | 0.96 [0.96,0.97] ✗ | 1.16 (gradual) ✓ | 1.00 ✓ | ✓ | no |
| R | arf | 5.16 [5.07,5.26] ✗ | 22.49 (false_drift) ✗ | 4.70 ✗ | ✓ | no |
| R | bank_rls | 1.23 [1.21,1.25] ✗ | 2.81 (gradual) ✗ | 1.11 ✓ | ✓ | no |
| R | batch | 5.15 [5.07,5.25] ✗ | 28.90 (gradual) ✗ | 4.33 ✗ | ✓ | no |
| R | blr | 0.78 [0.77,0.78] ✓ | 1.58 (false_drift) ✗ | 1.00 ✓ | ✓ | no |
| R | frozen | 7.93 [7.74,8.16] ✗ | 58.45 (gradual) ✗ | 1.00 ✓ | ✓ | no |
| R | hat | 1.73 [1.67,1.82] ✗ | 28.79 (false_drift) ✗ | 5.87 ✗ | ✓ | no |
| R | kalman | 1.05 [1.04,1.06] ✗ | 1.37 (abrupt_missing) ✗ | 1.00 ✓ | ✓ | no |
| R | par_reg | 1.18 [1.17,1.19] ✗ | 3.62 (false_drift) ✗ | 1.00 ✓ | ✓ | no |
| R | reset_rls | 1.25 [1.22,1.28] ✗ | 2.32 (gradual) ✗ | 1.03 ✓ | ✓ | no |
| R | rls | 0.85 [0.84,0.85] ✓ | 0.98 (abrupt_nonlinear) ✓ | 1.00 ✓ | ✓ | **YES** |
| R | sgd_lin | 1.07 [1.06,1.08] ✗ | 2.67 (false_drift) ✗ | 1.00 ✓ | ✓ | no |

(`rolling` is the reference itself, ratio 1.00 by construction.)

## 4.3 Full tables

### Track C — mean excess KL (nats/step) vs generating probability, held-out seeds n=15, mean ± sd

| model | abrupt | gradual | recurring | shock | random_walk | abrupt_missing | abrupt_delayed | abrupt_nonlinear | stationary | false_drift | drift-geomean ratio vs rolling |
|---|---|---|---|---|---|---|---|---|---|---|---|
| adwin_bag | 0.172±0.026 | 0.160±0.035 | 0.190±0.009 | 0.073±0.011 | 0.146±0.032 | 0.273±0.045 | 0.187±0.027 | 0.339±0.008 | 0.058±0.007 | 0.098±0.013 | 2.61 [2.53,2.70] |
| arf | 0.196±0.016 | 0.208±0.014 | 0.253±0.011 | 0.161±0.020 | 0.214±0.011 | 0.251±0.015 | 0.217±0.016 | 0.309±0.018 | 0.154±0.016 | 0.168±0.016 | 3.32 [3.26,3.38] |
| bank_sgd_log | 0.038±0.004 | 0.026±0.002 | 0.052±0.010 | 0.031±0.003 | 0.048±0.004 | 0.098±0.014 | 0.066±0.004 | 0.319±0.005 | 0.009±0.001 | 0.012±0.002 | 0.88 [0.87,0.90] |
| batch | 0.256±0.007 | 0.222±0.009 | 0.270±0.008 | 0.032±0.003 | 0.170±0.034 | 0.401±0.018 | 0.280±0.009 | 0.341±0.005 | 0.003±0.001 | 0.004±0.001 | 3.07 [3.02,3.11] |
| frozen | 0.556±0.058 | 0.538±0.054 | 0.557±0.049 | 0.036±0.004 | 0.388±0.125 | 0.620±0.050 | 0.569±0.046 | 0.383±0.018 | 0.009±0.002 | 0.013±0.006 | 5.40 [5.26,5.54] |
| hat | 0.163±0.019 | 0.162±0.043 | 0.244±0.014 | 0.105±0.020 | 0.173±0.026 | 0.315±0.050 | 0.202±0.028 | 0.369±0.016 | 0.076±0.018 | 0.138±0.032 | 2.99 [2.90,3.08] |
| ht | 0.205±0.031 | 0.181±0.038 | 0.230±0.022 | 0.090±0.008 | 0.165±0.035 | 0.303±0.026 | 0.228±0.026 | 0.365±0.015 | 0.072±0.006 | 0.129±0.025 | 3.04 [2.97,3.12] |
| pa_platt | 0.054±0.005 | 0.034±0.003 | 0.124±0.006 | 0.032±0.003 | 0.057±0.006 | 0.148±0.015 | 0.087±0.006 | 0.316±0.005 | 0.010±0.001 | 0.012±0.002 | 1.20 [1.18,1.21] |
| pa_raw | 0.059±0.004 | 0.051±0.003 | 0.073±0.004 | 0.062±0.003 | 0.061±0.003 | 0.073±0.009 | 0.081±0.004 | 0.385±0.007 | 0.049±0.005 | 0.053±0.003 | 1.21 [1.19,1.23] |
| reset_sgd_log | 0.036±0.003 | 0.026±0.002 | 0.078±0.004 | 0.039±0.004 | 0.048±0.004 | 0.087±0.014 | 0.062±0.004 | 0.319±0.005 | 0.010±0.002 | 0.019±0.005 | 0.93 [0.92,0.94] |
| rolling **(ref)** | 0.042±0.003 | 0.022±0.002 | 0.097±0.007 | 0.039±0.002 | 0.053±0.006 | 0.097±0.013 | 0.070±0.004 | 0.321±0.006 | 0.014±0.002 | 0.016±0.002 | 1.00 [1.00,1.00] |
| sgd_log | 0.038±0.003 | 0.027±0.002 | 0.063±0.004 | 0.041±0.003 | 0.041±0.003 | 0.068±0.014 | 0.069±0.005 | 0.355±0.006 | 0.024±0.002 | 0.037±0.003 | 0.90 [0.89,0.91] |
| sgd_log_platt | 0.039±0.003 | 0.026±0.002 | 0.092±0.004 | 0.028±0.002 | 0.049±0.004 | 0.103±0.014 | 0.070±0.005 | 0.318±0.005 | 0.010±0.001 | 0.012±0.002 | 0.96 [0.96,0.97] |


### Track R — mean excess MSE vs true conditional mean, held-out seeds n=15, mean ± sd

| model | abrupt | gradual | recurring | shock | random_walk | abrupt_missing | abrupt_delayed | abrupt_nonlinear | stationary | false_drift | drift-geomean ratio vs rolling |
|---|---|---|---|---|---|---|---|---|---|---|---|
| arf | 0.460±0.017 | 0.383±0.031 | 0.599±0.028 | 0.231±0.018 | 0.394±0.058 | 0.699±0.037 | 0.516±0.016 | 2.170±0.157 | 0.175±0.010 | 0.688±0.055 | 5.16 [5.07,5.26] |
| bank_rls | 0.058±0.006 | 0.052±0.005 | 0.090±0.007 | 0.041±0.004 | 0.147±0.020 | 0.182±0.029 | 0.114±0.009 | 2.356±0.094 | 0.001±0.000 | 0.014±0.005 | 1.23 [1.21,1.25] |
| batch | 0.622±0.024 | 0.532±0.016 | 0.658±0.017 | 0.059±0.007 | 0.391±0.103 | 0.921±0.034 | 0.672±0.019 | 2.446±0.098 | 0.001±0.001 | 0.003±0.001 | 5.15 [5.07,5.25] |
| blr | 0.038±0.002 | 0.022±0.002 | 0.069±0.005 | 0.049±0.003 | 0.040±0.003 | 0.075±0.014 | 0.095±0.010 | 2.544±0.102 | 0.021±0.001 | 0.048±0.006 | 0.78 [0.77,0.78] |
| frozen | 1.133±0.054 | 1.077±0.034 | 1.140±0.031 | 0.061±0.007 | 0.802±0.255 | 1.155±0.050 | 1.186±0.044 | 2.624±0.091 | 0.004±0.002 | 0.010±0.004 | 7.93 [7.74,8.16] |
| hat | 0.089±0.035 | 0.100±0.032 | 0.185±0.057 | 0.092±0.010 | 0.210±0.026 | 0.156±0.036 | 0.145±0.021 | 1.991±0.382 | 0.048±0.003 | 0.880±0.132 | 1.73 [1.67,1.82] |
| kalman | 0.055±0.004 | 0.021±0.002 | 0.147±0.005 | 0.050±0.004 | 0.061±0.008 | 0.163±0.021 | 0.111±0.008 | 2.368±0.093 | 0.007±0.001 | 0.028±0.005 | 1.05 [1.04,1.06] |
| par_reg | 0.070±0.007 | 0.030±0.003 | 0.153±0.011 | 0.067±0.005 | 0.054±0.005 | 0.170±0.026 | 0.126±0.011 | 2.340±0.089 | 0.027±0.001 | 0.111±0.008 | 1.18 [1.17,1.19] |
| reset_rls | 0.052±0.007 | 0.043±0.011 | 0.148±0.009 | 0.052±0.010 | 0.129±0.016 | 0.170±0.029 | 0.109±0.009 | 2.350±0.093 | 0.002±0.001 | 0.017±0.006 | 1.25 [1.22,1.28] |
| rls | 0.042±0.003 | 0.016±0.001 | 0.101±0.006 | 0.048±0.004 | 0.046±0.005 | 0.112±0.017 | 0.098±0.009 | 2.416±0.095 | 0.011±0.001 | 0.027±0.006 | 0.85 [0.84,0.85] |
| rolling **(ref)** | 0.051±0.006 | 0.018±0.002 | 0.123±0.007 | 0.072±0.006 | 0.058±0.006 | 0.119±0.019 | 0.106±0.009 | 2.473±0.106 | 0.015±0.001 | 0.031±0.006 | 1.00 [1.00,1.00] |
| sgd_lin | 0.056±0.003 | 0.021±0.002 | 0.151±0.003 | 0.050±0.004 | 0.063±0.008 | 0.166±0.023 | 0.113±0.006 | 2.369±0.094 | 0.006±0.001 | 0.082±0.008 | 1.07 [1.06,1.08] |


### Adaptation speed — steps to rolling-50 regret <= 1.5x own pre-change level + 0.01 (censored at 600), pooled over seeds; and 600-step post-change regret


**Track C**

| model | abrupt median steps [%censored] | abrupt post-600 regret | gradual median [%cens] | recurring return(t=2000) median [%cens] | shock post-return regret (t=2100) |
|---|---|---|---|---|---|
| adwin_bag | 600 [93%] | 0.440 | 0 [0%] | 0 [0%] | 0.053 |
| arf | 288 [7%] | 0.323 | 0 [0%] | 45 [0%] | 0.155 |
| bank_sgd_log | 600 [60%] | 0.162 | 0 [0%] | 39 [7%] | 0.029 |
| batch | 600 [100%] | 0.750 | 0 [0%] | 0 [0%] | 0.004 |
| frozen | 600 [100%] | 0.953 | 0 [0%] | 0 [0%] | 0.009 |
| hat | 600 [73%] | 0.460 | 0 [0%] | 0 [7%] | 0.124 |
| ht | 600 [93%] | 0.459 | 0 [0%] | 0 [0%] | 0.055 |
| pa_platt | 600 [100%] | 0.252 | 0 [0%] | 550 [33%] | 0.031 |
| pa_raw | 74 [0%] | 0.097 | 0 [0%] | 68 [0%] | 0.081 |
| reset_sgd_log | 600 [60%] | 0.144 | 0 [0%] | 415 [13%] | 0.075 |
| rolling | 266 [0%] | 0.173 | 0 [0%] | 263 [0%] | 0.057 |
| sgd_log | 144 [0%] | 0.106 | 0 [0%] | 133 [0%] | 0.053 |
| sgd_log_platt | 556 [27%] | 0.177 | 0 [0%] | 435 [0%] | 0.037 |

**Track R**

| model | abrupt median steps [%censored] | abrupt post-600 regret | gradual median [%cens] | recurring return(t=2000) median [%cens] | shock post-return regret (t=2100) |
|---|---|---|---|---|---|
| arf | 600 [100%] | 1.054 | 0 [0%] | 104 [0%] | 0.218 |
| bank_rls | 401 [7%] | 0.326 | 0 [0%] | 40 [0%] | 0.037 |
| batch | 600 [100%] | 1.659 | 0 [0%] | 0 [0%] | 0.004 |
| blr | 93 [0%] | 0.119 | 0 [0%] | 96 [0%] | 0.089 |
| frozen | 600 [100%] | 1.946 | 0 [0%] | 0 [0%] | 0.004 |
| hat | 128 [7%] | 0.279 | 0 [0%] | 127 [0%] | 0.117 |
| kalman | 402 [0%] | 0.288 | 0 [0%] | 342 [0%] | 0.065 |
| par_reg | 213 [0%] | 0.279 | 0 [0%] | 221 [0%] | 0.065 |
| reset_rls | 291 [0%] | 0.291 | 0 [0%] | 268 [0%] | 0.095 |
| rls | 219 [0%] | 0.193 | 0 [0%] | 204 [0%] | 0.079 |
| rolling | 134 [0%] | 0.230 | 0 [0%] | 141 [0%] | 0.154 |
| sgd_lin | 410 [0%] | 0.296 | 0 [0%] | 347 [0%] | 0.065 |


### Variance, state growth, compute (all scenarios pooled)


**Track C**

| model | median CV of regret across seeds | worst-seed / median-seed regret (max over scenarios) | state bytes @1000 (median) | @4000 (median) | max growth ratio | learn µs/label | predict µs |
|---|---|---|---|---|---|---|---|
| adwin_bag | 0.15 | 1.8 | 323,429 | 821,538 | 3.89 | 377 | 116 |
| arf | 0.07 | 1.2 | 2,341,288 | 8,084,329 | 5.10 | 510 | 102 |
| bank_sgd_log | 0.10 | 1.7 | 20,145 | 20,401 | 1.03 | 20 | 4 |
| batch | 0.04 | 1.8 | 116,260 | 464,326 | 4.33 | 13 | 7 |
| frozen | 0.10 | 2.2 | 334 | 334 | 1.00 | 1 | 6 |
| hat | 0.16 | 1.6 | 69,087 | 165,306 | 4.72 | 83 | 31 |
| ht | 0.11 | 1.7 | 63,342 | 125,620 | 3.96 | 42 | 23 |
| pa_platt | 0.09 | 1.3 | 611 | 611 | 1.00 | 21 | 10 |
| pa_raw | 0.05 | 1.2 | 505 | 505 | 1.00 | 10 | 9 |
| reset_sgd_log | 0.09 | 1.6 | 19,698 | 19,826 | 1.04 | 12 | 4 |
| rolling | 0.09 | 1.3 | 35,169 | 35,169 | 1.00 | 88 | 8 |
| sgd_log | 0.07 | 1.5 | 788 | 788 | 1.00 | 7 | 4 |
| sgd_log_platt | 0.08 | 1.3 | 894 | 894 | 1.00 | 17 | 10 |

**Track R**

| model | median CV of regret across seeds | worst-seed / median-seed regret (max over scenarios) | state bytes @1000 (median) | @4000 (median) | max growth ratio | learn µs/label | predict µs |
|---|---|---|---|---|---|---|---|
| arf | 0.07 | 1.4 | 564,170 | 2,126,360 | 4.70 | 1135 | 114 |
| bank_rls | 0.10 | 2.1 | 20,428 | 21,962 | 1.11 | 19 | 2 |
| batch | 0.04 | 2.1 | 116,247 | 464,313 | 4.33 | 2 | 2 |
| blr | 0.07 | 1.6 | 1,693 | 1,693 | 1.00 | 22 | 7 |
| frozen | 0.05 | 2.5 | 313 | 313 | 1.00 | 0 | 1 |
| hat | 0.17 | 2.7 | 159,369 | 275,844 | 5.87 | 320 | 13 |
| kalman | 0.09 | 1.5 | 838 | 838 | 1.00 | 13 | 2 |
| par_reg | 0.08 | 1.3 | 649 | 649 | 1.00 | 11 | 4 |
| reset_rls | 0.15 | 2.0 | 19,645 | 19,773 | 1.03 | 15 | 2 |
| rls | 0.09 | 1.5 | 841 | 841 | 1.00 | 11 | 1 |
| rolling | 0.09 | 1.5 | 17,755 | 17,755 | 1.00 | 3 | 1 |
| sgd_lin | 0.09 | 1.4 | 693 | 693 | 1.00 | 6 | 3 |


### Track C realised accuracy and log-loss (held-out, post burn-in) — context for the KL numbers

| model | abrupt | gradual | recurring | shock | random_walk | abrupt_missing | abrupt_delayed | abrupt_nonlinear | stationary | false_drift |
|---|---|---|---|---|---|---|---|---|---|---|
| adwin_bag | 0.734 / 0.534 | 0.740 / 0.525 | 0.724 / 0.548 | 0.810 / 0.431 | 0.752 / 0.507 | 0.674 / 0.631 | 0.729 / 0.546 | 0.592 / 0.673 | 0.818 / 0.418 | 0.817 / 0.434 |
| arf | 0.718 / 0.559 | 0.706 / 0.571 | 0.671 / 0.610 | 0.752 / 0.519 | 0.703 / 0.574 | 0.675 / 0.607 | 0.706 / 0.575 | 0.630 / 0.645 | 0.755 / 0.514 | 0.762 / 0.505 |
| bank_sgd_log | 0.819 / 0.402 | 0.823 / 0.388 | 0.815 / 0.411 | 0.823 / 0.389 | 0.808 / 0.409 | 0.799 / 0.457 | 0.813 / 0.424 | 0.619 / 0.655 | 0.832 / 0.368 | 0.840 / 0.350 |
| batch | 0.701 / 0.619 | 0.715 / 0.587 | 0.689 / 0.627 | 0.827 / 0.389 | 0.738 / 0.531 | 0.660 / 0.758 | 0.699 / 0.637 | 0.586 / 0.676 | 0.835 / 0.361 | 0.843 / 0.342 |
| frozen | 0.643 / 0.918 | 0.645 / 0.905 | 0.644 / 0.913 | 0.824 / 0.392 | 0.670 / 0.746 | 0.638 / 0.977 | 0.634 / 0.925 | 0.554 / 0.719 | 0.833 / 0.367 | 0.838 / 0.351 |
| hat | 0.766 / 0.525 | 0.761 / 0.525 | 0.704 / 0.603 | 0.801 / 0.464 | 0.749 / 0.537 | 0.688 / 0.673 | 0.751 / 0.561 | 0.601 / 0.705 | 0.812 / 0.436 | 0.804 / 0.476 |
| ht | 0.726 / 0.567 | 0.738 / 0.542 | 0.709 / 0.587 | 0.809 / 0.448 | 0.747 / 0.527 | 0.667 / 0.660 | 0.715 / 0.588 | 0.589 / 0.699 | 0.817 / 0.432 | 0.811 / 0.466 |
| pa_platt | 0.804 / 0.419 | 0.816 / 0.397 | 0.769 / 0.482 | 0.822 / 0.390 | 0.803 / 0.419 | 0.754 / 0.506 | 0.797 / 0.445 | 0.619 / 0.652 | 0.831 / 0.368 | 0.840 / 0.350 |
| pa_raw | 0.799 / 0.422 | 0.807 / 0.411 | 0.798 / 0.433 | 0.803 / 0.419 | 0.801 / 0.420 | 0.796 / 0.435 | 0.797 / 0.441 | 0.585 / 0.720 | 0.810 / 0.408 | 0.818 / 0.391 |
| reset_sgd_log | 0.820 / 0.400 | 0.823 / 0.388 | 0.806 / 0.437 | 0.822 / 0.397 | 0.808 / 0.410 | 0.803 / 0.447 | 0.814 / 0.421 | 0.619 / 0.655 | 0.832 / 0.369 | 0.839 / 0.356 |
| rolling | 0.811 / 0.407 | 0.823 / 0.385 | 0.787 / 0.454 | 0.817 / 0.397 | 0.807 / 0.415 | 0.785 / 0.457 | 0.806 / 0.429 | 0.619 / 0.657 | 0.828 / 0.373 | 0.838 / 0.353 |
| sgd_log | 0.817 / 0.402 | 0.823 / 0.387 | 0.808 / 0.422 | 0.818 / 0.398 | 0.815 / 0.402 | 0.805 / 0.429 | 0.810 / 0.429 | 0.602 / 0.692 | 0.826 / 0.382 | 0.832 / 0.375 |
| sgd_log_platt | 0.812 / 0.404 | 0.822 / 0.388 | 0.786 / 0.450 | 0.823 / 0.386 | 0.808 / 0.411 | 0.776 / 0.463 | 0.805 / 0.429 | 0.617 / 0.654 | 0.832 / 0.368 | 0.840 / 0.350 |

## 4.4 Low-SNR sensitivity (κ=1, σ=1.5; 8 seeds; abrupt/recurring/random_walk; **same configs, not re-tuned**)

| track | model | abrupt | recurring | random_walk | geomean ratio vs rolling |
|---|---|---|---|---|---|
| C | adwin_bag | 0.058 | 0.057 | 0.038 | 1.82 |
| C | arf | 0.082 | 0.089 | 0.076 | 2.98 |
| C | bank_sgd_log | 0.019 | 0.028 | 0.019 | 0.79 |
| C | batch | 0.066 | 0.068 | 0.040 | 2.05 |
| C | frozen | 0.128 | 0.125 | 0.079 | 3.93 |
| C | hat | 0.067 | 0.096 | 0.065 | 2.71 |
| C | ht | 0.076 | 0.077 | 0.054 | 2.47 |
| C | pa_platt | 0.020 | 0.034 | 0.020 | 0.87 |
| C | pa_raw | 0.075 | 0.073 | 0.075 | 2.71 |
| C | reset_sgd_log | 0.019 | 0.028 | 0.019 | 0.79 |
| C | rolling | 0.023 | 0.037 | 0.024 | 1.00 |
| C | sgd_log | 0.050 | 0.051 | 0.049 | 1.82 |
| C | sgd_log_platt | 0.020 | 0.028 | 0.020 | 0.81 |
| R | arf | 0.769 | 0.863 | 0.683 | 4.13 |
| R | bank_rls | 0.090 | 0.135 | 0.208 | 0.73 |
| R | batch | 0.634 | 0.668 | 0.376 | 2.91 |
| R | blr | 0.207 | 0.238 | 0.205 | 1.16 |
| R | frozen | 1.123 | 1.167 | 0.747 | 5.34 |
| R | hat | 0.663 | 0.846 | 0.707 | 3.95 |
| R | kalman | 0.106 | 0.193 | 0.117 | 0.72 |
| R | par_reg | 0.155 | 0.273 | 0.148 | 0.99 |
| R | reset_rls | 0.090 | 0.197 | 0.206 | 0.83 |
| R | rls | 0.124 | 0.181 | 0.131 | 0.77 |
| R | rolling | 0.161 | 0.233 | 0.172 | 1.00 |
| R | sgd_lin | 0.107 | 0.194 | 0.117 | 0.72 |

Reading: at ~3× lower SNR the tuned rolling window (chosen at normal SNR) is too short and its regret grows, so linear recursive learners with forgetting (RLS, Kalman, SGD, `bank_*`) gain 20–28 % over it instead of 12–15 %. Trees/ARF/batch/frozen remain 2–5× worse. Because neither side was re-tuned this partly measures *tuning robustness*, not a fixed capability (INFERENCE).

## 4.5 Observations worth stating plainly
* **Stationary / false-drift controls:** the expanding `batch` refit is best (0.003) — adaptive learners pay a variance tax (rolling 0.014, `sgd_log` 0.024; RLS 0.011). `false_drift` (3× feature scale + noise burst, no concept change) is the scenario that breaks plain SGD (C 0.037 vs rolling 0.016; R 0.082) and ARF/HAT (R 0.69–0.88 vs 0.03): adaptivity to *scale* is not adaptivity to *concept*.
* **Trees barely win on the nonlinear concept and nowhere else:** `abrupt_nonlinear` (C): ARF 0.309 (≈4 % below linear rolling 0.321, the only sub-0.31 value), other trees 0.339–0.369, frozen 0.383. Nothing learns the interaction concept well in ≤2 000 post-change labels (oracle regret is 0), so this is at best a weak signal for the "trees handle non-linearity" motivation at T=4000; larger n is UNKNOWN.
* **Compute (OBSERVED, shared container, indicative):** linear recursive learners 1–90 µs/label; Hoeffding tree family 40–320 µs; ARF/ADWIN-bagging 380–1 100 µs. State: linear 0.3–1.7 KB; rolling 18–35 KB (window buffer); trees 60 KB→ 8 MB (ARF, C) — trees grow ×4–6 between t=1000 and 4000.
