# 03 — Static calibration (Q1)

**Setup:** base model fit on train; calibrator fit on the calibration block; scores on held-out. Base models: LR, Gaussian NB, HistGradientBoosting (300 iters, no early stopping — deliberately over-confident). Mean ± 95% interval over 20 seeds (synthetic, breast-cancer); ELEC2 is one realisation. ECE = top-label, equal-mass 15 bins. `ORACLE` = the true generating probability.

## Synthetic world (held-out n=6000, cal n=3000)
| base | cal | brier | logloss | ece | ece_pos | fcr |
|---|---|---|---|---|---|---|
| GNB | bayes_bin | 0.203±0.001 | 0.593±0.002 | 0.027±0.003 | 0.027±0.002 | 0.040±0.005 |
| GNB | beta | 0.202±0.001 | 0.591±0.002 | 0.022±0.001 | 0.024±0.002 | 0.031±0.002 |
| GNB | isotonic | 0.203±0.001 | 0.593±0.003 | 0.024±0.003 | 0.025±0.003 | 0.042±0.005 |
| GNB | platt | 0.202±0.001 | 0.592±0.002 | 0.023±0.002 | 0.025±0.002 | 0.032±0.002 |
| GNB | raw | 0.202±0.001 | 0.592±0.002 | 0.027±0.003 | 0.029±0.004 | 0.024±0.001 |
| GNB | temperature | 0.202±0.001 | 0.592±0.002 | 0.023±0.002 | 0.025±0.003 | 0.032±0.002 |
| HGB | bayes_bin | 0.203±0.001 | 0.589±0.002 | 0.028±0.003 | 0.028±0.003 | 0.032±0.004 |
| HGB | beta | 0.201±0.001 | 0.585±0.002 | 0.022±0.002 | 0.022±0.002 | 0.027±0.002 |
| HGB | isotonic | 0.202±0.001 | 0.588±0.002 | 0.023±0.002 | 0.025±0.002 | 0.031±0.003 |
| HGB | platt | 0.201±0.001 | 0.586±0.002 | 0.022±0.002 | 0.023±0.002 | 0.028±0.002 |
| HGB | raw | 0.218±0.001 | 0.660±0.004 | 0.118±0.003 | 0.118±0.003 | 0.119±0.002 |
| HGB | temperature | 0.201±0.001 | 0.586±0.002 | 0.022±0.002 | 0.023±0.002 | 0.028±0.002 |
| LR | bayes_bin | 0.203±0.001 | 0.592±0.002 | 0.028±0.003 | 0.028±0.002 | 0.038±0.003 |
| LR | beta | 0.202±0.001 | 0.590±0.002 | 0.022±0.002 | 0.023±0.002 | 0.032±0.002 |
| LR | isotonic | 0.202±0.001 | 0.592±0.002 | 0.027±0.003 | 0.027±0.002 | 0.037±0.004 |
| LR | platt | 0.202±0.001 | 0.591±0.002 | 0.023±0.001 | 0.024±0.002 | 0.032±0.002 |
| LR | raw | 0.202±0.001 | 0.591±0.002 | 0.022±0.002 | 0.024±0.002 | 0.035±0.002 |
| LR | temperature | 0.202±0.001 | 0.591±0.002 | 0.023±0.002 | 0.024±0.002 | 0.032±0.002 |
| ORACLE | true_p | 0.182±0.001 | 0.536±0.002 | 0.017±0.002 | 0.016±0.001 | 0.035±0.001 |

Reading (OBSERVED):
* The over-confident GBM is badly miscalibrated raw (ECE 0.118, FCR 0.119). Platt, temperature and beta all bring it to ≈0.022 (ORACLE floor is 0.017 — the estimator's own noise), and log-loss falls 0.660 → 0.586 (oracle 0.536).
* LR and GNB are already ≈calibrated in this world (the world is logistic-like, so this **favours LR**): calibration does no harm (0.022 → 0.023) but gains nothing.
* Isotonic and Bayes-binning are slightly *worse* than the 2-parameter methods at n=3000 (0.027–0.028 vs 0.022–0.023 for LR/bayes_bin), consistent with variance of non-parametric maps.
* Calibration changes probabilities monotonically, so it **does not change the ranking / accuracy / AUROC** — Brier gains come only from removing calibration error.

## Small sample: breast cancer (cal n≈170; 20 random splits)
| base | cal | brier | logloss | ece | ece_pos | fcr |
|---|---|---|---|---|---|---|
| GNB | bayes_bin | 0.053±0.003 | 0.226±0.039 | 0.031±0.005 | 0.032±0.004 | 0.026±0.011 |
| GNB | beta | 0.049±0.005 | 0.201±0.029 | 0.049±0.005 | 0.042±0.005 | 0.039±0.007 |
| GNB | isotonic | 0.049±0.004 | 0.183±0.017 | 0.041±0.005 | 0.041±0.005 | 0.035±0.007 |
| GNB | platt | 0.049±0.005 | 0.189±0.019 | 0.049±0.007 | 0.041±0.006 | 0.038±0.006 |
| GNB | raw | 0.060±0.007 | 0.493±0.065 | 0.058±0.008 | 0.043±0.006 | 0.059±0.007 |
| GNB | temperature | 0.049±0.005 | 0.183±0.016 | 0.052±0.006 | 0.043±0.005 | 0.038±0.006 |
| HGB | bayes_bin | 0.049±0.005 | 0.195±0.024 | 0.027±0.003 | 0.032±0.004 | 0.021±0.007 |
| HGB | beta | 0.038±0.005 | 0.151±0.022 | 0.030±0.007 | 0.034±0.007 | 0.030±0.006 |
| HGB | isotonic | 0.038±0.005 | 0.146±0.016 | 0.034±0.005 | 0.037±0.006 | 0.029±0.008 |
| HGB | platt | 0.037±0.005 | 0.147±0.021 | 0.028±0.006 | 0.032±0.007 | 0.027±0.006 |
| HGB | raw | 0.042±0.006 | 0.253±0.042 | 0.038±0.006 | 0.033±0.005 | 0.038±0.006 |
| HGB | temperature | 0.037±0.004 | 0.137±0.015 | 0.029±0.006 | 0.032±0.004 | 0.024±0.006 |
| LR | bayes_bin | 0.052±0.004 | 0.173±0.013 | 0.027±0.004 | 0.028±0.004 | 0.020±0.009 |
| LR | beta | 0.039±0.003 | 0.152±0.023 | 0.028±0.004 | 0.028±0.004 | 0.025±0.005 |
| LR | isotonic | 0.043±0.004 | 0.159±0.014 | 0.039±0.005 | 0.042±0.003 | 0.028±0.007 |
| LR | platt | 0.039±0.003 | 0.135±0.012 | 0.024±0.004 | 0.027±0.005 | 0.022±0.004 |
| LR | raw | 0.040±0.003 | 0.152±0.019 | 0.025±0.004 | 0.029±0.004 | 0.030±0.004 |
| LR | temperature | 0.039±0.003 | 0.137±0.012 | 0.023±0.005 | 0.028±0.004 | 0.023±0.004 |

Isotonic is worse than Platt/temperature for LR (ECE 0.039 vs 0.024, raw 0.025); Bayes-binning gives the lowest ECE for GNB (0.031 vs 0.049–0.058) but a worse Brier than Platt (0.053 vs 0.049). With ~170 calibration points the ECE differences between methods are of the order of the interval widths — **no method is reliably distinguishable from raw except for the over-confident GNB/HGB log-loss gains**.

## Real, drifting data: ELEC2 (forecast y_{t+1}; cal 9000–13500; held-out 6 chunks)
Mean over the six held-out chunks:
| base | cal | brier | logloss | ece | fcr |
|---|---|---|---|---|---|
| GNB | bayes_bin | 0.164 | 0.5 | 0.062 | 0.046 |
| GNB | beta | 0.165 | 0.522 | 0.06 | 0.037 |
| GNB | isotonic | 0.163 | 0.5 | 0.056 | 0.032 |
| GNB | platt | 0.165 | 0.53 | 0.057 | 0.036 |
| GNB | raw | 0.181 | 0.611 | 0.101 | 0.093 |
| GNB | temperature | 0.172 | 0.536 | 0.061 | 0.042 |
| HGB | bayes_bin | 0.169 | 0.524 | 0.102 | 0.097 |
| HGB | beta | 0.168 | 0.521 | 0.081 | 0.101 |
| HGB | isotonic | 0.169 | 0.521 | 0.09 | 0.09 |
| HGB | platt | 0.166 | 0.53 | 0.08 | 0.099 |
| HGB | raw | 0.17 | 0.595 | 0.107 | 0.124 |
| HGB | temperature | 0.16 | 0.508 | 0.068 | 0.091 |
| LR | bayes_bin | 0.202 | 0.595 | 0.156 | 0.203 |
| LR | beta | 0.201 | 0.611 | 0.153 | 0.16 |
| LR | isotonic | 0.205 | 0.604 | 0.159 | 0.208 |
| LR | platt | 0.2 | 0.619 | 0.153 | 0.159 |
| LR | raw | 0.178 | 0.532 | 0.103 | 0.013 |
| LR | temperature | 0.209 | 0.647 | 0.168 | 0.173 |

ECE per chunk (calibration decay over time):
| base | cal | chunk0 | chunk1 | chunk2 | chunk3 | chunk4 | chunk5 |
|---|---|---|---|---|---|---|---|
| GNB | isotonic | 0.049 | 0.091 | 0.054 | 0.06 | 0.05 | 0.032 |
| GNB | platt | 0.072 | 0.071 | 0.054 | 0.059 | 0.05 | 0.039 |
| GNB | raw | 0.067 | 0.106 | 0.132 | 0.149 | 0.065 | 0.086 |
| GNB | temperature | 0.049 | 0.07 | 0.071 | 0.072 | 0.059 | 0.046 |
| HGB | isotonic | 0.072 | 0.109 | 0.138 | 0.158 | 0.035 | 0.03 |
| HGB | platt | 0.059 | 0.099 | 0.127 | 0.145 | 0.03 | 0.022 |
| HGB | raw | 0.096 | 0.129 | 0.148 | 0.17 | 0.059 | 0.042 |
| HGB | temperature | 0.048 | 0.082 | 0.104 | 0.125 | 0.025 | 0.024 |
| LR | isotonic | 0.174 | 0.177 | 0.213 | 0.225 | 0.096 | 0.069 |
| LR | platt | 0.173 | 0.168 | 0.212 | 0.232 | 0.078 | 0.054 |
| LR | raw | 0.1 | 0.132 | 0.124 | 0.12 | 0.049 | 0.092 |
| LR | temperature | 0.187 | 0.191 | 0.23 | 0.246 | 0.09 | 0.063 |

Reading (OBSERVED, single realisation):
* Static calibration **does not transfer across time** on real data. For LR, calibrating on the cal window *worsened* held-out ECE (0.103 raw → ≈0.15–0.17 calibrated): the calibration window was not representative of later chunks (and chunks 0–3 vs 4–5 differ sharply for every method).
* For HGB/GNB the calibrated variants are better than raw on average (e.g. temperature 0.068 vs raw 0.108 for HGB) but remain ≫ 0.03 and swing 0.025–0.125 between chunks.
* ELEC2 has known concept drift, so this is the behaviour the pre-declared criterion should expose: **Q1 is answered YES on stationary data and NO across time on the real drifting series.**

## Answer to Q1
* **Yes, under stationarity and with enough calibration data (≥ ~3000)**: 1–2-parameter calibrators (Platt/temperature/beta) reach ECE ≈ 0.02; simplest reference = **Platt (or temperature) fit on a held-aside calibration block**.
* Non-parametric maps (isotonic, Bayes-binning) offered no gain here and cost variance at moderate n. (Untested: much larger n, where isotonic is known to catch up — UNKNOWN.)
* No, across time on ELEC2 (see 04 for whether online updating repairs this).
